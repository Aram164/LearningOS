"""V3 probe, property 2 (read-only): derived reads never write anything.

Every derived surface is driven against a fixture repository that is a git
repository with a committed tree; after each probe `git status --porcelain`
must be empty. Any output — canonical or generated — written by a read is a
finding. (The outer git status of the clone is checked by the driver script
after this pytest process exits and recorded in the campaign logs.)
"""

from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path

import pytest
import yaml
from repo_builders import _add_material_overview, add_curriculum, run_los, write_yaml

from learning_os.derive.learning_runtime import (
    collect_requirements,
    read_observations,
    read_stage_results,
    stage_results_for,
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


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(["git", "-C", str(root), *args],
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    return out.stdout


@pytest.fixture
def committed_runtime_root(mini_repo):
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
    for i, (resource, affordance) in enumerate(
            zip(stage["resources"], ["intervention", "evidence", "mixed"], strict=True)):
        resource.update({"route_id": f"route-demo-{i}", "affordance": affordance,
                         "kind": "practise" if i else "read", "scope_triage": "required-now",
                         "vault_path": "work/active/workspace-demo/scratch/activity.md"})
    (mini_repo / "work/active/workspace-demo/scratch/activity.md").write_text("Synthetic task.\n")
    write_yaml(path, data)
    _git(mini_repo, "init", "-q")
    _git(mini_repo, "add", "-A")
    _git(mini_repo, "-c", "user.email=probe@example", "-c", "user.name=probe",
         "commit", "-qm", "fixture")
    return mini_repo


def _requirement(root):
    repo = load_repo(root)
    reqs = collect_requirements(repo)
    assert reqs, "fixture must compile one requirement"
    return repo, reqs[0]


def test_library_derived_reads_write_nothing(committed_runtime_root):
    root = committed_runtime_root
    repo, req = _requirement(root)
    read_observations(repo, [req])
    read_stage_results(repo)
    stage_results_for([], "unit-demo-l01", "stage-demo")
    for status in ("unseen", "uncertain", "fragile", "unresolved", "demonstrated"):
        compile_session(repo, req, {"status": status})
    previous = compile_session(repo, req, {"status": "uncertain"})
    packet = {"contract": "runtime-session-v1", "schema_version": 1,
              "snapshot_id": SNAP, "session": previous}
    replan_session(repo, packet, req, {"status": "uncertain"}, {},
                   "target-changed", SNAP)
    assert _git(root, "status", "--porcelain") == ""


def test_semantic_query_cli_writes_nothing(committed_runtime_root):
    root = committed_runtime_root
    listed = run_los(root, "semantic", "--list")
    assert listed.returncode == 0, listed.stderr
    assert _git(root, "status", "--porcelain") == ""
    verdict = run_los(root, "semantic", "RepoClean",
                      "--input", "error_count=0",
                      "--input", "new_or_grown_warnings=[]")
    assert verdict.returncode == 0, verdict.stderr
    assert _git(root, "status", "--porcelain") == ""
    refused = run_los(root, "semantic", "Nope")
    assert refused.returncode != 0
    assert _git(root, "status", "--porcelain") == ""


def test_semantic_query_cli_unknown_refusal_writes_nothing_json(committed_runtime_root):
    root = committed_runtime_root
    out = run_los(root, "semantic", "RepoClean", "--input", "novalue")
    assert out.returncode != 0
    assert _git(root, "status", "--porcelain") == ""
