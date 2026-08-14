"""Bounded, receipt-producing writes inside the quarantined Job surface.

ADR-010. Three capabilities — ``job.session.log``, ``job.note.stamp`` and
``job.track.progress`` — each reached only through ``los job-* --confirm-job-access``
after the learner deliberately opens the Job destination.

The containment guarantee is not re-implemented here. Every write goes through
the same :class:`~learning_os.transactions.TransactionService` the canon uses,
rooted at ``Job/`` instead of at the repository, so its existing ``_safe_relative``
guard refuses any path outside the quarantine for the same reason and by the same
code that a canonical write cannot escape the repository. Nothing in this module
publishes, validates against the canon, or touches a canonical file.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path

import yaml

from ..transactions import (
    TransactionConflict,
    TransactionFailure,
    TransactionService,
)
from .job import JobDashboardError, _job_root, _read_yaml
from .support import _operator_lock, _root

CONTRACT = "job-write-v1"

#: Where a Job write may land. Deliberately narrower than the dashboard's read
#: allowlist: reading a declared paper is fine, rewriting one is not.
WRITABLE_ROOTS = (
    "workspace-job-deem/scratch",
    "notes",
    "operations",
)

#: Aram's standing rule: the Stratum checkout is strictly read-only — nothing
#: changes there in any shape or form. It is absent from WRITABLE_ROOTS, so the
#: allowlist already refuses it; this names the rule so that adding "stratum"
#: later reads as the deliberate violation it would be, and pins it in a test.
FORBIDDEN_ROOTS = ("stratum",)

#: Digested by the snapshot guard. The authored dashboard is included because a
#: write that races an edit to it should be visible in the receipt.
_FINGERPRINTED = ("dashboard.yaml", "notes", "workspace-job-deem", "operations")

_PROGRESS_RELATIVE = "operations/progress.yaml"


# --------------------------------------------------------------- guards
def _require_confirmation(args) -> None:
    """Every Job write is an explicit gesture; none is implied by context."""
    if not getattr(args, "confirm_job_access", False):
        raise JobDashboardError(
            "Job writes require --confirm-job-access (CLAUDE.md §13, ADR-010)"
        )


def _writable_path(job_root: Path, relative: str) -> Path:
    """Resolve *relative* inside the quarantine, or refuse it."""
    value = str(relative or "").strip().replace("\\", "/")
    if not value or value.startswith("/"):
        raise JobDashboardError("Job write paths must be non-empty relative paths")
    candidate = (job_root / value).resolve()
    try:
        resolved = candidate.relative_to(job_root.resolve())
    except ValueError as exc:
        raise JobDashboardError(
            f"Job write path escapes the quarantine: {value}"
        ) from exc
    posix = resolved.as_posix()
    if any(posix == root or posix.startswith(f"{root}/") for root in FORBIDDEN_ROOTS):
        raise JobDashboardError(
            f"the Stratum checkout is read-only — refusing to write {posix}"
        )
    if not any(posix == root or posix.startswith(f"{root}/") for root in WRITABLE_ROOTS):
        raise JobDashboardError(
            f"Job write path is outside the write allowlist: {posix}"
        )
    return candidate


def _job_fingerprint(job_root: Path) -> str:
    """Digest the Job artifacts a write can touch.

    ``canonical_fingerprint`` digests the canonical roots, none of which exist
    under ``Job/``; rooted here it would return a constant and pretend to be a
    guard (ADR-010).
    """
    digest = hashlib.sha256()
    for relative in _FINGERPRINTED:
        base = job_root / relative
        if not base.exists():
            continue
        files = [base] if base.is_file() else sorted(
            path for path in base.rglob("*") if path.is_file()
        )
        for path in files:
            rel = path.relative_to(job_root)
            if any(part.startswith(".") for part in rel.parts):
                continue
            digest.update(rel.as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def _commit(job_root: Path, writes: dict[Path, str], *, capability: str,
            artifact_ids: list[str], metadata: dict | None = None) -> dict:
    """Commit one Job transaction and return its confirmation block."""
    service = TransactionService(job_root)
    for path in writes:
        if path.exists() and not path.is_file():
            raise JobDashboardError(f"cannot write {path}: target is not a regular file")
    try:
        result = service.commit(
            capability=capability,
            writes=writes,
            artifact_ids=artifact_ids,
            metadata={"contract": CONTRACT, **(metadata or {})},
            fingerprint=lambda: _job_fingerprint(job_root),
        )
    except TransactionConflict as exc:
        raise JobDashboardError(f"Job artifact revision conflict: {exc}") from exc
    except TransactionFailure as exc:
        raise JobDashboardError(f"Job transaction failed: {exc}") from exc
    return {
        "transaction_id": result.transaction_id,
        "receipt": result.receipt_path.relative_to(job_root).as_posix(),
        "revisions": result.revisions,
    }


def _emit(payload: dict, human: str) -> int:
    print(json.dumps({"contract": CONTRACT, "ok": True, **payload},
                     indent=2, sort_keys=True, ensure_ascii=False))
    print(human, file=sys.stderr)
    return 0


def _fail(exc: JobDashboardError) -> int:
    print(f"los: {exc}", file=sys.stderr)
    return 2


# ------------------------------------------------------- session logging
def _session_heading(now: _dt.datetime, args) -> str:
    parts = [f"## {now.strftime('%H:%M')}"]
    if getattr(args, "track", None):
        parts.append(f"· track `{args.track}`")
    if getattr(args, "session", None):
        parts.append(f"· session {args.session}")
    if getattr(args, "minutes", None):
        parts.append(f"· {args.minutes} min")
    return " ".join(parts)


def cmd_job_session_log(args) -> int:
    """Append one session entry to the Job workspace scratch log.

    The workspace's own Next Action asks for this and, until ADR-010, there was
    no mechanism for it — ``scratch/`` was empty.
    """
    try:
        _require_confirmation(args)
        job_root = _job_root(_root(args))
        if not job_root.is_dir():
            raise JobDashboardError(f"no Job directory at {job_root}")

        text = args.text if args.text is not None else sys.stdin.read()
        if not text.strip():
            raise JobDashboardError("nothing to log (empty input)")

        now = _dt.datetime.now().astimezone().replace(microsecond=0)
        relative = f"workspace-job-deem/scratch/{now.strftime('%Y-%m-%d')}-session.md"
        target = _writable_path(job_root, relative)

        entry = f"{_session_heading(now, args)}\n\n{text.strip()}\n"
        if target.is_file():
            existing = target.read_text(encoding="utf-8").rstrip("\n")
            content = f"{existing}\n\n{entry}"
        else:
            content = f"# Job sessions — {now.strftime('%Y-%m-%d')}\n\n{entry}"

        with _operator_lock(job_root):
            confirmation = _commit(
                job_root, {target: content},
                capability="job.session.log",
                artifact_ids=[f"job-session:{now.strftime('%Y-%m-%d')}"],
                metadata={"track": getattr(args, "track", None)},
            )
    except JobDashboardError as exc:
        return _fail(exc)
    return _emit({"logged": relative, **confirmation},
                 f"logged -> Job/{relative}")


# ---------------------------------------------------------- note stamping
def _stamp_frontmatter(text: str, commit: str, status: str) -> str:
    """Rewrite only the living-note header lines, never the body.

    ``notes/README.md`` is binding: Aram writes the notes, the operator files
    and stamps them. This touches ``verified_against`` and ``status`` inside the
    frontmatter block and nothing else — not even other frontmatter keys.
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        raise JobDashboardError("note has no frontmatter block to stamp")
    try:
        closing = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration as exc:
        raise JobDashboardError("note frontmatter is not terminated") from exc

    seen = {"verified_against": False, "status": False}
    for index in range(1, closing):
        stripped = lines[index].lstrip()
        if stripped.startswith("verified_against:"):
            lines[index] = f"verified_against: {commit}"
            seen["verified_against"] = True
        elif stripped.startswith("status:"):
            lines[index] = f"status: {status}"
            seen["status"] = True
    missing = [key for key, found in seen.items() if not found]
    if missing:
        raise JobDashboardError(
            f"note is not a living note — missing header key(s): {', '.join(missing)}"
        )
    return "\n".join(lines)


