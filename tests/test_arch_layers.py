"""A1 layers point down (PLAN D17): the import-linter contracts hold."""

from __future__ import annotations

import ast
import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"

FIX = "Move the import below the importer's layer, or split the module (PLAN D17)."


def _imports_mechanical_helper(source: str, package: str = "learning_os.app.handlers") -> bool:
    helper = "learning_os.store.durable_fs"
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import) and any(alias.name == helper for alias in node.names):
            return True
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                module = importlib.util.resolve_name("." * node.level + module, package)
            if module == helper:
                return True
            if module == "learning_os.store" and any(
                    alias.name == "durable_fs" for alias in node.names):
                return True
    return False


def test_mechanical_helper_has_one_production_importer():
    allowed = {"tools/learning_os/store/transactions.py", "tools/learning_os/store/durable_fs.py"}
    for path in (ROOT / "tools/learning_os").rglob("*.py"):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in allowed:
            package = ".".join(path.relative_to(ROOT / "tools").parts[:-1])
            assert not _imports_mechanical_helper(path.read_text(), package), f"protected helper imported by {relative}"


def test_mechanical_helper_protection_detects_all_import_forms():
    for source in (
        "import learning_os.store.durable_fs as fs",
        "from learning_os.store import durable_fs as fs",
        "from learning_os.store.durable_fs import replace_bytes",
        "from ...store.durable_fs import replace_bytes",
        "from ...store import durable_fs",
    ):
        assert _imports_mechanical_helper(source)


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
