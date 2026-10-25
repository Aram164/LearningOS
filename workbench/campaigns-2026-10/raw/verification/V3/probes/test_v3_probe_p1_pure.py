"""V3 probe, property 1 (pure): same records, byte-identical derived output.

Campaign glm-v-2026-10-25 / V3. Attacks the derived layer
(`derive/learning_runtime.py`, `derive/projection/session_compiler.py`,
`semantic.query`) with mini_repo fixture probes. No findings are asserted
here; each probe pins one purity claim so a violation fails loudly.
"""

from __future__ import annotations

import copy
import json

import pytest
import yaml
from conftest import build_mini_repo
from repo_builders import _add_material_overview, add_curriculum, run_los, write_yaml

from learning_os.derive.learning_runtime import (
    collect_requirements,
    read_observations,
    read_stage_results,
    stage_results_for,
)
from learning_os.derive.projection.session_compiler import compile_session
from learning_os.store.loader import load_repo

TARGET = {
    "concept": "concept-expected-value",
    "capability": {"kind": "explain", "operands": ["expectation"]},
    "conditions": ["unfamiliar-example"],
    "evidence_spec": ["explain-reason"],
}


def _make_runtime(root) -> None:
    add_curriculum(root)
    _add_material_overview(root)
    source_path = root / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(source_path.read_text())
    route = source_map["sources"][0]["unit_routes"][0]
    source_map["sources"][0]["unit_routes"] = [
        {**route, "id": f"route-demo-{i}", "locator": f"Task {i}"} for i in range(3)
    ]
    write_yaml(source_path, source_map)
    unit = root / "curriculum/modules/module-demo/units/unit-demo-l01"
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
    (root / "work/active/workspace-demo/scratch/activity.md").write_text("Synthetic task.\n")
    write_yaml(path, data)


@pytest.fixture
def runtime_root(mini_repo):
    _make_runtime(mini_repo)
    return mini_repo


def _derived(root) -> dict:
    """Everything the derived layer answers for this fixture, one dict."""
    repo = load_repo(root)
    reqs = collect_requirements(repo)
    observations = read_observations(repo, reqs)
    results = read_stage_results(repo)
    return {
        "requirements": reqs,
        "observations": observations,
        "stage_results": results,
        "live_results": stage_results_for(results, "unit-demo-l01", "stage-demo"),
        "session_unseen": compile_session(repo, reqs[0], {"status": "unseen"}),
    }


def _serialized(payload) -> bytes:
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=1).encode()


def test_same_records_two_runs_byte_identical(runtime_root):
    first = _serialized(_derived(runtime_root))
    second = _serialized(_derived(runtime_root))
    assert first == second


def test_two_identically_built_repos_byte_identical(mini_repo, tmp_path):
    _make_runtime(mini_repo)
    # Rebuild the same records in a second, independent fixture root.
    second_base = tmp_path / "second-base"
    second_base.mkdir()
    build_mini_repo(second_base)
    other = second_base / "LearningOS" / "repository"
    _make_runtime(other)
    assert _serialized(_derived(mini_repo)) == _serialized(_derived(other))


def test_unit_order_permutation_leaves_requirements_identical(runtime_root):
    before = collect_requirements(load_repo(runtime_root))
    module_path = runtime_root / "curriculum/modules/module-demo/module.yaml"
    module = yaml.safe_load(module_path.read_text())
    module["unit_order"] = list(reversed(module["unit_order"]))
    write_yaml(module_path, module)
    assert collect_requirements(load_repo(runtime_root)) == before


def test_semantic_query_cli_deterministic(runtime_root):
    first = run_los(runtime_root, "semantic", "--list")
    assert first.returncode == 0, first.stderr
    second = run_los(runtime_root, "semantic", "--list")
    assert first.stdout.encode() == second.stdout.encode()
    argv = ["semantic", "RepoClean", "--input", "error_count=0",
            "--input", "new_or_grown_warnings=[]"]
    one = run_los(runtime_root, *argv)
    two = run_los(runtime_root, *argv)
    assert one.returncode == 0, one.stderr
    assert one.stdout.encode() == two.stdout.encode()
