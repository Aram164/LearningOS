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
CHECK_ID2 = "A3-prose-2"

_SUFFIXES = ("message", "msg", "stderr", "stdout", "error", "errors",
             "text", "output", "complaint")
_WRAPPERS = ("lower", "upper", "strip", "casefold")
_METHODS = ("startswith", "endswith", "find", "index", "count", "rfind")
_REGEX_FUNCS = ("search", "match", "fullmatch")
_COMPILED_METHODS = ("search", "match", "fullmatch", "findall")

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
    """SPEC §3.7 item 2: the identifier equals a §3.1 word or ends with `_` + one."""
    lowered = identifier.lower()
    return lowered in _SUFFIXES or any(
        lowered.endswith("_" + suffix) for suffix in _SUFFIXES)


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


def _compile_literal(value: ast.AST) -> str | None:
    """The str constant passed to a `re.compile(...)` call, else None."""
    if not (isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute)
            and value.func.attr == "compile"
            and isinstance(value.func.value, ast.Name)
            and value.func.value.id == "re"):
        return None
    if (value.args and isinstance(value.args[0], ast.Constant)
            and isinstance(value.args[0].value, str)):
        return value.args[0].value
    return None


def _compiled_patterns(tree: ast.Module) -> dict[str, str]:
    """Module-level names assigned from `re.compile(const)` map to the constant."""
    found: dict[str, str] = {}
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign):
            targets: list[ast.AST] = list(stmt.targets)
            value = stmt.value
        elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
            targets = [stmt.target]
            value = stmt.value
        else:
            continue
        literal = _compile_literal(value)
        if literal is None:
            continue
        for target in targets:
            if isinstance(target, ast.Name):
                found[target.id] = literal
    return found


def _is_concat_operand(node: ast.AST, exc_names: set[str]) -> bool:
    """A §3.1 suspect text or, recursively, a (i) concatenation of those."""
    if _is_suspect(node, exc_names):
        return True
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return (_is_concat_operand(node.left, exc_names)
                and _is_concat_operand(node.right, exc_names))
    if isinstance(node, ast.JoinedStr):
        parts = [v for v in node.values if isinstance(v, ast.FormattedValue)]
        return (bool(parts) and len(parts) == len(node.values)
                and all(_is_concat_operand(v.value, exc_names) for v in parts))
    return False


def _is_concat_suspect(node: ast.AST, exc_names: set[str]) -> bool:
    """SPEC §3.7 item 3(i): a `+` BinOp or f-string over suspect operands only."""
    if not isinstance(node, (ast.BinOp, ast.JoinedStr)):
        return False
    return _is_concat_operand(node, exc_names)


def _is_compiled_arg(node: ast.AST, exc_names: set[str]) -> bool:
    """A (ii) search argument: a §3.1 suspect text or a (i) concatenation."""
    return _is_suspect(node, exc_names) or _is_concat_suspect(node, exc_names)


def _searched_text(node: ast.Call) -> ast.AST | None:
    """The text a compiled-pattern search reads: first arg, or `string=`."""
    if node.args:
        return node.args[0]
    for keyword in node.keywords:
        if keyword.arg == "string":
            return keyword.value
    return None


class _Prose2Visitor(ast.NodeVisitor):
    """SPEC §3.7 item 3: rules (a)-(c) over (i) texts, plus (ii) compiled searches."""

    def __init__(self, rel: str, source: str, exc_names: set[str],
                 parents: dict[ast.AST, ast.AST],
                 compiled: dict[str, str]) -> None:
        self._rel = rel
        self._source = source
        self._exc_names = exc_names
        self._parents = parents
        self._compiled = compiled
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
                and _is_concat_suspect(node.comparators[0], self._exc_names)):
            self._record("substring", node.left.value, node)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Attribute):
            if (func.attr in _METHODS and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)
                    and _is_concat_suspect(func.value, self._exc_names)):
                self._record("method", node.args[0].value, node)
            elif (func.attr in _REGEX_FUNCS and isinstance(func.value, ast.Name)
                    and func.value.id == "re" and len(node.args) >= 2
                    and _is_concat_suspect(node.args[1], self._exc_names)):
                pattern = node.args[0]
                if isinstance(pattern, ast.Constant) and isinstance(pattern.value, str):
                    literal = pattern.value
                else:
                    literal = ast.get_source_segment(self._source, pattern) or "<pattern>"
                self._record("regex", literal, node)
            elif (func.attr in _COMPILED_METHODS
                    and isinstance(func.value, ast.Name)
                    and func.value.id in self._compiled
                    and _searched_text(node) is not None
                    and _is_compiled_arg(_searched_text(node),
                                         self._exc_names)):
                self._record("regex", self._compiled[func.value.id], node)
            elif (func.attr == "search"
                    and _compile_literal(func.value) is not None
                    and _searched_text(node) is not None
                    and _is_compiled_arg(_searched_text(node),
                                         self._exc_names)):
                literal = _compile_literal(func.value)
                assert literal is not None
                self._record("regex", literal, node)
        self.generic_visit(node)


