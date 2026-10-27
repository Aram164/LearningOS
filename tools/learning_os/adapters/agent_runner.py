"""CLI transport and execution port for the shared agent-plan application."""
from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterator
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from pathlib import Path
from typing import cast

from learning_os.app.agent_plans import compile_plan, execute_plan, validate_plan
from learning_os.app.agent_presentation import _cluster_summary, _field, classify_scope, summarize
from learning_os.app.agent_reporting import ReportStore, minimum_ledger_bytes
from learning_os.app.projection_readiness import dependency_ready
from learning_os.app.validation_service import diagnostic_report
from learning_os.domain.agent_plans import (
    CompiledStep,
    PlanControls,
    PlanIndex,
    PlanInput,
    PlanStepError,
    RawOutcome,
    SummarySpec,
)
from learning_os.domain.codes import (
    DISCOVERY_FAILED,
    REPORT_BUDGET_TOO_SMALL,
    ROOT_MISMATCH,
    SESSION_MISMATCH,
    SESSION_REQUIRED,
    VALIDATION_FAILED,
)

TOOLS = Path(__file__).resolve().parents[2]

def build_index(root: Path, executor: CliExecutor | None = None, *, resolve_tasks: bool = True) -> PlanIndex:
    """Use declared effects and task dispatch; presentation prose is never parsed."""
    from learning_os.adapters.cli_parser import verb_table
    from learning_os.app.registry import REGISTRY, OperationEffects

    bindings = verb_table(getattr(executor, "parser", None))
    index: PlanIndex = {"verbs": sorted(bindings), "verb_to_operation": bindings,
             "task_to_use": {}, "write_verbs": [verb for verb, operation in bindings.items()
                 if (entry := REGISTRY.get(operation or "")) is None
                 or entry.effects != OperationEffects.READ]}
    if resolve_tasks:
        from learning_os.store.contracts.verb_catalogue import (
            VerbCatalogueError,
            build_verb_catalogue,
        )
        try:
            catalogue = build_verb_catalogue(root)
        except VerbCatalogueError as exc:
            raise PlanStepError(f"capability discovery failed: {exc}", DISCOVERY_FAILED) from exc
        index["task_to_use"] = {task.id: task.entry_verb for task in catalogue.tasks if task.entry_verb}
    return index


@contextmanager
def _session_bound_envelope(namespace: argparse.Namespace, session_id: str | None) -> Iterator[None]:
    if session_id is None or getattr(namespace, "command", None) != "capability":
        yield
        return
    if namespace.payload_file == "-":
        raise PlanStepError("session-bound gateway steps require an envelope file", SESSION_MISMATCH)
    content = Path(namespace.payload_file).read_bytes()
    try:
        envelope = json.loads(content)
    except ValueError as exc:
        raise PlanStepError("session-bound gateway steps require a JSON envelope", SESSION_MISMATCH) from exc
    if not isinstance(envelope, dict) or envelope.get("session_id") != session_id:
        raise PlanStepError("sealed envelope session differs from plan; reseal the approved intent", SESSION_MISMATCH)
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

class CliExecutor:
    def __init__(self, root: Path, *, session_id: str | None = None,
                 write_commands: set[str] | None = None) -> None:
        from learning_os.adapters.cli_parser import build_parser
        self.root = root
        self.session_id = session_id
        self.parser = build_parser()
        self.writers = write_commands if write_commands is not None else {"capability"}
        self.envelope_bytes: dict[tuple[str, ...], bytes] = {}
        self.process_count = 0

    def validate(self, argv: list[str]) -> argparse.Namespace:
        root, session_id, parser, writers = self.root, self.session_id, self.parser, self.writers
        if any(arg == "--root" or arg.startswith("--root=") for arg in argv):
            raise PlanStepError("step root overrides are forbidden; use runner --root")
        errors = io.StringIO()
        try:
            with redirect_stderr(errors), redirect_stdout(errors):
                namespace = parser.parse_args(["--root", str(root), *argv])
        except SystemExit as exc:
            raise PlanStepError("invalid step arguments: " + errors.getvalue()[-1000:]) from exc
        if Path(namespace.root).resolve() != root:
            raise PlanStepError("parsed step root differs from selected root", ROOT_MISMATCH)
        if session_id is not None and getattr(namespace, "session_id", None) not in (None, session_id):
            raise PlanStepError("parsed step session differs from plan", SESSION_MISMATCH)
        if session_id is None and namespace.command in writers:
            raise PlanStepError("parsed write command requires a plan session_id", SESSION_REQUIRED)
        return namespace

    def __call__(self, argv: list[str], selected_root: Path, *, timeout_s: float | None = None) -> tuple[int, str, str]:
        from learning_os.adapters.cli import invoke_outcome
        root, session_id = self.root, self.session_id
        if selected_root.resolve() != root:
            raise PlanStepError("executor root differs from plan", ROOT_MISMATCH)

        def launch(command: list[str], user_timeout: float | None = None) -> tuple[int, str, str]:
            timeout = timeout_s if user_timeout is None else min(user_timeout, timeout_s) if timeout_s is not None else user_timeout
            environment = os.environ.copy()
            if session_id is not None:
                environment["LOS_SESSION_ID"] = session_id
            if timeout is not None:
                environment["LOS_LOCK_TIMEOUT"] = str(timeout)
            self.process_count += 1
            proc = subprocess.run(command, capture_output=True, text=True, cwd=root,
                                  timeout=timeout, env=environment)
            return proc.returncode, proc.stdout, proc.stderr

        if argv[:1] == ["__seal_submit__"]:
            _, capability, payload, key, *session_args = argv
            return launch([sys.executable, str(TOOLS / "seal_envelope.py"), "--root", str(root),
                           "--capability", capability, "--payload=" + payload, "--key=" + key,
                           "--submit", *session_args])
        namespace = self.validate(argv)
        with _session_bound_envelope(namespace, session_id):
            expected = self.envelope_bytes.get(tuple(argv))
            if expected is not None and Path(namespace.payload_file).read_bytes() != expected:
                raise PlanStepError("approved envelope changed since plan admission")
            timeout = timeout_s if namespace.lock_timeout is None else min(namespace.lock_timeout, timeout_s) if timeout_s is not None else namespace.lock_timeout
            if hasattr(namespace, "_operation"):
                outcome = invoke_outcome(namespace, session_id=session_id, timeout_s=timeout)
                return outcome.exit_code, outcome.stdout, outcome.stderr
            return launch([sys.executable, str(TOOLS / "los.py"), "--root", str(root), *argv],
                          namespace.lock_timeout)

