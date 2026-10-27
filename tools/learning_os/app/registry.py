"""The operation registry (PLAN D4)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from learning_os.app.context import OpContext
from learning_os.app.proposal import Result


class OperationEffects(StrEnum):
    READ = "read"
    DERIVED_WRITE = "derived-write"
    CANONICAL_WRITE = "canonical-write"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Operation:
    name: str
    kind: str                          # query | command | porcelain | tool
    handler: Callable[[OpContext, dict], Result]
    # Renders the human default output; None = JSON default. One argument
    # (payload), or two (payload, human_view) when the Result sets one (SPEC (bu) 1).
    human: Callable[[dict], str] | Callable[[dict, dict], str] | None = None
    render_check: Callable[[dict, dict], dict] | None = None  # (check record, prepared Result.payload)
    # Execution traits (D05): conservative defaults; a query kind alone does
    # not prove purity. Traits describe execution, never write authority.
    parallel_safe: bool = False
    memo_profile: str = "none"
    read_session_profile: str = "none"
    # Invocation kind controls dispatch/locking, not effects. A new operation
    # is a write barrier until its owner explicitly declares a read.
    effects: OperationEffects = OperationEffects.UNKNOWN


REGISTRY: dict[str, Operation] = {}


def register(
    name: str,
    *,
    kind: str,
    human: Callable[[dict], str] | Callable[[dict, dict], str] | None = None,
    render_check: Callable[[dict, dict], dict] | None = None,
    parallel_safe: bool = False,
    memo_profile: str = "none",
    read_session_profile: str = "none",
    effects: OperationEffects = OperationEffects.UNKNOWN,
):
    """Register ``fn`` under ``name``; returns ``fn`` unchanged (stackable)."""

    def decorator(fn):
        REGISTRY[name] = Operation(
            name=name, kind=kind, handler=fn,
            human=human, render_check=render_check,
            parallel_safe=parallel_safe, memo_profile=memo_profile,
            read_session_profile=read_session_profile,
            effects=OperationEffects(effects),
        )
        return fn

    return decorator
