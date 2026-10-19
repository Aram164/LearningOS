"""OD15 (Phase 6, 6.A.10): no private name crosses a module boundary.

A module's ``_name`` belongs to that module. Code under ``tools/`` may import
or address only another module's public names. A package-private module (such
as ``app/handlers/_shared.py``) is importable only from inside its own parent
package. Dunder protocol names (``__version__``) are not private. Tests are
out of scope: they may reach into a module to test it.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"

FIX = ("import the owner's public name (promote the helper at its owner, no "
       "wrapper), or keep the helper inside its module (PLAN OD15)")


def _private(name: str) -> bool:
    return name.startswith("_") and not (name.startswith("__") and name.endswith("__"))


def _modules(tools: Path) -> dict[str, Path]:
    found = {}
    for path in (tools / "learning_os").rglob("*.py"):
        parts = list(path.relative_to(tools).with_suffix("").parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
        found[".".join(parts)] = path
    return found


def _module_of(tools: Path, path: Path) -> tuple[str | None, bool]:
    if not path.is_relative_to(tools / "learning_os"):
        return None, False
    parts = list(path.relative_to(tools).with_suffix("").parts)
    is_package = parts[-1] == "__init__"
    return ".".join(parts[:-1] if is_package else parts), is_package


def _absolute(me: str | None, is_package: bool, node: ast.ImportFrom) -> str | None:
    if node.level == 0:
        return node.module
    if me is None:
        return None
    base = me.split(".") if is_package else me.split(".")[:-1]
    if node.level > 1:
        base = base[: len(base) - (node.level - 1)]
    return ".".join(base + ([node.module] if node.module else []))


def _inside(me: str | None, module: str) -> bool:
    """Whether ``me`` lies inside the parent package of each private segment."""
    parts = module.split(".")
    for index, part in enumerate(parts[1:], start=1):
        if _private(part):
            parent = ".".join(parts[:index])
            if me is None or not (me == parent or me.startswith(parent + ".")):
                return False
    return True


def _violations(tools: Path) -> list[str]:
    modules = _modules(tools)
    found = []
    for path in sorted(tools.rglob("*.py")):
        if ".venv" in path.parts or "__pycache__" in path.parts:
            continue
        rel = path.relative_to(tools.parent).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        me, is_package = _module_of(tools, path)
        aliases: dict[str, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    if not name.name.startswith("learning_os"):
                        continue
                    if not _inside(me, name.name):
                        found.append(f"{rel}:{node.lineno} imports private module {name.name}")
                    if name.asname:
                        aliases[name.asname] = name.name
            elif isinstance(node, ast.ImportFrom):
                source = _absolute(me, is_package, node)
                if not source or not source.startswith("learning_os"):
                    continue
                if not _inside(me, source):
                    found.append(f"{rel}:{node.lineno} imports from private module {source}")
                for name in node.names:
                    full = f"{source}.{name.name}"
                    if full in modules:
                        aliases[name.asname or name.name] = full
                        if not _inside(me, full):
                            found.append(f"{rel}:{node.lineno} imports private module {full}")
                    elif _private(name.name):
                        found.append(f"{rel}:{node.lineno} imports {name.name} from {source}")
        for node in ast.walk(tree):
            if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                    and node.value.id in aliases and _private(node.attr)
                    and aliases[node.value.id] != me):
                found.append(f"{rel}:{node.lineno} uses {node.value.id}.{node.attr}"
                             f" of {aliases[node.value.id]}")
    return found


def test_no_private_name_crosses_a_module_boundary():
    violations = _violations(TOOLS)
    assert violations == [], "OD15:\n" + "\n".join(violations) + f"\n— {FIX}"


# --- controls --------------------------------------------------------------------------


def _tree(tmp_path: Path, files: dict[str, str]) -> Path:
    tools = tmp_path / "tools"
    for rel, text in files.items():
        path = tools / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    for package in {p.parent for p in tools.rglob("*.py")}:
        if package != tools:
            (package / "__init__.py").touch()
    return tools


def test_control_private_import_is_flagged(tmp_path):
    tools = _tree(tmp_path, {
        "learning_os/a.py": "def _helper():\n    return 1\n",
        "learning_os/b.py": "from learning_os.a import _helper\n",
    })
    assert _violations(tools) == [
        "tools/learning_os/b.py:1 imports _helper from learning_os.a"]


def test_control_relative_private_import_is_flagged(tmp_path):
    tools = _tree(tmp_path, {
        "learning_os/pkg/a.py": "_LIMIT = 3\n",
        "learning_os/pkg/b.py": "from .a import _LIMIT\n",
    })
    assert _violations(tools) == [
        "tools/learning_os/pkg/b.py:1 imports _LIMIT from learning_os.pkg.a"]


def test_control_private_attribute_on_another_module_is_flagged(tmp_path):
    tools = _tree(tmp_path, {
        "learning_os/a.py": "def _helper():\n    return 1\n",
        "learning_os/b.py": "import learning_os.a as a\n\nVALUE = a._helper()\n",
        "script.py": "from learning_os import a\n\nprint(a._helper())\n",
    })
    assert _violations(tools) == [
        "tools/learning_os/b.py:3 uses a._helper of learning_os.a",
        "tools/script.py:3 uses a._helper of learning_os.a"]


def test_control_public_alias_to_a_local_private_name_passes(tmp_path):
    tools = _tree(tmp_path, {
        "learning_os/a.py": "def helper():\n    return 1\n",
        "learning_os/b.py": "from learning_os.a import helper as _helper\n",
    })
    assert _violations(tools) == []


def test_control_package_private_module_only_inside_its_package(tmp_path):
    tools = _tree(tmp_path, {
        "learning_os/app/handlers/_shared.py": "def render():\n    return 1\n",
        "learning_os/app/handlers/notes.py":
            "from learning_os.app.handlers._shared import render\n",
        "learning_os/derive/view.py":
            "from learning_os.app.handlers._shared import render\n",
    })
    assert _violations(tools) == [
        "tools/learning_os/derive/view.py:1 imports from private module"
        " learning_os.app.handlers._shared"]


def test_control_dunder_names_are_not_private(tmp_path):
    tools = _tree(tmp_path, {
        "learning_os/__init__.py": "__version__ = '1'\n",
        "learning_os/b.py": "from learning_os import __version__\n",
    })
    assert _violations(tools) == []
