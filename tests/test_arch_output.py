"""Refusal output shape and exit mapping for registered operations (SPEC §3.3 A7).

For every registered operation, on its scenario cases: the real
generated parser accepts ``--json`` for its subcommand; every gateway
refusal recording's whole stdout validates against the resultV2
envelope and its error member against that schema's error definition;
every CLI refusal recording's stdout is empty, an error object, or
the (bd) legacy stream of a commit-refused unit whose handler module
passes ``refused_stdout``; and every refusal unit re-run live yields
exactly one witness line deciding the exit (SPEC (bf) item 8).
Unregistered operations are baselined ``operation::*`` exceptions,
the same derivation as A5, asserted equal in both directions.
"""

from __future__ import annotations

import ast
import json
import os
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
                                                str | None, int, str, str]]:
    """``(case, step, transport, site, exit, stdout, stderr)`` per refusal.

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
                                  result["exit"], result["stdout"],
                                  result["stderr"]))
        elif recorded["exit"] != 0:
            units.append((case["id"], None, case["transport"],
                          (case.get("expect") or {}).get("site"),
                          recorded["exit"], recorded["stdout"],
                          recorded["stderr"]))
    return units


def _all_refusal_units() -> list[tuple[str, str, int | None, str,
                                       str | None, int, str, str]]:
    units = []
    for operation in sorted(REGISTRY):
        units.extend((operation, *unit)
                     for unit in _refusal_units(operation))
    return units


def _unit_id(unit) -> str:
    operation, case_id, step, *_ = unit
    return (f"{operation}::{case_id}" if step is None
            else f"{operation}::{case_id}::step{step}")


# --- live re-runs ------------------------------------------------------------------

def _merged_case(operation: str, case_id: str) -> dict:
    """The case with its file-level fixture/observations (as effects)."""
    import scenario_harness as harness

    doc = harness.load_case_file(CASES_DIR / f"{operation}.yaml")
    bare = next(item for item in doc["cases"] if item["id"] == case_id)
    return {"fixture": doc.get("fixture", "rich_world"),
            "observations": doc["observations"],
            "fixture_mtime": doc.get(
                "fixture_mtime", harness.FIXTURE_MTIME_DEFAULT),
            **bare}


#: ``unit id -> (live exit, witness lines, live stdout, live stderr)``
#: for the target step, shared by the exit and CLI clauses over the
#: same live evidence.
_LIVE: dict[str, tuple[int, list[dict], str, str]] = {}


@pytest.fixture(scope="module")
def _witness_dir(tmp_path_factory):
    """One directory for the session's per-unit witness files."""
    return tmp_path_factory.mktemp("a7-witness")


def _live_target(unit, tmp_path: Path, witness_dir: Path):
    """``(live exit, lines, live stdout, live stderr)`` for the target.

    Item 8.2 plus SPEC (ct) item 2 and SPEC (cx) D-9: a fresh fixture
    with its prerequisites through the unchanged harness;
    prerequisites run unwitnessed and their live exits must match
    recorded, then the target step runs with the per-unit witness file
    in the harness environment. The cached live streams let the
    diagnostic and command-failure CLI clauses require byte-identical
    recorded output.
    """
    import scenario_harness as harness
    from arch_audit_hook import SITE_WITNESS_ENV

    key = _unit_id(unit)
    if key in _LIVE:
        return _LIVE[key]
    operation, case_id, step, _transport, _site, _exit, _stdout, _stderr = unit
    case = _merged_case(operation, case_id)
    target_index = step if step is not None else 0
    steps = (case.get("steps", []) if case.get("kind") == "sequence"
             else [case])
    recorded = _recorded(operation, case_id)
    recorded_steps = recorded["steps"] if step is not None else [recorded]
    workdir = tmp_path / "world"
    workdir.mkdir(parents=True, exist_ok=True)
    ctx = harness._prepare_world(case, operation, workdir)
    previous = os.environ.pop(SITE_WITNESS_ENV, None)
    try:
        for prereq in range(target_index):
            full = {"operation": operation, **steps[prereq]}
            result = harness._run_step(ctx, operation, full, prereq)
            want = recorded_steps[prereq]["exit"]
            assert result["exit"] == want, (
                f"A7 {key}: prerequisite step {prereq} exits "
                f"{result['exit']}, recorded {want}: "
                f"{result['stderr'][:300]!r} — {FIX}")
    finally:
        if previous is not None:
            os.environ[SITE_WITNESS_ENV] = previous
    witness_file = witness_dir / (key.replace(":", "_")
                                  .replace("/", "_") + ".jsonl")
    witness_file.touch()
    full = {"operation": operation, **steps[target_index]}
    os.environ[SITE_WITNESS_ENV] = str(witness_file)
    try:
        result = harness._run_step(ctx, operation, full, target_index)
    finally:
        if previous is None:
            os.environ.pop(SITE_WITNESS_ENV, None)
        else:
            os.environ[SITE_WITNESS_ENV] = previous
    harness.check_witnesses(ctx)
    lines = [json.loads(line)
             for line in witness_file.read_text(
                 encoding="utf-8").splitlines()
             if line.strip()]
    _LIVE[key] = (result["exit"], lines, result["stdout"],
                    result["stderr"])
    return _LIVE[key]


