"""Runtime-annotation review accountability (§19.6, first slice).

A stage carrying runtime semantics (``runtime_target`` or resource
``affordance`` rows) must carry a ``runtime_review`` attestation, and any
later change to the reviewed payload must surface as a warning. The checks
prove attestation plus an unchanged payload — never pedagogical correctness.
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml
from test_curriculum_v2 import _add_material_overview, add_curriculum, write_yaml

from learning_os.learning_runtime import runtime_review_fingerprint
from learning_os.loader import load_repo
from learning_os.rules import validate

MAP = "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"

TARGET = {
    "concept": "concept-expected-value",
    "capability": {"kind": "explain", "operands": ["expectation"]},
    "conditions": ["unfamiliar-example"],
    "evidence_spec": ["explain-reason"],
}


def _review_block(stage: dict) -> dict:
    """The attestation a careful reviewer would attach to this stage."""
    return {
        "reviewed_by": "Aram",
        "reviewed_on": "2026-09-10",
        "fingerprint": runtime_review_fingerprint(stage),
    }


@pytest.fixture
def review_root(mini_repo):
    add_curriculum(mini_repo)
    _add_material_overview(mini_repo)
    path = mini_repo / MAP
    data = yaml.safe_load(path.read_text())
    stage = data["stages"][0]
    stage["concepts"] = ["concept-expected-value"]
    stage["runtime_target"] = copy.deepcopy(TARGET)
    for resource, affordance in zip(stage["resources"], ["intervention", "evidence"], strict=False):
        resource.update({"affordance": affordance})
    write_yaml(path, data)
    return mini_repo


def _stage(root: Path) -> tuple[dict, Path]:
    path = root / MAP
    data = yaml.safe_load(path.read_text())
    return data, path


def _codes(root: Path, code: str) -> list:
    return [i for i in validate(load_repo(root)) if i.code == code]


def test_missing_review_warns(review_root):
    issues = _codes(review_root, "RUNTIME-REVIEW-MISSING")
    assert len(issues) == 1
    assert issues[0].severity == "W"
    assert issues[0].path == MAP
    assert "stage-demo" in issues[0].message


def test_valid_review_is_silent(review_root):
    data, path = _stage(review_root)
    data["stages"][0]["runtime_review"] = _review_block(data["stages"][0])
    write_yaml(path, data)
    assert _codes(review_root, "RUNTIME-REVIEW-MISSING") == []
    assert _codes(review_root, "RUNTIME-REVIEW-STALE") == []


@pytest.mark.parametrize("mutate", [
    pytest.param(lambda s: s["resources"][0].update(affordance="evidence"),
                 id="affordance-flip"),
    pytest.param(lambda s: s["runtime_target"]["evidence_spec"].append("show-steps"),
                 id="evidence-spec-grow"),
    pytest.param(lambda s: s["runtime_target"]["capability"]["operands"].append("variance"),
                 id="capability-operand-grow"),
    pytest.param(lambda s: s.update(id="stage-demo-renamed"),
                 id="stage-id-change"),
])
def test_semantic_change_becomes_stale(review_root, mutate):
    data, path = _stage(review_root)
    data["stages"][0]["runtime_review"] = _review_block(data["stages"][0])
    mutate(data["stages"][0])
    write_yaml(path, data)
    issues = _codes(review_root, "RUNTIME-REVIEW-STALE")
    assert len(issues) == 1
    assert issues[0].severity == "W"
    assert issues[0].path == MAP


@pytest.mark.parametrize("mutate", [
    pytest.param(lambda s: s.update(title="A retitled stage"),
                 id="title-retitle"),
    pytest.param(lambda s: s.update(objective="A reworded objective."),
                 id="objective-reword"),
    pytest.param(lambda s: s.update(estimate_minutes=45),
                 id="estimate-added"),
    pytest.param(lambda s: s["resources"][0].update(locator="Task 1, pp. 2-3"),
                 id="locator-clarified"),
])
def test_unrelated_change_stays_valid(review_root, mutate):
    data, path = _stage(review_root)
    data["stages"][0]["runtime_review"] = _review_block(data["stages"][0])
    mutate(data["stages"][0])
    write_yaml(path, data)
    assert _codes(review_root, "RUNTIME-REVIEW-STALE") == []
    assert _codes(review_root, "RUNTIME-REVIEW-MISSING") == []


def test_fingerprint_is_stable_across_key_order_and_yaml_round_trip(review_root):
    data, _ = _stage(review_root)
    stage = data["stages"][0]
    before = runtime_review_fingerprint(stage)
    reordered = {key: copy.deepcopy(stage[key]) for key in reversed(list(stage))}
    assert runtime_review_fingerprint(reordered) == before
    reloaded = yaml.safe_load(yaml.safe_dump(stage, sort_keys=False))
    assert runtime_review_fingerprint(reloaded) == before
