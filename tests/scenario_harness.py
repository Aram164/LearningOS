"""Effect-scenario harness: run a case in a fresh world, record, normalize, compare.

Implements SPEC §5.3 (PLAN D15/A12a). Each case builds a fresh ``rich_world``
fixture in its own directory, runs every step as a ``los`` child process with
controlled observations (SPEC §4), and records exit/stdout/stderr, the
canonical delta, new receipts, ledger deltas and a derived outcome.

Case-file fields beyond SPEC §5.2 (all documented in REPORT.md of the
introducing session): ``artifact_ids`` (default: the capability's
request-scoped id, else ``[]``), ``approval_kind`` (default
``"operator-approval"``), ``replay_only``, ``same_envelope_as`` (a step index
whose envelope file is resubmitted verbatim), ``git``
(``{failing_pre_commit, origin}`` fixture setup for session-end sequences),
and ``fixture_mtime`` (a file-level ISO 8601 instant, default
:data:`FIXTURE_MTIME_DEFAULT`). A case may carry its own ``observations``
object, which replaces the file-level one for that case. Every case's
override also carries ``"mtimes"``: every file directly under the fixture's
``work/inbox/``, mapped to ``fixture_mtime``.
``<ROOT>`` in request/argv strings is substituted with the fixture root;
prefer plain relative paths, which resolve against the fixture (children
run with cwd=root). ``<CASEDATA>`` substitutes the relative path to a copy
of the case's committed data directory
(``tests/scenarios/files/<operation>/<case-id>/``).

The caller merges file-level context into each case before calling
:func:`run_case`/:func:`run_sequence`: the case dict must carry the file's
``observations`` mapping and ``fixture_mtime`` value.
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import difflib
import json
import os
import re
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

import yaml

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
LOS = REPO_ROOT / "tools" / "los.py"
ARCH_SITE = TESTS_DIR / "arch_site"
CASES_DIR = TESTS_DIR / "scenarios" / "cases"
RECORDED_DIR = TESTS_DIR / "scenarios" / "recorded"
CASEDATA_DIR = TESTS_DIR / "scenarios" / "files"

FIXTURE_IDENTITY = ("Fixture", "fixture@local")
FIXTURE_COMMIT_MESSAGE = "fixture"
FIXTURE_MTIME_DEFAULT = "2026-09-28T09:00:00+02:00"

# Transaction ids are discovered only from declared keys (SPEC §5.3 rule 2,
# amendment (z) C8): never by pattern, never over free text.
_TX_KEY_NAMES = frozenset({"transaction_id", "receipt_id"})
_TX_KEY_SUFFIX = "_transaction_id"
_KEY_NAMES = frozenset({"request_id", "idempotency_key", "request_key"})
_STALE_SNAPSHOT = "STALE_SNAPSHOT"
_SHA256_RE = re.compile(r"sha256:[a-f0-9]{64}")
# D16 stderr rule (SPEC §5.3.4): present from S05, a no-op until S14 adds
# the `los: CODE: message` prefix.
_D16_RE = re.compile(r"^los: ([A-Z][A-Z0-9_]{2,}): ", re.MULTILINE)
# Elapsed-time redaction (SPEC §5.3 rule 3a, amendments (w) and (z) C8):
# validate.py --compact prints its own elapsed time, which session-end
# embeds in its payload. No observation seam covers monotonic(), so the
# harness redacts the operational timing instead of pinning the machine —
# but only in the validator's summary form, the one place it occurs.
_ELAPSED_RE = re.compile(
    r"(\d+ error\(s\), \d+ warning\(s\) — \S+ )\(\d+\.\ds\)")


def load_case_file(path: str | Path) -> dict:
    """Parse one ``tests/scenarios/cases/<operation>.yaml`` file."""
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def pretty(recording: dict) -> str:
    """Canonical pretty JSON for recordings and diffs."""
    return json.dumps(recording, indent=2, sort_keys=True,
                      ensure_ascii=False) + "\n"


def compare(recorded: dict, actual: dict) -> str | None:
    """A unified diff of the pretty JSON, or None when equal."""
    if recorded == actual:
        return None
    diff = difflib.unified_diff(
        pretty(recorded).splitlines(), pretty(actual).splitlines(),
        fromfile="recorded", tofile="actual", lineterm="")
    return "\n".join(diff) + "\n"


# --------------------------------------------------------------------------
# fixture
# --------------------------------------------------------------------------

def _build_fixture(name: str, container: Path) -> Path:
    if name != "rich_world":
        raise ValueError(f"unknown scenario fixture: {name}")
    sys.path.insert(0, str(TESTS_DIR))
    try:
        from conftest import build_mini_repo
        from scenario_fixtures import rich_world
    finally:
        del sys.path[0]
    root = build_mini_repo(container)
    rich_world(root)
    return root


def _git(root: Path, *args: str, env: dict | None = None) -> None:
    proc = subprocess.run(["git", *args], cwd=root, capture_output=True,
                          text=True, timeout=120, env=env or os.environ)
    if proc.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed: {proc.stderr[-1000:]}")


def _commit_fixture(root: Path, now_iso: str, git_setup: dict | None) -> None:
    # An explicit branch: the default branch name is environment-dependent
    # and leaks into session-end push output.
    _git(root, "init", "-q", "-b", "main")
    name, email = FIXTURE_IDENTITY
    _git(root, "config", "user.name", name)
    _git(root, "config", "user.email", email)
    # A repo-local identity lets session-end sequences commit; the dates of
    # those commits stay real time (git reads no seam) but no recording
    # observes .git, so they are invisible.
    _git(root, "add", "-A")
    env = dict(os.environ, GIT_AUTHOR_DATE=now_iso, GIT_COMMITTER_DATE=now_iso)
    _git(root, "commit", "-qm", FIXTURE_COMMIT_MESSAGE, env=env)
    git_setup = git_setup or {}
    if git_setup.get("failing_pre_commit"):
        hook = root / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        hook.chmod(0o755)
    if git_setup.get("origin"):
        _git(root, "remote", "add", "origin", str(git_setup["origin"]))


def _inbox_mtimes(root: Path, fixture_mtime: str) -> dict:
    """Every file directly under the fixture's inbox, mapped to one instant."""
    inbox = root / "work" / "inbox"
    if not inbox.is_dir():
        return {}
    return {path.relative_to(root).as_posix(): fixture_mtime
            for path in sorted(inbox.iterdir()) if path.is_file()}


