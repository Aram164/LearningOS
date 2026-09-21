"""Durable source-analysis notes: exact bytes, honest bindings, safe replay.

The handler owns authorship/review defaults, preserves body bytes verbatim
(including leading whitespace, CRLF, and Unicode), replays identical
requests, and refuses id collisions, frozen-hash mismatches, and resolved
bindings to unregistered sources.
"""

from __future__ import annotations

import hashlib
import json

from gateway_helpers import approved_v2_cli, file_sha256

from learning_os.loader import load_repo
from learning_os.material_analysis import binding_consistent, observe_local_material

NOTE_ID = "note-analysis-demo-pp1-3"
NOTE_PATH = "knowledge/notes/mathematics/note-analysis-demo-pp1-3.md"
BODY = "  \n# Demo analysis — Schmælzung\n\nLine one.\r\nLine two without final newline"


def _binding(**overrides):
    binding = {
        "resolution": "unresolved",
        "material": "demo/deck.pdf",
        "recorded_source_digest": "ab" * 32,
        "inspected_range": {"start": 1, "end": 3},
        "frozen_input_sha256": hashlib.sha256(BODY.encode("utf-8")).hexdigest(),
        "frozen_input_bytes": len(BODY.encode("utf-8")),
    }
    binding.update(overrides)
    return binding


def _save(mini_repo, body: bytes, binding: dict, key: str, note_id: str = NOTE_ID,
          path: str = NOTE_PATH, title: str = "Demo analysis"):
    body_file = mini_repo / f"body-{key}.bin"
    body_file.write_bytes(body)
    return approved_v2_cli(
        mini_repo, "note-analysis-save",
        "--analysis", json.dumps({"id": note_id, "title": title,
                                  "path": path, "binding": binding}),
        "--body-file", str(body_file),
        "--body-file-sha256", file_sha256(body_file),
        artifact_ids=[note_id], idempotency_key=key,
    )


def _note_bytes(mini_repo, path: str = NOTE_PATH) -> bytes:
    return (mini_repo / path).read_bytes()


def test_binding_rules_keep_resolutions_honest():
    base = {"material": "demo/deck.pdf", "recorded_source_digest": "ab" * 32,
            "inspected_range": {"start": 1, "end": 3},
            "frozen_input_sha256": "cd" * 32}
    assert binding_consistent({**base, "resolution": "resolved",
                               "source_id": "source-x",
                               "live_source_digest": "ab" * 32}) is None
    assert binding_consistent({**base, "resolution": "resolved",
                               "live_source_digest": "ab" * 32}) is not None
    assert binding_consistent({**base, "resolution": "resolved",
                               "source_id": "source-x"}) is not None
    assert binding_consistent({**base, "resolution": "resolved",
                               "source_id": "source-x",
                               "live_source_digest": "ef" * 32}) is not None
    assert binding_consistent({**base, "resolution": "stale",
                               "live_source_digest": "ef" * 32}) is None
    assert binding_consistent({**base, "resolution": "stale"}) is not None
    assert binding_consistent({**base, "resolution": "unavailable"}) is None
    assert binding_consistent({**base, "resolution": "unavailable",
                               "live_source_digest": "ab" * 32}) is not None
    assert binding_consistent({**base, "resolution": "unresolved"}) is None
    assert binding_consistent({**base, "resolution": "nope"}) is not None


def test_observe_local_material_reports_current_stale_missing(tmp_path):
    root = tmp_path / "materials"
    root.mkdir()
    target = root / "deck.pdf"
    target.write_bytes(b"v1")
    digest = hashlib.sha256(b"v1").hexdigest()
    assert observe_local_material(root, "deck.pdf", digest)["status"] == "current"
    target.write_bytes(b"v2")
    stale = observe_local_material(root, "deck.pdf", digest)
    assert stale["status"] == "stale"
    assert stale["live_digest"] == hashlib.sha256(b"v2").hexdigest()
    assert observe_local_material(root, "gone.pdf", digest)["status"] == "missing"
    assert observe_local_material(root, "../escape.pdf", digest)["status"] == "outside-boundary"
    assert observe_local_material(root, "/abs.pdf", digest)["status"] == "outside-boundary"


