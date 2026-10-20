"""Run the canvas's F-01 scope probe against a Core checkout of our choosing.

The canvas keeps its own clone of Core and points every probe at it. This
runner borrows the canvas's probe unchanged and points it at another
checkout, so the acceptance criterion can be measured against the branch
under review without mutating the canvas.

Usage:  .venv/bin/python <this file> <core checkout> [canvas dir]

The canvas directory defaults to the checkout this repository publishes
(``los-canvas/`` at the repository root) and then to the working copies
left on the machine; the probe itself is read from there, unchanged.
"""

from __future__ import annotations

import sys
from pathlib import Path


def canvas_dir() -> Path:
    """Where the harness lives: beside this checkout, or where it was left."""
    here = Path(__file__).resolve()
    for candidate in here.parents:
        published = candidate / "los-canvas" / "canvas"
        if published.is_dir():
            return published
    for candidate in (Path.home() / "los-canvas" / "canvas",
                      Path.home() / "los-canvas-fixed" / "canvas"):
        if candidate.is_dir():
            return candidate
    raise SystemExit("canvas directory not found — pass it as the second argument")


CANVAS = canvas_dir()
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
