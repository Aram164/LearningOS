"""Read-only Operations surface (track #2, Phase 4A).

Lists recent causal operations and explains one request id, for the
Diagnostics Operations view. Everything here reads the disposable trace
store plus the authority plane (receipts, ledger, manifest snapshot) and
runs the deterministic resolver — no new evidence, no new authority, and
no writes of any kind.
"""

from __future__ import annotations

import json
from pathlib import Path

from learning_os.diagnostics import conventions
from learning_os.diagnostics.resolver import AuthorityEvidence, collect_authority, resolve
from learning_os.diagnostics.store import read_records

from .support import _root


def _summaries(records: list[dict]) -> list[dict]:
    return [record for record in records
            if record.get("name") == conventions.EVENT_RESPONSE_EMITTED]


def _response_from_summary(summary: dict | None) -> dict | None:
    if summary is None:
        return None
    attrs = summary.get("attrs") or {}
    error = None if attrs.get("ok") else {"code": attrs.get("code"),
                                          "retryable": attrs.get("retryable")}
    return {"ok": attrs.get("ok"), "error": error,
            "replayed": attrs.get("replayed", False),
            "transaction_id": attrs.get("transaction_id"),
            "receipt_path": attrs.get("receipt_path"),
            "snapshot_after": attrs.get("snapshot_after")}


def _identity(records: list[dict]) -> tuple[str | None, str | None, str | None]:
    request_id = idempotency_key = capability = None
    for record in records:
        attrs = record.get("attrs") or {}
        if record.get("name") in (conventions.EVENT_ENVELOPE_VALIDATED,
                                  conventions.EVENT_ENVELOPE_PREPARED):
            request_id = request_id or attrs.get("request_id")
            idempotency_key = idempotency_key or attrs.get("idempotency_key")
        if record.get("kind") == "span-start" and record.get("name") == "attempt":
            capability = capability or attrs.get("capability")
    return request_id, idempotency_key, capability


def _observed_snapshot(root: Path) -> str | None:
    manifest = root / "generated" / "manifest.json"
    if not manifest.is_file():
        return None
    try:
        return (json.loads(manifest.read_text(encoding="utf-8"))
                .get("_generated", {}).get("snapshot_id"))
    except (ValueError, OSError):
        return None


def _observed_for(records: list[dict], snapshot_after: str | None,
                  manifest_snapshot: str | None) -> str | None:
    """What observation evidence exists for one operation.

    Publication is not observation: a projection-published event proves Core
    wrote the snapshot, not that any interface observed it, so it never
    counts here. Observation evidence is the live manifest showing this
    exact snapshot (current visibility), or the UI settling while observing
    it (the durable proof for a superseded snapshot). A receipt with
    neither stays unverified.
    """
    if snapshot_after is None:
        return manifest_snapshot
    if manifest_snapshot == snapshot_after:
        return manifest_snapshot
    for record in records:
        attrs = record.get("attrs") or {}
        if record.get("name") == conventions.EVENT_RECOVERY_SETTLED \
                and attrs.get("snapshot_after") == snapshot_after \
                and attrs.get("observed") is True:
            return snapshot_after
    return None


def _evidence_for(root: Path, records: list[dict],
                  observed: str | None) -> AuthorityEvidence:
    # One collection path: the strict receipt verification lives in
    # collect_authority, so Operations can never drift from it.
    request_id, idempotency_key, capability = _identity(records)
    summaries = sorted(_summaries(records), key=lambda row: row.get("ts", 0))
    response = _response_from_summary(summaries[-1] if summaries else None)
    codes: list = []
    for summary in summaries:
        attrs = summary.get("attrs") or {}
        codes.append(None if attrs.get("ok") else attrs.get("code"))
    return collect_authority(
        root, request_id=request_id or "unknown-request",
        idempotency_key=idempotency_key or "unknown-key",
        capability=capability or "unknown-capability",
        response=response,
        response_codes=codes,
        observed_snapshot=_observed_for(
            records, (response or {}).get("snapshot_after"), observed))


def list_operations(root: Path, limit: int = 20) -> list[dict]:
    """Newest-first operation summaries for the Operations list."""
    by_op: dict[str, list[dict]] = {}
    for record in read_records(root):
        if record.get("op"):
            by_op.setdefault(record["op"], []).append(record)
    observed = _observed_snapshot(root)
    rows = []
    for op, records in by_op.items():
        records = sorted(records, key=lambda row: row.get("ts", 0))
        request_id, _, capability = _identity(records)
        starts = [row for row in records if row.get("kind") == "span-start"]
        ends = [row for row in records if row.get("kind") == "span-end"]
        started = min([row.get("ts") for row in records if row.get("ts")] or [None])
        finished = max([row.get("ts") for row in ends if row.get("ts")] or [None])
        authority = _evidence_for(root, records, observed)
        diagnosis = resolve(records, authority)
        replayed = any((row.get("attrs") or {}).get("replayed") for row in
                       _summaries(records)) or len(starts) > 1
        rows.append({
            "trace_id": op,
            "request_id": request_id,
            "capability": capability or "unknown",
            "started_at": started,
            "duration_ms": (round((finished - started) * 1000.0, 1)
                            if started and finished else None),
            "attempts": len(starts),
            "replayed": replayed,
            "first_failure_stage": diagnosis.first_failure_stage,
            "canonical_outcome": diagnosis.canonical_outcome,
            "recovery_requirement": diagnosis.recovery_requirement,
            "needs_attention": diagnosis.recovery_requirement != "none",
        })
    rows.sort(key=lambda row: row["started_at"] or 0, reverse=True)
    return rows[:max(limit, 0)]


