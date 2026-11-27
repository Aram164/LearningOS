"""A2 one canonical writer: mandatory tools/ writer census and fixtures (SPEC §3.2, CL-06).

Coverage model (2A re-entry, REENTRY-CRITIQUE rev 2 §5.7; replaces FIX-V2-STATUS D1)
=====================================================================================

Four layers, each answering one question (REENTRY §4, §5.1):

1. Ownership: production contracts decide what is owned. Owned territory is
   ``capability_catalog.owned_territory()``: the canonical fingerprint roots,
   ``operations/``, every capability write scope, and the tree-contract roots
   whose owner is ``interface``. A declaration in ``effects.yaml`` grants
   nothing. Inside owned territory it needs one alternative authority, covering
   all of its owned scope (overlap is not containment): the engine, except
   ``_ENGINE_REFUSED_TERRITORY``; an ``operational-owners.yaml`` module row for
   the module or its package, or an ``excluded`` row; or a recorded exception in
   ``_RECORDED_CANONICAL_EXCEPTIONS`` for exactly the destinations it names.
   Outside owned territory the declaration is the ownership record, and blanket
   globs are still refused.
2. The bounded static census. For every tracked ``tools/**/*.py`` file (the
   scanned inventory equals ``git ls-files``; symlinked files are refused, and
   so is a Python-shebang file without ``.py``, N-11), and for every write
   primitive in the enumerated inventory, the target must be built only from
   declared anchors, literals, proved single segments and the runtime guards
   or validators. Anything else fails closed. The enumerated inventory is
   exactly the census tables: the open-family openers and their modes
   (``_DEFERRED_OPENERS`` plus ``Path.open``), ``_PATH_WRITE_METHODS``,
   ``_OS_WRITE_ATTRS`` and the ``os.open`` flags (``_OS_WRITE_OPEN_FLAGS``),
   ``_SHUTIL_WRITE_ATTRS``, ``_TEMPFILE_ATTRS``, ``_LOGGING_FILE_HANDLERS``,
   ``sqlite3`` connections, ``tarfile``/``zipfile`` write and extract modes,
   ``_WRITE_HELPERS`` (shared ``store.fs`` and engine helpers), and process
   launches (``_SUBPROCESS_FUNCS``, ``_OS_EXEC_ATTRS``,
   ``_ASYNCIO_SUBPROCESS_ATTRS``), where git is default-deny outside
   ``_READONLY_GIT_SUBCOMMANDS`` and filesystem commands accept only
   ``_FS_COMMAND_FLAGS``. An opener is read-only only with a literal read-only
   mode at the call: a starred or ``**`` argument or an unresolved mode counts
   as writing, and a ``functools.partial`` over any opener is refused where it
   is built (N-2). Refused outright, whatever the declaration:
   ``_FORBIDDEN_PRIMITIVES`` (N-5); the admission names in
   ``_ADMISSION_NAME_SITES`` outside their recorded sites (N-7); in-process use
   of a recorded exception outside ``_ENTRY_POINT_REFERENCES`` (N-6); and
   ``_unmediated_test_only`` anywhere under ``tools/``.
3. Production guards: ``write_scopes.guard_tool_output_path`` (inside a
   repository only a declared ``generated/`` child or the ``.venv/`` scratch),
   ``scoped_write_target``, the ``store.fs`` boundary checks, and
   ``TransactionService`` default-deny admission. They refuse unauthorized
   destinations in supported operations, whether or not the census saw them.
4. The runtime writer gate (``test_runtime_writer_conformance_population`` in
   ``tests/test_scenarios_zz_operational_owners.py``): every world write the
   CI population executes (scenario cases, procedure transcripts, audit
   windows) needs a resolved writer, a covering declaration and authority. An
   unresolved writer, destination or evidence fails closed. Every writer that
   reaches owned territory has a witness disposition (``witness: runtime``,
   ``helper``, or a named deferral; §5.6).

What the static census does not claim, and what covers it instead:

- N-3, object state: an instance attribute retargeted from outside its class,
  or a path carried in an object's container.
- N-4, a bad root passed to a public method from another module: method calls
  are not resolved. This withdraws D4's claim that bad roots are reported at
  the caller, for method calls.
- N-10 (D2): the ``.name`` of a path value is taken as one segment.
- Computed names: ``getattr`` with a dynamic name, ``eval``, ``exec``,
  ``importlib``, ``ctypes``, and runtime monkeypatching.
- Library callables that write internally but are not in the inventory, for
  example ``xml.etree.ElementTree.ElementTree.write``, ``shelve`` or ``dbm``.
  A future need moves one into the inventory with a destination rule.
- ``socket.bind`` of a filesystem socket: its one use, the study broker,
  passes ``guard_tool_output_path``.

For all of these, the production guards protect every supported operation,
and the runtime gate checks every write the CI population executes. Code that
never runs, and whose destination cannot be resolved statically, rests on the
guards alone (the 2A exit amendment, 27 November 2026).
"""

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

from learning_os.store.contracts import capability_catalog, write_scopes
from learning_os.store.fingerprint import DATA_ROOTS
from learning_os.store.fs import is_git_output_option
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

_DECLARATION_KEYS = frozenset({"effect", "destinations", "reason", "contract", "witness"})

# 2A §5.6 witness accounting. A writer that reaches owned territory needs a
# runtime witness (checked over the CI population by the zz runtime gate) or a
# named deferral; any other writer may rest on this static census plus the
# production output guard. ``helper`` marks a mechanical delegation helper.
_WITNESS_PACKAGES = ("2B", "2C", "2D", "Phase 3", "Phase 4", "Phase 5", "Phase 6", "Phase 7")


def _witness_failures(rel: str, raw: dict, owned: bool) -> list[str]:
    import arch_audit_hook

    witness = raw.get("witness")
    if witness is None:
        if owned:
            return [
                f"A2 {rel}: reaches owned territory, so it needs `witness: runtime` or "
                "`witness: \"deferred: <package>: <obligation>\"` (2A §5.6)"
            ]
        return []
    if witness == "runtime":
        return []
    if witness == "helper":
        if _module_identity(rel) not in arch_audit_hook.MECHANICAL_HELPERS:
            return [f"A2 {rel}: `witness: helper` is only for a mechanical delegation helper"]
        return []
    if isinstance(witness, str) and witness.startswith("deferred: "):
        package, _, obligation = witness.removeprefix("deferred: ").partition(": ")
        if package in _WITNESS_PACKAGES and obligation.strip():
            return []
    return [
        f"A2 {rel}: witness {witness!r} must be runtime, helper, or "
        f"\"deferred: <one of {list(_WITNESS_PACKAGES)}>: <obligation>\""
    ]

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
    # Generated contract artifacts in CANONICAL_ROOTS (system/schema,
    # system/contracts), written only on an explicit --write/--bump and
    # checked by --check upstream (Bar 4 v3 N-1).
    "tools/generate_capability_schemas.py": (
        "projection",
        frozenset({
            "system/schema/capabilities/**",
            "system/schema/capability-envelope.schema.json",
            "system/schema/envelope-error-details.fragment.json",
        }),
        "system/DEVELOPER.md",
    ),
    "tools/learning_os/store/contracts/data_contract.py": (
        "projection",
        frozenset({"system/contracts/data-contract.yaml"}),
        "system/developer/changing-contracts.md",
    ),
    "tools/learning_os/store/contracts/manifest_contract.py": (
        "projection",
        frozenset({"system/contracts/manifest-contract.yaml"}),
        "system/developer/changing-contracts.md",
    ),
}

# Bar 4 v3 N-6: each recorded exception runs only from its documented entry
# point. A script exception may not be imported in-process at all; a library
# exception's writing functions may be named only by its CLI. Every key of
# _RECORDED_CANONICAL_EXCEPTIONS must appear here (checked by a test).
_ENTRY_POINT_REFERENCES: dict[str, frozenset[str]] = {
    "migrations.curriculum_v2": frozenset({"tools/migrations/curriculum_v2.py"}),
    "library_reconciliation": frozenset({"tools/library_reconciliation.py"}),
    "material_summarize": frozenset({"tools/material_summarize.py"}),
    "generate_capability_schemas": frozenset({"tools/generate_capability_schemas.py"}),
    "learning_os.store.contracts.data_contract.bump": frozenset({
        "tools/learning_os/store/contracts/data_contract.py", "tools/schema_contract.py",
    }),
    "learning_os.store.contracts.data_contract.rebump": frozenset({
        "tools/learning_os/store/contracts/data_contract.py", "tools/schema_contract.py",
    }),
    "learning_os.store.contracts.manifest_contract.bump": frozenset({
        "tools/learning_os/store/contracts/manifest_contract.py", "tools/manifest_contract.py",
    }),
}

_WRITE_HELPERS = frozenset({
    "atomic_write_text_exclusive",
    "atomic_write_bytes_exclusive",
    "atomic_write_bytes",
    "exclusive_temp_path",
    "atomic_text",
    "write_file_create_only",
    "write_local_output_file",
    "prune_empty_dirs",
    "create_ancestors_and_track",
    "_create_ancestors_and_track",
})

_READONLY_GIT_SUBCOMMANDS = frozenset({
    "rev-parse", "status", "diff", "diff-index", "diff-tree",
    "log", "show", "show-ref", "ls-files", "ls-tree",
    "cat-file", "check-ignore", "merge-base", "rev-list",
    "for-each-ref", "describe",
})
_INDEX_OR_REF_GIT_SUBCOMMANDS = frozenset({
    "commit", "read-tree", "add", "update-ref", "push",
})
_MUTATING_FS_COMMANDS = frozenset({"cp", "mv", "rm"})
# Flags that leave every operand a plain path and the last one the destination.
_FS_COMMAND_FLAGS = {
    "subprocess.cp": frozenset({"-a", "-p", "-r", "-R", "-f", "-n", "-v", "--"}),
    "subprocess.mv": frozenset({"-f", "-n", "-v", "--"}),
    "subprocess.rm": frozenset({"-f", "-r", "-R", "-rf", "-fr", "-v", "--"}),
    "subprocess.git.mv": frozenset({"-f", "-k", "-n", "-v", "--"}),
    "subprocess.git.rm": frozenset({"-f", "-r", "-q", "-n", "--cached", "--quiet", "--"}),
}
# Write-capable callables that count as a write when used as a value
# (``functools.partial(p.write_text, ...)``, ``getattr(p, "unlink")``), Bar 4 v2 NF-4.
_PATH_WRITE_METHODS = frozenset({
    "write_text", "write_bytes", "unlink", "mkdir", "rmdir", "touch",
    "symlink_to", "hardlink_to", "chmod", "lchmod", "rename",
})
_OS_WRITE_OPEN_FLAGS = frozenset({"O_WRONLY", "O_RDWR", "O_CREAT", "O_TRUNC", "O_APPEND"})
_OS_READONLY_FLAGS = frozenset({"O_RDONLY", "O_NOFOLLOW", "O_CLOEXEC", "O_DIRECTORY", "O_NONBLOCK"})
_SUBPROCESS_FUNCS = frozenset({"run", "Popen", "check_call", "check_output", "call"})
_OS_WRITE_ATTRS = frozenset({
    "replace", "rename", "renames", "remove", "removedirs", "unlink", "write",
    "link", "symlink", "mkdir", "makedirs", "rmdir", "chmod", "fchmod", "lchmod",
    "chown", "fchown", "lchown", "truncate", "ftruncate", "mkfifo", "mknod", "utime",
})
_OS_EXEC_ATTRS = frozenset({
    "system", "popen",
    "execl", "execle", "execlp", "execlpe",
    "execv", "execve", "execvp", "execvpe",
    "spawnl", "spawnle", "spawnlp", "spawnlpe",
    "spawnv", "spawnve", "spawnvp", "spawnvpe",
    "posix_spawn", "posix_spawnp",
})
_ASYNCIO_SUBPROCESS_ATTRS = frozenset({
    "create_subprocess_exec", "create_subprocess_shell",
    "subprocess_exec", "subprocess_shell",
})
_SHUTIL_WRITE_ATTRS = frozenset({
    "move", "copy", "copy2", "copyfile", "copytree", "rmtree",
    "unpack_archive", "make_archive",
})
_TEMPFILE_ATTRS = frozenset({
    "mkstemp", "mkdtemp", "NamedTemporaryFile", "TemporaryFile",
    "TemporaryDirectory", "SpooledTemporaryFile",
})
# Position of ``dir`` in each tempfile signature (Bar 4 v2 NF-2).
_TEMPFILE_DIR_POSITION = {
    "mkstemp": 2, "mkdtemp": 2, "TemporaryDirectory": 2,
    "NamedTemporaryFile": 6, "TemporaryFile": 6, "SpooledTemporaryFile": 7,
}
# Helpers whose ``boundary=`` is enforced at runtime (fs._assert_no_symlinks_under_boundary).
_BOUNDARY_ENFORCING_HELPERS = frozenset({"atomic_write_bytes_exclusive", "atomic_write_text_exclusive"})


def _tempfile_dir_arg(leaf: str, call: ast.Call) -> ast.AST | None:
    """The ``dir`` operand of a tempfile call, positional or keyword."""
    for kw in call.keywords:
        if kw.arg == "dir":
            return kw.value
        if kw.arg is None:
            return kw.value  # ``**kwargs`` may carry dir: evaluates as unknown
    position = _TEMPFILE_DIR_POSITION.get(leaf)
    if position is not None and len(call.args) > position:
        return call.args[position]
    if any(isinstance(arg, ast.Starred) for arg in call.args):
        return call.args[-1]  # ``*args`` may reach dir: evaluates as unknown
    return None
