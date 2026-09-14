"""Runtime V0 checks: stage-owned IR, evidence governance, bounded repair."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import yaml
from gateway_helpers import approved_v2_envelope, run_v2_capability
from repo_builders import _add_material_overview, add_curriculum, run_los, write_yaml

from learning_os.contracts.json_schema import ContractValidationError
from learning_os.genout import generate_all
from learning_os.genout.learner_interpreter import _collect_and_interpret, interpret_observations
from learning_os.genout.session_compiler import compile_session, replan_session
from learning_os.learning_runtime import (
    RuntimeInputError,
    activity_fingerprint,
    collect_requirements,
    read_observations,
    requirement_fingerprint,
)
from learning_os.loader import load_repo
from learning_os.rules import validate

TARGET = {
    "concept": "concept-expected-value",
    "capability": {"kind": "explain", "operands": ["expectation"]},
    "conditions": ["unfamiliar-example"],
    "evidence_spec": ["explain-reason"],
}


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
    stage = data["stages"][0]
    stage["concepts"] = ["concept-expected-value"]
    stage["runtime_target"] = copy.deepcopy(TARGET)
    for i, (resource, affordance) in enumerate(zip(stage["resources"], ["intervention", "evidence", "mixed"], strict=True)):
        resource.update({"route_id": f"route-demo-{i}", "affordance": affordance,
                         "kind": "practise" if i else "read", "scope_triage": "required-now",
                         "vault_path": "work/active/workspace-demo/scratch/activity.md"})
    (mini_repo / "work/active/workspace-demo/scratch/activity.md").write_text("Synthetic task.\n")
    write_yaml(path, data)
    _review(mini_repo, "route-demo-1", ["unfamiliar-example"])
    _review(mini_repo, "route-demo-2", ["unfamiliar-example"])
    return mini_repo


def inputs(root):
    repo = load_repo(root)
    reqs = collect_requirements(repo)
    assert len(reqs) == 1
    return repo, reqs[0]


def observation(req_id, i, **changes):
    return {"id": f"observation-{i}", "requirement": req_id, "activity": f"task-{i}",
            "result": "correct", "assistance": "none", "timestamp": (datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=i)).isoformat(),
            "conditions": ["unfamiliar-example"], "evidence_tags": ["explain-reason"], **changes}


def test_requirement_compiles_from_owning_stage_only(runtime_root):
    _, req = inputs(runtime_root)
    assert req["id"] == "req-demo-l01-demo"
    assert req["concept"] == "concept-expected-value"
    assert req["source_stage"] == {"module_id": "module-demo", "unit_id": "unit-demo-l01", "stage_id": "stage-demo"}
    first = requirement_fingerprint(req)
    _, again = inputs(runtime_root)
    assert requirement_fingerprint(again) == first


def test_stage_without_target_contributes_no_requirement(runtime_root):
    path = runtime_root / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
    data = yaml.safe_load(path.read_text())
    del data["stages"][0]["runtime_target"]
    write_yaml(path, data)
    assert collect_requirements(load_repo(runtime_root)) == []


def test_sidecar_channel_is_retired(runtime_root):
    unit = runtime_root / "curriculum/modules/module-demo/units/unit-demo-l01"
    write_yaml(unit / "stages/stage-demo/requirements.yaml", [{
        "id": "req-demo", "concept": "concept-expected-value",
        "capability": {"kind": "explain", "operands": ["expectation"]},
        "conditions": ["unfamiliar-example"], "evidence_spec": ["explain-reason"],
        "source_stage": {"module_id": "module-demo", "unit_id": "unit-demo-l01", "stage_id": "stage-demo"},
    }])
    repo = load_repo(runtime_root)
    assert [r["id"] for r in collect_requirements(repo)] == ["req-demo-l01-demo"]
    assert any(issue.code == "LEARNING-RUNTIME" and "sidecar" in issue.message
               for issue in validate(repo))


@pytest.mark.parametrize("change", [
    {"concept": "concept-unknown"},
    {"capability": {"kind": "", "operands": ["x"]}},
    {"evidence_spec": []},
    {"concept": "knowledge-unknown"},
])
def test_requirement_validation_rejects_bad_target_semantics(runtime_root, change):
    path = runtime_root / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
    data = yaml.safe_load(path.read_text())
    data["stages"][0]["runtime_target"].update(change)
    write_yaml(path, data)
    with pytest.raises(RuntimeInputError):
        collect_requirements(load_repo(runtime_root))
    assert any(issue.code == "LEARNING-RUNTIME" for issue in validate(load_repo(runtime_root)))


@pytest.mark.parametrize("change", [{"conditions": []}, {"evidence_tags": []}, {"assistance": "hint"}, {"activity": "same-task"}])
def test_two_correct_answers_do_not_automatically_demonstrate(runtime_root, change):
    _, req = inputs(runtime_root)
    obs = [observation(req["id"], 1, requirement_sha256=requirement_fingerprint(req), **change),
           observation(req["id"], 2, requirement_sha256=requirement_fingerprint(req), **change)]
    assert interpret_observations(obs, req)["status"] == "uncertain"


def test_distinct_target_evidence_and_later_failure(runtime_root):
    _, req = inputs(runtime_root)
    obs = [observation(req["id"], 1, assistance="none", requirement_sha256=requirement_fingerprint(req)),
           observation(req["id"], 2, requirement_sha256=requirement_fingerprint(req))]
    assert interpret_observations(obs, req)["status"] == "demonstrated"
    obs += [observation(req["id"], 3, result="incorrect", requirement_sha256=requirement_fingerprint(req)),
            observation(req["id"], 4, assistance="hint", requirement_sha256=requirement_fingerprint(req))]
    result = interpret_observations(obs, req)
    assert result["status"] == "fragile"
    assert len(result["evidence_ids"]) == 4
    assert interpret_observations(list(reversed(obs)), req) == result


def test_legacy_evidence_ids_resolve_and_malformed_lines_refuse(runtime_root):
    ledger = runtime_root / "work/active/workspace-demo/observations.jsonl"
    _, req = inputs(runtime_root)
    obs = observation(req["id"], 1)
    del obs["id"]
    ledger.write_text(json.dumps(obs) + "\n")
    repo, req = inputs(runtime_root)
    first = read_observations(repo, [req])
    assert first == read_observations(repo, [req])
    assert first[0]["origin"]["line"] == 1
    assert first[0]["origin"]["path"] == str(ledger.relative_to(runtime_root))
    ledger.write_text(ledger.read_text() + '{"broken":\n')
    with pytest.raises(RuntimeInputError):
        read_observations(load_repo(runtime_root), [req])


def test_compiler_uses_current_map_binding_and_emits_target_evidence(runtime_root):
    repo, req = inputs(runtime_root)
    study_map = repo.study_maps.pop("study-map-demo-l01")
    study_map.id = "study-map-independent-name"
    repo.study_maps[study_map.id] = study_map
    repo.units["unit-demo-l01"].data["current_study_map"] = study_map.id
    proposal = compile_session(repo, req, {"status": "unseen"})
    assert proposal["plan_status"] == "ready"
    assert [s["intent"] for s in proposal["steps"]] == ["intervention", "evidence"]
    assert proposal["evidence_conditions"] == req["conditions"]
    assert proposal["rejected_alternatives"]
    assert proposal == compile_session(repo, req, {"status": "unseen"})


@pytest.mark.parametrize("change", [{"scope_triage": "reference-only"}, {"affordance": "intervention"}, {"vault_path": "missing.md"}])
def test_no_evidence_means_blocked_not_complete(runtime_root, change):
    repo, req = inputs(runtime_root)
    stage = repo.study_maps["study-map-demo-l01"].data["stages"][0]
    stage["resources"][1].update(change)
    stage["resources"][2]["scope_triage"] = "reference-only"
    proposal = compile_session(repo, req, {"status": "unseen"})
    assert proposal["plan_status"] == "blocked"
    assert proposal["steps"] and all(s["intent"] == "intervention" for s in proposal["steps"])
    assert "independent evidence" in proposal["blockers"][0]


def test_mixed_serves_as_evidence_when_no_pure_evidence(runtime_root):
    repo, req = inputs(runtime_root)
    repo.study_maps["study-map-demo-l01"].data["stages"][0]["resources"][1]["scope_triage"] = "reference-only"
    proposal = compile_session(repo, req, {"status": "unseen"})
    assert proposal["plan_status"] == "ready"
    assert [s["resource_id"] for s in proposal["steps"]] == ["route-demo-0", "route-demo-2"]
    assert proposal["steps"][1]["intent"] == "evidence"
    assert "reviewed prompt" in proposal["steps"][1]["reason"]


def test_budget_filters_and_unknown_durations(runtime_root):
    repo, req = inputs(runtime_root)
    durations = {"route-demo-0": 10, "route-demo-1": 10, "route-demo-2": 10}
    assert compile_session(repo, req, {}, {"available_minutes": 15, "resource_minutes": durations})["plan_status"] == "blocked"
    assert compile_session(repo, req, {}, {"available_minutes": 20, "resource_minutes": durations})["plan_status"] == "ready"
    assert compile_session(repo, req, {}, {"available_minutes": 100})["plan_status"] == "blocked"


SNAP = "sha256:" + "0" * 64


def packet(session, snapshot=SNAP):
    return {"contract": "runtime-session-v1", "schema_version": 1, "snapshot_id": snapshot, "session": session}


def replan(repo, previous, req, interpretation, context, event, snapshot=SNAP):
    return replan_session(repo, packet(previous, snapshot), req, interpretation, context, event, snapshot)


REPAIR_CTX = {"failed_prerequisites": ["standardization"],
              "prerequisite_repairs": {"standardization": "route-demo-2"}}


def test_prerequisite_failure_repairs_then_returns_to_target(runtime_root):
    repo, req = inputs(runtime_root)
    plan = compile_session(repo, req, {}, REPAIR_CTX)
    assert plan["plan_status"] == "ready"
    assert [s["resource_id"] for s in plan["steps"]] == ["route-demo-2", "route-demo-0", "route-demo-1"]
    assert [s["role"] for s in plan["steps"]] == [
        "prerequisite repair", "explanation", "independent evidence"]
    assert "standardization" in plan["steps"][0]["reason"]
    assert "explicitly mapped repair resources" in plan["assumptions"][-1]
    previous = compile_session(repo, req, {})
    repaired = replan(repo, previous, req, {}, REPAIR_CTX, "prerequisite-failure")
    assert repaired["plan_status"] == "ready"
    assert [s["resource_id"] for s in repaired["steps"]] == ["route-demo-2", "route-demo-0", "route-demo-1"]
    assert repaired["replan"] == {"action": "local", "reason": "prerequisite-failure"}
    assert previous == compile_session(repo, req, {})


def test_prerequisite_repair_without_mapping_is_blocked(runtime_root):
    repo, req = inputs(runtime_root)
    plan = compile_session(repo, req, {}, {"failed_prerequisites": ["standardization"]})
    assert plan["plan_status"] == "blocked"
    assert plan["steps"] and all(s["intent"] == "intervention" for s in plan["steps"])
    assert "explicit prerequisite-to-resource mapping" in plan["blockers"][0]


@pytest.mark.parametrize("repairs, reason", [
    ({"standardization": "route-demo-0"}, "no target intervention remains"),
    ({"standardization": "route-missing"}, "not eligible"),
    ({"standardization": "route-demo-1"}, "not an intervention resource"),
])
def test_prerequisite_repair_rejects_unusable_mapping(runtime_root, repairs, reason):
    repo, req = inputs(runtime_root)
    plan = compile_session(repo, req, {}, {"failed_prerequisites": ["standardization"],
                                           "prerequisite_repairs": repairs})
    assert plan["plan_status"] == "blocked"
    assert plan["steps"] and all(s["intent"] == "intervention" for s in plan["steps"])
    assert reason in plan["blockers"][0]


def test_prerequisite_repair_without_evidence_stays_blocked(runtime_root):
    repo, req = inputs(runtime_root)
    repo.study_maps["study-map-demo-l01"].data["stages"][0]["resources"][1]["scope_triage"] = "reference-only"
    plan = compile_session(repo, req, {}, REPAIR_CTX)
    assert plan["plan_status"] == "blocked"
    assert plan["steps"] and all(s["intent"] == "intervention" for s in plan["steps"])
    assert "no target evidence remains" in plan["blockers"][0]
    assert plan["replan_conditions"]


def test_prerequisite_repair_without_evidence_keeps_the_gap_remedy(runtime_root):
    repo, req = inputs(runtime_root)
    plan = compile_session(repo, req, {}, {"exposed_resources": ["route-demo-1", "route-demo-2"],
                                           "failed_prerequisites": ["standardization"],
                                           "prerequisite_repairs": {"standardization": "route-demo-0"}})
    assert plan["plan_status"] == "blocked"
    assert "prerequisite repair alone cannot produce target evidence" in plan["blockers"][0]
    assert any("no admissible activity remains" in note for note in plan["assumptions"])


def test_sticky_replanning_preserves_minor_events(runtime_root):
    repo, req = inputs(runtime_root)
    original = compile_session(repo, req, {})
    saved = copy.deepcopy(original)
    minor = replan(repo, original, req, {"status": "fragile"}, {}, "hint-request")
    assert minor["steps"] == original["steps"]
    assert minor["replan"]["action"] == "none"
    complete = replan(repo, original, req, {"status": "demonstrated"}, {}, "target-evidence-obtained-early")
    assert complete["plan_status"] == "satisfied" and not complete["steps"]
    assert original == saved
    with pytest.raises(RuntimeInputError):
        replan(repo, original, req, {}, {}, "target-evidence-obtained-early")


def test_replan_requires_the_previous_packet_snapshot(runtime_root):
    repo, req = inputs(runtime_root)
    previous = compile_session(repo, req, {})
    with pytest.raises(RuntimeInputError, match="bound to snapshot"):
        replan_session(repo, packet(previous), req, {}, {}, "hint-request", "sha256:" + "1" * 64)
    with pytest.raises(ContractValidationError):
        replan_session(repo, previous, req, {}, {}, "hint-request", SNAP)


def test_material_replan_rejects_changed_definition(runtime_root):
    repo, req = inputs(runtime_root)
    previous = compile_session(repo, req, {})
    req["capability"]["operands"] = ["a-different-target"]
    with pytest.raises(RuntimeInputError, match="definition snapshot"):
        replan(repo, previous, req, {}, {"available_minutes": 30}, "material-time-change")


def envelope(root, req_id, **payload):
    return approved_v2_envelope(root, capability="learner.observation.append",
        payload={"workspace": "workspace-demo", "requirement": req_id, "activity": "task-demo", "result": "correct", **payload},
        artifact_ids=["workspace-demo"], idempotency_key="runtime-test-1")


def test_gateway_append_receipt_retry_and_canonical_semantic_preservation(runtime_root):
    _, req = inputs(runtime_root)
    before = {str(p): p.read_bytes() for d in ["knowledge", "sources", "curriculum"] for p in (runtime_root / d).rglob('*') if p.is_file()}
    request = envelope(runtime_root, req["id"], condition=["unfamiliar-example"], tags="explain-reason")
    result = run_v2_capability(runtime_root, request)
    assert result.returncode == 0, result.stdout + result.stderr
    response = json.loads(result.stdout)
    ledger = runtime_root / "work/active/workspace-demo/observations.jsonl"
    original = ledger.read_bytes()
    assert json.loads(original)["id"] == response["result"]["observation_id"]
    receipt = yaml.safe_load((runtime_root / response["result"]["receipt_path"]).read_text())
    assert receipt["schema_version"] == 2
    replay = run_v2_capability(runtime_root, request)
    assert replay.returncode == 0, replay.stdout + replay.stderr
    assert ledger.read_bytes() == original
    assert all(Path(p).read_bytes() == data for p, data in before.items())
    assert _collect_and_interpret(load_repo(runtime_root))[req["id"]]["status"] == "uncertain"


@pytest.mark.parametrize("change", [{"requirement": "req-missing"}, {"workspace": "../escape"}, {"result": "mastered"}, {"activity": " "}])
def test_gateway_refuses_invalid_observation_without_writes(runtime_root, change):
    _, req = inputs(runtime_root)
    request = envelope(runtime_root, req["id"], **change)
    result = run_v2_capability(runtime_root, request)
    assert result.returncode != 0
    assert not (runtime_root / "work/active/workspace-demo/observations.jsonl").exists()


def test_direct_cli_and_stale_snapshot_refuse(runtime_root):
    _, req = inputs(runtime_root)
    result = run_los(runtime_root, "observation-append", "--workspace", "workspace-demo", "--requirement", req["id"], "--activity", "task", "--result", "correct")
    assert result.returncode == 2 and "GatewayEnvelopeV2" in result.stderr
    request = envelope(runtime_root, req["id"])
    (runtime_root / "work/inbox/later.md").write_text("changed\n")
    result = run_v2_capability(runtime_root, request)
    assert result.returncode != 0
    assert not (runtime_root / "work/active/workspace-demo/observations.jsonl").exists()


def test_symlinked_ledger_refuses_before_reading_or_writing(runtime_root, tmp_path):
    _, req = inputs(runtime_root)
    external = tmp_path / "external.jsonl"
    external.write_text("private\n")
    ledger = runtime_root / "work/active/workspace-demo/observations.jsonl"
    ledger.symlink_to(external)
    result = run_v2_capability(runtime_root, envelope(runtime_root, req["id"]))
    assert result.returncode != 0
    assert external.read_text() == "private\n"


def test_projection_rebuild_is_deterministic_and_read_only(runtime_root):
    _, req = inputs(runtime_root)
    before = {str(p): p.read_bytes() for p in runtime_root.rglob('*') if p.is_file()}
    repo = load_repo(runtime_root)
    one = generate_all(repo, "2026-09-09T00:00:00Z")
    two = generate_all(load_repo(runtime_root), "2026-09-09T00:00:00Z")
    assert one == two
    assert all(Path(p).read_bytes() == data for p, data in before.items())
    assert "learning-requirements.json" in one and "learner-interpretations.json" in one
    assert "compiled-sessions.json" not in one
    assert json.loads(one["learning-requirements.json"])["requirements"][0]["id"] == req["id"]


def test_runtime_cli_proposal_and_sticky_repair_are_read_only(runtime_root):
    _, req = inputs(runtime_root)
    result = run_los(runtime_root, "runtime-session", "--requirement", req["id"])
    assert result.returncode == 0, result.stderr
    issued = json.loads(result.stdout)
    assert issued["session"]["plan_status"] == "ready"
    repaired = run_los(runtime_root, "runtime-session", "--requirement", req["id"],
        "--previous-json", json.dumps(issued), "--event", "hint-request",
        "--expected-snapshot", issued["snapshot_id"])
    assert repaired.returncode == 0, repaired.stderr
    assert json.loads(repaired.stdout)["session"]["steps"] == issued["session"]["steps"]
    assert not (runtime_root / "work/active/workspace-demo/observations.jsonl").exists()
    assert not (runtime_root / "operations/transactions").exists()
    invalid = run_los(runtime_root, "runtime-session", "--requirement", req["id"], "--context-json", '{"available_minutes":0}')
    assert invalid.returncode == 2
    (runtime_root / "work/inbox/changed.md").write_text("new state")
    stale = run_los(runtime_root, "runtime-session", "--requirement", req["id"], "--expected-snapshot", issued["snapshot_id"])
    assert stale.returncode == 3


def test_runtime_cli_rejects_stale_previous_packet(runtime_root):
    _, req = inputs(runtime_root)
    issued = json.loads(run_los(runtime_root, "runtime-session", "--requirement", req["id"]).stdout)
    (runtime_root / "work/inbox/changed.md").write_text("new state")
    fresh = json.loads(run_los(runtime_root, "runtime-session", "--requirement", req["id"]).stdout)
    assert fresh["snapshot_id"] != issued["snapshot_id"]
    replay = run_los(runtime_root, "runtime-session", "--requirement", req["id"],
        "--previous-json", json.dumps(issued), "--event", "hint-request",
        "--expected-snapshot", fresh["snapshot_id"])
    assert replay.returncode == 3
    assert "different snapshot" in replay.stderr


def test_gateway_rejects_stale_revision_and_outside_workspace_scope(runtime_root):
    from learning_os.contracts.gateway import intent_sha256

    _, req = inputs(runtime_root)
    request = envelope(runtime_root, req["id"])
    request["expected_revisions"] = {"workspace-demo": 99}
    request["approval"]["subject_sha256"] = intent_sha256(request)
    result = run_v2_capability(runtime_root, request)
    assert result.returncode != 0
    assert not (runtime_root / "work/active/workspace-demo/observations.jsonl").exists()
    ws = runtime_root / "work/active/workspace-demo/CONTEXT.md"
    ws.write_text(ws.read_text().replace("- module-demo", "- module-other").replace("- unit-demo-l01", "- unit-other"))
    result = run_v2_capability(runtime_root, envelope(runtime_root, req["id"]))
    assert result.returncode != 0 and "outside the workspace" in result.stdout


def test_append_preserves_existing_ledger_without_trailing_newline(runtime_root):
    _, req = inputs(runtime_root)
    ledger = runtime_root / "work/active/workspace-demo/observations.jsonl"
    original = json.dumps(observation(req["id"], 1))
    ledger.write_text(original)
    result = run_v2_capability(runtime_root, envelope(runtime_root, req["id"]))
    assert result.returncode == 0, result.stdout + result.stderr
    assert ledger.read_text().startswith(original + "\n")
    assert len(ledger.read_text().splitlines()) == 2


def _with_spare_intervention(runtime_root):
    path = runtime_root / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
    data = yaml.safe_load(path.read_text())
    data["stages"][0]["resources"].append({
        "route_id": "route-demo-3", "affordance": "intervention", "kind": "practise",
        "label": "Spare guided task", "source_id": "source-demo-book", "locator": "Task 3",
        "scope_triage": "helpful-now",
        "vault_path": "work/active/workspace-demo/scratch/activity.md"})
    write_yaml(path, data)


def test_local_repair_replaces_only_the_unsuitable_step(runtime_root):
    _with_spare_intervention(runtime_root)
    repo, req = inputs(runtime_root)
    previous = compile_session(repo, req, {})
    assert [s["resource_id"] for s in previous["steps"]] == ["route-demo-0", "route-demo-1"]
    repaired = replan(repo, previous, req, {}, {"unsuitable_resources": ["route-demo-0"]}, "selected-resource-unsuitable")
    assert repaired["plan_status"] == "ready"
    assert repaired["replan"] == {"action": "local", "reason": "selected-resource-unsuitable"}
    assert repaired["steps"][0]["resource_id"] == "route-demo-3"
    assert "pedagogically unsuitable" in repaired["steps"][0]["reason"]
    assert repaired["steps"][1] == previous["steps"][1]
    assert all(step["resource_id"] != "route-demo-0" for step in repaired["steps"])
    assert "preserved verbatim" in repaired["assumptions"][-1]


def test_local_repair_separates_access_failure_from_pedagogy(runtime_root):
    _with_spare_intervention(runtime_root)
    repo, req = inputs(runtime_root)
    previous = compile_session(repo, req, {})
    repaired = replan(repo, previous, req, {}, {"unavailable_resources": ["route-demo-0"]}, "selected-resource-unsuitable")
    assert repaired["plan_status"] == "ready"
    assert repaired["steps"][0]["resource_id"] == "route-demo-3"
    assert "access failed" in repaired["steps"][0]["reason"]
    assert repaired["steps"][1] == previous["steps"][1]


def test_local_repair_without_alternative_is_blocked_not_recompiled(runtime_root):
    repo, req = inputs(runtime_root)
    repo.study_maps["study-map-demo-l01"].data["stages"][0]["resources"][2]["affordance"] = "evidence"
    previous = compile_session(repo, req, {})
    repaired = replan(repo, previous, req, {}, {"unsuitable_resources": ["route-demo-0"]}, "selected-resource-unsuitable")
    assert repaired["plan_status"] == "blocked"
    assert not repaired["steps"]
    assert repaired["replan"] == {"action": "local", "reason": "selected-resource-unsuitable"}
    assert "no same-intent alternative" in repaired["blockers"][0]
    assert "withdrawn rather than partially preserved" in repaired["assumptions"][-1]
    assert all("preserved verbatim" not in assumption for assumption in repaired["assumptions"])


def test_local_repair_must_identify_a_selected_resource(runtime_root):
    repo, req = inputs(runtime_root)
    previous = compile_session(repo, req, {})
    with pytest.raises(RuntimeInputError, match="must identify a selected resource"):
        replan(repo, previous, req, {}, {"unsuitable_resources": ["route-unused"]}, "selected-resource-unsuitable")


def test_time_change_still_recompiles_with_new_budget(runtime_root):
    repo, req = inputs(runtime_root)
    previous = compile_session(repo, req, {})
    durations = {"route-demo-0": 10, "route-demo-1": 10, "route-demo-2": 10}
    short = replan(repo, previous, req, {}, {"available_minutes": 15, "resource_minutes": durations}, "material-time-change")
    assert short["plan_status"] == "blocked" and short["replan"]["action"] == "local"


def test_requirement_changes_invalidate_prior_demonstration(runtime_root):
    _, req = inputs(runtime_root)
    obs = [observation(req["id"], i, requirement_sha256=requirement_fingerprint(req)) for i in [1, 2]]
    assert interpret_observations(obs, req)["status"] == "demonstrated"
    req["capability"]["operands"] = ["a-different-target"]
    assert interpret_observations(obs, req)["status"] == "uncertain"


def test_legacy_unbound_answers_cannot_demonstrate(runtime_root):
    _, req = inputs(runtime_root)
    assert interpret_observations([observation(req["id"], 1), observation(req["id"], 2)], req)["status"] == "uncertain"


def test_explicit_correction_preserves_history_and_withdraws_old_credit(runtime_root):
    from learning_os.contracts.gateway import intent_sha256

    repo, req = inputs(runtime_root)
    ledger = runtime_root / "work/active/workspace-demo/observations.jsonl"
    old = "".join(json.dumps(observation(req["id"], i, requirement_sha256=requirement_fingerprint(req))) + "\n" for i in [1, 2])
    ledger.write_text(old)
    request = envelope(runtime_root, req["id"], result="incorrect", supersedes="observation-2", condition=["unfamiliar-example"])
    result = run_v2_capability(runtime_root, request)
    assert result.returncode == 0, result.stdout + result.stderr
    assert ledger.read_text().startswith(old)
    interpreted = _collect_and_interpret(load_repo(runtime_root))[req["id"]]
    assert interpreted["status"] == "fragile"
    assert interpreted["superseded_evidence_ids"] == ["observation-2"]
    assert len(interpreted["evidence_ids"]) == 3
    repeated = envelope(runtime_root, req["id"], result="correct", supersedes="observation-2")
    repeated["idempotency_key"] = "correction-2"
    repeated["approval"]["subject_sha256"] = intent_sha256(repeated)
    rejected = run_v2_capability(runtime_root, repeated)
    assert rejected.returncode != 0
    assert len(ledger.read_text().splitlines()) == 3


def test_unreported_assistance_is_not_independent_evidence(runtime_root):
    _, req = inputs(runtime_root)
    obs = [observation(req["id"], i, requirement_sha256=requirement_fingerprint(req)) for i in [1, 2]]
    for item in obs:
        del item["assistance"]
    assert interpret_observations(obs, req)["status"] == "uncertain"


def test_sticky_replan_does_not_trust_previous_completion_or_foreign_steps(runtime_root):
    repo, req = inputs(runtime_root)
    previous = compile_session(repo, req, {"status": "demonstrated"})
    with pytest.raises(RuntimeInputError, match="completion claim"):
        replan(repo, previous, req, {"status": "uncertain"}, {}, "hint-request")
    previous = compile_session(repo, req, {})
    previous["steps"][0]["resource_id"] = "route-foreign"
    with pytest.raises(RuntimeInputError, match="no longer eligible"):
        replan(repo, previous, req, {}, {}, "hint-request")
    previous = compile_session(repo, req, {})
    req["capability"]["operands"] = ["changed-target"]
    with pytest.raises(RuntimeInputError, match="definition changed"):
        replan(repo, previous, req, {}, {}, "hint-request")


# --- F02: a reported difficulty that cannot be interpreted yet ---------------
# Recording a new partial result through the advertised minimal path — no
# --condition flags — used to be discarded silently, leaving the requirement
# reading demonstrated, satisfied, no next steps. The learner said "I still get
# this wrong" and the system went on telling him he was finished (audit
# `workbench/audits/synthetic-learner-2026-09-12`, F02).

def test_unqualified_difficulty_withholds_the_satisfied_verdict(runtime_root):
    repo, req = inputs(runtime_root)
    fingerprint = requirement_fingerprint(req)
    obs = [observation(req["id"], 1, requirement_sha256=fingerprint),
           observation(req["id"], 2, requirement_sha256=fingerprint)]
    assert interpret_observations(obs, req)["status"] == "demonstrated"
    obs.append(observation(
        req["id"], 3, result="partial", conditions=[], evidence_tags=[],
        requirement_sha256=fingerprint,
        context="a new unfamiliar, uncued example exposed the misconception"))
    result = interpret_observations(obs, req)
    assert result["status"] == "unresolved"
    assert [row["id"] for row in result["unresolved_evidence"]] == ["observation-3"]
    assert result["unresolved_evidence"][0]["missing_conditions"] == ["unfamiliar-example"]
    # The remedy travels with the finding, naming the exact flag that settles it.
    assert "--condition unfamiliar-example" in result["reason"]
    session = compile_session(repo, req, result)
    assert session["plan_status"] != "satisfied"
    assert any("reported difficulty" in line for line in session["assumptions"])
    assert session["steps"], "an unresolved target still proposes work"


def test_unresolved_never_infers_the_missing_qualifiers(runtime_root):
    """It is not a failure of this target either: fragile would be a claim."""
    _, req = inputs(runtime_root)
    fingerprint = requirement_fingerprint(req)
    obs = [observation(req["id"], 1, requirement_sha256=fingerprint),
           observation(req["id"], 2, requirement_sha256=fingerprint),
           observation(req["id"], 3, result="partial", conditions=[],
                       requirement_sha256=fingerprint)]
    result = interpret_observations(obs, req)
    assert result["status"] == "unresolved"
    # The history is intact — nothing was discarded — but those successes are
    # no longer a *current* basis, so they cannot answer the report by
    # themselves (review repair-review-2026-09-13, D4).
    assert result["evidence_ids"] == ["observation-1", "observation-2", "observation-3"]
    assert result["qualifying_evidence_ids"] == []


def test_qualifying_the_difficulty_makes_it_a_failure(runtime_root):
    """The correction path from the audit: supersede with the conditions stated."""
    _, req = inputs(runtime_root)
    fingerprint = requirement_fingerprint(req)
    obs = [observation(req["id"], 1, requirement_sha256=fingerprint),
           observation(req["id"], 2, requirement_sha256=fingerprint),
           observation(req["id"], 3, result="partial", conditions=[],
                       requirement_sha256=fingerprint),
           observation(req["id"], 4, result="partial", supersedes="observation-3",
                       requirement_sha256=fingerprint)]
    result = interpret_observations(obs, req)
    assert result["status"] == "fragile"
    assert result["unresolved_evidence"] == []
    assert "observation-3" in result["superseded_evidence_ids"]


def test_a_result_against_a_changed_definition_stays_distinguishable(runtime_root):
    """Stale is not unresolved: it is about a different question."""
    _, req = inputs(runtime_root)
    fingerprint = requirement_fingerprint(req)
    obs = [observation(req["id"], 1, requirement_sha256=fingerprint),
           observation(req["id"], 2, requirement_sha256=fingerprint),
           observation(req["id"], 3, result="partial", conditions=[],
                       requirement_sha256="sha256:" + "9" * 64)]
    result = interpret_observations(obs, req)
    assert result["status"] == "demonstrated"
    assert result["unresolved_evidence"] == []


def test_later_qualified_successes_close_an_unresolved_report(runtime_root):
    _, req = inputs(runtime_root)
    fingerprint = requirement_fingerprint(req)
    obs = [observation(req["id"], 1, result="partial", conditions=[],
                       requirement_sha256=fingerprint),
           observation(req["id"], 2, requirement_sha256=fingerprint),
           observation(req["id"], 3, requirement_sha256=fingerprint)]
    result = interpret_observations(obs, req)
    assert result["status"] == "demonstrated"
    assert result["unresolved_evidence"] == []


# --- F04: what a fragile target is offered ----------------------------------

def test_fragile_falls_back_to_explanation_when_no_guided_practice(runtime_root):
    """Understanding that broke down gets a repair, not another assessment.

    `fragile` prefers `mixed` — guided practice beats re-explaining something
    he understood once. Both branches used to fall back to `mixed` too, so when
    the stage had none the pool stayed empty and every pure explanation in the
    stage was excluded (audit F04).
    """
    unit = runtime_root / "curriculum/modules/module-demo/units/unit-demo-l01"
    data = yaml.safe_load((unit / "study-map.yaml").read_text())
    for resource in data["stages"][0]["resources"]:
        if resource["affordance"] == "mixed":
            resource["affordance"] = "evidence"
    write_yaml(unit / "study-map.yaml", data)
    repo, req = inputs(runtime_root)
    session = compile_session(repo, req, {"status": "fragile"})
    intents = [step["intent"] for step in session["steps"]]
    assert "intervention" in intents and "evidence" in intents


def test_fragile_still_prefers_guided_practice_when_it_exists(runtime_root):
    repo, req = inputs(runtime_root)
    session = compile_session(repo, req, {"status": "fragile"})
    by_intent = {step["intent"]: step["resource_id"] for step in session["steps"]}
    assert by_intent["intervention"] == "route-demo-2"  # the mixed resource


def test_an_evidence_only_proposal_says_why_it_offers_no_repair(runtime_root):
    """Assessing without explaining is allowed, but never silently."""
    unit = runtime_root / "curriculum/modules/module-demo/units/unit-demo-l01"
    data = yaml.safe_load((unit / "study-map.yaml").read_text())
    for resource in data["stages"][0]["resources"]:
        resource["affordance"] = "evidence"
    write_yaml(unit / "study-map.yaml", data)
    repo, req = inputs(runtime_root)
    session = compile_session(repo, req, {"status": "fragile"})
    assert [step["intent"] for step in session["steps"]] == ["evidence"]
    assert any("offers no repair" in line for line in session["assumptions"])


# --- F03: independence of the proposed assessment ---------------------------
# The compiler called the stage's `evidence` route "independent evidence" on
# the strength of an affordance the contract itself calls a candidate
# annotation. For the CLT target that route was Blatt 4, whose Aufgabe 3 is
# titled *Zentraler Grenzwertsatz*, against a target requiring the distinction
# on an unfamiliar example with no explicit CLT cue. Rejecting the lecture then
# replaced it with UE6 — the official solutions to that same worksheet — while
# the worksheet stayed on as the assessment (audit
# `workbench/audits/synthetic-learner-2026-09-12`, F03).

def _expose(root: Path, answering: str, *answered: str) -> None:
    """Declare that one route hands over the others' solutions."""
    path = root / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(path.read_text())
    for route in source_map["sources"][0]["unit_routes"]:
        if route["id"] == answering:
            route["exposes_solutions_for"] = list(answered)
    write_yaml(path, source_map)


