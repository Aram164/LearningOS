"""Practice extraction, verification gesture and bounded read (P6).

Synthetic notes in the four exercised dialects, one real PDF page, and the
actual GatewayEnvelopeV2 transaction — never learner records.
"""
import hashlib
import json

import yaml
from gateway_helpers import (
    approved_v2_call,
    approved_v2_envelope,
    run_v2_capability,
)
from repo_builders import run_los

BANK_SOLUTION = """\
**A1. What is 2+2?**
<details>
<summary>Solution</summary>
4
</details>

**A2. What is 3+3?**
<details>
<summary>Solution</summary>
6
</details>
"""

BANK_ANSWER = """\
**B1. Capital of France?**
<details>
<summary>Answer</summary>
Paris
</details>
"""

MOCK = """\
## Questions

**A1. First mock question?**

**A2. Second mock question?**

# ANSWER KEY

**A1. First keyed answer**

**A2. Second keyed answer**
"""

EXAM = """\
## Timed round

### Q1. Timed question one?

## Optional examiner follow-ups

1. **Follow-up question one?**

## Solutions and marking guide

### Q1. solution

Timed answer one.

## Follow-up solution sketches

1. Follow-up sketch one.
"""

QUOTE = "The official answer is four."


def _pdf_bytes(text: str) -> bytes:
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n"
        + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objects, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_at = len(out)
    out += b"xref\n0 6\n0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += b"trailer\n<< /Size 6 /Root 1 0 R >>\n"
    out += f"startxref\n{xref_at}\n%%EOF\n".encode()
    return bytes(out)


def _note(root, note_id, role, body):
    path = root / "knowledge" / "notes" / "mathematics" / f"{note_id}.md"
    lines = [
        "---",
        f"id: {note_id}",
        "type: note",
        f"title: {note_id}",
        "created: 2026-07-16",
        f"role: {role}",
        "concepts: [concept-expected-value]",
        "sources: [source-demo-book]",
        "---",
        "",
    ]
    path.write_text("\n".join(lines) + "\n" + body, encoding="utf-8")
    return path


def _record(root, record, key):
    return approved_v2_call(
        root, capability="practice.verification.record",
        payload={"record": record},
        artifact_ids=["registry-practice-index", record["item_id"].split("#")[0]],
        idempotency_key=key)


def _binding(root):
    pdf = _pdf_bytes(QUOTE)
    materials = root.parent / "materials"
    (materials / "book.pdf").write_bytes(pdf)
    return {
        "source_id": "source-demo-book",
        "material_relpath": "book.pdf",
        "file_sha256": hashlib.sha256(pdf).hexdigest(),
        "page": 1,
        "quote": QUOTE,
    }


def _base_record(binding=None, **overrides):
    record = {
        "item_id": "note-practice-bank#A1",
        "expected_old": None,
        "new_status": "source-matched",
        "method": "official-source",
        "concept_ids": ["concept-expected-value"],
        "artifact_sha256": "c" * 64,
        "reviewer_id": "aram",
        "source_binding": binding,
        "comparison_sha256": None,
    }
    record.update(overrides)
    return record


def test_four_dialects_extract_deterministically(mini_repo):
    from learning_os.derive.projection.practice_items import extract_items

    cases = [
        ("note-a", "exercise-bank", BANK_SOLUTION, ["note-a#A1", "note-a#A2"]),
        ("note-b", "exercise-bank", BANK_ANSWER, ["note-b#B1"]),
        ("note-c", "mock-exam", MOCK, ["note-c#A1", "note-c#A2"]),
        ("note-d", "mock-exam", EXAM, ["note-d#F1", "note-d#Q1"]),
    ]
    for note_id, role, body, ids in cases:
        result = extract_items(note_id, role, body)
        assert not result.diagnostics, (note_id, result.diagnostics)
        assert [item.item_id for item in result.items] == ids
    other = extract_items("note-a", "synthesis", BANK_SOLUTION)
    assert other.items == [] and other.diagnostics == []


