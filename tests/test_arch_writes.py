"""A2 one canonical writer: static lint plus the seven fixtures (SPEC §3.2)."""

from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path, PurePath

import arch_writes_fixtures
import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
ARCH = ROOT / "tests" / "architecture"
EFFECTS_PATH = ARCH / "effects.yaml"
RATCHETS_PATH = ARCH / "ratchets.yaml"
MODE_PATH = ARCH / "a2-mode.txt"

FIX = ("Return a TransactionProposal; only TransactionService writes "
       "canonical files (PLAN D4).")

RULE = "A2-static"


def _glob_match(path: str, glob: str) -> bool:
    if glob.endswith("/**"):
        prefix = glob[:-3]
        return path == prefix or path.startswith(prefix + "/")
    return PurePath(path).match(glob)


def _effect_for(path: str, effects: dict) -> str | None:
    for glob, effect in effects.items():
        if _glob_match(path, glob):
            return effect
    return None


class _Visitor(ast.NodeVisitor):
    def __init__(self, rel: str):
        self._rel = rel
        self._funcs: list[str] = []
        self.hits: list[tuple[str, int]] = []

    def _function(self) -> str:
        return self._funcs[-1] if self._funcs else "<module>"

    def _record(self, primitive: str, node: ast.AST) -> None:
        self.hits.append(
            (f"{self._rel}::{self._function()}::{primitive}", node.lineno))

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._funcs.append(node.name)
        self.generic_visit(node)
        self._funcs.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._funcs.append(node.name)
        self.generic_visit(node)
        self._funcs.pop()

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if self._rel == "tools/learning_os/transactions.py" and isinstance(
                func, ast.Name) and func.id == "_atomic_write_bytes":
            self.generic_visit(node)
            return
        primitive = None
        if isinstance(func, ast.Attribute):
            attr = func.attr
            is_os = isinstance(func.value, ast.Name) and func.value.id == "os"
            is_shutil = isinstance(func.value, ast.Name) and (
                func.value.id == "shutil")
            is_yaml = isinstance(func.value, ast.Name) and (
                func.value.id == "yaml")
            if attr == "write_text":
                primitive = "write_text"
            elif attr == "write_bytes":
                primitive = "write_bytes"
            elif attr == "unlink":
                primitive = "unlink"
            elif attr == "replace" and is_os:
                primitive = "os.replace"
            elif attr == "rename" and is_os:
                primitive = "os.rename"
            elif attr == "remove" and is_os:
                primitive = "os.remove"
            elif attr == "rename" and not is_os:
                primitive = "rename"
            elif attr == "replace" and not is_os:
                if len(node.args) == 1 and not node.keywords:
                    primitive = "replace"
            elif is_shutil and attr in (
                    "move", "copy", "copy2", "copyfile", "rmtree"):
                primitive = f"shutil.{attr}"
            elif attr == "safe_dump" and is_yaml:
                if len(node.args) >= 2 or any(
                        keyword.arg == "stream"
                        for keyword in node.keywords):
                    primitive = "yaml.safe_dump"
        elif isinstance(func, ast.Name) and func.id == "open":
            mode = None
            if len(node.args) >= 2 and isinstance(
                    node.args[1], ast.Constant):
                mode = node.args[1].value
            for keyword in node.keywords:
                if keyword.arg == "mode" and isinstance(
                        keyword.value, ast.Constant):
                    mode = keyword.value.value
            if isinstance(mode, str) and any(
                    mark in mode for mark in "wax+"):
                primitive = "open"
        if primitive is not None:
            self._record(primitive, node)
        self.generic_visit(node)


def _collect_static() -> tuple[Counter, dict[str, tuple[str, int]]]:
    effects = yaml.safe_load(EFFECTS_PATH.read_text(encoding="utf-8"))
    counter: Counter = Counter()
    first_seen: dict[str, tuple[str, int]] = {}
    for path in sorted((ROOT / "tools" / "learning_os").rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        if _effect_for(rel, effects) is not None:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        visitor = _Visitor(rel)
        visitor.visit(tree)
        for signature, lineno in visitor.hits:
            counter[signature] += 1
            first_seen.setdefault(signature, (rel, lineno))
    return counter, first_seen


def test_static_lint_matches_baseline():
    current, first_seen = _collect_static()
    recorded_entries = yaml.safe_load(
        RATCHETS_PATH.read_text(encoding="utf-8"))["checks"].get(RULE, [])
    recorded = {entry["signature"]: entry["count"]
                for entry in recorded_entries}
    failures = []
    for signature, count in sorted(current.items()):
        if recorded.get(signature, 0) < count:
            rel, lineno = first_seen[signature]
            failures.append(
                f"A2 {signature}: current count {count} exceeds recorded "
                f"{recorded.get(signature, 0)} — {rel}:{lineno} — {FIX}")
    for signature in sorted(recorded):
        if signature not in current:
            failures.append(
                f"A2 {signature}: no longer occurs — remove the fixed "
                f"exception from ratchets.yaml — {FIX}")
    assert not failures, "\n".join(failures)


def _read_mode() -> str:
    assert MODE_PATH.is_file(), f"missing {MODE_PATH.relative_to(ROOT)}"
    return MODE_PATH.read_text(encoding="utf-8").strip()


@pytest.mark.parametrize(
    "name", sorted(arch_writes_fixtures.FIXTURES))
def test_fixture(name: str, tmp_path: Path):
    mode = _read_mode()
    assert mode in ("block", "report"), f"a2-mode.txt must be block|report, got {mode!r}"
    func = arch_writes_fixtures.FIXTURES[name]
    try:
        func(tmp_path)
    except AssertionError as error:
        if mode == "report":
            print(f"A2 {name}: {error}")
            return
        raise
