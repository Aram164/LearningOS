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


def _git_init(root: Path) -> None:
    for command in (["git", "init", "-q"],
                    ["git", "config", "user.email", "tests@example.invalid"],
                    ["git", "config", "user.name", "Tests"],
                    ["git", "add", "."],
                    ["git", "commit", "-qm", "fixture baseline"]):
        subprocess.run(command, cwd=root, check=True)


def _hold_shared_in_background(root: Path):
    """Hold the repo's operator lock shared on a worker thread."""
    from learning_os.commands.support import _operator_lock

    release = threading.Event()
    acquired = threading.Event()

    def hold():
        with _operator_lock(root, shared=True):
            acquired.set()
            release.wait(timeout=60)

    worker = threading.Thread(target=hold, daemon=True)
    worker.start()
    assert acquired.wait(timeout=60), "worker never acquired the shared lock"
    return release, worker


def test_lock_lives_beside_the_checkout_not_the_tempdir(mini_repo):
    """A git checkout anchors its lock under its own git dir (#110)."""
    from learning_os.commands.support import _operator_lock, _operator_lock_path

    _git_init(mini_repo)
    with _operator_lock(mini_repo):
        pass
    assert _operator_lock_path(mini_repo) == (
        mini_repo / ".git" / "learningos" / "operator.lock")


def test_lock_without_git_dir_keeps_the_temp_location(mini_repo):
    """Synthetic roots without a git dir keep today's temp-dir lock."""
    import hashlib

    from learning_os.commands.support import _operator_lock_path

    token = hashlib.sha256(str(mini_repo.resolve()).encode("utf-8")).hexdigest()[:16]
    assert _operator_lock_path(mini_repo) == (
        Path(tempfile.gettempdir()) / f"learningos-{token}.lock")


def test_reader_without_tmpdir_waits_and_names_the_holder(mini_repo):
    """`env -u TMPDIR` no longer locks a different file than the holder."""
    _git_init(mini_repo)
    release, worker = _hold_in_background(mini_repo)
    try:
        env = {key: value for key, value in os.environ.items()
               if key != "TMPDIR"}
        start = time.monotonic()
        proc = subprocess.run(
            [sys.executable, str(LOS), "--root", str(mini_repo),
             "--lock-timeout", "1", "unit-list", "--compact"],
            capture_output=True, text=True, timeout=60, env=env)
        elapsed = time.monotonic() - start
    finally:
        release.set()
        worker.join(timeout=60)
    assert proc.returncode == 2, proc.stderr
    assert "waiting for the operator lock" in proc.stderr
    assert f"pid {os.getpid()}" in proc.stderr
    assert "timed out after 1s" in proc.stderr
    assert elapsed >= 1.0, elapsed


def test_reader_with_unrelated_tmpdir_waits_too(mini_repo, tmp_path):
    """A foreign TMPDIR joins the same anchored lock, not a sibling file."""
    other_tmp = tmp_path / "other-tmp"
    other_tmp.mkdir()
    _git_init(mini_repo)
    release, worker = _hold_in_background(mini_repo)
    try:
        env = {**os.environ, "TMPDIR": str(other_tmp)}
        proc = subprocess.run(
            [sys.executable, str(LOS), "--root", str(mini_repo),
             "--lock-timeout", "1", "unit-list", "--compact"],
            capture_output=True, text=True, timeout=60, env=env)
    finally:
        release.set()
        worker.join(timeout=60)
    assert proc.returncode == 2, proc.stderr
    assert "waiting for the operator lock" in proc.stderr
    assert f"pid {os.getpid()}" in proc.stderr
    assert list(other_tmp.iterdir()) == []


def test_shared_readers_do_not_wait_for_each_other(mini_repo):
    """Two concurrent current-manifest reads proceed together (#112)."""
    published = run_los(mini_repo, "generate")
    assert published.returncode == 0, published.stderr
    release, worker = _hold_shared_in_background(mini_repo)
    try:
        proc = run_los(mini_repo, "unit-list", "--compact")
    finally:
        release.set()
        worker.join(timeout=60)
    assert proc.returncode == 0, proc.stderr
    assert "waiting for the operator lock" not in proc.stderr
    assert json.loads(proc.stdout)["contract"] == "unit-list-summary"


def test_write_waits_for_a_shared_read(mini_repo, monkeypatch, capsys):
    """A shared read still excludes writers; the waiter is announced."""
    import pytest

    from learning_os.commands.support import WriteRefused, _operator_lock

    release, worker = _hold_shared_in_background(mini_repo)
    monkeypatch.setenv("LOS_LOCK_TIMEOUT", "1")
    try:
        start = time.monotonic()
        with pytest.raises(WriteRefused, match="timed out after 1s"):
            with _operator_lock(mini_repo):
                pass
        elapsed = time.monotonic() - start
    finally:
        release.set()
        worker.join(timeout=60)
    # The writer waited for the background reader instead of proceeding.
    assert elapsed >= 1.0, elapsed
    assert "waiting for the operator lock" in capsys.readouterr().err


def test_nested_exclusive_request_escalates_a_shared_section(mini_repo):
    """A write nested inside a read section strengthens it, safely in-process."""
    from learning_os.commands.support import _held_entry, _operator_lock

    root_key = str(mini_repo.resolve())
    with _operator_lock(mini_repo, shared=True):
        assert _held_entry(root_key)[0] == "shared"
        with _operator_lock(mini_repo):
            assert _held_entry(root_key)[0] == "exclusive"
        assert _held_entry(root_key)[0] == "exclusive"
    assert _held_entry(root_key) is None


