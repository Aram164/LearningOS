"""Pure binding types and resolution: every branch, no repository (S12)."""
from __future__ import annotations

import pytest

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