def _resolve_reconstruct_class(operation: str, class_name: str):
    """The witnessed class, resolved from where it is defined.

    The (bl) 5 way, extended: ``domain.failures`` first, then the
    already imported handler module's globals (registration imported
    it), then the one ``learning_os`` module that defines the name
    (verified through ``__module__``). Every candidate must be an
    exception class; a non-failure, an unknown name, or an ambiguous
    one resolves to None.
    """
    import sys

    from learning_os.domain import failures

    def failure(obj):
        if isinstance(obj, type) and issubclass(obj, Exception):
            return obj
        return None

    cls = failure(getattr(failures, class_name, None))
    if cls is not None:
        return cls
    handler = REGISTRY[operation].handler
    module = sys.modules[handler.__module__]
    cls = failure(module.__dict__.get(class_name))
    if cls is not None:
        return cls
    defining = []
    for module_name in sorted(sys.modules):
        if module_name != "learning_os" \
                and not module_name.startswith("learning_os."):
            continue
        obj = failure(getattr(sys.modules[module_name], class_name,
                              None))
        if obj is not None and obj.__module__ == module_name:
            defining.append(obj)
    if len(defining) == 1:
        return defining[0]
    return None


def _reconstruct(operation: str, class_name: str,
                 exit_code: int | None) -> BaseException:
    """The witnessed failure with its witnessed ``exit_code`` (probed values)."""
    from learning_os.domain import failures

    cls = _resolve_reconstruct_class(operation, class_name)
    assert cls is not None, f"A7 {class_name}: not a failure — {FIX}"
    try:
        if issubclass(cls, failures.NotFound):
            return cls("a7-kind", "a7-value", [], exit_code=exit_code)
        if issubclass(cls, failures.WriteRefused):
            return cls("a7-probe", exit_code=exit_code)
        return cls("a7-probe")
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


_CONTEXT = {"cli": "cli", "gateway": "gateway.dispatch"}


def _check_live_exit(label: str, transport: str, recorded_exit: int,
                     live_exit: int, lines: list[dict],
                     operation: str) -> None:
    """Item 8.2 plus (bg) 1 and (ct) 2: the target step's single line.

    A ``failure`` line gives ``exit_for`` for the reconstructed class
    with its witnessed ``exit_code``; a ``commit-refused`` line gives
    the witnessed code; a ``direct-refused`` line gives the witnessed
    direct code with its exact shape, null site, target operation and
    nonzero integer code; a ``diagnostic-failure`` line gives the
    witnessed integer 1 with its exact shape, target operation and
    null site, and recorded/live/witnessed exits are all 1 with no
    ``exit_for`` class; a ``command-failure`` line gives the witnessed
    nonzero integer exit with its exact shape, target operation and
    null site, and recorded/live/witnessed exits all agree, with no
    ``exit_for`` class. No line, or more than one, fails.
    """
    from learning_os.ops.outcomes import exit_for

    assert transport in _CONTEXT, (
        f"A7 {label}: transport {transport!r} has no outcomes context — {FIX}")
    assert live_exit == recorded_exit, (
        f"A7 {label}: live exit {live_exit}, recorded {recorded_exit} — {FIX}")
    if not lines:
        raise AssertionError(
            f"A7 {label}: no witness line for the refusal unit — {FIX}")
    assert len(lines) == 1, (
        f"A7 {label}: {len(lines)} witness lines for one refusal unit — {FIX}")
    line = lines[0]
    if line.get("kind") == "failure":
        exc = _reconstruct(operation, line["class"], line["exit_code"])
        want = exit_for(exc, _CONTEXT[transport])
        assert want is not None, (
            f"A7 {label}: no outcomes row for {line['class']} in "
            f"{_CONTEXT[transport]} — {FIX}")
        assert want == recorded_exit, (
            f"A7 {label}: exit_for gives {want} for {line['class']}, "
            f"recorded {recorded_exit} — {FIX}")
        return
    if line.get("kind") == "commit-refused":
        assert recorded_exit == line["code"], (
            f"A7 {label}: witnessed commit code {line['code']}, "
            f"recorded {recorded_exit} — {FIX}")
        return
    if line.get("kind") == "direct-refused":
        assert set(line) == {"operation", "kind", "site", "code"}, (
            f"A7 {label}: direct line has shape {sorted(line)} — {FIX}")
        assert line["site"] is None, (
            f"A7 {label}: direct line names site "
            f"{line['site']!r} — {FIX}")
        assert line["operation"] == operation, (
            f"A7 {label}: direct line names {line['operation']!r}, "
            f"unit {operation!r} — {FIX}")
        assert type(line["code"]) is int and line["code"] != 0, (
            f"A7 {label}: direct code {line['code']!r} is not a "
            f"nonzero integer — {FIX}")
        assert recorded_exit == line["code"], (
            f"A7 {label}: witnessed direct code {line['code']}, "
            f"recorded {recorded_exit} — {FIX}")
        return
    if line.get("kind") == "diagnostic-failure":
        assert set(line) == {"operation", "kind", "site", "code"}, (
            f"A7 {label}: diagnostic line has shape "
            f"{sorted(line)} — {FIX}")
        assert line["operation"] == operation, (
            f"A7 {label}: diagnostic line names "
            f"{line['operation']!r}, unit {operation!r} — {FIX}")
        assert line["site"] is None, (
            f"A7 {label}: diagnostic line names site "
            f"{line['site']!r} — {FIX}")
        assert type(line["code"]) is int and line["code"] == 1, (
            f"A7 {label}: diagnostic code {line['code']!r} is not "
            f"integer 1 — {FIX}")
        assert recorded_exit == 1 and live_exit == 1, (
            f"A7 {label}: diagnostic exits recorded {recorded_exit}, "
            f"live {live_exit}, want 1 — {FIX}")
        assert recorded_exit == line["code"], (
            f"A7 {label}: witnessed diagnostic code {line['code']}, "
            f"recorded {recorded_exit} — {FIX}")
        return
    if line.get("kind") == "command-failure":
        assert set(line) == {"operation", "kind", "site", "code"}, (
            f"A7 {label}: command line has shape "
            f"{sorted(line)} — {FIX}")
        assert line["operation"] == operation, (
            f"A7 {label}: command line names "
            f"{line['operation']!r}, unit {operation!r} — {FIX}")
        assert line["site"] is None, (
            f"A7 {label}: command line names site "
            f"{line['site']!r} — {FIX}")
        assert type(line["code"]) is int and line["code"] != 0, (
            f"A7 {label}: command code {line['code']!r} is not a "
            f"nonzero integer — {FIX}")
        assert recorded_exit == line["code"], (
            f"A7 {label}: witnessed command code {line['code']}, "
            f"recorded {recorded_exit} — {FIX}")
        return
    raise AssertionError(
        f"A7 {label}: witness kind {line.get('kind')!r} — {FIX}")


