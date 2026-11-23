"""Practice verification handlers (P6 steps 35-36).

`practice.context` is a bounded, snapshot-bound read of prompt-safe item
summaries — never solution text. `practice.verification.record` is the one
guarded gesture that writes the sidecar: it recomputes the item and its
content hash in the handler, checks the status-specific proof, and binds the
exact expected old row plus both artifact revisions.
"""

from __future__ import annotations

import copy
from datetime import UTC

from learning_os.app.context import OpContext
from learning_os.app.proposal import Result, TransactionProposal
from learning_os.app.registry import OperationEffects, register
from learning_os.domain.failures import NotFound, WriteRefused
from learning_os.domain.practice import content_sha256, extract_items
from learning_os.store import observations
from learning_os.store.contracts.gateway import current_gateway_request
from learning_os.store.contracts.json_schema import validate_contract
from learning_os.store.fingerprint import snapshot as _snapshot
from learning_os.store.practice import (
    ARTIFACT_ID,
    dump_sidecar,
    load_sidecar,
    note_items,
    row_for,
    sidecar_path,
    verified_binding,
)
from learning_os.store.revisions import artifact_revision
from learning_os.store.transactions import parse_expected_revisions

METHOD_FOR_STATUS = {
    "source-matched": "official-source",
    "cross-checked": "independent-solve",
    "confirmed": "explicit-review",
    "disputed": "explicit-review",
    "unverified": "explicit-review",
}


@register("practice.context", kind="porcelain", effects=OperationEffects.READ)
def practice_context(ctx: OpContext, req: dict) -> Result:
    """Prompt-safe practice summaries for one note, at one snapshot."""
    root = ctx.root
    snapshot = _snapshot(root, req.get("expected_snapshot"))
    repo = ctx.repo()
    note = repo.notes.get(req["note_id"])
    if note is None:
        raise NotFound(
            "note", req["note_id"], repo.notes,
            site="practice.context.unknown-note")
    effective, diagnostics = note_items(repo, note)
    if req.get("item_id"):
        effective = [row for row in effective if row.item.item_id == req["item_id"]]
        if not effective:
            raise NotFound(
                "practice item", req["item_id"], [],
                site="practice.context.unknown-item")
    items = []
    for entry in effective:
        row = entry.row
        items.append({
            "item_id": entry.item.item_id,
            "label": entry.item.label,
            "kind": entry.item.kind,
            "prompt": entry.item.prompt,
            "status": entry.status,
            "checked": entry.checked,
            "ineligibility": list(entry.reasons),
            "content_sha256": content_sha256(
                entry.item.item_id, entry.item.prompt, entry.item.solution),
            "concept_ids": list((row or {}).get("concept_ids")
                                or note.meta.get("concepts") or []),
            "stored_row": copy.deepcopy(row),
        })
    if _snapshot(root) != snapshot:
        raise WriteRefused(
            "snapshot changed while reading practice context",
            site="practice.context.snapshot-changed")
    result = {
        "schema_version": 1, "snapshot_id": snapshot,
        "contract": "practice-context-v1",
        "note_id": note.id,
        "note_revision": artifact_revision(root, note.id),
        "practice_index_revision": artifact_revision(root, ARTIFACT_ID),
        "diagnostics": diagnostics,
        "items": items,
    }
    validate_contract(root, "practice-context.schema.json", result)
    return Result(result)


@register("practice.verification.record", kind="command",
          effects=OperationEffects.CANONICAL_WRITE)
