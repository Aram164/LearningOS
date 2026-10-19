"""Transaction result values shared by writers and replay readers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class PublicationState(Enum):
    """Where one transaction's receipt stands in its publication run.

    ``NOT_PUBLISHED``: the receipt cannot have been exposed yet, so an
    ownership-guarded rollback is still allowed. ``PUBLICATION_UNCERTAIN``:
    the operation that can expose the receipt has been entered but its
    persistence barrier has not returned, so the receipt may be visible
    without being proven durable — forward state and the journal must be
    preserved. ``DURABLE``: the barrier returned; the commit is proven and
    only post-commit bookkeeping can still fail.
    """

    NOT_PUBLISHED = "not_published"
    PUBLICATION_UNCERTAIN = "publication_uncertain"
    DURABLE = "durable"


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
