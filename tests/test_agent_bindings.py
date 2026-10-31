"""Pure binding types and resolution: every branch, no repository (S12).

The slot declarations (S13) are additionally checked against real handler
output on the rich_world fixture, and the binding admission grammar (S14)
against the real runner on a mini repository.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
from repo_builders import add_curriculum

from learning_os.domain.agent_bindings import (
    BindingError,
    CompiledRef,
    OutputSlot,
    resolve,
    rows_of,
)
from learning_os.domain.codes import (
    BINDING_CARDINALITY,
    BINDING_EMPTY,
    BINDING_VALUE_INVALID,
)
from learning_os.domain.ids import is_valid

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("agent_run_bindings", ROOT / "tools/agent_run.py")
agent_run = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(agent_run)


def _record_slot(**overrides):
    base = {"path": ("*",), "kind": None, "value_key": "id",
            "columns": ("id", "type", "title", "status"), "kind_column": "type"}
    base.update(overrides)
    return OutputSlot(**base)


def _payload(*rows):
    return list(rows)


def test_rows_of_walks_dicts_lists_and_scalars():
    slot = OutputSlot(path=("module_id",), kind="module")
    assert rows_of({"module_id": "module-demo"}, slot) == ["module-demo"]
    assert rows_of({"other": 1}, slot) == []
    nested = OutputSlot(path=("artifacts", "ultimate_reference"), kind="note")
    assert rows_of({"artifacts": {"ultimate_reference": "note-demo"}}, nested) == ["note-demo"]
    assert rows_of({"artifacts": {}}, nested) == []
    expanded = _record_slot()
    assert rows_of(_payload({"id": "unit-a"}, {"id": "unit-b"}), expanded) == [
        {"id": "unit-a"}, {"id": "unit-b"}]
    assert rows_of({"not": "a list"}, expanded) == []


def test_rows_of_expands_nested_lists_with_parent_columns():
    slot = OutputSlot(path=("*", "matched_stages", "*"), kind="stage", value_key="id",
                      columns=("id", "title", "unit_id"),
                      parent_columns={"unit_id": "id"})
    payload = _payload({"id": "unit-a", "matched_stages": [{"id": "stage-a1"}, {"id": "stage-a2"}]},
                       {"id": "unit-b", "matched_stages": []})
    rows = rows_of(payload, slot)
    assert rows == [{"unit_id": "unit-a", "id": "stage-a1"},
                    {"unit_id": "unit-a", "id": "stage-a2"}]
    # A row's own field wins over the copied parent field.
    payload = _payload({"id": "unit-a", "matched_stages": [{"id": "stage-a1", "unit_id": "own"}]})
    assert rows_of(payload, slot) == [{"unit_id": "own", "id": "stage-a1"}]


def _ref(slot, where=None, source="a", param="unit_id"):
    return CompiledRef(param=param, source=source, slot_name="record" if source else None,
                       slot=slot if source else None, where=where or {})


def test_resolve_filters_by_where_and_extracts_value_key():
    slot = _record_slot()
    payload = _payload({"id": "module-demo", "type": "module", "title": "Demo"},
                       {"id": "unit-demo-l01", "type": "unit", "title": "L01"})
    ref = _ref(slot, where={"type": "unit"})
    assert resolve(ref, payload, "unit") == "unit-demo-l01"


def test_resolve_empty_rows_refuse_with_binding_empty():
    slot = _record_slot()
    payload = _payload({"id": "module-demo", "type": "module", "title": "Demo"})
    with pytest.raises(BindingError) as exc:
        resolve(_ref(slot, where={"type": "unit"}), payload, "unit")
    assert exc.value.code == BINDING_EMPTY
    assert exc.value.as_dict()["code"] == BINDING_EMPTY
    assert "candidates" not in exc.value.as_dict()


def test_resolve_cardinality_lists_at_most_five_candidates():
    slot = _record_slot()
    payload = _payload(*[{"id": f"unit-{i}", "type": "unit", "title": f"T{i}"} for i in range(7)])
    with pytest.raises(BindingError) as exc:
        resolve(_ref(slot, where={"type": "unit"}), payload, "unit")
    assert exc.value.code == BINDING_CARDINALITY
    candidates = exc.value.as_dict()["candidates"]
    assert len(candidates) == 5
    assert candidates[0] == {"id": "unit-0", "title": "T0"}
    assert all(set(candidate) == {"id", "title"} for candidate in candidates)


def test_resolve_scalar_slot_takes_the_row_itself():
    slot = OutputSlot(path=("module_id",), kind="module")
    assert resolve(_ref(slot, param="module_id"), {"module_id": "module-demo"}, "module") \
        == "module-demo"


def test_resolve_value_must_match_the_slot_kind():
    slot = _record_slot()
    payload = _payload({"id": "stage-x", "type": "unit", "title": "T"})
    with pytest.raises(BindingError) as exc:
        resolve(_ref(slot, where={"type": "unit"}), payload, "unit")
    assert exc.value.code == BINDING_VALUE_INVALID


def test_resolve_star_target_accepts_any_generic_kind_only():
    slot = _record_slot()
    payload = _payload({"id": "unit-demo-l01", "type": "unit", "title": "T"})
    assert resolve(_ref(slot, where={"type": "unit"}, param="id"), payload, "*") == "unit-demo-l01"
    payload = _payload({"id": "transaction-20261026-105325-001", "type": "module", "title": "T"})
    with pytest.raises(BindingError) as exc:
        resolve(_ref(slot, where={"type": "module"}, param="id"), payload, "*")
    assert exc.value.code == BINDING_VALUE_INVALID


def test_resolve_kind_column_slot_derives_kind_from_where():
    slot = _record_slot()
    # The where value both filters rows and names the static kind; a row that
    # matches the filter but carries a non-id value refuses on the derived kind.
    payload = _payload({"id": "--root=/etc", "type": "stage", "title": "T"})
    with pytest.raises(BindingError) as exc:
        resolve(_ref(slot, where={"type": "stage"}), payload, "stage")
    assert exc.value.code == BINDING_VALUE_INVALID
    payload = _payload({"id": "unit-demo-l01", "type": "unit", "title": "T"})
    with pytest.raises(BindingError) as exc:
        resolve(_ref(slot, where={"type": "stage"}), payload, "stage")
    assert exc.value.code == BINDING_EMPTY


def test_resolve_literal_ref_is_validated_against_the_target_kind():
    literal = CompiledRef(param="route_id", source=None, slot_name=None, slot=None,
                          where={}, literal="route-demo")
    assert resolve(literal, None, "route") == "route-demo"
    bad = CompiledRef(param="route_id", source=None, slot_name=None, slot=None,
                      where={}, literal="--root=/etc")
    with pytest.raises(BindingError) as exc:
        resolve(bad, None, "route")
    assert exc.value.code == BINDING_VALUE_INVALID
    star = CompiledRef(param="id", source=None, slot_name=None, slot=None,
                       where={}, literal="stage-demo")
    assert resolve(star, None, "*") == "stage-demo"


def test_binding_error_carries_code_message_candidates():
    error = BindingError(BINDING_CARDINALITY, "two rows", candidates=[{"id": "a", "title": "A"}])
    assert error.code == BINDING_CARDINALITY
    assert error.as_dict() == {"code": BINDING_CARDINALITY, "message": "two rows",
                               "candidates": [{"id": "a", "title": "A"}]}
    plain = BindingError(BINDING_EMPTY, "none")
    assert plain.as_dict() == {"code": BINDING_EMPTY, "message": "none"}


def _read_payload(root, argv):
    from learning_os.adapters.cli import invoke_outcome
    from learning_os.adapters.cli_parser import build_parser

    namespace = build_parser().parse_args(["--root", str(root), *argv])
    outcome = invoke_outcome(namespace)
    assert outcome.exit_code == 0, (argv, outcome.stdout, outcome.stderr)
    return json.loads(outcome.stdout)


def test_declared_slots_hold_real_output(mini_repo):
    """Every declared slot yields rows of its declared shape on rich_world."""
    from scenario_fixtures import rich_world

    from learning_os.app.registry import REGISTRY

    rich_world(mini_repo)
    search = _read_payload(mini_repo, ["search", "expected value", "--type", "unit", "--json"])
    stage_payload = _read_payload(mini_repo, ["inspect", "stage-demo", "--json"])
    unit_payload = _read_payload(mini_repo, ["inspect", "unit-demo-l01", "--json"])
    units = _read_payload(mini_repo, ["unit-list", "--module-id", "module-demo", "--json"])
    modules = _read_payload(mini_repo, ["module-list", "--json"])
    brief = _read_payload(mini_repo, ["plan-edit-context", "unit-demo-l01", "--brief", "--json"])
    cases = [
        ("note.search", "record", search),
        ("note.search", "matched_stage", search),
        ("unit.list", "unit", units),
        ("module.list", "module", modules),
        ("project.inspect", "module", stage_payload),
        ("project.inspect", "unit", stage_payload),
        ("project.inspect", "ultimate_reference", unit_payload),
        ("plan.edit-context", "unit", brief),
        ("plan.edit-context", "module", brief),
        ("plan.edit-context", "stage", brief),
        ("plan.edit-context", "route", brief),
    ]
    for operation, name, payload in cases:
        slot = REGISTRY[operation].output_slots[name]
        rows = rows_of(payload, slot)
        assert rows, (operation, name)
        for row in rows:
            if slot.value_key is not None:
                assert isinstance(row, dict) and isinstance(row.get(slot.value_key), str), \
                    (operation, name, row)
                kind = slot.kind if slot.kind is not None else row.get(slot.kind_column)
                assert is_valid(kind, row[slot.value_key]), (operation, name, row)
            else:
                assert isinstance(row, str) and is_valid(slot.kind, row), \
                    (operation, name, row)


def test_binding_params_declare_the_non_id_kind_params():
    from learning_os.app.registry import REGISTRY

    assert REGISTRY["project.inspect"].binding_params == {"id": "*"}
    assert REGISTRY["study.sequence"].binding_params == {"stage_ids_json": "stage[]"}
    assert REGISTRY["note.search"].binding_params == {}


def test_catalog_carries_slots_and_plan_example(mini_repo):
    from learning_os.adapters.cli_parser import build_parser
    from learning_os.app.agent_catalog import READ_VERBS, build_catalog
    from learning_os.app.registry import REGISTRY

    choices = build_parser()._subparsers._group_actions[0].choices  # noqa: SLF001
    verb_to_operation = {name: getattr(sub, "_defaults", {}).get("_operation")
                         for name, sub in choices.items()}
    catalog = build_catalog(mini_repo, verb_to_operation)
    assert catalog["plan_example"]["schema_version"] == 3
    assert catalog["plan_example"]["steps"][1]["bind"]["unit_id"]["slot"] == "record"
    by_verb = {row["verb"]: row for row in catalog["reads"]}
    assert [row["verb"] for row in catalog["reads"]] == list(READ_VERBS)
    search_row = by_verb["search"]
    assert search_row["slots"] == [
        {"name": "record", "kind": None, "columns": ["id", "type", "title", "status"],
         "kind_column": "type"},
        {"name": "matched_stage", "kind": "stage", "columns": ["id", "title", "unit_id"]},
    ]
    assert by_verb["inspect"]["slots"][0]["name"] == "module"
    for row in catalog["reads"]:
        for slot in row["slots"]:
            assert slot["name"] in REGISTRY[row["operation"]].output_slots



# ---------------------------------------------------------------------------
# S14 admission grammar (S17 adversarial cases 01-13). Each asserts the
# refusal code or reason, and where the case demands it, that no step ran.

def _v3_plan(steps, session="s"):
    return {"schema_version": 3, "session_id": session, "steps": steps}


def _code_of(report, index):
    return report["steps"][index]["error"]["code"]


def test_adversarial_01_unknown_plan_field_refuses_before_any_step(mini_repo):
    add_curriculum(mini_repo)
    plan = {"schema_version": 3, "read_worker": 2,
            "steps": [{"id": "a", "use": "inspect", "args": ["note-demo"]}]}
    with pytest.raises(agent_run.AgentRunError, match="unknown plan fields"):
        agent_run.run_plan(plan, mini_repo)


def test_adversarial_02_unknown_step_field_refuses(mini_repo):
    add_curriculum(mini_repo)
    plan = {"steps": [{"id": "a", "use": "inspect", "args": ["note-demo"], "effect": "read"}]}
    with pytest.raises(agent_run.AgentRunError, match="unknown step fields"):
        agent_run.run_plan(plan, mini_repo)


def test_adversarial_03_unknown_reference_field_refuses_binding_invalid(mini_repo):
    add_curriculum(mini_repo)
    plan = _v3_plan([
        {"id": "a", "use": "search", "args": ["demo"]},
        {"id": "b", "use": "inspect", "bind": {"id": {"path": "$.results[0].id"}}},
    ])
    with pytest.raises(agent_run.AgentRunError) as excinfo:
        agent_run.run_plan(plan, mini_repo)
    assert excinfo.value.code == "BINDING_INVALID"


def test_adversarial_04_bind_under_schema_2_refuses(mini_repo):
    add_curriculum(mini_repo)
    plan = {"schema_version": 2, "steps": [
        {"id": "a", "use": "search", "args": ["demo"]},
        {"id": "b", "use": "inspect", "bind": {"id": {"from": "a", "slot": "record"}}},
    ]}
    with pytest.raises(agent_run.AgentRunError) as excinfo:
        agent_run.run_plan(plan, mini_repo)
    assert excinfo.value.code == "BINDING_INVALID"
    assert "schema_version 3" in str(excinfo.value)


def test_adversarial_05_write_target_refuses_and_runs_nothing(mini_repo):
    add_curriculum(mini_repo)
    plan = _v3_plan([
        {"id": "a", "use": "search", "args": ["demo"]},
        {"id": "b", "use": "unit-map-import",
         "bind": {"unit_id": {"from": "a", "slot": "record", "where": {"type": "unit"}}}},
    ])
    report = agent_run.run_plan(plan, mini_repo)
    assert _code_of(report, 1) == "BINDING_INVALID"
    assert report["totals"]["ok"] == 0
    assert all(row["status"] in ("error", "skipped") for row in report["steps"])


def test_adversarial_06_capability_target_refuses_and_runs_nothing(mini_repo):
    add_curriculum(mini_repo)
    plan = _v3_plan([
        {"id": "a", "use": "search", "args": ["demo"]},
        {"id": "b", "use": "capability",
         "bind": {"text": {"from": "a", "slot": "record", "where": {"type": "unit"}}}},
    ])
    report = agent_run.run_plan(plan, mini_repo)
    assert _code_of(report, 1) == "BINDING_INVALID"
    assert report["totals"]["ok"] == 0


def test_adversarial_07_write_source_refuses(mini_repo):
    add_curriculum(mini_repo)
    write_hinted = _v3_plan([
        {"id": "w", "use": "inspect", "args": ["note-demo"], "write": True},
        {"id": "b", "use": "plan-edit-context", "args": ["--brief"],
         "bind": {"unit_id": {"from": "w", "slot": "unit"}}},
    ])
    report = agent_run.run_plan(write_hinted, mini_repo)
    assert _code_of(report, 1) == "BINDING_INVALID"
    assert report["totals"]["ok"] == 0
    log_source = _v3_plan([
        {"id": "w", "kind": "log", "text": "alpha fixture log", "key": "adv-07"},
        {"id": "b", "use": "plan-edit-context", "args": ["--brief"],
         "bind": {"unit_id": {"from": "w", "slot": "unit"}}},
    ])
    report = agent_run.run_plan(log_source, mini_repo)
    assert _code_of(report, 1) == "BINDING_INVALID"
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))


def test_adversarial_08_content_or_page_source_refuses(mini_repo):
    add_curriculum(mini_repo)
    for flag in ("--content", "--page"):
        plan = _v3_plan([
            {"id": "a", "use": "search", "args": ["demo", flag]},
            {"id": "b", "use": "plan-edit-context", "args": ["--brief"],
             "bind": {"unit_id": {"from": "a", "slot": "record", "where": {"type": "unit"}}}},
        ])
        report = agent_run.run_plan(plan, mini_repo)
        assert _code_of(report, 1) == "BINDING_INVALID", flag
        assert report["totals"]["ok"] == 0


def test_adversarial_09_declared_effect_field_is_unknown(mini_repo):
    add_curriculum(mini_repo)
    plan = {"steps": [{"id": "w", "use": "capture", "args": ["alpha fixture log"],
                       "effect": "read"}]}
    with pytest.raises(agent_run.AgentRunError, match="unknown step fields"):
        agent_run.run_plan(plan, mini_repo)


def test_adversarial_10_stage_slot_on_unit_param_refuses_at_admission(mini_repo):
    add_curriculum(mini_repo)
    plan = _v3_plan([
        {"id": "a", "use": "search", "args": ["demo", "--type", "unit"]},
        {"id": "b", "use": "plan-edit-context",
         "bind": {"unit_id": {"from": "a", "slot": "matched_stage"}}, "args": []},
    ])
    report = agent_run.run_plan(plan, mini_repo)
    assert _code_of(report, 1) == "BINDING_INVALID"
    assert report["totals"]["ok"] == 0


def test_adversarial_11_undeclared_slot_refuses(mini_repo):
    add_curriculum(mini_repo)
    plan = _v3_plan([
        {"id": "a", "use": "search", "args": ["demo", "--type", "unit"]},
        {"id": "b", "use": "plan-edit-context",
         "bind": {"unit_id": {"from": "a", "slot": "no_such_slot"}}, "args": []},
    ])
    report = agent_run.run_plan(plan, mini_repo)
    assert _code_of(report, 1) == "BINDING_INVALID"
    assert "no_such_slot" in report["steps"][1]["error"]["message"]


def test_adversarial_12_where_on_undeclared_column_refuses(mini_repo):
    add_curriculum(mini_repo)
    plan = _v3_plan([
        {"id": "a", "use": "search", "args": ["demo", "--type", "unit"]},
        {"id": "b", "use": "plan-edit-context",
         "bind": {"unit_id": {"from": "a", "slot": "record", "where": {"path": "x"}}},
         "args": []},
    ])
    report = agent_run.run_plan(plan, mini_repo)
    assert _code_of(report, 1) == "BINDING_INVALID"
    assert report["totals"]["ok"] == 0


def test_adversarial_13_forward_and_self_reference_refuse(mini_repo):
    add_curriculum(mini_repo)
    forward = _v3_plan([
        {"id": "b", "use": "plan-edit-context",
         "bind": {"unit_id": {"from": "a", "slot": "record", "where": {"type": "unit"}}},
         "args": []},
        {"id": "a", "use": "search", "args": ["demo", "--type", "unit"]},
    ])
    with pytest.raises(agent_run.AgentRunError) as excinfo:
        agent_run.run_plan(forward, mini_repo)
    assert excinfo.value.code == "BINDING_INVALID"
    self_ref = _v3_plan([
        {"id": "b", "use": "plan-edit-context",
         "bind": {"unit_id": {"from": "b", "slot": "record", "where": {"type": "unit"}}},
         "args": []},
    ])
    with pytest.raises(agent_run.AgentRunError) as excinfo:
        agent_run.run_plan(self_ref, mini_repo)
    assert excinfo.value.code == "BINDING_INVALID"


def test_bound_step_admits_with_placeholders_and_dependencies(mini_repo):
    """Admission compiles and shape-validates the bound argv; at run time the
    binding resolves (S15), so the append chain runs end to end."""
    add_curriculum(mini_repo)
    plan = _v3_plan([
        {"id": "a", "use": "search", "args": ["demo", "--type", "unit"]},
        {"id": "b", "use": "plan-edit-context", "args": ["--brief"],
         "bind": {"unit_id": {"from": "a", "slot": "record", "where": {"type": "unit"}}}},
    ])
    report = agent_run.run_plan(plan, mini_repo)
    assert report["steps"][0]["status"] == "ok", report
    ctx_row = report["steps"][1]
    assert ctx_row["status"] == "ok", ctx_row
    assert ctx_row["bound"] == {"unit_id": "unit-demo-l01"}


# ---------------------------------------------------------------------------
# S15 runtime resolution: a bound chain runs and matches typed direct calls.

def _direct_payload(root, argv):
    from learning_os.adapters.cli import invoke_outcome
    from learning_os.adapters.cli_parser import build_parser

    namespace = build_parser().parse_args(["--root", str(root), *argv])
    outcome = invoke_outcome(namespace)
    assert outcome.exit_code == 0, (argv, outcome.stdout, outcome.stderr)
    return json.loads(outcome.stdout)


def _without_snapshot(payload):
    if isinstance(payload, dict):
        return {k: v for k, v in payload.items() if k != "snapshot_id"}
    return payload


def test_seq_chain_binding_matches_typed_direct_call(mini_repo):
    """The seq chain from offline/chains.json, instantiated on the fixture's
    one mapped unit: stage refs resolve against the search's rows and the
    study-sequence payload equals the typed direct call's."""
    from scenario_fixtures import rich_world

    rich_world(mini_repo)
    plan = {"schema_version": 3, "steps": [
        {"id": "a", "use": "search", "args": ["expected value", "--type", "unit"]},
        {"id": "order", "use": "study-sequence",
         "bind": {"unit_id": {"literal": "unit-demo-l01"},
                  "stage_ids_json": [
                      {"from": "a", "slot": "matched_stage",
                       "where": {"title": "Derive expected value"}},
                      {"from": "a", "slot": "matched_stage",
                       "where": {"title": "Apply expected value"}},
                  ]},
         "args": []},
    ]}
    report = agent_run.run_plan(plan, mini_repo)
    row = report["steps"][1]
    assert row["status"] == "ok", report
    assert row["bound"] == {"unit_id": "unit-demo-l01",
                            "stage_ids_json": ["stage-demo", "stage-demo-pending"]}
    direct = _direct_payload(
        mini_repo, ["study-sequence", "unit-demo-l01",
                    "--stage-ids-json", '["stage-demo","stage-demo-pending"]', "--json"])
    assert _without_snapshot(row["output"]) == _without_snapshot(direct), row


