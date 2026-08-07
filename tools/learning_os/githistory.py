"""Batched Git history lookups.

Both the generator and the validator want "when did this path last change?"
for hundreds of paths. Asking Git once per path costs one subprocess each —
that was ~230 processes in generation and ~34 in validation, together the
single largest cost of a canonical write. Git answers for the whole tree in
one pass, so this module walks history once and serves lookups from a map.

Directories are supported. ``git log --name-only`` only ever emits file paths,
so a directory is answered by the newest entry beneath it — which is what
``git log -- <dir>`` reported when each caller asked separately.

Caching is per process. The CLI runs one command per invocation and a
transaction never commits mid-run, so a cached map cannot go stale in use.
"""

from __future__ import annotations

import subprocess
from functools import lru_cache
from pathlib import Path


def _walk(root: str, fmt: str) -> dict[str, str]:
    """path -> value of `fmt` for the newest commit touching it."""
    try:
        out = subprocess.run(
            ["git", "log", f"--format=%x00{fmt}", "--name-only", "--no-renames"],
            cwd=root, capture_output=True, text=True, timeout=120)
    except Exception:  # noqa: BLE001
        return {}
    found: dict[str, str] = {}
    current = ""
    for line in out.stdout.split("\n"):
        if line.startswith("\x00"):
            current = line[1:].strip()
        elif line and current:
            # git log walks newest-first, so the first sighting wins.
            found.setdefault(line, current)
    return found


@lru_cache(maxsize=4)
def last_commit_dates(root: str) -> dict[str, str]:
    """path -> last commit date, `%cs` (YYYY-MM-DD)."""
    return _walk(root, "%cs")


@lru_cache(maxsize=4)
def last_commit_timestamps(root: str) -> dict[str, str]:
    """path -> last commit Unix timestamp, `%ct`."""
    return _walk(root, "%ct")


def _lookup(table: dict[str, str], rel: str) -> str | None:
    exact = table.get(rel)
    if exact is not None:
        return exact
    prefix = rel.rstrip("/") + "/"
    beneath = [value for path, value in table.items() if path.startswith(prefix)]
    if not beneath:
        return None
    # Both formats sort correctly as numbers/ISO dates once padded equally.
    return max(beneath, key=lambda v: (len(v), v))


def last_commit_date(root: Path | str, rel: str) -> str:
    return _lookup(last_commit_dates(str(root)), rel) or ""


def last_commit_timestamp(root: Path | str, rel: str) -> float | None:
    found = _lookup(last_commit_timestamps(str(root)), rel)
    return float(found) if found else None
