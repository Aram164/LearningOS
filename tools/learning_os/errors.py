"""Dependency-light exception types shared across Core layers.

Leaf packages may raise these errors without importing the transaction engine.
The public compatibility surface remains ``learning_os.transactions``; this
module exists to keep projection and validation code below orchestration in the
dependency graph.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path


class TransactionFailure(Exception):
    """A governed write failed and its canonical changes were rolled back."""


class ProjectionFailure(TransactionFailure):
    """The commit-time projection/publication step failed.

    Carries whether rollback completed, so the gateway classifies by
    subsystem outcome instead of matching exception prose. A complete
    rollback proves NOT_COMMITTED (PROJECTION_FAILED); an incomplete one
    leaves the outcome unknown (INTERNAL_FAILURE).
    """

    def __init__(self, message: str, *, rollback_complete: bool):
        super().__init__(message)
        self.rollback_complete = rollback_complete


class PostCommitFailure(TransactionFailure):
    """The receipt is durable but post-commit bookkeeping failed.

    The write committed; only session-ownership recording or inflight
    cleanup broke. Carries the receipt facts so the gateway can return
    them and an exact retry can replay the committed receipt. Must never
    be classified as a definitive refusal.
    """

    def __init__(self, message: str, *, transaction_id: str,
                 receipt_path: str, snapshot_after: str):
        super().__init__(message)
        self.transaction_id = transaction_id
        self.receipt_path = receipt_path
        self.snapshot_after = snapshot_after


class TransactionIdempotencyConflict(TransactionFailure):
    """An idempotency key was reused for a different approved intent."""


class ReplayEvidenceError(TransactionFailure):
    """A persisted success claim does not match its own recorded evidence.

    Raised by ``replay_for_request`` whenever the idempotency ledger row and
    its named receipt disagree, are malformed, or fail schema validation.
    Always non-retryable: the underlying write may or may not have happened,
    but the *evidence* is contradictory, so the only safe response is a
    refusal that preserves everything for manual reconciliation. The original
    capability handler must never run in response to this.
    """


class TransactionRecoveryConflict(TransactionFailure):
    """Crash recovery cannot prove a stale journal still owns its paths.

    Raised by ``reconcile_inflight_transactions`` when a previous run's
    rollback journal names paths whose live state is neither the crashed
    transaction's exact post-state nor its original pre-state — or when the
    commit receipt the journal points at is contradictory. Recovery may
    modify a path only while it can prove the path is still the crashed
    transaction's own; anything else is foreign state a later writer owns
    and must never be touched.

    Nothing conflicting is modified: the paths keep their bytes, the
    journal stays on disk for diagnosis, and the calling command stops.
    The operator reconciles by hand — inspect the journal, deliberately
    place every conflicting path, remove the stale journal directory once
    nothing unfinished remains — and re-runs. A restore interrupted
    halfway stays completable: already-restored paths read as pre-state,
    so the next run finishes them as no-ops and continues.

    Carries the transaction and the per-path conflicts structurally so the
    gateway can report them without quoting file contents. Reason codes:

    - ``DIVERGED_FROM_TRANSACTION``: live bytes match neither recorded side.
    - ``BACKUP_HASH_MISMATCH``: the journal's own backup blob disagrees
      with its recorded hash, or is missing.
    - ``UNEXPECTED_FILE_TYPE``: a symlink, directory, or other non-file
      stands where a regular file or absence was recorded. Never followed.
    - ``INVALID_COMMIT_RECEIPT``: a receipt exists at the journal's path
      but fails to parse, validate, or match the journal's transaction.
    - ``LEGACY_JOURNAL_UNPROVABLE``: a version-1 journal (no post-state
      hashes) names paths that cannot be proven already rolled back.
    - ``CORRUPT_JOURNAL``: the journal entry itself is malformed or names
      a path outside the repository.
    - ``UNREADABLE_JOURNAL``: the journal cannot be read at all.
    - ``UNSUPPORTED_JOURNAL_VERSION``: the journal declares a schema
      version recovery does not implement. Preserved, never reinterpreted.
    - ``RESTORE_IO_FAILED``: a proven-safe restore, projection discard, or
      journal cleanup could not be written.
    """

    def __init__(self, message: str, *, transaction_id: str,
                 conflicts: Sequence[Mapping[str, str]] = ()):
        super().__init__(message)
        self.transaction_id = transaction_id
        self.conflicts = [dict(entry) for entry in conflicts]


def unreadable_refusal(root: Path, failures: list[tuple[Path, str]], action: str) -> str:
    """Why a command will not answer, naming the files it could not read.

    A count is not a diagnosis. The operator's next move is to open the file
    that failed and repair its frontmatter, and they cannot find it from
    "3 records failed to parse" — so the refusal names the paths and what the
    loader actually said about each, the way every other refusal here does.
    """
    def where(path) -> str:
        try:
            return str(Path(path).relative_to(root))
        except (ValueError, TypeError):
            return str(path)

    shown = "; ".join(f"{where(path)}: {message}" for path, message in failures[:5])
    more = f"; and {len(failures) - 5} more" if len(failures) > 5 else ""
    return (f"cannot {action}: {len(failures)} file(s) could not be read, so the answer "
            f"would silently omit them — {shown}{more}")