def _row_case_plan(where):
    return {"schema_version": 3, "on_error": "continue", "steps": [
        {"id": "a", "use": "search", "args": ["expected value", "--type", "unit"]},
        {"id": "order", "use": "study-sequence",
         "bind": {"unit_id": {"literal": "unit-demo-l01"},
                  "stage_ids_json": [{"from": "a", "slot": "matched_stage",
                                      "where": where}]},
         "args": []},
        {"id": "after", "use": "inspect", "args": ["note-demo"], "depends_on": ["order"]},
    ]}


def test_adversarial_14_zero_rows_binding_empty_dependents_blocked(mini_repo):
    from scenario_fixtures import rich_world

    rich_world(mini_repo)
    report = agent_run.run_plan(_row_case_plan({"unit_id": "unit-demo-nope"}), mini_repo)
    error = report["steps"][1]["error"]
    assert error["code"] == "BINDING_EMPTY"
    assert report["steps"][1]["status"] == "error"
    assert report["steps"][2]["status"] == "blocked"
    assert report["steps"][2]["error"]["code"] == "DEPENDENCY_FAILED"


def test_adversarial_15_two_rows_binding_cardinality_candidates_capped(mini_repo):
    from scenario_fixtures import rich_world

    rich_world(mini_repo)
    report = agent_run.run_plan(_row_case_plan({"unit_id": "unit-demo-l01"}), mini_repo)
    error = report["steps"][1]["error"]
    assert error["code"] == "BINDING_CARDINALITY"
    candidates = error["candidates"]
    assert 2 <= len(candidates) <= 5
    assert all(set(candidate) == {"id", "title"} for candidate in candidates)


