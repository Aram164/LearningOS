"""Admit, schedule and settle bounded plans through an injected adapter port."""
from __future__ import annotations

import dataclasses
import json
import math
import time
from contextlib import nullcontext
from pathlib import Path
from typing import cast

from learning_os.app.agent_reporting import ReportStore, bound_report
from learning_os.app.projection import fresh_manifest_and_repo
from learning_os.app.read_session import ReadSession
from learning_os.domain.agent_bindings import BindingError, bind_argv
from learning_os.domain.agent_plans import CompiledStep, Executor, PlanControls, RawOutcome
from learning_os.domain.codes import (
    ARTIFACT_FAILED,
    DEADLINE_EXPIRED,
    DEPENDENCY_FAILED,
    INVALID_STEP_OUTPUT,
    NOT_READY,
    PLAN_INVALID,
    PLAN_STOPPED,
    PREFLIGHT_FAILED,
    SNAPSHOT_CONFLICT,
    STEP_FAILED,
    UNCONFIRMED,
)

DEFAULT_CONTROLS = PlanControls()


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
        raise ValueError("nonfinite numeric step output")
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
    payloads: dict[str, object] = {}
    needed_sources = {ref.source for step in steps for ref in step.bindings if ref.source}
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
                raise ValueError("INVALID_STEP_OUTPUT: " + str(exc)) from exc
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
            if step.id in needed_sources and row["status"] == "ok":
                payloads[step.id] = payload
        except (OSError, ValueError, TypeError) as exc:
            code = INVALID_STEP_OUTPUT if str(exc).startswith(INVALID_STEP_OUTPUT) else getattr(exc, "code", STEP_FAILED)
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
    d_session = ReadSession(root) if controls.snapshot_one else None
    d_scope = d_session.activate(lambda: fresh_manifest_and_repo(root)) if d_session is not None else nullcontext()
    try:
        with d_scope:
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
                    if candidate.writer or not candidate.reusable or candidate.dependencies or candidate.preflight \
                            or candidate.bindings or controls.snapshot_one:
                        break
                    wave.append(candidate)
                if wave:
                    session = ReadSession(root) if port.epoch(root) else None
                    begin_rows = len(rows)
                    try:
                        if controls.read_workers > 1 and len(wave) > 1 and all(s.parallel_safe for s in wave):
                            # Coordinator holds no lock while waiting for child processes.
                            outputs = port.parallel(wave, controls.read_workers, remaining())
                            for item, raw in zip(wave, outputs, strict=True):
                                retain(item, consume(item, raw, time.monotonic()))
                                ancestors[item.id] = set()
                        else:
                            scope = session.activate(lambda: fresh_manifest_and_repo(root)) if session is not None else nullcontext()
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
                                    stopped = stopped or (wave[0].id if controls.on_error == "stop" else None)
                    except Exception as exc:
                        for item in wave[len(rows) - begin_rows:]:
                            retain(item, fail_row(item, "error", getattr(exc, "code", STEP_FAILED), message=str(exc)))
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
                        ready, reason = port.ready(required, list(writes.values()), step.submitting)
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
                    run_step = step
                    bound: dict[str, object] | None = None
                    if step.bindings:
                        # Resolve immediately before execution (PLAN S15): the
                        # placeholders never reach a handler.
                        argv, bound = bind_argv(step.argv, step.bindings, payloads)
                        run_step = dataclasses.replace(step, argv=tuple(argv))
                        port.validate_bound(run_step)
                    error = port.preflight(run_step) if step.preflight else None
                    if error:
                        retain(step, {**fail_row(step, "blocked", PREFLIGHT_FAILED), "error": error})
                    elif remaining() <= 0:
                        retain(step, fail_row(step, "deadline", DEADLINE_EXPIRED))
                    else:
                        row = consume(run_step, port.execute(run_step, remaining()), begin, ready_ms)
                        if bound is not None:
                            row["bound"] = bound
                        retain(step, row)
                except BindingError as exc:
                    retain(step, {**fail_row(step, "error", exc.code), "error": {**exc.as_dict(), "retryable": False}})
                except Exception as exc:
                    row = fail_row(step, "error", getattr(exc, "code", STEP_FAILED), message=str(exc))
                    # Dispatch may have crossed the commit boundary before transport failed.
                    if step.writer:
                        row["commit_certainty"] = "uncertain"
                    retain(step, row)
                index += 1

    finally:
        if d_session is not None:
            memo_hits += d_session.hits
            model_loads += d_session.loads
            if not d_session.unchanged():
                for row in rows:
                    row.update(status="error",
                               error={"code": SNAPSHOT_CONFLICT, "retryable": True,
                                      "message": "inputs changed during read epoch"})
                    row.pop("output", None)
            d_session.close()
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
            "process_count": processes, "memo_hits": memo_hits, "shared_model_loads": model_loads, "model_loads": (load_counter[0] if load_counter else 0) + port.resources().get("worker_model_loads", 0),
            "resources": port.resources()}}
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
        cast(dict[str, object], report["totals"])["ok"] = 0
    return bound_report(report, controls.report_max_bytes, str(full))
