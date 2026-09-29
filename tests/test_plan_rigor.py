import copy
from types import SimpleNamespace

import pytest

from learning_os.rules.plan_rigor import (
    ChecksPlanRigor,
    _has_unquoted_hedge,
    angle_review_fingerprint,
)


def test_exact_title_may_contain_selection_word():
    locator = (
        "Spring 2022 playlist, Lecture 10 "
        "'Bias/Variance, Regularization, and Model Selection'"
    )
    assert not _has_unquoted_hedge(locator)


def test_unquoted_selection_instruction_remains_vague():
    locator = "Lecture 10 'Model Selection' — selected chapters"
    assert _has_unquoted_hedge(locator)


class _StubChecker(ChecksPlanRigor):
    """Drive the stage/node checks without a repository on disk."""

    def __init__(self, units, study_maps, routes):
        self.repo = SimpleNamespace(units=units, study_maps=study_maps,
                                    module_source_maps={})
        self._routes = routes
        self.warnings = []

    def _routes_by_id(self):
        return self._routes

    def warn(self, code, message, where):
        self.warnings.append((code, message))

    def err(self, code, message, where):  # pragma: no cover
        raise AssertionError(f"unexpected error {code}: {message}")

    def _rel(self, path):
        return str(path)


def _unit(*node_ids):
    return SimpleNamespace(data={
        "knowledge_map": {"nodes": [{"id": nid} for nid in node_ids]},
    })


def _map(stage):
    return SimpleNamespace(path="study-map.yaml", unit_id="unit-demo",
                           data={"stages": [stage]})


def _codes(checker):
    return [code for code, _ in checker.warnings]


def test_convention_stage_links_silently_and_orphan_fires():
    """The UE3 shape: inferable stage, route that dropped the node."""
    stage = {"id": "stage-demo-bayes",
             "resources": [{"route_id": "route-ue3"}]}
    checker = _StubChecker(
        {"unit-demo": _unit("knowledge-demo-bayes")},
        {"sm": _map(stage)},
        {"route-ue3": {"id": "route-ue3", "covers": ["knowledge-demo-other"]}},
    )
    checker.check_plan_rigor()
    assert _codes(checker) == ["RESOURCE-NODE-ORPHAN"]


def test_covering_route_stays_silent():
    stage = {"id": "stage-demo-bayes",
             "resources": [{"route_id": "route-ue4"}]}
    checker = _StubChecker(
        {"unit-demo": _unit("knowledge-demo-bayes")},
        {"sm": _map(stage)},
        {"route-ue4": {"id": "route-ue4",
                       "covers": ["knowledge-demo-bayes"]}},
    )
    checker.check_plan_rigor()
    assert checker.warnings == []


def test_unconventional_stage_warns_unlinked_and_skips_orphan():
    stage = {"id": "stage-roadmap-step",
             "resources": [{"route_id": "route-x"}]}
    checker = _StubChecker(
        {"unit-demo": _unit("knowledge-demo-bayes")},
        {"sm": _map(stage)},
        {"route-x": {"id": "route-x",
                     "covers": ["knowledge-demo-bayes"]}},
    )
    checker.check_plan_rigor()
    assert _codes(checker) == ["STAGE-NODE-UNLINKED"]


def test_dangling_explicit_key_warns_and_skips_orphan():
    stage = {"id": "stage-demo-bayes",
             "knowledge_node_id": "knowledge-demo-gone",
             "resources": [{"route_id": "route-x"}]}
    checker = _StubChecker(
        {"unit-demo": _unit("knowledge-demo-bayes")},
        {"sm": _map(stage)},
        {"route-x": {"id": "route-x", "covers": []}},
    )
    checker.check_plan_rigor()
    assert _codes(checker) == ["STAGE-NODE-UNLINKED"]


def test_explicit_key_resolves_and_orphan_applies():
    stage = {"id": "stage-custom",
             "knowledge_node_id": "knowledge-demo-bayes",
             "resources": [{"route_id": "route-x"}]}
    checker = _StubChecker(
        {"unit-demo": _unit("knowledge-demo-bayes")},
        {"sm": _map(stage)},
        {"route-x": {"id": "route-x", "covers": []}},
    )
    checker.check_plan_rigor()
    assert _codes(checker) == ["RESOURCE-NODE-ORPHAN"]


def test_scaffold_note_records_deliberate_placement():
    stage = {"id": "stage-demo-bayes",
             "resources": [{"route_id": "route-ue3",
                            "node_scaffold_note": "Total-probability denominator the stage inverts."}]}
    checker = _StubChecker(
        {"unit-demo": _unit("knowledge-demo-bayes")},
        {"sm": _map(stage)},
        {"route-ue3": {"id": "route-ue3", "covers": ["knowledge-demo-other"]}},
    )
    checker.check_plan_rigor()
    assert checker.warnings == []


def test_blank_scaffold_note_still_warns():
    stage = {"id": "stage-demo-bayes",
             "resources": [{"route_id": "route-ue3",
                            "node_scaffold_note": "   "}]}
    checker = _StubChecker(
        {"unit-demo": _unit("knowledge-demo-bayes")},
        {"sm": _map(stage)},
        {"route-ue3": {"id": "route-ue3", "covers": []}},
    )
    checker.check_plan_rigor()
    assert _codes(checker) == ["RESOURCE-NODE-ORPHAN"]


def test_unit_without_knowledge_map_stays_silent():
    stage = {"id": "stage-roadmap-step",
             "resources": [{"route_id": "route-x"}]}
    checker = _StubChecker(
        {"unit-demo": SimpleNamespace(data={})},
        {"sm": _map(stage)},
        {"route-x": {"id": "route-x", "covers": []}},
    )
    checker.check_plan_rigor()
    assert checker.warnings == []


