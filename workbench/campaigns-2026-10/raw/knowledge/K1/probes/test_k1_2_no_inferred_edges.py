"""K1 invariant 2 (ADR-015 decision 2): a concept named only in a title, prose,
a note body, or a source evaluation licenses no module×concept edge — probed
through the full projection pipeline with the concept REGISTERED, so absence
can only come from the licensing rule, never from unknown-id dropping."""

from __future__ import annotations

import json
import textwrap

import yaml

from learning_os.derive.projection import generate_all
from learning_os.store.loader import load_repo


def _prose_repo(mini_repo):
    """Everything mentions `concept-kernels` EXCEPT the two licensed places."""
    from repo_builders import add_curriculum, write_yaml

    add_curriculum(mini_repo)
    concepts_path = mini_repo / "knowledge/concepts.yaml"
    concepts = yaml.safe_load(concepts_path.read_text(encoding="utf-8"))
    concepts["concepts"].append(
        {"id": "concept-kernels", "label": "Kernel methods", "aliases": []})
    write_yaml(concepts_path, concepts)

    unit_path = mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    unit = yaml.safe_load(unit_path.read_text(encoding="utf-8"))
    unit["title"] = "Kernels and expected value"
    unit["scope"] = "Kernels appear throughout; we derive expected value."
    unit["knowledge_map"] = {
        "summary": "Kernel methods frame the whole lecture.",
        "nodes": [
            # Title/summary prose only — deliberately no `concept_ids`.
            {"id": "knowledge-demo-kernels", "title": "Kernel trick",
             "summary": "The kernel trick implicit in every derivation."},
            {"id": "knowledge-demo-outcomes", "title": "Outcomes",
             "summary": "A variable maps outcomes to values."},
        ],
    }
    write_yaml(unit_path, unit)

    map_path = mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
    sm = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    sm["stages"][0]["objective"] = "Derive the kernel representation, then expected value."
    # No `concepts` tag on the stage.
    write_yaml(map_path, sm)

    module_path = mini_repo / "curriculum/modules/module-demo/module.yaml"
    module = yaml.safe_load(module_path.read_text(encoding="utf-8"))
    module["title"] = "Kernel methods (demo)"
    write_yaml(module_path, module)

    # A note body naming the concept, and a source evaluation targeting it:
    # neither is a licensed edge source (ADR-015 decision 2).
    note_path = mini_repo / "knowledge/notes/mathematics/note-demo.md"
    note_path.write_text(textwrap.dedent("""\
        ---
        id: note-demo
        type: note
        title: Demo note
        created: 2026-07-16
        role: synthesis
        concepts: [concept-kernels]
        sources: [source-demo-book]
        ---

        Body prose about kernel methods.
        """), encoding="utf-8")
    registry_path = mini_repo / "sources/sources.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["sources"][0]["evaluations"] = [
        {"concepts": ["concept-kernels"], "roles": ["first-learning"],
         "level": "introductory", "strengths": ["clear intuition"]},
    ]
    write_yaml(registry_path, registry)
    return mini_repo


def test_no_inferred_edge_from_any_prose_surface(mini_repo):
    root = _prose_repo(mini_repo)
    manifest = json.loads(generate_all(load_repo(root), generated_at="T1")["manifest.json"])
    assert manifest["module_concept_edges"] == []
    # The concept IS projected everywhere else; only the crossing stays empty.
    concept_ids = {r["id"] for r in manifest["records"] if r.get("type") == "concept"}
    assert "concept-kernels" in concept_ids


def test_module_and_unit_level_concept_fields_license_nothing():
    """ADR-015 rejects a `concepts` field on the module record, and only a
    knowledge-map NODE's concept_ids is licensed on the unit. At the edge
    builder (the licensed-sources function itself), planting both shapes
    produces no edge; the published pipeline additionally refuses the
    off-schema fields outright (manifest shape lock, fail closed)."""
    from learning_os.derive.projection.projection.atlas import build_module_concept_edges

    module_row = {"id": "module-demo",
                  "concepts": ["concept-expected-value", "concept-variance"]}
    node = {"id": "knowledge-n", "title": "t", "summary": "s",
            "concepts": ["concept-variance"]}  # unit-level shape: no license
    unit_row = {"id": "unit-demo-l01", "module_id": "module-demo",
                "concepts": ["concept-expected-value"],
                "knowledge_map": {"summary": "s", "nodes": [node]}}
    stage_row = {"module_id": "module-demo", "unit_id": "unit-demo-l01",
                 "study_map_id": "study-map-x", "id": "stage-x",
                 "concepts": None}
    edges = build_module_concept_edges(
        modules=[module_row],
        units=[unit_row],
        stages=[stage_row],
        concepts={"concept-expected-value": {}, "concept-variance": {}},
    )
    assert edges == []


def test_licensed_sources_still_work_alongside_prose(mini_repo):
    """Same prose-heavy fixture, plus one licensed tag: exactly one edge."""
    root = _prose_repo(mini_repo)
    map_path = root / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
    sm = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    sm["stages"][0]["concepts"] = ["concept-expected-value"]
    yaml.safe_dump(sm, map_path.open("w"), sort_keys=False)
    manifest = json.loads(generate_all(load_repo(root), generated_at="T1")["manifest.json"])
    edges = manifest["module_concept_edges"]
    assert [(e["module_id"], e["concept_id"]) for e in edges] == [
        ("module-demo", "concept-expected-value")]
    assert [i["kind"] for i in edges[0]["evidence"]] == ["stage-concept"]
