import copy
from pathlib import Path
from types import SimpleNamespace

import pytest

from learning_os.derive.validation.plan_rigor import (
    ChecksPlanRigor,
    _has_unquoted_hedge,
    angle_review_fingerprint,
    locator_binding_findings,
)
from learning_os.domain.route_identity import deterministic_route_id


def test_exact_title_may_contain_selection_word():
    locator = (
        "Spring 2022 playlist, Lecture 10 "
        "'Bias/Variance, Regularization, and Model Selection'"
    )
    assert not _has_unquoted_hedge(locator)


def test_unquoted_selection_instruction_remains_vague():
    locator = "Lecture 10 'Model Selection' — selected chapters"
    assert _has_unquoted_hedge(locator)


def _binding_route(rid, locator, file="script.pdf", unit="unit-demo"):
    return {"id": rid, "unit_id": unit, "locator": locator,
            "vault_path": "material://source-demo/" + file}


def test_broadcast_shape_has_duplicate_and_wrong_file_findings():
    rows = [_binding_route("route-script", "sheet.pdf, PDF p. 1"),
            _binding_route("route-sheet", "sheet.pdf, PDF p. 1", "sheet.pdf")]
    findings = locator_binding_findings("module-demo", "source-demo", rows, set())
    assert sorted(code for code, _ in findings) == ["ROUTE-LOCATOR-DUPLICATE", "ROUTE-VAULT-LOCATOR-MISMATCH"]
    assert "route-script" in str(findings)
    assert "route-sheet" in str(findings)


def test_duplicate_locators_are_bounded_by_source_and_unit():
    rows = [_binding_route("route-a", "Ch 2, PDF pp. 1-2"),
            _binding_route("route-b", "Ch 2,  PDF pp. 1-2", unit="unit-other")]
    assert locator_binding_findings("module-demo", "source-demo", rows, set()) == []
    rows[1]["unit_id"] = "unit-demo"
    assert [code for code, _ in locator_binding_findings("module-demo", "source-demo", rows, set())] == ["ROUTE-LOCATOR-DUPLICATE"]


def test_book_style_and_own_filename_with_other_file_are_allowed():
    for locator in ("Chapter 2, PDF pp. 17-50", "script.pdf and sheet.pdf, PDF pp. 1-2"):
        assert not locator_binding_findings("module-demo", "source-demo",
                                            [_binding_route("route-a", locator)], {"sheet.pdf"})


def test_filename_match_uses_whole_names_and_unicode_normalization():
    import unicodedata

    assert not locator_binding_findings("module-demo", "source-demo",
        [_binding_route("route-a", "supersheet.pdf, PDF p. 1")], {"sheet.pdf"})
    name = unicodedata.normalize("NFD", "Überblick.pdf")
    assert not locator_binding_findings("module-demo", "source-demo",
        [_binding_route("route-a", "ÜBERBLICK.PDF, PDF p. 1", name)], {"sheet.pdf"})
    assert [code for code, _ in locator_binding_findings("module-demo", "source-demo",
        [_binding_route("route-a", "sheet.pdf, PDF p. 1")], {"sheet.pdf"})] == ["ROUTE-VAULT-LOCATOR-MISMATCH"]


class _StubChecker(ChecksPlanRigor):
    """Drive the stage/node checks without a repository on disk."""

    def __init__(self, units, study_maps, routes):
        self.repo = SimpleNamespace(units=units, study_maps=study_maps,
                                    module_source_maps={}, modules={})
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
                           data={"stages": [stage]}, authored_data=None)


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


