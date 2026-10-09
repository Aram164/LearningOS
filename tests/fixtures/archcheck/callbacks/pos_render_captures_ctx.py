"""Positive fixture: the renderer captures a context (SPEC §3.5b).

``ctx`` is free in ``render``, so the static part flags it; at
runtime the test binds it to a real ``OpContext`` and the repo load
is audited under the render marker. Runs through a test-only
registered operation.
"""

ctx = None  # Bound to a real OpContext by the runtime test.


def render(payload):
    """A renderer that resolves unit ids through its captured context."""
    return {"units": sorted(ctx.repo().units)}
