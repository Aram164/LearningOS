"""The render marker: which rendering callback is running (SPEC 3.5b).

Rendering callbacks (``Result.finish``, ``Result.on_commit_refused``,
``Operation.human``, ``Operation.render_check``) must be pure: no I/O, no
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


def current_render() -> tuple[str, str] | None:
    """The running renderer as (operation, callback name), or None."""
    return _RENDER.get()


def call_renderer(operation: str, callback: str, fn, *args):
    """Run renderer ``fn`` under the (operation, callback) marker.

    When ``LOS_ARCH_RENDER_CHECK=1``, also proves purity: the arguments
    must be unchanged afterwards ("argument mutated") and a second run on
    a copy must return an equal result ("not deterministic"). A failure
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
    if args != before:
        raise RenderPurityError(f"{operation}::{callback}::argument-mutated")
    token = _RENDER.set((operation, callback))
    try:
        again = fn(*copy.deepcopy(before))
    finally:
        _RENDER.reset(token)
    if again != result:
        raise RenderPurityError(f"{operation}::{callback}::not-deterministic")
    return result
