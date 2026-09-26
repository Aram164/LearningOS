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
import stat
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

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
from .diagnostics import conventions as diag_conventions
from .diagnostics import tracer as diag_tracer
from .diagnostics.store import bind_store as _bind_diag_store
from .errors import (
    PostCommitFailure,
    ProjectionFailure,
    ReplayEvidenceError,
    TransactionFailure,
    TransactionIdempotencyConflict,
    TransactionRecoveryConflict,
)
from .evidence import (
    _default_authority_root,
    _idempotency_ledger_path,
    _load_idempotency_entries,
    verify_committed_evidence,
)

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
    "TransactionRecoveryConflict",
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


class TransactionSnapshotConflict(TransactionFailure):
    """The approved projection no longer names the canonical state."""

    def __init__(self, expected: str, actual: str):
        self.expected = expected
        self.actual = actual
        super().__init__(
            "canonical snapshot conflict "
            f"(expected {expected}, actual {actual})"
        )


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


def replay_for_request(
    root: Path,
    request: GatewayRequestContext,
    *,
    authority_root: Path | None = None,
) -> TransactionResult | None:
    """Return the original committed receipt for an exact approved retry.

    Verification itself lives in :mod:`learning_os.evidence`, shared with
    the Diagnostics resolver so the Gateway and Operations can never
    disagree about what a receipt proves. ``None`` means only one thing:
    no ledger row exists for this idempotency key at all — every other
    outcome is either a validated replay or an exception. Nothing here
    invokes a capability handler.
    """
    verified = verify_committed_evidence(
        root, request, authority_root=authority_root)
    if verified is None:
        return None
    receipt, row, receipt_path = verified
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


def _discard_stale_projection(root: Path, problems: list[str]) -> None:
    """Drop a published projection that describes the state a rollback just undid.

    The projection is published through a callback the committing process owns,
    so a crash between publication and the receipt leaves `generated/` describing
    a transaction that no longer happened — canonical files restored, manifest
    still newer. Recovery runs in a later process and has no way to call that
    callback back.

    Deleting is the honest move rather than a gap: `generated/` is disposable by
    contract and rebuilt by `make views`, an absent manifest is an ordinary
    pre-projection state the hygiene rule already names, and a stale one is read
    by the UI as current. The digest decides — a projection that still matches
    canonical state is left exactly where it is.
    """
    manifest = root / "generated" / "manifest.json"
    if not manifest.is_file():
        return
    try:
        stored = json.loads(manifest.read_text(encoding="utf-8"))
        published = (stored.get("_generated") or {}).get("source_fingerprint")
        if published and published == canonical_fingerprint(root):
            return
        manifest.unlink()
    except (OSError, ValueError) as exc:
        problems.append(
            f"a rolled-back transaction left generated/manifest.json describing the "
            f"undone state, and it could not be discarded ({exc}); run `make views`")


def _invalidate_projection(root: Path) -> str | None:
    """Drop the projection marker unconditionally; return an error, or None.

    Used when canonical state is AMBIGUOUS — rollback incomplete, or a
    recovery conflict no run could unwind. A manifest matching the
    ambiguous bytes would be read downstream as current, so absence (the
    honest "projection unavailable" state; `generated/` is disposable and
    rebuilt by `make views`) is the only safe publication. A missing
    marker is already success.
    """
    manifest = root / "generated" / "manifest.json"
    try:
        manifest.unlink(missing_ok=True)
    except OSError as exc:
        return str(exc)
    return None