_LOGGING_FILE_HANDLERS = frozenset({
    "FileHandler", "WatchedFileHandler", "RotatingFileHandler", "TimedRotatingFileHandler",
})

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
    "<DELEGATED_GATEWAY_LAUNCHER>",
    "<AGENT_WORKSPACE_WRITE_LAUNCHER>",
})
_DELEGATED_LAUNCHER_TOKEN = "<DELEGATED_GATEWAY_LAUNCHER>"
_AGENT_WORKSPACE_WRITE_TOKEN = "<AGENT_WORKSPACE_WRITE_LAUNCHER>"
# Placeholders a declaration alone must not grant (Bar 4 v2 NF-4): each names
# the only modules allowed to declare it.
_PINNED_PLACEHOLDER_OWNERS = {
    "<GIT_INDEX_AND_COMMIT>": frozenset({"tools/learning_os/app/session.py"}),
    "<DELEGATED_GATEWAY_LAUNCHER>": frozenset({
        "tools/agent_run.py", "tools/codex_obsidian.py", "tools/study_launch.py",
        "tools/learning_os/adapters/study_broker.py",
    }),
    # Recorded exception (Bar 4 v2 NF-5): detection lands in 2A, confinement in 2B.
    "<AGENT_WORKSPACE_WRITE_LAUNCHER>": frozenset({"tools/codex_obsidian.py"}),
}
# Bar 4 v3 N-2: openers whose mode or flags decide whether they write. A
# ``functools.partial`` over one is refused where it is built: a call-time
# keyword overrides the partial's own, so no pinned mode proves read-only.
_DEFERRED_OPENERS = frozenset({
    "open", "builtins.open", "io.open", "codecs.open", "os.fdopen", "os.open",
    "zipfile.ZipFile", "tarfile.open",
})
# Bar 4 v3 N-5: write primitives outside the supported inventory. None is used in
# tools/; a future need moves one into the inventory with a destination rule.
_FORBIDDEN_PRIMITIVES = frozenset({
    "urllib.request.urlretrieve", "io.FileIO", "_io.FileIO",
    "fileinput.input", "fileinput.FileInput", "pty.spawn",
    "shutil.copystat", "shutil.copymode", "shutil.chown",
    "os.setxattr", "os.removexattr", "os.chflags", "os.lchflags",
})
# Bar 4 v3 N-7: the only tools/ modules that may name the transaction service, a
# gateway request context, or the context installer outside annotations.
# Provenance and lifecycle are 2B's; this keeps new construction sites visible.
_ADMISSION_NAME_SITES = {
    "TransactionService": frozenset({
        "tools/learning_os/store/transactions.py",  # defines it
        "tools/learning_os/app/commit.py",          # the one production construction
    }),
    "GatewayRequestContext": frozenset({
        "tools/learning_os/store/contracts/gateway.py",            # defines it
        "tools/learning_os/app/gateway.py",                        # from a sealed V2 envelope
        "tools/learning_os/app/handlers/goals.py",                 # operator goal gesture
        "tools/learning_os/app/handlers/learner_observations.py",  # observation gesture
        "tools/learning_os/store/diagnostics/resolver.py",         # verifies recorded rows
        "tools/learning_os/store/evidence.py",                     # verifies recorded rows
        "tools/seal_envelope.py",                                  # the sealing CLI's check
    }),
    "gateway_request_context": frozenset({
        "tools/learning_os/store/contracts/gateway.py",            # defines it
        "tools/learning_os/app/handlers/learner_observations.py",
        "tools/learning_os/app/pipeline.py",
        "tools/seal_envelope.py",
    }),
}
# Runtime validators the census trusts for dynamic path operands (Bar 4 v2 NF-2).
_PATH_SEGMENT_VALIDATOR = "learning_os.store.contracts.write_scopes.path_segment"
_RELATIVE_PATH_VALIDATOR = "learning_os.store.contracts.write_scopes.relative_path"
# Calls whose text form never contains a path separator.
_SAFE_SEGMENT_FUNCS = frozenset({
    "os.getpid", "os.getppid", "len", "int", "time.time_ns", "time.monotonic_ns",
    "secrets.randbelow", "secrets.token_hex", "secrets.token_urlsafe", "uuid.uuid4",
    "os.geteuid", "os.getuid",
    "threading.get_ident",
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


OWNERS_PATH = ARCH / "operational-owners.yaml"
# Owned territory the engine itself may not declare: UI-owned roots, and
# operator-authored request envelopes Core never writes.
_ENGINE_REFUSED_TERRITORY = ("bases/**", "boards/**", "operations/gateway-requests/**")


def _segment_overlap(a: str, b: str) -> bool:
    if a in {"*", "**"} or b in {"*", "**"}:
        return True
    wild_a, wild_b = any(c in a for c in "*?["), any(c in b for c in "*?[")
    if not wild_a and not wild_b:
        return a == b
    if wild_a and not wild_b:
        return fnmatchcase(b, a)
    if wild_b and not wild_a:
        return fnmatchcase(a, b)
    return True  # two partial globs: conservatively overlapping


def _patterns_overlap(a: str, b: str) -> bool:
    """Could one repository path match both patterns? True when unsure (Bar 4 v3 N-1).

    Declarations are patterns, so path matching cannot answer this. ``**`` spans
    any number of segments; ``*`` and partial globs match one segment.
    """
    pa, pb = tuple(a.split("/")), tuple(b.split("/"))

    @cache
    def go(i: int, j: int) -> bool:
        if i == len(pa) and j == len(pb):
            return True
        if i < len(pa) and pa[i] == "**":
            return go(i + 1, j) or (j < len(pb) and go(i, j + 1))
        if j < len(pb) and pb[j] == "**":
            return go(i, j + 1) or (i < len(pa) and go(i + 1, j))
        if i == len(pa) or j == len(pb):
            return False
        return _segment_overlap(pa[i], pb[j]) and go(i + 1, j + 1)

    return go(0, 0)


def _pattern_contains(outer: str, inner: str) -> bool:
    """Does every path matching ``inner`` match ``outer``? False when unsure (Bar 4 v3 N-1)."""
    po, pi = tuple(outer.split("/")), tuple(inner.split("/"))

    @cache
    def go(i: int, j: int) -> bool:
        if i == len(po):
            return j == len(pi)
        if po[i] == "**":
            return any(go(i + 1, k) for k in range(j, len(pi) + 1))
        if j == len(pi) or pi[j] == "**":
            return False
        o, n = po[i], pi[j]
        if o == "*":
            covered = True
        elif any(c in o for c in "*?["):
            covered = o == n or (not any(c in n for c in "*?[") and fnmatchcase(n, o))
        else:
            covered = o == n
        return covered and go(i + 1, j + 1)

    return go(0, 0)


def _module_identity(rel: str) -> str:
    """``tools/learning_os/a/b.py`` → ``learning_os.a.b``; ``tools/migrations/x.py`` → ``migrations.x``."""
    return rel.removeprefix("tools/").removesuffix(".py").removesuffix("/__init__").replace("/", ".")


@cache
def _operational_owner_rows() -> tuple[tuple[str, str, str | None], ...]:
    """(glob, sink, owner) rows of the test-side operational ownership contract."""
    data = yaml.safe_load(OWNERS_PATH.read_text(encoding="utf-8")) or {}
    rows = [(str(row["glob"]), str(row["sink"]), row.get("owner")) for row in data.get("entries", [])]
    rows += [(str(row["glob"]), "excluded", None) for row in data.get("excluded", [])]
    return tuple(rows)


def _declaration_authorities(rel: str) -> list[str]:
    """Owned patterns a non-engine module may declare on its own authority (alternatives)."""
    identity = _module_identity(rel)
    found = []
    for glob, sink, owner in _operational_owner_rows():
        if sink == "module" and owner and (identity == owner or identity.startswith(owner + ".")):
            found.append(glob)
        elif sink == "excluded" and glob not in _ENGINE_REFUSED_TERRITORY:
            found.append(glob)  # a disposable store any declared writer may keep
    return found


def _owned_territory_failures(
    rel: str, dest: str, effect: object, contract: object, data_roots: tuple[str, ...],
) -> list[str]:
    """Bar 4 v3 N-1: a declaration cannot reach owned territory without authority.

    ``DATA_ROOTS`` keeps its recorded-exception branch in the caller. Owned
    territory comes from production contracts (``capability_catalog.owned_territory``);
    the authorities are alternatives: the engine, an ``operational-owners.yaml``
    module row for this module, an ``excluded`` row, or a recorded exception.
    """
    territory = capability_catalog.owned_territory()
    owned = [pattern for pattern in territory if _patterns_overlap(dest, pattern)]
    if rel == _CANONICAL_ENGINE_MODULE:
        refused = [p for p in _ENGINE_REFUSED_TERRITORY if _patterns_overlap(dest, p)]
        return [
            f"A2 {rel}: engine declaration {dest!r} reaches {refused}, which no Core writer owns "
            "(Bar 4 v3 N-1)"
        ] if refused else []
    owned = [p for p in owned if p.split("/", 1)[0] not in data_roots]
    if not owned:
        return []
    authorities = _declaration_authorities(rel)
    exception = _RECORDED_CANONICAL_EXCEPTIONS.get(rel)
    problems: list[str] = []
    if exception is not None and dest in exception[1]:
        allowed_eff, _, contract_marker = exception
        if effect != allowed_eff:
            problems.append(f"A2 {rel}: canonical exception requires effect {allowed_eff!r}, got {effect!r}")
        if not isinstance(contract, str) or contract_marker not in contract:
            problems.append(f"A2 {rel}: owned destination {dest!r} must cite {contract_marker!r} in contract")
        authorities = [*authorities, dest]
    uncovered = [
        p for p in owned
        if not any(_pattern_contains(a, dest) or _pattern_contains(a, p) for a in authorities)
    ]
    if uncovered:
        problems.append(
            f"A2 {rel}: declaration {dest!r} reaches owned territory {uncovered} without "
            "authority: a declaration grants none; only the owner, the engine or a recorded "
            f"exception may write there (Bar 4 v3 N-1) — {FIX}"
        )
    return problems


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
        if effect == "migration" and (not isinstance(contract, str) or not contract.strip()):
            failures.append(f"A2 {rel}: migration declaration must cite its recorded maintenance contract")

        parsed[rel] = raw
        territory = capability_catalog.owned_territory()
        owned = any(
            not _is_external_or_placeholder(dest) and any(
                _patterns_overlap(dest, pattern) for pattern in territory)
            for dest in destinations
        )
        failures.extend(_witness_failures(rel, raw, owned))

        for dest in destinations:
            owners = _PINNED_PLACEHOLDER_OWNERS.get(dest)
            if owners is not None and rel not in owners:
                failures.append(
                    f"A2 {rel}: {dest} is reserved for {sorted(owners)}; a declaration cannot grant it"
                )
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
            if not _is_external_or_placeholder(dest):
                failures.extend(_owned_territory_failures(rel, dest, effect, contract, data_roots))
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
            elif tree_roots is None and contract_marker == "tree-contract.yaml" and TREE_CONTRACT_PATH.is_file():
                tree_data = yaml.safe_load(TREE_CONTRACT_PATH.read_text(encoding="utf-8")) or {}
                purposes: dict[str, str] = {}
                for row in tree_data.get("directories", []) or []:
                    if isinstance(row, dict) and isinstance(row.get("path"), str):
                        purposes[row["path"]] = str(row.get("purpose") or "")
                        for child in row.get("children") or []:
                            if isinstance(child, dict) and isinstance(child.get("path"), str):
                                purposes[child["path"]] = str(child.get("purpose") or "")
                if rel == "tools/material_summarize.py":
                    if "tools/material_summarize.py" not in purposes.get("knowledge/summaries", ""):
                        failures.append(
                            f"A2 {rel}: tree-contract.yaml#knowledge/summaries does not name {rel}"
                        )
                elif rel == "tools/library_reconciliation.py":
                    if "output bundles" not in purposes.get("work/active", ""):
                        failures.append(
                            f"A2 {rel}: tree-contract.yaml#work/active does not allocate workspace output bundles"
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


_OPAQUE_MODE = ast.Name(id="\x00opaque-mode", ctx=ast.Load())


def _opener_mode(node: ast.Call, position: int) -> ast.AST | None:
    """The mode operand of an opener call (Bar 4 v3 N-2).

    ``*args`` reaching the mode position, or ``**kwargs`` with no explicit mode,
    may carry a writing mode: both evaluate as opaque, which ``_mode_writes``
    treats as writing. ``None`` means no mode at all, which is a read.
    """
    for kw in node.keywords:
        if kw.arg == "mode":
            return kw.value
    if any(isinstance(arg, ast.Starred) for arg in node.args[: position + 1]):
        return _OPAQUE_MODE
    if len(node.args) > position:
        return node.args[position]
    if any(kw.arg is None for kw in node.keywords):
        return _OPAQUE_MODE
    return None


def _str_const(node: ast.AST | None, env: dict[str, ast.AST]) -> str | None:
    resolved = _resolve_expr(node, env)
    if isinstance(resolved, ast.Constant) and isinstance(resolved.value, str):
        return resolved.value
    return None


def _is_readonly_git_subcommand(
    sub: str, tail: list[ast.AST], env: dict[str, ast.AST],
) -> bool:
    literal_strs = [_str_const(e, env) for e in tail if not isinstance(e, ast.Starred)]
    if any(s is not None and is_git_output_option(s) for s in literal_strs):
        return False
    # Bar 4 v2 NF-4: before a literal "--", no word may be able to form an
    # option, so ``f"--output={out}"`` or ``*extra`` cannot add an output file.
    separator = next((i for i, e in enumerate(tail)
                      if not isinstance(e, ast.Starred)
                      and _str_const(e, env) in {"--", "--end-of-options"}), len(tail))
    options = tail[:separator]
    options_literal = not any(
        _str_const(e, env) is None and _may_be_option(e, env) for e in options
    )
    has_star = any(isinstance(e, ast.Starred) for e in tail)
    if sub in _READONLY_GIT_SUBCOMMANDS and sub != "archive":
        if not options_literal:
            return False
        if not has_star:
            return True
        # Starred pathspecs after a literal "--" cannot add options.
        if sub in {"ls-files", "check-ignore", "status", "log", "diff", "diff-tree"}:
            return True
    if sub == "archive":
        if not has_star:
            return True
        # capture_world.py passes *wanted where wanted filters ("tools", "system").
        starred = [e.value for e in tail if isinstance(e, ast.Starred)]
        if len(starred) == 1 and isinstance(resolved := _resolve_expr(starred[0], env), ast.ListComp):
            return any(
                isinstance(gen.iter, ast.Tuple)
                and all(
                    isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                    and not elt.value.startswith("-")
                    for elt in gen.iter.elts
                )
                for gen in resolved.generators
            )
        return False
    if sub == "branch" and not has_star:
        return literal_strs == ["--show-current"]
    if sub == "symbolic-ref" and not has_star:
        return literal_strs in (["HEAD"], ["--quiet", "HEAD"], ["-q", "HEAD"])
    return False


def _git_subcommand_from_elts(
    elts: list[ast.AST], env: dict[str, ast.AST],
) -> tuple[str | None, list[ast.AST]]:
    idx = 1
    if idx + 1 < len(elts) and _str_const(elts[idx], env) == "-C" and not isinstance(elts[idx + 1], ast.Starred):
        idx += 2
    if idx >= len(elts) or isinstance(elts[idx], ast.Starred):
        return None, []
    sub = _str_const(elts[idx], env)
    if sub is None or sub.startswith("-"):
        return None, []
    return sub, elts[idx + 1:]


def _is_readonly_other_subprocess(
    rel: str, elts: list[ast.AST], env: dict[str, ast.AST],
) -> bool:
    non_star = [e for e in elts if not isinstance(e, ast.Starred)]
    strs = [_str_const(e, env) for e in non_star]
    if rel == "tools/ingest_transcript.py" and "--flat-playlist" in strs \
            and "--print" in strs and not any(
                s == "-o" or (s is not None and (s.startswith("--output") or s.startswith("--write-")))
                for s in strs
            ):
        return True
    if any(isinstance(e, ast.Starred) for e in elts):
        return False
    head = PurePosixPath(strs[0]).name if strs and strs[0] is not None else None
    if head == "tmutil" and len(strs) == 2 and strs[1] in {"destinationinfo", "latestbackup"}:
        return True
    if head == "pdftotext" and len(strs) == 7 and strs[1] == "-f" and strs[3] == "-l" and strs[6] == "-":
        return True
    if head == "launchctl" and len(strs) == 3 and strs[1] == "getenv":
        return True
    if head == "node" and len(strs) == 3 and strs[1] == "--check":
        return True
    if len(strs) == 2 and strs[1] == "--version":
        return True
    if len(strs) == 5 and strs[1:5] == ["-m", "pytest", "--collect-only", "-q"]:
        return True
    if len(strs) == 5 and strs[2] == "--root" and strs[4] == "status":
        return True
    if rel == "tools/compare_world.py" and len(strs) == 5 and strs[1] == "-c":
        snippet = _resolve_expr(elts[2], env)
        if isinstance(snippet, ast.Call) and isinstance(snippet.func, ast.Attribute) \
                and snippet.func.attr == "join" and snippet.args \
                and isinstance(snippet.args[0], ast.Name) \
                and snippet.args[0].id == "_FINGERPRINT_SNIPPET":
            return True
    if rel == "tools/stress_check.py" and len(strs) == 3 and strs[1] == "run" \
            and isinstance(elts[2], ast.Name) and elts[2].id == "script":
        return True
    return False


def _flatten_cmd_elts(node: ast.AST | None, env: dict[str, ast.AST]) -> list[ast.AST] | None:
    resolved = _resolve_expr(node, env)
    if isinstance(resolved, (ast.List, ast.Tuple)):
        return list(resolved.elts)
    if isinstance(resolved, ast.BinOp) and isinstance(resolved.op, ast.Add):
        left = _flatten_cmd_elts(resolved.left, env)
        if left is None:
            return None
        right = _flatten_cmd_elts(resolved.right, env)
        if right is not None:
            return left + right
        return [*left, ast.Starred(value=resolved.right, ctx=ast.Load())]
    return None


def _subprocess_mutation_primitive(
    rel: str, node: ast.Call, env: dict[str, ast.AST],
) -> str | None:
    for kw in node.keywords:
        if kw.arg is None:
            return "subprocess.dynamic"
        if kw.arg == "shell":
            resolved_shell = _resolve_expr(kw.value, env)
            if not (isinstance(resolved_shell, ast.Constant) and resolved_shell.value is False):
                return "subprocess.shell"
    cmd_node = node.args[0] if node.args else next(
        (kw.value for kw in node.keywords if kw.arg == "args"), None
    )
    elts = _flatten_cmd_elts(cmd_node, env)
    if not elts:
        return "subprocess.dynamic"
    head_str = _str_const(elts[0], env)
    cmd = PurePosixPath(head_str).name if head_str is not None else None
    if cmd == "git":
        sub, tail = _git_subcommand_from_elts(elts, env)
        if sub is None:
            return "subprocess.git.<dynamic>"
        if _is_readonly_git_subcommand(sub, tail, env):
            return None
        return f"subprocess.git.{sub}"
    if _is_readonly_other_subprocess(rel, elts, env):
        return None
    if cmd is not None:
        return f"subprocess.{cmd}"
    return "subprocess.dynamic"


def _discover_git_star_wrappers(tree: ast.Module) -> tuple[dict[ast.FunctionDef, int], set[int]]:
    """Identify non-escaping local ``def _git(..., *args)`` helpers so every call site is checked."""
    candidates: dict[ast.FunctionDef, tuple[int, int]] = {}
    func_by_name: dict[str, list[ast.FunctionDef]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            continue
        if not isinstance(node, ast.FunctionDef) or node.args.vararg is None or node.decorator_list:
            continue
        vararg_name = node.args.vararg.arg
        fixed_count = len(node.args.posonlyargs) + len(node.args.args)
        sub_calls = [
            sub for sub in ast.walk(node)
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute)
            and sub.func.attr in _SUBPROCESS_FUNCS and sub.args
            and isinstance(sub.args[0], (ast.List, ast.Tuple))
        ]
        if len(sub_calls) != 1:
            continue
        sub_call = sub_calls[0]
        if any(kw.arg == "shell" or kw.arg is None for kw in sub_call.keywords):
            continue
        elts = sub_call.args[0].elts  # type: ignore[attr-defined]
        if not elts or not (isinstance(elts[0], ast.Constant) and elts[0].value == "git"):
            continue
        idx = 1
        if idx + 1 < len(elts) and isinstance(elts[idx], ast.Constant) and elts[idx].value == "-C" \
                and not isinstance(elts[idx + 1], ast.Starred):
            idx += 2
        if idx != len(elts) - 1 or not isinstance(elts[idx], ast.Starred) \
                or not isinstance(elts[idx].value, ast.Name) or elts[idx].value.id != vararg_name:
            continue
        candidates[node] = (fixed_count, id(sub_call))
        func_by_name.setdefault(node.name, []).append(node)

    # Disqualify ambiguous names, functions with zero calls, or functions referenced outside Call.func.
    call_func_ids: set[int] = set()
    call_counts: Counter = Counter()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            call_func_ids.add(id(node.func))
            call_counts[node.func.id] += 1
    escaped_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and id(node) not in call_func_ids:
            escaped_names.add(node.id)

    wrappers: dict[ast.FunctionDef, int] = {}
    skipped_sub_calls: set[int] = set()
    for fn, (fixed_count, sub_call_id) in candidates.items():
        if len(func_by_name.get(fn.name, ())) != 1:
            continue
        if fn.name in escaped_names or call_counts[fn.name] == 0:
            continue
        wrappers[fn] = fixed_count
        skipped_sub_calls.add(sub_call_id)
    return wrappers, skipped_sub_calls


def _callee_dotted(visitor: _Visitor, func: ast.AST) -> str | None:
    """``module.attr`` for a call head, through import aliases."""
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        return f"{visitor._module_of(func.value)}.{func.attr}"
    if isinstance(func, ast.Name) and func.id in visitor._from_aliases:
        mod, orig = visitor._from_aliases[func.id]
        return f"{mod}.{orig}"
    return None


def _annotation_node_ids(tree: ast.AST) -> set[int]:
    """Ids of nodes in annotations and isinstance/issubclass class operands: not runtime values."""
    found: set[int] = set()
    for node in ast.walk(tree):
        roots: list[ast.AST] = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = node.args
            roots += [a.annotation for a in (*args.posonlyargs, *args.args, *args.kwonlyargs,
                                              args.vararg, args.kwarg) if a is not None and a.annotation]
            if node.returns is not None:
                roots.append(node.returns)
        elif isinstance(node, ast.AnnAssign):
            roots.append(node.annotation)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in {"isinstance", "issubclass"} and len(node.args) == 2:
            roots.append(node.args[1])
        for root in roots:
            found.update(id(sub) for sub in ast.walk(root))
    return found


_READONLY_GIT_VALIDATOR = "readonly_git_arguments"


def _call_leaf(func: ast.AST) -> str | None:
    return func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None


def _may_be_option(expr: ast.AST, env: dict[str, ast.AST], depth: int = 0) -> bool:
    """True when a git argument could render as an option (Bar 4 v2 NF-4).

    Plain data (a parameter, attribute, subscript or call result) is a value,
    not code; text built from a literal head starting with ``-``, a starred
    sequence, or a name bound to either could add ``--output`` or similar.
    """
    if depth > 6:
        return True
    if isinstance(expr, ast.Starred):
        # A sequence checked by the runtime validator cannot carry an output option.
        value = expr.value
        for _ in range(4):
            if isinstance(value, ast.Name) and value.id in env:
                value = env[value.id]
        return not (isinstance(value, ast.Call) and _call_leaf(value.func) == _READONLY_GIT_VALIDATOR)
    if isinstance(expr, ast.Constant):
        return isinstance(expr.value, str) and expr.value.startswith("-")
    if isinstance(expr, ast.JoinedStr):
        if not expr.values:
            return False
        first = expr.values[0]
        if isinstance(first, ast.Constant):
            return isinstance(first.value, str) and first.value.startswith("-")
        return isinstance(first, ast.FormattedValue) and _may_be_option(first.value, env, depth + 1)
    if isinstance(expr, ast.BinOp) and isinstance(expr.op, (ast.Add, ast.Mod)):
        return _may_be_option(expr.left, env, depth + 1)
    if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Attribute) and expr.func.attr == "format":
        return _may_be_option(expr.func.value, env, depth + 1)
    if isinstance(expr, ast.Name) and expr.id in env:
        return _may_be_option(env[expr.id], env, depth + 1)
    return False


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
        # Declaration-independent refusals (Bar 4 v3 N-2, N-5, N-6, N-7).
        self.refusals: list[tuple[int, str]] = []
        self._readonly_fd_helper = False
        self._git_wrappers_by_name: dict[str, int] = {}
        self._git_wrapper_sub_calls: set[int] = set()
        self._call_func_ids: set[int] = set()
        self._alias_rhs_ids: set[int] = set()
        self._non_value_ids: set[int] = set()

    def visit_Module(self, node: ast.Module) -> None:
        self._non_value_ids = _annotation_node_ids(node)
        wrappers, skipped = _discover_git_star_wrappers(node)
        self._git_wrappers_by_name = {fn.name: fixed for fn, fixed in wrappers.items()}
        self._git_wrapper_sub_calls = skipped
        if self._rel == "tools/learning_os/store/study_fence.py":
            for stmt in node.body:
                if not isinstance(stmt, ast.FunctionDef) or stmt.name != "fd_open_flags":
                    continue
                flags = {
                    child.attr for child in ast.walk(stmt)
                    if isinstance(child, ast.Attribute) and child.attr.startswith("O_")
                }
                has_numeric_const = any(
                    isinstance(child, ast.Constant)
                    and isinstance(child.value, (int, float, complex))
                    and not isinstance(child.value, bool)
                    for child in ast.walk(stmt)
                )
                bad_calls = [
                    child for child in ast.walk(stmt)
                    if isinstance(child, ast.Call)
                    and not (isinstance(child.func, ast.Name) and child.func.id == "hasattr")
                ]
                returns = [child.value for child in ast.walk(stmt) if isinstance(child, ast.Return)]
                self._readonly_fd_helper = (
                    not has_numeric_const
                    and not bad_calls
                    and "O_RDONLY" in flags and flags <= _OS_READONLY_FLAGS
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

    def _refuse(self, node: ast.AST, message: str) -> None:
        self.refusals.append((getattr(node, "lineno", 0), message))

    def _refuse_entry_only_import(self, node: ast.AST, module: str) -> None:
        """Bar 4 v3 N-6: a recorded canonical exception runs only from its entry point."""
        for name, entry_points in _ENTRY_POINT_REFERENCES.items():
            if self._rel not in entry_points and (module == name or module.startswith(name + ".")):
                self._refuse(
                    node,
                    f"in-process use of {name} is refused: its recorded canonical exception "
                    f"runs only from {sorted(entry_points)} (Bar 4 v3 N-6)",
                )

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            # ``import a.b`` binds ``a`` to package ``a``; only ``import a.b as x``
            # binds a name to ``a.b`` itself.
            bound = alias.asname or alias.name.split(".", 1)[0]
            self._mod_aliases[bound] = alias.name if alias.asname else bound
            self._refuse_entry_only_import(node, alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        mod = node.module or ""
        if node.level:
            package = PurePosixPath(self._rel).parent.parts[1:]  # drop the tools/ prefix
            if node.level > 1:
                package = package[: len(package) - (node.level - 1)]
            mod = ".".join((*package, *([mod] if mod else [])))
        for alias in node.names:
            bound = alias.asname or alias.name
            self._from_aliases[bound] = (mod, alias.name)
            self._mod_aliases[bound] = alias.name
            self._refuse_entry_only_import(node, f"{mod}.{alias.name}" if mod else alias.name)
        self.generic_visit(node)

    def _dotted_reference(self, node: ast.AST) -> str | None:
        """``pkg.mod.attr`` for a Name or Attribute chain, through import aliases."""
        attrs: list[str] = []
        cur = node
        while isinstance(cur, ast.Attribute):
            attrs.append(cur.attr)
            cur = cur.value
        if not isinstance(cur, ast.Name):
            return None
        if cur.id in self._from_aliases:
            mod, orig = self._from_aliases[cur.id]
            base = f"{mod}.{orig}" if mod else orig
        else:
            base = self._mod_aliases.get(cur.id, cur.id)
        return ".".join((base, *reversed(attrs)))

    def _check_refused_reference(self, node: ast.Name | ast.Attribute) -> None:
        """N-5 and N-7: references refused wherever they appear (calls, aliases, values)."""
        if not isinstance(getattr(node, "ctx", None), ast.Load) or id(node) in self._non_value_ids:
            return
        dotted = self._dotted_reference(node)
        if dotted is not None:
            self._refuse_entry_only_import(node, dotted)
        if dotted in _FORBIDDEN_PRIMITIVES:
            self._refuse(
                node,
                f"{dotted} is outside the supported write-primitive inventory (Bar 4 v3 N-5); "
                "add it to the census inventory with a destination rule before using it",
            )
        leaf = node.attr if isinstance(node, ast.Attribute) else (
            self._from_aliases[node.id][1] if node.id in self._from_aliases else node.id
        )
        sites = _ADMISSION_NAME_SITES.get(leaf)
        if sites is not None and self._rel not in sites:
            self._refuse(
                node,
                f"{leaf} may be named only at its recorded construction sites {sorted(sites)} "
                "(Bar 4 v3 N-7); production admission goes through the gateway",
            )

    def visit_Assign(self, node: ast.Assign) -> None:
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            self._env_stack[-1][node.targets[0].id] = node.value
            if isinstance(node.value, (ast.Name, ast.Attribute)):
                # ``w = p.write_text``: the alias is unwrapped where it is called.
                self._alias_rhs_ids.add(id(node.value))
        self.generic_visit(node)

    def _module_of(self, node: ast.AST) -> str | None:
        if not isinstance(node, ast.Name):
            return None
        if node.id in self._from_aliases:
            return self._from_aliases[node.id][1]
        return self._mod_aliases.get(node.id, node.id)

    def _write_callable(self, node: ast.AST, env: dict[str, ast.AST], depth: int = 0) -> str | None:
        """Name the write primitive ``node`` denotes when used as a value, if any."""
        if isinstance(node, ast.Attribute):
            mod = self._module_of(node.value)
            if mod == "os" and node.attr in (_OS_WRITE_ATTRS | _OS_EXEC_ATTRS):
                return f"os.{node.attr}"
            if mod == "shutil" and node.attr in _SHUTIL_WRITE_ATTRS:
                return f"shutil.{node.attr}"
            if mod == "subprocess" and node.attr in _SUBPROCESS_FUNCS:
                return f"subprocess.{node.attr}"
            if node.attr in _PATH_WRITE_METHODS or node.attr in _WRITE_HELPERS:
                return node.attr
            return None
        if isinstance(node, ast.Name):
            if node.id in self._from_aliases:
                mod, orig = self._from_aliases[node.id]
                if mod == "os" and orig in (_OS_WRITE_ATTRS | _OS_EXEC_ATTRS):
                    return f"os.{orig}"
                if mod == "shutil" and orig in _SHUTIL_WRITE_ATTRS:
                    return f"shutil.{orig}"
                if mod == "subprocess" and orig in _SUBPROCESS_FUNCS:
                    return f"subprocess.{orig}"
                if orig in _WRITE_HELPERS:
                    return orig
                return None
            if depth < 4 and node.id in env and node.id not in self._mod_aliases:
                return self._write_callable(env[node.id], env, depth + 1)
        return None

    def _deferred_opener(self, node: ast.AST, env: dict[str, ast.AST]) -> str | None:
        """The opener ``node`` denotes when used as a value, if any (Bar 4 v3 N-2)."""
        node = _resolve_expr(node, env) or node
        if isinstance(node, ast.Attribute) and node.attr in {"open", "fdopen", "ZipFile"}:
            return self._dotted_reference(node) or f"<object>.{node.attr}"
        dotted = self._dotted_reference(node) if isinstance(node, ast.Name) else None
        if dotted in _DEFERRED_OPENERS:
            return dotted
        return None

    def _defer_partial(self, node: ast.Call, env: dict[str, ast.AST]) -> None:
        """``functools.partial(f, *a, **k)`` is scanned as the deferred call ``f(*a, **k)``.

        A partial over an opener is refused instead (Bar 4 v3 N-2): a call-time
        keyword overrides the partial's own mode or flags, so the deferred call
        cannot be judged where it is built.
        """
        func = node.func
        is_partial = _callee_dotted(self, func) in {"functools.partial", "functools.partialmethod"}
        if is_partial and node.args:
            opener = self._deferred_opener(node.args[0], env)
            if opener is not None:
                self._refuse(
                    node,
                    f"functools.partial over the opener {opener} is refused (Bar 4 v3 N-2): "
                    "call the opener directly so its mode or flags are checked at the call",
                )
                return
        if not is_partial or not node.args or self._write_callable(node.args[0], env) is None:
            return
        deferred = ast.Call(func=node.args[0], args=list(node.args[1:]), keywords=list(node.keywords))
        ast.copy_location(deferred, node)
        deferred._los_synthetic = True  # type: ignore[attr-defined]
        self.visit_Call(deferred)

    def visit_Compare(self, node: ast.Compare) -> None:
        # ``subprocess.run is not _ORIGINAL`` compares identities; nothing is called.
        if any(isinstance(op, (ast.Is, ast.IsNot)) for op in node.ops):
            for operand in (node.left, *node.comparators):
                if isinstance(operand, (ast.Name, ast.Attribute)):
                    self._non_value_ids.add(id(operand))
        self.generic_visit(node)

    def _dynamic_write_call(self, node: ast.Call, env: dict[str, ast.AST]) -> str | None:
        func = node.func
        name = func.id if isinstance(func, ast.Name) else None
        dotted_mod = self._module_of(func.value) if isinstance(func, ast.Attribute) else None
        if name == "getattr" and len(node.args) >= 2:
            attr = _str_const(node.args[1], env)
            if attr is None:
                return None  # dynamic attribute: reported by the value check when called
            if attr in _PATH_WRITE_METHODS or attr in _WRITE_HELPERS:
                return f"indirect.{attr}"
            mod = self._module_of(node.args[0])
            if mod == "os" and attr in (_OS_WRITE_ATTRS | _OS_EXEC_ATTRS):
                return f"indirect.os.{attr}"
            if mod == "shutil" and attr in _SHUTIL_WRITE_ATTRS:
                return f"indirect.shutil.{attr}"
            if mod == "subprocess" and attr in _SUBPROCESS_FUNCS:
                return f"indirect.subprocess.{attr}"
        if (dotted_mod == "operator" and isinstance(func, ast.Attribute) and func.attr == "methodcaller") or (
            name is not None and self._from_aliases.get(name) == ("operator", "methodcaller")
        ):
            attr = _str_const(node.args[0], env) if node.args else None
            if attr is None or attr in _PATH_WRITE_METHODS or attr in _WRITE_HELPERS:
                return f"indirect.methodcaller.{attr or '<dynamic>'}"
        return None

    def _check_value_reference(self, node: ast.AST) -> None:
        if id(node) in self._call_func_ids or id(node) in self._alias_rhs_ids \
                or id(node) in self._non_value_ids \
                or not isinstance(getattr(node, "ctx", None), ast.Load):
            return
        env = {name: value for frame in self._env_stack for name, value in frame.items()}
        primitive = self._write_callable(node, env)
        if primitive is not None:
            self._record(f"indirect.{primitive}", node)

    def visit_Expr(self, node: ast.Expr) -> None:
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute) \
                and node.value.func.attr == "append" and isinstance(node.value.func.value, ast.Name) \
                and len(node.value.args) == 1:
            name = node.value.func.value.id
            env = {k: v for frame in self._env_stack for k, v in frame.items()}
            prev = env.get(name)
            if prev is not None:
                self._env_stack[-1][name] = ast.BinOp(
                    left=prev, op=ast.Add(), right=ast.List(elts=[node.value.args[0]], ctx=ast.Load()),
                )
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if isinstance(node.target, ast.Name) and node.value is not None:
            self._env_stack[-1][node.target.id] = node.value
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        if isinstance(node.target, ast.Name):
            env = {name: value for frame in self._env_stack for name, value in frame.items()}
            prev = env.get(node.target.id, ast.Name(id=node.target.id, ctx=ast.Load()))
            self._env_stack[-1][node.target.id] = ast.BinOp(
                left=prev, op=node.op, right=node.value,
            )
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
        self._check_value_reference(node)
        self._check_refused_reference(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr == "_unmediated_test_only":
            self.unmediated_lines.append(node.lineno)
        self._check_value_reference(node)
        self._check_refused_reference(node)
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        if node.value == "_unmediated_test_only":
            self.unmediated_lines.append(node.lineno)

    def visit_Call(self, node: ast.Call) -> None:
        self._call_func_ids.add(id(node.func))
        called = self._dotted_reference(node.func)
        literal = (
            node.args[1].value if called == "getattr" and len(node.args) >= 2
            and isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, str)
            else node.args[0].value if node.args and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str) else None
        )
        if literal is not None:
            if called in {"importlib.import_module", "runpy.run_module"}:
                self._refuse_entry_only_import(node, literal)
            elif called == "runpy.run_path":
                for name, entry_points in _ENTRY_POINT_REFERENCES.items():
                    if any(literal.endswith(rel.removeprefix("tools/")) for rel in entry_points):
                        self._refuse_entry_only_import(node, name)
            elif called == "getattr" and literal in _ADMISSION_NAME_SITES \
                    and self._rel not in _ADMISSION_NAME_SITES[literal]:
                self._refuse(
                    node,
                    f"{literal} may be named only at its recorded construction sites "
                    f"{sorted(_ADMISSION_NAME_SITES[literal])} (Bar 4 v3 N-7)",
                )
        if id(node) in self._git_wrapper_sub_calls:
            self.generic_visit(node)
            return
        func = node.func
        # Lexical lookup: the current scope's names shadow enclosing and
        # module-level ones, so a module constant such as a read-only flag
        # set still resolves inside the functions that use it.
        env = {name: value for frame in self._env_stack for name, value in frame.items()}

        # Bar 4 F8: forbid **kwargs on TransactionService(...) in tools/ so
        # _unmediated_test_only cannot be passed via dynamic key construction.
        callee_name = (
            self._from_aliases[func.id][1]
            if isinstance(func, ast.Name) and func.id in self._from_aliases
            else (self._mod_aliases.get(func.id, func.id) if isinstance(func, ast.Name) else (
                func.attr if isinstance(func, ast.Attribute) else None
            ))
        )
        if callee_name == "TransactionService" and any(kw.arg is None for kw in node.keywords):
            self.unmediated_lines.append(node.lineno)
            self.unmediated_call_lines.append(node.lineno)

        if isinstance(func, ast.Name) and func.id in self._git_wrappers_by_name:
            fixed = self._git_wrappers_by_name[func.id]
            if any(kw.arg is None for kw in node.keywords) or len(node.args) <= fixed \
                    or any(isinstance(a, ast.Starred) for a in node.args[:fixed]):
                self._record("subprocess.git.<dynamic>", node)
            else:
                first = node.args[fixed]
                sub = None if isinstance(first, ast.Starred) else _str_const(first, env)
                tail = node.args[fixed + 1:]
                if sub is None or sub.startswith("-"):
                    self._record("subprocess.git.<dynamic>", node)
                elif not _is_readonly_git_subcommand(sub, tail, env):
                    self._record(f"subprocess.git.{sub}", node)
            self.generic_visit(node)
            return

        # Bar 4 F3 (U21): unwrap bound-method aliases such as ``w = path.write_text; w('x')``,
        # and (Bar 4 v2 NF-4) name aliases such as ``from os import remove; fn = remove``.
        for _ in range(4):
            if not (isinstance(func, ast.Name) and func.id not in self._from_aliases
                    and func.id not in self._mod_aliases):
                break
            aliased = _resolve_expr(func, env)
            if not isinstance(aliased, (ast.Attribute, ast.Name)) or aliased is func:
                break
            func = aliased

        # Bar 4 v2 NF-4: calls whose callee the scan cannot name statically.
        dynamic = self._dynamic_write_call(node, env)
        if dynamic is not None:
            self._record(dynamic, node)
        self._defer_partial(node, env)
        if _callee_dotted(self, func) in {"shutil.copytree", "shutil.move"}:
            # The copy function writes only inside the destination checked at this site.
            for kw in node.keywords:
                if kw.arg == "copy_function":
                    self._non_value_ids.update(id(sub) for sub in ast.walk(kw.value))

        primitive = None
        if isinstance(func, ast.Attribute):
            attr = func.attr
            mod_name = func.value.id if isinstance(func.value, ast.Name) else None
            canonical_mod = self._mod_aliases.get(mod_name, mod_name) if mod_name else None
            if canonical_mod is None and mod_name in self._from_aliases:
                canonical_mod = self._from_aliases[mod_name][1]
            is_os = canonical_mod == "os"
            is_io = canonical_mod in {"io", "builtins"}
            is_codecs = canonical_mod == "codecs"
            is_shutil = canonical_mod == "shutil"
            is_yaml = canonical_mod == "yaml"
            is_sqlite = canonical_mod == "sqlite3"
            is_subprocess = canonical_mod == "subprocess"
            is_tempfile = canonical_mod == "tempfile"
            is_asyncio = canonical_mod == "asyncio"
            is_zipfile = canonical_mod == "zipfile"
            is_tarfile = canonical_mod == "tarfile"
            is_logging = canonical_mod in {"logging", "logging.handlers"}
            resolved_attr = self._mod_aliases.get(attr, attr)
            if is_os and attr in _OS_EXEC_ATTRS:
                primitive = f"os.{attr}"
            elif is_os and attr in _OS_WRITE_ATTRS:
                primitive = f"os.{attr}"
            elif is_os and attr == "open":
                if not _is_readonly_os_open(node, env, readonly_fd_helper=self._readonly_fd_helper):
                    primitive = "os.open"
            elif is_os and attr == "fdopen":
                mode_node = _opener_mode(node, 1)
                if _mode_writes(mode_node, env):
                    primitive = "os.fdopen"
            elif is_io and attr == "open":
                mode_node = _opener_mode(node, 1)
                if _mode_writes(mode_node, env):
                    primitive = "open"
            elif is_codecs and attr == "open":
                mode_node = _opener_mode(node, 1)
                if _mode_writes(mode_node, env):
                    primitive = "codecs.open"
            elif is_asyncio and attr in _ASYNCIO_SUBPROCESS_ATTRS:
                primitive = f"asyncio.{attr}"
            elif is_zipfile and attr == "ZipFile":
                mode_node = _opener_mode(node, 1)
                if _mode_writes(mode_node, env):
                    primitive = "zipfile.ZipFile"
            elif is_tarfile and attr == "open":
                mode_node = _opener_mode(node, 1)
                if _mode_writes(mode_node, env):
                    primitive = "tarfile.open"
            elif is_logging and attr in _LOGGING_FILE_HANDLERS:
                primitive = "logging.FileHandler"
            elif attr in ("extractall", "extract"):
                primitive = attr
            elif attr in (
                "write_text", "write_bytes", "unlink", "mkdir", "rmdir", "touch",
                "symlink_to", "hardlink_to", "chmod", "lchmod",
            ):
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
                mode_node = _opener_mode(node, 0)
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
                primitive = _subprocess_mutation_primitive(self._rel, node, env)
            elif resolved_attr in _WRITE_HELPERS or attr in _WRITE_HELPERS:
                primitive = resolved_attr if resolved_attr in _WRITE_HELPERS else attr
        elif isinstance(func, ast.Name):
            if func.id in self._from_aliases:
                mod_src, orig_name = self._from_aliases[func.id]
            else:
                mod_src, orig_name = "", self._mod_aliases.get(func.id, func.id)
            if orig_name == "open" and mod_src == "os":
                if not _is_readonly_os_open(node, env, readonly_fd_helper=self._readonly_fd_helper):
                    primitive = "os.open"
            elif orig_name == "fdopen" and mod_src == "os":
                mode_node = _opener_mode(node, 1)
                if _mode_writes(mode_node, env):
                    primitive = "os.fdopen"
            elif orig_name == "open" and mod_src == "codecs":
                mode_node = _opener_mode(node, 1)
                if _mode_writes(mode_node, env):
                    primitive = "codecs.open"
            elif orig_name == "open" and mod_src == "tarfile":
                mode_node = _opener_mode(node, 1)
                if _mode_writes(mode_node, env):
                    primitive = "tarfile.open"
            elif orig_name == "open":
                mode_node = _opener_mode(node, 1)
                if _mode_writes(mode_node, env):
                    primitive = "open"
            elif mod_src == "zipfile" and orig_name == "ZipFile":
                mode_node = _opener_mode(node, 1)
                if _mode_writes(mode_node, env):
                    primitive = "zipfile.ZipFile"
            elif mod_src in {"logging", "logging.handlers"} and orig_name in _LOGGING_FILE_HANDLERS:
                primitive = "logging.FileHandler"
            elif mod_src == "os" and orig_name in _OS_EXEC_ATTRS:
                primitive = f"os.{orig_name}"
            elif mod_src == "os" and orig_name in _OS_WRITE_ATTRS:
                primitive = f"os.{orig_name}"
            elif mod_src == "asyncio" and orig_name in _ASYNCIO_SUBPROCESS_ATTRS:
                primitive = f"asyncio.{orig_name}"
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
                primitive = _subprocess_mutation_primitive(self._rel, node, env)
            elif orig_name in _WRITE_HELPERS or func.id in _WRITE_HELPERS:
                primitive = orig_name if orig_name in _WRITE_HELPERS else func.id
        if primitive is not None:
            self._record(primitive, node)
        if not getattr(node, "_los_synthetic", False):
            self.generic_visit(node)


def _find_tool_symlinks(root: Path) -> list[str]:
    """Bar 4 F9: any symlinked directory or file under tools/ fails closed."""
    tools_root = root / "tools"
    if not tools_root.exists() and not tools_root.is_symlink():
        return []
    if tools_root.is_symlink():
        return ["tools"]
    bad: list[str] = []
    for dirpath, dirnames, filenames in os.walk(tools_root, followlinks=False):
        current = Path(dirpath)
        keep: list[str] = []
        for name in sorted(dirnames):
            if name == "__pycache__" or name.endswith(".egg-info"):
                continue
            cand = current / name
            if cand.is_symlink():
                bad.append(cand.relative_to(root).as_posix())
            else:
                keep.append(name)
        dirnames[:] = keep
        for name in sorted(filenames):
            cand = current / name
            if cand.is_symlink():
                bad.append(cand.relative_to(root).as_posix())
    return bad


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


def _python_scripts_without_suffix(root: Path) -> list[str]:
    """Bar 4 v3 N-11: a Python script under tools/ must be a .py file the census scans.

    ``tools/hooks/`` is the pinned non-Python inventory, checked by its own test.
    """
    tools_root = root / "tools"
    failures: list[str] = []
    if not tools_root.is_dir() or tools_root.is_symlink():
        return failures
    for dirpath, dirnames, filenames in os.walk(tools_root, followlinks=False):
        current = Path(dirpath)
        dirnames[:] = sorted(
            name for name in dirnames
            if name != "__pycache__" and not name.endswith(".egg-info")
            and not (current / name).is_symlink()
        )
        if current == tools_root / "hooks":
            continue
        for name in sorted(filenames):
            candidate = current / name
            if name.endswith(".py") or candidate.is_symlink() or not candidate.is_file():
                continue
            try:
                with candidate.open("rb") as handle:
                    first = handle.readline(256)
            except OSError:
                first = b""
            if first.startswith(b"#!") and b"python" in first:
                failures.append(
                    f"A2 {candidate.relative_to(root).as_posix()}: Python script without a .py "
                    "suffix is outside the census inventory (Bar 4 v3 N-11)"
                )
    return failures


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
        for lineno, message in sorted(set(visitor.refusals)):
            unmediated_failures.append(f"A2 {rel}:{lineno}: {message}")
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

_SYSTEM_TEMP_ROOTS = ("/private/tmp", "/tmp")
_TREE_WALK_HELPERS = frozenset({"learning_os.store.fs.iter_non_symlink_files"})
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


@dataclass(frozen=True)
class _GitState:
    """A Git subcommand that changes a checkout's index, refs or commits."""

    subcommand: str


@dataclass(frozen=True)
class _DelegatedLauncher:
    """A pinned subprocess launcher, and the placeholder its module must declare for it."""

    label: str
    token: str = "<DELEGATED_GATEWAY_LAUNCHER>"


def _describe(value: object) -> str:
    if isinstance(value, _DelegatedLauncher):
        return f"delegated-launcher:{value.label}"
    if isinstance(value, _GitState):
        return f"git-state:{value.subcommand}"
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
    """Return (kind, segments); kind is rel | abs | home | bad | dynamic.

    ``\\x01`` marks an interpolation proved to be one path segment and
    ``\\x02`` an unproved one (Bar 4 v2 NF-2).
    """
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
        elif "\x02" in seg:
            # An unproved interpolation can carry "/" or "..", or be absolute.
            return "dynamic", ()
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


_GIT_STATE_TOKEN = "<GIT_INDEX_AND_COMMIT>"


def _external_covers(prefix: str, destination: str, parts: tuple[str, ...]) -> bool:
    if not destination.startswith(prefix):
        return False
    try:
        return _pattern_covers(destination.removeprefix(prefix), parts)
    except write_scopes.WriteScopeError:
        return False


_GUARDED_DESTINATION_PREFIXES = (
    *_EXPLICIT_OUT_MARKERS,
    "<EXTERNAL_PRACTICE_VAULT>/",
    "<RESTORED_COPY>/",
    "$LOS_SCRATCH_DIR/",
    "<TRACE_DEBUG_FILE>",
    "<LOS_OBSERVATIONS>",
    "<COUNTER_FILE>",
    "../materials/",
    "../reading-memory/",
    "../scratch/",
)


def _declares_guarded_destination(destinations: list[str]) -> bool:
    return any(
        d == marker or d.startswith(marker)
        for d in destinations
        for marker in _GUARDED_DESTINATION_PREFIXES
    )


def _external_destination_problem(
    value: _ExtRel, destinations: list[str], primitive: str, repo_dir_names: frozenset[str],
) -> str | None:
    """Match an external value to a declared destination of its own kind (Bar 4 F1)."""
    def checkout_state() -> bool:
        return any(
            d.startswith("<STATE>/") and _checkout_state_covers(d, value, primitive) for d in destinations
        )

    tag = value.tag
    if tag == "tempdir":
        if any(d.startswith("<TMPDIR>/") for d in destinations) or checkout_state():
            return None
        if any(d.startswith("<STATE>/") for d in destinations):
            # Checkout state falls back to a temporary directory outside Git.
            return f"is outside declared checkout-state destinations {destinations}"
        return "writes a temporary path but the module declares no <TMPDIR> destination"
    if tag in {"guarded caller output", "temp sibling of guarded output"}:
        if _declares_guarded_destination(destinations):
            return None
        return f"uses a caller-guarded path in a module declaring only {destinations}"
    if tag in {"ancestor above parent of a guarded path", "sibling of parent of a guarded path"}:
        return "writes via a parent of a guarded path, which the guard does not cover"
    if tag == "parent of guarded output":
        if (
            primitive in {"mkdir", "os.mkdir", "os.makedirs", "create_ancestors_and_track"}
            and not value.parts
            and _declares_guarded_destination(destinations)
        ):
            return None
        return "writes to a parent of a guarded path, which the guard does not cover"
    if tag == "git directory":
        if checkout_state():
            return None
        return f"is outside declared checkout-state destinations {destinations}"
    if tag == "home":
        if any(_external_covers("~/", d, value.parts) for d in destinations):
            return None
        return f"is in the home directory outside declared destinations {destinations}"
    if tag == "repository parent":
        parts = value.parts
        if parts and parts[0] not in {"*", "**", *repo_dir_names} and any(
            _external_covers("../", d, parts) for d in destinations
        ):
            return None
        return f"writes beside the repository outside declared sibling destinations {destinations}"
    if tag == "absolute literal":
        return "uses an absolute path that no declared destination admits"
    return f"is external ({tag}) and no declared destination admits it"


def _is_destination_parent(pattern: str, parts: tuple[str, ...]) -> bool:
    declared = pattern.split("/")
    return bool(parts) and len(parts) < len(declared) and all(
        child == parent or (parent == "*" and child != "**")
        for child, parent in zip(parts, declared, strict=False)
    )


_EXPR_SCOPE_NODES = (ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)


def _iter_local(node: ast.AST):
    """Yield nodes of one scope, stopping at nested defs, classes and expression scopes.

    Lambdas and comprehensions are yielded but not entered: each is indexed as
    its own child scope (Bar 4 v2 NF-3), so its calls, bindings and value
    references are seen with Python's shadowing rules.
    """
    stack = list(ast.iter_child_nodes(node))
    while stack:
        cur = stack.pop()
        yield cur
        if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, *_EXPR_SCOPE_NODES)):
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
        self.nonlocals: set[str] = set()
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