def _write_observations(workdir: Path, file_observations: dict,
                        operation: str, case_id: str, root: Path,
                        fixture_mtime: str) -> Path:
    observations = copy.deepcopy(file_observations)
    observations["ids"] = {
        "seed": f"{operation}/{case_id}",
        "counter_file": str(workdir / "ids.counter"),
    }
    observations["mtimes"] = _inbox_mtimes(root, fixture_mtime)
    path = workdir / "observations.json"
    path.write_text(json.dumps(observations, indent=2, sort_keys=True)
                    + "\n", encoding="utf-8")
    return path


def prepare_transcript_fixture(fixture_name: str, container: str | Path, *,
                               seed: str,
                               now_iso: str = "2026-10-01T09:00:00+02:00"
                               ) -> dict:
    """Build the world one procedure transcript runs in (SPEC §7.1, PLAN D11).

    The one shared function behind ``los-fixture`` (Candidate A, Scrut) and
    the in-repo runner's built-in first block (Candidate B): amendment (o)
    items 1–3 plus the ``"mtimes"`` of amendment (z) item 5. Item 4 (the
    ``LOS_FX``/``LOS_OBSERVATIONS``/``TZ`` exports) is caller-side: shell
    output for Scrut, process env for the runner.

    ``container`` is an existing fresh directory; the fixture root is built
    inside it and ``observations.json``/``ids.counter`` sit next to it.
    ``seed`` is the transcript file name. Returns ``{"root", "observations"}``.
    """
    container = Path(container)
    root = _build_fixture(fixture_name, container)
    _commit_fixture(root, now_iso, None)
    observations = {
        "now": now_iso,
        "ids": {"seed": seed,
                "counter_file": str(container / "ids.counter")},
        "mtimes": _inbox_mtimes(root, FIXTURE_MTIME_DEFAULT),
    }
    observations_path = container / "observations.json"
    observations_path.write_text(json.dumps(observations, indent=2,
                                            sort_keys=True) + "\n",
                                 encoding="utf-8")
    return {"root": root, "observations": observations_path}


# --------------------------------------------------------------------------
# launching (SPEC amendment (m))
# --------------------------------------------------------------------------

class _CaseContext:
    def __init__(self, *, root: Path, workdir: Path, observations_path: Path,
                 operation: str, case_id: str):
        self.root = root
        self.workdir = workdir
        self.observations_path = observations_path
        self.operation = operation
        self.case_id = case_id
        self.log_path = workdir / "audit.jsonl"
        self.tokens: list[str] = []
        self.casedata = CASEDATA_DIR / operation / case_id


#: Scenario operations whose children observe a controlled Time Machine
#: input (SPEC (bm), disposition 3): exactly the two health-report
#: operations, nothing else.
_HEALTH_SCENARIO_OPERATIONS = frozenset({"cli.health-report", "health.report"})

