"""One strict verifier for committed-write evidence.

``replay_for_request`` (the Gateway) and the Diagnostics resolver
(Operations) must never disagree about whether a receipt proves a commit,
so both call :func:`verify_committed_evidence` here instead of each
carrying its own checklist. The checks bind the idempotency ledger row,
its named receipt file, the live revision floor, and the capability
catalog field by field; any mismatch raises rather than choosing a
lenient reading.

This module sits below orchestration in the dependency graph: it reads
evidence but never writes, never imports the transaction engine, and
keeps its heavier catalog/delivery imports lazy the way the moved code
always has.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from .contracts.gateway import GatewayRequestContext
from .contracts.write_scopes import WriteScopeError, scope_matches, write_target
from .errors import (
    ReplayEvidenceError,
    TransactionFailure,
    TransactionIdempotencyConflict,
)
from .pathing import PathBoundaryError, read_text_inside
from .revisions import load_revisions


def _idempotency_ledger_path(root: Path) -> Path:
    return root / "operations" / "transactions" / "idempotency.yaml"


def _load_idempotency_entries(root: Path) -> dict[str, dict]:
    path = _idempotency_ledger_path(root)
    if not path.exists() and not path.is_symlink():
        return {}
    try:
        from .loading.yamlio import UniqueKeySafeLoader

        data = yaml.load(read_text_inside(root, path), Loader=UniqueKeySafeLoader)
    except (OSError, PathBoundaryError, yaml.YAMLError) as exc:
        raise TransactionFailure(f"idempotency ledger is unreadable: {path}: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != 1 \
            or data.get("type") != "transaction-idempotency-ledger":
        raise TransactionFailure("idempotency ledger has an unsupported contract")
    entries = data.get("entries")
    if not isinstance(entries, dict):
        raise TransactionFailure("idempotency ledger entries must be a mapping")
    normalized: dict[str, dict] = {}
    for key, row in entries.items():
        if not isinstance(key, str) or not key or not isinstance(row, dict):
            raise TransactionFailure("idempotency ledger contains an invalid entry")
        required = {
            "request_id", "capability", "channel", "intent_sha256", "transaction_id",
            "receipt_path", "revisions", "snapshot_before", "snapshot_after",
        }
        if set(row) != required or not all(isinstance(row.get(name), str) for name in (
            "request_id", "capability", "channel", "intent_sha256", "transaction_id",
            "receipt_path", "snapshot_before", "snapshot_after",
        )) or not isinstance(row.get("revisions"), dict):
            raise TransactionFailure(f"idempotency ledger entry is malformed: {key}")
        if any(
            not isinstance(artifact, str) or isinstance(revision, bool)
            or not isinstance(revision, int) or revision < 0
            for artifact, revision in row["revisions"].items()
        ):
            raise TransactionFailure(f"idempotency ledger revisions are malformed: {key}")
        normalized[key] = dict(row)
    return normalized


def _default_authority_root(root: Path) -> Path | None:
    implicit_catalogue = root / "system" / "contracts" / "capabilities.yaml"
    return root if implicit_catalogue.is_file() else None


def _proven_delivery_delegation(root: Path, receipt: Mapping) -> set[str]:
    """Return the domain capabilities this receipt's bound delivery actually proves.

    An ``ai-action.delivery.apply`` receipt may claim delegated grants, but a
    claim in the receipt under review is not evidence of itself. This
    re-reads and hash-verifies the exact approved delivery the receipt names
    (the same binding ``apply_delivery`` performed at commit time) and treats
    only the capability names its own operations record as proven. It never
    trusts ``receipt["authority"]`` for this — that is precisely the field
    being checked.
    """
    metadata = receipt.get("metadata")
    delivery_id = metadata.get("delivery_id") if isinstance(metadata, dict) else None
    approved = metadata.get("approved_delivery") if isinstance(metadata, dict) else None
    delivery_sha256 = approved.get("delivery_sha256") if isinstance(approved, dict) else None
    artifact_sha256 = approved.get("artifact_sha256") if isinstance(approved, dict) else None
    if not isinstance(delivery_id, str) or not delivery_id \
            or not isinstance(delivery_sha256, str) \
            or not isinstance(artifact_sha256, dict):
        raise ReplayEvidenceError(
            "idempotent receipt for ai-action.delivery.apply carries no bound "
            "delivery evidence to prove its delegated authority"
        )

    from .ai_actions.binding import read_bound_delivery
    from .ai_actions.errors import AIActionError
    from .ai_actions.storage import FilesystemAIActionRepository

    # Resolving the id is inside the guard too: the exchange-identifier rule is
    # stricter than the receipt schema's `safeArtifactId` (which accepts a
    # two-character id the repository refuses), so a schema-valid receipt can
    # still make this raise. Letting an AIActionError escape here would leave
    # the gateway with an unhandled traceback instead of a typed refusal.
    try:
        directory = FilesystemAIActionRepository(root).delivery_dir(delivery_id)
        delivery, _artifacts = read_bound_delivery(
            directory, delivery_sha256=delivery_sha256, artifact_sha256=artifact_sha256,
        )
    except AIActionError as exc:
        raise ReplayEvidenceError(
            f"cannot re-verify the delivery this receipt claims: {exc}"
        ) from exc

    # The delivery must be the one whose request this transaction actually
    # wrote. `metadata.delivery_id` is part of the evidence under review, so on
    # its own it only proves that *some* real delivery has those bytes: a
    # tampered receipt could point at an unrelated delivery that happens to
    # carry the capability it wants proven. Every `ai-action.delivery.apply`
    # transaction writes its request record, and a delivery names that same
    # request, so requiring the two to agree ties the delivery back to a write
    # row this receipt cannot invent.
    request_id = delivery.get("request_id")
    if not isinstance(request_id, str) or not request_id:
        raise ReplayEvidenceError("bound delivery for this receipt names no request")
    written_paths = {
        row.get("path") for row in receipt.get("writes") or () if isinstance(row, dict)
    }
    if f"operations/ai-actions/requests/{request_id}/request.yaml" not in written_paths:
        raise ReplayEvidenceError(
            "the delivery this receipt names belongs to a different request than "
            "the one this transaction wrote"
        )

    operations = delivery.get("operations")
    if not isinstance(operations, list):
        raise ReplayEvidenceError("bound delivery for this receipt has no operations")
    proven: set[str] = set()
    for operation in operations:
        if not isinstance(operation, dict) or not isinstance(operation.get("capability"), str):
            raise ReplayEvidenceError("bound delivery for this receipt has a malformed operation")
        proven.add(operation["capability"])
    # `garden.update` bookkeeping (the AI-side state file) is written on every
    # pilot delivery except a whole-unit material-synthesis delivery, whether
    # or not an explicit `garden.update` operation is present — see
    # `AIActionService.apply_delivery`. The `action_id` that decides it is read
    # from the hash-verified delivery, never from the receipt's own metadata:
    # metadata is part of the evidence under review, so letting it name the
    # action would let a tampered receipt grant itself this scope by writing a
    # different action id.
    if delivery.get("action_id") != "unit.compare-materials":
        proven.add("garden.update")
    return proven


def verify_committed_evidence(
    root: Path,
    request: GatewayRequestContext,
    *,
    authority_root: Path | None = None,
) -> tuple[dict, dict, Path] | None:
    """Verify the committed evidence for one idempotency key, strictly.

    The single checklist behind both ``replay_for_request`` (which turns a
    hit into a ``TransactionResult``) and the Diagnostics resolver (which
    turns it into a COMMITTED verdict). Every cross-binding below runs
    before anything is returned, and a mismatch or malformed value always
    raises rather than silently choosing a lenient reading. ``None`` means
    only one thing: no ledger row exists for this idempotency key at all —
    every other outcome is either verified ``(receipt, row, receipt_path)``
    or an exception. Nothing here invokes a capability handler.

    The resolver passes the ledger row's own channel/intent as the trusted
    request facts (plus the trace's request/key/capability identity), with
    the approval subject bound by the admission invariant
    (approval == intent). Tampering with either side of the row/receipt
    pair therefore fails here exactly as it fails a live replay.
    """
    row = _load_idempotency_entries(root).get(request.idempotency_key)
    if row is None:
        return None
    if row["capability"] != request.capability \
            or row["intent_sha256"] != request.intent_sha256:
        raise TransactionIdempotencyConflict(
            "idempotency key was already used for a different approved intent"
        )
    if row["request_id"] != request.request_id:
        raise ReplayEvidenceError(
            "idempotency ledger records a different request id for this key"
        )
    if row["channel"] != request.channel:
        raise ReplayEvidenceError(
            "idempotency ledger records a different channel for this key"
        )

    receipt_relative = str(row["receipt_path"])
    try:
        receipt_path, normalized = write_target(root, root / receipt_relative)
    except WriteScopeError as exc:
        raise ReplayEvidenceError(
            f"idempotency ledger names an unsafe receipt: {exc}"
        ) from exc
    if normalized != receipt_relative or not receipt_path.is_file():
        raise ReplayEvidenceError(
            "idempotency ledger names a missing or non-canonical receipt"
        )

    from .loading.yamlio import UniqueKeySafeLoader

    try:
        receipt = yaml.load(read_text_inside(root, receipt_path), Loader=UniqueKeySafeLoader)
    except (OSError, PathBoundaryError, yaml.YAMLError) as exc:
        raise ReplayEvidenceError(f"idempotent receipt is unreadable: {exc}") from exc
    if not isinstance(receipt, dict):
        raise ReplayEvidenceError("idempotent receipt is not a mapping")

    schema_root = authority_root or _default_authority_root(root) or root
    schema_path = schema_root / "system" / "schema" / "transaction-receipt.schema.json"
    if not schema_path.is_file():
        raise ReplayEvidenceError(
            "no transaction receipt schema available to verify replay evidence"
        )
    receipt_schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema_errors = sorted(
        Draft202012Validator(receipt_schema).iter_errors(receipt),
        key=lambda error: list(error.path),
    )
    if schema_errors:
        detail = "; ".join(
            f"{'/'.join(str(part) for part in error.path) or '<receipt>'}: {error.message}"
            for error in schema_errors[:4]
        )
        raise ReplayEvidenceError(f"idempotent receipt fails schema validation: {detail}")

    if receipt.get("schema_version") != 2:
        raise ReplayEvidenceError("idempotent receipt is not a GatewayEnvelopeV2 receipt")
    if receipt.get("id") != row["transaction_id"]:
        raise ReplayEvidenceError("idempotent receipt id does not match its ledger entry")
    if receipt.get("capability") != request.capability:
        raise ReplayEvidenceError("idempotent receipt names a different capability")
    if receipt.get("status") != "committed":
        raise ReplayEvidenceError("idempotent receipt is not committed")

    receipt_request = receipt.get("request")
    if not isinstance(receipt_request, dict):
        raise ReplayEvidenceError("idempotent receipt has no request record")
    if receipt_request.get("idempotency_key") != request.idempotency_key:
        raise ReplayEvidenceError("idempotent receipt does not match its ledger entry")
    if receipt_request.get("intent_sha256") != request.intent_sha256:
        raise ReplayEvidenceError("idempotent receipt does not match its ledger entry")
    if receipt_request.get("request_id") != request.request_id:
        raise ReplayEvidenceError("idempotent receipt names a different request id")
    if receipt_request.get("channel") != request.channel:
        raise ReplayEvidenceError("idempotent receipt names a different channel")
    approval = receipt_request.get("approval")
    approval_subject = approval.get("subject_sha256") if isinstance(approval, dict) else None
    if approval_subject != request.approval_subject_sha256:
        raise ReplayEvidenceError(
            "idempotent receipt approval subject does not match this request"
        )

    if receipt.get("snapshot_before") != row["snapshot_before"] \
            or receipt.get("snapshot_after") != row["snapshot_after"]:
        raise ReplayEvidenceError("idempotent receipt snapshot does not match its ledger entry")

    artifact_revisions = receipt.get("artifact_revisions")
    if not isinstance(artifact_revisions, dict):
        raise ReplayEvidenceError("idempotent receipt has no artifact revisions")
    for artifact, after in row["revisions"].items():
        entry = artifact_revisions.get(artifact)
        if not isinstance(entry, dict) or entry.get("after") != after:
            raise ReplayEvidenceError(
                f"idempotent receipt artifact revision does not match its ledger entry: {artifact}"
            )

    # The live revision ledger must not contradict this receipt.
    #
    # Everything above cross-binds the ledger *row* against the receipt; until
    # this check, nothing compared either against `revisions.yaml` itself, so a
    # rolled-back or hand-edited revision ledger replayed cleanly. Revisions
    # only ever increase, so an artifact standing below the value this
    # transaction recorded is provable mutation — the one thing about these
    # shared, multi-entry ledgers a single receipt *can* prove. (The
    # idempotency ledger needs no equivalent: its row for this key is already
    # cross-bound field by field above.)
    live_revisions = load_revisions(root)
    for artifact, after in row["revisions"].items():
        current = live_revisions.get(artifact, 0)
        if current < after:
            raise ReplayEvidenceError(
                f"the artifact revision ledger contradicts this receipt: {artifact} "
                f"stands at {current}, below the {after} this transaction recorded"
            )

    writes = receipt.get("writes")
    if not isinstance(writes, list) or not writes:
        raise ReplayEvidenceError("idempotent receipt records no writes")

    # A transaction's writes are not always all authorized by its own top-level
    # capability: `ai-action.delivery.apply`, for example, writes its own
    # service-owned bookkeeping directly but delegates the canonical write to
    # whatever domain capability originally owns that destination (recorded in
    # `write_authorities` at commit time). But the receipt's own
    # `authority.grants` is a claim made by the same untrusted evidence under
    # review here — it can never be trusted merely because every named
    # capability is a real, known catalogue entry. An ordinary gateway receipt
    # may claim exactly the one grant its own top-level capability produced;
    # an `ai-action.delivery.apply` receipt may additionally claim delegated
    # domain grants, but only ones proven by re-reading and hash-verifying the
    # exact approved delivery this receipt names, never merely asserted.
    authority = receipt.get("authority")
    grants = authority.get("grants") if isinstance(authority, dict) else None
    if not isinstance(grants, list) or not grants:
        raise ReplayEvidenceError("idempotent receipt has no authority grants")

    resolved_authority_root = authority_root or _default_authority_root(root)
    allowed_scopes: list[str] = []
    if resolved_authority_root is not None:
        from .contracts.capability_catalog import (
            command_definitions,
            domain_capability_definitions,
        )

        scopes_by_capability = {
            name: definition.writes
            for name, definition in {
                **command_definitions(resolved_authority_root, include_internal=True),
                **domain_capability_definitions(resolved_authority_root),
            }.items()
        }

        def catalog_scopes_for(name: str) -> tuple[str, ...]:
            scopes = scopes_by_capability.get(name)
            if scopes is None:
                raise ReplayEvidenceError(
                    f"idempotent receipt names an unknown write authority: {name}"
                )
            return scopes

        granted_capabilities: list[str] = []
        for grant in grants:
            if not isinstance(grant, dict):
                raise ReplayEvidenceError("idempotent receipt authority grant is malformed")
            granted_capability = grant.get("capability")
            declared = grant.get("declared_writes")
            if not isinstance(granted_capability, str) or not isinstance(declared, list):
                raise ReplayEvidenceError("idempotent receipt authority grant is malformed")
            if tuple(declared) != tuple(catalog_scopes_for(granted_capability)):
                raise ReplayEvidenceError(
                    "idempotent receipt authority grant does not match the declared "
                    f"capability scope: {granted_capability}"
                )
            granted_capabilities.append(granted_capability)

        if request.capability == "ai-action.delivery.apply":
            if "ai-action.delivery.apply" not in granted_capabilities:
                raise ReplayEvidenceError(
                    "idempotent receipt for ai-action.delivery.apply carries no grant "
                    "for its own top-level capability"
                )
            delegated = sorted(
                {c for c in granted_capabilities if c != "ai-action.delivery.apply"}
            )
            if delegated:
                proven = _proven_delivery_delegation(root, receipt)
                unproven = [c for c in delegated if c not in proven]
                if unproven:
                    raise ReplayEvidenceError(
                        "idempotent receipt claims AI-action delegated authority its "
                        f"bound delivery does not prove: {', '.join(unproven)}"
                    )
        elif granted_capabilities != [request.capability]:
            raise ReplayEvidenceError(
                "idempotent receipt authority grants must carry exactly the top-level "
                "request capability"
            )

        for granted_capability in granted_capabilities:
            allowed_scopes.extend(catalog_scopes_for(granted_capability))

    for entry in writes:
        if not isinstance(entry, dict):
            raise ReplayEvidenceError("idempotent receipt write row is malformed")
        relative = entry.get("path")
        if not isinstance(relative, str) or not relative:
            raise ReplayEvidenceError("idempotent receipt write row names no path")
        try:
            _write_path, normalized_write = write_target(root, root / relative)
        except WriteScopeError as exc:
            raise ReplayEvidenceError(
                f"idempotent receipt write path is unsafe: {exc}"
            ) from exc
        if normalized_write != relative:
            raise ReplayEvidenceError(
                f"idempotent receipt write path is not canonical: {relative}"
            )
        if resolved_authority_root is not None and not any(
            scope_matches(relative, pattern) for pattern in allowed_scopes
        ):
            raise ReplayEvidenceError(
                "idempotent receipt write path is outside its capability's "
                f"declared scope: {relative}"
            )

    return receipt, row, receipt_path
