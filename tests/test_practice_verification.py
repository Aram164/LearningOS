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

from learning_os.store.contracts.gateway import intent_sha256

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
    path = materials / "source-demo-book" / "book.pdf"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pdf)
    return {
        "source_id": "source-demo-book",
        "material_relpath": "source-demo-book/book.pdf",
        "file_sha256": hashlib.sha256(pdf).hexdigest(),
        "page": 1,
        "quote": QUOTE,
    }


def _reviewed_digest(item_id, body=BANK_SOLUTION):
    """The content hash practice.context shows for the item under review."""
    from learning_os.domain.practice import content_sha256, extract_items

    note_id = item_id.split("#")[0]
    [item] = [i for i in extract_items(note_id, "exercise-bank", body).items
              if i.item_id == item_id]
    return content_sha256(item.item_id, item.prompt, item.solution)


def _base_record(binding=None, **overrides):
    record = {
        "item_id": "note-practice-bank#A1",
        "expected_old": None,
        "new_status": "source-matched",
        "method": "official-source",
        "concept_ids": ["concept-expected-value"],
        "artifact_sha256": None,
        "reviewer_id": "aram",
        "source_binding": binding,
        "comparison_sha256": None,
    }
    record.update(overrides)
    if record["artifact_sha256"] is None:
        record["artifact_sha256"] = _reviewed_digest(record["item_id"])
    return record


def test_four_dialects_extract_deterministically(mini_repo):
    from learning_os.domain.practice import extract_items

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
    from learning_os.domain.practice import extract_items

    dup = extract_items("note-a", "exercise-bank",
                        BANK_SOLUTION + "\n**A1. Again?**\n<details>\n"
                        "<summary>Solution</summary>\n4\n</details>\n")
    assert any(d.reason == "duplicate label" for d in dup.diagnostics)
    orphan = extract_items("note-c", "mock-exam",
                           MOCK.replace("**A2. Second keyed answer**",
                                        "**A3. Orphaned answer**"))
    repeated_key = extract_items("note-c", "mock-exam", MOCK + "\n**A1. Duplicated key**")
    assert any(d.reason == "duplicate label" for d in repeated_key.diagnostics)
    incomplete_exam = extract_items("note-d", "mock-exam",
                                    EXAM.replace("## Follow-up solution sketches", "## Other"))
    assert incomplete_exam.diagnostics[0].reason == "incomplete optional exam sections"
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
    envelope["approval"]["kind"] = "direct-user-gesture"
    envelope["channel"] = "codex"
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    machine = run_v2_capability(mini_repo, envelope)
    assert machine.returncode == 2 and json.loads(machine.stdout)["error"]["code"] == "UNCONFIRMED"
    assert not (mini_repo / "knowledge/practice-index.yaml").exists()

    envelope["channel"] = "ui"
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
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


def test_reviewed_digest_must_match_the_current_item(mini_repo):
    """The proof binds what was reviewed; a person never types a digest."""
    _note(mini_repo, "note-practice-bank", "exercise-bank", BANK_SOLUTION)
    binding = _binding(mini_repo)
    wrong = _record(mini_repo, _base_record(binding, artifact_sha256="c" * 64), "record-wrong")
    assert wrong.returncode != 0
    assert "reviewed item content differs" in wrong.stdout + wrong.stderr
    assert not (mini_repo / "knowledge/practice-index.yaml").exists()
    # A hand-edited sidecar whose proof names other content reads unverified.
    assert _record(mini_repo, _base_record(binding), "record-right").returncode == 0
    path = mini_repo / "knowledge/practice-index.yaml"
    data = yaml.safe_load(path.read_text())
    data["items"][0]["verifications"][0]["artifact_sha256"] = "d" * 64
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    first = json.loads(run_los(mini_repo, "practice-context", "note-practice-bank").stdout)["items"][0]
    assert first["checked"] is False
    assert "different item content" in " ".join(first["ineligibility"])


def test_core_pins_the_pdf_digest_when_the_binding_omits_it(mini_repo):
    _note(mini_repo, "note-practice-bank", "exercise-bank", BANK_SOLUTION)
    binding = _binding(mini_repo)
    typed = {key: value for key, value in binding.items() if key != "file_sha256"}
    result = _record(mini_repo, _base_record(typed), "record-no-digest")
    assert result.returncode == 0, result.stdout + result.stderr
    [row] = yaml.safe_load((mini_repo / "knowledge/practice-index.yaml").read_text())["items"]
    assert row["source_bindings"] == [binding]
    assert list(row["source_bindings"][0]) == list(binding)