# ---------------------------------------------------------------------------
# S16 Arm D: one snapshot for the whole plan.

_D_READS = [
    {"id": "s1", "use": "inspect", "args": ["stage-demo", "--json"]},
    {"id": "s2", "use": "plan-edit-context", "args": ["unit-demo-l01", "--brief", "--json"]},
    {"id": "s3", "use": "unit-list", "args": ["--module-id", "module-demo", "--json"]},
]


def test_snapshot_one_equivalence_with_direct_calls(mini_repo, tmp_path):
    """Every step's raw stdout under snapshot:one equals its direct-call stdout."""
    from scenario_fixtures import rich_world

    rich_world(mini_repo)
    report_dir = tmp_path / "reports"
    plan = {"schema_version": 3, "snapshot": "one", "steps": _D_READS}
    report = agent_run.run_plan(plan, mini_repo, report_dir=report_dir)
    assert report["totals"]["ok"] == 3, report
    raw = {}
    raw_path = Path(report["full_report"]).parent / "raw-steps.jsonl"
    for item in (json.loads(line) for line in raw_path.read_text().splitlines() if line):
        raw[item["index"]] = item["stdout"]
    assert len(raw) == 3
    for index, step in enumerate(_D_READS):
        argv = [step["use"], *step["args"]]
        direct = _read_payload_direct(mini_repo, argv)
        assert raw[index] == direct, step["id"]


