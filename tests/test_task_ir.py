"""Task IR P1: typed compilation, reviewed preview, one guarded write."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest
from repo_builders import material_fixture, run_los

from learning_os.adapters import agent_runner
from learning_os.app import task_ir
from learning_os.app.agent_reporting import encode
from learning_os.store.fingerprint import canonical_fingerprint
from learning_os.store.loader import load_repo

ROOT = Path(__file__).resolve().parents[1]


def _spec(**overrides):
    spec = {"schema_version": 1, "request_id": "task-test-1", "operations": [
        {"id": "inspect-unit", "op": "context.inspect", "unit_id": "unit-demo-l01"},
        {"id": "find-material", "op": "material.find", "unit_id": "unit-demo-l01",
         "stage_id": "stage-demo"},
        {"id": "patch-route", "op": "route.patch", "unit_id": "unit-demo-l01",
         "route_ref": {"from_operation": "find-material", "field": "route_id"},
         "set_fields": {"angle": "A task-ir angle"}}]}
    spec.update(overrides)
    return spec


def _run_reads(plan, root):
    return agent_runner.run_plan(plan, root)


def _receipts(root: Path) -> list[str]:
    tx = root / "operations/transactions"
    return sorted(p.name for p in tx.glob("transaction-*.yaml")) if tx.exists() else []


@pytest.mark.parametrize("mutate", [
    lambda s: s["operations"][0].update(op="context.delete"),
    lambda s: s["operations"][2].update(set_fields={"source_id": "x"}),
    lambda s: s["operations"][2].update(set_fields={"angle": "  "}),
    lambda s: s["operations"][2].update(route_ref={"from_operation": "patch-route", "field": "route_id"}),
    lambda s: s["operations"][2].update(route_ref={"from_operation": "find-material", "field": "snapshot_id"}),
    lambda s: s["operations"][2].update(surprise=True),
    lambda s: s.update(schema_version=2),
    lambda s: s["operations"].append(dict(s["operations"][2], id="patch-two")),
])
def test_spec_rejection(mutate):
    spec = _spec()
    mutate(spec)
    with pytest.raises(task_ir.TaskSpecError):
        task_ir.parse_spec(spec)


def test_expression_references_are_refused():
    spec = _spec()
    spec["operations"][2] = {"id": "patch-route", "op": "route.patch",
                             "unit_id": "unit-demo-l01",
                             "route_id": "$steps.find-material.route_id",
                             "set_fields": {"angle": "x"}}
    with pytest.raises(task_ir.TaskSpecError):
        task_ir.parse_spec(spec)


def test_compilation_is_deterministic_and_derives_requirement():
    spec = task_ir.parse_spec(_spec())
    assert encode(task_ir.compile_spec(spec).plan) == encode(task_ir.compile_spec(spec).plan)
    propose = task_ir.parse_spec({"schema_version": 1, "request_id": "task-test-2",
                                  "operations": [{"id": "propose", "op": "session.propose",
                                                  "unit_id": "unit-demo-l01",
                                                  "stage_id": "stage-demo"}]})
    argv = task_ir.compile_spec(propose).plan["steps"][0]["argv"]
    assert argv[:3] == ["runtime-session", "--requirement", "req-demo-l01-demo"]


def test_workflow_preview_apply_replay_and_isolation(mini_repo, tmp_path):
    repo, rid, smid = material_fixture(mini_repo)
    before_map = copy.deepcopy(repo.module_source_maps["module-demo"])
    before_stage = copy.deepcopy(repo.study_maps[smid].data["stages"][0])
    spec = task_ir.parse_spec(_spec())
    evidence = tmp_path / "evidence"
    fingerprint = canonical_fingerprint(mini_repo)

    preview = task_ir.preview_task(mini_repo, spec, evidence, run_reads=_run_reads)
    assert preview["status"] == "needs_review"
    by_id = {row["id"]: row for row in preview["operations"]}
    assert by_id["find-material"]["outputs"]["route_id"] == rid
    assert by_id["patch-route"]["status"] == "needs_review"
    # Preview purity: zero canonical writes, zero receipts.
    assert canonical_fingerprint(mini_repo) == fingerprint
    assert _receipts(mini_repo) == []

    applied = task_ir.apply_task(mini_repo, spec, evidence)
    assert applied["status"] == "committed"
    assert (mini_repo / applied["receipt"]["receipt_path"]).is_file()
    assert {row["id"]: row for row in applied["operations"]}["patch-route"]["status"] == "committed"

    changed = load_repo(mini_repo)
    route = changed.module_source_maps["module-demo"]["sources"][0]["unit_routes"][0]
    assert route["angle"] == "A task-ir angle"
    # Field isolation: every other route field and the stage override survive.
    for key, value in before_map["sources"][0]["unit_routes"][0].items():
        if key != "angle":
            assert route.get(key) == value
    stage = changed.study_maps[smid].data["stages"][0]
    assert stage["resources"][1]["angle"] == before_stage["resources"][1]["angle"]
    assert stage["resources"][2] == before_stage["resources"][2]
    assert len(_receipts(mini_repo)) == 1

    # Idempotent replay: evidence lookup, no second dispatch, no new receipt.
    replay = task_ir.apply_task(mini_repo, spec, evidence)
    assert replay["status"] == "committed" and replay["resumed"] is True
    assert replay["receipt"]["transaction_id"] == applied["receipt"]["transaction_id"]
    assert len(_receipts(mini_repo)) == 1


def test_unchanged_set_fields_never_dispatch(mini_repo, tmp_path):
    repo, _, _ = material_fixture(mini_repo)
    route = repo.module_source_maps["module-demo"]["sources"][0]["unit_routes"][0]
    raw = _spec()
    raw["operations"][2]["set_fields"] = {"angle": route["angle"]}
    spec = task_ir.parse_spec(raw)
    evidence = tmp_path / "evidence"
    preview = task_ir.preview_task(mini_repo, spec, evidence, run_reads=_run_reads)
    assert preview["status"] == "unchanged"
    applied = task_ir.apply_task(mini_repo, spec, evidence)
    assert applied["status"] == "unchanged"
    assert _receipts(mini_repo) == []


def test_stale_snapshot_refuses_apply(mini_repo, tmp_path):
    repo, rid, smid = material_fixture(mini_repo)
    spec = task_ir.parse_spec(_spec())
    evidence = tmp_path / "evidence"
    assert task_ir.preview_task(mini_repo, spec, evidence, run_reads=_run_reads)["status"] == "needs_review"
    # An unrelated reviewed write moves the snapshot after preview.
    other = task_ir.parse_spec({**_spec(), "request_id": "task-test-other"})
    other_evidence = tmp_path / "other-evidence"
    assert task_ir.preview_task(mini_repo, other, other_evidence, run_reads=_run_reads)["status"] == "needs_review"
    assert task_ir.apply_task(mini_repo, other, other_evidence)["status"] == "committed"
    refused = task_ir.apply_task(mini_repo, spec, evidence)
    assert refused["status"] == "refused"
    assert len(_receipts(mini_repo)) == 1  # only the unrelated write committed


def test_request_id_reuse_with_different_spec_is_an_error(mini_repo, tmp_path):
    material_fixture(mini_repo)
    evidence = tmp_path / "evidence"
    spec = task_ir.parse_spec(_spec())
    task_ir.preview_task(mini_repo, spec, evidence, run_reads=_run_reads)
    changed = _spec()
    changed["operations"][2]["set_fields"] = {"angle": "Another angle"}
    with pytest.raises(task_ir.TaskSpecError, match="different spec"):
        task_ir.apply_task(mini_repo, task_ir.parse_spec(changed), evidence)


def test_interrupted_dispatch_is_uncertain_and_never_redispatched(mini_repo, tmp_path):
    material_fixture(mini_repo)
    spec = task_ir.parse_spec(_spec())
    evidence = tmp_path / "evidence"
    calls = []

    def exploding_submit(root, record, payload, key, request_id):
        calls.append(key)
        raise TimeoutError("lost after dispatch")

    task_ir.preview_task(mini_repo, spec, evidence, run_reads=_run_reads)
    first = task_ir.apply_task(mini_repo, spec, evidence, seal_submit=exploding_submit)
    assert first["status"] == "uncertain"
    second = task_ir.apply_task(mini_repo, spec, evidence, seal_submit=exploding_submit)
    assert second["status"] == "uncertain" and second["resumed"] is True
    assert len(calls) == 1
    assert _receipts(mini_repo) == []


def test_preview_check_failure_is_refused_before_any_dispatch(mini_repo, tmp_path):
    material_fixture(mini_repo)
    spec = task_ir.parse_spec(_spec())
    evidence = tmp_path / "evidence"

    def failing_check(root, payload, key, record_path):
        return 2, "", "seal_envelope: refused by fixture"

    preview = task_ir.preview_task(mini_repo, spec, evidence, run_reads=_run_reads,
                                   seal_check=failing_check)
    assert preview["status"] == "partial"
    assert {r["id"]: r for r in preview["operations"]}["patch-route"]["status"] == "refused"
    assert _receipts(mini_repo) == []


def test_session_propose_without_runtime_target_refuses_cleanly(mini_repo, tmp_path):
    material_fixture(mini_repo)
    spec = task_ir.parse_spec({"schema_version": 1, "request_id": "task-test-3",
                               "operations": [{"id": "propose", "op": "session.propose",
                                               "unit_id": "unit-demo-l01",
                                               "stage_id": "stage-demo"}]})
    preview = task_ir.preview_task(mini_repo, spec, tmp_path / "evidence", run_reads=_run_reads)
    assert preview["operations"][0]["status"] == "refused"


def test_cli_preview_writes_nothing(mini_repo, tmp_path):
    material_fixture(mini_repo)
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(_spec()), encoding="utf-8")
    fingerprint = canonical_fingerprint(mini_repo)
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools/agent_run.py"), "--task", str(spec_path),
         "--root", str(mini_repo), "--evidence-dir", str(tmp_path / "evidence")],
        capture_output=True, text=True, timeout=600)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    report = json.loads(proc.stdout)
    assert report["status"] == "needs_review"
    assert canonical_fingerprint(mini_repo) == fingerprint
    assert _receipts(mini_repo) == []
    verify = run_los(mini_repo, "plan-edit-context", "unit-demo-l01", "--route-id",
                     report["operations"][1]["outputs"]["route_id"])
    assert verify.returncode == 0, verify.stderr
