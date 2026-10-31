"""Pure binding types and resolution for plan result binding (PLAN D3, D4).

A binding feeds a read's parameter from one earlier read's declared output
slot; writes never take a bound value (D2). This module is pure: standard
library plus the domain id and code owners, no registry, no I/O. Resolution
filters the source payload's rows by declared columns, refuses anything that
is not exactly one well-formed id, and never guesses a row.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from learning_os.domain.codes import (
    BINDING_CARDINALITY,
    BINDING_EMPTY,
    BINDING_VALUE_INVALID,
)
from learning_os.domain.ids import GENERIC_KINDS, is_valid

_CANDIDATE_LIMIT = 5


@dataclass(frozen=True)
class OutputSlot:
    """One declared output shape: where the rows live and what identifies them.

    ``path`` is a tuple of keys where ``"*"`` expands a list. Rows are dicts
    when ``value_key`` is set, else scalars. ``kind_column`` derives the row
    kind from a row field (the ``where`` value supplies it statically);
    ``parent_columns`` copies a parent's field into each nested row.
    """

    path: tuple[str, ...]
    kind: str | None
    value_key: str | None = None
    columns: tuple[str, ...] = ()
    kind_column: str | None = None
    parent_columns: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class CompiledRef:
    """One admission-compiled binding: either a source reference or a literal.

    ``target_kind`` is the bound target param's declared kind, recorded at
    admission so run-time resolution needs no schema lookup for it.
    """

    param: str
    source: str | None = None
    slot_name: str | None = None
    slot: OutputSlot | None = None
    where: Mapping[str, object] = field(default_factory=dict)
    literal: object = None
    target_kind: str = ""


class BindingError(Exception):
    def __init__(self, code: str, message: str, candidates=()):
        super().__init__(message)
        self.code = code
        self.message = message
        self.candidates = tuple(candidates)

    def as_dict(self) -> dict:
        payload = {"code": self.code, "message": self.message}
        if self.candidates:
            payload["candidates"] = list(self.candidates)
        return payload


def rows_of(payload: object, slot: OutputSlot) -> list:
    """Return the slot's rows from ``payload``; ``[]`` when the shape differs."""
    current: list[tuple[object, dict]] = [(payload, {})]
    for key in slot.path:
        nxt: list[tuple[object, dict]] = []
        for node, inherited in current:
            if key == "*":
                if isinstance(node, list):
                    nxt.extend((item, inherited) for item in node)
            elif isinstance(node, dict) and key in node:
                child_inherited = inherited
                if slot.parent_columns:
                    copied = {row_key: node[parent_key]
                              for row_key, parent_key in slot.parent_columns.items()
                              if parent_key in node}
                    if copied:
                        child_inherited = {**inherited, **copied}
                nxt.append((node[key], child_inherited))
        current = nxt
    rows: list = []
    for node, inherited in current:
        if isinstance(node, dict) and inherited:
            rows.append({**inherited, **node})
        else:
            rows.append(node)
    return rows


def _candidate(row: object) -> dict:
    if isinstance(row, dict):
        return {"id": row.get("id"), "title": row.get("title")}
    return {"id": row, "title": None}


def _value_ok(value: str, target_kind: str, source_kind: str | None) -> bool:
    if target_kind == "*":
        return any(is_valid(prefix, value) for prefix in GENERIC_KINDS)
    kind = source_kind if source_kind is not None else target_kind
    return is_valid(kind, value)


def resolve(ref: CompiledRef, payload: object, target_kind: str) -> str:
    """Resolve one compiled binding to exactly one id, or refuse (D3)."""
    if ref.source is None:
        value = ref.literal
        if not isinstance(value, str) or not _value_ok(value, target_kind, None):
            raise BindingError(
                BINDING_VALUE_INVALID,
                f"binding {ref.param!r}: literal is not a valid {target_kind} id")
        return value
    rows = rows_of(payload, ref.slot)
    if ref.where:
        rows = [row for row in rows
                if isinstance(row, dict)
                and all(row.get(key) == value for key, value in ref.where.items())]
    if not rows:
        raise BindingError(
            BINDING_EMPTY,
            f"binding {ref.param!r}: no matching rows in slot {ref.slot_name!r}")
    if len(rows) > 1:
        raise BindingError(
            BINDING_CARDINALITY,
            f"binding {ref.param!r}: {len(rows)} matching rows in slot "
            f"{ref.slot_name!r}; name one row with where",
            candidates=[_candidate(row) for row in rows[:_CANDIDATE_LIMIT]])
    row = rows[0]
    value = row.get(ref.slot.value_key) if ref.slot.value_key is not None else row
    kind = None
    if ref.slot.kind_column is not None:
        kind = ref.where.get(ref.slot.kind_column)
    elif ref.slot.kind is not None:
        kind = ref.slot.kind
    if not isinstance(value, str) or not _value_ok(value, target_kind, kind):
        raise BindingError(
            BINDING_VALUE_INVALID,
            f"binding {ref.param!r}: resolved value is not a valid "
            f"{kind or target_kind} id")
    return value
