"""K1 invariant 5 (ADR-016 decision 3): the generated Canvas draws every strict
edge prerequisite → dependent, keeps the canonical edge id, and renders
semantic edges in canonical direction. The Mermaid concept map must agree."""

from __future__ import annotations

import json

import yaml

from learning_os.derive.projection import generate_all
from learning_os.store.loader import load_repo

STRICT = "concept-variance--builds-on--concept-expected-value"
SEMANTIC = "concept-expected-value--motivates--concept-variance"


def _canvas_repo(mini_repo):
    from repo_builders import write_yaml

    (mini_repo / "knowledge/concept-relations.yaml").write_text(
        yaml.safe_dump({"relations": [
            {"from": "concept-variance", "type": "builds-on",
             "to": "concept-expected-value"},
            {"from": "concept-expected-value", "type": "motivates",
             "to": "concept-variance"},
        ]}, sort_keys=False), encoding="utf-8")
    write_yaml(mini_repo / "knowledge/concepts.yaml", {"concepts": [
        {"id": "concept-expected-value", "label": "Expected value",
         "aliases": ["Erwartungswert"]},
        {"id": "concept-variance", "label": "Variance", "aliases": ["Varianz"]},
    ]})
    return mini_repo


def _canvas(mini_repo):
    outputs = generate_all(load_repo(_canvas_repo(mini_repo)), generated_at="T1")
    return json.loads(outputs["concept-canvas.canvas"])


def test_strict_canvas_edge_points_prerequisite_to_dependent(mini_repo):
    canvas = _canvas(mini_repo)
    edge = next(e for e in canvas["edges"] if e["id"] == STRICT)
    # `variance builds-on expected-value`: expected-value is the prerequisite.
    assert edge["fromNode"] == "concept-expected-value"
    assert edge["toNode"] == "concept-variance"
    assert edge["fromSide"] == "right"
    assert edge["toSide"] == "left"
    assert edge["label"] == "prerequisite for (builds-on)"
    # Identity is preserved: the id keeps the canonical from--type--to spelling.
    assert "--builds-on--" in edge["id"]


def test_semantic_canvas_edge_keeps_canonical_direction(mini_repo):
    canvas = _canvas(mini_repo)
    edge = next(e for e in canvas["edges"] if e["id"] == SEMANTIC)
    assert edge["fromNode"] == "concept-expected-value"
    assert edge["toNode"] == "concept-variance"
    assert edge["fromSide"] == "left"
    assert edge["toSide"] == "right"
    assert edge["label"] == "motivates"


def test_prerequisite_sits_left_of_its_dependent(mini_repo):
    """x = prerequisite depth: the prerequisite's card is further left, so the
    rightward arrow reads as study order."""
    canvas = _canvas(mini_repo)
    nodes = {n["id"]: n for n in canvas["nodes"]}
    assert nodes["concept-expected-value"]["x"] < nodes["concept-variance"]["x"]


def test_mermaid_concept_map_agrees_with_the_canvas(mini_repo):
    """Two projections of one fact must not disagree (ADR-016 decision 3):
    the Mermaid map also draws the strict edge prerequisite -> dependent
    (dotted for builds-on) and excludes semantic edges."""
    outputs = generate_all(load_repo(_canvas_repo(mini_repo)), generated_at="T1")
    mermaid = outputs["concept-map.md"]
    block = mermaid.split("```mermaid", 1)[1].split("```", 1)[0]
    lines = [line.strip() for line in block.strip().splitlines()]
    assert "concept_expected_value -.-> concept_variance" in lines
    assert not any("motivates" in line for line in lines)
