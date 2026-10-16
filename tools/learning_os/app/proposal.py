"""Transaction proposals and handler results (PLAN D4)."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from learning_os.domain.failures import WriteRefused
from learning_os.store.contracts.gateway import GatewayRequestContext


class CommitIssues(list):
    """Human-readable validation issues plus structured refusal facts."""
    def __init__(self, issues=(), *, details=None):
        super().__init__(issues)
        self.details = dict(details or {})


@dataclass(frozen=True)
class DeliveryCompletion:
    service: Any
    touched_base: Any


@dataclass(frozen=True)
class InboxCompletion:
    inbox: Path
    target: Path


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
    completion: DeliveryCompletion | InboxCompletion | None = None
    refusal: tuple[list, WriteRefused] | None = None
    translate: Callable[[BaseException], BaseException | None] | None = None
    # The call site's own except-chain around commit; the pipeline raises the
    # translation `from` the original, or re-raises the original when None.


@dataclass(frozen=True)
class GatewayDispatch:
    """An already reviewed, guard-bound envelope for the shared pipeline."""
    envelope: dict


class ResponsePayload(dict):
    """Prepared check data and a declarative success projection."""

    def __init__(self, prepared: dict, success: dict | None = None,
                 *, confirmation: str = "merge"):
        super().__init__(prepared)
        self.prepared = prepared
        if confirmation not in ("merge", "prepend", "omit", "delivery"):
            raise ValueError(f"unknown confirmation projection: {confirmation}")
        self.success = dict(prepared if success is None else success)
        self.confirmation = confirmation


@dataclass(frozen=True)
class Presentation:
    view: dict | None = None
    notices: tuple[str, ...] = ()


@dataclass(frozen=True)
class Result:
    """What a registered handler returns (SPEC §11.1)."""

    payload: dict | GatewayDispatch
    proposal: TransactionProposal | None = None
    diagnostic_failed: bool = False                # exit 1, a result rather than a refusal
    human_view: dict | Presentation | None = None  # SPEC (bu) 1: render-only data for the human renderer; --json ignores it
    gesture: GatewayRequestContext | None = None  # SPEC (br) R7: a terminal direct-user-gesture write; the pipeline commits inside this context
