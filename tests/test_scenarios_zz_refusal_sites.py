"""Every declared refusal site is witnessed from its case (SPEC §3.3 A9).

``ops/pipeline.py`` emits one ``learningos.refusal`` audit event per
refusal it produces, and the audit hook appends one item 8.1 JSON
line per event while ``LOS_SITE_WITNESS_FILE`` is set (SPEC (bf)
item 10; a session fixture owns that file). This module runs after
every other ``test_scenarios*`` file, so in a full or ``-k
scenarios`` run it matches each statically declared site to both a
runtime witness line with a non-null site and a case whose
``expect.site`` equals it, and requires that line to come from that
case's own run (amendment (bh): ``scenario_harness`` attributes each
case run's lines to the case). An empty witness file skips locally and
fails under CI.
"""

from __future__ import annotations

import ast
import json
import os
import sys
from functools import lru_cache
from functools import partial as _phase4_partial
from pathlib import Path

import pytest
from arch_audit_hook import SITE_WITNESS_ENV

import learning_os.app.handlers  # noqa: F401  (registration side effect)
from learning_os.app.registry import REGISTRY

ROOT = Path(__file__).resolve().parent.parent
CASES_DIR = ROOT / "tests/scenarios/cases"
HANDLERS_DIR = ROOT / "tools/learning_os/app/handlers"

CHECK_ID = "A9-refusal-sites"
FIX = "Add a scenario that triggers this site and asserts its effects."


# --- static collection ----------------------------------------------------------

def _serving_ops() -> dict[str, set[str]]:
    """Handler file -> registered operations it serves.

    From REGISTRY's handler modules, plus ``_shared.py``, which serves
    its importers' operations.
    """
    serving: dict[str, set[str]] = {}
    for operation, entry in REGISTRY.items():
        module = entry.handler.__module__
        assert module.startswith("learning_os.app.handlers."), module
        serving.setdefault(module.rsplit(".", 1)[1] + ".py",
                           set()).add(operation)
    importers: set[str] = set()
    for path in HANDLERS_DIR.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (isinstance(node, ast.ImportFrom)
                    and node.module == "learning_os.app.handlers._shared"):
                importers.add(path.name)
    shared_ops: set[str] = set()
    for name in importers:
        shared_ops |= serving.get(name, set())
    assert shared_ops, "A9 _shared.py serves no registered operation"
    serving["_shared.py"] = shared_ops
    return serving


def _operation_templates(value: ast.AST) -> list[str]:
    """Slug suffixes of ``f"{<op>}.<slug>"`` / ``f"{<op>.operation}.<slug>"``.

    Found anywhere under ``value`` (a site kwarg, an ``exc.site``
    assignment, or a ``site`` variable's value). Anything else is not
    a template.
    """
    slugs = []
    for node in ast.walk(value):
        if not isinstance(node, ast.JoinedStr) or len(node.values) != 2:
            continue
        formatted, rest = node.values
        if (not isinstance(formatted, ast.FormattedValue)
                or formatted.conversion != -1
                or formatted.format_spec is not None):
            continue
        target = formatted.value
        is_operation = (
            isinstance(target, ast.Name)
            or (isinstance(target, ast.Attribute)
                and target.attr == "operation"
                and isinstance(target.value, ast.Name)))
        if not is_operation:
            continue
        if not (isinstance(rest, ast.Constant)
                and isinstance(rest.value, str)
                and rest.value.startswith(".")
                and rest.value[1:] and "." not in rest.value[1:]):
            continue
        slugs.append(rest.value[1:])
    return slugs


@lru_cache(maxsize=1)
def _entry_point_ops() -> frozenset[str]:
    """Registered operations with a runtime entry point (item 9.1).

    An operation that is the ``_operation`` default of a generated
    CLI subcommand, or a catalog command the gateway dispatches.
    """
    import los
    from learning_os.store.contracts.capability_catalog import command_definitions
    from learning_os.store.contracts.payloads import subparsers

    defaults = {sub.get_default("_operation")
                for sub in subparsers(los.build_parser()).values()}
    defaults.discard(None)
    return frozenset(
        (defaults | set(command_definitions(ROOT))) & set(REGISTRY))


def _excluded_ops() -> set[str]:
    """Registered names with no runtime entry point (item 9.1)."""
    return set(REGISTRY) - set(_entry_point_ops())


def _assert_shares_entry_point_handler(operation: str,
                                       entry_points) -> None:
    """The excluded operation shares its handler with an entry point."""
    handler = REGISTRY[operation].handler
    shared = sorted(op for op in entry_points
                    if REGISTRY[op].handler is handler)
    assert shared, (
        f"A9 {operation}: excluded but shares its handler with no "
        f"entry-point operation — {FIX}")


#: Bound on the twin-call map cache: the handler tree holds about
#: twenty files, so 64 keeps every live entry while bounding growth.
_TWIN_CALLERS_CACHE_MAX = 64

#: Exact source text -> the ``(calls, shared)`` map it analyzes to
#: (SPEC (cm)). The analysis is pure over the text; the path is
#: still read on every call, so edited source selects a fresh
#: entry. Only this static map is cached — never REGISTRY, the
#: census, witnesses or proof state. Callers must not mutate the
#: returned maps.
_TWIN_CALLERS_CACHE: dict[
    str, tuple[dict[str, set[str]], dict[str, str]]] = {}


def _analyze_twin_source(source: str) -> tuple[dict[str, set[str]],
                                               dict[str, str]]:
    """Static calls per top-level function, plus ``_shared`` aliases.

    Returns ``(calls, shared)`` where ``calls[func]`` is every bare
    name ``func`` calls (nested functions included) and
    ``shared[local]`` is the ``_shared.py`` twin a
    ``from ... _shared import ...`` name binds. Pure over ``source``.
    """
    tree = ast.parse(source)
    shared: dict[str, str] = {}
    for node in ast.walk(tree):
        if (isinstance(node, ast.ImportFrom)
                and node.module is not None
                and node.module.endswith("handlers._shared")):
            for entry in node.names:
                shared[entry.asname or entry.name] = entry.name
    calls: dict[str, set[str]] = {}
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        names = set()
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call) \
                    and isinstance(sub.func, ast.Name):
                names.add(sub.func.id)
        calls[node.name] = names
    return calls, shared


def _twin_callers_cached(source: str) -> tuple[dict[str, set[str]],
                                               dict[str, str]]:
    """``_analyze_twin_source`` memoized by exact source text (cm)."""
    try:
        return _TWIN_CALLERS_CACHE[source]
    except KeyError:
        pass
    result = _analyze_twin_source(source)
    if len(_TWIN_CALLERS_CACHE) >= _TWIN_CALLERS_CACHE_MAX:
        _TWIN_CALLERS_CACHE.pop(next(iter(_TWIN_CALLERS_CACHE)))
    _TWIN_CALLERS_CACHE[source] = result
    return result


def _twin_callers(path: Path) -> tuple[dict[str, set[str]],
                                     dict[str, str]]:
    """Static calls per top-level function, plus ``_shared`` aliases.

    Reads the path on every call; the pure analysis over its text
    is memoized by exact source (SPEC (cm)), so edited source and
    monkeypatched fixture paths select fresh entries.
    """
    return _twin_callers_cached(path.read_text(encoding="utf-8"))


def _handler_calls_twin(operation: str, twin_module: str,
                        twin_func: str) -> bool:
    """Whether the operation's handler statically calls the twin (R-A9-1).

    True when the registered handler function is the twin itself (a
    template raised inline) or its body calls the twin's name, resolved
    through the handler module's ``_shared`` imports or its own
    top-level functions. Anything else is a never-called expansion and
    declares no site for the operation.
    """
    handler = REGISTRY[operation].handler
    module = handler.__module__
    assert module.startswith("learning_os.app.handlers."), module
    stem = module.rsplit(".", 1)[1]
    if (stem, handler.__name__) == (twin_module, twin_func):
        return True
    calls, shared = _twin_callers(HANDLERS_DIR / f"{stem}.py")
    for name in calls.get(handler.__name__, set()):
        if name in shared:
            if (twin_module, twin_func) == ("_shared", shared[name]):
                return True
            continue
        if twin_module == stem and name == twin_func:
            return True
    return False


def _resolve_failure(stem: str, name: object):
    """A failure class named in one handler file, else None (disposition 5).

    ``domain.failures`` first, then the already imported handler
    module's globals (registration imported it). The resolved object
    must be a class subclassing ``WriteRefused``: an imported
    non-failure, a non-class global, or an unknown name resolves to
    None and declares no site.
    """
    from learning_os.domain import failures

    if not isinstance(name, str):
        return None
    cls = getattr(failures, name, None)
    if isinstance(cls, type) and issubclass(cls, failures.WriteRefused):
        return cls
    module = sys.modules.get(f"learning_os.app.handlers.{stem}")
    cls = getattr(module, name, None) if module is not None else None
    if isinstance(cls, type) and issubclass(cls, failures.WriteRefused):
        return cls
    return None


def _narrowed_template_ops(entered: list[str], stem: str,
                           twin_func: str | None) -> list[str]:
    """Entered operations whose handler reaches the twin (R-A9-1).

    A template site in function ``twin_func`` counts for an operation
    only when that operation's handler statically calls the twin (or
    is it). Module-level templates (``twin_func`` None) keep the
    whole entered set.
    """
    if twin_func is None:
        return list(entered)
    return [operation for operation in entered
            if _handler_calls_twin(operation, stem, twin_func)]


def _except_handler_sites(node: ast.ExceptHandler, *, stem: str,
                          serving: set[str], entered: list[str],
                          rel: str, twin_func: str | None = None,
                          ) -> list[tuple[str, str, int]]:
    """``[(operation, site, lineno)]`` from one ``except`` site assignment.

    The caught name must resolve to a failure (domain or the
    handler's own globals); anything else assigns no site. A literal
    site names its served operation as written, exactly like a
    literal ``site=`` on a raise; a template resolves over the
    entered operations whose handler calls the twin (R-A9-1). Both
    need the bare re-raise (disposition 5).
    """
    if not (isinstance(node.type, ast.Name)
            and _resolve_failure(stem, node.type.id) is not None):
        return []
    found: list[tuple[str, str, int]] = []
    for stmt in ast.walk(node):
        if not isinstance(stmt, ast.Assign):
            continue
        for target in stmt.targets:
            if not (isinstance(target, ast.Attribute)
                    and target.attr == "site"
                    and isinstance(target.value, ast.Name)
                    and target.value.id == node.name):
                continue
            if isinstance(stmt.value, ast.Constant):
                site = stmt.value.value
                assert isinstance(site, str) and any(
                    site == op or site.startswith(op + ".")
                    for op in serving), (
                    f"A9 {rel}:{stmt.lineno}: site {site!r} names no"
                    f" served operation — {FIX}")
                assert any(isinstance(sub, ast.Raise)
                           and sub.exc is None
                           for sub in ast.walk(node)), (
                    f"A9 {rel}:{stmt.lineno}: the assigned site"
                    f" needs its bare re-raise — {FIX}")
                operation = next(
                    op for op in serving
                    if site == op or site.startswith(op + "."))
                found.append((operation, site, stmt.lineno))
                continue
            slugs = _operation_templates(stmt.value)
            assert slugs, (
                f"A9 {rel}:{stmt.lineno}: unresolvable site"
                f" form — {FIX}")
            assert any(isinstance(sub, ast.Raise)
                       and sub.exc is None
                       for sub in ast.walk(node)), (
                f"A9 {rel}:{stmt.lineno}: the assigned site"
                f" needs its bare re-raise — {FIX}")
            for operation in _narrowed_template_ops(entered, stem,
                                                    twin_func):
                for slug in slugs:
                    found.append((operation, f"{operation}.{slug}",
                                  stmt.lineno))
    return found


def _declared_sites() -> dict[tuple[str, str], str]:
    """``(operation, site)`` -> ``"rel:line"`` for every declared site.

    A literal ``site="..."`` or an operation template on a failure
    raise, the capture ``exc.site`` assignment beside its bare
    re-raise (literal or template), or an operation template assigned
    to a ``site`` variable passed as ``site=``. Failure names resolve
    in ``domain.failures`` or the handler module's own globals
    (disposition 5). Templates resolve over the raising module's
    serving operations that have a runtime entry point (item 9.1),
    narrowed to the operations whose handler statically calls the
    twin (R-A9-1); literals name their operation as written.
    """
    serving = _serving_ops()
    entry_points = set(_entry_point_ops())
    declared: dict[tuple[str, str], str] = {}

    def record(operation: str, site: str, rel: str, lineno: int) -> None:
        declared.setdefault((operation, site), f"{rel}:{lineno}")

    for path in sorted(HANDLERS_DIR.glob("*.py")):
        if path.name == "__init__.py":
            continue
        rel = path.relative_to(ROOT).as_posix()
        assert serving.get(path.name), f"A9 {rel} serves nothing — {FIX}"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        entered = sorted(set(serving[path.name]) & entry_points)
        for top in tree.body:
            twin_func = top.name if isinstance(top, ast.FunctionDef) else None
            for node in ast.walk(top):
                if isinstance(node, ast.Raise) \
                        and isinstance(node.exc, ast.Call):
                    call = node.exc
                    if not (isinstance(call.func, ast.Name)
                            and _resolve_failure(path.stem, call.func.id)
                            is not None):
                        continue
                    site_kw = next((kw for kw in call.keywords
                                    if kw.arg == "site"), None)
                    if site_kw is None:
                        continue
                    if isinstance(site_kw.value, ast.Constant):
                        site = site_kw.value.value
                        assert isinstance(site, str) and any(
                            site == op or site.startswith(op + ".")
                            for op in serving[path.name]), (
                            f"A9 {rel}:{node.lineno}: site {site!r} names no"
                            f" served operation — {FIX}")
                        operation = next(
                            op for op in serving[path.name]
                            if site == op or site.startswith(op + "."))
                        record(operation, site, rel, node.lineno)
                        continue
                    slugs = _operation_templates(site_kw.value)
                    assert slugs, (
                        f"A9 {rel}:{node.lineno}: unresolvable site form — "
                        f"{FIX}")
                    narrowed = _narrowed_template_ops(entered, path.stem,
                                                       twin_func)
                    for operation in narrowed:
                        for slug in slugs:
                            record(operation, f"{operation}.{slug}", rel,
                                   node.lineno)
                if isinstance(node, ast.ExceptHandler):
                    for operation, site, lineno in _except_handler_sites(
                            node, stem=path.stem,
                            serving=serving[path.name], entered=entered,
                            rel=rel, twin_func=twin_func):
                        record(operation, site, rel, lineno)
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            assigns = [stmt for stmt in ast.walk(node)
                       if isinstance(stmt, ast.Assign)
                       and any(isinstance(target, ast.Name)
                               and target.id == "site"
                               for target in stmt.targets)]
            if not assigns:
                continue
            uses = [call for call in ast.walk(node)
                    if isinstance(call, ast.Call)
                    and any(kw.arg == "site"
                            and isinstance(kw.value, ast.Name)
                            and kw.value.id == "site"
                            for kw in call.keywords)]
            if not uses:
                continue
            narrowed = _narrowed_template_ops(entered, path.stem,
                                              node.name)
            for stmt in assigns:
                for slug in _operation_templates(stmt.value):
                    for operation in narrowed:
                        record(operation, f"{operation}.{slug}", rel,
                               stmt.lineno)
    return declared


# --- the match ---------------------------------------------------------------------

def _is_refusal_line(record) -> bool:
    """An item 8.1 line: exact keys per kind, null-or-named site.

    The operation value is unrestricted: admission refusals carry
    the envelope's own capability, which a refused envelope may
    omit. Such lines always have a null site and are never read.
    """
    if not isinstance(record, dict):
        return False
    kind = record.get("kind")
    if kind == "failure":
        return (set(record) == {"operation", "kind", "site", "class",
                                "exit_code"}
                and (record["site"] is None
                     or (isinstance(record["site"], str)
                         and record["site"]))
                and isinstance(record["class"], str)
                and bool(record["class"])
                and (record["exit_code"] is None
                     or isinstance(record["exit_code"], int)))
    if kind in ("commit-refused", "direct-refused"):
        return (set(record) == {"operation", "kind", "site", "code"}
                and record["site"] is None
                and isinstance(record["code"], int))
    if kind == "diagnostic-failure":
        return (set(record) == {"operation", "kind", "site", "code"}
                and record["site"] is None
                and type(record["code"]) is int
                and record["code"] == 1)
    if kind == "command-failure":
        return (set(record) == {"operation", "kind", "site", "code"}
                and record["site"] is None
                and type(record["code"]) is int
                and record["code"] != 0)
    return False


def _session_witnesses() -> set[tuple[str, str]]:
    """The session's ``(operation, site)`` witnesses.

    Reads only lines with a non-null ``site`` (SPEC (bf) item 8.1);
    null-site lines (commit refusals, direct refusals, siteless
    raises, admission refusals) are not sites. An empty file means
    no scenario ran in
    this session: skip locally, fail when CI is set.
    """
    path = os.environ.get(SITE_WITNESS_ENV)
    assert path, f"A9 {SITE_WITNESS_ENV} is unset — {FIX}"
    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        text = ""
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        reason = (f"A9 no scenario ran in this session "
                  f"({SITE_WITNESS_ENV} is empty) — {FIX}")
        if os.environ.get("CI"):
            pytest.fail(f"CI requires scenario witnesses: {reason}")
        pytest.skip(reason)
    witnesses = set()
    for lineno, line in enumerate(lines, 1):
        try:
            record = json.loads(line)
        except ValueError as exc:
            raise AssertionError(
                f"A9 witness line {lineno} is not JSON — {FIX}") from exc
        assert _is_refusal_line(record), (
            f"A9 witness line {lineno} is not an item 8.1 refusal line "
            f"({line[:120]!r}) — {FIX}")
        if record["site"] is not None:
            witnesses.add((record["operation"], record["site"]))
    return witnesses


def _cased_sites() -> dict[str, str]:
    """Typed ``expect.site`` -> ``"file:case"`` over every case file."""
    import scenario_harness as harness

    cased = {}
    for path in sorted(CASES_DIR.glob("*.yaml")):
        doc = harness.load_case_file(path)
        for case in doc.get("cases", []):
            site = (case.get("expect") or {}).get("site")
            if site is not None:
                cased.setdefault(site, f"{path.stem}:{case['id']}")
    return cased


