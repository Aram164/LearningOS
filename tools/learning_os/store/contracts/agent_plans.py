"""Strict loading/validation helpers for agent-plan controls (D12)."""
from __future__ import annotations

import math


def parse_controls(plan: dict[str, object]) -> dict[str, object]:
    """Validate optional plan controls; reject bools/nonfinite/misspellings."""
    allowed = {"steps", "session_id", "on_error", "schema_version",
               "read_workers", "deadline_s", "report_max_bytes", "snapshot"}
    unknown = set(plan) - allowed
    # Per-step fields are validated by the runner; only plan-level unknowns
    # that look like misspelled controls are refused here by caller.
    workers = plan.get("read_workers", 1)
    if isinstance(workers, bool) or not isinstance(workers, int) or not 1 <= workers <= 4:
        raise ValueError("read_workers must be an integer 1..4")
    deadline = plan.get("deadline_s", 120)
    if isinstance(deadline, bool) or not isinstance(deadline, (int, float)) \
            or not math.isfinite(deadline) or deadline <= 0:
        raise ValueError("deadline_s must be a finite positive number")
    budget = plan.get("report_max_bytes", 65536)
    if isinstance(budget, bool) or not isinstance(budget, int) or budget < 1024:
        raise ValueError("report_max_bytes must be an integer >= 1024")
    version = plan.get("schema_version", 1)
    if isinstance(version, bool) or not isinstance(version, int) or version not in (1, 2, 3):
        raise ValueError("unsupported plan schema_version")
    snapshot = plan.get("snapshot")
    if snapshot is not None and snapshot != "one":
        raise ValueError('snapshot must be the string "one"')
    return {"read_workers": workers, "deadline_s": float(deadline),
            "report_max_bytes": budget, "unknown_plan_fields": sorted(unknown)}
