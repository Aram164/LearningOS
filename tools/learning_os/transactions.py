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
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

import yaml

# One digest, one root list, shared with the projection (see fingerprint.py).
# Re-exported here because the receipt fields and every existing caller name it
# through this module.
from .fingerprint import canonical_fingerprint

__all__ = [
    "TransactionConflict",
    "TransactionFailure",
    "TransactionResult",
    "TransactionService",
    "artifact_revision",
    "canonical_fingerprint",
    "load_revisions",
    "parse_expected_revisions",
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


@dataclass(frozen=True)
class TransactionResult:
    transaction_id: str
    receipt_path: Path
    revisions: dict[str, int]
    snapshot_before: str
    snapshot_after: str


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


def load_revisions(root: Path) -> dict[str, int]:
    path = _revision_ledger_path(root)
    if not path.is_file():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    rows = data.get("revisions", {}) if isinstance(data, dict) else {}
    if not isinstance(rows, dict):
        return {}
    revisions: dict[str, int] = {}
    for artifact, value in rows.items():
        if isinstance(artifact, str) and isinstance(value, int) and value >= 0:
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


def _safe_relative(root: Path, path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise TransactionFailure(f"transaction path escapes repository: {path}") from exc


def _atomic_write_bytes(path: Path, content: bytes) -> None:
    # Preserve the gateway's established atomic sibling name. Existing
    # red-team checks deliberately block this path to verify rollback.
    tmp = path.with_name(f".{path.name}.tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_bytes(content)
        os.replace(tmp, path)
    except OSError as exc:
        with contextlib.suppress(OSError):
            tmp.unlink(missing_ok=True)
        raise TransactionFailure(
            f"cannot write {path}: {exc.strerror or exc}"
        ) from exc


def _next_transaction_identity(root: Path, now: dt.datetime) -> tuple[str, Path]:
    directory = root / "operations" / "transactions"
    directory.mkdir(parents=True, exist_ok=True)
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

    def __init__(self, root: Path):
        self.root = root.resolve()

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
        touched: Callable[[Iterable[Path]], None] | None = None,
        metadata: Mapping | None = None,
        fingerprint: Callable[[], str] | None = None,
    ) -> TransactionResult:
        if not capability or not capability.strip():
            raise TransactionFailure("transaction capability must be named")
        delete_paths = [Path(path).resolve() for path in deletes]
        if not writes and not delete_paths:
            raise TransactionFailure("transaction contains no writes")

        normalized_writes: dict[Path, bytes] = {}
        for raw_path, value in writes.items():
            path = Path(raw_path).resolve()
            _safe_relative(self.root, path)
            normalized_writes[path] = value.encode("utf-8") if isinstance(value, str) else bytes(value)

        for path in delete_paths:
            _safe_relative(self.root, path)
            if path in normalized_writes:
                raise TransactionFailure(f"transaction both writes and deletes {path}")

        artifacts = sorted({str(value).strip() for value in artifact_ids if str(value).strip()})
        if not artifacts:
            artifacts = [
                f"file:{_safe_relative(self.root, path)}"
                for path in [*normalized_writes, *delete_paths]
            ]

        revisions_before = load_revisions(self.root)
        expected = dict(expected_revisions or {})
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

        ledger_path = _revision_ledger_path(self.root).resolve()
        normalized_writes[ledger_path] = _dump_revisions(revisions_after).encode("utf-8")

        all_paths = [*normalized_writes, *delete_paths]
        backups: dict[Path, bytes | None] = {
            path: path.read_bytes() if path.is_file() else None for path in all_paths
        }
        # A transaction rooted somewhere without the canonical roots (the Job
        # surface, ADR-010) would digest nothing and record a constant snapshot,
        # which is worse than none: it looks like a guard. Such callers supply
        # their own digest over the artifacts they actually touch.
        take_fingerprint = fingerprint or (lambda: canonical_fingerprint(self.root))
        snapshot_before = take_fingerprint()
        receipt_path: Path | None = None

        def rollback() -> None:
            if receipt_path is not None:
                with contextlib.suppress(OSError):
                    receipt_path.unlink(missing_ok=True)
            for path, old in reversed(list(backups.items())):
                try:
                    if old is None:
                        if path.is_file():
                            path.unlink()
                    else:
                        _atomic_write_bytes(path, old)
                except Exception:
                    # Preserve the original failure; callers still receive a
                    # TransactionFailure and can inspect the named path.
                    pass
            if publish is not None:
                with contextlib.suppress(Exception):
                    publish()

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
            now = dt.datetime.now().astimezone().replace(microsecond=0)
            transaction_id, receipt_path = _next_transaction_identity(self.root, now)
            rows = []
            for path, after in normalized_writes.items():
                if path == ledger_path:
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
                "schema_version": 1,
                "id": transaction_id,
                "type": "transaction-receipt",
                "status": "committed",
                "capability": capability,
                "committed_at": now.isoformat(),
                "snapshot_before": f"sha256:{snapshot_before}",
                "snapshot_after": f"sha256:{snapshot_after}",
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
            if receipt_path.exists():
                raise TransactionFailure(f"receipt path already exists: {receipt_path}")
            _atomic_write_bytes(receipt_path, _receipt_text(receipt).encode("utf-8"))
            # Bookkeeping is part of the commit boundary. If it fails, remove
            # the newly-created receipt together with the canonical writes so
            # transaction history can never claim a rolled-back change.
            backups[receipt_path.resolve()] = None
            if touched is not None:
                touched([*normalized_writes, *delete_paths, receipt_path])
            return TransactionResult(
                transaction_id=transaction_id,
                receipt_path=receipt_path,
                revisions=changed_revisions,
                snapshot_before=f"sha256:{snapshot_before}",
                snapshot_after=f"sha256:{snapshot_after}",
            )
        except TransactionConflict:
            rollback()
            raise
        except Exception as exc:
            rollback()
            if isinstance(exc, TransactionFailure):
                raise
            raise TransactionFailure(str(exc)) from exc