# ------------------------------------------------------------------- scope
class _ScopeChecker(ChecksPlanRigor):
    """Drive the scope rule against one module's own source map.

    The scope rule answers a question the module's map is the record for:
    did this module adopt the material this stage teaches? So the stub
    carries a source map, a module and — because the loaded study map is
    expanded — the authored bytes a compact row was written in.
    """

    def __init__(self, source_map, *, resources, authored=None, modules=None,
                 unit_data=None):
        self.repo = SimpleNamespace(
            root=Path("/nonexistent-scope-checker"),
            units={"unit-demo": SimpleNamespace(data={
                "module_id": "module-demo", **(unit_data or {}),
            })},
            study_maps={"sm": SimpleNamespace(
                path="study-map.yaml",
                unit_id="unit-demo",
                data={"stages": [{"id": "stage-demo", "resources": resources}]},
                authored_data=authored,
            )},
            module_source_maps={"module-demo": source_map},
            module_source_map_origins={"module-demo": "source-map.yaml"},
            modules={"module-demo": {"status": "enrolled"}}
            if modules is None else modules,
        )
        self.warnings = []
        self._routes = {}

    def _routes_by_id(self):
        return self._routes

    def warn(self, code, message, where):
        self.warnings.append((code, message))

    def err(self, code, message, where):  # pragma: no cover
        raise AssertionError(f"unexpected error {code}: {message}")

    def _rel(self, path):
        return str(path)


def _demo_route(locator="Chapter 2, PDF pp. 17-50"):
    return {
        "unit_id": "unit-demo",
        "title": "Demo book — expected-value derivation",
        "format": "book",
        "angle": "Derives the weighted sum.",
        "angle_detail": "Works one discrete example end to end.",
        "covers": [],
        "depth": "derivation",
        "scope": "current",
        "locator": locator,
    }


def _demo_source_map(*routes):
    return {
        "module_id": "module-demo",
        "sources": [{
            "source_id": "source-demo-book",
            "unit_routes": list(routes),
        }],
    }


def _demo_route_id(route):
    return deterministic_route_id("module-demo", "source-demo-book", route)


def test_a_resource_naming_a_source_the_module_never_adopted_is_reported():
    """The F-01 shape: a globally registered source on a stage of a module
    whose source map never declared it."""
    checker = _ScopeChecker(
        _demo_source_map(_demo_route()),
        resources=[{
            "kind": "read",
            "label": "Probe Book chapter 42",
            "source_id": "source-probe-offmap",
            "locator": "chapter 42",
        }],
    )
    checker.check_plan_rigor()
    assert _codes(checker) == ["RESOURCE-SCOPE-UNBOUND"]
    assert "source-probe-offmap" in checker.warnings[0][1]


def test_a_resource_bound_to_a_module_route_is_not_reported():
    route = _demo_route()
    checker = _ScopeChecker(
        _demo_source_map(route),
        resources=[{
            "kind": "read",
            "label": "Demo Book §1",
            "source_id": "source-demo-book",
            "locator": "§1",
            "route_id": _demo_route_id(route),
        }],
    )
    checker.check_plan_rigor()
    assert checker.warnings == []


def test_a_resource_matching_a_module_route_by_source_and_locator_is_not_reported():
    route = _demo_route()
    checker = _ScopeChecker(
        _demo_source_map(route),
        resources=[{
            "kind": "read",
            "label": "Demo Book §1",
            "source_id": "source-demo-book",
            "locator": route["locator"],
        }],
    )
    checker.check_plan_rigor()
    assert checker.warnings == []


def test_spelling_a_sibling_units_material_does_not_bypass_route_ownership():
    sibling_route = {**_demo_route(), "unit_id": "unit-sibling"}
    checker = _ScopeChecker(
        _demo_source_map(sibling_route),
        resources=[{
            "kind": "read", "source_id": "source-demo-book",
            "locator": sibling_route["locator"],
        }],
    )
    checker.check_plan_rigor()
    assert _codes(checker) == ["RESOURCE-SCOPE-UNBOUND"]


def test_shared_material_still_resolves_when_the_owning_unit_declares_it():
    own = _demo_route()
    sibling = {**own, "unit_id": "unit-sibling"}
    checker = _ScopeChecker(
        _demo_source_map(own, sibling),
        resources=[{
            "kind": "read", "source_id": "source-demo-book",
            "locator": own["locator"],
        }],
    )
    checker.check_plan_rigor()
    assert checker.warnings == []


