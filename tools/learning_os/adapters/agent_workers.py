"""Spawn-based read workers (D09). Workers run reads in child processes via
the public los entry; they defer canonical recovery (see app.lock) and never
execute writes. Injected executors (tests) run in threads on the same API.
"""
from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[2]


def run_read_subprocess(root: Path, argv: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(TOOLS / "los.py"), "--root", str(root), *argv],
        capture_output=True, text=True, cwd=root,
        env={**__import__("os").environ, "LOS_WORKER_DEFER_RECOVERY": "1"})
    return proc.returncode, proc.stdout, proc.stderr


def parallel_reads(root: Path, argvs: list[list[str]], workers: int,
                   executor: Callable[[list[str]], tuple[int, str, str]] | None = None) -> list[tuple[int, str, str]]:
    if workers <= 1 or len(argvs) <= 1:
        if executor is not None:
            return [executor(a) for a in argvs]
        return [run_read_subprocess(root, a) for a in argvs]
    if executor is not None:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            return list(pool.map(executor, argvs))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(lambda a: run_read_subprocess(root, a), argvs))
