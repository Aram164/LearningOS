"""Explicit, read-only access to the quarantined Job dashboard.

The ordinary loader, projection, search, validation, and AI surfaces never call
this module.  It is reached only through ``los job-dashboard
--confirm-job-access`` after the learner deliberately opens the Job view.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import yaml

from .support import _fresh_manifest, _root


CONTRACT = "job-dashboard-v1"
ALLOWED_TOP_LEVELS = {
    "notes", "workspace-job-deem", "papers", "legacy-plans",
}


class JobDashboardError(ValueError):
    """The bounded Job catalogue cannot be read safely."""


def _job_root(repository_root: Path) -> Path:
    # <semestercontext>/LearningOS/repository -> <semestercontext>/Job
    return repository_root.parent.parent / "Job"


def _safe_job_path(job_root: Path, value: object) -> Path:
    relative = str(value or "").strip().replace("\\", "/")
    if not relative or relative.startswith("/"):
        raise JobDashboardError("Job dashboard paths must be non-empty relative paths")
    candidate = (job_root / relative).resolve()
    try:
        resolved_relative = candidate.relative_to(job_root.resolve())
    except ValueError as exc:
        raise JobDashboardError(f"Job dashboard path escapes the quarantine: {relative}") from exc
    if not resolved_relative.parts or resolved_relative.parts[0] not in ALLOWED_TOP_LEVELS:
        raise JobDashboardError(f"Job dashboard path is outside the read allowlist: {relative}")
    return candidate


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


def _workspace(path: Path, job_root: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    meta, body = _frontmatter(text)
    current_raw = _section(body, "Current Scope")
    scope: list[dict] = []
    labels = "Required now|Helpful now|Defer|Reference only"
    for match in re.finditer(
        rf"\*({labels})\*\s*[—-]\s*(.*?)(?=\n\s*\n\*?(?:{labels})\*?\s*[—-]|\Z)",
        current_raw,
        flags=re.DOTALL,
    ):
        scope.append({
            "label": match.group(1).lower().replace(" ", "-"),
            "text": _plain(match.group(2)),
        })
    open_raw = _section(body, "Open Questions")
    open_questions = [
        _plain(match.group(1)) for match in re.finditer(
            r"^-\s+(.*?)(?=^-\s+|\Z)",
            open_raw,
            flags=re.MULTILINE | re.DOTALL,
        )
        if _plain(match.group(1))
    ]
    return {
        "id": str(meta.get("id") or "workspace-job-deem"),
        "title": str(meta.get("title") or "BIFOLD/DEEM job — Stratum"),
        "status": str(meta.get("status") or "active"),
        "standing": bool(meta.get("standing", True)),
        "objective": _first_paragraph(_section(body, "Objective")),
        "current_scope": scope,
        "next_action": _first_paragraph(_section(body, "Next Action")),
        "open_questions": open_questions,
        "path": path.relative_to(job_root).as_posix(),
    }


def _note_summary(body: str) -> str:
    heading = re.search(r"^#\s+.+$", body, flags=re.MULTILINE)
    tail = body[heading.end():] if heading else body
    quote = re.search(r"(?:^>.*(?:\n>.*)*)", tail, flags=re.MULTILINE)
    if quote:
        return _plain(quote.group(0))
    return _first_paragraph(tail)


def _git_changed(repo: Path, revision: str, component: str) -> bool | None:
    if not revision or not component:
        return None
    try:
        result = subprocess.run(
            ["git", "diff", "--quiet", revision, "--", component],
            cwd=repo,
            capture_output=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode == 0:
        return False
    if result.returncode == 1:
        return True
    return None


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
    kind = "stratum" if relative.startswith("notes/stratum/") else "skrub"
    verified = str(meta.get("verified_against") or "").strip()
    revision = verified.split()[0] if verified else ""
    component = str(meta.get("component") or "").strip()
    declared = str(meta.get("status") or meta.get("state") or "reference").strip()
    changed = _git_changed(job_root / "stratum", revision, component) if kind == "stratum" else None
    if declared == "stale":
        freshness = "stale"
    elif changed is True:
        freshness = "drifting"
    elif changed is False:
        freshness = "current"
    else:
        freshness = declared
    concepts = [str(item) for item in (meta.get("concepts") or []) if str(item).strip()]
    family = next((item.removesuffix("-family") for item in concepts if item.endswith("-family")), "")
    return {
        "id": note_id,
        "title": title,
        "kind": kind,
        "family": family,
        "summary": _note_summary(body),
        "path": relative,
        "component": component,
        "layer": _layer_for(component, kind),
        "verified_against": verified,
        "declared_status": declared,
        "freshness": freshness,
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
    return {"skrub": skrub, "stratum": stratum, "health": health, "layers": layers}


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


def _track(entry: dict, job_root: Path, progress: dict | None = None) -> dict:
    path = _safe_job_path(job_root, entry.get("path"))
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise JobDashboardError(f"cannot read learning track {path.name}: {exc}") from exc
    sessions: list[dict] = []
    matches = list(re.finditer(r"^###\s+Session\s+(\d+)\s+[—-]\s+(.+?)\s*$", text, flags=re.MULTILINE))
    for index, match in enumerate(matches):
        block = text[match.end():matches[index + 1].start() if index + 1 < len(matches) else len(text)]
        sessions.append({
            "number": int(match.group(1)),
            "title": _plain(match.group(2)),
            "concept": _field(block, "Concept"),
            "source": _field(block, "Source"),
            "anchor": _field(block, "Stratum anchor"),
            "practice": _field(block, "Rebuild/stretch"),
        })
    outcome = _first_paragraph(_section(text, 'Definition of "there"'))
    track_id = str(entry.get("id") or path.stem)
    recorded = (progress or {}).get(track_id) or {}
    completed = [
        number for number in (recorded.get("completed_sessions") or [])
        if isinstance(number, int)
    ]
    for session in sessions:
        session["done"] = session["number"] in completed
    return {
        "id": track_id,
        "title": str(entry.get("title") or path.stem),
        "status": str(entry.get("status") or "ready"),
        "cadence": str(entry.get("cadence") or ""),
        "horizon": str(entry.get("horizon") or "now"),
        "outcome": outcome,
        "sessions": sessions,
        "completed_sessions": sorted(completed),
        "last_session_at": str(recorded.get("last_session_at") or ""),
        "path": path.relative_to(job_root).as_posix(),
    }


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
        workspace_path = _safe_job_path(job_root, workspace_config.get("path"))
        note_config = config.get("notes") or {}
        progress = _progress(job_root)
        tracks = [
            _track(entry, job_root, progress)
            for entry in (config.get("learning_tracks") or [])
            if isinstance(entry, dict)
        ]
        papers = [
            _paper(entry, job_root) for entry in (config.get("papers") or [])
            if isinstance(entry, dict)
        ]
        notes = _notes(note_config, job_root)
        shelf = _shelf(config.get("canonical_shelf") or [], repository_root)
        dashboard = {
            "id": str(config.get("id") or "job-dashboard"),
            "title": str(config.get("title") or "Job"),
            "subtitle": str(config.get("subtitle") or "Confidential workspace"),
            "workspace": _workspace(workspace_path, job_root),
            "notes": notes,
            "learning_tracks": tracks,
            "papers": papers,
            "canonical_shelf": shelf,
            "counts": {
                "notes": len(notes["skrub"]) + len(notes["stratum"]),
                "skrub_notes": len(notes["skrub"]),
                "system_notes": len(notes["stratum"]),
                "learning_sessions": sum(len(track["sessions"]) for track in tracks),
                "papers": len(papers),
                "canonical_sources": len(shelf),
            },
        }
    except (JobDashboardError, OSError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({
        "ok": True,
        "contract": CONTRACT,
        "access": {
            "scope": "job-dashboard",
            "read_only": True,
            "ephemeral": True,
            "excluded_from_manifest": True,
            "excluded_from_search": True,
            "excluded_from_ai": True,
        },
        "dashboard": dashboard,
    }, indent=2, sort_keys=True, ensure_ascii=False))
    return 0