def _read_payload_direct(root, argv):
    from learning_os.adapters.cli import invoke_outcome
    from learning_os.adapters.cli_parser import build_parser

    namespace = build_parser().parse_args(["--root", str(root), *argv])
    outcome = invoke_outcome(namespace)
    assert outcome.exit_code == 0, (argv, outcome.stdout, outcome.stderr)
    return outcome.stdout


def test_snapshot_one_reduces_model_loads(mini_repo):
    from scenario_fixtures import rich_world

    rich_world(mini_repo)
    # plan-edit-context holds no memo profile, so without snapshot:one each
    # call loads the model separately; inspect would wave and share anyway.
    plan = {"schema_version": 3, "steps": [
        {"id": "s1", "use": "plan-edit-context", "args": ["unit-demo-l01", "--brief", "--json"]},
        {"id": "s2", "use": "plan-edit-context", "args": ["unit-demo-l01", "--brief", "--json"]},
    ]}
    without = agent_run.run_plan(dict(plan), mini_repo)["totals"]["model_loads"]
    with_one = agent_run.run_plan({**plan, "snapshot": "one"}, mini_repo)["totals"]["model_loads"]
    assert with_one < without, (without, with_one)


def test_adversarial_20_snapshot_one_with_write_step_refuses(mini_repo):
    add_curriculum(mini_repo)
    plan = {"schema_version": 3, "snapshot": "one", "session_id": "s", "steps": [
        {"id": "w", "kind": "log", "text": "alpha fixture log", "key": "adv-d"},
        {"id": "r", "use": "inspect", "args": ["note-demo"], "depends_on": ["w"]},
    ]}
    with pytest.raises(agent_run.AgentRunError) as excinfo:
        agent_run.run_plan(plan, mini_repo)
    assert excinfo.value.code == "PLAN_INVALID"
    assert "snapshot" in str(excinfo.value)
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))