# The transaction engine selects these operands at runtime. The scan still
# checks any concrete result, and refuses an unresolved operand at a new sink.
# These entries correspond to the admitted write set, the preflighted recovery
# plan, and the engine-owned journal and receipt namespace.
_ENGINE_RUNTIME_OPERANDS = {
    ("atomic_write_bytes", "_create_ancestors_and_track"): ("path.parent",),
    ("atomic_write_bytes", "create_ancestors_and_track"): ("path.parent",),
    ("atomic_write_bytes", "exclusive_temp_path"): ("path",),
    ("atomic_write_bytes", "os.fdopen"): ("fd",),
    ("atomic_write_bytes", "os.replace"): ("tmp", "path"),
    ("atomic_write_bytes", "unlink"): ("tmp",),
    ("_update_intent_after", "atomic_write_bytes"): ("intent_path",),
    ("_remove_journal", "shutil.rmtree"): ("tx_dir",),
    ("_unwind_v2_entries", "atomic_write_bytes"): ("path",),
    ("_unwind_v2_entries", "unlink"): ("path",),
    ("_unwind_v2_entries", "rmdir"): ("directory",),
    ("TransactionService._rollback", "shutil.rmtree"): ("run.staging_dir",),
    ("TransactionService._publish_journal", "shutil.rmtree"): ("run.staging_dir",),
    ("TransactionService._publish_journal", "mkdir"): ("run.staging_dir",),
    ("TransactionService._publish_journal", "atomic_write_bytes"): (
        "run.staging_dir / path_segment(backup_id)", "run.staging_dir / 'intent.json'",
    ),
    ("TransactionService._publish_journal", "os.rename"): ("run.staging_dir", "run.inflight_dir"),
    ("TransactionService._apply", "atomic_write_bytes"): ("path",),
    ("TransactionService._apply", "unlink"): ("path",),
    ("TransactionService._record_idempotency", "atomic_write_bytes"): ("run.idempotency_path",),
    ("TransactionService._write_receipt", "atomic_write_bytes"): ("run.receipt_path",),
    ("TransactionService._finish", "shutil.rmtree"): ("run.inflight_dir",),
}
_ENGINE_DYNAMIC_ORIGINS = {
    "attribute run.staging_dir", "attribute run.inflight_dir",
    "attribute run.idempotency_path", "attribute run.receipt_path",
    "attribute action.path", "iteration", "tuple element",
}
_ENGINE_RUN_PATH_SOURCES = {
    "inflight_parent": (("TransactionService.commit", "self.root / 'operations' / 'transactions' / '.inflight'"),),
    "staging_dir": (("TransactionService.commit", "run.inflight_parent / f'.preparing-{run.transaction_id}'"),),
    "inflight_dir": (("TransactionService.commit", "run.inflight_parent / run.transaction_id"),),
    "receipt_path": (("TransactionService._allocate_identity", "_next_transaction_identity(self.root, run.now)"),),
    "idempotency_path": (
        ("TransactionService._capture_prestate", "None"),
        ("TransactionService._capture_prestate", "self._target(_idempotency_ledger_path(self.root))"),
    ),
}


