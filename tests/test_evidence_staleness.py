"""Findings 3 and 4: truth maintenance on the learning side, and the
predicate query surface.

Finding 3 compares the fingerprint recorded on each observation against
the live requirement — a belief held under assumptions that later moved
— and feeds mismatches to the scan as `evidence-superseded` goals plus
one line on `los resume`. Finding 4 exposes the 23 predicates through
`los semantic`, so agents can ask instead of re-deriving.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import yaml
from repo_builders import _add_material_overview, add_curriculum, run_los, write_yaml

from learning_os.learning_runtime import requirement_fingerprint
from learning_os.semantics import ScanInput, scan_observations
from learning_os.semantics.goals import stale_observations

MAP = "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
REQUIREMENT = "req-demo-l01-demo"

TARGET = {
    "concept": "concept-expected-value",
    "capability": {"kind": "explain", "operands": ["expectation"]},
    "conditions": ["unfamiliar-example"],
    "evidence_spec": ["explain-reason"],
}


def _requirement(**overrides):
    req = {
        "id": REQUIREMENT,
        "concept": "concept-expected-value",
        "capability": {"kind": "explain", "operands": ["expectation"]},
        "conditions": ["unfamiliar-example"],
        "evidence_spec": ["explain-reason"],
        "source_stage": {"module_id": "module-demo", "unit_id": "unit-demo-l01",
                         "stage_id": "stage-demo"},
    }
    req.update(overrides)
    return req


def test_matching_fingerprint_is_not_stale():
    req = _requirement()
    obs = {"id": "observation-1", "requirement": REQUIREMENT,
           "requirement_sha256": requirement_fingerprint(req)}
    assert stale_observations([req], [obs]) == ()


def test_moved_requirement_stales_its_results():
    req = _requirement()
    obs = {"id": "observation-1", "requirement": REQUIREMENT,
           "requirement_sha256": requirement_fingerprint(req)}
    moved = _requirement(conditions=["unfamiliar-example", "no-explicit-cue"])
    (row,) = stale_observations([moved], [obs])
    assert row.observation_id == "observation-1"
    assert row.requirement == REQUIREMENT
    assert row.recorded_sha != row.current_sha


def test_missing_fingerprint_is_stale_never_trusted():
    req = _requirement()
    assert len(stale_observations([req], [{"id": "observation-legacy",
                                           "requirement": REQUIREMENT}])) == 1


def test_unknown_requirements_are_skipped():
    assert stale_observations([], [{"id": "observation-x", "requirement": "req-ghost",
                                    "requirement_sha256": "sha256:" + "0" * 64}]) == ()


def test_scan_emits_evidence_superseded_with_dedup():
    goals = scan_observations(ScanInput(
        evidence_stale=(("observation-1", REQUIREMENT),)))
    assert [(goal.goal_id, goal.detector) for goal in goals] == [
        ("evidence-superseded:observation-1", "evidence-superseded")]
    assert goals[0].state == "detected"
    again = scan_observations(ScanInput(
        evidence_stale=(("observation-1", REQUIREMENT),),
        known_ids=("evidence-superseded:observation-1",)))
    assert again == ()


def _runtime_repo(mini_repo: Path) -> Path:
    add_curriculum(mini_repo)
    _add_material_overview(mini_repo)
    data = yaml.safe_load((mini_repo / MAP).read_text(encoding="utf-8"))
    stage = data["stages"][0]
    stage["concepts"] = ["concept-expected-value"]
    stage["runtime_target"] = copy.deepcopy(TARGET)
    write_yaml(mini_repo / MAP, data)
    return mini_repo


def test_resume_reports_results_against_a_moved_requirement(mini_repo: Path):
    root = _runtime_repo(mini_repo)
    assert run_los(root, "observe", REQUIREMENT,
                   "--activity", "exercise", "--result", "partial").returncode == 0
    assert "Changed since" not in run_los(root, "resume").stdout
    data = yaml.safe_load((root / MAP).read_text(encoding="utf-8"))
    data["stages"][0]["runtime_target"]["conditions"].append("no-explicit-cue")
    write_yaml(root / MAP, data)
    text = run_los(root, "resume")
    assert text.returncode == 0, text.stderr
    assert "1 earlier result" in text.stdout
    assert "against a requirement that has since changed" in text.stdout


def test_semantic_list_registers_23_predicates(mini_repo: Path):
    proc = run_los(mini_repo, "semantic", "--list")
    assert proc.returncode == 0, proc.stderr
    registry = json.loads(proc.stdout)
    assert len(registry) == 23
    by_name = {row["name"]: row for row in registry}
    assert by_name["NeedsStudyMap"]["inputs"] == [
        "unit_status", "module_status", "has_study_map"]
    assert by_name["NeedsStudyMap"]["authority"] == "OPERATOR.md rule 6"
    assert all({"name", "inputs", "authority", "description"} <= set(row)
               for row in registry)


def test_semantic_evaluates_one_predicate(mini_repo: Path):
    proc = run_los(mini_repo, "semantic", "NeedsStudyMap",
                   "--input", "unit_status=active",
                   "--input", "module_status=enrolled",
                   "--input", "has_study_map=false")
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == {
        "predicate": "NeedsStudyMap", "verdict": True,
        "inputs": {"unit_status": "active", "module_status": "enrolled",
                   "has_study_map": False}}


def test_semantic_refuses_unknown_predicates_and_inputs(mini_repo: Path):
    assert run_los(mini_repo, "semantic", "NoSuchPredicate").returncode == 2
    assert run_los(mini_repo, "semantic").returncode == 2
    proc = run_los(mini_repo, "semantic", "NeedsStudyMap",
                   "--input", "oops-no-equals")
    assert proc.returncode == 2
    proc = run_los(mini_repo, "semantic", "NeedsStudyMap",
                   "--input", "unit_status=active")
    assert proc.returncode == 2  # missing required inputs fail closed
