"""Parse failures, schema conformance, identity and file placement."""

from __future__ import annotations

import time

from ..loader import (
    ID_RE,
    PATH_ID_RE,
    PROGRAM_ID_RE,
    PROJECT_ID_RE,
    PROJECT_RELATION_ID_RE,
    STUDY_MAP_ID_RE,
    UNIT_ID_RE,
)
from .common import KNOWLEDGE_TEXT_SUFFIXES, SUFFIX_RE


class ChecksStructure:
    """Mixed into Validator; see rules/core.py."""
    # ------------------------------------------------------------- sections
    def check_parse_failures(self):
        for path, msg in self.repo.parse_failures:
            self.err("PARSE", msg, self._rel(path))
        for family, rec_id, origin in self.repo.duplicate_ids:
            self.err("ID-DUP", f"duplicate {family} id '{rec_id}'", self._rel(origin))

    def check_schemas(self):
        r = self.repo
        self._schema_check("concepts", {"concepts": list(r.concepts.values())},
                           "knowledge/concepts.yaml")
        self._schema_check("concept-relations", {"relations": r.relations},
                           "knowledge/concept-relations.yaml")
        self._schema_check("sources", {"sources": list(r.sources.values())},
                           "sources/sources.yaml")
        self._schema_check("modules", {"modules": list(r.legacy_modules.values())},
                           "records/modules.yaml")
        for program in r.programs.values():
            self._schema_check("program", program.data, self._rel(program.path))
        for mid, module in r.modules.items():
            origin = r.module_origins.get(mid)
            if origin and origin.name == "module.yaml":
                self._schema_check("module", module, self._rel(origin))
        for unit in r.units.values():
            self._schema_check("unit", unit.data, self._rel(unit.path))
        for mid, source_map in r.module_source_maps.items():
            self._schema_check("module-source-map", source_map,
                               self._rel(r.module_source_map_origins[mid]))
        for study_map in r.study_maps.values():
            if study_map.authored_data is not None and study_map.authored_data != study_map.data:
                self._schema_check("study-map", study_map.authored_data, self._rel(study_map.path))
            self._schema_check("study-map", study_map.data, self._rel(study_map.path))
        for synthesis_id, synthesis in r.unit_material_syntheses.items():
            self._schema_check(
                "unit-material-synthesis",
                synthesis,
                self._rel(r.unit_material_synthesis_origins[synthesis_id]),
            )
        if r.resume_pointer is not None and r.resume_pointer_path is not None:
            self._schema_check("resume", r.resume_pointer, self._rel(r.resume_pointer_path))
        for note in r.notes.values():
            self._schema_check("note", note.meta, self._rel(note.path))
        for ws in r.workspaces.values():
            self._schema_check("workspace", ws.meta, self._rel(ws.path))
        for path in r.learning_paths.values():
            self._schema_check("learning-path", path.data, self._rel(path.path))
        if r.coordination is not None:
            self._schema_check("coordination", r.coordination.meta, "work/COORDINATION.md")
        for name, doc in r.collections.items():
            self._schema_check("collections", doc, f"sources/collections/{name}.yaml")
        if r.thematic_groups_path is not None:
            self._schema_check(
                "thematic-groups",
                {"thematic_groups": list(r.thematic_groups.values())},
                self._rel(r.thematic_groups_path),
            )
        for project in r.projects.values():
            self._schema_check("project", project.data, self._rel(project.path))
        if r.project_aliases_path is not None:
            self._schema_check(
                "project-aliases", {"aliases": dict(r.project_aliases)},
                self._rel(r.project_aliases_path),
            )
        if r.project_relations_path is not None:
            self._schema_check(
                "project-relations", {"relations": list(r.project_relations)},
                self._rel(r.project_relations_path),
            )

    def check_identity(self):
        families = {
            "note": self.repo.notes, "concept": self.repo.concepts,
            "source": self.repo.sources, "workspace": self.repo.workspaces,
            "module": self.repo.modules,
        }
        for family, records in families.items():
            for rec_id in records:
                where = self._origin_for(family, rec_id)
                if not ID_RE.match(rec_id):
                    self.err("ID-PATTERN", f"{family} id '{rec_id}' does not match the ID pattern",
                             where)
                elif not rec_id.startswith(family + "-"):
                    self.err("ID-FAMILY", f"{family} id '{rec_id}' lacks family prefix '{family}-'",
                             where)
                m = SUFFIX_RE.match(rec_id)
                if m and m.group("base") not in records:
                    self.warn("ID-SUFFIX",
                              f"{family} id '{rec_id}' carries a numeric suffix without a "
                              f"collision counterpart '{m.group('base')}' (suffixes are collision-only)",
                              where)
        for project_id in self.repo.projects:
            if not PROJECT_ID_RE.match(project_id):
                self.err("ID-PATTERN",
                         f"project id '{project_id}' does not match the ID pattern",
                         self._origin_for("project", project_id))
        for relation in self.repo.project_relations:
            relation_id = relation.get("id")
            if not isinstance(relation_id, str) or not PROJECT_RELATION_ID_RE.match(relation_id):
                self.err("ID-PATTERN",
                         f"project relationship id '{relation_id}' does not match the ID pattern",
                         self._rel(self.repo.project_relations_path)
                         if self.repo.project_relations_path else "projects/relations/project-relations.yaml")
        for pid in self.repo.programs:
            if not PROGRAM_ID_RE.match(pid):
                self.err("ID-PATTERN", f"program id '{pid}' does not match the ID pattern",
                         self._origin_for("program", pid))
        for uid in self.repo.units:
            if not UNIT_ID_RE.match(uid):
                self.err("ID-PATTERN", f"unit id '{uid}' does not match the ID pattern",
                         self._origin_for("unit", uid))
        for smid in self.repo.study_maps:
            if not STUDY_MAP_ID_RE.match(smid):
                self.err("ID-PATTERN", f"study map id '{smid}' does not match the ID pattern",
                         self._origin_for("study-map", smid))
        for path_id, learning_path in self.repo.learning_paths.items():
            where = self._rel(learning_path.path)
            if not PATH_ID_RE.match(path_id):
                self.err("ID-PATTERN",
                         f"learning path id '{path_id}' does not match the ID pattern",
                         where)

    def check_files(self):
        r = self.repo
        # Note filename == <id>.md
        for note in r.notes.values():
            if note.path.name != f"{note.id}.md":
                self.err("FILE-NAME",
                         f"note file '{note.path.name}' does not equal its frontmatter id '{note.id}.md'",
                         self._rel(note.path))
        # Attachments resolve; orphaned attachment folders
        attach_root = r.root / "knowledge" / "attachments"
        referenced_dirs = set()
        for note in r.notes.values():
            note_attach_dir = (attach_root / note.id).resolve()
            for entry in note.meta.get("attachments", []) or []:
                referenced_dirs.add(note.id)
                p = (r.root / str(entry)).resolve()
                # Containment is decided on the RESOLVED filesystem path so that
                # '..' segments (or symlinks) cannot escape the note's own
                # attachment directory. A plain string-prefix check would accept
                # e.g. knowledge/attachments/<id>/../<other>/secret.pdf.
                if p != note_attach_dir and note_attach_dir not in p.parents:
                    self.err("ATTACH-PATH",
                             f"attachment '{entry}' of note '{note.id}' resolves outside its "
                             f"attachment directory knowledge/attachments/{note.id}/",
                             self._rel(note.path))
                    continue  # not owned by this note — do not run the existence check
                if not p.exists():
                    self.err("ATTACH-MISSING", f"attachment '{entry}' does not resolve",
                             self._rel(note.path))
        if attach_root.is_dir():
            for d in sorted(attach_root.iterdir()):
                if d.is_dir() and d.name not in referenced_dirs:
                    self.warn("ATTACH-ORPHAN",
                              f"attachment folder '{d.name}' has no owning note referencing it",
                              self._rel(d))
        # Binary files under knowledge/ outside attachments/
        knowledge = r.root / "knowledge"
        if knowledge.is_dir():
            for f in sorted(knowledge.rglob("*")):
                if not f.is_file():
                    continue
                if attach_root in f.parents:
                    continue
                if f.suffix.lower() not in KNOWLEDGE_TEXT_SUFFIXES:
                    self.warn("BINARY-IN-KNOWLEDGE",
                              f"non-Markdown/YAML file under knowledge/: {self._rel(f)} "
                              "(books/slides belong in materials)")
        # Inbox items older than 14 days
        inbox = r.root / "work" / "inbox"
        if inbox.is_dir():
            now = time.time()
            for f in sorted(inbox.iterdir()):
                if f.name.startswith("."):
                    continue
                age_days = (now - f.stat().st_mtime) / 86400
                if age_days > 14:
                    self.warn("INBOX-STALE",
                              f"inbox item '{f.name}' is {int(age_days)} days old "
                              "(unrouted capture — the inbox should trend toward empty)")