def _is_cli_error_object(stdout: str) -> bool:
    """Whether the stdout parses as a CLI error object."""
    try:
        whole = json.loads(stdout)
    except ValueError:
        return False
    return not list(_cli_error_validator().iter_errors(whole))


def _handler_module_has_refused_stdout(operation: str) -> bool:
    """AST: the handler's module passes ``Result(..., refused_stdout=...)``.

    A ``None`` value passes nothing, as in the A18 population rule.
    """
    module = REGISTRY[operation].handler.__module__
    assert module.startswith("learning_os.ops.handlers."), module
    path = HANDLERS_DIR / (module.rsplit(".", 1)[1] + ".py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        last = func.id if isinstance(func, ast.Name) else (
            func.attr if isinstance(func, ast.Attribute) else None)
        if last != "Result":
            continue
        for keyword in node.keywords:
            if keyword.arg != "refused_stdout":
                continue
            if isinstance(keyword.value, ast.Constant) \
                    and keyword.value.value is None:
                continue
            return True
    return False


def _check_cli_refusal_stdout(label: str, operation: str,
                              recorded_stdout: str,
                              line: dict | None,
                              live_stdout: str | None = None) -> None:
    """Item 8.3 plus (ct) 2: ordinary shape or the diagnostic report.

    A ``diagnostic-failure`` unit's stdout is the rendered JSON report
    object, byte-identical live and recorded. Every other non-empty
    non-error-object stdout needs the (bd) legacy stream: allowed only
    for a ``commit-refused`` unit of an operation whose registered
    handler module passes ``refused_stdout``. Every other CLI refusal
    stdout is empty or an error object.
    """
    if line is not None and line.get("kind") == "diagnostic-failure":
        try:
            parsed = json.loads(recorded_stdout)
        except ValueError as exc:
            raise AssertionError(
                f"A7 {label}: diagnostic stdout is not JSON — {FIX}"
            ) from exc
        assert isinstance(parsed, dict), (
            f"A7 {label}: diagnostic stdout is not a JSON object — {FIX}")
        assert live_stdout is not None, (
            f"A7 {label}: diagnostic live stdout is missing — {FIX}")
        assert live_stdout == recorded_stdout, (
            f"A7 {label}: diagnostic live stdout differs from "
            f"recorded — {FIX}")
        return
    if not recorded_stdout or _is_cli_error_object(recorded_stdout):
        return
    assert line is not None and line.get("kind") == "commit-refused", (
        f"A7 {label}: CLI stdout is not an error object and the unit "
        f"is not commit-refused — {FIX}")
    assert _handler_module_has_refused_stdout(operation), (
        f"A7 {label}: CLI stdout is not an error object and "
        f"{operation} passes no refused_stdout — {FIX}")


def _check_command_failure_streams(label: str, operation: str,
                                   recorded_stdout: str,
                                   recorded_stderr: str,
                                   line: dict | None,
                                   live_stdout: str | None,
                                   live_stderr: str | None) -> None:
    """SPEC (cx) D-9: a command unit's raw streams, byte-identical.

    A ``command-failure`` unit's stdout and stderr are the failed
    child's raw streams, byte-identical live and recorded. The line
    names the unit's operation and no site; the exit clause pins the
    strict shape and the nonzero integer code.
    """
    assert line is not None and line.get("kind") == "command-failure", (
        f"A7 {label}: command streams without a command-failure "
        f"line — {FIX}")
    assert line["operation"] == operation, (
        f"A7 {label}: command line names {line['operation']!r}, "
        f"unit {operation!r} — {FIX}")
    assert line["site"] is None, (
        f"A7 {label}: command line names site "
        f"{line['site']!r} — {FIX}")
    assert live_stdout is not None and live_stderr is not None, (
        f"A7 {label}: command live streams are missing — {FIX}")
    assert live_stdout == recorded_stdout, (
        f"A7 {label}: command live stdout differs from recorded — {FIX}")
    assert live_stderr == recorded_stderr, (
        f"A7 {label}: command live stderr differs from recorded — {FIX}")


# --- the sweep ---------------------------------------------------------------------

def _gateway_units():
    return [unit for unit in _all_refusal_units() if unit[3] == "gateway"]


def _cli_units():
    return [unit for unit in _all_refusal_units() if unit[3] == "cli"]


@pytest.mark.parametrize("unit", _gateway_units(), ids=_unit_id)
def test_gateway_refusal_stdout_validates(unit):
    operation, case_id, step, _, _site, _exit, stdout, _stderr = unit
    rel = f"tests/scenarios/recorded/{operation}/{case_id}.json"
    _check_gateway_stdout(_unit_id(unit), rel, stdout)


