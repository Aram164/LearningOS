"""note-evidence: recording that work exists, without judging it.

PHILOSOPHY §3.6 separates having seen a concept from being able to derive,
explain and apply it. These tests pin the properties that make the distinction
trustworthy: the note body is never touched, evidence is strictly append-only,
and a trail is addressed by typed URI so it survives the file moving.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from gateway_helpers import approved_v2_call

from learning_os.loader import EVIDENCE_SCHEMES, load_repo, parse_frontmatter

LOS = Path(__file__).resolve().parent.parent / "tools" / "los.py"

DERIVATION = "material://demo/mle-derivation.pdf"
EXERCISE = "material://demo/sheet-4.pdf"


def run_los(root: Path, *args: str):
    return subprocess.run(
        [sys.executable, str(LOS), "--root", str(root), *args],
        capture_output=True, text=True, timeout=120)


def _note(root: Path) -> Path:
    return root / "knowledge" / "notes" / "mathematics" / "note-demo.md"


def _meta(root: Path) -> dict:
    return parse_frontmatter(_note(root).read_text(encoding="utf-8"), _note(root))[0]


def _record_evidence(
    root: Path,
    evidence_type: str,
    ref: str,
    *,
    key: str,
):
    return approved_v2_call(
        root,
        capability="note.evidence.add",
        payload={
            "note_id": "note-demo",
            "evidence_type": evidence_type,
            "ref": ref,
        },
        artifact_ids=["note-demo"],
        idempotency_key=key,
    )


def test_records_evidence_and_leaves_the_body_verbatim(mini_repo):
    before = _note(mini_repo).read_text(encoding="utf-8")
    _, body_before = parse_frontmatter(before, _note(mini_repo))

    proc = _record_evidence(
        mini_repo,
        "derivation",
        DERIVATION,
        key="note-evidence-body-001",
    )
    assert proc.returncode == 0, proc.stderr
    response = json.loads(proc.stdout)
    assert response["ok"] is True
    payload = response["result"]
    assert payload["evidence"] == {"type": "derivation", "ref": DERIVATION}
    assert payload["evidence_count"] == 1
    assert payload["scheme"] == "material"

    meta_after, body_after = parse_frontmatter(
        _note(mini_repo).read_text(encoding="utf-8"), _note(mini_repo))
    assert body_after.strip() == body_before.strip(), "note body must survive verbatim"
    assert meta_after["evidence"] == [{"type": "derivation", "ref": DERIVATION}]
    # metadata this command has no business touching
    assert meta_after["id"] == "note-demo"
    assert meta_after["role"] == "synthesis"
    assert meta_after["title"] == "Demo note"


def test_explanation_is_a_recordable_type(mini_repo):
    """PHILOSOPHY §3.6 asks 'can I explain it'; the schema must be able to say so."""
    proc = _record_evidence(
        mini_repo,
        "explanation",
        "note://note-demo",
        key="note-evidence-explanation-001",
    )
    assert proc.returncode == 0, proc.stderr
    assert _meta(mini_repo)["evidence"][0]["type"] == "explanation"


def test_evidence_is_append_only(mini_repo):
    assert _record_evidence(
        mini_repo,
        "derivation",
        DERIVATION,
        key="note-evidence-append-001",
    ).returncode == 0
    second = _record_evidence(
        mini_repo,
        "exercise",
        EXERCISE,
        key="note-evidence-append-002",
    )
    assert second.returncode == 0, second.stderr

    assert _meta(mini_repo)["evidence"] == [
        {"type": "derivation", "ref": DERIVATION},
        {"type": "exercise", "ref": EXERCISE},
    ], "earlier trails must survive later ones, in order"
    assert json.loads(second.stdout)["result"]["evidence_count"] == 2


def test_duplicate_evidence_is_refused(mini_repo):
    assert _record_evidence(
        mini_repo,
        "derivation",
        DERIVATION,
        key="note-evidence-duplicate-001",
    ).returncode == 0
    again = _record_evidence(
        mini_repo,
        "derivation",
        DERIVATION,
        key="note-evidence-duplicate-002",
    )
    assert again.returncode == 2
    assert "already recorded" in json.loads(again.stdout)["error"]["message"]
    assert len(_meta(mini_repo)["evidence"]) == 1


def test_untyped_ref_is_refused_with_the_allowed_vocabulary(mini_repo):
    """A bare path would break the moment the file moved; say so usefully."""
    before = _note(mini_repo).read_text(encoding="utf-8")
    proc = run_los(mini_repo, "note-evidence", "note-demo",
                   "derivation", "knowledge/attachments/derivation.md")
    assert proc.returncode == 2
    assert "no valid URI scheme" in proc.stderr
    for scheme in EVIDENCE_SCHEMES:
        assert scheme in proc.stderr
    assert _note(mini_repo).read_text(encoding="utf-8") == before


def test_unknown_note_is_refused_without_writing(mini_repo):
    before = _note(mini_repo).read_text(encoding="utf-8")
    proc = run_los(mini_repo, "note-evidence", "note-missing", "exam", DERIVATION)
    assert proc.returncode == 2
    assert "note not found" in proc.stderr
    assert _note(mini_repo).read_text(encoding="utf-8") == before


def test_unknown_evidence_type_is_rejected_by_the_parser(mini_repo):
    proc = run_los(mini_repo, "note-evidence", "note-demo", "vibes", DERIVATION)
    assert proc.returncode != 0
    assert "invalid choice" in proc.stderr


def test_note_stays_loadable_and_valid_after_recording(mini_repo):
    assert _record_evidence(
        mini_repo,
        "derivation",
        DERIVATION,
        key="note-evidence-loadable-001",
    ).returncode == 0
    repo = load_repo(mini_repo)
    assert repo.notes["note-demo"].meta["evidence"][0]["type"] == "derivation"
    assert run_los(mini_repo, "validate").returncode == 0


def test_note_evidence_direct_cli_write_is_refused(mini_repo):
    proc = run_los(
        mini_repo,
        "note-evidence",
        "note-demo",
        "derivation",
        DERIVATION,
    )
    assert proc.returncode == 2
    assert "GatewayEnvelopeV2" in proc.stderr
    assert "evidence" not in _meta(mini_repo)
