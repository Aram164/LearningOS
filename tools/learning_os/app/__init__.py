"""Ops layer (PLAN D17)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Static edge for reachability analysis (ai_actions precedent): the
    # pipeline wiring that imports these modules is pending (S13 REPORT).
    from learning_os.app import context as context
    from learning_os.app import proposal as proposal
    from learning_os.app import registry as registry
