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

import os
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
    import json

    recorded = json.loads(recording_path.read_text(encoding="utf-8"))
    diff = scenario_harness.compare(recorded, actual)
    assert diff is None, (
        f"behaviour changed for {operation}/{case['id']}:\n{diff}")
