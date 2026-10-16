"""Transaction proposals and handler results (PLAN D4)."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from learning_os.store.contracts.gateway import GatewayRequestContext

JsonFormat = Literal[
    "ascii", "compact", "indented", "indented_sorted", "layout_sorted",
    "sorted", "unescaped",
]


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
class CommandOutput:
    """A raw child-process result for the CLI to pass through (SPEC (cx) D-9).

    Frozen: the stdout, stderr and exit code travel verbatim from the
    process to the adapter. Consumed only by the CLI pipeline through
    ``Result.command_output``; never composed with a proposal, a
    finish/render callback, a gesture or a diagnostic-failed result,
    and refused on the gateway path.
    """

    stdout: str
    stderr: str
    exit_code: int


@dataclass(frozen=True)
class Result:
    """What a registered handler returns (SPEC §11.1)."""

    payload: dict
    proposal: TransactionProposal | None = None
    finish: Callable[[dict], dict] | None = None  # receives the confirmation dict; default {**payload, **confirmation}
    on_commit_refused: Callable[[list[str]], list[str]] | None = None  # stderr lines for commit refusals
    diagnostic_failed: bool = False                # exit 1, a result rather than a refusal
    after_commit: Callable[[int, list, dict], None] | Literal["STANDARD"] | None = None   # recipes R4/R8: a callable may raise a typed refusal; "STANDARD" is the shared legacy raise
    json_format: JsonFormat | None = None
    refused_stdout: Callable[[list[str]], str] | None = None  # SPEC (bd): the legacy refusal print to stdout, without its newline
    human_view: dict | None = None  # SPEC (bu) 1: render-only data for the human renderer; --json ignores it
    notices: tuple[str, ...] = ()  # SPEC (bx) 2: success-path stderr lines; the CLI writes them verbatim, the gateway ignores them
    gesture: GatewayRequestContext | None = None  # SPEC (br) R7: a terminal direct-user-gesture write; the pipeline commits inside this context
    command_output: CommandOutput | None = None  # SPEC (cx) D-9: a raw child-process result; CLI-only, composes with nothing
