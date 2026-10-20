#!/usr/bin/env python3
"""Run every canvas suite and print the scoreboard.

    ./run-all.sh

Each suite builds its own synthetic worlds under `../worlds/<name>/` and
writes its reports to `../reports/<suite>/`. Nothing outside the canvas
directory is written to.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PYTHON = HERE.parent / "LearningOS" / "repository" / ".venv" / "bin" / "python"

SUITES = [
    ("T01", "t01_entry_points.py", "Operator entry points"),
    ("T02", "t02_filing_journey.py", "The operator's filing journey"),
    ("T03", "t03_adversarial.py", "Adversarial probes"),
    ("T04", "t04_consumption_seam.py", "The consumption seam"),
    ("T05", "t05_masters_promotion.py", "Workflow 27: the Master's promotion"),
    ("T06", "t06_term_boundary.py", "Workflow 24: turning the semester"),
    ("T07", "t07_ui_consumes_canvas.py", "The UI consuming a canvas world"),
]


def main() -> int:
    results = []
    for label, script, title in SUITES:
        print(f"\n{'=' * 70}\n{label} — {title}\n{'=' * 70}")
        proc = subprocess.run([str(PYTHON), script], cwd=str(HERE))
        results.append((label, title, proc.returncode))
    print(f"\n{'=' * 70}\nSCOREBOARD\n{'=' * 70}")
    for label, title, code in results:
        print(f"  {label}  {title:<36} {'ok' if code == 0 else 'FAILED'}")
    return 0 if all(code == 0 for _, _, code in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
