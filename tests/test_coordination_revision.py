"""Reviewed coordination edits preserve adjacent content and fail closed."""

from __future__ import annotations

import hashlib
import json

import pytest
import yaml
from gateway_helpers import approved_v2_envelope, file_sha256, run_v2_capability
from repo_builders import run_los

from learning_os.render import parse_sections

PATH = "work/COORDINATION.md"
TEXT = "AMLS is deferred to the next course run. See the owning module record."


def _envelope(root, *, text=TEXT, key="coordination-repair"):
    return approved_v2_envelope(
        root, capability="coordination.section.revise",
        payload={"section": "Deferrals", "text": text,
                 "expected_content_sha256": file_sha256(root / PATH)},
        artifact_ids=["coordination"], idempotency_key=key)


def test_check_is_read_only_and_apply_records_one_receipt(mini_repo):
    path = mini_repo / PATH
    before = path.read_bytes()
    check = run_los(mini_repo, "coordination-section-revise", "Deferrals",
                    "--text", TEXT, "--expected-content-sha256", file_sha256(path), "--check")
    assert check.returncode == 0, check.stderr
    preview = json.loads(check.stdout)
    assert preview["after"] == TEXT
    assert "Demo module deferred" in preview["before"]
    assert preview["expected_snapshot"].startswith("sha256:")
    assert preview["expected_revisions"] == {"coordination": 0}
    assert path.read_bytes() == before
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))

    envelope = _envelope(mini_repo)
    result = run_v2_capability(mini_repo, envelope)
    assert result.returncode == 0, result.stdout + result.stderr
    response = json.loads(result.stdout)
    after = path.read_text()
    preamble_before, sections_before = parse_sections(before.decode())
    preamble_after, sections_after = parse_sections(after)
    assert preamble_before == preamble_after
    assert {s.heading: "\n".join(s.lines).strip() for s in sections_before if s.heading != "Deferrals"} == {
        s.heading: "\n".join(s.lines).strip() for s in sections_after if s.heading != "Deferrals"}
    assert "\n".join(sections_after[-1].lines).strip() == TEXT
    receipt = yaml.safe_load((mini_repo / response["receipt_path"]).read_text())
    assert {row["path"] for row in receipt["writes"]} == {PATH}
    assert receipt["request"]["request_id"] == envelope["request_id"]
    projected = json.loads((mini_repo / "generated/manifest.json").read_text())
    record = next(row for row in projected["records"] if row["id"] == "coordination")
    assert TEXT in json.dumps(record)
    replay = run_v2_capability(mini_repo, envelope)
    assert replay.returncode == 0, replay.stdout + replay.stderr
    assert json.loads(replay.stdout)["replayed"] is True
    assert path.read_text() == after


def test_bare_application_refuses(mini_repo):
    path = mini_repo / PATH
    before = path.read_bytes()
    result = run_los(mini_repo, "coordination-section-revise", "Deferrals", "--text", TEXT,
                    "--expected-content-sha256", file_sha256(path))
    assert result.returncode == 2
    assert "GatewayEnvelopeV2" in result.stderr
    assert path.read_bytes() == before


@pytest.mark.parametrize("text", ["  ", "## Priorities\nReplace an adjacent section."])
def test_invalid_replacement_refuses_without_mutation(mini_repo, text):
    path = mini_repo / PATH
    before = path.read_bytes()
    result = run_v2_capability(mini_repo, _envelope(mini_repo, text=text))
    assert result.returncode != 0
    assert path.read_bytes() == before


def test_content_guard_refuses_even_with_fresh_snapshot(mini_repo):
    envelope = _envelope(mini_repo)
    path = mini_repo / PATH
    path.write_text(path.read_text() + "\nUnreviewed adjacent wording.\n")
    stale_hash = envelope["payload"]["expected_content_sha256"]
    fresh_envelope = _envelope(mini_repo)
    fresh_envelope["payload"]["expected_content_sha256"] = stale_hash
    from learning_os.contracts.gateway import intent_sha256

    fresh_envelope["approval"]["subject_sha256"] = intent_sha256(fresh_envelope)
    before = path.read_bytes()
    refused = run_v2_capability(mini_repo, fresh_envelope)
    assert refused.returncode == 3
    assert "changed before use" in refused.stdout
    assert stale_hash in refused.stdout
    assert path.read_bytes() == before


def test_fenced_headings_are_preserved_but_duplicate_targets_refuse(mini_repo):
    text = "A reviewed explanation.\n\n```md\n## Priorities\nquoted example\n```"
    applied = run_v2_capability(mini_repo, _envelope(mini_repo, text=text))
    assert applied.returncode == 0, applied.stdout + applied.stderr
    assert text in (mini_repo / PATH).read_text()
    path = mini_repo / PATH
    path.write_text(path.read_text() + "\n## Deferrals\nAmbiguous target.\n")
    before = path.read_bytes()
    refused = run_v2_capability(mini_repo, _envelope(mini_repo, key="ambiguous-coordination"))
    assert refused.returncode != 0
    assert path.read_bytes() == before


@pytest.mark.parametrize("guard", ["expected_snapshot", "expected_revisions"])
def test_stale_gateway_guards_refuse(mini_repo, guard):
    from learning_os.contracts.gateway import intent_sha256

    envelope = _envelope(mini_repo)
    if guard == "expected_snapshot":
        envelope[guard] = "sha256:" + "0" * 64
    else:
        envelope[guard] = {"coordination": 99}
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    path = mini_repo / PATH
    before = path.read_bytes()
    refused = run_v2_capability(mini_repo, envelope)
    assert refused.returncode != 0
    assert path.read_bytes() == before