#: The controlled `tmutil` the health scenarios observe: exit 1 with the
#: no-destination report on stderr, the external input producing the
#: already recorded backup row. Production health code is untouched.
_TMUTIL_SHIM = "#!/bin/sh\necho 'No destinations configured' >&2\nexit 1\n"


def _health_command_dir(ctx: _CaseContext) -> Path:
    """The directory holding one health case's controlled `tmutil`.

    It lives directly under the case workdir — outside the fixture root,
    never on any live path — and holds only the shim, so prepending it to
    the child's PATH can shadow nothing else.
    """
    bindir = ctx.workdir / "health-bin"
    bindir.mkdir(parents=True, exist_ok=True)
    shim = bindir / "tmutil"
    shim.write_text(_TMUTIL_SHIM, encoding="utf-8")
    shim.chmod(0o755)
    return bindir


def _launch_env(ctx, token: str, extra_env: dict | None) -> dict:
    env = dict(os.environ)
    env["LOS_ARCH_LAUNCH_TOKEN"] = token
    env["LOS_ARCH_AUDIT_LOG"] = str(ctx.log_path)
    env["LOS_OBSERVATIONS"] = str(ctx.observations_path)
    env["LOS_ARCH_RENDER_CHECK"] = "1"
    env["TZ"] = "Europe/Berlin"
    env["PYTHONPATH"] = str(ARCH_SITE) + os.pathsep + env.get("PYTHONPATH", "")
    if extra_env:
        env.update(extra_env)
    # A recovery context carries no operation and is never a health case.
    if getattr(ctx, "operation", None) in _HEALTH_SCENARIO_OPERATIONS:
        # Scoped after extras: the health observation must not depend on
        # whether the host carries macOS backup tooling or a configured
        # backup, so the controlled input is never dropped.
        bindir = _health_command_dir(ctx)
        path = env.get("PATH")
        env["PATH"] = (str(bindir) if not path
                       else str(bindir) + os.pathsep + path)
    return env


def launch(ctx: _CaseContext, argv: list[str],
           extra_env: dict | None = None) -> subprocess.CompletedProcess:
    """Run one child with its own audit window and a fresh launch token."""
    import arch_audit_hook

    token = f"scenario-{uuid.uuid4().hex}"
    ctx.tokens.append(token)
    env = _launch_env(ctx, token, extra_env)
    arch_audit_hook.install(str(ctx.log_path))
    try:
        # cwd=root: case-relative file references resolve inside the
        # fixture, so payloads (and the intent hashes covering them) hold
        # no per-run absolute path.
        proc = subprocess.run(argv, capture_output=True, text=True,
                              timeout=120, env=env, cwd=ctx.root)
    finally:
        arch_audit_hook.uninstall()
    arch_audit_hook.assert_capture_ok()
    return proc


def launch_many(ctx, argvs: list[list[str]],
                extra_envs: list[dict | None] | None = None,
                timeout: int = 300) -> list[subprocess.CompletedProcess]:
    """Run children concurrently under one shared audit window.

    Each child gets its own fresh launch token; ``check_witnesses`` still
    requires exactly one ``subprocess.Popen`` record per token. Used by the
    recovery scenarios (SPEC A16); the effect scenarios keep ``launch``.
    """
    import arch_audit_hook

    if extra_envs is None:
        extra_envs = [None] * len(argvs)
    assert len(extra_envs) == len(argvs)
    arch_audit_hook.install(str(ctx.log_path))
    try:
        handles = []
        for argv, extra in zip(argvs, extra_envs, strict=True):
            token = f"scenario-{uuid.uuid4().hex}"
            ctx.tokens.append(token)
            handles.append(subprocess.Popen(
                argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, env=_launch_env(ctx, token, extra), cwd=ctx.root))
        results = []
        for argv, handle in zip(argvs, handles, strict=True):
            try:
                stdout, stderr = handle.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                handle.kill()
                stdout, stderr = handle.communicate()
            results.append(subprocess.CompletedProcess(
                argv, handle.returncode, stdout, stderr))
    finally:
        arch_audit_hook.uninstall()
    arch_audit_hook.assert_capture_ok()
    return results


def check_witnesses(ctx: _CaseContext) -> None:
    """Fail unless every issued token launched exactly once and fully witnessed."""
    import arch_audit_hook
    from arch_writes_fixtures import witness_failures

    records = arch_audit_hook.read_log(ctx.log_path)
    popens = [rec for rec in records if rec.get("event") == "subprocess.Popen"]
    problems = []
    for token in ctx.tokens:
        count = sum(1 for rec in popens if rec.get("token") == token)
        if count != 1:
            problems.append(
                f"token {token!r} has {count} subprocess.Popen records, want 1")
    problems.extend(witness_failures(records))
    problems.extend(render_violations(records))
    if problems:
        raise AssertionError("audit witness failure:\n" + "\n".join(problems))


