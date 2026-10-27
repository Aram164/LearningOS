"""Task IR P1: typed compilation, reviewed preview, one guarded write."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from repo_builders import material_fixture, run_los, write_yaml

from learning_os.adapters import agent_runner
from learning_os.app import task_ir
from learning_os.app.agent_reporting import encode
from learning_os.derive.learning_runtime import collect_requirements, requirement_id_for
from learning_os.store.fingerprint import canonical_fingerprint
from learning_os.store.fingerprint import snapshot as current_snapshot
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
    expected_map = copy.deepcopy(before_map)
    expected_map["sources"][0]["unit_routes"][0].update(angle="A task-ir angle", id=rid)
    assert changed.module_source_maps["module-demo"] == expected_map
    assert {k: v for k, v in stage.items() if k != "resources"} == {
        k: v for k, v in before_stage.items() if k != "resources"}
    assert applied["operations"][-1]["outputs"]["transaction_id"] == applied["receipt"]["transaction_id"]
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

    def exploding_submit(root, content):
        calls.append(json.loads(content)["idempotency_key"])
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

    def failing_check(root, payload, key, record_path, session_id):
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


@pytest.mark.parametrize("phase", ["preview", "apply"])
@pytest.mark.parametrize("destination", ["evidence", "temporary", "check"])
def test_evidence_symlinks_never_touch_canonical_files(mini_repo, tmp_path, phase, destination):
    material_fixture(mini_repo)
    spec = task_ir.parse_spec(_spec())
    directory = tmp_path / "evidence"
    directory.mkdir()
    if phase == "apply":
        assert task_ir.preview_task(mini_repo, spec, directory,
                                    run_reads=_run_reads)["status"] == "needs_review"
    # The request evidence uses a hashed name, separate from its check record.
    evidence_path = directory / f"task-{hashlib.sha256(spec.request_id.encode()).hexdigest()[:32]}.json"
    paths = {"evidence": evidence_path,
             "temporary": evidence_path.with_name(f".{evidence_path.name}.tmp"),
             "check": directory / f"task-{spec.request_id}-patch-route.check.json"}
    redirected = paths[destination]
    redirected.unlink(missing_ok=True)
    redirected.symlink_to(mini_repo / "sources/sources.yaml")
    before = canonical_fingerprint(mini_repo)
    calls = []

    def submit(*args):
        calls.append(args)
        pytest.fail("redirected evidence must be refused before submission")

    with pytest.raises(task_ir.TaskSpecError, match="symlink") as exc:
        if phase == "preview":
            task_ir.preview_task(mini_repo, spec, directory, run_reads=_run_reads)
        else:
            task_ir.apply_task(mini_repo, spec, directory, seal_submit=submit)
    assert exc.value.code == "TASK_IR_EVIDENCE"
    assert calls == []
    assert canonical_fingerprint(mini_repo) == before
    assert _receipts(mini_repo) == []


def test_evidence_directory_cannot_resolve_into_data_root(mini_repo, tmp_path):
    material_fixture(mini_repo)
    spec = task_ir.parse_spec(_spec())
    directory = tmp_path / "redirected-evidence"
    directory.symlink_to(mini_repo, target_is_directory=True)
    before = canonical_fingerprint(mini_repo)
    for phase in (task_ir.preview_task, task_ir.apply_task):
        kwargs = {"run_reads": _run_reads} if phase is task_ir.preview_task else {}
        with pytest.raises(task_ir.TaskSpecError, match="outside the data root"):
            phase(mini_repo, spec, directory, **kwargs)
    assert canonical_fingerprint(mini_repo) == before
    assert _receipts(mini_repo) == []


def test_failed_checkpoint_publication_prevents_dispatch_and_keeps_preview(mini_repo, tmp_path, monkeypatch):
    from learning_os.store import transactions

    material_fixture(mini_repo)
    spec = task_ir.parse_spec(_spec())
    directory = tmp_path / "evidence"
    assert task_ir.preview_task(mini_repo, spec, directory,
                                run_reads=_run_reads)["status"] == "needs_review"
    evidence_path = next(path for path in directory.glob("task-*.json")
                         if not path.name.endswith((".check.json", ".envelope.json")))
    before_bytes = evidence_path.read_bytes()
    before = canonical_fingerprint(mini_repo)
    calls = []
    replace = transactions.os.replace

    def fail_publication(source, target):
        if target == evidence_path:
            raise OSError("simulated interruption before checkpoint publication")
        return replace(source, target)

    def submit(*args):
        calls.append(args)
        pytest.fail("dispatch must wait for its durable checkpoint")

    with monkeypatch.context() as patch:
        patch.setattr(transactions.os, "replace", fail_publication)
        with pytest.raises(task_ir.TaskSpecError, match="could not be persisted") as exc:
            task_ir.apply_task(mini_repo, spec, directory, seal_submit=submit)
        assert exc.value.code == "TASK_IR_EVIDENCE"
    assert calls == []
    assert evidence_path.read_bytes() == before_bytes
    assert canonical_fingerprint(mini_repo) == before
    assert _receipts(mini_repo) == []
    assert task_ir.apply_task(mini_repo, spec, directory)["status"] == "committed"
    assert len(_receipts(mini_repo)) == 1


def test_earlier_relative_check_record_still_applies(mini_repo, tmp_path, monkeypatch):
    material_fixture(mini_repo)
    spec = task_ir.parse_spec(_spec())
    monkeypatch.chdir(tmp_path)
    (tmp_path / "nested").mkdir()
    directory = Path("nested/../evidence")
    assert task_ir.preview_task(mini_repo, spec, directory,
                                run_reads=_run_reads)["status"] == "needs_review"
    evidence_path = next(path for path in directory.glob("task-*.json")
                         if not path.name.endswith((".check.json", ".envelope.json")))
    evidence = json.loads(evidence_path.read_text())
    # The preceding implementation persisted the caller's relative spelling.
    evidence["check_record"] = str(directory / Path(evidence["check_record"]).name)
    evidence_path.write_text(json.dumps(evidence))
    assert task_ir.apply_task(mini_repo, spec, directory)["status"] == "committed"
    assert len(_receipts(mini_repo)) == 1


def _state(directory):
    path = next(path for path in directory.glob("task-*.json")
                if not path.name.endswith((".check.json", ".envelope.json")))
    return path, json.loads(path.read_text())


@pytest.mark.parametrize("op,fields", [
    ("context.inspect", {"unit_id": "unit-demo-l01"}),
    ("material.find", {"unit_id": "unit-demo-l01"}),
    ("session.propose", {"unit_id": "unit-demo-l01", "stage_id": "stage-demo"}),
])
def test_every_read_operation_refuses_undeclared_fields(op, fields):
    with pytest.raises(task_ir.TaskSpecError, match="undeclared"):
        task_ir.parse_spec({"schema_version": 1, "request_id": "closed-read", "operations": [
            {"id": "read", "op": op, **fields, "surprise": True}]})


@pytest.mark.parametrize("invalid", [True, "1", 1.0])
def test_schema_version_is_an_integer_contract(invalid):
    with pytest.raises(task_ir.TaskSpecError):
        task_ir.parse_spec(_spec(schema_version=invalid))


def test_cli_successful_reads_expose_bounded_context_and_snapshot(mini_repo, tmp_path):
    material_fixture(mini_repo)
    raw = _spec()
    raw["operations"].pop()
    source = tmp_path / "read.json"
    source.write_text(json.dumps(raw))
    before = canonical_fingerprint(mini_repo)
    proc = subprocess.run([sys.executable, str(ROOT / "tools/agent_run.py"), "--task", str(source),
                           "--root", str(mini_repo), "--evidence-dir", str(tmp_path / "evidence")],
                          capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    result = json.loads(proc.stdout)
    assert result["status"] == "ok"
    inspect, materials = [row["outputs"] for row in result["operations"]]
    assert inspect["context"]["title"] == "Expected value"
    assert inspect["snapshot_id"] == materials["snapshot_id"] == current_snapshot(mini_repo)
    assert materials["complete"] is True
    resources = materials["materials"]["stage"]["resources"]
    assert len(resources) == 3  # Distinct authored placements survive route-id deduplication.
    assert resources[0]["source_id"] == "source-demo-book"
    assert resources[0]["angle"] != resources[1]["angle"]
    assert canonical_fingerprint(mini_repo) == before
    assert not _receipts(mini_repo)


@pytest.mark.parametrize("target", ["valid", "missing", "invalid"])
def test_session_proposal_uses_authored_runtime_and_preserves_learner_authority(mini_repo, tmp_path, target):
    repo, _, smid = material_fixture(mini_repo)
    path = repo.study_maps[smid].path
    data = yaml.safe_load(path.read_text())
    authored = {"concept": "concept-expected-value",
                "capability": {"kind": "explain", "operands": ["expectation"]},
                "conditions": ["unfamiliar-example"], "evidence_spec": ["explain-reason"]}
    if target != "missing":
        data["stages"][0]["runtime_target"] = {**authored, **({"evidence_spec": []} if target == "invalid" else {})}
        write_yaml(path, data)
    spec = task_ir.parse_spec({"schema_version": 1, "request_id": "runtime-proposal", "operations": [
        {"id": "propose", "op": "session.propose", "unit_id": "unit-demo-l01", "stage_id": "stage-demo"}]})
    before = canonical_fingerprint(mini_repo)
    report = task_ir.preview_task(mini_repo, spec, tmp_path / "evidence", run_reads=_run_reads)
    if target == "valid":
        requirement, = collect_requirements(load_repo(mini_repo))
        expected_id = requirement_id_for("unit-demo-l01", "stage-demo")
        assert requirement["id"] == expected_id == "req-demo-l01-demo"
        assert requirement["source_stage"] == {"module_id": "module-demo", "unit_id": "unit-demo-l01", "stage_id": "stage-demo"}
        assert report["status"] == "ok"
        outputs = report["operations"][0]["outputs"]
        assert outputs["requirement_id"] == expected_id
        assert outputs["snapshot_id"] == current_snapshot(mini_repo)
        proposal = outputs["proposal"]
        direct = run_los(mini_repo, "runtime-session", "--requirement", expected_id)
        assert direct.returncode == 0, direct.stderr
        assert proposal == json.loads(direct.stdout)
        assert proposal["contract"] == "runtime-session-v1"
        assert proposal["session"]["source_stage"] == requirement["source_stage"]
        assert proposal["session"]["current_status"] == "unseen"
        assert proposal["session"]["evidence_ids"] == []
        assert proposal["session"]["target_requirement_id"] == expected_id
        assert collect_requirements(load_repo(mini_repo)) == [requirement]
    else:
        assert report["status"] == "refused"
        assert report["operations"][0]["status"] == "refused"
    assert canonical_fingerprint(mini_repo) == before
    assert not _receipts(mini_repo)


@pytest.mark.parametrize("artifact,mutation", [
    ("check", "missing"), ("check", "invalid"), ("check", "payload"),
    ("envelope", "missing"), ("envelope", "payload"), ("envelope", "route"),
    ("envelope", "unit"), ("envelope", "approval"),
    ("state", "payload"), ("state", "route"), ("state", "unit"), ("state", "key"),
])
def test_review_artifact_substitution_refuses_before_dispatch(mini_repo, tmp_path, artifact, mutation):
    material_fixture(mini_repo)
    spec = task_ir.parse_spec(_spec())
    directory = tmp_path / "evidence"
    assert task_ir.preview_task(mini_repo, spec, directory, run_reads=_run_reads)["status"] == "needs_review"
    state_path, state = _state(directory)
    selected = state_path if artifact == "state" else directory / f"task-{spec.request_id}-patch-route.{artifact}.json"
    value = json.loads(selected.read_text())
    if mutation == "missing":
        selected.unlink()
    elif mutation == "invalid":
        selected.write_text("not-json")
    else:
        payload = value if artifact == "state" else value.get("payload", value)
        if mutation == "payload":
            if artifact == "state":
                value["payload"]["changes"]["angle"] = "substituted"
            else:
                payload["changes"]["angle"] = "substituted"
        elif mutation == "route":
            payload["route_id"] = "route-another"
        elif mutation == "unit":
            if artifact == "state":
                value["payload"]["unit_id"] = "unit-another"
            else:
                payload["unit_id"] = "unit-another"
        elif mutation == "key":
            value["key"] = "another-key"
        else:
            value["approval"]["kind"] = "direct-user-gesture"
        selected.write_text(json.dumps(value))
    before = canonical_fingerprint(mini_repo)

    def forbidden(*args):
        pytest.fail("unreviewed substitution reached dispatch")

    with pytest.raises(task_ir.TaskSpecError):
        task_ir.apply_task(mini_repo, spec, directory, seal_submit=forbidden)
    assert canonical_fingerprint(mini_repo) == before
    assert not _receipts(mini_repo)


def test_stale_artifact_revision_refuses_without_a_snapshot_change(mini_repo, tmp_path):
    from learning_os.store.revisions import dump_revisions

    material_fixture(mini_repo)
    spec = task_ir.parse_spec(_spec())
    directory = tmp_path / "evidence"
    task_ir.preview_task(mini_repo, spec, directory, run_reads=_run_reads)
    _, state = _state(directory)
    envelope = json.loads(next(directory.glob("*.envelope.json")).read_text())
    artifact, revision = next(iter(envelope["expected_revisions"].items()))
    before = canonical_fingerprint(mini_repo)
    target = mini_repo / "operations/transactions/revisions.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(dump_revisions({artifact: revision + 1}))
    assert canonical_fingerprint(mini_repo) == before
    responses = []

    def submit(root, content):
        result = task_ir.default_seal_submit(root, content)
        responses.append(json.loads(result[1]))
        return result

    assert task_ir.apply_task(mini_repo, spec, directory, seal_submit=submit)["status"] == "refused"
    assert responses[0]["error"]["code"] == "REVISION_CONFLICT"
    assert not _receipts(mini_repo)
    assert canonical_fingerprint(mini_repo) == before
    assert state["payload"]["changes"] == {"angle": "A task-ir angle"}


def test_lost_committed_response_reconciles_the_original_envelope(mini_repo, tmp_path):
    material_fixture(mini_repo)
    spec = task_ir.parse_spec(_spec())
    directory = tmp_path / "evidence"
    preview = task_ir.preview_task(mini_repo, spec, directory, run_reads=_run_reads)
    assert preview["status"] == "needs_review"
    original = next(directory.glob("*.envelope.json")).read_bytes()
    submitted, replayed = [], []

    def lost_response(root, content):
        submitted.append(content)
        code, out, err = task_ir.default_seal_submit(root, content)
        assert code == 0, err
        raise TimeoutError("reply lost after the real commit")

    assert task_ir.apply_task(mini_repo, spec, directory, seal_submit=lost_response)["status"] == "uncertain"
    after_commit = canonical_fingerprint(mini_repo)
    _, before = _state(directory)
    assert task_ir.preview_task(mini_repo, spec, directory, run_reads=_run_reads)["status"] == "uncertain"
    assert _state(directory)[1] == before

    def replay(root, content):
        replayed.append(content)
        return task_ir.default_seal_replay(root, content)

    def forbidden(*args):
        pytest.fail("uncertain write was blindly resubmitted")

    recovered = task_ir.apply_task(mini_repo, spec, directory, seal_submit=forbidden, seal_replay=replay)
    repeated = task_ir.apply_task(mini_repo, spec, directory, seal_submit=forbidden, seal_replay=replay)
    assert recovered["status"] == repeated["status"] == "committed"
    assert recovered["receipt"] == repeated["receipt"]
    assert recovered["receipt"]["replayed"] is True
    assert submitted == [original]
    assert replayed == [original, original]
    assert next(directory.glob("*.envelope.json")).read_bytes() == original
    assert len(_receipts(mini_repo)) == 1
    assert canonical_fingerprint(mini_repo) == after_commit


@pytest.mark.parametrize("commit_before_exit", [False, True])
def test_abrupt_process_exit_preserves_dispatched_evidence(mini_repo, tmp_path, commit_before_exit):
    material_fixture(mini_repo)
    raw = _spec()
    spec = task_ir.parse_spec(raw)
    directory = tmp_path / "evidence"
    task_ir.preview_task(mini_repo, spec, directory, run_reads=_run_reads)
    source = tmp_path / "spec.json"
    source.write_text(json.dumps(raw))
    program = '''
import json, os, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from learning_os.app import task_ir
def interrupted(root, content):
    if sys.argv[5] == "yes":
        code, out, err = task_ir.default_seal_submit(root, content)
        assert code == 0, err
    os._exit(19)
spec = task_ir.parse_spec(json.loads(Path(sys.argv[3]).read_text()))
task_ir.apply_task(Path(sys.argv[2]), spec, Path(sys.argv[4]), seal_submit=interrupted)
'''
    proc = subprocess.run([sys.executable, "-c", program, str(ROOT / "tools"), str(mini_repo),
                           str(source), str(directory), "yes" if commit_before_exit else "no"],
                          capture_output=True, text=True, timeout=60)
    assert proc.returncode == 19, proc.stdout + proc.stderr
    state_path, state = _state(directory)
    assert state["status"] == "dispatched"
    before = state_path.read_bytes()
    assert task_ir.preview_task(mini_repo, spec, directory, run_reads=_run_reads)["status"] == "dispatched"
    assert state_path.read_bytes() == before
    result = task_ir.apply_task(mini_repo, spec, directory)
    assert result["status"] == ("committed" if commit_before_exit else "uncertain")
    assert len(_receipts(mini_repo)) == int(commit_before_exit)


def test_conflicting_payload_under_a_committed_key_is_refused(mini_repo, tmp_path):
    material_fixture(mini_repo)
    first = task_ir.parse_spec(_spec())
    directory = tmp_path / "first"
    task_ir.preview_task(mini_repo, first, directory, run_reads=_run_reads)
    committed = task_ir.apply_task(mini_repo, first, directory)
    assert committed["status"] == "committed"
    changed = _spec()
    changed["operations"][2]["set_fields"] = {"angle": "Conflicting new intent"}
    second = task_ir.parse_spec(changed)
    other = tmp_path / "second"
    assert task_ir.preview_task(mini_repo, second, other, run_reads=_run_reads)["status"] == "needs_review"
    after_commit = canonical_fingerprint(mini_repo)
    result = task_ir.apply_task(mini_repo, second, other)
    assert result["status"] == "refused"
    assert len(_receipts(mini_repo)) == 1
    assert canonical_fingerprint(mini_repo) == after_commit


def test_operator_seal_does_not_claim_authenticated_human_approval(mini_repo, tmp_path):
    material_fixture(mini_repo)
    spec = task_ir.parse_spec(_spec())
    directory = tmp_path / "evidence"
    report = task_ir.preview_task(mini_repo, spec, directory, run_reads=_run_reads)
    envelope = json.loads(next(directory.glob("*.envelope.json")).read_text())
    assert envelope["channel"] == "operator"
    assert envelope["approval"]["kind"] == "operator-approval"
    assert envelope["session_id"] == spec.session_id
    assert report["operations"][-1]["outputs"]["changes"] == spec.operations[-1].set_fields
    assert "direct-user-gesture" not in json.dumps(report)
    assert "human_approved" not in json.dumps(report)
    assert not _receipts(mini_repo)


def test_truncated_material_discovery_retains_expansion_and_cannot_bind(mini_repo, tmp_path):
    repo, _, smid = material_fixture(mini_repo)
    data = copy.deepcopy(repo.study_maps[smid].data)
    data["stages"][0]["resources"][0]["angle_detail"] = "Long authored explanation. " * 1000
    write_yaml(repo.study_maps[smid].path, data)
    spec = task_ir.parse_spec(_spec())
    before = canonical_fingerprint(mini_repo)
    report = task_ir.preview_task(mini_repo, spec, tmp_path / "evidence", run_reads=_run_reads)
    assert report["status"] == "partial"
    material = report["operations"][1]["outputs"]
    assert material["complete"] is False
    assert material["route_id"] is None
    assert material["materials"]["_truncated_bytes"] > 8000
    expanded = subprocess.run(material["expand_argv"], capture_output=True, text=True, timeout=60)
    assert expanded.returncode == 0, expanded.stdout + expanded.stderr
    full = json.loads(expanded.stdout)
    original = json.loads(full["steps"][0]["raw"]["stdout"])
    assert len(original["stage"]["resources"]) == 3
    assert original["stage"]["resources"][0]["route_id"]
    assert canonical_fingerprint(mini_repo) == before
    assert not _receipts(mini_repo)


@pytest.mark.parametrize("attempt", ["route-in-another-unit", "stage-in-another-unit"])
def test_unit_and_stage_scope_mismatches_refuse(mini_repo, tmp_path, attempt):
    from learning_os.derive.validation import validate

    repo, route_id, _ = material_fixture(mini_repo)
    other_unit = copy.deepcopy(repo.units["unit-demo-l01"].data)
    other_unit.update(id="unit-demo-l02", title="Another unit", order=2,
                      status="archived", source_selections=[])
    other_unit.pop("current_study_map")
    path = mini_repo / "curriculum/modules/module-demo/module.yaml"
    module = yaml.safe_load(path.read_text())
    module["unit_order"].append("unit-demo-l02")
    write_yaml(path, module)
    write_yaml(path.parent / "units/unit-demo-l02/unit.yaml", other_unit)
    assert not [issue for issue in validate(load_repo(mini_repo)) if issue.severity == "error"]
    if attempt == "route-in-another-unit":
        operations = [{"id": "patch", "op": "route.patch", "unit_id": "unit-demo-l02",
                       "route_id": route_id, "set_fields": {"angle": "Cross-unit attempt"}}]
    else:
        operations = [{"id": "find", "op": "material.find", "unit_id": "unit-demo-l02", "stage_id": "stage-demo"},
                      {"id": "patch", "op": "route.patch", "unit_id": "unit-demo-l01",
                       "route_ref": {"from_operation": "find", "field": "route_id"},
                       "set_fields": {"angle": "Cross-stage attempt"}}]
    spec = task_ir.parse_spec({"schema_version": 1, "request_id": "scope-test", "operations": operations})
    before = canonical_fingerprint(mini_repo)
    report = task_ir.preview_task(mini_repo, spec, tmp_path / "evidence", run_reads=_run_reads)
    assert report["status"] == "partial"
    assert report["operations"][-1]["status"] == "refused"
    assert canonical_fingerprint(mini_repo) == before
    assert not _receipts(mini_repo)


def test_read_epoch_change_refuses_instead_of_attaching_a_fresh_snapshot(mini_repo, tmp_path):
    material_fixture(mini_repo)
    spec = task_ir.parse_spec(_spec())

    def changing_reads(plan, root):
        report = _run_reads(plan, root)
        path = root / "knowledge/notes/mathematics/note-demo.md"
        path.write_text(path.read_text() + "\nSynthetic concurrent change.\n")
        return report

    with pytest.raises(task_ir.TaskSpecError, match="snapshot changed") as exc:
        task_ir.preview_task(mini_repo, spec, tmp_path / "evidence", run_reads=changing_reads)
    assert exc.value.code == "TASK_IR_STALE_READ"
    assert not _receipts(mini_repo)


@pytest.mark.parametrize("field,value", [
    ("channel", "ui"), ("session_id", "another-session"),
    ("request_id", "another-request"), ("idempotency_key", "another-key"),
    ("approval", {"kind": "direct-user-gesture"}),
])
def test_rehashed_envelope_cannot_change_scope_or_claim_human_authority(mini_repo, tmp_path, field, value):
    from learning_os.store.contracts.gateway import intent_sha256

    material_fixture(mini_repo)
    spec = task_ir.parse_spec(_spec())
    directory = tmp_path / "evidence"
    task_ir.preview_task(mini_repo, spec, directory, run_reads=_run_reads)
    path = next(directory.glob("*.envelope.json"))
    envelope = json.loads(path.read_text())
    envelope[field] = value
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    path.write_text(json.dumps(envelope))
    state_path, state = _state(directory)
    state["envelope_sha256"] = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    state_path.write_text(json.dumps(state))
    with pytest.raises(task_ir.TaskSpecError):
        task_ir.apply_task(mini_repo, spec, directory)
    assert not _receipts(mini_repo)


@pytest.mark.parametrize("field,value", [("schema", 2), ("ok", False), ("capability", "capture.create")])
def test_rehashed_invalid_check_record_is_still_refused(mini_repo, tmp_path, field, value):
    material_fixture(mini_repo)
    spec = task_ir.parse_spec(_spec())
    directory = tmp_path / "evidence"
    task_ir.preview_task(mini_repo, spec, directory, run_reads=_run_reads)
    state_path, state = _state(directory)
    check_path = Path(state["check_record"])
    check = json.loads(check_path.read_text())
    check[field] = value
    check_path.write_text(json.dumps(check))
    state["check_sha256"] = "sha256:" + hashlib.sha256(check_path.read_bytes()).hexdigest()
    state_path.write_text(json.dumps(state))
    with pytest.raises(task_ir.TaskSpecError):
        task_ir.apply_task(mini_repo, spec, directory)
    assert not _receipts(mini_repo)


def test_missing_original_after_interruption_cannot_be_resealed(mini_repo, tmp_path, monkeypatch):
    material_fixture(mini_repo)
    spec = task_ir.parse_spec(_spec())
    directory = tmp_path / "evidence"
    task_ir.preview_task(mini_repo, spec, directory, run_reads=_run_reads)
    state_path, state = _state(directory)
    state["status"] = "dispatched"
    state_path.write_text(json.dumps(state))
    next(directory.glob("*.envelope.json")).unlink()

    def forbidden(*args):
        pytest.fail("an interrupted request must never be resealed or blindly submitted")

    monkeypatch.setattr(task_ir, "_run_seal", forbidden)
    result = task_ir.apply_task(mini_repo, spec, directory, seal_submit=forbidden)
    assert result["status"] == "uncertain"
    assert result["operations"][-1]["status"] == "uncertain"
    assert not _receipts(mini_repo)


def test_success_without_real_commit_evidence_remains_uncertain(mini_repo, tmp_path):
    material_fixture(mini_repo)
    spec = task_ir.parse_spec(_spec())
    directory = tmp_path / "evidence"
    task_ir.preview_task(mini_repo, spec, directory, run_reads=_run_reads)
    report = task_ir.apply_task(mini_repo, spec, directory,
                                seal_submit=lambda root, content: (0, '{"receipt_path":"invented.yaml"}', ""))
    assert report["status"] == "uncertain"
    assert "receipt" not in report
    assert task_ir.apply_task(mini_repo, spec, directory)["status"] == "uncertain"
    assert not _receipts(mini_repo)


def test_request_id_containing_check_suffix_keeps_one_artifact_stem(mini_repo, tmp_path):
    material_fixture(mini_repo)
    spec = task_ir.parse_spec(_spec(request_id="a.check.json"))
    directory = tmp_path / "evidence"
    assert task_ir.preview_task(mini_repo, spec, directory, run_reads=_run_reads)["status"] == "needs_review"
    assert (directory / "task-a.check.json-patch-route.envelope.json").is_file()
    assert task_ir.apply_task(mini_repo, spec, directory)["status"] == "committed"
    assert len(_receipts(mini_repo)) == 1


def test_unknown_unit_cannot_spoof_an_unchanged_result_through_error_text(mini_repo, tmp_path):
    _, route_id, _ = material_fixture(mini_repo)
    spec = task_ir.parse_spec({"schema_version": 1, "request_id": "spoof-no-change", "operations": [
        {"id": "patch", "op": "route.patch", "unit_id": "unit-no material changes to apply",
         "route_id": route_id, "set_fields": {"angle": "Not a valid scoped edit"}}]})
    before = canonical_fingerprint(mini_repo)
    report = task_ir.preview_task(mini_repo, spec, tmp_path / "evidence", run_reads=_run_reads)
    assert report["status"] == "partial"
    assert report["operations"][0]["status"] == "refused"
    assert canonical_fingerprint(mini_repo) == before
    assert not _receipts(mini_repo)


@pytest.mark.parametrize("destination", ["check", "temporary"])
def test_hard_linked_output_cannot_overwrite_canonical_data(mini_repo, tmp_path, destination):
    material_fixture(mini_repo)
    spec = task_ir.parse_spec(_spec())
    directory = tmp_path / "evidence"
    directory.mkdir()
    stem = hashlib.sha256(spec.request_id.encode()).hexdigest()[:32]
    path = (directory / f"task-{spec.request_id}-patch-route.check.json" if destination == "check"
            else directory / f".task-{stem}.json.tmp")
    canonical = mini_repo / "sources/sources.yaml"
    original = canonical.read_bytes()
    os.link(canonical, path)
    before = canonical_fingerprint(mini_repo)
    with pytest.raises(task_ir.TaskSpecError, match="hard links"):
        task_ir.preview_task(mini_repo, spec, directory, run_reads=_run_reads)
    assert canonical.read_bytes() == original
    assert canonical_fingerprint(mini_repo) == before
    assert not _receipts(mini_repo)
