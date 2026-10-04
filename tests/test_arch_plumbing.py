"""A4 plumbing lives only in the pipeline (PLAN D20): handler modules are ratcheted."""

from __future__ import annotations

import ast
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
RATCHETS_PATH = ROOT / "tests/architecture/ratchets.yaml"
COMMANDS_DIR = ROOT / "tools/learning_os/commands"
HANDLERS_DIR = ROOT / "tools/learning_os/ops/handlers"

FIX = "Handlers get the snapshot and lock from the pipeline (PLAN D20)."

CHECK_ID = "A4-plumbing"

_BARE_CALLEES = ("load_repo", "canonical_fingerprint", "_operator_lock", "print", "exit")


@dataclass(frozen=True)
class Hit:
    signature: str
    path: str
    lineno: int


def _is_main_test(test: ast.AST) -> bool:
    """`__name__ == "__main__"` in either order (the `__main__` exemption)."""
    return (
        isinstance(test, ast.Compare)
        and len(test.ops) == 1
        and isinstance(test.ops[0], ast.Eq)
        and (
            (isinstance(test.left, ast.Name) and test.left.id == "__name__"
             and isinstance(test.comparators[0], ast.Constant)
             and test.comparators[0].value == "__main__")
            or (isinstance(test.comparators[0], ast.Name)
                and test.comparators[0].id == "__name__"
                and isinstance(test.left, ast.Constant)
                and test.left.value == "__main__")
        )
    )


class _PlumbingVisitor(ast.NodeVisitor):
    """Flagged plumbing calls and int returns in function bodies (SPEC §3.3 A4)."""

    def __init__(self, rel: str, parents: dict[ast.AST, ast.AST]) -> None:
        self._rel = rel
        self._parents = parents
        self._funcs: list[str] = []
        self._lambdas = 0
        self.hits: list[Hit] = []

    def _in_function(self) -> bool:
        return bool(self._funcs) or self._lambdas > 0

    def _function(self) -> str:
        return self._funcs[-1] if self._funcs else "<lambda>"

    def _record(self, callee: str, node: ast.AST) -> None:
        signature = f"{self._rel}::{self._function()}::{callee}"
        self.hits.append(Hit(signature, self._rel, node.lineno))

    def _inside_main(self, node: ast.AST) -> bool:
        seen = node
        while True:
            parent = self._parents.get(seen)
            if parent is None:
                return False
            if (isinstance(parent, ast.If) and _is_main_test(parent.test)
                    and any(stmt is seen for stmt in parent.body)):
                return True
            seen = parent

    def _visit_def(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        for decorator in node.decorator_list:
            self.visit(decorator)
        self.visit(node.args)
        for param in node.type_params:
            self.visit(param)
        self._funcs.append(node.name)
        for stmt in node.body:
            self.visit(stmt)
        self._funcs.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_def(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_def(node)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        self.visit(node.args)
        self._lambdas += 1
        self.visit(node.body)
        self._lambdas -= 1

    def visit_Call(self, node: ast.Call) -> None:
        if self._in_function():
            func = node.func
            callee = None
            if isinstance(func, ast.Name) and func.id in _BARE_CALLEES:
                callee = func.id
            elif (isinstance(func, ast.Attribute) and func.attr == "exit"
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "sys"):
                callee = "sys.exit"
            if callee is not None:
                self._record(callee, node)
        self.generic_visit(node)

    def visit_Return(self, node: ast.Return) -> None:
        if (isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, int)
                and not isinstance(node.value.value, bool)
                and not self._inside_main(node)):
            self._record("return", node)
        self.generic_visit(node)


def scan_file(path: Path, rel: str) -> list[Hit]:
    """Flagged plumbing in one file: bare pipeline calls plus int returns."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    parents: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    visitor = _PlumbingVisitor(rel, parents)
    visitor.visit(tree)
    return visitor.hits


def scan_commands(root: Path) -> list[Hit]:
    """Every flagged construct in tools/learning_os/commands/*.py."""
    commands = root / "tools/learning_os/commands"
    hits: list[Hit] = []
    for path in sorted(commands.glob("*.py")):
        if path.is_file():
            hits.extend(scan_file(path, path.relative_to(root).as_posix()))
    return hits


def scan_handlers(root: Path) -> list[Hit]:
    """Every flagged construct in tools/learning_os/ops/handlers/**/*.py."""
    handlers = root / "tools/learning_os/ops/handlers"
    if not handlers.is_dir():
        return []
    hits: list[Hit] = []
    for path in sorted(handlers.rglob("*.py")):
        hits.extend(scan_file(path, path.relative_to(root).as_posix()))
    return hits


def test_handlers_have_no_plumbing():
    failures = [f"A4 {hit.signature} — {hit.path}:{hit.lineno} — {FIX}"
                for hit in scan_handlers(ROOT)]
    assert not failures, "\n".join(failures)


def test_current_exceptions_are_recorded():
    hits = scan_commands(ROOT)
    current = Counter(hit.signature for hit in hits)
    first_seen = {hit.signature: hit for hit in hits}
    data = yaml.safe_load(RATCHETS_PATH.read_text(encoding="utf-8"))
    recorded = {entry["signature"]: entry["count"]
                for entry in data["checks"].get(CHECK_ID, [])}
    failures = []
    for signature, count in sorted(current.items()):
        if recorded.get(signature, 0) < count:
            seen = first_seen[signature]
            failures.append(
                f"A4 {signature}: current count {count} exceeds recorded "
                f"{recorded.get(signature, 0)} — "
                f"{seen.path}:{seen.lineno} — {FIX}")
    for signature in sorted(recorded):
        if signature not in current:
            failures.append(
                f"A4 {signature}: no longer occurs — "
                f"remove the fixed exception from ratchets.yaml")
    assert not failures, "\n".join(failures)
