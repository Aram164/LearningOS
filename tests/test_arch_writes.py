"""A2 one canonical writer: mandatory tools/ writer census and fixtures (SPEC §3.2, CL-06)."""

from __future__ import annotations

import ast
import os
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from fnmatch import fnmatchcase
from functools import cache
from pathlib import Path, PurePosixPath

import arch_writes_fixtures
import pytest
import yaml

from learning_os.store.contracts import write_scopes
from learning_os.store.fingerprint import DATA_ROOTS
from learning_os.store.loading.yamlio import UniqueKeySafeLoader

ROOT = Path(__file__).resolve().parent.parent
ARCH = ROOT / "tests" / "architecture"
EFFECTS_PATH = ARCH / "effects.yaml"
RATCHETS_PATH = ARCH / "ratchets.yaml"
MODE_PATH = ARCH / "a2-mode.txt"
TREE_CONTRACT_PATH = ROOT / "system" / "contracts" / "tree-contract.yaml"

FIX = ("Return a TransactionProposal; only TransactionService writes "
       "canonical files (PLAN D4).")

RULE = "A2-static"

ALLOWED_EFFECTS = frozenset({
    "canonical-engine",
    "cache",
    "projection",
    "operational",
    "migration",
    "tooling",
})

_DECLARATION_KEYS = frozenset({"effect", "destinations", "reason", "contract"})

_CANONICAL_ENGINE_MODULE = "tools/learning_os/store/transactions.py"

# Non-engine writers allowed to touch specific DATA_ROOTS entries only under an
# explicit recorded migration or tree-contract allocation.
_RECORDED_CANONICAL_EXCEPTIONS: dict[str, tuple[str, frozenset[str], str]] = {
    "tools/migrations/curriculum_v2.py": (
        "migration",
        frozenset({
            "curriculum/**",
            "work/active/*/CONTEXT.md",
            "work/active/workspace-degree-planning",
            "sources/collections/degree-module-anchors.yaml",
        }),
        "tools/migrations/README.md",
    ),
    "tools/library_reconciliation.py": (
        "tooling",
        frozenset({
            "work/active/*/outputs/dispositions.yaml",
            "work/active/*/outputs/reconciliation-report.md",
            "work/active/*/outputs/applied-check.json",
        }),
        "tree-contract.yaml",
    ),
    "tools/material_summarize.py": (
        "cache",
        frozenset({"knowledge/summaries/**"}),
        "tree-contract.yaml",
    ),
}

_WRITE_HELPERS = frozenset({
    "atomic_write_text_exclusive",
    "atomic_write_bytes_exclusive",
    "atomic_write_bytes",
    "exclusive_temp_path",
    "atomic_text",
    "write_file_create_only",
    "write_local_output_file",
})

_MUTATING_GIT_SUBCOMMANDS = frozenset({"commit", "mv", "reset", "update-ref", "rm"})
_MUTATING_FS_COMMANDS = frozenset({"cp", "mv", "rm"})
_OS_WRITE_OPEN_FLAGS = frozenset({"O_WRONLY", "O_RDWR", "O_CREAT", "O_TRUNC", "O_APPEND"})
_OS_READONLY_FLAGS = frozenset({"O_RDONLY", "O_NOFOLLOW", "O_CLOEXEC", "O_DIRECTORY", "O_NONBLOCK"})
_SUBPROCESS_FUNCS = frozenset({"run", "Popen", "check_call", "check_output", "call"})
_OS_WRITE_ATTRS = frozenset({
    "replace", "rename", "remove", "unlink", "write", "link", "symlink",
    "mkdir", "makedirs", "rmdir", "chmod", "truncate",
})
_SHUTIL_WRITE_ATTRS = frozenset({"move", "copy", "copy2", "copyfile", "copytree", "rmtree"})
_TEMPFILE_ATTRS = frozenset({"mkstemp", "mkdtemp", "NamedTemporaryFile", "TemporaryFile"})

_ALLOWED_EXTERNAL_PREFIXES = (
    "../materials/",
    "../reading-memory/",
    "../scratch/",
    "~/.local/state/learningos/",
)
_ALLOWED_PLACEHOLDER_PREFIXES = (
    "<PRIVATE_REPORT_DIR>/",
    "<EXPLICIT_OUT_DIR>/",
    "<OUT_DIR>/",
    "<STATE>/",
    "<EXTERNAL_PRACTICE_VAULT>/",
    "<TMPDIR>/",
    "<RESTORED_COPY>/",
    "$LOS_SCRATCH_DIR/",
)
_ALLOWED_PLACEHOLDER_TOKENS = frozenset({
    "<EXPLICIT_OUT_FILE>",
    "<EXPLICIT_REPORT_OUT>",
    "<EXPLICIT_LOCAL_OUTPUT>",
    "<LOS_OBSERVATIONS>",
    "<COUNTER_FILE>",
    "<GIT_INDEX_AND_COMMIT>",
    "<CALLER_SCOPED_ATOMIC_WRITE_PRIMITIVES>",
    "<TRACE_DEBUG_FILE>",
})


def _load_effects_yaml(path: Path = EFFECTS_PATH) -> object:
    """Parse effects.yaml strictly: duplicate module or field keys fail closed (P2A-03)."""
    return yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeySafeLoader)


def _load_tree_roots(tree_contract_path: Path = TREE_CONTRACT_PATH) -> frozenset[str]:
    data = yaml.safe_load(tree_contract_path.read_text(encoding="utf-8")) or {}
    roots = set()
    for entry in data.get("directories", []):
        if isinstance(entry, dict) and isinstance(entry.get("path"), str):
            roots.add(entry["path"].split("/", 1)[0])
    # Top-level non-canonical directories/files recognized by tests / build tooling.
    roots.update({
        "tests", "migration", "system", "generated", "operations", "archive",
        "pyproject.toml", "Makefile", "README.md",
    })
    return frozenset(roots)


def _external_tail_ok(tail: str, *, placeholder: bool) -> bool:
    """A tail after an allowed external prefix must be a normalized relative pattern.

    Basename globs such as ``learningos-*.lock`` stay legal; traversal, empty or
    dot segments, backslashes, ``?[]`` and canonical root names do not.
    """
    if not tail or tail.endswith("/") or "//" in tail or "\\" in tail or "\x00" in tail:
        return False
    parts = tail.split("/")
    forbidden = set(DATA_ROOTS) | ({"system", "operations"} if placeholder else set())
    for part in parts:
        if part in {"", ".", ".."} or any(ch in part for ch in "?[]"):
            return False
        if part in forbidden:
            return False
    return True


def _is_external_or_placeholder(dest: str) -> bool:
    if dest in _ALLOWED_PLACEHOLDER_TOKENS:
        return True
    for prefix in _ALLOWED_EXTERNAL_PREFIXES:
        if dest.startswith(prefix) and len(dest) > len(prefix):
            return _external_tail_ok(dest[len(prefix):], placeholder=False)
    for prefix in _ALLOWED_PLACEHOLDER_PREFIXES:
        if dest.startswith(prefix) and len(dest) > len(prefix):
            return _external_tail_ok(dest[len(prefix):], placeholder=True)
    return False


def _dest_touches_data_root(dest: str, data_roots: tuple[str, ...]) -> str | None:
    if _is_external_or_placeholder(dest):
        return None
    normalized = dest.lstrip("./")
    first = normalized.split("/", 1)[0]
    for root in data_roots:
        if first == root or normalized == root or normalized.startswith(root + "/"):
            return root
    return None


def validate_effects_declarations(
    effects: object,
    *,
    root: Path = ROOT,
    data_roots: tuple[str, ...] = DATA_ROOTS,
    tree_roots: frozenset[str] | None = None,
) -> tuple[dict[str, dict], list[str]]:
    """Validate structured effects.yaml schema, ban wildcards, and guard DATA_ROOTS."""
    failures: list[str] = []
    parsed: dict[str, dict] = {}
    if not isinstance(effects, dict):
        return parsed, ["A2 effects.yaml must map exact module paths to declarations"]
    allowed_roots = tree_roots if tree_roots is not None else _load_tree_roots()

    for rel, raw in effects.items():
        if not isinstance(rel, str) or not rel.startswith("tools/") or not rel.endswith(".py"):
            failures.append(f"A2 effects.yaml key {rel!r} must be a tools/**/*.py path")
            continue
        if any(ch in rel for ch in ("*", "?", "[")):
            failures.append(f"A2 wildcard glob forbidden in effects.yaml: {rel!r}")
            continue
        if not (root / rel).is_file():
            failures.append(f"A2 effects.yaml target does not exist: {rel}")
            continue
        if not isinstance(raw, dict):
            failures.append(f"A2 {rel}: declaration must be a mapping with effect/destinations/reason")
            continue
        unknown_keys = set(raw) - _DECLARATION_KEYS
        if unknown_keys:
            failures.append(f"A2 {rel}: unknown declaration key(s) {sorted(unknown_keys)}")
        effect = raw.get("effect")
        destinations = raw.get("destinations")
        reason = raw.get("reason")
        contract = raw.get("contract")
        if effect not in ALLOWED_EFFECTS:
            failures.append(f"A2 {rel}: invalid effect {effect!r}")
        if (
            not isinstance(destinations, list)
            or not destinations
            or not all(isinstance(d, str) and d.strip() for d in destinations)
        ):
            failures.append(f"A2 {rel}: destinations must be a non-empty list of path strings")
            destinations = []
        if not isinstance(reason, str) or not reason.strip():
            failures.append(f"A2 {rel}: reason must be a non-empty string")
        if contract is not None and (not isinstance(contract, str) or not contract.strip()):
            failures.append(f"A2 {rel}: contract must be a non-empty string when present")

        parsed[rel] = raw

        for dest in destinations:
            if not _is_external_or_placeholder(dest):
                top = dest.lstrip("./").split("/", 1)[0]
                if top not in allowed_roots:
                    failures.append(
                        f"A2 {rel}: destination {dest!r} top root {top!r} not in tree-contract.yaml"
                    )
                try:
                    normalized = write_scopes.normalize_scope_pattern(dest)
                except write_scopes.WriteScopeError as exc:
                    failures.append(f"A2 {rel}: destination {dest!r} is not a normalized scope pattern: {exc}")
                    continue
                if normalized != dest:
                    failures.append(
                        f"A2 {rel}: destination {dest!r} must be spelled in normalized form {normalized!r}"
                    )
                    continue
            data_root = _dest_touches_data_root(dest, data_roots)
            if data_root is None or rel == _CANONICAL_ENGINE_MODULE:
                if rel == _CANONICAL_ENGINE_MODULE and effect != "canonical-engine":
                    failures.append(f"A2 {rel}: must declare effect canonical-engine")
                continue
            exception = _RECORDED_CANONICAL_EXCEPTIONS.get(rel)
            if exception is None:
                failures.append(
                    f"A2 {rel}: non-engine declaration claims canonical DATA_ROOTS destination "
                    f"{dest!r} ({data_root}/) without a recorded maintenance/migration contract — {FIX}"
                )
                continue
            allowed_eff, allowed_canonical_dests, contract_marker = exception
            if effect != allowed_eff:
                failures.append(
                    f"A2 {rel}: canonical exception requires effect {allowed_eff!r}, got {effect!r}"
                )
            if not isinstance(contract, str) or contract_marker not in contract:
                failures.append(
                    f"A2 {rel}: canonical destination {dest!r} must cite {contract_marker!r} in contract"
                )
            if dest not in allowed_canonical_dests:
                failures.append(
                    f"A2 {rel}: canonical destination {dest!r} exceeds recorded exception "
                    f"{sorted(allowed_canonical_dests)} — {FIX}"
                )

    return parsed, failures