def test_adversarial_16_source_payload_root_injection_never_executes_target(mini_repo):
    """A source payload value like --root=/etc is not an id; the target never runs."""
    add_curriculum(mini_repo)
    calls = []

    def executor(argv, root):
        calls.append(argv[0])
        payload = [{"id": "--root=/etc", "type": "unit", "title": "T"}]
        return 0, json.dumps(payload if argv[0] == "search" else {"id": "x"}), ""

    plan = _v3_plan([
        {"id": "a", "use": "search", "args": ["demo", "--type", "unit"]},
        {"id": "b", "use": "plan-edit-context",
         "bind": {"unit_id": {"from": "a", "slot": "record", "where": {"type": "unit"}}},
         "args": ["--brief"]},
    ])
    report = agent_run.run_plan(plan, mini_repo, executor=executor, index={"verbs": ["search", "plan-edit-context", "inspect"], "verb_to_operation": {"search": "note.search", "plan-edit-context": "plan.edit-context", "inspect": "project.inspect"}, "task_to_use": {}})
    assert report["steps"][1]["error"]["code"] == "BINDING_VALUE_INVALID"
    assert "plan-edit-context" not in calls


def test_adversarial_17_source_payload_wrong_kind_refuses(mini_repo):
    add_curriculum(mini_repo)

    def executor(argv, root):
        payload = [{"id": "stage-x", "type": "unit", "title": "T"}]
        return 0, json.dumps(payload if argv[0] == "search" else {"id": "x"}), ""

    plan = _v3_plan([
        {"id": "a", "use": "search", "args": ["demo", "--type", "unit"]},
        {"id": "b", "use": "plan-edit-context",
         "bind": {"unit_id": {"from": "a", "slot": "record", "where": {"type": "unit"}}},
         "args": ["--brief"]},
    ])
    report = agent_run.run_plan(plan, mini_repo, executor=executor, index={"verbs": ["search", "plan-edit-context", "inspect"], "verb_to_operation": {"search": "note.search", "plan-edit-context": "plan.edit-context", "inspect": "project.inspect"}, "task_to_use": {}})
    assert report["steps"][1]["error"]["code"] == "BINDING_VALUE_INVALID"


