"""Manifest v7 full-schema and route-identity acceptance tests."""

from __future__ import annotations

import json

import pytest
import yaml
from test_curriculum_v2 import _add_material_overview, add_curriculum, write_yaml

from learning_os.contracts.manifest_contract import check
from learning_os.genout.manifest import build_manifest
from learning_os.loader import load_repo
from learning_os.material_synthesis import current_unit_material_basis
from learning_os.routes import deterministic_route_id
from learning_os.rules import validate


def _rich_fixture(root):
    add_curriculum(root)
    _add_material_overview(root)
    source_map_path = root / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(source_map_path.read_text(encoding="utf-8"))
    route = source_map["sources"][0]["unit_routes"][0]
    route_id = deterministic_route_id(
        "module-demo", "source-demo-book", route
    )
    unit_path = root / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    unit = yaml.safe_load(unit_path.read_text(encoding="utf-8"))
    unit["source_selections"][0]["locator"] = route["locator"]
    unit["knowledge_map"]["nodes"][1]["concept_ids"] = [
        "concept-expected-value"
    ]
    write_yaml(unit_path, unit)
    return route_id, route


def test_v7_projects_stable_route_and_guarded_selection(mini_repo):
    route_id, _route = _rich_fixture(mini_repo)
    manifest = build_manifest(load_repo(mini_repo), "T1")

    projected_route = manifest["module_source_maps"][0]["sources"][0][
        "unit_routes"
    ][0]
    projected_selection = manifest["units"][0]["source_selections"][0]

    assert projected_route["id"] == route_id
    assert projected_selection == {
        "source_id": "source-demo-book",
        "locator": "lecture-01.pdf",
        "purpose": "Current derivation",
        "route_id": route_id,
    }
    assert manifest["indexes"]["unit_to_concepts"] == {
        "unit-demo-l01": ["concept-expected-value"]
    }
    assert manifest["indexes"]["concept_to_units"] == {
        "concept-expected-value": ["unit-demo-l01"]
    }


def test_v7_nested_violation_reports_rfc6901_pointer(mini_repo):
    add_curriculum(mini_repo)
    manifest = build_manifest(load_repo(mini_repo), "T1")
    manifest["units"][0]["unexpected_field"] = True

    ok, message = check(manifest, mini_repo)

    assert not ok
    assert "/units/0" in message
    assert "unexpected_field" in message


def _add_manifest_project(root):
    write_yaml(root / "projects/registry/project-demo.yaml", {
        "schema_version": 1,
        "id": "project-demo",
        "type": "project",
        "title": "Demo project",
        "project_type": "software",
        "status": "planned",
        "root_uri": "project://demo",
        "objective": "Exercise the strict public projection contract.",
        "milestone_ids": [],
        "linked_module_ids": [],
        "unit_ids": [],
        "workspace_ids": [],
        "thematic_group_ids": [],
        "boundaries": {
            "confidentiality": "private",
            "external_code_access": "none",
        },
    })


@pytest.mark.parametrize(("mutate", "pointer", "detail"), [
    (
        lambda manifest: manifest["modules"][0]["components"].append({
            "id": "component-demo", "title": "Demo", "order": "first",
        }),
        "/modules/0/components/0/order",
        "not of type 'integer'",
    ),
    (
        lambda manifest: manifest["programs"][0]["semesters"][0].update({
            "credential": "synthetic-secret",
        }),
        "/programs/0/semesters/0",
        "credential",
    ),
    (
        lambda manifest: manifest["projects"][0]["boundaries"].update({
            "absolute_private_path": "/Users/example/private",
        }),
        "/projects/0/boundaries",
        "absolute_private_path",
    ),
    (
        lambda manifest: manifest["ai_actions"]["available"][0].update({
            "raw_prompt": "undeclared",
        }),
        "/ai_actions/available/0",
        "raw_prompt",
    ),
])
def test_v7_rejects_unknown_or_malformed_nested_public_records(
    mini_repo,
    mutate,
    pointer,
    detail,
):
    add_curriculum(mini_repo)
    _add_manifest_project(mini_repo)
    manifest = build_manifest(load_repo(mini_repo), "T1")

    mutate(manifest)
    ok, message = check(manifest, mini_repo)

    assert not ok
    assert pointer in message
    assert detail in message


