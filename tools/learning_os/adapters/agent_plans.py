"""Adapter composition for agent plans: parser/catalogue compilation lives
in tools/agent_run.py, which delegates policy to app modules (D02)."""
from __future__ import annotations

from learning_os.app.agent_plans import Executor  # noqa: F401
