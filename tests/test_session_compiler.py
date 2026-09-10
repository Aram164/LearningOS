"""Adversarial runtime checks, including the real governed CLI boundary."""

from __future__ import annotations

import copy
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import yaml
from gateway_helpers import approved_v2_envelope, run_v2_capability
from test_curriculum_v2 import _add_material_overview, add_curriculum, run_los, write_yaml

from learning_os.genout import generate_all
from learning_os.genout.learner_interpreter import _collect_and_interpret, interpret_observations
from learning_os.genout.session_compiler import _compile_sessions, compile_session, replan_session
from learning_os.learning_runtime import (
    RuntimeInputError,
    collect_requirements,
    read_observations,
    requirement_fingerprint,
)
from learning_os.loader import load_repo
from learning_os.rules import validate


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
    for i, (resource, affordance) in enumerate(zip(stage["resources"], ["intervention", "evidence", "mixed"], strict=True)):
        resource.update({"route_id": f"route-demo-{i}", "affordance": affordance,
                         "kind": "practise" if i else "read", "scope_triage": "required-now",
                         "vault_path": "work/active/workspace-demo/scratch/activity.md"})
    (mini_repo / "work/active/workspace-demo/scratch/activity.md").write_text("Synthetic task.\n")
    write_yaml(path, data)
    req = {"id": "req-demo", "concept": "concept-expected-value",
           "capability": {"kind": "explain", "operands": ["expectation"]},
           "conditions": ["unfamiliar-example"], "evidence_spec": ["explain-reason"],
           "source_stage": {"module_id": "module-demo", "unit_id": "unit-demo-l01", "stage_id": "stage-demo"}}
    write_yaml(unit / "stages/stage-demo/requirements.yaml", [req])
    return mini_repo


def observation(i, **changes):
    return {"id": f"observation-{i}", "requirement": "req-demo", "activity": f"task-{i}",
            "result": "correct", "assistance": "none", "timestamp": (datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=i)).isoformat(),
            "conditions": ["unfamiliar-example"], "evidence_tags": ["explain-reason"], **changes}


def inputs(root):
    repo = load_repo(root)
    return repo, collect_requirements(repo)[0]


@pytest.mark.parametrize("change", [
    {"concept": "concept-unknown"}, {"capability": {"kind": "", "operands": ["x"]}},
    {"evidence_spec": []}, {"source_stage": {"module_id": "module-other", "unit_id": "unit-demo-l01", "stage_id": "stage-demo"}},
])
def test_requirement_validation_rejects_bad_semantics(runtime_root, change):
    repo, req = inputs(runtime_root)
    req.update(change)
    path = runtime_root / "curriculum/modules/module-demo/units/unit-demo-l01/stages/stage-demo/requirements.yaml"
    write_yaml(path, [req])
    with pytest.raises(RuntimeInputError):
        collect_requirements(load_repo(runtime_root))
    assert any(issue.code == "LEARNING-RUNTIME" for issue in validate(load_repo(runtime_root)))


def test_requirement_without_provenance_and_corrupt_yaml_fail_closed(runtime_root):
    _, req = inputs(runtime_root)
    del req["source_stage"]
    path = runtime_root / "curriculum/modules/module-demo/units/unit-demo-l01/stages/stage-demo/requirements.yaml"
    write_yaml(path, [req])
    with pytest.raises(RuntimeInputError):
        collect_requirements(load_repo(runtime_root))
    path.write_text("[broken: [")
    with pytest.raises(RuntimeInputError):
        collect_requirements(load_repo(runtime_root))


@pytest.mark.parametrize("change", [{"conditions": []}, {"evidence_tags": []}, {"assistance": "hint"}, {"activity": "same-task"}])
def test_two_correct_answers_do_not_automatically_demonstrate(runtime_root, change):
    _, req = inputs(runtime_root)
    obs = [observation(1, requirement_sha256=requirement_fingerprint(req), **change), observation(2, requirement_sha256=requirement_fingerprint(req), **change)]
    assert interpret_observations(obs, req)["status"] == "uncertain"


def test_distinct_target_evidence_and_later_failure(runtime_root):
    _, req = inputs(runtime_root)
    obs = [observation(1, assistance="none", requirement_sha256=requirement_fingerprint(req)), observation(2, requirement_sha256=requirement_fingerprint(req))]
    assert interpret_observations(obs, req)["status"] == "demonstrated"
    obs += [observation(3, result="incorrect", requirement_sha256=requirement_fingerprint(req)), observation(4, assistance="hint", requirement_sha256=requirement_fingerprint(req))]
    result = interpret_observations(obs, req)
    assert result["status"] == "fragile"
    assert len(result["evidence_ids"]) == 4
    assert interpret_observations(list(reversed(obs)), req) == result


def test_legacy_evidence_ids_resolve_and_malformed_lines_refuse(runtime_root):
    ledger = runtime_root / "work/active/workspace-demo/observations.jsonl"
    obs = observation(1)
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


