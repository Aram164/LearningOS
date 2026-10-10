"""LearningOS vNext comparison, archive, planning, backup, and health commands."""

from __future__ import annotations

import json

from learning_os.ops._legacy_plumbing import (
    _input_record_values,
)


def _input_record(args, label: str) -> dict:
    return _input_record_values(
        getattr(args, "record", None), getattr(args, "file", None), label)


def _refuse_without_approval(args, label: str) -> int | None:
    if getattr(args, "approve", False):
        return None
    print(json.dumps({"ok": False, "error": f"{label} requires explicit approval"}))
    return 2