def _declaring_cases() -> dict[str, list[str]]:
    """Typed ``expect.site`` -> every ``"operation:case"`` declaring it (bh).

    Keys use the case file's ``operation``, the name the harness
    attributes a run to (``scenario_harness.CASE_SITE_WITNESSES``).
    """
    import scenario_harness as harness

    declaring: dict[str, list[str]] = {}
    for path in sorted(CASES_DIR.glob("*.yaml")):
        doc = harness.load_case_file(path)
        for case in doc.get("cases", []):
            site = (case.get("expect") or {}).get("site")
            if site is not None:
                declaring.setdefault(site, []).append(
                    f"{doc['operation']}:{case['id']}")
    return declaring


def _attributed_witnesses(site: str) -> set[tuple[str, str]]:
    """What the site's declaring cases witnessed in their own runs (bh).

    Only runs attributed to this session's witness file count, so a
    case run against a private file (a control) never stands in.
    """
    import scenario_harness as harness

    path = os.environ.get(SITE_WITNESS_ENV)
    attributed: set[tuple[str, str]] = set()
    for key in _declaring_cases().get(site, []):
        attributed |= harness.CASE_SITE_WITNESSES.get((path, key), set())
    return attributed


#: Untriggered reasons (SPEC (bf) item 9.3, fixed vocabulary, plus
#: R-A9-2's reviewed reason: no scenario fixture input reaches the
#: site, and the proof triggers it by direct injection instead).
_UNTRIGGERED_REASONS = frozenset({
    "guarded-before-handler", "os-error-only", "race-only",
    "fixture-inexpressible",
})

#: Sites whose untriggered proof passed in this session (item 9.3).
#: Proof tests run before the matching tests and record here.
_PROOFS: dict[str, bool] = {}


def _untriggered_entries() -> dict[str, dict]:
    """Site -> entry for site-carrying ``untriggered`` entries (item 9.3).

    Entries without a site are legacy documentation and A9 ignores
    them. A site entry must name its operation's file, a declared
    site, and a fixed-vocabulary reason.
    """
    import scenario_harness as harness

    declared_where = {site: where
                      for (_, site), where in _declared_sites().items()}
    entries: dict[str, dict] = {}
    for path in sorted(CASES_DIR.glob("*.yaml")):
        doc = harness.load_case_file(path)
        for entry in doc.get("untriggered") or []:
            site = entry.get("site")
            if site is None:
                continue
            label = f"{path.stem}:{site}"
            assert site not in entries, (
                f"A9 {label}: duplicate untriggered entry — {FIX}")
            assert site in declared_where, (
                f"A9 {label}: not a declared site — {FIX}")
            assert isinstance(site, str) and site.startswith(
                path.stem + "."), (
                f"A9 {label}: the entry lives in another operation's "
                f"file — {FIX}")
            assert "where" not in entry, (
                f"A9 {label}: a site-carrying untriggered entry is "
                f"identified by its site id; remove where — {FIX}")
            assert entry.get("reason") in _UNTRIGGERED_REASONS, (
                f"A9 {label}: reason {entry.get('reason')!r} is outside "
                f"{sorted(_UNTRIGGERED_REASONS)} — {FIX}")
            entries[site] = entry
    return entries


def _proof_accepts(site: str, entries: dict[str, dict],
                   proofs: dict[str, bool]) -> bool:
    """Whether the site's untriggered proof passed (item 9.3)."""
    return entries.get(site) is not None and proofs.get(site) is True


def _assert_matched(operation: str, site: str, where: str,
                    witnesses: set[tuple[str, str]],
                    cased: dict[str, str], *,
                    entries: dict[str, dict] | None = None,
                    proofs: dict[str, bool] | None = None,
                    attributed: set[tuple[str, str]] | None = None) -> None:
    """The declared site has its witness and its case, or its proof.

    The witness must come from the run of a case whose ``expect.site``
    names the site (SPEC §3.3 A9, amendment (bh)): ``attributed`` holds
    what the declaring cases witnessed in their own runs. An uncased
    site is accepted only through an untriggered entry whose proof
    passed in this session (item 9.3); the proof stands in for the
    session witness, the case and the attribution.
    """
    if entries is None:
        entries = _untriggered_entries()
    if proofs is None:
        proofs = _PROOFS
    if attributed is None:
        attributed = _attributed_witnesses(site)
    if _proof_accepts(site, entries, proofs):
        return
    problems = []
    if (operation, site) not in witnesses:
        others = sorted({op for op, st in witnesses if st == site})
        detail = (f" (witnessed only as {others})" if others
                  else " (no witness at all)")
        problems.append(f"unwitnessed{detail}")
    elif site in cased and (operation, site) not in attributed:
        problems.append("witnessed, but not by the run of a case whose "
                        "expect.site names it")
    if site not in cased and not _proof_accepts(site, entries, proofs):
        problems.append("no case carries this expect.site "
                        "(and no untriggered proof passed)")
    assert not problems, (
        f"A9 {operation}::{site} [{where}]: "
        f"{'; '.join(problems)} — {FIX}")


# --- untriggered proofs (item 9.3; these run before the match) -----------------------

def _read_witness_lines(witness: Path) -> list[dict]:
    return [json.loads(line)
            for line in witness.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def _prove_cli_read_failed(mini_repo: Path, tmp_path: Path,
                           monkeypatch) -> None:
    """Drive inspect with an injected ``OSError`` (os-error-only proof).

    Asserts the witness line, the class and the exit.
    """
    import arch_audit_hook

    import learning_os.app.handlers.platform as platform
    import los
    from learning_os.app import pipeline as pipeline_module
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    log = tmp_path / "audit.jsonl"
    witness = tmp_path / "sites.jsonl"
    witness.touch()
    arch_audit_hook.install(str(log))
    monkeypatch.setenv(SITE_WITNESS_ENV, str(witness))

    def boom(root, expected=None):
        raise OSError("a9-proof: the read failed")

    monkeypatch.setattr(platform, "_snapshot", boom)
    try:
        args = los.build_parser().parse_args(
            ["inspect", "project-demo", "note-demo"])
        outcome = pipeline_module.run_cli(mini_repo, "project.inspect", args)
    finally:
        arch_audit_hook.uninstall()
    assert outcome.exit_code == 2
    lines = _read_witness_lines(witness)
    assert len(lines) == 1, lines
    assert lines[0] == {"operation": "project.inspect", "kind": "failure",
                        "site": "project.inspect.read-failed",
                        "class": "WriteRefused", "exit_code": 2}
    assert exit_for(WriteRefused("a9-proof", exit_code=2), "cli") == 2


def _prove_cli_stale_snapshot(mini_repo: Path, tmp_path: Path,
                              monkeypatch) -> None:
    """Drive inspect with a snapshot change between reads (race-only proof).

    The first read is the live tree; the re-read raises the real
    ``StaleSnapshot``. The manifest is canned so both batch ids
    resolve (fixture setup; the race, refusal and witness are real).
    Asserts the witness line, the class and the exit.
    """
    import arch_audit_hook

    import learning_os.app.handlers.platform as platform
    import learning_os.store.fingerprint as plumbing
    import los
    from learning_os.app import pipeline as pipeline_module
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import StaleSnapshot

    log = tmp_path / "audit.jsonl"
    witness = tmp_path / "sites.jsonl"
    witness.touch()
    arch_audit_hook.install(str(log))
    monkeypatch.setenv(SITE_WITNESS_ENV, str(witness))

    def flapping(root, expected=None):
        if expected is None:
            return plumbing.snapshot(root)
        raise StaleSnapshot(
            "snapshot changed; restart this read before continuing")

    manifest = {"records": [{"id": "project-demo", "type": "project"},
                            {"id": "note-demo", "type": "note"}]}
    monkeypatch.setattr(platform, "_snapshot", flapping)
    monkeypatch.setattr(platform, "_fresh_manifest_and_repo",
                        lambda root, snapshot_id=None: (manifest, None))
    try:
        args = los.build_parser().parse_args(
            ["inspect", "project-demo", "note-demo"])
        outcome = pipeline_module.run_cli(mini_repo, "project.inspect", args)
    finally:
        arch_audit_hook.uninstall()
    assert outcome.exit_code == 3
    lines = _read_witness_lines(witness)
    assert len(lines) == 1, lines
    assert lines[0] == {"operation": "project.inspect", "kind": "failure",
                        "site": "project.inspect.stale-snapshot",
                        "class": "StaleSnapshot", "exit_code": 3}
    assert exit_for(StaleSnapshot("a9-proof", exit_code=3), "cli") == 3


def _prove_stage_unknown_status_guarded(mini_repo: Path, tmp_path: Path,
                                        monkeypatch) -> None:
    """The guards refuse a bogus status; the site never fires (item 9.3).

    Shows the real parser and gateway admission both refuse the value
    (a valid value passes admission, pinning the refusal to it), then
    refuses through ``run_gateway`` and asserts no witness line names
    the site.
    """
    import arch_audit_hook
    from gateway_helpers import approved_v2_envelope

    import los
    from learning_os.app import pipeline as pipeline_module
    from learning_os.app.gateway import prepare_dispatch
    from learning_os.domain.failures import WriteRefused
    from learning_os.store.contracts.capability_catalog import command_definitions
    from learning_os.store.diagnostics import tracer as diag_tracer
    from learning_os.store.diagnostics.store import bind_store as _bind_diag_store

    site = "stage.progress.update.unknown-status"
    with pytest.raises(SystemExit) as status:
        los.build_parser().parse_args(
            ["stage-progress", "unit-demo-l01", "stage-demo", "bogus"])
    assert status.value.code == 2
    definitions = command_definitions(mini_repo)
    definition = definitions["stage.progress.update"]
    valid = {"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
             "status": "active"}
    prepare_dispatch(mini_repo, definition,
                     {"schema_version": 2, "payload": dict(valid)},
                     dict(valid), parser_factory=los.build_parser)
    bogus = dict(valid, status="bogus")
    envelope = approved_v2_envelope(
        mini_repo, capability="stage.progress.update", payload=bogus,
        artifact_ids=[], idempotency_key="a9-proof-unknown-status")
    with pytest.raises(WriteRefused):
        prepare_dispatch(mini_repo, definition, envelope, dict(bogus),
                         parser_factory=los.build_parser)
    log = tmp_path / "audit.jsonl"
    witness = tmp_path / "sites.jsonl"
    witness.touch()
    arch_audit_hook.install(str(log))
    monkeypatch.setenv(SITE_WITNESS_ENV, str(witness))
    try:
        _bind_diag_store(mini_repo)
        attempt = diag_tracer.begin_attempt(
            {"capability": "stage.progress.update"})
        outcome = pipeline_module.run_gateway(
            mini_repo, envelope, requested="stage.progress.update",
            definitions=definitions, attempt=attempt, replay_only=False,
            parser_factory=los.build_parser)
    finally:
        arch_audit_hook.uninstall()
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert "status" in (outcome.error or {}).get("message", "")
    lines = _read_witness_lines(witness)
    assert all(line.get("site") != site for line in lines), lines


#: Site -> its proof driver (item 9.3). One parametrized test below,
#: so each site's proof node carries the site id and the same-session
#: `-k` over operation names selects it.
_PROOF_FNS = {
    "project.inspect.read-failed": _prove_cli_read_failed,
    "project.inspect.stale-snapshot": _prove_cli_stale_snapshot,
    "stage.progress.update.unknown-status":
        _prove_stage_unknown_status_guarded,
}


def _a9_world(operation: str, case_id: str, tmp_path: Path):
    """A fresh rich_world from one success case (proofs only)."""
    import scenario_harness as harness

    doc = harness.load_case_file(CASES_DIR / f"{operation}.yaml")
    bare = next(item for item in doc["cases"] if item["id"] == case_id)
    case = {"fixture": doc.get("fixture", "rich_world"),
            "observations": doc["observations"],
            "fixture_mtime": doc.get(
                "fixture_mtime", harness.FIXTURE_MTIME_DEFAULT),
            **bare}
    return harness._prepare_world(case, operation, tmp_path / "world")


def _a9_run_gateway(root: Path, operation: str, payload: dict,
                    artifact_ids, key: str, tmp_path: Path, monkeypatch,
                    channel: str = "operator"):
    """One gateway attempt with a private witness file (proofs only).

    Returns ``(outcome, lines)``. The envelope is operator-approved,
    or carries the given channel with its approval recomputed; the
    attempt runs outside the scenario harness.
    """
    import arch_audit_hook
    from gateway_helpers import approved_v2_envelope

    import los
    from learning_os.app import pipeline as pipeline_module
    from learning_os.store.contracts.capability_catalog import (
        command_definitions,
    )
    from learning_os.store.contracts.gateway import intent_sha256
    from learning_os.store.diagnostics import tracer as diag_tracer
    from learning_os.store.diagnostics.store import bind_store as _bind_diag_store

    log = tmp_path / "audit.jsonl"
    witness = tmp_path / "sites.jsonl"
    witness.touch()
    envelope = approved_v2_envelope(
        root, capability=operation, payload=payload,
        artifact_ids=list(artifact_ids), idempotency_key=key)
    if channel != "operator":
        envelope["channel"] = channel
        envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    arch_audit_hook.install(str(log))
    monkeypatch.setenv(SITE_WITNESS_ENV, str(witness))
    try:
        _bind_diag_store(root)
        attempt = diag_tracer.begin_attempt({"capability": operation})
        outcome = pipeline_module.run_gateway(
            root, envelope, requested=operation,
            definitions=command_definitions(root), attempt=attempt,
            replay_only=False, parser_factory=los.build_parser)
    finally:
        arch_audit_hook.uninstall()
    return outcome, _read_witness_lines(witness)


def _prove_guarded_enum(mini_repo: Path, tmp_path: Path, monkeypatch, *,
                        site: str, operation: str, cli_argv: list,
                        field: str, valid: dict, key: str) -> None:
    """One enum-guarded backstop: guards refuse, the site never fires.

    The real parser refuses the bogus value; gateway admission passes
    the valid payload (pinning the refusal to the value) and refuses
    the bogus one; the gateway attempt refuses with no witness line
    naming the site. The item 9.3 guarded shape, per site data.
    """
    from gateway_helpers import approved_v2_envelope

    import los
    from learning_os.app.gateway import prepare_dispatch
    from learning_os.domain.failures import WriteRefused
    from learning_os.store.contracts.capability_catalog import command_definitions

    with pytest.raises(SystemExit) as refused:
        los.build_parser().parse_args(cli_argv)
    assert refused.value.code == 2
    definitions = command_definitions(mini_repo)
    definition = definitions[operation]
    prepare_dispatch(mini_repo, definition,
                     {"schema_version": 2, "payload": dict(valid)},
                     dict(valid), parser_factory=los.build_parser)
    bogus = dict(valid, **{field: "bogus"})
    envelope = approved_v2_envelope(
        mini_repo, capability=operation, payload=bogus,
        artifact_ids=[], idempotency_key=key)
    with pytest.raises(WriteRefused):
        prepare_dispatch(mini_repo, definition, envelope, dict(bogus),
                         parser_factory=los.build_parser)
    outcome, lines = _a9_run_gateway(
        mini_repo, operation, bogus, [], key, tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert field in (outcome.error or {}).get("message", "")
    assert all(line.get("site") != site for line in lines), lines


def _prove_detour_unknown_classification_guarded(mini_repo: Path,
                                                 tmp_path: Path,
                                                 monkeypatch) -> None:
    """The classification guards refuse ``bogus`` first (R-A9-3)."""
    _prove_guarded_enum(
        mini_repo, tmp_path, monkeypatch,
        site="detour.create.unknown-classification",
        operation="detour.create",
        cli_argv=["detour-create", "unit-demo-l01", "stage-demo",
                  "--title", "Revisit expectation",
                  "--classification", "bogus"],
        field="classification",
        valid={"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
               "title": "Revisit expectation",
               "classification": "required-now"},
        key="a9-proof-unknown-classification")


def _prove_path_unknown_status_guarded(mini_repo: Path, tmp_path: Path,
                                       monkeypatch) -> None:
    """The status guards refuse ``bogus`` first (R-A9-3)."""
    _prove_guarded_enum(
        mini_repo, tmp_path, monkeypatch,
        site="path.progress.update.unknown-status",
        operation="path.progress.update",
        cli_argv=["path-progress", "path-demo", "stage-demo-path",
                  "bogus"],
        field="status",
        valid={"path_id": "path-demo", "stage_id": "stage-demo-path",
               "status": "complete"},
        key="a9-proof-path-unknown-status")


def _prove_selection_unknown_action_guarded(mini_repo: Path,
                                            tmp_path: Path,
                                            monkeypatch) -> None:
    """The action guards refuse ``bogus`` first (R-A9-3)."""
    _prove_guarded_enum(
        mini_repo, tmp_path, monkeypatch,
        site="unit.source-selection.set.unknown-action",
        operation="unit.source-selection.set",
        cli_argv=["unit-source-selection", "unit-demo-l01",
                  "source-demo-book", "lecture-01.pdf", "bogus"],
        field="action",
        valid={"unit_id": "unit-demo-l01",
               "source_id": "source-demo-book",
               "locator": "lecture-01.pdf", "action": "select",
               "purpose": "Primary derivation"},
        key="a9-proof-unknown-action")


def _prove_stage_no_working_note(mini_repo: Path, tmp_path: Path,
                                 monkeypatch) -> None:
    """A stage without working_note fires the site (R-A9-2).

    Every rich_world stage carries one and no operation clears it,
    so no case input reaches the gate; the proof injects the
    condition by direct tree surgery and asserts the witness line,
    the class and the exit.
    """
    import yaml

    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("stage.note.write", "append-note", tmp_path)
    root = ctx.root
    map_path = (root / "curriculum/modules/module-demo/units"
                / "unit-demo-l01/study-map.yaml")
    data = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    stage = next(row for row in data["stages"]
                 if row["id"] == "stage-demo")
    assert stage["working_note"], "A9 proof needs a working_note to drop"
    del stage["working_note"]
    map_path.write_text(yaml.safe_dump(data, sort_keys=False),
                        encoding="utf-8")
    outcome, lines = _a9_run_gateway(
        root, "stage.note.write",
        {"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
         "text": "a9 proof note"},
        ["unit-demo-l01"], "a9-proof-no-working-note",
        tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "stage.note.write", "kind": "failure",
                      "site": "stage.note.write.no-working-note",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2),
                    "gateway.dispatch") == 2


def _prove_feedback_wrong_source(mini_repo: Path, tmp_path: Path,
                                 monkeypatch) -> None:
    """A resource bound to another source fires the site (R-A9-2).

    The registry carries a single source, so no case input can name
    a valid second one; the proof injects a second source plus a
    resource declaring the first and asserts the witness line, the
    class and the exit.
    """
    import yaml

    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("source.feedback.record", "record-feedback",
                    tmp_path)
    root = ctx.root
    sources_path = root / "sources/sources.yaml"
    sources = yaml.safe_load(sources_path.read_text(encoding="utf-8"))
    assert [row["id"] for row in sources["sources"]] == [
        "source-demo-book"]
    sources["sources"].append({"id": "source-demo-second",
                               "title": "Second Source", "type": "book"})
    sources_path.write_text(yaml.safe_dump(sources, sort_keys=False),
                            encoding="utf-8")
    map_path = (root / "curriculum/modules/module-demo/units"
                / "unit-demo-l01/study-map.yaml")
    data = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    stage = next(row for row in data["stages"]
                 if row["id"] == "stage-demo")
    stage.setdefault("resources", []).append(
        {"id": "resource-a9-proof", "source_id": "source-demo-book"})
    map_path.write_text(yaml.safe_dump(data, sort_keys=False),
                        encoding="utf-8")
    outcome, lines = _a9_run_gateway(
        root, "source.feedback.record",
        {"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
         "source_id": "source-demo-second", "feedback": "helpful",
         "resource_id": "resource-a9-proof"},
        ["unit-demo-l01", "study-map-demo-l01"],
        "a9-proof-wrong-source", tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "source.feedback.record",
                      "kind": "failure",
                      "site": "source.feedback.record.wrong-source",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2),
                    "gateway.dispatch") == 2


