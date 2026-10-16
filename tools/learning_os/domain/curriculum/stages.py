"""Stage and learning-path state machines: one status action applied in place.

Pure rules over loaded records. Callers refuse invalid actions first; these
functions assume a valid action and receive the clock as a callable, so the
clock is read exactly where the rule needs a date.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable

STAGE_ACTIONS = ("active", "paused", "complete", "skipped", "revisit")
PATH_ACTIONS = ("active", "complete", "skipped")


def apply_stage_action(data: dict, unit_data: dict, stage: dict, action: str,
                       today: Callable[[], dt.date]) -> None:
    """Move ``stage`` (one of ``data["stages"]``) by ``action``; update map and unit status."""
    stages = data.get("stages", []) or []
    if action in {"active", "revisit"}:
        for other in stages:
            if other.get("status") in {"active", "paused"}:
                other["status"] = "pending"
        stage["status"] = "active"
        stage.pop("completed", None)
        data["current_stage"] = stage["id"]
        data["status"] = "active"
        unit_data["status"] = "active"
    elif action == "paused":
        stage["status"] = "paused"
        data["current_stage"] = stage["id"]
        data["status"] = "paused"
        unit_data["status"] = "paused"
    else:
        stage["status"] = action
        if action == "complete":
            stage["completed"] = today().isoformat()
        following = next((row for row in stages[stages.index(stage) + 1:]
                          if row.get("status") == "pending"), None)
        if following:
            following["status"] = "active"
            data["current_stage"] = following["id"]
            data["status"] = "active"
            unit_data["status"] = "active"
        else:
            data["status"] = "ready-to-shelve"
            data.setdefault("shelving", {})["state"] = "draft"
            unit_data["status"] = "ready-to-shelve"


def apply_path_action(data: dict, stage: dict, action: str,
                      today: Callable[[], dt.date]) -> None:
    """Move a learning-path ``stage`` by ``action`` (active, complete or skipped)."""
    stages = data.get("stages", []) or []
    if action == "active":
        for other in stages:
            if other.get("status") == "active":
                other["status"] = "pending"
        stage["status"] = "active"
        stage.pop("completed", None)
        data["current_stage"] = stage["id"]
        data["status"] = "active"
    else:
        stage["status"] = action
        if action == "complete":
            stage["completed"] = today().isoformat()
        following = next((s for s in stages[stages.index(stage) + 1:]
                          if s.get("status") == "pending"), None)
        if following:
            following["status"] = "active"
            data["current_stage"] = following["id"]
            data["status"] = "active"
        else:
            data["status"] = "ready-to-shelve"
            shelving = data.setdefault("shelving", {})
            shelving["state"] = "draft"


def progress_entry(summary: str, upcoming: str | None,
                   today: Callable[[], dt.date]) -> dict:
    """The progress record for a validated summary and optional next step."""
    entry = {"updated": today().isoformat(), "summary": summary.strip()}
    if upcoming is not None:
        entry["next"] = upcoming.strip()
    return entry