@pytest.mark.parametrize("field", ["source_selections", "scope_sources"])
def test_scope_message_preserves_the_units_recorded_disposition(field):
    checker = _ScopeChecker(
        _demo_source_map("unit-demo"),
        resources=[{
            "kind": "read", "source_id": "source-demo-book", "locator": "§9",
        }],
        unit_data={field: [{"source_id": "source-demo-book"}]},
    )
    checker.check_plan_rigor()
    assert _codes(checker) == ["RESOURCE-SCOPE-UNBOUND"]
    assert "source disposition is recorded" in checker.warnings[0][1]
    assert "no route for this unit" in checker.warnings[0][1]


def test_scope_message_distinguishes_module_adoption_from_unit_disposition():
    checker = _ScopeChecker(
        _demo_source_map("unit-demo"),
        resources=[{
            "kind": "read", "source_id": "source-demo-book", "locator": "§9",
        }],
    )
    checker.check_plan_rigor()
    message = checker.warnings[0][1]
    assert "module declares this source" in message
    assert "unit has no recorded source disposition" in message
    assert "adopt the source" not in message


def test_scope_message_does_not_claim_an_unnamed_source_was_not_adopted():
    checker = _ScopeChecker(
        _demo_source_map(),
        resources=[{"kind": "exercise", "locator": "attachments/own-work.md"}],
    )
    checker.check_plan_rigor()
    assert "no source_id is named" in checker.warnings[0][1]
    assert "module adoption cannot be checked" in checker.warnings[0][1]


def test_a_reference_row_may_point_outside_the_module_map():
    """`kind: reference` is a pointer, and pointing outside the map is what
    it is for. `scope_triage` is not the exemption: a writer of the row
    also sets that flag, so an exemption on it would be an opt-out."""
    checker = _ScopeChecker(
        _demo_source_map(_demo_route()),
        resources=[{
            "kind": "reference",
            "label": "Full bibliography — preserved, not read for this stage",
            "source_id": "source-probe-offmap",
            "locator": "chapter 42",
            "scope_triage": "reference-only",
        }],
    )
    checker.check_plan_rigor()
    assert checker.warnings == []


def test_a_compact_row_bound_to_a_module_route_is_not_reported():
    """The loaded map is expanded: `material_ref` is popped and its
    inherited fields are copied onto the resource, so the route binding
    survives only in the authored bytes. The rule resolves it there."""
    route = _demo_route()
    checker = _ScopeChecker(
        _demo_source_map(route),
        resources=[{
            "kind": "read",
            "label": "Demo Book §1",
            "source_id": "source-demo-book",
            "locator": route["locator"],
        }],
        authored={"stages": [{"id": "stage-demo", "resources": [{
            "material_ref": {
                "route_id": _demo_route_id(route),
                "inherit": ["label", "source_id", "locator"],
            },
        }]}]},
    )
    checker.check_plan_rigor()
    assert checker.warnings == []


def test_a_compact_row_naming_a_route_of_another_module_is_reported():
    """A `material_ref` that names no route of the owning module is
    material the module never adopted, and the rule says so by name."""
    foreign = deterministic_route_id(
        "module-other", "source-other-book", _demo_route())
    checker = _ScopeChecker(
        _demo_source_map(_demo_route()),
        resources=[{
            "kind": "read",
            "label": "Other module's book",
            "source_id": "source-other-book",
            "locator": "§1",
        }],
        authored={"stages": [{"id": "stage-demo", "resources": [{
            "material_ref": {
                "route_id": foreign,
                "inherit": ["label", "source_id", "locator"],
            },
        }]}]},
    )
    checker.check_plan_rigor()
    assert _codes(checker) == ["RESOURCE-SCOPE-UNBOUND"]
    assert foreign in checker.warnings[0][1]