def test_adversarial_18_root_override_in_bound_args_refuses(mini_repo):
    add_curriculum(mini_repo)
    plan = _v3_plan([
        {"id": "a", "use": "search", "args": ["demo", "--type", "unit"]},
        {"id": "b", "use": "plan-edit-context", "args": ["--root", "/tmp"],
         "bind": {"unit_id": {"from": "a", "slot": "record", "where": {"type": "unit"}}}},
    ])
    with pytest.raises(agent_run.AgentRunError, match="root overrides"):
        agent_run.run_plan(plan, mini_repo)


def test_adversarial_19_failed_source_blocks_bound_dependent(mini_repo):
    add_curriculum(mini_repo)
    plan = {**_v3_plan([
        {"id": "a", "use": "inspect", "args": ["no-such-record"]},
        {"id": "b", "use": "plan-edit-context", "args": ["--brief"],
         "bind": {"unit_id": {"from": "a", "slot": "unit"}}},
    ]), "on_error": "continue"}
    report = agent_run.run_plan(plan, mini_repo)
    assert report["steps"][0]["status"] == "error"
    assert report["steps"][1]["status"] == "blocked"
    assert report["steps"][1]["error"]["code"] == "DEPENDENCY_FAILED"
    assert "output" not in report["steps"][1]


