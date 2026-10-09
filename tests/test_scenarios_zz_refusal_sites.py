"""Every declared refusal site is witnessed from its case (SPEC §3.3 A9).

``ops/pipeline.py`` emits one ``learningos.refusal`` audit event per
refusal it produces, and the audit hook appends one item 8.1 JSON
line per event while ``LOS_SITE_WITNESS_FILE`` is set (SPEC (bf)
item 10; a session fixture owns that file). This module runs after
every other ``test_scenarios*`` file, so in a full or ``-k
scenarios`` run it matches each statically declared site to both a
runtime witness line with a non-null site and a case whose
``expect.site`` equals it. An empty witness file skips locally and
fails under CI.
"""

from __future__ import annotations

import ast
import json
import os
from functools import lru_cache
from pathlib import Path

import pytest
from arch_audit_hook import SITE_WITNESS_ENV

import learning_os.ops.handlers  # noqa: F401  (registration side effect)
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


@lru_cache(maxsize=1)
def _entry_point_ops() -> frozenset[str]:
    """Registered operations with a runtime entry point (item 9.1).

    An operation that is the ``_operation`` default of a generated
    CLI subcommand, or a catalog command the gateway dispatches.
    """
    import los
    from learning_os.contracts.capability_catalog import command_definitions
    from learning_os.contracts.payloads import subparsers

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


def _declared_sites() -> dict[tuple[str, str], str]:
    """``(operation, site)`` -> ``"rel:line"`` for every declared site.

    A literal ``site="..."`` or an operation template on a failure
    raise, the capture ``exc.site`` assignment beside its bare
    re-raise, or an operation template assigned to a ``site``
    variable passed as ``site=``. Templates resolve over the raising
    module's serving operations that have a runtime entry point
    (item 9.1); literals name their operation as written.
    """
    from learning_os.domain import failures

    def is_failure(name: object) -> bool:
        cls = getattr(failures, name, None) if isinstance(name, str) else None
        return (isinstance(cls, type)
                and issubclass(cls, failures.WriteRefused))

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
                for operation in entered:
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
                        for operation in entered:
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
                    for operation in entered:
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
    if kind == "commit-refused":
        return (set(record) == {"operation", "kind", "site", "code"}
                and record["site"] is None
                and isinstance(record["code"], int))
    return False