def test_an_archived_module_is_not_scope_checked():
    """An archived module keeps its source map as history, not as an
    active learning surface."""
    checker = _ScopeChecker(
        _demo_source_map(_demo_route()),
        resources=[{
            "kind": "read",
            "label": "Probe Book chapter 42",
            "source_id": "source-probe-offmap",
            "locator": "chapter 42",
        }],
        modules={"module-demo": {"status": "archived"}},
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
    from learning_os.store.materials.resolution import project_material_resource

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


def _correction_case(mini_repo):
    """A correction review over a sliced unit, with its evidence bytes on disk."""
    from repo_builders import _sliced_route, _sliced_unit

    from learning_os.domain.material_refs import unit_routes
    from learning_os.store.loader import load_repo
    from learning_os.store.materials.resolution import resolve_route_material_files, sha256_file

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
    return checker, repo, route, stage, resource, resolved


def test_correction_requires_the_named_sources_current_bytes(mini_repo):
    from pathlib import Path

    from learning_os.store.loader import load_repo

    checker, _, route, stage, resource, resolved = _correction_case(mini_repo)
    assert checker._angle_review_current(route, stage, resource) == "current"
    # A new validation pass must observe changed bytes, not its earlier cache.
    Path(resolved.path).write_bytes(Path(resolved.path).read_bytes() + b"\nchanged source\n")
    fresh_checker, _, _, _ = _angle_case()
    fresh_checker.repo = load_repo(mini_repo)
    assert fresh_checker._angle_review_current(route, stage, resource) == "stale"
    resource["angle_review"]["evidence"][0]["material_uri"] = "material://source-other/lecture-01.pdf"
    assert fresh_checker._angle_review_current(route, stage, resource) == "stale"


def test_correction_with_changed_bytes_is_stale_when_mounted(mini_repo):
    """Online, bytes present and different is stale — and a baseline regression."""
    from collections import Counter

    from learning_os.domain.validation import Issue
    from learning_os.store.warning_baseline import delta, signatures_from_issues

    checker, repo, route, stage, resource, resolved = _correction_case(mini_repo)
    assert checker._angle_review_current(route, stage, resource) == "current"
    resolved.path.write_bytes(resolved.path.read_bytes() + b"\nchanged source\n")
    fresh_checker, _, _, _ = _angle_case()
    fresh_checker.repo = repo
    assert fresh_checker._angle_review_current(route, stage, resource) == "stale"
    fresh_checker._check_row_angle("sm", stage, resource, {route["id"]: route}, "study-map.yaml")
    assert "ANGLE-REVIEW-STALE" in _codes(fresh_checker)
    # The emitted warning survives the exempt filter and fails the gate as new.
    issues = [Issue("W", code, message, "study-map.yaml")
              for code, message in fresh_checker.warnings]
    current, errors = signatures_from_issues(issues)
    assert errors == []
    regressions, _ = delta(Counter(), current)
    assert any("ANGLE-REVIEW-STALE" in line for line in regressions)


def test_correction_with_absent_evidence_is_unverifiable_not_stale(mini_repo):
    """The CI shape: the evidence file is not on this machine, so the review
    is unverifiable — the content did not change, only the mount did."""
    checker, _, route, stage, resource, resolved = _correction_case(mini_repo)
    assert checker._angle_review_current(route, stage, resource) == "current"
    resolved.path.unlink()
    assert checker._angle_review_current(route, stage, resource) == "unverifiable"
    checker._check_row_angle("sm", stage, resource, {route["id"]: route}, "study-map.yaml")
    assert "ANGLE-REVIEW-UNVERIFIED" in _codes(checker)
    assert "ANGLE-REVIEW-STALE" not in _codes(checker)


def test_correction_with_materials_root_offline_is_unverifiable(mini_repo):
    """The whole materials tree absent reads the same as one file absent."""
    import shutil

    checker, _, route, stage, resource, _ = _correction_case(mini_repo)
    assert checker._angle_review_current(route, stage, resource) == "current"
    shutil.rmtree(mini_repo.parent / "materials")
    assert checker._angle_review_current(route, stage, resource) == "unverifiable"
    checker._check_row_angle("sm", stage, resource, {route["id"]: route}, "study-map.yaml")
    assert "ANGLE-REVIEW-UNVERIFIED" in _codes(checker)
    assert "ANGLE-REVIEW-STALE" not in _codes(checker)


def test_fingerprint_mismatch_is_stale_online_and_offline(mini_repo):
    """A changed input is stale in both environments — offline never excuses it."""
    checker, _, route, stage, resource, resolved = _correction_case(mini_repo)
    resource["angle"] = "Read a different example."
    assert checker._angle_review_current(route, stage, resource) == "stale"
    resolved.path.unlink()
    assert checker._angle_review_current(route, stage, resource) == "stale"


def test_frozen_broadcast_has_exact_historical_findings_and_repaired_rows_have_none():
    from pathlib import Path

    import yaml

    fixture = yaml.safe_load((Path(__file__).parent / "fixtures/m2-broadcast-2026-09-12.yaml").read_text())
    old = locator_binding_findings(fixture["module_id"], fixture["source_id"],
        fixture["revisions"]["damaged"]["routes"], {"ana_inf_serie05.pdf", "unser skript.pdf"})
    assert sum(code == "ROUTE-LOCATOR-DUPLICATE" for code, _ in old) == 2
    assert sum(code == "ROUTE-VAULT-LOCATOR-MISMATCH" for code, _ in old) == 3
    duplicates = [message for code, message in old if code == "ROUTE-LOCATOR-DUPLICATE"]
    assert sum(message.count("route-an-") for message in duplicates) == 6
    assert locator_binding_findings(fixture["module_id"], fixture["source_id"],
        fixture["revisions"]["repaired"]["routes"], {"ana_inf_serie05.pdf", "unser skript.pdf"}) == []


@pytest.mark.parametrize(("name", "locator"), [
    ("script.pdf", "script.pdf p. 3"),
    ("script.pdf", "see myscript.pdf p. 3"),
    ("script.pdf", "script.pdfx"),
    ("script.pdf", "Lecture 2, slides"),
    ("a.pdf", "a.pdf, b.pdf"),
    ("b.pdf", "a.pdf,b.pdf"),
    ("ü.pdf", "ü.pdf"),
    ("", "anything"),
    ("", ""),
])
def test_filename_present_prefilter_never_changes_the_answer(name, locator):
    """The substring pre-filter is only a cost guard: the boundary regex decides."""
    import re

    from learning_os.derive.validation.plan_rigor import _filename_present

    expected = bool(re.search(r"(?<!\w)" + re.escape(name) + r"(?!\w)", locator))
    assert _filename_present(name, locator) is expected


def test_overnight_compact_route_binding_reaches_angle_and_node_checks():
    route = {"id": "route-bound", "angle": "Original angle", "covers": ["node-original"]}
    resource = {"angle": "Changed angle", "locator": "Overridden locator"}
    checker = _StubChecker({}, {}, {})
    checker._check_row_angle("sm", {"id": "stage-demo"}, resource, {"route-bound": route}, "map",
                             material_route_id="route-bound")
    checker._check_row_node("sm", {"id": "stage-demo"}, "node-new", resource,
                            {"route-bound": route}, "map", material_route_id="route-bound")
    assert {code for code, _ in checker.warnings} == {"ANGLE-DIVERGES-FROM-ROUTE", "RESOURCE-NODE-ORPHAN"}


def test_overnight_fused_locator_does_not_hide_later_resources():
    checker = _StubChecker({"unit-demo": _unit("node-a")}, {"sm": _map({
        "id": "stage-demo", "knowledge_node_id": "node-a", "resources": [
            {"locator": "Ch 1 — an intuitive explanation of these examples."},
            {"route_id": "route-second", "angle": "Different"}]} )},
        {"route-second": {"angle": "Original", "covers": []}})
    errors = []
    checker.err = lambda code, *_: errors.append(code)
    checker.check_plan_rigor()
    assert "LOCATOR-ANGLE-FUSED" in errors
    assert "ANGLE-DIVERGES-FROM-ROUTE" in {code for code, _ in checker.warnings}


def test_overnight_rigor_indexes_legacy_route_ids():
    route = _demo_route()
    checker = _ScopeChecker(_demo_source_map(route), resources=[])
    index = ChecksPlanRigor._routes_by_id(checker)
    assert deterministic_route_id("module-demo", "source-demo-book", route) in index