# ------------------------------------------------- digest discovery (#102)


def _section_digest(text):
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_inspect_coordination_exposes_file_and_section_digests(mini_repo):
    path = mini_repo / PATH
    found = run_los(mini_repo, "inspect", "coordination")
    assert found.returncode == 0, found.stderr
    payload = json.loads(found.stdout)
    assert payload["content_sha256"] == file_sha256(path)
    assert set(payload["section_sha256"]) == {
        "Commitments", "Priorities", "Dependencies", "Deferrals"}
    for heading, body in payload["sections"].items():
        assert payload["section_sha256"][heading] == _section_digest(body)


def test_batch_inspect_includes_coordination_digests(mini_repo):
    from repo_builders import add_curriculum

    add_curriculum(mini_repo)
    found = run_los(mini_repo, "inspect", "coordination", "module-demo")
    assert found.returncode == 0, found.stderr
    records = json.loads(found.stdout)["records"]
    assert [record["id"] for record in records] == ["coordination", "module-demo"]
    assert records[0]["content_sha256"] == file_sha256(mini_repo / PATH)
    assert set(records[0]["section_sha256"]) == set(records[0]["sections"])


def test_check_without_digest_shows_diff_and_current_digest(mini_repo):
    path = mini_repo / PATH
    before = path.read_bytes()
    check = run_los(mini_repo, "coordination-section-revise", "Priorities",
                    "--text", TEXT, "--check")
    assert check.returncode == 0, check.stderr
    preview = json.loads(check.stdout)
    assert preview["after"] == TEXT
    assert preview["before"] != TEXT
    assert preview["expected_content_sha256"] == file_sha256(path)
    assert preview["expected_snapshot"].startswith("sha256:")
    assert preview["expected_revisions"] == {"coordination": 0}
    assert path.read_bytes() == before
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))


def test_revise_help_names_the_digest_source(mini_repo):
    shown = run_los(mini_repo, "coordination-section-revise", "--help")
    assert shown.returncode == 0, shown.stderr
    text = " ".join(shown.stdout.split())
    assert "inspect coordination" in text
    assert "content_sha256" in text


def test_apply_without_digest_refuses_naming_the_real_one(mini_repo):
    path = mini_repo / PATH
    before = path.read_bytes()
    refused = run_los(mini_repo, "coordination-section-revise", "Priorities",
                      "--text", TEXT)
    assert refused.returncode == 2
    assert file_sha256(path) in refused.stderr
    assert "inspect coordination" in refused.stderr
    assert path.read_bytes() == before


@pytest.mark.parametrize("digest", ["sha256:" + "0" * 64, "bogus", "sha256:xyz"])
def test_placeholder_and_malformed_digests_are_usage_errors(mini_repo, digest):
    path = mini_repo / PATH
    real = file_sha256(path)
    before = path.read_bytes()
    for extra in ([], ["--check"]):
        refused = run_los(mini_repo, "coordination-section-revise", "Priorities",
                          "--text", TEXT, "--expected-content-sha256", digest, *extra)
        assert refused.returncode == 2, (digest, extra)
        assert real in refused.stderr, (digest, extra)
        assert digest in refused.stderr, (digest, extra)
    assert path.read_bytes() == before


def test_stale_digest_refuses_with_exit_3_naming_both(mini_repo):
    path = mini_repo / PATH
    real = file_sha256(path)
    stale = real[:-1] + ("0" if real[-1] != "0" else "1")
    assert stale != real and stale != "sha256:" + "0" * 64
    before = path.read_bytes()
    refused = run_los(mini_repo, "coordination-section-revise", "Priorities",
                      "--text", TEXT, "--expected-content-sha256", stale)
    assert refused.returncode == 3
    assert "changed before use" in refused.stderr
    assert stale in refused.stderr and real in refused.stderr
    assert path.read_bytes() == before


def test_section_9_flow_works_end_to_end_using_only_product_reads(mini_repo):
    """inspect -> digest-free check -> apply with the read digest."""
    path = mini_repo / PATH
    found = run_los(mini_repo, "inspect", "coordination")
    assert found.returncode == 0, found.stderr
    digest = json.loads(found.stdout)["content_sha256"]

    check = run_los(mini_repo, "coordination-section-revise", "Priorities",
                    "--text", TEXT, "--check")
    assert check.returncode == 0, check.stderr
    preview = json.loads(check.stdout)
    assert preview["expected_content_sha256"] == digest

    applied = run_los(mini_repo, "coordination-section-revise", "Priorities",
                      "--text", TEXT, "--expected-content-sha256", digest,
                      "--expected-snapshot", preview["expected_snapshot"])
    # The bare named command never writes: the envelope carries the approval.
    assert applied.returncode == 2
    assert "GatewayEnvelopeV2" in applied.stderr

    envelope = approved_v2_envelope(
        mini_repo, capability="coordination.section.revise",
        payload={"section": "Priorities", "text": TEXT,
                 "expected_content_sha256": digest},
        artifact_ids=["coordination"], idempotency_key="section-9-flow")
    result = run_v2_capability(mini_repo, envelope)
    assert result.returncode == 0, result.stdout + result.stderr
    assert TEXT in path.read_text()
