"""The operation registry (PLAN D4)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from learning_os.ops.context import OpContext
from learning_os.ops.proposal import Result


@dataclass(frozen=True)
class Operation:
    name: str
    kind: str                          # query | command | porcelain
    handler: Callable[[OpContext, dict], Result]
    human: Callable[[dict], str] | None = None     # renders the human default output; None = JSON default
    render_check: Callable[[dict, dict], dict] | None = None  # (check record, prepared Result.payload)


REGISTRY: dict[str, Operation] = {}


def register(
    name: str,
    *,
    kind: str,
    human: Callable[[dict], str] | None = None,
    render_check: Callable[[dict, dict], dict] | None = None,
):
    """Register ``fn`` under ``name``; returns ``fn`` unchanged (stackable)."""

    def decorator(fn):
        REGISTRY[name] = Operation(
            name=name, kind=kind, handler=fn,
            human=human, render_check=render_check,
        )
        return fn

    return decorator