def _names_in_expr(node: ast.AST, env: dict[str, ast.AST], seen: set[str] | None = None) -> set[str]:
    """Collect symbolic flag names referenced directly or via one local binding."""
    seen = seen if seen is not None else set()
    names: set[str] = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name):
            if sub.id in env and sub.id not in seen:
                seen.add(sub.id)
                names |= _names_in_expr(env[sub.id], env, seen)
            else:
                names.add(sub.id)
        elif isinstance(sub, ast.Attribute):
            names.add(sub.attr)
        elif isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            names.add(sub.value)
    return names


def _is_readonly_os_open(
    node: ast.Call, env: dict[str, ast.AST], *, readonly_fd_helper: bool = False,
) -> bool:
    fnode = node.args[1] if len(node.args) >= 2 else next(
        (kw.value for kw in node.keywords if kw.arg == "flags"), None
    )
    if fnode is None:
        return False
    resolved = _resolve_expr(fnode, env)
    if readonly_fd_helper and isinstance(resolved, ast.Call) and isinstance(resolved.func, ast.Name) \
            and resolved.func.id == "fd_open_flags":
        return True
    names = _names_in_expr(fnode, env)
    if not names or (names & _OS_WRITE_OPEN_FLAGS):
        return False
    return "O_RDONLY" in names and names <= _OS_READONLY_FLAGS | {"os", "getattr", "O_RDONLY"}


def _resolve_expr(node: ast.AST | None, env: dict[str, ast.AST], seen: set[str] | None = None) -> ast.AST | None:
    seen = seen if seen is not None else set()
    cur = node
    while isinstance(cur, ast.Name) and cur.id in env and cur.id not in seen:
        seen.add(cur.id)
        cur = env[cur.id]
    return cur


def _mode_writes(mode_node: ast.AST | None, env: dict[str, ast.AST]) -> bool:
    resolved = _resolve_expr(mode_node, env)
    if resolved is None:
        return False
    return not (
        isinstance(resolved, ast.Constant)
        and isinstance(resolved.value, str)
        and not any(mark in resolved.value for mark in "wax+")
    )


def _subprocess_mutation_primitive(node: ast.Call, env: dict[str, ast.AST]) -> str | None:
    if any(
        kw.arg == "shell" and isinstance(_resolve_expr(kw.value, env), ast.Constant)
        and _resolve_expr(kw.value, env).value is True  # type: ignore[union-attr]
        for kw in node.keywords
    ):
        return "subprocess.shell"
    cmd_node = node.args[0] if node.args else next(
        (kw.value for kw in node.keywords if kw.arg == "args"), None
    )
    resolved_cmd = _resolve_expr(cmd_node, env)
    if not isinstance(resolved_cmd, (ast.List, ast.Tuple)) or not resolved_cmd.elts:
        return None
    elts = resolved_cmd.elts
    head = _resolve_expr(elts[0], env)
    if not (isinstance(head, ast.Constant) and isinstance(head.value, str)):
        return None
    cmd = PurePosixPath(head.value).name
    if cmd in _MUTATING_FS_COMMANDS:
        return f"subprocess.{cmd}"
    if cmd == "git":
        for elt in elts[1:]:
            resolved_elt = _resolve_expr(elt, env)
            if isinstance(resolved_elt, ast.Constant) and isinstance(resolved_elt.value, str):
                if resolved_elt.value in _MUTATING_GIT_SUBCOMMANDS:
                    return f"subprocess.git.{resolved_elt.value}"
    return None