def _prove_unit_note_outside_repo(mini_repo: Path, tmp_path: Path,
                                  monkeypatch) -> None:
    """A working note outside the root fires the site (R-A9-2).

    The unit default stays inside and no request field sets the
    note, so no case input reaches the gate; the proof injects an
    escaping working_note by direct tree surgery and asserts the
    witness line, the class and the exit.
    """
    import yaml

    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("unit.note.append", "append-note", tmp_path)
    root = ctx.root
    unit_path = (root / "curriculum/modules/module-demo/units"
                 / "unit-demo-l01/unit.yaml")
    data = yaml.safe_load(unit_path.read_text(encoding="utf-8"))
    data["working_note"] = "../../../../outside-a9-proof.md"
    unit_path.write_text(yaml.safe_dump(data, sort_keys=False),
                         encoding="utf-8")
    outcome, lines = _a9_run_gateway(
        root, "unit.note.append",
        {"unit_id": "unit-demo-l01", "title": "proof",
         "text": "a9 proof note"},
        ["unit-demo-l01"], "a9-proof-note-outside-repo",
        tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "unit.note.append", "kind": "failure",
                      "site": "unit.note.append.note-outside-repo",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2),
                    "gateway.dispatch") == 2


def _prove_ability_bad_app_confirmation(mini_repo: Path, tmp_path: Path,
                                        monkeypatch) -> None:
    """A mismatched app confirmation on channel ui fires it (R-A9-2).

    The harness seals channel operator, so no case input reaches the
    gate; the proof drives the gateway directly with a ui-channel
    envelope and asserts the witness line, the class and the exit.
    """
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import Unconfirmed

    ctx = _a9_world("learner.ability-observation.append",
                    "append-observation", tmp_path)
    root = ctx.root
    outcome, lines = _a9_run_gateway(
        root, "learner.ability-observation.append",
        {"workspace": "workspace-demo", "ability": "ability-demo-derive",
         "claim": "Derived expectation for the fixture gamble.",
         "work_ref": "conversation://fixture/work-2",
         "confirmation_ref": "conversation://fixture/confirmation-2",
         "activity": "worked derivation", "result": "correct",
         "assistance": "none",
         "condition": ["finite discrete outcomes"],
         "evidence_tag": ["correct derivation"]},
        ["workspace-demo"], "a9-proof-bad-app-confirmation",
        tmp_path, monkeypatch, channel="ui")
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "learner.ability-observation.append",
                      "kind": "failure",
                      "site": "learner.ability-observation.append."
                              "bad-app-confirmation",
                      "class": "Unconfirmed", "exit_code": 2}]
    assert exit_for(Unconfirmed("a9-proof", exit_code=2),
                    "gateway.dispatch") == 2


def _prove_evidence_unreadable_frontmatter(mini_repo: Path, tmp_path: Path,
                                           monkeypatch) -> None:
    """An unreadable note frontmatter fires the site (R-A9-2).

    The loader skips a corrupt note at load (a static corruption
    then refuses as unknown-note instead), so no static fixture
    input reaches the gate; the proof injects the LoaderError into
    the handler's own frontmatter re-read and asserts the witness
    line, the class and the exit.
    """
    import learning_os.app.handlers.notes as notes_handlers
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused
    from learning_os.store.loader import LoaderError

    ctx = _a9_world("note.evidence.add", "add-evidence", tmp_path)
    root = ctx.root

    def unreadable(content, path):
        raise LoaderError("a9-proof: frontmatter unreadable")

    monkeypatch.setattr(notes_handlers, "parse_frontmatter", unreadable)
    outcome, lines = _a9_run_gateway(
        root, "note.evidence.add",
        {"note_id": "note-demo", "evidence_type": "derivation",
         "ref": "material://source-demo-book/book.pdf"},
        ["note-demo"], "a9-proof-unreadable-frontmatter",
        tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "note.evidence.add", "kind": "failure",
                      "site": "note.evidence.add.unreadable-frontmatter",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2),
                    "gateway.dispatch") == 2


_PROOF_FNS.update({
    "detour.create.unknown-classification":
        _prove_detour_unknown_classification_guarded,
    "path.progress.update.unknown-status":
        _prove_path_unknown_status_guarded,
    "unit.source-selection.set.unknown-action":
        _prove_selection_unknown_action_guarded,
    "stage.note.write.no-working-note": _prove_stage_no_working_note,
    "source.feedback.record.wrong-source": _prove_feedback_wrong_source,
    "unit.note.append.note-outside-repo": _prove_unit_note_outside_repo,
    "learner.ability-observation.append.bad-app-confirmation":
        _prove_ability_bad_app_confirmation,
    "note.evidence.add.unreadable-frontmatter":
        _prove_evidence_unreadable_frontmatter,
})


def _prove_attempt_bad_termin_guarded(mini_repo: Path, tmp_path: Path,
                                          monkeypatch) -> None:
    """The termin guards refuse ``bogus`` first (R-A9-3)."""
    _prove_guarded_enum(
        mini_repo, tmp_path, monkeypatch,
        site="module.attempt.record.bad-termin",
        operation="module.attempt.record",
        cli_argv=["module-attempt", "module-demo", "--termin", "bogus",
                  "--date", "2026-10-09", "--result", "sat"],
        field="termin",
        valid={"module_id": "module-demo", "termin": 2,
               "date": "2026-10-09", "result": "sat"},
        key="a9-proof-attempt-bad-termin")

def _prove_attempt_bad_result_guarded(mini_repo: Path, tmp_path: Path,
                                        monkeypatch) -> None:
    """The result guards refuse ``bogus`` first (R-A9-3)."""
    _prove_guarded_enum(
        mini_repo, tmp_path, monkeypatch,
        site="module.attempt.record.bad-result",
        operation="module.attempt.record",
        cli_argv=["module-attempt", "module-demo", "--termin", "2",
                  "--date", "2026-10-09", "--result", "bogus"],
        field="result",
        valid={"module_id": "module-demo", "termin": 2,
               "date": "2026-10-09", "result": "sat"},
        key="a9-proof-attempt-bad-result")

def _prove_attempt_bad_grade_guarded(mini_repo: Path, tmp_path: Path,
                                       monkeypatch) -> None:
    """The grade guards refuse ``bogus`` first (R-A9-3)."""
    _prove_guarded_enum(
        mini_repo, tmp_path, monkeypatch,
        site="module.attempt.record.bad-grade",
        operation="module.attempt.record",
        cli_argv=["module-attempt", "module-demo", "--termin", "2",
                  "--date", "2026-10-09", "--result", "sat",
                  "--grade", "bogus"],
        field="grade",
        valid={"module_id": "module-demo", "termin": 2,
               "date": "2026-10-09", "result": "sat", "grade": 2.0},
        key="a9-proof-attempt-bad-grade")

def _prove_sitting_bad_termin_guarded(mini_repo: Path, tmp_path: Path,
                                        monkeypatch) -> None:
    """The termin guards refuse ``bogus`` first (R-A9-3)."""
    _prove_guarded_enum(
        mini_repo, tmp_path, monkeypatch,
        site="module.sitting.update.bad-termin",
        operation="module.sitting.update",
        cli_argv=["module-sitting", "module-demo", "--termin", "bogus",
                  "--withdrawal-deadline", "2026-09-30"],
        field="termin",
        valid={"module_id": "module-demo", "termin": 2,
               "withdrawal_deadline": "2026-09-30"},
        key="a9-proof-sitting-bad-termin")

def _prove_coordination_unknown_section_guarded(
        mini_repo: Path, tmp_path: Path, monkeypatch) -> None:
    """The section guards refuse ``bogus`` first (R-A9-3)."""
    _prove_guarded_enum(
        mini_repo, tmp_path, monkeypatch,
        site="coordination.section.revise.unknown-section",
        operation="coordination.section.revise",
        cli_argv=["coordination-section-revise", "bogus",
                  "--text", "Ship it.",
                  "--expected-content-sha256",
                  "sha256:667bbd75392b1acdc610aa249aa5f2fe3d7659603901f415b36eda30fe2b4655"],
        field="section",
        valid={"section": "Commitments", "text": "Ship it.",
               "expected_content_sha256":
               "sha256:667bbd75392b1acdc610aa249aa5f2fe3d7659603901f415b36eda30fe2b4655"},
        key="a9-proof-coordination-unknown-section")

def _prove_coordination_no_file(mini_repo: Path, tmp_path: Path,
                                monkeypatch) -> None:
    """A missing COORDINATION.md fires the site (R-A9-2).

    The fixture always carries the file and no operation deletes
    it, so no case input reaches the gate; the proof removes it by
    direct tree surgery and asserts the witness line, the class and
    the exit.
    """
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("coordination.section.revise", "revise-commitments",
                    tmp_path)
    root = ctx.root
    coord = root / "work" / "COORDINATION.md"
    assert coord.is_file(), "A9 proof needs COORDINATION.md to remove"
    coord.unlink()
    outcome, lines = _a9_run_gateway(
        root, "coordination.section.revise",
        {"section": "Commitments", "text": "Ship the demo module plan.",
         "expected_content_sha256":
         "sha256:667bbd75392b1acdc610aa249aa5f2fe3d7659603901f415b36eda30fe2b4655"},
        ["coordination"], "a9-proof-no-coordination-file",
        tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "coordination.section.revise",
                      "kind": "failure",
                      "site": "coordination.section.revise."
                              "no-coordination-file",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2),
                    "gateway.dispatch") == 2

def _prove_coordination_read_failed(mini_repo: Path, tmp_path: Path,
                                    monkeypatch) -> None:
    """An OSError reading the file fires the site (os-error-only proof).

    No step can set unreadable permissions, so no case input reaches
    the gate; the proof injects the OSError and asserts the witness
    line, the class and the exit.
    """
    import learning_os.app.handlers.admin as admin
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("coordination.section.revise", "revise-commitments",
                    tmp_path)
    root = ctx.root

    def boom(root, path):
        raise OSError("a9-proof: the read failed")

    monkeypatch.setattr(admin, "read_bytes_inside", boom)
    outcome, lines = _a9_run_gateway(
        root, "coordination.section.revise",
        {"section": "Commitments", "text": "Ship the demo module plan.",
         "expected_content_sha256":
         "sha256:667bbd75392b1acdc610aa249aa5f2fe3d7659603901f415b36eda30fe2b4655"},
        ["coordination"], "a9-proof-coordination-read-failed",
        tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "coordination.section.revise",
                      "kind": "failure",
                      "site": "coordination.section.revise.read-failed",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2),
                    "gateway.dispatch") == 2

def _prove_workspace_not_active(mini_repo: Path, tmp_path: Path,
                                monkeypatch) -> None:
    """A paused workspace fires the site (R-A9-2).

    Both fixture workspaces are active and no operation archives
    or pauses one, so no case input reaches the gate; the proof
    pauses workspace-demo by direct tree surgery and asserts the
    witness line, the class and the exit.
    """
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("workspace.next-action.update", "update-action",
                    tmp_path)
    root = ctx.root
    context = root / "work" / "active" / "workspace-demo" / "CONTEXT.md"
    text = context.read_text(encoding="utf-8")
    assert "\nstatus: active\n" in text, (
        "A9 proof needs an active workspace to pause")
    context.write_text(text.replace("\nstatus: active\n",
                                    "\nstatus: paused\n", 1),
                       encoding="utf-8")
    outcome, lines = _a9_run_gateway(
        root, "workspace.next-action.update",
        {"workspace_id": "workspace-demo",
         "next_action": "Work the appendix example."},
        ["workspace-demo"], "a9-proof-workspace-not-active",
        tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "workspace.next-action.update",
                      "kind": "failure",
                      "site": "workspace.next-action.update."
                              "workspace-not-active",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2),
                    "gateway.dispatch") == 2

def _prove_workspace_no_next_action(mini_repo: Path, tmp_path: Path,
                                    monkeypatch) -> None:
    """A workspace without the section fires the site (R-A9-2).

    Both fixture workspaces carry a Next Action section and no
    operation removes one, so no case input reaches the gate; the
    proof drops the section by direct tree surgery and asserts the
    witness line, the class and the exit.
    """
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("workspace.next-action.update", "update-action",
                    tmp_path)
    root = ctx.root
    context = root / "work" / "active" / "workspace-demo" / "CONTEXT.md"
    text = context.read_text(encoding="utf-8")
    assert "\n## Next Action\n" in text, (
        "A9 proof needs a Next Action section to drop")
    head, _, _ = text.partition("\n## Next Action\n")
    context.write_text(head.rstrip("\n") + "\n", encoding="utf-8")
    outcome, lines = _a9_run_gateway(
        root, "workspace.next-action.update",
        {"workspace_id": "workspace-demo",
         "next_action": "Work the appendix example."},
        ["workspace-demo"], "a9-proof-no-next-action",
        tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "workspace.next-action.update",
                      "kind": "failure",
                      "site": "workspace.next-action.update.no-next-action",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2),
                    "gateway.dispatch") == 2

_PROOF_FNS.update({
    'module.attempt.record.bad-termin': _prove_attempt_bad_termin_guarded,
    'module.attempt.record.bad-result': _prove_attempt_bad_result_guarded,
    'module.attempt.record.bad-grade': _prove_attempt_bad_grade_guarded,
    'module.sitting.update.bad-termin': _prove_sitting_bad_termin_guarded,
    'coordination.section.revise.unknown-section': _prove_coordination_unknown_section_guarded,
    'coordination.section.revise.no-coordination-file': _prove_coordination_no_file,
    'coordination.section.revise.read-failed': _prove_coordination_read_failed,
    'workspace.next-action.update.workspace-not-active': _prove_workspace_not_active,
    'workspace.next-action.update.no-next-action': _prove_workspace_no_next_action,
})


def _a9_run_cli(root: Path, operation: str, argv: list,
                tmp_path: Path, monkeypatch):
    """One CLI attempt with a private witness file (proofs only).

    Returns ``(outcome, lines)``. The real parser turns ``argv``
    into args; the attempt runs outside the scenario harness.
    """
    import arch_audit_hook

    import los
    from learning_os.app import pipeline as pipeline_module

    log = tmp_path / "audit.jsonl"
    witness = tmp_path / "sites.jsonl"
    witness.touch()
    arch_audit_hook.install(str(log))
    monkeypatch.setenv(SITE_WITNESS_ENV, str(witness))
    try:
        args = los.build_parser().parse_args(argv)
        outcome = pipeline_module.run_cli(root, operation, args)
    finally:
        arch_audit_hook.uninstall()
    return outcome, _read_witness_lines(witness)

def _prove_inbox_list_failed(mini_repo: Path, tmp_path: Path,
                             monkeypatch) -> None:
    """An OSError listing the inbox fires the site (os-error-only proof).

    No step can arrange an unreadable inbox, so no case input reaches
    the gate; the proof injects the OSError and asserts the witness
    line, the class and the exit.
    """
    import learning_os.app.handlers.capture as capture
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("inbox.list", "list-drops", tmp_path)
    root = ctx.root

    def boom(root):
        raise OSError("a9-proof: the listing failed")

    monkeypatch.setattr(capture, "_inbox_search_rows", boom)
    outcome, lines = _a9_run_cli(root, "inbox.list", ["inbox-list"],
                                 tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "inbox.list", "kind": "failure",
                      "site": "inbox.list.list-failed",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2),
                    "cli") == 2

def _prove_inbox_read_failed(mini_repo: Path, tmp_path: Path,
                             monkeypatch) -> None:
    """An OSError reading a drop fires the site (os-error-only proof).

    No step can arrange an unreadable drop, so no case input reaches
    the gate; the proof injects the OSError and asserts the witness
    line, the class and the exit.
    """
    import learning_os.app.handlers.capture as capture
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("inbox.content", "read-file", tmp_path)
    root = ctx.root

    def boom(*args, **kwargs):
        raise OSError("a9-proof: the read failed")

    monkeypatch.setattr(capture, "_bytes_inside_owner", boom)
    outcome, lines = _a9_run_cli(root, "inbox.content",
                                 ["inbox-read", "note-drop.md"],
                                 tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "inbox.content", "kind": "failure",
                      "site": "inbox.content.read-failed",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2),
                    "cli") == 2

def _prove_inbox_archive_collision(mini_repo: Path, tmp_path: Path,
                                   monkeypatch) -> None:
    """A pre-existing archive destination fires the site (R-A9-2).

    The archive starts empty and only this operation writes it,
    atomically with the removal, so no case input reaches the gate;
    the proof pre-creates the destination by direct tree surgery and
    asserts the witness line, the class and the exit.
    """
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("inbox.resolve", "resolve-file", tmp_path)
    root = ctx.root
    dest = root / "archive" / "inbox" / "2026" / "note-drop.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("a9-proof: a previous archive generation\n",
                    encoding="utf-8")
    outcome, lines = _a9_run_gateway(
        root, "inbox.resolve",
        {"name": "note-drop.md",
         "drop_sha256": "sha256:cff485a0c38476920bff529d70a47c19fddb0380750b9a0152521d7eb9b6c81d",
         "routed_to": ["note-demo"]},
        ["file:archive/inbox/2026/note-drop.md",
         "file:work/inbox/note-drop.md"],
        "a9-proof-archive-collision", tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "inbox.resolve", "kind": "failure",
                      "site": "inbox.resolve.archive-collision",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2),
                    "gateway.dispatch") == 2

