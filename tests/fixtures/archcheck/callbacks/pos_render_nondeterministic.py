"""Positive runtime fixture: the renderer is nondeterministic (SPEC §3.5b).

Each call returns a fresh counter value, so the render check's second run
on a copy returns a different result and must raise RenderPurityError
("not deterministic"). Runs through a test-only registered operation.
"""

import itertools

_counter = itertools.count()


def render(payload):
    """A renderer whose result changes between identical calls."""
    return {"payload": dict(payload), "call": next(_counter)}
