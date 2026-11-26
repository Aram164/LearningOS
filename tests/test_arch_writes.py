"""A2 one canonical writer: mandatory tools/ writer census and fixtures (SPEC §3.2, CL-06)."""

from __future__ import annotations

import ast
import os
from collections import Counter
from pathlib import Path

import arch_writes_fixtures
import pytest
import yaml

from learning_os.store.fingerprint import DATA_ROOTS

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
# explicit recorded maintenance, migration, or tree-contract allocation.
_RECORDED_CANONICAL_EXCEPTIONS: dict[str, tuple[str, frozenset[str], str]] = {
    "tools/move_map.py": (
        "tooling",
        frozenset({"knowledge/**", "curriculum/**"}),
        "OD9",
    ),
    "tools/migrations/curriculum_v2.py": (
        "migration",
        frozenset({"records/**", "curriculum/**"}),
        "tools/migrations/README.md",
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


def _load_tree_roots(tree_contract_path: Path = TREE_CONTRACT_PATH) -> frozenset[str]:
    data = yaml.safe_load(tree_contract_path.read_text(encoding="utf-8")) or {}
    roots = set()
    for entry in data.get("directories", []):
        if isinstance(entry, dict) and isinstance(entry.get("path"), str):
            roots.add(entry["path"].split("/", 1)[0])
    # Top-level non-canonical directories recognized by tests / build tooling.
    roots.update({"tests", "migration", "system", "generated", "operations", "archive"})
    return frozenset(roots)


def _is_external_or_placeholder(dest: str) -> bool:
    return (
        dest.startswith("<")
        or dest.startswith("$")
        or dest.startswith("~/")
        or dest.startswith("../")
        or dest.startswith("/")
    )


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


def _is_readonly_os_open(node: ast.Call, env: dict[str, ast.AST]) -> bool:
    fnode = node.args[1] if len(node.args) >= 2 else next(
        (kw.value for kw in node.keywords if kw.arg == "flags"), None
    )
    if fnode is None:
        return False
    names = _names_in_expr(fnode, env)
    if not names or (names & _OS_WRITE_OPEN_FLAGS):
        return False
    return "O_RDONLY" in names and names <= _OS_READONLY_FLAGS | {"os", "getattr", "O_RDONLY"}


def _subprocess_mutation_primitive(node: ast.Call) -> str | None:
    if any(
        kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True
        for kw in node.keywords
    ):
        return "subprocess.shell"
    if not node.args or not isinstance(node.args[0], (ast.List, ast.Tuple)) or not node.args[0].elts:
        return None
    elts = node.args[0].elts
    head = elts[0]
    if not (isinstance(head, ast.Constant) and isinstance(head.value, str)):
        return None
    cmd = head.value
    if cmd in _MUTATING_FS_COMMANDS:
        return f"subprocess.{cmd}"
    if cmd == "git":
        for elt in elts[1:]:
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                if elt.value in _MUTATING_GIT_SUBCOMMANDS:
                    return f"subprocess.git.{elt.value}"
    return None


class _Visitor(ast.NodeVisitor):
    def __init__(self, rel: str):
        self._rel = rel
        self._funcs: list[str] = []
        self._env_stack: list[dict[str, ast.AST]] = [{}]
        self._aliases: dict[str, str] = {}
        self.hits: list[tuple[str, int]] = []
        self.unmediated_lines: list[int] = []
        self.unmediated_call_lines: list[int] = []

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

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            bound = alias.asname or alias.name
            self._aliases[bound] = alias.name
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
        primitive = None
        if isinstance(func, ast.Attribute):
            attr = func.attr
            mod_name = func.value.id if isinstance(func.value, ast.Name) else None
            canonical_mod = self._aliases.get(mod_name, mod_name) if mod_name else None
            is_os = canonical_mod == "os"
            is_shutil = canonical_mod == "shutil"
            is_yaml = canonical_mod == "yaml"
            is_sqlite = canonical_mod == "sqlite3"
            is_subprocess = canonical_mod == "subprocess"
            resolved_attr = self._aliases.get(attr, attr)
            if attr in ("write_text", "write_bytes", "unlink"):
                primitive = attr
            elif attr == "open" and not is_os:
                mode_node = node.args[0] if node.args else next(
                    (kw.value for kw in node.keywords if kw.arg == "mode"), None
                )
                if mode_node is not None and not (
                    isinstance(mode_node, ast.Constant)
                    and isinstance(mode_node.value, str)
                    and not any(mark in mode_node.value for mark in "wax+")
                ):
                    primitive = "Path.open"
            elif is_os and attr in ("replace", "rename", "remove", "write", "link", "symlink"):
                primitive = f"os.{attr}"
            elif is_os and attr == "open":
                if not _is_readonly_os_open(node, self._env_stack[-1]):
                    primitive = "os.open"
            elif attr == "rename" and not is_os:
                primitive = "rename"
            elif attr == "replace" and not is_os:
                if len(node.args) == 1 and not node.keywords:
                    primitive = "replace"
            elif is_shutil and attr in ("move", "copy", "copy2", "copyfile", "rmtree"):
                primitive = f"shutil.{attr}"
            elif is_yaml and attr == "safe_dump":
                if len(node.args) >= 2 or any(kw.arg == "stream" for kw in node.keywords):
                    primitive = "yaml.safe_dump"
            elif is_sqlite and attr == "connect":
                primitive = "sqlite3.connect"
            elif is_subprocess and attr in _SUBPROCESS_FUNCS:
                primitive = _subprocess_mutation_primitive(node)
            elif resolved_attr in _WRITE_HELPERS:
                primitive = resolved_attr
        elif isinstance(func, ast.Name):
            canonical = self._aliases.get(func.id, func.id)
            if canonical == "open":
                mode_node = node.args[1] if len(node.args) >= 2 else next(
                    (kw.value for kw in node.keywords if kw.arg == "mode"), None
                )
                if mode_node is not None and not (
                    isinstance(mode_node, ast.Constant)
                    and isinstance(mode_node.value, str)
                    and not any(mark in mode_node.value for mark in "wax+")
                ):
                    primitive = "open"
            elif canonical in _WRITE_HELPERS:
                primitive = canonical
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

    undeclared_counts: Counter = Counter()
    first_seen: dict[str, tuple[str, int]] = {}
    writer_modules: set[str] = set()

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
            failures.append(
                f"A2 {rel}:{lineno}: _unmediated_test_only is forbidden anywhere under tools/ (CL-50)"
            )
        if visitor.hits:
            writer_modules.add(rel)
        if rel not in effects:
            for signature, lineno in visitor.hits:
                undeclared_counts[signature] += 1
                first_seen.setdefault(signature, (rel, lineno))

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
    return failures


def test_static_lint_matches_baseline():
    effects_raw = yaml.safe_load(EFFECTS_PATH.read_text(encoding="utf-8"))
    ratchet_entries = yaml.safe_load(
        RATCHETS_PATH.read_text(encoding="utf-8")
    )["checks"].get(RULE, [])
    failures = scan_tools_census(ROOT, effects_raw, ratchet_entries)
    assert not failures, "\n".join(failures)


def _synthetic_effects(tmp_path: Path) -> tuple[Path, dict]:
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools/writer_ok.py").write_text(
        "from pathlib import Path\ndef run(p: Path):\n    p.write_text('x', encoding='utf-8')\n",
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
        "def promote(p):\n    atomic_write_text_exclusive(p, 'x')\n",
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