def test_shared_section_escalates_past_a_published_journal(mini_repo, monkeypatch):
    """A shared acquisition with a crash journal awaiting recovery goes exclusive."""
    import pytest

    from learning_os.commands import support as command_support
    from learning_os.commands.support import (
        _has_armed_inflight,
        _held_entry,
        _operator_lock,
    )
    from learning_os.transactions import TransactionRecoveryConflict

    journal = mini_repo / "operations" / "transactions" / ".inflight" / "tx-crashed"
    journal.mkdir(parents=True)
    (journal / "intent.json").write_text('{"paths": []}', encoding="utf-8")
    assert _has_armed_inflight(mini_repo) is True
    # Recovery runs exactly as an exclusive acquisition would run it — the
    # hand-made journal is unprovable, so both modes refuse identically.
    with pytest.raises(TransactionRecoveryConflict):
        with _operator_lock(mini_repo, shared=True):
            pass
    recovered = []
    monkeypatch.setattr(command_support, "reconcile_inflight_transactions",
                        lambda root: recovered.append(root))
    root_key = str(mini_repo.resolve())
    with _operator_lock(mini_repo, shared=True):
        assert _held_entry(root_key)[0] == "exclusive"
    assert recovered == [mini_repo]


def test_staging_debris_alone_keeps_a_shared_section_shared(mini_repo):
    """`.preparing-*` debris died before any mutation, so reads stay shared."""
    from learning_os.commands.support import (
        _has_armed_inflight,
        _held_entry,
        _operator_lock,
    )

    staging = mini_repo / "operations" / "transactions" / ".inflight" / ".preparing-tx"
    staging.mkdir(parents=True)
    assert _has_armed_inflight(mini_repo) is False
    root_key = str(mini_repo.resolve())
    with _operator_lock(mini_repo, shared=True):
        assert _held_entry(root_key)[0] == "shared"


def test_git_environment_cannot_redirect_the_checkout_lock(mini_repo, tmp_path, monkeypatch):
    """An inherited GIT_DIR must not let a child bypass this checkout's lock."""
    from learning_os.commands import support

    _git_init(mini_repo)
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    (foreign / "fixture.txt").write_text("foreign git directory")
    _git_init(foreign)
    support._GIT_DIR_CACHE.clear()
    monkeypatch.setenv("GIT_DIR", str(foreign / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(foreign))
    assert support._operator_lock_path(mini_repo) == (
        mini_repo / ".git" / "learningos" / "operator.lock")
    assert not (foreign / ".git" / "learningos").exists()


def test_broken_git_anchor_refuses_instead_of_using_a_second_lock(mini_repo):
    import pytest

    from learning_os.commands.support import WriteRefused, _operator_lock_path

    (mini_repo / ".git").write_text("gitdir: /missing-learningos-git-dir\n")
    with pytest.raises(WriteRefused, match="git directory"):
        _operator_lock_path(mini_repo)


def test_unreadable_crash_journal_directory_refuses_shared_reads(mini_repo, monkeypatch):
    import pytest

    from learning_os.commands.support import _operator_lock

    original = Path.iterdir
    inflight = mini_repo / "operations" / "transactions" / ".inflight"

    def guarded_iterdir(path):
        if path == inflight:
            raise PermissionError("cannot examine armed journals")
        return original(path)

    monkeypatch.setattr(Path, "iterdir", guarded_iterdir)
    with pytest.raises(OSError, match="cannot examine armed journals"):
        with _operator_lock(mini_repo, shared=True):
            pytest.fail("served a read without proving recovery was unnecessary")


def test_failed_escalation_never_leaves_a_reentrant_unlocked_scope(mini_repo, monkeypatch):
    import pytest

    from learning_os.commands import support

    original = support._acquire_flock

    def fail_exclusive(handle, *, exclusive, **kwargs):
        if exclusive:
            raise support.WriteRefused("exclusive acquisition failed")
        return original(handle, exclusive=exclusive, **kwargs)

    monkeypatch.setattr(support, "_acquire_flock", fail_exclusive)
    with support._operator_lock(mini_repo, shared=True):
        with pytest.raises(support.WriteRefused, match="exclusive acquisition failed"):
            with support._operator_lock(mini_repo):
                pytest.fail("exclusive acquisition should fail")
        with pytest.raises(support.WriteRefused, match="no longer held"):
            with support._operator_lock(mini_repo, shared=True):
                pytest.fail("an unlocked outer scope cannot be reused")


def test_synthetic_root_inside_git_checkout_uses_its_own_fallback(tmp_path):
    from learning_os.commands.support import _operator_lock_path

    checkout = tmp_path / "checkout"
    checkout.mkdir()
    (checkout / "fixture.txt").write_text("checkout")
    _git_init(checkout)
    synthetic = checkout / "scratch" / "repository"
    synthetic.mkdir(parents=True)
    assert _operator_lock_path(synthetic) != _operator_lock_path(checkout)
    assert _operator_lock_path(synthetic).parent == Path(tempfile.gettempdir())


def test_linked_worktrees_keep_distinct_git_directory_locks(mini_repo, tmp_path):
    from learning_os.commands.support import _operator_lock_path

    _git_init(mini_repo)
    linked = tmp_path / "linked"
    subprocess.run(["git", "worktree", "add", "--detach", "-q", str(linked)],
                   cwd=mini_repo, check=True)
    original_lock = _operator_lock_path(mini_repo)
    linked_lock = _operator_lock_path(linked)
    assert linked_lock != original_lock
    assert linked_lock == mini_repo / ".git" / "worktrees" / "linked" / "learningos" / "operator.lock"
