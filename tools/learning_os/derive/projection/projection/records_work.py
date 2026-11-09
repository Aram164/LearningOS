"""Record projection for work/: workspaces, learning paths, coordination."""

from __future__ import annotations

from collections.abc import Callable

from learning_os.derive.projection.common import excerpt as _excerpt
from learning_os.derive.projection.common import first_para as _first_para
from learning_os.derive.projection.projection.stages import project_stages
from learning_os.domain.snapshot import Repo

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
            # Parsed HERE so no interface ever regexes CONTEXT.md again. Bounded
            # with an explicit marker, never silently: the authored paragraph in
            # CONTEXT.md stays the complete canonical text, and `inspect` reads
            # it whole; this projection carries a marked excerpt for display.
            "objective": _excerpt(_first_para(ws.section("Objective")), 1200),
            "next_action": _excerpt(_first_para(ws.section("Next Action")), 1200),
            "concepts": sorted(ws.meta.get("concepts", []) or []),
            "notes": sorted(ws.meta.get("notes", []) or []),
            "sources": sorted(ws.meta.get("sources", []) or []),
            "program_ids": sorted(ws.meta.get("program_ids", []) or []),
            "module_ids": sorted(ws.meta.get("module_ids", []) or []),
            "unit_ids": sorted(ws.meta.get("unit_ids", []) or []),
            "project_id": ws.meta.get("project_id"),
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
