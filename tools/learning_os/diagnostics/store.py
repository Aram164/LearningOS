"""Bounded persistent trace store (track #2, Phase 3A).

Causal evidence that survives restarts. The store is deliberately weaker
than everything around it:

- non-authoritative: receipts, the idempotency ledger, and typed refusals
  decide outcomes; these records only describe what execution appeared to do;
- disposable: gitignored, outside the canonical fingerprint, deletable at
  any time with zero effect on canonical behavior;
- bounded: append-oriented JSONL plus explicit retention (last N completed
  operations, with pinned unresolved operations never evicted);
- IDs and references only: no payloads, note text, drafts, or canonical
  file contents — ever.

Writes never fail a caller: every persistence path swallows its own errors,
because an unwritable trace file must never reject a learner's write.
Retention (`prune_store`) is explicit maintenance — it raises its own
errors to its own caller and never runs inside the write path.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from . import conventions

STORE_DIRNAME = "diagnostics"
TRACES_FILENAME = "traces.jsonl"
STORE_SCHEMA_VERSION = 1

#: Default retention: recent completed operations kept, everything older
#: compacted away unless pinned.
DEFAULT_KEEP_LAST = 500

_bound_root: Path | None = None


def store_dir(root: Path) -> Path:
    return Path(root) / "operations" / STORE_DIRNAME


def traces_path(root: Path) -> Path:
    return store_dir(root) / TRACES_FILENAME


def bind_store(root: Path | None) -> None:
    """Bind this process's persistent sink; None unbinds (tests)."""
    global _bound_root
    _bound_root = Path(root).resolve() if root is not None else None


def bound_root() -> Path | None:
    return _bound_root


def persist_record(record: dict) -> None:
    """Append one span/event record to the bound store, else do nothing.

    Only versioned span records persist; anything else (including the
    Phase-1 debug shape) stays on the debug sink. Failures are swallowed:
    persistence is best-effort by contract.
    """
    try:
        root = _bound_root
        if root is None or not isinstance(record, dict):
            return
        if record.get("v") != conventions.VOCAB_VERSION:
            return
        if record.get("kind") not in ("span-start", "span-end", "event"):
            return
        stored = {
            "schema_version": STORE_SCHEMA_VERSION,
            "conventions_version": conventions.VOCAB_VERSION,
            "timestamp": record.get("ts"),
            "trace_id": record.get("op"),
            "operation_id": record.get("op"),
            "attempt_id": record.get("span"),
            "span_id": record.get("span"),
            "parent_span_id": None,
            "kind": record.get("kind"),
            "name": record.get("name"),
            "stage": record.get("stage"),
            "status": record.get("status"),
            "attributes": record.get("attrs") or {},
        }
        directory = store_dir(root)
        directory.mkdir(parents=True, exist_ok=True)
        with open(directory / TRACES_FILENAME, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(stored, sort_keys=True) + "\n")
    except Exception:
        return


def read_records(root: Path, *, trace_id: str | None = None,
                 request_id: str | None = None) -> list[dict]:
    """Read persisted records, tolerating corruption line by line.

    Unparseable lines are skipped, never fatal: a torn tail from a killed
    process must degrade the view, not the system. Resolved back into the
    in-memory record shape the resolver already reads.
    """
    path = traces_path(root)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    records = []
    for line in lines:
        if not line.strip():
            continue
        try:
            stored = json.loads(line)
        except ValueError:
            continue
        if not isinstance(stored, dict):
            continue
        if stored.get("schema_version") != STORE_SCHEMA_VERSION:
            continue
        if stored.get("conventions_version") != conventions.VOCAB_VERSION:
            continue
        if trace_id is not None and stored.get("trace_id") != trace_id:
            continue
        record = {
            "v": stored.get("conventions_version"),
            "kind": stored.get("kind"),
            "name": stored.get("name"),
            "stage": stored.get("stage"),
            "status": stored.get("status"),
            "op": stored.get("trace_id"),
            "span": stored.get("span_id"),
            "ts": stored.get("timestamp"),
            "attrs": stored.get("attributes") or {},
        }
        if request_id is not None:
            attrs = record["attrs"] if isinstance(record["attrs"], dict) else {}
            if attrs.get("request_id") != request_id:
                continue
        records.append(record)
    return records


def _operation_ids(records: list[dict]) -> dict[str, float]:
    latest: dict[str, float] = {}
    for record in records:
        op = record.get("trace_id")
        if not op:
            continue
        ts = record.get("timestamp") or 0
        try:
            ts = float(ts)
        except (TypeError, ValueError):
            ts = 0.0
        latest[op] = max(latest.get(op, 0.0), ts)
    return latest


def prune_store(root: Path, *, keep_last: int = DEFAULT_KEEP_LAST,
                pinned_request_ids: frozenset[str] | set[str] = frozenset(),
                dry_run: bool = False) -> dict:
    """Compact the store: newest `keep_last` operations plus pinned ones.

    An operation is pinned when any of its records carries a
    `request_id` attribute in `pinned_request_ids` (e.g. the request an
    unresolved Gateway recovery record still references). Pinning is the
    caller's decision — retention never guesses it.

    Rewrites the file atomically; returns counts. Raises OSError/ValueError
    to its caller on failure: retention is explicit maintenance, never part
    of a write, so its errors must be visible, not swallowed.
    """
    path = traces_path(root)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return {"kept_operations": 0, "evicted_operations": 0,
                "kept_records": 0, "evicted_records": 0}
    parsed: list[tuple[str, dict | None]] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except ValueError:
            data = None
        parsed.append((line, data if isinstance(data, dict) else None))
    ops = _operation_ids([data for _, data in parsed if data is not None])
    pinned_ops = {
        data["trace_id"]
        for _, data in parsed
        if data is not None
        and isinstance(data.get("attributes"), dict)
        and data["attributes"].get("request_id") in pinned_request_ids
        and data.get("trace_id")
    }
    ranked = sorted(ops, key=lambda op: ops[op], reverse=True)
    keep = set(ranked[:max(keep_last, 0)]) | pinned_ops
    kept_lines = [line for line, data in parsed
                  if data is not None and data.get("trace_id") in keep]
    evicted_ops = len(ops) - len(keep)
    if not dry_run:
        tmp = path.with_name(f".{TRACES_FILENAME}.tmp")
        tmp.write_text(
            "".join(f"{line}\n" for line in kept_lines), encoding="utf-8")
        os.replace(tmp, path)
    return {"kept_operations": len(keep),
            "evicted_operations": max(evicted_ops, 0),
            "kept_records": len(kept_lines),
            "evicted_records": len(parsed) - len(kept_lines)}