@pytest.mark.parametrize("unit", _cli_units(), ids=_unit_id)
def test_cli_refusal_stdout_shape(unit, tmp_path, _witness_dir):
    operation, case_id, step, _, _site, _exit, stdout, stderr = unit
    _live_exit, lines, live_stdout, live_stderr = _live_target(
        unit, tmp_path, _witness_dir)
    line = lines[0] if len(lines) == 1 else None
    if line is not None and line.get("kind") == "command-failure":
        _check_command_failure_streams(
            _unit_id(unit), operation, stdout, stderr, line,
            live_stdout, live_stderr)
        return
    _check_cli_refusal_stdout(
        _unit_id(unit), operation, stdout, line, live_stdout)


@pytest.mark.parametrize("unit", _all_refusal_units(), ids=_unit_id)
def test_refusal_exit_matches_outcomes_live(unit, tmp_path, _witness_dir):
    operation, case_id, step, transport, _site, exit, _stdout, _stderr = unit
    live_exit, lines, _live_stdout, _live_stderr = _live_target(
        unit, tmp_path, _witness_dir)
    _check_live_exit(_unit_id(unit), transport, exit, live_exit, lines,
                     operation)


# --- --json acceptance ---------------------------------------------------------------

def _subcommand_for(operation: str) -> str:
    """The operation's subcommand, following the inspect alias."""
    doc = json.loads((REQUESTS_DIR / f"{operation}.schema.json")
                     .read_text(encoding="utf-8"))
    if "$ref" in doc:
        doc = json.loads((REQUESTS_DIR / doc["$ref"])
                         .read_text(encoding="utf-8"))
    return doc["x-los-cli-command"]["name"]


def _rendered_request_argv(operation: str, request: dict,
                           subcommand: str) -> list[str] | None:
    """One CLI request-form input as argv, or None (never partial).

    The actual request through the real ``request_to_argv`` and the
    capability catalogue, exactly as ``step_argv`` builds the child
    argv. A request with no CLI rendering (unknown command, keys with
    no flag) or a rendered command that is not the subcommand
    supplies no probe; the caller reads on.
    """
    import scenario_harness as harness

    try:
        command = harness._cli_command_for(operation, ROOT)
        rendered = harness.request_to_argv(operation, request, ROOT)
    except (KeyError, ValueError):
        return None
    argv = [command, *rendered]
    if argv[:1] != [subcommand]:
        return None
    return [str(word) for word in argv]


def _cli_argv_from_cases(operation: str, cases: list[dict],
                         subcommand: str) -> list[str] | None:
    """The probe argv from actual cases, or None (no invented argv).

    First the prior top-level literal, unchanged: the first
    non-sequence CLI case whose argv opens with the subcommand.
    Otherwise the first fallback source in original file order: an
    own-operation CLI sequence step (effective operation equal;
    foreign steps never supply a probe) as its literal argv, or a
    CLI request-form input rendered whole through
    ``_rendered_request_argv``. A literal whose command differs, an
    unrenderable request, and every gateway input supply nothing.
    """
    for case in cases:
        if case.get("kind") == "sequence":
            continue
        if case.get("transport") == "cli" \
                and case.get("argv", [])[:1] == [subcommand]:
            return [str(word) for word in case["argv"]]
    for case in cases:
        if case.get("kind") == "sequence":
            for step in case.get("steps", []):
                if step.get("operation", operation) != operation:
                    continue
                if step.get("transport") != "cli":
                    continue
                if "argv" in step:
                    if step.get("argv", [])[:1] == [subcommand]:
                        return [str(word) for word in step["argv"]]
                elif "request" in step:
                    rendered = _rendered_request_argv(
                        operation, step["request"], subcommand)
                    if rendered is not None:
                        return rendered
            continue
        if case.get("transport") != "cli":
            continue
        if "argv" in case:
            continue
        if "request" in case:
            rendered = _rendered_request_argv(
                operation, case["request"], subcommand)
            if rendered is not None:
                return rendered
    return None


def _cli_argv_for(operation: str) -> list[str]:
    """The operation's probe argv from its actual cases (no invented argv)."""
    import scenario_harness as harness

    subcommand = _subcommand_for(operation)
    doc = harness.load_case_file(CASES_DIR / f"{operation}.yaml")
    argv = _cli_argv_from_cases(operation, doc.get("cases", []),
                               subcommand)
    if argv is None:
        raise AssertionError(
            f"A7 {operation}: no CLI case argv for {subcommand} — {FIX}")
    return argv


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


# --- probe-selection controls ---------------------------------------------------

def _top_level_literals(cases: list[dict], subcommand: str) -> list[str]:
    """Ids of top-level CLI cases whose argv opens with the subcommand."""
    return [case["id"] for case in cases
            if case.get("kind") != "sequence"
            and case.get("transport") == "cli"
            and case.get("argv", [])[:1] == [subcommand]]


def test_control_argv_uses_first_sequence_own_step():
    """Without a top-level literal the probe is the first own-op step."""
    import scenario_harness as harness

    operation = "masters-planning.comparison.publish"
    subcommand = _subcommand_for(operation)
    doc = harness.load_case_file(CASES_DIR / f"{operation}.yaml")
    cases = doc.get("cases", [])
    assert _top_level_literals(cases, subcommand) == []
    first = None
    for case in cases:
        if case.get("kind") != "sequence":
            continue
        for index, step in enumerate(case.get("steps", [])):
            if step.get("operation", operation) == operation \
                    and step.get("transport") == "cli" \
                    and step.get("argv", [])[:1] == [subcommand]:
                first = (case["id"], index,
                         [str(word) for word in step["argv"]])
                break
        if first is not None:
            break
    assert first is not None, (
        f"A7 {operation} has no own-op CLI step — {FIX}")
    assert (first[0], first[1]) == ("direct-cli-refused", 1)
    assert _cli_argv_for(operation) == first[2]