def _find_note(job_root: Path, note_id: str) -> Path:
    matches = [
        path for path in (job_root / "notes").rglob("*.md")
        if path.stem == note_id
    ]
    if not matches:
        raise JobDashboardError(f"no Job note with id '{note_id}'")
    if len(matches) > 1:
        listing = ", ".join(sorted(p.relative_to(job_root).as_posix() for p in matches))
        raise JobDashboardError(f"ambiguous note id '{note_id}': {listing}")
    return matches[0]


def cmd_job_note_stamp(args) -> int:
    """Re-stamp one living note's ``verified_against`` after Aram confirms it holds."""
    try:
        _require_confirmation(args)
        job_root = _job_root(_root(args))
        note_path = _find_note(job_root, args.note)
        relative = note_path.relative_to(job_root).as_posix()
        _writable_path(job_root, relative)

        status = getattr(args, "status", None) or "current"
        if status not in {"current", "drifting", "stale"}:
            raise JobDashboardError(
                f"status must be current, drifting or stale (got '{status}')"
            )
        stamp = args.commit.strip()
        if not stamp:
            raise JobDashboardError("a stamp needs a commit")
        if getattr(args, "date", None):
            stamp = f"{stamp} ({args.date})"
        elif "(" not in stamp:
            stamp = f"{stamp} ({_dt.date.today().isoformat()})"

        content = _stamp_frontmatter(
            note_path.read_text(encoding="utf-8"), stamp, status)

        with _operator_lock(job_root):
            confirmation = _commit(
                job_root, {note_path: content},
                capability="job.note.stamp",
                artifact_ids=[f"job-note:{args.note}"],
                metadata={"verified_against": stamp, "status": status},
            )
    except JobDashboardError as exc:
        return _fail(exc)
    return _emit({"note": args.note, "verified_against": stamp,
                  "status": status, **confirmation},
                 f"stamped {args.note} -> {stamp} ({status})")


