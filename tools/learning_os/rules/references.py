"""Every reference resolves: ids, URIs and Markdown links."""

from __future__ import annotations

from .common import (
    CANONICAL_TREES, EVIDENCE_SCHEMES, MD_LINK_RE, Path, WORKSPACE_TOKEN_RE, _in_garden,
    _in_quarantine
)


class ChecksReferences:
    """Mixed into Validator; see rules/core.py."""
    def check_references(self):
        r = self.repo
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
            map_stage_ids = set()
            current_map = r.study_maps.get(data.get("current_study_map"))
            if current_map:
                map_stage_ids = {stage.get("id") for stage in current_map.data.get("stages", []) or []}
            for selection in data.get("source_selections", []) or []:
                sid = selection.get("source_id") if isinstance(selection, dict) else None
                if sid and sid not in r.sources:
                    self.err("REF-SOURCE", f"unit '{uid}' selects unknown source '{sid}'", where)
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
                for uid in entry.get("unit_routes", []) or []:
                    if uid not in r.units:
                        self.err("REF-UNIT", f"module source map routes to unknown unit '{uid}'", where)
                    elif r.units[uid].module_id != mid:
                        self.err("SOURCE-MAP-ROUTE", f"module source map routes to foreign unit '{uid}'", where)
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
            mat = source.get("material")
            if mat:
                self._check_uri(mat, f"sources registry ({source.get('id')})")
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
        if ref.startswith("note://"):
            if ref[len("note://"):] not in r.notes:
                self.err("URI-NOTE", f"'{ref}' does not resolve", where)
        elif ref.startswith("concept://"):
            if ref[len("concept://"):] not in r.concepts:
                self.err("URI-CONCEPT", f"'{ref}' does not resolve", where)
        elif ref.startswith("source://"):
            if ref[len("source://"):] not in r.sources:
                self.err("URI-SOURCE", f"'{ref}' does not resolve", where)
        elif ref.startswith("workspace://"):
            wid = ref[len("workspace://"):]
            if wid not in r.workspaces and wid not in r.quarantined_workspace_ids:
                self.err("URI-WORKSPACE", f"'{ref}' does not resolve", where)
        elif ref.startswith("material://"):
            rest = ref[len("material://"):]
            if not (r.materials_root / rest).exists():
                self.warn("URI-MATERIAL", f"'{ref}' does not resolve on disk (media may be offline)", where)
        elif ref.startswith("project://"):
            rest = ref[len("project://"):]
            if not (r.projects_root / rest).exists():
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
        if target.startswith(("http://", "https://", "mailto:")) or target.startswith("#"):
            return
        schemes = ("note://", "concept://", "source://", "workspace://",
                   "material://", "project://", "github://")
        if target.startswith(schemes):
            if target.startswith("github://"):
                return
            self._check_uri(target, where)
            return
        rel_path = target.split("#", 1)[0]
        if not rel_path:
            return
        resolved = (source_file.parent / rel_path).resolve()
        if not resolved.exists():
            self.err("LINK-BROKEN", f"internal link does not resolve: '{target}'", where)
