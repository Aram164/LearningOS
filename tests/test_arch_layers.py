"""A1 layers point down (PLAN D17): the import-linter contracts hold."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"

FIX = "Move the import below the importer's layer, or split the module (PLAN D17)."


def test_layer_contracts_hold():
    lint_imports = Path(sys.executable).parent / "lint-imports"
    # --no-cache: the graph cache would otherwise land in the tree as
    # .import_linter_cache/, which the tree contract forbids. The check
    # result is identical; only the speed differs.
    proc = subprocess.run(
        [str(lint_imports), "--no-cache"],
        cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode == 0, (
        f"A1: import-linter contracts broken "
        f"(baseline: {PYPROJECT.relative_to(ROOT).as_posix()}) — {FIX}\n"
        f"{proc.stdout}\n{proc.stderr}")