def _review(root: Path, route_id: str, conditions: list[str]) -> None:
    """Record that someone checked this activity against these conditions."""
    path = root / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
    data = yaml.safe_load(path.read_text())
    repo, req = inputs(root)
    current = {r["route_id"]: r for r in repo.study_maps["study-map-demo-l01"].data["stages"][0]["resources"]}
    for resource in data["stages"][0]["resources"]:
        if resource["route_id"] == route_id:
            resource["independent_evidence"] = {
                "reviewed_by": "aram", "reviewed_on": "2026-09-13",
                "verified_conditions": conditions,
                "requirement_sha256": requirement_fingerprint(req),
                "activity_sha256": activity_fingerprint(repo, current[route_id]),
            }
    write_yaml(path, data)


def test_unreviewed_assessment_is_blocked_while_practice_remains_available(runtime_root):
    repo, req = inputs(runtime_root)
    for resource in repo.study_maps["study-map-demo-l01"].data["stages"][0]["resources"]:
        resource.pop("independent_evidence", None)
    session = compile_session(repo, req, {"status": "uncertain"})
    assert session["plan_status"] == "blocked"
    assert session["steps"] and all(s["intent"] == "intervention" for s in session["steps"])
    assert any("has not been reviewed" in r["reason"] for r in session["rejected_alternatives"])


