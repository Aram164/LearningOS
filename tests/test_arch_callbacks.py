"""Transaction-callback population and rendering purity (SPEC §3.5 A18).

(a) The population ratchet counts, over ``tools/learning_os/**/*.py``
and ``tools/*.py``, every hook a transaction call passes, except in
the engine and the central wiring. (b) Every rendering callback a
registered operation passes is statically pure, and the fixtures
prove each impurity class fails at runtime through a test-only
registered operation.
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
from collections import Counter
from pathlib import Path

import arch_audit_hook
import pytest
import yaml
from scenario_harness import render_violations

import learning_os.ops.handlers  # noqa: F401  (registration side effect)
from learning_os.ops.registry import REGISTRY

ROOT = Path(__file__).resolve().parent.parent
LEARNING_OS_DIR = ROOT / "tools/learning_os"
TOOLS_DIR = ROOT / "tools"
HANDLERS_DIR = LEARNING_OS_DIR / "ops/handlers"
CALLBACKS_DIR = ROOT / "tests/fixtures/archcheck/callbacks"
RATCHETS_PATH = ROOT / "tests/architecture/ratchets.yaml"

CHECK_ID = "A18-callbacks"
FIX = ("Express the step as a declared gate or a pure renderer; callbacks "
       "must not grow or touch the world (PLAN A18).")


# --- (a) the population scan -----------------------------------------------------

#: Callee last-names the scan counts hooks for (SPEC §3.5a).
_SCAN_CALLEES = frozenset({
    "_write_transaction", "commit_proposal", "TransactionProposal", "commit",
})

#: Hook keywords counted on those calls (SPEC §3.5a).
_HOOKS = frozenset({
    "transaction_writes", "validate_extra", "validate_state", "publish",
    "rollback_publish", "touched", "translate",
})

#: Whole files the scan skips: the engine (SPEC §3.5a).
_EXCLUDED_FILES = frozenset({
    "tools/learning_os/transactions.py",
})

#: (file, function) the scan skips: the central wiring (SPEC §3.5a).
_EXCLUDED_FUNCS = frozenset({
    ("tools/learning_os/ops/commit.py", "commit_proposal"),
})


def _is_none_or_standard(value: ast.AST) -> bool:
    return (isinstance(value, ast.Constant)
            and (value.value is None or value.value == "STANDARD"))


def _scan_source(rel: str, text: str, *,
                 excluded_files: frozenset[str] = _EXCLUDED_FILES,
                 excluded_funcs: frozenset[tuple[str, str]] = _EXCLUDED_FUNCS
                 ) -> tuple[Counter, dict[str, int]]:
    """``(counts, first_seen)`` of hook signatures in one file.

    Each call whose callee's last name is scanned counts once per
    hook keyword it passes with a value other than ``None`` or
    ``"STANDARD"``; ``Result`` calls count for ``after_commit`` too.
    ``<capability>::<hook>`` when ``capability=`` is a string
    constant, else ``<path>::<function>::<hook>`` with the innermost
    enclosing function (as A4).
    """
    tree = ast.parse(text)
    counts: Counter = Counter()
    first_seen: dict[str, int] = {}

    def record(hook: str, capability: ast.AST | None,
               funcs: list[str], lineno: int) -> None:
        if isinstance(capability, ast.Constant) and isinstance(
                capability.value, str):
            signature = f"{capability.value}::{hook}"
        else:
            assert funcs, (
                f"A18 {rel}:{lineno}: a counted call outside any function"
                f" — {FIX}")
            signature = f"{rel}::{funcs[-1]}::{hook}"
        counts[signature] += 1
        first_seen.setdefault(signature, lineno)

    def excluded(funcs: list[str]) -> bool:
        if rel in excluded_files:
            return True
        return any((rel, name) in excluded_funcs for name in funcs)

    def visit(node: ast.AST, funcs: list[str]) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs = [*funcs, node.name]
        if isinstance(node, ast.Call):
            func = node.func
            last = func.id if isinstance(func, ast.Name) else (
                func.attr if isinstance(func, ast.Attribute) else None)
            if last in _SCAN_CALLEES or last == "Result":
                if not excluded(funcs):
                    capability = next(
                        (kw.value for kw in node.keywords
                         if kw.arg == "capability"), None)
                    for kw in node.keywords:
                        if kw.arg in _HOOKS or (
                                last == "Result"
                                and kw.arg == "after_commit"):
                            if not _is_none_or_standard(kw.value):
                                record(kw.arg, capability, funcs,
                                       node.lineno)
        for child in ast.iter_child_nodes(node):
            visit(child, funcs)

    visit(tree, [])
    return counts, first_seen


def _scan_tree() -> tuple[Counter, dict[str, int]]:
    """The measured (a) population over the prescribed scope."""
    counts: Counter = Counter()
    first_seen: dict[str, int] = {}
    paths = sorted(LEARNING_OS_DIR.rglob("*.py")) + sorted(
        TOOLS_DIR.glob("*.py"))
    assert paths, f"A18 no files in scope — {FIX}"
    for path in paths:
        rel = path.relative_to(ROOT).as_posix()
        file_counts, file_seen = _scan_source(
            rel, path.read_text(encoding="utf-8"))
        counts.update(file_counts)
        for signature, lineno in file_seen.items():
            first_seen.setdefault(signature, lineno)
    return counts, first_seen


def _recorded_counts() -> dict[str, int]:
    data = yaml.safe_load(RATCHETS_PATH.read_text(encoding="utf-8"))
    return {entry["signature"]: entry["count"]
            for entry in data["checks"].get(CHECK_ID, [])}


def test_population_matches_the_baseline():
    current, first_seen = _scan_tree()
    recorded = _recorded_counts()
    assert dict(current) == recorded, (
        "A18 population drift: "
        f"new={sorted(set(current) - set(recorded))} "
        f"fixed={sorted(set(recorded) - set(current))} "
        f"recounted={sorted(sig for sig in set(current) & set(recorded) if current[sig] != recorded[sig])} "
        f"(first seen: {first_seen}) — {FIX}")


def test_exclusions_are_the_spec_pair():
    assert _EXCLUDED_FILES == {"tools/learning_os/transactions.py"}
    assert _EXCLUDED_FUNCS == {
        ("tools/learning_os/ops/commit.py", "commit_proposal")}


def test_pos_hook_fixture_is_counted():
    path = CALLBACKS_DIR / "pos_hook_validate_extra.py"
    counts, _ = _scan_source(
        path.relative_to(ROOT).as_posix(),
        path.read_text(encoding="utf-8"))
    assert dict(counts) == {"fixture.pos-hook::validate_extra": 1}, (
        f"A18 the hook fixture counts {dict(counts)} — {FIX}")


def test_neg_central_wiring_fixture_is_not_counted():
    path = CALLBACKS_DIR / "neg_central_wiring.py"
    rel = path.relative_to(ROOT).as_posix()
    text = path.read_text(encoding="utf-8")
    counts, _ = _scan_source(
        rel, text, excluded_funcs=frozenset({(rel, "commit_proposal")}))
    assert dict(counts) == {}, f"A18 the wiring fixture counts {dict(counts)}"
    unexcluded, _ = _scan_source(rel, text, excluded_funcs=frozenset())
    assert dict(unexcluded) == {"fixture.wiring::validate_extra": 1}, (
        "A18 the wiring call would not count unexcluded — " + FIX)


# --- (b) discovery: the callbacks each registered operation passes -----------------

#: Rendering-callback keywords on ``Result`` (SPEC §3.5b, (bd)).
_RENDER_RESULT_KW = frozenset({"finish", "on_commit_refused", "refused_stdout"})

#: Rendering-callback keywords on ``register`` (SPEC §3.5b).
_RENDER_REGISTER_KW = frozenset({"human", "render_check"})


def _serving_modules() -> dict[str, set[str]]:
    """Handler file -> registered operations it serves.

    From REGISTRY's handler modules, plus ``_shared.py``, which serves
    its importers' operations.
    """
    serving: dict[str, set[str]] = {}
    for operation, entry in REGISTRY.items():
        module = entry.handler.__module__
        assert module.startswith("learning_os.ops.handlers."), module
        serving.setdefault(module.rsplit(".", 1)[1] + ".py",
                           set()).add(operation)
    importers: set[str] = set()
    for path in HANDLERS_DIR.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (isinstance(node, ast.ImportFrom)
                    and node.module == "learning_os.ops.handlers._shared"):
                importers.add(path.name)
    shared_ops: set[str] = set()
    for name in importers:
        shared_ops |= serving.get(name, set())
    assert shared_ops, "A18 _shared.py serves no registered operation"
    serving["_shared.py"] = shared_ops
    return serving


def _module_funcs(tree: ast.Module) -> dict[str, list]:
    """Every ``def`` in the module by name, nested or module-level."""
    funcs: dict[str, list] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs.setdefault(node.name, []).append(node)
    return funcs


def _resolve_callback(funcs: dict[str, list], rel: str,
                      kind: str, value: ast.AST, lineno: int):
    """A callback value to its node: unique def, lambda, or None."""
    if isinstance(value, ast.Constant) and value.value is None:
        return None
    if isinstance(value, ast.Lambda):
        return value
    if isinstance(value, ast.Name):
        matches = funcs.get(value.id, [])
        assert len(matches) == 1, (
            f"A18 {rel}:{lineno}: {value.id} resolves to "
            f"{len(matches)} defs — {FIX}")
        return matches[0]
    raise AssertionError(
        f"A18 {rel}:{lineno}: cannot resolve {kind} "
        f"{ast.dump(value)[:60]} — {FIX}")


def _renderers() -> list[tuple[str, str, str, str, ast.AST, dict]]:
    """``(operation, kind, name, rel, node, funcs)`` per callback passed.

    ``kind`` is the ``Result``/``register`` keyword. A ``Name`` value
    resolves to its unique same-module ``def``; a ``Lambda`` to its
    body; ``None`` passes nothing; anything else fails loud.
    """
    found = []
    for name, operations in sorted(_serving_modules().items()):
        path = HANDLERS_DIR / name
        rel = path.relative_to(ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        funcs = _module_funcs(tree)

        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call)
                    and ((isinstance(node.func, ast.Name)
                          and node.func.id == "register")
                         or (isinstance(node.func, ast.Name)
                             and node.func.id == "Result")
                         or (isinstance(node.func, ast.Attribute)
                             and node.func.attr == "Result"))):
                continue
            is_register = (isinstance(node.func, ast.Name)
                           and node.func.id == "register")
            keywords = (_RENDER_REGISTER_KW if is_register
                        else _RENDER_RESULT_KW)
            call_operations = sorted(operations)
            if is_register:
                assert (node.args and isinstance(node.args[0], ast.Constant)
                        and isinstance(node.args[0].value, str)), (
                    f"A18 {rel}:{node.lineno}: register without a literal"
                    f" operation — {FIX}")
                assert node.args[0].value in operations, (
                    f"A18 {rel}:{node.lineno}: register for "
                    f"{node.args[0].value} serves {sorted(operations)} — {FIX}")
                call_operations = [node.args[0].value]
            for kw in node.keywords:
                if kw.arg not in keywords:
                    continue
                resolved = _resolve_callback(
                    funcs, rel, kw.arg, kw.value, node.lineno)
                if resolved is None:
                    continue
                display = (kw.value.id if isinstance(kw.value, ast.Name)
                           else "<lambda>")
                for operation in call_operations:
                    found.append((operation, kw.arg, display, rel, resolved,
                                  funcs))
    return found


# --- (b) the static flagger ------------------------------------------------------------------

#: Bare-name calls the flagger reports (SPEC §3.5b item 5).
_BARE_CALLS = frozenset({
    "load_repo", "canonical_fingerprint", "_operator_lock",
    "TransactionService", "commit_proposal", "_write_transaction", "open",
})

#: Module-attribute calls the flagger reports (SPEC §3.5b item 5).
_MOD_CALLS = frozenset({"subprocess", "socket", "observations"})

#: Datetime calls the flagger reports (SPEC §3.5b item 5).
_DATETIME_CALLS = frozenset({
    ("datetime", "now"), ("datetime", "today"),
    ("date", "today"), ("time", "time"),
})

#: ``os.path`` calls the flagger reports (SPEC §3.5b item 5).
_OSPATH_CALLS = frozenset(
    {"exists", "isfile", "isdir", "getmtime", "getsize"})

#: ``Path`` method calls the flagger reports, by name (SPEC §3.5b item 5).
_PATH_METHODS = frozenset({
    "read_text", "read_bytes", "write_text", "write_bytes", "open",
    "exists", "is_file", "is_dir", "stat", "iterdir", "glob", "rglob",
    "unlink", "mkdir", "touch", "resolve",
})


def _scope_bound(root: ast.AST) -> set[str]:
    """Names bound anywhere under the root, nested scopes included.

    Over-approximating (a nested scope's locals also bind) prefers no
    false positive: the static part is supplementary and the runtime
    harness still guards what it cannot see.
    """
    bound: set[str] = set()
    for node in ast.walk(root):
        if isinstance(node, ast.arg):
            bound.add(node.arg)
        elif isinstance(node, ast.Name) and isinstance(
                node.ctx, ast.Store):
            bound.add(node.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                               ast.ClassDef)):
            bound.add(node.name)
        elif isinstance(node, ast.alias):
            bound.add(node.asname or node.name.split(".")[0])
        elif isinstance(node, ast.ExceptHandler) and node.name:
            bound.add(node.name)
    return bound


def _call_violation(func: ast.AST) -> str | None:
    """The violation for a call's callee, else None (SPEC §3.5b item 5)."""
    if isinstance(func, ast.Name):
        return f"call {func.id}" if func.id in _BARE_CALLS else None
    if not isinstance(func, ast.Attribute):
        return None
    value = func.value
    if isinstance(value, ast.Name) and value.id in _MOD_CALLS:
        return f"call {value.id}.{func.attr}"
    if isinstance(value, ast.Name) and (value.id, func.attr) in _DATETIME_CALLS:
        return f"call {value.id}.{func.attr}"
    if (isinstance(value, ast.Attribute) and value.attr == "path"
            and isinstance(value.value, ast.Name)
            and value.value.id == "os"
            and func.attr in _OSPATH_CALLS):
        return f"call os.path.{func.attr}"
    if func.attr in _PATH_METHODS:
        return f"call .{func.attr}"
    return None


def _flags_for(funcs: dict[str, list], root: ast.AST) -> list[tuple[int, str]]:
    """``(lineno, violation)`` in the body and its name-called callees.

    Same-module callees resolve by name to their unique ``def``;
    depth 0 is the body itself and depth ≤ 3 is checked.
    """
    flags: list[tuple[int, str]] = []
    seen: dict[str, int] = {}

    def check(node: ast.AST, remaining: int) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.Lambda)):
            bound = _scope_bound(node)
            for child in ast.walk(node):
                if (isinstance(child, ast.Name)
                        and isinstance(child.ctx, ast.Load)
                        and child.id in ("ctx", "repo")
                        and child.id not in bound):
                    flags.append((child.lineno, f"free {child.id}"))
        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue
            violation = _call_violation(child.func)
            if violation is not None:
                flags.append((child.lineno, violation))
            if (remaining > 0 and isinstance(child.func, ast.Name)
                    and child.func.id in funcs):
                matches = funcs[child.func.id]
                assert len(matches) == 1, (
                    f"A18 {child.func.id} resolves to {len(matches)} defs"
                    f" — {FIX}")
                name = child.func.id
                if seen.get(name, -1) < remaining - 1:
                    seen[name] = remaining - 1
                    check(matches[0], remaining - 1)

    if isinstance(root, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
        check(root, 3)
    else:  # pragma: no cover — resolution only yields defs and lambdas.
        raise AssertionError(f"A18 cannot check {type(root).__name__} — {FIX}")
    return sorted(set(flags))


def _renderer_params():
    return [((operation, kind, display),
             (rel, node, funcs))
            for operation, kind, display, rel, node, funcs in _renderers()]


@pytest.mark.parametrize(
    "key,location", _renderer_params(),
    ids=[f"{op}::{kind}:{name}" for (op, kind, name), _ in
         _renderer_params()])
def test_registered_renderer_is_statically_pure(key, location):
    operation, kind, _display = key
    _rel, node, funcs = location
    flags = _flags_for(funcs, node)
    assert flags == [], (
        f"A18 {operation}::{kind}: "
        f"{'; '.join(f'{line} {what}' for line, what in flags)} — {FIX}")


def test_discovery_covers_the_known_renderers():
    known = {
        ("ai-action.delivery.apply", "finish", "finish"),
        ("capture.create", "human", "_human_capture"),
        ("capture.create", "on_commit_refused", "_on_commit_refused"),
        ("stage.progress.update", "on_commit_refused", "_on_commit_refused"),
        ("route.patch", "render_check", "_render_plan_check"),
        ("route.patch", "finish", "finish"),
        ("route.patch", "refused_stdout", "refused_stdout"),
    }
    discovered = {(operation, kind, display)
                  for operation, kind, display, _, _, _ in _renderers()}
    assert known <= discovered, (
        f"A18 discovery lost {sorted(known - discovered)} — {FIX}")


# --- (b) fixture and resolution controls ----------------------------------------------

def _load_fixture_module(name: str):
    path = CALLBACKS_DIR / name
    assert path.is_file(), f"A18 missing fixture {name} — {FIX}"
    spec = importlib.util.spec_from_file_location(
        f"callback_fixture_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _fixture_flags(name: str) -> set[str]:
    path = CALLBACKS_DIR / name
    tree = ast.parse(path.read_text(encoding="utf-8"))
    funcs = _module_funcs(tree)
    matches = funcs.get("render", [])
    assert len(matches) == 1, f"A18 {name} has no unique render — {FIX}"
    return {violation for _, violation in _flags_for(funcs, matches[0])}


def test_fixture_flags_match_their_classes():
    assert _fixture_flags("pos_render_reads_file.py") == {"call open"}
    assert _fixture_flags("pos_render_observation.py") == {
        "call observations.now"}
    assert _fixture_flags("pos_render_captures_ctx.py") == {"free ctx"}
    # Runtime-only positives: neither the counter nor the assignment is
    # in the static flag list; call_renderer catches both live.
    assert _fixture_flags("pos_render_nondeterministic.py") == set()
    assert _fixture_flags("pos_render_mutates_arg.py") == set()
    assert _fixture_flags("neg_render_pure.py") == set()


def test_lambda_resolution_flags_its_body():
    tree = ast.parse("finish = lambda payload: open('x').read()\n")
    lambdas = [node for node in ast.walk(tree)
               if isinstance(node, ast.Lambda)]
    assert len(lambdas) == 1
    assert _flags_for({}, lambdas[0]) == [(1, "call open")], (
        f"A18 lambda flags {_flags_for({}, lambdas[0])} — {FIX}")


def _depth_chain_fixture() -> ast.Module:
    return ast.parse(
        "def root(payload):\n"
        "    return one(payload)\n"
        "def one(payload):\n"
        "    return two(payload)\n"
        "def two(payload):\n"
        "    return three(payload)\n"
        "def three(payload):\n"
        "    return four(payload)\n"
        "def four(payload):\n"
        "    return open('x').read()\n")


def test_depth_three_is_checked_and_depth_four_is_not():
    tree = _depth_chain_fixture()
    funcs = _module_funcs(tree)
    assert funcs["three"][0].lineno == 7
    assert [violation for _, violation in
            _flags_for(funcs, funcs["root"][0])] == [], (
        "A18 depth 4 must stay unchecked — " + FIX)
    assert [violation for _, violation in
            _flags_for(funcs, funcs["one"][0])] == ["call open"], (
        "A18 depth 3 must be checked — " + FIX)


def test_bound_ctx_and_repo_are_not_free():
    tree = ast.parse(
        "def render(payload, ctx):\n"
        "    repo = payload['repo']\n"
        "    return (ctx, repo)\n")
    funcs = _module_funcs(tree)
    assert _flags_for(funcs, funcs["render"][0]) == [], (
        "A18 bound names must not flag — " + FIX)


# --- (b) runtime: fixtures through a test-only operation --------------------------------

TEST_OP = "test-only.callbacks"


def _write_test_schema(root: Path) -> None:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "test-only/test-only.callbacks",
        "type": "object",
        "properties": {
            "alpha": {"type": "string", "default": "A"},
            "beta": {"type": "integer", "default": 3},
        },
    }
    path = root / "system" / "schema" / "requests" / f"{TEST_OP}.schema.json"
    path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")


@pytest.fixture
def apipe(mini_repo):
    """Register the test-only operation; restore the registry after."""

    _write_test_schema(mini_repo)

    def make(kind="query", handler=None, human=None, render_check=None):
        from learning_os.ops.proposal import Result

        def default_handler(ctx, req):
            return Result({"echo": req.get("alpha"), "n": req.get("beta")})

        from learning_os.ops.registry import register

        register(TEST_OP, kind=kind, human=human,
                 render_check=render_check)(handler or default_handler)

    yield make
    REGISTRY.pop(TEST_OP, None)


def _ns(root, *, json=False, alpha="hi", beta=7):
    return argparse.Namespace(
        root=str(root),
        _operation=TEST_OP,
        json=json,
        alpha=alpha,
        beta=beta,
        extra="dropped",
    )


def _load_fixture_renderer(name: str):
    return _load_fixture_module(name).render


def _run_finish_with_audit(mini_repo, tmp_path, render):
    """Run ``finish=render`` through run_cli under the installed hook."""
    from learning_os.ops import pipeline as pipeline_module
    from learning_os.ops.proposal import Result

    _write_test_schema(mini_repo)
    log = tmp_path / "audit.jsonl"

    def handler(ctx, req):
        return Result({"echo": "x"}, finish=render)

    from learning_os.ops.registry import register

    register(TEST_OP, kind="query")(handler)
    try:
        arch_audit_hook.install(str(log))
        try:
            outcome = pipeline_module.run_cli(
                mini_repo, TEST_OP, _ns(mini_repo))
        finally:
            arch_audit_hook.uninstall()
    finally:
        REGISTRY.pop(TEST_OP, None)
    arch_audit_hook.assert_capture_ok()
    return outcome, render_violations(arch_audit_hook.read_log(log))


def test_registry_has_no_leaked_callbacks_operation():
    assert TEST_OP not in REGISTRY


def test_runtime_file_read_fails(mini_repo, tmp_path, monkeypatch):
    """The file-read fixture is audited live, not only flagged."""
    from learning_os.ops.render import current_render

    monkeypatch.setenv("LOS_ARCH_RENDER_CHECK", "1")
    outcome, violations = _run_finish_with_audit(
        mini_repo, tmp_path,
        _load_fixture_renderer("pos_render_reads_file.py"))
    assert outcome.exit_code == 0
    assert any("::open" in problem for problem in violations), violations
    assert current_render() is None


def test_runtime_observation_fails(mini_repo, tmp_path, monkeypatch):
    """The observation fixture is audited live, not only flagged."""
    from learning_os.ops.render import current_render

    monkeypatch.setenv("LOS_ARCH_RENDER_CHECK", "1")
    outcome, violations = _run_finish_with_audit(
        mini_repo, tmp_path,
        _load_fixture_renderer("pos_render_observation.py"))
    assert outcome.exit_code == 0
    assert any("learningos.observation" in problem
               for problem in violations), violations
    assert current_render() is None


def test_runtime_captured_context_fails(mini_repo, tmp_path, monkeypatch):
    """The captured-context fixture loads the repo live, audited."""
    from learning_os.ops.context import OpContext
    from learning_os.ops.render import current_render

    module = _load_fixture_module("pos_render_captures_ctx.py")
    module.ctx = OpContext(root=mini_repo, operation=TEST_OP,
                           channel="operator", invocation="query",
                           gateway=None)
    monkeypatch.setenv("LOS_ARCH_RENDER_CHECK", "1")
    outcome, violations = _run_finish_with_audit(
        mini_repo, tmp_path, module.render)
    assert outcome.exit_code == 0
    assert any("::open" in problem for problem in violations), violations
    assert current_render() is None


def test_runtime_nondeterminism_fails(apipe, mini_repo, monkeypatch):
    """The nondeterminism fixture raises through the real run_cli path."""
    from learning_os.ops import pipeline as pipeline_module
    from learning_os.ops.proposal import Result
    from learning_os.ops.render import RenderPurityError, current_render

    render = _load_fixture_renderer("pos_render_nondeterministic.py")

    def handler(ctx, req):
        return Result({"echo": "x"}, finish=render)

    apipe("query", handler=handler)
    monkeypatch.setenv("LOS_ARCH_RENDER_CHECK", "1")
    with pytest.raises(RenderPurityError) as caught:
        pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo))
    assert str(caught.value) == f"{TEST_OP}::finish::not-deterministic"
    assert current_render() is None


