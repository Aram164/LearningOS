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
import contextvars
import datetime as dt
import fcntl
import hashlib
import inspect
import json
import os
import re
import shutil
import stat
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import NoReturn

import yaml
from jsonschema import Draft202012Validator

from learning_os.domain.failures import (
    PostCommitFailure,
    ProjectionFailure,
    ReplayEvidenceError,
    TransactionConflict,
    TransactionFailure,
    TransactionIdempotencyConflict,
    TransactionPublicationUncertain,
    TransactionRecoveryConflict,
    TransactionRollbackIncomplete,
    TransactionScopeError,
    TransactionSnapshotConflict,
    TransactionValidationFailure,
)
from learning_os.domain.transaction import PublicationState, TransactionResult
from learning_os.store import observations
from learning_os.store import revisions as revision_store
from learning_os.store.contracts.gateway import (
    APPROVAL_KINDS,
    GATEWAY_CHANNELS,
    GatewayRequestContext,
    current_gateway_request,
)
from learning_os.store.contracts.write_scopes import (
    WriteScopeError,
    require_write_scope,
    scope_matches,
    write_target,
)
from learning_os.store.diagnostics import conventions as diag_conventions
from learning_os.store.diagnostics import tracer as diag_tracer
from learning_os.store.diagnostics.store import bind_store as _bind_diag_store
from learning_os.store.evidence import default_authority_root as _default_authority_root
from learning_os.store.evidence import idempotency_ledger_path as _idempotency_ledger_path
from learning_os.store.evidence import load_idempotency_entries as _load_idempotency_entries
from learning_os.store.evidence import replay_for_request

# One digest, one root list, shared with the projection (see fingerprint.py).
# Re-exported here because the receipt fields and every existing caller name it
# through this module.
from learning_os.store.fingerprint import (
    FINGERPRINT_DEFINITION_VERSION,
    canonical_data_and_stat_fingerprints,
    canonical_fingerprint,
    canonical_stat_digest,
    data_roots_fingerprint,
)
from learning_os.store.layout import PathBoundaryError, read_text_inside
from learning_os.store.revisions import artifact_revision, load_revisions

__all__ = [
    "ReplayEvidenceError",
    "TransactionFailure",
    "TransactionIdempotencyConflict",
    "TransactionPublicationUncertain",
    "TransactionRecoveryConflict",
    "TransactionRollbackIncomplete",
    "TransactionValidationFailure",
    "TransactionService",
    "artifact_revision",
    "canonical_fingerprint",
    "load_revisions",
    "parse_expected_revisions",
    "reconcile_inflight_transactions",
]

_ENGINE_PHASE: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "learningos_engine_phase", default=None)


@contextlib.contextmanager
def _engine_phase(name: str):
    token = _ENGINE_PHASE.set(name)
    try:
        yield
    finally:
        _ENGINE_PHASE.reset(token)


def current_engine_phase() -> str | None:
    return _ENGINE_PHASE.get()


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


