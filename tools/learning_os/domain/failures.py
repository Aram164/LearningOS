"""Typed failures shared across Core layers (SPEC §8.3).

Dependency-light exception types: leaf packages raise these errors without
importing the transaction engine. The public compatibility surface remains
``learning_os.store.transactions``; this module exists to keep projection,
validation and refusal code below orchestration in the dependency graph.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, Sequence
from itertools import tee
from pathlib import Path
from typing import NamedTuple

from learning_os.domain import suggest
from learning_os.domain.codes import (
    AMBIGUOUS_MIGRATION,
    IDEMPOTENCY_CONFLICT,
    INVALID_REQUEST,
    OUT_OF_SCOPE,
    REVISION_CONFLICT,
    STALE_SNAPSHOT,
    UNCONFIRMED,
    VALIDATION_FAILED,
)


class Refusal(NamedTuple):
    """One typed gateway refusal: its V2 code and whether it may retry.

    The narrow alternative to carrying a bare ``(code, retryable)`` pair
    or reconstructing one from prose: producers build this value, and
    exactly one mapping (``app/outcomes.py``) turns failure types into it.
    """

    code: str
    retryable: bool


class TransactionFailure(Exception):
    """A governed write failed and its canonical changes were rolled back.

    ``pre_existing_defect`` names the JF-11 case: canonical rollback
    completed but the restored pre-state itself refuses re-publication
    for a content reason, so the defect pre-exists the write. The
    gateway classifies on this flag, never on message prose.
    """

    def __init__(self, *args, pre_existing_defect: bool = False):
        super().__init__(*args)
        self.pre_existing_defect = pre_existing_defect


class ProjectionFailure(TransactionFailure):
    """The commit-time projection/publication step failed.

    Carries whether rollback completed, so the gateway classifies by
    subsystem outcome instead of matching exception prose. A complete
    rollback proves NOT_COMMITTED (PROJECTION_FAILED); an incomplete one
    leaves the outcome unknown (INTERNAL_FAILURE). When the restored
    pre-state itself refuses re-publication for a content (non-OSError)
    reason, the defect pre-exists the write: ``pre_existing_defect`` names
    that case so the gateway reports it like the shadow-validation
    refusal it is (VALIDATION_FAILED), not as an unknown outcome (JF-11).
    """

    def __init__(self, message: str, *, rollback_complete: bool,
                 pre_existing_defect: bool = False):
        super().__init__(message, pre_existing_defect=pre_existing_defect)
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


class TransactionPublicationUncertain(TransactionFailure):
    """The receipt may have been published but its durability is unproven.

    Raised when the operation that can expose the receipt fails after
    uncertainty was marked: the forward state and the recovery journal are
    preserved, because rolling back behind a possibly committed receipt
    would contradict evidence a later process can verify. The outcome is
    ambiguous — never a definitive refusal and never ``committed: true``
    without proof. Carries the transaction identity so the gateway can
    report it without asserting a durable receipt.
    """

    def __init__(self, message: str, *, transaction_id: str,
                 receipt_path: str):
        super().__init__(message)
        self.transaction_id = transaction_id
        self.receipt_path = receipt_path


class TransactionValidationFailure(TransactionFailure):
    """The staged write failed canonical validation; nothing was committed.

    Carries the refusal type so the gateway reports ``VALIDATION_FAILED``
    without reading the validator prose, which may quote canonical content
    or name snapshots, approvals, and other classifier lookalikes.
    """


class TransactionRollbackIncomplete(TransactionFailure):
    """A non-projection failure whose rollback did not complete.

    The repository may contain part of the attempted write, so the outcome
    is unknown and the gateway reports retryable ``INTERNAL_FAILURE``.
    Projection-stage failures use ``ProjectionFailure`` with
    ``rollback_complete=False`` instead; this names every other stage.
    """


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


class WriteRefused(Exception):
    """A canonical write could not be performed; nothing was changed."""

    #: The V2 error code this refusal carries, and whether the caller may
    #: retry the same approved intent. The gateway classifies by this type,
    #: never by message prose: refusals echo user input, and a mistyped id
    #: may name snapshots, approvals, or any other lookalike.
    gateway_code = INVALID_REQUEST
    gateway_retryable = False

    def __init__(self, *args, site: str | None = None,
                 reason: str | None = None, remedy: str | None = None,
                 gateway_message: str | None = None,
                 prefixed: bool = False,
                 exit_code: int | None = None,
                 extra_stderr: tuple[str, ...] = ()):
        if prefixed:
            if gateway_message is not None:
                raise TypeError(
                    "WriteRefused: prefixed and gateway_message are exclusive")
            if len(args) != 1:
                raise TypeError(
                    "WriteRefused: prefixed needs exactly one message argument")
            gateway_message = f"los: {args[0]}"
        super().__init__(*args)
        self.site = site
        self.reason = reason
        self.remedy = remedy
        self.gateway_message = gateway_message
        self.exit_code = exit_code
        self.extra_stderr = extra_stderr


class ToolFailure(WriteRefused):
    """An external tool failed; preserve its exit while adapters render once."""

    def __init__(self, stdout: str, stderr: str, exit_code: int):
        super().__init__(stderr.strip() or stdout.strip() or "external tool failed",
                         exit_code=exit_code)


class StaleSnapshot(WriteRefused):
    """A supplied concurrency token no longer matches live state; nothing was changed.

    The only refusal that maps to exit 3 (optimistic-concurrency conflict).
    Raised only where a supplied snapshot — or the material-context
    observations digest — differs from the live one. Never inferred from
    message prose: refusals echo user input, and the word "snapshot" in a
    mistyped id or a missing-flag hint is not a conflict.
    """

    gateway_code = STALE_SNAPSHOT
    gateway_retryable = True


class AmbiguousMigration(WriteRefused):
    """A migration plan is not applicable; nothing was changed.

    Raised only where a genuine migration plan refuses to apply — never
    for an ambiguous lookup, which is an invalid request, not a migration.
    """

    gateway_code = AMBIGUOUS_MIGRATION
    gateway_retryable = False


class ValidationFailed(WriteRefused):
    """A pre-transaction validation gate refused the write; nothing was changed."""

    gateway_code = VALIDATION_FAILED
    gateway_retryable = False


class Unconfirmed(WriteRefused):
    """The envelope's approval does not cover this write; nothing was changed."""

    gateway_code = UNCONFIRMED
    gateway_retryable = False


