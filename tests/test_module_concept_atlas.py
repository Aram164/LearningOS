"""The crossing is exactly as licensed as ADR-015 says, and no more.

The risk this projection carries is not that it breaks — it is that it fills up
with relationships nobody authored, and stays plausible while doing it. Most of
what follows is therefore about what must NOT appear.
"""

from __future__ import annotations

import json

import pytest

from learning_os.genout.projection.atlas import (
    build_module_concept_edges,
    cross_module_concepts,
)

CONCEPTS = {"concept-backprop": {}, "concept-bias-variance": {}, "concept-kernels": {}}
MODULES = [{"id": "module-aml"}, {"id": "module-sad"}]


def _stage(module, unit, study_map, stage, concepts):
    return {"module_id": module, "unit_id": unit, "study_map_id": study_map,
            "id": stage, "concepts": concepts}


def _unit(module, unit, nodes):
    return {"id": unit, "module_id": module,
            "knowledge_map": {"summary": "s", "nodes": nodes}}


def _build(**kw):
    return build_module_concept_edges(
        modules=kw.get("modules", MODULES),
        units=kw.get("units", []),
        stages=kw.get("stages", []),
        concepts=kw.get("concepts", CONCEPTS),
    )


# ---- what licenses an edge -------------------------------------------------

def test_a_stage_concept_tag_makes_an_edge_carrying_stage_identity():
    edges = _build(stages=[
        _stage("module-aml", "unit-aml-l07", "study-map-aml-l07",
               "stage-aml-l07-a", ["concept-backprop"]),
    ])
    assert edges == [{
        "module_id": "module-aml",
        "concept_id": "concept-backprop",
        "evidence": [{"kind": "stage-concept", "unit_id": "unit-aml-l07",
                      "study_map_id": "study-map-aml-l07",
                      "stage_id": "stage-aml-l07-a"}],
    }]


def test_a_knowledge_node_concept_id_makes_an_edge_carrying_node_identity():
    edges = _build(units=[
        _unit("module-sad", "unit-sad-l11",
              [{"id": "knowledge-knn", "title": "t", "summary": "s",
                "concept_ids": ["concept-kernels"]}]),
    ])
    assert edges[0]["evidence"] == [
        {"kind": "knowledge-node", "unit_id": "unit-sad-l11", "node_id": "knowledge-knn"},
    ]


def test_both_sources_merge_into_one_edge():
    edges = _build(
        stages=[_stage("module-aml", "unit-aml-l07", "study-map-aml-l07",
                       "stage-a", ["concept-backprop"])],
        units=[_unit("module-aml", "unit-aml-l08",
                     [{"id": "knowledge-bp", "title": "t", "summary": "s",
                       "concept_ids": ["concept-backprop"]}])],
    )
    assert len(edges) == 1
    assert [e["kind"] for e in edges[0]["evidence"]] == ["knowledge-node", "stage-concept"]


def test_repeated_evidence_is_deduplicated_not_counted_twice():
    row = _stage("module-aml", "unit-a", "study-map-a", "stage-a", ["concept-backprop"])
    edges = _build(stages=[row, dict(row)])
    assert len(edges[0]["evidence"]) == 1


# ---- what must never appear ------------------------------------------------

def test_no_edge_without_evidence():
    for edge in _build(stages=[
        _stage("module-aml", "u", "s", "st", ["concept-backprop"])]):
        assert edge["evidence"], edge


def test_a_concept_outside_the_registry_is_dropped_not_invented():
    edges = _build(stages=[
        _stage("module-aml", "u", "s", "st", ["concept-not-registered"])])
    assert edges == []


def test_a_module_that_is_not_projected_is_dropped():
    edges = _build(stages=[
        _stage("module-ghost", "u", "s", "st", ["concept-backprop"])])
    assert edges == []


def test_an_empty_concepts_tag_produces_nothing():
    assert _build(stages=[_stage("module-aml", "u", "s", "st", [])]) == []


def test_a_stage_missing_any_identity_field_is_skipped():
    """Evidence that cannot be drilled into is not evidence."""
    for missing in ("unit_id", "study_map_id", "id"):
        stage = _stage("module-aml", "u", "s", "st", ["concept-backprop"])
        stage[missing] = ""
        assert _build(stages=[stage]) == [], missing


def test_titles_and_prose_license_nothing():
    """The failure mode ADR-015 exists to prevent, stated as a test."""
    edges = _build(
        modules=[{"id": "module-aml", "title": "Backpropagation and Kernels"}],
        units=[{"id": "unit-x", "module_id": "module-aml",
                "title": "Backpropagation", "summary": "kernels, bias-variance",
                "knowledge_map": {"summary": "backprop and kernels",
                                  "nodes": [{"id": "knowledge-n", "title": "Backpropagation",
                                             "summary": "kernels"}]}}],
        stages=[{"module_id": "module-aml", "unit_id": "unit-x",
                 "study_map_id": "study-map-x", "id": "stage-x",
                 "title": "Backpropagation", "objective": "kernels and bias-variance"}],
    )
    assert edges == []


# ---- determinism and ordering ----------------------------------------------

