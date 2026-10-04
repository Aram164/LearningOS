"""A3 no decisions from prose (PLAN D3): text matching over suspect text is ratcheted."""

from __future__ import annotations

import ast
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
RATCHETS_PATH = ROOT / "tests/architecture/ratchets.yaml"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures/archcheck/prose"
UI_SRC = ROOT.parent / "obsidian-ui/src"

FIX = "Raise a typed failure; classify by type, never by message text (PLAN D3)."

CHECK_ID = "A3-prose"

_SUFFIXES = ("message", "msg", "stderr", "stdout", "error", "errors",
             "text", "output", "complaint")
_WRAPPERS = ("lower", "upper", "strip", "casefold")
_METHODS = ("startswith", "endswith", "find", "index", "count", "rfind")
_REGEX_FUNCS = ("search", "match", "fullmatch")

_TS_PATTERNS = (
    re.compile(r"\.(message|stderr|text)\??\.(includes|startsWith|endsWith|indexOf|match)\("),
    re.compile(r"/.*/\.test\(\s*[\w.]*(message|stderr)"),
)


@dataclass(frozen=True)
class Hit:
    signature: str
    path: str
    lineno: int


def _name_is_suspect(identifier: str) -> bool:
    lowered = identifier.lower()
    return any(lowered.endswith(suffix) for suffix in _SUFFIXES)


def _is_suspect(node: ast.AST, exc_names: set[str]) -> bool:
    """SPEC §3.1 suspect text: exception forms, message-ish names, wrappers."""
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Name) and func.id in ("str", "repr", "format"):
            return (
                len(node.args) == 1
                and not node.keywords
                and isinstance(node.args[0], ast.Name)
                and node.args[0].id in exc_names
            )
        if isinstance(func, ast.Attribute) and func.attr in _WRAPPERS:
            return _is_suspect(func.value, exc_names)
        return False
    if isinstance(node, ast.Name):
        return _name_is_suspect(node.id)
    if isinstance(node, ast.Attribute):
        if (node.attr == "args" and isinstance(node.value, ast.Name)
                and node.value.id in exc_names):
            return True
        return _name_is_suspect(node.attr)
    if isinstance(node, ast.Subscript):
        value = node.value
        return (isinstance(value, ast.Attribute) and value.attr == "args"
                and isinstance(value.value, ast.Name)
                and value.value.id in exc_names)
    return False


def _is_print_or_logging_call(node: ast.Call) -> bool:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id == "print"
    return (isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name)
            and func.value.id == "logging")


def _is_excluded(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    """A flagged test used only inside formatting, a print/logging call, or raise."""
    seen = node
    while True:
        parent = parents.get(seen)
        if parent is None:
            return False
        if isinstance(parent, ast.JoinedStr):
            return True
        if isinstance(parent, ast.BinOp) and isinstance(parent.op, ast.Mod):
            return True
        if isinstance(parent, ast.Call):
            if _is_print_or_logging_call(parent):
                return True
        elif isinstance(parent, ast.Raise):
            return True
        elif isinstance(parent, ast.stmt):
            return False
        seen = parent


class _ProseVisitor(ast.NodeVisitor):
    def __init__(self, rel: str, source: str, exc_names: set[str],
                 parents: dict[ast.AST, ast.AST]) -> None:
        self._rel = rel
        self._source = source
        self._exc_names = exc_names
        self._parents = parents
        self._funcs: list[str] = []
        self.hits: list[Hit] = []

    def _record(self, rule: str, literal: str, node: ast.AST) -> None:
        if _is_excluded(node, self._parents):
            return
        function = self._funcs[-1] if self._funcs else "<module>"
        signature = f"{self._rel}::{function}::{rule}::{literal[:40]}"
        self.hits.append(Hit(signature, self._rel, node.lineno))

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._funcs.append(node.name)
        self.generic_visit(node)
        self._funcs.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._funcs.append(node.name)
        self.generic_visit(node)
        self._funcs.pop()

    def visit_Compare(self, node: ast.Compare) -> None:
        if (node.ops and isinstance(node.ops[0], (ast.In, ast.NotIn))
                and isinstance(node.left, ast.Constant)
                and isinstance(node.left.value, str)
                and node.comparators
                and _is_suspect(node.comparators[0], self._exc_names)):
            self._record("substring", node.left.value, node)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Attribute):
            if (func.attr in _METHODS and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)
                    and _is_suspect(func.value, self._exc_names)):
                self._record("method", node.args[0].value, node)
            elif (func.attr in _REGEX_FUNCS and isinstance(func.value, ast.Name)
                    and func.value.id == "re" and len(node.args) >= 2
                    and _is_suspect(node.args[1], self._exc_names)):
                pattern = node.args[0]
                if isinstance(pattern, ast.Constant) and isinstance(pattern.value, str):
                    literal = pattern.value
                else:
                    literal = ast.get_source_segment(self._source, pattern) or "<pattern>"
                self._record("regex", literal, node)
        self.generic_visit(node)


