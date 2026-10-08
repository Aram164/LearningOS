"""Positive runtime fixture: the renderer mutates its argument (SPEC §3.5b).

The render check deep-copies the arguments first and must raise
RenderPurityError ("argument mutated") after the call. Runs through a
test-only registered operation.
"""


def render(payload):
    """A renderer that writes back into the payload it was given."""
    payload["mutated"] = True
    return payload
