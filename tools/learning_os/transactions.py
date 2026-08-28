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
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

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

# One digest, one root list, shared with the projection (see fingerprint.py).
# Re-exported here because the receipt fields and every existing caller name it
# through this module.
from .fingerprint import canonical_fingerprint
from .pathing import PathBoundaryError, read_text_inside

__all__ = [
    "TransactionConflict",
    "TransactionFailure",
    "TransactionIdempotencyConflict",
    "TransactionResult",
    "TransactionScopeError",
    "TransactionService",
    "artifact_revision",
    "canonical_fingerprint",
    "load_revisions",
    "parse_expected_revisions",
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


class TransactionFailure(Exception):
    """The transaction could not commit and its canonical writes were rolled back."""


class TransactionScopeError(TransactionFailure):
    """A transaction target is unsafe or outside its declared capability."""


class TransactionIdempotencyConflict(TransactionFailure):
    """An idempotency key was reused for a different approved intent."""


@dataclass(frozen=True)
class TransactionResult:
    transaction_id: str
    receipt_path: Path
    revisions: dict[str, int]
    snapshot_before: str
    snapshot_after: str
    replayed: bool = False


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


def _revision_ledger_path(root: Path) -> Path:
    return root / "operations" / "transactions" / "revisions.yaml"


def _idempotency_ledger_path(root: Path) -> Path:
    return root / "operations" / "transactions" / "idempotency.yaml"


def load_revisions(root: Path) -> dict[str, int]:
    path = _revision_ledger_path(root)
    if not path.exists() and not path.is_symlink():
        return {}
    try:
        from .loading.yamlio import UniqueKeySafeLoader

        data = yaml.load(
            read_text_inside(root, path),
            Loader=UniqueKeySafeLoader,
        )
    except (OSError, PathBoundaryError, yaml.YAMLError) as exc:
        raise TransactionFailure(
            f"artifact revision ledger is unreadable: {path}: {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise TransactionFailure("artifact revision ledger must be a mapping")
    if data.get("schema_version") != 1 \
            or data.get("type") != "artifact-revision-ledger":
        raise TransactionFailure(
            "artifact revision ledger has an unsupported contract"
        )
    rows = data.get("revisions")
    if not isinstance(rows, dict):
        raise TransactionFailure("artifact revision ledger revisions must be a mapping")
    revisions: dict[str, int] = {}
    for artifact, value in rows.items():
        if not isinstance(artifact, str) or not artifact.strip() \
                or isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise TransactionFailure(
                f"artifact revision ledger contains an invalid row: {artifact!r}"
            )
        revisions[artifact] = value
    return revisions


def artifact_revision(root: Path, artifact_id: str) -> int:
    return load_revisions(root).get(artifact_id, 0)


def _dump_revisions(revisions: Mapping[str, int]) -> str:
    return yaml.safe_dump(
        {
            "schema_version": 1,
            "type": "artifact-revision-ledger",
            "revisions": dict(sorted(revisions.items())),
        },
        sort_keys=False,
        allow_unicode=True,
    )


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


def replay_for_request(root: Path, request: GatewayRequestContext) -> TransactionResult | None:
    """Return the original committed receipt for an exact approved retry."""
    row = _load_idempotency_entries(root).get(request.idempotency_key)
    if row is None:
        return None
    if row["intent_sha256"] != request.intent_sha256 \
            or row["capability"] != request.capability:
        raise TransactionIdempotencyConflict(
            "idempotency key was already used for a different approved intent"
        )
    receipt_relative = str(row["receipt_path"])
    try:
        receipt_path, normalized = write_target(root, root / receipt_relative)
    except WriteScopeError as exc:
        raise TransactionFailure(f"idempotency ledger names an unsafe receipt: {exc}") from exc
    if normalized != receipt_relative or not receipt_path.is_file():
        raise TransactionFailure(
            "idempotency ledger names a missing or non-canonical receipt"
        )
    try:
        receipt = yaml.safe_load(read_text_inside(root, receipt_path))
    except (OSError, PathBoundaryError, yaml.YAMLError) as exc:
        raise TransactionFailure(f"idempotent receipt is unreadable: {exc}") from exc
    receipt_request = receipt.get("request") if isinstance(receipt, dict) else None
    if not isinstance(receipt, dict) or receipt.get("schema_version") != 2 \
            or not isinstance(receipt_request, dict) \
            or receipt_request.get("idempotency_key") != request.idempotency_key \
            or receipt_request.get("intent_sha256") != request.intent_sha256:
        raise TransactionFailure("idempotent receipt does not match its ledger entry")
    return TransactionResult(
        transaction_id=str(row["transaction_id"]),
        receipt_path=receipt_path,
        revisions={str(key): int(value) for key, value in row["revisions"].items()},
        snapshot_before=str(row["snapshot_before"]),
        snapshot_after=str(row["snapshot_after"]),
        replayed=True,
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
        publish: Callable[[], None] | None = None,
        rollback_publish: Callable[[], None] | None = None,
        touched: Callable[[Iterable[Path]], None] | None = None,
        metadata: Mapping | None = None,
        fingerprint: Callable[[], str] | None = None,
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
            replay = replay_for_request(self.root, request)
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
        if conflicts:
            raise TransactionConflict(conflicts)

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

        ledger_path, _ledger_relative = target(_revision_ledger_path(self.root))
        normalized_writes[ledger_path] = _dump_revisions(revisions_after).encode("utf-8")

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
            return sorted(set(failures))

        try:
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
            if publish is not None:
                publish()

            snapshot_after = take_fingerprint()
            snapshot_before_id = f"sha256:{snapshot_before}"
            snapshot_after_id = f"sha256:{snapshot_after}"
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
