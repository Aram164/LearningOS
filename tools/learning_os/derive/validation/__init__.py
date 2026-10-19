"""Validation rules for Learning OS v3 (BUILD-SPEC Step 4).

Split from a single 1,403-line module. The public surface is unchanged:
callers import `validate` and `render_report` from `learning_os.derive.validation`.
"""

from __future__ import annotations

from learning_os.derive.validation.core import Validator, render_report, validate
from learning_os.domain.validation import Issue

__all__ = ["Issue", "Validator", "render_report", "validate"]