_ENGINE_LOCAL_BINDINGS = {
    ("atomic_write_bytes", "fd"): (
        "__tuple_item__(_exclusive_temp_path(path, mode=438), 0)",
    ),
    ("atomic_write_bytes", "tmp"): (
        "None", "__tuple_item__(_exclusive_temp_path(path, mode=438), 1)", "None",
    ),
    ("_update_intent_after", "intent_path"): ("inflight_dir / 'intent.json'",),
    ("_unwind_v2_entries", "path"): ("action.path",),
    ("_unwind_v2_entries", "action"): (
        "__iter_child__(plan)", "__iter_child__(plan)",
        "__tuple_item__(_preflight_v2_entry(root, tx_dir, entry), 0)",
    ),
    ("_unwind_v2_entries", "plan"): ("[]",),
    ("_unwind_v2_entries", "directory"): ("__tuple_item__(write_target(root, relative), 0)",),
    ("TransactionService._apply", "path"): (
        "__iter_child__(run.delete_paths)",
        "__tuple_item__(__iter_child__(run.normalized_writes.items()), 0)",
    ),
}


def _is_engine_runtime_operand(scope: _Scope, primitive: str, expr: ast.AST) -> bool:
    operand = ast.unparse(expr)
    if operand not in _ENGINE_RUNTIME_OPERANDS.get((scope.qualname, primitive), ()):
        return False
    if scope.assigns.get("run"):
        return False
    names = [operand] if isinstance(expr, ast.Name) else []
    if scope.qualname == "_unwind_v2_entries" and operand == "path":
        names.extend(("action", "plan"))
        if tuple(map(ast.unparse, scope.appends.get("plan", ()))) != ("action",):
            return False
    return all(
        tuple(map(ast.unparse, scope.assigns.get(name, ())))
        == _ENGINE_LOCAL_BINDINGS.get((scope.qualname, name), ())
        for name in names
    )


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
        # Calls inside a lambda or comprehension, mapped to that scope.
        self.expr_scope_of: dict[int, _Scope] = {}
        # Calls into this module from other tools/ modules (Bar 4 v2 NF-3):
        # callee scope -> [(caller module, call, caller scope)].
        self.external_calls: dict[_Scope, list[tuple[_ModuleWriteSites, ast.Call, _Scope]]] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".", 1)[0]
                    self.mod_aliases[alias.asname or top] = alias.name if alias.asname else top
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if node.level:
                    # Resolve "from .config import X" against this module's
                    # package under tools/, so imported constants are traced.
                    package = rel.split("/")[1:-1]
                    package = package[: len(package) - (node.level - 1)] if node.level > 1 else package
                    module = ".".join([*package, *([module] if module else [])])
                for alias in node.names:
                    self.from_aliases[alias.asname or alias.name] = (module, alias.name)
        self.root_arguments = {
            argument.value[2:]
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument"
            for argument in node.args
            if isinstance(argument, ast.Constant) and argument.value in ("--root", "--repo")
        }
        self.non_value_refs: set[int] = set()
        for node in ast.walk(tree):
            annotations: list[ast.AST] = []
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = node.args
                annotations += [a.annotation for a in (*args.posonlyargs, *args.args, *args.kwonlyargs,
                                                        args.vararg, args.kwarg) if a is not None and a.annotation]
                if node.returns is not None:
                    annotations.append(node.returns)
            elif isinstance(node, ast.AnnAssign):
                annotations.append(node.annotation)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                    and node.func.id in {"isinstance", "issubclass"} and len(node.args) == 2:
                annotations.append(node.args[1])
            for annotation in annotations:
                self.non_value_refs.update(id(sub) for sub in ast.walk(annotation))
        # Mutations are attached to the container's owning scope once every
        # binding is known, so statement order cannot hide them (Bar 4 v2 NF-3).
        self._pending_appends: list[tuple[_Scope, str, ast.AST]] = []
        self._index_scope(self.module, tree.body, cls=None)
        for mut_scope, name, value in self._pending_appends:
            self._owner_scope(mut_scope, name).appends.setdefault(name, []).append(value)
        self._index_calls()
        self._engine_paths_bound = (
            rel == _CANONICAL_ENGINE_MODULE and self._engine_run_path_sources() == _ENGINE_RUN_PATH_SOURCES
        )

    def _engine_run_path_sources(self) -> dict[str, tuple[tuple[str, str], ...]]:
        assignments: dict[str, list[tuple[str, str]]] = {}
        for scope in self.scopes.values():
            for node in _iter_local(scope.node):
                if not isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)) or node.value is None:
                    continue
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    for field in ast.walk(target):
                        if isinstance(field, ast.Attribute) and isinstance(field.ctx, ast.Store) \
                                and isinstance(field.value, ast.Name) and field.value.id == "run" \
                                and field.attr in _ENGINE_RUN_PATH_SOURCES:
                            assignments.setdefault(field.attr, []).append((scope.qualname, ast.unparse(node.value)))
        return {name: tuple(sorted(sources)) for name, sources in assignments.items()}

    # -- indexing ---------------------------------------------------------
    def _index_scope(self, scope: _Scope, body: list[ast.stmt], cls: str | None) -> None:
        holder = ast.Module(body=body, type_ignores=[])
        local = list(_iter_local(holder))
        scope.globals.update(name for node in local if isinstance(node, ast.Global) for name in node.names)
        scope.nonlocals.update(name for node in local if isinstance(node, ast.Nonlocal) for name in node.names)
        for node in local:
            self._collect_binding(scope, node, cls)
            if isinstance(node, ast.Call):
                scope.calls.append(node)
            if isinstance(node, ast.Return) and node.value is not None:
                scope.returns.append(node.value)
            if isinstance(node, _EXPR_SCOPE_NODES):
                self._index_expr_scope(scope, node, cls)
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

    def _function_scope(self, scope: _Scope) -> _Scope:
        """The nearest enclosing scope that is not a lambda or comprehension."""
        while scope.parent is not None and isinstance(scope.node, _EXPR_SCOPE_NODES):
            scope = scope.parent
        return scope

    def _owner_scope(self, scope: _Scope, name: str) -> _Scope:
        """The scope whose binding of ``name`` a lookup from ``scope`` finds."""
        cursor: _Scope | None = scope
        while cursor is not None:
            if name in cursor.assigns or name in cursor.all_params:
                return cursor
            cursor = cursor.parent
        return self._function_scope(scope)

    def _index_expr_scope(self, parent: _Scope, node: ast.AST, cls: str | None) -> None:
        """Index a lambda or comprehension as a child scope (Bar 4 v2 NF-3)."""
        child = _Scope(node, parent, cls, f"{parent.qualname}.<{type(node).__name__.lower()}>")
        self.scopes[node] = child
        roots: list[ast.AST]
        if isinstance(node, ast.Lambda):
            lam = node.args
            child.params = [a.arg for a in (*lam.posonlyargs, *lam.args)]
            child.kwonly = [a.arg for a in lam.kwonlyargs]
            child.star_params = {a.arg for a in (lam.vararg, lam.kwarg) if a is not None}
            child.returns.append(node.body)
            roots = [node.body]
            # Defaults are evaluated in the enclosing scope.
            for default in (*lam.defaults, *[d for d in lam.kw_defaults if d is not None]):
                for sub in (default, *_iter_local(default)):
                    if isinstance(sub, ast.Call):
                        parent.calls.append(sub)
        else:
            roots = [*node.generators]
            roots += [node.key, node.value] if isinstance(node, ast.DictComp) else [node.elt]
        for root in roots:
            for sub in (root, *_iter_local(root)):
                self._collect_binding(child, sub, cls)
                if isinstance(sub, ast.Call):
                    child.calls.append(sub)
                    self.expr_scope_of[id(sub)] = child
                if isinstance(sub, _EXPR_SCOPE_NODES) and sub is not node:
                    self._index_expr_scope(child, sub, cls)

    def _collect_binding(self, scope: _Scope, node: ast.AST, cls: str | None) -> None:
        def bind_target(target: ast.AST, value: ast.AST) -> None:
            if isinstance(target, ast.Name):
                if target.id in scope.globals and scope is not self.module:
                    self.global_assignments.setdefault(target.id, []).append((scope, value))
                elif target.id in scope.nonlocals:
                    # ``nonlocal x; x = ...`` rebinds an enclosing function's x. Every
                    # enclosing function gets the binding: an over-approximation that
                    # does not depend on the order scopes are indexed in.
                    scope.bind(target.id, value)
                    owner = scope.parent
                    while owner is not None and owner is not self.module:
                        if not isinstance(owner.node, _EXPR_SCOPE_NODES):
                            owner.bind(target.id, value)
                        owner = owner.parent
                else:
                    scope.bind(target.id, value)
            elif isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name):
                # ``xs[i] = value`` adds a possible element to xs.
                self._pending_appends.append((scope, target.value.id, value))
            elif isinstance(target, ast.Starred):
                bind_target(target.value, _synthetic_call("__unknown__"))
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
            if isinstance(node.target, ast.Name) and isinstance(scope.node, _EXPR_SCOPE_NODES):
                self._function_scope(scope).bind(node.target.id, node.value)
            else:
                bind_target(node.target, node.value)
        elif isinstance(node, ast.comprehension):
            bind_target(node.target, _synthetic_call("__iter_child__", node.iter))

        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and isinstance(node.func.value, ast.Name):
            # Container mutations add possible elements (Bar 4 v2 NF-3), recorded
            # on the scope that owns the container so closures and comprehensions count.
            owner_name, attr = node.func.value.id, node.func.attr
            pending = self._pending_appends
            if attr in {"append", "add", "appendleft"} and len(node.args) == 1:
                pending.append((scope, owner_name, node.args[0]))
            elif attr == "insert" and len(node.args) == 2:
                pending.append((scope, owner_name, node.args[1]))
            elif attr in {"extend", "extendleft", "update"} and node.args:
                for arg in node.args:
                    pending.append((scope, owner_name, _synthetic_call("__iter_child__", arg)))
            elif attr in {"setdefault", "__setitem__", "__iadd__"}:
                pending.append((scope, owner_name, _synthetic_call("__unknown__")))

    def _callee_scope(self, func: ast.AST, scope: _Scope) -> _Scope | None:
        if isinstance(func, ast.Name):
            cursor: _Scope | None = scope
            while cursor is not None:
                if func.id in cursor.nested:
                    return cursor.nested[func.id]
                cursor = cursor.parent
            if func.id in self.class_methods:
                # ``Store(x)`` binds x to Store.__init__ (Bar 4 v2 NF-3).
                return self.class_methods[func.id].get("__init__")
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
                if id(node) in call_funcs or id(node) in self.non_value_refs:
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
                    # The system temporary roots are temporary storage, the same
                    # destination tempfile.gettempdir() yields; nothing else
                    # absolute is admitted by a declaration.
                    for temp_root in _SYSTEM_TEMP_ROOTS:
                        if text == temp_root or text.startswith(temp_root + "/"):
                            temp_kind, temp_parts = _parse_path_text(text[len(temp_root) + 1:])
                            if temp_kind == "rel":
                                return frozenset({_ExtRel("tempdir", temp_parts)})
                    return frozenset({_ExtRel("absolute literal")})
                if kind == "home":
                    # Keep the segments after "~/" so a home write is matched
                    # against the declared "~/..." destination, not waved through.
                    home_kind, home_parts = _parse_path_text(text[2:]) if text.startswith("~/") else ("rel", ())
                    if home_kind != "rel":
                        return frozenset({_BadTraversal(text)})
                    return frozenset({_ExtRel("home", home_parts)})
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
            if self._dotted(node.value) == "os.environ" and isinstance(node.slice, ast.Constant) \
                    and node.slice.value == "HOME":
                return frozenset({_ExtRel("home")})
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
                if owner == "args" and owner in scope.all_params and not assignments:
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
            tmp_leaf = self.from_aliases[func.id][1] if isinstance(func, ast.Name) \
                and func.id in self.from_aliases else leaf
            dir_expr = _tempfile_dir_arg(tmp_leaf, node)
            if dir_expr is not None:
                return frozenset(self._join(v, ("*",)) for v in ev(dir_expr))
            return frozenset({_ExtRel("tempdir")})
        if dotted in {
            "learning_os.store.contracts.write_scopes.guard_tool_output_path",
            "learning_os.store.contracts.write_scopes.open_guarded_directory",
        }:
            # A guarded path, or a descriptor opened on one.
            return frozenset({_ExtRel("guarded caller output")})
        if dotted == "_open_local_parent_dir_fd" and self.rel == "tools/learning_os/store/study_fence.py":
            return frozenset({_ExtRel("guarded caller output")})
        if dotted == "os.open" and node.args:
            # A descriptor stands for the directory it was opened on, so a
            # later dir_fd-relative write can be traced to that directory.
            if "dir_fd" not in kwargs:
                return ev(node.args[0])
            segs = self._segments(node.args[0], scope, bindings, depth, active)
            return frozenset(self._join(base, seg) for base in ev(kwargs["dir_fd"]) for seg in segs)
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
            if node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == "HOME":
                return frozenset({_ExtRel("home")})
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
            for val in self.eval(expr, callee, bound, depth + 1, active | {key}):
                if isinstance(val, _Param) and val.func in self.scopes:
                    out |= self.resolve_param(val, set())
                else:
                    out.add(val)
        return frozenset(out)

    def _iter_child(self, expr: ast.AST, scope, bindings, depth, active) -> frozenset:
        if isinstance(expr, ast.Call):
            dotted = self._dotted(expr.func) or ""
            if dotted in {"sorted", "list", "reversed", "tuple", "set"} and expr.args:
                return self._iter_child(expr.args[0], scope, bindings, depth, active)
            if dotted in _TREE_WALK_HELPERS and expr.args:
                # These helpers yield only files below their first argument.
                return frozenset(
                    self._join(base, ("**",))
                    for base in self.eval(expr.args[0], scope, bindings, depth, active)
                )
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
            owner = self._owner_scope(scope, expr.id)
            values |= frozenset().union(*(
                self.eval(value, owner, bindings if owner is scope else None, depth, inner)
                for value in owner.appends.get(expr.id, ())
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
            if dotted == "__iter_child__" and value.args and isinstance(
                seq := value.args[0], (ast.Tuple, ast.List, ast.Set)
            ):
                return frozenset().union(*(
                    self.eval(row.elts[index], scope, bindings, depth, active)
                    if isinstance(row, (ast.Tuple, ast.List)) and index < len(row.elts)
                    else frozenset({_Unknown("tuple element")})
                    for row in seq.elts
                )) or frozenset({_Unknown("tuple element")})
            if dotted in {"__iter_child__", "sorted", "list", "reversed", "tuple"} and value.args:
                return self._tuple_item(value.args[0], index, scope, bindings, depth, active)
            if leaf in {"exclusive_temp_path", "_exclusive_temp_path"} and index in (0, 1) and value.args:
                base = self.eval(value.args[0], scope, bindings, depth, active)
                return frozenset(
                    _ExtRel("temp sibling of guarded output")
                    if isinstance(v, _ExtRel) and v.tag == "guarded caller output" and not v.parts
                    else self._join(self._parent(v), ("*",))
                    for v in base
                )
            if leaf == "mkstemp" and index in (0, 1):
                dir_expr = _tempfile_dir_arg("mkstemp", value)
                if dir_expr is not None:
                    base = self.eval(dir_expr, scope, bindings, depth, active)
                    return frozenset(self._join(v, ("*",)) for v in base)
                return frozenset({_ExtRel("tempdir")})
        if isinstance(value, ast.Name):
            owner = self._owner_scope(scope, value.id)
            rows = owner.appends.get(value.id, ())
            if owner is not scope:
                scope, bindings = owner, None
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
                if texts is None or any("\x01" in text or "\x02" in text for text in texts):
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
                elif isinstance(part, ast.FormattedValue) and part.format_spec is None \
                        and part.conversion == -1 \
                        and (inlined := self._string_values(part.value, scope, seen)) is not None \
                        and len(inlined) == 1 and not any(m in inlined[0] for m in "\x01\x02"):
                    # A name bound to one constant string renders as that text.
                    text += inlined[0]
                elif isinstance(part, ast.FormattedValue) and self._safe_segment_value(part, scope):
                    text += "\x01"
                else:
                    text += "\x02"
            return [text]
        if isinstance(expr, ast.Name) and expr.id not in seen:
            exprs = self._lookup_exprs(expr.id, scope)
            if not exprs:
                module_exprs = self.module.assigns.get(expr.id, [])
                exprs = module_exprs
            if not exprs and expr.id in self.from_aliases:
                # A string constant imported from another tools/ module.
                source, member = self.from_aliases[expr.id]
                imported = self._imported_member(f"{source}.{member}")
                if imported is not None:
                    mod, name = imported
                    values = mod.module.assigns.get(name, [])
                    if values and all(isinstance(v, ast.Constant) and isinstance(v.value, str)
                                      for v in values):
                        return [v.value for v in values]
            if exprs:
                out: list[str] = []
                for sub in exprs:
                    values = self._string_values(sub, scope, seen | {expr.id})
                    if values is None:
                        return None
                    out.extend(values)
                return out
        return None

    def _safe_segment_value(self, node: ast.AST, scope: _Scope, seen: frozenset = frozenset()) -> bool:
        """True when ``node`` provably renders as text with no "/" or "\\" (Bar 4 v2 NF-2).

        Accepted: integers and integer formats, hex digests and tokens, the
        Path ``name``/``stem``/``suffix`` attributes, ``path_segment(...)``,
        and names whose every binding is one of these.
        """
        if isinstance(node, ast.FormattedValue):
            spec = node.format_spec
            if isinstance(spec, ast.JoinedStr) and len(spec.values) == 1 \
                    and isinstance(spec.values[0], ast.Constant) \
                    and isinstance(spec.values[0].value, str) \
                    and spec.values[0].value[-1:] in {"d", "x", "X", "o", "b"} \
                    and "/" not in spec.values[0].value:
                return True
            if spec is not None:
                return False
            return self._safe_segment_value(node.value, scope, seen)
        if isinstance(node, ast.Constant):
            return isinstance(node.value, int) and not isinstance(node.value, bool) or (
                isinstance(node.value, str) and node.value not in {"", ".", ".."}
                and "/" not in node.value and "\\" not in node.value
            )
        if isinstance(node, ast.Attribute):
            if node.attr == "hex":
                return isinstance(node.value, ast.Call) \
                    and (self._dotted(node.value.func) or "") in {"uuid.uuid4", "uuid.uuid1"}
            return node.attr in {"name", "stem", "suffix"} and self._is_path_receiver(node.value, scope)
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Slice):
            # A slice of separator-free text is separator-free.
            return self._safe_segment_value(node.value, scope, seen)
        if isinstance(node, ast.BoolOp):
            return all(self._safe_segment_value(value, scope, seen) for value in node.values)
        if isinstance(node, ast.Call):
            dotted = self._dotted(node.func) or ""
            if dotted in _SAFE_SEGMENT_FUNCS or dotted == _PATH_SEGMENT_VALIDATOR:
                return True
            if isinstance(node.func, ast.Attribute) and node.func.attr in {"hexdigest", "hex"} \
                    and not node.args:
                return True
            callee = self._callee_scope(node.func, scope)
            key = ("segment", id(callee))
            if callee is not None and callee.returns and key not in seen:
                return all(
                    self._safe_segment_value(expr, callee, seen | {key}) for expr in callee.returns
                )
            return False
        if isinstance(node, ast.JoinedStr):
            return all(
                (isinstance(part, ast.Constant) and isinstance(part.value, str)
                 and "/" not in part.value and "\\" not in part.value)
                or (isinstance(part, ast.FormattedValue) and self._safe_segment_value(part, scope, seen))
                for part in node.values
            )
        if isinstance(node, ast.Name) and node.id not in seen:
            exprs = self._lookup_exprs(node.id, scope) or self.module.assigns.get(node.id, [])
            return bool(exprs) and all(
                self._safe_segment_value(sub, scope, seen | {node.id}) for sub in exprs
            )
        return False

    def _is_path_receiver(self, node: ast.AST, scope: _Scope) -> bool:
        """``node`` evaluates only to path values, so ``.name`` holds no "/"."""
        values = self.eval(node, scope)
        return bool(values) and not any(isinstance(v, (_Unknown, _Null)) for v in values)

    def _segments(self, expr: ast.AST, scope, bindings, depth, active) -> list[object]:
        if isinstance(expr, ast.Call):
            dotted = self._dotted(expr.func) or ""
            if dotted == _PATH_SEGMENT_VALIDATOR:
                return [("*",)]
            if dotted == _RELATIVE_PATH_VALIDATOR:
                return [("**",)]
        texts = self._string_values(expr, scope)
        if texts is None:
            if isinstance(expr, ast.Attribute) and expr.attr == "name" \
                    and self._is_path_receiver(expr.value, scope):
                return [("*",)]
            if self._safe_segment_value(expr, scope):
                return [("*",)]
            return [
                value.parts if isinstance(value, _Relative) else
                value if isinstance(value, (_RepoRel, _ExtRel, _BadTraversal, _Param)) else
                _Unknown(f"path join operand at {self.rel}:{getattr(expr, 'lineno', '?')} "
                         "can replace or escape its base")
                for value in self.eval(expr, scope, bindings, depth, active)
            ]
        out: list[object] = []
        for text in texts:
            kind, segs = _parse_path_text(text)
            if kind == "rel":
                out.append(segs)
            elif kind == "bad":
                out.append(_BadTraversal(text))
            elif kind == "dynamic":
                out.append(_Unknown(f"formatted path operand at {self.rel}:{getattr(expr, 'lineno', '?')} "
                                    "can replace or escape its base"))
            else:
                out.append(_ExtRel(f"{kind} literal"))
        return out

    @staticmethod
    def _join(value: object, seg: object) -> object:
        if isinstance(seg, (_BadTraversal, _Unknown)):
            return seg
        if isinstance(seg, (_ExtRel, _RepoRel)):
            return seg
        if isinstance(seg, _Param):
            return _Unknown("path join operand can replace its base")
        assert isinstance(seg, tuple)
        if isinstance(value, _ExtRel) and value.tag in {
            "parent of guarded output",
            "ancestor above parent of a guarded path",
            "sibling of parent of a guarded path",
        }:
            return _ExtRel("sibling of parent of a guarded path", seg)
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
        if isinstance(value, _ExtRel) and value.tag in {
            "parent of guarded output",
            "ancestor above parent of a guarded path",
            "sibling of parent of a guarded path",
        }:
            return _ExtRel("ancestor above parent of a guarded path")
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
    def write_target_exprs(self, primitive: str, call: ast.Call, scope: _Scope) -> list[ast.AST | None] | None:
        """Target expressions for one write primitive; None means no path operand."""
        func = call.func
        if isinstance(func, ast.Name) and func.id not in self.from_aliases and func.id not in self.mod_aliases:
            exprs = self._lookup_exprs(func.id, scope)
            if len(exprs) == 1 and isinstance(exprs[0], ast.Attribute):
                func = exprs[0]
        args = call.args
        kwargs = {kw.arg: kw.value for kw in call.keywords if kw.arg}

        def arg(index: int, name: str) -> ast.AST | None:
            return args[index] if len(args) > index else kwargs.get(name)

        receiver = func.value if isinstance(func, ast.Attribute) else None
        if primitive in {"write_text", "write_bytes", "unlink", "mkdir", "rmdir", "touch",
                         "symlink_to", "hardlink_to", "chmod", "lchmod", "Path.open"}:
            return [receiver]
        if primitive in {"rename", "replace"}:
            return [receiver, arg(0, "target")]
        if primitive in {"os.replace", "os.rename"}:
            return [arg(0, "src"), arg(1, "dst")]
        if primitive == "os.renames":
            return [arg(0, "old"), arg(1, "new")]
        if primitive in {"os.link", "os.symlink"}:
            return [arg(1, "dst")]
        if primitive in {
            "os.remove", "os.removedirs", "os.unlink", "os.mkdir", "os.makedirs", "os.rmdir",
            "os.chmod", "os.lchmod", "os.chown", "os.lchown", "os.truncate",
            "os.mkfifo", "os.mknod", "os.utime", "os.open",
        }:
            if "dir_fd" in kwargs:
                return [ast.Constant(value=None)]
            return [arg(0, "path")]
        if primitive in {"os.fdopen", "os.fchmod", "os.fchown", "os.ftruncate"}:
            return [arg(0, "fd")]
        if primitive == "os.write":
            return None
        if primitive == "open":
            return [arg(0, "file")]
        if primitive in {"codecs.open", "logging.FileHandler"}:
            return [arg(0, "filename")]
        if primitive == "zipfile.ZipFile":
            return [arg(0, "file")]
        if primitive == "tarfile.open":
            return [arg(0, "name")]
        if primitive == "extractall":
            return [arg(0, "path") or ast.Constant(value=".")]
        if primitive == "extract":
            return [arg(1, "path") or ast.Constant(value=".")]
        if primitive == "shutil.move":
            return [arg(0, "src"), arg(1, "dst")]
        if primitive in {"shutil.copy", "shutil.copy2", "shutil.copyfile", "shutil.copytree"}:
            return [arg(1, "dst")]
        if primitive == "shutil.unpack_archive":
            return [arg(1, "extract_dir") or ast.Constant(value=".")]
        if primitive == "shutil.make_archive":
            return [arg(0, "base_name")]
        if primitive == "shutil.rmtree":
            return [arg(0, "path")]
        if primitive == "sqlite3.connect":
            return [arg(0, "database")]
        if primitive.startswith("tempfile."):
            dir_expr = _tempfile_dir_arg(primitive.removeprefix("tempfile."), call)
            return [dir_expr] if dir_expr is not None else None
        if primitive.startswith(("yaml.", "subprocess.", "os.", "asyncio.")):
            return None
        if primitive == "prune_empty_dirs":
            return [arg(0, "inbox")]
        if primitive in {"create_ancestors_and_track", "_create_ancestors_and_track"}:
            return [arg(0, "parent")]
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
        is_root_convention = (
            param.name in _ROOT_PARAM_NAMES
            and param.name not in self.non_root_params
            and callee not in self.escaped
        )
        if not sites or callee in self.escaped:
            if is_root_convention:
                out.add(self.apply_suffix(_RepoRel(()), param.suffix))
                if param.name in callee.defaults:
                    for default_val in self.eval(callee.defaults[param.name], callee.parent or self.module):
                        if not isinstance(default_val, _Null):
                            shifted = self.apply_suffix(default_val, param.suffix)
                            if isinstance(shifted, _Param):
                                out |= self.resolve_param(shifted, visited)
                            else:
                                out.add(shifted)
            else:
                default_vals = (
                    self.eval(callee.defaults[param.name], callee.parent or self.module)
                    if param.name in callee.defaults and callee not in self.escaped
                    else frozenset()
                )
                if default_vals and all(isinstance(dv, _RepoRel) for dv in default_vals):
                    for dv in default_vals:
                        out.add(self.apply_suffix(dv, param.suffix))
                else:
                    out.add(_Unknown(f"parameter {param.name!r} of {callee.qualname} is supplied outside this module"))
        elif is_root_convention and (
            callee is self.module_funcs.get(callee.qualname) or callee.cls is not None
        ) and not callee.qualname.rsplit(".", 1)[-1].startswith("_"):
            # Public entry points may also be called from outside the module;
            # every intra-module call site below is still resolved and checked.
            out.add(self.apply_suffix(_RepoRel(()), param.suffix))
        leaf = callee.qualname.rsplit(".", 1)[-1]
        if callee.cls is not None and not leaf.startswith("_") and not is_root_convention:
            # Instance-method calls from other modules cannot be resolved, so a
            # public method's path parameter is caller-supplied (Bar 4 v2 NF-3).
            out.add(_Unknown(f"parameter {param.name!r} of public method {callee.qualname} "
                             "may be supplied by any caller"))
        for caller_mod, call, caller_scope in self.external_calls.get(callee, ()):
            origin = f"{caller_mod.rel}:{call.lineno}"
            bound = caller_mod._call_bindings(callee, call, caller_scope, None, 0, frozenset())
            if bound is None:
                out.add(_Unknown(f"starred call to {callee.qualname} at {origin}"))
                continue
            if param.name in bound:
                external = set(bound[param.name])
            elif param.name in callee.defaults:
                external = set(self.eval(callee.defaults[param.name], callee.parent or self.module))
            else:
                out.add(_Unknown(f"parameter {param.name!r} of {callee.qualname} unbound at {origin}"))
                continue
            for value in external:
                resolved = (
                    caller_mod.resolve_param(value, visited)
                    if isinstance(value, _Param) and value.func in caller_mod.scopes else {value}
                )
                for item in resolved:
                    if is_root_convention and isinstance(item, (_Unknown, _Null)):
                        # The root convention: an unproved root is a repository root.
                        item = _RepoRel(())
                    out.add(self.apply_suffix(item, param.suffix))
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

    def _study_fence_chain_mkdir_bound(self) -> bool:
        """``open_dir_chain_nofollow`` creates directories only for ``_open_local_parent_dir_fd``.

        Its one creating call site passes the missing tail of the parent of an
        output that ``write_local_output_file`` guarded (or confined to the study
        scratch directory), so each ``os.mkdir`` makes an ancestor of a guarded
        output. Every other call site must pass ``create_missing=False``.
        """
        chain = self.module_funcs.get("open_dir_chain_nofollow")
        opener = self.module_funcs.get("_open_local_parent_dir_fd")
        if chain is None or opener is None or chain in self.escaped or opener in self.escaped \
                or self.external_calls.get(chain) or self.external_calls.get(opener):
            return False
        for call, caller in self.call_sites.get(chain, []):
            create = next((kw.value for kw in call.keywords if kw.arg == "create_missing"), None)
            if isinstance(create, ast.Constant) and create.value is False:
                continue
            if caller is not opener or [ast.unparse(a) for a in call.args] != ["base_path", "tail_parts"]:
                return False
        return all(
            caller.qualname == "write_local_output_file" and ast.unparse(call.args[0]) == "target.parent"
            for call, caller in self.call_sites.get(opener, [])
        ) and bool(self.call_sites.get(opener))

    def site_values(self, primitive: str, call: ast.Call, scope: _Scope) -> list[object]:
        if primitive.startswith("indirect."):
            return [_Unknown(f"write callable {primitive.removeprefix('indirect.')} used as a value")]
        if self.rel == "tools/learning_os/store/study_fence.py" and primitive == "os.mkdir" \
                and scope.qualname == "open_dir_chain_nofollow" and getattr(call, "_los_synthetic", False) \
                and self._study_fence_chain_mkdir_bound():
            return [_ExtRel("parent of guarded output")]
        if primitive.startswith(("os.", "asyncio.")) and (
            primitive.removeprefix("os.") in _OS_EXEC_ATTRS
            or primitive.removeprefix("asyncio.") in _ASYNCIO_SUBPROCESS_ATTRS
        ):
            return [_Unknown(f"{primitive} executes external command")]
        if primitive in {"subprocess.git.mv", "subprocess.git.rm", "subprocess.mv",
                         "subprocess.cp", "subprocess.rm"}:
            return self._subprocess_targets(primitive, call, scope)
        if primitive == "subprocess.shell":
            # A shell string hides its write targets from any static check.
            return [_Unknown("shell=True command")]
        if primitive == "subprocess.git.worktree":
            return self._git_worktree_targets(call, scope)
        if primitive.startswith("subprocess.git."):
            subcommand = primitive.removeprefix("subprocess.git.")
            if subcommand == "reset":
                words = self._option_words(call, scope)
                if words is None:
                    return [_Unknown("unresolved git reset command")]
                if {"--hard", "--merge", "--keep"} & set(words):
                    return [_Unknown("git reset rewrites the working tree")]
                return [_GitState(subcommand)]
            if subcommand in _INDEX_OR_REF_GIT_SUBCOMMANDS:
                return [_GitState(subcommand)]
            return [_Unknown(f"git {subcommand} rewrites working tree or has unproved target")]
        if primitive.startswith("subprocess."):
            return self._other_subprocess_targets(primitive, call, scope)
        dotted = self._dotted(call.func)
        if dotted == "learning_os.store.study_fence.write_local_output_file":
            return [_ExtRel("guarded caller output")]
        fd_relative = self._dir_fd_targets(primitive, call, scope)
        if fd_relative is not None:
            return fd_relative
        exprs = self.write_target_exprs(primitive, call, scope)
        if exprs is None:
            if primitive.startswith("tempfile."):
                return [_ExtRel("tempdir")]
            return []
        boundary_values: frozenset | None = None
        for kw in call.keywords if primitive in _BOUNDARY_ENFORCING_HELPERS else ():
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
            if self._engine_paths_bound and expr is not None and _is_engine_runtime_operand(
                scope, primitive, expr
            ):
                resolved = {
                    value for value in resolved
                    if not isinstance(value, _Unknown) or value.why not in _ENGINE_DYNAMIC_ORIGINS
                }
            out.extend(sorted(resolved, key=_describe))
        return out

    def _resolved(self, values) -> set:
        out: set = set()
        for value in values:
            if isinstance(value, _Param):
                out |= self.resolve_param(value, set())
            else:
                out.add(value)
        return out

    def _dir_fd_targets(self, primitive: str, call: ast.Call, scope: _Scope) -> list[object] | None:
        """Targets of an os.* write made relative to a directory descriptor.

        The destination is the descriptor's directory joined with the name
        operand; None when the call carries no descriptor keyword.
        """
        if not primitive.startswith("os."):
            return None
        kwargs = {kw.arg: kw.value for kw in call.keywords if kw.arg}
        if primitive in {"os.rename", "os.replace"}:
            operands = [("src_dir_fd", 0, "src"), ("dst_dir_fd", 1, "dst")]
        elif primitive == "os.link":
            operands = [("dst_dir_fd", 1, "dst")]
        elif primitive == "os.symlink":
            operands = [("dir_fd", 1, "dst")]
        else:
            operands = [("dir_fd", 0, "path")]
        if not any(keyword in kwargs for keyword, _, _ in operands):
            return None
        out: set = set()
        for keyword, index, name in operands:
            operand = call.args[index] if len(call.args) > index else kwargs.get(name)
            if operand is None:
                out.add(_Unknown("missing path operand"))
            elif keyword not in kwargs:
                out |= self._resolved(self.eval(operand, scope))
            else:
                segs = self._segments(operand, scope, None, 0, frozenset())
                for base in self._resolved(self.eval(kwargs[keyword], scope)):
                    out |= self._resolved({self._join(base, seg) for seg in segs})
        return sorted(out, key=_describe)

    def _command_list(self, call: ast.Call, scope: _Scope) -> ast.List | ast.Tuple | None:
        command = call.args[0] if call.args else next(
            (kw.value for kw in call.keywords if kw.arg == "args"), None
        )
        if isinstance(command, ast.Name):
            assignments = self._lookup_exprs(command.id, scope)
            command = assignments[0] if len(assignments) == 1 else None
        return command if isinstance(command, (ast.List, ast.Tuple)) else None

    def _option_words(self, call: ast.Call, scope: _Scope) -> list[str] | None:
        """The command's literal words before a ``--`` separator.

        None when the command is not a literal list, or when a non-literal
        element precedes ``--`` and so could itself be an option.
        """
        command = self._command_list(call, scope)
        if command is None:
            return None
        words: list[str] = []
        for item in command.elts:
            if not (isinstance(item, ast.Constant) and isinstance(item.value, str)):
                return None
            if item.value == "--":
                break
            words.append(item.value)
        return words

    def _subprocess_targets(self, primitive: str, call: ast.Call, scope: _Scope) -> list[object]:
        command = self._command_list(call, scope)
        if command is None:
            return [_Unknown("unresolved filesystem command")]
        start = 1
        if primitive in {"subprocess.git.mv", "subprocess.git.rm"}:
            subcommand = primitive.removeprefix("subprocess.git.")
            start = next((i + 1 for i, item in enumerate(command.elts)
                          if isinstance(item, ast.Constant) and item.value == subcommand), len(command.elts))
        allowed_flags = _FS_COMMAND_FLAGS.get(primitive, frozenset())
        operands = []
        for item in command.elts[start:]:
            if isinstance(item, ast.Constant) and isinstance(item.value, str) and item.value.startswith("-"):
                if item.value not in allowed_flags:
                    # ``-t DIR`` / ``--target-directory=DIR`` move the destination.
                    return [_Unknown(f"unsupported option {item.value!r} on {primitive}")]
                continue
            if isinstance(item, ast.Starred):
                return [_Unknown(f"starred operands on {primitive}")]
            operands.append(item)
        if primitive == "subprocess.cp":
            operands = operands[-1:]
        if not operands:
            return [_Unknown("filesystem command has no resolved path operands")]
        cwd = next((kw.value for kw in call.keywords if kw.arg == "cwd"), None)
        roots = self._resolved(self.eval(cwd, scope))
        values: set = set()
        for item in operands:
            for target in self._resolved(self.eval(item, scope)):
                if isinstance(target, _Relative):
                    values.update(self._resolved({self._join(root, target.parts) for root in roots}))
                else:
                    values.add(target)
        return sorted(values, key=_describe)

    def _git_worktree_targets(self, call: ast.Call, scope: _Scope) -> list[object]:
        """Resolve ``_git(repo, 'worktree', 'add'|'remove'|'prune', ...)`` destinations."""
        args = call.args
        idx = next(
            (i for i, a in enumerate(args) if isinstance(a, ast.Constant) and a.value == "worktree"),
            None,
        )
        if idx is None or idx + 1 >= len(args) or not isinstance(args[idx + 1], ast.Constant):
            return [_Unknown("unresolved git worktree subcommand")]
        action = args[idx + 1].value
        if action == "prune" and idx + 2 == len(args):
            # Prunes stale metadata for already-removed worktrees in compare_world.
            if self.rel == "tools/compare_world.py":
                return [_ExtRel("guarded caller output")]
            return [_Unknown("git worktree prune outside declared worktree owner")]
        if action == "remove" and idx + 4 == len(args) \
                and isinstance(args[idx + 2], ast.Constant) and args[idx + 2].value == "--force":
            return sorted(self._resolved(self.eval(args[idx + 3], scope)), key=_describe)
        if action == "add" and idx + 5 == len(args) \
                and isinstance(args[idx + 2], ast.Constant) and args[idx + 2].value == "--detach":
            return sorted(self._resolved(self.eval(args[idx + 3], scope)), key=_describe)
        return [_Unknown(f"unresolved git worktree {action!r} operands")]

    def _other_subprocess_targets(self, primitive: str, call: ast.Call, scope: _Scope) -> list[object]:
        """Verify non-git subprocess sites in declared modules against explicit operands or launcher pins."""
        cmd_arg = call.args[0] if call.args else next(
            (kw.value for kw in call.keywords if kw.arg == "args"), None
        )
        unparsed_cmd = ast.unparse(cmd_arg) if cmd_arg is not None else ""
        # 1. yt-dlp caption staging via -o <dest> in ingest_transcript.py
        if self.rel == "tools/ingest_transcript.py" and scope.qualname == "fetch":
            env_map = {
                name: exprs[-1]
                for name, exprs in scope.assigns.items()
                if exprs
            }
            elts = _flatten_cmd_elts(cmd_arg, env_map)
            if elts is not None:
                for i, elt in enumerate(elts[:-1]):
                    if isinstance(elt, ast.Constant) and elt.value == "-o":
                        return sorted(self._resolved(self.eval(elts[i + 1], scope)), key=_describe)
        # 2. compare_world.py running tools/generate.py --root <tree> on its scratch worktree
        if self.rel == "tools/compare_world.py" \
                and unparsed_cmd == "[sys.executable, str(generate), '--root', str(tree)]":
            if isinstance(cmd_arg, ast.List) and len(cmd_arg.elts) == 4:
                return sorted(self._resolved(self.eval(cmd_arg.elts[3], scope)), key=_describe)
        # 3. backup_manifest.py dry-run installer preflight against TemporaryDirectory vault
        if self.rel == "tools/learning_os/app/backup_manifest.py" \
                and unparsed_cmd == "[sys.executable, '-I', '-B', str(resolved_installer), *args, vault]" \
                and isinstance(cmd_arg, ast.List) and cmd_arg.elts:
            return sorted(self._resolved(self.eval(cmd_arg.elts[-1], scope)), key=_describe)
        # 4. Pinned gateway / sandbox launcher delegations (must declare <DELEGATED_GATEWAY_LAUNCHER>)
        pinned_launchers = {
            ("tools/agent_run.py", "_run_subprocess_bounded", "argv"): _DELEGATED_LAUNCHER_TOKEN,
            ("tools/learning_os/adapters/study_broker.py", "_run_subprocess_bounded", "cmd"):
                _DELEGATED_LAUNCHER_TOKEN,
            ("tools/study_launch.py", "launch_study", "[str(effective_sandbox), '-f', str(sb_path), *command]"):
                _DELEGATED_LAUNCHER_TOKEN,
            # Bar 4 v2 NF-5: Codex with --sandbox workspace-write can edit the
            # checkout directly; the gateway does not mediate it.
            ("tools/codex_obsidian.py", "main", "cmd"): _AGENT_WORKSPACE_WRITE_TOKEN,
            ("tools/codex_obsidian.py", "main", "[python_binary(), str(ROOT / 'tools' / 'los.py'), 'validate']"):
                _DELEGATED_LAUNCHER_TOKEN,
            ("tools/codex_obsidian.py", "main", "[python_binary(), str(ROOT / 'tools' / 'los.py'), 'generate']"):
                _DELEGATED_LAUNCHER_TOKEN,
        }
        token = pinned_launchers.get((self.rel, scope.qualname, unparsed_cmd))
        if token is not None:
            return [_DelegatedLauncher(f"{self.rel}::{scope.qualname}", token)]
        return [_Unknown(f"unclassified subprocess write {primitive}")]

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
        # A write callable used as a value is recorded at the reference itself.
        assert isinstance(node, ast.Call) or primitive.startswith("indirect.")
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

    def module_for(rel: str) -> _ModuleWriteSites | None:
        dotted = rel.removeprefix("tools/").removesuffix(".py").removesuffix("/__init__").replace("/", ".")
        mod = load_module(dotted)
        return mod if mod is not None and mod.rel == rel else None

    # Bar 4 v2 NF-3: register every call from one tools/ module into a function
    # or class of a declared module, so the callee's parameters are resolved
    # from all callers, not only those inside its own module.
    caller_scoped = {
        rel for rel, decl in effects.items()
        if decl.get("destinations") == ["<CALLER_SCOPED_ATOMIC_WRITE_PRIMITIVES>"]
    }
    for caller_file in _iter_tool_python_files(root):
        caller_rel = caller_file.relative_to(root).as_posix()
        caller_mod = module_for(caller_rel)
        if caller_mod is None:
            continue
        for caller_scope in list(caller_mod.scopes.values()):
            call_funcs: set[int] = set()
            for call in caller_scope.calls:
                call_funcs.add(id(call.func))
                imported = caller_mod._imported_member(caller_mod._dotted(call.func) or "")
                if imported is None:
                    continue
                target_mod, name = imported
                if target_mod.rel not in effects or target_mod.rel in caller_scoped \
                        or target_mod.rel == caller_rel or name in _WRITE_HELPERS:
                    # A recognized write helper is checked at the caller's own site.
                    continue
                callee = target_mod.module_funcs.get(name) or (
                    target_mod.class_methods.get(name, {}).get("__init__")
                )
                if callee is not None:
                    target_mod.external_calls.setdefault(callee, []).append((caller_mod, call, caller_scope))
            # A declared module's function used as a value elsewhere has callers
            # this analysis cannot see.
            for node in _iter_local(caller_scope.node):
                if id(node) in call_funcs or not isinstance(node, (ast.Name, ast.Attribute)) \
                        or not isinstance(node.ctx, ast.Load):
                    continue
                imported = caller_mod._imported_member(caller_mod._dotted(node) or "")
                if imported is None:
                    continue
                target_mod, name = imported
                callee = target_mod.module_funcs.get(name)
                if callee is not None and target_mod.rel in effects and target_mod.rel not in caller_scoped \
                        and name not in _WRITE_HELPERS and id(node) not in caller_mod.non_value_refs:
                    target_mod.escaped.add(callee)

    analyzed_modules: dict[str, _ModuleWriteSites] = {}
    for rel in sorted(effects):
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
        repo_dir_names = frozenset({"repository", root.name})
        caller_scoped_primitive = destinations == ["<CALLER_SCOPED_ATOMIC_WRITE_PRIMITIVES>"]
        shared = module_for(rel)
        analysis = shared if shared is not None else _ModuleWriteSites(
            rel, ast.parse(path.read_text(encoding="utf-8"), filename=rel), load_module,
        )
        visitor = _SiteVisitor(rel)
        visitor.visit(analysis.tree)
        analyzed_modules[rel] = analysis
        reported: set[tuple[int, str]] = set()
        for primitive, call, scope_node in visitor.sites:
            scope = analysis.expr_scope_of.get(id(call)) or (
                analysis.scopes.get(scope_node, analysis.module) if scope_node else analysis.module
            )
            for value in analysis.site_values(primitive, call, scope):
                if isinstance(value, _ReadOnlySQLite) and primitive == "sqlite3.connect" and any(
                    kw.arg == "uri" and isinstance(kw.value, ast.Constant) and kw.value.value is True
                    for kw in call.keywords
                ):
                    continue
                problem: str | None = None
                if isinstance(value, _BadTraversal):
                    problem = "joins a '..' traversal onto a repository-anchored path"
                elif isinstance(value, _DelegatedLauncher):
                    if value.token not in destinations:
                        problem = f"spawns a pinned launcher without declaring {value.token}"
                elif isinstance(value, _GitState):
                    if _GIT_STATE_TOKEN not in destinations:
                        problem = f"changes Git index or refs but the module does not declare {_GIT_STATE_TOKEN}"
                elif isinstance(value, _RepoRel):
                    if not repo_patterns:
                        problem = "is repository-anchored but the module declares no repository destination"
                    elif not any(
                        _pattern_covers(pattern, value.parts)
                        or (
                            primitive in {"mkdir", "os.mkdir", "os.makedirs", "create_ancestors_and_track"}
                            and _is_destination_parent(pattern, value.parts)
                        )
                        for pattern in repo_patterns
                    ):
                        problem = f"is outside declared destinations {repo_patterns}"
                elif caller_scoped_primitive:
                    # The shared atomic-write primitives take their target from
                    # the caller; each caller's own site is checked instead.
                    # Only targets originating from a function parameter are valid here (Bar 4 D12).
                    if not (isinstance(value, _Unknown) and value.why.startswith("parameter ")):
                        problem = "is not derived from a caller-supplied parameter in caller-scoped primitive"
                elif isinstance(value, _ExtRel):
                    if concrete:
                        problem = "is external but the module declares only repository destinations"
                    else:
                        problem = _external_destination_problem(
                            value, destinations, primitive, repo_dir_names,
                        )
                elif isinstance(value, (_Unknown, _Relative, _ReadOnlySQLite)):
                    # Fail closed in every declaration class (Bar 4 F1): a write
                    # whose destination the census cannot prove is never accepted
                    # because the module declares some other destination.
                    problem = (
                        "is unanchored in a module that declares only repository destinations"
                        if concrete else
                        "has no proved destination at this write site"
                    )
                if problem is None:
                    continue
                key = (call.lineno, _describe(value))
                if key in reported:
                    continue
                reported.add(key)
                failures.append(
                    f"A2-sites {rel}:{call.lineno}: {primitive} target {_describe(value)} {problem} — {FIX}"
                )

    # Bar 4 F4: verify cross-module callers under tools/ never pass a non-root
    # path into a declared writer's root/repo_root/core_root/repo parameter.
    for caller_file in _iter_tool_python_files(root):
        caller_rel = caller_file.relative_to(root).as_posix()
        caller_mod = analyzed_modules.get(caller_rel)
        if caller_mod is None:
            caller_tree = ast.parse(caller_file.read_text(encoding="utf-8"), filename=caller_rel)
            caller_mod = _ModuleWriteSites(caller_rel, caller_tree, load_module)
        for caller_scope in caller_mod.scopes.values():
            for call in caller_scope.calls:
                dotted = caller_mod._dotted(call.func) or ""
                imported = caller_mod._imported_member(dotted)
                if imported is None:
                    continue
                target_mod, fn_name = imported
                if target_mod.rel not in effects:
                    continue
                callee_scope = target_mod.module_funcs.get(fn_name)
                if callee_scope is None:
                    continue
                root_params = (
                    (set(callee_scope.params) | set(callee_scope.kwonly)) & _ROOT_PARAM_NAMES
                ) - target_mod.non_root_params
                if not root_params:
                    continue
                bound = caller_mod._call_bindings(callee_scope, call, caller_scope, None, 0, frozenset())
                if bound is None:
                    failures.append(
                        f"A2-sites {caller_rel}:{call.lineno}: starred call to {target_mod.rel}::{fn_name} "
                        f"hides root parameter — {FIX}"
                    )
                    continue
                for rname in sorted(root_params & set(bound)):
                    for val in bound[rname]:
                        bad_root = (
                            (isinstance(val, _RepoRel) and bool(val.parts))
                            or isinstance(val, (_Relative, _BadTraversal, _ExtRel))
                        )
                        if bad_root:
                            failures.append(
                                f"A2-sites {caller_rel}:{call.lineno}: call to {target_mod.rel}::{fn_name} "
                                f"passes non-repository root {_describe(val)} for {rname!r} — {FIX}"
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
    for symlink_rel in _find_tool_symlinks(root):
        failures.append(
            f"A2 {symlink_rel}: symlinked module or directory under tools/ is forbidden (Bar 4 F9)"
        )
    failures.extend(_python_scripts_without_suffix(root))
    if ratchet_entries:
        for entry in ratchet_entries:
            failures.append(
                f"A2 {entry.get('signature', '<unknown>')}: A2-static ratchets are retired; "
                f"declare writers in effects.yaml so check_declared_write_sites runs (Bar 4 F6)"
            )
    recorded: dict[str, int] = {}

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
    (tmp_path / "tools").mkdir(parents=True, exist_ok=True)
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
            "witness": "runtime",  # an owned-territory writer carries a disposition (2A §5.6)
        },
    }
    failures = scan_tools_census(root, valid, [], tree_roots=_load_tree_roots())
    assert failures == [], failures
    # Without its witness disposition the same writer fails (the negative half).
    bare = {**valid, "tools/material_summarize.py": {
        k: v for k, v in valid["tools/material_summarize.py"].items() if k != "witness"}}
    assert any("needs `witness: runtime`" in f for f in scan_tools_census(
        root, bare, [], tree_roots=_load_tree_roots()))


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


