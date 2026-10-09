"""Every declared refusal site is witnessed from its case (SPEC §3.3 A9).

``ops/pipeline.py`` appends one ``{"operation", "site"}`` line per
handled failure with a non-empty site while ``LOS_SITE_WITNESS_FILE``
is set (a session fixture owns that file). This module runs after
every other ``test_scenarios*`` file, so in a full or ``-k scenarios``
run it matches each statically declared site to both a runtime
witness and a case whose ``expect.site`` equals it. An empty witness
file skips locally and fails under CI.
"""

from __future__ import annotations

import ast
import json
import os
from pathlib import Path

import pytest

import learning_os.ops.handlers  # noqa: F401  (registration side effect)
from learning_os.ops.pipeline import SITE_WITNESS_ENV
from learning_os.ops.registry import REGISTRY

ROOT = Path(__file__).resolve().parent.parent
CASES_DIR = ROOT / "tests/scenarios/cases"
HANDLERS_DIR = ROOT / "tools/learning_os/ops/handlers"

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


def _declared_sites() -> dict[tuple[str, str], str]:
    """``(operation, site)`` -> ``"rel:line"`` for every declared site.

    A literal ``site="..."`` or an operation template on a failure
    raise, the capture ``exc.site`` assignment beside its bare
    re-raise, or an operation template assigned to a ``site``
    variable passed as ``site=``. Templates resolve over the raising
    module's serving operations.
    """
    from learning_os.domain import failures

    def is_failure(name: object) -> bool:
        cls = getattr(failures, name, None) if isinstance(name, str) else None
        return (isinstance(cls, type)
                and issubclass(cls, failures.WriteRefused))

    serving = _serving_ops()
    declared: dict[tuple[str, str], str] = {}

    def record(operation: str, site: str, rel: str, lineno: int) -> None:
        declared.setdefault((operation, site), f"{rel}:{lineno}")

    for path in sorted(HANDLERS_DIR.glob("*.py")):
        if path.name == "__init__.py":
            continue
        rel = path.relative_to(ROOT).as_posix()
        assert serving.get(path.name), f"A9 {rel} serves nothing — {FIX}"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call):
                call = node.exc
                if not (isinstance(call.func, ast.Name)
                        and is_failure(call.func.id)):
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
                    f"A9 {rel}:{node.lineno}: unresolvable site form — {FIX}")
                for operation in sorted(serving[path.name]):
                    for slug in slugs:
                        record(operation, f"{operation}.{slug}", rel,
                               node.lineno)
            if isinstance(node, ast.ExceptHandler) and isinstance(
                    node.type, ast.Name) and is_failure(node.type.id):
                for stmt in ast.walk(node):
                    if not isinstance(stmt, ast.Assign):
                        continue
                    for target in stmt.targets:
                        if not (isinstance(target, ast.Attribute)
                                and target.attr == "site"
                                and isinstance(target.value, ast.Name)
                                and target.value.id == node.name):
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
                        for operation in sorted(serving[path.name]):
                            for slug in slugs:
                                record(operation, f"{operation}.{slug}", rel,
                                       stmt.lineno)
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
            for stmt in assigns:
                for slug in _operation_templates(stmt.value):
                    for operation in sorted(serving[path.name]):
                        record(operation, f"{operation}.{slug}", rel,
                               stmt.lineno)
    return declared


# --- the match ---------------------------------------------------------------------

def _session_witnesses() -> set[tuple[str, str]]:
    """The session's ``(operation, site)`` witnesses.

    An empty file means no scenario ran in this session: skip
    locally, fail when CI is set.
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
        assert (isinstance(record, dict)
                and set(record) == {"operation", "site"}
                and isinstance(record["operation"], str)
                and record["operation"]
                and isinstance(record["site"], str)
                and record["site"]), (
            f"A9 witness line {lineno} is not an operation/site line — {FIX}")
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


def _assert_matched(operation: str, site: str, where: str,
                    witnesses: set[tuple[str, str]],
                    cased: dict[str, str]) -> None:
    """The declared site has its witness and its case (both required)."""
    problems = []
    if (operation, site) not in witnesses:
        others = sorted({op for op, st in witnesses if st == site})
        detail = (f" (witnessed only as {others})" if others
                  else " (no witness at all)")
        problems.append(f"unwitnessed{detail}")
    if site not in cased:
        problems.append("no case carries this expect.site")
    assert not problems, (
        f"A9 {operation}::{site} [{where}]: "
        f"{'; '.join(problems)} — {FIX}")


@pytest.mark.parametrize(
    "operation,site", sorted(_declared_sites()),
    ids=[site for _, site in sorted(_declared_sites())])
def test_declared_site_is_witnessed_from_its_case(operation, site):
    where = _declared_sites()[(operation, site)]
    _assert_matched(operation, site, where,
                    _session_witnesses(), _cased_sites())


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
                    {"capture.create.empty-input": "capture.create:x"})


def test_witness_propagates_into_a_real_child(mini_repo, tmp_path,
                                              monkeypatch):
    """A real child refusal appends; without the variable bytes match."""
    from repo_builders import run_los

    witness = tmp_path / "sites.jsonl"
    monkeypatch.setenv(SITE_WITNESS_ENV, str(witness))
    with_witness = run_los(mini_repo, "inspect", "nope-id")
    assert with_witness.returncode == 2
    lines = witness.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1, lines
    assert json.loads(lines[0]) == {"operation": "cli.inspect",
                                    "site": "cli.inspect.unknown-id"}
    monkeypatch.delenv(SITE_WITNESS_ENV)
    bare = run_los(mini_repo, "inspect", "nope-id")
    assert (bare.returncode, bare.stdout, bare.stderr) == (
        with_witness.returncode, with_witness.stdout, with_witness.stderr)


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
        _assert_matched("cli.inspect", "cli.inspect.unknown-id",
                        "a9-control:1", set(),
                        {"cli.inspect.unknown-id": "cli.inspect:unknown-id"})
