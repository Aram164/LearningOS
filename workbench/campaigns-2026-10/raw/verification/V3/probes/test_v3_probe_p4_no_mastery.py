"""V3 probe, property 4 (no mastery): derived proposals never declare mastery.

The learner-derivations invariant: "Derived proposals must never declare
mastery or move recorded progress" (system/developer/components/
learner-derivations.md). Every output string of every compiled session is
searched for mastery/understanding vocabulary; with no recorded evidence the
interpreter must report the absence as `unseen`, never as competence.
"""

from __future__ import annotations

import copy
import re

import pytest
import yaml
from repo_builders import _add_material_overview, add_curriculum, write_yaml

from learning_os.derive.learning_runtime import collect_requirements
from learning_os.derive.projection.learner_interpreter import interpret_observations
from learning_os.derive.projection.session_compiler import compile_session
from learning_os.store.loader import load_repo

TARGET = {
    "concept": "concept-expected-value",
    "capability": {"kind": "explain", "operands": ["expectation"]},
    "conditions": ["unfamiliar-example"],
    "evidence_spec": ["explain-reason"],
}

MASTERY_VOCABULARY = re.compile(
    r"\b(master(?:ed|y|ing)?|understand(?:s|ing)?|understood|proficien\w*|"
    r"has learned|knowledgeable|competent|competence)\b", re.IGNORECASE)


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
    for i, (resource, affordance) in enumerate(
            zip(stage["resources"], ["intervention", "evidence", "mixed"], strict=True)):
        resource.update({"route_id": f"route-demo-{i}", "affordance": affordance,
                         "kind": "practise" if i else "read", "scope_triage": "required-now",
                         "vault_path": "work/active/workspace-demo/scratch/activity.md"})
    (mini_repo / "work/active/workspace-demo/scratch/activity.md").write_text("Synthetic task.\n")
    write_yaml(path, data)
    return mini_repo


def _all_strings(node) -> list[str]:
    if isinstance(node, str):
        return [node]
    if isinstance(node, dict):
        return [text for value in node.values() for text in _all_strings(value)]
    if isinstance(node, (list, tuple)):
        return [text for value in node for text in _all_strings(value)]
    return []


@pytest.mark.parametrize("status", ["unseen", "uncertain", "fragile", "unresolved", "demonstrated"])
def test_no_session_output_string_declares_mastery(runtime_root, status):
    repo = load_repo(runtime_root)
    (req,) = collect_requirements(repo)
    session = compile_session(repo, req, {"status": status})
    matches = [text for text in _all_strings(session) if MASTERY_VOCABULARY.search(text)]
    assert matches == [], f"mastery vocabulary in session output: {matches}"


def test_absent_evidence_is_reported_as_absent(runtime_root):
    repo = load_repo(runtime_root)
    (req,) = collect_requirements(repo)
    interpretation = interpret_observations([], req)
    assert interpretation["status"] == "unseen"
    session = compile_session(repo, req, interpretation)
    assert session["current_status"] == "unseen"
    assert session["evidence_ids"] == []
    # The plan must not imply evidence exists: "demonstrated" only appears
    # when the recorded interpretation carries it.
    assert session["plan_status"] != "satisfied"


def test_demonstrated_status_is_the_records_not_a_declaration(runtime_root):
    repo = load_repo(runtime_root)
    (req,) = collect_requirements(repo)
    session = compile_session(repo, req, {"status": "demonstrated"})
    assert session["current_status"] == "demonstrated"
    # The compiler reports the recorded state; it adds no mastery sentence.
    assert session["plan_status"] == "satisfied"
    matches = [text for text in _all_strings(session) if MASTERY_VOCABULARY.search(text)]
    assert matches == [], f"mastery vocabulary in session output: {matches}"


def test_requirement_ir_carries_no_mastery_vocabulary(runtime_root):
    repo = load_repo(runtime_root)
    for req in collect_requirements(repo):
        matches = [text for text in _all_strings(req) if MASTERY_VOCABULARY.search(text)]
        assert matches == [], f"mastery vocabulary in requirement IR: {matches}"