def _prove_inbox_resolve_read_failed(mini_repo: Path, tmp_path: Path,
                                     monkeypatch) -> None:
    """An unreadable drop fires the site (os-error-only proof).

    No step can set unreadable permissions, so no case input reaches
    the gate; the proof revokes the drop's read bit by direct tree
    surgery and asserts the witness line, the class and the exit.
    """
    import os

    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("inbox.resolve", "resolve-file", tmp_path)
    root = ctx.root
    drop = root / "work" / "inbox" / "note-drop.md"
    assert drop.is_file(), "A9 proof needs the drop to revoke"
    os.chmod(drop, 0)
    try:
        outcome, lines = _a9_run_gateway(
            root, "inbox.resolve",
            {"name": "note-drop.md",
             "drop_sha256": "sha256:cff485a0c38476920bff529d70a47c19fddb0380750b9a0152521d7eb9b6c81d",
             "routed_to": ["note-demo"]},
            ["file:archive/inbox/2026/note-drop.md",
             "file:work/inbox/note-drop.md"],
            "a9-proof-inbox-resolve-read-failed", tmp_path, monkeypatch)
    finally:
        os.chmod(drop, 0o644)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "inbox.resolve", "kind": "failure",
                      "site": "inbox.resolve.read-failed",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2),
                    "gateway.dispatch") == 2

def _prove_note_not_an_object_guarded(mini_repo: Path, tmp_path: Path,
                                      monkeypatch) -> None:
    """The note guards refuse ``bogus`` first (R-A9-3)."""
    _prove_guarded_enum(
        mini_repo, tmp_path, monkeypatch,
        site="note.create.not-an-object",
        operation="note.create",
        cli_argv=["note-create", "--note", "bogus",
                  "--body-file", "work/inbox/note-drop.md"],
        field="note",
        valid={"note": {"id": "note-scenario-create-1",
                        "title": "Scenario synthesis one",
                        "path": "knowledge/notes/mathematics/"
                                "note-scenario-create-1.md",
                        "concepts": ["concept-expected-value"],
                        "sources": ["source-demo-book"],
                        "contexts": ["workspace-demo"],
                        "supersedes": ["note-demo"]},
               "body_file": "work/a9-proof-body.md",
               "body_file_sha256": "sha256:" + "0" * 64},
        key="a9-proof-note-not-an-object")

def _note_create_proof_body(root: Path) -> dict:
    """A real body file plus its sha for note.create proofs."""
    import hashlib

    body = root / "work" / "a9-proof-body.md"
    body.write_text("A9 proof body.\n", encoding="utf-8")
    digest = "sha256:" + hashlib.sha256(
        body.read_bytes()).hexdigest()
    # Absolute: the bound reader resolves against the process cwd.
    return {"body_file": str(body), "body_file_sha256": digest}

def _prove_note_destination_exists(mini_repo: Path, tmp_path: Path,
                                   monkeypatch) -> None:
    """An unregistered destination file fires the site (R-A9-2).

    Every fixture ``.md`` under knowledge/notes/ registers, and
    creating one registers it too, so no case input reaches the
    gate; the proof pre-creates the destination by direct tree
    surgery and asserts the witness line, the class and the exit.
    """
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("note.create", "create-note", tmp_path)
    root = ctx.root
    # Valid frontmatter under a different id: the path exists but the
    # created id stays fresh, so the destination check fires instead
    # of the earlier id collision.
    dest = (root / "knowledge" / "notes" / "mathematics"
            / "note-scenario-create-24.md")
    dest.write_text("---\nid: note-scenario-other\ntitle: Other\n---\n"
                    "A9 proof body.\n", encoding="utf-8")
    payload = {"note": {"id": "note-scenario-create-24",
                        "title": "A9 proof note",
                        "path": "knowledge/notes/mathematics/"
                                "note-scenario-create-24.md"},
               **_note_create_proof_body(root)}
    outcome, lines = _a9_run_gateway(
        root, "note.create", payload, ["note-scenario-create-24"],
        "a9-proof-destination-exists", tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "note.create", "kind": "failure",
                      "site": "note.create.destination-exists",
                      "class": "WriteRefused", "exit_code": None}]
    assert exit_for(WriteRefused("a9-proof"), "gateway.dispatch") == 2

def _prove_note_symlink_path(mini_repo: Path, tmp_path: Path,
                             monkeypatch) -> None:
    """A symlinked destination fires the site (R-A9-2).

    The fixture carries no symlinks and no step can create one, so
    no case input reaches the gate; the proof plants the symlink by
    direct tree surgery and asserts the witness line, the class and
    the exit.
    """
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("note.create", "create-note", tmp_path)
    root = ctx.root
    # The link target carries a different id, so the created id stays
    # fresh and the symlink check fires instead of id collision.
    target = (root / "knowledge" / "notes" / "mathematics"
              / "note-scenario-other.md")
    target.write_text("---\nid: note-scenario-other\ntitle: Other\n---\n"
                      "A9 proof body.\n", encoding="utf-8")
    dest = (root / "knowledge" / "notes" / "mathematics"
            / "note-scenario-create-25.md")
    dest.symlink_to(target)
    payload = {"note": {"id": "note-scenario-create-25",
                        "title": "A9 proof note",
                        "path": "knowledge/notes/mathematics/"
                                "note-scenario-create-25.md"},
               **_note_create_proof_body(root)}
    outcome, lines = _a9_run_gateway(
        root, "note.create", payload, ["note-scenario-create-25"],
        "a9-proof-symlink-path", tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "note.create", "kind": "failure",
                      "site": "note.create.symlink-path",
                      "class": "WriteRefused", "exit_code": None}]
    assert exit_for(WriteRefused("a9-proof"), "gateway.dispatch") == 2

def _prove_note_unreadable_superseded(mini_repo: Path, tmp_path: Path,
                                      monkeypatch) -> None:
    """An unreadable superseded note fires the site (R-A9-2).

    Fixture notes read cleanly and no write path stores an
    unreadable one, so no case input reaches the gate; the proof
    injects the loader failure and asserts the witness line, the
    class and the exit.
    """
    import learning_os.app.handlers.notes as notes
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused
    from learning_os.store.loader import LoaderError

    ctx = _a9_world("note.create", "create-note", tmp_path)
    root = ctx.root

    def boom(content, source):
        raise LoaderError("a9-proof: the superseded note is unreadable")

    monkeypatch.setattr(notes, "parse_frontmatter", boom)
    payload = {"note": {"id": "note-scenario-create-26",
                        "title": "A9 proof note",
                        "path": "knowledge/notes/mathematics/"
                                "note-scenario-create-26.md",
                        "supersedes": ["note-demo"]},
               **_note_create_proof_body(root)}
    outcome, lines = _a9_run_gateway(
        root, "note.create", payload,
        ["note-scenario-create-26", "note-demo"],
        "a9-proof-unreadable-superseded", tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "note.create", "kind": "failure",
                      "site": "note.create.unreadable-superseded",
                      "class": "WriteRefused", "exit_code": None}]
    assert exit_for(WriteRefused("a9-proof"), "gateway.dispatch") == 2

def _prove_note_read_failed(mini_repo: Path, tmp_path: Path,
                            monkeypatch) -> None:
    """An OSError reading a note fires the site (os-error-only proof).

    No step can arrange an unreadable note, so no case input reaches
    the gate; the proof injects the OSError and asserts the witness
    line, the class and the exit.
    """
    import learning_os.app.handlers.notes as notes
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("note.content", "read-note", tmp_path)
    root = ctx.root

    def boom(root, note):
        raise OSError("a9-proof: the read failed")

    monkeypatch.setattr(notes, "_note_bytes", boom)
    outcome, lines = _a9_run_cli(root, "note.content",
                                 ["note-read", "note-demo"],
                                 tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "note.content", "kind": "failure",
                      "site": "note.content.read-failed",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2),
                    "cli") == 2

def _prove_note_read_bad_encoding(mini_repo: Path, tmp_path: Path,
                                  monkeypatch) -> None:
    """Non-UTF-8 note bytes fire the site (R-A9-2).

    Writes validate UTF-8, so no step can author non-UTF-8 canonical
    bytes and no case input reaches the gate; the proof injects the
    bad bytes and asserts the witness line, the class and the exit.
    """
    import learning_os.app.handlers.notes as notes
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("note.content", "read-note", tmp_path)
    root = ctx.root

    def boom(root, note):
        return b"\xff\xfe-not-utf8-\xff"

    monkeypatch.setattr(notes, "_note_bytes", boom)
    outcome, lines = _a9_run_cli(root, "note.content",
                                 ["note-read", "note-demo"],
                                 tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "note.content", "kind": "failure",
                      "site": "note.content.bad-encoding",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2),
                    "cli") == 2

def _prove_search_read_failed(mini_repo: Path, tmp_path: Path,
                              monkeypatch) -> None:
    """An OSError mid-read fires the site (os-error-only proof).

    No step can arrange an unreadable record, so no case input
    reaches the gate; the proof injects the OSError and asserts the
    witness line, the class and the exit. It fires the content arm;
    the entry pins the metadata arm's identical raise.
    """
    import learning_os.app.handlers.notes as notes
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("note.search", "content-hit", tmp_path)
    root = ctx.root

    def boom(root, note):
        raise OSError("a9-proof: the read failed")

    monkeypatch.setattr(notes, "_note_bytes", boom)
    outcome, lines = _a9_run_cli(root, "note.search",
                                 ["search", "demo", "--content"],
                                 tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "note.search", "kind": "failure",
                      "site": "note.search.read-failed",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2),
                    "cli") == 2

def _prove_search_bad_encoding(mini_repo: Path, tmp_path: Path,
                               monkeypatch) -> None:
    """Non-UTF-8 note bytes fire the site (R-A9-2).

    Writes validate UTF-8, so no step can author non-UTF-8 canonical
    bytes and no case input reaches the gate; the proof injects the
    bad bytes and asserts the witness line, the class and the exit.
    """
    import learning_os.app.handlers.notes as notes
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("note.search", "content-hit", tmp_path)
    root = ctx.root

    def boom(root, note):
        return b"\xff\xfe-not-utf8-\xff"

    monkeypatch.setattr(notes, "_note_bytes", boom)
    outcome, lines = _a9_run_cli(root, "note.search",
                                 ["search", "demo", "--content"],
                                 tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "note.search", "kind": "failure",
                      "site": "note.search.bad-encoding",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2),
                    "cli") == 2

def _prove_goal_malformed_ledger(mini_repo: Path, tmp_path: Path,
                                 monkeypatch) -> None:
    """A corrupt goal ledger fires the site (R-A9-2).

    The fixture ledger parses and the only writer stores valid
    YAML, so no case input reaches the gate; the proof corrupts the
    ledger by direct tree surgery and asserts the witness line, the
    class and the exit.
    """
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("goal.decide", "close-goal", tmp_path)
    root = ctx.root
    ledger = root / "operations" / "goal-ledger.yaml"
    assert ledger.is_file(), "A9 proof needs the ledger to corrupt"
    ledger.write_text("not: [valid\n  yaml: {\n", encoding="utf-8")
    outcome, lines = _a9_run_cli(root, "goal.decide",
                                 ["goal", "goal-demo-deferred", "--close"],
                                 tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "goal.decide", "kind": "failure",
                      "site": "goal.decide.malformed-ledger",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2),
                    "cli") == 2

def _prove_goal_unreadable_ledger(mini_repo: Path, tmp_path: Path,
                                  monkeypatch) -> None:
    """An unreadable goal ledger fires the site (os-error-only proof).

    No step can set unreadable permissions, so no case input reaches
    the gate; the proof revokes the ledger's read bit by direct tree
    surgery and asserts the witness line, the class and the exit.
    """
    import os

    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("goal.decide", "close-goal", tmp_path)
    root = ctx.root
    ledger = root / "operations" / "goal-ledger.yaml"
    assert ledger.is_file(), "A9 proof needs the ledger to revoke"
    os.chmod(ledger, 0)
    try:
        outcome, lines = _a9_run_cli(
            root, "goal.decide", ["goal", "goal-demo-deferred", "--close"],
            tmp_path, monkeypatch)
    finally:
        os.chmod(ledger, 0o644)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "goal.decide", "kind": "failure",
                      "site": "goal.decide.unreadable-ledger",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2),
                    "cli") == 2

def _prove_goal_unreadable_session(mini_repo: Path, tmp_path: Path,
                                   monkeypatch) -> None:
    """A corrupt own session ledger fires the site (R-A9-2).

    Session files are written valid and no case input corrupts the
    caller's own session ledger, so no case input reaches the gate;
    the proof injects the load failure and asserts the witness line,
    the class and the exit.
    """
    import learning_os.app.handlers.goals as goals
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("goal.decide", "close-goal", tmp_path)
    root = ctx.root

    def fake_ledger(root, session_id):
        return root / "operations" / "goal-ledger.yaml"

    def boom(root, session_id):
        raise WriteRefused("a9-proof: the session ledger is corrupt")

    monkeypatch.setattr(goals, "_session_ledger", fake_ledger)
    monkeypatch.setattr(goals, "_load_session_paths", boom)
    outcome, lines = _a9_run_cli(
        root, "goal.decide", ["goal", "goal-demo-deferred", "--close"],
        tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "goal.decide", "kind": "failure",
                      "site": "goal.decide.unreadable-session",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2),
                    "cli") == 2

def _prove_goal_not_admitted(mini_repo: Path, tmp_path: Path,
                             monkeypatch) -> None:
    """A gated gesture fires the site (R-A9-2).

    The static allowlist admits the gesture in this tree and no case
    input changes it, so no case input reaches the gate; the proof
    closes the gate by direct injection and asserts the witness
    line, the class and the exit.
    """
    import learning_os.app.handlers.goals as goals
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("goal.decide", "close-goal", tmp_path)
    root = ctx.root
    monkeypatch.setattr(goals, "gesture_allowed",
                        lambda capability: False)
    outcome, lines = _a9_run_cli(
        root, "goal.decide", ["goal", "goal-demo-deferred", "--close"],
        tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "goal.decide", "kind": "failure",
                      "site": "goal.decide.not-admitted",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2),
                    "cli") == 2

def _prove_observe_invalid_target(mini_repo: Path, tmp_path: Path,
                                  monkeypatch) -> None:
    """A broken runtime target fires the site (R-A9-2).

    The fixture carries one valid target and no step can break a
    study map's runtime_target, so no case input reaches the gate;
    the proof injects the collection failure and asserts the
    witness line, the class and the exit.
    """
    import learning_os.app.handlers.learner_observations as learner_observations
    from learning_os.app.outcomes import exit_for
    from learning_os.derive.learning_runtime import RuntimeInputError
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("learner.observe", "record-evidence", tmp_path)
    root = ctx.root

    def boom(repo):
        raise RuntimeInputError("a9-proof: the target is broken")

    monkeypatch.setattr(learner_observations, "collect_requirements", boom)
    outcome, lines = _a9_run_cli(
        root, "learner.observe",
        ["observe", "req-demo-l01-demo", "--activity", "exercise",
         "--result", "partial"],
        tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "learner.observe", "kind": "failure",
                      "site": "learner.observe.invalid-target",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2),
                    "cli") == 2

def _prove_observe_not_admitted(mini_repo: Path, tmp_path: Path,
                                monkeypatch) -> None:
    """A gated gesture fires the site (R-A9-2).

    The static allowlist admits the gesture in this tree and no case
    input changes it, so no case input reaches the gate; the proof
    closes the gate by direct injection and asserts the witness
    line, the class and the exit.
    """
    import learning_os.app.handlers.learner_observations as learner_observations
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("learner.observe", "record-evidence", tmp_path)
    root = ctx.root
    monkeypatch.setattr(learner_observations, "gesture_allowed",
                        lambda capability: False)
    outcome, lines = _a9_run_cli(
        root, "learner.observe",
        ["observe", "req-demo-l01-demo", "--activity", "exercise",
         "--result", "partial"],
        tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "learner.observe", "kind": "failure",
                      "site": "learner.observe.not-admitted",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2),
                    "cli") == 2

_PROOF_FNS.update({
    'inbox.list.list-failed': _prove_inbox_list_failed,
    'inbox.content.read-failed': _prove_inbox_read_failed,
    'inbox.resolve.archive-collision': _prove_inbox_archive_collision,
    'inbox.resolve.read-failed': _prove_inbox_resolve_read_failed,
    'note.create.not-an-object': _prove_note_not_an_object_guarded,
    'note.create.destination-exists': _prove_note_destination_exists,
    'note.create.symlink-path': _prove_note_symlink_path,
    'note.create.unreadable-superseded': _prove_note_unreadable_superseded,
    'note.content.read-failed': _prove_note_read_failed,
    'note.content.bad-encoding': _prove_note_read_bad_encoding,
    'note.search.read-failed': _prove_search_read_failed,
    'note.search.bad-encoding': _prove_search_bad_encoding,
    'goal.decide.malformed-ledger': _prove_goal_malformed_ledger,
    'goal.decide.unreadable-ledger': _prove_goal_unreadable_ledger,
    'goal.decide.unreadable-session': _prove_goal_unreadable_session,
    'goal.decide.not-admitted': _prove_goal_not_admitted,
    'learner.observe.invalid-target': _prove_observe_invalid_target,
    'learner.observe.not-admitted': _prove_observe_not_admitted,
})


def _prove_cli_guarded(tmp_path: Path, monkeypatch, *, site: str,
                       cli_argv: list, valid_argv: list) -> None:
    """A CLI-only guard: the real parser refuses, the site never fires.

    The bogus argv dies in argparse (exit 2) before any handler runs;
    the valid argv parses, pinning the refusal to the value. No query
    routes through the gateway, so the parser is the only guard.
    """
    import arch_audit_hook

    import los

    log = tmp_path / "audit.jsonl"
    witness = tmp_path / "sites.jsonl"
    witness.touch()
    arch_audit_hook.install(str(log))
    monkeypatch.setenv(SITE_WITNESS_ENV, str(witness))
    try:
        with pytest.raises(SystemExit) as refused:
            los.build_parser().parse_args(cli_argv)
        los.build_parser().parse_args(valid_argv)
    finally:
        arch_audit_hook.uninstall()
    assert refused.value.code == 2
    assert [line for line in _read_witness_lines(witness)
            if line.get("site") == site] == []