def render_violations(records: list[dict]) -> list[str]:
    """A18 violations: audited I/O while a renderer ran (SPEC §3.5b).

    Every record whose ``render`` marker is not null fails the case as
    ``<operation>::<callback>::<event>``. Records without the field
    (install/completion witnesses) count as unmarked.
    """
    problems = []
    for rec in records:
        render = rec.get("render")
        if render is None:
            continue
        try:
            operation, callback = render
        except (TypeError, ValueError):
            problems.append(f"A18 malformed render marker: {render!r}")
            continue
        problems.append(
            f"A18 {operation}::{callback}::{rec.get('event')}: "
            f"renderer performed audited I/O")
    return problems


def check_render_purity_error(stderr: str) -> None:
    """Fail as an A18 violation when a child raised RenderPurityError."""
    import re

    if "RenderPurityError" not in stderr:
        return
    match = re.search(r"RenderPurityError: (\S+)", stderr)
    if match:
        try:
            operation, callback, _reason = match.group(1).split("::")
        except ValueError:
            operation, callback = "unknown", "unknown"
    else:
        operation, callback = "unknown", "unknown"
    raise AssertionError(
        f"A18 {operation}::{callback}::RenderPurityError: "
        f"renderer failed the purity check")


# --------------------------------------------------------------------------
# envelopes and argv
# --------------------------------------------------------------------------

def _substitute(value, ctx: _CaseContext):
    import os.path as _osp

    casedata_rel = _osp.relpath(ctx.workdir / "casedata", ctx.root)
    if isinstance(value, str):
        return (value.replace("<ROOT>", str(ctx.root))
                .replace("<CASEDATA>", casedata_rel))
    if isinstance(value, list):
        return [_substitute(item, ctx) for item in value]
    if isinstance(value, dict):
        return {key: _substitute(item, ctx) for key, item in value.items()}
    return value


def _default_artifact_ids(capability: str, key: str) -> list[str]:
    sys.path.insert(0, str(REPO_ROOT / "tools"))
    try:
        from learning_os.contracts.gateway import request_artifact_id
    finally:
        del sys.path[0]
    try:
        return [request_artifact_id(capability, key)]
    except ValueError:
        return []


def build_envelope(ctx: _CaseContext, operation: str, step: dict,
                   step_index: int) -> Path:
    """Seal the step's envelope with guards from the live fixture (SPEC §5.2)."""
    sys.path.insert(0, str(TESTS_DIR))
    try:
        from gateway_helpers import approved_v2_envelope
    finally:
        del sys.path[0]
    reuse = step.get("same_envelope_as")
    path = ctx.workdir / f"envelope-s{step_index}.json"
    if reuse is not None:
        source = ctx.workdir / f"envelope-s{reuse}.json"
        path.write_bytes(source.read_bytes())
        return path
    key = f"scenario-{operation}-{ctx.case_id}-s{step_index}"
    payload = _substitute(copy.deepcopy(step.get("request", {})), ctx)
    if "artifact_ids" in step:
        artifact_ids = list(step["artifact_ids"])
    else:
        artifact_ids = _default_artifact_ids(operation, key)
    envelope = approved_v2_envelope(
        ctx.root, capability=operation, payload=payload,
        artifact_ids=artifact_ids, idempotency_key=key)
    approval_kind = step.get("approval_kind", "operator-approval")
    if approval_kind != "operator-approval":
        # intent_sha256 covers no approval kind, so the binding survives.
        envelope["approval"]["kind"] = approval_kind
    path.write_text(json.dumps(envelope, indent=2, sort_keys=True)
                    + "\n", encoding="utf-8")
    return path


def _cli_command_for(operation: str, root: Path) -> str:
    if operation.startswith("cli."):
        return operation[len("cli."):]
    sys.path.insert(0, str(REPO_ROOT / "tools"))
    try:
        from learning_os.contracts.capability_catalog import command_definitions
    finally:
        del sys.path[0]
    return command_definitions(root)[operation].cli_command


def request_to_argv(operation: str, request: dict, root: Path) -> list[str]:
    """Render a gateway request to CLI flags for a capability command.

    Each field is rendered by its own argparse action in the operation's
    subparser (SPEC §5.2 "CLI transport", amendment (x) C3).
    """
    sys.path.insert(0, str(REPO_ROOT / "tools"))
    try:
        import los
        from learning_os.contracts.payloads import subparsers
    finally:
        del sys.path[0]
    parser = subparsers(los.build_parser())[_cli_command_for(operation, root)]
    remaining = dict(request)
    argv: list[str] = []
    for action in parser._actions:
        if action.dest in ("help", "func"):
            continue
        if action.option_strings or action.dest not in remaining:
            continue
        value = remaining.pop(action.dest)
        argv.extend(_render_positional(action, value))
    for action in parser._actions:
        if not action.option_strings or action.dest not in remaining:
            continue
        value = remaining.pop(action.dest)
        argv.extend(_render_option(action, value))
    if remaining:
        raise ValueError(
            f"request keys have no CLI flag for {operation}: "
            f"{sorted(remaining)}")
    return argv


