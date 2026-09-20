from types import SimpleNamespace

from learning_os.rules.plan_rigor import ChecksPlanRigor, _has_unquoted_hedge


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