def test_a_review_that_covers_the_conditions_removes_the_qualifier(runtime_root):
    _review(runtime_root, "route-demo-1", ["unfamiliar-example"])
    repo, req = inputs(runtime_root)
    session = compile_session(repo, req, {"status": "uncertain"})
    step = next(s for s in session["steps"] if s["intent"] == "evidence")
    assert step["role"] == "independent evidence"
    assert "nobody has checked" not in step["reason"]


# A gate that fails closed still has to say which side of the door the work is
# on. Every one of these blockages printed the same sentence, and one of them
# is not a task at all: the live CLT stage carries exactly two activities able
# to satisfy a two-distinct-unfamiliar-tasks criterion, so a single honest
# assessment spends the pool and no further study reopens it.

def test_a_spent_evidence_pool_is_named_as_a_dead_end(runtime_root):
    """Attempted and solution-exposed activities are gone, not pending."""
    repo, req = inputs(runtime_root)
    session = compile_session(repo, req, {"status": "uncertain"},
                              {"exposed_resources": ["route-demo-1", "route-demo-2"]})
    assert session["plan_status"] == "blocked"
    assert any("is spent" in blocker for blocker in session["blockers"])
    assert any("Register a new activity for this target" in note
               for note in session["assumptions"])
    assert not any("what would clear it" in note for note in session["assumptions"])