def _is_json_object_action(action) -> bool:
    """Whether the action converts with the shared ``json_object`` callable."""
    sys.path.insert(0, str(REPO_ROOT / "tools"))
    try:
        from learning_os.contracts.payloads import json_object
    finally:
        del sys.path[0]
    return action.type is json_object


def _scalar_text(action, value) -> str:
    """One value as one argv word: a JSON string only for ``json_object``."""
    if isinstance(value, (dict, list)):
        if _is_json_object_action(action):
            return json.dumps(value, sort_keys=True)
        return str(value)
    return str(value)


def _takes_values(action) -> bool:
    """A list-valued action: ``nargs`` of ``+``, ``*`` or a positive int."""
    return action.nargs in ("+", "*") or (
        isinstance(action.nargs, int) and action.nargs > 0)


def _render_positional(action, value) -> list[str]:
    if _takes_values(action) and isinstance(value, list):
        return [_scalar_text(action, item) for item in value]
    if isinstance(value, bool):
        return [str(value)]
    if isinstance(value, (dict, list)):
        if _is_json_object_action(action):
            return [json.dumps(value, sort_keys=True)]
        return [str(value)]
    return [str(value)]


def _render_option(action, value) -> list[str]:
    flag = action.option_strings[0]
    if isinstance(action, (argparse._StoreTrueAction,
                           argparse._StoreFalseAction)):
        if value is None:
            return []
        return [flag] if value != action.default else []
    if isinstance(action, argparse._AppendAction) and isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend([flag, _scalar_text(action, item)])
        return out
    if _takes_values(action):
        items = value if isinstance(value, list) else [value]
        return [flag, *[_scalar_text(action, item) for item in items]]
    if value is None or value is False:
        return []
    if value is True:
        return [flag]
    if isinstance(value, list):
        out = []
        for item in value:
            out.extend(_render_option(action, item))
        return out
    if isinstance(value, dict):
        return [flag, _scalar_text(action, value)]
    return [flag, str(value)]


def step_argv(ctx: _CaseContext, operation: str, step: dict,
              step_index: int) -> list[str]:
    """The child argv for one step (SPEC §5.2 transports)."""
    transport = step["transport"]
    if transport == "gateway":
        envelope_path = build_envelope(ctx, operation, step, step_index)
        argv = ["--root", str(ctx.root), "capability", operation,
               "--payload-file", str(envelope_path)]
        if step.get("replay_only"):
            argv.append("--replay-only")
        return [sys.executable, str(LOS), *argv]
    if transport == "cli":
        if "argv" in step:
            rest = [str(item) for item in
                    _substitute(list(step["argv"]), ctx)]
        else:
            request = _substitute(copy.deepcopy(step.get("request", {})), ctx)
            rest = [_cli_command_for(operation, ctx.root),
                    *request_to_argv(operation, request, ctx.root)]
        return [sys.executable, str(LOS), "--root", str(ctx.root), *rest]
    raise ValueError(f"unknown transport: {transport}")


# --------------------------------------------------------------------------
# recording
# --------------------------------------------------------------------------

def _read_ledger_file(root: Path, *parts: str):
    path = root.joinpath(*parts)
    if not path.is_file():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _session_ledger_path(root: Path):
    sys.path.insert(0, str(REPO_ROOT / "tools"))
    try:
        from learning_os.store.session_ledger import (
            _session_ledger,
        )
    finally:
        del sys.path[0]
    return _session_ledger(root)


def _snapshot_ledgers(root: Path) -> dict:
    ledgers = {
        "revisions": _read_ledger_file(
            root, "operations", "transactions", "revisions.yaml"),
        "idempotency": _read_ledger_file(
            root, "operations", "transactions", "idempotency.yaml"),
        "session": None,
    }
    ledger_path = _session_ledger_path(root)
    if ledger_path.is_file():
        ledgers["session"] = json.loads(ledger_path.read_text(
            encoding="utf-8"))
    return ledgers


