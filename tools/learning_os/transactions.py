"""Shared transaction pipeline for every LearningOS canonical write.

The existing gateway already serialized writes and rolled them back on validation
failure.  This module turns that mechanism into an explicit service with:

* artifact-level optimistic concurrency;
* an append-only transaction receipt for every committed write;
* one revision ledger shared by CLI capabilities and migrations;
* rollback when staging, validation, projection publication, or receipt writing
  fails.

Revision zero is implicit.  Existing authored files do not need a migration; the
ledger records an artifact the first time a transaction changes it.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import hashlib
import json
import os
import re
import shutil
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from . import revisions as revision_store
from .contracts.gateway import (
    APPROVAL_KINDS,
    GATEWAY_CHANNELS,
    GatewayRequestContext,
    current_gateway_request,
)
from .contracts.write_scopes import (
    WriteScopeError,
    require_write_scope,
    scope_matches,
    write_target,
)
from .errors import TransactionFailure

# One digest, one root list, shared with the projection (see fingerprint.py).
# Re-exported here because the receipt fields and every existing caller name it
# through this module.
from .fingerprint import canonical_fingerprint
from .pathing import PathBoundaryError, read_text_inside
from .revisions import artifact_revision, load_revisions

__all__ = [
    "ReplayEvidenceError",
    "TransactionConflict",
    "TransactionFailure",
    "TransactionIdempotencyConflict",
    "TransactionResult",
    "TransactionSnapshotConflict",
    "TransactionScopeError",
    "TransactionService",
    "artifact_revision",
    "canonical_fingerprint",
    "load_revisions",
    "parse_expected_revisions",
    "reconcile_inflight_transactions",
    "replay_for_request",
]


class TransactionConflict(Exception):
    """One or more expected artifact revisions are stale."""

    def __init__(self, conflicts: Mapping[str, tuple[int, int]]):
        self.conflicts = dict(conflicts)
        detail = ", ".join(
            f"{artifact}: expected {expected}, actual {actual}"
            for artifact, (expected, actual) in sorted(self.conflicts.items())
        )
        super().__init__(f"artifact revision conflict ({detail})")


class TransactionScopeError(TransactionFailure):
    """A transaction target is unsafe or outside its declared capability."""


class TransactionIdempotencyConflict(TransactionFailure):
    """An idempotency key was reused for a different approved intent."""


class TransactionSnapshotConflict(TransactionFailure):
    """The approved projection no longer names the canonical state."""

    def __init__(self, expected: str, actual: str):
        self.expected = expected
        self.actual = actual
        super().__init__(
            "canonical snapshot conflict "
            f"(expected {expected}, actual {actual})"
        )


class ReplayEvidenceError(TransactionFailure):
    """A persisted success claim does not match its own recorded evidence.

    Raised by ``replay_for_request`` whenever the idempotency ledger row and
    its named receipt disagree, are malformed, or fail schema validation.
    Always non-retryable: the underlying write may or may not have happened,
    but the *evidence* is contradictory, so the only safe response is a
    refusal that preserves everything for manual reconciliation. The original
    capability handler must never run in response to this.
    """


@dataclass(frozen=True)
class TransactionResult:
    transaction_id: str
    receipt_path: Path
    revisions: dict[str, int]
    snapshot_before: str
    snapshot_after: str
    replayed: bool = False
    # Populated only for a replayed result: the exact validated receipt
    # ``replay_for_request`` cross-bound against the idempotency ledger. A
    # caller building the replay response or repairing session ownership must
    # read this rather than reopening the receipt file through a separate,
    # weaker helper — every field here has already been checked.
    receipt: Mapping[str, object] | None = None


def parse_expected_revisions(values: Sequence[str] | None) -> dict[str, int]:
    """Parse repeatable ``artifact-id=revision`` CLI tokens."""
    parsed: dict[str, int] = {}
    for raw in values or ():
        artifact, sep, value = str(raw).partition("=")
        artifact = artifact.strip()
        if not sep or not artifact or not value.strip().isdigit():
            raise ValueError(
                f"invalid expected revision '{raw}'; use <artifact-id>=<non-negative integer>"
            )
        revision = int(value)
        if artifact in parsed and parsed[artifact] != revision:
            raise ValueError(f"conflicting expected revisions for '{artifact}'")
        parsed[artifact] = revision
    return parsed


def _sha256_bytes(value: bytes | None) -> str | None:
    return hashlib.sha256(value).hexdigest() if value is not None else None


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


def _dump_idempotency_entries(entries: Mapping[str, Mapping]) -> str:
    return yaml.safe_dump(
        {
            "schema_version": 1,
            "type": "transaction-idempotency-ledger",
            "entries": {key: dict(entries[key]) for key in sorted(entries)},
        },
        sort_keys=False,
        allow_unicode=True,
        width=100,
    )


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


def replay_for_request(
    root: Path,
    request: GatewayRequestContext,
    *,
    authority_root: Path | None = None,
) -> TransactionResult | None:
    """Return the original committed receipt for an exact approved retry.

    Every cross-binding below runs before anything is returned, and a
    mismatch or malformed value always raises rather than silently choosing a
    lenient reading. ``None`` means only one thing: no ledger row exists for
    this idempotency key at all — every other outcome is either a validated
    replay or an exception. Nothing here invokes a capability handler.
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

    return TransactionResult(
        transaction_id=str(row["transaction_id"]),
        receipt_path=receipt_path,
        revisions={str(key): int(value) for key, value in row["revisions"].items()},
        snapshot_before=str(row["snapshot_before"]),
        snapshot_after=str(row["snapshot_after"]),
        replayed=True,
        receipt=receipt,
    )


