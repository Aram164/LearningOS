"""The atomic v2 projection every interface reads."""

from __future__ import annotations

import hashlib
import json
import re
from ..contracts.manifest_contract import declared_version, enforce
from ..loader import Repo
from ..transactions import load_revisions
from .atlas import ATLAS_COLLECTION_DOMAIN
from .common import _first_para, _git_last_commit, _git_state, _json_header, _strip_headings
from .coordination import adoption_counts
from .materials import _material_location, _project_material_resource
from .modules_view import _academic_deadlines

def _source_fingerprint(repo: Repo) -> str:
    """Content identity of every authored input used by the projection.

    Memoised on the ``Repo``. A ``Repo`` is the result of one ``load_repo``
    walk and is never mutated afterwards, so every caller holding the same
    instance is asking about the same bytes. Publishing alone asked twice —
    once for backlinks, once for the manifest — and each answer costs a full
    read-and-hash of every authored file. A write that changes the repository
    loads it again, which produces a new instance and therefore a new answer.
    """
    cached = getattr(repo, "_source_fingerprint_cache", None)
    if cached is not None:
        return cached
    digest = hashlib.sha256()
    roots = ("knowledge", "sources", "records", "work", "curriculum", "projects", "system/schema", "system/contracts")
    for rel_root in roots:
        base = repo.root / rel_root
        if not base.exists():
            continue
        files = [base] if base.is_file() else sorted(p for p in base.rglob("*") if p.is_file())
        for path in files:
            rel = path.relative_to(repo.root).as_posix()
            if any(part.startswith(".") for part in path.relative_to(repo.root).parts):
                continue
            digest.update(rel.encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    result = digest.hexdigest()
    try:
        repo._source_fingerprint_cache = result
    except (AttributeError, TypeError):
        pass          # a frozen or slotted Repo simply recomputes
    return result


_UNIT_NOTE_MARKER = re.compile(r"^<!-- learningos:unit-note (\{.*\}) -->\s*$", re.MULTILINE)


def _unit_note_sections(text: str) -> list[dict]:
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


def _ordered_thematic_group_ids(repo: Repo, values) -> list[str]:
    """Return unique group ids in the canonical registry order.

    Authored records own membership; the registry owns display order. Unknown
    ids remain at the end so a generated snapshot does not silently erase an
    invalid authored reference before validation reports it.
    """
    unique = {str(value) for value in (values or []) if value}
    order = {
        gid: (int(group.get("order", 0)), gid)
        for gid, group in repo.thematic_groups.items()
    }
    return sorted(unique, key=lambda gid: order.get(gid, (10**9, gid)))


def _source_thematic_groups(repo: Repo) -> dict[str, list[str]]:
    """Project source placement from explicit canonical relationships.

    This is deliberately a core projection rule: interfaces receive resolved
    group ids and never infer placement from a source title, path or id. A
    source can be placed directly, through a curated collection, or through a
    module source map whose module has explicit thematic membership.
    """
    grouped: dict[str, set[str]] = {
        sid: set(source.get("thematic_group_ids", []) or [])
        for sid, source in repo.sources.items()
    }
    for doc in repo.collections.values():
        group_ids = set(doc.get("thematic_group_ids", []) or [])
        for entry in doc.get("entries", []) or []:
            if not isinstance(entry, dict):
                continue
            sid = entry.get("source")
            if sid in grouped:
                grouped[sid].update(group_ids)
    for mid, source_map in repo.module_source_maps.items():
        group_ids = set((repo.modules.get(mid) or {}).get("thematic_group_ids", []) or [])
        for entry in source_map.get("sources", []) or []:
            if not isinstance(entry, dict):
                continue
            sid = entry.get("source_id")
            if sid in grouped:
                grouped[sid].update(group_ids)
    return {
        sid: _ordered_thematic_group_ids(repo, group_ids)
        for sid, group_ids in grouped.items()
    }


def build_manifest(repo: Repo, generated_at: str, backlinks: dict | None = None,
                   enforce_contract: bool = True) -> dict:
    """The COMPLETE machine-readable projection of the repository (ADR-001):
    every canonical record (notes incl. attachments/evidence/contexts, concepts,
    sources, modules incl. attempts, workspaces, coordination) plus all
    relations. A consumer needing repository state should read this file, not
    parse the tree.

    ADR-006 addendum (2026-08-03, fourth): this is also the INTERFACE contract.
    Every field an interface would otherwise re-derive by parsing Markdown or
    YAML is projected here — workspace `next_action`/`objective`, source
    `url`/`material`/`evaluations`, note `domain`/`summary`, and structured
    `academic_deadlines`. Usability lives in the interface; deriving meaning
    stays here, once. If a UI needs to regex a canonical file, that is a
    manifest bug.

    One fact, one shape: where a projection could be expressed two ways the
    manifest carries exactly one. `academic_deadlines` replaced the narrower
    `exam_spine` key (2026-08-03), and `stages` is the flat by-id index for
    stage lookup while `study_maps[].stages` stays the ordering authority —
    an index plus an ordered list, never two copies of the same access path."""
    artifact_revisions = load_revisions(repo.root)

    def projected_revision(record_id: str, data: dict | None = None) -> int:
        embedded = (data or {}).get("revision", 0)
        return artifact_revisions.get(record_id, embedded if isinstance(embedded, int) else 0)

    source_thematic_groups = _source_thematic_groups(repo)
    unit_to_projects: dict[str, list[str]] = {}
    for project_id, project in sorted(repo.projects.items()):
        for unit_id in project.data.get("unit_ids", []) or []:
            unit_to_projects.setdefault(unit_id, []).append(project_id)
    for unit_id in unit_to_projects:
        unit_to_projects[unit_id] = sorted(set(unit_to_projects[unit_id]))

    thematic_groups = [
        {
            "id": gid,
            "title": group.get("title", gid),
            "description": " ".join(str(group.get("description", "")).split()),
            "order": group.get("order", 0),
        }
        for gid, group in sorted(
            repo.thematic_groups.items(),
            key=lambda item: (int(item[1].get("order", 0)), item[0]),
        )
    ]
    # The topic vocabulary itself, so an interface can render titles and group
    # topics under their display domain instead of showing bare ids. `domain`
    # is a display grouping only — never a constraint on which sources may
    # carry a topic (ADR-009).
    topics_v2 = [
        {
            "id": tid,
            "title": topic.get("title", tid),
            "domain": topic.get("domain"),
        }
        for tid, topic in sorted(repo.topics.items())
    ]
    records = []
    for note in sorted(repo.notes.values(), key=lambda n: n.id):
        rel = note.path.relative_to(repo.root)
        records.append({
            "id": note.id, "type": "note",
            "title": note.meta.get("title", ""),
            "path": str(rel),
            "domain": rel.parent.name if rel.parent.name != "notes" else "",
            "summary": _first_para(_strip_headings(note.body))[:400],
            "role": note.meta.get("role", "synthesis"),
            "state": note.meta.get("state"),
            "authorship": note.meta.get("authorship"),
            "concepts": sorted(note.meta.get("concepts", []) or []),
            "sources": sorted(note.meta.get("sources", []) or []),
            "contexts": sorted(note.meta.get("contexts", []) or []),
            "attachments": list(note.meta.get("attachments", []) or []),
            "evidence": list(note.meta.get("evidence", []) or []),
            "supersedes": sorted(note.meta.get("supersedes", []) or []),
            "reviewed": note.meta.get("reviewed"),
            # The note-life axis: how the text got here and whether its meaning
            # has been checked. Both are schema fields (v3) and both are
            # authored today; omitting them meant the provenance of a
            # transcribed note stopped at the repository boundary.
            "transcription": note.meta.get("transcription"),
            "semantic_review": note.meta.get("semantic_review"),
        })
    for cid in sorted(repo.concepts):
        c = repo.concepts[cid]
        records.append({
            "id": cid, "type": "concept", "title": c.get("label", ""),
            "path": str(repo.concept_origins.get(cid, "").relative_to(repo.root))
            if repo.concept_origins.get(cid) else "knowledge/concepts.yaml",
            "aliases": sorted(c.get("aliases", []) or []),
            "deprecated": bool(c.get("deprecated", False)),
        })
    for sid in sorted(repo.sources):
        s = repo.sources[sid]
        records.append({
            "id": sid, "type": "source", "title": s.get("title", ""),
            "revision": projected_revision(sid, s),
            "path": str(repo.source_origins.get(sid, "").relative_to(repo.root))
            if repo.source_origins.get(sid) else "sources/sources.yaml",
            "source_type": s.get("type", ""),
            "thematic_group_ids": source_thematic_groups.get(sid, []),
            # ADR-009 topic facet. Projected even when empty, so an interface can
            # tell "no topics yet" from "this build predates topics" — on-use
            # population means most sources carry none for a long time, and that
            # sparsity is a fact to render, not a gap to hide.
            "topics": list(s.get("topics", []) or []),
            # interface fields: everything needed to SHOW and OPEN a source.
            # `material_path` is resolved HERE (material:// → the .flat farm is
            # a business rule, loader.materials_root) so no interface has to
            # reimplement URI resolution. It is relative to the LearningOS
            # root, i.e. the vault's parent.
            "url": s.get("url"),
            "material": s.get("material"),
            **_material_location(repo, s.get("material")),
            "authors": list(s.get("authors", []) or []),
            "organization": s.get("organization"),
            "year": s.get("year"),
            "identifiers": dict(s.get("identifiers", {}) or {}),
            "roles": sorted({str(r) for ev in (s.get("evaluations") or [])
                             for r in (ev.get("roles") or [])}),
            # `useful_sections` is where the reading plan actually lives ("read
            # ch. 3 for X") — projected with its concept links so an interface
            # can turn a source into a navigable table of contents.
            # Every field the evaluation schema allows is projected. It is a
            # closed schema (`additionalProperties: false`), so this list and
            # that one are the same list by construction — a projection that
            # emitted a subset silently held pedagogical judgment inside the
            # repository, and one that emitted an extra ("verdict", which the
            # schema has never allowed) shipped a field that could only ever
            # be null.
            "evaluations": [
                {"roles": list(ev.get("roles", []) or []),
                 "level": ev.get("level"),
                 "audience": list(ev.get("audience", []) or []),
                 "prerequisites": list(ev.get("prerequisites", []) or []),
                 "strengths": list(ev.get("strengths", []) or []),
                 "weaknesses": list(ev.get("weaknesses", []) or []),
                 "reviewed": ev.get("reviewed"),
                 "concepts": sorted(ev.get("concepts", []) or []),
                 "useful_sections": [
                     {"section": str(k), "note": str(v)}
                     for entry in (ev.get("useful_sections") or [])
                     if isinstance(entry, dict)
                     for k, v in entry.items()
                 ]}
                for ev in (s.get("evaluations") or []) if isinstance(ev, dict)
            ],
        })
    for project_id in sorted(repo.projects):
        project = repo.projects[project_id]
        data = project.data
        records.append({
            **dict(data),
            "revision": projected_revision(project_id, data),
            "path": str(project.path.relative_to(repo.root)),
            "relationship_ids": [
                relation.get("id") for relation in repo.project_relations
                if relation.get("from_project_id") == project_id
            ],
        })
    for relation in sorted(repo.project_relations, key=lambda row: str(row.get("id"))):
        records.append({**dict(relation), "type": "project-relationship",
                        "path": "projects/relations/project-relations.yaml"})
    for old_id, target_id in sorted(repo.project_aliases.items()):
        records.append({
            "id": old_id, "type": "compatibility-alias",
            "target_id": target_id, "target_type": "project",
            "path": "projects/aliases.yaml",
        })
    for mid in sorted(repo.modules):
        m = repo.modules[mid]
        if m.get("compatibility_only"):
            continue
        origin = repo.module_origins.get(mid)
        records.append({
            "id": mid, "type": "module", "title": m.get("title", ""),
            "revision": projected_revision(mid, m),
            "path": str(origin.relative_to(repo.root)) if origin else "records/modules.yaml",
            "kind": m.get("kind", "academic"), "area_id": m.get("area_id"),
            "thematic_group_ids": _ordered_thematic_group_ids(
                repo, m.get("thematic_group_ids", []) or []),
            "status": m.get("status", ""),
            "institution": m.get("institution"), "code": m.get("code"),
            "credits": m.get("credits"), "semester": m.get("semester"),
            "components": list(m.get("components", []) or []),
            "examination": m.get("examination"),
            "attempts": list(m.get("attempts", []) or []),
            "grade": m.get("grade"),
            "unit_order": list(m.get("unit_order", []) or []),
            "source_map": m.get("source_map"),
        })
    for name in sorted(repo.collections):
        doc = repo.collections[name]
        entries = [e for e in doc.get("entries", []) or [] if isinstance(e, dict)]
        collection_kind = doc.get("collection_kind", "catalogue")
        records.append({
            "id": name,
            "type": "topic-pack" if collection_kind == "topic-pack" else "collection",
            "revision": projected_revision(name, doc),
            "collection_kind": collection_kind,
            "title": doc.get("title", name),
            "path": f"sources/collections/{name}.yaml",
            "thematic_group_ids": _ordered_thematic_group_ids(
                repo, doc.get("thematic_group_ids", []) or []),
            "purpose": " ".join(str(doc.get("purpose", "")).split()) or None,
            "sources": [str(e.get("source", "")) for e in entries],
            # A shelf is curation, not a bag of ids: its rationale, its domain and
            # each entry's group + role are what make it browsable. Projected here
            # so no interface re-parses the collection YAML (ADR-006).
            "summary": " ".join(str(doc.get("description", "")).split()),
            "domain": ATLAS_COLLECTION_DOMAIN.get(name, "cross-domain"),
            # File order is canonical for topic packs and catalogues alike.
            "entries": [{"source": str(e.get("source", "")),
                         "group": str(e.get("group", "")) or None,
                         "why": " ".join(str(e.get("why", "")).split()) or None}
                        for e in entries],
        })
    for ws in sorted(repo.workspaces.values(), key=lambda w: w.id):
        records.append({
            "id": ws.id, "type": "workspace", "title": ws.meta.get("title", ""),
            "revision": projected_revision(ws.id, ws.meta),
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
    for learning_path in sorted(repo.learning_paths.values(), key=lambda p: p.id):
        data = learning_path.data
        projected_stages = []
        for stage in data.get("stages", []) or []:
            projected = dict(stage)
            if isinstance(stage, dict) and isinstance(
                    stage.get("resources"), list):
                projected["resources"] = [
                    _project_material_resource(repo, resource)
                    if isinstance(resource, dict) else resource
                    for resource in stage["resources"]
                ]
            note_ref = stage.get("notes_path") if isinstance(stage, dict) else None
            note_file = repo.root / str(note_ref) if note_ref else None
            if note_file and note_file.is_file():
                projected["notes_text"] = note_file.read_text(
                    encoding="utf-8", errors="replace")
                projected["notes_updated"] = _git_last_commit(
                    repo.root, note_file.relative_to(repo.root).as_posix())
            else:
                projected["notes_text"] = ""
                projected["notes_updated"] = None
            projected_stages.append(projected)
        records.append({
            "id": learning_path.id, "type": "learning-path",
            "revision": projected_revision(learning_path.id, data),
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
            "stages": projected_stages,
            "shelving": dict(data.get("shelving", {}) or {}),
            "archived": learning_path.archived,
        })
    for program in sorted(repo.programs.values(), key=lambda p: p.id):
        records.append({
            **dict(program.data),
            "revision": projected_revision(program.id, program.data),
            "path": str(program.path.relative_to(repo.root)),
        })
    for unit in sorted(repo.units.values(), key=lambda u: u.id):
        data = unit.data
        note_ref = data.get("working_note")
        note_file = repo.root / str(note_ref) if note_ref else None
        note_text = note_file.read_text(encoding="utf-8", errors="replace") \
            if note_file and note_file.is_file() else ""
        records.append({
            **dict(data),
            "revision": projected_revision(unit.id, data),
            "path": str(unit.path.relative_to(repo.root)),
            # Projects own units explicitly in the Project record. The legacy
            # module_id remains for compatibility until Gate F, while interfaces
            # receive the first-class ownership edge directly from the core.
            "project_ids": unit_to_projects.get(unit.id, []),
            "notes_text": note_text,
            "note_sections": _unit_note_sections(note_text),
            "notes_updated": _git_last_commit(
                repo.root, note_file.relative_to(repo.root).as_posix())
                if note_file and note_file.is_file() else None,
        })
    for study_map in sorted(repo.study_maps.values(), key=lambda sm: sm.id):
        data = study_map.data
        projected_stages = []
        for stage in data.get("stages", []) or []:
            projected = dict(stage)
            if isinstance(stage, dict) and isinstance(
                    stage.get("resources"), list):
                projected["resources"] = [
                    _project_material_resource(repo, resource)
                    if isinstance(resource, dict) else resource
                    for resource in stage["resources"]
                ]
            note_ref = stage.get("working_note") if isinstance(stage, dict) else None
            note_file = repo.root / str(note_ref) if note_ref else None
            if note_file and note_file.is_file():
                projected["notes_text"] = note_file.read_text(
                    encoding="utf-8", errors="replace")
                projected["notes_updated"] = _git_last_commit(
                    repo.root, note_file.relative_to(repo.root).as_posix())
            else:
                projected["notes_text"] = ""
                projected["notes_updated"] = None
            projected_stages.append(projected)
        records.append({
            **{k: v for k, v in data.items() if k != "stages"},
            "revision": projected_revision(study_map.id, data),
            "module_id": study_map.module_id,
            "path": str(study_map.path.relative_to(repo.root)),
            "stages": projected_stages,
        })
    for mid in sorted(repo.module_source_maps):
        source_map = repo.module_source_maps[mid]
        source_map_id = f"source-map-{mid.removeprefix('module-')}"
        records.append({
            "id": source_map_id,
            **dict(source_map),
            "revision": projected_revision(source_map_id, source_map),
            "path": str(repo.module_source_map_origins[mid].relative_to(repo.root)),
        })
    if repo.coordination is not None:
        records.append({
            "id": "coordination", "type": "coordination",
            "path": "work/COORDINATION.md",
            "sections": {h: (repo.coordination.section(h) or "")
                         for h in ("Commitments", "Priorities", "Dependencies", "Deferrals")},
        })
    relations = [
        {"from": r.get("from"), "type": r.get("type"), "to": r.get("to"),
         "context": r.get("context"), "source": r.get("source")}
        for r in sorted(repo.relations,
                        key=lambda r: (str(r.get("from")), str(r.get("type")), str(r.get("to"))))
    ]
    ad = adoption_counts(repo)
    fingerprint = _source_fingerprint(repo)
    revision, dirty = _git_state(repo.root)
    generated_meta = _json_header(generated_at)
    generated_meta.update({
        # Read from system/contracts/manifest-contract.yaml, never hardcoded:
        # the version announced and the shape declared must have one source.
        "contract_version": declared_version(repo.root),
        "snapshot_id": f"sha256:{fingerprint}",
        "source_fingerprint": fingerprint,
        "source_revision": revision,
        "source_dirty": dirty,
    })
    programs_v2 = [r for r in records if r.get("type") == "program"]
    projects_v2 = [r for r in records if r.get("type") == "project"]
    project_relationships_v2 = [
        r for r in records if r.get("type") == "project-relationship"
    ]
    modules_v2 = [r for r in records if r.get("type") == "module"]
    units_v2 = [r for r in records if r.get("type") == "unit"]
    study_maps_v2 = [r for r in records if r.get("type") == "study-map"]
    source_maps_v2 = [r for r in records if r.get("type") == "module-source-map"]
    topic_packs_v2 = [r for r in records if r.get("type") == "topic-pack"]
    stages_v2 = [
        {**stage, "study_map_id": study_map["id"],
         "unit_id": study_map["unit_id"], "module_id": study_map["module_id"]}
        for study_map in study_maps_v2 for stage in study_map.get("stages", [])
    ]
    module_to_units = {
        module["id"]: [uid for uid in module.get("unit_order", []) if uid]
        for module in modules_v2
    }
    unit_to_study_map = {
        unit["id"]: unit.get("current_study_map")
        for unit in units_v2 if unit.get("current_study_map")
    }
    component_to_units: dict[str, list[str]] = {}
    source_to_modules: dict[str, list[str]] = {}
    source_to_units: dict[str, list[str]] = {}
    workspace_to_modules: dict[str, list[str]] = {}
    workspace_to_units: dict[str, list[str]] = {}
    project_to_units: dict[str, list[str]] = {
        project["id"]: list(project.get("unit_ids", []) or []) for project in projects_v2
    }
    project_to_workspaces: dict[str, list[str]] = {
        project["id"]: list(project.get("workspace_ids", []) or []) for project in projects_v2
    }
    project_to_relationships: dict[str, list[str]] = {
        project["id"]: [
            relation["id"] for relation in project_relationships_v2
            if relation.get("from_project_id") == project["id"]
        ]
        for project in projects_v2
    }
    for unit in units_v2:
        if unit.get("component_id"):
            component_to_units.setdefault(unit["component_id"], []).append(unit["id"])
        for scoped in unit.get("scope_sources", []) or []:
            if scoped.get("source_id"):
                source_to_units.setdefault(scoped["source_id"], []).append(unit["id"])
        for selection in unit.get("source_selections", []) or []:
            if selection.get("source_id"):
                source_to_units.setdefault(selection["source_id"], []).append(unit["id"])
    for source_map in source_maps_v2:
        mid = source_map.get("module_id")
        for entry in source_map.get("sources", []) or []:
            sid = entry.get("source_id")
            if sid:
                source_to_modules.setdefault(sid, []).append(mid)
            for uid in entry.get("unit_routes", []) or []:
                source_to_units.setdefault(sid, []).append(uid)
    for study_map in study_maps_v2:
        for stage in study_map.get("stages", []) or []:
            for resource in stage.get("resources", []) or []:
                sid = resource.get("source_id")
                if sid:
                    source_to_units.setdefault(sid, []).append(study_map["unit_id"])
    for workspace in [r for r in records if r.get("type") == "workspace" and not r.get("archived")]:
        workspace_to_modules[workspace["id"]] = list(workspace.get("module_ids", []) or [])
        workspace_to_units[workspace["id"]] = list(workspace.get("unit_ids", []) or [])
    for table in (component_to_units, source_to_modules, source_to_units,
                  workspace_to_modules, workspace_to_units, project_to_units,
                  project_to_workspaces, project_to_relationships):
        for key in table:
            table[key] = sorted(set(table[key]))
    progress = {}
    study_map_by_unit = {sm["unit_id"]: sm for sm in study_maps_v2}
    unit_by_id = {u["id"]: u for u in units_v2}
    for module in modules_v2:
        module_units = [unit_by_id[uid] for uid in module.get("unit_order", [])
                        if uid in unit_by_id]
        stage_rows = [stage for unit in module_units
                      for stage in (study_map_by_unit.get(unit["id"], {}).get("stages", []) or [])]
        progress[module["id"]] = {
            "units_total": len(module_units),
            "units_complete": sum(1 for unit in module_units if unit.get("status") == "complete"),
            "units_needing_map": sum(1 for unit in module_units if unit.get("status") == "needs-map"),
            "stages_total": len(stage_rows),
            "stages_complete": sum(1 for stage in stage_rows if stage.get("status") == "complete"),
        }
    semesters_v2 = [
        {**semester, "program_id": program["id"]}
        for program in programs_v2 for semester in program.get("semesters", []) or []
    ]
    inbox_dir = repo.root / "work" / "inbox"
    inbox_items = len([
        item for item in inbox_dir.iterdir() if not item.name.startswith(".")
    ]) if inbox_dir.is_dir() else 0
    # Additive feature contract: AI action state is projected by the core and
    # remains optional for older consumers of manifest contract v2.
    from learning_os.ai_actions import manifest_ai_projection
    ai_projection = manifest_ai_projection(repo.root)
    payload = {
        "_generated": generated_meta,
        "records": records,
        "relations": relations,
        # Backlinks are part of the SAME atomic manifest snapshot. The legacy
        # backlinks.json remains as a compatibility view, but interfaces never
        # need to race two separately-written files again.
        "backlinks": {k: v for k, v in (backlinks or {}).items() if k != "_generated"},
        # Interface convenience: every academic date an interface can render
        # with no Python running at all — registered attempts, available
        # sittings that have no attempt yet, and grouped registration windows,
        # already ordered. `_academic_deadlines` correlates attempts with
        # `examination.sittings` here so no interface repeats that rule.
        #
        # There is deliberately no separate `exam_spine` key: it was a strict
        # subset of this list (registered attempts only) and a second shape for
        # the same facts. `_exam_spine` survives as the internal helper behind
        # the Markdown views and `los.py status --json` (ADR-006, 2026-08-03).
        "academic_deadlines": _academic_deadlines(repo),
        "thematic_groups": thematic_groups,
        "topics": topics_v2,
        "topic_packs": topic_packs_v2,
        "projects": projects_v2,
        "project_relationships": project_relationships_v2,
        "project_aliases": dict(sorted(repo.project_aliases.items())),
        "artifact_revisions": dict(sorted(artifact_revisions.items())),
        "programs": programs_v2,
        "semesters": semesters_v2,
        "modules": modules_v2,
        "units": units_v2,
        "study_maps": study_maps_v2,
        "stages": stages_v2,
        "module_source_maps": source_maps_v2,
        "resume_pointer": dict(repo.resume_pointer or {}),
        "garden_entries": ai_projection["garden_entries"],
        "ai_actions": ai_projection["ai_actions"],
        "quarantine_boundaries": [
            {k: program.get(k) for k in
             ("id", "title", "kind", "status", "description", "boundary_action")}
            for program in programs_v2
            if program.get("status") in {"quarantined", "boundary-only"}
        ],
        "indexes": {
            "module_to_units": module_to_units,
            "unit_to_study_map": unit_to_study_map,
            "component_to_units": dict(sorted(component_to_units.items())),
            "source_to_modules": dict(sorted(source_to_modules.items())),
            "source_to_units": dict(sorted(source_to_units.items())),
            "workspace_to_modules": dict(sorted(workspace_to_modules.items())),
            "workspace_to_units": dict(sorted(workspace_to_units.items())),
            "project_to_units": dict(sorted(project_to_units.items())),
            "project_to_workspaces": dict(sorted(project_to_workspaces.items())),
            "project_to_relationships": dict(sorted(project_to_relationships.items())),
            "project_aliases": dict(sorted(repo.project_aliases.items())),
        },
        "progress": progress,
        "counts": {
            "notes": len(repo.notes), "concepts": len(repo.concepts),
            "sources": len(repo.sources), "collections": len(repo.collections),
            "topic_packs": len(topic_packs_v2),
            "thematic_groups": len(thematic_groups),
            "topics": len(topics_v2),
            "sources_with_topics": sum(
                1 for s in repo.sources.values() if s.get("topics")),
            "projects": len(projects_v2),
            "modules": len(modules_v2),
            "workspaces_active": len(repo.active_workspaces()),
            "workspaces_archived": len(repo.archived_workspaces()),
            "learning_paths": len(repo.learning_paths),
            "learning_paths_active": sum(
                1 for p in repo.active_learning_paths() if p.status == "active"),
            "programs": len(repo.programs),
            "units": len(repo.units),
            "study_maps": len(repo.study_maps),
            "stages": len(stages_v2),
            "stages_complete": sum(1 for stage in stages_v2 if stage.get("status") == "complete"),
            "source_feedback_records": sum(
                len(stage.get("source_feedback", []) or []) for stage in stages_v2),
            "units_needing_map": sum(1 for unit in units_v2 if unit.get("status") == "needs-map"),
            "inbox_items": inbox_items,
            "garden_entries": len(ai_projection["garden_entries"]),
            "ai_action_requests": len(ai_projection["ai_actions"]["requests"]),
            "relations": len(repo.relations),
            "notes_reviewed": ad["notes_reviewed"],
            "notes_with_evidence": ad["notes_with_evidence"],
        },
    }
    # The published shape is a versioned interface, so the producer proves it
    # still matches what it announced. Adding a top-level key while continuing
    # to call the projection v2 is what turned UI CI red on 2026-08-08; that
    # class of mistake now fails here, in Core's own test run, instead of in a
    # downstream repository after the push.
    if enforce_contract:
        enforce(payload, repo.root)
    return payload