def derive_outcome(exit_code: int, stdout: str, stderr: str,
                   stdout_json, new_receipts: list) -> str:
    """Classify one step's outcome for the recording."""
    if exit_code != 0 and new_receipts:
        return "committed-with-failure"
    if exit_code == 0:
        return "ok"
    if isinstance(stdout_json, dict) and isinstance(
            stdout_json.get("error"), dict):
        code = stdout_json["error"].get("code")
        if code == "INTERNAL_FAILURE":
            return "diagnostic-failure"
        return "refused"
    if "Traceback (most recent call last)" in stderr:
        return "diagnostic-failure"
    if exit_code in (2, 3):
        return "refused"
    if exit_code > 0:
        # A nonzero, non-refusal exit is a failed external step (git, the
        # validator): session-end passes those codes through.
        return "diagnostic-failure"
    return "unknown"


def _run_step(ctx: _CaseContext, file_operation: str, step: dict,
              step_index: int) -> dict:
    import arch_effects

    operation = step.get("operation", file_operation)
    before_tree = arch_effects.capture_tree(ctx.root)
    receipts_dir = ctx.root / "operations" / "transactions"
    before_receipts = [p.name for p in receipts_dir.glob("transaction-*.yaml")
                       ] if receipts_dir.is_dir() else []
    before_ledgers = _snapshot_ledgers(ctx.root)
    argv = step_argv(ctx, operation, step, step_index)
    proc = launch(ctx, argv)
    check_render_purity_error(proc.stderr)
    after_tree = arch_effects.capture_tree(ctx.root)
    after_ledgers = _snapshot_ledgers(ctx.root)
    receipts = arch_effects.new_receipts(before_receipts, ctx.root)
    changed = {}
    for path in sorted(set(before_tree) | set(after_tree)):
        if before_tree.get(path) != after_tree.get(path):
            changed[path] = after_tree.get(path)
    try:
        stdout_json = json.loads(proc.stdout) if proc.stdout.strip() else None
    except json.JSONDecodeError:
        stdout_json = None
    revisions = {}
    if before_ledgers["revisions"] != after_ledgers["revisions"]:
        revisions = {"before": before_ledgers["revisions"],
                     "after": after_ledgers["revisions"]}
    idempotency = {}
    if before_ledgers["idempotency"] != after_ledgers["idempotency"]:
        idempotency = {"before": before_ledgers["idempotency"],
                       "after": after_ledgers["idempotency"]}
    session_changed = None
    if not (before_ledgers["session"] is None
            and after_ledgers["session"] is None):
        session_changed = {"before": before_ledgers["session"],
                           "after": after_ledgers["session"]}
    return {
        "exit": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "stdout_json": stdout_json,
        "canonical_changed": changed,
        "receipts": receipts,
        "revisions_changed": revisions,
        "idempotency_changed": idempotency,
        "session_ledger_changed": session_changed,
        "outcome": derive_outcome(proc.returncode, proc.stdout, proc.stderr,
                                  stdout_json, receipts),
    }


# --------------------------------------------------------------------------
# normalize (SPEC §5.3)
# --------------------------------------------------------------------------

def _walk_strings(node, func):
    if isinstance(node, str):
        return func(node)
    if isinstance(node, list):
        return [_walk_strings(item, func) for item in node]
    if isinstance(node, dict):
        return {func(key) if isinstance(key, str) else key:
                _walk_strings(value, func)
                for key, value in node.items()}
    return node


def _is_tx_key(name) -> bool:
    return (isinstance(name, str)
            and (name in _TX_KEY_NAMES or name.endswith(_TX_KEY_SUFFIX)))


def _discover_identities(steps: list) -> tuple[set, set, set]:
    """Identity values per SPEC §5.3 rule 2 (amendments (x) C2 and (z) C8).

    A value under a JSON key named ``transaction_id``, ending in
    ``_transaction_id`` or named ``receipt_id``, plus each recorded
    receipt's own transaction id (its ``id`` field); a value under a JSON
    key named ``request_id``, ``idempotency_key`` or ``request_key``; or a
    ``sha256:`` value under a JSON key whose name contains ``snapshot``
    (or under ``expected``/``actual`` in a ``STALE_SNAPSHOT`` error's
    details). Parsed stdout JSON, receipts and ledgers are walked; nothing
    is discovered by regex over free text, and no string is classified by
    pattern alone.
    """
    tx: set[str] = set()
    keys: set[str] = set()
    snaps: set[str] = set()

    def visit(node) -> None:
        if isinstance(node, str):
            return
        if isinstance(node, list):
            for item in node:
                visit(item)
            return
        if not isinstance(node, dict):
            return
        if node.get("code") == _STALE_SNAPSHOT and isinstance(
                node.get("details"), dict):
            details = node["details"]
            for leaf in ("expected", "actual"):
                value = details.get(leaf)
                if (isinstance(value, str)
                        and _SHA256_RE.fullmatch(value) is not None):
                    snaps.add(value)
        for name, value in node.items():
            if _is_tx_key(name):
                if isinstance(value, str) and value:
                    tx.add(value)
            elif isinstance(name, str) and name in _KEY_NAMES:
                if isinstance(value, str) and value:
                    keys.add(value)
            elif (isinstance(name, str) and "snapshot" in name
                    and isinstance(value, str)
                    and _SHA256_RE.fullmatch(value) is not None):
                snaps.add(value)
            visit(value)

    for step in steps:
        for section in ("stdout_json", "receipts", "revisions_changed",
                        "idempotency_changed", "session_ledger_changed"):
            visit(step.get(section))
        for receipt in step.get("receipts") or []:
            if isinstance(receipt, dict):
                own = receipt.get("id")
                if isinstance(own, str) and own:
                    tx.add(own)
    return tx, keys, snaps


