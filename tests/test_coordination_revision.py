"""Reviewed coordination edits preserve adjacent content and fail closed."""

from __future__ import annotations

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
    assert refused.returncode != 0
    assert "changed before use" in refused.stdout
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
