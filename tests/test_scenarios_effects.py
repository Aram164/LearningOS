"""Effect scenarios: characterization recordings over a fresh world (SPEC §5).

Parametrized over every (case file, case) in ``tests/scenarios/cases/``.
Without ``LOS_RECORD_SCENARIOS=1`` each case compares against its recording
in ``tests/scenarios/recorded/<operation>/<case-id>.json``; with it, the
recording is written instead. A session may record only for the operations
its kickoff authorizes.

After each case, A2 runs in report mode: ``reconcile`` over the recording
prints violations without failing (the failing comes later, with a2-mode).
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import pytest
import scenario_harness

CASE_FILES = sorted(scenario_harness.CASES_DIR.glob("*.yaml")) \
    if scenario_harness.CASES_DIR.is_dir() else []


def _collect():
    params = []
    for path in CASE_FILES:
        file_data = scenario_harness.load_case_file(path)
        operation = file_data["operation"]
        for case in file_data.get("cases", []):
            merged = {"fixture": file_data.get("fixture", "rich_world"),
                      "observations": file_data["observations"],
                      "fixture_mtime": file_data.get(
                          "fixture_mtime",
                          scenario_harness.FIXTURE_MTIME_DEFAULT),
                      **case}
            params.append(pytest.param(
                operation, merged,
                id=f"{operation}::{case['id']}"))
    return params


@pytest.fixture(autouse=True)
def _berlin_time(monkeypatch):
    """Pin TZ=Europe/Berlin in-process, restoring afterwards (SPEC §0)."""
    old = os.environ.get("TZ")
    monkeypatch.setenv("TZ", "Europe/Berlin")
    if hasattr(time, "tzset"):
        time.tzset()
    yield
    if old is None:
        os.environ.pop("TZ", None)
    else:
        os.environ["TZ"] = old
    if hasattr(time, "tzset"):
        time.tzset()


@pytest.mark.parametrize("operation,case", _collect())
def test_scenario_effects(operation: str, case: dict, tmp_path: Path):
    workdir = tmp_path / "case"
    workdir.mkdir()
    if case.get("kind") == "sequence":
        actual = scenario_harness.run_sequence(case, operation, workdir)
    else:
        actual = scenario_harness.run_case(case, operation, workdir)
    for violation in scenario_harness.reconcile_recorded(actual):
        print(f"A2 report: {violation}")
    recording_path = (scenario_harness.RECORDED_DIR / operation
                      / f"{case['id']}.json")
    if os.environ.get("LOS_RECORD_SCENARIOS") == "1":
        recording_path.parent.mkdir(parents=True, exist_ok=True)
        recording_path.write_text(scenario_harness.pretty(actual),
                                  encoding="utf-8")
        print(f"recorded {operation}/{case['id']}")
        return
    assert recording_path.is_file(), (
        f"no recording for {operation}/{case['id']}: "
        f"{recording_path} — record it only when the kickoff authorizes it")
    recorded = json.loads(recording_path.read_text(encoding="utf-8"))
    diff = scenario_harness.compare(recorded, actual)
    assert diff is None, (
        f"behaviour changed for {operation}/{case['id']}:\n{diff}")


def _bare_recording(stdout_json: dict, **sections) -> dict:
    """A minimal recording shape for normalize() regression tests."""
    recording = {
        "exit": 0,
        "stdout": json.dumps(stdout_json),
        "stderr": "",
        "stdout_json": stdout_json,
        "receipts": [],
        "revisions_changed": {},
        "idempotency_changed": {},
        "session_ledger_changed": None,
    }
    recording.update(sections)
    return recording


def test_normalize_keeps_authored_text_values_distinct(tmp_path):
    """C2: authored text is never an identity, and compare() reports it."""
    first = scenario_harness.normalize(
        _bare_recording({"ok": True, "note": "scenario-original"}), tmp_path)
    second = scenario_harness.normalize(
        _bare_recording({"ok": True, "note": "scenario-corrupted"}), tmp_path)
    assert first != second
    assert "scenario-original" in json.dumps(first)
    assert "scenario-corrupted" in json.dumps(second)
    diff = scenario_harness.compare(first, second)
    assert diff is not None
    assert "scenario-original" in diff and "scenario-corrupted" in diff


def test_normalize_orders_a_ledger_only_snapshot(tmp_path):
    """C5: a snapshot seen only in a ledger normalizes, after text ones."""
    text_snap = "sha256:" + "ab" * 32
    ledger_snap = "sha256:" + "cd" * 32
    recording = _bare_recording(
        {"ok": True, "snapshot_after": text_snap},
        revisions_changed={"before": None,
                           "after": {"snapshot_after": ledger_snap}})
    normalized = scenario_harness.normalize(recording, tmp_path)
    assert normalized["stdout_json"]["snapshot_after"] == "SNAP1"
    assert (normalized["revisions_changed"]["after"]["snapshot_after"]
            == "SNAP2")


def test_normalize_replaces_learningos_container(tmp_path):
    """Amendment (y): a sibling path normalizes, ROOT/MATERIALS unchanged."""
    container = tmp_path / "LearningOS"
    root = container / "repository"
    sibling = str(container / "obsidian-ui" / "x")
    recording = _bare_recording(
        {"sibling": sibling},
        stdout=f"root {root} sibling {sibling}",
        stderr=f"materials {container / 'materials'} sibling {sibling}")
    normalized = scenario_harness.normalize(recording, root)
    assert normalized["stdout_json"]["sibling"] == "<LEARNINGOS>/obsidian-ui/x"
    assert normalized["stdout"] == (
        "root <ROOT> sibling <LEARNINGOS>/obsidian-ui/x")
    assert normalized["stderr"] == (
        "materials <MATERIALS> sibling <LEARNINGOS>/obsidian-ui/x")


def _subparser(command: str):
    sys.path.insert(0, str(scenario_harness.REPO_ROOT / "tools"))
    try:
        import los
        from learning_os.contracts.payloads import subparsers
    finally:
        del sys.path[0]
    return subparsers(los.build_parser())[command]


def test_request_rendering_round_trips():
    """C3: each field renders by its own argparse action and parses back."""
    root = scenario_harness.REPO_ROOT
    request = {"unit_id": "unit-demo-l01",
               "selected": ["stage-demo", "stage-demo-pending"],
               "approve": True}
    argv = scenario_harness.request_to_argv("review.apply", request, root)
    assert argv == ["unit-demo-l01", "--selected", "stage-demo",
                   "stage-demo-pending", "--approve"]
    parsed = _subparser("shelving-apply").parse_args(argv)
    assert parsed.unit_id == request["unit_id"]
    assert parsed.selected == request["selected"]
    assert parsed.approve is True
    request = {"claim_ids": ["claim-a", "claim-b"],
               "expected_revision": ["unit-demo-l01=3",
                                     "study-map-demo-l01=1"]}
    argv = scenario_harness.request_to_argv("lineage.restamp", request, root)
    assert argv == ["--claim-ids", "claim-a", "claim-b",
                   "--expected-revision", "unit-demo-l01=3",
                   "--expected-revision", "study-map-demo-l01=1"]
    parsed = _subparser("lineage-restamp").parse_args(argv)
    assert parsed.claim_ids == request["claim_ids"]
    assert parsed.expected_revision == request["expected_revision"]
    request = {"goal_id": ["lineage-stale:claim-1",
                           "evidence-superseded:obs-2"],
               "reject": True}
    argv = scenario_harness.request_to_argv("cli.goal", request, root)
    assert argv == ["lineage-stale:claim-1", "evidence-superseded:obs-2",
                   "--reject"]
    parsed = _subparser("goal").parse_args(argv)
    assert parsed.goal_id == request["goal_id"]
    assert parsed.reject is True
