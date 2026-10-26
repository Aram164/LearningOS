"""Persistent spawn workers for contiguous, explicitly safe read waves."""
from __future__ import annotations

import json
import multiprocessing
import os
import resource
import sys
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from multiprocessing.connection import wait
from pathlib import Path
from typing import Protocol, cast

from learning_os.app.read_session import ReadSession, dependency_pin
from learning_os.domain.codes import DEADLINE_EXPIRED, READ_WAVE_FAILED, SNAPSHOT_CONFLICT

Raw = tuple[int, str, str]


class Channel(Protocol):
    def send(self, value: object) -> None: ...
    def recv(self) -> object: ...
    def close(self) -> None: ...


def _worker_run(connection: Channel, root_text: str, tasks: list[tuple[int, list[str]]],
            session_id: str | None, expected: str, deadline: float, load_counter: list[int]) -> None:
    from learning_os.adapters.cli import invoke_outcome
    from learning_os.adapters.cli_parser import build_parser
    from learning_os.app.projection import fresh_manifest_and_repo
    from learning_os.app.registry import REGISTRY

    os.environ["LOS_WORKER_DEFER_RECOVERY"] = "1"
    if session_id is not None:
        os.environ["LOS_SESSION_ID"] = session_id
    root = Path(root_text)
    results: list[tuple[int, Raw, int]] = []
    parser = build_parser()
    try:
        if dependency_pin(root) != expected:
            raise ValueError("inputs changed before worker admission")
        session = ReadSession(root)
        with session.activate(lambda: fresh_manifest_and_repo(root)):
            for ordinal, argv in tasks:
                if time.monotonic() >= deadline:
                    results.append((ordinal, (3, json.dumps({"ok": False, "error": {
                        "code": DEADLINE_EXPIRED, "retryable": False}}), ""), 0))
                    continue
                begin = time.monotonic()
                args = parser.parse_args(["--root", root_text, *argv])
                entry = REGISTRY.get(getattr(args, "_operation", ""))
                if Path(args.root).resolve() != root or entry is None or not entry.parallel_safe or entry.kind not in ("query", "tool"):
                    raise ValueError("operation is not admitted as a parallel read")
                outcome = invoke_outcome(args)
                results.append((ordinal, (outcome.exit_code, outcome.stdout, outcome.stderr), round((time.monotonic() - begin) * 1000)))
            if not session.unchanged():
                raise ValueError("inputs changed during read wave")
        connection.send((results, resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024), load_counter[0]))
    except BaseException as exc:
        connection.send(([(ordinal, (3, json.dumps({"ok": False, "error": {
            "code": READ_WAVE_FAILED, "message": str(exc), "retryable": True}}), ""), 0)
            for ordinal, _ in tasks], 0, load_counter[0]))
    finally:
        connection.close()


def _worker(connection: Channel, root_text: str, tasks: list[tuple[int, list[str]]],
            session_id: str | None, expected: str, deadline: float) -> None:
    from learning_os.store.loading import count_repo_loads

    with count_repo_loads() as counter:
        _worker_run(connection, root_text, tasks, session_id, expected, deadline, counter)


def parallel_reads(root: Path, argvs: list[list[str]], workers: int,
                   executor: Callable[[list[str]], Raw] | None = None, *,
                   timeout_s: float = 120, session_id: str | None = None,
                   process_counter: list[int] | None = None,
                   resource_stats: dict[str, int] | None = None,
                   elapsed_times: dict[int, int] | None = None) -> list[Raw]:
    # The injected API is only a test seam; production never threads CLI execution.
    if executor is not None:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            return list(pool.map(executor, argvs))
    from learning_os.app.lock import operator_lock
    from learning_os.app.projection import publish
    from learning_os.app.projection_readiness import observe

    started = time.monotonic()
    with operator_lock(root):
        if not observe(root)["published"]:
            publish(root)
    expected = dependency_pin(root)
    context = multiprocessing.get_context("spawn")
    children = []
    connections = []
    tasks = list(enumerate(argvs))
    count = min(workers, len(tasks))
    result: list[Raw] = [(3, json.dumps({"ok": False, "error": {
        "code": DEADLINE_EXPIRED, "retryable": False}}), "") for _ in tasks]
    try:
        for number in range(count):
            if time.monotonic() - started >= timeout_s:
                break
            parent, child = context.Pipe(duplex=False)
            process = context.Process(target=_worker, args=(
                child, str(root.resolve()), tasks[number::count], session_id, expected, started + timeout_s))
            process.start()
            if process_counter is not None:
                process_counter[0] += 1
            child.close()
            children.append(process)
            connections.append(parent)
        pending = set(connections)
        while pending:
            remaining = timeout_s - (time.monotonic() - started)
            if remaining <= 0:
                break
            ready = wait(list(pending), timeout=remaining)
            if not ready:
                break
            for connection in list(pending):
                if connection not in ready:
                    continue
                try:
                    values, peak, loads = cast(tuple[list[tuple[int, Raw, int]], int, int], connection.recv())
                    if resource_stats is not None:
                        resource_stats["worker_model_loads"] = resource_stats.get("worker_model_loads", 0) + loads
                        resource_stats["worker_peak_rss_sum_upper_bound_bytes"] = resource_stats.get("worker_peak_rss_sum_upper_bound_bytes", 0) + peak
                        resource_stats["worker_peak_rss_max_bytes"] = max(resource_stats.get("worker_peak_rss_max_bytes", 0), peak)
                    for ordinal, outcome, elapsed in values:
                        result[ordinal] = outcome
                        if elapsed_times is not None:
                            elapsed_times[ordinal] = elapsed
                except (EOFError, OSError, ValueError, TypeError):
                    pass
                pending.remove(connection)
        if dependency_pin(root) != expected:
            return [(3, json.dumps({"ok": False, "error": {
                "code": SNAPSHOT_CONFLICT, "retryable": True}}), "") for _ in tasks]
        return result
    finally:
        # Only the enforced defer-recovery workers can be terminated here.
        for process in children:
            if process.is_alive():
                process.terminate()
            process.join(timeout=5)
            if process.is_alive():
                process.kill()
                process.join()
        for connection in connections:
            connection.close()
