"""The operator lock: shared and exclusive acquisition, escalation, and the holder record."""

from __future__ import annotations

import contextlib
import contextvars
import fcntl
import hashlib
import json
import math
import os
import sys
import tempfile
import time
from pathlib import Path

from learning_os.domain.failures import WriteRefused
from learning_os.store import observations
from learning_os.store.session_ledger import (
    _is_anchored,
    _process_state_dir,
)
from learning_os.store.transactions import reconcile_inflight_transactions

#: Roots locked by this context: ``((root_key, mode, handle), ...)`` with
#: mode ``"shared"``, ``"exclusive"``, or ``"released"`` after a failed
#: escalation. Immutable tuples, never mutated in
#: place: escalation replaces the whole value, and the owning scope's reset
#: still restores the pre-scope value afterwards.
_HELD_OPERATOR_LOCKS: contextvars.ContextVar[tuple] = (
    contextvars.ContextVar("learningos_held_operator_locks", default=())
)


#: Environment override for the operator-lock wait. `los --lock-timeout`
#: sets this for the process; in-process callers set it directly. Unset or
#: malformed means wait as long as the holder needs, announced on stderr.
LOS_LOCK_TIMEOUT_ENV = "LOS_LOCK_TIMEOUT"


#: Poll interval while a lock timeout is armed. The default (unbounded)
#: wait keeps kernel blocking with no polling.
_LOCK_POLL_INTERVAL_S = 0.05


def _lock_timeout_seconds() -> float | None:
    """The configured lock wait bound, or None for an unbounded announced wait."""
    raw = os.environ.get(LOS_LOCK_TIMEOUT_ENV)
    if raw is None or not raw.strip():
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    if not math.isfinite(value):
        return None
    return max(0.0, value)


def _read_holder(lock_path: Path) -> str | None:
    """The advisory `(held by pid N: <command>, since HH:MM:SS)` fragment.

    Display only, never trusted for correctness: anything unreadable or
    misshapen answers None and the waiter prints the bare waiting line.
    """
    try:
        record = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(record, dict):
        return None
    pid = record.get("pid")
    command = record.get("command")
    since = record.get("since")
    if (not isinstance(pid, int) or isinstance(pid, bool)
            or not isinstance(command, str) or not isinstance(since, str)):
        return None
    return f"(held by pid {pid}: {command[:200]}, since {since[:32]})"


def _write_holder(handle) -> None:
    """Record this process as the lock holder. Best effort: advisory only."""
    prog = Path(sys.argv[0]).name if sys.argv and sys.argv[0] else "los"
    command = " ".join([prog, *sys.argv[1:3]])[:160] or "los"
    record = {"pid": os.getpid(), "command": command,
              "since": observations.now().replace(tzinfo=None).strftime("%H:%M:%S")}
    try:
        handle.seek(0)
        handle.truncate()
        handle.write(json.dumps(record))
        handle.flush()
    except OSError:
        pass  # a waiter then prints the bare waiting line instead


def _operator_lock_path(root: Path) -> Path:
    if _is_anchored(root):
        return _process_state_dir(root) / "operator.lock"
    token = hashlib.sha256(str(root.resolve()).encode("utf-8")).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / f"learningos-{token}.lock"


def _held_entry(root_key: str) -> tuple[str, object] | None:
    for key, mode, handle in _HELD_OPERATOR_LOCKS.get():
        if key == root_key:
            return mode, handle
    return None


def _acquire_flock(handle, *, exclusive: bool, lock_path: Path,
                   timeout: float | None) -> None:
    """Take the flock both modes contend for, announcing the wait (#101).

    A contender probes first and announces the wait on stderr — with the
    holder's pid, command, and start time when the lock file names them —
    instead of hanging silently. `LOS_LOCK_TIMEOUT` (or `los
    --lock-timeout`) bounds the wait identically for both modes; on expiry
    a WriteRefused naming the holder propagates, which every entry point
    maps to exit 2 with nothing changed.
    """
    flag = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
    try:
        fcntl.flock(handle.fileno(), flag | fcntl.LOCK_NB)
        return
    except BlockingIOError:
        pass
    holder = _read_holder(lock_path)
    detail = f" {holder}" if holder else ""
    print(f"los: waiting for the operator lock{detail}", file=sys.stderr)
    if timeout is None:
        fcntl.flock(handle.fileno(), flag)
        return
    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise WriteRefused(
                f"timed out after {timeout:g}s waiting for the "
                f"operator lock{detail}") from None
        time.sleep(min(_LOCK_POLL_INTERVAL_S, remaining))
        try:
            fcntl.flock(handle.fileno(), flag | fcntl.LOCK_NB)
            return
        except BlockingIOError:
            continue


