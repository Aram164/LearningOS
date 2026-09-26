"""W3C-shaped trace context for the UI -> Core child-process hop.

Pure functions of their inputs: no module-level mutable state, so concurrent
operations in one process cannot cross contexts by construction. Malformed
input yields ``None`` — the caller proceeds exactly as if tracing were
absent — and the debug sink swallows its own failures for the same reason:
diagnostics must never break, slow materially, or alter a write.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

from .conventions import (
    TRACE_DEBUG_FILE_ENV,
    TRACE_OWNERSHIP_ENV,
    TRACEPARENT_ENV,
)

#: Strict W3C traceparent, version 00 only: ``00-<trace-id>-<span-id>-<flags>``.
_TRACEPARENT_RE = re.compile(
    r"^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$"
)


@dataclass(frozen=True)
class TraceContext:
    """One operation attempt's correlation identity.

    ``trace_id`` is the operation (stable across retries); ``span_id`` is
    this physical attempt; ``sampled`` is the W3C sampling flag bit.
    ``parent`` is the propagated caller context when one was provided:
    parentage, never identity — adopting it would merge unrelated
    requests sharing one ambient trace into one operation (JF-04).
    """

    trace_id: str
    span_id: str
    sampled: bool = True
    parent: TraceContext | None = None

    def format(self) -> str:
        flags = "01" if self.sampled else "00"
        return f"00-{self.trace_id}-{self.span_id}-{flags}"


def parse_traceparent(value: str | None) -> TraceContext | None:
    """Parse a W3C traceparent value; ``None`` for anything else.

    All-zero trace/span IDs are invalid per the W3C spec and rejected, as is
    any non-``00`` version: an old writer's context must never be mistaken
    for a current one.
    """
    if not value or not isinstance(value, str):
        return None
    match = _TRACEPARENT_RE.match(value.strip())
    if match is None:
        return None
    trace_id, span_id, flags = match.groups()
    if trace_id == "0" * 32 or span_id == "0" * 16:
        return None
    return TraceContext(
        trace_id=trace_id, span_id=span_id, sampled=bool(int(flags, 16) & 1))


def trace_context_from_env(env: os._Environ | dict | None = None) -> TraceContext | None:
    """Read the propagated context; ``None`` when absent or malformed."""
    source = os.environ if env is None else env
    try:
        value = source.get(TRACEPARENT_ENV)
    except Exception:
        return None
    return parse_traceparent(value)


def is_learningos_owned(propagated: TraceContext | None,
                        env: os._Environ | dict | None = None) -> bool:
    """Whether the propagated context is explicitly LearningOS-owned.

    Owner-selected Option A (JF-04): the UI marks every dispatch it mints
    by setting ``LOS_TRACE_OWNED`` to the operation id alongside
    TRACEPARENT. Only a marker naming this exact context adopts it as
    operation identity; an absent, mismatched, or malformed marker leaves
    the context as ambient parentage, never identity.
    """
    if propagated is None:
        return False
    source = os.environ if env is None else env
    try:
        marker = source.get(TRACE_OWNERSHIP_ENV)
    except Exception:
        return False
    return isinstance(marker, str) and marker.strip() == propagated.trace_id


def record_debug(
    context: TraceContext | None,
    *,
    operation: str,
    extra: dict | None = None,
) -> None:
    """Append one JSONL record to the opt-in debug sink, else do nothing.

    The sink exists so tests and human diagnosis can prove, through the real
    gateway path, that the child received the intended context. It is capped
    at IDs and structural labels (see the privacy rule in conventions); any
    failure to write is swallowed — a broken sink must be invisible.
    """
    if context is None:
        return
    try:
        path = os.environ.get(TRACE_DEBUG_FILE_ENV)
        if not path:
            return
        record = {
            "trace_id": context.trace_id,
            "span_id": context.span_id,
            "sampled": context.sampled,
            "operation": operation,
            "pid": os.getpid(),
        }
        if extra:
            record.update(extra)
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    except Exception:
        return