# --------------------------------------------------------- track progress
def _load_progress(job_root: Path) -> dict:
    path = job_root / _PROGRESS_RELATIVE
    if not path.is_file():
        return {"type": "job-progress", "schema_version": 1, "tracks": {}}
    data = _read_yaml(path)
    data.setdefault("type", "job-progress")
    data.setdefault("schema_version", 1)
    tracks = data.get("tracks")
    data["tracks"] = tracks if isinstance(tracks, dict) else {}
    return data


def cmd_job_track_progress(args) -> int:
    """Record one completed learning-track session.

    Progress is machine-owned state and lives in ``operations/progress.yaml``,
    never in the hand-authored ``dashboard.yaml`` — re-serialising an authored
    file destroys its comments, a bug the 2026-08-08 engineering audit already
    found once in the canon (ADR-010).
    """
    try:
        _require_confirmation(args)
        job_root = _job_root(_root(args))
        dashboard = _read_yaml(job_root / "dashboard.yaml")
        known = {
            str(track.get("id")) for track in dashboard.get("learning_tracks", []) or []
            if isinstance(track, dict)
        }
        if args.track not in known:
            listing = ", ".join(sorted(known)) or "none declared"
            raise JobDashboardError(
                f"unknown learning track '{args.track}' (declared: {listing})"
            )
        if args.session < 1:
            raise JobDashboardError("session numbers start at 1")

        progress = _load_progress(job_root)
        entry = progress["tracks"].setdefault(args.track, {})
        completed = entry.get("completed_sessions")
        completed = sorted({*(completed if isinstance(completed, list) else []),
                            args.session})
        entry["completed_sessions"] = completed
        entry["last_session_at"] = _dt.date.today().isoformat()

        target = _writable_path(job_root, _PROGRESS_RELATIVE)
        content = yaml.safe_dump(progress, sort_keys=False, allow_unicode=True,
                                 width=100)

        with _operator_lock(job_root):
            confirmation = _commit(
                job_root, {target: content},
                capability="job.track.progress",
                artifact_ids=[f"job-track:{args.track}"],
                metadata={"session": args.session},
            )
    except JobDashboardError as exc:
        return _fail(exc)
    return _emit({"track": args.track, "completed_sessions": completed,
                  **confirmation},
                 f"{args.track}: session {args.session} done "
                 f"({len(completed)} recorded)")
