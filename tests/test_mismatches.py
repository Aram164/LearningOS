"""Regression checks for the five delegated mismatch decisions (2026-10-10).

Historical observations stay in architecture/mismatches.yaml. These checks
now exercise the decided behavior ordinarily; setup and command failures
are never hidden by expected-failure handling.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
import yaml
from conftest import build_mini_repo
from gateway_helpers import approved_v2_call, approved_v2_envelope, run_v2_capability
from repo_builders import run_los, write_yaml
from scenario_fixtures import rich_world

from learning_os.fingerprint import canonical_fingerprint
from learning_os.loader import load_repo


def _world(tmp_path: Path) -> Path:
    root = build_mini_repo(tmp_path)
    rich_world(root)
    return root


def _state(root):
    return (canonical_fingerprint(root),
            {p.relative_to(root).as_posix(): p.read_bytes()
             for p in (root / "operations").rglob("*")
             if p.is_file() and not p.is_relative_to(root / "operations/diagnostics")})


@pytest.mark.parametrize("argv,first_clause", [
    (["stage-result", "--workspace", "workspace-demo", "--unit", "unit-demo-l01",
      "--stage", "stage-demo-pending", "--activity", "exercise", "--result", "correct"],
     "stage results require GatewayEnvelopeV2"),
    (["inbox-resolve", "note-drop.md", "--drop-sha256", "sha256:" + "cf" * 32,
      "--routed-to", "note-demo"], "inbox resolve requires GatewayEnvelopeV2"),
])
def test_m01_m02_action_specific_bare_refusal(tmp_path, argv, first_clause):
    root = _world(tmp_path)
    before = _state(root)
    proc = run_los(root, *argv)
    assert proc.returncode == 2, proc.stderr
    assert first_clause in proc.stderr
    assert "direct CLI application is disabled" in proc.stderr
    assert not proc.stdout
    assert _state(root) == before


def _remove(root, unit="unit-demo-l01", locator="lecture-01.pdf", key="wired-remove"):
    return approved_v2_call(root, capability="unit.source-selection.set",
        payload={"unit_id": unit, "source_id": "source-demo-book",
                 "locator": locator, "action": "remove"},
        artifact_ids=[unit], idempotency_key=key)


@pytest.mark.parametrize("representation", ["legacy", "route-id", "material-ref"])
def test_m03_wired_removal_refuses_without_a_transaction(tmp_path, representation):
    root = _world(tmp_path)
    repo = load_repo(root)
    unit = repo.units["unit-demo-l01"]
    rid = unit.data["source_selections"][0]["route_id"]
    assert not unit.data["source_selections"][0].get("stage_ids")
    study_map = repo.study_maps[unit.data["current_study_map"]]
    data = yaml.safe_load(study_map.path.read_text())
    resource = data["stages"][0]["resources"][0]
    # Isolate this representation so a second fixture resource cannot mask it.
    data["stages"][0]["resources"] = [resource]
    resource.update(source_id="source-demo-book", locator="lecture-01.pdf")
    if representation == "legacy":
        resource.pop("route_id", None)
    elif representation == "route-id":
        resource["route_id"] = rid
        resource.pop("locator", None)
    elif representation == "material-ref":
        resource["material_ref"] = {"route_id": rid, "inherit": ["label", "source_id"]}
        resource.pop("route_id", None)
        resource.pop("label", None)
        resource.pop("source_id", None)
        resource["locator"] = "lecture-01.pdf p.1"
    write_yaml(study_map.path, data)
    before = _state(root)
    proc = _remove(root)
    assert proc.returncode == 2, (proc.stdout, proc.stderr)
    doc = json.loads(proc.stdout)
    assert doc["ok"] is False
    assert doc["error"]["code"] == "INVALID_REQUEST"
    assert "used by the current study path" in doc["error"]["message"]
    assert doc["transaction_id"] is None and doc["receipt_path"] is None
    assert _state(root) == before


def test_m03_unused_removal_and_exact_replay(tmp_path):
    root = _world(tmp_path)
    envelope = approved_v2_envelope(root, capability="unit.source-selection.set",
        payload={"unit_id": "unit-demo-l02", "source_id": "source-demo-book",
                 "locator": "lecture-02.pdf", "action": "remove"},
        artifact_ids=["unit-demo-l02"], idempotency_key="unused-remove")
    proc = run_v2_capability(root, envelope)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    response = json.loads(proc.stdout)
    assert response["ok"] is True and response["result"]["selected"] is False
    assert load_repo(root).units["unit-demo-l02"].data["source_selections"] == []
    # Submit the identical approved envelope again, including its original guards.
    before_replay = _state(root)
    replay = run_v2_capability(root, envelope)
    assert replay.returncode == 0, replay.stderr
    replayed = json.loads(replay.stdout)
    assert replayed["replayed"] is True
    assert replayed["transaction_id"] == response["transaction_id"]
    assert _state(root) == before_replay


def test_m03_other_locator_in_current_map_does_not_pin_choice(tmp_path):
    root = _world(tmp_path)
    repo = load_repo(root)
    study_map = repo.study_maps["study-map-demo-l01"]
    data = yaml.safe_load(study_map.path.read_text())
    for stage in data["stages"]:
        for resource in stage.get("resources", []):
            if resource.get("locator") == "lecture-01.pdf":
                resource.pop("route_id", None)
                resource["locator"] = "Appendix A"
    write_yaml(study_map.path, data)
    proc = _remove(root)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert json.loads(proc.stdout)["result"]["selected"] is False


def test_m04_validation_owns_its_report(tmp_path):
    root = _world(tmp_path)
    report = root / "generated/reports/validation-report.md"
    assert not report.exists()
    generation = run_los(root, "generate")
    assert generation.returncode == 0, generation.stderr
    assert (root / "generated/manifest.json").is_file()
    assert not report.exists()
    validation = run_los(root, "validate")
    assert validation.returncode == 0, validation.stdout
    assert report.is_file()


def test_m05_complete_path_workspace_in_place(tmp_path):
    root = _world(tmp_path)
    context = root / "work/active/workspace-demo/CONTEXT.md"
    # Disposable-fixture setup, not an assertion that a completion capability exists.
    text = context.read_text()
    assert "status: active" in text
    context.write_text(text.replace("status: active", "status: complete", 1))
    repo = load_repo(root)
    assert repo.workspaces["workspace-demo"].meta["status"] == "complete"
    assert not repo.learning_paths["path-demo"].archived
    proc = run_los(root, "validate")
    assert proc.returncode == 0, proc.stdout
    assert context.is_file()


def test_m05_unchanged_path_workspace_move_remains_rejected(tmp_path):
    root = _world(tmp_path)
    source = root / "work/active/workspace-demo"
    target = root / "archive/workspaces/2026/workspace-demo"
    target.parent.mkdir(parents=True)
    shutil.move(str(source), str(target))
    before = _state(root)
    proc = run_los(root, "validate")
    assert proc.returncode == 1, proc.stdout
    errors = [line for line in proc.stdout.splitlines() if line.startswith("E ")]
    assert len(errors) == 1 and errors[0].startswith("E PATH-NOTE-OWNER:"), proc.stdout
    assert _state(root) == before
