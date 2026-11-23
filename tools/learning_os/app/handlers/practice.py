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
from typing import NotRequired, TypedDict, cast

from learning_os.app.context import OpContext
from learning_os.app.proposal import Result, TransactionProposal
from learning_os.app.registry import OperationEffects, register
from learning_os.domain.failures import NotFound, WriteRefused
from learning_os.domain.practice import content_sha256, extract_items
from learning_os.domain.relations import EvidenceBinding
from learning_os.store import observations
from learning_os.store.contracts.gateway import current_gateway_request
from learning_os.store.contracts.json_schema import validate_contract
from learning_os.store.fingerprint import snapshot as _snapshot
from learning_os.store.practice import (
    ARTIFACT_ID,
    PracticeIndex,
    PracticeProof,
    PracticeRow,
    dump_sidecar,
    load_sidecar,
    note_items,
    current_material_digest,
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


class PracticeContextRequest(TypedDict):
    note_id: str
    item_id: NotRequired[str]
    expected_snapshot: NotRequired[str]


class ReviewedVerification(TypedDict):
    item_id: str
    expected_old: object
    new_status: str
    method: str
    concept_ids: list[str]
    artifact_sha256: str
    reviewer_id: str
    source_binding: NotRequired[dict[str, object] | None]
    comparison_sha256: NotRequired[str | None]


@register("practice.context", kind="porcelain", effects=OperationEffects.READ)
def practice_context(ctx: OpContext, req: dict[str, object]) -> Result:
    """Prompt-safe practice summaries for one note, at one snapshot."""
    root = ctx.root
    request = cast(PracticeContextRequest, req)
    snapshot = _snapshot(root, request.get("expected_snapshot"))
    repo = ctx.repo()
    note = repo.notes.get(request["note_id"])
    if note is None:
        raise NotFound(
            "note", request["note_id"], repo.notes,
            site="practice.context.unknown-note")
    effective, diagnostics = note_items(repo, note)
    if request.get("item_id"):
        matched = [row for row in effective if row.item.item_id == request["item_id"]]
        if not matched:
            raise NotFound(
                "practice item", request["item_id"],
                [entry.item.item_id for entry in effective],
                site="practice.context.unknown-item")
        effective = matched
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
            "concept_ids": list((row["concept_ids"] if row else []) or note.meta.get("concepts") or []),
            "stored_row": copy.deepcopy(row),
        })
    if _snapshot(root) != snapshot:
        raise WriteRefused(
            "snapshot changed while reading practice context",
            site="practice.context.snapshot-changed")
    result: dict[str, object] = {
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
def practice_verification_record(ctx: OpContext, req: dict[str, object]) -> Result:
    """Record one reviewed verification in the practice sidecar."""
    root = ctx.root
    if current_gateway_request() is None:
        raise WriteRefused(
            "practice verification requires GatewayEnvelopeV2",
            site="practice.verification.record.gateway-required",
            prefixed=True, exit_code=2)
    record = cast(ReviewedVerification, req["record"])
    item_id = record["item_id"]
    note_id, _, label = item_id.partition("#")
    repo = ctx.repo()
    note = repo.notes.get(note_id)
    if note is None or not label:
        raise WriteRefused(
            "record names an unknown practice item",
            site="practice.verification.record.unknown-item")
    extraction = extract_items(note.id, note.meta.get("role"), note.body)
    item = next((row for row in extraction.items if row.item_id == item_id), None)
    if item is None:
        # Gated per item: a problem with one item (or the whole note's
        # markup) blocks that item only; its clean siblings stay recordable.
        problems = [d.reason for d in extraction.diagnostics
                    if d.label in (None, label)]
        if problems:
            raise WriteRefused(
                f"practice item {item_id} is ambiguous or unsupported: "
                + "; ".join(problems),
                site="practice.verification.record.ambiguous-item")
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
        if "file_sha256" not in binding:
            # Core pins the file it can read; a person never types a digest.
            binding = {
                "source_id": binding.get("source_id"),
                "material_relpath": binding.get("material_relpath"),
                "file_sha256": current_material_digest(
                    repo, binding.get("material_relpath")) or "",
                **{key: value for key, value in binding.items()
                   if key not in ("source_id", "material_relpath")},
            }
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

    source_binding = cast(EvidenceBinding, copy.deepcopy(binding)) if status == "source-matched" else None
    proof: PracticeProof = {
        "method": record["method"],
        "verified_at": observations.now().astimezone(UTC).isoformat(),
        "artifact_sha256": record["artifact_sha256"],
        "reviewer_id": record["reviewer_id"],
        "source_binding": source_binding,
        "comparison_sha256": record.get("comparison_sha256"),
    }
    bindings = list(current["source_bindings"]) if current else []
    if source_binding is not None and source_binding not in bindings:
        bindings.append(source_binding)
    new_row: PracticeRow = {
        "item_id": item_id,
        "concept_ids": list(record["concept_ids"]),
        "kind": item.kind,
        "status": status,
        "content_sha256": content_sha256(item.item_id, item.prompt, item.solution),
        "source_bindings": bindings,
        "verifications": [*(current["verifications"] if current else []), proof],
    }
    rows = [row for row in data["items"] if row["item_id"] != item_id]
    rows.append(new_row)
    new_data: PracticeIndex = {"items": rows}
    from learning_os.store.contracts.json_schema import load_standalone_validator

    validator = load_standalone_validator(
        root / "system/schema/practice-index.schema.json", format_checker=True)
    errors = sorted(validator.iter_errors(new_data), key=str)
    if errors:
        raise WriteRefused(
            f"practice-index: {errors[0].message}",
            site="practice.verification.record.bad-proof")
    if record["artifact_sha256"] != new_row["content_sha256"]:
        # The proof binds what was reviewed: the item's content hash as
        # practice.context showed it. Anything else reviewed other content.
        raise WriteRefused(
            "the reviewed item content differs from the current item; "
            "reload practice items and review it again",
            site="practice.verification.record.artifact-mismatch")
    path = sidecar_path(root)
    try:
        expected_revisions = parse_expected_revisions(cast(list[str] | None, req.get("expected_revision")))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site="practice.verification.record.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "item_id": item_id, "status": status},
        proposal=TransactionProposal(
            capability="practice.verification.record",
            writes={path: dump_sidecar(new_data)},
            artifact_ids=(ARTIFACT_ID, note.id),
            expected_revisions=expected_revisions,
        ),
    )
