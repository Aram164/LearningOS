"""Research track #2, Phase 4C gate: the 8 scenarios through the real UI.

The UI-driven harness walks the full client path (prepare → dispatch →
settle) for eight writes against a throwaway mini repository. This gate
then reads each scenario back through the `operations` command — the exact
payload Diagnostics renders — and requires it to identify the first causal
failure, the canonical outcome, and the required recovery action with no
raw log, receipt, or manifest inspection.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parent
REPO_ROOT = TESTS.parent
UI_ROOT = REPO_ROOT.parent / "obsidian-ui"
HARNESS = UI_ROOT / "tests" / "operations-gate-harness.js"
LOS = REPO_ROOT / "tools" / "los.py"

EXPECTED = {
    # scenario: (stage, execution, canonical, recovery)
    "G1": (None, "committed", "COMMITTED", "none"),
    "G2": ("core.snapshot_guard", "refused", "NOT_COMMITTED", "none"),
    "G3": ("core.revision_guard", "refused", "NOT_COMMITTED", "none"),
    "G4": ("core.admission", "refused", "NOT_COMMITTED", "none"),
    "G5": ("ui.transport", "transport-lost", "AMBIGUOUS",
           "reconcile-exact-request"),
    "G6": ("ui.transport", "committed", "COMMITTED", "none"),
    "G7": ("core.projection", "rolled-back", "AMBIGUOUS",
           "reconcile-exact-request"),
    "G8": (None, "committed", "COMMITTED", "none"),
}


def _operations(mini: Path, *args: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(LOS), "--root", str(mini), "operations", *args],
        capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


@pytest.fixture(scope="module")
def gate(tmp_path_factory):
    if not HARNESS.is_file() or shutil.which("node") is None:
        pytest.skip("the sibling obsidian-ui gate harness (or Node) is missing")
    from conftest import build_mini_repo
    from repo_builders import add_curriculum

    tmp = tmp_path_factory.mktemp("operations-gate")
    mini = build_mini_repo(tmp / "gate")
    add_curriculum(mini)
    proc = subprocess.run(
        ["node", str(HARNESS), "--core-root", str(REPO_ROOT),
         "--repo", str(mini), "--python", sys.executable],
        cwd=str(UI_ROOT), capture_output=True, text=True, timeout=600,
        env={**os.environ, "TMPDIR": str(tmp)})
    assert proc.returncode == 0, (
        f"the UI gate harness failed\n--- stdout ---\n{proc.stdout}"
        f"\n--- stderr ---\n{proc.stderr}")
    marker = [line for line in proc.stdout.splitlines()
              if line.startswith("HARNESS_RESULT ")]
    assert marker, f"the harness printed no result:\n{proc.stdout}"
    result = json.loads(marker[-1][len("HARNESS_RESULT "):])
    assert result["ok"] is True
    assert set(result["scenarios"]) == set(EXPECTED), result["scenarios"]
    # 4 UI events per scenario, 6 for the two-attempt G6/G8.
    assert result["ui_event_count"] == 36, result["ui_event_count"]
    return mini, result["scenarios"]


@pytest.mark.parametrize("code", sorted(EXPECTED))
def test_operations_identifies_verdict(gate, code: str):
    mini, scenarios = gate
    detail = _operations(mini, "--request-id", scenarios[code])
    diagnosis = detail["diagnosis"]
    assert (diagnosis["first_failure_stage"],
            diagnosis["execution_outcome"],
            diagnosis["canonical_outcome"],
            diagnosis["recovery_requirement"]) == EXPECTED[code]


def test_operations_detail_is_render_complete(gate):
    """Every detail carries the timeline, facts, and reasons the view shows —
    Diagnostics must not need any other source."""
    mini, scenarios = gate
    for code, request_id in scenarios.items():
        detail = _operations(mini, "--request-id", request_id)
        assert detail["timeline"], code
        assert detail["ui_outcome"] in ("SETTLED", "REFUSED", "BLOCKED"), code
        assert detail["facts"]["transaction_id"] is not None \
            or detail["diagnosis"]["canonical_outcome"] != "COMMITTED", code
        assert detail["diagnosis"]["reasons"], code
        assert detail["diagnosis"]["authoritative_evidence"] or \
            detail["diagnosis"]["canonical_outcome"] == "AMBIGUOUS", code


def test_operations_list_covers_all_gate_scenarios(gate):
    mini, scenarios = gate
    rows = _operations(mini, "--limit", "50")["operations"]
    assert len(rows) == 8, (
        "one operation per scenario: UI and Core must share the trace, "
        "never record as two operations")
    listed = {row["request_id"] for row in rows}
    assert set(scenarios.values()) <= listed
    attention = {row["request_id"] for row in rows if row["needs_attention"]}
    assert scenarios["G5"] in attention and scenarios["G7"] in attention
    assert scenarios["G1"] not in attention
    recoveries = {row["request_id"] for row in rows
                  if row["replayed"] or row["attempts"] > 1}
    assert scenarios["G6"] in recoveries and scenarios["G8"] in recoveries
