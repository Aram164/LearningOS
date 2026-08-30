"""The module-plan preflight applies the repository's warning policy, not a stricter one.

`module-plan-import --check` validates the planned writes in a shadow copy of
the whole repository. Until 2026-08-29 it refused the plan if that validation
produced *any* warning outside the eight environmental codes — which made it
unsatisfiable, because the 535 baselined warnings of CRITIQUE-POINTS §1 live in
the source maps. One module's plan import failed on another module's deferred
locators, and the failure was indistinguishable from a real defect in the plan.

The policy the rest of the repository runs on is in `learning_os.warning_baseline`
and in CLAUDE.md hard rule 9: zero errors, warnings stay visible and never
block, no NEW warning signature and no existing signature that grows. These
tests pin that the preflight now enforces exactly that — still refusing a plan
that *introduces* a warning, which is the part worth keeping.
"""

from __future__ import annotations

import yaml
from test_curriculum_v2 import _add_material_overview, add_curriculum

from learning_os.commands.module import _module_plan_validation_errors
from learning_os.warning_baseline import collect, write_baseline

SOURCE_MAP = "curriculum/modules/module-demo/source-map.yaml"


def _prepared(root):
    """A valid synthetic curriculum whose one book route has a vague locator.

    `lecture-01.pdf` names a file and no page range, so it raises LOCATOR-VAGUE
    — the same content-debt warning the real repository has 535 of. That is the
    condition under test, not an accident of the fixture.
    """
    add_curriculum(root)
    _add_material_overview(root)
    signatures, errors = collect(root)
    assert errors == [], f"fixture must start error-free, got {errors}"
    assert signatures, "fixture must raise at least one baseline-managed warning"
    return signatures


def test_a_deferred_warning_does_not_refuse_an_unrelated_plan(mini_repo):
    signatures = _prepared(mini_repo)
    write_baseline(mini_repo, signatures, "test fixture")

    assert _module_plan_validation_errors(mini_repo, {}) == []


def test_a_warning_the_plan_introduces_is_still_refused(mini_repo):
    signatures = _prepared(mini_repo)
    write_baseline(mini_repo, signatures, "test fixture")

    source_map = yaml.safe_load((mini_repo / SOURCE_MAP).read_text(encoding="utf-8"))
    route = source_map["sources"][0]["unit_routes"][0]
    source_map["sources"][0]["unit_routes"].append(
        dict(route, title="A second vague route", locator="Chapter 4"))
    planned = {mini_repo / SOURCE_MAP: yaml.safe_dump(source_map, sort_keys=False)}

    failures = _module_plan_validation_errors(mini_repo, planned)

    assert failures, "a plan that adds a vague locator must be refused"
    assert any("NEW-OR-GROWN-WARNING" in line and "LOCATOR-VAGUE" in line
               for line in failures), failures


def test_a_signature_that_grows_is_refused_even_though_its_code_is_baselined(mini_repo):
    """The gate is (code, path) with multiplicity, so a second instance still fails."""
    signatures = _prepared(mini_repo)
    write_baseline(mini_repo, signatures, "test fixture")
    before = signatures[("LOCATOR-VAGUE", SOURCE_MAP)]

    source_map = yaml.safe_load((mini_repo / SOURCE_MAP).read_text(encoding="utf-8"))
    route = source_map["sources"][0]["unit_routes"][0]
    source_map["sources"][0]["unit_routes"].append(
        dict(route, title="Another route with the same defect", locator="Chapter 9"))
    planned = {mini_repo / SOURCE_MAP: yaml.safe_dump(source_map, sort_keys=False)}

    failures = _module_plan_validation_errors(mini_repo, planned)

    assert any(f"LOCATOR-VAGUE at {SOURCE_MAP}: {before} → {before + 1}" in line
               for line in failures), failures


def test_an_error_still_refuses_the_plan_whatever_the_baseline_says(mini_repo):
    signatures = _prepared(mini_repo)
    write_baseline(mini_repo, signatures, "test fixture")

    source_map = yaml.safe_load((mini_repo / SOURCE_MAP).read_text(encoding="utf-8"))
    source_map["sources"][0]["unit_routes"][0]["covers"] = ["knowledge-demo-missing"]
    planned = {mini_repo / SOURCE_MAP: yaml.safe_dump(source_map, sort_keys=False)}

    failures = _module_plan_validation_errors(mini_repo, planned)

    assert any("REF-KNOWLEDGE" in line for line in failures), failures
