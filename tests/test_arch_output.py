"""Refusal output shape and exit mapping for registered operations (SPEC §3.3 A7).

For every registered operation, on its scenario cases: the real
generated parser accepts ``--json`` for its subcommand; every gateway
refusal recording's whole stdout validates against the resultV2
envelope and its error member against that schema's error definition;
every CLI refusal recording's stdout object validates against the
CLI-error schema; and the recorded exit equals
``ops.outcomes.exit_for`` for the failure class derived from the
case's typed ``expect.site`` and the handler's raise at that site.
Unregistered operations are baselined ``operation::*`` exceptions,
the same derivation as A5, asserted equal in both directions.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

import learning_os.ops.handlers  # noqa: F401  (registration side effect)
from learning_os.ops.registry import REGISTRY

ROOT = Path(__file__).resolve().parent.parent
CASES_DIR = ROOT / "tests/scenarios/cases"
HANDLERS_DIR = ROOT / "tools/learning_os/ops/handlers"
RATCHETS_PATH = ROOT / "tests/architecture/ratchets.yaml"
REQUESTS_DIR = ROOT / "system/schema/requests"
RECORDED_DIR = ROOT / "tests/scenarios/recorded"
ENVELOPE_SCHEMA_PATH = ROOT / "system/schema/capability-envelope.schema.json"
CLI_ERROR_SCHEMA_PATH = ROOT / "tests/architecture/cli-error.schema.json"

CHECK_ID = "A7-output"
FIX = "Render through adapters.cli (PLAN D16)."


# --- refusal units ------------------------------------------------------------

def _recorded(operation: str, case_id: str) -> dict:
    return json.loads(
        (RECORDED_DIR / operation / f"{case_id}.json").read_text(
            encoding="utf-8"))


def _refusal_units(operation: str) -> list[tuple[str, int | None, str,
                                                str | None, int, str]]:
    """``(case, step, transport, site, exit, stdout)`` per own-operation refusal.

    A refusal unit is an own-operation run whose recorded exit is not 0:
    a single case, or a sequence step whose effective operation is the
    file's own. Steps carry no ``expect.site``; their site is None.
    """
    import scenario_harness as harness

    doc = harness.load_case_file(CASES_DIR / f"{operation}.yaml")
    units = []
    for case in doc.get("cases", []):
        recorded = _recorded(operation, case["id"])
        if case.get("kind") == "sequence":
            for index, step in enumerate(case.get("steps", [])):
                if step.get("operation", operation) != operation:
                    continue
                result = recorded["steps"][index]
                if result["exit"] != 0:
                    units.append((case["id"], index, step["transport"], None,
                                  result["exit"], result["stdout"]))
        elif recorded["exit"] != 0:
            units.append((case["id"], None, case["transport"],
                          (case.get("expect") or {}).get("site"),
                          recorded["exit"], recorded["stdout"]))
    return units


def _all_refusal_units() -> list[tuple[str, str, int | None, str,
                                       str | None, int, str]]:
    units = []
    for operation in sorted(REGISTRY):
        units.extend((operation, *unit)
                     for unit in _refusal_units(operation))
    return units


def _unit_id(unit) -> str:
    operation, case_id, step, *_ = unit
    return (f"{operation}::{case_id}" if step is None
            else f"{operation}::{case_id}::step{step}")


# --- the static site -> raise map ----------------------------------------------

class _Unresolvable(Exception):
    """No static raise carries this site (a pinned exit gap)."""


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
    assert shared_ops, "A7 _shared.py serves no registered operation"
    serving["_shared.py"] = shared_ops
    return serving


def _template_slug(value: ast.AST) -> str | None:
    """The slug of ``f"{ctx.operation}.<slug>"``, else None (fail closed)."""
    if not isinstance(value, ast.JoinedStr) or len(value.values) != 2:
        return None
    formatted, rest = value.values
    if (not isinstance(formatted, ast.FormattedValue)
            or formatted.conversion != -1
            or formatted.format_spec is not None):
        return None
    target = formatted.value
    if not (isinstance(target, ast.Attribute)
            and target.attr == "operation"
            and isinstance(target.value, ast.Name)
            and target.value.id == "ctx"):
        return None
    if not (isinstance(rest, ast.Constant) and isinstance(rest.value, str)
            and rest.value.startswith(".") and "." not in rest.value[1:]
            and rest.value[1:]):
        return None
    return rest.value[1:]


def _site_raises() -> dict[str, tuple[str, int | None, str, int]]:
    """Declared site -> ``(class, exit_code, file, line)``.

    A literal ``site="..."`` on a failure raise, an
    ``f"{ctx.operation}.<slug>"`` resolved over the raising module's
    serving operations, or the capture ``bad-file`` form: a site
    assigned to the in-flight ``WriteRefused`` beside its literal
    ``exit_code`` and bare re-raise. Duplicate raises of one site must
    agree on class and exit; anything else is unresolvable.
    """
    from learning_os.domain import failures

    serving = _serving_ops()
    resolved: dict[str, tuple[str, int | None, str, int]] = {}

    def record(site: str, class_name: str, exit_code: int | None,
               rel: str, lineno: int) -> None:
        if site in resolved:
            assert resolved[site][:2] == (class_name, exit_code), (
                f"A7 {site}: conflicting raises "
                f"({resolved[site][2]}:{resolved[site][3]} vs "
                f"{rel}:{lineno}) — {FIX}")
            return
        resolved[site] = (class_name, exit_code, rel, lineno)

    for path in sorted(HANDLERS_DIR.glob("*.py")):
        if path.name == "__init__.py":
            continue
        rel = path.relative_to(ROOT).as_posix()
        assert serving.get(path.name), f"A7 {rel} serves nothing — {FIX}"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call):
                call = node.exc
                if not isinstance(call.func, ast.Name):
                    continue
                cls = getattr(failures, call.func.id, None)
                if not (isinstance(cls, type)
                        and issubclass(cls, failures.WriteRefused)):
                    continue
                site_kw = next((kw for kw in call.keywords
                                if kw.arg == "site"), None)
                if site_kw is None:
                    continue
                exit_kw = next((kw for kw in call.keywords
                                if kw.arg == "exit_code"), None)
                exit_code = None
                if exit_kw is not None:
                    assert isinstance(exit_kw.value, ast.Constant), (
                        f"A7 {rel}:{node.lineno}: non-literal exit_code"
                        f" — {FIX}")
                    exit_code = exit_kw.value.value
                    assert exit_code is None or isinstance(exit_code, int), (
                        f"A7 {rel}:{node.lineno}: exit_code {exit_code!r}"
                        f" — {FIX}")
                if isinstance(site_kw.value, ast.Constant):
                    site = site_kw.value.value
                    assert isinstance(site, str) and any(
                        site == op or site.startswith(op + ".")
                        for op in serving[path.name]), (
                        f"A7 {rel}:{node.lineno}: site {site!r} names no"
                        f" served operation — {FIX}")
                    record(site, call.func.id, exit_code, rel, node.lineno)
                    continue
                slug = _template_slug(site_kw.value)
                assert slug is not None, (
                    f"A7 {rel}:{node.lineno}: unresolvable site form — {FIX}")
                for operation in sorted(serving[path.name]):
                    record(f"{operation}.{slug}", call.func.id, exit_code,
                           rel, node.lineno)
            if isinstance(node, ast.ExceptHandler) and isinstance(
                    node.type, ast.Name):
                cls = getattr(failures, node.type.id, None)
                if not (isinstance(cls, type)
                        and issubclass(cls, failures.WriteRefused)):
                    continue
                name = node.name
                site_assign = exit_assign = None
                for stmt in ast.walk(node):
                    if not isinstance(stmt, ast.Assign):
                        continue
                    for target in stmt.targets:
                        if (isinstance(target, ast.Attribute)
                                and isinstance(target.value, ast.Name)
                                and target.value.id == name):
                            if target.attr == "site":
                                site_assign = stmt
                            elif target.attr == "exit_code":
                                exit_assign = stmt
                if site_assign is None:
                    continue
                slug = _template_slug(site_assign.value)
                assert slug is not None, (
                    f"A7 {rel}:{site_assign.lineno}: unresolvable site"
                    f" form — {FIX}")
                assert exit_assign is not None and isinstance(
                    exit_assign.value, ast.Constant) and isinstance(
                    exit_assign.value.value, int), (
                    f"A7 {rel}:{site_assign.lineno}: the assigned site"
                    f" needs a literal exit_code beside it — {FIX}")
                assert any(isinstance(stmt, ast.Raise) and stmt.exc is None
                           for stmt in ast.walk(node)), (
                    f"A7 {rel}:{site_assign.lineno}: the assigned site"
                    f" needs its bare re-raise — {FIX}")
                exit_code = exit_assign.value.value
                for operation in sorted(serving[path.name]):
                    record(f"{operation}.{slug}", node.type.id, exit_code,
                           rel, site_assign.lineno)
    return resolved


def _resolve_site(site: str) -> tuple[str, int | None, str, int]:
    try:
        return _site_raises()[site]
    except KeyError:
        raise _Unresolvable(site) from None


def _reconstruct(class_name: str, exit_code: int | None) -> BaseException:
    """The raise's failure with its static ``exit_code`` (probed values)."""
    from learning_os.domain import failures

    cls = getattr(failures, class_name)
    assert isinstance(cls, type) and issubclass(cls, failures.WriteRefused), (
        f"A7 {class_name}: not a failure — {FIX}")
    try:
        if cls is failures.NotFound:
            return cls("a7-kind", "a7-value", [], exit_code=exit_code)
        return cls("a7-probe", exit_code=exit_code)
    except TypeError as exc:
        raise AssertionError(
            f"A7 {class_name}: cannot reconstruct the raise — {FIX}"
        ) from exc


