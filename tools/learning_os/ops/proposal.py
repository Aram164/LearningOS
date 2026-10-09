"""Transaction proposals and handler results (PLAN D4)."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class TransactionProposal:
    """Every input of one ``TransactionService.commit`` call (SPEC §11.1)."""

    capability: str
    writes: Mapping[Path, str | bytes]
    artifact_ids: tuple[str, ...]
    deletes: tuple[Path, ...] | None = ()
    expected_revisions: Mapping[str, int] = field(default_factory=dict)
    metadata: Mapping | None = None
    write_authorities: Mapping[Path, str] | None = None
    transaction_writes: Callable[[str], Mapping[Path, str | bytes]] | None = None
    validate_extra: Callable | None = None        # the _write_transaction validate_extra contract
    # Engine hooks (amendment (i), K9). STANDARD = the wiring
    # _write_transaction passes today; None = not passed, exactly as a call
    # site that omits it today; a callable = that call site's own hook.
    validate_state: Callable | None | Literal["STANDARD"] = "STANDARD"
    publish: Callable | None | Literal["STANDARD"] = "STANDARD"
    rollback_publish: Callable | None | Literal["STANDARD"] = "STANDARD"
    touched: Callable | None | Literal["STANDARD"] = "STANDARD"
    clock: Callable | None = None                 # a call site's own TransactionService clock, else the default
    expected_snapshot: str | None = None        # None omits the engine kwarg (standard shapes); AI carries its explicit token
    translate: Callable[[BaseException], BaseException | None] | None = None
    # The call site's own except-chain around commit; the pipeline raises the
    # translation `from` the original, or re-raises the original when None.


@dataclass(frozen=True)
class Result:
    """What a registered handler returns (SPEC §11.1)."""

    payload: dict
    proposal: TransactionProposal | None = None
    finish: Callable[[dict], dict] | None = None  # receives the confirmation dict; default {**payload, **confirmation}
    on_commit_refused: Callable[[list[str]], list[str]] | None = None  # stderr lines for commit refusals
    diagnostic_failed: bool = False                # exit 1, a result rather than a refusal
    after_commit: Callable[[int, list, dict], None] | None = None   # recipe R4: may raise a typed refusal
