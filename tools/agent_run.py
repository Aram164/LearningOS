#!/usr/bin/env python3
"""Experimental CLI plan runner; canonical writes still use the gateway.

``use`` accepts a task, operation id or verb; ``describe: true`` reads its
contract. Log steps require an explicit, unique ``key`` stable across retries.
Write plans require a stable ``session_id``; presealed gateway envelopes
must already bind that session. ``on_error`` defaults to ``stop``; explicitly
choose ``continue`` to keep running independent steps after a failure.
Only operations explicitly declaring read effects are reads. Derived, canonical
and unknown effects are write barriers for both ``argv`` and ``use``.
Dependencies mean completion of successful receipted writes, not persistence
of their effects after later writes. Before a dependent read, the current
projection must match a successful write at or after the latest required write
in this plan's execution order. Unrecognised
projection changes refuse; the CLI's own freshness/snapshot guards still run.

Each summary has a UTF-8 byte budget; report_max_bytes caps all stdout,
including metadata. Every run retains a private full report and raw journals.
Use --expand-report PATH [--step ID] to verify and retrieve complete output.
``clusters: true`` retains omission counts and an executable full-scan route;
it neither makes learner decisions nor implements bulk mutations. Optional
preflight reuses the existing validation cache under its complete pins,
refusing on any error or unusable validation result. It never replaces gateway validation.

Example::

    {"session_id": "agent-session-42", "on_error": "stop", "steps": [
      {"id": "boot", "use": "open-work-or-priority-question",
       "args": ["--brief"], "summary": {"fields": ["counts.modules"]}},
      {"id": "note", "kind": "log", "text": "...", "key": "intent-42"},
      {"id": "after", "use": "inspect", "args": ["unit-demo"],
       "depends_on": ["note"]}
    ]}

Exit codes: 0 all steps succeeded; 3 a step failed/was blocked; 2 invalid plan.
"""
from __future__ import annotations

import argparse
import fnmatch
import io
import json
import math
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from pathlib import Path

from learning_os.app.projection_readiness import observe as _observe_projection
from learning_os.domain.codes import (
    DISCOVERY_FAILED,
    INVALID_REQUEST,
    INVALID_STEP_OUTPUT,
    PREFLIGHT_FAILED,
    REPORT_BUDGET_TOO_SMALL,
    ROOT_MISMATCH,
    SESSION_MISMATCH,
    SESSION_REQUIRED,
    VALIDATION_FAILED,
)
from learning_os.store.contracts.agent_plans import parse_controls

TOOLS = Path(__file__).resolve().parent


class AgentRunError(Exception):
    def __init__(self, message: str, code: str = INVALID_REQUEST):
        super().__init__(message)
        self.code = code


def _declared_read(namespace) -> bool:
    """True when this parsed step's operation declares a read mode holding for it.

    Core owns the declaration; the plan can never claim it. The registered
    effect stays the write barrier for every other mode of the operation.
    """
    from learning_os.app.registry import REGISTRY

    entry = REGISTRY.get(getattr(namespace, "_operation", None))
    return entry is not None and entry.read_when is not None and bool(entry.read_when(namespace))


def _json(value) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    except (ValueError, TypeError) as exc:
        raise AgentRunError("output must be finite JSON", INVALID_STEP_OUTPUT) from exc


