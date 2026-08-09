"""Record projection for work/: workspaces, learning paths, coordination."""

from __future__ import annotations

from typing import Callable

from ...loader import Repo
from ..common import _first_para
from .stages import project_stages

Revision = Callable[..., int]


def project_workspaces(repo: Repo, revision: Revision) -> list[dict]:
    records = []
    for ws in sorted(repo.workspaces.values(), key=lambda w: w.id):
        records.append({
            "id": ws.id, "type": "workspace", "title": ws.meta.get("title", ""),
            "revision": revision(ws.id, ws.meta),
            "path": str(ws.path.relative_to(repo.root)),
            "status": ws.status, "standing": ws.standing, "archived": ws.archived,
            "deadline": ws.meta.get("deadline"),
            # interface fields: the two sections every surface wants to show.
            # Parsed HERE so no interface ever regexes CONTEXT.md again.
            "objective": _first_para(ws.section("Objective"))[:400],
            "next_action": _first_para(ws.section("Next Action"))[:400],
            "concepts": sorted(ws.meta.get("concepts", []) or []),
            "notes": sorted(ws.meta.get("notes", []) or []),
            "sources": sorted(ws.meta.get("sources", []) or []),
            "program_ids": sorted(ws.meta.get("program_ids", []) or []),
            "module_ids": sorted(ws.meta.get("module_ids", []) or []),
            "unit_ids": sorted(ws.meta.get("unit_ids", []) or []),
            "project_id": ws.meta.get("project_id"),
        })
    return records


def project_learning_paths(repo: Repo, revision: Revision) -> list[dict]:
    records = []
    for learning_path in sorted(repo.learning_paths.values(), key=lambda p: p.id):
        data = learning_path.data
        records.append({
            "id": learning_path.id, "type": "learning-path",
            "revision": revision(learning_path.id, data),
            "title": data.get("title", ""),
            "path": str(learning_path.path.relative_to(repo.root)),
            "workspace_id": learning_path.workspace_id,
            "area": data.get("area", "university"),
            "module_id": data.get("module_id"),
            "status": data.get("status", ""),
            "current_stage": data.get("current_stage", ""),
            "created": data.get("created"), "updated": data.get("updated"),
            "objective": data.get("objective", ""),
            "source_plan": data.get("source_plan"),
            "stages": project_stages(repo, data, "notes_path"),
            "shelving": dict(data.get("shelving", {}) or {}),
            "archived": learning_path.archived,
        })
    return records


def project_coordination(repo: Repo) -> list[dict]:
    if repo.coordination is None:
        return []
    return [{
        "id": "coordination", "type": "coordination",
        "path": "work/COORDINATION.md",
        "sections": {h: (repo.coordination.section(h) or "")
                     for h in ("Commitments", "Priorities", "Dependencies", "Deferrals")},
    }]