def scan_source2(source: str, rel: str) -> list[Hit]:
    """Flagged SPEC §3.7 item 3 constructs in one source string (fixtures, probes)."""
    tree = ast.parse(source)
    parents: dict[ast.AST, ast.AST] = {}
    exc_names: set[str] = set()
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
        if isinstance(node, ast.ExceptHandler) and node.name:
            exc_names.add(node.name)
    visitor = _Prose2Visitor(rel, source, exc_names, parents,
                             _compiled_patterns(tree))
    visitor.visit(tree)
    return visitor.hits


def scan_file2(path: Path, rel: str) -> list[Hit]:
    """Flagged SPEC §3.7 item 3 constructs in one file."""
    return scan_source2(path.read_text(encoding="utf-8"), rel)


def scan_tree2(root: Path) -> list[Hit]:
    """Every §3.7 item 3 hit under tools/learning_os/**/*.py and tools/*.py."""
    files = sorted((root / "tools" / "learning_os").rglob("*.py"))
    files += sorted(p for p in (root / "tools").glob("*.py") if p.is_file())
    hits: list[Hit] = []
    for path in files:
        hits.extend(scan_file2(path, path.relative_to(root).as_posix()))
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
    rel = "tools/learning_os/ops/outcomes.py"
    hits = [hit for hit in scan_file(ROOT / rel, rel)
            if "::classify::" in hit.signature]
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


_POSITIVE2 = ("pos2_binop.py", "pos2_compiled.py", "pos2_compiled_kw.py")
_NEGATIVE2 = ("neg2_binop_format.py",)


def test_positive2_fixtures_are_flagged():
    for name in _POSITIVE2:
        hits = scan_file2(FIXTURES_DIR / name, f"fixtures/{name}")
        assert hits, f"A3 {name}: positive-2 fixture produced no hits — {FIX}"
        old = scan_file(FIXTURES_DIR / name, f"fixtures/{name}")
        assert old == [], (
            f"A3 {name}: positive-2 fixture must stay clean under A3-prose: "
            + ", ".join(hit.signature for hit in old) + f" — {FIX}")


def test_negative2_fixtures_are_clean():
    failures = []
    for name in _NEGATIVE2:
        for hit in scan_file2(FIXTURES_DIR / name, f"fixtures/{name}"):
            failures.append(f"A3 {hit.signature} — {name}:{hit.lineno} — {FIX}")
    assert not failures, "\n".join(failures)


def test_plain_suspect_texts_are_not_flagged():
    hits = scan_source2(
        'def decide(msg: str) -> bool:\n    return "x" in msg\n',
        "inline/plain.py")
    assert hits == [], (
        "A3-prose-2 must not re-flag A3-prose territory: "
        + ", ".join(hit.signature for hit in hits) + f" — {FIX}")


def test_current2_exceptions_are_recorded():
    hits = scan_tree2(ROOT)
    current = Counter(hit.signature for hit in hits)
    first_seen = {hit.signature: hit for hit in hits}
    data = yaml.safe_load(RATCHETS_PATH.read_text(encoding="utf-8"))
    recorded = {entry["signature"]: entry["count"]
                for entry in data["checks"].get(CHECK_ID2, [])}
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
