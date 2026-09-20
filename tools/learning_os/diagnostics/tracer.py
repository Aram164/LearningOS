"""Span and event emission for the commit boundary (track #2, Phase 2A).

Emission writes JSONL records to the opt-in ``LOS_TRACE_DEBUG_FILE`` sink and
is a strict no-op when the sink is unset. Every function swallows its own
failures: instrumentation observes the write path and can never break, slow
materially, or alter it.

Operation identity: the propagated UI context when present, else one lazily
minted process operation. A CLI invocation is one operation by construction,
so the process-global fallback cannot cross contexts between processes; it
only gives direct-CLI (operator) calls a stable identity without a UI.
"""

from __future__ import annotations

import json
import os
import secrets
import time
from dataclasses import dataclass

from .context import TraceContext, trace_context_from_env
from .conventions import TRACE_DEBUG_FILE_ENV, VOCAB_VERSION
from .store import persist_record

_current: TraceContext | None = None


def operation() -> TraceContext:
    """This process's operation: propagated context, else one minted root."""
    global _current
    propagated = trace_context_from_env()
    if propagated is not None:
        return propagated
    if _current is None:
        _current = TraceContext(trace_id=secrets.token_hex(16),
                                span_id=secrets.token_hex(8))
    return _current


def new_attempt_span_id() -> str:
    return secrets.token_hex(8)


def _clean_attrs(attrs: dict | None) -> dict:
    cleaned: dict = {}
    for key, value in (attrs or {}).items():
        if not isinstance(key, str):
            continue
        if isinstance(value, str):
            cleaned[key] = value[:200]
        elif isinstance(value, (bool, int, float)) or value is None:
            cleaned[key] = value
        elif isinstance(value, (list, tuple)):
            cleaned[key] = [str(item)[:80] for item in list(value)[:8]]
    return cleaned


def _append(record: dict) -> None:
    try:
        path = os.environ.get(TRACE_DEBUG_FILE_ENV)
        if path:
            with open(path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, sort_keys=True) + "\n")
    except Exception:
        pass
    # The persistent store is independent of the debug sink: per-run capture
    # and restart-surviving history are separate sinks with separate fates.
    persist_record(record)


def emit_event(name: str, *, stage: str | None = None,
               status: str = "ok", span_id: str | None = None,
               attrs: dict | None = None,
               context: TraceContext | None = None) -> None:
    """Append one event record; silent unless the sink is set."""
    try:
        active = context if context is not None else operation()
        _append({
            "v": VOCAB_VERSION,
            "kind": "event",
            "name": name,
            "stage": stage,
            "status": status,
            "op": active.trace_id,
            "span": span_id or active.span_id,
            "ts": time.time(),
            "pid": os.getpid(),
            "attrs": _clean_attrs(attrs),
        })
    except Exception:
        return


def span_start(name: str, *, attrs: dict | None = None,
               context: TraceContext | None = None) -> str:
    """Open an attempt span; returns its span id (caller closes it)."""
    active = context if context is not None else operation()
    span_id = active.span_id if name == "attempt" else new_attempt_span_id()
    try:
        _append({
            "v": VOCAB_VERSION,
            "kind": "span-start",
            "name": name,
            "op": active.trace_id,
            "span": span_id,
            "ts": time.time(),
            "pid": os.getpid(),
            "attrs": _clean_attrs(attrs),
        })
    except Exception:
        pass
    return span_id


def span_end(span_id: str, name: str, *, status: str = "ok",
             attrs: dict | None = None,
             context: TraceContext | None = None) -> None:
    """Close a span opened by :func:`span_start`; silent unless set."""
    try:
        active = context if context is not None else operation()
        _append({
            "v": VOCAB_VERSION,
            "kind": "span-end",
            "name": name,
            "status": status,
            "op": active.trace_id,
            "span": span_id,
            "ts": time.time(),
            "pid": os.getpid(),
            "attrs": _clean_attrs(attrs),
        })
    except Exception:
        return


@dataclass(frozen=True)
class Attempt:
    """One gateway attempt's open span; explicit close at each return."""

    span_id: str
    context: TraceContext

    def event(self, name: str, **kwargs) -> None:
        emit_event(name, span_id=self.span_id, context=self.context, **kwargs)

    def close(self, status: str = "ok", attrs: dict | None = None) -> None:
        span_end(self.span_id, "attempt", status=status,
                 attrs=attrs, context=self.context)


def begin_attempt(attrs: dict | None = None) -> Attempt:
    """Open the attempt span for this process's operation."""
    active = operation()
    span_id = span_start("attempt", attrs=attrs, context=active)
    return Attempt(span_id=span_id, context=active)
