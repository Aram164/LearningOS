"""Bounded, receipt-producing writes inside the quarantined Job surface.

ADR-010. Job capabilities are reached only through ``los job-* --confirm-job-access``
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
import json
import re
import sys
from pathlib import Path

import yaml

from ..transactions import (
    TransactionConflict,
    TransactionFailure,
    TransactionService,
    parse_expected_revisions,
)
from .job import (
    JobDashboardError,
    _frontmatter,
    _job_root,
    _learning_tracks,
    _read_yaml,
    job_fingerprint,
)
from .support import _operator_lock, _root

CONTRACT = "job-write-v1"

#: Where a Job write may land. Deliberately narrower than the dashboard's read
#: allowlist: reading a declared paper is fine, rewriting one is not.
WRITABLE_ROOTS = (
    "workspace-job-deem/scratch",
    "notes",
    "plans",
    "operations",
)

#: Aram's standing rule: the Stratum checkout is strictly read-only — nothing
#: changes there in any shape or form. It is absent from WRITABLE_ROOTS, so the
#: allowlist already refuses it; this names the rule so that adding "stratum"
#: later reads as the deliberate violation it would be, and pins it in a test.
FORBIDDEN_ROOTS = ("stratum",)

_PROGRESS_RELATIVE = "operations/progress.yaml"
_TASKS_RELATIVE = "operations/tasks.yaml"


class JobWriteConflict(JobDashboardError):
    """The Job domain moved since the caller loaded its ephemeral snapshot."""


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


def _expected_revisions(args) -> dict[str, int]:
    try:
        return parse_expected_revisions(getattr(args, "expected_revision", None))
    except ValueError as exc:
        raise JobDashboardError(str(exc)) from exc


def _require_expected_snapshot(args, job_root: Path) -> None:
    expected = str(getattr(args, "expected_snapshot", None) or "").strip()
    if not expected:
        # Human CLI use remains possible. Machine callers always send the
        # dashboard snapshot through the capability envelope.
        return
    actual = f"sha256:{job_fingerprint(job_root)}"
    if expected != actual:
        raise JobWriteConflict(
            "Job workspace changed since this view loaded; reload it before saving"
        )


def _commit(job_root: Path, writes: dict[Path, str], *, capability: str,
            artifact_ids: list[str], expected_revisions: dict[str, int] | None = None,
            metadata: dict | None = None) -> dict:
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
            expected_revisions=expected_revisions or {},
            metadata={"contract": CONTRACT, **(metadata or {})},
            fingerprint=lambda: job_fingerprint(job_root),
        )
    except TransactionConflict as exc:
        raise JobWriteConflict(f"Job artifact revision conflict: {exc}") from exc
    except TransactionFailure as exc:
        raise JobDashboardError(f"Job transaction failed: {exc}") from exc
    return {
        "transaction_id": result.transaction_id,
        "receipt_path": result.receipt_path.relative_to(job_root).as_posix(),
        "artifact_revisions": result.revisions,
    }


def _emit(payload: dict, human: str) -> int:
    print(json.dumps({"contract": CONTRACT, "ok": True, **payload},
                     indent=2, sort_keys=True, ensure_ascii=False))
    print(human, file=sys.stderr)
    return 0


def _fail(exc: JobDashboardError) -> int:
    print(f"los: {exc}", file=sys.stderr)
    return 3 if isinstance(exc, JobWriteConflict) else 2


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

        with _operator_lock(job_root):
            _require_expected_snapshot(args, job_root)
            entry = f"{_session_heading(now, args)}\n\n{text.strip()}\n"
            if target.is_file():
                existing = target.read_text(encoding="utf-8").rstrip("\n")
                content = f"{existing}\n\n{entry}"
            else:
                content = f"# Job sessions — {now.strftime('%Y-%m-%d')}\n\n{entry}"
            confirmation = _commit(
                job_root, {target: content},
                capability="job.session.log",
                artifact_ids=[f"job-session:{now.strftime('%Y-%m-%d')}"],
                expected_revisions=_expected_revisions(args),
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
    matches = []
    for path in (job_root / "notes").rglob("*.md"):
        try:
            meta, _ = _frontmatter(path.read_text(encoding="utf-8"))
        except OSError:
            continue
        if str(meta.get("id") or "").strip() == note_id:
            matches.append(path)
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

        with _operator_lock(job_root):
            _require_expected_snapshot(args, job_root)
            note_path = _find_note(job_root, args.note)
            relative = note_path.relative_to(job_root).as_posix()
            _writable_path(job_root, relative)
            content = _stamp_frontmatter(
                note_path.read_text(encoding="utf-8"), stamp, status)
            confirmation = _commit(
                job_root, {note_path: content},
                capability="job.note.stamp",
                artifact_ids=[f"job-note:{args.note}"],
                expected_revisions=_expected_revisions(args),
                metadata={"verified_against": stamp, "status": status},
            )
    except JobDashboardError as exc:
        return _fail(exc)
    return _emit({"note": args.note, "verified_against": stamp,
                  "status": status, **confirmation},
                 f"stamped {args.note} -> {stamp} ({status})")


# -------------------------------------------------------------- note saving
_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{1,79}$")


def _slug_id(value: object, prefix: str) -> str:
    raw = str(value or "").strip()
    if _ID_PATTERN.fullmatch(raw):
        return raw
    slug = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")
    slug = slug[:60].rstrip("-")
    candidate = f"{prefix}-{slug}" if slug and not slug.startswith(f"{prefix}-") else slug
    if not candidate or not _ID_PATTERN.fullmatch(candidate):
        raise JobDashboardError(
            f"id must use lowercase letters, numbers and hyphens (got '{value}')"
        )
    return candidate


def _render_note(meta: dict, body: str) -> str:
    header = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, width=100).rstrip()
    return f"---\n{header}\n---\n\n{body.strip()}\n"


def _optional_note(job_root: Path, note_id: str) -> Path | None:
    try:
        return _find_note(job_root, note_id)
    except JobDashboardError as exc:
        if str(exc).startswith("no Job note with id"):
            return None
        raise


def cmd_job_note_save(args) -> int:
    """Create or explicitly revise one learner-authored Job note."""
    try:
        _require_confirmation(args)
        if not getattr(args, "approve", False):
            raise JobDashboardError("Job note saving requires --approve")
        note_id = _slug_id(args.note, "job-note")
        title = str(args.title or "").strip()
        body = str(args.body or "").strip()
        folder = str(getattr(args, "folder", None) or "learning").strip()
        if not title or not body:
            raise JobDashboardError("a Job note needs both title and body")
        if folder not in {"learning", "skrub", "stratum"}:
            raise JobDashboardError("note folder must be learning, skrub or stratum")
        job_root = _job_root(_root(args))
        with _operator_lock(job_root):
            _require_expected_snapshot(args, job_root)
            existing = _optional_note(job_root, note_id)
            now = _dt.datetime.now().astimezone().replace(microsecond=0).isoformat()
            if existing is not None:
                relative = existing.relative_to(job_root).as_posix()
                _writable_path(job_root, relative)
                meta, _ = _frontmatter(existing.read_text(encoding="utf-8"))
                if not meta:
                    raise JobDashboardError("existing Job note has no readable frontmatter")
                target = existing
            else:
                relative = f"notes/{folder}/{note_id}.md"
                target = _writable_path(job_root, relative)
                meta = {
                    "id": note_id,
                    "type": "job-note",
                    "status": "draft",
                    "created_at": now,
                }
            meta["title"] = title
            meta["updated_at"] = now
            content = _render_note(meta, body)
            confirmation = _commit(
                job_root, {target: content},
                capability="job.note.save",
                artifact_ids=[f"job-note:{note_id}"],
                expected_revisions=_expected_revisions(args),
                metadata={"created": existing is None},
            )
    except JobDashboardError as exc:
        return _fail(exc)
    return _emit({"note": note_id, "path": relative, **confirmation},
                 f"saved Job note {note_id}")


# -------------------------------------------------------------- plan saving
_STAGE_STATUSES = {"pending", "active", "paused", "complete", "skipped"}
_SCOPE_TRIAGE = {"required-now", "helpful-now", "deferred", "reference-only"}
_RESOURCE_KINDS = {"watch", "read", "practise", "reference"}
_CONCEPT_PATTERN = re.compile(r"^concept-[a-z0-9]+(?:-[a-z0-9]+)*$")
_RESOURCE_PATTERN = re.compile(r"^resource-[a-z0-9]+(?:-[a-z0-9]+)*$")


def _nonempty_strings(value: object, field: str, *, required: bool = False) -> list[str]:
    if value is None and not required:
        return []
    if not isinstance(value, list):
        raise JobDashboardError(f"{field} must be a list")
    result = [str(item).strip() for item in value]
    if any(not item for item in result):
        raise JobDashboardError(f"{field} cannot contain empty values")
    if required and not result:
        raise JobDashboardError(f"{field} needs at least one item")
    return result


def _plan_resource(value: object, stage_id: str) -> dict:
    if not isinstance(value, dict):
        raise JobDashboardError(f"every resource on {stage_id} must be an object")
    kind = str(value.get("kind") or "").strip()
    label = str(value.get("label") or "").strip()
    if kind not in _RESOURCE_KINDS or not label:
        raise JobDashboardError(
            f"resources on {stage_id} need a kind ({', '.join(sorted(_RESOURCE_KINDS))}) "
            "and a label"
        )
    result = {"kind": kind, "label": label}
    resource_id = str(value.get("id") or "").strip()
    if resource_id:
        if not _RESOURCE_PATTERN.fullmatch(resource_id):
            raise JobDashboardError(f"invalid resource id '{resource_id}' on {stage_id}")
        result["id"] = resource_id
    source_id = str(value.get("source_id") or "").strip()
    if source_id:
        if not source_id.startswith("source-") or not _ID_PATTERN.fullmatch(source_id):
            raise JobDashboardError(f"invalid source id '{source_id}' on {stage_id}")
        result["source_id"] = source_id
    for field in ("locator", "url", "vault_path"):
        text = str(value.get(field) or "").strip()
        if text:
            result[field] = text
    scope = str(value.get("scope_triage") or "").strip()
    if scope:
        if scope not in _SCOPE_TRIAGE:
            raise JobDashboardError(f"invalid resource scope '{scope}' on {stage_id}")
        result["scope_triage"] = scope
    return result


def _job_context(value: object, stage_id: str) -> dict:
    if value is None:
        return {"mental_models": [], "read_only_anchor": ""}
    if not isinstance(value, dict):
        raise JobDashboardError(f"job_context on {stage_id} must be an object")
    models = []
    for raw in value.get("mental_models") or []:
        if not isinstance(raw, dict):
            raise JobDashboardError(f"mental models on {stage_id} must be objects")
        label = str(raw.get("label") or "").strip()
        text = str(raw.get("text") or "").strip()
        if not label or not text:
            raise JobDashboardError(f"mental models on {stage_id} need label and text")
        models.append({"label": label, "text": text})
    return {
        "mental_models": models,
        "read_only_anchor": str(value.get("read_only_anchor") or "").strip(),
    }


def _legacy_plan_stage(raw: dict, plan_id: str, index: int) -> dict:
    """Accept the retired flat editor payload but persist only the v2 shape."""
    number = raw.get("number", index)
    title = str(raw.get("title") or "").strip()
    concept = str(raw.get("concept") or "").strip()
    source = str(raw.get("source") or "").strip()
    practice = str(raw.get("practice") or "").strip()
    return {
        "id": f"stage-{plan_id.removeprefix('job-track-')}-{number}",
        "number": number,
        "title": title,
        "status": "pending",
        "objective": concept or f"Build working fluency in {title}.",
        "done_when": [practice or f"Explain and apply {title} without notes."],
        "estimate_minutes": 90,
        "exam_critical": False,
        "concepts": [],
        "scope_triage": "required-now",
        "resources": ([{
            "kind": "read",
            "label": "Legacy learning material",
            "locator": source,
            "scope_triage": "required-now",
        }] if source else []),
        "attachments": [],
        "source_feedback": [],
        "job_context": {
            "mental_models": ([{"label": "Mental model", "text": concept}] if concept else []),
            "read_only_anchor": str(raw.get("anchor") or "").strip(),
        },
    }


def _plan_stage(value: object, plan_id: str, index: int, seen: set[int]) -> dict:
    if not isinstance(value, dict):
        raise JobDashboardError("every plan stage must be an object")
    number = value.get("number", index)
    title = str(value.get("title") or "").strip()
    if not isinstance(number, int) or number < 1 or number in seen or not title:
        raise JobDashboardError("plan stages need unique positive numbers and titles")
    seen.add(number)
    stage_id = str(value.get("id") or "").strip()
    if not stage_id:
        stage_id = _slug_id(f"stage-{plan_id}-{number}-{title}", "stage")
    if not stage_id.startswith("stage-") or not _ID_PATTERN.fullmatch(stage_id):
        raise JobDashboardError(f"invalid stage id '{stage_id}'")
    status = str(value.get("status") or "pending").strip()
    if status not in _STAGE_STATUSES:
        raise JobDashboardError(f"invalid stage status '{status}' on {stage_id}")
    objective = str(value.get("objective") or "").strip()
    if not objective:
        raise JobDashboardError(f"{stage_id} needs an objective")
    done_when = _nonempty_strings(value.get("done_when"), f"done_when on {stage_id}", required=True)
    estimate = value.get("estimate_minutes")
    if estimate is not None and (not isinstance(estimate, int) or estimate < 1):
        raise JobDashboardError(f"estimate_minutes on {stage_id} must be a positive integer")
    concepts = _nonempty_strings(value.get("concepts"), f"concepts on {stage_id}")
    if any(not _CONCEPT_PATTERN.fullmatch(item) for item in concepts) or len(set(concepts)) != len(concepts):
        raise JobDashboardError(f"concepts on {stage_id} must be unique concept ids")
    scope = str(value.get("scope_triage") or "required-now").strip()
    if scope not in _SCOPE_TRIAGE:
        raise JobDashboardError(f"invalid stage scope '{scope}' on {stage_id}")
    resources = [
        _plan_resource(resource, stage_id) for resource in (value.get("resources") or [])
    ]
    result = {
        "id": stage_id,
        "number": number,
        "title": title,
        "status": status,
        "objective": objective,
        "done_when": done_when,
    }
    if estimate is not None:
        result["estimate_minutes"] = estimate
    result.update({
        "exam_critical": value.get("exam_critical") is True,
        "concepts": concepts,
        "scope_triage": scope,
        "resources": resources,
        "attachments": list(value.get("attachments") or []),
        "source_feedback": list(value.get("source_feedback") or []),
        "job_context": _job_context(value.get("job_context"), stage_id),
    })
    return result


def _plan_record(value: object) -> dict:
    if not isinstance(value, dict):
        raise JobDashboardError("plan must be an object")
    title = str(value.get("title") or "").strip()
    plan_id = _slug_id(value.get("id") or title, "job-plan")
    if not title:
        raise JobDashboardError("a learning plan needs a title")
    horizon = str(value.get("horizon") or "now")
    if horizon not in {"now", "next", "later"}:
        raise JobDashboardError("plan horizon must be now, next or later")
    raw_stages = value.get("stages")
    if raw_stages is None and value.get("sessions") is not None:
        raw_stages = [
            _legacy_plan_stage(raw, plan_id, index)
            for index, raw in enumerate(value.get("sessions") or [], start=1)
            if isinstance(raw, dict)
        ]
    if not isinstance(raw_stages, list):
        raise JobDashboardError("plan stages must be a list")
    stages = []
    seen: set[int] = set()
    for index, raw in enumerate(raw_stages, start=1):
        stages.append(_plan_stage(raw, plan_id, index, seen))
    if not stages:
        raise JobDashboardError("a learning plan needs at least one stage")
    return {
        "type": "job-learning-plan",
        "schema_version": 2,
        "id": plan_id,
        "title": title,
        "status": str(value.get("status") or "ready"),
        "horizon": horizon,
        "cadence": str(value.get("cadence") or "").strip(),
        "outcome": str(value.get("outcome") or "").strip(),
        "stages": sorted(stages, key=lambda row: row["number"]),
    }


def cmd_job_plan_save(args) -> int:
    """Create or replace one structured plan without touching legacy Markdown."""
    try:
        _require_confirmation(args)
        if not getattr(args, "approve", False):
            raise JobDashboardError("Job plan saving requires --approve")
        plan = _plan_record(args.plan)
        job_root = _job_root(_root(args))
        with _operator_lock(job_root):
            _require_expected_snapshot(args, job_root)
            relative = f"plans/{plan['id']}.yaml"
            target = _writable_path(job_root, relative)
            content = yaml.safe_dump(plan, sort_keys=False, allow_unicode=True, width=100)
            confirmation = _commit(
                job_root, {target: content},
                capability="job.plan.save",
                artifact_ids=[f"job-plan:{plan['id']}"],
                expected_revisions=_expected_revisions(args),
            )
    except JobDashboardError as exc:
        return _fail(exc)
    return _emit({"plan": plan["id"], "path": relative, **confirmation},
                 f"saved Job plan {plan['id']}")


# -------------------------------------------------------------- task saving
def _load_tasks(job_root: Path) -> dict:
    path = job_root / _TASKS_RELATIVE
    if not path.is_file():
        return {"type": "job-task-list", "schema_version": 1, "tasks": []}
    data = _read_yaml(path)
    if data.get("type") != "job-task-list" or data.get("schema_version") != 1:
        raise JobDashboardError("unsupported Job task-list contract")
    data["tasks"] = [row for row in (data.get("tasks") or []) if isinstance(row, dict)]
    return data


def cmd_job_task_save(args) -> int:
    """Create or update one task in the machine-owned Job task list."""
    try:
        _require_confirmation(args)
        raw = args.task
        if not isinstance(raw, dict):
            raise JobDashboardError("task must be an object")
        title = str(raw.get("title") or "").strip()
        if not title:
            raise JobDashboardError("a Job task needs a title")
        task_id = _slug_id(raw.get("id") or title, "job-task")
        horizon = str(raw.get("horizon") or "now")
        status = str(raw.get("status") or "open")
        if horizon not in {"now", "next", "later"}:
            raise JobDashboardError("task horizon must be now, next or later")
        if status not in {"open", "done"}:
            raise JobDashboardError("task status must be open or done")
        job_root = _job_root(_root(args))
        with _operator_lock(job_root):
            _require_expected_snapshot(args, job_root)
            task_list = _load_tasks(job_root)
            rows = task_list["tasks"]
            existing = next((row for row in rows if str(row.get("id")) == task_id), None)
            now = _dt.datetime.now().astimezone().replace(microsecond=0).isoformat()
            record = {
                "id": task_id,
                "title": title,
                "details": str(raw.get("details") or "").strip(),
                "horizon": horizon,
                "status": status,
                "track_id": str(raw.get("track_id") or "").strip(),
                "created_at": str((existing or {}).get("created_at") or now),
                "updated_at": now,
            }
            if existing is None:
                rows.append(record)
            else:
                rows[rows.index(existing)] = record
            target = _writable_path(job_root, _TASKS_RELATIVE)
            content = yaml.safe_dump(task_list, sort_keys=False, allow_unicode=True, width=100)
            confirmation = _commit(
                job_root, {target: content},
                capability="job.task.save",
                artifact_ids=[f"job-task:{task_id}"],
                expected_revisions=_expected_revisions(args),
            )
    except JobDashboardError as exc:
        return _fail(exc)
    return _emit({"task": task_id, "status": status, **confirmation},
                 f"saved Job task {task_id}")


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
    """Complete or reopen one declared learning-track session.

    Progress is machine-owned state and lives in ``operations/progress.yaml``,
    never in the hand-authored ``dashboard.yaml`` — re-serialising an authored
    file destroys its comments, a bug the 2026-08-08 engineering audit already
    found once in the canon (ADR-010).
    """
    try:
        _require_confirmation(args)
        job_root = _job_root(_root(args))
        state = str(getattr(args, "state", None) or "done")
        if state not in {"done", "open"}:
            raise JobDashboardError("track progress state must be done or open")
        with _operator_lock(job_root):
            _require_expected_snapshot(args, job_root)
            dashboard = _read_yaml(job_root / "dashboard.yaml")
            progress = _load_progress(job_root)
            tracks = {track["id"]: track for track in _learning_tracks(
                dashboard, job_root, progress.get("tracks") or {},
            )}
            track = tracks.get(args.track)
            if track is None:
                listing = ", ".join(sorted(tracks)) or "none declared"
                raise JobDashboardError(
                    f"unknown learning track '{args.track}' (declared: {listing})"
                )
            session_numbers = {stage["number"] for stage in track["stages"]}
            if args.session not in session_numbers:
                raise JobDashboardError(
                    f"track '{args.track}' has no session {args.session}"
                )
            entry = progress["tracks"].setdefault(args.track, {})
            existing = {
                number for number in (entry.get("completed_sessions") or [])
                if isinstance(number, int)
            }
            if state == "done":
                existing.add(args.session)
                entry["last_session_at"] = _dt.date.today().isoformat()
            else:
                existing.discard(args.session)
            completed = sorted(existing)
            entry["completed_sessions"] = completed
            target = _writable_path(job_root, _PROGRESS_RELATIVE)
            content = yaml.safe_dump(progress, sort_keys=False, allow_unicode=True,
                                     width=100)
            confirmation = _commit(
                job_root, {target: content},
                capability="job.track.progress",
                artifact_ids=[f"job-track:{args.track}"],
                expected_revisions=_expected_revisions(args),
                metadata={"session": args.session, "state": state},
            )
    except JobDashboardError as exc:
        return _fail(exc)
    return _emit({"track": args.track, "state": state,
                  "completed_sessions": completed,
                  **confirmation},
                 f"{args.track}: session {args.session} {state} "
                 f"({len(completed)} recorded)")
