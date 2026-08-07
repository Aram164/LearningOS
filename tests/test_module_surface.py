"""Guards for the package splits.

A mechanical split moves definitions between files. Anything it silently
fails to move becomes a `NameError` on whatever code path happens to use it —
which the suite will not catch unless that path is covered. `DEFAULT_ADAPTERS`
was lost exactly this way: it survived `pytest`, `validate.py` and byte-identical
generated output, and only surfaced when the adapter registry fell back to its
defaults because no adapters file existed.

These tests assert two cheap invariants instead: nothing in the package refers
to a name that does not exist, and the public re-export surfaces resolve.
"""

from __future__ import annotations

import ast
import importlib
import pkgutil
from pathlib import Path

import pytest

PACKAGES = [
    "learning_os.ai_actions",
    "learning_os.commands",
    "learning_os.genout",
    "learning_os.rules",
    "materials_index",
]


def _modules(package_name: str):
    package = importlib.import_module(package_name)
    yield package
    for info in pkgutil.iter_modules(package.__path__):
        yield importlib.import_module(f"{package_name}.{info.name}")


@pytest.mark.parametrize("package_name", PACKAGES)
def test_every_public_name_resolves(package_name: str):
    """__all__ must not promise a name the package cannot produce."""
    package = importlib.import_module(package_name)
    for name in getattr(package, "__all__", []):
        assert hasattr(package, name), f"{package_name}.__all__ promises missing {name}"


@pytest.mark.parametrize("package_name", PACKAGES)
def test_no_module_references_an_undefined_global(package_name: str):
    """Catch a constant or helper the split failed to carry across.

    Compares the free variables of each module against what it defines,
    imports, or can reach as a builtin.
    """
    problems: list[str] = []
    for module in _modules(package_name):
        source_file = getattr(module, "__file__", None)
        if not source_file:
            continue
        tree = ast.parse(Path(source_file).read_text(encoding="utf-8"))
        defined = set(dir(module)) | set(dir(__builtins__)) | {"__file__", "__name__"}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                defined.add(node.name)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                defined.add(node.id)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                defined.add(node.target.id)
            elif isinstance(node, ast.arg):
                defined.add(node.arg)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    defined.add(alias.asname or alias.name.split(".")[0])
            elif isinstance(node, ast.ExceptHandler) and node.name:
                defined.add(node.name)
            elif isinstance(node, (ast.Global, ast.Nonlocal)):
                defined.update(node.names)
        # Names that look like module-level constants are the ones a split drops.
        for node in ast.walk(tree):
            if (isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
                    and node.id.isupper() and node.id not in defined):
                problems.append(f"{module.__name__}:{node.lineno} undefined {node.id}")
    assert not problems, "names a split failed to carry:\n  " + "\n  ".join(sorted(set(problems)))


def test_adapter_registry_falls_back_without_an_adapters_file(tmp_path: Path):
    """The exact path that lost DEFAULT_ADAPTERS."""
    from learning_os.ai_actions.registry import AdapterRegistry

    adapters = AdapterRegistry(tmp_path / "does-not-exist.yaml").list()
    assert [a.id for a in adapters] == ["manual-bundle"]
