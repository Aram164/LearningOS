"""Typed agent-plan values (D01/D13). No filesystem or parser imports."""
from __future__ import annotations

from dataclasses import dataclass

COMMIT_NONE = "none"
COMMIT_COMMITTED = "committed"
COMMIT_UNCERTAIN = "uncertain"


@dataclass(frozen=True)
class StepOutcome:
    step_id: str
    status: str  # ok | error | blocked | not_ready | skipped | deadline
    exit_code: int | None = None
    error_code: str | None = None
    retryable: bool = False
    commit_certainty: str = COMMIT_NONE
    receipt_path: str | None = None
    raw_bytes: int = 0
    out_bytes: int = 0
    ms: int = 0
    ready_wait_ms: int = 0


@dataclass(frozen=True)
class PlanControls:
    read_workers: int = 1
    deadline_s: float = 120.0
    report_max_bytes: int = 65536
    on_error: str = "stop"
    session_id: str | None = None
