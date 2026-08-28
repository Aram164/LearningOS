"""Every reference resolves: ids, URIs and Markdown links."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ..loader import EVIDENCE_SCHEMES
from ..routes import exact_selection_matches, iter_route_references
from .common import CANONICAL_TREES, MD_LINK_RE, WORKSPACE_TOKEN_RE, _in_garden, _in_quarantine


@dataclass(frozen=True)
class ParsedReference:
    scheme: str
    target: str


@dataclass(frozen=True)
class ClassifiedLink:
    kind: Literal["skip", "uri", "relative"]
    target: str


def parse_reference_uri(value: str) -> ParsedReference | None:
    """Split one declared reference URI without consulting repository state."""
    for prefix in EVIDENCE_SCHEMES:
        if value.startswith(prefix):
            return ParsedReference(prefix.removesuffix("://"), value[len(prefix):])
    return None


def classify_markdown_link(target: str) -> ClassifiedLink:
    """Classify a Markdown target before any filesystem or registry lookup."""
    if target.startswith(("http://", "https://", "mailto:", "#")):
        return ClassifiedLink("skip", target)
    if parse_reference_uri(target) is not None:
        return ClassifiedLink("uri", target)
    relative = target.split("#", 1)[0]
    return ClassifiedLink("relative" if relative else "skip", relative)


class ChecksReferences:
    """Mixed into Validator; see rules/core.py."""
    def check_references(self):
        r = self.repo
        route_refs = list(iter_route_references(r))
        routes_by_id: dict[str, list] = {}
        for route_ref in route_refs:
            routes_by_id.setdefault(route_ref.route_id, []).append(route_ref)
            if not route_ref.authored_id:
                where = self._rel(r.module_source_map_origins[route_ref.module_id])
                self.warn(
                    "ROUTE-ID-MISSING",
                    f"source '{route_ref.source_id}' route to "
                    f"'{route_ref.unit_id}' has no persisted route id; "
                    f"v13 projects '{route_ref.route_id}' until migration",
                    where,
                )
        for route_id, matches in sorted(routes_by_id.items()):
            if len(matches) < 2:
                continue
            owners = sorted(
                f"{match.module_id}/{match.unit_id}/{match.source_id}"
                for match in matches
            )
            self.err(
                "ROUTE-ID-DUPLICATE",
                f"route id '{route_id}' is owned by more than one rich route: "
                + ", ".join(owners),
                "curriculum/modules",
            )
        for synthesis_id, synthesis in r.unit_material_syntheses.items():
            where = self._rel(r.unit_material_synthesis_origins[synthesis_id])
            synthesis_unit = synthesis.get("unit_id")
            if synthesis_unit not in r.units:
                self.err(
                    "REF-UNIT",
                    f"material synthesis '{synthesis_id}' references unknown "
                    f"unit '{synthesis_unit}'",
                    where,
                )
            for assessment in synthesis.get("route_assessments", []) or []:
                if not isinstance(assessment, dict):
                    continue
                route_id = assessment.get("route_id")
                matches = routes_by_id.get(str(route_id), [])
                if len(matches) != 1:
                    self.err(
                        "REF-ROUTE",
                        f"material synthesis '{synthesis_id}' route "
                        f"'{route_id}' resolves {len(matches)} rich routes",
                        where,
                    )
                    continue
                route_ref = matches[0]
                if route_ref.unit_id != synthesis_unit:
                    self.err(
                        "SYNTHESIS-ROUTE-OWNER",
                        f"material synthesis '{synthesis_id}' uses route "
                        f"'{route_id}' owned by '{route_ref.unit_id}'",
                        where,
                    )
                if route_ref.source_id != assessment.get("source_id"):
                    self.err(
                        "SYNTHESIS-SOURCE-GUARD",
                        f"material synthesis route '{route_id}' source guard "
                        "does not match the current route",
                        where,
                    )
                if route_ref.locator != assessment.get("locator"):
                    self.err(
                        "SYNTHESIS-LOCATOR-GUARD",
                        f"material synthesis route '{route_id}' locator guard "
                        "does not match the current route",
                        where,
                    )
                for concept_id in assessment.get("concept_ids", []) or []:
                    if concept_id not in r.concepts:
                        self.err(
                            "REF-CONCEPT",
                            f"material synthesis '{synthesis_id}' references "
                            f"unknown concept '{concept_id}'",
                            where,
                        )
            for group in synthesis.get("concept_groups", []) or []:
                if not isinstance(group, dict):
                    continue
                concept_id = group.get("concept_id")
                if concept_id not in r.concepts:
                    self.err(
                        "REF-CONCEPT",
                        f"material synthesis '{synthesis_id}' references "
                        f"unknown concept '{concept_id}'",
                        where,
                    )
                for related_unit_id in group.get("related_unit_ids", []) or []:
                    if related_unit_id not in r.units:
                        self.err(
                            "REF-UNIT",
                            f"material synthesis '{synthesis_id}' references "
                            f"unknown related unit '{related_unit_id}'",
                            where,
                        )
                for note_id in group.get("bridge_note_ids", []) or []:
                    if note_id not in r.notes:
                        self.err(
                            "REF-NOTE",
                            f"material synthesis '{synthesis_id}' references "
                            f"unknown bridge note '{note_id}'",
                            where,
                        )
        for note in r.notes.values():
            where = self._rel(note.path)
            for cid in note.meta.get("concepts", []) or []:
                if cid not in r.concepts:
                    self.err("REF-CONCEPT", f"note '{note.id}' references unknown concept '{cid}'", where)
            for sid in note.meta.get("sources", []) or []:
                if sid not in r.sources:
                    self.err("REF-SOURCE", f"note '{note.id}' references unknown source '{sid}'", where)
            for wid in note.meta.get("contexts", []) or []:
                if wid not in r.workspaces and wid not in r.quarantined_workspace_ids:
                    self.err("REF-WORKSPACE", f"note '{note.id}' references unknown workspace '{wid}'", where)
            for target in note.meta.get("supersedes", []) or []:
                if target not in r.notes:
                    self.err("REF-SUPERSEDES", f"note '{note.id}' supersedes unknown note '{target}'", where)
            for ev in note.meta.get("evidence", []) or []:
                ref = str(ev.get("ref", ""))
                if not ref.startswith(EVIDENCE_SCHEMES):
                    self.err("REF-EVIDENCE",
                             f"note '{note.id}' evidence ref '{ref}' uses no valid URI scheme", where)
                else:
                    self._check_uri(ref, where)
        for ws in r.workspaces.values():
            where = self._rel(ws.path)
            for cid in ws.meta.get("concepts", []) or []:
                if cid not in r.concepts:
                    self.err("REF-CONCEPT", f"workspace '{ws.id}' references unknown concept '{cid}'", where)
            for nid in ws.meta.get("notes", []) or []:
                if nid not in r.notes:
                    self.err("REF-NOTE", f"workspace '{ws.id}' references unknown note '{nid}'", where)
            for sid in ws.meta.get("sources", []) or []:
                if sid not in r.sources:
                    self.err("REF-SOURCE", f"workspace '{ws.id}' references unknown source '{sid}'", where)
            for pid in ws.meta.get("program_ids", []) or []:
                if pid not in r.programs:
                    self.err("REF-PROGRAM", f"workspace '{ws.id}' references unknown program '{pid}'", where)
            for mid in ws.meta.get("module_ids", []) or []:
                if mid not in r.modules:
                    self.err("REF-MODULE", f"workspace '{ws.id}' references unknown module '{mid}'", where)
            project_id = ws.meta.get("project_id")
            if project_id and project_id not in r.projects:
                self.err("REF-PROJECT",
                         f"workspace '{ws.id}' references unknown project '{project_id}'", where)
            for uid in ws.meta.get("unit_ids", []) or []:
                if uid not in r.units:
                    self.err("REF-UNIT", f"workspace '{ws.id}' references unknown unit '{uid}'", where)
        for mid, module in r.modules.items():
            where = self._origin_for("module", mid)
            for gid in module.get("thematic_group_ids", []) or []:
                if gid not in r.thematic_groups:
                    self.err(
                        "REF-THEMATIC-GROUP",
                        f"module '{mid}' references unknown thematic group '{gid}'",
                        where,
                    )
            area_id = module.get("area_id")
            if area_id and area_id not in r.programs:
                self.err("REF-PROGRAM", f"module '{mid}' references unknown program '{area_id}'", where)
            component_ids = {c.get("id") for c in module.get("components", []) or []
                             if isinstance(c, dict)}
            for uid in module.get("unit_order", []) or []:
                unit = r.units.get(uid)
                if unit is None:
                    self.err("REF-UNIT", f"module '{mid}' orders unknown unit '{uid}'", where)
                elif unit.module_id != mid:
                    self.err("UNIT-OWNER", f"module '{mid}' orders unit '{uid}' owned by '{unit.module_id}'", where)
            source_map = r.module_source_maps.get(mid)
            if module.get("source_map") and source_map is None:
                self.err("REF-SOURCE-MAP", f"module '{mid}' declares a missing source map", where)
            for related in module.get("related_module_ids", []) or []:
                if related not in r.modules:
                    self.err("REF-MODULE", f"module '{mid}' references unknown related module '{related}'", where)
            for uid, unit in r.units.items():
                if unit.module_id != mid:
                    continue
                component_id = unit.data.get("component_id")
                if component_id and component_id not in component_ids:
                    self.err("REF-COMPONENT",
                             f"unit '{uid}' references unknown component '{component_id}' in '{mid}'",
                             self._rel(unit.path))
        for uid, unit in r.units.items():
            where = self._rel(unit.path)
            data = unit.data
            if data.get("module_id") != unit.module_id:
                self.err("UNIT-OWNER",
                         f"unit '{uid}' declares module '{data.get('module_id')}' but lives under '{unit.module_id}'",
                         where)
            working_note = data.get("working_note")
            if working_note:
                target = r.root / str(working_note)
                expected_parent = unit.path.parent.resolve()
                try:
                    owned = target.resolve().is_relative_to(expected_parent)
                except OSError:
                    owned = False
                if not owned:
                    self.err("UNIT-NOTE-OWNER",
                             f"unit '{uid}' working note must live inside its unit directory", where)
                elif not target.is_file():
                    self.err("REF-UNIT-NOTE",
                             f"unit '{uid}' declares missing working note '{working_note}'", where)
            for scoped in data.get("scope_sources", []) or []:
                sid = scoped.get("source_id") if isinstance(scoped, dict) else None
                if sid and sid not in r.sources:
                    self.err("REF-SOURCE", f"unit '{uid}' references unknown scope source '{sid}'", where)
            for node in (data.get("knowledge_map") or {}).get("nodes", []) or []:
                if not isinstance(node, dict):
                    continue
                for concept_id in node.get("concept_ids", []) or []:
                    if concept_id not in r.concepts:
                        self.err(
                            "REF-CONCEPT",
                            f"unit '{uid}' knowledge node '{node.get('id')}' "
                            f"references unknown global concept '{concept_id}'",
                            where,
                        )
            map_stage_ids = set()
            current_map = r.study_maps.get(data.get("current_study_map"))
            if current_map:
                map_stage_ids = {stage.get("id") for stage in current_map.data.get("stages", []) or []}
            for selection in data.get("source_selections", []) or []:
                if not isinstance(selection, dict):
                    continue
                sid = selection.get("source_id") if isinstance(selection, dict) else None
                if sid and sid not in r.sources:
                    self.err("REF-SOURCE", f"unit '{uid}' selects unknown source '{sid}'", where)
                route_id = selection.get("route_id")
                if route_id:
                    id_matches = routes_by_id.get(str(route_id), [])
                    if not id_matches:
                        self.err(
                            "REF-ROUTE",
                            f"unit '{uid}' selects unknown route '{route_id}'",
                            where,
                        )
                    elif len(id_matches) == 1:
                        route_ref = id_matches[0]
                        if route_ref.unit_id != uid:
                            self.err(
                                "SELECTION-ROUTE-OWNER",
                                f"unit '{uid}' selects route '{route_id}' owned by "
                                f"'{route_ref.unit_id}'",
                                where,
                            )
                        if route_ref.source_id != selection.get("source_id"):
                            self.err(
                                "SELECTION-SOURCE-GUARD",
                                f"selection route '{route_id}' belongs to source "
                                f"'{route_ref.source_id}', not "
                                f"'{selection.get('source_id')}'",
                                where,
                            )
                        if route_ref.locator != selection.get("locator"):
                            self.err(
                                "SELECTION-LOCATOR-GUARD",
                                f"selection route '{route_id}' locator no longer "
                                "matches its stored guard",
                                where,
                            )
                else:
                    legacy_matches = exact_selection_matches(
                        route_refs,
                        unit_id=uid,
                        selection=selection,
                    )
                    # A legacy string edge has no route locator to match and
                    # remains valid evidence. Warn only when migration has one
                    # exact rich-route answer; unresolved/ambiguous cases stay
                    # in the explicit v13 migration report rather than making
                    # every preflight noisy forever.
                    if len(legacy_matches) == 1:
                        self.warn(
                            "SELECTION-ROUTE-ID-MISSING",
                            f"unit '{uid}' has a readable pre-v13 source "
                            f"selection without route_id; exact route "
                            f"'{legacy_matches[0].route_id}' is available",
                            where,
                        )
                for stage_id in selection.get("stage_ids", []) or []:
                    if stage_id not in map_stage_ids:
                        self.err("REF-STAGE", f"unit '{uid}' source selection routes to unknown stage '{stage_id}'", where)
            for nid in (data.get("artifacts") or {}).values():
                values = nid if isinstance(nid, list) else [nid]
                for value in values:
                    if value and value not in r.notes:
                        self.err("REF-NOTE", f"unit '{uid}' references unknown artifact '{value}'", where)
            for wid in data.get("workspace_ids", []) or []:
                if wid not in r.workspaces:
                    self.err("REF-WORKSPACE", f"unit '{uid}' references unknown workspace '{wid}'", where)
            for related in data.get("related_module_ids", []) or []:
                if related not in r.modules:
                    self.err("REF-MODULE", f"unit '{uid}' references unknown related module '{related}'", where)
            for related_uid in [data.get("parent_unit_id"), *(data.get("child_unit_ids", []) or [])]:
                if related_uid and related_uid not in r.units:
                    self.err("REF-UNIT", f"unit '{uid}' references unknown unit '{related_uid}'", where)
            smid = data.get("current_study_map")
            if smid:
                sm = r.study_maps.get(smid)
                if sm is None:
                    self.err("REF-STUDY-MAP", f"unit '{uid}' references unknown study map '{smid}'", where)
                elif sm.unit_id != uid:
                    self.err("MAP-OWNER", f"study map '{smid}' belongs to '{sm.unit_id}', not '{uid}'", where)
        for mid, source_map in r.module_source_maps.items():
            where = self._rel(r.module_source_map_origins[mid])
            if source_map.get("module_id") != mid:
                self.err("SOURCE-MAP-OWNER", f"source map declares '{source_map.get('module_id')}', lives under '{mid}'", where)
            for entry in source_map.get("sources", []) or []:
                sid = entry.get("source_id") if isinstance(entry, dict) else None
                if sid and sid not in r.sources:
                    self.err("REF-SOURCE", f"module source map references unknown source '{sid}'", where)
                for route in entry.get("unit_routes", []) or []:
                    uid = route if isinstance(route, str) else (
                        route.get("unit_id") if isinstance(route, dict) else None
                    )
                    if not uid:
                        continue
                    if uid not in r.units:
                        self.err("REF-UNIT", f"module source map routes to unknown unit '{uid}'", where)
                    elif r.units[uid].module_id != mid:
                        self.err("SOURCE-MAP-ROUTE", f"module source map routes to foreign unit '{uid}'", where)
                    elif isinstance(route, dict):
                        node_ids = {
                            node.get("id")
                            for node in (
                                (r.units[uid].data.get("knowledge_map") or {}).get("nodes", [])
                            )
                            if isinstance(node, dict) and node.get("id")
                        }
                        for knowledge_id in route.get("covers", []) or []:
                            if knowledge_id not in node_ids:
                                self.err(
                                    "REF-KNOWLEDGE",
                                    f"source '{sid}' route to '{uid}' covers unknown knowledge node '{knowledge_id}'",
                                    where,
                                )
        for smid, study_map in r.study_maps.items():
            where = self._rel(study_map.path)
            data = study_map.data
            if data.get("unit_id") != study_map.unit_id:
                self.err("MAP-OWNER", f"study map '{smid}' declares unit '{data.get('unit_id')}' but lives under '{study_map.unit_id}'", where)
            for stage in data.get("stages", []) or []:
                for resource in stage.get("resources", []) or []:
                    sid = resource.get("source_id") if isinstance(resource, dict) else None
                    if sid and sid not in r.sources:
                        self.err("REF-SOURCE", f"study map '{smid}' references unknown source '{sid}'", where)
                    route_id = resource.get("route_id") if isinstance(resource, dict) else None
                    if route_id:
                        id_matches = routes_by_id.get(str(route_id), [])
                        if not id_matches:
                            self.err(
                                "REF-ROUTE",
                                f"study map '{smid}' references unknown route "
                                f"'{route_id}'",
                                where,
                            )
                        elif len(id_matches) == 1:
                            route_ref = id_matches[0]
                            if route_ref.unit_id != study_map.unit_id:
                                self.err(
                                    "RESOURCE-ROUTE-OWNER",
                                    f"study map '{smid}' resource route "
                                    f"'{route_id}' belongs to "
                                    f"'{route_ref.unit_id}'",
                                    where,
                                )
                            if sid and sid != route_ref.source_id:
                                self.err(
                                    "RESOURCE-SOURCE-GUARD",
                                    f"study map '{smid}' resource route "
                                    f"'{route_id}' belongs to source "
                                    f"'{route_ref.source_id}', not '{sid}'",
                                    where,
                                )
                for feedback in stage.get("source_feedback", []) or []:
                    sid = feedback.get("source_id") if isinstance(feedback, dict) else None
                    if sid and sid not in r.sources:
                        self.err("REF-SOURCE", f"study map '{smid}' records feedback for unknown source '{sid}'", where)
        if r.resume_pointer:
            pointer = r.resume_pointer
            where = self._rel(r.resume_pointer_path) if r.resume_pointer_path else "curriculum/resume.yaml"
            if pointer.get("module_id") not in r.modules:
                self.err("REF-MODULE", "resume pointer references an unknown module", where)
            if pointer.get("unit_id") not in r.units:
                self.err("REF-UNIT", "resume pointer references an unknown unit", where)
            sm = r.study_maps.get(pointer.get("study_map_id"))
            if sm is None:
                self.err("REF-STUDY-MAP", "resume pointer references an unknown study map", where)
            elif pointer.get("stage_id") not in {s.get("id") for s in sm.data.get("stages", []) or []}:
                self.err("REF-STAGE", "resume pointer references an unknown stage", where)
        for path in r.learning_paths.values():
            where = self._rel(path.path)
            data = path.data
            declared = data.get("workspace_id")
            if declared not in r.workspaces:
                self.err("REF-WORKSPACE",
                         f"learning path '{path.id}' references unknown workspace '{declared}'",
                         where)
            elif declared != path.workspace_id:
                self.err("PATH-OWNER",
                         f"learning path declares '{declared}' but lives under '{path.workspace_id}'",
                         where)
            module_id = data.get("module_id")
            if module_id and module_id not in r.modules:
                self.err("REF-MODULE",
                         f"learning path '{path.id}' references unknown module '{module_id}'",
                         where)
            for stage in data.get("stages", []) or []:
                for cid in stage.get("concepts", []) or []:
                    if cid not in r.concepts:
                        self.err("REF-CONCEPT",
                                 f"learning path '{path.id}' references unknown concept '{cid}'",
                                 where)
                for resource in stage.get("resources", []) or []:
                    sid = resource.get("source_id") if isinstance(resource, dict) else None
                    if sid and sid not in r.sources:
                        self.err("REF-SOURCE",
                                 f"learning path '{path.id}' references unknown source '{sid}'",
                                 where)
        for concept in r.concepts.values():
            rb = concept.get("replaced_by")
            if rb and rb not in r.concepts:
                self.err("REF-REPLACED-BY",
                         f"concept '{concept.get('id')}' replaced_by unknown concept '{rb}'")
        for source in r.sources.values():
            sid = source.get("id")
            for gid in source.get("thematic_group_ids", []) or []:
                if gid not in r.thematic_groups:
                    self.err(
                        "REF-THEMATIC-GROUP",
                        f"source '{sid}' references unknown thematic group '{gid}'",
                        self._origin_for("source", str(sid)),
                    )
            # The topic vocabulary is closed on purpose (ADR-009): an unlisted
            # topic is how tag soup starts, so it is an error rather than an
            # implicit new topic.
            for tid in source.get("topics", []) or []:
                if tid not in r.topics:
                    self.err(
                        "REF-TOPIC",
                        f"source '{sid}' references unknown topic '{tid}' — add it to "
                        "sources/topics.yaml deliberately, or use an existing one",
                        self._origin_for("source", str(sid)),
                    )
            mat = source.get("material")
            if mat:
                self._check_uri(mat, f"sources registry ({source.get('id')})")
        # A topic's `domain` is a display grouping for the Library, not a
        # constraint on which sources may carry it — but it still has to name a
        # real group, or the browser renders a heading for nothing.
        for tid, topic in r.topics.items():
            domain = topic.get("domain")
            if domain and domain not in r.thematic_groups:
                self.err(
                    "REF-TOPIC-DOMAIN",
                    f"topic '{tid}' declares unknown display domain '{domain}'",
                    "sources/topics.yaml",
                )
        for i, rel in enumerate(r.relations):
            frm, to = str(rel.get("from", "")), str(rel.get("to", ""))
            where = "knowledge/concept-relations.yaml"
            if frm not in r.concepts:
                self.err("REL-ENDPOINT", f"relation[{i}] 'from' does not resolve: '{frm}'", where)
            if to not in r.concepts:
                self.err("REL-ENDPOINT", f"relation[{i}] 'to' does not resolve: '{to}'", where)
            if frm and frm == to:
                self.err("REL-SELF", f"relation[{i}] endpoints are not distinct ('{frm}')", where)
            src = rel.get("source")
            if src and src not in r.notes and src not in r.sources:
                self.err("REL-SOURCE", f"relation[{i}] cites unknown note/source '{src}'", where)
        # COORDINATION dependencies must reference active workspaces
        if r.coordination is not None:
            deps = r.coordination.section("Dependencies") or ""
            for wid in set(WORKSPACE_TOKEN_RE.findall(deps)):
                ws = r.workspaces.get(wid)
                if ws is None:
                    self.err("COORD-DEP", f"COORDINATION dependency cites unknown workspace '{wid}'",
                             "work/COORDINATION.md")
                elif ws.archived:
                    self.err("COORD-DEP", f"COORDINATION dependency cites archived workspace '{wid}'",
                             "work/COORDINATION.md")

    def _check_uri(self, ref: str, where: str):
        r = self.repo
        parsed = parse_reference_uri(ref)
        if parsed is None:
            return
        if parsed.scheme == "note":
            if parsed.target not in r.notes:
                self.err("URI-NOTE", f"'{ref}' does not resolve", where)
        elif parsed.scheme == "concept":
            if parsed.target not in r.concepts:
                self.err("URI-CONCEPT", f"'{ref}' does not resolve", where)
        elif parsed.scheme == "source":
            if parsed.target not in r.sources:
                self.err("URI-SOURCE", f"'{ref}' does not resolve", where)
        elif parsed.scheme == "workspace":
            wid = parsed.target
            if wid not in r.workspaces and wid not in r.quarantined_workspace_ids:
                self.err("URI-WORKSPACE", f"'{ref}' does not resolve", where)
        elif parsed.scheme == "material":
            # When the whole tree is unmounted every reference "fails", which is
            # noise, not information — check_materials() reports that situation
            # once. Per-reference warnings are only meaningful against a tree
            # that is actually present.
            if (r.learningos_root / "materials").is_dir():
                if not (r.materials_root / parsed.target).exists():
                    self.warn("URI-MATERIAL",
                              f"'{ref}' does not resolve on disk", where)
        elif parsed.scheme == "project":
            if not (r.projects_root / parsed.target).exists():
                self.warn("URI-PROJECT", f"'{ref}' does not resolve on disk", where)

    def check_links(self):
        r = self.repo
        for tree in CANONICAL_TREES:
            base = r.root / tree
            if not base.is_dir():
                continue
            for f in sorted(base.rglob("*.md")):
                if _in_garden(r.root, f) or _in_quarantine(r.root, f):
                    continue
                text = f.read_text(encoding="utf-8", errors="replace")
                for target in MD_LINK_RE.findall(text):
                    self._check_link(target, f)

    def _check_link(self, target: str, source_file: Path):
        where = self._rel(source_file)
        classified = classify_markdown_link(target)
        if classified.kind == "skip":
            return
        if classified.kind == "uri":
            if target.startswith("github://"):
                return
            self._check_uri(target, where)
            return
        resolved = (source_file.parent / classified.target).resolve()
        try:
            resolved.relative_to(self.repo.root.resolve())
        except ValueError:
            self.err(
                "LINK-ESCAPE",
                f"internal link escapes the repository: '{target}'",
                where,
            )
            return
        if not resolved.exists():
            self.err("LINK-BROKEN", f"internal link does not resolve: '{target}'", where)
