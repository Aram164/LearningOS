"""Pure binding types and resolution for plan result binding (PLAN D3, D4).

A binding feeds a read's parameter from one earlier read's declared output
slot; writes never take a bound value (D2). This module is pure: standard
library plus the domain id and code owners, no registry, no I/O. Resolution
filters the source payload's rows by declared columns, refuses anything that
is not exactly one well-formed id, and never guesses a row.
"""
from __future__ import annotations

import json
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

    ``target_kind`` is the bound target param's declared kind and ``position``
    its place in the compiled argv, so run time needs no schema lookup.
    """

    param: str
    source: str | None = None
    slot_name: str | None = None
    slot: OutputSlot | None = None
    where: Mapping[str, object] = field(default_factory=dict)
    literal: object = None
    target_kind: str = ""
    position: int = 0


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


def valid_for(kind: str, value: object) -> bool:
    """Is ``value`` an id of this target kind? ``*`` is any generic id; ``x[]`` holds x."""
    kind = kind.removesuffix("[]")
    if kind == "*":
        return any(is_valid(generic, value) for generic in GENERIC_KINDS)
    return is_valid(kind, value)


def rows_of(payload: object, slot: OutputSlot) -> list:
    """Return the slot's rows from ``payload``; ``[]`` when the shape differs."""
    current: list[tuple[object, dict]] = [(payload, {})]
    for key in slot.path:
        following: list[tuple[object, dict]] = []
        for node, inherited in current:
            if key == "*":
                if isinstance(node, list):
                    following.extend((item, inherited) for item in node)
            elif isinstance(node, dict) and key in node:
                copied = {row_key: node[parent_key] for row_key, parent_key in slot.parent_columns.items()
                          if parent_key in node}
                following.append((node[key], {**inherited, **copied}))
        current = following
    return [{**inherited, **node} if isinstance(node, dict) and inherited else node
            for node, inherited in current]


def _candidate(row: object) -> dict:
    if isinstance(row, dict):
        return {"id": row.get("id"), "title": row.get("title")}
    return {"id": row, "title": None}


def resolve(ref: CompiledRef, payload: object, target_kind: str) -> str:
    """Resolve one compiled binding to exactly one id, or refuse (D3)."""
    slot = ref.slot
    rows = [ref.literal] if slot is None else [
        row for row in rows_of(payload, slot)
        if not ref.where or (isinstance(row, dict)
                             and all(row.get(key) == value for key, value in ref.where.items()))]
    if not rows:
        raise BindingError(BINDING_EMPTY, f"binding {ref.param!r}: no matching rows in slot {ref.slot_name!r}")
    if len(rows) > 1:
        raise BindingError(
            BINDING_CARDINALITY,
            f"binding {ref.param!r}: {len(rows)} matching rows in slot {ref.slot_name!r}; name one row with where",
            candidates=[_candidate(row) for row in rows[:_CANDIDATE_LIMIT]])
    value = rows[0]
    kind = target_kind
    if slot is not None:
        if slot.value_key is not None:
            value = value.get(slot.value_key) if isinstance(value, dict) else None
        if target_kind != "*":
            kind = (ref.where.get(slot.kind_column) if slot.kind_column else slot.kind) or target_kind
    if not isinstance(value, str) or not valid_for(kind, value):
        raise BindingError(BINDING_VALUE_INVALID, f"binding {ref.param!r}: value is not a valid {kind} id")
    return value


def bind_argv(argv, refs, payloads: Mapping) -> tuple[list, dict]:
    """Resolve ``refs`` and put each value at its compiled place in ``argv``."""
    final, bound = list(argv), {}
    for ref in refs:
        value = resolve(ref, payloads.get(ref.source), ref.target_kind)
        if ref.target_kind.endswith("[]"):
            bound.setdefault(ref.param, []).append(value)
            final[ref.position] = json.dumps(bound[ref.param])
        else:
            bound[ref.param] = final[ref.position] = value
    return final, bound