# --- the checks ------------------------------------------------------------------

def _result_v2_validator() -> Draft202012Validator:
    envelope = json.loads(ENVELOPE_SCHEMA_PATH.read_text(encoding="utf-8"))
    return Draft202012Validator(envelope["$defs"]["resultV2"])


def _error_validator() -> Draft202012Validator:
    envelope = json.loads(ENVELOPE_SCHEMA_PATH.read_text(encoding="utf-8"))
    return Draft202012Validator(
        envelope["$defs"]["resultV2"]["properties"]["error"])


def _cli_error_validator() -> Draft202012Validator:
    return Draft202012Validator(json.loads(
        CLI_ERROR_SCHEMA_PATH.read_text(encoding="utf-8")))


def _check_gateway_stdout(label: str, rel: str, stdout: str) -> None:
    """The whole stdout is resultV2; its error member matches the definition."""
    try:
        whole = json.loads(stdout)
    except ValueError as exc:
        raise AssertionError(
            f"A7 {label}: gateway stdout is not JSON ({rel}) — {FIX}"
        ) from exc
    errors = list(_result_v2_validator().iter_errors(whole))
    assert not errors, (
        f"A7 {label}: gateway stdout fails resultV2 "
        f"({errors[0].message}, {rel}) — {FIX}")
    error = whole["error"]
    assert error is not None, (
        f"A7 {label}: a refusal recording carries no error object "
        f"({rel}) — {FIX}")
    errors = list(_error_validator().iter_errors(error))
    assert not errors, (
        f"A7 {label}: error member fails the error definition "
        f"({errors[0].message}, {rel}) — {FIX}")


