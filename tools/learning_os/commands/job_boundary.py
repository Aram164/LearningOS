"""The auditable filesystem boundary around the quarantined Job domain.

Read and write commands share these guards so a new Job capability cannot
quietly invent a second containment policy.  This module never discovers Job
content; callers must already be inside an explicitly confirmed Job workflow.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

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