def _safe_relative(root: Path, path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise TransactionFailure(f"transaction path escapes repository: {path}") from exc


def _atomic_write_bytes(path: Path, content: bytes) -> None:
    """Atomically replace *path* and make the replacement crash-durable.

    ``os.replace`` alone guarantees visibility, not persistence. Flushing the
    file before replacement and the directory after it closes the window where
    a committed receipt can survive while the content it records does not.
    """
    # Preserve the gateway's established atomic sibling name. Existing red-team
    # checks deliberately block this path to verify rollback.
    tmp = path.with_name(f".{path.name}.tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tmp.open("wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except OSError as exc:
        with contextlib.suppress(OSError):
            tmp.unlink(missing_ok=True)
        raise TransactionFailure(
            f"cannot write {path}: {exc.strerror or exc}"
        ) from exc


def _next_transaction_identity(root: Path, now: dt.datetime) -> tuple[str, Path]:
    directory = root / "operations" / "transactions"
    stamp = now.strftime("%Y%m%d-%H%M%S")
    prefix = f"transaction-{stamp}"
    existing = sorted(directory.glob(f"{prefix}-*.yaml"))
    serials = []
    for path in existing:
        match = re.search(r"-(\d+)\.yaml$", path.name)
        if match:
            serials.append(int(match.group(1)))
    serial = max(serials, default=0) + 1
    transaction_id = f"{prefix}-{serial:03d}"
    return transaction_id, directory / f"{transaction_id}.yaml"


def _receipt_text(receipt: Mapping) -> str:
    return yaml.safe_dump(dict(receipt), sort_keys=False, allow_unicode=True, width=100)


def reconcile_inflight_transactions(root: Path) -> None:
    """Roll back any transaction a dead process left half-applied.

    Runs while the operator lock is held, before the command that acquired it
    does anything, so a crashed predecessor's partial write is undone before it
    can be read as canonical state.

    Nothing here is allowed to fail quietly. A recovery that cannot restore a
    file leaves the repository in exactly the half-applied state it was called
    to repair, and a caller that proceeds anyway then reads that state as
    authored truth — the failure this whole mechanism exists to prevent. So
    every problem is collected and raised, and the record is left on disk for
    the next attempt rather than deleted.

    Idempotent by construction: restoring a file to bytes it already holds is a
    no-op, and a record is removed only once its own rollback has fully
    succeeded, so running twice does the same thing as running once.
    """
    inflight_dir = root / "operations" / "transactions" / ".inflight"
    if not inflight_dir.is_dir():
        return

    problems: list[str] = []
    for tx_dir in sorted(inflight_dir.iterdir()):
        if not tx_dir.is_dir():
            continue
        intent_path = tx_dir / "intent.json"
        if not intent_path.is_file():
            # The intent is written before the first canonical replacement, so
            # its absence means the crash happened before anything changed.
            # Only the staged backups are here, and they describe nothing.
            shutil.rmtree(tx_dir, ignore_errors=True)
            continue
        try:
            intent = json.loads(intent_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            problems.append(f"{tx_dir.name}: its record of what to undo is unreadable ({exc})")
            continue

        failures: list[str] = []
        for row in reversed(intent.get("backups", [])):
            relative = row.get("path")
            if not isinstance(relative, str) or not relative:
                failures.append("a record entry names no path")
                continue
            path = (root / relative).resolve()
            if root.resolve() not in path.parents:
                failures.append(f"{relative} resolves outside the repository")
                continue
            try:
                if row.get("created"):
                    # The transaction created this file; undoing means removing it.
                    path.unlink(missing_ok=True)
                elif row.get("backup_id"):
                    backup_file = tx_dir / str(row["backup_id"])
                    if not backup_file.is_file():
                        failures.append(f"{relative}: its backup copy is missing")
                        continue
                    _atomic_write_bytes(path, backup_file.read_bytes())
                else:
                    failures.append(f"{relative}: the record says neither created nor backed up")
            except OSError as exc:
                failures.append(f"{relative}: {exc}")

        if failures:
            problems.append(f"{tx_dir.name}: " + "; ".join(failures))
            continue
        shutil.rmtree(tx_dir, ignore_errors=True)

    if problems:
        raise TransactionFailure(
            "a previous run was interrupted mid-write and could not be rolled back; "
            "the repository may hold part of an unfinished change. Resolve these before "
            "writing again — the rollback records are preserved under "
            f"operations/transactions/.inflight/: {'; '.join(problems)}")


class TransactionService:
    """Commit one validated set of authored writes and one append-only receipt."""

    def __init__(
        self,
        root: Path,
        *,
        clock: Callable[[], dt.datetime] | None = None,
        authority_root: Path | None = None,
        scope_prefix: str | None = None,
    ):
        self.root = root.resolve()
        self.clock = clock or (lambda: dt.datetime.now().astimezone())
        implicit_catalogue = self.root / "system" / "contracts" / "capabilities.yaml"
        self.authority_root = (
            Path(authority_root).resolve()
            if authority_root is not None
            else (self.root if implicit_catalogue.is_file() else None)
        )
        self.scope_prefix = str(scope_prefix or "").strip("/")

    def commit(
        self,
        *,
        capability: str,
        writes: Mapping[Path, str | bytes],
        artifact_ids: Iterable[str],
        deletes: Iterable[Path] = (),
        expected_revisions: Mapping[str, int] | None = None,
        validate_state: Callable[[], Sequence] | None = None,
        publish: Callable[[], str | None] | None = None,
        rollback_publish: Callable[[], None] | None = None,
        touched: Callable[[Iterable[Path]], None] | None = None,
        metadata: Mapping | None = None,
        fingerprint: Callable[[], str] | None = None,
        expected_snapshot: str | None = None,
        transaction_writes: Callable[[str], Mapping[Path, str | bytes]] | None = None,
        write_authorities: Mapping[Path, str] | None = None,
        gateway_request: GatewayRequestContext | None = None,
    ) -> TransactionResult:
        if not capability or not capability.strip():
            raise TransactionFailure("transaction capability must be named")
        request = gateway_request or current_gateway_request()
        if request is not None:
            if request.capability != capability:
                raise TransactionFailure(
                    "gateway request capability does not match transaction capability"
                )
            if request.channel not in GATEWAY_CHANNELS \
                    or request.approval_kind not in APPROVAL_KINDS:
                raise TransactionFailure("gateway request authority is unsupported")
            if request.approval_subject_sha256 != request.intent_sha256 \
                    or not re.fullmatch(r"sha256:[a-f0-9]{64}", request.intent_sha256):
                raise TransactionFailure(
                    "gateway approval is not bound to the transaction intent"
                )
            if self.authority_root is None:
                raise TransactionScopeError(
                    "GatewayEnvelopeV2 requires an enforced capability catalogue"
                )
            replay = replay_for_request(self.root, request, authority_root=self.authority_root)
            if replay is not None:
                return replay

        def target(raw_path: Path) -> tuple[Path, str]:
            try:
                return write_target(self.root, raw_path)
            except WriteScopeError as exc:
                raise TransactionScopeError(str(exc)) from exc

        delete_paths: list[Path] = []
        relative_paths: dict[Path, str] = {}
        for raw_path in deletes:
            path, relative = target(Path(raw_path))
            delete_paths.append(path)
            relative_paths[path] = relative
        if not writes and not delete_paths:
            raise TransactionFailure("transaction contains no writes")

        normalized_writes: dict[Path, bytes] = {}
        for raw_path, value in writes.items():
            path, relative = target(Path(raw_path))
            relative_paths[path] = relative
            normalized_writes[path] = value.encode("utf-8") if isinstance(value, str) else bytes(value)

        for path in delete_paths:
            if path in normalized_writes:
                raise TransactionFailure(f"transaction both writes and deletes {path}")

        authority_by_path: dict[Path, str] = {}
        for raw_path, authority in (write_authorities or {}).items():
            path, relative = target(Path(raw_path))
            relative_paths.setdefault(path, relative)
            if not isinstance(authority, str) or not authority.strip():
                raise TransactionScopeError("write authority names must be non-empty")
            existing = authority_by_path.get(path)
            if existing is not None and existing != authority.strip():
                raise TransactionScopeError(
                    f"transaction declares conflicting authorities for {_safe_relative(self.root, path)}"
                )
            authority_by_path[path] = authority.strip()

        artifacts = sorted({str(value).strip() for value in artifact_ids if str(value).strip()})
        if not artifacts:
            artifacts = [
                f"file:{_safe_relative(self.root, path)}"
                for path in [*normalized_writes, *delete_paths]
            ]

        revisions_before = load_revisions(self.root)
        expected = dict(expected_revisions or {})
        if request is not None and set(expected) != set(artifacts):
            missing = sorted(set(artifacts) - set(expected))
            unexpected = sorted(set(expected) - set(artifacts))
            raise TransactionFailure(
                "GatewayEnvelopeV2 expected_revisions must cover exactly every "
                f"transaction artifact (missing={missing}, unexpected={unexpected})"
            )
        conflicts = {
            artifact: (wanted, revisions_before.get(artifact, 0))
            for artifact, wanted in expected.items()
            if revisions_before.get(artifact, 0) != wanted
        }
        revisions_after = dict(revisions_before)
        changed_revisions: dict[str, int] = {}
        for artifact in artifacts:
            next_value = revisions_before.get(artifact, 0) + 1
            revisions_after[artifact] = next_value
            changed_revisions[artifact] = next_value

        # Allocate the one shared transaction identity before finalising writes.
        # Some transactional bookkeeping (for example an AI request moving to
        # ``completed``) must record that identity in the same atomic commit as
        # the canonical change.  ``transaction_writes`` provides that without
        # inventing a second receipt or updating state after the commit.
        now = self.clock().astimezone().replace(microsecond=0)
        # Prove the service-owned transaction directory is not an indirection
        # before it is created or enumerated for the next receipt identity.
        target(self.root / "operations" / "transactions" / ".authority-check")
        transaction_id, receipt_path = _next_transaction_identity(self.root, now)
        owned_paths: set[Path] = set()
        if transaction_writes is not None:
            try:
                owned_writes = transaction_writes(transaction_id)
            except Exception as exc:
                raise TransactionFailure(
                    f"cannot prepare transaction-owned writes: {exc}"
                ) from exc
            for raw_path, value in owned_writes.items():
                path, relative = target(Path(raw_path))
                relative_paths[path] = relative
                owned_paths.add(path)
                if path in delete_paths:
                    raise TransactionFailure(f"transaction both writes and deletes {path}")
                content = value.encode("utf-8") if isinstance(value, str) else bytes(value)
                if path in normalized_writes and normalized_writes[path] != content:
                    raise TransactionFailure(f"transaction defines conflicting writes for {path}")
                normalized_writes[path] = content

        # The declaration is enforced once, here, after every caller-owned and
        # transaction-owned destination is known and before any file changes.
        authority_grants: dict[str, tuple[str, ...]] = {}
        if self.authority_root is not None:
            from .contracts.capability_catalog import (
                command_definitions,
                domain_capability_definitions,
            )

            definitions = {
                name: definition.writes
                for name, definition in command_definitions(
                    self.authority_root, include_internal=True
                ).items()
            }
            definitions.update({
                name: definition.writes
                for name, definition in domain_capability_definitions(
                    self.authority_root
                ).items()
            })
            service_owned_scopes = ("operations/ai-actions/requests/**",)
            authored_paths = set(normalized_writes) | set(delete_paths)
            for path in sorted(authored_paths, key=lambda value: relative_paths[value]):
                relative = relative_paths[path]
                scoped_relative = (
                    f"{self.scope_prefix}/{relative}" if self.scope_prefix else relative
                )
                authority = authority_by_path.get(path)
                if path in owned_paths and authority is None:
                    if not any(scope_matches(relative, row) for row in service_owned_scopes):
                        raise TransactionScopeError(
                            f"transaction-owned write is not service-owned: {relative}"
                        )
                    continue
                authority = authority or capability
                scopes = definitions.get(authority)
                if scopes is None:
                    raise TransactionScopeError(
                        f"unknown write authority {authority}; refusing {relative}"
                    )
                try:
                    require_write_scope(authority, scoped_relative, scopes)
                except WriteScopeError as exc:
                    raise TransactionScopeError(str(exc)) from exc
                authority_grants[authority] = tuple(scopes)
            unused = set(authority_by_path) - authored_paths
            if unused:
                listing = ", ".join(sorted(relative_paths[path] for path in unused))
                raise TransactionScopeError(
                    f"write authority declared for a path outside the transaction: {listing}"
                )
        elif authority_by_path:
            raise TransactionScopeError(
                "write authorities were supplied without a capability catalogue"
            )

        ledger_path, _ledger_relative = target(
            revision_store.revision_ledger_path(self.root)
        )
        normalized_writes[ledger_path] = revision_store.dump_revisions(
            revisions_after
        ).encode("utf-8")

        idempotency_path: Path | None = None
        idempotency_entries: dict[str, dict] | None = None
        if request is not None:
            idempotency_path, _idempotency_relative = target(
                _idempotency_ledger_path(self.root)
            )
            idempotency_entries = _load_idempotency_entries(self.root)

        all_paths = [*normalized_writes, *delete_paths]
        if idempotency_path is not None:
            all_paths.append(idempotency_path)
        backups: dict[Path, bytes | None] = {
            path: path.read_bytes() if path.is_file() else None for path in all_paths
        }
        # A transaction service rooted somewhere without the canonical roots
        # would digest nothing and record a constant snapshot, which is worse
        # than none: it looks like a guard. Such callers may supply their own
        # digest over the artifacts they actually touch.
        take_fingerprint = fingerprint or (lambda: canonical_fingerprint(self.root))
        snapshot_before = take_fingerprint()
        snapshot_before_id = f"sha256:{snapshot_before}"
        approved_snapshot = expected_snapshot
        if request is not None:
            if approved_snapshot is not None \
                    and request.expected_snapshot is not None \
                    and approved_snapshot != request.expected_snapshot:
                raise TransactionFailure(
                    "transaction expected snapshot does not match its gateway approval"
                )
            approved_snapshot = approved_snapshot or request.expected_snapshot
        if approved_snapshot is not None and approved_snapshot != snapshot_before_id:
            raise TransactionSnapshotConflict(
                approved_snapshot,
                snapshot_before_id,
            )
        # Snapshot staleness is the broader approved-state conflict and keeps
        # its historical precedence when the same concurrent write also moved
        # an artifact revision.
        if conflicts:
            raise TransactionConflict(conflicts)

        inflight_dir = self.root / "operations" / "transactions" / ".inflight" / transaction_id

        def rollback() -> list[str]:
            failures: list[str] = []
            try:
                receipt_path.unlink(missing_ok=True)
            except OSError:
                failures.append(_safe_relative(self.root, receipt_path))
            for path, old in reversed(list(backups.items())):
                try:
                    if old is None:
                        if path.is_file():
                            path.unlink()
                    else:
                        _atomic_write_bytes(path, old)
                except Exception:
                    failures.append(_safe_relative(self.root, path))
            restore_projection = rollback_publish or publish
            if restore_projection is not None:
                try:
                    restore_projection()
                except Exception:
                    failures.append("<projection publication>")
            shutil.rmtree(inflight_dir, ignore_errors=True)
            return sorted(set(failures))

        try:
            inflight_dir.mkdir(parents=True, exist_ok=True)
            intent = {"transaction_id": transaction_id, "backups": []}
            for i, (path, old) in enumerate(backups.items()):
                row = {"path": _safe_relative(self.root, path), "created": old is None}
                if old is not None:
                    backup_id = f"backup-{i}"
                    row["backup_id"] = backup_id
                    _atomic_write_bytes(inflight_dir / backup_id, old)
                intent["backups"].append(row)
            _atomic_write_bytes(inflight_dir / "intent.json", json.dumps(intent).encode("utf-8"))

            for path, content in normalized_writes.items():
                _atomic_write_bytes(path, content)
            for path in delete_paths:
                if path.is_dir():
                    raise TransactionFailure(f"transaction refuses to delete directory: {path}")
                path.unlink(missing_ok=True)
            if validate_state is not None:
                errors = list(validate_state())
                if errors:
                    preview = "; ".join(str(issue) for issue in errors[:6])
                    raise TransactionFailure(
                        f"transaction failed canonical validation: {preview}"
                    )
            projected_snapshot = publish() if publish is not None else None

            snapshot_after = take_fingerprint()
            snapshot_after_id = f"sha256:{snapshot_after}"
            if projected_snapshot is not None \
                    and projected_snapshot != snapshot_after_id:
                raise TransactionFailure(
                    "canonical state changed during projection publication "
                    f"(projected {projected_snapshot}, actual {snapshot_after_id})"
                )
            if request is not None and idempotency_path is not None \
                    and idempotency_entries is not None:
                idempotency_entries[request.idempotency_key] = {
                    "request_id": request.request_id,
                    "capability": capability,
                    "channel": request.channel,
                    "intent_sha256": request.intent_sha256,
                    "transaction_id": transaction_id,
                    "receipt_path": _safe_relative(self.root, receipt_path),
                    "revisions": dict(changed_revisions),
                    "snapshot_before": snapshot_before_id,
                    "snapshot_after": snapshot_after_id,
                }
                idempotency_content = _dump_idempotency_entries(
                    idempotency_entries
                ).encode("utf-8")
                _atomic_write_bytes(idempotency_path, idempotency_content)
                normalized_writes[idempotency_path] = idempotency_content
            rows = []
            for path, after in normalized_writes.items():
                if path == ledger_path or path == idempotency_path:
                    continue
                before = backups.get(path)
                rows.append({
                    "path": _safe_relative(self.root, path),
                    "sha256_before": _sha256_bytes(before),
                    "sha256_after": _sha256_bytes(after),
                    "created": before is None,
                })
            for path in delete_paths:
                before = backups.get(path)
                rows.append({
                    "path": _safe_relative(self.root, path),
                    "sha256_before": _sha256_bytes(before),
                    "sha256_after": None,
                    "created": False,
                })
            receipt = {
                "schema_version": 2 if request is not None else 1,
                "id": transaction_id,
                "type": "transaction-receipt",
                "status": "committed",
                "capability": capability,
                "committed_at": now.isoformat(),
                "snapshot_before": snapshot_before_id,
                "snapshot_after": snapshot_after_id,
                "expected_revisions": expected,
                "artifact_revisions": {
                    artifact: {
                        "before": revisions_before.get(artifact, 0),
                        "after": changed_revisions[artifact],
                    }
                    for artifact in artifacts
                },
                "writes": sorted(rows, key=lambda row: row["path"]),
                "metadata": dict(metadata or {}),
            }
            if request is not None:
                receipt["authority"] = {
                    "capability_contract_version": 2,
                    "enforced": self.authority_root is not None,
                    "grants": [
                        {
                            "capability": authority,
                            "declared_writes": list(authority_grants[authority]),
                        }
                        for authority in sorted(authority_grants)
                    ],
                }
                receipt["request"] = {
                    "channel": request.channel,
                    "request_id": request.request_id,
                    "idempotency_key": request.idempotency_key,
                    "intent_sha256": request.intent_sha256,
                    "approval": {
                        "kind": request.approval_kind,
                        "subject_sha256": request.approval_subject_sha256,
                    },
                }
            receipt_schema = json.loads(
                (self.authority_root or self.root).joinpath(
                    "system", "schema", "transaction-receipt.schema.json"
                ).read_text(encoding="utf-8")
            ) if (self.authority_root or self.root).joinpath(
                "system", "schema", "transaction-receipt.schema.json"
            ).is_file() else None
            if receipt_schema is not None:
                receipt_errors = sorted(
                    Draft202012Validator(receipt_schema).iter_errors(receipt),
                    key=lambda error: list(error.path),
                )
                if receipt_errors:
                    detail = "; ".join(
                        f"/{'/'.join(str(part) for part in error.path)}: {error.message}"
                        for error in receipt_errors[:4]
                    )
                    raise TransactionFailure(
                        f"transaction receipt v{receipt['schema_version']} is invalid: {detail}"
                    )
            if receipt_path.exists():
                raise TransactionFailure(f"receipt path already exists: {receipt_path}")
            _atomic_write_bytes(receipt_path, _receipt_text(receipt).encode("utf-8"))
            # Bookkeeping is part of the commit boundary. If it fails, remove
            # the newly-created receipt together with the canonical writes so
            # transaction history can never claim a rolled-back change.
            safe_receipt_path, _receipt_relative = target(receipt_path)
            backups[safe_receipt_path] = None
            if touched is not None:
                touched([*normalized_writes, *delete_paths, receipt_path])
            shutil.rmtree(inflight_dir, ignore_errors=True)
            return TransactionResult(
                transaction_id=transaction_id,
                receipt_path=receipt_path,
                revisions=changed_revisions,
                snapshot_before=snapshot_before_id,
                snapshot_after=snapshot_after_id,
            )
        except Exception as exc:
            rollback_failures = rollback()
            if rollback_failures:
                raise TransactionFailure(
                    f"{exc}; rollback incomplete for: {', '.join(rollback_failures)}"
                ) from exc
            if isinstance(exc, TransactionFailure):
                raise
            raise TransactionFailure(str(exc)) from exc