class RevisionConflict(WriteRefused):
    """An artifact revision guard no longer matches; nothing was changed."""

    gateway_code = REVISION_CONFLICT
    gateway_retryable = True


class OutOfScope(WriteRefused):
    """A planned write falls outside its capability's declared scope."""

    gateway_code = OUT_OF_SCOPE
    gateway_retryable = False


class IdempotencyConflict(WriteRefused):
    """The idempotency key already names a different request."""

    gateway_code = IDEMPOTENCY_CONFLICT
    gateway_retryable = False


class NotFound(WriteRefused):
    """A lookup value matched nothing; carries bounded suggestions."""

    gateway_code = INVALID_REQUEST
    gateway_retryable = False

    def __init__(self, kind: str, value: str, candidates: Iterable[str], *,
                 site: str | None = None,
                 gateway_message: str | None = None,
                 exit_code: int | None = None,
                 message: str | None = None):
        # Preserve the legacy helper's iterator behavior for the message,
        # while giving its structured suggestions an independent traversal.
        message_candidates, suggestion_candidates = (
            tee(candidates) if isinstance(candidates, Iterator)
            else (candidates, candidates))
        super().__init__(
            message if message is not None
            else suggest.not_found(kind, value, message_candidates),
            site=site, reason="NOT_FOUND",
            gateway_message=gateway_message, exit_code=exit_code)
        self.suggestions = suggest.suggestions(value, suggestion_candidates)


class MalformedId(WriteRefused):
    """An id value is not canonical for its kind."""

    def __init__(self, kind: str, value: object, *,
                 site: str | None = None,
                 gateway_message: str | None = None,
                 exit_code: int | None = None):
        super().__init__(f"malformed {kind} id: {value!r}", site=site,
                         reason="MALFORMED_ID",
                         gateway_message=gateway_message,
                         exit_code=exit_code)
        self.kind = kind
        self.value = value


class ReplayRecoveryError(Exception):
    """The committed receipt cannot prove what the original call wrote."""


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
