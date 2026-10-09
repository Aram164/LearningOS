"""Positive fixture: the renderer emits an observation (SPEC §3.5b).

Flagged statically (``observations.*``) and at runtime (the
``learningos.observation`` audit event under the render marker).
The clock value is discarded, so the result stays deterministic.
Runs through a test-only registered operation.
"""

from learning_os import observations


def render(payload):
    """A renderer that observes the clock, then returns its payload."""
    observations.now()
    return dict(payload)