def test_one_problem_item_does_not_block_its_siblings(mini_repo):
    """Gated per item: 27 of 57 real banks carry at least one diagnostic."""
    body = BANK_SOLUTION + "\n**A3. Unanswered and not marked open**\n"
    _note(mini_repo, "note-practice-bank", "exercise-bank", body)
    binding = _binding(mini_repo)
    ok = _record(mini_repo, _base_record(binding), "record-sibling")
    assert ok.returncode == 0, ok.stdout + ok.stderr
    blocked = _record(mini_repo, _base_record(
        binding, item_id="note-practice-bank#A3", artifact_sha256="c" * 64),
        "record-problem")
    assert blocked.returncode != 0
    assert "A3 is ambiguous or unsupported" in blocked.stdout + blocked.stderr
    data = json.loads(run_los(mini_repo, "practice-context", "note-practice-bank").stdout)
    assert [item["item_id"] for item in data["items"]] == [
        "note-practice-bank#A1", "note-practice-bank#A2"]
    assert data["items"][0]["checked"] is True
    assert any("A3" in line for line in data["diagnostics"])

    from learning_os.store.loading import load_repo
    from learning_os.store.practice import checked_practice_by_note

    checked = checked_practice_by_note(load_repo(mini_repo))
    assert [e.item.item_id for e in checked["note-practice-bank"]] == ["note-practice-bank#A1"]


def test_cross_checked_and_unquoted_source_matched_are_refused(mini_repo):
    """Review 2026-11-23 P2: no self-attested comparison, no page-only proof."""
    _note(mini_repo, "note-practice-bank", "exercise-bank", BANK_SOLUTION)
    binding = _binding(mini_repo)
    crossed = _record(mini_repo, _base_record(
        None, new_status="cross-checked", method="independent-solve",
        comparison_sha256="e" * 64), "record-cross-checked")
    assert crossed.returncode != 0
    assert "cross-checked cannot be recorded" in crossed.stdout + crossed.stderr
    unquoted = {key: value for key, value in binding.items() if key != "quote"}
    paged = _record(mini_repo, _base_record(unquoted), "record-page-only")
    assert paged.returncode != 0
    assert "needs an excerpt of the official answer" in paged.stdout + paged.stderr
    assert not (mini_repo / "knowledge/practice-index.yaml").exists()

    # Rows written before these rules read unverified, never checked.
    assert _record(mini_repo, _base_record(binding), "record-quoted").returncode == 0
    path = mini_repo / "knowledge/practice-index.yaml"
    data = yaml.safe_load(path.read_text())
    row = data["items"][0]
    del row["verifications"][0]["source_binding"]["quote"]
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    first = json.loads(run_los(mini_repo, "practice-context", "note-practice-bank").stdout)["items"][0]
    assert first["checked"] is False and "no excerpt" in " ".join(first["ineligibility"])
    row["status"] = "cross-checked"
    row["verifications"].append({**row["verifications"][0], "method": "independent-solve",
                                 "source_binding": None, "comparison_sha256": "e" * 64})
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    first = json.loads(run_los(mini_repo, "practice-context", "note-practice-bank").stdout)["items"][0]
    assert first["checked"] is False
    assert "no stored independent comparison" in " ".join(first["ineligibility"])


def test_a_fabricated_stored_excerpt_reads_unverified(mini_repo):
    """Second review, 2026-11-23: read-back re-verifies the excerpt on the page."""
    _note(mini_repo, "note-practice-bank", "exercise-bank", BANK_SOLUTION)
    binding = _binding(mini_repo)
    assert _record(mini_repo, _base_record(binding), "record-before-edit").returncode == 0
    path = mini_repo / "knowledge/practice-index.yaml"
    data = yaml.safe_load(path.read_text())
    row = data["items"][0]
    fabricated = "This sentence was never printed in the book."
    row["source_bindings"][0]["quote"] = fabricated
    row["verifications"][0]["source_binding"]["quote"] = fabricated
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    first = json.loads(run_los(mini_repo, "practice-context", "note-practice-bank").stdout)["items"][0]
    assert first["checked"] is False and first["status"] == "unverified"
    assert "does not appear verbatim" in " ".join(first["ineligibility"])


def test_bindings_resolve_through_the_flat_alias_tree(mini_repo, tmp_path):
    """Live layout: materials/.flat/<source> is a symlink into the topic tree.

    Requiring the resolved file to stay under .flat refused every real
    material; Core's rule is that every hop stays inside materials/.
    """
    import os
    import shutil

    _note(mini_repo, "note-practice-bank", "exercise-bank", BANK_SOLUTION)
    binding = _binding(mini_repo)
    materials = mini_repo.parent / "materials"
    topic = materials / "mathematics" / "demo-book"
    topic.parent.mkdir(parents=True)
    shutil.move(str(materials / "source-demo-book"), str(topic))
    (materials / ".flat").mkdir()
    os.symlink("../mathematics/demo-book", materials / ".flat" / "source-demo-book")
    ok = _record(mini_repo, _base_record(binding), "record-through-flat")
    assert ok.returncode == 0, ok.stdout + ok.stderr
    first = json.loads(run_los(mini_repo, "practice-context", "note-practice-bank").stdout)["items"][0]
    assert first["checked"] is True, first["ineligibility"]

    # An alias that leaves materials/ is refused, on write and on read.
    outside = tmp_path / "elsewhere"
    shutil.copytree(topic, outside)
    (materials / ".flat" / "source-demo-book").unlink()
    os.symlink(str(outside), materials / ".flat" / "source-demo-book")
    first = json.loads(run_los(mini_repo, "practice-context", "note-practice-bank").stdout)["items"][0]
    assert first["checked"] is False
    escaped = _record(mini_repo, _base_record(
        binding, item_id="note-practice-bank#A2"), "record-escaping-alias")
    assert escaped.returncode != 0


