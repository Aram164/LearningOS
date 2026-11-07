"""Pytest plugin to swap in the SQLite-backed reference validator for test execution.

Use:
    PYTHONPATH="tools:workbench/spikes/validation-sqlite-2026-11-07" \
        .venv/bin/pytest -p spike_validation_swap tests/test_validation.py ...

Loaded before test collection, rebinding learning_os.derive.validation.references
to spike_references_sqlite. Production files remain untouched.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SPIKE_DIR = Path(__file__).resolve().parent
_REPO = _SPIKE_DIR.parents[2]
for _p in (str(_REPO / "tools"), str(_SPIKE_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import spike_references_sqlite as spike_references  # noqa: E402

sys.modules["learning_os.derive.validation.references"] = spike_references
try:
    import learning_os.derive.validation as _pkg  # noqa: E402
    if hasattr(_pkg, "references"):
        _pkg.references = spike_references
except Exception:
    pass