def test_v7_exact_schema_hash_drift_fails_closed(mini_repo):
    add_curriculum(mini_repo)
    manifest = build_manifest(load_repo(mini_repo), "T1")
    # The declared schema, not a hardcoded version: this test is about the
    # hash gate, and pinning it to v7 made it pass vacuously the moment the
    # contract moved to v8 — it mutated a file nothing was checking.
    contract = yaml.safe_load(
        (mini_repo / "system/contracts/manifest-contract.yaml").read_text(encoding="utf-8"))
    schema = mini_repo / contract["schema_path"]
    schema.write_text(schema.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    ok, message = check(manifest, mini_repo)

    assert not ok
    assert "schema hash" in message
    assert "exact file" in message


def test_route_references_reject_duplicate_dangling_and_guard_drift(mini_repo):
    _route_id, _route = _rich_fixture(mini_repo)
    source_map_path = mini_repo / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(source_map_path.read_text(encoding="utf-8"))
    route = source_map["sources"][0]["unit_routes"][0]
    route["id"] = "route-demo-exact"
    duplicate_one = {
        **route,
        "id": "route-demo-duplicate",
        "title": "First duplicated id",
    }
    duplicate_two = {
        **route,
        "id": "route-demo-duplicate",
        "title": "Second duplicated id",
    }
    source_map["sources"][0]["unit_routes"].extend([
        duplicate_one,
        duplicate_two,
    ])
    write_yaml(source_map_path, source_map)

    unit_path = mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    unit = yaml.safe_load(unit_path.read_text(encoding="utf-8"))
    unit["source_selections"] = [
        {
            "route_id": "route-does-not-exist",
            "source_id": "source-demo-book",
            "locator": route["locator"],
            "purpose": "Dangling route fixture.",
        },
        {
            "route_id": "route-demo-exact",
            "source_id": "source-demo-book",
            "locator": "changed locator",
            "purpose": "Guard drift fixture.",
        },
    ]
    write_yaml(unit_path, unit)

    codes = {
        issue.code
        for issue in validate(load_repo(mini_repo))
        if issue.severity == "E"
    }

    assert "ROUTE-ID-DUPLICATE" in codes
    assert "REF-ROUTE" in codes
    assert "SELECTION-LOCATOR-GUARD" in codes


def test_route_selection_must_stay_on_its_owning_unit(mini_repo):
    add_curriculum(mini_repo)
    module_path = mini_repo / "curriculum/modules/module-demo/module.yaml"
    module = yaml.safe_load(module_path.read_text(encoding="utf-8"))
    module["unit_order"].append("unit-demo-l02")
    write_yaml(module_path, module)

    first_path = mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    first = yaml.safe_load(first_path.read_text(encoding="utf-8"))
    second = {
        **first,
        "id": "unit-demo-l02",
        "title": "Second lecture",
        "order": 2,
        "current_study_map": None,
        "source_selections": [],
    }
    second.pop("current_study_map")
    write_yaml(
        mini_repo / "curriculum/modules/module-demo/units/unit-demo-l02/unit.yaml",
        second,
    )
    source_map_path = mini_repo / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(source_map_path.read_text(encoding="utf-8"))
    source_map["sources"][0]["unit_routes"] = [{
        "id": "route-demo-l02",
        "unit_id": "unit-demo-l02",
        "title": "Second lecture route",
        "format": "book",
        "angle": "Belongs only to the second lecture.",
        "covers": ["knowledge-demo-l02"],
        "depth": "course-aligned",
        "scope": "current",
        "locator": "p. 2",
    }]
    write_yaml(source_map_path, source_map)
    first["source_selections"] = [{
        "route_id": "route-demo-l02",
        "source_id": "source-demo-book",
        "locator": "p. 2",
        "purpose": "Foreign-unit fixture.",
    }]
    write_yaml(first_path, first)

    codes = {
        issue.code
        for issue in validate(load_repo(mini_repo))
        if issue.severity == "E"
    }

    assert "SELECTION-ROUTE-OWNER" in codes


def test_approved_synthesis_projects_strictly_and_indexes_by_unit(mini_repo):
    route_id, route = _rich_fixture(mini_repo)
    source_map_path = mini_repo / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(source_map_path.read_text(encoding="utf-8"))
    source_map["sources"][0]["unit_routes"][0]["id"] = route_id
    write_yaml(source_map_path, source_map)
    basis = current_unit_material_basis(mini_repo, "unit-demo-l01")
    checksum = basis["material_checksums"][route_id]
    synthesis = {
        "schema_version": 1,
        "id": "material-synthesis-demo-l01",
        "type": "unit-material-synthesis",
        "unit_id": "unit-demo-l01",
        "status": "approved",
        "basis": {
            **basis,
            "ai_provenance": {
                "request_id": "request-demo",
                "delivery_id": "delivery-demo",
                "provider": "local",
            },
        },
        "route_assessments": [{
            "route_id": route_id,
            "source_id": "source-demo-book",
            "locator": route["locator"],
            "review_status": "deep-reviewed",
            "concept_ids": ["concept-expected-value"],
            "contribution": "Derives the weighted sum.",
            "assumptions": "Discrete outcomes are already defined.",
            "notation": "Uses E[X].",
            "exercise_value": "Contains one worked calculation.",
            "best_for": "Rebuilding the derivation.",
            "limitations": "Does not cover continuous variables.",
            "evidence": [{"locator": route["locator"], "checksum": checksum}],
        }],
        "comparisons": [],
        "concept_groups": [{
            "concept_id": "concept-expected-value",
            "local_node_ids": ["knowledge-demo-expectation"],
            "related_unit_ids": [],
            "bridge_note_ids": [],
            "narrative": "The local derivation maps to expected value.",
        }],
    }
    write_yaml(
        mini_repo
        / "curriculum/modules/module-demo/units/unit-demo-l01/material-synthesis.yaml",
        synthesis,
    )

    repo = load_repo(mini_repo)
    manifest = build_manifest(repo, "T1")

    [projected] = manifest["unit_material_syntheses"]
    assert {key: projected[key] for key in synthesis} == synthesis
    assert projected["freshness"] == {"status": "current", "reasons": []}
    assert projected["completeness"] == {
        "complete": True,
        "current_route_count": 1,
        "assessed_route_count": 1,
        "deep_reviewed_count": 1,
        "screened_count": 0,
        "unevaluated_count": 0,
        "unavailable_count": 0,
        "missing_route_ids": [],
        "orphaned_route_ids": [],
        "duplicate_route_ids": [],
    }
    assert manifest["indexes"]["unit_to_material_synthesis"] == {
        "unit-demo-l01": "material-synthesis-demo-l01"
    }
    encoded = json.dumps(manifest, sort_keys=True)
    assert "material-synthesis-demo-l01" in encoded

    projected["freshness"]["raw_detail"] = "/Users/example/private"
    ok, message = check(manifest, mini_repo)
    assert not ok
    assert "/unit_material_syntheses/0/freshness" in message
    assert "raw_detail" in message

    source_map = yaml.safe_load(source_map_path.read_text(encoding="utf-8"))
    source_map["sources"][0]["unit_routes"][0]["angle"] = "Changed evidence basis."
    write_yaml(source_map_path, source_map)

    stale_manifest = build_manifest(load_repo(mini_repo), "T2")
    [stale] = stale_manifest["unit_material_syntheses"]
    assert stale["route_assessments"] == synthesis["route_assessments"]
    assert stale["freshness"]["status"] == "stale"
    assert "route_set_checksum" in stale["freshness"]["reasons"]
    assert stale["completeness"]["complete"] is True

    duplicate_route = dict(source_map["sources"][0]["unit_routes"][0])
    duplicate_route["title"] = "Duplicate identity fixture"
    source_map["sources"][0]["unit_routes"].append(duplicate_route)
    write_yaml(source_map_path, source_map)
    [duplicate] = build_manifest(
        load_repo(mini_repo), "T3"
    )["unit_material_syntheses"]
    assert duplicate["completeness"]["complete"] is False
    assert duplicate["completeness"]["duplicate_route_ids"] == [route_id]