@pytest.mark.parametrize("rel, effect, destinations, control", [
    (
        "tools/learning_os/store/transactions.py",
        "canonical-engine",
        ["records/**", "generated/manifest.json"],
        "    (root / 'generated/manifest.json').unlink()\n",
    ),
    (
        "tools/learning_os/store/fs.py",
        "operational",
        ["<CALLER_SCOPED_ATOMIC_WRITE_PRIMITIVES>"],
        "    caller_path.write_text('sample')\n",
    ),
])
def test_declared_boundary_owner_still_checks_concrete_destination(
    tmp_path, rel, effect, destinations, control,
):
    root = tmp_path / "disposable-checkout"
    source = root / rel
    source.parent.mkdir(parents=True)
    inventory = {rel: {"effect": effect, "destinations": destinations}}
    header = "def run(root, caller_path):\n"
    source.write_text(header + control, encoding="utf-8")
    assert check_declared_write_sites(root, inventory) == []

    source.write_text(
        header + control + "    (root / 'generated/outside-scope').write_text('sample')\n",
        encoding="utf-8",
    )
    findings = check_declared_write_sites(root, inventory)
    assert len(findings) == 1
    assert "repo:generated/outside-scope" in findings[0]


def test_transaction_engine_rejects_unanchored_write_in_existing_owner(tmp_path):
    root = tmp_path / "disposable-checkout"
    rel = _CANONICAL_ENGINE_MODULE
    writer = root / rel
    writer.parent.mkdir(parents=True)
    inventory = {rel: {"effect": "canonical-engine", "destinations": [
        "records/**", "operations/transactions/**", "generated/manifest.json",
    ]}}
    source = (
        "from pathlib import Path\n"
        "def maintenance(root):\n"
        "    (root / 'generated/manifest.json').unlink()\n"
    )
    writer.write_text(source, encoding="utf-8")
    assert check_declared_write_sites(root, inventory) == []

    writer.write_text(
        source + "    (Path.cwd() / 'unowned.txt').write_text('sample')\n",
        encoding="utf-8",
    )
    findings = check_declared_write_sites(root, inventory)
    assert len(findings) == 1
    assert "unanchored (cwd)" in findings[0]