def test_ordering_is_total_and_derived_only_from_ids():
    stages = [
        _stage("module-sad", "unit-b", "study-map-b", "stage-b", ["concept-kernels"]),
        _stage("module-aml", "unit-a", "study-map-a", "stage-z", ["concept-kernels"]),
        _stage("module-aml", "unit-a", "study-map-a", "stage-a", ["concept-backprop"]),
    ]
    edges = _build(stages=stages)
    assert [(e["module_id"], e["concept_id"]) for e in edges] == [
        ("module-aml", "concept-backprop"),
        ("module-aml", "concept-kernels"),
        ("module-sad", "concept-kernels"),
    ]
    assert json.dumps(edges) == json.dumps(_build(stages=list(reversed(stages))))


def test_evidence_within_an_edge_is_ordered():
    edges = _build(stages=[
        _stage("module-aml", "unit-b", "study-map-b", "stage-b", ["concept-backprop"]),
        _stage("module-aml", "unit-a", "study-map-a", "stage-a", ["concept-backprop"]),
    ])
    assert [e["unit_id"] for e in edges[0]["evidence"]] == ["unit-a", "unit-b"]


def test_cross_module_concepts_are_exactly_those_in_more_than_one_module():
    edges = _build(stages=[
        _stage("module-aml", "u1", "s1", "st1", ["concept-backprop", "concept-kernels"]),
        _stage("module-sad", "u2", "s2", "st2", ["concept-backprop"]),
    ])
    assert cross_module_concepts(edges) == ["concept-backprop"]


# ---- the live repository ---------------------------------------------------

@pytest.mark.full_repo
def test_the_live_projection_is_deterministic_and_fully_evidenced(repo_root):
    from learning_os.genout.common import stable_generated_at
    from learning_os.genout.manifest import build_manifest
    from learning_os.genout.outputs import build_backlinks
    from learning_os.loader import load_repo

    repo = load_repo(repo_root)
    generated_at = stable_generated_at(repo_root)
    first = build_manifest(repo, generated_at, build_backlinks(repo, generated_at))
    second = build_manifest(repo, generated_at, build_backlinks(repo, generated_at))
    edges = first["module_concept_edges"]

    assert json.dumps(edges) == json.dumps(second["module_concept_edges"])
    assert edges, "the crossing published nothing"

    known_modules = {m["id"] for m in first["modules"]}
    known_concepts = {r["id"] for r in first["records"] if r.get("type") == "concept"}
    known_units = {u["id"] for u in first["units"]}
    known_maps = {s["id"] for s in first["study_maps"]}
    known_stages = {s["id"] for s in first["stages"]}

    for edge in edges:
        assert edge["module_id"] in known_modules
        assert edge["concept_id"] in known_concepts
        assert edge["evidence"], edge
        for item in edge["evidence"]:
            assert item["unit_id"] in known_units
            if item["kind"] == "stage-concept":
                assert item["study_map_id"] in known_maps
                assert item["stage_id"] in known_stages
            else:
                assert item["kind"] == "knowledge-node"

    assert edges == sorted(edges, key=lambda e: (e["module_id"], e["concept_id"]))


@pytest.mark.full_repo
def test_the_concept_indexes_agree_with_the_edges(repo_root):
    """The divergence that let two indexes ship empty cannot recur."""
    from learning_os.genout.common import stable_generated_at
    from learning_os.genout.manifest import build_manifest
    from learning_os.genout.outputs import build_backlinks
    from learning_os.loader import load_repo

    repo = load_repo(repo_root)
    generated_at = stable_generated_at(repo_root)
    manifest = build_manifest(repo, generated_at, build_backlinks(repo, generated_at))
    edges, indexes = manifest["module_concept_edges"], manifest["indexes"]

    expected_module_to_concepts: dict[str, set[str]] = {}
    expected_concept_to_modules: dict[str, set[str]] = {}
    for edge in edges:
        expected_module_to_concepts.setdefault(edge["module_id"], set()).add(edge["concept_id"])
        expected_concept_to_modules.setdefault(edge["concept_id"], set()).add(edge["module_id"])

    assert indexes["module_to_concepts"] == {
        k: sorted(v) for k, v in sorted(expected_module_to_concepts.items())}
    assert indexes["concept_to_modules"] == {
        k: sorted(v) for k, v in sorted(expected_concept_to_modules.items())}


@pytest.mark.full_repo
def test_the_repaired_indexes_are_no_longer_empty(repo_root):
    """`unit_to_concepts` and `concept_to_units` shipped as {} from v2 to v7."""
    from learning_os.genout.common import stable_generated_at
    from learning_os.genout.manifest import build_manifest
    from learning_os.genout.outputs import build_backlinks
    from learning_os.loader import load_repo

    repo = load_repo(repo_root)
    generated_at = stable_generated_at(repo_root)
    indexes = build_manifest(
        repo, generated_at, build_backlinks(repo, generated_at))["indexes"]
    assert indexes["unit_to_concepts"], "unit_to_concepts is empty again"
    assert indexes["concept_to_units"], "concept_to_units is empty again"
