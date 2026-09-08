"""Intelligence scan: observe the live world, interpret, propose.

Pure assembly tests run on synthetic observations (fast); CLI tests run
against the synthetic mini repo (no history, no ledger, no curriculum
units — the scan observes nothing and says so) plus one full-repo run
proving the command works on the checked-in state.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from learning_os.semantics import ScanInput, intelligence_scan, scan_observations

LOS = Path(__file__).resolve().parent.parent / "tools" / "los.py"


def _input(**overrides):
    fields = {
        "changed_nodes": (),
        "route_covers": (),
        "changed_sources": (),
        "claim_sources": (),
        "stale_claims": (),
        "obligations": (),
        "known_ids": (),
    }
    fields.update(overrides)
    return ScanInput(**fields)


def test_empty_observations_propose_nothing():
    assert scan_observations(_input()) == ()


def test_changed_nodes_reach_covering_routes():
    goals = scan_observations(_input(
        changed_nodes=("knowledge-a",),
        route_covers=(("route-1", ("knowledge-a", "knowledge-b")),),
    ))
    assert [(goal.goal_id, goal.detector) for goal in goals] == [
        ("covering-routes-stale:route-1", "covering-routes-stale")]
    assert goals[0].state == "detected"


def test_changed_sources_reach_dependent_claims():
    goals = scan_observations(_input(
        changed_sources=("source-x",),
        claim_sources=(("covers:route-1", ("source-x",)),),
    ))
    assert [(goal.goal_id, goal.detector) for goal in goals] == [
        ("source-changed-under-claim:covers:route-1",
         "source-changed-under-claim")]


def test_stale_claims_and_obligations_emit_with_evidence():
    goals = scan_observations(_input(
        stale_claims=(("covers:route-9", ("unit-x",)),),
        obligations=("unit-needs-map",),
    ))
    assert [(goal.goal_id, goal.detector) for goal in goals] == [
        ("lineage-stale:covers:route-9", "lineage-stale"),
        ("study-map-obligation:unit-needs-map", "study-map-obligation"),
    ]
    assert goals[0].evidence[0] == "claim:covers:route-9"
    assert goals[1].evidence == ("unit:unit-needs-map",)


def test_known_ids_dedup_every_detector():
    known = ("covering-routes-stale:route-1",
             "lineage-stale:covers:route-9",
             "study-map-obligation:unit-needs-map")
    goals = scan_observations(_input(
        changed_nodes=("knowledge-a",),
        route_covers=(("route-1", ("knowledge-a",)),),
        stale_claims=(("covers:route-9", ("unit-x",)),),
        obligations=("unit-needs-map",),
        known_ids=known,
    ))
    assert goals == ()


def test_goals_sort_deterministically():
    first = scan_observations(_input(obligations=("unit-b", "unit-a")))
    second = scan_observations(_input(obligations=("unit-a", "unit-b")))
    assert [goal.goal_id for goal in first] == [
        "study-map-obligation:unit-a", "study-map-obligation:unit-b"]
    assert first == second


def test_scan_on_a_quiet_repo_reports_nothing(mini_repo):
    proc = subprocess.run(
        [sys.executable, str(LOS), "--root", str(mini_repo),
         "intelligence-scan", "--json"],
        capture_output=True, text=True, timeout=180)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == {"goals": []}


def test_scan_refuses_a_negative_window(mini_repo):
    proc = subprocess.run(
        [sys.executable, str(LOS), "--root", str(mini_repo),
         "intelligence-scan", "--days", "-1"],
        capture_output=True, text=True, timeout=120)
    assert proc.returncode == 2


@pytest.mark.full_repo
def test_scan_runs_on_the_checked_in_state():
    root = Path(__file__).resolve().parent.parent
    proc = subprocess.run(
        [sys.executable, str(LOS), "--root", str(root),
         "intelligence-scan", "--json"],
        capture_output=True, text=True, timeout=300)
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert set(payload) == {"goals"}
    for goal in payload["goals"]:
        assert {"goal_id", "detector", "title", "rationale",
                "evidence", "state"} <= set(goal)
        assert goal["state"] == "detected"


def test_intelligence_scan_reads_a_quiet_repo_directly(mini_repo):
    assert intelligence_scan(mini_repo, days=30) == ()