def test_sticky_replanning_preserves_minor_events_and_records_material_changes(runtime_root):
    repo, req = inputs(runtime_root)
    original = compile_session(repo, req, {})
    saved = copy.deepcopy(original)
    minor = replan_session(repo, original, req, {"status": "fragile"}, {}, "hint-request")
    assert minor["steps"] == original["steps"]
    assert minor["replan"]["action"] == "none"
    failed = replan_session(repo, original, req, {}, {"failed_prerequisites": ["standardization"]}, "prerequisite-failure")
    assert failed["plan_status"] == "blocked"
    assert failed["replan"] == {"action": "local", "reason": "prerequisite-failure"}
    complete = replan_session(repo, original, req, {"status": "demonstrated"}, {}, "target-evidence-obtained-early")
    assert complete["plan_status"] == "satisfied" and not complete["steps"]
    assert original == saved
    with pytest.raises(RuntimeInputError):
        replan_session(repo, original, req, {}, {}, "target-evidence-obtained-early")


def envelope(root, **payload):
    return approved_v2_envelope(root, capability="learner.observation.append",
        payload={"workspace": "workspace-demo", "requirement": "req-demo", "activity": "task-demo", "result": "correct", **payload},
        artifact_ids=["workspace-demo"], idempotency_key="runtime-test-1")


def test_gateway_append_receipt_retry_and_canonical_semantic_preservation(runtime_root):
    before = {str(p): p.read_bytes() for d in ["knowledge", "sources", "curriculum"] for p in (runtime_root / d).rglob('*') if p.is_file()}
    request = envelope(runtime_root, condition=["unfamiliar-example"], tags="explain-reason")
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
    assert _collect_and_interpret(load_repo(runtime_root))["req-demo"]["status"] == "uncertain"


@pytest.mark.parametrize("change", [{"requirement": "req-missing"}, {"workspace": "../escape"}, {"result": "mastered"}, {"activity": " "}])
def test_gateway_refuses_invalid_observation_without_writes(runtime_root, change):
    request = envelope(runtime_root, **change)
    result = run_v2_capability(runtime_root, request)
    assert result.returncode != 0
    assert not (runtime_root / "work/active/workspace-demo/observations.jsonl").exists()


def test_direct_cli_and_stale_snapshot_refuse(runtime_root):
    result = run_los(runtime_root, "observation-append", "--workspace", "workspace-demo", "--requirement", "req-demo", "--activity", "task", "--result", "correct")
    assert result.returncode == 2 and "GatewayEnvelopeV2" in result.stderr
    request = envelope(runtime_root)
    (runtime_root / "work/inbox/later.md").write_text("changed\n")
    result = run_v2_capability(runtime_root, request)
    assert result.returncode != 0
    assert not (runtime_root / "work/active/workspace-demo/observations.jsonl").exists()


def test_symlinked_ledger_refuses_before_reading_or_writing(runtime_root, tmp_path):
    external = tmp_path / "external.jsonl"
    external.write_text("private\n")
    ledger = runtime_root / "work/active/workspace-demo/observations.jsonl"
    ledger.symlink_to(external)
    result = run_v2_capability(runtime_root, envelope(runtime_root))
    assert result.returncode != 0
    assert external.read_text() == "private\n"


def test_projection_rebuild_is_deterministic_and_read_only(runtime_root):
    before = {str(p): p.read_bytes() for p in runtime_root.rglob('*') if p.is_file()}
    repo = load_repo(runtime_root)
    one = generate_all(repo, "2026-09-09T00:00:00Z")
    two = generate_all(load_repo(runtime_root), "2026-09-09T00:00:00Z")
    assert one == two
    assert all(Path(p).read_bytes() == data for p, data in before.items())
    assert _compile_sessions(repo)[0]["plan_status"] == "ready"


def test_runtime_cli_proposal_and_sticky_repair_are_read_only(runtime_root):
    result = run_los(runtime_root, "runtime-session", "--requirement", "req-demo")
    assert result.returncode == 0, result.stderr
    packet = json.loads(result.stdout)
    proposal = packet["session"]
    assert proposal["plan_status"] == "ready"
    repaired = run_los(runtime_root, "runtime-session", "--requirement", "req-demo",
        "--previous-json", json.dumps(proposal), "--event", "hint-request",
        "--expected-snapshot", packet["snapshot_id"])
    assert repaired.returncode == 0, repaired.stderr
    assert json.loads(repaired.stdout)["session"]["steps"] == proposal["steps"]
    assert not (runtime_root / "work/active/workspace-demo/observations.jsonl").exists()
    assert not (runtime_root / "operations/transactions").exists()
    invalid = run_los(runtime_root, "runtime-session", "--requirement", "req-demo", "--context-json", '{"available_minutes":0}')
    assert invalid.returncode == 2
    (runtime_root / "work/inbox/changed.md").write_text("new state")
    stale = run_los(runtime_root, "runtime-session", "--requirement", "req-demo", "--expected-snapshot", packet["snapshot_id"])
    assert stale.returncode == 3


