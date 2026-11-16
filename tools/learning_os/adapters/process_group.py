"""Shared process-group termination for study broker and launcher children.

Both the broker's Core subprocesses and the launcher's sandboxed child run
in their own session (``start_new_session=True``), so descendants share the
leader's process group. Termination must not stop at the leader: a leader
can exit on SIGTERM while a grandchild that ignores it keeps running.
Escalation therefore checks whether the *group* is still alive after the
leader exits, and only then returns.
"""

from __future__ import annotations

import contextlib
import os
import signal
import subprocess
import time


def _group_alive(pgid: int) -> bool:
    try:
        os.killpg(pgid, 0)
    except (ProcessLookupError, PermissionError, OSError):
        return False
    return True


def terminate_process_group(
    proc: subprocess.Popen,  # type: ignore[type-arg]
    *,
    grace_s: float = 1.0,
    kill_wait_s: float = 2.0,
) -> None:
    """SIGTERM the whole group, then SIGKILL survivors — leader or not."""
    try:
        pgid = os.getpgid(proc.pid)
    except (ProcessLookupError, OSError):
        return
    with contextlib.suppress(ProcessLookupError, PermissionError, OSError):
        os.killpg(pgid, signal.SIGTERM)
    with contextlib.suppress(subprocess.TimeoutExpired):
        proc.wait(timeout=grace_s)
    if not _group_alive(pgid):
        return
    with contextlib.suppress(ProcessLookupError, PermissionError, OSError):
        os.killpg(pgid, signal.SIGKILL)
    with contextlib.suppress(subprocess.TimeoutExpired):
        proc.wait(timeout=kill_wait_s)
    deadline = time.monotonic() + kill_wait_s
    while _group_alive(pgid) and time.monotonic() < deadline:
        time.sleep(0.02)