class _Visitor(ast.NodeVisitor):
    def __init__(self, rel: str):
        self._rel = rel
        self._funcs: list[str] = []
        self._env_stack: list[dict[str, ast.AST]] = [{}]
        self._mod_aliases: dict[str, str] = {}
        self._from_aliases: dict[str, tuple[str, str]] = {}
        self.hits: list[tuple[str, int]] = []
        self.unmediated_lines: list[int] = []
        self.unmediated_call_lines: list[int] = []
        self._readonly_fd_helper = False

    def visit_Module(self, node: ast.Module) -> None:
        if self._rel == "tools/learning_os/store/study_fence.py":
            for stmt in node.body:
                if not isinstance(stmt, ast.FunctionDef) or stmt.name != "fd_open_flags":
                    continue
                flags = {
                    child.attr for child in ast.walk(stmt)
                    if isinstance(child, ast.Attribute) and child.attr.startswith("O_")
                }
                returns = [child.value for child in ast.walk(stmt) if isinstance(child, ast.Return)]
                self._readonly_fd_helper = (
                    "O_RDONLY" in flags and flags <= _OS_READONLY_FLAGS
                    and len(returns) == 1
                    and isinstance(returns[0], ast.Name) and returns[0].id == "flags"
                )
        self.generic_visit(node)

    def _function(self) -> str:
        return self._funcs[-1] if self._funcs else "<module>"

    def _record(self, primitive: str, node: ast.AST) -> None:
        self.hits.append((f"{self._rel}::{self._function()}::{primitive}", node.lineno))

    def _push_func(self, name: str, node: ast.AST) -> None:
        self._funcs.append(name)
        self._env_stack.append({})
        self.generic_visit(node)
        self._env_stack.pop()
        self._funcs.pop()

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            bound = alias.asname or alias.name.split(".", 1)[0]
            self._mod_aliases[bound] = alias.name
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        mod = node.module or ""
        for alias in node.names:
            bound = alias.asname or alias.name
            self._from_aliases[bound] = (mod, alias.name)
            self._mod_aliases[bound] = alias.name
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            self._env_stack[-1][node.targets[0].id] = node.value
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if isinstance(node.target, ast.Name) and node.value is not None:
            self._env_stack[-1][node.target.id] = node.value
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._push_func(node.name, node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._push_func(node.name, node)

    def visit_keyword(self, node: ast.keyword) -> None:
        if node.arg == "_unmediated_test_only":
            self.unmediated_lines.append(node.lineno)
            self.unmediated_call_lines.append(node.lineno)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id == "_unmediated_test_only":
            self.unmediated_lines.append(node.lineno)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr == "_unmediated_test_only":
            self.unmediated_lines.append(node.lineno)
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        if node.value == "_unmediated_test_only":
            self.unmediated_lines.append(node.lineno)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        env = self._env_stack[-1]
        primitive = None
        if isinstance(func, ast.Attribute):
            attr = func.attr
            mod_name = func.value.id if isinstance(func.value, ast.Name) else None
            canonical_mod = self._mod_aliases.get(mod_name, mod_name) if mod_name else None
            if canonical_mod is None and mod_name in self._from_aliases:
                canonical_mod = self._from_aliases[mod_name][1]
            is_os = canonical_mod == "os"
            is_io = canonical_mod == "io"
            is_shutil = canonical_mod == "shutil"
            is_yaml = canonical_mod == "yaml"
            is_sqlite = canonical_mod == "sqlite3"
            is_subprocess = canonical_mod == "subprocess"
            is_tempfile = canonical_mod == "tempfile"
            resolved_attr = self._mod_aliases.get(attr, attr)
            if is_os and attr in _OS_WRITE_ATTRS:
                primitive = f"os.{attr}"
            elif is_os and attr == "open":
                if not _is_readonly_os_open(node, env, readonly_fd_helper=self._readonly_fd_helper):
                    primitive = "os.open"
            elif is_io and attr == "open":
                mode_node = node.args[1] if len(node.args) >= 2 else next(
                    (kw.value for kw in node.keywords if kw.arg == "mode"), None
                )
                if _mode_writes(mode_node, env):
                    primitive = "open"
            elif attr in ("write_text", "write_bytes", "unlink", "mkdir", "rmdir", "touch", "symlink_to", "hardlink_to"):
                receiver = _resolve_expr(func.value, env)
                delegated_touch = (
                    attr == "touch" and isinstance(receiver, ast.Call)
                    and isinstance(receiver.func, ast.Name)
                    and self._from_aliases.get(receiver.func.id) == (
                        "learning_os.store.materials.reading_cards", "ReadingStore",
                    )
                )
                if not delegated_touch:
                    primitive = attr
            elif attr == "open":
                mode_node = node.args[0] if node.args else next(
                    (kw.value for kw in node.keywords if kw.arg == "mode"), None
                )
                if _mode_writes(mode_node, env):
                    primitive = "Path.open"
            elif attr == "rename":
                primitive = "rename"
            elif attr == "replace":
                if (len(node.args) == 1 and not node.keywords) or (
                    not node.args and len(node.keywords) == 1 and node.keywords[0].arg == "target"
                ):
                    primitive = "replace"
            elif is_shutil and attr in _SHUTIL_WRITE_ATTRS:
                primitive = f"shutil.{attr}"
            elif is_yaml and attr in ("safe_dump", "dump"):
                if len(node.args) >= 2 or any(kw.arg == "stream" for kw in node.keywords):
                    primitive = f"yaml.{attr}"
            elif is_sqlite and attr == "connect":
                primitive = "sqlite3.connect"
            elif is_tempfile and attr in _TEMPFILE_ATTRS:
                primitive = f"tempfile.{attr}"
            elif is_subprocess and attr in _SUBPROCESS_FUNCS:
                primitive = _subprocess_mutation_primitive(node, env)
            elif resolved_attr in _WRITE_HELPERS:
                primitive = resolved_attr
        elif isinstance(func, ast.Name):
            if func.id in self._from_aliases:
                mod_src, orig_name = self._from_aliases[func.id]
            else:
                mod_src, orig_name = "", self._mod_aliases.get(func.id, func.id)
            if orig_name == "open" and mod_src == "os":
                if not _is_readonly_os_open(node, env, readonly_fd_helper=self._readonly_fd_helper):
                    primitive = "os.open"
            elif orig_name == "open":
                mode_node = node.args[1] if len(node.args) >= 2 else next(
                    (kw.value for kw in node.keywords if kw.arg == "mode"), None
                )
                if _mode_writes(mode_node, env):
                    primitive = "open"
            elif mod_src == "os" and orig_name in _OS_WRITE_ATTRS:
                primitive = f"os.{orig_name}"
            elif mod_src == "shutil" and orig_name in _SHUTIL_WRITE_ATTRS:
                primitive = f"shutil.{orig_name}"
            elif mod_src == "sqlite3" and orig_name == "connect":
                primitive = "sqlite3.connect"
            elif mod_src == "yaml" and orig_name in ("safe_dump", "dump"):
                if len(node.args) >= 2 or any(kw.arg == "stream" for kw in node.keywords):
                    primitive = f"yaml.{orig_name}"
            elif mod_src == "tempfile" and orig_name in _TEMPFILE_ATTRS:
                primitive = f"tempfile.{orig_name}"
            elif mod_src == "subprocess" and orig_name in _SUBPROCESS_FUNCS:
                primitive = _subprocess_mutation_primitive(node, env)
            elif orig_name in _WRITE_HELPERS:
                primitive = orig_name
        if primitive is not None:
            self._record(primitive, node)
        self.generic_visit(node)


def _iter_tool_python_files(root: Path) -> list[Path]:
    tools_root = root / "tools"
    found: list[Path] = []
    if not tools_root.is_dir() or tools_root.is_symlink():
        return found
    for dirpath, dirnames, filenames in os.walk(tools_root, followlinks=False):
        current = Path(dirpath)
        dirnames[:] = sorted(
            name for name in dirnames
            if name != "__pycache__" and not name.endswith(".egg-info") and not (current / name).is_symlink()
        )
        for name in sorted(filenames):
            if not name.endswith(".py"):
                continue
            candidate = current / name
            if not candidate.is_symlink() and candidate.is_file():
                found.append(candidate)
    return found


def _scan_static_tree(
    root: Path = ROOT,
    effects: dict[str, dict] | None = None,
) -> tuple[Counter, dict[str, tuple[str, int]], set[str], list[str]]:
    declared = effects or {}
    undeclared_counts: Counter = Counter()
    first_seen: dict[str, tuple[str, int]] = {}
    writer_modules: set[str] = set()
    unmediated_failures: list[str] = []

    for path in _iter_tool_python_files(root):
        rel = path.relative_to(root).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        visitor = _Visitor(rel)
        visitor.visit(tree)
        forbidden_unmediated = (
            visitor.unmediated_call_lines
            if rel == _CANONICAL_ENGINE_MODULE
            else visitor.unmediated_lines
        )
        for lineno in sorted(set(forbidden_unmediated)):
            unmediated_failures.append(
                f"A2 {rel}:{lineno}: _unmediated_test_only is forbidden anywhere under tools/ (CL-50)"
            )
        if visitor.hits:
            writer_modules.add(rel)
        if rel not in declared:
            for signature, lineno in visitor.hits:
                undeclared_counts[signature] += 1
                first_seen.setdefault(signature, (rel, lineno))

    return undeclared_counts, first_seen, writer_modules, unmediated_failures


def _collect_static(
    root: Path = ROOT,
    effects: dict[str, dict] | None = None,
) -> tuple[Counter, dict[str, tuple[str, int]]]:
    """Return undeclared AST write-primitive counts and first-seen locations."""
    if effects is None:
        raw = _load_effects_yaml()
        effects = raw if isinstance(raw, dict) else {}
    undeclared_counts, first_seen, _, _ = _scan_static_tree(root, effects)
    return undeclared_counts, first_seen


# ---------------------------------------------------------------------------
# P2A-01: write-site destination conformance for declared modules.
#
# Presence in effects.yaml is not an uninspected pass.  For every declared
# module (except the canonical engine and the caller-scoped fs primitives) each
# write site's target expression is abstractly resolved to one of:
#   _RepoRel   anchored at the repository root (``Path(__file__)``-derived
#              constants, or ``root``/``repo_root``/``core_root``/``repo``
#              parameters by LearningOS convention), with ``*``/``**`` for
#              unknown segments;
#   _ExtRel    anchored outside the repository (tempdir, home, sibling of the
#              repository root, an absolute literal, or a guarded caller path);
#   _Param     a parameter of the enclosing function, resolved through every
#              intra-module call site (and parameter defaults);
#   _Unknown   caller-controlled or unresolvable;
#   _BadTraversal  a ``..`` segment joined onto a repository-anchored path.
# Anchored repository writes must be covered by the module's declared
# repository destinations; modules declaring only repository destinations may
# not perform unanchored or external writes; explicit-out modules must call a
# recognized output-boundary guard.  This is a destination conformance check
# for declared writers. Imported tools/ constants and pure path helpers are
# resolved on demand; a path passed into a writer by an unknown caller remains
# unanchored.
# ---------------------------------------------------------------------------

_SITE_EXCLUDED_MODULES = frozenset({_CANONICAL_ENGINE_MODULE, "tools/learning_os/store/fs.py"})
_ROOT_PARAM_NAMES = frozenset({"root", "repo_root", "core_root", "repo"})
# Parameters that share a root-like name but are documented non-repository
# roots.  ReadingCardStore(root=...) is the external reading-memory store root.
_NON_REPO_ROOT_PARAMS: dict[str, frozenset[str]] = {
    "tools/learning_os/store/materials/reading_cards.py": frozenset({"root"}),
}
_EXPLICIT_OUT_MARKERS = (
    "<EXPLICIT_OUT_DIR>/",
    "<EXPLICIT_OUT_FILE>",
    "<EXPLICIT_REPORT_OUT>",
    "<EXPLICIT_LOCAL_OUTPUT>",
    "<OUT_DIR>/",
    "<PRIVATE_REPORT_DIR>/",
)
_PATH_CTORS = frozenset({"Path", "PurePath", "PosixPath", "PurePosixPath"})
_IDENTITY_FUNCS = frozenset({
    "str", "os.fspath", "os.path.realpath", "os.path.abspath", "os.path.normpath",
    "os.path.expanduser", "os.fsencode", "os.fsdecode",
})
_IDENTITY_METHODS = frozenset({"resolve", "absolute", "expanduser", "as_posix"})
_PARENT_TOKEN = "\x00parent"
_MAX_VALUES = 64
_MAX_INLINE_DEPTH = 6


@dataclass(frozen=True)
class _RepoRel:
    parts: tuple[str, ...]


@dataclass(frozen=True)
class _Relative:
    parts: tuple[str, ...]


@dataclass(frozen=True)
class _ExtRel:
    tag: str
    parts: tuple[str, ...] = ()


@dataclass(frozen=True)
class _Param:
    func: ast.AST
    name: str
    suffix: tuple[str, ...]


@dataclass(frozen=True)
class _Unknown:
    why: str


@dataclass(frozen=True)
class _Null:
    """An optional path's None branch, which cannot be a path operand."""


@dataclass(frozen=True)
class _BadTraversal:
    text: str


@dataclass(frozen=True)
class _ReadOnlySQLite:
    """A percent-encoded Path URI with a fixed SQLite read-only mode."""


def _describe(value: object) -> str:
    if isinstance(value, _RepoRel):
        return "repo:" + ("/".join(value.parts) or ".")
    if isinstance(value, _Relative):
        return "cwd-relative:" + ("/".join(value.parts) or ".")
    if isinstance(value, _ExtRel):
        return f"external:{value.tag}/" + "/".join(value.parts)
    if isinstance(value, _BadTraversal):
        return f"traversal:{value.text}"
    if isinstance(value, _Unknown):
        return f"unanchored ({value.why})"
    if isinstance(value, _Param):
        return f"parameter {value.name}"
    return repr(value)


def _norm_parts(parts: tuple[str, ...]) -> tuple[str, ...]:
    out: list[str] = []
    for part in parts:
        if part == "**" and out and out[-1] == "**":
            continue
        out.append(part)
    return tuple(out)


def _parse_path_text(text: str) -> tuple[str, tuple[str, ...]]:
    """Return (kind, segments); kind is rel | abs | home | bad.  ``\\x01`` marks formatted values."""
    if text.startswith("/"):
        return "abs", ()
    if text.startswith("~"):
        return "home", ()
    segs: list[str] = []
    for seg in text.split("/"):
        if seg in {"", "."}:
            continue
        if seg == "..":
            return "bad", ()
        if seg == "**":
            segs.append("**")
        elif "\x01" in seg:
            segs.append(seg.replace("\x01", "*"))
        elif any(ch in seg for ch in "*?["):
            segs.append("*")
        else:
            segs.append(seg)
    return "rel", tuple(segs)


def _pattern_covers(pattern: str, vparts: tuple[str, ...]) -> bool:
    """True iff every path matched by value pattern ``vparts`` matches declared ``pattern``."""
    pparts = tuple(write_scopes.normalize_scope_pattern(pattern).split("/"))

    @cache
    def match(i: int, j: int) -> bool:
        if i == len(pparts):
            return j == len(vparts)
        token = pparts[i]
        if token == "**":
            return match(i + 1, j) or (j < len(vparts) and match(i, j + 1))
        if j == len(vparts):
            return False
        value = vparts[j]
        if token == "*":
            return value != "**" and match(i + 1, j + 1)
        return value == token and match(i + 1, j + 1)

    return match(0, 0)


def _checkout_state_covers(destination: str, value: _ExtRel, primitive: str) -> bool:
    parts = value.parts
    if value.tag == "git directory":
        if not parts or parts[0] != "learningos":
            return False
        parts = parts[1:]
    elif value.tag != "tempdir":
        return False

    if not parts:
        return primitive == "mkdir" and value.tag == "git directory"
    pattern = destination.removeprefix("<STATE>/").split("/")

    @cache
    def match(pattern_index: int, part_index: int) -> bool:
        if pattern_index == len(pattern):
            return part_index == len(parts)
        segment = pattern[pattern_index]
        if segment == "**":
            return match(pattern_index + 1, part_index) or (
                part_index < len(parts) and match(pattern_index, part_index + 1)
            )
        if part_index == len(parts):
            return False
        part = parts[part_index]
        if part == "**":
            return False
        compatible = part == segment or segment == "*" or (
            "*" not in part and fnmatchcase(part, segment)
        )
        return compatible and match(pattern_index + 1, part_index + 1)

    return match(0, 0)


def _is_destination_parent(pattern: str, parts: tuple[str, ...]) -> bool:
    declared = pattern.split("/")
    return bool(parts) and len(parts) < len(declared) and all(
        child == parent or (parent == "*" and child != "**")
        for child, parent in zip(parts, declared, strict=False)
    )


def _iter_local(node: ast.AST):
    """Yield nodes of one scope without descending into nested defs/lambdas/classes."""
    stack = list(ast.iter_child_nodes(node))
    while stack:
        cur = stack.pop()
        yield cur
        if isinstance(cur, (
            ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef,
            ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp,
        )):
            continue
        stack.extend(ast.iter_child_nodes(cur))


def _synthetic_call(name: str, *args: ast.AST) -> ast.Call:
    return ast.Call(func=ast.Name(id=name, ctx=ast.Load()), args=list(args), keywords=[])


class _Scope:
    def __init__(self, node: ast.AST, parent: _Scope | None, cls: str | None, qualname: str):
        self.node = node
        self.parent = parent
        self.cls = cls
        self.qualname = qualname
        self.params: list[str] = []
        self.kwonly: list[str] = []
        self.defaults: dict[str, ast.AST] = {}
        self.star_params: set[str] = set()
        self.assigns: dict[str, list[ast.AST]] = {}
        self.globals: set[str] = set()
        self.appends: dict[str, list[ast.AST]] = {}
        self.returns: list[ast.AST] = []
        self.nested: dict[str, _Scope] = {}
        self.calls: list[ast.Call] = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = node.args
            positional = [a.arg for a in (*args.posonlyargs, *args.args)]
            self.params = positional
            self.kwonly = [a.arg for a in args.kwonlyargs]
            for name, default in zip(positional[len(positional) - len(args.defaults):], args.defaults, strict=True):
                self.defaults[name] = default
            for arg, default in zip(args.kwonlyargs, args.kw_defaults, strict=True):
                if default is not None:
                    self.defaults[arg.arg] = default
            for star in (args.vararg, args.kwarg):
                if star is not None:
                    self.star_params.add(star.arg)

    @property
    def all_params(self) -> set[str]:
        return set(self.params) | set(self.kwonly) | self.star_params

    def bind(self, name: str, value: ast.AST) -> None:
        self.assigns.setdefault(name, []).append(value)


class _ModuleWriteSites:
    """Abstract target resolution for one declared module (P2A-01)."""

    def __init__(
        self, rel: str, tree: ast.Module, load_module: Callable[[str], _ModuleWriteSites | None],
    ):
        self.rel = rel
        self.tree = tree
        self._load_module = load_module
        self.non_root_params = _NON_REPO_ROOT_PARAMS.get(rel, frozenset())
        self.from_aliases: dict[str, tuple[str, str]] = {}
        self.mod_aliases: dict[str, str] = {}
        self.module = _Scope(tree, None, None, "<module>")
        self.scopes: dict[ast.AST, _Scope] = {tree: self.module}
        self.module_funcs: dict[str, _Scope] = {}
        self.global_assignments: dict[str, list[tuple[_Scope, ast.AST]]] = {}
        self.class_methods: dict[str, dict[str, _Scope]] = {}
        self.class_attrs: dict[str, dict[str, list[tuple[ast.AST, _Scope]]]] = {}
        self.class_body: dict[str, dict[str, list[ast.AST]]] = {}
        self.escaped: set[_Scope] = set()
        self.call_sites: dict[_Scope, list[tuple[ast.Call, _Scope]]] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.mod_aliases[alias.asname or alias.name.split(".", 1)[0]] = alias.name
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    self.from_aliases[alias.asname or alias.name] = (node.module or "", alias.name)
        self.root_arguments = {
            argument.value[2:]
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument"
            for argument in node.args
            if isinstance(argument, ast.Constant) and argument.value in ("--root", "--repo")
        }
        self._index_scope(self.module, tree.body, cls=None)
        self._index_calls()

    # -- indexing ---------------------------------------------------------
    def _index_scope(self, scope: _Scope, body: list[ast.stmt], cls: str | None) -> None:
        holder = ast.Module(body=body, type_ignores=[])
        local = list(_iter_local(holder))
        scope.globals.update(name for node in local if isinstance(node, ast.Global) for name in node.names)
        for node in local:
            self._collect_binding(scope, node, cls)
            if isinstance(node, ast.Call):
                scope.calls.append(node)
            if isinstance(node, ast.Return) and node.value is not None:
                scope.returns.append(node.value)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qual = node.name if scope is self.module else f"{scope.qualname}.{node.name}"
                child = _Scope(node, scope, cls, qual)
                self.scopes[node] = child
                if scope is self.module:
                    self.module_funcs[node.name] = child
                else:
                    scope.nested[node.name] = child
                self._index_scope(child, node.body, cls)
                for default in (*node.args.defaults, *[d for d in node.args.kw_defaults if d is not None]):
                    for sub in ast.walk(default):
                        if isinstance(sub, ast.Call):
                            scope.calls.append(sub)
            elif isinstance(node, ast.ClassDef):
                self.class_body.setdefault(node.name, {})
                self.class_methods.setdefault(node.name, {})
                for stmt in node.body:
                    if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method = _Scope(stmt, self.module, node.name, f"{node.name}.{stmt.name}")
                        self.scopes[stmt] = method
                        self.class_methods[node.name][stmt.name] = method
                        self._index_scope(method, stmt.body, node.name)
                    elif isinstance(stmt, ast.Assign):
                        for target in stmt.targets:
                            if isinstance(target, ast.Name):
                                self.class_body[node.name].setdefault(target.id, []).append(stmt.value)
                    elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name) and stmt.value:
                        self.class_body[node.name].setdefault(stmt.target.id, []).append(stmt.value)

    def _collect_binding(self, scope: _Scope, node: ast.AST, cls: str | None) -> None:
        def bind_target(target: ast.AST, value: ast.AST) -> None:
            if isinstance(target, ast.Name):
                if target.id in scope.globals and scope is not self.module:
                    self.global_assignments.setdefault(target.id, []).append((scope, value))
                else:
                    scope.bind(target.id, value)
            elif isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) \
                    and target.value.id == "self" and cls:
                self.class_attrs.setdefault(cls, {}).setdefault(target.attr, []).append((value, scope))
            elif isinstance(target, (ast.Tuple, ast.List)):
                if isinstance(value, (ast.Tuple, ast.List)) and len(value.elts) == len(target.elts):
                    for sub_t, sub_v in zip(target.elts, value.elts, strict=True):
                        bind_target(sub_t, sub_v)
                else:
                    for index, sub_t in enumerate(target.elts):
                        bind_target(sub_t, _synthetic_call("__tuple_item__", value, ast.Constant(index)))

        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and isinstance(node.value, ast.Call) \
                        and isinstance(func := node.value.func, ast.Attribute) \
                        and func.attr in _IDENTITY_METHODS and isinstance(func.value, ast.Name) \
                        and func.value.id == target.id:
                    continue
                bind_target(target, node.value)
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            bind_target(node.target, node.value)
        elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
            scope.bind(node.target.id, ast.BinOp(
                left=ast.Name(id=node.target.id, ctx=ast.Load()), op=node.op, right=node.value))
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            bind_target(node.target, _synthetic_call("__iter_child__", node.iter))
        elif isinstance(node, ast.withitem) and node.optional_vars is not None:
            bind_target(node.optional_vars, node.context_expr)
        elif isinstance(node, ast.NamedExpr):
            bind_target(node.target, node.value)

        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr == "append" and isinstance(node.func.value, ast.Name) and len(node.args) == 1:
            scope.appends.setdefault(node.func.value.id, []).append(node.args[0])

    def _callee_scope(self, func: ast.AST, scope: _Scope) -> _Scope | None:
        if isinstance(func, ast.Name):
            cursor: _Scope | None = scope
            while cursor is not None:
                if func.id in cursor.nested:
                    return cursor.nested[func.id]
                cursor = cursor.parent
            return self.module_funcs.get(func.id)
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            owner = func.value.id
            if owner in {"self", "cls"} and scope.cls:
                return self.class_methods.get(scope.cls, {}).get(func.attr)
            if owner in self.class_methods:
                return self.class_methods[owner].get(func.attr)
        return None

    def _index_calls(self) -> None:
        call_funcs: set[int] = set()
        for scope in list(self.scopes.values()):
            for call in scope.calls:
                call_funcs.add(id(call.func))
                callee = self._callee_scope(call.func, scope)
                if callee is not None:
                    self.call_sites.setdefault(callee, []).append((call, scope))
        # A function referenced as a value (callback, decorator, map target) has
        # callers this analysis cannot see: its parameters stay unanchored.
        for scope in list(self.scopes.values()):
            holder = scope.node
            for node in _iter_local(holder):
                if id(node) in call_funcs:
                    continue
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    target = self._callee_scope(node, scope)
                    if target is not None:
                        self.escaped.add(target)
                elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load) \
                        and isinstance(node.value, ast.Name) and node.value.id in {"self", "cls"}:
                    target = self._callee_scope(node, scope)
                    if target is not None:
                        self.escaped.add(target)
            if isinstance(holder, (ast.FunctionDef, ast.AsyncFunctionDef)) and holder.decorator_list:
                decorators = {
                    d.id if isinstance(d, ast.Name) else getattr(d, "attr", "")
                    for d in holder.decorator_list
                }
                if not decorators <= {"staticmethod", "classmethod", "property", "cache", "lru_cache"}:
                    self.escaped.add(scope)

    # -- evaluation -------------------------------------------------------
    def _dotted(self, node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            if node.id in self.from_aliases:
                mod, orig = self.from_aliases[node.id]
                return f"{mod}.{orig}" if mod else orig
            return self.mod_aliases.get(node.id, node.id)
        if isinstance(node, ast.Attribute):
            base = self._dotted(node.value)
            return f"{base}.{node.attr}" if base else None
        return None

    def _imported_member(self, dotted: str) -> tuple[_ModuleWriteSites, str] | None:
        module_name, sep, member = dotted.rpartition(".")
        if sep and (mod := self._load_module(module_name)) is not None:
            return mod, member
        return None

    def _imported_value(self, dotted: str, depth: int, active: frozenset) -> frozenset | None:
        imported = self._imported_member(dotted)
        if imported is None:
            return None
        mod, name = imported
        key = ("imported", mod.rel, name)
        if key in active or depth >= _MAX_INLINE_DEPTH:
            return frozenset({_Unknown(f"recursive or deep import {dotted}")})
        return mod._eval_name(name, mod.module, None, depth + 1, active | {key})

    def _param_value(self, scope: _Scope, name: str) -> object:
        if name in _ROOT_PARAM_NAMES and name not in self.non_root_params:
            return _RepoRel(())
        if name in scope.star_params:
            return _Unknown(f"variadic parameter {name}")
        return _Param(scope.node, name, ())

    def eval(self, node: ast.AST | None, scope: _Scope, bindings: dict | None = None,
             depth: int = 0, active: frozenset = frozenset()) -> frozenset:
        values = self._eval(node, scope, bindings, depth, active)
        if len(values) > _MAX_VALUES:
            return frozenset({_Unknown("value explosion")})
        return values

    def _eval(self, node, scope, bindings, depth, active) -> frozenset:
        if node is None:
            return frozenset({_Unknown("missing expression")})
        if isinstance(node, ast.Name):
            if node.id == "__file__":
                return frozenset({_RepoRel(tuple(self.rel.split("/")))})
            return self._eval_name(node.id, scope, bindings, depth, active)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (str, bytes)):
                text = node.value if isinstance(node.value, str) else os.fsdecode(node.value)
                kind, parts = _parse_path_text(text)
                if kind == "abs":
                    return frozenset({_ExtRel("absolute literal")})
                if kind == "home":
                    return frozenset({_ExtRel("home")})
                if kind == "rel":
                    return frozenset({_Relative(parts)})
                return frozenset({_BadTraversal(text)})
            if node.value is None:
                return frozenset({_Null()})
            return frozenset({_Unknown("non-path constant")})
        if isinstance(node, ast.JoinedStr):
            first = node.values[0] if node.values else None
            if isinstance(first, ast.Constant) and isinstance(first.value, str) and first.value.startswith("/"):
                return frozenset({_ExtRel("absolute literal")})
            return frozenset({_Unknown("formatted string")})
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add) \
                and isinstance(node.right, ast.Constant) and node.right.value in {"?mode=ro", "?mode=rw"} \
                and isinstance(node.left, ast.Call) and isinstance(node.left.func, ast.Attribute) \
                and node.left.func.attr == "as_uri":
            if node.right.value == "?mode=ro":
                return frozenset({_ReadOnlySQLite()})
            return self.eval(node.left.func.value, scope, bindings, depth, active)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            left = self.eval(node.left, scope, bindings, depth, active)
            segs = self._segments(node.right, scope, bindings, depth, active)
            return frozenset(self._join(value, seg) for value in left for seg in segs)
        if isinstance(node, ast.IfExp):
            return self.eval(node.body, scope, bindings, depth, active) | \
                self.eval(node.orelse, scope, bindings, depth, active)
        if isinstance(node, ast.BoolOp):
            out: frozenset = frozenset()
            for value in node.values:
                out |= self.eval(value, scope, bindings, depth, active)
            return out
        if isinstance(node, ast.NamedExpr):
            return self.eval(node.value, scope, bindings, depth, active)
        if isinstance(node, ast.Attribute):
            return self._eval_attribute(node, scope, bindings, depth, active)
        if isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Attribute) and node.value.attr == "parents" \
                    and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, int):
                base = self.eval(node.value.value, scope, bindings, depth, active)
                for _ in range(node.slice.value + 1):
                    base = frozenset(self._parent(v) for v in base)
                return base
            return frozenset({_Unknown("subscript")})
        if isinstance(node, ast.Call):
            return self._eval_call(node, scope, bindings, depth, active)
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            return frozenset({_Unknown("container")})
        return frozenset({_Unknown(type(node).__name__)})

    def _eval_name(self, name, scope, bindings, depth, active) -> frozenset:
        cursor: _Scope | None = scope
        current_bindings = bindings
        while cursor is not None:
            is_param = name in cursor.all_params
            global_assignments = self.global_assignments.get(name, ()) if cursor is self.module else ()
            if is_param or name in cursor.assigns or global_assignments:
                key = ("name", id(cursor), name, id(current_bindings))
                if current_bindings is not None and name in current_bindings:
                    base = frozenset(current_bindings[name])
                elif is_param:
                    if current_bindings is not None and name in cursor.defaults:
                        base = self.eval(cursor.defaults[name], cursor.parent or self.module,
                                         None, depth, active)
                    else:
                        base = frozenset({self._param_value(cursor, name)})
                else:
                    base = frozenset()
                if key in active:
                    return base | frozenset({_Unknown("__cycle__")})
                values = set(base)
                inner = active | {key}
                cycled = False
                for expr in cursor.assigns.get(name, []):
                    result = self.eval(expr, cursor, current_bindings, depth, inner)
                    if _Unknown("__cycle__") in result:
                        cycled = True
                        result = result - {_Unknown("__cycle__")}
                    values |= result
                for defining_scope, expr in global_assignments:
                    values |= self.eval(expr, defining_scope, None, depth, inner)
                if cycled:
                    values |= {_RepoRel(_norm_parts((*v.parts, "**"))) for v in values if isinstance(v, _RepoRel)}
                    values |= {
                        _Param(v.func, v.name, (*v.suffix, "**")) for v in values if isinstance(v, _Param)
                    }
                return frozenset(values)
            cursor = cursor.parent
            current_bindings = None
        if name in self.module_funcs or name in self.class_methods:
            return frozenset({_Unknown(f"callable {name}")})
        imported = self._imported_value(self._dotted(ast.Name(id=name)) or name, depth, active)
        return imported if imported is not None else frozenset({_Unknown(f"name {name}")})

    def _eval_attribute(self, node: ast.Attribute, scope, bindings, depth, active) -> frozenset:
        if node.attr == "parent":
            return frozenset(self._parent(v) for v in self.eval(node.value, scope, bindings, depth, active))
        if isinstance(node.value, ast.Name):
            owner = node.value.id
            if node.attr == "stdout":
                git_root = self._git_root_result(owner, scope)
                if git_root:
                    return frozenset({_RepoRel(())})
            if node.attr == "root" and isinstance(scope.node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                annotated_repo = any(
                    arg.arg == owner and isinstance(arg.annotation, ast.Name)
                    and arg.annotation.id == "Repo" for arg in scope.node.args.args
                )
                if annotated_repo and owner not in scope.assigns:
                    return frozenset({_RepoRel(())})
            if node.attr in self.root_arguments:
                assignments = self._lookup_exprs(owner, scope)
                if assignments and all(
                    isinstance(expr, ast.Call) and isinstance(expr.func, ast.Attribute)
                    and expr.func.attr == "parse_args" for expr in assignments
                ):
                    return frozenset({_RepoRel(())})
            cls = scope.cls if owner in {"self", "cls"} else (owner if owner in self.class_body else None)
            if cls is not None:
                key = ("attr", cls, node.attr)
                if key in active:
                    return frozenset({_Unknown("__cycle__")})
                inner = active | {key}
                values: set = set()
                for expr, defining in self.class_attrs.get(cls, {}).get(node.attr, []):
                    values |= self.eval(expr, defining, None, depth, inner)
                for expr in self.class_body.get(cls, {}).get(node.attr, []):
                    values |= self.eval(expr, self.module, None, depth, inner)
                if values:
                    return frozenset(values)
                return frozenset({_Unknown(f"attribute {owner}.{node.attr}")})
        dotted = self._dotted(node)
        imported = self._imported_value(dotted or "", depth, active)
        return imported if imported is not None else frozenset({_Unknown(f"attribute {dotted or node.attr}")})

    def _git_root_result(self, name: str, scope: _Scope) -> bool:
        assignments = self._lookup_exprs(name, scope)
        if len(assignments) != 1 or not isinstance(call := assignments[0], ast.Call) \
                or self._dotted(call.func) != "subprocess.run" or not call.args \
                or not isinstance(command := call.args[0], ast.List):
            return False
        return [arg.value if isinstance(arg, ast.Constant) else None for arg in command.elts] == [
            "git", "rev-parse", "--show-toplevel",
        ]

    def _eval_call(self, node: ast.Call, scope, bindings, depth, active) -> frozenset:
        func = node.func
        kwargs = {kw.arg: kw.value for kw in node.keywords if kw.arg}

        def ev(expr):
            return self.eval(expr, scope, bindings, depth, active)

        if isinstance(func, ast.Name) and func.id == "__iter_child__":
            return self._iter_child(node.args[0], scope, bindings, depth, active)
        if isinstance(func, ast.Name) and func.id == "__tuple_item__":
            return self._tuple_item(node.args[0], node.args[1].value, scope, bindings, depth, active)  # type: ignore[attr-defined]
        dotted = self._dotted(func) or ""
        leaf = dotted.rsplit(".", 1)[-1]
        if leaf in _PATH_CTORS and (dotted == leaf or dotted.startswith("pathlib.")):
            if not node.args:
                return frozenset({_Unknown("Path() without argument")})
            values = ev(node.args[0])
            for extra in node.args[1:]:
                segs = self._segments(extra, scope, bindings, depth, active)
                values = frozenset(self._join(v, s) for v in values for s in segs)
            return values
        if dotted.endswith("Path.home") or dotted == "os.path.expanduser":
            if dotted == "os.path.expanduser" and node.args:
                return ev(node.args[0])
            return frozenset({_ExtRel("home")})
        if dotted.endswith("Path.cwd") or dotted == "os.getcwd":
            return frozenset({_Unknown("cwd")})
        if dotted in _IDENTITY_FUNCS:
            return ev(node.args[0]) if node.args else frozenset({_Unknown(dotted)})
        if dotted == "os.path.dirname":
            return frozenset(self._parent(v) for v in ev(node.args[0])) if node.args \
                else frozenset({_Unknown(dotted)})
        if dotted == "os.path.join":
            if not node.args:
                return frozenset({_Unknown(dotted)})
            values = ev(node.args[0])
            for extra in node.args[1:]:
                segs = self._segments(extra, scope, bindings, depth, active)
                values = frozenset(self._join(v, s) for v in values for s in segs)
            return values
        if dotted.startswith("tempfile.") or (isinstance(func, ast.Name) and func.id in self.from_aliases
                                              and self.from_aliases[func.id][0] == "tempfile"):
            if "dir" in kwargs:
                return frozenset(self._join(v, ("*",)) for v in ev(kwargs["dir"]))
            return frozenset({_ExtRel("tempdir")})
        if dotted == "learning_os.store.contracts.write_scopes.guard_tool_output_path":
            return frozenset({_ExtRel("guarded caller output")})
        if dotted == "learning_os.store.contracts.write_scopes.scoped_write_target" and len(node.args) == 3:
            patterns = self._scope_patterns(node.args[2], scope)
            if not patterns:
                return frozenset({_Unknown("unresolved runtime write scope")})
            return frozenset(
                self._join(base, tuple(pattern.split("/")))
                for base in ev(node.args[0]) for pattern in patterns
            )
        if dotted == "tempfile.gettempdir":
            return frozenset({_ExtRel("tempdir")})
        if dotted == "_git_dir" and self.rel == "tools/learning_os/store/session_ledger.py":
            # Git resolves this checkout's metadata directory, which can be
            # outside the working tree for linked worktrees and gitfiles.
            return frozenset({_ExtRel("git directory"), _Null()})
        if dotted in {"os.environ.get", "os.getenv"}:
            return frozenset({_Unknown("environment variable")})
        if isinstance(func, ast.Attribute):
            if func.attr in _IDENTITY_METHODS or (func.attr == "strip" and not node.args and not node.keywords):
                return ev(func.value)
            if func.attr == "relative_to" and len(node.args) == 1 and not node.keywords:
                result = set()
                for child in ev(func.value):
                    for parent in ev(node.args[0]):
                        if isinstance(child, _RepoRel) and isinstance(parent, _RepoRel) \
                                and child.parts[:len(parent.parts)] == parent.parts:
                            result.add(_Relative(child.parts[len(parent.parts):]))
                        else:
                            result.add(_Unknown("relative_to a different or unresolved root"))
                return frozenset(result)
            if func.attr == "joinpath":
                values = ev(func.value)
                for extra in node.args:
                    segs = self._segments(extra, scope, bindings, depth, active)
                    values = frozenset(self._join(v, s) for v in values for s in segs)
                return values
            if func.attr in {"with_suffix", "with_name", "with_stem"}:
                return frozenset(self._join(self._parent(v), ("*",)) for v in ev(func.value))
            if func.attr in {"iterdir", "glob", "rglob"}:
                return self._iter_child(node, scope, bindings, depth, active)
        callee = self._callee_scope(func, scope)
        if callee is not None:
            return self._inline(callee, node, scope, bindings, depth, active)
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Attribute) \
                and isinstance(func.value.value, ast.Name) and func.value.value.id == "self" and scope.cls:
            alternatives = self.class_attrs.get(scope.cls, {}).get(func.value.attr, ())
            if alternatives:
                values = set()
                for obj, _ in alternatives:
                    imported = self._imported_member(self._dotted(obj.func) or "") if isinstance(obj, ast.Call) else None
                    if imported is not None:
                        mod, cls = imported
                        method = mod.class_methods.get(cls, {}).get(func.attr)
                        if method is not None:
                            bound = self._call_bindings(method, node, scope, bindings, depth, active)
                            values.update(mod._eval_returns(method, bound, depth, active))
                            continue
                    values.add(_Unknown(f"unresolved receiver {func.value.attr}"))
                return frozenset(values)
        imported = self._imported_member(dotted)
        if imported is not None:
            mod, name = imported
            callee = mod.module_funcs.get(name)
            if callee is not None:
                bound = self._call_bindings(callee, node, scope, bindings, depth, active)
                return mod._eval_returns(callee, bound, depth, active)
        return frozenset({_Unknown(f"call {dotted or type(func).__name__}")})

    def _call_bindings(self, callee: _Scope, call: ast.Call, scope, bindings, depth, active) -> dict | None:
        params = list(callee.params)
        if params and isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name) \
                and call.func.value.id in {"self", "cls"} and params[0] in {"self", "cls"}:
            params = params[1:]
        elif params and params[0] in {"self", "cls"} and callee.cls:
            params = params[1:]
        bound: dict[str, frozenset] = {}
        for index, arg in enumerate(call.args):
            if isinstance(arg, ast.Starred):
                return None
            if index < len(params):
                bound[params[index]] = self.eval(arg, scope, bindings, depth, active)
        for kw in call.keywords:
            if kw.arg is None:
                return None
            bound[kw.arg] = self.eval(kw.value, scope, bindings, depth, active)
        return bound

    def _inline(self, callee: _Scope, call: ast.Call, scope, bindings, depth, active) -> frozenset:
        bound = self._call_bindings(callee, call, scope, bindings, depth, active)
        return self._eval_returns(callee, bound, depth, active)

    def _eval_returns(self, callee: _Scope, bound: dict | None, depth, active) -> frozenset:
        key = ("inline", callee.node)
        if depth >= _MAX_INLINE_DEPTH or key in active:
            return frozenset({_Unknown(f"recursive or deep call {callee.qualname}")})
        if not callee.returns:
            return frozenset({_Unknown(f"call {callee.qualname} returns no path")})
        if bound is None:
            return frozenset({_Unknown(f"starred call {callee.qualname}")})
        out: set = set()
        for expr in callee.returns:
            out |= self.eval(expr, callee, bound, depth + 1, active | {key})
        return frozenset(out)

    def _iter_child(self, expr: ast.AST, scope, bindings, depth, active) -> frozenset:
        if isinstance(expr, ast.Call):
            dotted = self._dotted(expr.func) or ""
            if dotted in {"sorted", "list", "reversed", "tuple", "set"} and expr.args:
                return self._iter_child(expr.args[0], scope, bindings, depth, active)
            if isinstance(expr.func, ast.Attribute):
                attr = expr.func.attr
                if attr in {"iterdir", "glob", "rglob"}:
                    base = self.eval(expr.func.value, scope, bindings, depth, active)
                    if attr == "iterdir":
                        segs: tuple[str, ...] = ("*",)
                    elif attr == "rglob":
                        segs = ("**",)
                    else:
                        pattern = expr.args[0] if expr.args else None
                        if isinstance(pattern, ast.Constant) and isinstance(pattern.value, str):
                            kind, parsed = _parse_path_text(pattern.value)
                            segs = parsed if kind == "rel" and parsed else ("**",)
                        else:
                            segs = ("**",)
                    return frozenset(self._join(v, segs) for v in base)
        if isinstance(expr, ast.IfExp):
            return (
                self._iter_child(expr.body, scope, bindings, depth, active)
                | self._iter_child(expr.orelse, scope, bindings, depth, active)
            )
        if isinstance(expr, (ast.List, ast.Tuple, ast.Set)):
            out: frozenset = frozenset()
            for elt in expr.elts:
                out |= self.eval(elt, scope, bindings, depth, active)
            return out or frozenset({_Unknown("empty iteration")})
        if isinstance(expr, ast.Name):
            key = ("iteration", scope.node, expr.id)
            if key in active:
                return frozenset({_Unknown("recursive iteration")})
            inner = active | {key}
            values = frozenset().union(*(
                self._iter_child(value, scope, bindings, depth, inner)
                for value in self._lookup_exprs(expr.id, scope)
                if not isinstance(value, (ast.List, ast.Tuple, ast.Set)) or value.elts
            ))
            values |= frozenset().union(*(
                self.eval(value, scope, bindings, depth, inner)
                for value in scope.appends.get(expr.id, ())
            ))
            if values:
                return values
        return frozenset({_Unknown("iteration")})

    def _lookup_exprs(self, name: str, scope: _Scope) -> list[ast.AST]:
        cursor: _Scope | None = scope
        while cursor is not None:
            if name in cursor.assigns:
                return cursor.assigns[name]
            if name in cursor.all_params:
                return []
            cursor = cursor.parent
        return []

    def _tuple_item(self, value: ast.AST, index: int, scope, bindings, depth, active) -> frozenset:
        if isinstance(value, ast.Call):
            dotted = self._dotted(value.func) or ""
            leaf = dotted.rsplit(".", 1)[-1]
            if dotted in {"__iter_child__", "sorted", "list", "reversed", "tuple"} and value.args:
                return self._tuple_item(value.args[0], index, scope, bindings, depth, active)
            if leaf in {"exclusive_temp_path", "_exclusive_temp_path"} and index == 1 and value.args:
                base = self.eval(value.args[0], scope, bindings, depth, active)
                return frozenset(self._join(self._parent(v), ("*",)) for v in base)
            if leaf == "mkstemp" and index == 1:
                for kw in value.keywords:
                    if kw.arg == "dir":
                        base = self.eval(kw.value, scope, bindings, depth, active)
                        return frozenset(self._join(v, ("*",)) for v in base)
                return frozenset({_ExtRel("tempdir")})
        if isinstance(value, ast.Name):
            rows = scope.appends.get(value.id, ())
            if rows:
                return frozenset().union(*(
                    self.eval(row.elts[index], scope, bindings, depth, active)
                    if isinstance(row, (ast.Tuple, ast.List)) and index < len(row.elts)
                    else frozenset({_Unknown("tuple element")})
                    for row in rows
                ))
        return frozenset({_Unknown("tuple element")})

    def _scope_patterns(self, expr: ast.AST, scope: _Scope) -> list[str] | None:
        if isinstance(expr, ast.Name):
            values = self._lookup_exprs(expr.id, scope)
            expr = values[0] if len(values) == 1 else expr
        if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Attribute) \
                and expr.func.attr == "values" and isinstance(expr.func.value, ast.Name):
            values = self._lookup_exprs(expr.func.value.id, scope)
            if len(values) == 1 and isinstance(values[0], ast.Dict):
                expr = ast.Tuple(elts=values[0].values)
        if not isinstance(expr, (ast.Tuple, ast.List, ast.Set)):
            return None
        patterns: list[str] = []
        for item in expr.elts:
            if isinstance(item, ast.Starred):
                entries = self._scope_patterns(item.value, scope)
                if entries is None:
                    return None
                patterns.extend(entries)
            else:
                texts = self._string_values(item, scope)
                if texts is None or any("\x01" in text for text in texts):
                    return None
                for text in texts:
                    try:
                        patterns.append(write_scopes.normalize_scope_pattern(text))
                    except write_scopes.WriteScopeError:
                        return None
        return patterns

    def _string_values(self, expr: ast.AST, scope: _Scope, seen: frozenset = frozenset()) -> list[str] | None:
        if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
            return [expr.value]
        if isinstance(expr, ast.JoinedStr):
            text = ""
            for part in expr.values:
                if isinstance(part, ast.Constant) and isinstance(part.value, str):
                    text += part.value
                else:
                    text += "\x01"
            return [text]
        if isinstance(expr, ast.Name) and expr.id not in seen:
            exprs = self._lookup_exprs(expr.id, scope)
            if not exprs:
                module_exprs = self.module.assigns.get(expr.id, [])
                exprs = module_exprs
            if exprs:
                out: list[str] = []
                for sub in exprs:
                    values = self._string_values(sub, scope, seen | {expr.id})
                    if values is None:
                        return None
                    out.extend(values)
                return out
        return None

    def _segments(self, expr: ast.AST, scope, bindings, depth, active) -> list[object]:
        texts = self._string_values(expr, scope)
        if texts is None:
            if isinstance(expr, ast.Attribute) and expr.attr == "name":
                return [("*",)]
            return [
                value.parts if isinstance(value, _Relative) else
                value if isinstance(value, (_RepoRel, _ExtRel, _BadTraversal, _Param)) else ("**",)
                for value in self.eval(expr, scope, bindings, depth, active)
            ]
        out: list[object] = []
        for text in texts:
            kind, segs = _parse_path_text(text)
            if kind == "rel":
                out.append(segs)
            elif kind == "bad":
                out.append(_BadTraversal(text))
            else:
                out.append(_ExtRel(f"{kind} literal"))
        return out

    @staticmethod
    def _join(value: object, seg: object) -> object:
        if isinstance(seg, _BadTraversal):
            return seg if isinstance(value, (_RepoRel, _Param, _BadTraversal)) else value
        if isinstance(seg, (_ExtRel, _RepoRel)):
            return seg
        if isinstance(seg, _Param):
            return _Unknown("path join operand can replace its base")
        assert isinstance(seg, tuple)
        if isinstance(value, (_RepoRel, _Relative)):
            return type(value)(_norm_parts((*value.parts, *seg)))
        if isinstance(value, _Param):
            return _Param(value.func, value.name, (*value.suffix, *seg))
        if isinstance(value, _ExtRel):
            return _ExtRel(value.tag, _norm_parts((*value.parts, *seg)))
        return value

    @staticmethod
    def _parent(value: object) -> object:
        if isinstance(value, _RepoRel):
            if not value.parts:
                return _ExtRel("repository parent")
            if value.parts[-1] == "**":
                return value
            return _RepoRel(value.parts[:-1])
        if isinstance(value, _Param):
            return _Param(value.func, value.name, (*value.suffix, _PARENT_TOKEN))
        if isinstance(value, _ExtRel) and value.parts and value.parts[-1] != "**":
            return _ExtRel(value.tag, value.parts[:-1])
        if isinstance(value, _ExtRel) and not value.parts and value.tag == "guarded caller output":
            return _ExtRel("parent of guarded output")
        return value

    def apply_suffix(self, value: object, suffix: tuple[str, ...]) -> object:
        for token in suffix:
            value = self._parent(value) if token == _PARENT_TOKEN else self._join(value, (token,))
        return value

    # -- write sites ------------------------------------------------------
    @staticmethod
    def write_target_exprs(primitive: str, call: ast.Call) -> list[ast.AST | None] | None:
        """Target expressions for one write primitive; None means no path operand."""
        func = call.func
        args = call.args
        kwargs = {kw.arg: kw.value for kw in call.keywords if kw.arg}

        def arg(index: int, name: str) -> ast.AST | None:
            return args[index] if len(args) > index else kwargs.get(name)

        receiver = func.value if isinstance(func, ast.Attribute) else None
        if primitive in {"write_text", "write_bytes", "unlink", "mkdir", "rmdir", "touch",
                         "symlink_to", "hardlink_to", "Path.open"}:
            return [receiver]
        if primitive in {"rename", "replace"}:
            return [receiver, arg(0, "target")]
        if primitive in {"os.replace", "os.rename"}:
            return [arg(0, "src"), arg(1, "dst")]
        if primitive in {"os.link", "os.symlink"}:
            return [arg(1, "dst")]
        if primitive in {"os.remove", "os.unlink", "os.mkdir", "os.makedirs", "os.rmdir",
                         "os.chmod", "os.truncate", "os.open"}:
            if "dir_fd" in kwargs:
                return [ast.Constant(value=None)]
            return [arg(0, "path")]
        if primitive == "os.write":
            return None
        if primitive == "open":
            return [arg(0, "file")]
        if primitive == "shutil.move":
            return [arg(0, "src"), arg(1, "dst")]
        if primitive in {"shutil.copy", "shutil.copy2", "shutil.copyfile", "shutil.copytree"}:
            return [arg(1, "dst")]
        if primitive == "shutil.rmtree":
            return [arg(0, "path")]
        if primitive == "sqlite3.connect":
            return [arg(0, "database")]
        if primitive.startswith("tempfile."):
            return [kwargs.get("dir")] if "dir" in kwargs else None
        if primitive.startswith(("yaml.", "subprocess.")):
            return None
        if primitive in _WRITE_HELPERS:
            return [arg(0, "path")]
        return [None]

    def resolve_param(self, param: _Param, visited: set) -> set:
        key = (param.func, param.name, param.suffix)
        if key in visited:
            return set()
        visited.add(key)
        callee = self.scopes.get(param.func)
        if callee is None:
            return {_Unknown(f"parameter {param.name}")}
        sites = self.call_sites.get(callee, [])
        out: set = set()
        if not sites or callee in self.escaped:
            out.add(_Unknown(f"parameter {param.name!r} of {callee.qualname} is supplied outside this module"))
        for call, caller in sites:
            bound = self._call_bindings(callee, call, caller, None, 0, frozenset())
            if bound is None:
                out.add(_Unknown(f"starred call to {callee.qualname}"))
                continue
            if param.name in bound:
                values = bound[param.name]
            elif param.name in callee.defaults:
                values = self.eval(callee.defaults[param.name], callee.parent or self.module)
            else:
                out.add(_Unknown(f"parameter {param.name!r} of {callee.qualname} unbound at a call site"))
                continue
            for value in values:
                shifted = self.apply_suffix(value, param.suffix)
                if isinstance(shifted, _Param):
                    out |= self.resolve_param(shifted, visited)
                else:
                    out.add(shifted)
        return out

    def site_values(self, primitive: str, call: ast.Call, scope: _Scope) -> list[object]:
        if primitive in {"subprocess.git.mv", "subprocess.mv", "subprocess.cp", "subprocess.rm"}:
            return self._subprocess_targets(primitive, call, scope)
        dotted = self._dotted(call.func)
        if dotted == "learning_os.store.study_fence.write_local_output_file":
            return [_ExtRel("guarded caller output")]
        exprs = self.write_target_exprs(primitive, call)
        if exprs is None:
            if primitive.startswith("tempfile."):
                return [_ExtRel("tempdir")]
            return []
        boundary_values: frozenset | None = None
        for kw in call.keywords:
            if kw.arg == "boundary":
                candidate = self.eval(kw.value, scope)
                if candidate and all(isinstance(v, (_RepoRel, _ExtRel)) for v in candidate):
                    boundary_values = candidate
        out: list[object] = []
        for expr in exprs:
            if isinstance(expr, ast.Constant) and expr.value is None:
                out.append(_Unknown("dir_fd-relative target"))
                continue
            values = self.eval(expr, scope) if expr is not None else frozenset({_Unknown("unparsed target")})
            resolved: set = set()
            for value in values:
                if isinstance(value, _Param):
                    resolved |= self.resolve_param(value, set())
                else:
                    resolved.add(value)
            if boundary_values is not None and any(isinstance(v, _Unknown) for v in resolved):
                resolved = {v for v in resolved if not isinstance(v, _Unknown)}
                resolved |= {self._join(b, ("**",)) for b in boundary_values}
            if resolved == {_Null()}:
                resolved = {_Unknown("no path operand")}
            else:
                resolved.discard(_Null())
            out.extend(sorted(resolved, key=_describe))
        return out

    def _subprocess_targets(self, primitive: str, call: ast.Call, scope: _Scope) -> list[object]:
        command = call.args[0] if call.args else next(
            (kw.value for kw in call.keywords if kw.arg == "args"), None
        )
        if isinstance(command, ast.Name):
            assignments = self._lookup_exprs(command.id, scope)
            command = assignments[0] if len(assignments) == 1 else None
        if not isinstance(command, (ast.List, ast.Tuple)):
            return [_Unknown("unresolved filesystem command")]
        start = 1
        if primitive == "subprocess.git.mv":
            start = next((i + 1 for i, item in enumerate(command.elts)
                          if isinstance(item, ast.Constant) and item.value == "mv"), len(command.elts))
        operands = [
            item for item in command.elts[start:]
            if not (isinstance(item, ast.Constant) and isinstance(item.value, str)
                    and item.value.startswith("-"))
        ]
        if primitive == "subprocess.cp":
            operands = operands[-1:]
        if not operands:
            return [_Unknown("filesystem command has no resolved path operands")]
        cwd = next((kw.value for kw in call.keywords if kw.arg == "cwd"), None)
        roots = self.eval(cwd, scope)
        values: set = set()
        for item in operands:
            for target in self.eval(item, scope):
                if isinstance(target, _Relative):
                    values.update(self._join(root, target.parts) for root in roots)
                else:
                    values.add(target)
        return sorted(values, key=_describe)