@pytest.mark.parametrize(
    ("operation", "case_id"),
    [("note.analysis.save", "unknown-analysis-field"),
     ("note.analysis.save_batch", "bundle-unknown-field"),
     ("review.apply", "apply-needs-approve")])
def test_control_argv_renders_first_request_form(operation, case_id):
    """Without a literal the probe renders the first request-form case."""
    import scenario_harness as harness

    subcommand = _subcommand_for(operation)
    doc = harness.load_case_file(CASES_DIR / f"{operation}.yaml")
    cases = doc.get("cases", [])
    assert _top_level_literals(cases, subcommand) == []
    first_request = next(case["id"] for case in cases
                         if case.get("kind") != "sequence"
                         and case.get("transport") == "cli"
                         and "request" in case and "argv" not in case)
    assert first_request == case_id
    request = next(case for case in cases
                   if case["id"] == case_id)["request"]
    command = harness._cli_command_for(operation, ROOT)
    assert command == subcommand, (
        f"A7 {operation}: catalogue command {command!r} is not "
        f"{subcommand!r} — {FIX}")
    assert _cli_argv_for(operation) == [
        command, *harness.request_to_argv(operation, request, ROOT)]


def test_control_argv_fallback_follows_original_order():
    """review.apply's earlier request-form wins over its later step."""
    import scenario_harness as harness

    operation = "review.apply"
    subcommand = _subcommand_for(operation)
    doc = harness.load_case_file(CASES_DIR / f"{operation}.yaml")
    cases = doc.get("cases", [])
    positions = {case["id"]: index for index, case in enumerate(cases)}
    assert positions["apply-needs-approve"] < positions["direct-cli-refused"]
    later = next(case for case in cases
                 if case["id"] == "direct-cli-refused")
    step = later["steps"][1]
    assert step.get("operation", operation) == operation
    assert step.get("transport") == "cli"
    assert step["argv"][:1] == [subcommand]
    request = next(case for case in cases
                   if case["id"] == "apply-needs-approve")["request"]
    assert _cli_argv_for(operation) == [
        subcommand, *harness.request_to_argv(operation, request, ROOT)]


@pytest.mark.parametrize(
    "operation",
    ["cli.ai-action-import-delivery", "cli.ai-action-validate-delivery",
     "note.create"])
def test_control_argv_prefers_original_top_level_literal(operation):
    """An earlier fallback source never shadows the top-level literal."""
    import scenario_harness as harness

    subcommand = _subcommand_for(operation)
    doc = harness.load_case_file(CASES_DIR / f"{operation}.yaml")
    cases = doc.get("cases", [])
    at = next(index for index, case in enumerate(cases)
              if case.get("kind") != "sequence"
              and case.get("transport") == "cli"
              and case.get("argv", [])[:1] == [subcommand])
    assert _cli_argv_from_cases(
        operation, cases[:at], subcommand) is not None, (
        f"A7 {operation} has no earlier fallback source — {FIX}")
    assert _cli_argv_for(operation) == [
        str(word) for word in cases[at]["argv"]]


def test_control_argv_rejects_foreign_operation_step():
    """A foreign-operation step never supplies the probe (own-op only).

    No case file carries a foreign-operation CLI step (verified by
    scan), so the branch is exercised with the real shelving-apply
    step argv placed in synthetic own/foreign steps.
    """
    subcommand = "shelving-apply"
    words = [subcommand, "unit-demo-l01", "--selected", "proposal-keep",
             "--approve"]
    foreign = {"id": "foreign-first", "kind": "sequence", "steps": [
        {"operation": "review.prepare", "transport": "cli",
         "argv": list(words)}]}
    own = {"id": "own-second", "kind": "sequence", "steps": [
        {"transport": "cli", "argv": list(words)}]}
    assert _cli_argv_from_cases(
        "review.apply", [foreign, own], subcommand) == words
    assert _cli_argv_from_cases(
        "review.apply", [foreign], subcommand) is None


def test_control_argv_without_source_fails_closed(monkeypatch):
    """With no CLI source the probe refuses instead of inventing argv."""
    import scenario_harness as harness

    operation = "review.apply"
    doc = harness.load_case_file(CASES_DIR / f"{operation}.yaml")
    gateway_only = {"cases": [case for case in doc["cases"]
                              if case.get("kind") != "sequence"
                              and case.get("transport") == "gateway"]}
    assert gateway_only["cases"], (
        f"A7 {operation} has no gateway case for the control — {FIX}")
    monkeypatch.setattr(harness, "load_case_file",
                        lambda path: gateway_only)
    with pytest.raises(AssertionError, match="no CLI case argv"):
        _cli_argv_for(operation)


def test_control_argv_unsupported_request_supplies_no_probe():
    """An unrenderable request yields no probe, never a partial argv."""
    import scenario_harness as harness

    operation = "review.apply"
    subcommand = _subcommand_for(operation)
    bogus = {"id": "bogus-keys", "transport": "cli",
             "request": {"unit_id": "unit-demo-l01", "no_such_flag": 1}}
    with pytest.raises(ValueError, match="no CLI flag"):
        harness.request_to_argv(operation, bogus["request"], ROOT)
    assert _cli_argv_from_cases(operation, [bogus], subcommand) is None


def test_control_argv_probe_targets_own_subcommand():
    """Every probe opens with its own operation's subcommand."""
    for operation in sorted(REGISTRY):
        assert _cli_argv_for(operation)[:1] == [
            _subcommand_for(operation)], (
            f"A7 {operation}: probe targets another subcommand — {FIX}")


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


