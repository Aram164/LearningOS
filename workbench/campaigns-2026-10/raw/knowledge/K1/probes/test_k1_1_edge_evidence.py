"""K1 invariant 1 (ADR-015 decision 2): every module_concept_edges row carries
evidence, and every evidence item resolves to the exact stage or knowledge node
that carries that concept tag — checked through the published manifest, the
surface a consumer actually reads."""

from __future__ import annotations

import json

import yaml

from learning_os.derive.projection import generate_all
from learning_os.store.loader import load_repo


def _tagged_repo(mini_repo):
    """mini_repo + curriculum; the stage tags one concept, a knowledge-map node
    tags another, so both evidence kinds exist on distinct edges."""
    from repo_builders import add_curriculum, write_yaml

    add_curriculum(mini_repo)
    unit_path = mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    unit = yaml.safe_load(unit_path.read_text(encoding="utf-8"))
    unit["knowledge_map"] = {
        "summary": "Expected value connects outcomes to probability weights.",
        "nodes": [
            {"id": "knowledge-demo-outcomes", "title": "Outcomes",
             "summary": "A variable maps outcomes to values."},
            {"id": "knowledge-demo-expectation", "title": "Expectation",
             "summary": "Expectation is a probability-weighted average.",
             "concept_ids": ["concept-variance"]},
        ],
    }
    write_yaml(unit_path, unit)
    map_path = mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
    sm = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    sm["stages"][0]["concepts"] = ["concept-expected-value"]
    write_yaml(map_path, sm)
    return mini_repo


def test_every_published_edge_carries_evidence_that_resolves_to_its_source(mini_repo):
    root = _tagged_repo(mini_repo)
    repo = load_repo(root)
    manifest = json.loads(generate_all(repo, generated_at="T1")["manifest.json"])
    edges = manifest["module_concept_edges"]
    assert edges, "the fixture licensed no edges at all"

    for edge in edges:
        assert edge["evidence"], edge
        for item in edge["evidence"]:
            if item["kind"] == "stage-concept":
                study_map = repo.study_maps[item["study_map_id"]]
                stage = next(s for s in study_map.data["stages"]
                             if s["id"] == item["stage_id"])
                # The stage the item names is the stage carrying the tag.
                assert edge["concept_id"] in (stage.get("concepts") or [])
            else:
                assert item["kind"] == "knowledge-node"
                unit = repo.units[item["unit_id"]]
                node = next(n for n in unit.data["knowledge_map"]["nodes"]
                            if n["id"] == item["node_id"])
                assert edge["concept_id"] in (node.get("concept_ids") or [])


def test_published_evidence_resolves_through_the_manifest_consumer_surface(mini_repo):
    """The manifest's own units/study_maps/stages rows must admit every evidence
    identity, or a consumer drilling into a cell hits a dangling id."""
    root = _tagged_repo(mini_repo)
    manifest = json.loads(generate_all(load_repo(root), generated_at="T1")["manifest.json"])
    known_units = {u["id"] for u in manifest["units"]}
    known_maps = {s["id"] for s in manifest["study_maps"]}
    known_stages = {s["id"] for s in manifest["stages"]}
    known_modules = {m["id"] for m in manifest["modules"]}

    for edge in manifest["module_concept_edges"]:
        assert edge["module_id"] in known_modules
        for item in edge["evidence"]:
            assert item["unit_id"] in known_units
            if item["kind"] == "stage-concept":
                assert item["study_map_id"] in known_maps
                assert item["stage_id"] in known_stages


def test_both_evidence_kinds_merge_into_one_edge_with_distinct_rows(mini_repo):
    """Stage tag and knowledge node on the SAME concept merge into one edge
    holding both evidence rows (the drill-in stays exact per kind)."""
    root = _tagged_repo(mini_repo)
    map_path = root / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
    sm = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    sm["stages"][0]["concepts"] = ["concept-variance"]
    yaml.safe_dump(sm, map_path.open("w"), sort_keys=False)
    manifest = json.loads(generate_all(load_repo(root), generated_at="T1")["manifest.json"])
    edges = {e["concept_id"]: e for e in manifest["module_concept_edges"]}
    # Both licensed sources now name concept-variance; the old stage tag for
    # concept-expected-value was overwritten, so exactly one edge remains.
    assert set(edges) == {"concept-variance"}
    kinds = sorted(item["kind"] for item in edges["concept-variance"]["evidence"])
    assert kinds == ["knowledge-node", "stage-concept"]