def test_practice_context_omits_stored_quote_and_round_trips_expected_old(mini_repo, tmp_path):
    import shutil

    path = _note(mini_repo, "note-practice-bank", "exercise-bank", BANK_SOLUTION)
    binding = _binding(mini_repo)
    assert _record(mini_repo, _base_record(binding), "record-redact-init").returncode == 0
    raw_row = yaml.safe_load((mini_repo / "knowledge/practice-index.yaml").read_text())["items"][0]
    assert raw_row["source_bindings"][0]["quote"] == binding["quote"]

    ctx_out = run_los(
        mini_repo, "practice-context", "note-practice-bank",
        "--item-id", "note-practice-bank#A1")
    assert ctx_out.returncode == 0, ctx_out.stdout + ctx_out.stderr
    stored_row = json.loads(ctx_out.stdout)["items"][0]["stored_row"]
    assert stored_row is not None
    assert "quote" not in stored_row["source_bindings"][0]
    assert "quote" not in stored_row["verifications"][0]["source_binding"]

    path.write_text(path.read_text().replace("\n4\n", "\nFour\n"), encoding="utf-8")
    digest_after = _reviewed_digest("note-practice-bank#A1", path.read_text().split("\n---\n", 1)[1])

    # Clone identical starting state (including sibling materials/) so both accepted
    # forms of expected_old are proven against the exact same starting revision.
    clone_base = tmp_path / "same-start"
    shutil.copytree(mini_repo.parent, clone_base)
    clone_repo = clone_base / "repository"

    # A raw row with a different quote must still be rejected.
    wrong_quote_row = json.loads(json.dumps(raw_row))
    wrong_quote_row["source_bindings"][0]["quote"] = "tampered quote"
    wrong_quote = _record(
        mini_repo,
        _base_record(
            None, expected_old=wrong_quote_row, new_status="confirmed", method="explicit-review",
            artifact_sha256=digest_after),
        "record-wrong-quote-old",
    )
    assert wrong_quote.returncode != 0
    assert "expected old verification row no longer matches" in wrong_quote.stdout + wrong_quote.stderr

    # Accepted form 1: redacted stored_row from practice.context.
    redacted_ok = _record(
        mini_repo,
        _base_record(
            None, expected_old=stored_row, new_status="confirmed", method="explicit-review",
            artifact_sha256=digest_after),
        "record-redacted-old",
    )
    assert redacted_ok.returncode == 0, redacted_ok.stdout + redacted_ok.stderr

    # Accepted form 2: exact raw row straight from knowledge/practice-index.yaml.
    raw_ok = _record(
        clone_repo,
        _base_record(
            None, expected_old=raw_row, new_status="confirmed", method="explicit-review",
            artifact_sha256=digest_after),
        "record-raw-old",
    )
    assert raw_ok.returncode == 0, raw_ok.stdout + raw_ok.stderr