def _has_armed_inflight(root: Path) -> bool:
    """Whether a published crash journal awaits recovery (read-only probe).

    Staging debris (`.preparing-*`) died before the first canonical
    mutation, so it proves nothing and waits for the next exclusive
    acquisition to drop it. A published journal means canonical state may
    be torn, and a shared lock must not serve it without recovery.
    """
    inflight = root / "operations" / "transactions" / ".inflight"
    try:
        return any(not entry.name.startswith(".preparing-")
                   for entry in inflight.iterdir())
    except FileNotFoundError:
        return False


def _escalate_operator_lock(root: Path) -> bool:
    """Drop a held shared lock and take the exclusive one; True when it dropped.

    Never upgrades in place: the shared lock is released first, then the
    exclusive lock is contended for like any fresh acquisition (announced,
    bounded by the same timeout), and only then do the holder record and
    crash recovery run. Already-exclusive answers False having changed
    nothing. The mode update replaces the context value; the owning
    scope's reset still restores the pre-scope value on exit.
    """
    root_key = str(root.resolve())
    entry = _held_entry(root_key)
    if entry is None:
        raise RuntimeError(
            f"cannot escalate the operator lock for {root_key}: not held")
    mode, handle = entry
    if mode == "exclusive":
        return False
    if mode == "released":
        raise WriteRefused("operator lock is no longer held after a failed escalation")
    # Invalidate re-entrancy before dropping SH. If acquisition, holder
    # publication, or recovery fails, an outer caller that catches the
    # exception must never mistake this scope for a still-held read lock.
    _HELD_OPERATOR_LOCKS.set(tuple(
        (key, "released" if key == root_key else held_mode, held_handle)
        for key, held_mode, held_handle in _HELD_OPERATOR_LOCKS.get()
    ))
    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    _acquire_flock(handle, exclusive=True,
                   lock_path=_operator_lock_path(root),
                   timeout=_lock_timeout_seconds())
    _write_holder(handle)
    reconcile_inflight_transactions(root)
    _HELD_OPERATOR_LOCKS.set(tuple(
        (key, "exclusive" if key == root_key else held_mode, held_handle)
        for key, held_mode, held_handle in _HELD_OPERATOR_LOCKS.get()
    ))
    return True


@contextlib.contextmanager
def _operator_lock(root: Path, *, shared: bool = False):
    """Cross-process lock for every read and write/generation transaction.

    Writes take it exclusive, as before. Reads that only serve a provably
    current manifest take it shared (`LOCK_SH`) so they no longer
    serialize against each other; a read that must rebuild drops the
    shared lock, takes the exclusive one, re-checks the identity, then
    builds (see `_fresh_manifest_and_repo`). A write nested inside a
    shared section escalates it — exclusive subsumes the read guarantee,
    it never violates it — and a shared request inside an exclusive
    section passes straight through.

    Shared holders neither write the holder record (concurrent writers
    would garble it) nor run crash recovery (it writes); when a published
    crash journal is present the acquisition escalates to exclusive
    immediately, so every read still observes post-recovery state. The
    wait announcement and `--lock-timeout` semantics are identical for
    both modes, and re-entrancy is unchanged.
    """
    root_key = str(root.resolve())
    entry = _held_entry(root_key)
    if entry is not None:
        held_mode, _ = entry
        if held_mode == "released":
            raise WriteRefused("operator lock is no longer held after a failed escalation")
        if not shared and held_mode == "shared":
            _escalate_operator_lock(root)
        yield
        return
    lock_path = _operator_lock_path(root)
    timeout = _lock_timeout_seconds()
    try:
        handle = lock_path.open("a+", encoding="utf-8")
    except OSError as exc:
        raise WriteRefused(
            f"operator lock is not writable: {lock_path}: "
            f"{exc.strerror or exc}") from exc
    with handle:
        _acquire_flock(handle, exclusive=not shared, lock_path=lock_path,
                       timeout=timeout)
        mode = "shared" if shared else "exclusive"
        if not shared:
            _write_holder(handle)
            reconcile_inflight_transactions(root)
        context_token = _HELD_OPERATOR_LOCKS.set(
            _HELD_OPERATOR_LOCKS.get() + ((root_key, mode, handle),))
        try:
            if shared and _has_armed_inflight(root):
                _escalate_operator_lock(root)
            yield
        finally:
            _HELD_OPERATOR_LOCKS.reset(context_token)
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