def _check_cli_stdout(label: str, rel: str, stdout: str) -> None:
    """A CLI stdout object matches the CLI-error schema (empty: no object)."""
    if not stdout:
        return
    try:
        whole = json.loads(stdout)
    except ValueError as exc:
        raise AssertionError(
            f"A7 {label}: CLI stdout is not JSON ({rel}) — {FIX}"
        ) from exc
    errors = list(_cli_error_validator().iter_errors(whole))
    assert not errors, (
        f"A7 {label}: CLI stdout fails cli-error "
        f"({errors[0].message}, {rel}) — {FIX}")


#: Exit units whose class the site+raise method cannot derive (SPEC-GAP,
#: pinned fail-closed: drift in either direction fails).
_EXIT_GAPS: frozenset[tuple[str, str, int | None]] = frozenset({
    ("route.patch", "blank-changes", None),
    ("ai-action.delivery.apply", "wrong-approval", None),
    ("ai-action.delivery.apply", "unknown-delivery", None),
    ("capture.create", "replay-only-miss", None),
    ("stage.progress.update", "replay-only-miss", None),
    ("route.patch", "replay-only-miss", None),
    ("ai-action.delivery.apply", "replay-only-miss", None),
    ("capture.create", "direct-cli-refused", None),
    ("stage.progress.update", "direct-cli-refused", None),
    ("route.patch", "direct-cli-refused", None),
    ("ai-action.delivery.apply", "direct-cli-refused", None),
    ("route.patch", "valid-plan-hits-warning-gate", 1),
    ("ai-action.delivery.apply", "sha-mismatch", 2),
})