class _SiteVisitor(_Visitor):
    def __init__(self, rel: str):
        super().__init__(rel)
        self._scope_nodes: list[ast.AST] = []
        self.sites: list[tuple[str, ast.Call, ast.AST | None]] = []

    def _push_func(self, name: str, node: ast.AST) -> None:
        self._scope_nodes.append(node)
        super()._push_func(name, node)
        self._scope_nodes.pop()

    def _record(self, primitive: str, node: ast.AST) -> None:
        super()._record(primitive, node)
        assert isinstance(node, ast.Call)
        self.sites.append((primitive, node, self._scope_nodes[-1] if self._scope_nodes else None))


def check_declared_write_sites(root: Path, effects: dict[str, dict]) -> list[str]:
    """P2A-01: every declared module's write sites must land inside its declaration."""
    failures: list[str] = []

    @cache
    def load_module(dotted: str) -> _ModuleWriteSites | None:
        parts = dotted.split(".")
        if not all(part.isidentifier() for part in parts):
            return None
        module_path = Path("tools", *parts)
        for relative in (module_path.with_suffix(".py"), module_path / "__init__.py"):
            path = root / relative
            if path.is_file():
                rel = relative.as_posix()
                return _ModuleWriteSites(rel, ast.parse(path.read_text(encoding="utf-8"), filename=rel), load_module)
        return None

    for rel in sorted(effects):
        if rel in _SITE_EXCLUDED_MODULES:
            continue
        path = root / rel
        if not path.is_file():
            continue
        destinations = [d for d in effects[rel].get("destinations") or [] if isinstance(d, str)]
        repo_patterns: list[str] = []
        for dest in destinations:
            if _is_external_or_placeholder(dest):
                continue
            try:
                if write_scopes.normalize_scope_pattern(dest) == dest:
                    repo_patterns.append(dest)
            except write_scopes.WriteScopeError:
                continue
        concrete = len(repo_patterns) == len(destinations)
        explicit_output = any(d.startswith(_EXPLICIT_OUT_MARKERS) for d in destinations)
        checkout_state_only = bool(destinations) and all(d.startswith("<STATE>/") for d in destinations)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        visitor = _SiteVisitor(rel)
        visitor.visit(tree)
        analysis = _ModuleWriteSites(rel, tree, load_module)
        reported: set[tuple[int, str]] = set()
        for primitive, call, scope_node in visitor.sites:
            scope = analysis.scopes.get(scope_node, analysis.module) if scope_node else analysis.module
            for value in analysis.site_values(primitive, call, scope):
                if isinstance(value, _ReadOnlySQLite) and primitive == "sqlite3.connect" and any(
                    kw.arg == "uri" and isinstance(kw.value, ast.Constant) and kw.value.value is True
                    for kw in call.keywords
                ):
                    continue
                problem: str | None = None
                if isinstance(value, _BadTraversal):
                    problem = "joins a '..' traversal onto a repository-anchored path"
                elif isinstance(value, _RepoRel):
                    if not repo_patterns:
                        problem = "is repository-anchored but the module declares no repository destination"
                    elif not any(
                        _pattern_covers(pattern, value.parts)
                        or (primitive == "mkdir" and _is_destination_parent(pattern, value.parts))
                        for pattern in repo_patterns
                    ):
                        problem = f"is outside declared destinations {repo_patterns}"
                elif concrete and isinstance(value, _ExtRel):
                    problem = "is external but the module declares only repository destinations"
                elif concrete and isinstance(value, (_Unknown, _Relative, _ReadOnlySQLite)):
                    problem = "is unanchored in a module that declares only repository destinations"
                elif (explicit_output or checkout_state_only) and isinstance(
                    value, (_Unknown, _Relative, _ReadOnlySQLite)
                ):
                    problem = "has no proved destination at this write site"
                elif checkout_state_only and isinstance(value, _ExtRel) and not any(
                    _checkout_state_covers(dest, value, primitive) for dest in destinations
                ):
                    problem = f"is outside declared checkout-state destinations {destinations}"
                elif explicit_output and isinstance(value, _ExtRel) and value.tag == "absolute literal":
                    problem = "uses an absolute path without a caller-output boundary"
                if problem is None:
                    continue
                key = (call.lineno, _describe(value))
                if key in reported:
                    continue
                reported.add(key)
                failures.append(
                    f"A2-sites {rel}:{call.lineno}: {primitive} target {_describe(value)} {problem} — {FIX}"
                )
    return failures