def test_duplicate_orphan_and_unsupported_stay_ineligible(mini_repo):
    from learning_os.derive.projection.practice_items import extract_items

    dup = extract_items("note-a", "exercise-bank",
                        BANK_SOLUTION + "\n**A1. Again?**\n<details>\n"
                        "<summary>Solution</summary>\n4\n</details>\n")
    assert any(d.reason == "duplicate label" for d in dup.diagnostics)
    orphan = extract_items("note-c", "mock-exam",
                           MOCK.replace("**A2. Second keyed answer**",
                                        "**A3. Orphaned answer**"))
    assert any(d.reason == "orphan answer with no question"
               for d in orphan.diagnostics)
    bad = extract_items("note-a", "exercise-bank", "Just prose, no items.")
    assert bad.diagnostics[0].reason == "unsupported markup"
    opened = extract_items("note-a", "exercise-bank",
                           "**C1. [open] Not finished yet**\n")
    assert opened.items == [] and opened.diagnostics == []


def test_source_matched_record_and_context_round_trip(mini_repo):
    _note(mini_repo, "note-practice-bank", "exercise-bank", BANK_SOLUTION)
    binding = _binding(mini_repo)
    envelope = approved_v2_envelope(
        mini_repo, capability="practice.verification.record",
        payload={"record": _base_record(binding)},
        artifact_ids=["registry-practice-index", "note-practice-bank"],
        idempotency_key="record-a1")
    result = run_v2_capability(mini_repo, envelope)
    assert result.returncode == 0, result.stdout + result.stderr

    sidecar = yaml.safe_load(
        (mini_repo / "knowledge/practice-index.yaml").read_text())
    [row] = sidecar["items"]
    assert row["status"] == "source-matched"
    assert row["source_bindings"] == [binding]
    assert row["verifications"][0]["method"] == "official-source"

    out = run_los(mini_repo, "practice-context", "note-practice-bank")
    assert out.returncode == 0, out.stdout + out.stderr
    data = json.loads(out.stdout)
    first = data["items"][0]
    assert first["status"] == "source-matched" and first["checked"] is True
    assert "solution" not in first and "4" != first.get("solution")

    # Replaying the same envelope writes nothing twice (idempotent gateway).
    again = run_v2_capability(mini_repo, envelope)
    assert again.returncode == 0, again.stdout + again.stderr
    assert json.loads(again.stdout)["replayed"] is True
    sidecar = yaml.safe_load(
        (mini_repo / "knowledge/practice-index.yaml").read_text())
    assert len(sidecar["items"][0]["verifications"]) == 1


def test_stale_row_unknown_concept_and_method_mismatch_refuse(mini_repo):
    _note(mini_repo, "note-practice-bank", "exercise-bank", BANK_SOLUTION)
    binding = _binding(mini_repo)
    ok = _record(mini_repo, _base_record(binding), "record-first")
    assert ok.returncode == 0, ok.stdout + ok.stderr
    stale = _record(mini_repo, _base_record(binding), "record-stale")
    assert stale.returncode != 0
    unknown = _record(mini_repo, _base_record(
        binding, item_id="note-practice-bank#A2",
        expected_old=None, concept_ids=["concept-missing"]), "record-unknown")
    assert unknown.returncode != 0
    mismatch = _record(mini_repo, _base_record(
        binding, item_id="note-practice-bank#A2",
        expected_old=None, method="explicit-review"), "record-mismatch")
    assert mismatch.returncode != 0


def test_changed_answer_unverifies_and_quote_is_checked(mini_repo):
    path = _note(mini_repo, "note-practice-bank", "exercise-bank", BANK_SOLUTION)
    binding = _binding(mini_repo)
    assert _record(mini_repo, _base_record(binding), "record-quote").returncode == 0
    # A quote that is not on the pinned page refuses before any write.
    bad = dict(binding, quote="This sentence is not in the book.")
    refused = _record(mini_repo, _base_record(
        bad, item_id="note-practice-bank#A2", expected_old=None), "record-bad-quote")
    assert refused.returncode != 0
    # Editing the canonical answer makes the stored row stale on read.
    path.write_text(path.read_text().replace("\n4\n", "\nFour\n"), encoding="utf-8")
    out = run_los(mini_repo, "practice-context", "note-practice-bank")
    data = json.loads(out.stdout)
    first = data["items"][0]
    assert first["status"] == "unverified" and first["checked"] is False
    assert "content changed" in " ".join(first["ineligibility"])


def test_no_direct_cli_bypass(mini_repo):
    _note(mini_repo, "note-practice-bank", "exercise-bank", BANK_SOLUTION)
    result = run_los(
        mini_repo, "practice-verification-record", "--record",
        json.dumps(_base_record(_binding(mini_repo))))
    assert result.returncode != 0
    assert not (mini_repo / "knowledge/practice-index.yaml").exists()