def _corrupt_note_demo(root: Path) -> None:
    """Break one note's frontmatter so the loader records a failure."""
    note = root / "knowledge" / "notes" / "mathematics" / "note-demo.md"
    assert note.is_file(), "A9 proof needs note-demo to corrupt"
    note.write_text("---\n\t: bad: [yaml\n---\nA9 proof body.\n",
                    encoding="utf-8")

def _prove_dossier_unreadable_records(mini_repo: Path, tmp_path: Path,
                                      monkeypatch) -> None:
    """Unreadable canonical records fire the site (R-A9-2).

    The fixture parses cleanly and no write path stores a broken
    record, so no case input reaches the gate; the proof corrupts one
    note by direct tree surgery and asserts the witness line, the
    class and the exit.
    """
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("dossier.read", "serve-l01", tmp_path)
    root = ctx.root
    _corrupt_note_demo(root)
    outcome, lines = _a9_run_cli(root, "dossier.read",
                                 ["dossier", "unit-demo-l01"],
                                 tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "dossier.read", "kind": "failure",
                      "site": "dossier.read.unreadable-records",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2), "cli") == 2

def _prove_dossier_no_source_map(mini_repo: Path, tmp_path: Path,
                                 monkeypatch) -> None:
    """A module without a source map fires the site (R-A9-2).

    Every fixture unit's module carries a map and no step can
    remove one, so no case input reaches the gate; the proof drops
    the map by direct tree surgery and asserts the witness line,
    the class and the exit.
    """
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("dossier.read", "serve-l01", tmp_path)
    root = ctx.root
    source_map = (root / "curriculum" / "modules" / "module-demo"
                  / "source-map.yaml")
    assert source_map.is_file(), "A9 proof needs the map to drop"
    source_map.unlink()
    outcome, lines = _a9_run_cli(root, "dossier.read",
                                 ["dossier", "unit-demo-l01"],
                                 tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "dossier.read", "kind": "failure",
                      "site": "dossier.read.no-source-map",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2), "cli") == 2

def _prove_dossier_bad_knowledge_map(mini_repo: Path, tmp_path: Path,
                                     monkeypatch) -> None:
    """A non-mapping knowledge map fires the site (R-A9-2).

    Both fixture units carry mapping knowledge maps and no step can
    rewrite one, so no case input reaches the gate; the proof swaps
    in a list by direct tree surgery and asserts the witness line,
    the class and the exit.
    """
    import yaml

    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("dossier.read", "serve-l01", tmp_path)
    root = ctx.root
    unit_file = (root / "curriculum" / "modules" / "module-demo"
                 / "units" / "unit-demo-l01" / "unit.yaml")
    data = yaml.safe_load(unit_file.read_text(encoding="utf-8"))
    assert isinstance(data.get("knowledge_map"), dict), (
        "A9 proof needs a mapping knowledge map to break")
    data["knowledge_map"] = ["not", "a", "mapping"]
    unit_file.write_text(yaml.safe_dump(data, sort_keys=False),
                         encoding="utf-8")
    outcome, lines = _a9_run_cli(root, "dossier.read",
                                 ["dossier", "unit-demo-l01"],
                                 tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "dossier.read", "kind": "failure",
                      "site": "dossier.read.bad-knowledge-map",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2), "cli") == 2

def _prove_dossier_build_failed(mini_repo: Path, tmp_path: Path,
                                monkeypatch) -> None:
    """A dossier build failure fires the site (R-A9-2).

    The handler builds well-shaped inputs and both fixture units
    build, so no case input reaches the gate; the proof injects the
    builder failure and asserts the witness line, the class and the
    exit.
    """
    import learning_os.app.handlers.resume as resume
    from learning_os.app.outcomes import exit_for
    from learning_os.derive.semantics.dossiers import DossierError
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("dossier.read", "serve-l01", tmp_path)
    root = ctx.root

    def boom(**kwargs):
        raise DossierError("a9-proof: the build failed")

    monkeypatch.setattr(resume, "build_dossier", boom)
    outcome, lines = _a9_run_cli(root, "dossier.read",
                                 ["dossier", "unit-demo-l01"],
                                 tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "dossier.read", "kind": "failure",
                      "site": "dossier.read.build-failed",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2), "cli") == 2

def _prove_dossier_stale_snapshot(mini_repo: Path, tmp_path: Path,
                                  monkeypatch) -> None:
    """A mid-read change fires the site (race-only proof).

    A single-threaded read cannot race itself, so no case input
    reaches the gate; the proof injects the mid-read change and
    asserts the witness line, the class and the exit.
    """
    import learning_os.app.handlers.resume as resume
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import StaleSnapshot

    ctx = _a9_world("dossier.read", "serve-l01", tmp_path)
    root = ctx.root
    real_snapshot = resume._snapshot
    calls = []

    def racing(root, expected=None):
        calls.append(expected)
        if len(calls) == 1:
            return real_snapshot(root, expected)
        raise StaleSnapshot("a9-proof: a write landed mid-read")

    monkeypatch.setattr(resume, "_snapshot", racing)
    outcome, lines = _a9_run_cli(root, "dossier.read",
                                 ["dossier", "unit-demo-l01"],
                                 tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 3
    assert lines == [{"operation": "dossier.read", "kind": "failure",
                      "site": "dossier.read.stale-snapshot",
                      "class": "StaleSnapshot", "exit_code": 3}]
    assert exit_for(StaleSnapshot("a9-proof", exit_code=3), "cli") == 3

def _prove_dossier_read_failed(mini_repo: Path, tmp_path: Path,
                               monkeypatch) -> None:
    """An OSError mid-read fires the site (os-error-only proof).

    No step can arrange an unreadable record, so no case input
    reaches the gate; the proof injects the OSError and asserts the
    witness line, the class and the exit.
    """
    import learning_os.app.handlers.resume as resume
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("dossier.read", "serve-l01", tmp_path)
    root = ctx.root

    def boom(root, expected=None):
        raise OSError("a9-proof: the read failed")

    monkeypatch.setattr(resume, "_snapshot", boom)
    outcome, lines = _a9_run_cli(root, "dossier.read",
                                 ["dossier", "unit-demo-l01"],
                                 tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "dossier.read", "kind": "failure",
                      "site": "dossier.read.read-failed",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2), "cli") == 2

def _prove_bootstrap_read_failed(mini_repo: Path, tmp_path: Path,
                                 monkeypatch) -> None:
    """An OSError mid-read fires the site (os-error-only proof).

    No step can arrange an unreadable record, so no case input
    reaches the gate; the proof injects the OSError and asserts the
    witness line, the class and the exit.
    """
    import learning_os.app.handlers.reads as reads
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("operator.bootstrap", "compact", tmp_path)
    root = ctx.root

    def boom(root, expected=None):
        raise OSError("a9-proof: the read failed")

    monkeypatch.setattr(reads, "_snapshot", boom)
    outcome, lines = _a9_run_cli(root, "operator.bootstrap",
                                 ["bootstrap", "--compact"],
                                 tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "operator.bootstrap", "kind": "failure",
                      "site": "operator.bootstrap.read-failed",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2), "cli") == 2

def _prove_status_unreadable_records(mini_repo: Path, tmp_path: Path,
                                     monkeypatch) -> None:
    """Unreadable canonical records fire the site (R-A9-2).

    The fixture validates and no step can damage it, so no case
    input reaches the gate; the proof corrupts one note by direct
    tree surgery and asserts the witness line, the class and the
    exit.
    """
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("status.read", "screen", tmp_path)
    root = ctx.root
    _corrupt_note_demo(root)
    outcome, lines = _a9_run_cli(root, "status.read", ["status"],
                                 tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "status.read", "kind": "failure",
                      "site": "status.read.unreadable-records",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2), "cli") == 2

def _prove_intelligence_git_history(mini_repo: Path, tmp_path: Path,
                                    monkeypatch) -> None:
    """An unreadable Git history fires the site (R-A9-2).

    The seam supplies an empty history and the fixture scans
    cleanly, so no case input reaches the gate; the proof injects
    the history failure and asserts the witness line, the class and
    the exit.
    """
    import learning_os.app.handlers.reads as reads
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused
    from learning_os.store.session.githistory import GitHistoryError

    ctx = _a9_world("intelligence.scan", "scan-text", tmp_path)
    root = ctx.root

    def boom(root, days=None, feed=None, *, goal_ledger=None):
        raise GitHistoryError("a9-proof: git is corrupt")

    monkeypatch.setattr(reads, "ranked_scan", boom)
    outcome, lines = _a9_run_cli(root, "intelligence.scan",
                                 ["intelligence-scan"],
                                 tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "intelligence.scan",
                      "kind": "failure",
                      "site": "intelligence.scan.git-history",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2), "cli") == 2

def _prove_intelligence_unrankable_queue(mini_repo: Path, tmp_path: Path,
                                         monkeypatch) -> None:
    """An unrankable queue fires the site (R-A9-2).

    The fixture scans and ranks cleanly, so no case input reaches
    the gate; the proof injects the rank failure and asserts the
    witness line, the class and the exit.
    """
    import learning_os.app.handlers.reads as reads
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("intelligence.scan", "scan-text", tmp_path)
    root = ctx.root

    def boom(root, days=None, feed=None, *, goal_ledger=None):
        raise ValueError("a9-proof: the queue is malformed")

    monkeypatch.setattr(reads, "ranked_scan", boom)
    outcome, lines = _a9_run_cli(root, "intelligence.scan",
                                 ["intelligence-scan"],
                                 tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "intelligence.scan",
                      "kind": "failure",
                      "site": "intelligence.scan.unrankable-queue",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2), "cli") == 2

def _prove_resume_no_resumable_stage(mini_repo: Path, tmp_path: Path,
                                     monkeypatch) -> None:
    """No resumable stage fires the site (R-A9-2).

    The fixture pointer resolves and no step can break it, so no
    case input reaches the gate; the proof injects the resolution
    failure and asserts the witness line, the class and the exit.
    """
    import learning_os.app.handlers.resume as resume
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("resume.read", "screen", tmp_path)
    root = ctx.root

    def boom(repo):
        return None, "a9-proof: nothing is resumable"

    monkeypatch.setattr(resume, "_resolve_stage", boom)
    outcome, lines = _a9_run_cli(root, "resume.read", ["resume"],
                                 tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "resume.read", "kind": "failure",
                      "site": "resume.read.no-resumable-stage",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2), "cli") == 2

def _prove_resume_dossier_build_failed(mini_repo: Path, tmp_path: Path,
                                       monkeypatch) -> None:
    """A resume dossier build failure fires the site (R-A9-2).

    The fixture builds cleanly and no step can author
    dossier-breaking data, so no case input reaches the gate; the
    proof injects the builder failure and asserts the witness line,
    the class and the exit.
    """
    import learning_os.app.handlers.resume as resume
    from learning_os.app.outcomes import exit_for
    from learning_os.derive.projection.resume_dossier import ResumeDossierError
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("resume.read", "screen", tmp_path)
    root = ctx.root

    def boom(**kwargs):
        raise ResumeDossierError("a9-proof: the build failed")

    monkeypatch.setattr(resume, "build_resume_dossier", boom)
    outcome, lines = _a9_run_cli(root, "resume.read", ["resume"],
                                 tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "resume.read", "kind": "failure",
                      "site": "resume.read.dossier-build-failed",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2), "cli") == 2

def _prove_runtime_mid_read_stale(mini_repo: Path, tmp_path: Path,
                                  monkeypatch) -> None:
    """A mid-read change fires the site (race-only proof).

    A single-threaded read cannot race itself, so no case input
    reaches the gate; the proof injects the mid-read change and
    asserts the witness line, the class and the exit.
    """
    import learning_os.app.handlers.reads as reads
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import StaleSnapshot

    ctx = _a9_world("runtime.session", "propose", tmp_path)
    root = ctx.root

    def stale(root):
        return "a9-proof-stale-snapshot"

    monkeypatch.setattr(reads, "_snapshot", stale)
    outcome, lines = _a9_run_cli(
        root, "runtime.session",
        ["runtime-session", "--requirement", "req-demo-l01-demo"],
        tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 3
    assert lines == [{"operation": "runtime.session", "kind": "failure",
                      "site": "runtime.session.mid-read-stale",
                      "class": "StaleSnapshot", "exit_code": None}]
    assert exit_for(StaleSnapshot("a9-proof"), "cli") == 3

def _prove_capabilities_unreadable_schema(mini_repo: Path, tmp_path: Path,
                                          monkeypatch) -> None:
    """A missing payload schema fires the site (R-A9-2).

    Every catalog command carries one and no step can remove it,
    so no case input reaches the gate; the proof drops the schema
    by direct tree surgery and asserts the witness line, the class
    and the exit.
    """
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("capabilities.read", "one-command", tmp_path)
    root = ctx.root
    schema = (root / "system" / "schema" / "capabilities"
              / "stage.progress.update.schema.json")
    assert schema.is_file(), "A9 proof needs the schema to drop"
    schema.unlink()
    outcome, lines = _a9_run_cli(root, "capabilities.read",
                                 ["capabilities", "stage.progress.update"],
                                 tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "capabilities.read", "kind": "failure",
                      "site": "capabilities.read.unreadable-payload-schema",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2), "cli") == 2

def _prove_unit_list_read_failed(mini_repo: Path, tmp_path: Path,
                                 monkeypatch) -> None:
    """An OSError mid-read fires the site (os-error-only proof).

    No step can arrange an unreadable record, so no case input
    reaches the gate; the proof injects the OSError and asserts the
    witness line, the class and the exit.
    """
    import learning_os.app.handlers.reads as reads
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("unit.list", "filter-module", tmp_path)
    root = ctx.root

    def boom(root, expected=None):
        raise OSError("a9-proof: the read failed")

    monkeypatch.setattr(reads, "_snapshot", boom)
    outcome, lines = _a9_run_cli(
        root, "unit.list",
        ["unit-list", "--module-id", "module-demo", "--compact"],
        tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "unit.list", "kind": "failure",
                      "site": "unit.list.read-failed",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2), "cli") == 2

def _prove_ability_unreadable_records(mini_repo: Path, tmp_path: Path,
                                      monkeypatch) -> None:
    """Unreadable canonical records fire the site (R-A9-2).

    The fixture parses cleanly and no write path stores a broken
    record, so no case input reaches the gate; the proof corrupts
    one note by direct tree surgery and asserts the witness line,
    the class and the exit.
    """
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("ability.context", "horizon", tmp_path)
    root = ctx.root
    _corrupt_note_demo(root)
    outcome, lines = _a9_run_cli(root, "ability.context",
                                 ["ability-context"],
                                 tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "ability.context", "kind": "failure",
                      "site": "ability.context.unreadable-records",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2), "cli") == 2

def _prove_ability_reasons_not_parallel(mini_repo: Path, tmp_path: Path,
                                        monkeypatch) -> None:
    """Non-parallel reason rows fire the site (R-A9-2).

    The computed horizon rows are always consistent, so no case
    input reaches the gate; the proof injects ragged rows and
    asserts the witness line, the class and the exit.
    """
    import learning_os.app.handlers.atlas as atlas
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("ability.context", "horizon", tmp_path)
    root = ctx.root

    def ragged(repo, **kwargs):
        return {"abilities": [{"reasons": ["a9-proof reason"],
                               "reason_codes": []}]}

    monkeypatch.setattr(atlas.abilities, "ability_context", ragged)
    monkeypatch.setattr(atlas, "validate_contract",
                        lambda *args, **kwargs: None)
    outcome, lines = _a9_run_cli(root, "ability.context",
                                 ["ability-context"],
                                 tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "ability.context", "kind": "failure",
                      "site": "ability.context.reasons-not-parallel",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2), "cli") == 2

def _prove_atlas_snapshot_changed(mini_repo: Path, tmp_path: Path,
                                  monkeypatch) -> None:
    """A mid-read change fires the site (race-only proof).

    A single-threaded read cannot race itself, so no case input
    reaches the gate; the proof injects the mid-read change and
    asserts the witness line, the class and the exit.
    """
    import learning_os.app.handlers.atlas as atlas
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("atlas.context", "editor-read", tmp_path)
    root = ctx.root
    calls = []

    def racing(root, expected=None):
        calls.append(expected)
        return f"a9-proof-snapshot-{len(calls)}"

    monkeypatch.setattr(atlas, "_snapshot", racing)
    outcome, lines = _a9_run_cli(root, "atlas.context",
                                 ["atlas-context", "concept-expected-value"],
                                 tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "atlas.context", "kind": "failure",
                      "site": "atlas.context.snapshot-changed",
                      "class": "WriteRefused", "exit_code": None}]
    assert exit_for(WriteRefused("a9-proof"), "cli") == 2

def _prove_edit_empty_batch_guarded(mini_repo: Path, tmp_path: Path,
                                    monkeypatch) -> None:
    """The batch guard refuses zero ids first (R-A9-3)."""
    _prove_cli_guarded(
        tmp_path, monkeypatch,
        site="plan.edit-context.empty-batch",
        cli_argv=["plan-edit-context", "unit-demo-l01", "--route-ids"],
        valid_argv=["plan-edit-context", "unit-demo-l01",
                    "--route-ids", "route-b2f1f80014860a929a3af0bc"])

def _prove_edit_one_selector_guarded(mini_repo: Path, tmp_path: Path,
                                     monkeypatch) -> None:
    """The selector guard refuses two selectors first (R-A9-3)."""
    _prove_cli_guarded(
        tmp_path, monkeypatch,
        site="plan.edit-context.one-selector",
        cli_argv=["plan-edit-context", "unit-demo-l01",
                  "--route-id", "route-b2f1f80014860a929a3af0bc",
                  "--stage-id", "stage-demo"],
        valid_argv=["plan-edit-context", "unit-demo-l01",
                    "--route-id", "route-b2f1f80014860a929a3af0bc"])