def scan_tools_census(
    root: Path,
    effects_raw: object,
    ratchet_entries: list[dict],
    *,
    tree_roots: frozenset[str] | None = None,
) -> list[str]:
    """Run the full tools/**/*.py AST census and return all A2-static violations."""
    effects, failures = validate_effects_declarations(
        effects_raw, root=root, data_roots=DATA_ROOTS, tree_roots=tree_roots,
    )
    recorded = {entry["signature"]: entry["count"] for entry in ratchet_entries}
    ratchet_modules = {sig.split("::", 1)[0] for sig in recorded}
    for rel in sorted(set(effects) & ratchet_modules):
        failures.append(f"A2 {rel}: appears in both effects.yaml and ratchets.yaml")

    undeclared_counts, first_seen, writer_modules, unmediated_failures = _scan_static_tree(
        root, effects,
    )
    failures.extend(unmediated_failures)

    for signature, count in sorted(undeclared_counts.items()):
        if recorded.get(signature, 0) < count:
            rel, lineno = first_seen[signature]
            failures.append(
                f"A2 {signature}: undeclared write ({count} > recorded {recorded.get(signature, 0)}) "
                f"— {rel}:{lineno} — {FIX}"
            )
    for signature in sorted(recorded):
        if signature not in undeclared_counts:
            failures.append(
                f"A2 {signature}: no longer occurs — remove the fixed exception from ratchets.yaml — {FIX}"
            )
    for rel in sorted(set(effects) - writer_modules):
        failures.append(
            f"A2 {rel}: stale zero-write declaration in effects.yaml (module has no write primitives)"
        )
    failures.extend(check_declared_write_sites(root, effects))
    return failures