def test_unreadable_or_symlinked_sidecar_fails_cleanly(mini_repo, tmp_path):
    import os

    import pytest

    from learning_os.app.outcomes import classify, exit_for, refusal_from_failure
    from learning_os.derive.projection.atlas_boards import build_atlas_boards
    from learning_os.domain.failures import PracticeSidecarUnreadable, TransactionFailure
    from learning_os.store.loading import load_repo

    assert not issubclass(PracticeSidecarUnreadable, ValueError)
    assert not issubclass(PracticeSidecarUnreadable, TransactionFailure)
    assert classify(PracticeSidecarUnreadable("bad"), "cli") is not None
    assert exit_for(PracticeSidecarUnreadable("bad"), "cli") == 2
    assert refusal_from_failure(PracticeSidecarUnreadable("bad")) == ("VALIDATION_FAILED", False)

    _note(mini_repo, "note-practice-bank", "exercise-bank", BANK_SOLUTION)
    binding = _binding(mini_repo)
    assert _record(mini_repo, _base_record(binding), "record-before-corrupt").returncode == 0

    sidecar = mini_repo / "knowledge/practice-index.yaml"
    data = yaml.safe_load(sidecar.read_text(encoding="utf-8"))

    # Overlong quote violates maxLength schema: field & safe reason appear, secret excerpt never leaks.
    secret = "SECRET_EXCERPT_LEAK_GUARD_" + ("x" * 240)
    data["items"][0]["source_bindings"][0]["quote"] = secret
    data["items"][0]["verifications"][0]["source_binding"]["quote"] = secret
    sidecar.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    cli_res = run_los(mini_repo, "practice-context", "note-practice-bank")
    assert cli_res.returncode == 2
    assert "VALIDATION_FAILED" in cli_res.stderr
    assert "items.0.source_bindings.0.quote" in cli_res.stderr
    assert "exceeds maximum length" in cli_res.stderr
    assert "SECRET_EXCERPT_LEAK_GUARD" not in cli_res.stdout + cli_res.stderr

    gw_res = _record(
        mini_repo,
        _base_record(None, new_status="confirmed", method="explicit-review",
                     item_id="note-practice-bank#A2"),
        "gw-corrupt-sidecar",
    )
    assert gw_res.returncode == 2
    gw_json = json.loads(gw_res.stdout)
    assert gw_json["error"]["code"] == "VALIDATION_FAILED"
    assert gw_json["error"]["retryable"] is False
    assert "items.0.source_bindings.0.quote" in gw_json["error"]["message"]
    assert "exceeds maximum length" in gw_json["error"]["message"]
    assert "SECRET_EXCERPT_LEAK_GUARD" not in gw_res.stdout + gw_res.stderr

    with pytest.raises(PracticeSidecarUnreadable) as exc_info:
        build_atlas_boards(load_repo(mini_repo), {})
    assert "SECRET_EXCERPT_LEAK_GUARD" not in str(exc_info.value)

    # Malformed YAML near an excerpt also fails via PracticeSidecarUnreadable cleanly.
    sidecar.write_text(f"items: [\n  quote: {secret}\n", encoding="utf-8")
    malformed = run_los(mini_repo, "practice-context", "note-practice-bank")
    assert malformed.returncode == 2
    assert "practice-index unreadable" in malformed.stderr
    assert "SECRET_EXCERPT_LEAK_GUARD" not in malformed.stdout + malformed.stderr

    sidecar.unlink()
    outside = tmp_path / "external-sidecar.yaml"
    outside.write_text("items: []\n", encoding="utf-8")
    os.symlink(str(outside), sidecar)
    sym = run_los(mini_repo, "practice-context", "note-practice-bank")
    assert sym.returncode == 2
    assert "practice-index cannot be a symlink" in sym.stderr


def test_verified_binding_handles_dotted_dir_and_mismatched_file(mini_repo):
    from learning_os.store.loading import load_repo
    from learning_os.store.practice import verified_binding

    pdf = _pdf_bytes(QUOTE)
    materials = mini_repo.parent / "materials"
    dotted_dir = materials / "source-demo-book.v2"
    dotted_dir.mkdir(parents=True, exist_ok=True)
    dotted_pdf = dotted_dir / "book.pdf"
    dotted_pdf.write_bytes(pdf)
    binding = {
        "source_id": "source-demo-book",
        "material_relpath": "source-demo-book.v2/book.pdf",
        "file_sha256": hashlib.sha256(pdf).hexdigest(),
        "page": 1,
        "quote": QUOTE,
    }
    sources_path = mini_repo / "sources/sources.yaml"
    sources_data = yaml.safe_load(sources_path.read_text(encoding="utf-8"))
    sources_data["sources"][0]["material"] = "material://source-demo-book.v2"
    sources_path.write_text(yaml.safe_dump(sources_data, sort_keys=False), encoding="utf-8")
    assert verified_binding(load_repo(mini_repo), binding) is None

    # A registered source directory literally named packet.pdf resolves as a directory,
    # so bindings like packet.pdf/chapter.pdf remain accepted.
    packet_dir = materials / "packet.pdf"
    packet_dir.mkdir(parents=True, exist_ok=True)
    (packet_dir / "chapter.pdf").write_bytes(pdf)
    packet_binding = {
        **binding,
        "material_relpath": "packet.pdf/chapter.pdf",
    }
    sources_data["sources"][0]["material"] = "material://packet.pdf"
    sources_path.write_text(yaml.safe_dump(sources_data, sort_keys=False), encoding="utf-8")
    assert verified_binding(load_repo(mini_repo), packet_binding) is None

    (dotted_dir / "other.pdf").write_bytes(pdf)
    sources_data["sources"][0]["material"] = "material://source-demo-book.v2/other.pdf"
    sources_path.write_text(yaml.safe_dump(sources_data, sort_keys=False), encoding="utf-8")
    assert verified_binding(load_repo(mini_repo), binding) == "binding PDF does not match the registered source file"