#: Registered operations with no refusal unit (SPEC (bu) 6): every
#: registered operation owns a refusal unit or exactly one table row,
#: never both.
NO_REFUSAL_UNIT = {
    "cli.ai-action-list": ("no refusal raise in the handler closure: list_actions "
                           "only projects the action registry"),
    "cli.program-list": "no refusal raise in the handler closure",
    "cli.status": ("only refusal is cli.status.unreadable-records, unreachable "
                   "from inputs: parse failures need corrupt canonical records "
                   "and no status input writes records"),
    "cli.health-report": ("no refusal raise in the handler closure: "
                           "health_report only builds the report"),
    "health.report": ("shares cli.health-report's handler; no refusal raise "
                       "declares for health.report"),
    "cli.inbox-list": ("only refusal is cli.inbox-list.list-failed, unreachable "
                        "from inputs: listing work/inbox fails only on OSError"),
    "inbox.list": ("shares cli.inbox-list's handler; the closure's only "
                    "refusal declares as cli.inbox-list.list-failed"),
    "cli.legacy-archive-status": ("no refusal raise in the handler closure: "
                                   "legacy_archive_status only loads the "
                                   "published lock"),
    "legacy.archive.status": ("shares cli.legacy-archive-status's handler; no "
                               "refusal raise declares for "
                               "legacy.archive.status"),
    "cli.module-list": ("no refusal raise in the handler closure: module_list "
                         "only filters manifest rows"),
    "cli.project-list": ("no refusal raise in the handler closure: "
                          "project_list only filters manifest rows"),
    "project.list": ("shares cli.project-list's handler; no refusal raise "
                      "declares for project.list"),
}


def _check_sweep_census(swept: set[str], table: dict | None = None) -> None:
    owned = set(NO_REFUSAL_UNIT if table is None else table)
    missing = set(REGISTRY) - swept - owned
    both = swept & owned
    assert not missing and not both, (
        "A7 sweep census drift: "
        f"missing={sorted(missing)} both={sorted(both)} — {FIX}")


def test_sweep_covers_every_registered_operation():
    _check_sweep_census(
        {operation for operation, *_ in _all_refusal_units()})


def test_sweep_control_missing_registered_op_fails():
    with pytest.raises(AssertionError, match="sweep census"):
        _check_sweep_census(set(REGISTRY) - {"route.patch"})


def test_control_reconstruct_resolves_from_where_defined():
    """An ai_actions error reconstructs to its defining module's class."""
    from learning_os.ai_actions.errors import TargetNotFoundError
    from learning_os.ops.outcomes import exit_for

    exc = _reconstruct("cli.ai-action-status", "TargetNotFoundError",
                       None)
    assert type(exc) is TargetNotFoundError
    assert exit_for(exc, "cli") == 1


def test_control_reconstruct_rejects_non_failure():
    """A non-failure global and an unknown name reconstruct to nothing."""
    with pytest.raises(AssertionError, match="not a failure"):
        _reconstruct("cli.ai-action-list", "AIActionService", None)
    with pytest.raises(AssertionError, match="not a failure"):
        _reconstruct("cli.ai-action-list", "NoSuchFailure", None)


def test_sweep_control_table_row_for_refusing_op_fails():
    """SPEC (bu) 6 control: a table row for an operation that owns a
    refusal unit fails the census."""
    units = {operation for operation, *_ in _all_refusal_units()}
    assert "cli.dossier" in units
    with pytest.raises(AssertionError, match="sweep census"):
        _check_sweep_census(units, {**NO_REFUSAL_UNIT, "cli.dossier": "control"})


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


def _a_failure_line() -> dict:
    return {"operation": "capture.create", "kind": "failure",
            "site": "capture.create.empty-input",
            "class": "WriteRefused", "exit_code": 2}


def _a_commit_line() -> dict:
    return {"operation": "capture.create", "kind": "commit-refused",
            "site": None, "code": 2}


def test_control_unit_without_witness_line_fails():
    with pytest.raises(AssertionError, match="no witness line"):
        _check_live_exit("a7-control::no-line", "gateway", 2, 2, [],
                         "capture.create")


def test_control_unit_with_two_witness_lines_fails():
    with pytest.raises(AssertionError, match="2 witness lines"):
        _check_live_exit("a7-control::two-lines", "gateway", 2, 2,
                         [_a_failure_line(), _a_failure_line()],
                         "capture.create")


def test_control_wrong_recorded_exit_for_failure_fails():
    with pytest.raises(AssertionError, match="exit_for gives"):
        _check_live_exit("a7-control::failure-exit", "gateway", 3, 3,
                         [_a_failure_line()], "capture.create")


def test_control_wrong_recorded_exit_for_commit_refused_fails():
    with pytest.raises(AssertionError, match="witnessed commit code"):
        _check_live_exit("a7-control::commit-exit", "cli", 3, 3,
                         [_a_commit_line()], "capture.create")


def _a_direct_line() -> dict:
    return {"operation": "capture.create", "kind": "direct-refused",
            "site": None, "code": 2}


def test_control_wrong_operation_for_direct_refused_fails():
    line = _a_direct_line()
    line["operation"] = "route.patch"
    with pytest.raises(AssertionError, match="unit 'capture.create'"):
        _check_live_exit("a7-control::direct-op", "gateway", 2, 2,
                         [line], "capture.create")


def test_control_zero_code_for_direct_refused_fails():
    line = _a_direct_line()
    line["code"] = 0
    with pytest.raises(AssertionError, match="not a nonzero integer"):
        _check_live_exit("a7-control::direct-zero", "gateway", 2, 2,
                         [line], "capture.create")


def test_control_bool_code_for_direct_refused_fails():
    line = _a_direct_line()
    line["code"] = True
    with pytest.raises(AssertionError, match="not a nonzero integer"):
        _check_live_exit("a7-control::direct-bool", "gateway", 2, 2,
                         [line], "capture.create")


