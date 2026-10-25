"""C1-C finding: note.revise voids the dedicated capabilities' guarantees.

``note.revise`` guards only id, type and role. Two handler-owned facts that
the dedicated capabilities promise to preserve survive the revision untouched
while the bytes they describe are replaced:

1. A question note's ``atlas_question.target`` — atlas.question.save refuses
   retargeting with "the original question target is preserved"
   (capabilities.yaml, atlas.question.save invariants).
2. A reference note's ``material_analysis`` binding — note.schema.json says
   ``frozen_input_bytes`` is "the note body is exactly the file's last N
   bytes" and ``frozen_input_sha256`` "the sha256 of the frozen input bytes
   this note body preserves".

These tests state the system-level post-condition (the command is refused, or
the stored fact still describes the stored bytes) so either fix shape —
refusing the revision, or refreshing the fact — satisfies them. On base main
both fail: the revision commits and the stored facts go stale.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from gateway_helpers import approved_v2_call, file_sha256

from learning_os.store.loader import parse_frontmatter

QUESTION_ID = "note-question-demo"
ANALYSIS_ID = "note-analysis-demo"


def _write(path: Path, text: str) -> str:
    path.write_text(text, encoding="utf-8")
    return str(path)


def _split(raw: bytes) -> tuple[dict, bytes, bytes]:
    """(parsed frontmatter, whole raw bytes, body after the fence)."""
    text = raw.decode("utf-8")
    meta, body = parse_frontmatter(text, Path("x"))
    return meta, raw, body.encode("utf-8")


def _binding_describes_body(raw: bytes) -> bool:
    """note.schema.json's material_analysis claim about the live bytes."""
    meta, raw, _body = _split(raw)
    binding = meta.get("material_analysis")
    if not isinstance(binding, dict):
        return True
    n = binding.get("frozen_input_bytes")
    if not isinstance(n, int):
        return True
    tail = raw[-n:]
    digest = "sha256:" + hashlib.sha256(tail).hexdigest()
    return digest == binding.get("frozen_input_sha256")


def test_revise_cannot_retarget_a_question_target(mini_repo: Path):
    proc = approved_v2_call(
        mini_repo,
        capability="atlas.question.save",
        payload={
            "question": {
                "id": QUESTION_ID,
                "title": "Where does variance live?",
                "text": "Is variance the second central moment, and why?",
                "target": {"concepts": ["concept-variance"]},
            },
        },
        artifact_ids=[QUESTION_ID],
        idempotency_key="c1c-question-create-001",
    )
    assert proc.returncode == 0, proc.stderr
    question_path = mini_repo / "knowledge" / "notes" / "questions" / f"{QUESTION_ID}.md"
    meta_before, raw_before, _ = _split(question_path.read_bytes())
    target_before = meta_before["atlas_question"]["target"]

    replacement = mini_repo / "work" / "c1c-question-replacement.md"
    meta = dict(meta_before)
    meta["atlas_question"] = {
        **meta_before["atlas_question"],
        "target": {"concepts": ["concept-expected-value", "concept-variance"]},
    }
    import yaml

    front = "---\n" + yaml.safe_dump(
        meta, sort_keys=False, allow_unicode=True).rstrip() + "\n---\n\n"
    _write(replacement, front + "Revised question wording.\n")

    proc = approved_v2_call(
        mini_repo,
        capability="note.revise",
        payload={
            "note_id": QUESTION_ID,
            "file": str(replacement),
            "file_sha256": file_sha256(replacement),
        },
        artifact_ids=[QUESTION_ID],
        idempotency_key="c1c-question-retarget-001",
    )
    # The original target is preserved (capabilities.yaml, atlas.question.save):
    # either the revision is refused, or the stored target is unchanged.
    meta_after, _, _ = _split(question_path.read_bytes())
    assert proc.returncode != 0 or \
        meta_after["atlas_question"]["target"] == target_before, (
        "note.revise rewrote a question's atlas_question.target: "
        f"{json.dumps(meta_after['atlas_question']['target'])}"
    )


def test_revise_leaves_a_reference_binding_describing_its_body(mini_repo: Path):
    body_a = b"Original frozen analysis prose.\n"
    import hashlib as _h

    binding = {
        "resolution": "unresolved",
        "material": "demo/book.pdf",
        "recorded_source_digest": "a" * 64,
        "inspected_range": {"start": 1, "end": 3},
        "frozen_input_sha256": _h.sha256(body_a).hexdigest(),
        "frozen_input_bytes": len(body_a),
    }
    body_file = mini_repo / "work" / "c1c-analysis-body.bin"
    body_file.parent.mkdir(parents=True, exist_ok=True)
    body_file.write_bytes(body_a)
    proc = approved_v2_call(
        mini_repo,
        capability="note.analysis.save",
        payload={
            "analysis": {
                "id": ANALYSIS_ID,
                "title": "Demo analysis",
                "path": f"knowledge/notes/mathematics/{ANALYSIS_ID}.md",
                "binding": binding,
            },
            "body_file": str(body_file),
            "body_file_sha256": "sha256:" + _h.sha256(body_a).hexdigest(),
        },
        artifact_ids=[ANALYSIS_ID],
        idempotency_key="c1c-analysis-create-001",
    )
    assert proc.returncode == 0, proc.stderr
    note_path = mini_repo / "knowledge" / "notes" / "mathematics" / f"{ANALYSIS_ID}.md"
    assert _binding_describes_body(note_path.read_bytes())

    _, raw_before, _ = _split(note_path.read_bytes())
    text_before = raw_before.decode("utf-8")
    front_end = text_before.index("\n---\n", 4) + len("\n---\n")
    replacement = mini_repo / "work" / "c1c-analysis-replacement.md"
    _write(replacement, text_before[:front_end] + "\nReplacement prose that is not the frozen analysis.\n")

    proc = approved_v2_call(
        mini_repo,
        capability="note.revise",
        payload={
            "note_id": ANALYSIS_ID,
            "file": str(replacement),
            "file_sha256": file_sha256(replacement),
        },
        artifact_ids=[ANALYSIS_ID],
        idempotency_key="c1c-analysis-revise-001",
    )
    # The binding must still describe the stored body (note.schema.json
    # material_analysis.frozen_input_bytes): either the revision is refused,
    # or the handler re-binds it to the replacement bytes.
    raw_after = note_path.read_bytes()
    assert proc.returncode != 0 or _binding_describes_body(raw_after), (
        "note.revise replaced a reference note's body and left "
        "material_analysis claiming bytes it no longer preserves"
    )
