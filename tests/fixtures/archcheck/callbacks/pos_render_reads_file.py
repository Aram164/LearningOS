"""Positive fixture: the renderer reads a file (SPEC §3.5b).

Flagged statically (``open``) and at runtime (the audit hook logs
the read under the render marker). Deterministic and non-mutating,
so the failure is the read alone. Runs through a test-only
registered operation.
"""


def render(payload):
    """A renderer that reads one byte before returning its payload."""
    with open(__file__, encoding="utf-8") as handle:
        handle.read(1)
    return dict(payload)
