"""Immutable application plan requests and the adapter execution port."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import NotRequired, Protocol, TypedDict

from learning_os.domain.codes import INVALID_REQUEST


class PlanStepError(Exception):
    def __init__(self, message: str, code: str = INVALID_REQUEST) -> None:
        super().__init__(message)
        self.code = code


class SummarySpec(TypedDict, total=False):
    fields: list[str]
    max_items: int
    max_bytes: int


class PlanStep(TypedDict, total=False):
    id: str
    kind: str
    depends_on: list[str]
    use: str
    argv: list[str]
    args: list[str]
    writes: list[str]
    ready_timeout_s: float
    summary: SummarySpec
    key: str
    text: str
    unit_id: str
    stage_id: str
    describe: bool
    write: bool
    preflight: bool
    clusters: bool


class PlanInput(TypedDict):
    steps: list[PlanStep]
    schema_version: NotRequired[int]
    session_id: NotRequired[str]
    on_error: NotRequired[str]
    read_workers: NotRequired[int]
    deadline_s: NotRequired[float]
    report_max_bytes: NotRequired[int]


class PlanIndex(TypedDict):
    verbs: list[str]
    verb_to_operation: dict[str, str | None]
    task_to_use: dict[str, str]
    write_verbs: NotRequired[list[str]]


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
    ready_timeout_s: float = 10.0
    preflight: bool = False
    scope: tuple[str, ...] = ()
    presentation: PlanStep | None = None
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
    def preflight(self, step: CompiledStep) -> dict[str, object] | None: ...
    def summarize(self, step: CompiledStep, payload: object) -> str: ...
    def ready(self, required: list[object], known: list[object],
              submitting: bool) -> tuple[bool, str]: ...
    def epoch(self, root: Path) -> bool: ...
    def resources(self) -> dict[str, int]: ...