#: CLI-shape units with no A7 stdout object (SPEC-GAP, pinned fail-closed).
_CLI_GAPS: frozenset[tuple[str, str, int | None]] = frozenset({
    ("route.patch", "direct-cli-refused", None),
})

_CONTEXT = {"cli": "cli", "gateway": "gateway.dispatch"}


def _check_exit(label: str, key: tuple[str, str, int | None],
                transport: str, site: str | None, recorded_exit: int) -> None:
    """The recorded exit equals ``exit_for`` for the derived class.

    Gap units pass only while pinned; a resolvable site on a pinned
    gap fails (the gap healed).
    """
    from learning_os.ops.outcomes import exit_for

    assert transport in _CONTEXT, (
        f"A7 {label}: transport {transport!r} has no outcomes context — {FIX}")
    try:
        if site is None:
            raise _Unresolvable(label)
        class_name, exit_code, rel, lineno = _resolve_site(site)
    except _Unresolvable:
        assert key in _EXIT_GAPS, (
            f"A7 {label}: unrecorded exit gap — {FIX}")
        return
    assert key not in _EXIT_GAPS, (
        f"A7 {label}: the exit gap healed; remove the pin — {FIX}")
    exc = _reconstruct(class_name, exit_code)
    want = exit_for(exc, _CONTEXT[transport])
    assert want is not None, (
        f"A7 {label}: no outcomes row for {class_name} in "
        f"{_CONTEXT[transport]} ({rel}:{lineno}) — {FIX}")
    assert want == recorded_exit, (
        f"A7 {label}: exit_for gives {want} for {class_name}, "
        f"recorded {recorded_exit} ({rel}:{lineno}) — {FIX}")


# --- the sweep ---------------------------------------------------------------------

def _gateway_units():
    return [unit for unit in _all_refusal_units() if unit[3] == "gateway"]


def _cli_units():
    return [unit for unit in _all_refusal_units() if unit[3] == "cli"]


@pytest.mark.parametrize("unit", _gateway_units(), ids=_unit_id)
def test_gateway_refusal_stdout_validates(unit):
    operation, case_id, step, _, _site, _exit, stdout = unit
    rel = f"tests/scenarios/recorded/{operation}/{case_id}.json"
    _check_gateway_stdout(_unit_id(unit), rel, stdout)


@pytest.mark.parametrize("unit", _cli_units(), ids=_unit_id)
def test_cli_refusal_stdout_validates(unit):
    operation, case_id, step, _, _site, _exit, stdout = unit
    key = (operation, case_id, step)
    if key in _CLI_GAPS:
        return
    rel = f"tests/scenarios/recorded/{operation}/{case_id}.json"
    _check_cli_stdout(_unit_id(unit), rel, stdout)


