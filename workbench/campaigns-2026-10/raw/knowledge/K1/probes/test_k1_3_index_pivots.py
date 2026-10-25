"""K1 invariant 3 (ADR-015 decision 3): unit_to_concepts, concept_to_units,
module_to_concepts and concept_to_modules are exact pivots of the published
module_concept_edges — one computation, no independent recomputation."""

from __future__ import annotations

import json

import yaml

from learning_os.derive.projection import generate_all
from learning_os.store.loader import load_repo


def _pivoted_repo(mini_repo):
    """Two stages (one unit, same concept twice) + two nodes carrying the same
    second concept, so every pivot has a duplicate to collapse."""
    from repo_builders import add_curriculum, write_yaml

    add_curriculum(mini_repo)
    map_path = mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
    sm = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    sm["stages"][0]["concepts"] = ["concept-expected-value"]
    sm["stages"].append({
        "id": "stage-demo-2", "title": "Second stage", "status": "active",
        "objective": "Revisit expected value.",
        "done_when": ["Explain it again."], "scope_triage": "required-now",
        "resources": [],
        "working_note": "curriculum/modules/module-demo/units/unit-demo-l01/"
                        "stages/stage-demo-2/notes.md",
        "attachments": [], "source_feedback": [],
        "concepts": ["concept-expected-value"],
    })
    note_rel = ("curriculum/modules/module-demo/units/unit-demo-l01/"
                "stages/stage-demo-2/notes.md")
    (mini_repo / note_rel).parent.mkdir(parents=True, exist_ok=True)
    (mini_repo / note_rel).write_text("", encoding="utf-8")
    write_yaml(map_path, sm)
    unit_path = mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    unit = yaml.safe_load(unit_path.read_text(encoding="utf-8"))
    unit["knowledge_map"] = {
        "summary": "Expected value connects outcomes to probability weights.",
        "nodes": [
            {"id": "knowledge-demo-outcomes", "title": "Outcomes",
             "summary": "A variable maps outcomes to values.",
             "concept_ids": ["concept-variance"]},
            {"id": "knowledge-demo-expectation", "title": "Expectation",
             "summary": "Expectation is a probability-weighted average.",
             "concept_ids": ["concept-variance"]},
        ],
    }
    write_yaml(unit_path, unit)
    return mini_repo


def _expected_pivots(edges):
    module_to_concepts: dict[str, set] = {}
    concept_to_modules: dict[str, set] = {}
    unit_to_concepts: dict[str, set] = {}
    concept_to_units: dict[str, set] = {}
    for edge in edges:
        module_to_concepts.setdefault(edge["module_id"], set()).add(edge["concept_id"])
        concept_to_modules.setdefault(edge["concept_id"], set()).add(edge["module_id"])
        for item in edge["evidence"]:
            unit_to_concepts.setdefault(item["unit_id"], set()).add(edge["concept_id"])
            concept_to_units.setdefault(edge["concept_id"], set()).add(item["unit_id"])
    return (
        {k: sorted(v) for k, v in sorted(module_to_concepts.items())},
        {k: sorted(v) for k, v in sorted(concept_to_modules.items())},
        {k: sorted(v) for k, v in sorted(unit_to_concepts.items())},
        {k: sorted(v) for k, v in sorted(concept_to_units.items())},
    )


def test_all_four_concept_indexes_equal_pivots_of_the_published_edges(mini_repo):
    root = _pivoted_repo(mini_repo)
    manifest = json.loads(generate_all(load_repo(root), generated_at="T1")["manifest.json"])
    edges = manifest["module_concept_edges"]
    assert edges
    exp_m2c, exp_c2m, exp_u2c, exp_c2u = _expected_pivots(edges)
    indexes = manifest["indexes"]
    assert indexes["module_to_concepts"] == exp_m2c
    assert indexes["concept_to_modules"] == exp_c2m
    assert indexes["unit_to_concepts"] == exp_u2c
    assert indexes["concept_to_units"] == exp_c2u
    # The duplicates the fixture plants must actually be collapsed: one unit
    # maps to two concepts, one concept to one unit, each listed once.
    assert indexes["unit_to_concepts"] == {
        "unit-demo-l01": ["concept-expected-value", "concept-variance"]}
    assert indexes["concept_to_units"] == {
        "concept-expected-value": ["unit-demo-l01"],
        "concept-variance": ["unit-demo-l01"]}


def test_indexes_stay_empty_exactly_when_the_edges_are_empty(mini_repo):
    """The repaired-tables regression: no edges ⇒ all four tables are {}
    (and never a stale independent computation)."""
    from repo_builders import add_curriculum

    add_curriculum(mini_repo)
    manifest = json.loads(generate_all(load_repo(mini_repo), generated_at="T1")["manifest.json"])
    assert manifest["module_concept_edges"] == []
    indexes = manifest["indexes"]
    for key in ("unit_to_concepts", "concept_to_units",
                "module_to_concepts", "concept_to_modules"):
        assert indexes[key] == {}, key