def test_gateway_rejects_stale_revision_and_outside_workspace_scope(runtime_root):
    from learning_os.contracts.gateway import intent_sha256

    request = envelope(runtime_root)
    request["expected_revisions"] = {"workspace-demo": 99}
    request["approval"]["subject_sha256"] = intent_sha256(request)
    result = run_v2_capability(runtime_root, request)
    assert result.returncode != 0
    assert not (runtime_root / "work/active/workspace-demo/observations.jsonl").exists()
    ws = runtime_root / "work/active/workspace-demo/CONTEXT.md"
    ws.write_text(ws.read_text().replace("- module-demo", "- module-other").replace("- unit-demo-l01", "- unit-other"))
    result = run_v2_capability(runtime_root, envelope(runtime_root))
    assert result.returncode != 0 and "outside the workspace" in result.stdout


def test_append_preserves_existing_ledger_without_trailing_newline(runtime_root):
    ledger = runtime_root / "work/active/workspace-demo/observations.jsonl"
    original = json.dumps(observation(1))
    ledger.write_text(original)
    result = run_v2_capability(runtime_root, envelope(runtime_root))
    assert result.returncode == 0, result.stdout + result.stderr
    assert ledger.read_text().startswith(original + "\n")
    assert len(ledger.read_text().splitlines()) == 2


def test_local_repair_excludes_failed_resource_and_checks_time(runtime_root):
    repo, req = inputs(runtime_root)
    previous = compile_session(repo, req, {})
    resource = previous["steps"][0]["resource_id"]
    repaired = replan_session(repo, previous, req, {}, {"unavailable_resources": [resource]}, "selected-resource-unsuitable")
    assert all(step["resource_id"] != resource for step in repaired["steps"])
    short = replan_session(repo, previous, req, {}, {"available_minutes": 1}, "material-time-change")
    assert short["plan_status"] == "blocked" and short["replan"]["action"] == "local"


def test_requirement_changes_invalidate_prior_demonstration(runtime_root):
    _, req = inputs(runtime_root)
    obs = [observation(i, requirement_sha256=requirement_fingerprint(req)) for i in [1, 2]]
    assert interpret_observations(obs, req)["status"] == "demonstrated"
    req["capability"]["operands"] = ["a-different-target"]
    assert interpret_observations(obs, req)["status"] == "uncertain"


def test_legacy_unbound_answers_cannot_demonstrate(runtime_root):
    _, req = inputs(runtime_root)
    assert interpret_observations([observation(1), observation(2)], req)["status"] == "uncertain"


def test_explicit_correction_preserves_history_and_withdraws_old_credit(runtime_root):
    from learning_os.contracts.gateway import intent_sha256

    repo, req = inputs(runtime_root)
    ledger = runtime_root / "work/active/workspace-demo/observations.jsonl"
    old = "".join(json.dumps(observation(i, requirement_sha256=requirement_fingerprint(req))) + "\n" for i in [1, 2])
    ledger.write_text(old)
    request = envelope(runtime_root, result="incorrect", supersedes="observation-2", condition=["unfamiliar-example"])
    result = run_v2_capability(runtime_root, request)
    assert result.returncode == 0, result.stdout + result.stderr
    assert ledger.read_text().startswith(old)
    interpreted = _collect_and_interpret(load_repo(runtime_root))["req-demo"]
    assert interpreted["status"] == "fragile"
    assert interpreted["superseded_evidence_ids"] == ["observation-2"]
    assert len(interpreted["evidence_ids"]) == 3
    repeated = envelope(runtime_root, result="correct", supersedes="observation-2")
    repeated["idempotency_key"] = "correction-2"
    repeated["approval"]["subject_sha256"] = intent_sha256(repeated)
    rejected = run_v2_capability(runtime_root, repeated)
    assert rejected.returncode != 0
    assert len(ledger.read_text().splitlines()) == 3


def test_unreported_assistance_is_not_independent_evidence(runtime_root):
    _, req = inputs(runtime_root)
    obs = [observation(i, requirement_sha256=requirement_fingerprint(req)) for i in [1, 2]]
    for item in obs:
        del item["assistance"]
    assert interpret_observations(obs, req)["status"] == "uncertain"


def test_sticky_replan_does_not_trust_previous_completion_or_foreign_steps(runtime_root):
    repo, req = inputs(runtime_root)
    previous = compile_session(repo, req, {"status": "demonstrated"})
    with pytest.raises(RuntimeInputError, match="completion claim"):
        replan_session(repo, previous, req, {"status": "uncertain"}, {}, "hint-request")
    previous = compile_session(repo, req, {})
    previous["steps"][0]["resource_id"] = "route-foreign"
    with pytest.raises(RuntimeInputError, match="no longer eligible"):
        replan_session(repo, previous, req, {}, {}, "hint-request")
    previous = compile_session(repo, req, {})
    req["capability"]["operands"] = ["changed-target"]
    with pytest.raises(RuntimeInputError, match="definition changed"):
        replan_session(repo, previous, req, {}, {}, "hint-request")