def test_static_lint_matches_baseline():
    effects_raw = _load_effects_yaml()
    ratchet_entries = yaml.safe_load(
        RATCHETS_PATH.read_text(encoding="utf-8")
    )["checks"].get(RULE, [])
    failures = scan_tools_census(ROOT, effects_raw, ratchet_entries)
    assert not failures, "\n".join(failures)


def _synthetic_effects(tmp_path: Path) -> tuple[Path, dict]:
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools/writer_ok.py").write_text(
        "from pathlib import Path\n"
        "def run(root: Path):\n"
        "    (root / 'generated/reports/demo.txt').write_text('x', encoding='utf-8')\n",
        encoding="utf-8",
    )
    (tmp_path / "tools/read_only.py").write_text(
        "def run() -> int:\n    return 1\n",
        encoding="utf-8",
    )
    effects = {
        "tools/writer_ok.py": {
            "effect": "cache",
            "destinations": ["generated/reports/demo.txt"],
            "reason": "Bounded test cache.",
        }
    }
    return tmp_path, effects


def test_writer_census_blocks_undeclared_tool_script(tmp_path: Path):
    """J3 #2 witness 1: an undeclared writer in tools/ fails the static gate."""
    root, effects = _synthetic_effects(tmp_path)
    (root / "tools/rogue_writer.py").write_text(
        "import subprocess\ndef apply():\n    subprocess.run(['git', 'commit', '-m', 'x'])\n",
        encoding="utf-8",
    )
    failures = scan_tools_census(root, effects, [], tree_roots=_load_tree_roots())
    assert any("tools/rogue_writer.py::apply::subprocess.git.commit" in msg for msg in failures), failures