def _finite_number(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise AgentRunError("nonfinite JSON number in step output", INVALID_STEP_OUTPUT)
    return number


@contextmanager
def _session_environment(session_id):
    previous = os.environ.get("LOS_SESSION_ID")
    if session_id is not None:
        os.environ["LOS_SESSION_ID"] = session_id
    try:
        yield
    finally:
        if session_id is not None:
            if previous is None:
                os.environ.pop("LOS_SESSION_ID", None)
            else:
                os.environ["LOS_SESSION_ID"] = previous


def resolve_use(use: str, index: dict) -> str:
    """Map a task id, operation id, or verb to the canonical CLI verb."""
    if use in index.get("verbs", []):
        return use
    operation_to_verb = {op: verb for verb, op in index.get("verb_to_operation", {}).items()}
    if use in operation_to_verb:
        return operation_to_verb[use]
    if use in index.get("task_to_use", {}):
        return index["task_to_use"][use]
    raise AgentRunError(f"unknown task, capability, or verb: {use}")


def build_index(root: Path, executor, *, resolve_tasks: bool = True) -> dict:
    """Use the executing parser and selected root's capability catalogue."""
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    from learning_os.adapters.cli_parser import build_parser
    from learning_os.app.registry import REGISTRY, OperationEffects

    parser = getattr(executor, "parser", None) or build_parser()
    choices = parser._subparsers._group_actions[0].choices  # noqa: SLF001
    verb_to_operation = {}
    for name, sub in choices.items():
        operation = getattr(sub, "_defaults", {}).get("_operation")
        if operation:
            verb_to_operation[name] = operation
    # The executing parser/registry owns effects for every plan shape. Only
    # an explicitly declared read is a read. Neither invocation kind nor
    # task discovery can weaken the default barrier for undeclared effects.
    index = {"verbs": sorted(choices), "verb_to_operation": verb_to_operation,
             "task_to_use": {}, "write_verbs": [name for name in choices
                 if (entry := REGISTRY.get(verb_to_operation.get(name))) is None
                 or entry.effects != OperationEffects.READ]}
    if not resolve_tasks:
        return index  # Explicit argv/log steps need no task prose expansion.
    if hasattr(executor, "parser"):
        from learning_os.store.contracts.verb_catalogue import (
            VerbCatalogueError,
            build_verb_catalogue,
        )
        try:
            catalogue = build_verb_catalogue(root)
        except VerbCatalogueError as exc:
            raise AgentRunError(f"capability discovery failed: {exc}", DISCOVERY_FAILED) from exc
        compact = {"verbs": [row.as_dict() for row in catalogue.verbs],
                   "tasks": [row.as_dict() for row in catalogue.tasks]}
    else:
        code, out, err = executor(["capabilities", "--json"], root)
        if code:
            raise AgentRunError(f"capability discovery failed: {err.strip()}", DISCOVERY_FAILED)
        compact = json.loads(out)
    task_to_use = {}
    operation_to_verb = {op: v for v, op in verb_to_operation.items()}
    for task in compact.get("tasks", []):
        segments = re.findall(r"`([^`]+)`", task.get("entry_read") or "")
        tokens = segments[0].split() if segments else []
        if not tokens:
            continue
        if tokens[0] == "capabilities" and len(tokens) > 1 and tokens[1] in operation_to_verb:
            task_to_use[task["id"]] = operation_to_verb[tokens[1]]
        elif tokens[0] in verb_to_operation:
            task_to_use[task["id"]] = tokens[0]
    index["task_to_use"] = task_to_use
    return index


def _field(payload, name):
    if isinstance(payload, dict):
        if payload.get(name):
            return payload[name]
        nested = payload.get("result")
        if isinstance(nested, dict):
            return nested.get(name)
    return None


def _receipt_ready(root: Path, result) -> tuple[bool, str]:
    if not isinstance(result, dict) or result.get("ok") is not True:
        return False, "write-not-ok"
    receipt = _field(result, "receipt_path")
    if not isinstance(receipt, str) or not receipt:
        return False, "receipt-missing-from-result"
    path = (root / receipt).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        return False, "receipt-not-on-disk-in-root"
    if not isinstance(_field(result, "snapshot_after"), str) or not _field(result, "snapshot_after"):
        return False, "snapshot-after-missing"
    return True, "completed"


def _writes_completed(root: Path, required: list) -> tuple[bool, str]:
    for result in required:
        ready, reason = _receipt_ready(root, result)
        if not ready:
            return ready, reason
    return True, "completed"


def writes_ready(root: Path, required: list, known: list) -> tuple[bool, str]:
    """Required writes completed; projection cannot precede their last write.

    Gateway success plus the retained receipt proves historical completion.
    ``known`` is in plan execution order. A later known write may supersede
    earlier effects; an earlier completion cannot stand in for a later one.
    An arbitrary different
    projection is not accepted as a successor, and actual reads retain their
    normal current-input guards. This also supports replaying a multi-write
    plan while its final projection is still current.
    """
    completed, reason = _writes_completed(root, required)
    if not completed:
        return False, reason
    signatures = {(_field(result, "receipt_path"), _field(result, "snapshot_after")) for result in required}
    positions = {(_field(result, "receipt_path"), _field(result, "snapshot_after")): i
                 for i, result in enumerate(known) if _receipt_ready(root, result)[0]}
    if not signatures or not signatures.issubset(positions):
        return False, "required-write-not-known"
    latest = max(positions[signature] for signature in signatures)
    snapshots = {_field(result, "snapshot_after") for result in known[latest:]
                 if _receipt_ready(root, result)[0]}
    obs = _observe_projection(root, verify_current=False)
    stamp = obs["snapshot_id"]
    if stamp is None:
        return False, ("projection-publication-pending" if (root / "generated/manifest.json").exists()
                       else "projection-not-readable")
    if stamp not in snapshots:
        return False, "projection-not-current"
    return True, "ready"


def write_ready(root: Path, write_result) -> tuple[bool, str]:
    return writes_ready(root, [write_result], [write_result])


def _extract(payload, dotted: str):
    node = payload
    for part in dotted.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        elif isinstance(node, list) and part.isdigit() and int(part) < len(node):
            node = node[int(part)]
        else:
            return None, False
    return node, True


def _place(target: dict, dotted: str, value) -> None:
    parts = dotted.split(".")
    node = target
    for part in parts[:-1]:
        existing = node.setdefault(part, {})
        if not isinstance(existing, dict):
            raise AgentRunError("summary fields must not overlap")
        node = existing
    node[parts[-1]] = value


def _cap(node, max_items: int):
    if isinstance(node, dict):
        return {key: _cap(value, max_items) for key, value in node.items()}
    if isinstance(node, list):
        capped = [_cap(value, max_items) for value in node[:max_items]]
        if len(node) > max_items:
            capped.append({"_omitted": len(node) - max_items})
        return capped
    if isinstance(node, str) and len(node) > 240:
        return node[:240] + "…"
    return node


def summarize(payload, *, fields=None, max_items: int = 5, max_bytes: int = 2000) -> str:
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes < 64:
        raise AgentRunError("summary.max_bytes must be an integer >= 64")
    if not isinstance(max_items, int) or isinstance(max_items, bool) or max_items < 1:
        raise AgentRunError("summary.max_items must be a positive integer")
    missing = []
    if fields:
        picked: dict = {}
        for dotted in fields:
            value, found = _extract(payload, dotted)
            if found:
                _place(picked, dotted, value)
            else:
                missing.append(dotted)
        if missing:
            picked["_missing_fields"] = missing
        encoded = _json(picked)
    elif isinstance(payload, str):
        encoded = _json({"text": payload})
    else:
        encoded = _json(_cap(payload, max_items))
    size = len(encoded.encode("utf-8"))
    if size <= max_bytes:
        return encoded
    metadata = {"_truncated_bytes": size, **({"_missing_fields": missing} if missing else {})}
    if len(_json({**metadata, "preview": ""}).encode("utf-8")) > max_bytes:
        raise AgentRunError("budget cannot hold missing-field metadata; increase max_bytes", "SUMMARY_BUDGET_TOO_SMALL")
    # Search the final escaped JSON bytes, not source character count.
    lo, hi = 0, min(len(encoded), max_bytes)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        candidate = _json({**metadata, "preview": encoded[:mid]})
        if len(candidate.encode("utf-8")) <= max_bytes:
            lo = mid
        else:
            hi = mid - 1
    return _json({**metadata, "preview": encoded[:lo]})


def cluster_preview(scan: dict, *, argv=None, sample: int = 3) -> dict:
    """Preserve the public scan's bounds and route to complete membership."""
    if not isinstance(scan.get("groups"), list):
        raise AgentRunError("cluster preview requires the brief scan's groups")
    if argv is None:
        argv = shlex.split(scan.get("full_result") or "intelligence-scan --json")
    full_argv = [token for token in argv if token != "--brief"]
    if "--json" not in full_argv:
        full_argv.append("--json")
    groups = []
    for group in scan.get("groups", []):
        members = group.get("sample_goal_ids", [])
        count = group.get("member_count", len(members))
        groups.append({"cluster_id": group.get("cluster_id"), "title": group.get("title"),
                       "member_count": count, "sample_goal_ids": members[:sample],
                       "omitted_members": max(0, count - len(members[:sample]))})
    return {"groups": groups, "total_groups": scan.get("total_groups", len(groups)),
            "total_goals": scan.get("total_goals", sum(g["member_count"] for g in groups)),
            "omitted_groups": scan.get("omitted_groups", 0),
            "omitted_goals": scan.get("omitted_goals", 0),
            "full_result": shlex.join(full_argv), "expand_argv": full_argv}


def _cluster_summary(scan: dict, argv: list[str], summary: dict) -> str:
    preview = cluster_preview(scan, argv=argv, sample=summary.get("max_items", 3))
    budget = summary.get("max_bytes", 2000)
    # Keep recovery metadata even when groups/samples need to be removed.
    while len(_json(preview).encode("utf-8")) > budget:
        sampled = next((g for g in reversed(preview["groups"]) if g["sample_goal_ids"]), None)
        if sampled:
            sampled["sample_goal_ids"].pop()
            sampled["omitted_members"] += 1
        elif preview["groups"]:
            removed = preview["groups"].pop()
            preview["omitted_groups"] += 1
            preview["omitted_goals"] += removed["member_count"]
        else:
            raise AgentRunError("cluster budget cannot hold counts and expansion; increase max_bytes")
    return _json(preview)


def classify_scope(errors: list[dict], writes: list[str]) -> dict:
    in_scope, unrelated = [], []
    for error in errors:
        path = error.get("path", "")
        (in_scope if path and any(fnmatch.fnmatch(path, glob) for glob in writes)
         else unrelated).append(error)
    return {"in_scope": in_scope, "unrelated": unrelated}


def _preflight(executor, root: Path, writes: list[str]) -> dict | None:
    code, out, err = executor(["validate"], root)
    errors = []
    for line in out.splitlines():
        match = re.match(r"^E ([^:]+): (.*)$", line)
        if match:
            location = re.search(r" \[([^\]]+)\]$", match[2])
            errors.append({"code": match[1], "message": match[2],
                           "path": location[1] if location else ""})
    summary = re.search(r"(?m)^(\d+) error\(s\), \d+ warning\(s\) — (OK|FAIL)$", out)
    if code not in (0, 1) or not summary or int(summary[1]) != len(errors) \
            or (code == 0) != (not errors) or (summary[2] == "OK") != (not errors):
        return {"code": PREFLIGHT_FAILED, "retryable": False,
                "message": "validation did not return a trustworthy result",
                "exit": code, "stderr": err.strip()[-400:]}
    if errors:
        return {"code": VALIDATION_FAILED, "retryable": False,
                "scope": classify_scope(errors, writes)}
    return None


@contextmanager
def _session_bound_envelope(namespace, session_id):
    if session_id is None or getattr(namespace, "command", None) != "capability":
        yield
        return
    if namespace.payload_file == "-":
        raise AgentRunError("session-bound gateway steps require an envelope file", SESSION_MISMATCH)
    content = Path(namespace.payload_file).read_bytes()
    try:
        envelope = json.loads(content)
    except ValueError as exc:
        raise AgentRunError("session-bound gateway steps require a JSON envelope", SESSION_MISMATCH) from exc
    if not isinstance(envelope, dict) or envelope.get("session_id") != session_id:
        raise AgentRunError("sealed envelope session differs from plan; reseal the approved intent", SESSION_MISMATCH)
    # Preserve approved bytes. Submit an immutable copy of the file checked
    # here, avoiding a second read of a caller-changeable source pathname.
    previous = namespace.payload_file
    with tempfile.TemporaryDirectory(prefix="agent-run-envelope-") as directory:
        target = Path(directory) / "envelope.json"
        target.write_bytes(content)
        namespace.payload_file = str(target)
        try:
            yield
        finally:
            namespace.payload_file = previous


def _cli_executor_factory(root: Path, *, session_id=None, write_commands=None):
    from learning_os.adapters.cli import invoke_outcome
    from learning_os.adapters.cli_parser import build_parser
    from learning_os.app.lock import LOS_LOCK_TIMEOUT_ENV

    parser = build_parser()
    writers = write_commands if write_commands is not None else {"capability"}
    admitted_envelopes = {}

    def validate(argv):
        if any(arg == "--root" or arg.startswith("--root=") for arg in argv):
            raise AgentRunError("step root overrides are forbidden; use runner --root")
        errors = io.StringIO()
        try:
            with redirect_stderr(errors), redirect_stdout(errors):
                namespace = parser.parse_args(["--root", str(root), *argv])
        except SystemExit as exc:
            raise AgentRunError("invalid step arguments: " + errors.getvalue()[-1000:]) from exc
        if Path(namespace.root).resolve() != root:
            raise AgentRunError("parsed step root differs from selected root", ROOT_MISMATCH)
        if session_id is not None and getattr(namespace, "session_id", None) not in (None, session_id):
            raise AgentRunError("parsed step session differs from plan", SESSION_MISMATCH)
        if session_id is None and namespace.command in writers and not _declared_read(namespace):
            raise AgentRunError("parsed write command requires a plan session_id", SESSION_REQUIRED)
        return namespace

    def executor(argv, selected_root):
        if selected_root.resolve() != root:
            raise AgentRunError("executor root differs from plan", ROOT_MISMATCH)
        if argv[:1] == ["__seal_submit__"]:
            _, capability, payload, key, *session_args = argv
            proc = subprocess.run(
                [sys.executable, str(TOOLS / "seal_envelope.py"), "--root", str(root),
                 "--capability", capability, "--payload=" + payload, "--key=" + key,
                 "--submit", *session_args], capture_output=True, text=True, cwd=root)
            return proc.returncode, proc.stdout, proc.stderr
        namespace = validate(argv)
        previous = os.environ.get(LOS_LOCK_TIMEOUT_ENV)
        try:
            if namespace.lock_timeout is not None:
                os.environ[LOS_LOCK_TIMEOUT_ENV] = str(namespace.lock_timeout)
            with _session_bound_envelope(namespace, session_id):
                expected = admitted_envelopes.get(tuple(argv))
                if expected is not None and Path(namespace.payload_file).read_bytes() != expected:
                    raise AgentRunError("approved envelope changed since plan admission")
                if hasattr(namespace, "_operation"):
                    outcome = invoke_outcome(namespace)
                    return outcome.exit_code, outcome.stdout, outcome.stderr
                proc = subprocess.run(
                    [sys.executable, str(TOOLS / "los.py"), "--root", str(root), *argv],
                    capture_output=True, text=True, cwd=root)
                return proc.returncode, proc.stdout, proc.stderr
        finally:
            if previous is None:
                os.environ.pop(LOS_LOCK_TIMEOUT_ENV, None)
            else:
                os.environ[LOS_LOCK_TIMEOUT_ENV] = previous

    executor.validate = validate
    executor.parser = parser
    executor.envelope_bytes = admitted_envelopes
    return executor


def _expand_log_step(step: dict, session_id=None) -> list[str]:
    if step.get("stage_id"):
        capability = "stage.note.write"
        payload = {"unit_id": step["unit_id"], "stage_id": step["stage_id"], "text": step["text"]}
    else:
        capability, payload = "capture.create", {"text": step["text"]}
    return ["__seal_submit__", capability, _json(payload), step["key"],
            *(["--session-id=" + session_id] if session_id is not None else [])]


def _validate_plan(plan, poll_s: float) -> list[dict]:
    if len(_json(plan).encode("utf-8")) > 1048576:
        raise AgentRunError("plan input exceeds 1 MiB")
    if isinstance(poll_s, bool) or not math.isfinite(poll_s) or poll_s < 0:
        raise AgentRunError("poll interval must be finite and nonnegative")
    if isinstance(plan, dict):
        unknown = set(plan) - {"steps", "session_id", "on_error", "schema_version",
                               "read_workers", "deadline_s", "report_max_bytes"}
        if unknown:
            raise AgentRunError(f"unknown plan fields: {sorted(unknown)}")
        try:
            parse_controls(plan)
        except ValueError as exc:
            raise AgentRunError(str(exc)) from exc
    steps = plan.get("steps") if isinstance(plan, dict) else None
    if not isinstance(steps, list) or not steps:
        raise AgentRunError("plan needs a non-empty steps list")
    if len(steps) > 256:
        raise AgentRunError("plans are limited to 256 steps")
    if plan.get("on_error", "stop") not in ("stop", "continue"):
        raise AgentRunError("on_error must be stop or continue")
    session_id = plan.get("session_id")
    if "session_id" in plan and (not isinstance(session_id, str) or not session_id.strip()
                                or session_id != session_id.strip() or len(session_id) > 128):
        raise AgentRunError("session_id must be a nonblank, trimmed string of at most 128 characters")
    seen, keys = set(), set()
    for step in steps:
        if not isinstance(step, dict) or not isinstance(step.get("id"), str) or not step["id"]:
            raise AgentRunError("steps need nonempty string ids")
        if len(step["id"]) > 64:
            raise AgentRunError("step ids are limited to 64 characters")
        if step["id"] in seen:
            raise AgentRunError("step ids must be unique")
        allowed_step = {"id", "depends_on", "kind", "describe", "write", "preflight", "clusters",
                        "ready_timeout_s", "args", "argv", "writes", "summary", "key", "text",
                        "stage_id", "unit_id", "use"}
        if set(step) - allowed_step:
            raise AgentRunError("unknown step fields: " + str(sorted(set(step) - allowed_step)))
        if "argv" in step and ("use" in step or "args" in step):
            raise AgentRunError("argv and use/args are mutually exclusive")
        deps = step.get("depends_on", [])
        if not isinstance(deps, list) or any(not isinstance(d, str) or d not in seen for d in deps):
            raise AgentRunError("dependencies must name earlier steps")
        seen.add(step["id"])
        if step.get("kind") not in (None, "log"):
            raise AgentRunError("kind must be log or omitted")
        for flag in ("describe", "write", "preflight", "clusters"):
            if flag in step and not isinstance(step[flag], bool):
                raise AgentRunError(f"{flag} must be boolean")
        if step.get("describe") and not isinstance(step.get("use"), str):
            raise AgentRunError("describe requires use")
        timeout = step.get("ready_timeout_s", 10)
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout < 0:
            raise AgentRunError("readiness timeout must be finite and nonnegative")
        for name in ("args", "argv", "writes"):
            values = step.get(name, [])
            if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
                raise AgentRunError(f"{name} must be a string list")
        if step.get("argv", [])[:1] == ["__seal_submit__"]:
            raise AgentRunError("internal executor commands cannot be supplied in a plan")
        if any(a == "--root" or a.startswith("--root=") for a in step.get("argv", []) + step.get("args", [])):
            raise AgentRunError("step root overrides are forbidden")
        summary = step.get("summary", {})
        if not isinstance(summary, dict):
            raise AgentRunError("summary must be an object")
        if set(summary) - {"fields", "max_items", "max_bytes"}:
            raise AgentRunError("unknown summary fields")
        fields = summary.get("fields", [])
        if not isinstance(fields, list) or any(not isinstance(f, str) or not f or "" in f.split(".") for f in fields):
            raise AgentRunError("summary fields must be dotted strings")
        if any(f == "_missing_fields" or f.startswith("_missing_fields.") for f in fields):
            raise AgentRunError("_missing_fields is reserved summary metadata")
        if any(a != b and (a.startswith(b + ".") or b.startswith(a + ".")) for a in fields for b in fields):
            raise AgentRunError("summary fields must not overlap")
        summarize({}, max_items=summary.get("max_items", 5), max_bytes=summary.get("max_bytes", 2000))
        if step.get("kind") == "log":
            key = step.get("key")
            if not isinstance(key, str) or not key.strip() or key in keys:
                raise AgentRunError("each log needs a unique explicit key stable across retries")
            keys.add(key)
            if not isinstance(step.get("text"), str) or not step["text"].strip():
                raise AgentRunError("log text must be nonempty")
            if step.get("stage_id") and not step.get("unit_id"):
                raise AgentRunError("stage log requires unit_id")
        elif not isinstance(step.get("use"), str) and "argv" not in step:
            raise AgentRunError("step needs use or argv")
        command = (step.get("argv") or [step.get("use")])[0]
        if session_id is None and (step.get("kind") == "log" or step.get("write")
                                   or command in ("capability", "cli.capability")):
            raise AgentRunError("log/gateway plans require an explicit session_id stable across retries")
        if session_id is not None and any(a == "--session-id" or a.startswith("--session-id=")
                                          for a in step.get("argv", []) + step.get("args", [])):
            raise AgentRunError("step session overrides are forbidden; use plan session_id")
    return steps


def _step_argv(step: dict, index: dict, session_id=None) -> list[str]:
    if step.get("kind") == "log":
        argv = _expand_log_step(step, session_id)
    elif step.get("describe"):
        argv = ["capabilities", step["use"], "--json"]
    elif "argv" in step:
        argv = list(step["argv"])
    else:
        argv = [resolve_use(step["use"], index), *step.get("args", [])]
    if step.get("clusters"):
        if not argv or argv[0] != "intelligence-scan":
            raise AgentRunError("clusters requires intelligence-scan")
        for flag in ("--brief", "--json"):
            if flag not in argv:
                argv.append(flag)
    return argv


def run_plan(plan: dict, root: Path, *, executor=None, poll_s: float = 0.1,
             index: dict | None = None, report_dir=None) -> dict:
    from learning_os.adapters.agent_workers import parallel_reads
    from learning_os.app.agent_plans import execute_plan
    from learning_os.app.agent_reporting import ReportStore, minimum_ledger_bytes
    from learning_os.app.projection_readiness import dependency_ready
    from learning_os.app.registry import REGISTRY
    from learning_os.app.validation_service import diagnostic_report
    from learning_os.domain.agent_plans import CompiledStep, PlanControls, RawOutcome

    started = time.monotonic()
    steps = _validate_plan(plan, poll_s)
    root = root.resolve()
    injected = executor is not None
    session_id = plan.get("session_id")
    writers = {"capability"}
    actual = executor or _cli_executor_factory(root, session_id=session_id, write_commands=writers)
    with _session_environment(session_id):
        index = index if index is not None else build_index(root, actual,
            resolve_tasks=any("use" in s and not s.get("describe") and s.get("kind") != "log"
                              for s in steps) or injected)
        writers.update(index.get("write_verbs", []))
        compiled = []
        for step in steps:
            direct = (step.get("argv") or [step.get("use")])[0]
            namespace = None
            # A Core-declared read mode skips this coarse verb check; the parsed
            # check in validate() decides mode by mode.
            early_entry = REGISTRY.get(index.get("verb_to_operation", {}).get(direct))
            if session_id is None and direct in writers and not step.get("describe") \
                    and not (early_entry is not None and early_entry.read_when is not None):
                raise AgentRunError("write plans require an explicit session_id stable across retries", SESSION_REQUIRED)
            try:
                argv = _step_argv(step, index, session_id)
                command = argv[0] if argv else ""
                if not injected and command != "__seal_submit__":
                    namespace = actual.validate(argv)
                    command = namespace.command
                    # Check all static envelope/session bindings before the first mutation.
                    with _session_bound_envelope(namespace, session_id):
                        if command == "capability":
                            actual.envelope_bytes[tuple(argv)] = Path(namespace.payload_file).read_bytes()
                writer = (command in writers and not (namespace is not None and _declared_read(namespace))) \
                    or step.get("kind") == "log" or step.get("write", False)
                if writer and session_id is None:
                    raise AgentRunError("write plans require an explicit session_id stable across retries", SESSION_REQUIRED)
                operation = index.get("verb_to_operation", {}).get(command)
                entry = REGISTRY.get(operation)
                profile = entry.memo_profile if entry is not None else "none"
                reusable = not injected and not writer and profile != "none"
                if profile == "manifest-brief" and ("--brief" not in argv or
                        (not injected and getattr(namespace, "feed", None))):
                    reusable = False
                compiled.append(CompiledStep(
                    id=step["id"], argv=tuple(argv), dependencies=tuple(step.get("depends_on", [])),
                    writer=bool(writer), submitting=command in ("capability", "__seal_submit__"),
                    reusable=reusable, parallel_safe=bool(reusable and entry.parallel_safe),
                    ready_timeout_s=float(step.get("ready_timeout_s", 10)),
                    preflight=step.get("preflight", False), scope=tuple(step.get("writes", [])),
                    presentation=step))
            except AgentRunError as exc:
                compiled.append(CompiledStep(id=step["id"], argv=(),
                    admission_error={"code": exc.code, "retryable": False, "message": str(exc)}))
        store = ReportStore(root, Path(report_dir) if report_dir is not None else None)
        budget = plan.get("report_max_bytes", 65536)
        if minimum_ledger_bytes([s.id for s in compiled], str(store.full_path)) > budget:
            raise AgentRunError("report_max_bytes cannot hold the minimum step ledger",
                                REPORT_BUDGET_TOO_SMALL)

        class Port:
            def __init__(self):
                self.resource_info = {}

            def execute(self, step, remaining):
                code, out, err = actual(list(step.argv), root)
                count = int(not injected and step.submitting and step.argv[0] == "__seal_submit__")
                return RawOutcome(code, out, err, count)

            def parallel(self, batch, workers, remaining):
                counter = [0]
                elapsed = {}
                outcomes = parallel_reads(root, [list(s.argv) for s in batch], workers,
                                          timeout_s=remaining, session_id=session_id,
                                          process_counter=counter, resource_stats=self.resource_info, elapsed_times=elapsed)
                return [RawOutcome(*outcome, processes=counter[0] if i == 0 else 0, elapsed_ms=elapsed.get(i, 0))
                        for i, outcome in enumerate(outcomes)]

            def preflight(self, step):
                if injected:
                    return _preflight(actual, root, list(step.scope))
                report = diagnostic_report(root)
                if not report.get("trustworthy"):
                    return report.get("error")
                errors = report.get("errors", [])
                return ({"code": VALIDATION_FAILED, "retryable": False,
                         "scope": classify_scope(errors, list(step.scope))}
                        if errors else None)

            def summarize(self, step, payload):
                description = step.presentation
                summary = description.get("summary") or {}
                return (_cluster_summary(payload, list(step.argv), summary)
                        if description.get("clusters") and isinstance(payload, dict)
                        else summarize(payload, fields=summary.get("fields"),
                                       max_items=summary.get("max_items", 5),
                                       max_bytes=summary.get("max_bytes", 2000)))

            def ready(self, required, known, submitting):
                if injected:
                    return (_writes_completed(root, required) if submitting
                            else writes_ready(root, required, known))
                records = [{"receipt_path": _field(r, "receipt_path"),
                            "snapshot_after": _field(r, "snapshot_after")} for r in required]
                all_records = [{"receipt_path": _field(r, "receipt_path"),
                                "snapshot_after": _field(r, "snapshot_after")} for r in known]
                return dependency_ready(root, records, all_records, completion_only=submitting)

            def epoch(self, selected_root):
                return not injected

            def resources(self):
                import resource
                return {**self.resource_info, "runner_peak_rss_bytes":
                    resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024)}

        store.inputs(plan, list(actual.envelope_bytes.values()) if not injected else [])
        controls = PlanControls(read_workers=plan.get("read_workers", 1),
            deadline_s=float(plan.get("deadline_s", 120)), report_max_bytes=budget,
            on_error=plan.get("on_error", "stop"), session_id=session_id)
        return execute_plan(compiled, root, Port(), controls, store, started, poll_s)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", nargs="?", help="plan JSON file, or - for stdin")
    parser.add_argument("--catalog", action="store_true",
                        help="print the read catalog as JSON and exit")
    parser.add_argument("--expand-report", help="verify and expand a finalized full report")
    parser.add_argument("--step", help="expand only this step (with --expand-report)")
    parser.add_argument("--root", default=None, help="selected data root (default: tool repository)")
    parser.add_argument("--poll-s", type=float, default=0.1)
    parser.add_argument("--report-dir", default=None,
                        help="directory for the full report artifact (bounded stdout)")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = Path(args.root).resolve() if args.root else TOOLS.parent
    try:
        if args.catalog:
            from learning_os.app.agent_catalog import build_catalog
            index = build_index(root, _cli_executor_factory(root), resolve_tasks=False)
            print(_json(build_catalog(root, index["verb_to_operation"])))
            return 0
        if args.expand_report:
            from learning_os.app.agent_reporting import expand_report
            if args.plan:
                raise AgentRunError("choose a plan or --expand-report")
            print(_json(expand_report(Path(args.expand_report), args.step)))
            return 0
        if not args.plan or args.step:
            raise AgentRunError("a plan is required; --step needs --expand-report")
        if args.plan == "-":
            plan_text = sys.stdin.read(1048577)
            if len(plan_text.encode("utf-8")) > 1048576:
                raise AgentRunError("plan input exceeds 1 MiB")
            report = run_plan(json.loads(plan_text, parse_float=_finite_number, parse_constant=_finite_number), root, poll_s=args.poll_s, report_dir=args.report_dir)
        else:
            if Path(args.plan).stat().st_size > 1048576:
                raise AgentRunError("plan input exceeds 1 MiB")
            report = run_plan(json.loads(Path(args.plan).read_text(encoding="utf-8"), parse_float=_finite_number, parse_constant=_finite_number), root, poll_s=args.poll_s, report_dir=args.report_dir)
    except (OSError, ValueError, KeyError, TypeError, AgentRunError) as exc:
        print(_json({"error": {"code": getattr(exc, "code", INVALID_REQUEST),
                               "message": str(exc), "retryable": False}}))
        return 2
    print(_json(report))
    return 0 if all(row["status"] == "ok" for row in report["steps"]) else 3


if __name__ == "__main__":
    raise SystemExit(main())
