"""Ops layer (PLAN D17)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Static edge for reachability analysis (ai_actions precedent): the
    # pipeline wiring that imports these modules is pending (S13 REPORT).
    from . import context as context
    from . import proposal as proposal
    from . import registry as registry
