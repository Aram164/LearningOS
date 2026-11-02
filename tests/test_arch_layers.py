"""A1 layers point down (PLAN D17): the import-linter contracts hold."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"

FIX = "Move the import below the importer's layer, or split the module (PLAN D17)."


def _missing_declared_helpers(modules, tools_root: Path) -> list[str]:
    """Declared protected modules with no source file: a guard on them proves nothing."""
    return [module for module in modules
            if not (tools_root / (module.replace(".", "/") + ".py")).is_file()]


def test_declared_mechanical_helpers_exist():
    import arch_audit_hook
    owners = yaml.safe_load((ROOT / "tests/architecture/operational-owners.yaml").read_text())
    declared = [row["module"] for row in owners["io_helpers"]] + list(arch_audit_hook.MECHANICAL_HELPERS)
    assert _missing_declared_helpers(declared, ROOT / "tools") == []


def test_missing_declared_helper_is_detected():
    tools = ROOT / "tools"
    assert _missing_declared_helpers(["learning_os.store.transactions"], tools) == []
    assert _missing_declared_helpers(["learning_os.store.durable_fs"], tools) == ["learning_os.store.durable_fs"]


def _impure_derivation(source: str) -> list[str]:
    pure = {"collections", "dataclasses", "datetime", "enum", "functools", "hashlib",
            "json", "math", "re", "statistics", "string", "typing", "unicodedata", "__future__"}
    problems = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            modules = ([alias.name for alias in node.names] if isinstance(node, ast.Import)
                       else [node.module or ""])
            for module in modules:
                if module.split(".")[0] not in pure and not module.startswith("learning_os.domain"):
                    problems.append(module)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"open", "eval", "exec", "__import__"}:
                problems.append(node.func.id)
    return problems


def test_migrated_material_derivation_has_no_observation_access():
    for relative in ("tools/learning_os/derive/material_context.py", "tools/learning_os/domain/verbatim.py"):
        path = ROOT / relative
        if path.exists():
            assert not _impure_derivation(path.read_text()), relative


def test_impure_derivation_negative_controls():
    for source in ("import os", "from pathlib import Path", "import subprocess",
                   "import socket", "open('material.pdf')", "__import__('os')"):
        assert _impure_derivation(source), source


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