def test_control_wrong_code_for_direct_refused_fails():
    with pytest.raises(AssertionError, match="witnessed direct code"):
        _check_live_exit("a7-control::direct-code", "gateway", 3, 3,
                         [_a_direct_line()], "capture.create")


def test_control_unsupported_witness_kind_fails():
    line = _a_direct_line()
    line["kind"] = "bogus-kind"
    with pytest.raises(AssertionError, match="witness kind"):
        _check_live_exit("a7-control::direct-kind", "gateway", 2, 2,
                         [line], "capture.create")


def test_control_malformed_direct_shape_fails():
    extra = _a_direct_line()
    extra["class"] = "WriteRefused"
    with pytest.raises(AssertionError, match="direct line has shape"):
        _check_live_exit("a7-control::direct-shape", "gateway", 2, 2,
                         [extra], "capture.create")
    sited = _a_direct_line()
    sited["site"] = "capture.create.bad-file"
    with pytest.raises(AssertionError, match="direct line names site"):
        _check_live_exit("a7-control::direct-site", "gateway", 2, 2,
                         [sited], "capture.create")


def _a_refused_stdout() -> str:
    return json.loads((RECORDED_DIR / "route.patch"
                       / "direct-cli-refused.json").read_text(
                           encoding="utf-8"))["stdout"]


def test_control_non_error_stdout_without_refused_stdout_fails():
    with pytest.raises(AssertionError, match="passes no refused_stdout"):
        _check_cli_refusal_stdout("a7-control::no-stream",
                                  "capture.create", _a_refused_stdout(),
                                  _a_commit_line())


def test_control_non_error_stdout_on_non_commit_refused_fails():
    with pytest.raises(AssertionError, match="not commit-refused"):
        _check_cli_refusal_stdout("a7-control::no-commit",
                                  "route.patch", _a_refused_stdout(),
                                  _a_failure_line())


def test_control_refused_stdout_allowance_passes():
    """The (bd) legacy stream passes for a commit-refused unit of its op."""
    assert _handler_module_has_refused_stdout("route.patch")
    assert not _handler_module_has_refused_stdout("capture.create")
    _check_cli_refusal_stdout("a7-control::stream-ok",
                              "route.patch", _a_refused_stdout(),
                              _a_commit_line())


def test_control_cli_error_shape_is_checked():
    clean = {"error": {"code": "INVALID_REQUEST", "message": "nope",
                       "retryable": False, "details": {}}}
    _check_cli_refusal_stdout("a7-control::clean", "capture.create",
                              json.dumps(clean), _a_failure_line())
    _check_cli_refusal_stdout("a7-control::empty", "capture.create",
                              "", _a_failure_line())


# --- SPEC (ct) diagnostic controls -------------------------------------------

def _a_diagnostic_line() -> dict:
    return {"operation": "cli.backup-verify",
            "kind": "diagnostic-failure", "site": None, "code": 1}


def _a_diagnostic_stdout() -> str:
    return json.loads((RECORDED_DIR / "cli.backup-verify"
                       / "checksums-fail.json").read_text(
                           encoding="utf-8"))["stdout"]


def test_control_diagnostic_clean_passes():
    """The recorded backup report passes both diagnostic clauses."""
    stdout = _a_diagnostic_stdout()
    assert isinstance(json.loads(stdout), dict)
    _check_live_exit("a7-control::diag-clean", "cli", 1, 1,
                     [_a_diagnostic_line()], "cli.backup-verify")
    _check_cli_refusal_stdout("a7-control::diag-clean",
                              "cli.backup-verify", stdout,
                              _a_diagnostic_line(), stdout)


def test_control_diagnostic_duplicate_lines_fail():
    with pytest.raises(AssertionError, match="2 witness lines"):
        _check_live_exit("a7-control::diag-two", "cli", 1, 1,
                         [_a_diagnostic_line(), _a_diagnostic_line()],
                         "cli.backup-verify")


def test_control_diagnostic_wrong_operation_fails():
    line = _a_diagnostic_line()
    line["operation"] = "route.patch"
    with pytest.raises(AssertionError, match="unit 'cli.backup-verify'"):
        _check_live_exit("a7-control::diag-op", "cli", 1, 1,
                         [line], "cli.backup-verify")


def test_control_diagnostic_non_null_site_fails():
    line = _a_diagnostic_line()
    line["site"] = "cli.backup-verify.bad-file"
    with pytest.raises(AssertionError, match="diagnostic line names site"):
        _check_live_exit("a7-control::diag-site", "cli", 1, 1,
                         [line], "cli.backup-verify")


def test_control_diagnostic_malformed_shape_fails():
    extra = _a_diagnostic_line()
    extra["class"] = "WriteRefused"
    with pytest.raises(AssertionError, match="diagnostic line has shape"):
        _check_live_exit("a7-control::diag-shape", "cli", 1, 1,
                         [extra], "cli.backup-verify")


def test_control_diagnostic_zero_code_fails():
    line = _a_diagnostic_line()
    line["code"] = 0
    with pytest.raises(AssertionError, match="not integer 1"):
        _check_live_exit("a7-control::diag-zero", "cli", 1, 1,
                         [line], "cli.backup-verify")


def test_control_diagnostic_bool_code_fails():
    line = _a_diagnostic_line()
    line["code"] = True
    with pytest.raises(AssertionError, match="not integer 1"):
        _check_live_exit("a7-control::diag-bool", "cli", 1, 1,
                         [line], "cli.backup-verify")