def _prove_edit_bad_stage_results(mini_repo: Path, tmp_path: Path,
                                  monkeypatch) -> None:
    """Broken stage results fire the site (R-A9-2).

    The fixture ledgers read cleanly and no step can damage them,
    so no case input reaches the gate; the proof injects the read
    failure and asserts the witness line, the class and the exit.
    """
    import learning_os.app.handlers.materials as materials
    from learning_os.app.outcomes import exit_for
    from learning_os.derive.learning_runtime import RuntimeInputError
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("plan.edit-context", "stage-entry", tmp_path)
    root = ctx.root

    def boom(*args, **kwargs):
        raise RuntimeInputError("a9-proof: the results are broken")

    monkeypatch.setattr(materials, "stage_results_for", boom)
    outcome, lines = _a9_run_cli(
        root, "plan.edit-context",
        ["plan-edit-context", "unit-demo-l01",
         "--stage-id", "stage-demo"],
        tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "plan.edit-context", "kind": "failure",
                      "site": "plan.edit-context.bad-stage-results",
                      "class": "WriteRefused", "exit_code": None}]
    assert exit_for(WriteRefused("a9-proof"), "cli") == 2

def _prove_template_bad_response(mini_repo: Path, tmp_path: Path,
                                 monkeypatch) -> None:
    """A schema-breaking template fires the site (R-A9-2).

    The producer-owned shape validates for every fixture input, so
    no case input reaches the gate; the proof injects the response
    validator's failure and asserts the witness line, the class and
    the exit.
    """
    import learning_os.app.handlers.maps as maps
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused
    from learning_os.store.contracts.json_schema import ContractValidationError

    ctx = _a9_world("plan.template", "template-yaml", tmp_path)
    root = ctx.root
    real_validate = maps.validate_contract
    calls = []

    def second_fails(*args, **kwargs):
        calls.append(args)
        if len(calls) == 1:
            return real_validate(*args, **kwargs)
        raise ContractValidationError("a9-proof: the response is invalid")

    monkeypatch.setattr(maps, "validate_contract", second_fails)
    outcome, lines = _a9_run_cli(
        root, "plan.template",
        ["plan-template", "curriculum", "--title", "Scenario Template",
         "--unit-id", "unit-demo-l01", "--module-id", "module-demo"],
        tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "plan.template", "kind": "failure",
                      "site": "plan.template.bad-response",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2), "cli") == 2

def _prove_span_placement_mismatch(mini_repo: Path, tmp_path: Path,
                                   monkeypatch) -> None:
    """A mismatched placement source fires the site (R-A9-2).

    No fixture placement links the route, so the foreign check
    fires first, and every fixture placement matches its route's
    source; no case input reaches the gate. The proof injects a
    belonging use plus a flipped loaded source by direct injection
    and asserts the witness line, the class and the exit.
    """
    import learning_os.app.handlers.materials as materials
    import learning_os.store.loading.curriculum as curriculum
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("material.span", "span", tmp_path)
    root = ctx.root
    real_expand = curriculum.expand_map

    def flipped(data, source_map, module_id, unit_id):
        expanded = real_expand(data, source_map, module_id, unit_id)
        for stage in expanded.get("stages", []):
            for resource in stage.get("resources", []):
                resource["source_id"] = "source-other"
        return expanded

    real_entry = materials._route_entry

    def belonging(ctx, routes, study_map, source_map, unit, route_id):
        entry = real_entry(ctx, routes, study_map, source_map, unit,
                           route_id)
        entry["uses"].append({"stage_id": "stage-demo",
                              "resource_index": 0})
        return entry

    monkeypatch.setattr(curriculum, "expand_map", flipped)
    monkeypatch.setattr(materials, "_route_entry", belonging)
    outcome, lines = _a9_run_cli(
        root, "material.span",
        ["material-span", "unit-demo-l01", "route-b2f1f80014860a929a3af0bc",
         "--stage", "stage-demo", "--resource-index", "0"],
        tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    # The span's outer arm stamps exit 2 onto the bare raise.
    assert lines == [{"operation": "material.span", "kind": "failure",
                      "site": "material.span.placement-source-mismatch",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof"), "cli") == 2

def _prove_span_read_failed(mini_repo: Path, tmp_path: Path,
                            monkeypatch) -> None:
    """An OSError mid-read fires the site (os-error-only proof).

    No step can arrange an unreadable record, so no case input
    reaches the gate; the proof injects the OSError and asserts the
    witness line, the class and the exit.
    """
    import learning_os.app.handlers.materials as materials
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("material.span", "span", tmp_path)
    root = ctx.root

    def boom(root, expected=None):
        raise OSError("a9-proof: the read failed")

    monkeypatch.setattr(materials, "_snapshot", boom)
    outcome, lines = _a9_run_cli(
        root, "material.span",
        ["material-span", "unit-demo-l01", "route-b2f1f80014860a929a3af0bc"],
        tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "material.span", "kind": "failure",
                      "site": "material.span.read-failed",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2), "cli") == 2

def _prove_material_context_read_failed(mini_repo: Path, tmp_path: Path,
                                        monkeypatch) -> None:
    """An OSError mid-read fires the site (os-error-only proof).

    No step can arrange an unreadable record, so no case input
    reaches the gate; the proof injects the OSError and asserts the
    witness line, the class and the exit.
    """
    import learning_os.app.handlers.materials as materials
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("material.context", "query-hit", tmp_path)
    root = ctx.root

    def boom(root, expected=None):
        raise OSError("a9-proof: the read failed")

    monkeypatch.setattr(materials, "_snapshot", boom)
    outcome, lines = _a9_run_cli(root, "material.context",
                                 ["material-context", "derivation"],
                                 tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "material.context", "kind": "failure",
                      "site": "material.context.read-failed",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2), "cli") == 2

def _prove_project_create_unknown_project(mini_repo: Path, tmp_path: Path,
                                          monkeypatch) -> None:
    """The update-only arm fires for create (R-A9-2).

    The create handler hardcodes its own capability, so no case
    input reaches the update-only arm; the proof drives the shared
    writer with the update capability by direct injection and
    asserts the witness line, the class and the exit.
    """
    import learning_os.app.handlers.platform as platform
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import NotFound

    ctx = _a9_world("project.create", "create-project", tmp_path)
    root = ctx.root
    real_write = platform._project_write

    def as_update(root, data, *, capability, operation):
        return real_write(root, data, capability="project.update",
                          operation=operation)

    monkeypatch.setattr(platform, "_project_write", as_update)
    outcome, lines = _a9_run_gateway(
        root, "project.create",
        {"project": {"schema_version": 1, "id": "project-scenario-new",
                     "type": "project", "title": "Scenario project",
                     "project_type": "software", "status": "active",
                     "root_uri": "project://scenario",
                     "objective": "Characterize project creation.",
                     "milestone_ids": [], "linked_module_ids": [],
                     "unit_ids": [], "workspace_ids": [],
                     "thematic_group_ids": [],
                     "boundaries": {"confidentiality": "private",
                                    "external_code_access": "approved"}}},
        ["project-scenario-new"], "a9-proof-create-unknown-project",
        tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "project.create", "kind": "failure",
                      "site": "project.create.unknown-project",
                      "class": "NotFound", "exit_code": None}]
    assert exit_for(NotFound("project", "project-scenario-new", []),
                    "gateway.dispatch") == 2

_PROOF_FNS.update({
    'dossier.read.unreadable-records': _prove_dossier_unreadable_records,
    'dossier.read.no-source-map': _prove_dossier_no_source_map,
    'dossier.read.bad-knowledge-map': _prove_dossier_bad_knowledge_map,
    'dossier.read.build-failed': _prove_dossier_build_failed,
    'dossier.read.stale-snapshot': _prove_dossier_stale_snapshot,
    'dossier.read.read-failed': _prove_dossier_read_failed,
    'operator.bootstrap.read-failed': _prove_bootstrap_read_failed,
    'status.read.unreadable-records': _prove_status_unreadable_records,
    'intelligence.scan.git-history': _prove_intelligence_git_history,
    'intelligence.scan.unrankable-queue': _prove_intelligence_unrankable_queue,
    'resume.read.no-resumable-stage': _prove_resume_no_resumable_stage,
    'resume.read.dossier-build-failed': _prove_resume_dossier_build_failed,
    'runtime.session.mid-read-stale': _prove_runtime_mid_read_stale,
    'capabilities.read.unreadable-payload-schema': _prove_capabilities_unreadable_schema,
    'unit.list.read-failed': _prove_unit_list_read_failed,
    'ability.context.unreadable-records': _prove_ability_unreadable_records,
    'ability.context.reasons-not-parallel': _prove_ability_reasons_not_parallel,
    'atlas.context.snapshot-changed': _prove_atlas_snapshot_changed,
    'plan.edit-context.empty-batch': _prove_edit_empty_batch_guarded,
    'plan.edit-context.one-selector': _prove_edit_one_selector_guarded,
    'plan.edit-context.bad-stage-results': _prove_edit_bad_stage_results,
    'plan.template.bad-response': _prove_template_bad_response,
    'material.span.placement-source-mismatch': _prove_span_placement_mismatch,
    'material.span.read-failed': _prove_span_read_failed,
    'material.context.read-failed': _prove_material_context_read_failed,
    'project.create.unknown-project': _prove_project_create_unknown_project,
})


def _prove_goal_invalid_ledger(mini_repo: Path, tmp_path: Path,
                               monkeypatch) -> None:
    """A schema-invalid ledger row fires the site (R-A9-2).

    The load guards accept any mapping ledger while the handler-built
    entry always validates, so no case input reaches the gate; the
    proof plants a pre-existing invalid row by direct tree surgery
    and asserts the witness line, the class and the exit.
    """
    from learning_os.app.outcomes import exit_for
    from learning_os.domain.failures import WriteRefused

    ctx = _a9_world("goal.decide", "close-goal", tmp_path)
    root = ctx.root
    ledger = root / "operations" / "goal-ledger.yaml"
    assert ledger.is_file(), "A9 proof needs the ledger to plant into"
    import yaml
    data = yaml.safe_load(ledger.read_text(encoding="utf-8"))
    data["decisions"]["goal-demo-bogus"] = {
        "state": "bogus", "decided_at": "2026-10-01"}
    ledger.write_text(yaml.safe_dump(data, sort_keys=False),
                      encoding="utf-8")
    outcome, lines = _a9_run_cli(
        root, "goal.decide", ["goal", "goal-demo-deferred", "--close"],
        tmp_path, monkeypatch)
    assert outcome.ok is False
    assert outcome.exit_code == 2
    assert lines == [{"operation": "goal.decide", "kind": "failure",
                      "site": "goal.decide.invalid-ledger",
                      "class": "WriteRefused", "exit_code": 2}]
    assert exit_for(WriteRefused("a9-proof", exit_code=2),
                    "cli") == 2

_PROOF_FNS.update({
    'goal.decide.invalid-ledger': _prove_goal_invalid_ledger,
})


def _prove_session_unreadable_ledger(mini_repo: Path, tmp_path: Path,
                                     monkeypatch) -> None:
    """Drive session-end with a damaged own ledger (A9 proof)."""
    import subprocess

    import arch_audit_hook

    import los
    from learning_os.app import pipeline as pipeline_module
    from learning_os.store.session_ledger import session_ledger as _session_ledger

    for command in (["git", "init", "-q"],
                    ["git", "config", "user.email", "tests@example.invalid"],
                    ["git", "config", "user.name", "Tests"],
                    ["git", "add", "."],
                    ["git", "commit", "-qm", "fixture baseline"]):
        subprocess.run(command, cwd=mini_repo, check=True)
    _session_ledger(mini_repo, "channel:operator").write_text(
        "{nope", encoding="utf-8")
    log = tmp_path / "audit.jsonl"
    witness = tmp_path / "sites.jsonl"
    witness.touch()
    arch_audit_hook.install(str(log))
    monkeypatch.setenv(SITE_WITNESS_ENV, str(witness))
    try:
        args = los.build_parser().parse_args(["session-end"])
        outcome = pipeline_module.run_cli(mini_repo, "session.end", args)
    finally:
        arch_audit_hook.uninstall()
    assert outcome.exit_code == 2
    lines = _read_witness_lines(witness)
    assert len(lines) == 1, lines
    assert lines[0] == {"operation": "session.end", "kind": "failure",
                        "site": "session.end.unreadable-ledger",
                        "class": "WriteRefused", "exit_code": 2}


def _prove_session_ownership_conflict(mini_repo: Path, tmp_path: Path,
                                      monkeypatch) -> None:
    """Drive session-end with an off-ledger change (A9 proof)."""
    import subprocess

    import arch_audit_hook

    import los
    from learning_os.app import pipeline as pipeline_module
    from learning_os.store.session_ledger import record_touched as _record_touched

    for command in (["git", "init", "-q"],
                    ["git", "config", "user.email", "tests@example.invalid"],
                    ["git", "config", "user.name", "Tests"],
                    ["git", "add", "."],
                    ["git", "commit", "-qm", "fixture baseline"]):
        subprocess.run(command, cwd=mini_repo, check=True)
    target = mini_repo / "work" / "notes.md"
    target.write_text("claimed\n", encoding="utf-8")
    _record_touched(mini_repo, [target])
    target.write_text("changed off-ledger\n", encoding="utf-8")
    log = tmp_path / "audit.jsonl"
    witness = tmp_path / "sites.jsonl"
    witness.touch()
    arch_audit_hook.install(str(log))
    monkeypatch.setenv(SITE_WITNESS_ENV, str(witness))
    try:
        args = los.build_parser().parse_args(
            ["session-end", "--commit-message", "conflict"])
        outcome = pipeline_module.run_cli(mini_repo, "session.end", args)
    finally:
        arch_audit_hook.uninstall()
    assert outcome.exit_code == 2
    lines = _read_witness_lines(witness)
    assert len(lines) == 1, lines
    assert lines[0] == {"operation": "session.end", "kind": "failure",
                        "site": "session.end.ownership-conflict",
                        "class": "WriteRefused", "exit_code": 2}


def _prove_session_head_changed(mini_repo: Path, tmp_path: Path,
                                monkeypatch) -> None:
    """Drive a push retry after HEAD moved (A9 proof).

    The failed push runs unwitnessed (no witness file in the
    environment yet); only the retry's refusal line is witnessed.
    """
    import subprocess

    import arch_audit_hook

    import los
    from learning_os.app import pipeline as pipeline_module
    from learning_os.store.session_ledger import record_touched as _record_touched

    for command in (["git", "init", "-q"],
                    ["git", "config", "user.email", "tests@example.invalid"],
                    ["git", "config", "user.name", "Tests"],
                    ["git", "add", "."],
                    ["git", "commit", "-qm", "fixture baseline"]):
        subprocess.run(command, cwd=mini_repo, check=True)
    target = mini_repo / "work" / "notes.md"
    target.write_text("pushed\n", encoding="utf-8")
    _record_touched(mini_repo, [target])
    subprocess.run(["git", "remote", "add", "origin", "/nonexistent"],
                   cwd=mini_repo, check=True)
    log = tmp_path / "audit.jsonl"
    witness = tmp_path / "sites.jsonl"
    witness.touch()
    arch_audit_hook.install(str(log))
    try:
        args = los.build_parser().parse_args(
            ["session-end", "--commit-message", "push me", "--push"])
        outcome = pipeline_module.run_cli(mini_repo, "session.end", args)
        assert outcome.exit_code == 128
        extra = mini_repo / "work" / "diverged.md"
        extra.write_text("diverge\n", encoding="utf-8")
        subprocess.run(["git", "add", "--", "work/diverged.md"],
                       cwd=mini_repo, check=True)
        subprocess.run(["git", "commit", "-qm", "diverge"], cwd=mini_repo,
                       check=True)
        monkeypatch.setenv(SITE_WITNESS_ENV, str(witness))
        retry_args = los.build_parser().parse_args(
            ["session-end", "--push"])
        retry = pipeline_module.run_cli(mini_repo, "session.end",
                                        retry_args)
    finally:
        arch_audit_hook.uninstall()
    assert retry.exit_code == 2
    lines = _read_witness_lines(witness)
    assert len(lines) == 1, lines
    assert lines[0] == {"operation": "session.end", "kind": "failure",
                        "site": "session.end.head-changed",
                        "class": "WriteRefused", "exit_code": 2}


_PROOF_FNS.update({
    "session.end.unreadable-ledger": _prove_session_unreadable_ledger,
    "session.end.ownership-conflict": _prove_session_ownership_conflict,
    "session.end.head-changed": _prove_session_head_changed,
})



