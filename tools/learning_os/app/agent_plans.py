"""Admit, schedule and settle bounded plans through the shared execution port."""
from __future__ import annotations

import json
import math
import time
from collections.abc import Callable
from contextlib import nullcontext
from pathlib import Path
from typing import cast

from learning_os.app.agent_presentation import _step_argv
from learning_os.app.agent_reporting import ReportStore, bound_report
from learning_os.app.lock import lock_wait_budget
from learning_os.app.projection import fresh_manifest_and_repo
from learning_os.app.read_session import ReadSession
from learning_os.app.registry import REGISTRY, CacheProfile
from learning_os.domain.agent_plans import (
    CompiledStep,
    Executor,
    PlanControls,
    PlanIndex,
    PlanStep,
    PlanStepError,
    RawOutcome,
)
from learning_os.domain.codes import (
    ARTIFACT_FAILED,
    DEADLINE_EXPIRED,
    DEPENDENCY_FAILED,
    INVALID_STEP_OUTPUT,
    NOT_READY,
    PLAN_INVALID,
    PLAN_STOPPED,
    PREFLIGHT_FAILED,
    SESSION_REQUIRED,
    SNAPSHOT_CONFLICT,
    STEP_FAILED,
    UNCONFIRMED,
)
from learning_os.store.contracts.agent_plans import validate_input


def validate_plan(plan: object, poll_s: float) -> list[PlanStep]:
    if isinstance(poll_s, bool) or not isinstance(poll_s, (int, float)) or not math.isfinite(poll_s) or poll_s < 0:
        raise PlanStepError("poll interval must be finite and nonnegative")
    plan = validate_input(plan)
    seen, keys = set(), set()
    session_id = plan.get("session_id")
    for step in plan["steps"]:
        if step["id"] in seen:
            raise PlanStepError("step ids must be unique")
        if any(dep not in seen for dep in step.get("depends_on", [])):
            raise PlanStepError("dependencies must name earlier steps")
        seen.add(step["id"])
        fields = step.get("summary", {}).get("fields", [])
        if any(a != b and (a.startswith(b + ".") or b.startswith(a + ".")) for a in fields for b in fields):
            raise PlanStepError("summary fields must not overlap")
        if step.get("kind") == "log":
            if step["key"] in keys:
                raise PlanStepError("each log needs a unique explicit key stable across retries")
            keys.add(step["key"])
        args = step.get("argv", []) + step.get("args", [])
        if args[:1] == ["__seal_submit__"]:
            raise PlanStepError("internal executor commands cannot be supplied in a plan")
        if any(a == "--root" or a.startswith("--root=") for a in args):
            raise PlanStepError("step root overrides are forbidden")
        command = (step.get("argv") or [step.get("use", "")])[0]
        if session_id is None and (step.get("kind") == "log" or step.get("write") or command in ("capability", "cli.capability")):
            raise PlanStepError("log/gateway plans require an explicit session_id stable across retries", SESSION_REQUIRED)
        if session_id is not None and any(a == "--session-id" or a.startswith("--session-id=") for a in args):
            raise PlanStepError("step session overrides are forbidden; use plan session_id")
    return plan["steps"]


def compile_plan(steps: list[PlanStep], index: PlanIndex, admit: Callable[[list[str]], tuple[str, bool]], session_id: str | None) -> list[CompiledStep]:
    writers = {"capability", *index.get("write_verbs", [])}
    compiled = []
    for step in steps:
        direct = (step.get("argv") or [step.get("use", "")])[0]
        if session_id is None and direct in writers and not step.get("describe"):
            raise PlanStepError("write plans require an explicit session_id stable across retries", SESSION_REQUIRED)
        try:
            argv = _step_argv(step, index, session_id)
            command, feed = ("__seal_submit__", False) if argv[0] == "__seal_submit__" else admit(argv)
            writer = command in writers or step.get("kind") == "log" or step.get("write", False)
            if writer and session_id is None:
                raise PlanStepError("write plans require an explicit session_id stable across retries", SESSION_REQUIRED)
            entry = REGISTRY.get(index["verb_to_operation"].get(command) or "")
            cache = entry.cache if entry is not None else CacheProfile.NONE
            reusable = not writer and cache != CacheProfile.NONE
            if cache == CacheProfile.MANIFEST_BRIEF and ("--brief" not in argv or feed):
                reusable = False
            compiled.append(CompiledStep(id=step["id"], argv=tuple(argv), dependencies=tuple(step.get("depends_on", [])),
                writer=bool(writer), submitting=command in ("capability", "__seal_submit__"), reusable=reusable,
                ready_timeout_s=float(step.get("ready_timeout_s", 10)), preflight=step.get("preflight", False),
                scope=tuple(step.get("writes", [])), presentation=step))
        except PlanStepError as exc:
            compiled.append(CompiledStep(id=step["id"], argv=(), admission_error={"code":exc.code,"retryable":False,"message":str(exc)}))
    return compiled


