"""Immutable application plan requests and the adapter execution port."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

COMMIT_NONE = "none"
COMMIT_COMMITTED = "committed"
COMMIT_UNCERTAIN = "uncertain"


@dataclass(frozen=True)
class PlanControls:
    read_workers: int = 1
    deadline_s: float = 120.0
    report_max_bytes: int = 65536
    on_error: str = "stop"
    session_id: str | None = None


@dataclass(frozen=True)
class CompiledStep:
    id: str
    argv: tuple[str, ...]
    dependencies: tuple[str, ...] = ()
    writer: bool = False
    submitting: bool = False
    reusable: bool = False
    parallel_safe: bool = False
    ready_timeout_s: float = 10.0
    preflight: bool = False
    scope: tuple[str, ...] = ()
    bindings: tuple = ()
    presentation: object = None
    admission_error: dict[str, object] | None = None


@dataclass(frozen=True)
class RawOutcome:
    code: int
    stdout: str
    stderr: str
    processes: int = 0
    elapsed_ms: int | None = None


class Executor(Protocol):
    def execute(self, step: CompiledStep, remaining: float) -> RawOutcome: ...
    def parallel(self, steps: list[CompiledStep], workers: int,
                 remaining: float) -> list[RawOutcome]: ...
    def preflight(self, step: CompiledStep) -> dict[str, object] | None: ...
    def summarize(self, step: CompiledStep, payload: object) -> str: ...
    def ready(self, required: list[object], known: list[object],
              submitting: bool) -> tuple[bool, str]: ...
    def epoch(self, root: Path) -> bool: ...
    def resources(self) -> dict[str, int]: ...
    def validate_bound(self, step: CompiledStep) -> None: ...


# Backward-compatible value retained for existing importers.
@dataclass(frozen=True)
class StepOutcome:
    step_id: str
    status: str
    exit_code: int | None = None
    error_code: str | None = None
    retryable: bool = False
    commit_certainty: str = COMMIT_NONE
    receipt_path: str | None = None
    raw_bytes: int = 0
    out_bytes: int = 0
    ms: int = 0
    ready_wait_ms: int = 0