def _cli_executor_factory(root: Path, *, session_id: str | None = None,
                          write_commands: set[str] | None = None) -> CliExecutor:
    return CliExecutor(root, session_id=session_id, write_commands=write_commands)


class CliPlanPort:
    """Production plan port; tests replace this protocol, never its semantics."""

    def __init__(self, root: Path, executor: CliExecutor) -> None:
        self.root = root
        self.executor = executor
        self.reported_processes = 0

    def execute(self, step: CompiledStep, remaining: float) -> RawOutcome:
        code, out, err = self.executor(list(step.argv), self.root, timeout_s=remaining)
        count = self.executor.process_count - self.reported_processes
        self.reported_processes = self.executor.process_count
        return RawOutcome(code, out, err, processes=count)

    def preflight(self, step: CompiledStep) -> dict[str, object] | None:
        report = diagnostic_report(self.root)
        if not report.get("trustworthy"):
            return cast(dict[str, object] | None, report.get("error"))
        errors = cast(list[dict[str, object]], report.get("errors", []))
        return ({"code": VALIDATION_FAILED, "retryable": False,
                 "scope": classify_scope(errors, list(step.scope))} if errors else None)

    def summarize(self, step: CompiledStep, payload: object) -> str:
        description = step.presentation or {}
        summary = description.get("summary") or SummarySpec()
        return (_cluster_summary(cast(dict[str, object], payload), list(step.argv), summary)
                if description.get("clusters") and isinstance(payload, dict)
                else summarize(payload, fields=summary.get("fields"),
                               max_items=summary.get("max_items", 5),
                               max_bytes=summary.get("max_bytes", 2000)))

    def ready(self, required: list[object], known: list[object], submitting: bool) -> tuple[bool, str]:
        records = [{"receipt_path": cast(str | None, _field(row, "receipt_path")),
                    "snapshot_after": cast(str | None, _field(row, "snapshot_after"))} for row in required]
        all_records = [{"receipt_path": cast(str | None, _field(row, "receipt_path")),
                        "snapshot_after": cast(str | None, _field(row, "snapshot_after"))} for row in known]
        return dependency_ready(self.root, records, all_records, completion_only=submitting)

    def epoch(self, root: Path) -> bool:
        return True

    def resources(self) -> dict[str, int]:
        import resource
        return {"runner_peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                * (1 if sys.platform == "darwin" else 1024),
                "unreported_processes": self.executor.process_count - self.reported_processes}


def run_plan(plan: PlanInput, root: Path, *, poll_s: float = 0.1,
             report_dir: str | Path | None = None, keep_report: bool = False) -> dict[str, object]:
    started = time.monotonic()
    steps = validate_plan(plan, poll_s)
    root = root.resolve()
    session_id = plan.get("session_id")
    writers = {"capability"}
    actual = _cli_executor_factory(root, session_id=session_id, write_commands=writers)
    index = build_index(root, actual, resolve_tasks=any("use" in step and not step.get("describe")
                       and step.get("kind") != "log" for step in steps))
    writers.update(index["write_verbs"])

    def admit(argv: list[str]) -> tuple[str, bool]:
        namespace = actual.validate(argv)
        with _session_bound_envelope(namespace, session_id):
            if namespace.command == "capability":
                actual.envelope_bytes[tuple(argv)] = Path(namespace.payload_file).read_bytes()
        return str(namespace.command), bool(getattr(namespace, "feed", None))

    compiled = compile_plan(steps, index, admit, session_id)
    budget = plan.get("report_max_bytes", 65536)
    with ReportStore(root, Path(report_dir) if report_dir is not None else None,
                     keep_report=keep_report) as store:
        if minimum_ledger_bytes([step.id for step in compiled], str(store.full_path)) > budget:
            raise PlanStepError("report_max_bytes cannot hold the minimum step ledger", REPORT_BUDGET_TOO_SMALL)
        store.inputs(plan, list(actual.envelope_bytes.values()))
        controls = PlanControls(read_workers=1, deadline_s=float(plan.get("deadline_s", 120)),
                                report_max_bytes=budget, on_error=plan.get("on_error", "stop"),
                                session_id=session_id)
        return execute_plan(compiled, root, CliPlanPort(root, actual), controls, store, started, poll_s)
