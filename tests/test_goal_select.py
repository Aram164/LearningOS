"""Finding 1: a detector without a selector is worse than no detector.

1a feeds the dedup channel: `los goal` records Aram's explicit decisions
and the scan reads them back as `known_ids`, so rejected goals stay
rejected. 1b clusters the queue by shared cause (Calcite's CSE applied to
the goal queue, where the redundancy actually lives). 1c orders it by exam
proximity — a hand-written sort, not a learned cost model.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

import yaml
from repo_builders import run_los

from learning_os.semantics import ScanInput, scan_observations
from learning_os.semantics.goals import (
    CandidateGoal,
    GoalCluster,
    cluster_goals,
    rank_clusters,
)
from learning_os.semantics.scan import _read_goal_ledger, collect_observations


def _goal(goal_id: str, detector: str, evidence=()) -> CandidateGoal:
    return CandidateGoal(
        goal_id=goal_id, detector=detector, title=f"Title {goal_id}",
        rationale=f"Rationale {goal_id}", evidence=tuple(evidence))


# ---- 1a: the ledger feeds known_ids ------------------------------------------


def test_goal_reject_writes_a_schema_valid_ledger(mini_repo: Path, repo_root: Path):
    proc = run_los(mini_repo, "goal", "covering-routes-stale:route-1", "--reject",
                   "--note", "route dropped")
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == {
        "ok": True, "goal_id": "covering-routes-stale:route-1", "state": "rejected"}
    ledger = yaml.safe_load(
        (mini_repo / "operations/goal-ledger.yaml").read_text(encoding="utf-8"))
    import json as _json

    from jsonschema import Draft202012Validator, FormatChecker

    schema = _json.loads(
        (repo_root / "system/schema/goal-ledger.schema.json").read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(
        schema, format_checker=FormatChecker()).iter_errors(ledger))
    assert errors == []
    assert ledger["decisions"]["covering-routes-stale:route-1"]["state"] == "rejected"
    assert ledger["decisions"]["covering-routes-stale:route-1"]["note"] == "route dropped"


def test_goal_decision_is_revisable(mini_repo: Path):
    assert run_los(mini_repo, "goal", "g1", "--defer").returncode == 0
    assert run_los(mini_repo, "goal", "g1", "--close").returncode == 0
    ledger = yaml.safe_load(
        (mini_repo / "operations/goal-ledger.yaml").read_text(encoding="utf-8"))
    assert ledger["decisions"]["g1"]["state"] == "closed"


def test_decided_goals_leave_the_scan(mini_repo: Path):
    assert run_los(mini_repo, "goal", "study-map-obligation:unit-x", "--reject").returncode == 0
    assert run_los(mini_repo, "goal", "lineage-stale:claim-y", "--defer").returncode == 0
    decided = _read_goal_ledger(mini_repo)
    assert decided == ("lineage-stale:claim-y", "study-map-obligation:unit-x")
    assert collect_observations(mini_repo, days=0).known_ids == decided
    goals = scan_observations(ScanInput(
        stale_claims=(("claim-y", ("unit-x",)),),
        obligations=("unit-x",),
        known_ids=decided,
    ))
    assert goals == ()


def test_malformed_ledger_reads_as_no_decisions(mini_repo: Path):
    ledger = mini_repo / "operations/goal-ledger.yaml"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text("decisions: [not, a, mapping]\n", encoding="utf-8")
    assert _read_goal_ledger(mini_repo) == ()
    assert collect_observations(mini_repo, days=0).known_ids == ()


def test_goal_refuses_a_blank_id(mini_repo: Path):
    proc = run_los(mini_repo, "goal", "  ", "--reject")
    assert proc.returncode == 2


def test_quiet_scan_reports_no_candidates_in_text(mini_repo: Path):
    proc = run_los(mini_repo, "intelligence-scan", "--days", "0")
    assert proc.returncode == 0, proc.stderr
    assert "no candidates" in proc.stdout


# ---- 1b: clustering -----------------------------------------------------------


def test_shared_cause_clusters_nothing_lost():
    goals = [
        _goal("covering-routes-stale:r1", "covering-routes-stale",
              ["route:r1", "node:n1", "node:n2", "unit:u1"]),
        _goal("covering-routes-stale:r2", "covering-routes-stale",
              ["route:r2", "node:n2", "node:n1", "unit:u1"]),
        _goal("covering-routes-stale:r3", "covering-routes-stale",
              ["route:r3", "node:n9", "unit:u2"]),
    ]
    clusters = cluster_goals(goals)
    assert len(clusters) == 2
    big = next(cluster for cluster in clusters if len(cluster.member_ids) == 2)
    assert big.detector == "covering-routes-stale"
    assert big.member_ids == ("covering-routes-stale:r1", "covering-routes-stale:r2")
    assert big.cause == ("unit:u1",)
    assert "2 routes" in big.title
    assert "unit:u1" in big.title
    assert sorted(member for cluster in clusters for member in cluster.member_ids) == sorted(
        goal.goal_id for goal in goals)


def test_one_unit_is_one_decision_despite_extra_nodes():
    """The ch04 regression: routes over the same moved unit cluster
    together even when one route also covers one more node. The extra
    node does not create a second revalidation decision."""
    goals = [
        _goal("covering-routes-stale:r1", "covering-routes-stale",
              ["route:r1", "node:ch04-a", "node:ch04-b", "unit:u-ch04"]),
        _goal("covering-routes-stale:r2", "covering-routes-stale",
              ["route:r2", "node:ch04-a", "node:ch04-b",
               "node:ch04-extra", "unit:u-ch04"]),
    ]
    (cluster,) = cluster_goals(goals)
    assert cluster.member_ids == (
        "covering-routes-stale:r1", "covering-routes-stale:r2")
    assert cluster.cause == ("unit:u-ch04",)


def test_lineage_and_source_causes_cluster():
    goals = [
        _goal("lineage-stale:a", "lineage-stale",
              ["claim:a", "moved:file:x", "moved:rev:y"]),
        _goal("lineage-stale:b", "lineage-stale",
              ["claim:b", "moved:rev:y", "moved:file:x"]),
        _goal("source-changed-under-claim:c", "source-changed-under-claim",
              ["claim:c", "source:s1"]),
    ]
    clusters = cluster_goals(goals)
    assert len(clusters) == 2
    assert clusters[0].member_ids == ("lineage-stale:a", "lineage-stale:b")
    assert clusters[0].cause == ("moved:file:x", "moved:rev:y")


def test_causeless_detectors_stay_single():
    goals = [
        _goal("study-map-obligation:u1", "study-map-obligation", ["unit:u1"]),
        _goal("study-map-obligation:u2", "study-map-obligation", ["unit:u2"]),
        _goal("repeated-question-gap:q", "repeated-question-gap", ["question-class:q"]),
    ]
    clusters = cluster_goals(goals)
    assert len(clusters) == 3
    assert all(len(cluster.member_ids) == 1 for cluster in clusters)
    by_member = {cluster.member_ids[0]: cluster for cluster in clusters}
    assert by_member["study-map-obligation:u1"].title == "Title study-map-obligation:u1"


def test_clustering_is_deterministic():
    goals = [
        _goal(f"covering-routes-stale:r{n}", "covering-routes-stale",
              [f"route:r{n}", "node:shared", "unit:u1"])
        for n in range(10)
    ]
    first, second = cluster_goals(goals), cluster_goals(list(reversed(goals)))
    assert first == second
    assert len(first) == 1
    assert len(first[0].member_ids) == 10


# ---- 1c: exam-proximity ranking -------------------------------------------------


_TODAY = _dt.date(2026, 9, 11)


def _cluster(cluster_id: str, *members: str) -> GoalCluster:
    return GoalCluster(cluster_id=cluster_id, detector="covering-routes-stale",
                       title=cluster_id, member_ids=tuple(members))


def test_enrolled_sitting_inside_30_days_comes_first():
    urgent = _cluster("c-urgent", "g1")
    near = _cluster("c-near", "g2")
    study = _cluster("c-study", "g3")
    rest = _cluster("c-rest", "g4")
    retired = _cluster("c-retired", "g5")
    deadlines = [
        {"kind": "exam", "module_id": "m-urgent", "start_date": "2026-09-30"},
        {"kind": "exam", "module_id": "m-near", "start_date": "2026-11-15"},
    ]
    status = {"m-urgent": "enrolled", "m-near": "enrolled",
              "m-study": "active", "m-retired": "archived"}
    modules = {"c-urgent": {"m-urgent"}, "c-near": {"m-near"},
               "c-study": {"m-study"}, "c-retired": {"m-retired"}}
    ranked = rank_clusters(
        [rest, retired, study, near, urgent], today=_TODAY,
        deadlines=deadlines, module_status=status, cluster_modules=modules)
    assert [(row.cluster.cluster_id, row.tier) for row in ranked] == [
        ("c-urgent", 1), ("c-near", 2), ("c-study", 3),
        ("c-rest", 4), ("c-retired", 5)]
    assert ranked[0].nearest_sitting == "2026-09-30"
    assert ranked[0].days_until == 19


def test_retired_module_sorts_last_despite_a_near_sitting():
    retired = _cluster("c-retired", "g1")
    ranked = rank_clusters(
        [retired], today=_TODAY,
        deadlines=[{"kind": "exam", "module_id": "m-old", "start_date": "2026-09-20"}],
        module_status={"m-old": "archived"},
        cluster_modules={"c-retired": {"m-old"}})
    assert ranked[0].tier == 5


def test_ties_break_on_cluster_size_then_id():
    small = _cluster("c-a", "g1")
    big = _cluster("c-b", "g1", "g2", "g3")
    ranked = rank_clusters([small, big], today=_TODAY, deadlines=[],
                           module_status={})
    assert [row.cluster.cluster_id for row in ranked] == ["c-b", "c-a"]


def test_malformed_deadlines_never_go_urgent():
    cluster = _cluster("c-x", "g1")
    ranked = rank_clusters(
        [cluster], today=_TODAY,
        deadlines=[{"kind": "exam", "module_id": "m", "start_date": "not-a-date"},
                   {"kind": "registration-window", "module_id": "m",
                    "start_date": "2026-09-12"},
                   "garbage"],
        module_status={"m": "enrolled"},
        cluster_modules={"c-x": {"m"}})
    assert ranked[0].tier == 3