def _prove_phase4_plan_backstop(mini_repo, tmp_path, monkeypatch, *, site):
    """Fault-inject the actual pipeline backstop, preserving its typed witness.

    These branches require I/O faults, a torn internal owner handoff, or a
    malformed internal revision value. Reviewed lineage's bytes/report
    branches are algebraically guarded by the public handler; inject only
    after proving that guard, rather than inventing an input that reaches it.
    """
    import copy
    import hashlib

    import scenario_harness as harness

    import learning_os.app.handlers.plan as plan
    import learning_os.app.handlers.synthesis as synthesis
    from learning_os.derive.semantics.lineage import LineageError

    operation, slug = site.rsplit(".", 1)
    if operation == "lineage.restamp":
        ctx = _a9_world(operation, "apply-success", tmp_path)
        doc = harness.load_case_file(CASES_DIR / f"{operation}.yaml")
        payload = copy.deepcopy(next(c for c in doc["cases"] if c["id"] == "apply-success")["request"])
        if slug in ("reviewed-bytes-changed", "reviewed-needs-report"):
            claims = ["claim-a"]
            raw = synthesis._canonical_list_bytes(claims)
            digest = synthesis.claims_list_sha256(claims)
            assert digest == "sha256:" + hashlib.sha256(raw).hexdigest()
            argv = ["lineage-restamp", "--claim-ids", *claims,
                    "--claims-sha256", digest, "--review-report", "not-used.json"]
            if slug == "reviewed-bytes-changed":
                monkeypatch.setattr(synthesis, "_canonical_list_bytes", lambda ids: b"changed\n")
            else:
                original = synthesis.apply_reviewed_envelope
                def without_report(*args, **kwargs):
                    assert kwargs["review_report"]
                    kwargs["review_report"] = None
                    return original(*args, **kwargs)
                monkeypatch.setattr(synthesis, "apply_reviewed_envelope", without_report)
            outcome, lines = _a9_run_cli(ctx.root, operation, argv, tmp_path, monkeypatch)
        elif slug == "analysis-failed":
            def bad_analysis(root):
                raise OSError("a9 analysis read fault")
            monkeypatch.setattr(synthesis, "analyze", bad_analysis)
            outcome, lines = _a9_run_cli(ctx.root, operation, ["lineage-restamp", "--check"], tmp_path, monkeypatch)
        else:
            if slug == "restamp-failed":
                def failed_claim(*args, **kwargs):
                    raise LineageError("a9 claim changed after analysis")
                monkeypatch.setattr(synthesis, "restamp_claim", failed_claim)
            else:
                def bad_revision(value):
                    raise ValueError("a9 malformed internal revision")
                monkeypatch.setattr(synthesis, "parse_expected_revisions", bad_revision)
            outcome, lines = _a9_run_gateway(ctx.root, operation, payload,
                ["file:operations/transactions/lineage.yaml"], "a9-"+slug, tmp_path, monkeypatch)
    else:
        case_id = "import-success" if operation == "module.plan.import" else "revise-success"
        ctx = _a9_world(operation, case_id, tmp_path)
        doc = harness.load_case_file(CASES_DIR / f"{operation}.yaml")
        original_case = next(c for c in doc["cases"] if c["id"] == case_id)
        payload = harness._substitute(copy.deepcopy(original_case["request"]), ctx)
        if payload.get("file"):
            payload["file"] = str((ctx.root / payload["file"]).resolve())
        if slug == "unknown-module":
            original = plan._execute_plan_import
            def changed_owner(context, request, **kwargs):
                assert context.repo().modules.get(kwargs["module_id"]) is not None
                kwargs["module_id"] = "module-nope"
                return original(context, request, **kwargs)
            monkeypatch.setattr(plan, "_execute_plan_import", changed_owner)
        else:
            def bad_revision(value):
                raise ValueError("a9 malformed internal revision")
            monkeypatch.setattr(plan, "parse_expected_revisions", bad_revision)
        outcome, lines = _a9_run_gateway(ctx.root, operation, payload,
            original_case.get("artifact_ids", []), "a9-"+slug, tmp_path, monkeypatch)
    assert outcome.exit_code == 2
    witness_exit = None if site == "lineage.restamp.bad-expected-revision" else 2
    assert lines == [{"operation": operation, "kind": "failure", "site": site,
                      "class": "NotFound" if slug == "unknown-module" else "WriteRefused", "exit_code": witness_exit}]


for _phase4_site in ('lineage.restamp.analysis-failed', 'lineage.restamp.restamp-failed', 'lineage.restamp.bad-expected-revision', 'lineage.restamp.reviewed-bytes-changed', 'lineage.restamp.reviewed-needs-report', 'module.plan.import.bad-expected-revision', 'unit.plan.revise.bad-expected-revision', 'unit.plan.revise.unknown-module'):
    _PROOF_FNS[_phase4_site] = _phase4_partial(_prove_phase4_plan_backstop, site=_phase4_site)


@pytest.mark.parametrize("site", sorted(_PROOF_FNS))
def test_proof_untriggered_site(mini_repo, tmp_path, monkeypatch, site):
    _PROOF_FNS[site](mini_repo, tmp_path, monkeypatch)
    _PROOFS[site] = True


@pytest.mark.parametrize("site", sorted(_untriggered_entries()))
def test_untriggered_entry_has_a_passing_proof(site):
    """An untriggered entry without a passing proof fails (item 9.3)."""
    assert _PROOFS.get(site) is True, (
        f"A9 {site}: untriggered entry without a passing proof — {FIX}")


@pytest.mark.parametrize(
    "operation,site", sorted(_declared_sites()),
    ids=[site for _, site in sorted(_declared_sites())])
def test_declared_site_is_witnessed_from_its_case(operation, site):
    where = _declared_sites()[(operation, site)]
    _assert_matched(operation, site, where,
                    _session_witnesses(), _cased_sites())


@pytest.mark.parametrize("operation", sorted(_excluded_ops()))
def test_excluded_name_shares_an_entry_point_handler(operation):
    """Every excluded name shares its handler with an entry point (9.1).

    The entry-point operation's own sites are covered by the
    per-site tests above, in the same session.
    """
    _assert_shares_entry_point_handler(operation, _entry_point_ops())


# --- controls ------------------------------------------------------------------------

def test_control_declared_but_unwitnessed_fails():
    with pytest.raises(AssertionError, match="unwitnessed"):
        _assert_matched("capture.create", "capture.create.empty-input",
                        "a9-control:1", set(),
                        {"capture.create.empty-input": "capture.create:x"})


def test_control_wrong_operation_fails():
    with pytest.raises(AssertionError, match="unwitnessed"):
        _assert_matched("capture.create", "capture.create.empty-input",
                        "a9-control:1",
                        {("stage.progress.update",
                          "capture.create.empty-input")},
                        {"capture.create.empty-input": "capture.create:x"})


def test_control_wrong_case_site_fails():
    with pytest.raises(AssertionError, match="no case carries"):
        _assert_matched("capture.create", "capture.create.empty-input",
                        "a9-control:1",
                        {("capture.create", "capture.create.empty-input")},
                        {"capture.create.other": "capture.create:x"})


def test_control_clean_match_passes():
    _assert_matched("capture.create", "capture.create.empty-input",
                    "a9-control:1",
                    {("capture.create", "capture.create.empty-input")},
                    {"capture.create.empty-input": "capture.create:x"},
                    attributed={("capture.create",
                                 "capture.create.empty-input")})


def test_control_witness_from_another_run_fails():
    """A session line no declaring case's own run produced fails (bh)."""
    with pytest.raises(AssertionError, match="not by the run of a case"):
        _assert_matched("capture.create", "capture.create.empty-input",
                        "a9-control:1",
                        {("capture.create", "capture.create.empty-input")},
                        {"capture.create.empty-input": "capture.create:x"},
                        attributed=set())


def test_control_wrong_case_registry_witness_fails(tmp_path, monkeypatch):
    """Use the ordinary selector: another case's registry entry cannot count."""
    import scenario_harness as harness

    site = "capture.create.empty-input"
    pair = ("capture.create", site)
    destination = str(tmp_path / "case-registry.jsonl")
    monkeypatch.setenv(SITE_WITNESS_ENV, destination)
    monkeypatch.setattr(harness, "CASE_SITE_WITNESSES", {
        (destination, "capture.create:declaring"): set(),
        (destination, "capture.create:other"): {pair},
        (destination + ".other-session", "capture.create:declaring"): {pair},
    })
    monkeypatch.setattr(__import__(__name__), "_declaring_cases", lambda: {
        site: ["capture.create:declaring"],
    })
    with pytest.raises(AssertionError, match="not by the run of a case"):
        _assert_matched("capture.create", site, "a9-control:1", {pair},
                        {site: "capture.create:declaring"}, entries={}, proofs={})
    harness.CASE_SITE_WITNESSES[(destination, "capture.create:declaring")] = {pair}
    _assert_matched("capture.create", site, "a9-control:1", {pair},
                    {site: "capture.create:declaring"}, entries={}, proofs={})


def test_control_attribution_counts_only_the_case_run(tmp_path,
                                                      monkeypatch):
    """Only lines written inside a case run are attributed to it (bh).

    A line already in the witness file (any non-harness writer, e.g. an
    A5 probe) stays in the file but is attributed to no case; the case's
    own line is appended unchanged after it.
    """
    import scenario_harness as harness

    dest = tmp_path / "sites.jsonl"
    outside = json.dumps({"operation": "route.patch", "kind": "failure",
                          "site": "route.patch.unknown-route",
                          "class": "NotFound", "exit_code": 2})
    inside = json.dumps({"operation": "project.inspect", "kind": "failure",
                         "site": "project.inspect.unknown-id",
                         "class": "WriteRefused", "exit_code": 2})
    dest.write_text(outside + "\n", encoding="utf-8")
    monkeypatch.setenv(SITE_WITNESS_ENV, str(dest))
    with harness._case_site_witnesses("project.inspect", "a9-control"):
        private = os.environ[SITE_WITNESS_ENV]
        assert private != str(dest)
        with open(private, "a", encoding="utf-8") as handle:
            handle.write(inside + "\n")
    assert os.environ[SITE_WITNESS_ENV] == str(dest)
    assert not Path(private).exists()
    assert dest.read_text(encoding="utf-8").splitlines() == [outside, inside]
    attributed = harness.CASE_SITE_WITNESSES.pop(
        (str(dest), "project.inspect:a9-control"))
    assert attributed == {("project.inspect", "project.inspect.unknown-id")}
    assert not [key for key in harness.CASE_SITE_WITNESSES
                if key[0] == str(dest)]


def test_control_failed_append_leaves_the_case_unattributed(tmp_path,
                                                            monkeypatch):
    """An unwritable witness file attributes nothing and raises nothing."""
    import scenario_harness as harness

    dest = tmp_path / "no-such-dir" / "sites.jsonl"
    monkeypatch.setenv(SITE_WITNESS_ENV, str(dest))
    with harness._case_site_witnesses("project.inspect", "a9-control-fail"):
        with open(os.environ[SITE_WITNESS_ENV], "a",
                  encoding="utf-8") as handle:
            handle.write(json.dumps({
                "operation": "project.inspect", "kind": "failure",
                "site": "project.inspect.unknown-id", "class": "WriteRefused",
                "exit_code": 2}) + "\n")
    assert os.environ[SITE_WITNESS_ENV] == str(dest)
    assert not dest.exists()
    assert (str(dest), "project.inspect:a9-control-fail") \
        not in harness.CASE_SITE_WITNESSES


def test_control_unshared_excluded_name_fails():
    with pytest.raises(AssertionError, match="shares its handler with no"):
        _assert_shares_entry_point_handler("project.inspect",
                                           {"route.patch"})


def test_control_untriggered_entry_without_proof_fails():
    entry = {"site": "a9-control.proof-missing",
             "where": "a9-control:1", "reason": "os-error-only"}
    with pytest.raises(AssertionError, match="no untriggered proof passed"):
        _assert_matched("a9-control", "a9-control.proof-missing",
                        "a9-control:1", set(), {},
                        entries={"a9-control.proof-missing": entry},
                        proofs={})


def test_control_untriggered_entry_with_failed_proof_fails():
    entry = {"site": "a9-control.proof-failed",
             "where": "a9-control:1", "reason": "race-only"}
    with pytest.raises(AssertionError, match="no untriggered proof passed"):
        _assert_matched("a9-control", "a9-control.proof-failed",
                        "a9-control:1", set(), {},
                        entries={"a9-control.proof-failed": entry},
                        proofs={"a9-control.proof-failed": False})


def test_control_site_entry_with_where_fails(tmp_path, monkeypatch):
    """A site-carrying entry that still carries ``where`` fails (OD9)."""
    import test_scenarios_zz_refusal_sites as zz
    import yaml

    cases = tmp_path / "cases"
    cases.mkdir()
    (cases / "project.inspect.yaml").write_text(yaml.safe_dump({
        "operation": "project.inspect",
        "untriggered": [{
            "site": "project.inspect.read-failed",
            "where": "tools/learning_os/app/handlers/platform.py:325",
            "reason": "os-error-only",
        }],
    }), encoding="utf-8")
    monkeypatch.setattr(zz, "CASES_DIR", cases)
    with pytest.raises(
            AssertionError,
            match="identified by its site id; remove where"):
        _untriggered_entries()


def test_control_imported_subtype_sites_are_declared():
    """The two typed append-slices misses resolve via handler globals (D5)."""
    from learning_os.domain import failures

    assert getattr(failures, "RouteNotFound", None) is None
    assert getattr(failures, "ConceptNotFound", None) is None
    declared = _declared_sites()
    assert ("ai-action.append-slices",
            "ai-action.append-slices.unknown-route") in declared
    assert ("ai-action.append-slices",
            "ai-action.append-slices.unknown-concept") in declared


def test_control_resolve_failure_accepts_only_write_refused():
    """Domain or imported failure classes resolve; nothing else does (D5)."""
    from learning_os.domain.ai_errors import (
        ConceptNotFound,
        RouteNotFound,
    )
    from learning_os.domain.failures import WriteRefused

    assert _resolve_failure("ai", "RouteNotFound") is RouteNotFound
    assert _resolve_failure("ai", "ConceptNotFound") is ConceptNotFound
    assert _resolve_failure("ai", "WriteRefused") is WriteRefused
    assert _resolve_failure("ai", "AIActionError") is None
    assert _resolve_failure("ai", "_TYPED") is None
    assert _resolve_failure("ai", "NoSuchName") is None
    assert _resolve_failure("ai", None) is None


def _a9_control_handler(source: str) -> ast.ExceptHandler:
    """The one ``except`` arm of a control snippet."""
    tree = ast.parse(source)
    handlers = tree.body[0].handlers
    assert len(handlers) == 1
    return handlers[0]


_A9_CONTROL_SERVING = {"ai-action.append-slices"}
_A9_CONTROL_ENTERED = ["ai-action.append-slices"]


def test_control_literal_assigned_site_is_recorded():
    """A literal ``exc.site`` in a typed catch names its operation (D5)."""
    node = _a9_control_handler(
        "try:\n"
        "    pass\n"
        "except RouteNotFound as exc:\n"
        '    exc.site = "ai-action.append-slices.unknown-route"\n'
        "    raise\n")
    assert _except_handler_sites(
        node, stem="ai", serving=_A9_CONTROL_SERVING,
        entered=_A9_CONTROL_ENTERED, rel="a9-control") == [
        ("ai-action.append-slices",
         "ai-action.append-slices.unknown-route", 4)]


def test_control_literal_assigned_site_needs_its_reraise():
    """A literal assignment without the bare re-raise fails (D5)."""
    node = _a9_control_handler(
        "try:\n"
        "    pass\n"
        "except RouteNotFound as exc:\n"
        '    exc.site = "ai-action.append-slices.unknown-route"\n')
    with pytest.raises(AssertionError, match="bare re-raise"):
        _except_handler_sites(
            node, stem="ai", serving=_A9_CONTROL_SERVING,
            entered=_A9_CONTROL_ENTERED, rel="a9-control")


def test_control_non_failure_catch_assigns_no_site():
    """A site assignment under a non-failure catch is not a site (D5)."""
    node = _a9_control_handler(
        "try:\n"
        "    pass\n"
        "except ValueError as exc:\n"
        '    exc.site = "ai-action.append-slices.unknown-route"\n'
        "    raise\n")
    assert _except_handler_sites(
        node, stem="ai", serving=_A9_CONTROL_SERVING,
        entered=_A9_CONTROL_ENTERED, rel="a9-control") == []


def test_control_template_assigned_site_still_resolves():
    """The template path survives the literal support unchanged (D5)."""
    node = _a9_control_handler(
        "try:\n"
        "    pass\n"
        "except RouteNotFound as exc:\n"
        '    exc.site = f"{operation}.unknown-route"\n'
        "    raise\n")
    assert _except_handler_sites(
        node, stem="ai", serving=_A9_CONTROL_SERVING,
        entered=_A9_CONTROL_ENTERED, rel="a9-control") == [
        ("ai-action.append-slices",
         "ai-action.append-slices.unknown-route", 4)]


def test_control_twin_template_keeps_called_operations():
    """A twin site counts for handlers that call the twin (R-A9-1)."""
    declared = _declared_sites()
    # _shared.py twins over their static callers.
    assert ("stage.note.write",
            "stage.note.write.unknown-stage") in declared
    assert ("path.note.write",
            "path.note.write.unknown-path") in declared
    assert ("detour.resolve",
            "detour.resolve.unknown-unit") in declared
    # In-handler templates count for their own handler.
    assert ("stage.progress.update",
            "stage.progress.update.not-active") in declared
    assert ("note.evidence.add",
            "note.evidence.add.already-recorded") in declared
    # The ai _refusal twin counts for its one caller.
    assert ("ai-action.delivery.apply",
            "ai-action.delivery.apply.binding") in declared


def test_control_twin_template_drops_never_called_operations():
    """A twin site counts for no handler that never calls it (R-A9-1)."""
    declared = _declared_sites()
    # The learner never-called _shared.py expansions.
    assert ("unit.source-selection.set",
            "unit.source-selection.set.unknown-stage") not in declared
    assert ("path.note.write",
            "path.note.write.unknown-unit") not in declared
    assert ("stage.progress.update",
            "stage.progress.update.unknown-path") not in declared
    # In-handler templates do not leak across operations.
    assert ("detour.create", "detour.create.not-active") not in declared
    assert ("note.revise",
            "note.revise.already-recorded") not in declared
    # The AI phantom .binding expansions.
    assert ("ai-action.list",
            "ai-action.list.binding") not in declared
    assert ("ai-action.append-slices",
            "ai-action.append-slices.binding") not in declared


