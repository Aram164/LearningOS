"""The operation registry (PLAN D4)."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from learning_os.app.context import OpContext
from learning_os.app.proposal import Result
from learning_os.domain.agent_bindings import OutputSlot


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
    # Core declares a mode of this operation that only reads; a plan can never
    # claim this. The registered effect stays authoritative for every mode.
    read_when: Callable[[object], bool] | None = None
    # Binding surface (D3, D5): declared output slots are the only binding
    # sources; binding_params declares target params beyond x-los-id-kind.
    # An operation with no slots can never be a binding source.
    output_slots: Mapping[str, OutputSlot] = field(default_factory=dict)
    binding_params: Mapping[str, str] = field(default_factory=dict)


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
    read_when: Callable[[object], bool] | None = None,
    output_slots: Mapping[str, OutputSlot] | None = None,
    binding_params: Mapping[str, str] | None = None,
):
    """Register ``fn`` under ``name``; returns ``fn`` unchanged (stackable)."""

    def decorator(fn):
        REGISTRY[name] = Operation(
            name=name, kind=kind, handler=fn,
            human=human, render_check=render_check,
            parallel_safe=parallel_safe, memo_profile=memo_profile,
            read_session_profile=read_session_profile,
            effects=OperationEffects(effects), read_when=read_when,
            output_slots=output_slots or {}, binding_params=binding_params or {},
        )
        return fn

    return decorator
