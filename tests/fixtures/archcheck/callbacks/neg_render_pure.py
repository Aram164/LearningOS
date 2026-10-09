"""Negative fixture: a pure renderer passes (SPEC §3.5b).

No static flag and a clean runtime run through a test-only
registered operation: deterministic, non-mutating, no I/O, no
observations, no captured context.
"""


def render(payload):
    """A renderer that only reshapes the payload it was given."""
    return {"echo": payload.get("alpha"), "n": payload.get("beta", 0) + 1}
