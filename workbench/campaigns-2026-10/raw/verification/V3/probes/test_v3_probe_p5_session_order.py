"""V3 probe, property 5: stage order, current-map binding, detours, shelving.

The session compiler and replanning must respect study-map stage order and
the current-map binding, honour detours and shelving as recorded context,
and never reorder selection by semantic relations (ADR-016 decision 2:
only the strict layer orders; semantic relations never reorder a
prerequisite).
"""

from __future__ import annotations

import copy
import json

import pytest
import yaml
from repo_builders import _add_material_overview, add_curriculum, write_yaml

from learning_os.derive.learning_runtime import (
    RuntimeInputError,
    activity_fingerprint,
    collect_requirements,
    requirement_fingerprint,
)
from learning_os.derive.projection.session_compiler import compile_session, replan_session
from learning_os.store.loader import load_repo

TARGET = {
    "concept": "concept-expected-value",
    "capability": {"kind": "explain", "operands": ["expectation"]},
    "conditions": ["unfamiliar-example"],
    "evidence_spec": ["explain-reason"],
}

SNAP = "sha256:" + "0" * 64


@pytest.fixture
def runtime_root(mini_repo):
    add_curriculum(mini_repo)
    _add_material_overview(mini_repo)
    source_path = mini_repo / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(source_path.read_text())
    route = source_map["sources"][0]["unit_routes"][0]
    source_map["sources"][0]["unit_routes"] = [
        {**route, "id": f"route-demo-{i}", "locator": f"Task {i}"} for i in range(3)
    ]
    write_yaml(source_path, source_map)
    unit = mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01"
    path = unit / "study-map.yaml"
    data = yaml.safe_load(path.read_text())
    first = data["stages"][0]
    first["concepts"] = ["concept-expected-value"]
    first["runtime_target"] = copy.deepcopy(TARGET)
    for i, (resource, affordance) in enumerate(
            zip(first["resources"], ["intervention", "evidence", "mixed"], strict=True)):
        resource.update({"route_id": f"route-demo-{i}", "affordance": affordance,
                         "kind": "practise" if i else "read", "scope_triage": "required-now",
                         "vault_path": "work/active/workspace-demo/scratch/activity.md"})
    (mini_repo / "work/active/workspace-demo/scratch/activity.md").write_text("Synthetic task.\n")
    # A second, later stage with its own targeted requirement.
    later = copy.deepcopy(first)
    later["id"] = "stage-later"
    later["title"] = "Later stage"
    later["objective"] = "A later stage in authored order."
    later["runtime_target"] = {
        "concept": "concept-variance",
        "capability": {"kind": "explain", "operands": ["variance"]},
        "conditions": ["unfamiliar-example"],
        "evidence_spec": ["explain-reason"],
    }
    later["concepts"] = ["concept-variance"]
    data["stages"].append(later)
    write_yaml(path, data)
    # Review both evidence-capable resources so the ready path is exercised.
    repo = load_repo(mini_repo)
    req = next(r for r in collect_requirements(repo) if r["id"] == "req-demo-l01-demo")
    current = {r["route_id"]: r
               for r in repo.study_maps["study-map-demo-l01"].data["stages"][0]["resources"]}
    for route_id in ("route-demo-1", "route-demo-2"):
        for resource in data["stages"][0]["resources"]:
            if resource.get("route_id") == route_id:
                resource["independent_evidence"] = {
                    "reviewed_by": "aram", "reviewed_on": "2026-09-13",
                    "verified_conditions": ["unfamiliar-example"],
                    "requirement_sha256": requirement_fingerprint(req),
                    "activity_sha256": activity_fingerprint(repo, current[route_id]),
                }
    write_yaml(path, data)
    return mini_repo


def _inputs(root):
    repo = load_repo(root)
    reqs = collect_requirements(repo)
    assert len(reqs) == 2
    return repo, reqs


def test_session_selects_only_owning_stage_resources(runtime_root):
    repo, reqs = _inputs(runtime_root)
    study_map = repo.study_maps["study-map-demo-l01"]
    stage_ids = {stage["id"] for stage in study_map.data["stages"]}
    owned = {
        stage["id"]: {r.get("route_id") for r in stage["resources"]}
        for stage in study_map.data["stages"]
    }
    for req in reqs:
        session = compile_session(repo, req, {"status": "unseen"})
        assert session["source_stage"]["stage_id"] in stage_ids
        for step in session["steps"]:
            assert step["resource_id"] in owned[session["source_stage"]["stage_id"]]


def test_session_binds_to_current_study_map(runtime_root):
    repo, reqs = _inputs(runtime_root)
    unit = repo.units["unit-demo-l01"]
    unit.data["current_study_map"] = "study-map-nowhere"
    with pytest.raises(RuntimeInputError):
        compile_session(repo, reqs[0], {"status": "unseen"})


def test_replan_refuses_packet_from_another_stage(runtime_root):
    repo, reqs = _inputs(runtime_root)
    (first, second) = sorted(reqs, key=lambda r: r["id"])
    session = compile_session(repo, first, {"status": "uncertain"})
    session["source_stage"] = dict(session["source_stage"], stage_id="stage-later")
    packet = {"contract": "runtime-session-v1", "schema_version": 1,
              "snapshot_id": SNAP, "session": session}
    with pytest.raises(RuntimeInputError, match="different stage"):
        replan_session(repo, packet, first, {"status": "uncertain"}, {},
                       "target-changed", SNAP)