def test_control_diagnostic_wrong_code_fails():
    line = _a_diagnostic_line()
    line["code"] = 2
    with pytest.raises(AssertionError, match="not integer 1"):
        _check_live_exit("a7-control::diag-code", "cli", 1, 1,
                         [line], "cli.backup-verify")


def test_control_diagnostic_wrong_exit_fails():
    with pytest.raises(AssertionError, match="want 1"):
        _check_live_exit("a7-control::diag-exit", "cli", 2, 2,
                         [_a_diagnostic_line()], "cli.backup-verify")


def test_control_diagnostic_non_json_stdout_fails():
    with pytest.raises(AssertionError, match="not JSON"):
        _check_cli_refusal_stdout("a7-control::diag-nojson",
                                  "cli.backup-verify", "not json",
                                  _a_diagnostic_line(), "not json")


def test_control_diagnostic_non_object_stdout_fails():
    with pytest.raises(AssertionError, match="not a JSON object"):
        _check_cli_refusal_stdout("a7-control::diag-noobj",
                                  "cli.backup-verify", "[]",
                                  _a_diagnostic_line(), "[]")


def test_control_diagnostic_changed_stdout_fails():
    stdout = _a_diagnostic_stdout()
    with pytest.raises(AssertionError, match="differs from recorded"):
        _check_cli_refusal_stdout("a7-control::diag-changed",
                                  "cli.backup-verify", stdout,
                                  _a_diagnostic_line(), stdout + " ")


# --- SPEC (cx) D-9 command-failure controls ------------------------------------

def _a_command_line() -> dict:
    return {"operation": "cli.session-end",
            "kind": "command-failure", "site": None, "code": 128}


def _a_command_streams() -> tuple[str, str]:
    """The recorded failed-push raw streams (real child output)."""
    step = json.loads((RECORDED_DIR / "cli.session-end"
                       / "failed-push.json").read_text(
                           encoding="utf-8"))["steps"][1]
    assert step["exit"] == 128
    return step["stdout"], step["stderr"]


def test_control_command_clean_passes():
    """The recorded failed-push streams pass both command clauses."""
    stdout, stderr = _a_command_streams()
    _check_live_exit("a7-control::cmd-clean", "cli", 128, 128,
                     [_a_command_line()], "cli.session-end")
    _check_command_failure_streams(
        "a7-control::cmd-clean", "cli.session-end", stdout, stderr,
        _a_command_line(), stdout, stderr)


def test_control_command_duplicate_lines_fail():
    with pytest.raises(AssertionError, match="2 witness lines"):
        _check_live_exit("a7-control::cmd-two", "cli", 128, 128,
                         [_a_command_line(), _a_command_line()],
                         "cli.session-end")


def test_control_command_wrong_operation_fails():
    line = _a_command_line()
    line["operation"] = "route.patch"
    with pytest.raises(AssertionError, match="unit 'cli.session-end'"):
        _check_live_exit("a7-control::cmd-op", "cli", 128, 128,
                         [line], "cli.session-end")


def test_control_command_non_null_site_fails():
    line = _a_command_line()
    line["site"] = "cli.session-end.nothing-touched"
    with pytest.raises(AssertionError, match="command line names site"):
        _check_live_exit("a7-control::cmd-site", "cli", 128, 128,
                         [line], "cli.session-end")


def test_control_command_malformed_shape_fails():
    extra = _a_command_line()
    extra["class"] = "WriteRefused"
    with pytest.raises(AssertionError, match="command line has shape"):
        _check_live_exit("a7-control::cmd-shape", "cli", 128, 128,
                         [extra], "cli.session-end")


def test_control_command_missing_code_fails():
    line = _a_command_line()
    del line["code"]
    with pytest.raises(AssertionError, match="command line has shape"):
        _check_live_exit("a7-control::cmd-nocode", "cli", 128, 128,
                         [line], "cli.session-end")


@pytest.mark.parametrize("code", [0, True, False, 128.0, "128", None])
def test_control_command_bad_code_fails(code):
    line = _a_command_line()
    line["code"] = code
    with pytest.raises(AssertionError, match="not a nonzero integer"):
        _check_live_exit("a7-control::cmd-code", "cli", 128, 128,
                         [line], "cli.session-end")


def test_control_command_wrong_exit_fails():
    with pytest.raises(AssertionError, match="witnessed command code 1"):
        _check_live_exit("a7-control::cmd-exit", "cli", 128, 128,
                         [{"operation": "cli.session-end",
                           "kind": "command-failure", "site": None,
                           "code": 1}], "cli.session-end")


def test_control_command_changed_stdout_fails():
    stdout, stderr = _a_command_streams()
    with pytest.raises(AssertionError, match="live stdout differs"):
        _check_command_failure_streams(
            "a7-control::cmd-stdout", "cli.session-end", stdout, stderr,
            _a_command_line(), stdout + " ", stderr)


def test_control_command_changed_stderr_fails():
    stdout, stderr = _a_command_streams()
    with pytest.raises(AssertionError, match="live stderr differs"):
        _check_command_failure_streams(
            "a7-control::cmd-stderr", "cli.session-end", stdout, stderr,
            _a_command_line(), stdout, stderr + " ")


def test_control_command_missing_live_streams_fails():
    stdout, stderr = _a_command_streams()
    with pytest.raises(AssertionError, match="live streams are missing"):
        _check_command_failure_streams(
            "a7-control::cmd-nolive", "cli.session-end", stdout, stderr,
            _a_command_line(), stdout, None)


def test_control_command_streams_without_line_fails():
    stdout, stderr = _a_command_streams()
    with pytest.raises(AssertionError, match="without a command-failure"):
        _check_command_failure_streams(
            "a7-control::cmd-noline", "cli.session-end", stdout, stderr,
            None, stdout, stderr)
