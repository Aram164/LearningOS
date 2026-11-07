"""Snapshot exporter for SQLite Reference-Validation Spike (Role A).

Consumes the memoized Repo snapshot and extracts entity tables, scoped entities,
rich routes, and reference edges into the in-memory SQLite database.

Maintains exact semantics:
- id_list_items / list_items: schema errors own malformed shapes, non-lists emit 0 rows.
- Multi-key ordinal tracking: (family_ordinal, source_ordinal, occurrence_ordinal, emission_rank).
- BINARY collation strings.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from learning_os.derive.routes import iter_route_references
from learning_os.domain.snapshot import Repo
from learning_os.domain.validation import (
    WORKSPACE_TOKEN_RE,
    id_list_items,
    list_items,
)
from learning_os.domain.vocabulary import EVIDENCE_SCHEMES


@dataclass(frozen=True)
class ParsedReference:
    scheme: str
    target: str


def parse_reference_uri(value: str) -> ParsedReference | None:
    for prefix in EVIDENCE_SCHEMES:
        if value.startswith(prefix):
            target = value[len(prefix):]
            for mark in ("#", "?") if prefix == "material://" else ("#",):
                target = target.split(mark, 1)[0]
            return ParsedReference(prefix.removesuffix("://"), target)
    return None


def _rel_path(p: Path, root: Path) -> str:
    try:
        return str(p.relative_to(root))
    except ValueError:
        return str(p)


def _origin_for(repo: Repo, family: str, rec_id: str) -> str:
    if family == "concept":
        o = repo.concept_origins.get(rec_id)
        return _rel_path(o, repo.root) if o else "knowledge/concepts.yaml"
    if family == "ability":
        o = repo.ability_origins.get(rec_id)
        return _rel_path(o, repo.root) if o else "knowledge/abilities.yaml"
    if family == "source":
        o = repo.source_origins.get(rec_id)
        return _rel_path(o, repo.root) if o else "sources/sources.yaml"
    if family == "module":
        o = repo.module_origins.get(rec_id)
        return _rel_path(o, repo.root) if o else "records/modules.yaml"
    if family == "program":
        p = repo.programs.get(rec_id)
        return _rel_path(p.path, repo.root) if p else ""
    if family == "project":
        project = repo.projects.get(rec_id)
        return _rel_path(project.path, repo.root) if project else ""
    if family == "unit":
        u = repo.units.get(rec_id)
        return _rel_path(u.path, repo.root) if u else ""
    if family == "study-map":
        sm = repo.study_maps.get(rec_id)
        return _rel_path(sm.path, repo.root) if sm else ""
    if family == "note":
        n = repo.notes.get(rec_id)
        return _rel_path(n.path, repo.root) if n else ""
    if family == "workspace":
        w = repo.workspaces.get(rec_id)
        return _rel_path(w.path, repo.root) if w else ""
    return ""


def _check_uri_internal(repo: Repo, ref: str, where: str, fam_ord: int, s_ord: int, occ: int) -> tuple | None:
    parsed = parse_reference_uri(ref)
    if parsed is None:
        return None
    if parsed.scheme == "note":
        if parsed.target not in repo.notes:
            return (fam_ord, s_ord, occ, 0, "E", "URI-NOTE", f"'{ref}' does not resolve", where)
    elif parsed.scheme == "concept":
        if parsed.target not in repo.concepts:
            return (fam_ord, s_ord, occ, 0, "E", "URI-CONCEPT", f"'{ref}' does not resolve", where)
    elif parsed.scheme == "source":
        if parsed.target not in repo.sources:
            return (fam_ord, s_ord, occ, 0, "E", "URI-SOURCE", f"'{ref}' does not resolve", where)
    elif parsed.scheme == "workspace":
        wid = parsed.target
        if wid not in repo.workspaces and wid not in repo.quarantined_workspace_ids:
            return (fam_ord, s_ord, occ, 0, "E", "URI-WORKSPACE", f"'{ref}' does not resolve", where)
    elif parsed.scheme == "material":
        if (repo.learningos_root / "materials").is_dir():
            if not (repo.materials_root / parsed.target).exists():
                return (fam_ord, s_ord, occ, 0, "W", "URI-MATERIAL", f"'{ref}' does not resolve on disk", where)
    elif parsed.scheme == "project":
        if not (repo.projects_root / parsed.target).exists():
            return (fam_ord, s_ord, occ, 0, "W", "URI-PROJECT", f"'{ref}' does not resolve on disk", where)
    return None


def export_repo_to_sqlite(repo: Repo, conn: sqlite3.Connection) -> None:
    """Export the given Repo snapshot into the SQLite validation database."""
    cur = conn.cursor()

    # 1. Populate Target Entities
    entities = []
    for cid in repo.concepts:
        entities.append(("concept", str(cid)))
    for sid in repo.sources:
        entities.append(("source", str(sid)))
    for nid in repo.notes:
        entities.append(("note", str(nid)))
    for wid in repo.workspaces:
        entities.append(("workspace", str(wid)))
    for wid in repo.quarantined_workspace_ids:
        entities.append(("workspace", str(wid)))
    for uid in repo.units:
        entities.append(("unit", str(uid)))
    for mid in repo.modules:
        entities.append(("module", str(mid)))
    for pid in repo.programs:
        entities.append(("program", str(pid)))
    for prid in repo.projects:
        entities.append(("project", str(prid)))
    for gid in repo.thematic_groups:
        entities.append(("thematic_group", str(gid)))
    for tid in repo.topics:
        entities.append(("topic", str(tid)))
    for smid in repo.study_maps:
        entities.append(("study_map", str(smid)))

    cur.executemany("INSERT OR IGNORE INTO entities (family, id) VALUES (?, ?)", entities)

    # 2. Populate Scoped Entities
    scoped_entities = []
    for mid, module in repo.modules.items():
        for comp in module.get("components", []) or []:
            if isinstance(comp, dict) and comp.get("id"):
                scoped_entities.append(("module", str(mid), "component", str(comp["id"])))

    for uid, unit in repo.units.items():
        kmap = unit.data.get("knowledge_map") or {}
        for node in kmap.get("nodes", []) or []:
            if isinstance(node, dict) and node.get("id"):
                scoped_entities.append(("unit", str(uid), "knowledge_node", str(node["id"])))

    for smid, sm in repo.study_maps.items():
        for stage in sm.data.get("stages", []) or []:
            if isinstance(stage, dict) and stage.get("id"):
                scoped_entities.append(("study_map", str(smid), "stage", str(stage["id"])))

    cur.executemany(
        "INSERT OR IGNORE INTO scoped_entities (scope_kind, scope_id, target_family, id) VALUES (?, ?, ?, ?)",
        scoped_entities,
    )

    # 3. Rich Routes & Solution Exposures
    route_rows = []
    exposure_rows = []
    route_refs = list(iter_route_references(repo))
    for s_ord, rref in enumerate(route_refs):
        where = _rel_path(repo.module_source_map_origins.get(rref.module_id, Path("curriculum/modules")), repo.root)
        route_rows.append((
            str(rref.route_id),
            str(rref.module_id),
            str(rref.unit_id),
            str(rref.source_id),
            str(rref.locator) if rref.locator is not None else None,
            1 if rref.authored_id else 0,
            s_ord,
            where,
        ))

    cur.executemany(
        "INSERT INTO rich_routes (route_id, module_id, unit_id, source_id, locator, authored_id, source_ordinal, origin_path) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        route_rows,
    )

    # Build routes_by_id for solution exposure checks
    routes_by_id: dict[str, list] = {}
    for rref in route_refs:
        routes_by_id.setdefault(str(rref.route_id), []).append(rref)

    for s_ord, (route_id, matches) in enumerate(sorted(routes_by_id.items())):
        for match in matches:
            declared = match.route.get("exposes_solutions_for")
            if declared is None:
                continue
            where = _rel_path(repo.module_source_map_origins.get(match.module_id, Path("curriculum/modules")), repo.root)
            for o_ord, answered in enumerate(declared):
                exposure_rows.append((
                    str(route_id),
                    str(answered),
                    where,
                    s_ord,
                    o_ord,
                ))

    cur.executemany(
        "INSERT INTO route_solution_exposures (route_id, answered_id, origin_path, source_ordinal, occurrence_ordinal) VALUES (?, ?, ?, ?, ?)",
        exposure_rows,
    )

    # 4. Reference Edges & Family Extractions
    ref_edges = []
    route_ref_rows = []
    synthesis_assessment_concept_rows = []
    legacy_selection_rows = []
    structural_violations = []

    # Family 2: Unit Material Syntheses
    for s_ord, (synthesis_id, synthesis) in enumerate(repo.unit_material_syntheses.items()):
        where = _rel_path(repo.unit_material_synthesis_origins.get(synthesis_id, Path("curriculum")), repo.root)
        synthesis_unit = synthesis.get("unit_id")
        # synthesis unit membership
        ref_edges.append((
            2, s_ord, 0, 0,
            "unit_material_synthesis", str(synthesis_id),
            "unit", str(synthesis_unit),
            where, None, None, None,
            "E", "REF-UNIT",
            f"material synthesis '{synthesis_id}' references unknown unit '{synthesis_unit}'",
        ))

        # route assessments
        for o_ord, assessment in enumerate(synthesis.get("route_assessments", []) or []):
            if not isinstance(assessment, dict):
                continue
            route_id = assessment.get("route_id")
            route_ref_rows.append((
                "synthesis", str(synthesis_id), str(route_id),
                str(synthesis_unit),
                assessment.get("source_id"),
                assessment.get("locator"),
                where,
                2, s_ord, 100 + o_ord,
            ))
            for c_ord, concept_id in enumerate(id_list_items(assessment.get("concept_ids"))):
                synthesis_assessment_concept_rows.append((
                    str(synthesis_id), str(route_id), str(concept_id),
                    where, 2, s_ord, 100 + o_ord, 4 + c_ord,
                ))

        # concept groups
        for o_ord, group in enumerate(synthesis.get("concept_groups", []) or []):
            if not isinstance(group, dict):
                continue
            concept_id = group.get("concept_id")
            ref_edges.append((
                2, s_ord, 200 + o_ord, 0,
                "unit_material_synthesis", str(synthesis_id),
                "concept", str(concept_id),
                where, None, None, None,
                "E", "REF-CONCEPT",
                f"material synthesis '{synthesis_id}' references unknown concept '{concept_id}'",
            ))
            for u_ord, related_unit_id in enumerate(id_list_items(group.get("related_unit_ids"))):
                ref_edges.append((
                    2, s_ord, 200 + o_ord, 1 + u_ord,
                    "unit_material_synthesis", str(synthesis_id),
                    "unit", str(related_unit_id),
                    where, None, None, None,
                    "E", "REF-UNIT",
                    f"material synthesis '{synthesis_id}' references unknown related unit '{related_unit_id}'",
                ))
            for n_ord, note_id in enumerate(id_list_items(group.get("bridge_note_ids"))):
                ref_edges.append((
                    2, s_ord, 200 + o_ord, 10 + n_ord,
                    "unit_material_synthesis", str(synthesis_id),
                    "note", str(note_id),
                    where, None, None, None,
                    "E", "REF-NOTE",
                    f"material synthesis '{synthesis_id}' references unknown bridge note '{note_id}'",
                ))

    # Family 3: Notes
    for s_ord, note in enumerate(repo.notes.values()):
        where = _rel_path(note.path, repo.root)
        occ = 0
        for cid in id_list_items(note.meta.get("concepts")):
            ref_edges.append((
                3, s_ord, occ, 0,
                "note", note.id, "concept", str(cid),
                where, None, None, None,
                "E", "REF-CONCEPT",
                f"note '{note.id}' references unknown concept '{cid}'",
            ))
            occ += 1

        for sid in id_list_items(note.meta.get("sources")):
            ref_edges.append((
                3, s_ord, occ, 0,
                "note", note.id, "source", str(sid),
                where, None, None, None,
                "E", "REF-SOURCE",
                f"note '{note.id}' references unknown source '{sid}'",
            ))
            occ += 1

        for wid in id_list_items(note.meta.get("contexts")):
            ref_edges.append((
                3, s_ord, occ, 0,
                "note", note.id, "workspace", str(wid),
                where, None, None, None,
                "E", "REF-WORKSPACE",
                f"note '{note.id}' references unknown workspace '{wid}'",
            ))
            occ += 1

        for target in id_list_items(note.meta.get("supersedes")):
            ref_edges.append((
                3, s_ord, occ, 0,
                "note", note.id, "note", str(target),
                where, None, None, None,
                "E", "REF-SUPERSEDES",
                f"note '{note.id}' supersedes unknown note '{target}'",
            ))
            occ += 1

        question = note.meta.get("atlas_question") or {}
        if isinstance(question, dict):
            for answer in id_list_items(question.get("answer_notes")):
                if answer == note.id:
                    structural_violations.append((
                        3, s_ord, occ, 0, "E", "REF-ANSWER-NOTE",
                        f"question {note.id!r} must reference an existing other answer note: {answer!r}",
                        where,
                    ))
                else:
                    ref_edges.append((
                        3, s_ord, occ, 0,
                        "note", note.id, "note", str(answer),
                        where, None, None, None,
                        "E", "REF-ANSWER-NOTE",
                        f"question {note.id!r} must reference an existing other answer note: {answer!r}",
                    ))
                occ += 1

        for ev in note.meta.get("evidence", []) or []:
            ref = str(ev.get("ref", ""))
            if not ref.startswith(EVIDENCE_SCHEMES):
                structural_violations.append((
                    3, s_ord, occ, 0, "E", "REF-EVIDENCE",
                    f"note '{note.id}' evidence ref '{ref}' uses no valid URI scheme",
                    where,
                ))
            else:
                uri_issue = _check_uri_internal(repo, ref, where, 3, s_ord, occ)
                if uri_issue:
                    structural_violations.append(uri_issue)
            occ += 1

    # Family 4: Workspaces
    for s_ord, ws in enumerate(repo.workspaces.values()):
        where = _rel_path(ws.path, repo.root)
        occ = 0
        for cid in id_list_items(ws.meta.get("concepts")):
            ref_edges.append((
                4, s_ord, occ, 0, "workspace", ws.id, "concept", str(cid),
                where, None, None, None, "E", "REF-CONCEPT",
                f"workspace '{ws.id}' references unknown concept '{cid}'",
            ))
            occ += 1
        for nid in id_list_items(ws.meta.get("notes")):
            ref_edges.append((
                4, s_ord, occ, 0, "workspace", ws.id, "note", str(nid),
                where, None, None, None, "E", "REF-NOTE",
                f"workspace '{ws.id}' references unknown note '{nid}'",
            ))
            occ += 1
        for sid in id_list_items(ws.meta.get("sources")):
            ref_edges.append((
                4, s_ord, occ, 0, "workspace", ws.id, "source", str(sid),
                where, None, None, None, "E", "REF-SOURCE",
                f"workspace '{ws.id}' references unknown source '{sid}'",
            ))
            occ += 1
        for pid in id_list_items(ws.meta.get("program_ids")):
            ref_edges.append((
                4, s_ord, occ, 0, "workspace", ws.id, "program", str(pid),
                where, None, None, None, "E", "REF-PROGRAM",
                f"workspace '{ws.id}' references unknown program '{pid}'",
            ))
            occ += 1
        for mid in id_list_items(ws.meta.get("module_ids")):
            ref_edges.append((
                4, s_ord, occ, 0, "workspace", ws.id, "module", str(mid),
                where, None, None, None, "E", "REF-MODULE",
                f"workspace '{ws.id}' references unknown module '{mid}'",
            ))
            occ += 1
        project_id = ws.meta.get("project_id")
        if project_id:
            ref_edges.append((
                4, s_ord, occ, 0, "workspace", ws.id, "project", str(project_id),
                where, None, None, None, "E", "REF-PROJECT",
                f"workspace '{ws.id}' references unknown project '{project_id}'",
            ))
            occ += 1
        for uid in id_list_items(ws.meta.get("unit_ids")):
            ref_edges.append((
                4, s_ord, occ, 0, "workspace", ws.id, "unit", str(uid),
                where, None, None, None, "E", "REF-UNIT",
                f"workspace '{ws.id}' references unknown unit '{uid}'",
            ))
            occ += 1

    # Family 5: Modules
    for s_ord, (mid, module) in enumerate(repo.modules.items()):
        where = _origin_for(repo, "module", mid)
        occ = 0
        for gid in id_list_items(module.get("thematic_group_ids")):
            ref_edges.append((
                5, s_ord, occ, 0, "module", str(mid), "thematic_group", str(gid),
                where, None, None, None, "E", "REF-THEMATIC-GROUP",
                f"module '{mid}' references unknown thematic group '{gid}'",
            ))
            occ += 1
        area_id = module.get("area_id")
        if area_id:
            ref_edges.append((
                5, s_ord, occ, 0, "module", str(mid), "program", str(area_id),
                where, None, None, None, "E", "REF-PROGRAM",
                f"module '{mid}' references unknown program '{area_id}'",
            ))
            occ += 1

        for uid in id_list_items(module.get("unit_order")):
            unit = repo.units.get(uid)
            if unit is None:
                ref_edges.append((
                    5, s_ord, occ, 0, "module", str(mid), "unit", str(uid),
                    where, None, None, None, "E", "REF-UNIT",
                    f"module '{mid}' orders unknown unit '{uid}'",
                ))
            elif unit.module_id != mid:
                structural_violations.append((
                    5, s_ord, occ, 0, "E", "UNIT-OWNER",
                    f"module '{mid}' orders unit '{uid}' owned by '{unit.module_id}'",
                    where,
                ))
            occ += 1

        source_map = repo.module_source_maps.get(mid)
        if module.get("source_map") and source_map is None:
            structural_violations.append((
                5, s_ord, occ, 0, "E", "REF-SOURCE-MAP",
                f"module '{mid}' declares a missing source map",
                where,
            ))
            occ += 1

        for related in id_list_items(module.get("related_module_ids")):
            ref_edges.append((
                5, s_ord, occ, 0, "module", str(mid), "module", str(related),
                where, None, None, None, "E", "REF-MODULE",
                f"module '{mid}' references unknown related module '{related}'",
            ))
            occ += 1

        for uid, unit in repo.units.items():
            if unit.module_id != mid:
                continue
            component_id = unit.data.get("component_id")
            if component_id:
                ref_edges.append((
                    5, s_ord, occ, 0, "unit", str(uid), "component", str(component_id),
                    _rel_path(unit.path, repo.root), "module", str(mid), None, "E", "REF-COMPONENT",
                    f"unit '{uid}' references unknown component '{component_id}' in '{mid}'",
                ))
                occ += 1

    # Family 6: Units
    for s_ord, (uid, unit) in enumerate(repo.units.items()):
        where = _rel_path(unit.path, repo.root)
        data = unit.data
        occ = 0
        if data.get("module_id") != unit.module_id:
            structural_violations.append((
                6, s_ord, occ, 0, "E", "UNIT-OWNER",
                f"unit '{uid}' declares module '{data.get('module_id')}' but lives under '{unit.module_id}'",
                where,
            ))
            occ += 1

        working_note = data.get("working_note")
        if working_note:
            target = repo.root / str(working_note)
            expected_parent = unit.path.parent.resolve()
            try:
                owned = target.resolve().is_relative_to(expected_parent)
            except OSError:
                owned = False
            if not owned:
                structural_violations.append((
                    6, s_ord, occ, 0, "E", "UNIT-NOTE-OWNER",
                    f"unit '{uid}' working note must live inside its unit directory",
                    where,
                ))
            elif not target.is_file():
                structural_violations.append((
                    6, s_ord, occ, 0, "E", "REF-UNIT-NOTE",
                    f"unit '{uid}' declares missing working note '{working_note}'",
                    where,
                ))
            occ += 1

        for scoped in data.get("scope_sources", []) or []:
            sid = scoped.get("source_id") if isinstance(scoped, dict) else None
            if sid:
                ref_edges.append((
                    6, s_ord, occ, 0, "unit", str(uid), "source", str(sid),
                    where, None, None, None, "E", "REF-SOURCE",
                    f"unit '{uid}' references unknown scope source '{sid}'",
                ))
                occ += 1

        for node in (data.get("knowledge_map") or {}).get("nodes", []) or []:
            if not isinstance(node, dict):
                continue
            for concept_id in id_list_items(node.get("concept_ids")):
                ref_edges.append((
                    6, s_ord, occ, 0, "unit", str(uid), "concept", str(concept_id),
                    where, None, None, None, "E", "REF-CONCEPT",
                    f"unit '{uid}' knowledge node '{node.get('id')}' references unknown global concept '{concept_id}'",
                ))
                occ += 1

        current_map_id = data.get("current_study_map")
        for selection in data.get("source_selections", []) or []:
            if not isinstance(selection, dict):
                continue
            sid = selection.get("source_id")
            if sid:
                ref_edges.append((
                    6, s_ord, occ, 0, "unit", str(uid), "source", str(sid),
                    where, None, None, None, "E", "REF-SOURCE",
                    f"unit '{uid}' selects unknown source '{sid}'",
                ))
            route_id = selection.get("route_id")
            if route_id:
                route_ref_rows.append((
                    "selection", str(uid), str(route_id),
                    str(uid),
                    selection.get("source_id"),
                    selection.get("locator"),
                    where,
                    6, s_ord, occ,
                ))
            else:
                legacy_selection_rows.append((
                    str(uid),
                    str(sid or ""),
                    selection.get("locator"),
                    where,
                    6, s_ord, occ,
                ))
            for stage_id in id_list_items(selection.get("stage_ids")):
                ref_edges.append((
                    6, s_ord, occ, 6, "unit", str(uid), "stage", str(stage_id),
                    where, "study_map", str(current_map_id) if current_map_id else "", None,
                    "E", "REF-STAGE",
                    f"unit '{uid}' source selection routes to unknown stage '{stage_id}'",
                ))
            occ += 1

        for nid in (data.get("artifacts") or {}).values():
            values = nid if isinstance(nid, list) else [nid]
            for value in values:
                if value:
                    ref_edges.append((
                        6, s_ord, occ, 0, "unit", str(uid), "note", str(value),
                        where, None, None, None, "E", "REF-NOTE",
                        f"unit '{uid}' references unknown artifact '{value}'",
                    ))
                    occ += 1

        workspace_ids = data.get("workspace_ids", [])
        for wid in workspace_ids if isinstance(workspace_ids, list) else []:
            if isinstance(wid, str):
                ref_edges.append((
                    6, s_ord, occ, 0, "unit", str(uid), "workspace", str(wid),
                    where, None, None, None, "E", "REF-WORKSPACE",
                    f"unit '{uid}' references unknown workspace '{wid}'",
                ))
                occ += 1

        for related in id_list_items(data.get("related_module_ids")):
            ref_edges.append((
                6, s_ord, occ, 0, "unit", str(uid), "module", str(related),
                where, None, None, None, "E", "REF-MODULE",
                f"unit '{uid}' references unknown related module '{related}'",
            ))
            occ += 1

        for related_uid in [data.get("parent_unit_id"), *id_list_items(data.get("child_unit_ids"))]:
            if related_uid:
                ref_edges.append((
                    6, s_ord, occ, 0, "unit", str(uid), "unit", str(related_uid),
                    where, None, None, None, "E", "REF-UNIT",
                    f"unit '{uid}' references unknown unit '{related_uid}'",
                ))
                occ += 1

        smid = data.get("current_study_map")
        if smid:
            sm = repo.study_maps.get(smid)
            if sm is None:
                ref_edges.append((
                    6, s_ord, occ, 0, "unit", str(uid), "study_map", str(smid),
                    where, None, None, None, "E", "REF-STUDY-MAP",
                    f"unit '{uid}' references unknown study map '{smid}'",
                ))
            elif sm.unit_id != uid:
                structural_violations.append((
                    6, s_ord, occ, 0, "E", "MAP-OWNER",
                    f"study map '{smid}' belongs to '{sm.unit_id}', not '{uid}'",
                    where,
                ))
            occ += 1

    # Family 7: Module Source Maps
    for s_ord, (mid, source_map) in enumerate(repo.module_source_maps.items()):
        where = _rel_path(repo.module_source_map_origins.get(mid, Path("curriculum/modules")), repo.root)
        occ = 0
        if source_map.get("module_id") != mid:
            structural_violations.append((
                7, s_ord, occ, 0, "E", "SOURCE-MAP-OWNER",
                f"source map declares '{source_map.get('module_id')}', lives under '{mid}'",
                where,
            ))
            occ += 1

        for entry in source_map.get("sources", []) or []:
            sid = entry.get("source_id") if isinstance(entry, dict) else None
            if sid:
                ref_edges.append((
                    7, s_ord, occ, 0, "module_source_map", str(mid), "source", str(sid),
                    where, None, None, None, "E", "REF-SOURCE",
                    f"module source map references unknown source '{sid}'",
                ))
                occ += 1
            for route in list_items(entry.get("unit_routes") if isinstance(entry, dict) else None):
                uid = route if isinstance(route, str) else (
                    route.get("unit_id") if isinstance(route, dict) else None
                )
                if not uid:
                    continue
                if uid not in repo.units:
                    ref_edges.append((
                        7, s_ord, occ, 0, "module_source_map", str(mid), "unit", str(uid),
                        where, None, None, None, "E", "REF-UNIT",
                        f"module source map routes to unknown unit '{uid}'",
                    ))
                elif repo.units[uid].module_id != mid:
                    structural_violations.append((
                        7, s_ord, occ, 0, "E", "SOURCE-MAP-ROUTE",
                        f"module source map routes to foreign unit '{uid}'",
                        where,
                    ))
                elif isinstance(route, dict):
                    for knowledge_id in id_list_items(route.get("covers")):
                        ref_edges.append((
                            7, s_ord, occ, 0, "unit_route", str(uid), "knowledge_node", str(knowledge_id),
                            where, "unit", str(uid), None, "E", "REF-KNOWLEDGE",
                            f"source '{sid}' route to '{uid}' covers unknown knowledge node '{knowledge_id}'",
                        ))
                occ += 1

    # Family 8: Study Maps
    for s_ord, (smid, study_map) in enumerate(repo.study_maps.items()):
        where = _rel_path(study_map.path, repo.root)
        data = study_map.data
        occ = 0
        if data.get("unit_id") != study_map.unit_id:
            structural_violations.append((
                8, s_ord, occ, 0, "E", "MAP-OWNER",
                f"study map '{smid}' declares unit '{data.get('unit_id')}' but lives under '{study_map.unit_id}'",
                where,
            ))
            occ += 1

        for stage in data.get("stages", []) or []:
            for resource in stage.get("resources", []) or []:
                sid = resource.get("source_id") if isinstance(resource, dict) else None
                if sid:
                    ref_edges.append((
                        8, s_ord, occ, 0, "study_map", str(smid), "source", str(sid),
                        where, None, None, None, "E", "REF-SOURCE",
                        f"study map '{smid}' references unknown source '{sid}'",
                    ))
                route_id = resource.get("route_id") if isinstance(resource, dict) else None
                if route_id:
                    route_ref_rows.append((
                        "resource", str(smid), str(route_id),
                        str(study_map.unit_id),
                        sid,
                        None, # Resource locator guard is omitted by design
                        where,
                        8, s_ord, occ,
                    ))
                occ += 1

            for feedback in stage.get("source_feedback", []) or []:
                sid = feedback.get("source_id") if isinstance(feedback, dict) else None
                if sid:
                    ref_edges.append((
                        8, s_ord, occ, 0, "study_map", str(smid), "source", str(sid),
                        where, None, None, None, "E", "REF-SOURCE",
                        f"study map '{smid}' records feedback for unknown source '{sid}'",
                    ))
                    occ += 1

    # Family 9: Resume Pointer
    if repo.resume_pointer:
        pointer = repo.resume_pointer
        where = _rel_path(repo.resume_pointer_path, repo.root) if repo.resume_pointer_path else "curriculum/resume.yaml"
        occ = 0
        ref_edges.append((
            9, 0, occ, 0, "resume_pointer", "resume", "module", str(pointer.get("module_id")),
            where, None, None, None, "E", "REF-MODULE",
            "resume pointer references an unknown module",
        ))
        occ += 1
        ref_edges.append((
            9, 0, occ, 0, "resume_pointer", "resume", "unit", str(pointer.get("unit_id")),
            where, None, None, None, "E", "REF-UNIT",
            "resume pointer references an unknown unit",
        ))
        occ += 1
        ref_edges.append((
            9, 0, occ, 0, "resume_pointer", "resume", "study_map", str(pointer.get("study_map_id")),
            where, None, None, None, "E", "REF-STUDY-MAP",
            "resume pointer references an unknown study map",
        ))
        occ += 1
        if pointer.get("study_map_id") in repo.study_maps:
            ref_edges.append((
                9, 0, occ, 0, "resume_pointer", "resume", "stage", str(pointer.get("stage_id")),
                where, "study_map", str(pointer.get("study_map_id")), None, "E", "REF-STAGE",
                "resume pointer references an unknown stage",
            ))

    # Family 10: Learning Paths
    for s_ord, path in enumerate(repo.learning_paths.values()):
        where = _rel_path(path.path, repo.root)
        data = path.data
        declared = data.get("workspace_id")
        occ = 0
        ref_edges.append((
            10, s_ord, occ, 0, "learning_path", str(path.id), "workspace", str(declared),
            where, None, None, None, "E", "REF-WORKSPACE",
            f"learning path '{path.id}' references unknown workspace '{declared}'",
        ))
        occ += 1
        if declared in repo.workspaces and declared != path.workspace_id:
            structural_violations.append((
                10, s_ord, occ, 0, "E", "PATH-OWNER",
                f"learning path declares '{declared}' but lives under '{path.workspace_id}'",
                where,
            ))
            occ += 1
        module_id = data.get("module_id")
        if module_id:
            ref_edges.append((
                10, s_ord, occ, 0, "learning_path", str(path.id), "module", str(module_id),
                where, None, None, None, "E", "REF-MODULE",
                f"learning path '{path.id}' references unknown module '{module_id}'",
            ))
            occ += 1
        for stage in data.get("stages", []) or []:
            for cid in stage.get("concepts", []) or []:
                ref_edges.append((
                    10, s_ord, occ, 0, "learning_path", str(path.id), "concept", str(cid),
                    where, None, None, None, "E", "REF-CONCEPT",
                    f"learning path '{path.id}' references unknown concept '{cid}'",
                ))
                occ += 1
            for resource in stage.get("resources", []) or []:
                sid = resource.get("source_id") if isinstance(resource, dict) else None
                if sid:
                    ref_edges.append((
                        10, s_ord, occ, 0, "learning_path", str(path.id), "source", str(sid),
                        where, None, None, None, "E", "REF-SOURCE",
                        f"learning path '{path.id}' references unknown source '{sid}'",
                    ))
                    occ += 1

    # Family 11: Concepts
    for s_ord, concept in enumerate(repo.concepts.values()):
        rb = concept.get("replaced_by")
        if rb:
            ref_edges.append((
                11, s_ord, 0, 0, "concept", str(concept.get("id")), "concept", str(rb),
                "", None, None, None, "E", "REF-REPLACED-BY",
                f"concept '{concept.get('id')}' replaced_by unknown concept '{rb}'",
            ))

    # Family 12: Sources
    child_title_rows = []
    source_ident_rows = []
    for s_ord, source in enumerate(repo.sources.values()):
        sid = source.get("id")
        where = _origin_for(repo, "source", str(sid))
        occ = 0
        for gid in id_list_items(source.get("thematic_group_ids")):
            ref_edges.append((
                12, s_ord, occ, 0, "source", str(sid), "thematic_group", str(gid),
                where, None, None, None, "E", "REF-THEMATIC-GROUP",
                f"source '{sid}' references unknown thematic group '{gid}'",
            ))
            occ += 1
        for tid in source.get("topics", []) or []:
            ref_edges.append((
                12, s_ord, occ, 0, "source", str(sid), "topic", str(tid),
                where, None, None, None, "E", "REF-TOPIC",
                f"source '{sid}' references unknown topic '{tid}' — add it to sources/topics.yaml deliberately, or use an existing one",
            ))
            occ += 1

        identifiers = source.get("identifiers")
        labels = identifiers if isinstance(identifiers, dict) else {}
        for lab in labels:
            source_ident_rows.append((str(sid), str(lab)))

        discovery = source.get("discovery")
        if isinstance(discovery, dict):
            titles = discovery.get("child_titles")
            if isinstance(titles, dict):
                for ct_ord, label in enumerate(sorted(titles)):
                    child_title_rows.append((
                        str(sid), str(label), where, 12, s_ord, ct_ord,
                    ))

        mat = source.get("material")
        if mat:
            uri_issue = _check_uri_internal(repo, mat, f"sources registry ({source.get('id')})", 12, s_ord, occ)
            if uri_issue:
                structural_violations.append(uri_issue)
            occ += 1

    # Family 13: Topics
    for s_ord, (tid, topic) in enumerate(repo.topics.items()):
        domain = topic.get("domain")
        if domain:
            ref_edges.append((
                13, s_ord, 0, 0, "topic", str(tid), "thematic_group", str(domain),
                "sources/topics.yaml", None, None, None, "E", "REF-TOPIC-DOMAIN",
                f"topic '{tid}' declares unknown display domain '{domain}'",
            ))

    # Family 14: Relations
    relation_rows = []
    for i, rel in enumerate(repo.relations):
        frm, to = str(rel.get("from", "")), str(rel.get("to", ""))
        src = rel.get("source")
        relation_rows.append((
            i, frm, to, str(src) if src is not None else None,
            "knowledge/concept-relations.yaml",
        ))

    # Family 15: Coordination
    if repo.coordination is not None:
        deps = repo.coordination.section("Dependencies") or ""
        where = "work/COORDINATION.md"
        for c_ord, wid in enumerate(sorted(set(WORKSPACE_TOKEN_RE.findall(deps)))):
            ws = repo.workspaces.get(wid)
            if ws is None:
                structural_violations.append((
                    15, 0, c_ord, 0, "E", "COORD-DEP",
                    f"COORDINATION dependency cites unknown workspace '{wid}'",
                    where,
                ))
            elif ws.archived:
                structural_violations.append((
                    15, 0, c_ord, 0, "E", "COORD-DEP",
                    f"COORDINATION dependency cites archived workspace '{wid}'",
                    where,
                ))

    # Batch Insert Everything into SQLite
    cur.executemany(
        """INSERT INTO reference_edges (
            family_ordinal, source_ordinal, occurrence_ordinal, emission_rank,
            source_family, source_id, target_family, target_id, origin_path,
            scope_kind, scope_id, alt_target_family, severity, code, msg
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ref_edges,
    )

    cur.executemany(
        """INSERT INTO route_references (
            ref_kind, caller_id, route_id, guard_unit_id, guard_source_id,
            guard_locator, origin_path, family_ordinal, source_ordinal, occurrence_ordinal
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        route_ref_rows,
    )

    cur.executemany(
        """INSERT INTO synthesis_assessment_concepts (
            synthesis_id, route_id, concept_id, origin_path,
            family_ordinal, source_ordinal, occurrence_ordinal, emission_rank
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        synthesis_assessment_concept_rows,
    )

    cur.executemany(
        """INSERT INTO legacy_selections (
            unit_id, source_id, locator, origin_path,
            family_ordinal, source_ordinal, occurrence_ordinal
        ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
        legacy_selection_rows,
    )

    cur.executemany(
        """INSERT INTO child_titles (
            source_id, label, origin_path, family_ordinal, source_ordinal, occurrence_ordinal
        ) VALUES (?, ?, ?, ?, ?, ?)""",
        child_title_rows,
    )

    cur.executemany(
        "INSERT OR IGNORE INTO source_identifiers (source_id, label) VALUES (?, ?)",
        source_ident_rows,
    )

    cur.executemany(
        "INSERT INTO relations (ordinal, from_id, to_id, source_id, origin_path) VALUES (?, ?, ?, ?, ?)",
        relation_rows,
    )

    cur.executemany(
        """INSERT INTO structural_violations (
            family_ordinal, source_ordinal, occurrence_ordinal, emission_rank,
            severity, code, msg, origin_path
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        structural_violations,
    )

    conn.commit()
