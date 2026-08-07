"""Validation rules for Learning OS v3 (BUILD-SPEC Step 4).

Split from a single 1,403-line module. The public surface is unchanged:
callers import `validate` and `render_report` from `learning_os.rules`.
"""

from __future__ import annotations

from .common import Issue
from .core import Validator, render_report, validate

__all__ = ["Issue", "Validator", "render_report", "validate"]
