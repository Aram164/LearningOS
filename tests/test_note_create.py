"""General durable-note creation: governed bytes, honest defaults, atomic succession.

`note.create` is the governed form of WORKFLOWS §3: capture and scratch
become durable understanding through an approved envelope, never a direct
file save. The handler owns authorship/review defaults, preserves body
bytes verbatim, refuses id collisions (updates go through note.revise),
keeps the reference/question roles with their dedicated capabilities, and
deprecates superseded predecessors in the same transaction.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date

from gateway_helpers import LOS, approved_v2_cli, file_sha256

from learning_os.loader import load_repo

NOTE_ID = "note-create-demo"
NOTE_PATH = "knowledge/notes/mathematics/note-create-demo.md"
BODY = "  \n# Demo synthesis — Schmælzung\n\nLine one.\r\nLine two without final newline"


def _save(mini_repo, body: bytes, key: str, note: dict | None = None,
          note_id: str = NOTE_ID, path: str = NOTE_PATH,
          title: str = "Demo synthesis", sha256: str | None = None,
          artifact_ids: list[str] | None = None):
    record = {"id": note_id, "title": title, "path": path}
    if note:
        record.update(note)
    body_file = mini_repo / f"body-{key}.bin"
    body_file.write_bytes(body)
    return approved_v2_cli(
        mini_repo, "note-create",
        "--note", json.dumps(record),
        "--body-file", str(body_file),
        "--body-file-sha256", sha256 or file_sha256(body_file),
        artifact_ids=artifact_ids or [note_id], idempotency_key=key,
    )


def _note_bytes(mini_repo, path: str = NOTE_PATH) -> bytes:
    return (mini_repo / path).read_bytes()


def test_create_preserves_bytes_and_sets_unreviewed_defaults(mini_repo):
    body = BODY.encode("utf-8")
    result = _save(mini_repo, body, "create-new", note={
        "concepts": ["concept-expected-value"],
        "sources": ["source-demo-book"],
        "contexts": ["workspace-demo"],
    })
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    created = payload["result"]
    assert created["note_id"] == NOTE_ID
    assert created["deprecated"] == []
    raw = _note_bytes(mini_repo)
    assert raw.endswith(body)
    assert b"operator-drafted" in raw and b"unreviewed" in raw
    repo = load_repo(mini_repo)
    note = repo.notes[NOTE_ID]
    assert note.meta["role"] == "synthesis"
    assert note.meta["state"] == "rough"
    assert note.meta["authorship"] == "operator-drafted"
    assert note.meta["semantic_review"] == "unreviewed"
    assert note.meta["created"] == date.today().isoformat()
    assert "reviewed" not in note.meta
    assert note.meta["concepts"] == ["concept-expected-value"]
    assert note.meta["sources"] == ["source-demo-book"]
    assert note.meta["contexts"] == ["workspace-demo"]
    # The loader strips leading whitespace and normalizes CRLF on read
    # (shared frontmatter behavior); the file bytes above are the
    # authoritative preserved body.
    assert note.body == BODY.replace("\r\n", "\n").lstrip()


def test_bare_command_never_writes(mini_repo):
    body_file = mini_repo / "body-bare.bin"
    body_file.write_bytes(BODY.encode("utf-8"))
    result = subprocess.run(
        [sys.executable, str(LOS), "--root", str(mini_repo), "note-create",
         "--note", json.dumps({"id": NOTE_ID, "title": "Demo", "path": NOTE_PATH}),
         "--body-file", str(body_file),
         "--body-file-sha256", file_sha256(body_file)],
        capture_output=True, text=True, cwd=mini_repo.parent,
    )
    assert result.returncode == 2, result.stdout + result.stderr
    assert "GatewayEnvelopeV2" in result.stderr
    assert not (mini_repo / NOTE_PATH).exists()


def test_second_create_with_same_id_refuses(mini_repo):
    body = BODY.encode("utf-8")
    first = _save(mini_repo, body, "collision-first")
    assert first.returncode == 0, first.stdout + first.stderr
    before = _note_bytes(mini_repo)
    again = _save(mini_repo, body, "collision-again")
    assert again.returncode != 0
    assert "note.revise" in again.stdout + again.stderr
    assert _note_bytes(mini_repo) == before


def test_existing_note_id_refuses(mini_repo):
    body = BODY.encode("utf-8")
    result = _save(mini_repo, body, "collision-user-note", note_id="note-demo",
                    path="knowledge/notes/mathematics/note-demo.md")
    assert result.returncode != 0


def test_reserved_roles_keep_their_dedicated_capabilities(mini_repo):
    body = BODY.encode("utf-8")
    reference = _save(mini_repo, body, "reserved-reference",
                       note={"role": "reference"})
    assert reference.returncode != 0
    assert "note.analysis.save" in reference.stdout + reference.stderr
    question = _save(mini_repo, body, "reserved-question",
                      note={"role": "question"})
    assert question.returncode != 0
    assert "atlas.question.save" in question.stdout + question.stderr
    assert not (mini_repo / NOTE_PATH).exists()


def test_unknown_fields_and_self_promotion_refuse(mini_repo):
    body = BODY.encode("utf-8")
    promoted = _save(mini_repo, body, "self-promotion",
                      note={"reviewed": True, "authorship": "user"})
    assert promoted.returncode != 0
    assert not (mini_repo / NOTE_PATH).exists()


def test_body_sha_mismatch_refuses(mini_repo):
    body = BODY.encode("utf-8")
    result = _save(mini_repo, body, "sha-mismatch", sha256="sha256:" + "00" * 32)
    assert result.returncode != 0
    assert not (mini_repo / NOTE_PATH).exists()


def test_successor_deprecates_predecessor_atomically(mini_repo):
    before = load_repo(mini_repo).notes["note-demo"]
    before_body = before.body
    body = BODY.encode("utf-8")
    result = _save(mini_repo, body, "successor-new",
                    note={"supersedes": ["note-demo"]},
                    artifact_ids=[NOTE_ID, "note-demo"])
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["result"]["deprecated"] == ["knowledge/notes/mathematics/note-demo.md"]
    repo = load_repo(mini_repo)
    assert repo.notes[NOTE_ID].meta["supersedes"] == ["note-demo"]
    old = repo.notes["note-demo"]
    assert old.meta["state"] == "deprecated"
    assert old.body == before_body


def test_failed_succession_writes_nothing(mini_repo):
    body = BODY.encode("utf-8")
    before_old = (mini_repo / "knowledge/notes/mathematics/note-demo.md").read_bytes()
    result = _save(mini_repo, body, "successor-bad",
                    note={"supersedes": ["note-demo", "note-missing"]},
                    artifact_ids=[NOTE_ID, "note-demo", "note-missing"])
    assert result.returncode != 0
    assert not (mini_repo / NOTE_PATH).exists()
    assert (mini_repo / "knowledge/notes/mathematics/note-demo.md").read_bytes() == before_old


def test_supersedes_self_and_dangling_refs_refuse(mini_repo):
    body = BODY.encode("utf-8")
    self_ref = _save(mini_repo, body, "supersede-self",
                      note={"supersedes": [NOTE_ID]})
    assert self_ref.returncode != 0
    dangling_concept = _save(mini_repo, body, "dangling-concept",
                              note={"concepts": ["concept-missing"]})
    assert dangling_concept.returncode != 0
    dangling_source = _save(mini_repo, body, "dangling-source",
                             note={"sources": ["source-missing"]})
    assert dangling_source.returncode != 0
    dangling_context = _save(mini_repo, body, "dangling-context",
                              note={"contexts": ["workspace-missing"]})
    assert dangling_context.returncode != 0
    assert not (mini_repo / NOTE_PATH).exists()


def test_bad_id_and_path_refuse(mini_repo):
    body = BODY.encode("utf-8")
    mismatch = _save(mini_repo, body, "path-mismatch",
                      path="knowledge/notes/mathematics/note-other.md")
    assert mismatch.returncode != 0
    escape = _save(mini_repo, body, "path-escape",
                    path="knowledge/garden/note-create-demo.md")
    assert escape.returncode != 0
    bad_id = _save(mini_repo, body, "bad-id", note_id="Not A Note Id",
                    path="knowledge/notes/mathematics/Not A Note Id.md")
    assert bad_id.returncode != 0
    assert not (mini_repo / NOTE_PATH).exists()


def test_empty_and_non_utf8_bodies_refuse(mini_repo):
    empty = _save(mini_repo, b"", "empty-body")
    assert empty.returncode != 0
    binary = _save(mini_repo, b"\xff\xfe not utf-8", "binary-body")
    assert binary.returncode != 0
    assert not (mini_repo / NOTE_PATH).exists()