def practice_verification_record(ctx: OpContext, req: dict) -> Result:
    """Record one reviewed verification in the practice sidecar."""
    root = ctx.root
    if current_gateway_request() is None:
        raise WriteRefused(
            "practice verification requires GatewayEnvelopeV2",
            site="practice.verification.record.gateway-required",
            prefixed=True, exit_code=2)
    record = req["record"]
    item_id = record["item_id"]
    note_id, _, label = item_id.partition("#")
    repo = ctx.repo()
    note = repo.notes.get(note_id)
    if note is None or not label:
        raise WriteRefused(
            "record names an unknown practice item",
            site="practice.verification.record.unknown-item")
    extraction = extract_items(note.id, note.meta.get("role"), note.body)
    if extraction.diagnostics:
        raise WriteRefused(
            "note items are ambiguous or unsupported: "
            + "; ".join(d.reason for d in extraction.diagnostics),
            site="practice.verification.record.ambiguous-note")
    item = next((row for row in extraction.items if row.item_id == item_id), None)
    if item is None:
        raise WriteRefused(
            "record names an unknown practice item",
            site="practice.verification.record.unknown-item")
    unknown = [cid for cid in record["concept_ids"] if cid not in repo.concepts]
    if unknown:
        raise WriteRefused(
            f"record names unknown concepts: {', '.join(sorted(unknown))}",
            site="practice.verification.record.unknown-concept")

    status = record["new_status"]
    if status not in METHOD_FOR_STATUS:
        raise WriteRefused(
            f"unknown verification status: {status}",
            site="practice.verification.record.bad-status")
    if record["method"] != METHOD_FOR_STATUS[status]:
        raise WriteRefused(
            f"status {status} requires method {METHOD_FOR_STATUS[status]}",
            site="practice.verification.record.method-mismatch")
    binding = record.get("source_binding")
    if status == "source-matched":
        if not isinstance(binding, dict):
            raise WriteRefused(
                "source-matched requires the official answer's source binding",
                site="practice.verification.record.binding-required")
        problem = verified_binding(repo, binding)
        if problem:
            raise WriteRefused(
                problem, site="practice.verification.record.binding-refused")
    if status == "cross-checked" and not record.get("comparison_sha256"):
        raise WriteRefused(
            "cross-checked requires an independently solved comparison digest",
            site="practice.verification.record.comparison-required")

    data = load_sidecar(root)
    current = row_for(data, item_id)
    if record["expected_old"] != current:
        raise WriteRefused(
            "the expected old verification row no longer matches; reload and review",
            site="practice.verification.record.stale-row")

    proof = {
        "method": record["method"],
        "verified_at": observations.now().astimezone(UTC).isoformat(),
        "artifact_sha256": record["artifact_sha256"],
        "reviewer_id": record["reviewer_id"],
        "source_binding": copy.deepcopy(binding) if status == "source-matched" else None,
        "comparison_sha256": record.get("comparison_sha256"),
    }
    bindings = list((current or {}).get("source_bindings") or [])
    if status == "source-matched" and binding not in bindings:
        bindings.append(copy.deepcopy(binding))
    new_row = {
        "item_id": item_id,
        "concept_ids": list(record["concept_ids"]),
        "kind": item.kind,
        "status": status,
        "content_sha256": content_sha256(item.item_id, item.prompt, item.solution),
        "source_bindings": bindings,
        "verifications": [*((current or {}).get("verifications") or []), proof],
    }
    rows = [row for row in data["items"] if row["item_id"] != item_id]
    rows.append(new_row)
    new_data = {"items": rows}
    from learning_os.store.contracts.json_schema import load_standalone_validator

    validator = load_standalone_validator(
        root / "system/schema/practice-index.schema.json", format_checker=True)
    errors = sorted(validator.iter_errors(new_data), key=str)
    if errors:
        raise WriteRefused(
            f"practice-index: {errors[0].message}",
            site="practice.verification.record.bad-proof")
    path = sidecar_path(root)
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site="practice.verification.record.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "item_id": item_id, "status": status},
        proposal=TransactionProposal(
            capability="practice.verification.record",
            writes={path: dump_sidecar(new_data)},
            artifact_ids=[ARTIFACT_ID, note.id],
            expected_revisions=expected_revisions,
        ),
    )
