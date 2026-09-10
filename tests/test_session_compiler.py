"""Runtime V0 checks: stage-owned IR, evidence governance, bounded repair."""

from __future__ import annotations

import copy
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import yaml
from gateway_helpers import approved_v2_envelope, run_v2_capability
from test_curriculum_v2 import _add_material_overview, add_curriculum, run_los, write_yaml

from learning_os.contracts.json_schema import ContractValidationError
from learning_os.genout import generate_all
from learning_os.genout.learner_interpreter import _collect_and_interpret, interpret_observations
from learning_os.genout.session_compiler import compile_session, replan_session
from learning_os.learning_runtime import (
    RuntimeInputError,
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
    repo.study_maps["study-map-demo-l01"].data["stages"][0]["resources"][1].update(change)
    proposal = compile_session(repo, req, {"status": "unseen"})
    assert proposal["plan_status"] == "blocked"
    assert not proposal["steps"]
    assert "independent evidence" in proposal["blockers"][0]


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
    assert [s["role"] for s in plan["steps"]] == ["prerequisite repair", "explanation", "independent evidence"]
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
    assert not plan["steps"]
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
    assert not plan["steps"]
    assert reason in plan["blockers"][0]


def test_prerequisite_repair_without_evidence_stays_blocked(runtime_root):
    repo, req = inputs(runtime_root)
    repo.study_maps["study-map-demo-l01"].data["stages"][0]["resources"][1]["scope_triage"] = "reference-only"
    plan = compile_session(repo, req, {}, REPAIR_CTX)
    assert plan["plan_status"] == "blocked"
    assert not plan["steps"]
    assert plan["replan_conditions"]


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