@pytest.mark.parametrize("unit", _all_refusal_units(), ids=_unit_id)
def test_refusal_exit_matches_outcomes(unit):
    operation, case_id, step, transport, site, exit, _stdout = unit
    _check_exit(_unit_id(unit), (operation, case_id, step),
                transport, site, exit)


def test_exit_gaps_all_occur():
    keys = {(op, case, step) for op, case, step, *_ in _all_refusal_units()}
    assert _EXIT_GAPS <= keys, (
        f"A7 stale exit pin: {sorted(_EXIT_GAPS - keys)} — {FIX}")


def test_cli_gap_occurs():
    keys = {(op, case, step) for op, case, step, *_ in _cli_units()}
    assert _CLI_GAPS <= keys, (
        f"A7 stale CLI pin: {sorted(_CLI_GAPS - keys)} — {FIX}")


# --- --json acceptance ---------------------------------------------------------------

def _subcommand_for(operation: str) -> str:
    """The operation's subcommand, following the inspect alias."""
    doc = json.loads((REQUESTS_DIR / f"{operation}.schema.json")
                     .read_text(encoding="utf-8"))
    if "$ref" in doc:
        doc = json.loads((REQUESTS_DIR / doc["$ref"])
                         .read_text(encoding="utf-8"))
    return doc["x-los-cli-command"]["name"]


def _cli_argv_for(operation: str) -> list[str]:
    """The operation's first CLI case argv (no invented argv)."""
    import scenario_harness as harness

    subcommand = _subcommand_for(operation)
    doc = harness.load_case_file(CASES_DIR / f"{operation}.yaml")
    for case in doc.get("cases", []):
        if case.get("transport") == "cli" and case.get("argv", [])[:1] == [
                subcommand]:
            return [str(word) for word in case["argv"]]
    raise AssertionError(
        f"A7 {operation}: no CLI case argv for {subcommand} — {FIX}")


def _check_json_accepted(operation: str) -> None:
    import los

    parser = los.build_parser()
    argv = _cli_argv_for(operation)
    try:
        want = parser.parse_args(argv)
    except SystemExit as exc:
        raise AssertionError(
            f"A7 {operation}: the real parser rejects {argv!r} — {FIX}"
        ) from exc
    flagged = list(argv)
    flagged.insert(1, "--json")
    try:
        got = parser.parse_args(flagged)
    except SystemExit as exc:
        raise AssertionError(
            f"A7 {operation}: the real parser rejects --json — {FIX}"
        ) from exc
    assert got.json is True, f"A7 {operation}: --json did not parse — {FIX}"
    assert vars(got) == {**vars(want), "json": True}, (
        f"A7 {operation}: --json changes more than json — {FIX}")


@pytest.mark.parametrize("operation", sorted(REGISTRY))
def test_json_accepted_for_every_registered_subcommand(operation):
    _check_json_accepted(operation)


# --- the exception census -------------------------------------------------------

def _unregistered_universe() -> set[str]:
    """Every request-schema operation minus the registered names (as A5)."""
    schemas = {path.name[: -len(".schema.json")]
               for path in REQUESTS_DIR.glob("*.schema.json")}
    return schemas - set(REGISTRY)


def _recorded_signatures() -> set[str]:
    data = yaml.safe_load(RATCHETS_PATH.read_text(encoding="utf-8"))
    return {entry["signature"]
            for entry in data["checks"].get(CHECK_ID, [])}


def _check_star_census(recorded_star: set[str]) -> None:
    """The recorded ``operation::*`` set equals the unregistered universe."""
    expected = {f"{operation}::*" for operation in _unregistered_universe()}
    assert recorded_star == expected, (
        "A7 star census drift: "
        f"new={sorted(recorded_star - expected)} "
        f"fixed={sorted(expected - recorded_star)} — {FIX}")