def _ledger_strings(node) -> list[str]:
    """Every string in a recorded ledger, in sorted JSON-path order."""
    out: list[str] = []

    def visit(node) -> None:
        if isinstance(node, str):
            out.append(node)
        elif isinstance(node, dict):
            for name in sorted(node, key=str):
                visit(name)
                visit(node[name])
        elif isinstance(node, list):
            for item in node:
                visit(item)

    visit(node)
    return out


def _number_family(values: set, texts: list, ledger_runs: list,
                   prefix: str) -> dict:
    """Number one token family by first appearance (amendment (x) C5).

    Across stdout, stderr and receipts first (every step, in order), then
    across the recorded ledgers in walk order. The value itself breaks ties,
    so the numbering is total.
    """
    def rank(value: str):
        for index, text in enumerate(texts):
            at = text.find(value)
            if at >= 0:
                return (0, index, at)
        for index, run in enumerate(ledger_runs):
            if value in run:
                return (1, index, run.index(value))
        return (2, 0, 0)

    return {value: f"{prefix}{n + 1}"
            for n, value in enumerate(sorted(values, key=lambda v: (rank(v), v)))}


def _single_steps(recording: dict) -> list:
    if isinstance(recording.get("steps"), list):
        return recording["steps"]
    return [recording]


def normalize(recording: dict, root: str | Path) -> dict:
    """Apply the SPEC §5.3 rules; returns a new recording.

    For sequences the TX/KEY/SNAP mapping is shared across steps so that
    cross-references (exact replay, snapshot chains) keep one token.
    """
    root = str(root)
    materials = str(Path(root).parent / "materials")
    learningos = str(Path(root).parent)
    recording = _walk_strings(
        copy.deepcopy(recording),
        lambda text: text.replace(root, "<ROOT>").replace(
            materials, "<MATERIALS>").replace(
            learningos, "<LEARNINGOS>"))
    steps = _single_steps(recording)
    tx_values, key_values, snap_values = _discover_identities(steps)
    texts = []
    for step in steps:
        texts.append(step.get("stdout", ""))
        texts.append(step.get("stderr", ""))
        texts.append(json.dumps(step.get("receipts", []), sort_keys=True))
    ledger_runs = []
    for step in steps:
        for section in ("revisions_changed", "idempotency_changed",
                        "session_ledger_changed"):
            ledger_runs.append(_ledger_strings(step.get(section)))
    mapping = {}
    mapping.update(_number_family(tx_values, texts, ledger_runs, "TX"))
    mapping.update(_number_family(key_values, texts, ledger_runs, "KEY"))
    mapping.update(_number_family(snap_values, texts, ledger_runs, "SNAP"))

    def _map(text: str) -> str:
        # Longest first, so `request-<key>` maps as a unit before `<key>`.
        for original in sorted(mapping, key=len, reverse=True):
            if original in text:
                text = text.replace(original, mapping[original])
        return text

    recording = _walk_strings(recording, _map)
    recording = _walk_strings(
        recording, lambda text: _ELAPSED_RE.sub(r"\1(Xs)", text))
    # D16 stderr rule, last. A no-op until S14 introduces the prefix.
    for step in _single_steps(recording):
        step["stderr"] = _D16_RE.sub("los: ", step.get("stderr", ""))
    return recording


def reconcile_recorded(recording: dict) -> list[str]:
    """A2 report-mode check over a recording: every recorded canonical change
    must have an owning receipt entry. Prints nothing; returns violations."""
    violations = []
    steps = recording.get("steps")
    units = ([(index, step) for index, step in enumerate(steps)]
             if isinstance(steps, list) else [(None, recording)])
    for index, unit in units:
        entries = []
        for receipt in unit.get("receipts", []):
            writes = receipt.get("writes") if isinstance(receipt, dict) else None
            if isinstance(writes, list):
                entries.extend(
                    (row.get("path"), row.get("sha256_after"))
                    for row in writes if isinstance(row, dict))
        for path, after in sorted(unit.get("canonical_changed", {}).items()):
            if not any(entry_path == path and sha_after == after
                       for entry_path, sha_after in entries):
                where = f"step {index} " if index is not None else ""
                violations.append(
                    f"{where}unaccounted canonical change: {path}")
    return violations