# Bar 4 (27 Nov 2026) F1/F2 counterexamples, each with its control. F1: a write
# whose destination the census cannot prove fails in every declaration class,
# and an external value must match a declared destination of its own kind.
# F2: subprocess writes are destination-checked or refused.
_GUARD_IMPORT = "from learning_os.store.contracts.write_scopes import guard_tool_output_path\n"


@pytest.mark.parametrize("destinations, body, expected", [
    pytest.param(["<TMPDIR>/**"], "    Path('records/x.yaml').write_text('x')\n",
                 "has no proved destination", id="F1-relative-records-in-tmpdir-module"),
    pytest.param(["<TMPDIR>/**"], "    Path(os.environ['PROBE']).write_text('x')\n",
                 "has no proved destination", id="F1-environment-destination"),
    pytest.param(["<TMPDIR>/**"], "    (Path.home() / '.zshrc').write_text('x')\n",
                 "home directory outside declared", id="F1-home-outside-declaration"),
    pytest.param(["../materials/**"],
                 "    (ROOT.parent / 'repository' / 'records' / 'x').write_text('x')\n",
                 "beside the repository outside declared", id="F1-parent-reenters-repository"),
    pytest.param(["<TMPDIR>/**"],
                 "    (Path(tempfile.mkdtemp()) / 'x').write_text('x')\n"
                 "    (Path('/private/tmp') / 'x').write_text('x')\n",
                 None, id="F1-control-temporary"),
    pytest.param(["../materials/**"], "    (ROOT.parent / 'materials' / 'x').write_text('x')\n",
                 None, id="F1-control-declared-sibling"),
    pytest.param(["<EXPLICIT_OUT_DIR>/**"], "    (guard_tool_output_path(raw) / 'x').write_text('x')\n",
                 None, id="F1-control-guarded-caller-path"),
    pytest.param(["<EXPLICIT_OUT_DIR>/**"],
                 "    (guard_tool_output_path(raw).parent.parent / 'records').write_text('x')\n",
                 "parent of a guarded path", id="F5-parent-of-guarded-path"),
    pytest.param(["generated/reports/**"], "    (guard_tool_output_path(raw) / 'x').write_text('x')\n",
                 "declares only repository destinations", id="F1-guarded-path-in-repository-only-module"),
    pytest.param(["generated/reports/x.md"],
                 "    subprocess.run(['git', 'rm', '-q', 'records/x.yaml'], check=True)\n",
                 "is unanchored", id="F2-git-rm"),
    pytest.param(["<GIT_INDEX_AND_COMMIT>"],
                 "    subprocess.run(['git', 'reset', '--hard', 'HEAD~1'], check=True)\n",
                 "git reset rewrites the working tree", id="F2-git-reset-hard"),
    pytest.param(["<GIT_INDEX_AND_COMMIT>"],
                 "    subprocess.run(['git', 'reset', '-q', 'HEAD', '--', *raw], check=True)\n",
                 None, id="F2-control-index-reset-with-pathspec"),
    pytest.param(["generated/reports/x.md"],
                 "    subprocess.run('rm -rf records', shell=True, check=True)\n",
                 "shell=True command", id="F2-shell-true"),
    pytest.param(["generated/reports/x.md"],
                 "    subprocess.run(['git', 'commit', '-m', 'x'], check=True)\n",
                 "does not declare <GIT_INDEX_AND_COMMIT>", id="F2-git-commit-undeclared"),
    pytest.param(["<GIT_INDEX_AND_COMMIT>"],
                 "    subprocess.run(['git', 'commit', '-m', 'x'], check=True)\n",
                 None, id="F2-control-git-commit-declared"),
    pytest.param(["<EXPLICIT_OUT_DIR>/**"],
                 "    with ExitStack() as stack:\n"
                 "        fd = open_guarded_directory(raw, stack)\n"
                 "        os.close(os.open('x', os.O_WRONLY | os.O_CREAT, 0o600, dir_fd=fd))\n",
                 None, id="dir-fd-control-guarded-directory"),
    pytest.param(["<EXPLICIT_OUT_DIR>/**"],
                 "    fd = os.open('/etc', os.O_RDONLY | os.O_DIRECTORY)\n"
                 "    os.close(os.open('x', os.O_WRONLY | os.O_CREAT, 0o600, dir_fd=fd))\n",
                 "absolute path", id="dir-fd-unguarded-absolute-directory"),
])
def test_census_fails_closed_on_unproved_destinations(tmp_path, destinations, body, expected):
    root = tmp_path / "repository"
    writer = root / "tools/zz_bar4_probe.py"
    writer.parent.mkdir(parents=True)
    writer.write_text(
        "import os\nimport subprocess\nimport tempfile\nfrom contextlib import ExitStack\n"
        "from pathlib import Path\n" + _GUARD_IMPORT
        + "from learning_os.store.contracts.write_scopes import open_guarded_directory\n"
        + "ROOT = Path(__file__).resolve().parents[1]\n\n\ndef run(raw):\n" + body,
        encoding="utf-8",
    )
    findings = check_declared_write_sites(
        root, {"tools/zz_bar4_probe.py": {"effect": "operational", "destinations": destinations}},
    )
    if expected is None:
        assert findings == []
    else:
        assert findings, "the census accepted the counterexample"
        assert any(expected in finding for finding in findings), findings


