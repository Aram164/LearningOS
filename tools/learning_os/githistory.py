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

import os
import subprocess
from functools import lru_cache
from pathlib import Path


class GitHistoryError(Exception):
    """Git history could not be read; this is not an empty history."""


def _git(
    root: str, *args: str, git_dir: str | None = None, allowed: tuple[int, ...] = (0,),
) -> subprocess.CompletedProcess:
    try:
        out = subprocess.run(
            ["git", *args],
            cwd=root, capture_output=True, text=True, timeout=120,
            env=None if git_dir is None else {**os.environ, "GIT_DIR": git_dir})
    except (OSError, subprocess.SubprocessError, UnicodeError) as exc:
        detail = getattr(exc, "stderr", None) or ""
        if isinstance(detail, bytes):
            detail = detail.decode(errors="replace")
        raise GitHistoryError(f"git {' '.join(args)} failed: {exc} {detail}".strip()) from exc
    if out.returncode not in allowed:
        raise GitHistoryError(
            f"git {' '.join(args)} failed (exit {out.returncode}): {out.stderr.strip()}")
    return out


def discover_git_dir(root: Path | str) -> str | None:
    """Find the Git metadata directory for root without walking up."""
    root = os.path.abspath(root)
    try:
        if not Path(root).is_dir():
            raise GitHistoryError(f"history root is not a directory: {root}")
        for name in (".git", "HEAD"):  # worktrees (including gitfiles) and bare repos
            try:
                (Path(root) / name).lstat()
            except FileNotFoundError:
                continue
            return str(Path(root) / ".git") if name == ".git" else root
        return None
    except OSError as exc:
        raise GitHistoryError(f"cannot inspect Git metadata at {root}: {exc}") from exc


def read_history(root: Path | str, *args: str) -> str:
    """Read HEAD history, preserving Git's environment and reporting failures.

    The supplied root is a repository boundary: exports without Git metadata
    must not inherit an enclosing checkout's history. Explicit Git environment
    overrides still take precedence. An unborn symbolic HEAD is empty only if
    Git confirms that its target ref is absent, before attempting the log.
    """
    root = os.path.abspath(root)
    git_dir = discover_git_dir(root)
    if git_dir is None and not any(
        name in os.environ for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR")
    ):
        return ""

    # Pin discovered metadata so a damaged .git cannot make Git silently walk
    # up to an enclosing repository. Never replace the caller's GIT_DIR.
    if "GIT_DIR" in os.environ:
        git_dir = None
    head = _git(root, "rev-parse", "--verify", "--quiet", "HEAD",
                git_dir=git_dir, allowed=(0, 1))
    if head.returncode == 1:
        ref = _git(root, "symbolic-ref", "--quiet", "HEAD", git_dir=git_dir).stdout.strip()
        target = _git(root, "show-ref", "--verify", "--quiet", ref,
                      git_dir=git_dir, allowed=(0, 1))
        if target.returncode == 1:
            return ""
    return _git(root, "log", *args, git_dir=git_dir).stdout


def _walk(root: str, fmt: str) -> dict[str, str]:
    """path -> value of `fmt` for the newest commit touching it."""
    stdout = read_history(root, f"--format=%x00{fmt}", "--name-only", "--no-renames")

    found: dict[str, str] = {}
    current = ""
    for line in stdout.split("\n"):
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
