"""Explicit, read-only access to the quarantined Job dashboard.

The ordinary loader, projection, search, validation, and AI surfaces never call
this module.  It is reached only through ``los job-dashboard
--confirm-job-access`` after the learner deliberately opens the Job view.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Sequence
from pathlib import Path

import yaml

from ..contracts import ContractValidationError, validate_contract
from ..transactions import artifact_revision
from .job_boundary import (
    READABLE_ROOTS,
    STRATUM_ACCESS,
    JobDashboardError,
    component_freshness,
    job_fingerprint,
    job_root,
    safe_job_path,
    stratum_component_changed,
)
from .support import _fresh_manifest, _root

CONTRACT = "job-dashboard-v2"
# Backward-compatible internal names used by the command module and older tests.
ALLOWED_TOP_LEVELS = READABLE_ROOTS
_job_root = job_root
_safe_job_path = safe_job_path


def _read_yaml(path: Path) -> dict:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise JobDashboardError(f"cannot read {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise JobDashboardError(f"expected an object in {path.name}")
    return value


def _frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    try:
        data = yaml.safe_load(text[4:end]) or {}
    except yaml.YAMLError:
        data = {}
    return (data if isinstance(data, dict) else {}), text[end + 5:]


def _plain(value: object) -> str:
    text = str(value or "")
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"[`*>#]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" -–—\n\t")


def _section(text: str, heading: str) -> str:
    match = re.search(
        rf"^##\s+{re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def _first_paragraph(value: str) -> str:
    return _plain(re.split(r"\n\s*\n", value.strip(), maxsplit=1)[0] if value else "")


def _workspace(config: dict, path: Path, job_root: Path) -> dict:
    """Project the record-shaped workspace block from ``dashboard.yaml``.

    The dashboard used to rename Markdown headings into API fields with regular
    expressions.  That made prose structure an undeclared wire contract.  Job's
    bounded catalogue now carries the small read record explicitly; ``path`` is
    retained only as the user-openable source document.
    """
    fields = (
        "id", "title", "status", "standing", "objective", "current_scope",
        "next_action", "open_questions",
    )
    missing = [field for field in fields if field not in config]
    if missing:
        raise JobDashboardError(
            "workspace catalogue record is missing: " + ", ".join(missing)
        )
    return {
        "id": config["id"],
        "title": config["title"],
        "status": config["status"],
        "standing": config["standing"],
        "objective": config["objective"],
        "current_scope": config["current_scope"],
        "next_action": config["next_action"],
        "open_questions": config["open_questions"],
        "path": path.relative_to(job_root).as_posix(),
    }


def _note_summary(body: str) -> str:
    heading = re.search(r"^#\s+.+$", body, flags=re.MULTILINE)
    tail = body[heading.end():] if heading else body
    quote = re.search(r"(?:^>.*(?:\n>.*)*)", tail, flags=re.MULTILINE)
    if quote:
        return _plain(quote.group(0))
    return _first_paragraph(tail)


# Drift detection now lives on the Job boundary, so the note surface, the plan
# surface and the offline checker all ask the checkout the same question in the
# same way. Kept as a module-level alias because this name is how the command
# module has always referred to it.
_git_changed = stratum_component_changed


#: Stratum's own pipeline, capture → run. `notes/README.md` already groups the
#: components this way; deriving the layer here means the interface can render a
#: map instead of a flat list without owning a second copy of the grouping rule.
LAYERS = (
    ("capture", "Capture / frontend", "building the DAG from user code"),
    ("logical", "Logical IR", "the operator tree"),
    ("rewrites", "Rewrites", "logical and cost-based optimization"),
    ("physical", "Physical", "lowering to executable ops"),
    ("runtime", "Runtime", "execution"),
    ("cross-cutting", "Cross-cutting", ""),
)

#: Each entry matches the package form (`optimizer/ir/…`) and the single-module
#: form (`optimizer/ir.py`) — a layer can be either, and reading only the first
#: would silently file the module under the broader `optimizer/` bucket below.
_LAYER_RULES = (
    ("logical", ("optimizer/ir/", "optimizer/ir.")),
    ("physical", ("optimizer/physical/", "optimizer/physical.")),
    ("rewrites", ("optimizer/",)),
    ("runtime", ("runtime/", "_rust")),
    ("capture", ("_api.py", "patching/")),
)


def _layer_for(component: str, kind: str) -> str:
    """Place one note on the pipeline. Upstream skrub notes describe capture."""
    if kind == "skrub":
        return "capture"
    value = component.strip().replace("\\", "/")
    if not value:
        return ""
    # `optimizer/ir/` and `optimizer/physical/` are tested before the bare
    # `optimizer/` prefix, so the specific layers win over the rewrites bucket.
    for layer, prefixes in _LAYER_RULES:
        if any(prefix in value for prefix in prefixes):
            return layer
    return "cross-cutting"


def _note_record(path: Path, job_root: Path) -> dict | None:
    if path.name in {"README.md", "_TEMPLATE.md"}:
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    meta, body = _frontmatter(text)
    note_id = str(meta.get("id") or "").strip()
    title = str(meta.get("title") or "").strip()
    if not note_id or not title:
        return None
    relative = path.relative_to(job_root).as_posix()
    if relative.startswith("notes/stratum/"):
        kind = "stratum"
    elif relative.startswith("notes/skrub/") or path.name.startswith("note-skrub"):
        kind = "skrub"
    else:
        kind = "learning"
    verified = str(meta.get("verified_against") or "").strip()
    revision = verified.split()[0] if verified else ""
    component = str(meta.get("component") or "").strip()
    declared = str(meta.get("status") or meta.get("state") or "reference").strip()
    changed = (
        stratum_component_changed(job_root / "stratum", revision, component)
        if kind == "stratum" else None
    )
    freshness = component_freshness(
        declared, changed, stamped=(kind == "stratum" and bool(component))
    )
    concepts = [str(item) for item in (meta.get("concepts") or []) if str(item).strip()]
    family = next((item.removesuffix("-family") for item in concepts if item.endswith("-family")), "")
    return {
        "id": note_id,
        "title": title,
        "kind": kind,
        "family": family,
        "summary": _note_summary(body),
        "body": body.strip(),
        "path": relative,
        "component": component,
        "layer": _layer_for(component, kind),
        "verified_against": verified,
        "declared_status": declared,
        "freshness": freshness,
        "revision": artifact_revision(job_root, f"job-note:{note_id}"),
    }


def _notes(config: dict, job_root: Path) -> dict:
    roots = config.get("roots") or []
    if not isinstance(roots, list):
        raise JobDashboardError("notes.roots must be a list")
    paths: set[Path] = set()
    for root_value in roots:
        root = _safe_job_path(job_root, root_value)
        if not root.is_dir():
            continue
        paths.update(root.rglob("*.md"))
    records = [record for path in sorted(paths)
               if (record := _note_record(path, job_root)) is not None]
    skrub = [record for record in records if record["kind"] == "skrub"]
    stratum = [record for record in records if record["kind"] == "stratum"]
    learning = [record for record in records if record["kind"] == "learning"]
    health = {
        label: sum(1 for record in stratum if record["freshness"] == label)
        for label in ("current", "drifting", "stale")
    }
    health["unverified"] = len(stratum) - sum(health.values())
    # The layer roster is published whole, empty layers included: a layer with no
    # notes is the finding, and a view that omitted it would hide exactly that.
    layers = [
        {
            "id": layer_id,
            "title": title,
            "summary": summary,
            "note_ids": [record["id"] for record in records if record["layer"] == layer_id],
        }
        for layer_id, title, summary in LAYERS
    ]
    return {
        "learning": learning,
        "skrub": skrub,
        "stratum": stratum,
        "health": health,
        "layers": layers,
    }


def _field(block: str, label: str) -> str:
    match = re.search(
        rf"^-\s+\*\*{re.escape(label)}:\*\*\s*(.*?)(?=^-\s+\*\*|^##{{2,3}}\s+|^---\s*$|\Z)",
        block,
        flags=re.MULTILINE | re.DOTALL,
    )
    return _plain(match.group(1)) if match else ""


def _progress(job_root: Path) -> dict:
    """Machine-owned track progress, merged at read time.

    It lives in ``operations/progress.yaml`` rather than in the authored
    ``dashboard.yaml`` so a write never re-serialises a hand-written file
    (ADR-010). The dashboard therefore stays config; this stays state.
    """
    path = job_root / "operations" / "progress.yaml"
    if not path.is_file():
        return {}
    tracks = _read_yaml(path).get("tracks")
    return tracks if isinstance(tracks, dict) else {}


def _legacy_stage(number: int, title: str, concept: str, source: str,
                  anchor: str, practice: str) -> dict:
    """Project retired prose sessions into the common stage read model."""
    return {
        "id": f"stage-legacy-{number}",
        "number": number,
        "title": title,
        "status": "pending",
        "objective": concept or f"Build working fluency in {title}.",
        "done_when": [practice] if practice else [],
        "estimate_minutes": None,
        "exam_critical": False,
        "concepts": [],
        "scope_triage": "required-now",
        "resources": ([{
            "id": None,
            "kind": "read",
            "label": "Legacy learning material",
            "source_id": None,
            "locator": source,
            "url": None,
            "vault_path": None,
            "scope_triage": "required-now",
        }] if source else []),
        "attachments": [],
        "source_feedback": [],
        "job_context": {
            "mental_models": ([{"label": "Mental model", "text": concept}] if concept else []),
            "read_only_anchor": anchor,
            # Legacy Markdown plans carry no stamp, so their anchors report
            # `unverified` rather than borrowing a freshness they never earned.
            "component": [],
            "verified_against": "",
            "freshness": "unverified" if anchor else "",
        },
    }


def _structured_resource(value: object, stage_id: str) -> dict:
    if not isinstance(value, dict):
        raise JobDashboardError(f"learning plan stage {stage_id} has an invalid resource")
    kind = str(value.get("kind") or "").strip()
    label = str(value.get("label") or "").strip()
    if kind not in {"watch", "read", "practise", "reference"} or not label:
        raise JobDashboardError(f"learning plan stage {stage_id} has an invalid resource")
    return {
        "id": str(value.get("id") or "").strip() or None,
        "kind": kind,
        "label": label,
        "source_id": str(value.get("source_id") or "").strip() or None,
        "locator": str(value.get("locator") or "").strip() or None,
        "url": str(value.get("url") or "").strip() or None,
        "vault_path": str(value.get("vault_path") or "").strip() or None,
        "scope_triage": str(value.get("scope_triage") or "").strip() or None,
    }


def _stage_freshness_resolver(job_root: Path) -> Callable[[Sequence[str], str], str]:
    """One drift question per distinct (component, revision) pair, per build.

    Ninety-one stages can easily point at a few dozen distinct source files, and
    every uncached lookup is a `git diff` subprocess. The cache is created per
    dashboard build rather than held on the module so that a long-lived process
    (or a test) cannot serve an answer from a checkout that has since moved.
    """
    repo = job_root / "stratum"
    cache: dict[tuple[tuple[str, ...], str], str] = {}

    def resolve(component: Sequence[str], verified: str) -> str:
        key = (tuple(component), verified)
        if key not in cache:
            revision = verified.split()[0] if verified else ""
            changed = stratum_component_changed(repo, revision, component)
            # `stamped` is true whenever the stage names source files: those
            # are a checkable claim, so an unanswerable question is
            # `unverified` rather than a silent pass.
            cache[key] = component_freshness("", changed, stamped=bool(key[0]))
        return cache[key]

    return resolve


def _structured_stage(value: object, freshness: Callable[[str, str], str]) -> dict:
    if not isinstance(value, dict):
        raise JobDashboardError("learning plan has an invalid stage")
    stage_id = str(value.get("id") or "").strip()
    number = value.get("number")
    title = str(value.get("title") or "").strip()
    objective = str(value.get("objective") or "").strip()
    done_when = [
        str(item).strip() for item in (value.get("done_when") or [])
        if str(item).strip()
    ]
    if (not stage_id.startswith("stage-") or not isinstance(number, int)
            or number < 1 or not title or not objective or not done_when):
        raise JobDashboardError("learning plan has an invalid stage contract")
    context = value.get("job_context") or {}
    if not isinstance(context, dict):
        raise JobDashboardError(f"learning plan stage {stage_id} has invalid job_context")
    models = []
    for model in context.get("mental_models") or []:
        if not isinstance(model, dict):
            continue
        label = str(model.get("label") or "").strip()
        text = str(model.get("text") or "").strip()
        if label and text:
            models.append({"label": label, "text": text})
    anchor = str(context.get("read_only_anchor") or "").strip()
    component = [
        str(item).strip() for item in (context.get("component") or []) if str(item).strip()
    ]
    verified = str(context.get("verified_against") or "").strip()
    estimate = value.get("estimate_minutes")
    return {
        "id": stage_id,
        "number": number,
        "title": title,
        "status": str(value.get("status") or "pending"),
        "objective": objective,
        "done_when": done_when,
        "estimate_minutes": estimate if isinstance(estimate, int) and estimate > 0 else None,
        "exam_critical": value.get("exam_critical") is True,
        "concepts": [str(item) for item in (value.get("concepts") or []) if str(item)],
        "scope_triage": str(value.get("scope_triage") or "required-now"),
        "resources": [
            _structured_resource(resource, stage_id)
            for resource in (value.get("resources") or [])
        ],
        "attachments": list(value.get("attachments") or []),
        "source_feedback": list(value.get("source_feedback") or []),
        "job_context": {
            "mental_models": models,
            "read_only_anchor": anchor,
            "component": component,
            "verified_against": verified,
            # Computed, never authored. A stage that names components gets the
            # same treatment a Stratum note gets: the checkout is asked, and an
            # unanswerable question reports `unverified` rather than `current`.
            # A stage whose anchor names no source file at all — the git track
            # anchors are about git commands, not code — reports nothing, because
            # there is nothing that could drift.
            "freshness": freshness(component, verified) if component else "",
        },
    }


def _track(entry: dict, job_root: Path, progress: dict | None = None) -> dict:
    path = _safe_job_path(job_root, entry.get("path"))
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise JobDashboardError(f"cannot read learning track {path.name}: {exc}") from exc
    stages: list[dict] = []
    matches = list(re.finditer(r"^###\s+Session\s+(\d+)\s+[—-]\s+(.+?)\s*$", text, flags=re.MULTILINE))
    for index, match in enumerate(matches):
        block = text[match.end():matches[index + 1].start() if index + 1 < len(matches) else len(text)]
        stages.append(_legacy_stage(
            int(match.group(1)),
            _plain(match.group(2)),
            _field(block, "Concept"),
            _field(block, "Source"),
            _field(block, "Stratum anchor"),
            _field(block, "Rebuild/stretch"),
        ))
    outcome = _first_paragraph(_section(text, 'Definition of "there"'))
    track_id = str(entry.get("id") or path.stem)
    recorded = (progress or {}).get(track_id) or {}
    completed = [
        number for number in (recorded.get("completed_sessions") or [])
        if isinstance(number, int)
    ]
    for stage in stages:
        stage["done"] = stage["number"] in completed
    return {
        "id": track_id,
        "title": str(entry.get("title") or path.stem),
        "status": str(entry.get("status") or "ready"),
        "cadence": str(entry.get("cadence") or ""),
        "horizon": str(entry.get("horizon") or "now"),
        "outcome": outcome,
        "stages": stages,
        "completed_sessions": sorted(completed),
        "last_session_at": str(recorded.get("last_session_at") or ""),
        "path": path.relative_to(job_root).as_posix(),
        "source_kind": "legacy-markdown",
        "revision": artifact_revision(job_root, f"job-plan:{track_id}"),
    }


def _structured_track(
    path: Path,
    job_root: Path,
    progress: dict,
    repository_root: Path,
) -> dict:
    data = _read_yaml(path)
    version = data.get("schema_version")
    if data.get("type") != "job-learning-plan" or version not in {1, 2}:
        raise JobDashboardError(f"unsupported learning plan contract in {path.name}")
    if version == 2:
        try:
            validate_contract(
                repository_root,
                "job-plan.schema.json",
                data,
                label=f"job-plan-v2 ({path.name})",
            )
        except ContractValidationError as exc:
            raise JobDashboardError(str(exc)) from exc
    track_id = str(data.get("id") or path.stem).strip()
    title = str(data.get("title") or "").strip()
    if not track_id or not title:
        raise JobDashboardError(f"learning plan {path.name} needs id and title")
    stages = []
    seen: set[int] = set()
    freshness = _stage_freshness_resolver(job_root)
    rows = data.get("stages") if version == 2 else data.get("sessions")
    for row in rows or []:
        if version == 2:
            stage = _structured_stage(row, freshness)
        elif isinstance(row, dict):
            stage = _legacy_stage(
                row.get("number"),
                str(row.get("title") or "").strip(),
                str(row.get("concept") or "").strip(),
                str(row.get("source") or "").strip(),
                str(row.get("anchor") or "").strip(),
                str(row.get("practice") or "").strip(),
            )
        else:
            continue
        number = stage["number"]
        if not isinstance(number, int) or number < 1 or number in seen or not stage["title"]:
            raise JobDashboardError(
                f"learning plan {track_id} has an invalid or duplicate stage"
            )
        seen.add(number)
        stages.append(stage)
    stages.sort(key=lambda row: row["number"])
    recorded = progress.get(track_id) or {}
    completed = sorted(
        number for number in (recorded.get("completed_sessions") or [])
        if isinstance(number, int) and number in seen
    )
    for stage in stages:
        stage["done"] = stage["number"] in completed
    return {
        "id": track_id,
        "title": title,
        "status": str(data.get("status") or "ready"),
        "cadence": str(data.get("cadence") or ""),
        "horizon": str(data.get("horizon") or "now"),
        "outcome": str(data.get("outcome") or "").strip(),
        "stages": stages,
        "completed_sessions": completed,
        "last_session_at": str(recorded.get("last_session_at") or ""),
        "path": path.relative_to(job_root).as_posix(),
        "source_kind": "structured",
        "revision": artifact_revision(job_root, f"job-plan:{track_id}"),
    }


def _learning_tracks(
    config: dict,
    job_root: Path,
    progress: dict,
    repository_root: Path,
) -> list[dict]:
    """Merge legacy declared plans with structured, editable Job plans.

    A structured plan with the same id deliberately shadows its legacy
    Markdown predecessor. This adds an editable path without re-serialising or
    deleting the learner's original document.
    """
    tracks = {
        track["id"]: track
        for entry in (config.get("learning_tracks") or [])
        if isinstance(entry, dict)
        for track in [_track(entry, job_root, progress)]
    }
    plans_root = job_root / "plans"
    if plans_root.is_dir():
        for path in sorted(plans_root.glob("*.yaml")):
            track = _structured_track(path, job_root, progress, repository_root)
            tracks[track["id"]] = track
    return sorted(
        tracks.values(),
        key=lambda row: ({"now": 0, "next": 1, "later": 2}.get(row["horizon"], 3), row["title"]),
    )


def _tasks(job_root: Path) -> list[dict]:
    path = job_root / "operations" / "tasks.yaml"
    if not path.is_file():
        return []
    data = _read_yaml(path)
    if data.get("type") != "job-task-list" or data.get("schema_version") != 1:
        raise JobDashboardError("unsupported Job task-list contract")
    output = []
    for row in data.get("tasks") or []:
        if not isinstance(row, dict):
            continue
        task_id = str(row.get("id") or "").strip()
        title = str(row.get("title") or "").strip()
        if not task_id or not title:
            continue
        output.append({
            "id": task_id,
            "title": title,
            "details": str(row.get("details") or "").strip(),
            "horizon": str(row.get("horizon") or "now"),
            "status": str(row.get("status") or "open"),
            "track_id": str(row.get("track_id") or "").strip(),
            "created_at": str(row.get("created_at") or ""),
            "updated_at": str(row.get("updated_at") or ""),
            "revision": artifact_revision(job_root, f"job-task:{task_id}"),
        })
    return sorted(
        output,
        key=lambda row: (
            row["status"] == "done",
            {"now": 0, "next": 1, "later": 2}.get(row["horizon"], 3),
            row["title"],
        ),
    )


def _paper(entry: dict, job_root: Path) -> dict:
    path = _safe_job_path(job_root, entry.get("path"))
    return {
        "id": str(entry.get("id") or path.stem),
        "title": str(entry.get("title") or path.stem),
        "authors": [str(value) for value in (entry.get("authors") or [])],
        "year": entry.get("year"),
        "pages": entry.get("pages"),
        "horizon": str(entry.get("horizon") or "later"),
        "angle": str(entry.get("angle") or "").strip(),
        "path": path.relative_to(job_root).as_posix(),
        "available": path.is_file(),
    }


def _shelf(entries: list, repository_root: Path) -> list[dict]:
    manifest = _fresh_manifest(repository_root)
    sources = {
        str(record.get("id")): record for record in manifest.get("records", [])
        if isinstance(record, dict)
        and record.get("type") == "source"
        and record.get("id")
    }
    output = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        source_id = str(entry.get("source_id") or "")
        source = sources.get(source_id)
        if source is None:
            raise JobDashboardError(f"canonical shelf source is missing: {source_id}")
        output.append({
            "source_id": source_id,
            "title": str(source.get("title") or source_id),
            "type": str(source.get("type") or "source"),
            "authors": [str(value) for value in (source.get("authors") or [])],
            "horizon": str(entry.get("horizon") or "later"),
            "why": str(entry.get("why") or "").strip(),
        })
    return output


def cmd_job_dashboard(args) -> int:
    if not args.confirm_job_access:
        print(json.dumps({
            "ok": False,
            "error": "Job access requires the explicit --confirm-job-access gesture.",
        }))
        return 2
    repository_root = _root(args)
    job_root = _job_root(repository_root)
    dashboard_path = job_root / "dashboard.yaml"
    if not dashboard_path.is_file():
        print(json.dumps({
            "ok": False,
            "error": "The quarantined Job dashboard is unavailable.",
        }))
        return 2
    try:
        config = _read_yaml(dashboard_path)
        if config.get("type") != "job-dashboard" or config.get("schema_version") != 1:
            raise JobDashboardError("unsupported Job dashboard contract")
        workspace_config = config.get("workspace") or {}
        if not isinstance(workspace_config, dict):
            raise JobDashboardError("Job dashboard workspace must be an object")
        workspace_path = _safe_job_path(job_root, workspace_config.get("path"))
        note_config = config.get("notes") or {}
        if not isinstance(note_config, dict):
            raise JobDashboardError("Job dashboard notes must be an object")
        progress = _progress(job_root)
        tracks = _learning_tracks(config, job_root, progress, repository_root)
        papers = [
            _paper(entry, job_root) for entry in (config.get("papers") or [])
            if isinstance(entry, dict)
        ]
        notes = _notes(note_config, job_root)
        tasks = _tasks(job_root)
        shelf = _shelf(config.get("canonical_shelf") or [], repository_root)
        dashboard = {
            "id": str(config.get("id") or "job-dashboard"),
            "title": str(config.get("title") or "Job"),
            "subtitle": str(config.get("subtitle") or "Confidential workspace"),
            "workspace": _workspace(workspace_config, workspace_path, job_root),
            "notes": notes,
            "learning_tracks": tracks,
            "tasks": tasks,
            "papers": papers,
            "canonical_shelf": shelf,
            "counts": {
                "notes": len(notes["learning"]) + len(notes["skrub"]) + len(notes["stratum"]),
                "learning_notes": len(notes["learning"]),
                "skrub_notes": len(notes["skrub"]),
                "system_notes": len(notes["stratum"]),
                "learning_tracks": len(tracks),
                "learning_stages": sum(len(track["stages"]) for track in tracks),
                "open_tasks": sum(task["status"] != "done" for task in tasks),
                "completed_tasks": sum(task["status"] == "done" for task in tasks),
                "papers": len(papers),
                "canonical_sources": len(shelf),
            },
        }
    except (JobDashboardError, OSError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    response = {
        "ok": True,
        "contract": CONTRACT,
        "access": {
            "scope": "job-dashboard",
            "read_only": True,
            "ephemeral": True,
            "excluded_from_manifest": True,
            "excluded_from_search": True,
            "excluded_from_ai": True,
            "writes_through_gateway": True,
            "stratum": dict(STRATUM_ACCESS),
            "allowed_roots": sorted(ALLOWED_TOP_LEVELS),
            "snapshot_id": f"sha256:{job_fingerprint(job_root)}",
        },
        "dashboard": dashboard,
    }
    try:
        validate_contract(
            repository_root,
            "job-dashboard.schema.json",
            response,
            label=CONTRACT,
        )
    except ContractValidationError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(response, indent=2, sort_keys=True, ensure_ascii=False))
    return 0