def test_a_recoverable_block_names_what_would_clear_it(runtime_root):
    """A review nobody has run yet is work, and the proposal says which work."""
    repo, req = inputs(runtime_root)
    for resource in repo.study_maps["study-map-demo-l01"].data["stages"][0]["resources"]:
        resource.pop("independent_evidence", None)
    session = compile_session(repo, req, {"status": "uncertain"})
    assert session["plan_status"] == "blocked"
    assert "no accessible, in-scope independent evidence activity" in session["blockers"]
    assert any("what would clear it" in note and "review its suitability" in note
               for note in session["assumptions"])
    assert not any("Register a new activity" in note for note in session["assumptions"])


def test_a_mixed_block_separates_the_spent_activities_from_the_pending_work(runtime_root):
    repo, req = inputs(runtime_root)
    for resource in repo.study_maps["study-map-demo-l01"].data["stages"][0]["resources"]:
        if resource["route_id"] == "route-demo-1":
            resource.pop("independent_evidence", None)
    session = compile_session(repo, req, {"status": "uncertain"},
                              {"exposed_resources": ["route-demo-2"]})
    assert session["plan_status"] == "blocked"
    assert any("what would clear it" in note and "review its suitability" in note
               for note in session["assumptions"])
    assert any("spent for this target and not reusable: route-demo-2" in note
               for note in session["assumptions"])