def test_save_preserves_bytes_and_sets_unreviewed_defaults(mini_repo):
    body = BODY.encode("utf-8")
    result = _save(mini_repo, body, _binding(), "save-new")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True and payload["replayed"] is False
    raw = _note_bytes(mini_repo)
    assert raw.endswith(body)
    assert b"operator-drafted" in raw and b"unreviewed" in raw
    repo = load_repo(mini_repo)
    note = repo.notes[NOTE_ID]
    assert note.meta["role"] == "reference"
    assert note.meta["state"] == "rough"
    assert note.meta["authorship"] == "operator-drafted"
    assert note.meta["semantic_review"] == "unreviewed"
    # The loader strips leading whitespace and normalizes CRLF on read
    # (shared frontmatter behavior); the file bytes above are the
    # authoritative preserved body.
    assert note.body == BODY.replace("\r\n", "\n").lstrip()
    stored = note.meta["material_analysis"]["frozen_input_bytes"]
    assert raw[-stored:] == body


def test_identical_request_replays_without_a_second_write(mini_repo):
    body = BODY.encode("utf-8")
    first = _save(mini_repo, body, _binding(), "replay-first")
    assert first.returncode == 0, first.stdout + first.stderr
    before = _note_bytes(mini_repo)
    second = _save(mini_repo, body, _binding(), "replay-second")
    assert second.returncode == 0, second.stdout + second.stderr
    assert json.loads(second.stdout)["replayed"] is True
    assert _note_bytes(mini_repo) == before


def test_collision_with_different_analysis_refuses(mini_repo):
    body = BODY.encode("utf-8")
    first = _save(mini_repo, body, _binding(), "collision-first")
    assert first.returncode == 0, first.stdout + first.stderr
    before = _note_bytes(mini_repo)
    other = _save(mini_repo, body + b"\nchanged", _binding(), "collision-body")
    assert other.returncode != 0
    assert _note_bytes(mini_repo) == before
    retitled = _save(mini_repo, body, _binding(), "collision-title", title="Other")
    assert retitled.returncode != 0
    rebound = _save(mini_repo, body, _binding(resolution="stale",
                                              live_source_digest="ef" * 32),
                     "collision-binding")
    assert rebound.returncode != 0
    assert _note_bytes(mini_repo) == before


def test_existing_non_analysis_note_id_refuses(mini_repo):
    body = BODY.encode("utf-8")
    result = _save(mini_repo, body, _binding(), "collision-user-note",
                    note_id="note-demo",
                    path="knowledge/notes/mathematics/note-demo.md")
    assert result.returncode != 0


def test_frozen_hash_mismatch_and_self_promotion_refuse(mini_repo):
    body = BODY.encode("utf-8")
    tampered = _save(mini_repo, body, _binding(frozen_input_sha256="00" * 32),
                      "frozen-mismatch")
    assert tampered.returncode != 0
    assert not (mini_repo / NOTE_PATH).exists()
    shortened = _save(mini_repo, body, _binding(frozen_input_bytes=len(body) - 1),
                       "frozen-length")
    assert shortened.returncode != 0
    assert not (mini_repo / NOTE_PATH).exists()
    promoted_binding = {"id": NOTE_ID, "title": "Demo", "path": NOTE_PATH,
                        "binding": _binding(), "authorship": "user"}
    body_file = mini_repo / "body-promoted.bin"
    body_file.write_bytes(body)
    refused = approved_v2_cli(
        mini_repo, "note-analysis-save",
        "--analysis", json.dumps(promoted_binding),
        "--body-file", str(body_file),
        "--body-file-sha256", file_sha256(body_file),
        artifact_ids=[NOTE_ID], idempotency_key="self-promotion",
    )
    assert refused.returncode != 0
    assert not (mini_repo / NOTE_PATH).exists()


def test_resolved_binding_requires_a_registered_source(mini_repo):
    body = BODY.encode("utf-8")
    digest = "ab" * 32
    unknown = _save(mini_repo, body,
                     _binding(resolution="resolved", source_id="source-nope",
                              live_source_digest=digest), "resolved-unknown")
    assert unknown.returncode != 0
    assert not (mini_repo / NOTE_PATH).exists()
    known = _save(mini_repo, body,
                   _binding(resolution="resolved", source_id="source-demo-book",
                            live_source_digest=digest), "resolved-known")
    assert known.returncode == 0, known.stdout + known.stderr
    assert load_repo(mini_repo).notes[NOTE_ID].meta[
        "material_analysis"]["source_id"] == "source-demo-book"


def test_dishonest_bindings_refuse(mini_repo):
    body = BODY.encode("utf-8")
    for key, binding in (
        ("stale-equal", _binding(resolution="stale", live_source_digest="ab" * 32)),
        ("unavailable-live", _binding(resolution="unavailable",
                                      live_source_digest="ab" * 32)),
        ("resolved-noid", _binding(resolution="resolved",
                                   live_source_digest="ab" * 32)),
    ):
        result = _save(mini_repo, body, binding, key)
        assert result.returncode != 0, key
    assert not (mini_repo / NOTE_PATH).exists()