def test_assembler_emits_the_join_key():
    from tools.assemble_lecture_study_maps import build

    unit = {"id": "unit-demo",
            "knowledge_map": {"nodes": [
                {"id": "knowledge-demo-bayes", "title": "Bayes",
                 "summary": "Inversion."},
            ]}}
    draft = build(unit, "module-demo", [], {}, False)
    assert draft["stages"][0]["knowledge_node_id"] == "knowledge-demo-bayes"


def _angle_case():
    route = {"id": "route-demo", "source_id": "source-demo-book",
             "angle": "Explains probability and inference.",
             "covers": ["knowledge-demo-bayes"], "locator": "PDF pp. 1-3"}
    resource = {"route_id": "route-demo", "source_id": "source-demo-book",
                "kind": "read", "locator": "PDF p. 2",
                "angle": "Work the Bayes example at this stage."}
    stage = {"id": "stage-demo-bayes", "title": "Bayes",
             "objective": "Normalize the posterior.", "resources": [resource]}
    resource["angle_review"] = {
        "kind": "refinement", "reviewed_by": "operator-test",
        "reviewed_on": "2026-09-30", "rationale": "The row selects the route's Bayes example.",
        "fingerprint": angle_review_fingerprint(route, stage, resource),
    }
    checker = _StubChecker({"unit-demo": _unit("knowledge-demo-bayes")},
                           {"sm": _map(stage)}, {"route-demo": route})
    return checker, route, stage, resource


def test_reviewed_refinement_preserves_stage_specific_description():
    checker, _, _, resource = _angle_case()
    checker.check_plan_rigor()
    assert checker.warnings == []
    assert resource["angle"] == "Work the Bayes example at this stage."


def test_projection_preserves_description_and_keeps_review_in_its_canonical_owner():
    from learning_os.materials_resolution import project_material_resource

    _, _, _, resource = _angle_case()
    # An already-resolved row still passes through the metadata boundary.
    resource["material_path"] = "materials/demo.pdf"
    projected = project_material_resource(None, resource)
    assert "angle_review" not in projected
    assert projected["angle"] == resource["angle"]
    assert "angle_review" in resource


@pytest.mark.parametrize("change", ["missing-angle", "missing-route", "dangling-route"])
def test_unbound_reviews_are_visible_even_without_a_comparison(change):
    checker, _, _, resource = _angle_case()
    if change == "missing-angle":
        resource.pop("angle")
    elif change == "missing-route":
        resource.pop("route_id")
    else:
        resource["route_id"] = "route-missing"
    checker.check_plan_rigor()
    assert "ANGLE-REVIEW-STALE" in _codes(checker)


@pytest.mark.parametrize("owner,field,value", [
    ("route", "angle", "The source does not teach Bayes."),
    ("route", "covers", ["knowledge-demo-other"]),
    ("route", "source_id", "source-other"),
    ("resource", "locator", "PDF p. 3"),
    ("resource", "angle", "Read a different example."),
    ("stage", "objective", "Do something else."),
    ("stage", "id", "stage-other"),
])
def test_input_changes_invalidate_an_angle_review(owner, field, value):
    checker, route, stage, resource = _angle_case()
    {"route": route, "stage": stage, "resource": resource}[owner][field] = value
    checker.check_plan_rigor()
    assert "ANGLE-REVIEW-STALE" in _codes(checker)


@pytest.mark.parametrize("change", [{"kind": []}, {"kind": "unknown"},
                                  {"rationale": " "}, {"kind": "correction"}])
def test_malformed_or_unevidenced_reviews_never_suppress_a_warning(change):
    checker, _, _, resource = _angle_case()
    resource["angle_review"].update(copy.deepcopy(change))
    checker.check_plan_rigor()
    assert "ANGLE-REVIEW-STALE" in _codes(checker)


def test_correction_requires_the_named_sources_current_bytes(mini_repo):
    from pathlib import Path

    from repo_builders import _sliced_route, _sliced_unit

    from learning_os.loader import load_repo
    from learning_os.material_refs import unit_routes
    from learning_os.materials_resolution import resolve_route_material_files, sha256_file

    _sliced_unit(mini_repo, [_sliced_route("route-demo-book", "lecture-01.pdf")])
    repo = load_repo(mini_repo)
    route = unit_routes(repo.module_source_maps["module-demo"], "module-demo", "unit-demo-l01")[0]
    checker, _, stage, resource = _angle_case()
    checker.repo = repo
    resource["route_id"] = route["id"]
    resolved = resolve_route_material_files(repo, route)[0]
    resource["angle_review"].update(kind="correction", evidence=[{
        "material_uri": resolved.material_uri, "file_sha256": sha256_file(resolved.path),
        "locator": "PDF p. 1",
    }])
    resource["angle_review"]["fingerprint"] = angle_review_fingerprint(route, stage, resource)
    assert checker._angle_review_current(route, stage, resource)
    # A new validation pass must observe changed bytes, not its earlier cache.
    Path(resolved.path).write_bytes(Path(resolved.path).read_bytes() + b"\nchanged source\n")
    fresh_checker, _, _, _ = _angle_case()
    fresh_checker.repo = load_repo(mini_repo)
    assert not fresh_checker._angle_review_current(route, stage, resource)
    resource["angle_review"]["evidence"][0]["material_uri"] = "material://source-other/lecture-01.pdf"
    assert not fresh_checker._angle_review_current(route, stage, resource)