def test_a_negative_review_outranks_a_missing_asset(runtime_root):
    """Found by synthetic use: 'obtain the missing asset' was offered for Blatt 4.

    A current review of the exact content had already judged it unable to test
    the target, so no download could ever unblock it. Reporting the transient
    obstacle in front of the permanent one turned a dead end into a chore.
    """
    source_path = runtime_root / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(source_path.read_text())
    for route in source_map["sources"][0]["unit_routes"]:
        if route["id"] == "route-demo-1":
            route["requires_assets"] = [{"name": "template.py", "needed_for": "part (b)",
                                         "obtain_from": "Moodle"}]
    write_yaml(source_path, source_map)
    _review(runtime_root, "route-demo-1", [])
    _review(runtime_root, "route-demo-2", [])
    repo, req = inputs(runtime_root)
    session = compile_session(repo, req, {"status": "uncertain"})
    assert any("is spent or already judged unsuitable" in b for b in session["blockers"])
    assert any("reviewed and found unable to test this target" in note
               and "route-demo-1" in note for note in session["assumptions"])
    assert not any("obtain the missing asset" in note for note in session["assumptions"])
    assert any("does not establish an activity suitable for" in row["reason"]
               for row in session["rejected_alternatives"]
               if row["resource_id"] == "route-demo-1")


