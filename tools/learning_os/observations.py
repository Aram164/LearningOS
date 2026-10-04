"""Observations of the outside world, overridable for characterization (PLAN D19)."""

from __future__ import annotations

import datetime
import fcntl
import hashlib
import json
import os
import sys
import time
import uuid
from pathlib import Path

OVERRIDE_ENV = "LOS_OBSERVATIONS"
RECORD_ENV = "LOS_OBSERVATIONS_RECORD"

_override_cache: tuple[str | None, dict] | None = None


def _override_file() -> dict:
    """The parsed override object, read once per path.

    ``{}`` when the env var is unset or empty, so every missing key falls
    back to the real observation. A file that cannot be read or parsed
    raises: silently replaying the live world as fixed would only surface
    as a confusing characterization diff.
    """
    global _override_cache
    path = os.environ.get(OVERRIDE_ENV)
    if not path:
        return {}
    if _override_cache is not None and _override_cache[0] == path:
        return _override_cache[1]
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        data = {}
    _override_cache = (path, data)
    return data


def _record_fragment(fragment: dict) -> None:
    """Merge one first-wins fragment into the record file, if recording.

    Called by ``now()`` and, through ``_record_git``, by the Git readers
    in ``githistory``; each records only real observations, never override
    values. Keys already present — from an earlier call in this process or
    from a pre-existing file — are kept.
    """
    path = os.environ.get(RECORD_ENV)
    if not path:
        return
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        existing: dict = {}
    else:
        existing = json.loads(raw)
        if not isinstance(existing, dict):
            existing = {}
    changed = False
    for key, value in fragment.items():
        if isinstance(value, dict) and isinstance(existing.get(key), dict):
            slot = existing[key]
            for subkey, subvalue in value.items():
                if subkey not in slot:
                    slot[subkey] = subvalue
                    changed = True
        elif key not in existing:
            existing[key] = value
            changed = True
    if not changed:
        return
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(existing, sort_keys=True, indent=2) + "\n")


def _record_git(**items: object) -> None:
    """File one real Git fragment under ``git``; called by ``githistory``.

    Private: only the two Git readers call it, with values just read from
    real Git. ``None`` heads are recorded, so a history-less checkout
    replays as null instead of falling back to live Git.
    """
    if items:
        _record_fragment({"git": dict(items)})


def now() -> datetime.datetime:
    """The current time, tz-aware in the local zone.

    The override's ``now`` (ISO 8601) wins when present; a naive value
    reads as local wall time. The real clock is recorded first when
    ``LOS_OBSERVATIONS_RECORD`` names a file.
    """
    real = datetime.datetime.now().astimezone()
    _record_fragment({"now": real.isoformat()})
    raw = _override_file().get("now")
    if raw is None:
        return real
    parsed = datetime.datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        parsed = parsed.astimezone()
    return parsed


def today() -> datetime.date:
    """The current local date: ``now().date()``."""
    return now().date()


def epoch() -> float:
    """Seconds since the Unix epoch: real, or fixed under an override.

    Without an override this is ``time.time()``. With one it is
    ``now().timestamp()``, so semantic clock reads follow the fixed clock.
    """
    if not os.environ.get(OVERRIDE_ENV):
        return time.time()
    return now().timestamp()


def mtime(path: Path, root: Path) -> float:
    """A file's modification time as epoch seconds, fixed under an override.

    Without an override, or when the override has no ``"mtimes"`` object,
    this is ``path.stat().st_mtime``. With one, a path listed under its
    POSIX path relative to ``root`` reads the listed ISO 8601 instant, and
    an unlisted path — including one outside ``root`` — reads
    ``now().timestamp()``. A file the run itself created is therefore
    "now", deterministically.
    """
    mtimes = _override_file().get("mtimes")
    if not isinstance(mtimes, dict):
        return Path(path).stat().st_mtime
    try:
        rel = Path(path).relative_to(Path(root)).as_posix()
    except ValueError:
        return now().timestamp()
    raw = mtimes.get(rel)
    if raw is None:
        return now().timestamp()
    parsed = datetime.datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        parsed = parsed.astimezone()
    return parsed.timestamp()


def git_override() -> dict | None:
    """The override's ``git`` object; None when unset or without that key."""
    data = _override_file()
    if "git" not in data:
        return None
    git = data["git"]
    return git if isinstance(git, dict) else None


def runtime_identity() -> dict:
    """The interpreter this process runs on."""
    return {"python": sys.version.split()[0], "platform": sys.platform}


def new_hex() -> str:
    """Thirty-two hex characters: random, or deterministic under an override.

    Without the override's ``ids`` key this is ``uuid.uuid4().hex``,
    unchanged production randomness. With
    ``"ids": {"seed": str, "counter_file": abs path}`` it reads the counter
    (0 when the file is absent), writes back n+1 under an exclusive lock,
    and returns ``sha256(f"{seed}:{n}").hexdigest()[:32]``: processes
    sharing one counter file never collide, and a fresh counter file
    replays the same sequence.
    """
    ids = _override_file().get("ids")
    if ids is None:
        return uuid.uuid4().hex
    seed = ids["seed"]
    counter_file = ids["counter_file"]
    fd = os.open(counter_file, os.O_RDWR | os.O_CREAT, 0o644)
    with os.fdopen(fd, "r+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            raw = handle.read().strip()
            n = int(raw) if raw else 0
            handle.seek(0)
            handle.truncate()
            handle.write(str(n + 1))
            handle.flush()
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    return hashlib.sha256(f"{seed}:{n}".encode()).hexdigest()[:32]