def test_star_exceptions_match_the_unregistered_universe():
    recorded = {signature for signature in _recorded_signatures()
                if signature.endswith("::*")}
    _check_star_census(recorded)
    for signature in _recorded_signatures():
        assert signature.endswith("::*"), (
            f"A7 {signature}: unknown exception shape — {FIX}")


def test_star_census_rejects_extra_and_missing():
    expected = {f"{operation}::*" for operation in _unregistered_universe()}
    with pytest.raises(AssertionError, match="star census"):
        _check_star_census(expected | {"route.patch::*"})
    missing = set(expected)
    missing.pop()
    with pytest.raises(AssertionError, match="star census"):
        _check_star_census(missing)


def _check_sweep_census(swept: set[str]) -> None:
    assert swept == set(REGISTRY), (
        "A7 sweep census drift: "
        f"new={sorted(swept - set(REGISTRY))} "
        f"missing={sorted(set(REGISTRY) - swept)} — {FIX}")


def test_sweep_covers_every_registered_operation():
    _check_sweep_census(
        {operation for operation, *_ in _all_refusal_units()})


def test_sweep_control_missing_registered_op_fails():
    with pytest.raises(AssertionError, match="sweep census"):
        _check_sweep_census(set(REGISTRY) - {"route.patch"})


# --- required controls ----------------------------------------------------------

def _a_gateway_stdout() -> tuple[str, str]:
    unit = _gateway_units()[0]
    operation, case_id = unit[0], unit[1]
    return (f"tests/scenarios/recorded/{operation}/{case_id}.json", unit[6])


def test_control_malformed_envelope_fails():
    rel, stdout = _a_gateway_stdout()
    broken = json.loads(stdout)
    del broken["request_id"]
    with pytest.raises(AssertionError, match="resultV2"):
        _check_gateway_stdout("a7-control::malformed", rel,
                              json.dumps(broken))


def test_control_wrong_error_shape_fails():
    rel, stdout = _a_gateway_stdout()
    broken = json.loads(stdout)
    broken["error"] = {"code": "NOT_A_CODE"}
    # The envelope embeds the error definition, so the whole-stdout
    # check rejects it; the member check rejects it too, directly.
    with pytest.raises(AssertionError, match="resultV2"):
        _check_gateway_stdout("a7-control::error-shape", rel,
                              json.dumps(broken))
    assert list(_error_validator().iter_errors(broken["error"])), (
        "A7 the error member check accepts a bad shape — " + FIX)
    clean = json.loads(stdout)["error"]
    assert list(_error_validator().iter_errors(clean)) == [], (
        "A7 the error member check rejects a clean error — " + FIX)


def test_control_wrong_exit_fails():
    with pytest.raises(AssertionError, match="exit_for gives"):
        _check_exit("capture.create::empty-capture",
                    ("capture.create", "empty-capture", None),
                    "gateway", "capture.create.empty-input", 3)


def test_control_non_2_exit_flows_without_assumption():
    """The stale-snapshot raise computes exit 3 in both contexts."""
    from learning_os.ops.outcomes import exit_for

    class_name, exit_code, _rel, _lineno = _resolve_site(
        "cli.inspect.stale-snapshot")
    assert (class_name, exit_code) == ("StaleSnapshot", 3)
    exc = _reconstruct(class_name, exit_code)
    assert exit_for(exc, "cli") == 3
    assert exit_for(exc, "gateway.dispatch") == 3


def test_control_cli_error_shape_is_checked():
    rel, _ = _a_gateway_stdout()
    refused = json.loads((RECORDED_DIR / "route.patch"
                          / "direct-cli-refused.json").read_text(
                              encoding="utf-8"))["stdout"]
    with pytest.raises(AssertionError, match="cli-error"):
        _check_cli_stdout("a7-control::refused-stdout", rel, refused)
    clean = {"error": {"code": "INVALID_REQUEST", "message": "nope",
                       "retryable": False, "details": {}}}
    _check_cli_stdout("a7-control::clean", rel, json.dumps(clean))
    assert _check_cli_stdout("a7-control::empty", rel, "") is None
