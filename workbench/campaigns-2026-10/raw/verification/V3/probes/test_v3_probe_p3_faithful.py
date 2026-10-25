"""V3 probe, property 3 (faithful): derived items cite records that exist.

Every compiled requirement must resolve against the records it cites
(unit, module, current study map, stage). Changing an unrelated canonical
record leaves the derived output unchanged; removing a cited record changes
the output or names the loss precisely.
"""

from __future__ import annotations

import copy
import json

import pytest
import yaml
from repo_builders import _add_material_overview, add_curriculum, write_yaml

from learning_os.derive.learning_runtime import (
    RuntimeInputError,
    collect_requirements,
    read_observations,
    read_stage_results,
    requirement_fingerprint,
    requirement_stage,
)
from learning_os.store.loader import load_repo

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
    write_yaml(path, data)
    return mini_repo


def test_every_requirement_resolves_its_citations(runtime_root):
    repo = load_repo(runtime_root)
    reqs = collect_requirements(repo)
    assert reqs
    for req in reqs:
        unit, study_map, stage = requirement_stage(repo, req)
        assert unit.id == req["source_stage"]["unit_id"]
        assert study_map.id == unit.data.get("current_study_map")
        assert stage["id"] == req["source_stage"]["stage_id"]


def test_unrelated_record_change_is_inert(runtime_root):
    before = collect_requirements(load_repo(runtime_root))
    fingerprint = requirement_fingerprint(before[0])
    note = runtime_root / "knowledge/notes/mathematics/note-demo.md"
    note.write_text(note.read_text().replace("Body prose.", "Completely other prose."),
                    encoding="utf-8")
    study_map_path = (runtime_root /
                      "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml")
    data = yaml.safe_load(study_map_path.read_text())
    data["stages"][0]["title"] = "A brand new stage title"
    write_yaml(study_map_path, data)
    after = collect_requirements(load_repo(runtime_root))
    assert after == before
    assert requirement_fingerprint(after[0]) == fingerprint


def test_removing_the_runtime_target_changes_output_and_names_the_loss(runtime_root):
    reqs = collect_requirements(load_repo(runtime_root))
    ledger = runtime_root / "work/active/workspace-demo/observations.jsonl"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text(json.dumps({
        "id": "observation-1", "requirement": reqs[0]["id"], "activity": "route-demo-1",
        "result": "correct", "assistance": "none", "timestamp": "2026-01-01T00:00:00+00:00",
        "conditions": ["unfamiliar-example"], "evidence_tags": ["explain-reason"],
    }) + "\n", encoding="utf-8")
    assert read_observations(load_repo(runtime_root), reqs)
    study_map_path = (runtime_root /
                      "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml")
    data = yaml.safe_load(study_map_path.read_text())
    del data["stages"][0]["runtime_target"]
    write_yaml(study_map_path, data)
    repo = load_repo(runtime_root)
    assert collect_requirements(repo) == []
    with pytest.raises(RuntimeInputError) as excinfo:
        read_observations(repo, [])
    message = str(excinfo.value)
    assert "no stage declares requirement" in message
    assert reqs[0]["id"] in message
    assert "observations.jsonl" in message


def test_stage_result_citing_gone_stage_names_stage_and_unit(runtime_root):
    ledger = runtime_root / "work/active/workspace-demo/stage-results.jsonl"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text(json.dumps({
        "id": "stage-result-1", "unit": "unit-demo-l01", "stage": "stage-vanished",
        "activity": "route-demo-1", "result": "correct",
        "timestamp": "2026-01-01T00:00:00+00:00",
    }) + "\n", encoding="utf-8")
    with pytest.raises(RuntimeInputError) as excinfo:
        read_stage_results(load_repo(runtime_root))
    message = str(excinfo.value)
    assert "stage-vanished" in message
    assert "unit-demo-l01" in message


def test_requirement_citing_unknown_concept_is_refused_by_name(runtime_root):
    study_map_path = (runtime_root /
                      "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml")
    data = yaml.safe_load(study_map_path.read_text())
    data["stages"][0]["runtime_target"]["concept"] = "concept-unknown"
    write_yaml(study_map_path, data)
    with pytest.raises(RuntimeInputError) as excinfo:
        collect_requirements(load_repo(runtime_root))
    assert "concept-unknown" in str(excinfo.value)