def _safe_relative(root: Path, path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise TransactionFailure(f"transaction path escapes repository: {path}") from exc


def transaction_artifacts(root: Path, artifact_ids: Iterable[str],
                          writes: Iterable[Path],
                          deletes: Iterable[Path] = ()) -> list[str]:
    """The exact artifact set one transaction guards.

    Declared ids win; a transaction that declares none guards each touched
    path instead. ``commit`` enforces this set, and the seal-time dry run
    derives it through this same function — so the guards an envelope is
    sealed with are the guards the gateway checks, by construction rather
    than by a second implementation that could drift.
    """
    artifacts = sorted({str(value).strip() for value in artifact_ids
                        if str(value).strip()})
    if not artifacts:
        artifacts = [f"file:{_safe_relative(root, path)}"
                     for path in [*writes, *deletes]]
    return artifacts


def _sync_fd(fd: int) -> None:
    """One persistence barrier: flush, then the stronger full flush.

    ``os.fsync`` alone does not flush the drive cache on macOS; where the
    platform offers ``F_FULLFSYNC`` the barrier is not proven until it
    returns. Its failure is the barrier's failure — never silently
    downgraded to the weaker guarantee.
    """
    os.fsync(fd)
    fullfsync = getattr(fcntl, "F_FULLFSYNC", None)
    if fullfsync is not None:
        fcntl.fcntl(fd, fullfsync)


def _sync_directory(path: Path) -> None:
    """Make one directory's entries durable; a missing directory is done."""
    try:
        fd = os.open(path, os.O_RDONLY)
    except FileNotFoundError:
        return
    try:
        _sync_fd(fd)
    finally:
        os.close(fd)


def atomic_write_bytes(path: Path, content: bytes) -> None:
    """Atomically replace *path* and make the replacement crash-durable.

    ``os.replace`` alone guarantees visibility, not persistence. Flushing the
    file before replacement and the directory after it closes the window where
    a committed receipt can survive while the content it records does not.
    Newly created ancestors are part of the same guarantee: each created
    directory's entry lives in its parent, so every created level is
    synchronized after the replacement, deepest first.
    """
    # Preserve the gateway's established atomic sibling name. Existing red-team
    # checks deliberately block this path to verify rollback.
    tmp = path.with_name(f".{path.name}.tmp")
    try:
        created: list[Path] = []
        cursor = path.parent
        while not cursor.exists():
            created.append(cursor)
            if cursor.parent == cursor:
                break
            cursor = cursor.parent
        path.parent.mkdir(parents=True, exist_ok=True)
        with tmp.open("wb") as handle:
            handle.write(content)
            handle.flush()
            _sync_fd(handle.fileno())
        os.replace(tmp, path)
        _sync_directory(path.parent)
        for ancestor in created:
            _sync_directory(ancestor.parent)
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
    atomic_write_bytes(intent_path, json.dumps(intent).encode("utf-8"))


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


def _receipt_binding_detail(root: Path, data: dict, intent: Mapping) -> str:
    """Join a receipt to its journal and request evidence, or say why not.

    Returns "" when the receipt is bound, else a short structural detail.
    Schema validity, committed status and a matching transaction id alone
    are not evidence: the receipt's recorded effects must equal the
    journal's intended effects for every non-ledger path, and a version-2
    receipt must join the idempotency row its request created. Historical
    evidence is verified against the recorded transaction — live files
    and the whole current ledger are never required to equal an old
    postimage, so later legitimate writes do not invalidate it.
    """
    entries = intent.get("paths")
    if not isinstance(entries, list):
        # A version-1 journal carries no intended effects to join against;
        # its conservative handling lives in its own reconciler.
        return ""
    journal: dict[str, dict] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            return "the journal entry is malformed"
        if entry["path"] in journal:
            return "the journal lists a path twice"
        journal[entry["path"]] = entry
    exempt: set[str] = set()
    for ledger_path in (revision_store.revision_ledger_path(root),
                        _idempotency_ledger_path(root)):
        with contextlib.suppress(TransactionFailure):
            exempt.add(_safe_relative(root, ledger_path))
    writes = data.get("writes")
    if not isinstance(writes, list):
        return "the receipt records no writes"
    rows: dict[str, dict] = {}
    for row in writes:
        if not isinstance(row, dict) or not isinstance(row.get("path"), str):
            return "the receipt write row is malformed"
        if row["path"] in rows:
            return "the receipt records a write twice"
        rows[row["path"]] = row
    for relative, row in rows.items():
        entry = journal.get(relative)
        if entry is None:
            return f"the receipt records a write the journal does not: {relative}"
        after = entry.get("after")
        if not isinstance(after, dict):
            return f"the journal records no intended effect for {relative}"
        expected_after = (
            None if after.get("kind") == "absent"
            else _strip_journal_digest(after.get("sha256"))
        )
        if after.get("kind") not in ("absent", "file") \
                or (after.get("kind") == "file" and expected_after is None) \
                or row.get("sha256_after") != expected_after:
            return f"the receipt effect does not match the journal: {relative}"
        before = entry.get("before")
        if not isinstance(before, dict):
            return f"the journal entry is malformed: {relative}"
        expected_before = (
            None if before.get("kind") == "absent"
            else _strip_journal_digest(before.get("sha256"))
        )
        if before.get("kind") not in ("absent", "file") \
                or (before.get("kind") == "file" and expected_before is None) \
                or row.get("sha256_before") != expected_before \
                or row.get("created") != (before.get("kind") == "absent"):
            return f"the receipt origin does not match the journal: {relative}"
    for relative in journal:
        if relative not in exempt and relative not in rows:
            return f"the journal effect is missing from the receipt: {relative}"
    if data.get("schema_version") == 2:
        request = data.get("request")
        if not isinstance(request, dict):
            return "the receipt has no request record"
        try:
            ledger = _load_idempotency_entries(root)
        except TransactionFailure:
            return "the idempotency evidence is unreadable"
        row = ledger.get(request.get("idempotency_key"))
        if row is None:
            return "the receipt is not bound to an idempotency entry"
        if row.get("transaction_id") != data.get("id") \
                or row.get("receipt_path") != intent.get("receipt_path") \
                or row.get("request_id") != request.get("request_id") \
                or row.get("intent_sha256") != request.get("intent_sha256") \
                or row.get("capability") != data.get("capability") \
                or row.get("snapshot_before") != data.get("snapshot_before") \
                or row.get("snapshot_after") != data.get("snapshot_after"):
            return "the idempotency entry does not match the receipt"
        artifact_revisions = data.get("artifact_revisions")
        if not isinstance(artifact_revisions, dict):
            return "the receipt has no artifact revisions"
        recorded = {}
        for artifact, entry in artifact_revisions.items():
            if not isinstance(entry, dict):
                return "the receipt artifact revision is malformed"
            recorded[artifact] = entry.get("after")
        if recorded != dict(row.get("revisions") or {}):
            return "the idempotency revisions do not match the receipt"
    return ""


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
        from learning_os.store.loading.yamlio import UniqueKeySafeLoader

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
    detail = _receipt_binding_detail(root, data, intent)
    if detail:
        return ("CONTRADICTORY", detail)
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
        _sync_directory(tx_dir.parent)
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
                with _engine_phase("restore"):
                    path.unlink()
                    _sync_directory(path.parent)
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
                with _engine_phase("restore"):
                    atomic_write_bytes(path, blob)
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


def _retire_committed_journal(root: Path, tx_dir: Path, intent: dict,
                              transaction_id: str, journal_rel: str) -> None:
    """Retire a proven commit's journal — after re-proving durability.

    A bound receipt proves what was published, not that its directory
    entry is durable: the barrier that failed during the original commit
    may still be failing. Retry the receipt-parent synchronization
    before deleting the recovery evidence; if it still fails, the
    journal (and the ambiguous outcome) is preserved.
    """
    raw_receipt = intent.get("receipt_path")
    if isinstance(raw_receipt, str) and raw_receipt:
        try:
            _sync_directory((root / raw_receipt).parent)
        except OSError as exc:
            raise TransactionRecoveryConflict(
                f"transaction {transaction_id} commit receipt durability "
                f"could not be established ({exc}); no canonical path is "
                f"affected, the journal was preserved under {journal_rel}, "
                f"and the next run retries the barrier",
                transaction_id=transaction_id,
                conflicts=[{"path": raw_receipt,
                            "reason": "RECEIPT_DURABILITY_UNPROVEN",
                            "detail": str(exc)}]) from exc
    _remove_journal(tx_dir, transaction_id, journal_rel)


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
        _retire_committed_journal(root, tx_dir, intent, transaction_id, journal_rel)
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
        _retire_committed_journal(root, tx_dir, intent, transaction_id, journal_rel)
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


def _accepts_snapshot_seed(publish: Callable[..., str | None]) -> bool:
    """Whether ``publish`` takes the post-commit snapshot seed (#104).

    Seeded publishers stamp the projection without a second canonical walk;
    zero-argument publishers (migrations, test doubles) walk themselves.
    """
    try:
        parameters = inspect.signature(publish).parameters.values()
    except (TypeError, ValueError):
        return False
    return any(p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD, p.VAR_POSITIONAL)
               for p in parameters)