def test_writer_census_blocks_declared_writer_touching_canonical_data(tmp_path: Path):
    """J3 #2 witness 2: an already-declared writer claiming knowledge/ or curriculum/ fails."""
    root, effects = _synthetic_effects(tmp_path)
    for bad_dest in ("knowledge/notes/**", "curriculum/**"):
        bad = {
            "tools/writer_ok.py": {
                **effects["tools/writer_ok.py"],
                "destinations": [bad_dest],
            }
        }
        failures = scan_tools_census(root, bad, [], tree_roots=_load_tree_roots())
        assert any("claims canonical DATA_ROOTS destination" in msg and bad_dest in msg for msg in failures), failures


def test_writer_census_blocks_wildcards_stale_declarations_and_unmediated(tmp_path: Path):
    root, effects = _synthetic_effects(tmp_path)
    wildcard_effects = {
        **effects,
        "tools/*.py": {
            "effect": "tooling",
            "destinations": ["generated/**"],
            "reason": "Wildcard",
        },
    }
    assert any("wildcard glob forbidden" in msg for msg in scan_tools_census(
        root, wildcard_effects, [], tree_roots=_load_tree_roots()))

    stale_effects = {
        **effects,
        "tools/read_only.py": {
            "effect": "tooling",
            "destinations": ["generated/**"],
            "reason": "Stale",
        },
    }
    assert any("stale zero-write declaration" in msg for msg in scan_tools_census(
        root, stale_effects, [], tree_roots=_load_tree_roots()))

    (root / "tools/bypass.py").write_text(
        "def run(cls, root):\n    return cls(root, _unmediated_test_only=True)\n",
        encoding="utf-8",
    )
    assert any("_unmediated_test_only is forbidden" in msg for msg in scan_tools_census(
        root, effects, [], tree_roots=_load_tree_roots()))