@pytest.mark.parametrize("probe_id, code", [
    ("U01-git-checkout", "import subprocess\ndef f():\n    subprocess.run(['git', 'checkout', 'HEAD', '--', 'records/x.yaml'])\n"),
    ("U02-git-restore", "import subprocess\ndef f():\n    subprocess.run(['git', 'restore', '--source=HEAD~1', 'records/x.yaml'])\n"),
    ("U03-git-apply", "import subprocess\ndef f():\n    subprocess.run(['git', 'apply', '/tmp/p.diff'])\n"),
    ("U04-git-clean", "import subprocess\ndef f():\n    subprocess.run(['git', 'clean', '-fdx', 'records'])\n"),
    ("U05-git-stash", "import subprocess\ndef f():\n    subprocess.run(['git', 'stash', '--include-untracked'])\n"),
    ("U06-rsync", "import subprocess\ndef f():\n    subprocess.run(['rsync', '-a', '/tmp/x/', 'records/'])\n"),
    ("U07-ln", "import subprocess\ndef f():\n    subprocess.run(['ln', '-sf', '/tmp/x', 'records/x.yaml'])\n"),
    ("U08-sh-c", "import subprocess\ndef f():\n    subprocess.run(['sh', '-c', 'echo x > records/x.yaml'])\n"),
    ("U09-os-system", "import os\ndef f():\n    os.system('echo x > records/x.yaml')\n"),
    ("U10-os-popen", "import os\ndef f():\n    os.popen('cp /tmp/x records/x.yaml')\n"),
    ("U11-builtins-open", "import builtins\ndef f():\n    builtins.open('records/log.md', 'w').write('x')\n"),
    ("U12-codecs-open", "import codecs\ndef f():\n    codecs.open('records/log.md', 'w', 'utf-8').write('x')\n"),
    ("U13-os-renames", "import os\ndef f():\n    os.renames('/tmp/x', 'records/x.yaml')\n"),
    ("U14-zipfile-extract", "import zipfile\ndef f():\n    zipfile.ZipFile('/tmp/b.zip').extractall('records')\n"),
    ("U15-shutil-unpack", "import shutil\ndef f():\n    shutil.unpack_archive('/tmp/b.zip', 'records')\n"),
    ("U17-cmd-concat", "import subprocess\ndef f(paths):\n    subprocess.run(['git', 'rm'] + list(paths))\n"),
    ("U18-os-execvp", "import os\ndef f():\n    os.execvp('cp', ['cp', '/tmp/x', 'records/x.yaml'])\n"),
    ("U19-path-chmod", "from pathlib import Path\ndef f():\n    Path('records/x.yaml').chmod(0o777)\n"),
    ("U20-sqlite-cli", "import subprocess\ndef f():\n    subprocess.run(['sqlite3', 'records/x.db', 'create table t(a)'])\n"),
    ("U21-bound-method", "from pathlib import Path\ndef f():\n    w = Path('records/x.yaml').write_text\n    w('x')\n"),
    ("U22-augassign-fdopen", "import os\ndef f():\n    flags = os.O_RDONLY\n    flags |= os.O_WRONLY | os.O_CREAT\n    fd = os.open('records/x.yaml', flags)\n    os.fdopen(fd, 'w').write('x')\n"),
    ("U23-tarfile-extract", "import tarfile\ndef f():\n    tarfile.open('/tmp/b.tgz').extractall('records')\n"),
    ("U24-logging-filehandler", "import logging\ndef f():\n    logging.getLogger('x').addHandler(logging.FileHandler('records/x.log'))\n"),
    ("U25-asyncio-exec", "import asyncio\nasync def f():\n    await asyncio.create_subprocess_exec('cp', '/tmp/x', 'records/x.yaml')\n"),
    ("U26-fs-prune-helper", "from pathlib import Path\nfrom learning_os.store.fs import prune_empty_dirs\ndef f():\n    prune_empty_dirs(Path('records'), Path('records/a/b'))\n"),
    ("U27-unmediated-concat", "from learning_os.store.transactions import TransactionService\ndef f(root):\n    TransactionService(root, **{'_unmediated_' + 'test_only': True})\n"),
    ("U28-starred-git-wrapper", "import subprocess\ndef _git(*args):\n    return subprocess.run(['git', *args], check=True)\ndef f():\n    _git('checkout', 'HEAD', '--', 'records/x.yaml')\n"),
])
def test_census_catches_bar4_f3_and_f8_undeclared_primitives(tmp_path: Path, probe_id: str, code: str):
    root, effects = _synthetic_effects(tmp_path)
    (root / "tools/zz_probe.py").write_text(code, encoding="utf-8")
    failures = scan_tools_census(root, effects, [], tree_roots=_load_tree_roots())
    assert failures, f"{probe_id} was accepted by scan_tools_census"


def test_census_catches_bar4_f4_f5_f6_f10_f11_and_d12(tmp_path: Path):
    """Bar 4 F4, F5 residual, F6, D12, F10, and F11 counterexamples and controls."""
    # F4 intra-module and cross-module non-root passed to parameter named ``root``
    root = tmp_path / "f4"
    (root / "tools").mkdir(parents=True)
    (root / "tools/writer.py").write_text(
        "from pathlib import Path\n"
        "def write_report(root: Path):\n"
        "    (root / 'generated/reports/out.md').write_text('x')\n"
        "def bad_caller():\n"
        "    write_report(Path(__file__).resolve().parents[1] / 'records')\n",
        encoding="utf-8",
    )
    f4_effects = {"tools/writer.py": {"effect": "cache", "destinations": ["generated/reports/out.md"], "reason": "r"}}
    f4_intra = check_declared_write_sites(root, f4_effects)
    assert any("repo:records/generated/reports/out.md is outside declared destinations" in m for m in f4_intra), f4_intra

    (root / "tools/writer.py").write_text(
        "from pathlib import Path\n"
        "def write_report(root: Path):\n"
        "    (root / 'generated/reports/out.md').write_text('x')\n",
        encoding="utf-8",
    )
    assert check_declared_write_sites(root, f4_effects) == []
    (root / "tools/caller.py").write_text(
        "from pathlib import Path\n"
        "from writer import write_report\n"
        "def bad():\n"
        "    write_report(Path(__file__).resolve().parents[1] / 'records')\n",
        encoding="utf-8",
    )
    f4_cross = check_declared_write_sites(root, f4_effects)
    assert any("passes non-repository root repo:records" in m for m in f4_cross), f4_cross

    # F5 residual: .parent.parent.mkdir() and guarded path in <TMPDIR>-only module
    f5_root = tmp_path / "f5"
    (f5_root / "tools").mkdir(parents=True)
    (f5_root / "tools/out_tool.py").write_text(
        _GUARD_IMPORT
        + "def run(raw):\n"
        "    safe = guard_tool_output_path(raw)\n"
        "    safe.parent.parent.mkdir(parents=True, exist_ok=True)\n",
        encoding="utf-8",
    )
    f5_res = check_declared_write_sites(
        f5_root, {"tools/out_tool.py": {"effect": "tooling", "destinations": ["<EXPLICIT_OUT_FILE>"]}}
    )
    assert any("parent of a guarded path" in m for m in f5_res), f5_res

    (f5_root / "tools/tmp_only.py").write_text(
        _GUARD_IMPORT + "def run(raw):\n    guard_tool_output_path(raw).write_text('x')\n",
        encoding="utf-8",
    )
    f5_tmp = check_declared_write_sites(
        f5_root, {"tools/tmp_only.py": {"effect": "operational", "destinations": ["<TMPDIR>/**"]}}
    )
    assert any("uses a caller-guarded path in a module declaring only" in m for m in f5_tmp), f5_tmp

    # F6: non-empty A2-static ratchet entries are rejected
    r_root, r_effects = _synthetic_effects(tmp_path / "f6")
    r_fail = scan_tools_census(
        r_root, r_effects, [{"signature": "tools/read_only.py::run::write_text", "count": 1}],
        tree_roots=_load_tree_roots(),
    )
    assert any("A2-static ratchets are retired" in m for m in r_fail), r_fail

    # D12: fs.py (<CALLER_SCOPED_ATOMIC_WRITE_PRIMITIVES>) rejects cwd-relative literals
    d12_root = tmp_path / "d12"
    (d12_root / "tools/learning_os/store").mkdir(parents=True)
    (d12_root / "tools/learning_os/store/fs.py").write_text(
        "from pathlib import Path\ndef leak():\n    Path('records/x.yaml').write_text('x')\n",
        encoding="utf-8",
    )
    d12_fail = check_declared_write_sites(
        d12_root,
        {"tools/learning_os/store/fs.py": {"effect": "operational", "destinations": ["<CALLER_SCOPED_ATOMIC_WRITE_PRIMITIVES>"]}},
    )
    assert any("not derived from a caller-supplied parameter" in m for m in d12_fail), d12_fail

    # F10: numeric write flag in study_fence.fd_open_flags fails closed
    f10_root = tmp_path / "f10"
    (f10_root / "tools/learning_os/store").mkdir(parents=True)
    sf_src = (ROOT / "tools/learning_os/store/study_fence.py").read_text(encoding="utf-8")
    (f10_root / "tools/learning_os/store/study_fence.py").write_text(
        sf_src.replace("    return flags\n", "    flags |= 0x0201\n    return flags\n", 1),
        encoding="utf-8",
    )
    f10_fail = check_declared_write_sites(
        f10_root,
        {"tools/learning_os/store/study_fence.py": {
            "effect": "operational",
            "destinations": ["$LOS_SCRATCH_DIR/**", "<TMPDIR>/**", "<EXPLICIT_LOCAL_OUTPUT>"],
        }},
    )
    assert f10_fail, "numeric write flag in fd_open_flags was accepted"

    # F11: migration declaration without contract fails even outside DATA_ROOTS
    mig_root, mig_effects = _synthetic_effects(tmp_path / "f11")
    bad_mig = {
        "tools/writer_ok.py": {
            "effect": "migration",
            "destinations": ["generated/reports/demo.txt"],
            "reason": "Migration without contract",
        }
    }
    mig_fail = scan_tools_census(mig_root, bad_mig, [], tree_roots=_load_tree_roots())
    assert any("migration declaration must cite its recorded maintenance contract" in m for m in mig_fail), mig_fail


def test_census_input_inventory_matches_tracked_tools_and_rejects_symlinks(tmp_path: Path):
    """Bar 4 F9: scanned tools/**/*.py equals tracked + untracked .py files, and symlinks fail."""
    import subprocess

    scanned = {p.relative_to(ROOT).as_posix() for p in _iter_tool_python_files(ROOT)}
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z", "--", "tools"],
        capture_output=True, check=True,
    )
    tracked_py = {
        entry.decode("utf-8")
        for entry in proc.stdout.split(b"\0")
        if entry and entry.decode("utf-8").endswith(".py")
    }
    assert tracked_py <= scanned, f"tracked tools/*.py skipped by census: {sorted(tracked_py - scanned)}"

    root, effects = _synthetic_effects(tmp_path)
    outside = tmp_path / "outside.py"
    outside.write_text("from pathlib import Path\nPath('records/x').write_text('x')\n", encoding="utf-8")
    (root / "tools/sneaky_link.py").symlink_to(outside)
    failures = scan_tools_census(root, effects, [], tree_roots=_load_tree_roots())
    assert any("tools/sneaky_link.py: symlinked module or directory" in m for m in failures), failures


def test_git_hooks_inventory_and_write_safety():
    """Bar 4 F12: mechanical inventory and canonical-write check for non-Python tools/hooks/*."""
    hooks_dir = ROOT / "tools" / "hooks"
    entries = sorted(p.name for p in hooks_dir.iterdir())
    assert entries == ["post-commit", "pre-commit", "pre-push"], entries
    for name in entries:
        hook = hooks_dir / name
        assert hook.is_file() and not hook.is_symlink(), name
        text = hook.read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            for canonical_root in DATA_ROOTS:
                assert f">{canonical_root}/" not in stripped.replace(" ", ""), (name, stripped)
                assert f"rm -rf {canonical_root}" not in stripped, (name, stripped)


# ---------------------------------------------------------------------------
# Bar 4 v2 (REVIEW-V2-17a4c5e) counterexamples NF-2..NF-5, each with a control.
# ---------------------------------------------------------------------------
_V2_IMPORTS = (
    "import functools\nimport operator\nimport os\nimport subprocess\nimport tempfile\n"
    "from pathlib import Path\n" + _GUARD_IMPORT
    + "from learning_os.store.contracts.write_scopes import path_segment, relative_path\n"
    + "ROOT = Path(__file__).resolve().parents[1]\n\n\n"
)


@pytest.mark.parametrize("destinations, body, expected", [
    # NF-2: '..' on external anchors, dynamic and formatted operands, tempfile dir.
    pytest.param(["<EXPLICIT_OUT_FILE>"],
                 "def run(raw):\n    (guard_tool_output_path(raw) / '..' / '..' / 'records/m.yaml').write_text('x')\n",
                 "'..'", id="NF2-dotdot-on-guarded-output"),
    pytest.param(["../materials/**"],
                 "def run(raw):\n    (ROOT.parent / 'materials' / '..' / 'repository' / 'records/m.yaml').write_text('x')\n",
                 "'..'", id="NF2-dotdot-on-sibling"),
    pytest.param(["<TMPDIR>/**"],
                 "def run(raw):\n    (Path(tempfile.gettempdir()) / os.environ['EVIL']).write_text('x')\n",
                 "can replace or escape its base", id="NF2-environment-join-operand"),
    pytest.param(["generated/reports/**"],
                 "def run(raw):\n    (ROOT / 'generated/reports' / f'{raw}').write_text('x')\n",
                 "can replace or escape its base", id="NF2-formatted-join-operand"),
    pytest.param(["<TMPDIR>/**"],
                 "def run(raw):\n    d = tempfile.mkdtemp('', 'pwn-', ROOT / 'records')\n    (Path(d) / 'e.yaml').write_text('x')\n",
                 "declares no repository destination", id="NF2-mkdtemp-positional-dir"),
    pytest.param(["<TMPDIR>/**"],
                 "def run(raw):\n    with tempfile.TemporaryDirectory(dir=ROOT / 'records') as d:\n        pass\n",
                 "declares no repository destination", id="NF2-TemporaryDirectory-dir"),
    pytest.param(["generated/reports/**"],
                 "from learning_os.store.transactions import atomic_write_bytes\n"
                 "def run(raw):\n    atomic_write_bytes(Path(raw), b'x', boundary=ROOT / 'generated/reports')\n",
                 "unanchored", id="NF1-boundary-only-for-enforcing-helpers"),
    pytest.param(["generated/reports/**"],
                 "from learning_os.store.fs import atomic_write_text_exclusive\n"
                 "def run(raw):\n    atomic_write_text_exclusive(Path(raw), 'x', boundary=ROOT / 'generated/reports')\n",
                 None, id="NF1-control-boundary-enforcing-helper"),
    pytest.param(["generated/reports/**"],
                 "def run(raw):\n    (ROOT / 'generated/reports' / path_segment(raw)).write_text('x')\n"
                 "    (ROOT / 'generated/reports' / relative_path(raw)).write_text('x')\n"
                 "    (ROOT / 'generated/reports' / f'r-{os.getpid()}.md').write_text('x')\n",
                 None, id="NF2-control-validated-and-proved-segments"),
    # NF-3: comprehensions, walrus, shadowing, nonlocal, container mutation.
    pytest.param(["generated/reports/**"],
                 "def write_report(path):\n    path.write_text('x')\n"
                 "def run(raw):\n    write_report(ROOT / 'generated/reports/a.md')\n"
                 "    [write_report(ROOT / 'records') for _ in (1,)]\n",
                 "outside declared destinations", id="NF3-call-inside-comprehension"),
    pytest.param(["generated/reports/**"],
                 "def run(raw):\n    p = ROOT / 'generated/reports/a.md'\n"
                 "    [(p := ROOT / 'records/m.yaml') for _ in (1,)]\n    p.write_text('x')\n",
                 "outside declared destinations", id="NF3-walrus-in-comprehension"),
    pytest.param(["generated/reports/**"],
                 "def run(raw):\n    p = ROOT / 'generated/reports/a.md'\n"
                 "    [p.write_text('x') for p in [ROOT / 'records/m.yaml']]\n",
                 "outside declared destinations", id="NF3-comprehension-shadowing"),
    pytest.param(["generated/reports/**"],
                 "def run(raw):\n    p = ROOT / 'generated/reports/a.md'\n"
                 "    def inner():\n        nonlocal p\n        p = ROOT / 'records/m.yaml'\n"
                 "    inner()\n    p.write_text('x')\n",
                 "outside declared destinations", id="NF3-nonlocal"),
    pytest.param(["generated/reports/**"],
                 "def run(raw):\n    xs = [ROOT / 'generated/reports/a.md']\n    xs.extend([ROOT / 'records/m.yaml'])\n"
                 "    for x in xs:\n        x.write_text('x')\n",
                 "outside declared destinations", id="NF3-list-extend"),
    pytest.param(["generated/reports/**"],
                 "def run(raw):\n    xs = [ROOT / 'generated/reports/a.md']\n    xs[0] = ROOT / 'records/m.yaml'\n"
                 "    for x in xs:\n        x.write_text('x')\n",
                 "outside declared destinations", id="NF3-subscript-store"),
    pytest.param(["generated/reports/**"],
                 "def run(raw):\n    p = ROOT / 'generated/reports/a.md'\n"
                 "    [q.write_text('x') for q in [p]]\n",
                 None, id="NF3-control-comprehension-in-scope"),
    # NF-4: git options, fs flags, indirect write callables.
    pytest.param(["generated/reports/**"],
                 "def run(raw):\n    subprocess.run(['git', 'diff', f'--output={raw}'])\n",
                 "unanchored", id="NF4-git-diff-formatted-output"),
    pytest.param(["generated/reports/**"],
                 "def run(raw):\n    subprocess.run(['git', 'diff', *raw])\n",
                 "unanchored", id="NF4-git-diff-starred-options"),
    pytest.param(["generated/reports/**"],
                 "def run(raw):\n    subprocess.run(['cp', '--target-directory=records', str(ROOT / 'generated/reports/r.md')])\n",
                 "unsupported option", id="NF4-cp-target-directory"),
    pytest.param(["generated/reports/**"],
                 "def run(raw):\n    functools.partial(Path('records/x.yaml').write_text, 'x')()\n",
                 "cwd-relative:records/x.yaml", id="NF4-partial-write-text"),
    pytest.param(["generated/reports/**"],
                 "def run(raw):\n    getattr(Path('records/x.yaml'), 'write_text')('x')\n",
                 "used as a value", id="NF4-getattr-write-text"),
    pytest.param(["generated/reports/**"],
                 "def run(raw):\n    subprocess.run(['git', 'diff', '--name-only', raw, '--', *raw])\n"
                 "    subprocess.run(['git', 'diff-tree', '-r', '--end-of-options', *raw])\n",
                 None, id="NF4-control-git-data-arguments"),
])
def test_census_catches_bar4_v2_declared_counterexamples(tmp_path, destinations, body, expected):
    root = tmp_path / "repository"
    writer = root / "tools/zz_v2_probe.py"
    writer.parent.mkdir(parents=True)
    writer.write_text(_V2_IMPORTS + body, encoding="utf-8")
    findings = check_declared_write_sites(
        root, {"tools/zz_v2_probe.py": {"effect": "operational", "destinations": destinations}},
    )
    if expected is None:
        assert findings == []
    else:
        assert findings, "the census accepted the counterexample"
        assert any(expected in finding for finding in findings), findings