@dataclass
class _CommitRun:
    """The state one ``TransactionService.commit`` call carries between its phases."""

    request: GatewayRequestContext | None
    capability: str
    delete_paths: list[Path] = field(default_factory=list)
    relative_paths: dict[Path, str] = field(default_factory=dict)
    normalized_writes: dict[Path, bytes] = field(default_factory=dict)
    authority_by_path: dict[Path, str] = field(default_factory=dict)
    artifacts: list[str] = field(default_factory=list)
    revisions_before: dict[str, int] = field(default_factory=dict)
    expected: dict[str, int] = field(default_factory=dict)
    conflicts: dict[str, tuple[int, int]] = field(default_factory=dict)
    revisions_after: dict[str, int] = field(default_factory=dict)
    changed_revisions: dict[str, int] = field(default_factory=dict)
    now: dt.datetime | None = None
    transaction_id: str = ""
    receipt_path: Path | None = None
    owned_paths: set[Path] = field(default_factory=set)
    authority_grants: dict[str, tuple[str, ...]] = field(default_factory=dict)
    ledger_path: Path | None = None
    idempotency_path: Path | None = None
    idempotency_relative: str | None = None
    idempotency_entries: dict[str, dict] | None = None
    backups: dict[Path, bytes | None] = field(default_factory=dict)
    take_fingerprint: Callable[[], str] | None = None
    snapshot_before: str = ""
    snapshot_before_id: str = ""
    inflight_parent: Path | None = None
    staging_dir: Path | None = None
    inflight_dir: Path | None = None
    journal_published: bool = False
    republication_defects: list[Exception] = field(default_factory=list)
    publication_state: PublicationState = PublicationState.NOT_PUBLISHED
    failed_stage: str = "core.commit"
    use_combined: bool = False
    pre_stat: str | None = None
    snapshot_after_id: str | None = None
    data_roots_after_id: str | None = None


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
        self.clock = clock or observations.now
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
        request, replay = self._admit(capability, gateway_request)
        if replay is not None:
            return replay
        run = _CommitRun(request=request, capability=capability)
        self._normalize(run, writes, deletes, write_authorities, artifact_ids)
        self._plan_revisions(run, expected_revisions)
        self._allocate_identity(run, transaction_writes)
        self._enforce_authority(run)
        self._capture_prestate(run, fingerprint)
        self._guard_snapshot(run, expected_snapshot)
        run.inflight_parent = self.root / "operations" / "transactions" / ".inflight"
        run.staging_dir = run.inflight_parent / f".preparing-{run.transaction_id}"
        run.inflight_dir = run.inflight_parent / run.transaction_id
        run.journal_published = False
        # Content (non-OSError) failures re-publishing over proven pre-state.
        # The defect pre-exists the write: canonical rollback completed, so
        # the journal is removed and the refusal reports the pre-existing
        # defect instead of an unknown outcome (JF-11).
        run.republication_defects = []
        try:
            run.publication_state = PublicationState.NOT_PUBLISHED
            run.failed_stage = "core.commit"
            self._publish_journal(run)
            self._apply(run)
            self._validate(run, validate_state, fingerprint)
            self._publish_projection(run, publish)
            self._record_idempotency(run)
            self._write_receipt(run, metadata)
            return self._finish(run, touched)
        except Exception as exc:
            failure = self._failure(run, exc, publish, rollback_publish)
            if failure is None:
                raise
            raise failure from exc

    def _admit(self, capability: str, gateway_request: GatewayRequestContext | None) -> tuple[GatewayRequestContext | None, TransactionResult | None]:
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
                return request, replay
        return request, None

    def _target(self, raw_path: Path) -> tuple[Path, str]:
        try:
            return write_target(self.root, raw_path)
        except WriteScopeError as exc:
            raise TransactionScopeError(str(exc)) from exc

    def _normalize(self, run: _CommitRun, writes, deletes, write_authorities, artifact_ids) -> None:
        run.delete_paths = []
        run.relative_paths = {}
        for raw_path in deletes:
            path, relative = self._target(Path(raw_path))
            run.delete_paths.append(path)
            run.relative_paths[path] = relative
        if not writes and not run.delete_paths:
            raise TransactionFailure("transaction contains no writes")

        run.normalized_writes = {}
        for raw_path, value in writes.items():
            path, relative = self._target(Path(raw_path))
            run.relative_paths[path] = relative
            run.normalized_writes[path] = value.encode("utf-8") if isinstance(value, str) else bytes(value)

        for path in run.delete_paths:
            if path in run.normalized_writes:
                raise TransactionFailure(f"transaction both writes and deletes {path}")

        run.authority_by_path = {}
        for raw_path, authority in (write_authorities or {}).items():
            path, relative = self._target(Path(raw_path))
            run.relative_paths.setdefault(path, relative)
            if not isinstance(authority, str) or not authority.strip():
                raise TransactionScopeError("write authority names must be non-empty")
            existing = run.authority_by_path.get(path)
            if existing is not None and existing != authority.strip():
                raise TransactionScopeError(
                    f"transaction declares conflicting authorities for {_safe_relative(self.root, path)}"
                )
            run.authority_by_path[path] = authority.strip()

        run.artifacts = transaction_artifacts(
            self.root, artifact_ids, run.normalized_writes, run.delete_paths)

    def _plan_revisions(self, run: _CommitRun, expected_revisions) -> None:
        run.revisions_before = load_revisions(self.root)
        run.expected = dict(expected_revisions or {})
        if run.request is not None and set(run.expected) != set(run.artifacts):
            missing = sorted(set(run.artifacts) - set(run.expected))
            unexpected = sorted(set(run.expected) - set(run.artifacts))
            raise TransactionFailure(
                "GatewayEnvelopeV2 expected_revisions must cover exactly every "
                f"transaction artifact (missing={missing}, unexpected={unexpected}, "
                f"artifacts={run.artifacts})"
            )
        run.conflicts = {
            artifact: (wanted, run.revisions_before.get(artifact, 0))
            for artifact, wanted in run.expected.items()
            if run.revisions_before.get(artifact, 0) != wanted
        }
        run.revisions_after = dict(run.revisions_before)
        run.changed_revisions = {}
        for artifact in run.artifacts:
            next_value = run.revisions_before.get(artifact, 0) + 1
            run.revisions_after[artifact] = next_value
            run.changed_revisions[artifact] = next_value

    def _allocate_identity(self, run: _CommitRun, transaction_writes) -> None:
        # Allocate the one shared transaction identity before finalising writes.
        # Some transactional bookkeeping (for example an AI request moving to
        # ``completed``) must record that identity in the same atomic commit as
        # the canonical change.  ``transaction_writes`` provides that without
        # inventing a second receipt or updating state after the commit.
        run.now = self.clock().astimezone().replace(microsecond=0)
        # Prove the service-owned transaction directory is not an indirection
        # before it is created or enumerated for the next receipt identity.
        self._target(self.root / "operations" / "transactions" / ".authority-check")
        run.transaction_id, run.receipt_path = _next_transaction_identity(self.root, run.now)
        run.owned_paths = set()
        if transaction_writes is not None:
            try:
                owned_writes = transaction_writes(run.transaction_id)
            except Exception as exc:
                raise TransactionFailure(
                    f"cannot prepare transaction-owned writes: {exc}"
                ) from exc
            for raw_path, value in owned_writes.items():
                path, relative = self._target(Path(raw_path))
                run.relative_paths[path] = relative
                run.owned_paths.add(path)
                if path in run.delete_paths:
                    raise TransactionFailure(f"transaction both writes and deletes {path}")
                content = value.encode("utf-8") if isinstance(value, str) else bytes(value)
                if path in run.normalized_writes and run.normalized_writes[path] != content:
                    raise TransactionFailure(f"transaction defines conflicting writes for {path}")
                run.normalized_writes[path] = content

    def _enforce_authority(self, run: _CommitRun) -> None:
        # The declaration is enforced once, here, after every caller-owned and
        # transaction-owned destination is known and before any file changes.
        run.authority_grants = {}
        if self.authority_root is not None:
            from learning_os.store.contracts.capability_catalog import (
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
            authored_paths = set(run.normalized_writes) | set(run.delete_paths)
            for path in sorted(authored_paths, key=lambda value: run.relative_paths[value]):
                relative = run.relative_paths[path]
                scoped_relative = (
                    f"{self.scope_prefix}/{relative}" if self.scope_prefix else relative
                )
                authority = run.authority_by_path.get(path)
                if path in run.owned_paths and authority is None:
                    if not any(scope_matches(relative, row) for row in service_owned_scopes):
                        raise TransactionScopeError(
                            f"transaction-owned write is not service-owned: {relative}"
                        )
                    continue
                authority = authority or run.capability
                scopes = definitions.get(authority)
                if scopes is None:
                    raise TransactionScopeError(
                        f"unknown write authority {authority}; refusing {relative}"
                    )
                try:
                    require_write_scope(authority, scoped_relative, scopes)
                except WriteScopeError as exc:
                    raise TransactionScopeError(str(exc)) from exc
                run.authority_grants[authority] = tuple(scopes)
            unused = set(run.authority_by_path) - authored_paths
            if unused:
                listing = ", ".join(sorted(run.relative_paths[path] for path in unused))
                raise TransactionScopeError(
                    f"write authority declared for a path outside the transaction: {listing}"
                )
        elif run.authority_by_path:
            raise TransactionScopeError(
                "write authorities were supplied without a capability catalogue"
            )

    def _capture_prestate(self, run: _CommitRun, fingerprint) -> None:
        run.ledger_path, _ledger_relative = self._target(
            revision_store.revision_ledger_path(self.root)
        )
        run.normalized_writes[run.ledger_path] = revision_store.dump_revisions(
            run.revisions_after
        ).encode("utf-8")

        run.idempotency_path = None
        run.idempotency_entries = None
        if run.request is not None:
            run.idempotency_path, run.idempotency_relative = self._target(
                _idempotency_ledger_path(self.root)
            )
            run.idempotency_entries = _load_idempotency_entries(self.root)

        all_paths = [*run.normalized_writes, *run.delete_paths]
        if run.idempotency_path is not None:
            all_paths.append(run.idempotency_path)
        run.backups = {
            path: path.read_bytes() if path.is_file() else None for path in all_paths
        }
        # A transaction service rooted somewhere without the canonical roots
        # would digest nothing and record a constant snapshot, which is worse
        # than none: it looks like a guard. Such callers may supply their own
        # digest over the artifacts they actually touch.
        run.take_fingerprint = fingerprint or (lambda: canonical_fingerprint(self.root))
        run.snapshot_before = run.take_fingerprint()
        run.snapshot_before_id = f"sha256:{run.snapshot_before}"

    def _guard_snapshot(self, run: _CommitRun, expected_snapshot) -> None:
        approved_snapshot = expected_snapshot
        if run.request is not None:
            if approved_snapshot is not None \
                    and run.request.expected_snapshot is not None \
                    and approved_snapshot != run.request.expected_snapshot:
                raise TransactionFailure(
                    "transaction expected snapshot does not match its gateway approval"
                )
            approved_snapshot = approved_snapshot or run.request.expected_snapshot
        if approved_snapshot is not None and approved_snapshot != run.snapshot_before_id:
            diag_tracer.emit_event(
                diag_conventions.EVENT_STAGE_FAILED,
                stage="core.snapshot_guard", status="error",
                attrs={"error": "snapshot changed since approval"})
            raise TransactionSnapshotConflict(
                approved_snapshot,
                run.snapshot_before_id,
            )
        # Snapshot staleness is the broader approved-state conflict and keeps
        # its historical precedence when the same concurrent write also moved
        # an artifact revision.
        if run.conflicts:
            diag_tracer.emit_event(
                diag_conventions.EVENT_STAGE_FAILED,
                stage="core.revision_guard", status="error",
                attrs={"error": "artifact revision moved",
                       "artifacts": sorted(run.conflicts)})
            raise TransactionConflict(run.conflicts)

    def _rollback(self, run: _CommitRun, publish, rollback_publish) -> list[str]:
        """Unwind through the published journal, never from memory alone.

        Live rollback and crash recovery execute the same
        compare-and-undo engine against the same on-disk journal, so a
        foreign write landing during validation or projection is
        preserved and reported instead of blindly overwritten. On
        ambiguity the journal stays for the next run and the caller
        gets the unrestored paths, never a false success.
        """
        failures: list[str] = []
        if os.path.lexists(run.receipt_path):
            # Commit was not reached, so this transaction never wrote
            # a receipt: anything here is foreign evidence. Report it;
            # never delete it.
            failures.append(_safe_relative(self.root, run.receipt_path))
        if not run.journal_published:
            # The journal never armed, so no canonical mutation could
            # have happened. Verify live state still equals the
            # pre-state snapshots and touch nothing — even here a
            # blind memory restore could clobber a foreign write that
            # landed while staging.
            for path, old in run.backups.items():
                try:
                    live = path.read_bytes() if path.is_file() else None
                except OSError:
                    live = "<unreadable>"
                if live != old:
                    failures.append(_safe_relative(self.root, path))
            shutil.rmtree(run.staging_dir, ignore_errors=True)
        else:
            journal_rel = _safe_relative(self.root, run.inflight_dir)
            try:
                disk_intent = json.loads(
                    (run.inflight_dir / "intent.json").read_text(
                        encoding="utf-8"))
            except (OSError, ValueError):
                failures.append(journal_rel)
                disk_intent = None
            if disk_intent is not None:
                if not isinstance(disk_intent, dict):
                    failures.append(journal_rel)
                else:
                    try:
                        _admit_v2_journal(self.root, run.inflight_dir,
                                          disk_intent)
                        _unwind_v2_entries(
                            self.root, run.inflight_dir, disk_intent["paths"],
                            run.transaction_id, journal_rel)
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
                            run.take_fingerprint() == run.snapshot_before)
                    except Exception:
                        prestate_intact = False
                    if prestate_intact:
                        run.republication_defects.append(exc)
                    else:
                        failures.append("<projection publication>")
        if failures or run.republication_defects:
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
            if run.journal_published:
                try:
                    _remove_journal(run.inflight_dir, run.transaction_id,
                                    journal_rel)
                except TransactionRecoveryConflict as exc:
                    failures.extend(conflict["path"]
                                    for conflict in exc.conflicts)
            else:
                shutil.rmtree(run.staging_dir, ignore_errors=True)
        return sorted(set(failures))

    def _publish_journal(self, run: _CommitRun) -> None:
        if os.path.lexists(run.inflight_dir):
            raise TransactionFailure(
                f"transaction {run.transaction_id} cannot start: a recovery "
                f"journal with this identity already exists under "
                f"{_safe_relative(self.root, run.inflight_dir)}; reconcile it "
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
        shutil.rmtree(run.staging_dir, ignore_errors=True)
        run.staging_dir.mkdir(parents=True)
        delete_set = set(run.delete_paths)
        intent: dict = {
            "schema_version": 2,
            "transaction_id": run.transaction_id,
            "receipt_path": _safe_relative(self.root, run.receipt_path),
            "paths": [],
        }
        for i, (path, old) in enumerate(run.backups.items()):
            if old is None:
                before: dict = {"kind": "absent"}
            else:
                backup_id = f"backup-{i}"
                atomic_write_bytes(run.staging_dir / backup_id, old)
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
            elif path in run.normalized_writes:
                entry["after"] = {
                    "kind": "file",
                    "sha256": f"sha256:{_sha256_bytes(run.normalized_writes[path])}",
                }
            # Otherwise the entry carries no `after`: the idempotency
            # ledger's after-image is computed after projection (it
            # embeds snapshot_after) and completed by
            # _update_intent_after before that write lands. Until then
            # recovery treats anything but `before` as unprovable.
            intent["paths"].append(entry)
        atomic_write_bytes(
            run.staging_dir / "intent.json", json.dumps(intent).encode("utf-8"))
        os.rename(run.staging_dir, run.inflight_dir)
        run.journal_published = True
        _sync_directory(run.inflight_parent)
        # A prior failed publication can leave an existing but unproven
        # directory entry. Re-establish the whole journal namespace on
        # every attempt, deepest first, before the first canonical effect.
        ancestor = run.inflight_parent
        while ancestor != self.root:
            try:
                _sync_directory(ancestor.parent)
            except OSError as exc:
                raise TransactionFailure(
                    f"cannot make transaction journal namespace durable: {exc}"
                ) from exc
            ancestor = ancestor.parent

    def _guard_apply(self, run: _CommitRun, path: Path,
                     intended: bytes | None) -> None:
        """Uncached comparison immediately before one mutation.

        The captured backup is the only pre-state this transaction may
        replace, and the intended bytes are the only forward state it may
        find already placed. Anything else is a foreign edit that landed
        between capture and apply: refuse here, and the compare-and-undo
        rollback preserves those bytes. This recheck cannot atomically
        exclude a writer racing after it — that cooperative-writer
        boundary is stated on ``reconcile_inflight_transactions``.
        """
        kind, digest = _inspect_live_path(path)
        if kind == "other":
            raise TransactionFailure(
                f"canonical state changed during transaction apply: "
                f"{_safe_relative(self.root, path)} is not a regular file"
            )
        live = digest if kind == "file" else None
        allowed = {
            _sha256_bytes(run.backups.get(path)),
            _sha256_bytes(intended),
        }
        if live not in allowed:
            raise TransactionFailure(
                f"canonical state changed during transaction apply: "
                f"{_safe_relative(self.root, path)}"
            )

    def _apply(self, run: _CommitRun) -> None:
        for path, content in run.normalized_writes.items():
            self._guard_apply(run, path, content)
            # Compare with the bytes already captured for rollback. Keep
            # scope/revision checks and receipt evidence for the complete
            # approved write set, but avoid replacing identical files.
            if run.backups[path] != content:
                with _engine_phase("apply"):
                    atomic_write_bytes(path, content)
        for path in run.delete_paths:
            if path.is_dir():
                raise TransactionFailure(f"transaction refuses to delete directory: {path}")
            self._guard_apply(run, path, None)
            with _engine_phase("apply"):
                path.unlink(missing_ok=True)
                _sync_directory(path.parent)

    def _validate(self, run: _CommitRun, validate_state, fingerprint) -> None:
        # Deduplicated post-commit fingerprint (#104 step 1): when the
        # guard digest is the canonical walk (the overwhelmingly common
        # path — no caller currently supplies a double), one traversal
        # yields canonical, data-roots, and stat digests. The canonical
        # value seeds the projection stamp so publish performs no second
        # walk; the stat value guards the publication window without
        # re-hashing bytes. Computed here, before validation, so the
        # validated repo loads at least as fresh as the seed — any
        # mutation between seed and post-publish check is caught below.
        run.use_combined = fingerprint is None
        if run.use_combined:
            post_hex, data_hex, run.pre_stat = (
                canonical_data_and_stat_fingerprints(self.root)
            )
            run.snapshot_after_id = f"sha256:{post_hex}"
            run.data_roots_after_id = f"sha256:{data_hex}"
        else:
            run.pre_stat = None
        run.failed_stage = "core.validation"
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
                raise TransactionValidationFailure(
                    f"transaction failed canonical validation: {preview}"
                )
        diag_tracer.emit_event(diag_conventions.EVENT_VALIDATION_PASSED)

    def _publish_projection(self, run: _CommitRun, publish) -> None:
        run.failed_stage = "core.projection"
        diag_tracer.emit_event(diag_conventions.EVENT_PROJECTION_STARTED)
        if run.use_combined:
            if publish is None:
                projected_snapshot = None
            else:
                # Decided by signature, never by catching TypeError: a
                # publisher's own TypeError must fail the projection, not
                # re-run it unseeded.
                projected_snapshot = (publish(run.snapshot_after_id)
                                      if _accepts_snapshot_seed(publish)
                                      else publish())
        else:
            projected_snapshot = publish() if publish is not None else None
        diag_tracer.emit_event(
            diag_conventions.EVENT_PROJECTION_PUBLISHED,
            attrs={"snapshot": projected_snapshot})

        if run.use_combined:
            post_stat = canonical_stat_digest(self.root)
            if post_stat != run.pre_stat:
                actual_hex, actual_data_hex, _ = (
                    canonical_data_and_stat_fingerprints(self.root)
                )
                actual_id = f"sha256:{actual_hex}"
                if projected_snapshot is not None \
                        and projected_snapshot != actual_id:
                    raise TransactionFailure(
                        "canonical state changed during projection publication "
                        f"(projected {projected_snapshot}, actual {actual_id})"
                    )
                run.snapshot_after_id = actual_id
                run.data_roots_after_id = f"sha256:{actual_data_hex}"
            elif projected_snapshot is not None \
                    and projected_snapshot != run.snapshot_after_id:
                actual_hex = canonical_fingerprint(self.root)
                actual_id = f"sha256:{actual_hex}"
                raise TransactionFailure(
                    "canonical state changed during projection publication "
                    f"(projected {projected_snapshot}, actual {actual_id})"
                )
        else:
            snapshot_after = run.take_fingerprint()
            run.snapshot_after_id = f"sha256:{snapshot_after}"
            # The authored-data half of the same post-commit tree, for
            # read-only diagnostics: the resolver compares it against the
            # current data roots to tell a contract-only move from data
            # drift. Computed from disk even when the guard digest is a
            # caller-supplied double — it records the tree, never the
            # double — and it never guards a write.
            run.data_roots_after_id = f"sha256:{data_roots_fingerprint(self.root)}"
            if projected_snapshot is not None \
                    and projected_snapshot != run.snapshot_after_id:
                raise TransactionFailure(
                    "canonical state changed during projection publication "
                    f"(projected {projected_snapshot}, actual {run.snapshot_after_id})"
                )

    def _record_idempotency(self, run: _CommitRun) -> None:
        run.failed_stage = "core.commit"
        if run.request is not None and run.idempotency_path is not None \
                and run.idempotency_entries is not None:
            run.idempotency_entries[run.request.idempotency_key] = {
                "request_id": run.request.request_id,
                "capability": run.capability,
                "channel": run.request.channel,
                "intent_sha256": run.request.intent_sha256,
                "transaction_id": run.transaction_id,
                "receipt_path": _safe_relative(self.root, run.receipt_path),
                "revisions": dict(run.changed_revisions),
                "snapshot_before": run.snapshot_before_id,
                "snapshot_after": run.snapshot_after_id,
            }
            idempotency_content = _dump_idempotency_entries(
                run.idempotency_entries
            ).encode("utf-8")
            self._guard_apply(run, run.idempotency_path, idempotency_content)
            # The journal leads the mutation it describes: record the
            # after-image before these bytes land.
            _update_intent_after(
                run.inflight_dir, run.idempotency_relative, idempotency_content)
            atomic_write_bytes(run.idempotency_path, idempotency_content)
            run.normalized_writes[run.idempotency_path] = idempotency_content

    def _write_receipt(self, run: _CommitRun, metadata) -> None:
        run.failed_stage = "core.receipt"
        rows = []
        for path, after in run.normalized_writes.items():
            if path == run.ledger_path or path == run.idempotency_path:
                continue
            before = run.backups.get(path)
            rows.append({
                "path": _safe_relative(self.root, path),
                "sha256_before": _sha256_bytes(before),
                "sha256_after": _sha256_bytes(after),
                "created": before is None,
            })
        for path in run.delete_paths:
            before = run.backups.get(path)
            rows.append({
                "path": _safe_relative(self.root, path),
                "sha256_before": _sha256_bytes(before),
                "sha256_after": None,
                "created": False,
            })
        receipt = {
            "schema_version": 2 if run.request is not None else 1,
            "id": run.transaction_id,
            "type": "transaction-receipt",
            "status": "committed",
            "capability": run.capability,
            "committed_at": run.now.isoformat(),
            "snapshot_before": run.snapshot_before_id,
            "snapshot_after": run.snapshot_after_id,
            "expected_revisions": run.expected,
            "artifact_revisions": {
                artifact: {
                    "before": run.revisions_before.get(artifact, 0),
                    "after": run.changed_revisions[artifact],
                }
                for artifact in run.artifacts
            },
            "writes": sorted(rows, key=lambda row: row["path"]),
            "metadata": {
                **dict(metadata or {}),
                "data_roots_sha256": run.data_roots_after_id,
                "fingerprint_definition": FINGERPRINT_DEFINITION_VERSION,
            },
        }
        if run.request is not None:
            receipt["authority"] = {
                "capability_contract_version": 2,
                "enforced": self.authority_root is not None,
                "grants": [
                    {
                        "capability": authority,
                        "declared_writes": list(run.authority_grants[authority]),
                    }
                    for authority in sorted(run.authority_grants)
                ],
            }
            receipt["request"] = {
                "channel": run.request.channel,
                "request_id": run.request.request_id,
                "idempotency_key": run.request.idempotency_key,
                "intent_sha256": run.request.intent_sha256,
                "approval": {
                    "kind": run.request.approval_kind,
                    "subject_sha256": run.request.approval_subject_sha256,
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
        if run.receipt_path.exists():
            raise TransactionFailure(f"receipt path already exists: {run.receipt_path}")
        # Mark uncertainty BEFORE entering the operation that can expose
        # the receipt: atomic_write_bytes makes the receipt visible at
        # os.replace, before its parent-directory barrier returns. Any
        # failure from here until the barrier returns is ambiguous, not a
        # licence to roll back behind a possibly published receipt.
        run.publication_state = PublicationState.PUBLICATION_UNCERTAIN
        atomic_write_bytes(run.receipt_path, _receipt_text(receipt).encode("utf-8"))
        run.publication_state = PublicationState.DURABLE
        # The irrevocable point: receipt bytes are durable and the except
        # path below no longer rolls back. `core.transaction.committed`
        # names exactly this line, nothing earlier.
        diag_tracer.emit_event(
            diag_conventions.EVENT_CORE_TRANSACTION_COMMITTED,
            attrs={"transaction_id": run.transaction_id,
                   "snapshot_after": run.snapshot_after_id})
        diag_tracer.emit_event(
            diag_conventions.EVENT_RECEIPT_PERSISTED,
            attrs={"receipt": _safe_relative(self.root, run.receipt_path)})

    def _finish(self, run: _CommitRun, touched) -> TransactionResult:
        # The receipt above is already the commit boundary: it is
        # irrevocable, and no failure below undoes it. Bookkeeping
        # failure preserves canonical state and the receipt and raises
        # PostCommitFailure; exact replay repairs the remaining
        # bookkeeping.
        if touched is not None:
            touched([*run.normalized_writes, *run.delete_paths, run.receipt_path])

        try:
            shutil.rmtree(run.inflight_dir)
            _sync_directory(run.inflight_dir.parent)
        except OSError as exc:
            raise TransactionFailure(f"transaction committed successfully but inflight journal cleanup failed: {exc}") from exc

        return TransactionResult(
            transaction_id=run.transaction_id,
            receipt_path=run.receipt_path,
            revisions=run.changed_revisions,
            snapshot_before=run.snapshot_before_id,
            snapshot_after=run.snapshot_after_id,
        )

    def _failure(self, run: _CommitRun, exc: Exception, publish, rollback_publish) -> Exception | None:
        if run.publication_state is PublicationState.PUBLICATION_UNCERTAIN:
            # The receipt may already be visible. Distinguish this
            # transaction's matching evidence from absence and from
            # foreign/contradictory files: only proven absence means the
            # publication boundary was never crossed and the guarded
            # rollback below may still run. Anything else preserves the
            # forward state and the journal for restart reconciliation.
            verdict, _detail = _inspect_commit_receipt(
                self.root,
                {
                    "transaction_id": run.transaction_id,
                    "receipt_path": _safe_relative(self.root, run.receipt_path),
                },
            )
            if verdict != "ABSENT":
                diag_tracer.emit_event(
                    diag_conventions.EVENT_STAGE_FAILED,
                    stage="core.receipt", status="error",
                    attrs={"error": "publication uncertain",
                           "committed": "unknown"})
                return TransactionPublicationUncertain(
                    f"transaction receipt publication is uncertain: {exc}",
                    transaction_id=run.transaction_id,
                    receipt_path=_safe_relative(self.root, run.receipt_path),
                )
            run.publication_state = PublicationState.NOT_PUBLISHED
        if run.publication_state is PublicationState.DURABLE:
            diag_tracer.emit_event(
                diag_conventions.EVENT_STAGE_FAILED,
                stage="core.commit", status="error",
                attrs={"error": "post-commit hook failed after commit",
                       "committed": True})
            return PostCommitFailure(
                f"transaction committed but post-commit hooks failed: {exc}",
                transaction_id=run.transaction_id,
                receipt_path=_safe_relative(self.root, run.receipt_path),
                snapshot_after=run.snapshot_after_id,
            )

        # Telemetry carries the exception kind, never its body: messages
        # quote paths, errno text, and handler prose. The body still
        # travels to the caller on the re-raised exception.
        diag_tracer.emit_event(
            diag_conventions.EVENT_STAGE_FAILED,
            stage=run.failed_stage, status="error",
            attrs={"error": type(exc).__name__})
        diag_tracer.emit_event(diag_conventions.EVENT_ROLLBACK_STARTED)
        rollback_failures = self._rollback(run, publish, rollback_publish)
        diag_tracer.emit_event(
            diag_conventions.EVENT_ROLLBACK_COMPLETED,
            status="ok" if not rollback_failures else "error",
            attrs={"failures": sorted(rollback_failures)})
        if run.failed_stage == "core.projection":
            # Typed projection provenance: the gateway classifies by
            # subsystem and rollback outcome, never by exception prose.
            # Message text stays byte-identical to the untyped path.
            if rollback_failures:
                return ProjectionFailure(
                    f"{exc}; rollback incomplete for: {', '.join(rollback_failures)}",
                    rollback_complete=False,
                )
            if run.republication_defects:
                # Fixed wording: the message names only the defect's
                # type, never its text (which may quote snapshots,
                # revisions, or canonical prose). The chained original
                # exception already carries the full defect.
                defect = type(run.republication_defects[0]).__name__
                return ProjectionFailure(
                    f"{exc}; rolled back completely but the restored pre-state "
                    f"cannot be re-published ({defect}); the defect pre-exists "
                    "this write",
                    rollback_complete=True,
                    pre_existing_defect=True,
                )
            return ProjectionFailure(str(exc), rollback_complete=True)
        if rollback_failures:
            return TransactionRollbackIncomplete(
                f"{exc}; rollback incomplete for: {', '.join(rollback_failures)}"
            )
        if run.republication_defects:
            defect = type(run.republication_defects[0]).__name__
            return TransactionFailure(
                f"{exc}; rolled back completely but the restored pre-state "
                f"cannot be re-published ({defect}); the defect pre-exists "
                "this write",
                pre_existing_defect=True,
            )
        if isinstance(exc, TransactionFailure):
            return None
        return TransactionFailure(str(exc))