# Found by synthetic use: retiring a stage's runtime_target is an ordinary plan
# edit, but every attempt already recorded against it is then orphaned. The
# reader pointed at observations.jsonl — the one file that was still correct —
# and `tools/generate.py`, the rebuild hard rule 1 sends every canonical repair
# through, answered with an uncaught traceback and no projection.

def _orphan_the_requirement(root: Path, req_id: str) -> None:
    """Record one attempt, then stop declaring the target it belongs to."""
    ledger = root / "work/active/workspace-demo/observations.jsonl"
    ledger.write_text(json.dumps({
        "id": "observation-orphan", "requirement": req_id, "activity": "task-demo",
        "result": "correct", "assistance": "none", "conditions": ["unfamiliar-example"],
        "evidence_tags": ["explain-reason"],
        "timestamp": datetime(2026, 1, 1, tzinfo=UTC).isoformat(),
    }) + "\n", encoding="utf-8")
    path = root / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
    data = yaml.safe_load(path.read_text())
    del data["stages"][0]["runtime_target"]
    write_yaml(path, data)


def test_an_orphaned_attempt_names_the_stage_not_the_ledger(runtime_root):
    _, req = inputs(runtime_root)
    _orphan_the_requirement(runtime_root, req["id"])
    repo = load_repo(runtime_root)
    with pytest.raises(RuntimeInputError) as caught:
        read_observations(repo, collect_requirements(repo))
    message = str(caught.value)
    assert "runtime_target" in message
    assert "The ledger line itself is not the fault." in message


def test_the_rebuild_refuses_an_orphaned_attempt_without_a_traceback(runtime_root):
    _, req = inputs(runtime_root)
    _orphan_the_requirement(runtime_root, req["id"])
    generate = Path(__file__).resolve().parent.parent / "tools/generate.py"
    proc = subprocess.run([sys.executable, str(generate), "--root", str(runtime_root)],
                          capture_output=True, text=True)
    assert proc.returncode == 1
    assert "generation refused" in proc.stdout
    assert "Traceback" not in proc.stderr


def test_a_session_with_nothing_left_does_not_promise_practice(runtime_root):
    """Found by synthetic use against the real vault.

    A finite budget with no duration estimates rules out every resource, so the
    proposal carried an empty step list under the sentence "the listed practice
    remains available". There was no list.
    """
    repo, req = inputs(runtime_root)
    session = compile_session(repo, req, {"status": "uncertain"}, {"available_minutes": 5})
    assert session["plan_status"] == "blocked"
    assert session["steps"] == []
    assert any("no practice resource is reachable either" in note
               for note in session["assumptions"])
    assert not any("the listed practice remains available" in note
                   for note in session["assumptions"])


def test_answers_inside_the_same_material_are_named_before_the_attempt(runtime_root):
    """Route separation is not page separation when both live in one book."""
    _expose(runtime_root, "route-demo-2", "route-demo-1")
    repo, req = inputs(runtime_root)
    session = compile_session(repo, req, {"status": "uncertain"})
    step = next(s for s in session["steps"] if s["intent"] == "evidence")
    assert step["resource_id"] == "route-demo-1"
    assert any("are in the same material as the task" in note and "route-demo-2" in note
               for note in session["assumptions"])


def test_an_evidence_step_names_the_review_it_rests_on(runtime_root):
    repo, req = inputs(runtime_root)
    session = compile_session(repo, req, {"status": "uncertain"})
    step = next(s for s in session["steps"] if s["intent"] == "evidence")
    assert "content review by aram of 2026-09-13" in step["reason"]
    assert "not re-examined while they hold" in step["reason"]


def test_blocked_assessment_still_offers_a_partly_runnable_activity(runtime_root):
    """Practice survives a blocked assessment even when an asset is missing."""
    source_path = runtime_root / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(source_path.read_text())
    for route in source_map["sources"][0]["unit_routes"]:
        route["requires_assets"] = [{"name": "template.py", "needed_for": "part (b)",
                                     "obtain_from": "Moodle"}]
    write_yaml(source_path, source_map)
    repo, req = inputs(runtime_root)
    session = compile_session(repo, req, {"status": "uncertain"})
    assert session["plan_status"] == "blocked"
    assert session["steps"] and all(s["role"] == "practice" for s in session["steps"])
    assert any("needs template.py for part (b)" in note for note in session["assumptions"])


