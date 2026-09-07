"""Record projection for curriculum/: programs, modules, units, study maps, source maps."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from ...loader import Repo
from ...pathing import PathBoundaryError, read_text_inside, resolved_inside
from ...routes import (
    exact_selection_matches,
    iter_route_references,
    route_with_identity,
)
from ...unit_notes import unit_note_sections as parse_unit_note_sections
from ..common import _first_para, _git_last_commit
from ..materials import _project_material_resource
from .grouping import ordered_thematic_group_ids
from .lifecycle import module_lifecycle
from .stages import project_stages

Revision = Callable[..., int]



def unit_note_sections(text: str) -> list[dict]:
    """Project session sections so interfaces never parse unit-note Markdown."""
    return [
        {**section, "summary": _first_para(section["text"])[:400]}
        for section in parse_unit_note_sections(text)
    ]


def project_programs(repo: Repo, revision: Revision) -> list[dict]:
    """Project only programs that belong to ordinary LearningOS navigation.

    Quarantined and boundary-only programs are deliberate open gestures, not
    current study records.  Their dedicated diagnostics/planning surfaces own
    that metadata; publishing even the boundary row here would leak it into
    normal manifests, search, counts, and ordinary AI context.
    """
    return [
        {
            **dict(program.data),
            "revision": revision(program.id, program.data),
            "path": str(program.path.relative_to(repo.root)),
        }
        for program in sorted(repo.programs.values(), key=lambda p: p.id)
        if program.data.get("status") not in {"quarantined", "boundary-only"}
        and program.data.get("kind") not in {"quarantine", "boundary"}
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


# A module whose units are still being studied. A dropped or archived module
# keeps its records as history and is never asked for new plans.
_STUDIED_MODULE_STATUSES = frozenset({"active", "enrolled"})

# A unit that is finished, paused/inactive, or explicitly set aside is not owed
# a plan either.  `ready-to-shelve` is operationally inactive: asking it to
# acquire a new study map while it is leaving active study would reverse the
# user's lifecycle decision.
_UNIT_STATUSES_WITHOUT_OBLIGATION = frozenset({
    "complete", "archived", "paused", "ready-to-shelve",
})


def _needs_study_map(unit_data: dict, module_status: str | None,
                     has_study_map: bool) -> bool:
    """Whether this unit still owes an ordered study map.

    Derived, not declared. `status: needs-map` was the only signal before, and
    an authored label is a claim someone has to remember to set: 26 lecture
    units across two enrolled modules had no map and none of them carried it,
    so every count and badge downstream read zero while the Review queue —
    which had always filtered on the map itself — listed all of them. One
    derivation ends that disagreement.
    """
    if has_study_map:
        return False
    if module_status not in _STUDIED_MODULE_STATUSES:
        return False
    return unit_data.get("status") not in _UNIT_STATUSES_WITHOUT_OBLIGATION


def project_units(repo: Repo, revision: Revision,
                  unit_to_projects: dict[str, list[str]]) -> list[dict]:
    records = []
    route_refs = list(iter_route_references(repo))
    module_status = {
        mid: (module.data if hasattr(module, "data") else module).get("status")
        for mid, module in repo.modules.items()
    }
    mapped_units = {
        study_map.unit_id for study_map in repo.study_maps.values()
    }
    for unit in sorted(repo.units.values(), key=lambda u: u.id):
        data = unit.data
        projected_selections = []
        for selection in data.get("source_selections", []) or []:
            if not isinstance(selection, dict) or selection.get("route_id"):
                projected_selections.append(selection)
                continue
            matches = exact_selection_matches(
                route_refs,
                unit_id=unit.id,
                selection=selection,
            )
            projected_selections.append(
                {**selection, "route_id": matches[0].route_id}
                if len(matches) == 1 else selection
            )
        note_ref = data.get("working_note")
        note_file: Path | None = repo.root / str(note_ref) if note_ref else None
        try:
            if note_file is not None:
                resolved_inside(repo.root, note_file)
                note_text = read_text_inside(
                    repo.root, note_file, errors="replace"
                )
            else:
                note_text = ""
        except (OSError, PathBoundaryError):
            note_file = None
            note_text = ""
        records.append({
            **dict(data),
            "source_selections": projected_selections,
            "revision": revision(unit.id, data),
            "path": str(unit.path.relative_to(repo.root)),
            # Projects own units explicitly in the Project record. The legacy
            # module_id remains for compatibility until Gate F, while interfaces
            # receive the first-class ownership edge directly from the core.
            "project_ids": unit_to_projects.get(unit.id, []),
            # The producer answers the obligation once so the count, the badge
            # and the Review queue cannot disagree about it.
            "needs_study_map": _needs_study_map(
                data,
                module_status.get(str(data.get("module_id") or "")),
                unit.id in mapped_units,
            ),
            "notes_text": note_text,
            "note_sections": unit_note_sections(note_text),
            "notes_updated": _git_last_commit(
                repo.root, note_file.relative_to(repo.root).as_posix())
                if note_file else None,
        })
    return records


def project_study_maps(repo: Repo, revision: Revision,
                       source_maps: list[dict] | None = None) -> list[dict]:
    # Resolve routes once in their owning source map and reuse the results.
    # Pair with the owner's keys rather than trusting a malformed module_id.
    if source_maps is None:
        source_maps = project_module_source_maps(repo, revision)
    routes_by_unit: dict[tuple[str, str], list[dict]] = {}
    for mid, source_map in zip(sorted(repo.module_source_maps), source_maps, strict=True):
        for entry in source_map.get("sources", []) or []:
            if not isinstance(entry, dict):
                continue
            for route in entry.get("unit_routes", []) or []:
                if isinstance(route, dict) and isinstance(route.get("unit_id"), str):
                    routes_by_unit.setdefault((mid, route["unit_id"]), []).append(route)
    records = []
    for study_map in sorted(repo.study_maps.values(), key=lambda sm: sm.id):
        data = study_map.data
        records.append({
            **{k: v for k, v in data.items() if k != "stages"},
            "revision": revision(study_map.id, data),
            "module_id": study_map.module_id,
            "path": str(study_map.path.relative_to(repo.root)),
            "stages": project_stages(
                repo,
                data,
                "working_note",
                routes_by_unit.get((study_map.module_id, study_map.unit_id), ()),
            ),
        })
    return records


def project_unit_material_syntheses(repo: Repo) -> list[dict]:
    """Retain approved evidence and derive its current projection status.

    The already-loaded repository and one per-build material-hash memo are
    passed into both derivations. Each dossier previously triggered two more
    full repository loads and rehashed every route's file, including the routes
    sharing one deck (2026-09-05 audit, F13).
    """

    # Local import avoids a package-initialization cycle: the synthesis module
    # is a domain service and this is a projection of its output.
    from ...material_synthesis import (
        material_synthesis_completeness,
        material_synthesis_freshness,
    )

    cache: dict = {}
    return [
        {
            **dict(repo.unit_material_syntheses[synthesis_id]),
            "freshness": material_synthesis_freshness(
                repo.root,
                str(repo.unit_material_syntheses[synthesis_id].get("unit_id", "")),
                repo.unit_material_syntheses[synthesis_id],
                repo=repo,
                cache=cache,
            ),
            "completeness": material_synthesis_completeness(
                repo.root,
                str(repo.unit_material_syntheses[synthesis_id].get("unit_id", "")),
                repo.unit_material_syntheses[synthesis_id],
                repo=repo,
            ),
        }
        for synthesis_id in sorted(repo.unit_material_syntheses)
    ]


def project_module_source_maps(repo: Repo, revision: Revision) -> list[dict]:
    records = []
    for mid in sorted(repo.module_source_maps):
        source_map = repo.module_source_maps[mid]
        source_map_id = f"source-map-{mid.removeprefix('module-')}"
        projected_sources = []
        for entry in source_map.get("sources", []) or []:
            if not isinstance(entry, dict):
                projected_sources.append(entry)
                continue
            projected_entry = dict(entry)
            projected_entry["unit_routes"] = [
                _project_material_resource(
                    repo,
                    {
                        **route_with_identity(
                            mid,
                            str(entry.get("source_id") or ""),
                            route,
                        ),
                        "source_id": entry.get("source_id"),
                    },
                )
                if isinstance(route, dict)
                else route
                for route in entry.get("unit_routes", []) or []
            ]
            projected_sources.append(projected_entry)
        records.append({
            "id": source_map_id,
            **{k: v for k, v in source_map.items() if k != "sources"},
            "sources": projected_sources,
            "revision": revision(source_map_id, source_map),
            "path": str(repo.module_source_map_origins[mid].relative_to(repo.root)),
        })
    return records