TIMELINE = (
    ("UI recovery persisted", ("gateway.envelope.prepared",)),
    ("Core admitted request", (conventions.EVENT_ENVELOPE_VALIDATED,)),
    ("Approval", (conventions.EVENT_APPROVAL_PASSED,)),
    ("Replay lookup", (conventions.EVENT_REPLAY_CHECKED,)),
    ("Snapshot guard", (conventions.EVENT_SNAPSHOT_GUARD_PASSED,)),
    ("Handler", (conventions.EVENT_HANDLER_COMPLETED,)),
    ("Validation", (conventions.EVENT_VALIDATION_PASSED,)),
    ("Projection", (conventions.EVENT_PROJECTION_STARTED,
                    conventions.EVENT_PROJECTION_PUBLISHED)),
    ("Transaction committed", (conventions.EVENT_CORE_TRANSACTION_COMMITTED,)),
    ("Receipt persisted", (conventions.EVENT_RECEIPT_PERSISTED,)),
    ("Response classified", ("ui.response.received",)),
    ("Recovery settled", (conventions.EVENT_RECOVERY_SETTLED,)),
    ("Recovery blocked", (conventions.EVENT_RECOVERY_BLOCKED,)),
)

_STAGE_ROW = {
    "ui.prepare": "UI recovery persisted",
    "core.admission": "Core admitted request",
    "core.approval": "Approval",
    "core.replay": "Replay lookup",
    "core.snapshot_guard": "Snapshot guard",
    "core.validation": "Validation",
    "core.projection": "Projection",
    "core.commit": "Transaction committed",
    "core.receipt": "Receipt persisted",
    "ui.reconcile": "Snapshot observed",
    "ui.recovery": "Recovery settled",
}


def build_timeline(records: list[dict], diagnosis) -> list[dict]:
    """Ordered stage checklist; rows without evidence are omitted."""
    names = [record.get("name") for record in records
             if record.get("kind") == "event"]
    failed_label = _STAGE_ROW.get(diagnosis.first_failure_stage or "")
    rows = []
    for label, events in TIMELINE:
        present = [name for name in events if name in names]
        if not present and label != failed_label:
            continue
        state = "passed" if present else "missing"
        if label == failed_label:
            state = "failed"
        detail = None
        if label == "Replay lookup":
            for record in records:
                if record.get("name") == conventions.EVENT_REPLAY_CHECKED:
                    detail = (record.get("attrs") or {}).get("outcome")
        if label == "Projection" and state == "passed" \
                and conventions.EVENT_PROJECTION_PUBLISHED not in names:
            state = "failed"
            detail = "started, never published"
        rows.append({"stage": label, "state": state, "detail": detail})
    return rows


def describe_operation(root: Path, request_id: str) -> dict | None:
    """Full diagnosis plus timeline for one request id, or None."""
    everything = read_records(root)
    ops = {record["op"] for record in everything
           if (record.get("attrs") or {}).get("request_id") == request_id
           and record.get("op")}
    records = sorted((record for record in everything if record.get("op") in ops),
                     key=lambda row: row.get("ts", 0))
    if not records:
        return None
    observed = _observed_snapshot(root)
    authority = _evidence_for(root, records, observed)
    diagnosis = resolve(records, authority)
    receipt = authority.verified_receipt or {}
    if diagnosis.canonical_outcome == "COMMITTED" \
            and diagnosis.recovery_requirement == "none":
        ui_outcome = "SETTLED"
    elif diagnosis.canonical_outcome == "NOT_COMMITTED" \
            and diagnosis.recovery_requirement == "none":
        ui_outcome = "REFUSED"
    else:
        ui_outcome = "BLOCKED"
    return {
        "request_id": request_id,
        "capability": authority.capability,
        "diagnosis": diagnosis.to_dict(),
        "timeline": build_timeline(records, diagnosis),
        "observed_snapshot": observed,
        "ui_outcome": ui_outcome,
        "facts": {
            "transaction_id": receipt.get("id"),
            "receipt_path": receipt.get("_path"),
            "snapshot_before": receipt.get("snapshot_before"),
            "snapshot_after": receipt.get("snapshot_after"),
        },
    }


def cmd_operations(args) -> int:
    root = _root(args)
    if getattr(args, "request_id", None):
        detail = describe_operation(root, args.request_id)
        if detail is None:
            print(json.dumps({"error": "unknown request_id",
                              "request_id": args.request_id}))
            return 2
        print(json.dumps(detail, indent=2, ensure_ascii=False))
        return 0
    limit = getattr(args, "limit", 20) or 20
    print(json.dumps({"operations": list_operations(root, limit=min(limit, 50))},
                     indent=2, ensure_ascii=False))
    return 0