def test_a_review_that_falls_short_disqualifies_the_activity(runtime_root):
    """Someone opened it and said it does not test this; that is not advice."""
    _review(runtime_root, "route-demo-1", [])
    _review(runtime_root, "route-demo-2", [])
    repo, req = inputs(runtime_root)
    session = compile_session(repo, req, {"status": "uncertain"})
    assert session["plan_status"] == "blocked"
    # Not the generic "none available": a current review looked and said no.
    assert any("is spent or already judged unsuitable" in b for b in session["blockers"])
    assert any("does not establish an activity suitable for: unfamiliar-example" in row["reason"]
               for row in session["rejected_alternatives"])


def _add_solution_route(root: Path) -> None:
    """A second explanation that happens to be the assessment's answer key."""
    source_path = root / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(source_path.read_text())
    routes = source_map["sources"][0]["unit_routes"]
    routes.append({**copy.deepcopy(routes[0]), "id": "route-demo-solutions",
                   "locator": "Worked solutions",
                   "exposes_solutions_for": ["route-demo-1"]})
    write_yaml(source_path, source_map)
    path = root / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
    data = yaml.safe_load(path.read_text())
    resources = data["stages"][0]["resources"]
    resources.append({**copy.deepcopy(resources[0]),
                      "route_id": "route-demo-solutions",
                      "affordance": "intervention"})
    write_yaml(path, data)


def test_a_solution_key_is_never_paired_with_the_activity_it_answers(runtime_root):
    _expose(runtime_root, "route-demo-0", "route-demo-1")
    repo, req = inputs(runtime_root)
    session = compile_session(repo, req, {"status": "uncertain"})
    pairs = {(s["intent"], s["resource_id"]) for s in session["steps"]}
    assert ("intervention", "route-demo-0") not in pairs or \
           ("evidence", "route-demo-1") not in pairs


def test_no_unaided_pairing_is_said_plainly_not_blamed_on_time(runtime_root):
    """Every explanation answers the assessment, and the blocker says that."""
    path = runtime_root / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
    data = yaml.safe_load(path.read_text())
    for resource in data["stages"][0]["resources"]:
        if resource["route_id"] == "route-demo-2":  # no mixed fallback here
            resource["affordance"] = "evidence"
    write_yaml(path, data)
    _expose(runtime_root, "route-demo-0", "route-demo-1", "route-demo-2")
    repo, req = inputs(runtime_root)
    session = compile_session(repo, req, {"status": "uncertain"})
    assert session["plan_status"] == "blocked"
    assert any("exposes the solutions" in b for b in session["blockers"])
    assert not any("available time" in b for b in session["blockers"])


def test_replacing_an_explanation_never_hands_over_the_preserved_answers(runtime_root):
    """The exact F03 sequence: reject the explanation, keep the assessment.

    Rejecting the CLT lecture replaced it with UE6 — the official Blatt 4
    solutions — while Blatt 4 stayed on as the independent-evidence step.
    """
    _add_solution_route(runtime_root)
    repo, req = inputs(runtime_root)
    repo.study_maps["study-map-demo-l01"].data["stages"][0]["resources"][2]["affordance"] = "evidence"
    previous = compile_session(repo, req, {"status": "uncertain"})
    assert [s["resource_id"] for s in previous["steps"]] == ["route-demo-0", "route-demo-1"]
    repaired = replan(repo, previous, req, {"status": "uncertain"},
                      {"unsuitable_resources": ["route-demo-0"]},
                      "selected-resource-unsuitable")
    ids = {s["resource_id"] for s in repaired["steps"]}
    assert "route-demo-solutions" not in ids, \
        "the replacement answers the preserved assessment"
    assert repaired["plan_status"] == "blocked"
    assert any("expose the preserved assessment's solutions" in b
               for b in repaired["blockers"])


# --- F06: reachable is not the same as doable -------------------------------

def _require_asset(root: Path, route_id: str, asset: dict) -> None:
    path = root / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(path.read_text())
    for route in source_map["sources"][0]["unit_routes"]:
        if route["id"] == route_id:
            route["requires_assets"] = [asset]
    write_yaml(path, source_map)


def test_a_missing_task_asset_is_named_not_silently_included(runtime_root):
    """The worksheet opens; part (b) cannot be done. Both are true (audit F06)."""
    _require_asset(runtime_root, "route-demo-1", {
        "name": "International_Education_Costs.csv",
        "needed_for": "Aufgabe 3(b)",
        "obtain_from": "the Moodle course",
    })
    repo, req = inputs(runtime_root)
    session = compile_session(repo, req, {"status": "uncertain"})
    assert all(s["resource_id"] != "route-demo-1" for s in session["steps"])
    assert session["plan_status"] == "ready", "the other reviewed activity remains usable"
    note = next(row["reason"] for row in session["rejected_alternatives"]
                if "International_Education_Costs.csv" in row["reason"])
    assert "Aufgabe 3(b)" in note and "Moodle" in note
    assert "do not substitute" in note


def test_a_registered_asset_produces_no_warning(runtime_root):
    """A declared asset that resolves says nothing; only absence is news."""
    materials = runtime_root.parent / "materials/source-demo-book"
    materials.mkdir(parents=True, exist_ok=True)
    (materials / "dataset.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    _require_asset(runtime_root, "route-demo-1", {
        "name": "dataset.csv",
        "material_uri": "material://source-demo-book/dataset.csv",
    })
    repo, req = inputs(runtime_root)
    session = compile_session(repo, req, {"status": "uncertain"})
    assert not any("dataset.csv" in a for a in session["assumptions"])


def test_an_unreadable_report_is_visible_even_when_nothing_was_claimed(runtime_root):
    """An open report is an open report, whether or not it displaced a verdict."""
    repo, req = inputs(runtime_root)
    obs = [observation(req["id"], 1, result="partial", conditions=[],
                       requirement_sha256=requirement_fingerprint(req))]
    result = interpret_observations(obs, req)
    assert result["status"] == "unresolved"
    # Nothing was displaced here, and the sentence does not pretend otherwise.
    assert "resets nothing" in result["unresolved_reason"]
    assert "withheld" not in result["unresolved_reason"]
    session = compile_session(repo, req, result)
    assert any("reported difficulty" in line for line in session["assumptions"])


# --- D4 / R1: an unresolved difficulty is not cleared by old evidence -------
# A correct, B correct, unknown-condition partial, then A correct again read
# `demonstrated`/`satisfied`: the pre-difficulty success set still held A and
# B, so re-adding A put it back at two and cleared the report. The difficulty
# was answered by evidence that predated it (review
# `workbench/audits/repair-review-2026-09-13`, R1).

def _after(runtime_root, *rows):
    _, req = inputs(runtime_root)
    fingerprint = requirement_fingerprint(req)
    obs = []
    for i, row in enumerate(rows, start=1):
        obs.append(observation(req["id"], i, requirement_sha256=fingerprint, **row))
    return req, obs, interpret_observations(obs, req)


def test_repeating_a_credited_activity_cannot_clear_the_difficulty(runtime_root):
    _, _, result = _after(
        runtime_root,
        {"activity": "task-a"},
        {"activity": "task-b"},
        {"activity": "task-c", "result": "partial", "conditions": [], "evidence_tags": []},
        {"activity": "task-a"},
    )
    assert result["status"] == "unresolved"
    assert [row["id"] for row in result["unresolved_evidence"]] == ["observation-3"]


def test_one_new_distinct_activity_is_still_not_a_new_basis(runtime_root):
    _, _, result = _after(
        runtime_root,
        {"activity": "task-a"},
        {"activity": "task-b"},
        {"activity": "task-c", "result": "partial", "conditions": [], "evidence_tags": []},
        {"activity": "task-d"},
    )
    assert result["status"] == "unresolved"


