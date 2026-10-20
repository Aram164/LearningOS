"""Run the canvas's F-01 scope probe against a Core checkout of our choosing.

The canvas keeps its own clone of Core and points every probe at it. This
runner borrows the canvas's probe unchanged and points it at another
checkout, so the acceptance criterion can be measured against the branch
under review without mutating the canvas.

Usage:  .venv/bin/python <this file> <core checkout>
"""

from __future__ import annotations

import sys
from pathlib import Path

CANVAS = Path.home() / "los-canvas" / "canvas"
sys.path.insert(0, str(CANVAS / "lib"))

import canvaslib as C  # noqa: E402

core = Path(sys.argv[1]).resolve()
C.CORE_CLONE = core
C.LOS = core / "tools" / "los.py"
C.VENV_PY = core / ".venv" / "bin" / "python"
C.TESTS_DIR = core / "tests"

# The probe, verbatim from the canvas.
probe = (CANVAS / "probes" / "probe_scope_gap.py").read_text(encoding="utf-8")
probe = probe.replace('sys.path.insert(0, "lib")', "pass")
namespace = {"__name__": "__main__", "Path": Path}
exec(compile(probe, "probe_scope_gap.py", "exec"), namespace)