def scan_file(path: Path, rel: str) -> list[Hit]:
    """Flagged prose tests in one file (SPEC §3.1 rules a–c with exclusions)."""
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    parents: dict[ast.AST, ast.AST] = {}
    exc_names: set[str] = set()
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
        if isinstance(node, ast.ExceptHandler) and node.name:
            exc_names.add(node.name)
    visitor = _ProseVisitor(rel, source, exc_names, parents)
    visitor.visit(tree)
    return visitor.hits


def scan_tree(root: Path) -> list[Hit]:
    """Every flagged prose test under tools/learning_os/**/*.py and tools/*.py."""
    files = sorted((root / "tools" / "learning_os").rglob("*.py"))
    files += sorted(p for p in (root / "tools").glob("*.py") if p.is_file())
    hits: list[Hit] = []
    for path in files:
        hits.extend(scan_file(path, path.relative_to(root).as_posix()))
    return hits


def scan_ts(src: Path) -> list[tuple[str, int, str]]:
    """TS prose matches as (path, lineno, line); the caller skips when absent."""
    matches: list[tuple[str, int, str]] = []
    for path in sorted(src.rglob("*.ts")):
        rel = path.relative_to(src.parent.parent).as_posix()
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if any(pattern.search(line) for pattern in _TS_PATTERNS):
                matches.append((rel, lineno, line.strip()))
    return matches


_POSITIVE = ("pos_substring.py", "pos_lower.py", "pos_regex.py",
             "pos_args.py", "pos_startswith.py")
_NEGATIVE = ("neg_fstring.py", "neg_logging.py", "neg_typed.py", "neg_raise_arg.py")
_ADVERSARIAL = ("adv_token_in_id.py",)


def test_positive_fixtures_are_flagged():
    for name in _POSITIVE:
        hits = scan_file(FIXTURES_DIR / name, f"fixtures/{name}")
        assert hits, f"A3 {name}: positive fixture produced no hits — {FIX}"


def test_adversarial_fixtures_are_flagged():
    for name in _ADVERSARIAL:
        hits = scan_file(FIXTURES_DIR / name, f"fixtures/{name}")
        assert hits, f"A3 {name}: adversarial fixture produced no hits — {FIX}"


def test_negative_fixtures_are_clean():
    failures = []
    for name in _NEGATIVE:
        for hit in scan_file(FIXTURES_DIR / name, f"fixtures/{name}"):
            failures.append(f"A3 {hit.signature} — {name}:{hit.lineno} — {FIX}")
    assert not failures, "\n".join(failures)


def test_classify_failure_is_not_flagged():
    rel = "tools/learning_os/commands/capability.py"
    hits = [hit for hit in scan_file(ROOT / rel, rel)
            if "::_classify_failure::" in hit.signature]
    assert hits == [], (
        "A3 _classify_failure regressed to prose matching: "
        + ", ".join(hit.signature for hit in hits) + f" — {FIX}")


def test_current_exceptions_are_recorded():
    hits = scan_tree(ROOT)
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
                f"A3 {signature}: current count {count} exceeds recorded "
                f"{recorded.get(signature, 0)} — "
                f"{seen.path}:{seen.lineno} — {FIX}")
    for signature in sorted(recorded):
        if signature not in current:
            failures.append(
                f"A3 {signature}: no longer occurs — "
                f"remove the fixed exception from ratchets.yaml")
    assert not failures, "\n".join(failures)


@pytest.mark.paired
def test_ts_sources_have_no_prose_matches():
    if not UI_SRC.is_dir():
        pytest.skip("no sibling obsidian-ui checkout")
    failures = [f"A3 {rel}:{lineno}: {line} — {FIX}"
                for rel, lineno, line in scan_ts(UI_SRC)]
    assert not failures, "\n".join(failures)