def test_control_twin_cache_matches_uncached_analysis():
    """The cached map equals a fresh analysis of the same text (cm).

    Over every real handler file: the wrapper (which reads the path)
    and the cached helper (which keys the text) both return the same
    call/import map as the uncached analysis, and a repeated call
    returns the identical map.
    """
    for path in sorted(HANDLERS_DIR.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        fresh = _analyze_twin_source(source)
        assert _twin_callers(path) == fresh, path.name
        assert _twin_callers_cached(source) == fresh, path.name
        assert _twin_callers_cached(source) is _twin_callers_cached(
            source), path.name


def test_control_twin_cache_invalidates_on_source_change(
        tmp_path, monkeypatch):
    """Edited source changes called-site behavior (SPEC (cm)).

    The same path read before and after an edit selects the fresh
    entry: removing the handler's twin call flips
    ``_handler_calls_twin`` from True to False, and restoring the
    bytes flips it back. Not a counter check: the asserted values
    are the R-A9-1 narrowing predicate's own answers.
    """
    import test_scenarios_zz_refusal_sites as zz

    staged = tmp_path / "handlers"
    staged.mkdir()
    staged_ai = staged / "ai.py"
    original = (HANDLERS_DIR / "ai.py").read_text(encoding="utf-8")
    staged_ai.write_text(original, encoding="utf-8")
    monkeypatch.setattr(zz, "HANDLERS_DIR", staged)
    operation = "ai-action.delivery.apply"
    assert REGISTRY[operation].handler.__name__ == (
        "ai_action_apply_delivery")
    assert _handler_calls_twin(operation, "ai", "_refusal") is True
    calls, _ = _twin_callers(staged_ai)
    assert "_refusal" in calls["ai_action_apply_delivery"]
    edited = original.replace(
        "raise _refusal(exc, ctx.operation) from exc",
        "raise _refusal_gone(exc, ctx.operation) from exc").replace(
        "else _refusal(translated, ctx.operation)",
        "else _refusal_gone(translated, ctx.operation)")
    assert edited != original
    staged_ai.write_text(edited, encoding="utf-8")
    assert _handler_calls_twin(operation, "ai", "_refusal") is False
    calls, _ = _twin_callers(staged_ai)
    assert "_refusal" not in calls["ai_action_apply_delivery"]
    staged_ai.write_text(original, encoding="utf-8")
    assert _handler_calls_twin(operation, "ai", "_refusal") is True


def test_control_twin_cache_is_bounded():
    """The cache keeps at most ``_TWIN_CALLERS_CACHE_MAX`` entries (cm).

    Past the bound the oldest entry is evicted; every text — kept
    or evicted — still analyzes exactly as the uncached analysis.
    The cache is transparent, so clearing it here changes no other
    test's answers.
    """
    _TWIN_CALLERS_CACHE.clear()
    sources = [f"def f{index}():\n    g{index}()\n"
               for index in range(_TWIN_CALLERS_CACHE_MAX + 6)]
    for source in sources:
        _twin_callers_cached(source)
    assert len(_TWIN_CALLERS_CACHE) == _TWIN_CALLERS_CACHE_MAX
    assert sources[0] not in _TWIN_CALLERS_CACHE
    for source in sources:
        assert _twin_callers_cached(source) == _analyze_twin_source(
            source)


def test_witness_propagates_into_a_real_child(tmp_path, monkeypatch):
    """A real harness child refusal writes exactly one line (item 10.4).

    The same run with the variable unset is byte-identical in exit,
    stdout, stderr and effects.
    """
    import scenario_harness as harness

    doc = harness.load_case_file(CASES_DIR / "project.inspect.yaml")
    bare_case = next(item for item in doc["cases"]
                     if item["id"] == "unknown-id")
    case = {"fixture": doc.get("fixture", "rich_world"),
            "observations": doc["observations"],
            "fixture_mtime": doc.get(
                "fixture_mtime", harness.FIXTURE_MTIME_DEFAULT),
            **bare_case}
    witness = tmp_path / "sites.jsonl"
    monkeypatch.setenv(SITE_WITNESS_ENV, str(witness))
    with_witness = harness.run_case(case, "project.inspect",
                                   tmp_path / "with-witness")
    assert with_witness["exit"] == 2
    lines = witness.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1, lines
    assert json.loads(lines[0]) == {
        "operation": "project.inspect", "kind": "failure",
        "site": "project.inspect.unknown-id", "class": "WriteRefused",
        "exit_code": 2}
    # SPEC (bh): the real case run is attributed to exactly that case.
    assert harness.CASE_SITE_WITNESSES.pop(
        (str(witness), "project.inspect:unknown-id")) == {
        ("project.inspect", "project.inspect.unknown-id")}
    monkeypatch.delenv(SITE_WITNESS_ENV)
    bare = harness.run_case(case, "project.inspect", tmp_path / "bare")
    assert bare == with_witness


_DIRECT_PILOTS = [
    "ai-action.delivery.apply",
    "capture.create",
    "route.patch",
    "stage.progress.update",
]


@pytest.mark.parametrize("operation", _DIRECT_PILOTS)
def test_direct_replay_only_miss_propagates_from_a_real_child(
        operation, tmp_path, monkeypatch):
    """A real harness child replay-only miss writes one direct line (bg 1)."""
    import scenario_harness as harness

    doc = harness.load_case_file(CASES_DIR / f"{operation}.yaml")
    bare_case = next(item for item in doc["cases"]
                     if item["id"] == "replay-only-miss")
    case = {"fixture": doc.get("fixture", "rich_world"),
            "observations": doc["observations"],
            "fixture_mtime": doc.get(
                "fixture_mtime", harness.FIXTURE_MTIME_DEFAULT),
            **bare_case}
    witness = tmp_path / "sites.jsonl"
    monkeypatch.setenv(SITE_WITNESS_ENV, str(witness))
    result = harness.run_case(case, operation, tmp_path / "world")
    assert result["exit"] == 2
    lines = witness.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1, lines
    assert json.loads(lines[0]) == {
        "operation": operation, "kind": "direct-refused",
        "site": None, "code": 2}


def _run_capability_child(root: Path, name: str, envelope: dict):
    """``los capability`` in a real child (bg 1 direct-branch proof)."""
    import subprocess
    import sys

    from gateway_helpers import LOS

    return subprocess.run(
        [sys.executable, str(LOS), "--root", str(root), "capability",
         name, "--payload-file", "-"],
        input=json.dumps(envelope), capture_output=True, text=True,
        timeout=120)


def _hooked_child_env(monkeypatch, tmp_path: Path) -> Path:
    """A fresh audit log plus witness for a real hooked child (bg 1)."""
    import scenario_harness as harness

    log = tmp_path / "audit.jsonl"
    witness = tmp_path / "sites.jsonl"
    monkeypatch.setenv("LOS_ARCH_AUDIT_LOG", str(log))
    monkeypatch.setenv("LOS_ARCH_LAUNCH_TOKEN", "bg1-direct")
    monkeypatch.setenv(SITE_WITNESS_ENV, str(witness))
    pythonpath = os.environ.get("PYTHONPATH", "")
    arch_site = str(harness.ARCH_SITE)
    if arch_site not in pythonpath.split(os.pathsep):
        monkeypatch.setenv(
            "PYTHONPATH", arch_site + os.pathsep + pythonpath)
    return witness


def _assert_single_direct_line(witness: Path, operation, code: int) -> None:
    lines = witness.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1, lines
    assert json.loads(lines[0]) == {
        "operation": operation, "kind": "direct-refused",
        "site": None, "code": code}


def test_direct_capability_mismatch_emits_in_a_real_child(
        mini_repo, tmp_path, monkeypatch):
    """A real child V2 capability mismatch writes one direct line (bg 1)."""
    from gateway_helpers import approved_v2_envelope

    witness = _hooked_child_env(monkeypatch, tmp_path)
    envelope = approved_v2_envelope(
        mini_repo, capability="stage.progress.update",
        payload={"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
                 "status": "active"},
        artifact_ids=[], idempotency_key="bg1-direct-mismatch")
    proc = _run_capability_child(mini_repo, "route.patch", envelope)
    assert proc.returncode == 2, proc.stderr[-500:]
    _assert_single_direct_line(
        witness, "stage.progress.update", 2)


def test_direct_unknown_capability_emits_in_a_real_child(
        mini_repo, tmp_path, monkeypatch):
    """A real child V2 unknown capability writes one direct line (bg 1)."""
    from gateway_helpers import approved_v2_envelope

    witness = _hooked_child_env(monkeypatch, tmp_path)
    envelope = approved_v2_envelope(
        mini_repo, capability="nope.unknown-capability",
        payload={}, artifact_ids=[],
        idempotency_key="bg1-direct-unknown")
    proc = _run_capability_child(
        mini_repo, "nope.unknown-capability", envelope)
    assert proc.returncode == 2, proc.stderr[-500:]
    _assert_single_direct_line(
        witness, "nope.unknown-capability", 2)


def test_direct_forbidden_gesture_emits_in_a_real_child(
        mini_repo, tmp_path, monkeypatch):
    """A real child forbidden gesture writes one direct line (bg 1)."""
    from gateway_helpers import approved_v2_envelope

    from learning_os.store.contracts.gateway import intent_sha256

    witness = _hooked_child_env(monkeypatch, tmp_path)
    envelope = approved_v2_envelope(
        mini_repo, capability="route.patch",
        payload={"unit_id": "unit-demo-l01"}, artifact_ids=[],
        idempotency_key="bg1-direct-gesture")
    envelope["approval"]["kind"] = "direct-user-gesture"
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    proc = _run_capability_child(mini_repo, "route.patch", envelope)
    assert proc.returncode == 2, proc.stderr[-500:]
    _assert_single_direct_line(witness, "route.patch", 2)


def test_direct_snapshot_mismatch_emits_in_a_real_child(
        mini_repo, tmp_path, monkeypatch):
    """A real child snapshot mismatch writes one direct line (bg 1)."""
    from gateway_helpers import approved_v2_envelope

    witness = _hooked_child_env(monkeypatch, tmp_path)
    envelope = approved_v2_envelope(
        mini_repo, capability="stage.progress.update",
        payload={"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
                 "status": "active"},
        artifact_ids=[], idempotency_key="bg1-direct-snapshot",
        expected_snapshot="sha256:" + "0" * 64)
    proc = _run_capability_child(
        mini_repo, "stage.progress.update", envelope)
    assert proc.returncode == 3, proc.stderr[-500:]
    _assert_single_direct_line(
        witness, "stage.progress.update", 3)


def test_control_v1_envelope_refuses_at_admission_without_a_line(
        mini_repo, tmp_path, monkeypatch):
    """A schema-less envelope never reaches the V1 direct arms (bg 1).

    Admission requires ``schema_version: 2`` and re-raises for older
    shapes, so the V1 audit sites are unreachable defense in depth:
    instrumented per SPEC, with no triggerable line.
    """
    from gateway_helpers import approved_v2_envelope

    witness = _hooked_child_env(monkeypatch, tmp_path)
    envelope = approved_v2_envelope(
        mini_repo, capability="stage.progress.update",
        payload={"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
                 "status": "active"},
        artifact_ids=[], idempotency_key="bg1-direct-v1")
    del envelope["schema_version"]
    proc = _run_capability_child(
        mini_repo, "stage.progress.update", envelope)
    assert proc.returncode == 2, proc.stderr[-500:]
    assert "schema_version 2 required" in proc.stderr
    assert not witness.exists()


def test_control_direct_audit_helper_emits_the_exact_line(
        tmp_path, monkeypatch):
    """The helper plus hook write exactly the (bg) 1 line shape."""
    import arch_audit_hook

    from learning_os.app.pipeline import _audit_direct_refused

    log = tmp_path / "audit.jsonl"
    witness = tmp_path / "sites.jsonl"
    witness.touch()
    arch_audit_hook.install(str(log))
    monkeypatch.setenv(SITE_WITNESS_ENV, str(witness))
    try:
        _audit_direct_refused("route.patch", 2)
        _audit_direct_refused("route.patch", 3)
    finally:
        arch_audit_hook.uninstall()
    assert _read_witness_lines(witness) == [
        {"operation": "route.patch", "kind": "direct-refused",
         "site": None, "code": 2},
        {"operation": "route.patch", "kind": "direct-refused",
         "site": None, "code": 3}]
    assert "learningos.refusal" not in log.read_text(encoding="utf-8")


def test_control_process_without_hook_writes_no_file(mini_repo, tmp_path,
                                                     monkeypatch):
    """A process with no hook writes no file (item 10.4)."""
    from repo_builders import run_los

    witness = tmp_path / "sites.jsonl"
    monkeypatch.setenv(SITE_WITNESS_ENV, str(witness))
    monkeypatch.delenv("LOS_ARCH_AUDIT_LOG", raising=False)
    monkeypatch.setenv(
        "PYTHONPATH",
        os.pathsep.join(part for part in
                        os.environ.get("PYTHONPATH", "").split(os.pathsep)
                        if part and "arch_site" not in part))
    refused = run_los(mini_repo, "inspect", "nope-id")
    assert refused.returncode == 2
    assert "record not found: nope-id" in refused.stderr
    assert not witness.exists()


def test_control_failed_witness_write_is_swallowed(tmp_path, monkeypatch):
    """An unwritable witness file perturbs nothing (item 10.2)."""
    import sys

    import arch_audit_hook

    log = tmp_path / "audit.jsonl"
    arch_audit_hook.install(str(log))
    try:
        monkeypatch.setenv(
            SITE_WITNESS_ENV,
            str(tmp_path / "no-such-dir" / "sites.jsonl"))
        sys.audit("learningos.refusal", "project.inspect", "failure",
                  "project.inspect.unknown-id", "WriteRefused", 2)
    finally:
        arch_audit_hook.uninstall()
    assert not (tmp_path / "no-such-dir").exists()


def test_control_pipeline_witness_adds_no_a2_entry():
    """The witness transport adds no A2 census entry (item 10.4)."""
    import test_arch_writes
    import yaml

    current, _ = test_arch_writes._collect_static()
    recorded_entries = yaml.safe_load(
        test_arch_writes.RATCHETS_PATH.read_text(encoding="utf-8"))[
            "checks"].get(test_arch_writes.RULE, [])
    recorded = {entry["signature"]: entry["count"]
                for entry in recorded_entries}
    rel = "tools/learning_os/app/pipeline.py"
    for signature, count in sorted(current.items()):
        if not signature.startswith(rel + "::"):
            continue
        assert count <= recorded.get(signature, 0), (
            f"A9 {signature}: the witness transport adds an A2 entry "
            f"(current {count}, recorded "
            f"{recorded.get(signature, 0)}) — {FIX}")


def test_control_null_site_lines_are_not_read(tmp_path, monkeypatch):
    """A9 reads only lines with a non-null site (item 8.1)."""
    witness = tmp_path / "sites.jsonl"
    witness.write_text(
        json.dumps({"operation": "route.patch", "kind": "commit-refused",
                    "site": None, "code": 2})
        + "\n"
        + json.dumps({"operation": "route.patch", "kind": "failure",
                      "site": None, "class": "WriteRefused",
                      "exit_code": None})
        + "\n"
        + json.dumps({"operation": "route.patch", "kind": "direct-refused",
                      "site": None, "code": 2})
        + "\n",
        encoding="utf-8")
    monkeypatch.setenv(SITE_WITNESS_ENV, str(witness))
    assert _session_witnesses() == set()


def test_control_malformed_witness_line_fails(tmp_path, monkeypatch):
    """A line outside the item 8.1 shapes fails the read."""
    witness = tmp_path / "sites.jsonl"
    witness.write_text(
        json.dumps({"operation": "project.inspect",
                    "site": "project.inspect.unknown-id"})
        + "\n",
        encoding="utf-8")
    monkeypatch.setenv(SITE_WITNESS_ENV, str(witness))
    with pytest.raises(AssertionError, match="not an item 8.1 refusal line"):
        _session_witnesses()


def test_control_failed_append_is_reported_unwitnessed(mini_repo, tmp_path,
                                                       monkeypatch):
    """An unwritable witness file perturbs nothing; the match reports it."""
    from repo_builders import run_los

    monkeypatch.setenv(SITE_WITNESS_ENV,
                       str(tmp_path / "no-such-dir" / "sites.jsonl"))
    refused = run_los(mini_repo, "inspect", "nope-id")
    assert refused.returncode == 2
    assert "record not found: nope-id" in refused.stderr
    with pytest.raises(AssertionError, match="unwitnessed"):
        _assert_matched("project.inspect", "project.inspect.unknown-id",
                        "a9-control:1", set(),
                        {"project.inspect.unknown-id": "project.inspect:unknown-id"})


def test_control_diagnostic_line_never_supplies_a_site(tmp_path, monkeypatch):
    witness = tmp_path / "sites.jsonl"
    diagnostic = {"operation": "backup.verify",
                  "kind": "diagnostic-failure", "site": None, "code": 1}
    witness.write_text(json.dumps(diagnostic) + "\n", encoding="utf-8")
    monkeypatch.setenv(SITE_WITNESS_ENV, str(witness))
    assert _session_witnesses() == set()
    genuine = {"operation": "ability.context", "kind": "failure",
               "site": "ability.context.bad-limit", "class": "WriteRefused",
               "exit_code": 2}
    with witness.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(genuine) + "\n")
    assert _session_witnesses() == {
        ("ability.context", "ability.context.bad-limit")}


@pytest.mark.parametrize("mutation", [
    {"code": True}, {"code": 1.0}, {"code": 0}, {"code": 2},
    {"code": None}, {"site": "invented.site"}, {"class": None},
    {"kind": "unknown-diagnostic-kind"},
])
def test_control_malformed_diagnostic_line_fails(tmp_path, monkeypatch,
                                                mutation):
    witness = tmp_path / "sites.jsonl"
    record = {"operation": "backup.verify", "kind": "diagnostic-failure",
              "site": None, "code": 1, **mutation}
    witness.write_text(json.dumps(record) + "\n", encoding="utf-8")
    monkeypatch.setenv(SITE_WITNESS_ENV, str(witness))
    with pytest.raises(AssertionError, match="not an item 8.1 refusal line"):
        _session_witnesses()


def test_control_command_line_never_supplies_a_site(tmp_path, monkeypatch):
    """A command-failure line witnesses no business refusal site (D-9)."""
    witness = tmp_path / "sites.jsonl"
    command = {"operation": "session.end",
               "kind": "command-failure", "site": None, "code": 128}
    witness.write_text(json.dumps(command) + "\n", encoding="utf-8")
    monkeypatch.setenv(SITE_WITNESS_ENV, str(witness))
    assert _session_witnesses() == set()
    genuine = {"operation": "session.end", "kind": "failure",
               "site": "session.end.nothing-touched",
               "class": "WriteRefused", "exit_code": 2}
    with witness.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(genuine) + "\n")
    assert _session_witnesses() == {
        ("session.end", "session.end.nothing-touched")}


@pytest.mark.parametrize("mutation", [
    {"code": True}, {"code": 128.0}, {"code": "128"}, {"code": 0},
    {"code": None}, {"site": "invented.site"},
    {"site": "session.end.nothing-touched"}, {"class": None},
    {"class": "WriteRefused"}, {"kind": "unknown-command-kind"},
])
def test_control_malformed_command_line_fails(tmp_path, monkeypatch,
                                              mutation):
    witness = tmp_path / "sites.jsonl"
    record = {"operation": "session.end", "kind": "command-failure",
              "site": None, "code": 128, **mutation}
    witness.write_text(json.dumps(record) + "\n", encoding="utf-8")
    monkeypatch.setenv(SITE_WITNESS_ENV, str(witness))
    with pytest.raises(AssertionError, match="not an item 8.1 refusal line"):
        _session_witnesses()


def test_control_command_line_without_code_fails(tmp_path, monkeypatch):
    """A command line without a code is not an item 8.1 line (D-9)."""
    witness = tmp_path / "sites.jsonl"
    record = {"operation": "session.end", "kind": "command-failure",
              "site": None}
    witness.write_text(json.dumps(record) + "\n", encoding="utf-8")
    monkeypatch.setenv(SITE_WITNESS_ENV, str(witness))
    with pytest.raises(AssertionError, match="not an item 8.1 refusal line"):
        _session_witnesses()
