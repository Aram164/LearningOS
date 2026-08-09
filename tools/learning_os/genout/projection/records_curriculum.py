"""Record projection for curriculum/: programs, modules, units, study maps, source maps."""

from __future__ import annotations

import json
import re
from typing import Callable

from ...loader import Repo
from ..common import _first_para, _git_last_commit
from .grouping import ordered_thematic_group_ids
from .lifecycle import module_lifecycle
from .stages import project_stages

Revision = Callable[..., int]

_UNIT_NOTE_MARKER = re.compile(r"^<!-- learningos:unit-note (\{.*\}) -->\s*$", re.MULTILINE)


def unit_note_sections(text: str) -> list[dict]:
    """Project session sections so interfaces never parse unit-note Markdown."""
    matches = list(_UNIT_NOTE_MARKER.finditer(text or ""))
    sections: list[dict] = []
    for index, match in enumerate(matches):
        try:
            metadata = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end():end].strip()
        heading = ""
        lines = body.splitlines()
        if lines and lines[0].startswith("## "):
            heading = lines[0][3:].strip()
            body = "\n".join(lines[1:]).strip()
        sections.append({
            "recorded_at": metadata.get("recorded_at"),
            "title": metadata.get("title") or heading or "Learning session note",
            "stage_ids": list(metadata.get("stage_ids") or []),
            "attachments": list(metadata.get("attachments") or []),
            "text": body,
            "summary": _first_para(body)[:400],
        })
    return sections


def project_programs(repo: Repo, revision: Revision) -> list[dict]:
    return [
        {
            **dict(program.data),
            "revision": revision(program.id, program.data),
            "path": str(program.path.relative_to(repo.root)),
        }
        for program in sorted(repo.programs.values(), key=lambda p: p.id)
    ]


def project_modules(repo: Repo, revision: Revision) -> list[dict]:
    records = []
    for mid in sorted(repo.modules):
        m = repo.modules[mid]
        if m.get("compatibility_only"):
            continue
        origin = repo.module_origins.get(mid)
        records.append({
            "id": mid, "type": "module", "title": m.get("title", ""),
            "revision": revision(mid, m),
            "path": str(origin.relative_to(repo.root)) if origin else "records/modules.yaml",
            "kind": m.get("kind", "academic"), "area_id": m.get("area_id"),
            "thematic_group_ids": ordered_thematic_group_ids(
                repo, m.get("thematic_group_ids", []) or []),
            "status": m.get("status", ""),
            # `status` stays exactly as authored for anything that needs the raw
            # field; the three derived keys below are what interfaces should read.
            **module_lifecycle(m, [
                str(unit.data.get("status", ""))
                for unit in repo.units.values() if unit.module_id == mid
            ]),
            "institution": m.get("institution"), "code": m.get("code"),
            "credits": m.get("credits"), "semester": m.get("semester"),
            "components": list(m.get("components", []) or []),
            "examination": m.get("examination"),
            "attempts": list(m.get("attempts", []) or []),
            "grade": m.get("grade"),
            "unit_order": list(m.get("unit_order", []) or []),
            "source_map": m.get("source_map"),
        })
    return records


def project_units(repo: Repo, revision: Revision,
                  unit_to_projects: dict[str, list[str]]) -> list[dict]:
    records = []
    for unit in sorted(repo.units.values(), key=lambda u: u.id):
        data = unit.data
        note_ref = data.get("working_note")
        note_file = repo.root / str(note_ref) if note_ref else None
        note_text = note_file.read_text(encoding="utf-8", errors="replace") \
            if note_file and note_file.is_file() else ""
        records.append({
            **dict(data),
            "revision": revision(unit.id, data),
            "path": str(unit.path.relative_to(repo.root)),
            # Projects own units explicitly in the Project record. The legacy
            # module_id remains for compatibility until Gate F, while interfaces
            # receive the first-class ownership edge directly from the core.
            "project_ids": unit_to_projects.get(unit.id, []),
            "notes_text": note_text,
            "note_sections": unit_note_sections(note_text),
            "notes_updated": _git_last_commit(
                repo.root, note_file.relative_to(repo.root).as_posix())
                if note_file and note_file.is_file() else None,
        })
    return records


def project_study_maps(repo: Repo, revision: Revision) -> list[dict]:
    records = []
    for study_map in sorted(repo.study_maps.values(), key=lambda sm: sm.id):
        data = study_map.data
        records.append({
            **{k: v for k, v in data.items() if k != "stages"},
            "revision": revision(study_map.id, data),
            "module_id": study_map.module_id,
            "path": str(study_map.path.relative_to(repo.root)),
            "stages": project_stages(repo, data, "working_note"),
        })
    return records


def project_module_source_maps(repo: Repo, revision: Revision) -> list[dict]:
    records = []
    for mid in sorted(repo.module_source_maps):
        source_map = repo.module_source_maps[mid]
        source_map_id = f"source-map-{mid.removeprefix('module-')}"
        records.append({
            "id": source_map_id,
            **dict(source_map),
            "revision": revision(source_map_id, source_map),
            "path": str(repo.module_source_map_origins[mid].relative_to(repo.root)),
        })
    return records
