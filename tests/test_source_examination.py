"""Projected examination state: evaluated plus approved unit analyses.

Manifest contract v15 (two-pass intake, step 5): every projected source
carries `examination`, so the Library can mark a metadata-only source "placed
from metadata" while none exists — and tell that apart from an older build.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from repo_builders import add_curriculum, write_minimal_pdf, write_yaml

from learning_os.genout.projection.records_library import project_sources
from learning_os.loader import load_repo
from learning_os.material_synthesis import current_unit_material_basis


def _routed_unit(root: Path) -> None:
    add_curriculum(root)
    unit_path = root / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    unit = yaml.safe_load(unit_path.read_text(encoding="utf-8"))
    unit["knowledge_map"] = {
        "summary": "Expected value connects outcomes to probability weights.",
        "nodes": [
            {"id": "knowledge-demo-outcomes", "title": "Outcomes",
             "summary": "A variable maps outcomes to values."},
            {"id": "knowledge-demo-expectation", "title": "Expectation",
             "summary": "Expectation is a probability-weighted average.",
             "builds_on": ["knowledge-demo-outcomes"]},
        ],
    }
    write_yaml(unit_path, unit)
    source_map_path = root / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(source_map_path.read_text(encoding="utf-8"))
    source_map["sources"][0]["unit_routes"] = [{
        "id": "route-demo-l01-book",
        "unit_id": "unit-demo-l01",
        "title": "Demo Book — expectation",
        "format": "book",
        "angle": "Derives the weighted sum with one discrete example.",
        "covers": ["knowledge-demo-outcomes", "knowledge-demo-expectation"],
        "depth": "derivation",
        "scope": "current",
        "locator": "lecture-01.pdf",
    }]
    write_yaml(source_map_path, source_map)
    registry_path = root / "sources/sources.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["sources"][0]["material"] = "material://source-demo-book/book.pdf"
    write_yaml(registry_path, registry)
    write_minimal_pdf(
        root.parent / "materials/source-demo-book/lecture-01.pdf",
        ["synthetic expected-value lecture",
         "the weighted sum over finite outcomes"],
    )


def _dossier(root: Path, synthesis_id: str = "material-synthesis-demo-l01") -> dict:
    basis = current_unit_material_basis(root, "unit-demo-l01")
    checksum = basis["material_checksums"]["route-demo-l01-book"]
    return {
        "schema_version": 1,
        "id": synthesis_id,
        "type": "unit-material-synthesis",
        "unit_id": "unit-demo-l01",
        "status": "approved",
        "basis": {
            **basis,
            "ai_provenance": {
                "request_id": "ai-request-demo",
                "delivery_id": "ai-delivery-demo",
                "provider": "manual-bundle",
            },
        },
        "route_assessments": [{
            "route_id": "route-demo-l01-book",
            "source_id": "source-demo-book",
            "locator": "lecture-01.pdf",
            "review_status": "deep-reviewed",
            "concept_ids": ["concept-expected-value"],
            "contribution": "A direct derivation of the weighted sum.",
            "assumptions": "Finite discrete outcomes are assumed.",
            "notation": "Uses uppercase X and lowercase outcome values.",
            "exercise_value": "Includes a small worked calculation.",
            "best_for": "Checking the lecture's core derivation.",
            "limitations": "Does not cover continuous variables.",
            "scope_of_absence": "lecture-01.pdf, PDF p. 1 of 1",
            "evidence": [{"locator": "lecture-01.pdf p.1", "checksum": checksum}],
        }],
        "comparisons": [],
        "concept_groups": [],
    }


def _write_dossier(root: Path, dossier: dict) -> None:
    write_yaml(
        root / "curriculum/modules/module-demo/units/unit-demo-l01/material-synthesis.yaml",
        dossier)


def _projected(root: Path) -> dict:
    rows = project_sources(load_repo(root), lambda *args: 0)
    return {row["id"]: row for row in rows}


def test_evaluated_reflects_evaluations(mini_repo):
    rows = _projected(mini_repo)
    assert rows["source-demo-book"]["discovery"] is None
    assert rows["source-demo-book"]["examination"] == {
        "evaluated": True, "approved_analysis_count": 0, "metadata_placed": False}
    path = mini_repo / "sources" / "sources.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["sources"].append({
        "id": "source-new-course", "title": "New Course", "type": "course",
        "url": "https://example.org/cs000/",
        "discovery": {
            "observed": "2026-09-23",
            "basis": [{"kind": "list-entry", "ref": "legacy/EXAMPLE-LIST.md#L10"}],
            "possible_use": "Possibly a lecture spine.",
        },
    })
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    rows = _projected(mini_repo)
    assert rows["source-new-course"]["discovery"]["possible_use"] == "Possibly a lecture spine."
    assert rows["source-new-course"]["discovery"]["basis"][0]["ref"] == "legacy/EXAMPLE-LIST.md#L10"
    assert rows["source-new-course"]["examination"] == {
        "evaluated": False, "approved_analysis_count": 0, "metadata_placed": True}


def test_current_approved_assessment_counts_once(mini_repo):
    _routed_unit(mini_repo)
    _write_dossier(mini_repo, _dossier(mini_repo))
    rows = _projected(mini_repo)
    assert rows["source-demo-book"]["examination"] == {
        "evaluated": True, "approved_analysis_count": 1, "metadata_placed": False}


def test_draft_or_stale_dossier_does_not_count(mini_repo):
    _routed_unit(mini_repo)
    draft = _dossier(mini_repo)
    draft["status"] = "draft"
    _write_dossier(mini_repo, draft)
    assert _projected(mini_repo)["source-demo-book"]["examination"] == {
        "evaluated": True, "approved_analysis_count": 0, "metadata_placed": False}
    _write_dossier(mini_repo, _dossier(mini_repo))
    assert _projected(mini_repo)["source-demo-book"]["examination"][
        "approved_analysis_count"] == 1
    source_map_path = mini_repo / "curriculum/modules/module-demo/source-map.yaml"
    changed = yaml.safe_load(source_map_path.read_text(encoding="utf-8"))
    changed["sources"][0]["unit_routes"][0]["covers"] = ["knowledge-demo-l01-extra"]
    write_yaml(source_map_path, changed)
    assert _projected(mini_repo)["source-demo-book"]["examination"] == {
        "evaluated": True, "approved_analysis_count": 0, "metadata_placed": False}


def test_route_source_is_authoritative_over_the_row_copy(mini_repo):
    _routed_unit(mini_repo)
    dossier = _dossier(mini_repo)
    dossier["route_assessments"][0]["source_id"] = "source-row-copy"
    _write_dossier(mini_repo, dossier)
    rows = _projected(mini_repo)
    assert rows["source-demo-book"]["examination"]["approved_analysis_count"] == 1
    assert "source-row-copy" not in rows