def test_adversarial_21_canonical_change_mid_plan_marks_all_rows(mini_repo):
    from scenario_fixtures import rich_world

    rich_world(mini_repo)
    state = {"calls": 0}

    def executor(argv, root):
        state["calls"] += 1
        if state["calls"] == 2:
            note = root / "knowledge/notes/mathematics/note-demo.md"
            note.write_text(note.read_text() + "\n\nchanged mid plan\n")
        from learning_os.adapters.cli import invoke_outcome
        from learning_os.adapters.cli_parser import build_parser

        namespace = build_parser().parse_args(["--root", str(root), *argv])
        outcome = invoke_outcome(namespace)
        return outcome.exit_code, outcome.stdout, outcome.stderr

    plan = {"schema_version": 3, "snapshot": "one", "steps": [
        {"id": "s1", "use": "inspect", "args": ["note-demo", "--json"]},
        {"id": "s2", "use": "inspect", "args": ["stage-demo", "--json"]},
    ]}
    report = agent_run.run_plan(plan, mini_repo, executor=executor)
    assert report["totals"]["ok"] == 0, report
    for row in report["steps"]:
        assert row["status"] == "error"
        assert row["error"]["code"] == "SNAPSHOT_CONFLICT"
        assert row["error"]["retryable"] is True
        assert "output" not in row


def test_adversarial_22_stale_sealed_write_refuses_and_leaves_no_receipt(mini_repo):
    import subprocess

    add_curriculum(mini_repo)
    record = mini_repo.parent.parent / "adv-22-record.json"
    payload = json.dumps({"text": "adversarial 22"})

    def seal(*args):
        return subprocess.run(
            [sys.executable, str(ROOT / "tools/seal_envelope.py"), "--root", str(mini_repo), *args],
            capture_output=True, text=True, timeout=120)

    checked = seal("--capability", "capture.create", "--payload", payload, "--key", "adv-22",
                   "--guards", "auto", "--check-out", str(record))
    assert checked.returncode == 0, checked.stdout + checked.stderr
    assert record.exists()
    # Read at S1 happened with the check; now a canonical file changes.
    note = mini_repo / "knowledge/notes/mathematics/note-demo.md"
    note.write_text(note.read_text() + "\n\nchanged after S1\n")
    submitted = seal("--capability", "capture.create", "--payload", payload, "--key", "adv-22",
                     "--guards-from", str(record), "--submit")
    assert submitted.returncode != 0
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))


def test_adversarial_23_bound_read_only_plan_leaves_fingerprint_unchanged(mini_repo):
    from scenario_fixtures import rich_world

    from learning_os.store.fingerprint import canonical_fingerprint

    rich_world(mini_repo)
    before = canonical_fingerprint(mini_repo)
    plan = {"schema_version": 3, "steps": [
        {"id": "a", "use": "search", "args": ["expected value", "--type", "unit"]},
        {"id": "order", "use": "study-sequence",
         "bind": {"unit_id": {"literal": "unit-demo-l01"},
                  "stage_ids_json": [
                      {"from": "a", "slot": "matched_stage",
                       "where": {"title": "Derive expected value"}},
                      {"from": "a", "slot": "matched_stage",
                       "where": {"title": "Apply expected value"}},
                  ]},
         "args": []},
    ]}
    report = agent_run.run_plan(plan, mini_repo)
    assert report["totals"]["ok"] == 2, report
    assert canonical_fingerprint(mini_repo) == before


def test_adversarial_24_oversized_candidates_stay_within_report_budget(mini_repo):
    add_curriculum(mini_repo)
    rows = [{"id": f"unit-long-{i}", "type": "unit", "title": "T" * 2000} for i in range(7)]

    def executor(argv, root):
        return 0, json.dumps(rows if argv[0] == "search" else {"id": "x"}), ""

    plan = _v3_plan([
        {"id": "a", "use": "search", "args": ["demo", "--type", "unit"]},
        {"id": "b", "use": "plan-edit-context",
         "bind": {"unit_id": {"from": "a", "slot": "record", "where": {"type": "unit"}}},
         "args": ["--brief"]},
    ])
    report = agent_run.run_plan({**plan, "report_max_bytes": 4096}, mini_repo, executor=executor,
                                index={"verbs": ["search", "plan-edit-context", "inspect"], "verb_to_operation": {"search": "note.search", "plan-edit-context": "plan.edit-context", "inspect": "project.inspect"}, "task_to_use": {}})
    encoded = agent_run._json(report)
    assert len(encoded.encode("utf-8")) + 1 <= 4096
    assert report.get("output_omitted") is True
    codes = json.dumps(report)
    assert "BINDING_CARDINALITY" in codes


def test_adversarial_25_write_verbs_frozen_at_base(mini_repo):
    index = agent_run.build_index(mini_repo, agent_run._cli_executor_factory(mini_repo),
                                  resolve_tasks=False)
    assert sorted(index["write_verbs"]) == [
        "ability-candidate-append", "ability-observation-append", "ai-action-append-slices",
        "ai-action-apply-delivery", "ai-action-import-delivery", "ai-action-prepare",
        "atlas-question-save", "backup-manifest", "backup-verify", "capability", "capture",
        "collection-create", "collection-entry-revise", "concept-relations-change",
        "coordination-section-revise", "detour-create", "detour-resolve", "dossier",
        "garden-seed-create", "generate", "goal", "inbox-resolve",
        "legacy-archive-lock-publish", "lineage-restamp", "masters-planning-catalog-update",
        "masters-planning-comparison-publish", "module-attempt", "module-create",
        "module-materials-compact", "module-plan-import", "module-sitting",
        "note-analysis-prepare", "note-analysis-save", "note-analysis-save-batch",
        "note-create", "note-evidence", "note-revise", "observation-append", "observe",
        "path-attach", "path-note", "path-progress", "program-semester-update", "route-patch",
        "search", "session-end", "shelving-apply", "shelving-prepare", "source-feedback",
        "source-intake", "source-revise", "stage-attach", "stage-note", "stage-progress",
        "stage-result", "status", "unit-map-import", "unit-material-synthesis-publish",
        "unit-note", "unit-plan-revise", "unit-source-selection", "validate",
        "workspace-next-action",
    ]


