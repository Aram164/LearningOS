"""The render marker: which rendering callback is running (SPEC 3.5b).

Rendering callbacks (``Operation.human``, ``Operation.render_check``) must be pure: no I/O, no
observations, deterministic, non-mutating. Every invocation goes through
:func:`call_renderer`, which sets :data:`_RENDER` around the call so the
audit hook (``tests/arch_audit_hook.py``) can attribute any audited event
to the running renderer.
"""

from __future__ import annotations

import contextvars
import copy
import os

#: (operation, callback name) while a renderer runs, else None.
_RENDER: contextvars.ContextVar[tuple[str, str] | None] = contextvars.ContextVar(
    "los_arch_render", default=None)

RENDER_CHECK_ENV = "LOS_ARCH_RENDER_CHECK"


class RenderPurityError(AssertionError):
    """A rendering callback mutated its argument or was nondeterministic."""


#: Exact-type leaves for the recursive JSON comparison (SPEC (az)).
_JSON_SCALAR_TYPES = (type(None), bool, int, float, str)


def _json_equal(first, second) -> bool:
    """Recursive JSON type-and-value equality (SPEC (az), S15 item 4).

    Dicts compare by key set then values, lists by length then items, and
    ``None``/``bool``/``int``/``float``/``str`` by exact ``type(...)`` plus
    value, so ``False`` differs from ``0``. Any other type compares by
    ``==``, as before.
    """
    if isinstance(first, dict) and isinstance(second, dict):
        return (first.keys() == second.keys()
                and all(_json_equal(first[key], second[key])
                        for key in first))
    if isinstance(first, list) and isinstance(second, list):
        return (len(first) == len(second)
                and all(_json_equal(left, right)
                        for left, right in zip(first, second, strict=True)))
    if (type(first) in _JSON_SCALAR_TYPES
            or type(second) in _JSON_SCALAR_TYPES):
        return type(first) is type(second) and first == second
    return first == second


def current_render() -> tuple[str, str] | None:
    """The running renderer as (operation, callback name), or None."""
    return _RENDER.get()


def call_renderer(operation: str, callback: str, fn, *args):
    """Run renderer ``fn`` under the (operation, callback) marker.

    When ``LOS_ARCH_RENDER_CHECK=1``, also proves purity: the arguments
    must be unchanged afterwards ("argument mutated") and a second run on
    a copy must return an equal result ("not deterministic"). Both
    comparisons are recursive JSON type-and-value equality. A failure
    raises :class:`RenderPurityError` whose message is
    ``<operation>::<callback>::<reason>``.
    """
    check = os.environ.get(RENDER_CHECK_ENV) == "1"
    if not check:
        token = _RENDER.set((operation, callback))
        try:
            return fn(*args)
        finally:
            _RENDER.reset(token)
    before = copy.deepcopy(args)
    token = _RENDER.set((operation, callback))
    try:
        result = fn(*args)
    finally:
        _RENDER.reset(token)
    if len(args) != len(before) or any(
            not _json_equal(now, was)
            for now, was in zip(args, before, strict=True)):
        raise RenderPurityError(f"{operation}::{callback}::argument-mutated")
    token = _RENDER.set((operation, callback))
    try:
        again = fn(*copy.deepcopy(before))
    finally:
        _RENDER.reset(token)
    if not _json_equal(again, result):
        raise RenderPurityError(f"{operation}::{callback}::not-deterministic")
    return result
