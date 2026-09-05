"""The lecture-map assembly operation is durable, bounded, and fail-closed."""

from __future__ import annotations

import assemble_lecture_study_maps as assembler


def _unit() -> dict:
    return {
        "id": "unit-demo-l01",
        "knowledge_map": {
            "nodes": [
                {
                    "id": "knowledge-demo-result",
                    "title": "Expected value result",
                    "summary": "Derive the expected value result.",
                    "builds_on": ["knowledge-demo-formulation"],
                },
                {
                    "id": "knowledge-demo-formulation",
                    "title": "Expected value formulation",
                    "summary": "State the expected value formulation.",
                },
            ]
        },
    }


def _routes() -> list[dict]:
    return [
        {
            # Routes reach the assembler through the projected manifest, which
            # carries the v13 route id. The assembler must pass it through.
            "id": "route-demo-course-deck",
            "source_id": "source-demo-book",
            "unit_id": "unit-demo-l01",
            "title": "Course deck",
            "format": "course-material",
            "angle": "Defines the notation used in the lecture.",
            "locator": "slides/VL 01.pdf",
            "covers": ["knowledge-demo-formulation", "knowledge-demo-result"],
            "depth": "course-aligned",
            "scope": "current",
        },
        {
            "id": "route-demo-worked-exercises",
            "source_id": "source-demo-practice",
            "unit_id": "unit-demo-l01",
            "title": "Worked exercises",
            "format": "exercise",
            "angle": "Tests transfer to unfamiliar examples.",
            "locator": "sheet 1",
            "covers": ["knowledge-demo-result"],
            "depth": "practice",
            "scope": "complementary",
        },
    ]


def test_assembly_preserves_order_material_angles_and_absent_estimates():
    unit = _unit()
    routes = _routes()
    phrases = {"concept-expected-value": ["expected value"]}

    record = assembler.build(
        unit,
        "module-demo",
        routes,
        phrases,
        exam_bearing=True,
    )

    stages = record["stages"]
    assert [stage["id"] for stage in stages] == [
        "stage-demo-formulation",
        "stage-demo-result",
    ]
    assert [resource["source_id"] for resource in stages[1]["resources"]] == [
        "source-demo-book",
        "source-demo-practice",
    ]
    # The angle is a field of its own, not prose appended to the locator: an
    # interface has to be able to render it, and the validator has to be able
    # to tell a row that carries one from a row that does not.
    assert "Defines the notation" in stages[0]["resources"][0]["angle"]
    assert "Tests transfer" in stages[1]["resources"][1]["angle"]
    assert "Defines the notation" not in stages[0]["resources"][0]["locator"]
    assert stages[0]["resources"][0]["locator"] == "slides/VL 01.pdf"
    assert all("estimate_minutes" not in stage for stage in stages)
    assert all(stage["concepts"] == ["concept-expected-value"] for stage in stages)
    # F01 (2026-09-05 audit): the route id reaches the stage resource, so the
    # stage can resolve its exact material without matching on prose.
    assert [resource["route_id"] for resource in stages[1]["resources"]] == [
        "route-demo-course-deck",
        "route-demo-worked-exercises",
    ]
    assert assembler.assembly_problems(unit, routes, record) == []


def test_assembly_refuses_invisible_or_unrouted_stages():
    unit = _unit()
    routes = _routes()[:1]
    routes[0]["covers"] = ["knowledge-demo-formulation"]
    record = assembler.build(unit, "module-demo", routes, {}, exam_bearing=False)

    problems = assembler.assembly_problems(unit, routes, record)

    assert any("has no material route: knowledge-demo-result" in problem for problem in problems)
    assert any("has no concept coverage" in problem for problem in problems)


def test_curated_edges_still_name_live_nodes_and_concepts(repo_root):
    """A renamed node or concept must fail before the next bulk draft is written."""
    manifest = assembler._manifest(repo_root)
    assert assembler.curation_problems(manifest) == []
