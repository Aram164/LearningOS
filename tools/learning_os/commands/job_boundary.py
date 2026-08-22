"""The auditable filesystem boundary around the quarantined Job domain.

Read and write commands share these guards so a new Job capability cannot
quietly invent a second containment policy.  This module never discovers Job
content; callers must already be inside an explicitly confirmed Job workflow.
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
from collections.abc import Sequence
from pathlib import Path, PurePosixPath

READABLE_ROOTS = frozenset({
    "notes", "workspace-job-deem", "papers", "legacy-plans", "plans",
})

# Deliberately narrower than the read boundary: declared papers may be opened,
# but the gateway may not rewrite them.
WRITABLE_ROOTS = (
    "workspace-job-deem/scratch",
    "notes",
    "plans",
    "operations",
)

# The Stratum checkout is strictly read-only.  Keeping this explicit makes any
# future attempt to add it to the write allowlist fail with the domain rule,
# rather than with a generic containment message.
FORBIDDEN_WRITE_ROOTS = ("stratum",)

# This is a system invariant, not a UI preference.  LearningOS may ask the
# checkout one narrowly-scoped question (whether an exact component changed),
# but neither the worktree nor its Git metadata is a write target.
STRATUM_ACCESS = {
    "mode": "read-only",
    "worktree_writes_allowed": False,
    "git_metadata_writes_allowed": False,
}

_STRATUM_REVISION = re.compile(r"^[0-9a-fA-F]{7,64}$")
_PATHSPEC_META = frozenset("*?[")

# Transaction receipts are bookkeeping, not Job domain state, and therefore do
# not stale a dashboard immediately after a successful write.
FINGERPRINTED_PATHS = (
    "dashboard.yaml",
    "notes",
    "workspace-job-deem",
    "plans",
    "operations/progress.yaml",
    "operations/tasks.yaml",
)


class JobDashboardError(ValueError):
    """The bounded Job catalogue cannot be accessed safely."""


def job_root(repository_root: Path) -> Path:
    """Return the declared sibling Job root for a LearningOS repository."""
    # <semestercontext>/LearningOS/repository -> <semestercontext>/Job
    return repository_root.parent.parent / "Job"


def _contained_relative(root: Path, value: object, *, operation: str) -> tuple[Path, Path]:
    relative = str(value or "").strip().replace("\\", "/")
    if not relative or relative.startswith("/"):
        raise JobDashboardError(
            f"Job {operation} paths must be non-empty relative paths"
        )
    candidate = (root / relative).resolve()
    try:
        resolved = candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise JobDashboardError(
            f"Job {operation} path escapes the quarantine: {relative}"
        ) from exc
    return candidate, resolved


def safe_job_path(root: Path, value: object) -> Path:
    """Resolve a dashboard-declared read path inside the read allowlist."""
    candidate, relative = _contained_relative(root, value, operation="dashboard")
    if not relative.parts or relative.parts[0] not in READABLE_ROOTS:
        raise JobDashboardError(
            f"Job dashboard path is outside the read allowlist: {relative.as_posix()}"
        )
    return candidate


def writable_job_path(root: Path, value: object) -> Path:
    """Resolve a write destination inside the narrower write allowlist."""
    candidate, relative = _contained_relative(root, value, operation="write")
    posix = relative.as_posix()
    if any(
        posix == forbidden or posix.startswith(f"{forbidden}/")
        for forbidden in FORBIDDEN_WRITE_ROOTS
    ):
        raise JobDashboardError(
            f"the Stratum checkout is read-only — refusing to write {posix}"
        )
    if not any(
        posix == allowed or posix.startswith(f"{allowed}/")
        for allowed in WRITABLE_ROOTS
    ):
        raise JobDashboardError(
            f"Job write path is outside the write allowlist: {posix}"
        )
    return candidate


#: The freshness labels a stamped anchor can carry.  ``unverified`` is not a
#: failure state: it is the honest answer when the checkout could not be asked.
FRESHNESS_LABELS = ("current", "drifting", "stale", "unverified")


def validate_stratum_revision(value: object) -> str:
    """Return one inert commit id or refuse it before Git sees an argument.

    A revision occupies an option-sensitive position in ``git diff``.  Accepting
    arbitrary authored text there would let a value such as ``--output=...``
    turn a read into a write.  Hash-only stamps make that impossible.
    """
    revision = str(value or "").strip()
    if not _STRATUM_REVISION.fullmatch(revision):
        raise JobDashboardError(
            "Stratum revisions must be 7-64 hexadecimal characters"
        )
    return revision


def validate_stratum_components(value: str | Sequence[str]) -> list[str]:
    """Return exact repo-relative paths safe to pass after Git's ``--``.

    Components are provenance anchors, never pathspec programs.  Canonical
    relative spelling, no traversal, no glob/pathspec syntax, and no ``.git``
    target keep the only permitted Stratum operation a literal read query.
    Deleted files remain valid anchors, so existence is deliberately not part
    of this lexical boundary.
    """
    raw = [value] if isinstance(value, str) else list(value)
    paths: list[str] = []
    for item in raw:
        component = str(item or "").strip()
        canonical = component[:-1] if component.endswith("/") else component
        path = PurePosixPath(canonical)
        if (
            not canonical
            or "\\" in component
            or component.startswith(("/", "-", ":"))
            or component.endswith("//")
            or any(char.isspace() or char == "\x00" for char in component)
            or any(char in component for char in _PATHSPEC_META)
            or path.as_posix() != canonical
            or any(part in {"", ".", "..", ".git"} for part in path.parts)
        ):
            raise JobDashboardError(
                f"unsafe Stratum component path refused: {component or '<empty>'}"
            )
        paths.append(canonical)
    return paths


def stratum_component_changed(
    repo: Path, revision: str, component: str | Sequence[str]
) -> bool | None:
    """Has *component* moved since *revision*? Asked without touching the repo.

    The Stratum checkout is strictly read-only (Aram's standing rule): nothing
    may change there in any shape or form. A plain ``git diff`` still refreshes
    ``.git/index`` as a stat cache, which is a write to a repository we have no
    permission to write to. ``GIT_OPTIONAL_LOCKS=0`` tells git to skip every
    lock and index refresh it would otherwise take for a read command, so drift
    detection observes the checkout without leaving a trace in it.

    *component* may be one path or several. A note is about a single file and
    passes a string; a plan stage's anchor usually spans a few, and passes the
    list — ``git diff`` takes many pathspecs, so both are one subprocess and one
    answer. Several paths mean "has any of them moved", which is the question a
    stage that reads all of them needs answered.

    Returns ``None`` — not ``False`` — when the question could not be asked at
    all: a missing stamp, an unreadable checkout, an unknown revision. The
    caller must not read that as evidence of freshness.
    """
    paths = validate_stratum_components(component)
    if not paths:
        return None
    revision = str(revision or "").strip()
    if not revision:
        return None
    revision = validate_stratum_revision(revision)
    try:
        result = subprocess.run(
            [
                "git", "--no-optional-locks", "diff", "--quiet",
                "--no-ext-diff", "--no-textconv", revision, "--", *paths,
            ],
            cwd=repo,
            capture_output=True,
            timeout=10,
            check=False,
            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode == 0:
        return False
    if result.returncode == 1:
        return True
    return None


def component_freshness(declared: str, changed: bool | None, *, stamped: bool) -> str:
    """Reconcile a hand-written status with what the checkout actually says.

    Computed drift outranks the declared label in one direction only: an author
    may declare ``stale`` and be believed, because they know something the diff
    does not. They may not declare ``current`` and be believed — that is the
    claim the stamp exists to check. A stamped anchor whose checkout could not
    be read reports ``unverified`` rather than falling back to the label.

    Shared by the note surface and the plan surface so that a stage and a note
    pointing at the same component cannot disagree about whether it has moved.
    """
    if declared == "stale":
        return "stale"
    if changed is True:
        return "drifting"
    if changed is False:
        return "current"
    if stamped:
        return "unverified"
    return declared


def job_fingerprint(root: Path) -> str:
    """Digest only authored and machine-owned Job domain state."""
    digest = hashlib.sha256()
    for relative in FINGERPRINTED_PATHS:
        base = root / relative
        if not base.exists():
            continue
        files = [base] if base.is_file() else sorted(
            path for path in base.rglob("*") if path.is_file()
        )
        for path in files:
            rel = path.relative_to(root)
            if any(part.startswith(".") for part in rel.parts):
                continue
            digest.update(rel.as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()
