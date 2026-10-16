"""The operation registry (PLAN D4)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from learning_os.ops.context import OpContext
from learning_os.ops.proposal import JsonFormat, Result


@dataclass(frozen=True)
class Operation:
    name: str
    kind: str                          # query | command | porcelain
    handler: Callable[[OpContext, dict], Result]
    # Renders the human default output; None = JSON default. One argument
    # (payload), or two (payload, human_view) when the Result sets one (SPEC (bu) 1).
    human: Callable[[dict], str] | Callable[[dict, dict], str] | None = None
    render_check: Callable[[dict, dict], dict] | None = None  # (check record, prepared Result.payload)
    json_formats: tuple[JsonFormat, ...] = ()


REGISTRY: dict[str, Operation] = {}


def register(
    name: str,
    *,
    kind: str,
    human: Callable[[dict], str] | Callable[[dict, dict], str] | None = None,
    render_check: Callable[[dict, dict], dict] | None = None,
    json_formats: tuple[JsonFormat, ...] = (),
):
    """Register ``fn`` under ``name``; returns ``fn`` unchanged (stackable)."""

    def decorator(fn):
        REGISTRY[name] = Operation(
            name=name, kind=kind, handler=fn,
            human=human, render_check=render_check,
            json_formats=json_formats,
        )
        return fn

    return decorator