def test_writer_census_accepts_valid_scoped_and_contract_writers(tmp_path: Path):
    """J3 #2 witness 3: scoped writers and contract-backed exceptions pass."""
    root, effects = _synthetic_effects(tmp_path)
    (root / "tools/material_summarize.py").write_text(
        "from learning_os.store.fs import atomic_write_text_exclusive\n"
        "def promote(root):\n"
        "    atomic_write_text_exclusive(root / 'knowledge/summaries/chapter.md', 'x')\n",
        encoding="utf-8",
    )
    valid = {
        **effects,
        "tools/material_summarize.py": {
            "effect": "cache",
            "destinations": ["knowledge/summaries/**"],
            "reason": "Digest-keyed promoted chapter summary cache.",
            "contract": "system/contracts/tree-contract.yaml#knowledge/summaries",
        },
    }
    failures = scan_tools_census(root, valid, [], tree_roots=_load_tree_roots())
    assert failures == [], failures


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("import os as _os\ndef f(a, b):\n    _os.replace(a, b)\n", "::f::os.replace"),
        ("import shutil as sh\ndef f(a, b):\n    sh.move(a, b)\n", "::f::shutil.move"),
        ("import sqlite3 as sq\ndef f(p):\n    sq.connect(p)\n", "::f::sqlite3.connect"),
        ("import subprocess as sp\ndef f():\n    sp.run(['git', 'commit', '-m', 'x'])\n", "::f::subprocess.git.commit"),
        ("import yaml as y\ndef f(d, s):\n    y.safe_dump(d, s)\n", "::f::yaml.safe_dump"),
        ("from os import replace as r\ndef f(a, b):\n    r(a, b)\n", "::f::os.replace"),
        ("import os\nfrom os import open as os_open\ndef f(p):\n    os_open(p, flags=os.O_WRONLY)\n", "::f::os.open"),
        ("from shutil import move\ndef f(a, b):\n    move(a, b)\n", "::f::shutil.move"),
        ("from sqlite3 import connect\ndef f(p):\n    connect(p)\n", "::f::sqlite3.connect"),
        ("from subprocess import run\ndef f():\n    run(['/usr/bin/git', 'commit'])\n", "::f::subprocess.git.commit"),
        ("import subprocess\ndef f():\n    subprocess.run(args=['git', 'commit'])\n", "::f::subprocess.git.commit"),
        ("import subprocess\ndef f():\n    cmd = ['git', 'commit']\n    subprocess.run(cmd)\n", "::f::subprocess.git.commit"),
        ("import io\ndef f(p):\n    io.open(p, 'wb')\n", "::f::open"),
        ("from pathlib import Path\ndef f(p):\n    Path(p).mkdir()\n", "::f::mkdir"),
        ("import tempfile\ndef f():\n    tempfile.mkstemp()\n", "::f::tempfile.mkstemp"),
        ("import yaml\ndef f(d, s):\n    yaml.dump(d, s)\n", "::f::yaml.dump"),
    ],
)
def test_writer_census_catches_aliased_from_imported_and_fs_primitives(tmp_path, code, expected):
    root, effects = _synthetic_effects(tmp_path)
    (root / "tools/probe.py").write_text(code, encoding="utf-8")
    failures = scan_tools_census(root, effects, [], tree_roots=_load_tree_roots())
    assert any(expected in msg for msg in failures), failures


def test_writer_census_blocks_arbitrary_placeholders_and_movemap_canonical_claim(tmp_path):
    root, effects = _synthetic_effects(tmp_path)
    (root / "tools/move_map.py").write_text(
        "from pathlib import Path\ndef f(p: Path):\n    p.write_text('x', encoding='utf-8')\n",
        encoding="utf-8",
    )
    bad_movemap = {
        **effects,
        "tools/move_map.py": {
            "effect": "tooling",
            "destinations": ["knowledge/**"],
            "reason": "Fake claim",
            "contract": "OD9",
        },
    }
    assert any("claims canonical DATA_ROOTS destination" in msg for msg in scan_tools_census(
        root, bad_movemap, [], tree_roots=_load_tree_roots()))

    for sneaky_dest in (
        "../repository/knowledge/**",
        "<ANYTHING>/knowledge/**",
        "<TMPDIR>/../knowledge/**",
        "/etc/passwd",
        "$HOME/knowledge/**",
    ):
        bad_dest = {
            "tools/writer_ok.py": {
                **effects["tools/writer_ok.py"],
                "destinations": [sneaky_dest],
            }
        }
        failures = scan_tools_census(root, bad_dest, [], tree_roots=_load_tree_roots())
        assert any("not in tree-contract.yaml" in msg for msg in failures), (sneaky_dest, failures)


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


@pytest.mark.parametrize("scope,passes", [
    ("generated/reports/**", True),
    ("generated/cache/**", False),
])
def test_writer_census_follows_imported_path_owner(tmp_path, scope, passes):
    tools = tmp_path / "tools"
    tools.mkdir()
    (tools / "paths.py").write_text(
        "from pathlib import Path\n"
        "REPORT = Path('generated/reports/report.txt')\n"
        "def report_path(root):\n    return root / REPORT\n",
        encoding="utf-8",
    )
    (tools / "report.py").write_text(
        "from paths import report_path\n"
        "def run(root):\n    report_path(root).write_text('report')\n",
        encoding="utf-8",
    )
    effects = {"tools/report.py": {"destinations": [scope]}}
    findings = check_declared_write_sites(tmp_path, effects)
    if passes:
        assert findings == []
    else:
        assert len(findings) == 1
        assert "generated/reports/report.txt is outside declared destinations" in findings[0]


@pytest.mark.parametrize("contents", [
    "writer.py: {}\nwriter.py: {}\n",
    "writer.py:\n  effect: cache\n  effect: tooling\n",
])
def test_effects_inventory_rejects_duplicate_yaml_keys(tmp_path, contents):
    path = tmp_path / "effects.yaml"
    path.write_text(contents, encoding="utf-8")
    with pytest.raises(yaml.YAMLError, match="duplicate key"):
        _load_effects_yaml(path)



def test_same_declaration_detects_writer_destination_drift(tmp_path):
    root = tmp_path / "disposable-checkout"
    tools = root / "tools"
    tools.mkdir(parents=True)
    writer = tools / "report.py"
    inventory = root / "effects.yaml"
    inventory.write_text(
        "tools/report.py:\n"
        "  effect: cache\n"
        "  destinations: [generated/reports/**]\n"
        "  reason: report fixture\n",
        encoding="utf-8",
    )
    original = inventory.read_bytes()
    source = "def run(root):\n    (root / '{}').write_text('sample')\n"
    writer.write_text(source.format("generated/reports/report.txt"), encoding="utf-8")
    assert scan_tools_census(root, _load_effects_yaml(inventory), [], tree_roots=_load_tree_roots()) == []

    writer.write_text(source.format("knowledge/fixture-probe.txt"), encoding="utf-8")
    assert inventory.read_bytes() == original
    failures = scan_tools_census(root, _load_effects_yaml(inventory), [], tree_roots=_load_tree_roots())
    assert len(failures) == 1
    assert "repo:knowledge/fixture-probe.txt is outside declared destinations" in failures[0]


@pytest.mark.parametrize("extra, reason", [
    ("    raw.write_text('sample')", "has no proved destination at this write site"),
    ("    (root / 'generated/reports' / raw).write_text('sample')", "can replace its base"),
    (
        "    subprocess.run(['git', 'mv', '--', 'generated/reports/a', 'knowledge/b'], cwd=root)",
        "repo:knowledge/b is outside declared destinations",
    ),
])
def test_guard_proves_only_the_site_that_uses_its_result(tmp_path, extra, reason):
    root = tmp_path / "disposable-checkout"
    tools = root / "tools"
    tools.mkdir(parents=True)
    writer = tools / "report.py"
    source = (
        "import subprocess\n"
        "from learning_os.store.contracts.write_scopes import guard_tool_output_path\n"
        "def run(root, raw):\n"
        "    safe = guard_tool_output_path(raw, repo_root=root)\n"
        "    safe.write_text('sample')\n"
    )
    inventory = {"tools/report.py": {"destinations": ["generated/reports/**", "<EXPLICIT_OUT_FILE>"]}}
    writer.write_text(source, encoding="utf-8")
    assert not check_declared_write_sites(root, inventory)

    writer.write_text(source + extra + "\n", encoding="utf-8")
    failures = check_declared_write_sites(root, inventory)
    assert len(failures) == 1
    assert reason in failures[0]


def test_state_anchor_does_not_authorize_another_state_owner(tmp_path):
    root = tmp_path / "disposable-checkout"
    ledger = Path("tools/learning_os/store/session_ledger.py")
    (root / ledger).parent.mkdir(parents=True)
    (root / ledger).write_bytes((ROOT / ledger).read_bytes())
    writer = root / "tools/lock_writer.py"
    source = (
        "from learning_os.store.session_ledger import process_state_dir\n"
        "def run(root):\n"
        "    (process_state_dir(root) / '{}').write_text('sample')\n"
    )
    effects = {"tools/lock_writer.py": {"destinations": ["<STATE>/operator.lock"]}}
    writer.write_text(source.format("operator.lock"), encoding="utf-8")
    assert check_declared_write_sites(root, effects) == []

    writer.write_text(source.format("sealed-requests/fixture.json"), encoding="utf-8")
    failures = check_declared_write_sites(root, effects)
    assert failures
    assert all("outside declared checkout-state destinations" in failure for failure in failures)
