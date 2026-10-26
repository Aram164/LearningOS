"""Application orchestration facade for agent plans (D01/D02).

Scheduling, deadline and stop/continue policy live in the runner adapter
today; this service owns the policy values so adapters stay thin. The
executor port is a callable ``(argv, root) -> (code, stdout, stderr)``.
"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

Executor = Callable[[list[str], Path], tuple[int, str, str]]

from learning_os.domain.agent_plans import PlanControls  # noqa: E402

DEFAULT_CONTROLS = PlanControls()