def test_two_distinct_activities_after_the_difficulty_establish_a_new_basis(runtime_root):
    _, _, result = _after(
        runtime_root,
        {"activity": "task-a"},
        {"activity": "task-b"},
        {"activity": "task-c", "result": "partial", "conditions": [], "evidence_tags": []},
        {"activity": "task-d"},
        {"activity": "task-e"},
    )
    assert result["status"] == "demonstrated"
    # The report stays on the record, and the reason says what answered it
    # rather than pretending the missing facts were filled in.
    assert [row["id"] for row in result["resolved_difficulty"]] == ["observation-3"]
    assert result["resolved_difficulty"][0]["resolved_by"] == ["observation-4", "observation-5"]
    assert "still unknown" in result["reason"]
    assert "observation-3" in result["reason"]


def test_an_explicit_correction_settles_it_without_new_evidence(runtime_root):
    _, _, result = _after(
        runtime_root,
        {"activity": "task-a"},
        {"activity": "task-b"},
        {"activity": "task-c", "result": "partial", "conditions": [], "evidence_tags": []},
        {"activity": "task-c", "result": "partial", "supersedes": "observation-3"},
    )
    assert result["status"] == "fragile"
    assert result["unresolved_evidence"] == []


def test_a_condition_stated_as_not_met_is_a_different_situation(runtime_root):
    """The alternative D4 asked for: say what did not hold, not what did."""
    _, _, result = _after(
        runtime_root,
        {"activity": "task-a"},
        {"activity": "task-b"},
        {"activity": "task-c", "result": "partial", "conditions": [],
         "evidence_tags": [], "conditions_not_met": ["unfamiliar-example"]},
    )
    # He had seen the example before, so the attempt says nothing about the
    # target under its own conditions: no reset, and nothing left open.
    assert result["status"] == "demonstrated"
    assert result["unresolved_evidence"] == []
    assert [row["id"] for row in result["different_condition_evidence"]] == ["observation-3"]


def test_a_condition_cannot_be_both_met_and_not_met(runtime_root):
    """The two lists are disjoint by construction, so the record cannot lie."""
    _, _, result = _after(
        runtime_root,
        {"activity": "task-a", "result": "partial", "conditions": ["unfamiliar-example"],
         "evidence_tags": [], "conditions_not_met": ["unfamiliar-example"]},
    )
    # The interpreter reads a contradictory record conservatively rather than
    # crashing; intake refuses to create one in the first place.
    assert result["status"] in {"uncertain", "unresolved"}


def test_a_credited_activity_is_spent_and_cannot_rebuild_the_basis(runtime_root):
    """D4's "previously credited activities cannot provide that new basis"."""
    _, _, result = _after(
        runtime_root,
        {"activity": "task-a"},
        {"activity": "task-b"},
        {"activity": "task-c", "result": "partial", "conditions": [], "evidence_tags": []},
        {"activity": "task-a"},   # spent
        {"activity": "task-d"},   # one genuinely new activity is not two
    )
    assert result["status"] == "unresolved"
    assert [row["activity"] for row in result["not_counted_evidence"]] == ["task-a"]
    assert "already credited" in result["not_counted_evidence"][0]["reason"]


@pytest.mark.parametrize("failure_conditions, expected_status", [
    ([], "unresolved"),
    (["unfamiliar-example"], "fragile"),
])
def test_old_credit_cannot_clear_a_second_difficulty(runtime_root, failure_conditions, expected_status):
    """Recovering once does not make the first pair new evidence again."""
    req, obs, result = _after(
        runtime_root,
        {"activity": "task-a"},
        {"activity": "task-b"},
        {"activity": "task-c", "result": "partial", "conditions": [], "evidence_tags": []},
        {"activity": "task-d"},
        {"activity": "task-e"},   # a valid new basis
        {"activity": "task-f", "result": "incorrect", "conditions": failure_conditions},
        {"activity": "task-a"},
        {"activity": "task-b"},
    )
    assert result["status"] == expected_status
    assert {row["activity"] for row in result["not_counted_evidence"]} == {"task-a", "task-b"}
    assert result["qualifying_evidence_ids"] == []
    for i, activity in enumerate(["task-g", "task-h"], start=9):
        obs.append(observation(req["id"], i, activity=activity,
                               requirement_sha256=requirement_fingerprint(req)))
    recovered = interpret_observations(obs, req)
    assert recovered["status"] == "demonstrated"
    assert recovered["qualifying_evidence_ids"] == ["observation-9", "observation-10"]


@pytest.mark.parametrize("blockage", ["unreviewed", "exposed"])
def test_replacing_practice_cannot_erase_an_assessment_blocker(runtime_root, blockage):
    repo, req = inputs(runtime_root)
    resources = repo.study_maps["study-map-demo-l01"].data["stages"][0]["resources"]
    resources.append({**resources[0], "route_id": "route-demo-alternative"})
    context = {}
    if blockage == "unreviewed":
        for resource in resources:
            resource.pop("independent_evidence", None)
    else:
        context["exposed_resources"] = ["route-demo-1", "route-demo-2"]
    previous = compile_session(repo, req, {}, context)
    assert previous["plan_status"] == "blocked"
    flagged = previous["steps"][0]["resource_id"]
    result = replan(repo, previous, req, {},
                    {**context, "unsuitable_resources": [flagged]},
                    "selected-resource-unsuitable")
    assert result["plan_status"] == "blocked"
    assert result["blockers"]
    assert result["steps"] and all(step["intent"] == "intervention" for step in result["steps"])
    assert flagged not in {step["resource_id"] for step in result["steps"]}


def test_replacement_keeps_asset_limits_and_same_material_answer_notice(runtime_root):
    source_path = runtime_root / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(source_path.read_text())
    routes = source_map["sources"][0]["unit_routes"]
    routes[2]["requires_assets"] = [{"name": "template.py", "needed_for": "part (b)",
                                     "obtain_from": "Moodle"}]
    routes.append({**routes[0], "id": "route-demo-answers", "locator": "Answers",
                   "exposes_solutions_for": ["route-demo-1"]})
    write_yaml(source_path, source_map)
    repo, req = inputs(runtime_root)
    previous = compile_session(repo, req, {})
    result = replan(repo, previous, req, {}, {"unsuitable_resources": ["route-demo-0"]},
                    "selected-resource-unsuitable")
    assert result["plan_status"] == "ready"
    assert [step["resource_id"] for step in result["steps"]] == ["route-demo-2", "route-demo-1"]
    assert result["steps"][1] == previous["steps"][1]
    assert any("template.py" in note and "part (b)" in note for note in result["assumptions"])
    assert any("same material as the task" in note for note in result["assumptions"])


def test_replacement_evidence_keeps_its_review_provenance(runtime_root):
    repo, req = inputs(runtime_root)
    previous = compile_session(repo, req, {})
    result = replan(repo, previous, req, {}, {"unsuitable_resources": ["route-demo-1"]},
                    "selected-resource-unsuitable")
    assert result["plan_status"] == "ready"
    evidence = next(step for step in result["steps"] if step["intent"] == "evidence")
    assert evidence["resource_id"] == "route-demo-2"
    assert "Admitted on a content review by aram of 2026-09-13" in evidence["reason"]
    assert "structural replacement" in evidence["reason"]


def test_a_qualified_failure_spends_its_credit_too(runtime_root):
    """The same defect, one branch over: D4's reasoning is not unresolved-only."""
    _, _, result = _after(
        runtime_root,
        {"activity": "task-a"},
        {"activity": "task-b"},
        {"activity": "task-c", "result": "incorrect"},   # fully qualified failure
        {"activity": "task-a"},
        {"activity": "task-b"},
    )
    assert result["status"] == "fragile"
    assert {row["activity"] for row in result["not_counted_evidence"]} == {"task-a", "task-b"}