def test_adversarial_26_catalog_refuses_faked_write(mini_repo):
    import dataclasses

    from learning_os.app.agent_catalog import build_catalog
    from learning_os.app.registry import REGISTRY, OperationEffects

    entry = REGISTRY["project.inspect"]
    REGISTRY["project.inspect"] = dataclasses.replace(entry, effects=OperationEffects.CANONICAL_WRITE)
    try:
        index = agent_run.build_index(mini_repo, agent_run._cli_executor_factory(mini_repo), resolve_tasks=False)
        with pytest.raises(ValueError, match="project.inspect"):
            build_catalog(mini_repo, index["verb_to_operation"])
    finally:
        REGISTRY["project.inspect"] = entry


# ---------------------------------------------------------------------------
# Amendment 1: defects the first suite missed, and the grammar corners merged
# into one check. Each must refuse with the code, or run, not crash.

def _seq_plan(stage_refs, unit=None):
    return {"schema_version": 3, "steps": [
        {"id": "a", "use": "search", "args": ["expected value", "--type", "unit"]},
        {"id": "order", "use": "study-sequence",
         "bind": {"unit_id": unit or {"literal": "unit-demo-l01"}, "stage_ids_json": stage_refs},
         "args": []},
    ]}


def test_literal_inside_a_list_binding_resolves(mini_repo):
    from scenario_fixtures import rich_world

    rich_world(mini_repo)
    report = agent_run.run_plan(_seq_plan([
        {"literal": "stage-demo"},
        {"from": "a", "slot": "matched_stage", "where": {"title": "Apply expected value"}},
    ]), mini_repo)
    assert report["steps"][1]["status"] == "ok", report
    assert report["steps"][1]["bound"]["stage_ids_json"] == ["stage-demo", "stage-demo-pending"]


def test_literal_on_an_any_kind_target_resolves(mini_repo):
    from scenario_fixtures import rich_world

    rich_world(mini_repo)
    plan = {"schema_version": 3, "steps": [
        {"id": "s", "use": "inspect", "bind": {"id": {"literal": "stage-demo"}}, "args": []}]}
    report = agent_run.run_plan(plan, mini_repo)
    assert report["steps"][0]["status"] == "ok", report
    assert report["steps"][0]["bound"] == {"id": "stage-demo"}


def test_adversarial_27_snapshot_under_an_older_schema_refuses(mini_repo):
    plan = {"schema_version": 2, "snapshot": "one", "steps": [
        {"id": "s", "use": "inspect", "args": ["note-demo"]}]}
    with pytest.raises(agent_run.AgentRunError, match="schema_version 3"):
        agent_run.run_plan(plan, mini_repo)


@pytest.mark.parametrize("stage_refs", [
    [{"from": "a", "slot": "matched_stage", "literal": "stage-demo"}],
    [{"literal": "stage-demo", "where": {"title": "x"}}],
    [{"from": "a"}],
    [{"slot": "matched_stage"}],
    [{"from": ["a"], "slot": "matched_stage"}],
    [{"from": "a", "slot": ["matched_stage"]}],
    ["stage-demo"],
])
def test_adversarial_28_malformed_references_refuse_before_any_step(mini_repo, stage_refs):
    with pytest.raises(agent_run.AgentRunError) as excinfo:
        agent_run.run_plan(_seq_plan(stage_refs), mini_repo)
    assert excinfo.value.code == "BINDING_INVALID"


@pytest.mark.parametrize("stage_refs", [
    [],
    {"from": "a", "slot": "matched_stage"},
    [{"literal": "unit-demo-l01"}],
    [{"from": "a", "slot": "matched_stage", "where": ["title"]}],
])
def test_adversarial_29_wrong_binding_shapes_refuse_at_admission(mini_repo, stage_refs):
    from scenario_fixtures import rich_world

    rich_world(mini_repo)
    report = agent_run.run_plan(_seq_plan(stage_refs), mini_repo)
    assert report["steps"][1]["error"]["code"] == "BINDING_INVALID", report
    assert report["steps"][0]["status"] != "ok"


def test_adversarial_30_missing_required_positional_refuses_at_admission(mini_repo):
    from scenario_fixtures import rich_world

    rich_world(mini_repo)
    plan = {"schema_version": 3, "steps": [
        {"id": "a", "use": "search", "args": ["expected value", "--type", "unit"]},
        {"id": "order", "use": "study-sequence",
         "bind": {"stage_ids_json": [{"from": "a", "slot": "matched_stage"}]}, "args": []},
    ]}
    report = agent_run.run_plan(plan, mini_repo)
    assert report["steps"][1]["error"]["code"] == "BINDING_INVALID", report
    assert "unit_id" in report["steps"][1]["error"]["message"]
