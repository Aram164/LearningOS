"""Strict coverage cannot silently omit a newly introduced production module."""

from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_new_production_modules_have_strict_coverage():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())["tool"]["mypy"]
    assert config["strict"] is True
    assert config["follow_imports"] != "skip", "typed imports must keep their actual types"
    legacy = set(json.loads((ROOT / "tests/architecture/typecheck-legacy.json").read_text())["modules"])
    current = {path.relative_to(ROOT).as_posix()
               for path in (ROOT / "tools/learning_os").rglob("*.py")}
    checked = set(config["files"])
    assert not checked - current, f"stale strict modules: {sorted(checked - current)}"
    assert not current - legacy - checked, f"new modules missing strict coverage: {sorted(current - legacy - checked)}"


def test_strict_gate_rejects_incorrect_boundary_alternatives(tmp_path):
    source = tmp_path / "bad_boundary.py"
    source.write_text(
        "from learning_os.domain.transaction import TransactionResult\n"
        "def boundary() -> TransactionResult:\n"
        "    return {'transaction_id': 'looks-similar'}\n")
    proc = subprocess.run([sys.executable, "-m", "mypy", "--no-incremental", str(source)],
                          cwd=ROOT, text=True, capture_output=True)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "return-value" in proc.stdout, proc.stdout


def test_system_gate_runs_maintained_types():
    source = (ROOT / "Makefile").read_text()
    assert "typecheck:\n\t$(PY) -m mypy" in source
    assert "$(MAKE) typecheck" in source.split("system-check:", 1)[1].split("\n#", 1)[0]