@pytest.mark.parametrize("probe_id, code", [
    ("NF4-name-alias", "from os import remove\ndef f():\n    fn = remove\n    fn('records/x.yaml')\n"),
    ("NF4-partial", "import functools\nfrom pathlib import Path\ndef f():\n"
                    "    functools.partial(Path('records/x.yaml').write_text, 'x')()\n"),
    ("NF4-getattr", "from pathlib import Path\ndef f():\n    getattr(Path('records/x.yaml'), 'write_text')('x')\n"),
    ("NF4-methodcaller", "import operator\nfrom pathlib import Path\ndef f():\n"
                         "    operator.methodcaller('write_text', 'x')(Path('records/x.yaml'))\n"),
    ("NF4-callback-value", "import os\ndef f(xs):\n    list(map(os.remove, xs))\n"),
    ("NF4-git-diff-output", "import subprocess\ndef f(out):\n    subprocess.run(['git', 'diff', f'--output={out}'])\n"),
    ("NF4-git-diff-starred", "import subprocess\ndef f(extra):\n    subprocess.run(['git', 'diff', *extra])\n"),
    ("NF4-git-log-abbreviated-output", "import subprocess\ndef f():\n    subprocess.run(['git', 'log', '--outp=x'])\n"),
])
def test_census_catches_bar4_v2_undeclared_indirection(tmp_path: Path, probe_id: str, code: str):
    root, effects = _synthetic_effects(tmp_path)
    (root / "tools/zz_probe.py").write_text(code, encoding="utf-8")
    failures = scan_tools_census(root, effects, [], tree_roots=_load_tree_roots())
    assert failures, f"{probe_id} was accepted by scan_tools_census"


def test_census_bar4_v2_cross_module_callers_and_constructors(tmp_path: Path):
    """NF-3: a declared helper's non-root parameter and class constructors from other modules."""
    root = tmp_path / "repository"
    (root / "tools").mkdir(parents=True)
    (root / "tools/writer.py").write_text(
        "from pathlib import Path\n"
        "ROOT = Path(__file__).resolve().parents[1]\n"
        "def write_one(path: Path) -> None:\n    path.write_text('x')\n"
        "def main() -> None:\n    write_one(ROOT / 'generated/reports/a.md')\n"
        "class Store:\n"
        "    def __init__(self, root: Path) -> None:\n        self.root = root\n"
        "    def _put(self) -> None:\n        (self.root / 'generated/reports/s.md').write_text('x')\n",
        encoding="utf-8",
    )
    effects = {"tools/writer.py": {"effect": "cache", "destinations": ["generated/reports/**"], "reason": "r"}}
    assert check_declared_write_sites(root, effects) == []
    (root / "tools/rogue.py").write_text(
        "from pathlib import Path\nfrom writer import Store, write_one\n"
        "ROOT = Path(__file__).resolve().parents[1]\n"
        "def run() -> None:\n    write_one(ROOT / 'records/m.yaml')\n    Store(ROOT / 'records')\n",
        encoding="utf-8",
    )
    findings = check_declared_write_sites(root, effects)
    assert any("repo:records/m.yaml is outside declared destinations" in f for f in findings), findings
    assert any("repo:records/generated/reports/s.md is outside declared destinations" in f
               for f in findings), findings


def test_census_bar4_v2_pins_placeholders_that_would_bless_new_writers(tmp_path: Path):
    """NF-4/NF-5: reserved placeholders cannot be granted by a new declaration."""
    root, effects = _synthetic_effects(tmp_path)
    (root / "tools/rogue_git.py").write_text(
        "import subprocess\ndef f():\n"
        "    subprocess.run(['git', 'add', 'records/m.yaml'])\n"
        "    subprocess.run(['git', 'commit', '-m', 'x'])\n",
        encoding="utf-8",
    )
    effects = {**effects, "tools/rogue_git.py": {
        "effect": "operational", "destinations": ["<GIT_INDEX_AND_COMMIT>"], "reason": "r"}}
    failures = scan_tools_census(root, effects, [], tree_roots=_load_tree_roots())
    assert any("<GIT_INDEX_AND_COMMIT> is reserved" in f for f in failures), failures

    (root / "tools/rogue_agent.py").write_text(
        "import subprocess\ndef f(cmd):\n    subprocess.run(cmd)\n", encoding="utf-8",
    )
    effects = {**effects, "tools/rogue_agent.py": {
        "effect": "operational", "destinations": ["<AGENT_WORKSPACE_WRITE_LAUNCHER>"], "reason": "r"}}
    failures = scan_tools_census(root, effects, [], tree_roots=_load_tree_roots())
    assert any("<AGENT_WORKSPACE_WRITE_LAUNCHER> is reserved" in f for f in failures), failures


def test_codex_launcher_is_declared_as_agent_workspace_write():
    """NF-5: the Codex workspace-write launch is not a gateway delegate."""
    effects = _load_effects_yaml()
    declaration = effects["tools/codex_obsidian.py"]
    assert "<AGENT_WORKSPACE_WRITE_LAUNCHER>" in declaration["destinations"]
    assert "2B" in declaration["contract"]


# ---- 2A re-entry (REENTRY-CRITIQUE rev 2): census unit tests -------------
#
# Each case is disposable census input; the real tree stays green through
# test_static_lint_matches_baseline. Upstream -reg branches repeat the §7
# regressions against the real tree.


def _probe_failures(tmp_path: Path, modules: dict[str, str], effects: dict | None = None) -> list[str]:
    root, base = _synthetic_effects(tmp_path)
    for rel, source in modules.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
    return scan_tools_census(root, {**base, **(effects or {})}, [], tree_roots=_load_tree_roots())


@pytest.mark.parametrize("declaration, owned, expected", [
    ("operations/transactions/**", "operations/transactions/transaction-*.yaml", True),
    ("operations/transactions/revisions.yaml", "operations/transactions/revisions.yaml", True),
    ("operations/**", "operations/ai-actions/**", True),
    ("generated/reports/**", "operations/transactions/**", False),
])
def test_reentry_declaration_overlap_cases(declaration, owned, expected):
    """REENTRY §5.2 table: overlap is a pattern operation in both directions."""
    assert _patterns_overlap(declaration, owned) is expected
    assert _patterns_overlap(owned, declaration) is expected


def test_reentry_overlap_is_not_containment():
    """REENTRY §4: a broad declaration must be authorized in full."""
    assert _patterns_overlap("operations/**", "operations/ai-actions/**")
    assert not _pattern_contains("operations/ai-actions/**", "operations/**")
    assert _pattern_contains("operations/**", "operations/ai-actions/x.yaml")
    assert not _pattern_contains("operations/ai-actions/*", "operations/ai-actions/a/b.yaml")


def _declaration_failures(tmp_path: Path, rel: str, dest: str) -> list[str]:
    root = tmp_path / "decl"
    (root / rel).parent.mkdir(parents=True, exist_ok=True)
    (root / rel).write_text("def f():\n    return None\n", encoding="utf-8")
    _, failures = validate_effects_declarations(
        {rel: {"effect": "operational", "destinations": [dest], "reason": "r"}}, root=root)
    assert not any("target does not exist" in f for f in failures), failures
    return failures


def test_reentry_pattern_outside_both_grammars_is_rejected(tmp_path):
    for bad in ("operations/tran**/x.yaml", "operations/**x", "operations/../records/**"):
        assert _declaration_failures(tmp_path, "tools/zz_grammar.py", bad), bad
    assert _declaration_failures(tmp_path, "tools/zz_grammar.py", "generated/reports/**") == []


@pytest.mark.parametrize("dest", [
    "operations/transactions/transaction-*.yaml",
    "operations/transactions/**",
    "operations/migrations/projects-to-modules-v62/**",
    "archive/inbox/**",
    "system/contracts/**",
])
def test_reentry_a_new_module_cannot_declare_owned_territory(tmp_path, dest):
    """N-1: a declaration alone never grants owned territory (REENTRY §7)."""
    failures = _declaration_failures(tmp_path, "tools/zz_claim.py", dest)
    assert any("owned territory" in f or "canonical DATA_ROOTS" in f for f in failures), failures


def test_reentry_alternative_authorities_and_the_engine_refusals():
    """N-1 controls: the module row and the engine row are alternatives."""
    data_roots = tuple(DATA_ROOTS)
    storage = "tools/learning_os/store/ai_actions/storage.py"
    service = "tools/learning_os/app/ai_actions/service.py"
    assert _owned_territory_failures(storage, "operations/ai-actions/**", "operational", None, data_roots) == []
    assert _owned_territory_failures(service, "operations/ai-actions/**", "operational", None, data_roots)
    engine = _CANONICAL_ENGINE_MODULE
    assert _owned_territory_failures(engine, "operations/ai-actions/**", "canonical-engine", None, data_roots) == []
    for refused in ("boards/**", "bases/**", "operations/gateway-requests/**"):
        assert _owned_territory_failures(engine, refused, "canonical-engine", None, data_roots), refused


@pytest.mark.parametrize("probe_id, code", [
    ("open-kwargs", "def f(p, kw):\n    open(p, **kw)\n"),
    ("open-starred", "def f(p, a):\n    open(p, *a)\n"),
    ("open-unresolved-mode", "def f(p, m):\n    open(p, mode=m)\n"),
    ("path-open-kwargs", "from pathlib import Path\ndef f(p, kw):\n    Path(p).open(**kw)\n"),
    ("io-open-kwargs", "import io\ndef f(p, kw):\n    io.open(p, **kw)\n"),
    ("codecs-open-kwargs", "import codecs\ndef f(p, kw):\n    codecs.open(p, **kw)\n"),
    ("fdopen-starred", "import os\ndef f(fd, a):\n    os.fdopen(fd, *a)\n"),
    ("zipfile-kwargs", "import zipfile\ndef f(p, kw):\n    zipfile.ZipFile(p, **kw)\n"),
    ("tarfile-kwargs", "import tarfile\ndef f(p, kw):\n    tarfile.open(p, **kw)\n"),
    ("partial-open-read", "import functools\ndef f():\n    return functools.partial(open, mode='r')\n"),
    ("partial-os-open", "import functools, os\ndef f(p):\n    return functools.partial(os.open, p, os.O_RDONLY)\n"),
    ("dotted-import-remove", "import os.path\ndef f(p):\n    os.remove(p)\n"),
])
def test_reentry_opaque_modes_and_deferred_openers_fail_closed(tmp_path, probe_id, code):
    """N-2 (REENTRY §5.3): only a literal read-only mode at the call is read-only."""
    failures = _probe_failures(tmp_path, {"tools/zz_n2.py": code})
    assert any("tools/zz_n2.py" in f for f in failures), (probe_id, failures)


@pytest.mark.parametrize("code", [
    "def f(p):\n    with open(p, 'r', encoding='utf-8') as h:\n        return h.read()\n",
    "def f(p):\n    with open(p) as h:\n        return h.read()\n",
    "from pathlib import Path\ndef f(p):\n    with Path(p).open('rb') as h:\n        return h.read()\n",
])
def test_reentry_literal_read_only_openers_stay_read_only(tmp_path, code):
    failures = _probe_failures(tmp_path, {"tools/zz_reader.py": code})
    assert not any("tools/zz_reader.py" in f for f in failures), failures


def test_reentry_declared_writer_using_open_kwargs_outside_its_scope(tmp_path):
    """§7: an already-declared writer's opaque-mode open is checked against its scope."""
    root, effects = _synthetic_effects(tmp_path)
    (root / "tools/writer_ok.py").write_text(
        "from pathlib import Path\n"
        "ROOT = Path(__file__).resolve().parents[1]\n"
        "def run(root: Path):\n"
        "    (root / 'generated/reports/demo.txt').write_text('x', encoding='utf-8')\n"
        "def leak(kw):\n"
        "    open(ROOT / 'knowledge/notes/leak.md', **kw)\n",
        encoding="utf-8",
    )
    findings = check_declared_write_sites(root, effects)
    assert any("knowledge/notes/leak.md" in f and "outside declared destinations" in f
               for f in findings), findings


@pytest.mark.parametrize("probe_id, code", [
    ("urlretrieve", "import urllib.request\ndef f(u, p):\n    urllib.request.urlretrieve(u, p)\n"),
    ("urlretrieve-from", "from urllib.request import urlretrieve\ndef f(u, p):\n    urlretrieve(u, p)\n"),
    ("fileio", "import io\ndef f(p):\n    io.FileIO(p, 'w')\n"),
    ("fileinput", "import fileinput\ndef f(p):\n    fileinput.input(p, inplace=True)\n"),
    ("fileinput-class", "import fileinput\ndef f(p):\n    fileinput.FileInput(p)\n"),
    ("pty", "import pty\ndef f():\n    pty.spawn('sh')\n"),
    ("copystat", "import shutil\ndef f(a, b):\n    shutil.copystat(a, b)\n"),
    ("copymode", "import shutil\ndef f(a, b):\n    shutil.copymode(a, b)\n"),
    ("chown", "import shutil\ndef f(p):\n    shutil.chown(p, 'x')\n"),
    ("setxattr", "import os\ndef f(p):\n    os.setxattr(p, 'user.x', b'1')\n"),
    ("removexattr", "import os\ndef f(p):\n    os.removexattr(p, 'user.x')\n"),
    ("chflags", "import os\ndef f(p):\n    os.chflags(p, 0)\n"),
    ("lchflags", "import os\ndef f(p):\n    os.lchflags(p, 0)\n"),
])
def test_reentry_primitives_outside_the_inventory_are_refused(tmp_path, probe_id, code):
    """N-5: the enumerated inventory is closed; these REVIEW-V3 primitives are refused."""
    failures = _probe_failures(tmp_path, {"tools/zz_n5.py": code})
    assert any("tools/zz_n5.py" in f and "outside the supported write-primitive inventory" in f
               for f in failures), (probe_id, failures)


def test_reentry_annotation_only_use_is_not_refused(tmp_path):
    failures = _probe_failures(tmp_path, {
        "tools/zz_annot.py": (
            "import io\nfrom learning_os.store.transactions import TransactionService\n"
            "def f(h: io.FileIO, s: 'TransactionService') -> None:\n    return None\n"),
    })
    assert not any("tools/zz_annot.py" in f for f in failures), failures


@pytest.mark.parametrize("probe_id, code", [
    ("service", "from learning_os.store.transactions import TransactionService\n"
                "def f(root):\n    return TransactionService(root)\n"),
    ("context", "from learning_os.store.contracts.gateway import GatewayRequestContext\n"
                "def f():\n    return GatewayRequestContext(channel='ui')\n"),
    ("installer", "from learning_os.store.contracts.gateway import gateway_request_context\n"
                  "def f(c):\n    return gateway_request_context(c)\n"),
    ("getattr", "import learning_os.store.transactions as t\n"
                "def f(root):\n    return getattr(t, 'TransactionService')(root)\n"),
])
def test_reentry_admission_names_only_at_recorded_sites(tmp_path, probe_id, code):
    """N-7: construction sites are finite; provenance and lifecycle stay with 2B."""
    failures = _probe_failures(tmp_path, {"tools/zz_n7.py": code})
    assert any("tools/zz_n7.py" in f and "recorded construction sites" in f
               for f in failures), (probe_id, failures)


@pytest.mark.parametrize("probe_id, code", [
    ("w01-migration", "from migrations.curriculum_v2 import run\ndef f(root):\n    run(root, apply=True)\n"),
    ("w02-summarize", "import material_summarize\ndef f():\n    material_summarize.main(['--promote'])\n"),
    ("w03-reconcile", "import library_reconciliation\ndef f():\n    library_reconciliation.main(['--apply'])\n"),
    ("bump-in-process", "from learning_os.store.contracts.data_contract import bump\n"
                        "def f(root):\n    bump(root, note='x')\n"),
])
def test_reentry_recorded_exceptions_run_only_from_their_entry_points(tmp_path, probe_id, code):
    """N-6: REVIEW-V3 probes w01–w03 now fail closed, as does an in-process bump."""
    failures = _probe_failures(tmp_path, {"tools/zz_n6.py": code})
    assert any("tools/zz_n6.py" in f and "(Bar 4 v3 N-6)" in f for f in failures), (probe_id, failures)


def test_reentry_every_recorded_exception_has_entry_point_references():
    """N-6: each recorded exception names its documented entry point."""
    for rel in _RECORDED_CANONICAL_EXCEPTIONS:
        identity = _module_identity(rel)
        keys = [key for key in _ENTRY_POINT_REFERENCES
                if key == identity or key.startswith(identity + ".")]
        assert keys, f"{rel} has no _ENTRY_POINT_REFERENCES row"
        assert all(rel in _ENTRY_POINT_REFERENCES[key] for key in keys), (rel, keys)


def test_reentry_extensionless_python_scripts_are_outside_the_inventory(tmp_path):
    """N-11: a Python shebang without .py is refused; other scripts are not."""
    root, effects = _synthetic_effects(tmp_path)
    (root / "tools/zz_shebang").write_text("#!/usr/bin/env python3\nprint('x')\n", encoding="utf-8")
    (root / "tools/zz_shell").write_text("#!/bin/sh\necho x\n", encoding="utf-8")
    failures = scan_tools_census(root, effects, [], tree_roots=_load_tree_roots())
    assert any("tools/zz_shebang" in f and "(Bar 4 v3 N-11)" in f for f in failures), failures
    assert not any("tools/zz_shell" in f for f in failures), failures


@pytest.mark.parametrize("raw, owned, ok", [
    ({}, True, False),
    ({}, False, True),
    ({"witness": "runtime"}, True, True),
    ({"witness": "deferred: 2B: witness the schema regeneration"}, True, True),
    ({"witness": "deferred: 2Z: nowhere"}, True, False),
    ({"witness": "deferred: 2B: "}, True, False),
    ({"witness": "helper"}, True, False),
    ({"witness": "maybe"}, False, False),
])
def test_reentry_every_owned_writer_needs_a_witness_disposition(raw, owned, ok):
    """§5.6: a writer reaching owned territory without a disposition fails."""
    failures = _witness_failures("tools/zz_writer.py", raw, owned)
    assert (failures == []) is ok, failures


def test_reentry_recorded_exceptions_run_from_registered_commands():
    """N-6: every recorded exception is a registered command or is driven by one."""
    import code_reachability

    commands = {f"tools/{rel}" for rel in code_reachability.ENTRYPOINTS}
    for rel in _RECORDED_CANONICAL_EXCEPTIONS:
        identity = _module_identity(rel)
        refs = set().union(*(sites for key, sites in _ENTRY_POINT_REFERENCES.items()
                             if key == identity or key.startswith(identity + ".")))
        assert rel in commands or refs & commands, (rel, sorted(refs))
    for sites in _ENTRY_POINT_REFERENCES.values():
        for site in sites:
            if not site.startswith("tools/learning_os/"):
                assert site in commands, f"{site} is not a registered entry point"