def test_runtime_mutation_fails(apipe, mini_repo, monkeypatch):
    """The mutation fixture raises through the real run_cli path."""
    from learning_os.ops import pipeline as pipeline_module
    from learning_os.ops.proposal import Result
    from learning_os.ops.render import RenderPurityError, current_render

    render = _load_fixture_renderer("pos_render_mutates_arg.py")

    def handler(ctx, req):
        return Result({"echo": "x"}, finish=render)

    apipe("query", handler=handler)
    monkeypatch.setenv("LOS_ARCH_RENDER_CHECK", "1")
    with pytest.raises(RenderPurityError) as caught:
        pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo))
    assert str(caught.value) == f"{TEST_OP}::finish::argument-mutated"
    assert current_render() is None


def test_runtime_nested_false_to_zero_fails(apipe, mini_repo, monkeypatch):
    """A nested False→0 mutation fails through the human path (SPEC (az))."""
    from learning_os.ops import pipeline as pipeline_module
    from learning_os.ops.proposal import Result
    from learning_os.ops.render import RenderPurityError, current_render

    def nested_mutator(payload):
        payload["nested"]["flag"] = 0
        return payload

    def handler(ctx, req):
        return Result({"nested": {"flag": False}})

    apipe("query", handler=handler, human=nested_mutator)
    monkeypatch.setenv("LOS_ARCH_RENDER_CHECK", "1")
    with pytest.raises(RenderPurityError) as caught:
        pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo))
    assert str(caught.value) == f"{TEST_OP}::human::argument-mutated"
    assert current_render() is None


def test_runtime_pure_fixture_passes_clean(mini_repo, tmp_path, monkeypatch):
    """The pure fixture runs with no violation and no purity error."""
    from learning_os.ops.render import current_render

    monkeypatch.setenv("LOS_ARCH_RENDER_CHECK", "1")
    outcome, violations = _run_finish_with_audit(
        mini_repo, tmp_path, _load_fixture_renderer("neg_render_pure.py"))
    assert outcome.exit_code == 0
    assert violations == []
    assert current_render() is None