def field(payload: object, name: str) -> object:
    if not isinstance(payload, dict):
        return None
    if payload.get(name) is not None:
        return payload[name]
    nested = payload.get("result")
    return nested.get(name) if isinstance(nested, dict) else None


def finite(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise PlanStepError("nonfinite numeric step output", INVALID_STEP_OUTPUT)
    return number


def execute_plan(steps: list[CompiledStep], root: Path, port: Executor,
                 controls: PlanControls, store: ReportStore, started: float,
                 poll_s: float = 0.1) -> dict[str, object]:
    from learning_os.store.loading import count_repo_loads

    with count_repo_loads() as counter:
        return _execute_plan(steps, root, port, controls, store, started, poll_s, counter)


def _execute_plan(steps: list[CompiledStep], root: Path, port: Executor,
                 controls: PlanControls, store: ReportStore, started: float,
                 poll_s: float = 0.1, load_counter: list[int] | None = None) -> dict[str, object]:
    deadline = started + controls.deadline_s
    rows: list[dict[str, object]] = []
    results: dict[str, dict[str, object]] = {}
    writes: dict[str, object] = {}
    ancestors: dict[str, set[str]] = {}
    stopped: str | None = None
    uncertain = False
    processes = 1
    memo_hits = 0
    model_loads = 0

    def remaining() -> float:
        return max(0.0, deadline - time.monotonic())

    def fail_row(step: CompiledStep, status: str, code: str,
                 **details: object) -> dict[str, object]:
        return {"id": step.id, "status": status, "ms": 0, "ready_wait_ms": 0,
                "commit_certainty": "none",
                "error": {"code": code, "retryable": False, **details}}

    def retain(step: CompiledStep, row: dict[str, object]) -> None:
        nonlocal stopped, uncertain
        try:
            store.record(row)
        except OSError as exc:
            row.update(status="error", error={"code": ARTIFACT_FAILED,
                       "retryable": False, "message": str(exc)})
            uncertain = True  # report storage failure blocks further writes too
        rows.append(row)
        results[step.id] = row
        error = row.get("error")
        if isinstance(error, dict) and error.get("code") == ARTIFACT_FAILED:
            uncertain = True
        if row.get("commit_certainty") == "uncertain":
            uncertain = True
        if row["status"] != "ok" and controls.on_error == "stop":
            stopped = stopped or step.id

    def correct(row: dict[str, object]) -> None:
        nonlocal uncertain
        try:
            store.correct(row)
        except OSError as exc:
            row.update(status="error", error={"code": ARTIFACT_FAILED,
                       "retryable": False, "message": str(exc)})
            uncertain = True

    def consume(step: CompiledStep, raw: RawOutcome, begin: float,
                ready_ms: int = 0) -> dict[str, object]:
        nonlocal processes
        processes += raw.processes
        row: dict[str, object] = {"id": step.id, "status": "ok", "exit": raw.code,
            "ready_wait_ms": ready_ms, "commit_certainty": "uncertain" if step.writer else "none",
            "raw_bytes": len(raw.stdout.encode("utf-8"))}
        try:
            try:
                payload: object = json.loads(raw.stdout, parse_float=finite, parse_constant=finite)
            except json.JSONDecodeError:
                payload = raw.stdout  # established human-output support
            except ValueError as exc:
                raise PlanStepError(str(exc), INVALID_STEP_OUTPUT) from exc
            snapshot = field(payload, "snapshot_after")
            receipt = field(payload, "receipt_path")
            if snapshot and receipt:
                row["receipt"] = {"snapshot_after": snapshot, "receipt_path": receipt}
                row["commit_certainty"] = "committed"
            if raw.code or (isinstance(payload, dict) and payload.get("ok") is False):
                detail = payload.get("error") if isinstance(payload, dict) else None
                row.update(status="error", error=detail if isinstance(detail, dict) else {
                    "code": STEP_FAILED, "retryable": False, "stderr": raw.stderr[-400:]})
                # Only a gateway refusal proves no commit. Porcelain may
                # have changed files or Git before returning a generic failure.
                # A receipt remains stronger evidence than a refusal field.
                if (step.submitting and isinstance(payload, dict) and payload.get("commit") == "none"
                        and row["commit_certainty"] != "committed"):
                    row["commit_certainty"] = "none"
            elif step.writer or snapshot:
                writes[step.id] = payload
            if row["status"] == "ok" and step.submitting and not receipt:
                row.update(status="error", error={"code": UNCONFIRMED,
                           "retryable": False, "message": "write returned no receipt"})
            validation = [line for line in raw.stderr.splitlines() if "seal_envelope: validation:" in line]
            if validation:
                row["validation"] = validation[-1]
            encoded = port.summarize(step, payload)
            row.update(output=json.loads(encoded), out_bytes=len(encoded.encode("utf-8")))
        except (OSError, ValueError, TypeError) as exc:
            code = getattr(exc, "code", STEP_FAILED)
            row.update(status="error", error={"code": code, "retryable": False, "message": str(exc)})
        except Exception as exc:
            # Adapter refusals remain step-scoped and retain any committed receipt.
            row.update(status="error", error={"code": getattr(exc, "code", STEP_FAILED),
                       "retryable": False, "message": str(exc)})
        try:
            row["raw_artifact"], row["raw_sha256"] = store.raw(len(rows), raw.stdout, raw.stderr)
        except OSError as exc:
            row.update(status="error", error={"code": ARTIFACT_FAILED, "retryable": False, "message": str(exc)})
        row["ms"] = raw.elapsed_ms if raw.elapsed_ms is not None else round((time.monotonic() - begin) * 1000)
        return row

    invalid = next((s for s in steps if s.admission_error is not None), None)
    if invalid is not None:
        for step in steps:
            row = fail_row(step, "error" if step.admission_error else "skipped", PLAN_INVALID)
            if step.admission_error is not None:
                row["error"] = step.admission_error
            retain(step, row)
    index = len(steps) if invalid is not None else 0
    while index < len(steps):
        step = steps[index]
        ancestors[step.id] = set(step.dependencies).union(
            *(ancestors[d] for d in step.dependencies))
        if stopped is not None or (uncertain and step.writer):
            retain(step, fail_row(step, "skipped", PLAN_STOPPED, failed_step=stopped,
                                  reason="unresolved write or report storage" if uncertain else "stop policy"))
            index += 1
            continue
        if remaining() <= 0:
            retain(step, fail_row(step, "deadline", DEADLINE_EXPIRED))
            index += 1
            continue
        failed = next((d for d in step.dependencies if results[d]["status"] != "ok"), None)
        if failed:
            retain(step, fail_row(step, "blocked", DEPENDENCY_FAILED, dependency=failed))
            index += 1
            continue

        # Only contiguous eligible reads share an epoch. Never prefetch across a write.
        wave: list[CompiledStep] = []
        for candidate in steps[index:]:
            if candidate.writer or not candidate.reusable or candidate.dependencies or candidate.preflight:
                break
            wave.append(candidate)
        if wave:
            session = ReadSession(root) if port.epoch(root) else None
            begin_rows = len(rows)
            try:
                scope = session.activate(lambda: fresh_manifest_and_repo(root), timeout_s=remaining()) if session is not None else nullcontext()
                with scope:
                    for item in wave:
                        ancestors[item.id] = set()
                        if stopped or remaining() <= 0:
                            retain(item, fail_row(item, "skipped" if stopped else "deadline",
                                                 PLAN_STOPPED if stopped else DEADLINE_EXPIRED))
                            continue
                        begin = time.monotonic()
                        key = item.argv
                        cached = session.get(key) if session is not None else None
                        raw = cached if isinstance(cached, RawOutcome) else port.execute(item, remaining())
                        row = consume(item, raw, begin)
                        if session is not None and row["status"] == "ok" and not cached:
                            session.put(key, raw)
                        retain(item, row)
                if session is not None and not session.unchanged():
                    for row in rows[begin_rows:]:
                        row.update(status="error", error={"code": SNAPSHOT_CONFLICT,
                                   "retryable": True, "message": "inputs changed during read epoch"})
                        row.pop("output", None)
                        correct(row)
                    stopped = stopped or (wave[0].id if controls.on_error == "stop" else None)
            except Exception as exc:
                # A failed epoch close cannot attest the already emitted reads.
                for row in rows[begin_rows:]:
                    if row["status"] == "ok":
                        row.update(status="error", error={"code": SNAPSHOT_CONFLICT,
                            "retryable": True, "message": "read epoch did not complete"})
                        row.pop("output", None)
                        correct(row)
                if controls.on_error == "stop":
                    stopped = stopped or wave[0].id
                for item in wave[len(rows) - begin_rows:]:
                    retain(item, fail_row(item, "deadline" if remaining() <= 0 else "error",
                        DEADLINE_EXPIRED if remaining() <= 0 else getattr(exc, "code", STEP_FAILED), message=str(exc)))
            finally:
                if session is not None:
                    memo_hits += session.hits
                    model_loads += session.loads
                    session.close()
            index += len(wave)
            continue

        begin = time.monotonic()
        required = [writes[d] for d in writes if d in ancestors[step.id]]
        ready_ms = 0
        if required:
            until = min(deadline, time.monotonic() + step.ready_timeout_s)
            while True:
                try:
                    with lock_wait_budget(remaining()):
                        ready, reason = port.ready(required, list(writes.values()), step.submitting)
                except Exception as exc:
                    expired = remaining() <= 0
                    retain(step, fail_row(step, "deadline" if expired else "error",
                        DEADLINE_EXPIRED if expired else getattr(exc, "code", STEP_FAILED), message=str(exc)))
                    break
                if ready:
                    break
                if time.monotonic() >= until:
                    expired = remaining() <= 0
                    conflict = reason == "projection-not-current"
                    row = fail_row(step, "deadline" if expired else "not_ready",
                                   DEADLINE_EXPIRED if expired else SNAPSHOT_CONFLICT if conflict else NOT_READY,
                                   reason=reason, dependencies=list(ancestors[step.id]))
                    cast(dict[str, object], row["error"])["retryable"] = not expired and not conflict
                    retain(step, row)
                    break
                time.sleep(min(poll_s, max(0.0, until - time.monotonic())))
            ready_ms = round((time.monotonic() - begin) * 1000)
            if step.id in results:
                index += 1
                continue
        try:
            with lock_wait_budget(remaining()):
                error = port.preflight(step) if step.preflight else None
            if error:
                retain(step, {**fail_row(step, "blocked", PREFLIGHT_FAILED), "error": error})
            elif remaining() <= 0:
                retain(step, fail_row(step, "deadline", DEADLINE_EXPIRED))
            else:
                retain(step, consume(step, port.execute(step, remaining()), begin, ready_ms))
        except Exception as exc:
            expired = remaining() <= 0
            row = fail_row(step, "deadline" if expired else "error",
                           DEADLINE_EXPIRED if expired else getattr(exc, "code", STEP_FAILED), message=str(exc))
            # Dispatch may have crossed the commit boundary before transport failed.
            if step.writer:
                row["commit_certainty"] = "uncertain"
            retain(step, row)
        index += 1

    resource_info = port.resources()
    report: dict[str, object] = {"schema_version": 2, "experimental": True,
        "session_id": controls.session_id, "on_error": controls.on_error, "steps": rows,
        "plan_sha256": store.plan_digest, "plan_artifact": "plan.json",
        "totals": {"steps": len(rows), "ok": sum(r["status"] == "ok" for r in rows),
            "not_ready": sum(r["status"] == "not_ready" for r in rows),
            "ms": round((time.monotonic() - started) * 1000),
            "step_ms_sum": sum(cast(int, r.get("ms", 0)) for r in rows),
            "deadline_overshoot_ms": max(0, round((time.monotonic() - deadline) * 1000)),
            "raw_bytes": sum(cast(int, r.get("raw_bytes", 0)) for r in rows),
            "out_bytes": sum(cast(int, r.get("out_bytes", 0)) for r in rows),
            "process_count": processes + resource_info.get("unreported_processes", 0), "memo_hits": memo_hits, "shared_model_loads": model_loads, "model_loads": (load_counter[0] if load_counter else 0),
            "resources": resource_info}}
    report["full_report"] = str(store.full_path)
    try:
        from learning_os.app.agent_reporting import write_full_report
        store.sync()
        full = write_full_report(store.path, report)
    except OSError as exc:
        # The incremental checkpoint and inline receipt ledger remain available.
        report["artifact_error"] = str(exc)
        full = store.path / "checkpoint.jsonl"
        for row in rows:
            if row["status"] == "ok":
                row["status"] = "error"
                row["error"] = {"code": ARTIFACT_FAILED, "retryable": False}
                correct(row)
        cast(dict[str, object], report["totals"])["ok"] = 0
    return bound_report(report, controls.report_max_bytes, str(full))
