"""The operator lock announces its holder instead of hanging silently (#101)."""

from __future__ import annotations

import json
import os
import select
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

from repo_builders import LOS, run_los


def _hold_in_background(root: Path):
    """Hold the repo's operator lock on a worker thread; returns (release, done)."""
    from learning_os.commands.support import _operator_lock

    release = threading.Event()
    acquired = threading.Event()

    def hold():
        with _operator_lock(root):
            acquired.set()
            release.wait(timeout=60)

    worker = threading.Thread(target=hold, daemon=True)
    worker.start()
    assert acquired.wait(timeout=60), "worker never acquired the operator lock"
    return release, worker


def test_waiting_line_announces_holder_then_completes(mini_repo):
    release, worker = _hold_in_background(mini_repo)
    try:
        proc = subprocess.Popen(
            [sys.executable, str(LOS), "--root", str(mini_repo),
             "unit-list", "--compact"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            # The waiting line must arrive while the lock is still held.
            ready, _, _ = select.select([proc.stderr], [], [], 10)
            assert ready, "no waiting line within 10s while the lock is held"
            line = proc.stderr.readline()
            assert "waiting for the operator lock" in line
            assert f"pid {os.getpid()}" in line
        finally:
            release.set()
        out, err = proc.communicate(timeout=60)
        assert proc.returncode == 0, err
        assert json.loads(out)["contract"] == "unit-list-summary"
    finally:
        release.set()
        worker.join(timeout=60)


def test_lock_timeout_exits_2_naming_holder(mini_repo):
    release, worker = _hold_in_background(mini_repo)
    try:
        start = time.monotonic()
        proc = run_los(mini_repo, "--lock-timeout", "1",
                       "unit-list", "--compact")
        elapsed = time.monotonic() - start
    finally:
        release.set()
        worker.join(timeout=60)
    assert proc.returncode == 2, proc.stderr
    assert "timed out after 1s waiting for the operator lock" in proc.stderr
    assert f"pid {os.getpid()}" in proc.stderr
    assert not proc.stdout
    # The 60s holder was still holding: the timeout fired instead of waiting.
    assert elapsed < 30, elapsed


def test_released_lock_ignores_stale_holder_metadata(mini_repo):
    from learning_os.commands.support import _operator_lock

    with _operator_lock(mini_repo):
        pass  # writes holder metadata; the kernel releases the lock on exit
    proc = run_los(mini_repo, "unit-list", "--compact")
    assert proc.returncode == 0, proc.stderr
    assert "waiting for the operator lock" not in proc.stderr


def test_holder_fragment_ignores_garbage_metadata(tmp_path):
    from learning_os.commands.support import _read_holder

    missing = tmp_path / "absent.lock"
    assert _read_holder(missing) is None
    garbage = tmp_path / "garbage.lock"
    garbage.write_text("not json {{{", encoding="utf-8")
    assert _read_holder(garbage) is None
    partial = tmp_path / "partial.lock"
    partial.write_text(json.dumps({"pid": os.getpid()}), encoding="utf-8")
    assert _read_holder(partial) is None
    valid = tmp_path / "valid.lock"
    valid.write_text(json.dumps({"pid": 123, "command": "los status",
                                 "since": "14:03:22"}),
                     encoding="utf-8")
    assert _read_holder(valid) == "(held by pid 123: los status, since 14:03:22)"


def test_lock_timeout_env_parsing(monkeypatch):
    from learning_os.commands.support import _lock_timeout_seconds

    monkeypatch.delenv("LOS_LOCK_TIMEOUT", raising=False)
    assert _lock_timeout_seconds() is None
    monkeypatch.setenv("LOS_LOCK_TIMEOUT", "2.5")
    assert _lock_timeout_seconds() == 2.5
    monkeypatch.setenv("LOS_LOCK_TIMEOUT", "bogus")
    assert _lock_timeout_seconds() is None
    monkeypatch.setenv("LOS_LOCK_TIMEOUT", "-3")
    assert _lock_timeout_seconds() == 0.0


def test_crashed_holder_never_blocks_next_acquirer(mini_repo, tmp_path):
    """A lock file with a dead holder's metadata still acquires instantly."""
    import hashlib

    from learning_os.commands.support import _operator_lock

    token = hashlib.sha256(str(mini_repo.resolve()).encode("utf-8")).hexdigest()[:16]
    lock_path = Path(tempfile.gettempdir()) / f"learningos-{token}.lock"
    lock_path.write_text(json.dumps({"pid": 2**30, "command": "los crashed",
                                     "since": "00:00:00"}),
                         encoding="utf-8")
    start = time.monotonic()
    with _operator_lock(mini_repo):
        pass
    assert time.monotonic() - start < 10