def _session_witnesses() -> set[tuple[str, str]]:
    """The session's ``(operation, site)`` witnesses.

    Reads only lines with a non-null ``site`` (SPEC (bf) item 8.1);
    null-site lines (commit refusals, siteless raises, admission
    refusals) are not sites. An empty file means no scenario ran in
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


#: Untriggered reasons (SPEC (bf) item 9.3, fixed vocabulary).
_UNTRIGGERED_REASONS = frozenset({
    "guarded-before-handler", "os-error-only", "race-only",
})

#: Sites whose untriggered proof passed in this session (item 9.3).
#: Proof tests run before the matching tests and record here.
_PROOFS: dict[str, bool] = {}


def _untriggered_entries() -> dict[str, dict]:
    """Site -> entry for site-carrying ``untriggered`` entries (item 9.3).

    Entries without a site are legacy documentation and A9 ignores
    them. A site entry must name its operation's file, a declared
    site at its declared raise line, and a fixed-vocabulary reason.
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
            where = entry.get("where")
            assert where == declared_where[site], (
                f"A9 {label}: where {where!r} is not the declared raise "
                f"{declared_where[site]!r} — {FIX}")
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
                    proofs: dict[str, bool] | None = None) -> None:
    """The declared site has its witness and its case, or its proof.

    An uncased site is accepted only through an untriggered entry
    whose proof passed in this session (item 9.3); the proof stands
    in for both the session witness and the case.
    """
    if entries is None:
        entries = _untriggered_entries()
    if proofs is None:
        proofs = _PROOFS
    if _proof_accepts(site, entries, proofs):
        return
    problems = []
    if (operation, site) not in witnesses:
        others = sorted({op for op, st in witnesses if st == site})
        detail = (f" (witnessed only as {others})" if others
                  else " (no witness at all)")
        problems.append(f"unwitnessed{detail}")
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

    import learning_os.ops.handlers.platform as platform
    import los
    from learning_os.domain.failures import WriteRefused
    from learning_os.ops import pipeline as pipeline_module
    from learning_os.ops.outcomes import exit_for

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
        outcome = pipeline_module.run_cli(mini_repo, "cli.inspect", args)
    finally:
        arch_audit_hook.uninstall()
    assert outcome.exit_code == 2
    lines = _read_witness_lines(witness)
    assert len(lines) == 1, lines
    assert lines[0] == {"operation": "cli.inspect", "kind": "failure",
                        "site": "cli.inspect.read-failed",
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

    import learning_os.ops._legacy_plumbing as plumbing
    import learning_os.ops.handlers.platform as platform
    import los
    from learning_os.domain.failures import StaleSnapshot
    from learning_os.ops import pipeline as pipeline_module
    from learning_os.ops.outcomes import exit_for

    log = tmp_path / "audit.jsonl"
    witness = tmp_path / "sites.jsonl"
    witness.touch()
    arch_audit_hook.install(str(log))
    monkeypatch.setenv(SITE_WITNESS_ENV, str(witness))

    def flapping(root, expected=None):
        if expected is None:
            return plumbing._snapshot(root)
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
        outcome = pipeline_module.run_cli(mini_repo, "cli.inspect", args)
    finally:
        arch_audit_hook.uninstall()
    assert outcome.exit_code == 3
    lines = _read_witness_lines(witness)
    assert len(lines) == 1, lines
    assert lines[0] == {"operation": "cli.inspect", "kind": "failure",
                        "site": "cli.inspect.stale-snapshot",
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
    from learning_os.contracts.capability_catalog import command_definitions
    from learning_os.diagnostics import tracer as diag_tracer
    from learning_os.diagnostics.store import bind_store as _bind_diag_store
    from learning_os.domain.failures import WriteRefused
    from learning_os.ops import pipeline as pipeline_module
    from learning_os.ops.legacy import prepare_dispatch

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
    "cli.inspect.read-failed": _prove_cli_read_failed,
    "cli.inspect.stale-snapshot": _prove_cli_stale_snapshot,
    "stage.progress.update.unknown-status":
        _prove_stage_unknown_status_guarded,
}


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
                    {"capture.create.empty-input": "capture.create:x"})


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


def test_witness_propagates_into_a_real_child(tmp_path, monkeypatch):
    """A real harness child refusal writes exactly one line (item 10.4).

    The same run with the variable unset is byte-identical in exit,
    stdout, stderr and effects.
    """
    import scenario_harness as harness

    doc = harness.load_case_file(CASES_DIR / "cli.inspect.yaml")
    bare_case = next(item for item in doc["cases"]
                     if item["id"] == "unknown-id")
    case = {"fixture": doc.get("fixture", "rich_world"),
            "observations": doc["observations"],
            "fixture_mtime": doc.get(
                "fixture_mtime", harness.FIXTURE_MTIME_DEFAULT),
            **bare_case}
    witness = tmp_path / "sites.jsonl"
    monkeypatch.setenv(SITE_WITNESS_ENV, str(witness))
    with_witness = harness.run_case(case, "cli.inspect",
                                   tmp_path / "with-witness")
    assert with_witness["exit"] == 2
    lines = witness.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1, lines
    assert json.loads(lines[0]) == {
        "operation": "cli.inspect", "kind": "failure",
        "site": "cli.inspect.unknown-id", "class": "WriteRefused",
        "exit_code": 2}
    monkeypatch.delenv(SITE_WITNESS_ENV)
    bare = harness.run_case(case, "cli.inspect", tmp_path / "bare")
    assert bare == with_witness


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
        sys.audit("learningos.refusal", "cli.inspect", "failure",
                  "cli.inspect.unknown-id", "WriteRefused", 2)
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
    rel = "tools/learning_os/ops/pipeline.py"
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
        + "\n",
        encoding="utf-8")
    monkeypatch.setenv(SITE_WITNESS_ENV, str(witness))
    assert _session_witnesses() == set()


def test_control_malformed_witness_line_fails(tmp_path, monkeypatch):
    """A line outside the item 8.1 shapes fails the read."""
    witness = tmp_path / "sites.jsonl"
    witness.write_text(
        json.dumps({"operation": "cli.inspect",
                    "site": "cli.inspect.unknown-id"})
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
        _assert_matched("cli.inspect", "cli.inspect.unknown-id",
                        "a9-control:1", set(),
                        {"cli.inspect.unknown-id": "cli.inspect:unknown-id"})