# --------------------------------------------------------------------------
# entry points
# --------------------------------------------------------------------------

def _prepare_world(case: dict, operation: str, workdir: Path
                   ) -> _CaseContext:
    workdir = Path(workdir)
    container = workdir / "fx"
    root = _build_fixture(case.get("fixture", "rich_world"), container)
    now_iso = case["observations"]["now"]
    _commit_fixture(root, now_iso, case.get("git"))
    observations_path = _write_observations(
        workdir, case["observations"], operation, case["id"], root,
        case.get("fixture_mtime", FIXTURE_MTIME_DEFAULT))
    # The case's data directory, copied to a stable depth beside the
    # fixture so <CASEDATA> substitutes a relative path: an absolute
    # committed path would leak the checkout location into intent hashes.
    committed = CASEDATA_DIR / operation / case["id"]
    if committed.is_dir():
        import shutil

        shutil.copytree(committed, workdir / "casedata")
    return _CaseContext(root=root, workdir=workdir,
                        observations_path=observations_path,
                        operation=operation, case_id=case["id"])


#: ``(witness file, "<operation>:<case-id>")`` -> the ``(operation, site)``
#: pairs that case's own run witnessed, for every case this process ran
#: through :func:`run_case`/:func:`run_sequence` while
#: ``LOS_SITE_WITNESS_FILE`` was set (SPEC (bh)). A9 attributes a declared
#: site to a case that declares it from this map, not from the shared
#: session file alone.
CASE_SITE_WITNESSES: dict[tuple[str, str], set[tuple[str, str]]] = {}


@contextlib.contextmanager
def _case_site_witnesses(operation: str, case_id: str):
    """Collect one case's witness lines privately, then hand them on (bh).

    The case runs against a private witness file, so its children write
    only that case's lines there. Afterwards the lines are appended
    unchanged, in order, to the witness file that was set, and only then
    are their non-null sites attributed to the case. A failed append is
    swallowed, as the hook swallows one (SPEC (bf) item 10.2): the case
    stays unattributed and the missing line fails the A9 match.
    """
    from arch_audit_hook import SITE_WITNESS_ENV

    dest = os.environ.get(SITE_WITNESS_ENV)
    if not dest:
        yield
        return
    fd, private = tempfile.mkstemp(prefix="los-case-sites-", suffix=".jsonl")
    os.close(fd)
    os.environ[SITE_WITNESS_ENV] = private
    try:
        yield
    finally:
        os.environ[SITE_WITNESS_ENV] = dest
        data = Path(private).read_bytes()
        Path(private).unlink()
        try:
            with open(dest, "ab") as handle:
                handle.write(data)
        except OSError:
            pass
        else:
            sites = CASE_SITE_WITNESSES.setdefault(
                (dest, f"{operation}:{case_id}"), set())
            for line in data.decode("utf-8", "replace").splitlines():
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                if isinstance(record, dict) \
                        and isinstance(record.get("site"), str):
                    sites.add((record.get("operation"), record["site"]))


def run_case(case: dict, operation: str, workdir: str | Path) -> dict:
    """Run one non-sequence case; returns the normalized §5.3 recording."""
    if case.get("kind") == "sequence":
        raise ValueError("use run_sequence for sequence cases")
    with _case_site_witnesses(operation, case["id"]):
        ctx = _prepare_world(case, operation, Path(workdir))
        recording = _run_step(ctx, operation, case, 0)
        check_witnesses(ctx)
    return normalize(recording, ctx.root)


def run_sequence(case: dict, operation: str, workdir: str | Path) -> dict:
    """Run one sequence case in a single world; returns {"steps": [...]}."""
    with _case_site_witnesses(operation, case["id"]):
        ctx = _prepare_world(case, operation, Path(workdir))
        steps = []
        for index, step in enumerate(case.get("steps", [])):
            full = {"operation": operation, **step}
            result = _run_step(ctx, operation, full, index)
            result["step"] = index
            result["transport"] = step["transport"]
            if step["transport"] == "gateway":
                result["operation"] = full["operation"]
            elif "argv" in step:
                result["argv"] = [str(item) for item in step["argv"]]
            else:
                request = _substitute(
                    copy.deepcopy(step.get("request", {})), ctx)
                result["argv"] = [
                    _cli_command_for(full["operation"], ctx.root),
                    *request_to_argv(full["operation"], request, ctx.root)]
            steps.append(result)
        check_witnesses(ctx)
    return normalize({"steps": steps}, ctx.root)