def test_replan_target_changed_compiles_for_new_stage_and_refuses_without_event(runtime_root):
    repo, reqs = _inputs(runtime_root)
    (first, second) = sorted(reqs, key=lambda r: r["id"])
    session = compile_session(repo, first, {"status": "uncertain"})
    packet = {"contract": "runtime-session-v1", "schema_version": 1,
              "snapshot_id": SNAP, "session": session}
    replanned = replan_session(repo, packet, second, {"status": "unseen"}, {},
                               "target-changed", SNAP)
    assert replanned["source_stage"] == second["source_stage"]
    assert replanned["replan"]["action"] == "session"
    with pytest.raises(RuntimeInputError, match="target-changed"):
        replan_session(repo, packet, second, {"status": "unseen"}, {},
                       "hesitation", SNAP)


def test_replan_refuses_stale_snapshot_and_unknown_event(runtime_root):
    repo, reqs = _inputs(runtime_root)
    (req,) = [r for r in reqs if r["id"] == "req-demo-l01-demo"]
    session = compile_session(repo, req, {"status": "uncertain"})
    packet = {"contract": "runtime-session-v1", "schema_version": 1,
              "snapshot_id": SNAP, "session": session}
    other_snap = "sha256:" + "1" * 64
    with pytest.raises(RuntimeInputError, match="snapshot"):
        replan_session(repo, packet, req, {"status": "uncertain"}, {},
                       "target-changed", other_snap)
    with pytest.raises(RuntimeInputError, match="unknown replan event"):
        replan_session(repo, packet, req, {"status": "uncertain"}, {},
                       "because-i-feel-like-it", SNAP)


def test_semantic_relations_never_reorder_session_selection(runtime_root):
    repo, reqs = _inputs(runtime_root)
    req = next(r for r in reqs if r["id"] == "req-demo-l01-demo")
    baseline = compile_session(repo, req, {"status": "unseen"})
    relations_path = runtime_root / "knowledge/concept-relations.yaml"
    relations = yaml.safe_load(relations_path.read_text())
    # Semantic-layer relations per ADR-016 decision 2, in both directions,
    # including a cycle: none of these may reorder a selection.
    relations["relations"] += [
        {"from": "concept-variance", "type": "derives", "to": "concept-expected-value"},
        {"from": "concept-expected-value", "type": "derives", "to": "concept-variance"},
        {"from": "concept-variance", "type": "equivalent-to", "to": "concept-expected-value"},
        {"from": "concept-expected-value", "type": "motivates", "to": "concept-variance"},
    ]
    write_yaml(relations_path, relations)
    repo = load_repo(runtime_root)
    assert compile_session(repo, req, {"status": "unseen"}) == baseline


def test_authored_order_decides_among_same_triage_resources(runtime_root):
    repo, reqs = _inputs(runtime_root)
    req = next(r for r in reqs if r["id"] == "req-demo-l01-demo")
    study_map_path = (runtime_root /
                      "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml")
    data = yaml.safe_load(study_map_path.read_text())
    stage = next(s for s in data["stages"] if s["id"] == "stage-demo")
    authored = [r["route_id"] for r in stage["resources"]]
    # The role structure is fixed (intervention step first, evidence second);
    # within the evidence pool the authored order decides.
    session = compile_session(repo, req, {"status": "unseen"})
    assert session["plan_status"] == "ready"
    assert [s["resource_id"] for s in session["steps"]] == [authored[0], authored[1]]
    assert session["steps"][0]["intent"] == "intervention"
    # Reversing authored order flips which evidence resource is picked, never
    # the role structure and never by any relation.
    stage["resources"] = list(reversed(stage["resources"]))
    write_yaml(study_map_path, data)
    repo = load_repo(runtime_root)
    flipped = compile_session(repo, req, {"status": "unseen"})
    assert [s["resource_id"] for s in flipped["steps"]] == [authored[0], authored[2]]
    assert [s["intent"] for s in flipped["steps"]] == ["intervention", "evidence"]


def test_detours_and_shelving_leave_session_output_byte_identical(runtime_root):
    repo, reqs = _inputs(runtime_root)
    req = next(r for r in reqs if r["id"] == "req-demo-l01-demo")
    baseline = compile_session(repo, req, {"status": "uncertain"})
    study_map_path = (runtime_root /
                      "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml")
    data = yaml.safe_load(study_map_path.read_text())
    data["detours"] = [{
        "id": "detour-demo", "title": "A detour", "spawned_by_stage": "stage-demo",
        "classification": "helpful-now", "status": "open",
        "return_to_stage": "stage-demo",
    }]
    data["shelving"] = {"state": "proposed", "summary": "A proposal.",
                        "items": [{"id": "proposal-demo", "kind": "garden",
                                   "title": "Seed", "destination": "knowledge/garden",
                                   "rationale": "Worth keeping."}]}
    write_yaml(study_map_path, data)
    repo = load_repo(runtime_root)
    assert compile_session(repo, req, {"status": "uncertain"}) == baseline