def _update_intent_after(inflight_dir: Path, relative: str,
                         content: bytes) -> None:
    """Complete one journal entry's intended post-state, durably.

    The idempotency ledger's after-image is computed after projection (it
    embeds snapshot_after), so its journal entry starts without `after`
    and is completed here, strictly before those bytes are written. The
    rewrite is atomic: a crash leaves either the previous intent (entry
    without `after`, treated as unprovable) or the completed one, never a
    torn journal.
    """
    intent_path = inflight_dir / "intent.json"
    try:
        intent = json.loads(intent_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise TransactionFailure(
            f"transaction cannot update its recovery journal: {exc}"
        ) from exc
    if not isinstance(intent, dict) or not isinstance(intent.get("paths"), list):
        raise TransactionFailure("transaction recovery journal is malformed")
    for entry in intent["paths"]:
        if isinstance(entry, dict) and entry.get("path") == relative:
            entry["after"] = {
                "kind": "file",
                "sha256": f"sha256:{hashlib.sha256(content).hexdigest()}",
            }
            break
    else:
        raise TransactionFailure(
            f"transaction recovery journal has no entry for {relative}"
        )
    _atomic_write_bytes(intent_path, json.dumps(intent).encode("utf-8"))


def _inspect_live_path(path: Path) -> tuple[str, str | None]:
    """Hostile-safe state of one filesystem path. Never follows symlinks.

    Returns ``("absent", None)``, ``("file", hex-digest)``, or
    ``("other", detail)``. Anything unstatable or unreadable is "other":
    recovery fails closed rather than guessing about state it cannot read.
    """
    try:
        st = path.lstat()
    except FileNotFoundError:
        return ("absent", None)
    except OSError:
        return ("other", "unstatable")
    if stat.S_ISLNK(st.st_mode):
        return ("other", "symlink")
    if stat.S_ISDIR(st.st_mode):
        return ("other", "directory")
    if not stat.S_ISREG(st.st_mode):
        return ("other", "special")
    try:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ("other", "unreadable")
    return ("file", digest)


def _resolve_journaled(root: Path, relative: object) -> Path | None:
    """The live path a journal entry names, or None when corrupt.

    Lexical validation plus a containment check. A terminal symlink is NOT
    resolved here — inspection classifies it as unexpected without ever
    following it.
    """
    if not isinstance(relative, str) or not relative.strip() \
            or os.path.isabs(relative):
        return None
    candidate = root / relative
    try:
        if candidate.is_symlink():
            return candidate
        resolved = candidate.resolve()
    except OSError:
        return None
    root_resolved = root.resolve()
    if resolved != root_resolved and root_resolved not in resolved.parents:
        return None
    return candidate


def _strip_journal_digest(value: object) -> str | None:
    if isinstance(value, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", value):
        return value[len("sha256:"):]
    return None


_JOURNAL_BACKUP_ID = re.compile(r"[A-Za-z0-9_.-]+")


def _valid_journal_side(side: object, *, need_backup: bool) -> bool:
    if not isinstance(side, dict):
        return False
    kind = side.get("kind")
    if kind == "absent":
        return True
    if kind != "file":
        return False
    if _strip_journal_digest(side.get("sha256")) is None:
        return False
    if not need_backup:
        return True
    backup_id = side.get("backup_id")
    return isinstance(backup_id, str) \
        and _JOURNAL_BACKUP_ID.fullmatch(backup_id) is not None \
        and backup_id not in (".", "..")


def _matches_journal_side(kind: str, digest: str | None, side: dict) -> bool:
    if side.get("kind") == "absent":
        return kind == "absent"
    return kind == "file" and digest == _strip_journal_digest(side.get("sha256"))


def _inspect_commit_receipt(root: Path, intent: Mapping) -> tuple[str, str]:
    """VALID_COMMIT, ABSENT, or CONTRADICTORY for the journal's receipt.

    A file merely existing proves nothing: the receipt must parse,
    validate against the receipt schema, name this journal's transaction,
    and read committed — reached through a canonical, non-symlink path.
    Returns the verdict plus a short structural note.
    """
    relative = intent.get("receipt_path")
    if not isinstance(relative, str) or not relative.strip():
        return ("CONTRADICTORY", "the journal names no receipt")
    if os.path.isabs(relative):
        return ("CONTRADICTORY", "the journal names an absolute receipt path")
    candidate = root / relative
    try:
        if candidate.is_symlink():
            return ("CONTRADICTORY", "the receipt path is a symlink")
    except OSError:
        return ("CONTRADICTORY", "the receipt path cannot be inspected")
    try:
        resolved = candidate.resolve()
    except OSError:
        return ("CONTRADICTORY", "the receipt path cannot be resolved")
    root_resolved = root.resolve()
    if resolved != root_resolved and root_resolved not in resolved.parents:
        return ("CONTRADICTORY", "the receipt path escapes the repository")
    if not candidate.exists():
        return ("ABSENT", "")
    try:
        from .loading.yamlio import UniqueKeySafeLoader

        data = yaml.load(
            read_text_inside(root, candidate), Loader=UniqueKeySafeLoader)
    except (OSError, PathBoundaryError, yaml.YAMLError):
        return ("CONTRADICTORY", "the receipt is unreadable")
    if not isinstance(data, dict):
        return ("CONTRADICTORY", "the receipt is not a mapping")
    schema_root = _default_authority_root(root) or root
    schema_path = schema_root / "system" / "schema" / "transaction-receipt.schema.json"
    if not schema_path.is_file():
        return ("CONTRADICTORY", "no receipt schema can verify the receipt")
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        invalid = list(Draft202012Validator(schema).iter_errors(data))
    except (OSError, ValueError):
        return ("CONTRADICTORY", "the receipt schema cannot be read")
    if invalid:
        return ("CONTRADICTORY", "the receipt fails schema validation")
    if data.get("id") != intent.get("transaction_id"):
        return ("CONTRADICTORY", "the receipt names a different transaction")
    if data.get("status") != "committed":
        return ("CONTRADICTORY", "the receipt is not committed")
    return ("VALID_COMMIT", "")


def _conflict_message(transaction_id: str, journal_rel: str, summary: str,
                      conflicts: list[dict]) -> str:
    shown = "; ".join(
        f"{entry['path']} ({entry['reason']})" for entry in conflicts[:5]
    )
    more = f"; and {len(conflicts) - 5} more" if len(conflicts) > 5 else ""
    return (
        f"a previous run of transaction {transaction_id} was interrupted "
        f"mid-write and {summary}: {shown}{more}. No conflicting path was "
        f"modified and the recovery journal was preserved under {journal_rel} "
        f"for diagnosis — reconcile the paths by hand, remove the stale "
        f"journal directory once every path is deliberately placed, and re-run"
    )


def _remove_journal(tx_dir: Path, transaction_id: str, journal_rel: str) -> None:
    try:
        shutil.rmtree(tx_dir)
    except OSError as exc:
        raise TransactionRecoveryConflict(
            f"transaction {transaction_id} was reconciled but its recovery "
            f"journal at {journal_rel} could not be removed ({exc}); no "
            f"canonical path is affected and the next run retries the cleanup",
            transaction_id=transaction_id,
            conflicts=[{"path": journal_rel, "reason": "RESTORE_IO_FAILED",
                        "detail": "journal cleanup failed"}],
        ) from exc


def _refuse_journal(root: Path, tx_dir: Path, detail: str,
                    path: str | None = None,
                    reason: str = "CORRUPT_JOURNAL",
                    summary: str = "its journal is not self-bound") -> NoReturn:
    """Raise for a journal that fails admission, reading, or versioning.

    The directory name grounds every field: a journal that disagrees with
    its own location proves nothing, so recovery preserves the directory
    untouched and stops.
    """
    journal_rel = _safe_relative(root, tx_dir)
    conflict = {"path": path or journal_rel, "reason": reason,
                "detail": detail}
    raise TransactionRecoveryConflict(
        _conflict_message(tx_dir.name, journal_rel, summary, [conflict]),
        transaction_id=tx_dir.name, conflicts=[conflict])


def _admit_v2_journal(root: Path, tx_dir: Path, intent: dict) -> str:
    """Prove a version-2 journal is self-bound before anything is inspected.

    Admission is lexical and structural: the journal must name its own
    directory, its own canonical receipt path, and a normalized, unique,
    in-root path set reachable without crossing a symlink. Backup ids
    must be normalized, unique, and plain files. Anything else is
    CORRUPT_JOURNAL with everything preserved — raised before receipt
    inspection, before preflight, and therefore before any restore.

    One deliberate terminal exemption: a symlink (or any other unexpected
    node) AT the journaled path itself is live state that may have
    appeared after journaling, so it stays preflight's verdict
    (UNEXPECTED_FILE_TYPE) like any other post-journal divergence.
    Intermediate components get no such exemption: with an indirection
    in the middle, inspection itself cannot be trusted.
    """
    transaction_id = tx_dir.name
    if intent.get("transaction_id") != transaction_id:
        _refuse_journal(
            root, tx_dir,
            "the journal names a different transaction than its directory")
    if intent.get("receipt_path") \
            != f"operations/transactions/{transaction_id}.yaml":
        _refuse_journal(
            root, tx_dir,
            "the journal names a receipt outside its canonical path")
    entries = intent.get("paths")
    if not isinstance(entries, list) or not entries:
        _refuse_journal(root, tx_dir, "journal lists no paths")
    resolved_root = root.resolve()
    seen_paths: set[str] = set()
    seen_backups: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            _refuse_journal(root, tx_dir, "journal entry names an unsafe path")
        relative = entry.get("path")
        if not isinstance(relative, str):
            _refuse_journal(root, tx_dir, "journal entry names an unsafe path",
                            path=str(relative))
        rel = relative
        # The same lexical grammar write_target() enforces for live
        # transactions: normalized posix, relative, no dot segments.
        candidate = Path(rel)
        if "\x00" in rel or "\\" in rel or candidate.as_posix() != rel \
                or candidate.is_absolute() \
                or any(part in {".", ".."} for part in candidate.parts):
            _refuse_journal(root, tx_dir,
                            f"journal path is not normalized: {rel}", path=rel)
        if rel in seen_paths:
            _refuse_journal(root, tx_dir, f"journal lists {rel} twice",
                            path=rel)
        seen_paths.add(rel)
        cursor = resolved_root
        for part in candidate.parts[:-1]:
            cursor = cursor / part
            if cursor.is_symlink():
                _refuse_journal(
                    root, tx_dir, f"journal path traverses symlink: {rel}",
                    path=rel)
        try:
            (resolved_root / rel).resolve(
                strict=False).relative_to(resolved_root)
        except (OSError, ValueError):
            _refuse_journal(root, tx_dir,
                            f"journal path escapes the repository: {rel}",
                            path=rel)
        before = entry.get("before")
        if isinstance(before, dict) and before.get("kind") == "file":
            backup_id = before.get("backup_id")
            if not isinstance(backup_id, str) \
                    or _JOURNAL_BACKUP_ID.fullmatch(backup_id) is None \
                    or backup_id in (".", ".."):
                _refuse_journal(
                    root, tx_dir,
                    f"journal backup id is malformed: {backup_id!r}", path=rel)
            if backup_id in seen_backups:
                _refuse_journal(root, tx_dir,
                                f"journal reuses backup {backup_id}", path=rel)
            seen_backups.add(backup_id)
            if (tx_dir / backup_id).is_symlink():
                _refuse_journal(root, tx_dir,
                                f"backup {backup_id} is a symlink", path=rel)
    return transaction_id


def _preflight_v2_entry(root: Path, tx_dir: Path, entry: object
                        ) -> tuple[dict | None, dict | None]:
    """Classify one version-2 journal entry without touching anything.

    Returns (action, None) where action restores or no-ops the path, or
    (None, conflict) describing why the path is unprovable.
    """
    relative = entry.get("path") if isinstance(entry, dict) else None
    path = _resolve_journaled(root, relative)
    if path is None or not isinstance(entry, dict):
        return None, {"path": str(relative), "reason": "CORRUPT_JOURNAL",
                      "detail": "journal entry names an unsafe path"}
    rel = str(relative)
    before = entry.get("before")
    after = entry.get("after")
    if not _valid_journal_side(before, need_backup=True) \
            or (after is not None
                and not _valid_journal_side(after, need_backup=False)):
        return None, {"path": rel, "reason": "CORRUPT_JOURNAL",
                      "detail": "journal entry is malformed"}
    if before["kind"] == "file":
        backup_id = before["backup_id"]
        backup_path = tx_dir / backup_id
        try:
            inside = tx_dir.resolve() in backup_path.resolve().parents
        except OSError:
            inside = False
        if not inside:
            return None, {"path": rel, "reason": "CORRUPT_JOURNAL",
                          "detail": f"backup {backup_id} escapes the journal"}
        try:
            backup_bytes = backup_path.read_bytes()
        except OSError:
            return None, {"path": rel, "reason": "BACKUP_HASH_MISMATCH",
                          "detail": f"backup {backup_id} is missing"}
        if hashlib.sha256(backup_bytes).hexdigest() \
                != _strip_journal_digest(before["sha256"]):
            return None, {"path": rel, "reason": "BACKUP_HASH_MISMATCH",
                          "detail": f"backup {backup_id} disagrees with the journal"}
    kind, observed = _inspect_live_path(path)
    if _matches_journal_side(kind, observed, before):
        return {"path": path, "before": before, "after": after,
                "restore": False}, None
    if after is not None and _matches_journal_side(kind, observed, after):
        return {"path": path, "before": before, "after": after,
                "restore": True}, None
    if kind == "other":
        return None, {"path": rel, "reason": "UNEXPECTED_FILE_TYPE",
                      "detail": f"live path is {observed}"}
    current = "absent" if kind == "absent" else f"file@{observed[:12]}"
    return None, {"path": rel, "reason": "DIVERGED_FROM_TRANSACTION",
                  "detail": f"live {current} matches neither recorded side"}


def _unwind_v2_entries(root: Path, tx_dir: Path, entries: list,
                       transaction_id: str, journal_rel: str) -> None:
    """Run one admitted journal's compare-and-undo plan (passes 1-3).

    The one unwind engine: crash recovery and live rollback both execute
    exactly this against the published journal. Either every path is
    proven back at pre-state or TransactionRecoveryConflict is raised
    with the journal preserved for the next attempt — a mid-restore
    crash or IO failure completes idempotently because restored paths
    read as pre-state. Journal removal and projection handling belong to
    the caller, which knows whether its commit boundary was reached.
    """
    # PASS 1 — read-only preflight over every path. One conflict anywhere
    # stops the whole unwind before a single byte changes.
    plan = []
    conflicts = []
    for entry in entries:
        action, conflict = _preflight_v2_entry(root, tx_dir, entry)
        if conflict is not None:
            conflicts.append(conflict)
        else:
            plan.append(action)
    if conflicts:
        raise TransactionRecoveryConflict(
            _conflict_message(
                transaction_id, journal_rel,
                f"{len(conflicts)} of {len(entries)} paths cannot be proven "
                f"transaction-owned", conflicts),
            transaction_id=transaction_id, conflicts=conflicts)
    # PASS 2 — restore proven-owned paths, rechecking each first so a
    # mutation between preflight and restore fails closed instead of
    # clobbering it. Cooperative LearningOS writers hold the operator
    # lock across recovery, so this recheck only ever fires on
    # non-cooperative filesystem mutation mid-run.
    restores = [action for action in plan if action["restore"]]
    for action in restores:
        path, before, after = action["path"], action["before"], action["after"]
        kind, observed = _inspect_live_path(path)
        if after is None or not _matches_journal_side(kind, observed, after):
            conflict = {"path": _safe_relative(root, path),
                        "reason": "DIVERGED_FROM_TRANSACTION",
                        "detail": "path changed during recovery"}
            raise TransactionRecoveryConflict(
                _conflict_message(transaction_id, journal_rel,
                                  "a path changed during recovery", [conflict]),
                transaction_id=transaction_id, conflicts=[conflict])
        try:
            if before["kind"] == "absent":
                path.unlink()
            else:
                blob = (tx_dir / before["backup_id"]).read_bytes()
                if hashlib.sha256(blob).hexdigest() \
                        != _strip_journal_digest(before["sha256"]):
                    conflict = {"path": _safe_relative(root, path),
                                "reason": "BACKUP_HASH_MISMATCH",
                                "detail": "backup changed during recovery"}
                    raise TransactionRecoveryConflict(
                        _conflict_message(transaction_id, journal_rel,
                                          "a backup changed during recovery",
                                          [conflict]),
                        transaction_id=transaction_id, conflicts=[conflict])
                _atomic_write_bytes(path, blob)
        except TransactionRecoveryConflict:
            raise
        except Exception as exc:
            conflict = {"path": _safe_relative(root, path),
                        "reason": "RESTORE_IO_FAILED",
                        "detail": f"restore could not be written: {exc}"}
            raise TransactionRecoveryConflict(
                _conflict_message(transaction_id, journal_rel,
                                  "a proven-safe restore could not be written",
                                  [conflict]),
                transaction_id=transaction_id, conflicts=[conflict]) from exc
    # PASS 3 — prove the footprint is fully pre-state before the caller
    # drops the evidence that describes it.
    drifted = []
    for action in plan:
        kind, observed = _inspect_live_path(action["path"])
        if not _matches_journal_side(kind, observed, action["before"]):
            drifted.append({"path": _safe_relative(root, action["path"]),
                            "reason": "DIVERGED_FROM_TRANSACTION",
                            "detail": "path changed during recovery"})
    if drifted:
        raise TransactionRecoveryConflict(
            _conflict_message(transaction_id, journal_rel,
                              "a path changed during recovery", drifted),
            transaction_id=transaction_id, conflicts=drifted)


def _reconcile_v2_journal(root: Path, tx_dir: Path, intent: dict) -> None:
    """Compare-and-undo recovery for one schema-2 journal.

    Either fully unwinds the crashed transaction (every path proven back
    at its pre-state, journal removed) or raises
    TransactionRecoveryConflict having changed nothing — except a
    mid-restore crash or IO failure, which the next run completes
    idempotently because restored paths read as pre-state.
    """
    transaction_id = _admit_v2_journal(root, tx_dir, intent)
    journal_rel = _safe_relative(root, tx_dir)
    verdict, detail = _inspect_commit_receipt(root, intent)
    raw_receipt = intent.get("receipt_path")
    receipt_ref = raw_receipt if isinstance(raw_receipt, str) and raw_receipt \
        else journal_rel
    if verdict == "VALID_COMMIT":
        _remove_journal(tx_dir, transaction_id, journal_rel)
        return
    if verdict == "CONTRADICTORY":
        conflicts = [{"path": receipt_ref, "reason": "INVALID_COMMIT_RECEIPT",
                      "detail": detail or "receipt contradicts the journal"}]
        raise TransactionRecoveryConflict(
            _conflict_message(transaction_id, journal_rel,
                              "its commit receipt is contradictory", conflicts),
            transaction_id=transaction_id, conflicts=conflicts)
    _unwind_v2_entries(root, tx_dir, intent["paths"], transaction_id,
                       journal_rel)
    problems: list[str] = []
    _discard_stale_projection(root, problems)
    if problems:
        raise TransactionRecoveryConflict(
            f"transaction {transaction_id} was unwound but its stale "
            f"projection could not be discarded ({problems[0][:160]}); no "
            f"canonical path is affected, the journal was preserved under "
            f"{journal_rel}, and the next run retries the cleanup",
            transaction_id=transaction_id,
            conflicts=[{"path": "generated/manifest.json",
                        "reason": "RESTORE_IO_FAILED",
                        "detail": "stale projection could not be discarded"}])
    _remove_journal(tx_dir, transaction_id, journal_rel)


def _reconcile_v1_journal(root: Path, tx_dir: Path, intent: dict) -> None:
    """Fail-closed handling for a version-1 (undo-only) journal.

    Version 1 records pre-state but no post-state, so a diverged path
    cannot distinguish crashed bytes from foreign bytes. Clean only what
    is provably already rolled back; anything else conflicts with the
    journal preserved. A `created` file that exists is NEVER unlinked:
    nobody can prove who owns those bytes.
    """
    if intent.get("transaction_id") != tx_dir.name:
        _refuse_journal(
            root, tx_dir,
            "the journal names a different transaction than its directory")
    transaction_id = tx_dir.name
    journal_rel = _safe_relative(root, tx_dir)
    verdict, detail = _inspect_commit_receipt(root, intent)
    raw_receipt = intent.get("receipt_path")
    receipt_ref = raw_receipt if isinstance(raw_receipt, str) and raw_receipt \
        else journal_rel
    if verdict == "VALID_COMMIT":
        _remove_journal(tx_dir, transaction_id, journal_rel)
        return
    if verdict == "CONTRADICTORY":
        conflicts = [{"path": receipt_ref, "reason": "INVALID_COMMIT_RECEIPT",
                      "detail": detail or "receipt contradicts the journal"}]
        raise TransactionRecoveryConflict(
            _conflict_message(transaction_id, journal_rel,
                              "its commit receipt is contradictory", conflicts),
            transaction_id=transaction_id, conflicts=conflicts)
    rows = intent.get("backups")
    if not isinstance(rows, list):
        conflicts = [{"path": journal_rel, "reason": "CORRUPT_JOURNAL",
                      "detail": "journal lists no backups"}]
        raise TransactionRecoveryConflict(
            _conflict_message(transaction_id, journal_rel,
                              "its journal lists no backups", conflicts),
            transaction_id=transaction_id, conflicts=conflicts)
    unprovable = []
    for row in rows:
        relative = row.get("path") if isinstance(row, dict) else None
        path = _resolve_journaled(root, relative)
        if path is None or not isinstance(row, dict):
            unprovable.append(
                {"path": str(relative), "reason": "CORRUPT_JOURNAL",
                 "detail": "journal entry names an unsafe path"})
            continue
        rel = str(relative)
        created = row.get("created") is True
        backup_id = row.get("backup_id")
        has_backup = isinstance(backup_id, str) and backup_id != ""
        if created == has_backup:
            unprovable.append(
                {"path": rel, "reason": "CORRUPT_JOURNAL",
                 "detail": "journal entry is malformed"})
            continue
        if created:
            kind, _observed = _inspect_live_path(path)
            if kind != "absent":
                unprovable.append(
                    {"path": rel, "reason": "LEGACY_JOURNAL_UNPROVABLE",
                     "detail": "a version-1 journal cannot prove who owns "
                              "these bytes; never deleted"})
            continue
        backup_path = tx_dir / backup_id
        try:
            inside = tx_dir.resolve() in backup_path.resolve().parents
        except OSError:
            inside = False
        if not inside:
            unprovable.append(
                {"path": rel, "reason": "CORRUPT_JOURNAL",
                 "detail": f"backup {backup_id} escapes the journal"})
            continue
        try:
            blob = backup_path.read_bytes()
        except OSError:
            unprovable.append(
                {"path": rel, "reason": "LEGACY_JOURNAL_UNPROVABLE",
                 "detail": f"backup {backup_id} is missing"})
            continue
        kind, observed = _inspect_live_path(path)
        if kind != "file" or observed != hashlib.sha256(blob).hexdigest():
            unprovable.append(
                {"path": rel, "reason": "LEGACY_JOURNAL_UNPROVABLE",
                 "detail": "live bytes differ from the recorded pre-state"})
    if unprovable:
        raise TransactionRecoveryConflict(
            _conflict_message(
                transaction_id, journal_rel,
                f"its version-1 journal cannot prove {len(unprovable)} of "
                f"{len(rows)} paths already rolled back", unprovable),
            transaction_id=transaction_id, conflicts=unprovable)
    problems: list[str] = []
    _discard_stale_projection(root, problems)
    if problems:
        raise TransactionRecoveryConflict(
            f"transaction {transaction_id} was reconciled but its stale "
            f"projection could not be discarded ({problems[0][:160]}); no "
            f"canonical path is affected, the journal was preserved under "
            f"{journal_rel}, and the next run retries the cleanup",
            transaction_id=transaction_id,
            conflicts=[{"path": "generated/manifest.json",
                        "reason": "RESTORE_IO_FAILED",
                        "detail": "stale projection could not be discarded"}])
    _remove_journal(tx_dir, transaction_id, journal_rel)


def reconcile_inflight_transactions(root: Path) -> None:
    """Unwind any transaction a dead process left half-applied, provably.

    Runs while the operator lock is held, before the command that acquired it
    does anything, so a crashed predecessor's partial write is undone before it
    can be read as canonical state.

    Compare-and-undo: recovery may modify a path only while it can prove the
    path is still either the crashed transaction's exact post-state (safe to
    undo) or its original pre-state (already undone, a no-op). A path
    matching neither is foreign state a later writer owns: recovery touches
    nothing, preserves the journal, and raises
    TransactionRecoveryConflict. When evidence is insufficient, preserve
    state and report ambiguity rather than guessing.

    CRASH RECOVERY BOUNDARY:
    The commit boundary is exactly a valid, matching, committed receipt at
    the journal's receipt path — a file merely existing there proves
    nothing. A valid receipt means the transaction committed: never roll
    back, just clean the stale journal. No receipt means compare-and-undo;
    a contradictory receipt means conflict with everything preserved.

    Journals unwind newest first, so stacked crashes resolve from the latest
    backwards instead of deadlocking. Recovery is restart-idempotent: paths
    restored by an interrupted run read as pre-state, so the next run
    finishes them as no-ops and continues. Version-1 journals (pre-state
    only, no post-state hashes) are handled conservatively: cleaned when
    provably already rolled back, conflicted otherwise, never blindly
    replayed.

    PUBLICATION BOUNDARY:
    The journal is staged whole under `.inflight/.preparing-<id>/` and
    published by one atomic rename before the first canonical mutation.
    Recovery therefore treats staging as never-armed debris (safe to
    drop without inspection) and a published directory as complete by
    construction: a published journal with a missing or unreadable
    intent is corruption after arming, preserved and reported, never
    silently cleaned.

    OWNERSHIP BOUNDARY (ABA):
    Hashes prove live state EQUALS recorded state, not that it never
    changed in between. A non-cooperative writer that alters a file and
    restores byte-identical content is undetectable, as is an
    independent re-deletion of a deleted file. The contract is:
    cooperative LearningOS writers are serialized by the operator lock;
    non-cooperative changes that leave different state are detected;
    byte-identical/ABA changes are state-equivalent and accepted as
    such. Stronger proof would need locks or version tokens, which this
    system deliberately does not add. Likewise, a hostile writer swapping
    a parent directory for a symlink between admission and restore is
    outside the model: cooperative writers hold the operator lock across
    recovery, and closing that TOCTOU would need no-follow directory
    operations the model does not require.
    """
    inflight_dir = root / "operations" / "transactions" / ".inflight"
    if not inflight_dir.is_dir():
        return
    tx_dirs = []
    for entry in sorted(inflight_dir.iterdir()):
        if entry.name.startswith(".preparing-"):
            # Never armed: publication is the atomic rename, so anything
            # still under a staging name died before the first canonical
            # mutation. Drop it without inspection; debris that cannot be
            # removed is simply retried next run, never treated as proof.
            with contextlib.suppress(OSError):
                if entry.is_symlink() or not entry.is_dir():
                    entry.unlink(missing_ok=True)
                else:
                    shutil.rmtree(entry, ignore_errors=True)
            continue
        if entry.is_dir() and not entry.is_symlink():
            tx_dirs.append(entry)
    # Newest first: stacked journals unwind from the latest crash backwards.
    # Transaction ids sort chronologically, so descending names unwinds the
    # stack instead of reading a newer transaction's bytes as foreign.
    for tx_dir in reversed(tx_dirs):
        try:
            _reconcile_one_journal(root, tx_dir)
        except TransactionRecoveryConflict as exc:
            # Recovery proved nothing about this tree, so no manifest may
            # keep vouching for it — drop the marker regardless of
            # fingerprint. If the marker itself cannot be dropped, say so
            # structurally: a surviving manifest over ambiguous bytes is
            # exactly what downstream must not trust.
            problem = _invalidate_projection(root)
            if problem is not None:
                exc.conflicts.append({
                    "path": "generated/manifest.json",
                    "reason": "RESTORE_IO_FAILED",
                    "detail": "projection marker could not be dropped: "
                              f"{problem}"})
            raise


def _reconcile_one_journal(root: Path, tx_dir: Path) -> None:
    """Dispatch one published journal to its schema's recovery."""
    intent_path = tx_dir / "intent.json"
    if intent_path.is_symlink() or not intent_path.is_file():
        # Published journals are complete by construction (staged
        # whole, then renamed), so a missing intent is corruption or
        # tampering after arming — never the harmless early crash the
        # old code assumed. Preserve the directory and stop.
        _refuse_journal(
            root, tx_dir, "published journal is missing intent.json")
    try:
        intent = json.loads(intent_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise TransactionRecoveryConflict(
            f"transaction {tx_dir.name} left a recovery journal that "
            f"cannot be read ({exc}); nothing was modified and the "
            f"journal was preserved under "
            f"{_safe_relative(root, tx_dir)} for diagnosis",
            transaction_id=tx_dir.name,
            conflicts=[{
                "path": _safe_relative(root, intent_path),
                "reason": "UNREADABLE_JOURNAL",
                "detail": "journal cannot be read"}],
        ) from exc
    if not isinstance(intent, dict):
        journal_rel = _safe_relative(root, tx_dir)
        conflicts = [{"path": journal_rel, "reason": "CORRUPT_JOURNAL",
                      "detail": "journal is not a mapping"}]
        raise TransactionRecoveryConflict(
            _conflict_message(tx_dir.name, journal_rel,
                              "its journal is not a mapping", conflicts),
            transaction_id=tx_dir.name, conflicts=conflicts)
    schema_version = intent.get("schema_version", 1)
    if schema_version == 2:
        _reconcile_v2_journal(root, tx_dir, intent)
    elif schema_version == 1:
        _reconcile_v1_journal(root, tx_dir, intent)
    else:
        _refuse_journal(
            root, tx_dir,
            f"unsupported journal schema version: {schema_version!r}",
            reason="UNSUPPORTED_JOURNAL_VERSION",
            summary="its journal uses an unsupported schema version")


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
        _bind_diag_store(self.root)
        diag_tracer.emit_event(
            diag_conventions.EVENT_TRANSACTION_STARTED,
            attrs={"capability": capability})
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
                diag_tracer.emit_event(
                    diag_conventions.EVENT_STAGE_FAILED,
                    stage="core.approval", status="error",
                    attrs={"error": "approval not bound to intent"})
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
            diag_tracer.emit_event(
                diag_conventions.EVENT_STAGE_FAILED,
                stage="core.snapshot_guard", status="error",
                attrs={"error": "snapshot changed since approval"})
            raise TransactionSnapshotConflict(
                approved_snapshot,
                snapshot_before_id,
            )
        # Snapshot staleness is the broader approved-state conflict and keeps
        # its historical precedence when the same concurrent write also moved
        # an artifact revision.
        if conflicts:
            diag_tracer.emit_event(
                diag_conventions.EVENT_STAGE_FAILED,
                stage="core.revision_guard", status="error",
                attrs={"error": "artifact revision moved",
                       "artifacts": sorted(conflicts)})
            raise TransactionConflict(conflicts)

        inflight_parent = self.root / "operations" / "transactions" / ".inflight"
        staging_dir = inflight_parent / f".preparing-{transaction_id}"
        inflight_dir = inflight_parent / transaction_id
        journal_published = False
        # Content (non-OSError) failures re-publishing over proven pre-state.
        # The defect pre-exists the write: canonical rollback completed, so
        # the journal is removed and the refusal reports the pre-existing
        # defect instead of an unknown outcome (JF-11).
        republication_defects: list[Exception] = []

        def rollback() -> list[str]:
            """Unwind through the published journal, never from memory alone.

            Live rollback and crash recovery execute the same
            compare-and-undo engine against the same on-disk journal, so a
            foreign write landing during validation or projection is
            preserved and reported instead of blindly overwritten. On
            ambiguity the journal stays for the next run and the caller
            gets the unrestored paths, never a false success.
            """
            failures: list[str] = []
            if os.path.lexists(receipt_path):
                # Commit was not reached, so this transaction never wrote
                # a receipt: anything here is foreign evidence. Report it;
                # never delete it.
                failures.append(_safe_relative(self.root, receipt_path))
            if not journal_published:
                # The journal never armed, so no canonical mutation could
                # have happened. Verify live state still equals the
                # pre-state snapshots and touch nothing — even here a
                # blind memory restore could clobber a foreign write that
                # landed while staging.
                for path, old in backups.items():
                    try:
                        live = path.read_bytes() if path.is_file() else None
                    except OSError:
                        live = "<unreadable>"
                    if live != old:
                        failures.append(_safe_relative(self.root, path))
                shutil.rmtree(staging_dir, ignore_errors=True)
            else:
                journal_rel = _safe_relative(self.root, inflight_dir)
                try:
                    disk_intent = json.loads(
                        (inflight_dir / "intent.json").read_text(
                            encoding="utf-8"))
                except (OSError, ValueError):
                    failures.append(journal_rel)
                    disk_intent = None
                if disk_intent is not None:
                    if not isinstance(disk_intent, dict):
                        failures.append(journal_rel)
                    else:
                        try:
                            _admit_v2_journal(self.root, inflight_dir,
                                              disk_intent)
                            _unwind_v2_entries(
                                self.root, inflight_dir, disk_intent["paths"],
                                transaction_id, journal_rel)
                        except TransactionRecoveryConflict as exc:
                            failures.extend(conflict["path"]
                                            for conflict in exc.conflicts)
            if not failures:
                # Canonical unwind is proven complete: re-publish the
                # projection from the restored pre-state as before.
                restore_projection = rollback_publish or publish
                if restore_projection is not None:
                    try:
                        restore_projection()
                    except OSError:
                        failures.append("<projection publication>")
                    except Exception as exc:
                        # Unwind only proves the write set was restored; a
                        # concurrent foreign change elsewhere in the tree
                        # (which the snapshot guard, not unwind, detects)
                        # may be what breaks re-publication. Only a tree
                        # that still equals the transaction's pre-state
                        # proves the defect pre-exists this write — and
                        # only then is this not a rollback failure (JF-11).
                        try:
                            prestate_intact = (
                                take_fingerprint() == snapshot_before)
                        except Exception:
                            prestate_intact = False
                        if prestate_intact:
                            republication_defects.append(exc)
                        else:
                            failures.append("<projection publication>")
            if failures or republication_defects:
                # Canonical state is ambiguous — unwind proved nothing, or
                # re-publication just failed over a proven tree — or the
                # pre-state itself does not publish. Either way a manifest
                # now would present uncertainty as current, so drop the
                # marker instead: "projection unavailable" is the
                # truthful state.
                problem = _invalidate_projection(self.root)
                if problem is not None:
                    failures.append("generated/manifest.json")
            if not failures:
                if journal_published:
                    try:
                        _remove_journal(inflight_dir, transaction_id,
                                        journal_rel)
                    except TransactionRecoveryConflict as exc:
                        failures.extend(conflict["path"]
                                        for conflict in exc.conflicts)
                else:
                    shutil.rmtree(staging_dir, ignore_errors=True)
            return sorted(set(failures))

        try:
            commit_reached = False
            failed_stage = "core.commit"
            if os.path.lexists(inflight_dir):
                raise TransactionFailure(
                    f"transaction {transaction_id} cannot start: a recovery "
                    f"journal with this identity already exists under "
                    f"{_safe_relative(self.root, inflight_dir)}; reconcile it "
                    f"before committing")
            # Compare-and-undo journal (schema v2): for every mutated path,
            # the pre-state (with its backup blob) AND the intended
            # post-state hash. Recovery restores a path only while the live
            # file still equals one of the two recorded sides; anything
            # else is foreign state a later writer owns and must never be
            # touched. The journal is staged whole under a `.preparing-`
            # name and published by one atomic rename, fsynced with its
            # parent, before the first canonical mutation below — so
            # recovery can tell never-armed staging from a published
            # journal that must be complete.
            shutil.rmtree(staging_dir, ignore_errors=True)
            staging_dir.mkdir(parents=True)
            delete_set = set(delete_paths)
            intent: dict = {
                "schema_version": 2,
                "transaction_id": transaction_id,
                "receipt_path": _safe_relative(self.root, receipt_path),
                "paths": [],
            }
            for i, (path, old) in enumerate(backups.items()):
                if old is None:
                    before: dict = {"kind": "absent"}
                else:
                    backup_id = f"backup-{i}"
                    _atomic_write_bytes(staging_dir / backup_id, old)
                    before = {
                        "kind": "file",
                        "sha256": f"sha256:{_sha256_bytes(old)}",
                        "backup_id": backup_id,
                    }
                entry: dict = {
                    "path": _safe_relative(self.root, path),
                    "before": before,
                }
                if path in delete_set:
                    entry["after"] = {"kind": "absent"}
                elif path in normalized_writes:
                    entry["after"] = {
                        "kind": "file",
                        "sha256": f"sha256:{_sha256_bytes(normalized_writes[path])}",
                    }
                # Otherwise the entry carries no `after`: the idempotency
                # ledger's after-image is computed after projection (it
                # embeds snapshot_after) and completed by
                # _update_intent_after before that write lands. Until then
                # recovery treats anything but `before` as unprovable.
                intent["paths"].append(entry)
            _atomic_write_bytes(
                staging_dir / "intent.json", json.dumps(intent).encode("utf-8"))
            os.rename(staging_dir, inflight_dir)
            journal_published = True
            dir_fd = os.open(inflight_parent, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)

            for path, content in normalized_writes.items():
                # Compare with the bytes already captured for rollback. Keep
                # scope/revision checks and receipt evidence for the complete
                # approved write set, but avoid replacing identical files.
                if backups[path] != content:
                    _atomic_write_bytes(path, content)
            for path in delete_paths:
                if path.is_dir():
                    raise TransactionFailure(f"transaction refuses to delete directory: {path}")
                path.unlink(missing_ok=True)
            failed_stage = "core.validation"
            if validate_state is not None:
                errors = list(validate_state())
                if errors:
                    preview = "; ".join(str(issue) for issue in errors[:6])
                    # Telemetry carries the tag and the count, never the
                    # preview: validator text may quote canonical prose. The
                    # detail still travels to the caller on the exception.
                    diag_tracer.emit_event(
                        diag_conventions.EVENT_STAGE_FAILED,
                        stage="core.validation", status="error",
                        attrs={"error": "canonical validation failed",
                               "issues": len(errors)})
                    raise TransactionFailure(
                        f"transaction failed canonical validation: {preview}"
                    )
            diag_tracer.emit_event(diag_conventions.EVENT_VALIDATION_PASSED)
            failed_stage = "core.projection"
            diag_tracer.emit_event(diag_conventions.EVENT_PROJECTION_STARTED)
            projected_snapshot = publish() if publish is not None else None
            diag_tracer.emit_event(
                diag_conventions.EVENT_PROJECTION_PUBLISHED,
                attrs={"snapshot": projected_snapshot})

            snapshot_after = take_fingerprint()
            snapshot_after_id = f"sha256:{snapshot_after}"
            if projected_snapshot is not None \
                    and projected_snapshot != snapshot_after_id:
                raise TransactionFailure(
                    "canonical state changed during projection publication "
                    f"(projected {projected_snapshot}, actual {snapshot_after_id})"
                )
            failed_stage = "core.commit"
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
                # The journal leads the mutation it describes: record the
                # after-image before these bytes land.
                _update_intent_after(
                    inflight_dir, _idempotency_relative, idempotency_content)
                _atomic_write_bytes(idempotency_path, idempotency_content)
                normalized_writes[idempotency_path] = idempotency_content
            failed_stage = "core.receipt"
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
            commit_reached = True
            # The irrevocable point: receipt bytes are durable and the except
            # path below no longer rolls back. `core.transaction.committed`
            # names exactly this line, nothing earlier.
            diag_tracer.emit_event(
                diag_conventions.EVENT_CORE_TRANSACTION_COMMITTED,
                attrs={"transaction_id": transaction_id,
                       "snapshot_after": snapshot_after_id})
            diag_tracer.emit_event(
                diag_conventions.EVENT_RECEIPT_PERSISTED,
                attrs={"receipt": _safe_relative(self.root, receipt_path)})

            # The receipt above is already the commit boundary: it is
            # irrevocable, and no failure below undoes it. Bookkeeping
            # failure preserves canonical state and the receipt and raises
            # PostCommitFailure; exact replay repairs the remaining
            # bookkeeping.
            if touched is not None:
                touched([*normalized_writes, *delete_paths, receipt_path])

            try:
                shutil.rmtree(inflight_dir)
            except OSError as exc:
                raise TransactionFailure(f"transaction committed successfully but inflight journal cleanup failed: {exc}") from exc

            return TransactionResult(
                transaction_id=transaction_id,
                receipt_path=receipt_path,
                revisions=changed_revisions,
                snapshot_before=snapshot_before_id,
                snapshot_after=snapshot_after_id,
            )
        except Exception as exc:
            if commit_reached:
                diag_tracer.emit_event(
                    diag_conventions.EVENT_STAGE_FAILED,
                    stage="core.commit", status="error",
                    attrs={"error": "post-commit hook failed after commit",
                           "committed": True})
                raise PostCommitFailure(
                    f"transaction committed but post-commit hooks failed: {exc}",
                    transaction_id=transaction_id,
                    receipt_path=_safe_relative(self.root, receipt_path),
                    snapshot_after=snapshot_after_id,
                ) from exc

            # Telemetry carries the exception kind, never its body: messages
            # quote paths, errno text, and handler prose. The body still
            # travels to the caller on the re-raised exception.
            diag_tracer.emit_event(
                diag_conventions.EVENT_STAGE_FAILED,
                stage=failed_stage, status="error",
                attrs={"error": type(exc).__name__})
            diag_tracer.emit_event(diag_conventions.EVENT_ROLLBACK_STARTED)
            rollback_failures = rollback()
            diag_tracer.emit_event(
                diag_conventions.EVENT_ROLLBACK_COMPLETED,
                status="ok" if not rollback_failures else "error",
                attrs={"failures": sorted(rollback_failures)})
            if failed_stage == "core.projection":
                # Typed projection provenance: the gateway classifies by
                # subsystem and rollback outcome, never by exception prose.
                # Message text stays byte-identical to the untyped path.
                if rollback_failures:
                    raise ProjectionFailure(
                        f"{exc}; rollback incomplete for: {', '.join(rollback_failures)}",
                        rollback_complete=False,
                    ) from exc
                if republication_defects:
                    # Fixed wording: the gateway classifies TransactionFailure
                    # prose, so the defect's own text (which may name
                    # snapshots, revisions, …) must not leak into this
                    # message. The original exception already names the
                    # defect; the type here only aids debugging.
                    defect = type(republication_defects[0]).__name__
                    raise ProjectionFailure(
                        f"{exc}; rolled back completely but the restored pre-state "
                        f"cannot be re-published ({defect}); the defect pre-exists "
                        "this write",
                        rollback_complete=True,
                        pre_existing_defect=True,
                    ) from exc
                raise ProjectionFailure(str(exc), rollback_complete=True) from exc
            if rollback_failures:
                raise TransactionFailure(
                    f"{exc}; rollback incomplete for: {', '.join(rollback_failures)}"
                ) from exc
            if republication_defects:
                defect = type(republication_defects[0]).__name__
                raise TransactionFailure(
                    f"{exc}; rolled back completely but the restored pre-state "
                    f"cannot be re-published ({defect}); the defect pre-exists "
                    "this write",
                    pre_existing_defect=True,
                ) from exc
            if isinstance(exc, TransactionFailure):
                raise
            raise TransactionFailure(str(exc)) from exc
