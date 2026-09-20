"""Dependency-light exception types shared across Core layers.

Leaf packages may raise these errors without importing the transaction engine.
The public compatibility surface remains ``learning_os.transactions``; this
module exists to keep projection and validation code below orchestration in the
dependency graph.
"""

from __future__ import annotations

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
