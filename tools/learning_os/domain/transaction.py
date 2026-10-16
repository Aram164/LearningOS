"""Transaction result values shared by writers and replay readers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


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
