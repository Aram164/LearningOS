"""Validation rules for Learning OS v3 (BUILD-SPEC Step 4).

Implements system/VALIDATION.md on top of the JSON Schemas in system/schema/.
Severity: E = error (blocks acceptance), W = warning.

Scope notes (documented decisions):
  - Internal-link integrity is checked for canonical trees (knowledge/, sources/,
    records/, work/) — NOT for archive/ (archived workspaces are preserved
    unchanged and may carry legacy paths) and NOT for system/ (spec package).
  - The generated-input boundary is checked for the same canonical trees.
"""

from __future__ import annotations

import datetime as _dt
import json
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

import jsonschema

from .loader import (
    EVIDENCE_SCHEMES,
    ID_RE,
    PATH_ID_RE,
    PROGRAM_ID_RE,
    RELATION_TYPES,
    Repo,
    STUDY_MAP_ID_RE,
    UNIT_ID_RE,
)

ISO_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
# Collision suffixes are short counters (-02, -03, …); longer trailing numbers
# are usually identifiers (course numbers like -1805, -6036), not suffixes.
SUFFIX_RE = re.compile(r"^(?P<base>.+)-(?P<num>\d{1,2})$")
WORKSPACE_TOKEN_RE = re.compile(r"\bworkspace-[a-z0-9]+(?:-[a-z0-9]+)*\b")

REQUIRED_WORKSPACE_SECTIONS = ("Objective", "Current Scope", "Open Questions", "Next Action")
COORDINATION_SECTIONS = ("Commitments", "Priorities", "Dependencies", "Deferrals")

# Crosswalk judgment-table heuristic vocabulary (exact header cells, case-insensitive)
JUDGMENT_HEADERS = {"strengths", "weaknesses", "level", "best for", "best-for"}

GENERATED_ALLOWED = {
    "manifest.json", "concept-index.md", "source-index.md", "module-view.md",
    "coordination-view.md", "dependency-report.md", "concept-map.md",
    "backlinks.json", "nebula.md", "domain-atlas.md", "reading-room.md",
    "concept-canvas.canvas",
    ".gitkeep",
    ".DS_Store",  # OS metadata noise, gitignored — not an agent artifact
}
GENERATED_REPORT_PREFIXES = ("validation-report", "health")

CANONICAL_TREES = ("knowledge", "sources", "records", "work", "curriculum")

# File extensions that are legitimately authored text under knowledge/ (notes and
# registries). Anything else there (PDFs, slides, images) is a misplaced binary
# — see BINARY-IN-KNOWLEDGE. (Formerly the misleadingly named IMAGE_OK.)
KNOWLEDGE_TEXT_SUFFIXES = {".md", ".yaml", ".yml"}

# knowledge/garden/ is the exploratory layer (CLAUDE.md §14): deliberately
# free-form and exempt from every structural rule. The validator skips it
# wherever it walks the canonical trees, so half-formed notes — informal links,
# bare wikilinks, references to generated/ — never block `make check`. (Stray
# non-Markdown files there are still flagged, keeping the Garden text-only.)
GARDEN_SUBTREE = ("knowledge", "garden")

# ---- Hygiene sweep (ADR-004, 2026-08-03) -----------------------------------
# Mess must be self-announcing: the four failure classes that previously cost
# audit sessions (stale git locks, stale views, unfiled files, shadow copies)
# are detected here as WARNINGS — they nag, never block.
#
# Shadow roots live OUTSIDE the repository, resolved from the container that
# holds LearningOS/ (repo root's grandparent). Listing the Job root is a
# narrow, Aram-approved carve-out to the CLAUDE.md §13 quarantine: the sweep
# reads file NAMES and mtimes only, never content. Roots are optional — the
# repository stays location-independent.
SHADOW_ROOTS = (
    ("legacy", Path("legacy") / "Plans"),
    ("job-inputs", Path("Job") / "workspace-job-deem" / "inputs"),
)
STALE_LOCK_AGE_S = 600       # index.lock older than this = crashed git process
SHADOW_MTIME_SLACK_S = 120   # clock slack before a shadow counts as "newer"


def _in_garden(root: Path, path: Path) -> bool:
    garden = root.joinpath(*GARDEN_SUBTREE)
    return path == garden or garden in path.parents


def _in_quarantine(root: Path, path: Path) -> bool:
    """Normal validation never reads sealed prospective content."""
    quarantine = root / "curriculum" / "quarantine"
    return path == quarantine or quarantine in path.parents


@dataclass
class Issue:
    severity: str  # "E" | "W"
    code: str
    message: str
    path: str = ""

    def __str__(self) -> str:
        loc = f" [{self.path}]" if self.path else ""
        return f"{self.severity} {self.code}: {self.message}{loc}"


class Validator:
    def __init__(self, repo: Repo, online: bool = False):
        self.repo = repo
        self.online = online
        self.issues: list[Issue] = []
        self.schemas = self._load_schemas()

    # ------------------------------------------------------------------ util
    def err(self, code: str, msg: str, path: str = ""):
        self.issues.append(Issue("E", code, msg, path))

    def warn(self, code: str, msg: str, path: str = ""):
        self.issues.append(Issue("W", code, msg, path))

    def _load_schemas(self) -> dict:
        schema_dir = self.repo.root / "system" / "schema"
        schemas = {}
        for f in schema_dir.glob("*.schema.json"):
            schemas[f.stem.replace(".schema", "")] = json.loads(f.read_text(encoding="utf-8"))
        return schemas

    def _schema_check(self, name: str, instance, where: str):
        schema = self.schemas.get(name)
        if schema is None:
            self.err("SCHEMA-MISSING", f"no schema '{name}' in system/schema/", where)
            return
        validator = jsonschema.Draft202012Validator(schema)
        for e in sorted(validator.iter_errors(instance), key=str):
            locator = "/".join(str(p) for p in e.absolute_path)
            self.err("SCHEMA", f"{name}: {e.message} (at {locator or 'root'})", where)

    def _rel(self, p: Path) -> str:
        try:
            return str(p.relative_to(self.repo.root))
        except ValueError:
            return str(p)

    def _origin_for(self, family: str, rec_id: str) -> str:
        """Best-known originating file for a record.

        Registries may be partitioned (knowledge/concepts/*.yaml,
        sources/registry/*.yaml); the loader remembers which file each record
        came from. Diagnostics use this so they name the actual partition file
        instead of the consolidated default — otherwise an error about a concept
        defined in knowledge/concepts/ml.yaml would misleadingly point at
        knowledge/concepts.yaml.
        """
        r = self.repo
        if family == "concept":
            o = r.concept_origins.get(rec_id)
            return self._rel(o) if o else "knowledge/concepts.yaml"
        if family == "source":
            o = r.source_origins.get(rec_id)
            return self._rel(o) if o else "sources/sources.yaml"
        if family == "module":
            o = r.module_origins.get(rec_id)
            return self._rel(o) if o else "records/modules.yaml"
        if family == "program":
            p = r.programs.get(rec_id)
            return self._rel(p.path) if p else ""
        if family == "unit":
            u = r.units.get(rec_id)
            return self._rel(u.path) if u else ""
        if family == "study-map":
            sm = r.study_maps.get(rec_id)
            return self._rel(sm.path) if sm else ""
        if family == "note":
            n = r.notes.get(rec_id)
            return self._rel(n.path) if n else ""
        if family == "workspace":
            w = r.workspaces.get(rec_id)
            return self._rel(w.path) if w else ""
        return ""

    # ------------------------------------------------------------------ run
    def run(self) -> list[Issue]:
        self.check_parse_failures()
        self.check_schemas()
        self.check_identity()
        self.check_references()
        self.check_registries()
        self.check_collections()
        self.check_ownership()
        self.check_modules()
        self.check_curriculum()
        self.check_files()
        self.check_workspaces()
        self.check_learning_paths()
        self.check_study_maps()
        self.check_links()
        self.check_generated()
        self.check_hygiene()
        if self.online:
            self.check_external_urls()
        return self.issues

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
            self._schema_check("study-map", study_map.data, self._rel(study_map.path))
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
            for uid in ws.meta.get("unit_ids", []) or []:
                if uid not in r.units:
                    self.err("REF-UNIT", f"workspace '{ws.id}' references unknown unit '{uid}'", where)
        for mid, module in r.modules.items():
            where = self._origin_for("module", mid)
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

    def check_registries(self):
        r = self.repo
        seen_edges = set()
        for i, rel in enumerate(r.relations):
            rtype = rel.get("type")
            if rtype not in RELATION_TYPES:
                self.err("REL-TYPE", f"relation[{i}] type '{rtype}' is not one of the eight supported types",
                         "knowledge/concept-relations.yaml")
            edge = (rel.get("from"), rtype, rel.get("to"))
            if edge in seen_edges:
                self.err("REL-DUP", f"duplicate relation edge {edge}", "knowledge/concept-relations.yaml")
            seen_edges.add(edge)
        # Alias collisions. Normalize with strip().casefold() so that stray
        # whitespace or case ('Erwartungswert', ' erwartungswert ') still
        # collides; empty keys are ignored rather than colliding vacuously.
        alias_map: dict[str, list[str]] = {}
        for concept in r.concepts.values():
            cid = str(concept.get("id"))
            for alias in concept.get("aliases", []) or []:
                key = str(alias).strip().casefold()
                if key:
                    alias_map.setdefault(key, []).append(cid)
            label = str(concept.get("label", "")).strip().casefold()
            if label:
                alias_map.setdefault(label, []).append(cid)
        for key, owners in sorted(alias_map.items()):
            distinct = sorted(set(owners))
            if len(distinct) > 1:
                located = ", ".join(f"{oid} ({self._origin_for('concept', oid)})"
                                    for oid in distinct)
                self.warn("ALIAS-COLLISION",
                          f"alias/label '{key}' maps to multiple concepts: {located}")
        # Duplicate sources
        seen_ident: dict[tuple, str] = {}
        seen_url: dict[str, str] = {}
        for source in r.sources.values():
            sid = str(source.get("id"))
            key = (str(source.get("title", "")).casefold(),
                   tuple(a.casefold() for a in source.get("authors", []) or []))
            if key in seen_ident and key[0]:
                self.warn("SOURCE-DUP", f"sources '{seen_ident[key]}' and '{sid}' share title+authors")
            seen_ident.setdefault(key, sid)
            url = source.get("url")
            if url:
                if url in seen_url:
                    self.warn("SOURCE-DUP", f"sources '{seen_url[url]}' and '{sid}' share URL {url}")
                seen_url.setdefault(url, sid)

    def check_collections(self):
        """Collections (sources/collections/*.yaml) are curated lists OVER the
        registry: filename kebab-case, every entry resolves, no duplicates."""
        name_re = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
        for name, doc in self.repo.collections.items():
            where = f"sources/collections/{name}.yaml"
            if not name_re.match(name):
                self.err("COLLECTION-NAME",
                         f"collection filename '{name}' is not kebab-case", where)
            seen: set[str] = set()
            for i, entry in enumerate(doc.get("entries", []) or []):
                if not isinstance(entry, dict):
                    continue  # schema check reports the shape error
                sid = str(entry.get("source", ""))
                if sid and sid not in self.repo.sources:
                    self.err("COLLECTION-REF",
                             f"entries[{i}] references unknown source '{sid}'", where)
                if sid in seen:
                    self.warn("COLLECTION-DUP",
                              f"source '{sid}' listed more than once", where)
                seen.add(sid)

    def check_ownership(self):
        r = self.repo
        # No canonical file references generated/ as input
        for tree in CANONICAL_TREES:
            base = r.root / tree
            if not base.is_dir():
                continue
            for f in sorted(base.rglob("*")):
                if f.suffix.lower() not in (".md", ".yaml", ".yml") or not f.is_file():
                    continue
                if _in_garden(r.root, f) or _in_quarantine(r.root, f):
                    continue
                text = f.read_text(encoding="utf-8", errors="replace")
                # Only the repository's own generated/ tree counts — 'generated/'
                # inside URLs or longer paths (e.g. sklearn.org/modules/generated/)
                # must not be preceded by a slash or word character.
                if re.search(r"(?<![\w/])generated/", text):
                    self.err("GEN-INPUT",
                             "canonical file references 'generated/' — generated files are never inputs",
                             self._rel(f))
        # No file under generated/ tracked by git (except .gitkeep)
        tracked = self._git(["ls-files", "generated/"])
        for line in tracked.splitlines():
            if line.strip() and not line.strip().endswith(".gitkeep"):
                self.err("GEN-TRACKED", f"file under generated/ is tracked by Git: {line.strip()}")
        # COORDINATION: no exam-date duplication, no status restatements, only allowed sections
        if r.coordination is not None:
            attempt_dates = set()
            for module in r.modules.values():
                for att in module.get("attempts", []) or []:
                    if att.get("date"):
                        attempt_dates.add(str(att["date"]))
            body = r.coordination.body
            for date in ISO_DATE_RE.findall(body):
                if date in attempt_dates:
                    self.err("COORD-EXAM-DATE",
                             f"COORDINATION.md contains ISO date {date} equal to a modules.yaml "
                             "attempt date (exam dates are owned by records/modules.yaml)",
                             "work/COORDINATION.md")
            if re.search(r"^\s*status\s*:", body, re.MULTILINE | re.IGNORECASE):
                self.err("COORD-STATUS",
                         "COORDINATION.md restates workspace status (owned by workspace frontmatter)",
                         "work/COORDINATION.md")
            headings = re.findall(r"^##\s+(.+?)\s*$", body, re.MULTILINE)
            for h in headings:
                if h not in COORDINATION_SECTIONS:
                    self.err("COORD-SECTION",
                             f"COORDINATION.md contains unexpected section '{h}' "
                             f"(allowed: {', '.join(COORDINATION_SECTIONS)})",
                             "work/COORDINATION.md")
        # Crosswalk judgment-table heuristic (warning)
        for note in r.notes.values():
            if note.meta.get("role") != "crosswalk":
                continue
            for line in note.body.splitlines():
                if not line.lstrip().startswith("|"):
                    continue
                cells = {c.strip().casefold() for c in line.strip().strip("|").split("|")}
                if cells & JUDGMENT_HEADERS:
                    self.warn("CROSSWALK-TABLE",
                              f"crosswalk note '{note.id}' contains a Markdown table with evaluation "
                              "vocabulary headers — judgments belong in source records",
                              self._rel(note.path))
                    break

    def check_modules(self):
        for module in self.repo.modules.values():
            mid = module.get("id")
            attempts = module.get("attempts", []) or []
            # Coerce to str before comparing: the loader normalizes YAML dates to
            # ISO strings, but a bare-year int (date: 2026) would stay an int and
            # `sorted()` on mixed str/int raises TypeError. ISO-8601 strings sort
            # chronologically, so a uniform str view is a correct comparison key.
            dates = [str(a.get("date")) for a in attempts if a.get("date")]
            if dates != sorted(dates):
                self.err("MOD-ORDER", f"module '{mid}' attempt dates are not chronologically ordered",
                         "records/modules.yaml")
            for i, att in enumerate(attempts):
                if att.get("grade") is not None and att.get("result") != "passed" \
                        and module.get("status") != "completed":
                    self.err("MOD-GRADE",
                             f"module '{mid}' attempt[{i}] carries a grade but result is "
                             f"'{att.get('result')}' and module is not completed",
                             "records/modules.yaml")
                if att.get("result") == "registered" and i != len(attempts) - 1:
                    self.err("MOD-REGISTERED",
                             f"module '{mid}' attempt[{i}] is 'registered' but is not the latest attempt",
                             self._origin_for("module", str(mid)))

    def check_curriculum(self):
        """Cross-file invariants for the module-first operational tree."""
        r = self.repo
        if not r.programs and not r.units and not r.study_maps:
            return  # backward-compatible v1/synthetic repository
        defaults = [p.id for p in r.programs.values()
                    if p.data.get("default") and p.data.get("status") == "active"]
        if defaults != ["program-bachelors"]:
            self.err("PROGRAM-DEFAULT",
                     "the active/default program must be exactly program-bachelors",
                     "curriculum/programs")
        if "workspace-degree-planning" in r.workspaces:
            self.err("QUARANTINE-MASTERS",
                     "Master's Planning workspace is loaded as current work instead of quarantined",
                     self._origin_for("workspace", "workspace-degree-planning"))
        missing_legacy = sorted(set(r.legacy_modules) - set(r.modules))
        if missing_legacy:
            self.err("MODULE-MIGRATION",
                     "partitioned records do not cover legacy module ids: " + ", ".join(missing_legacy),
                     "records/modules.yaml")
        for mid, module in r.modules.items():
            where = self._origin_for("module", mid)
            if module.get("kind") == "academic":
                for field in ("institution", "semester"):
                    if not module.get(field):
                        self.err("MODULE-ACADEMIC", f"academic module '{mid}' lacks {field}", where)
            components = module.get("components", []) or []
            component_ids = [c.get("id") for c in components if isinstance(c, dict)]
            if len(component_ids) != len(set(component_ids)):
                self.err("COMPONENT-DUP", f"module '{mid}' has duplicate component ids", where)
            ordered = module.get("unit_order", []) or []
            actual = [u.id for u in r.units.values() if u.module_id == mid]
            if set(ordered) != set(actual) or len(ordered) != len(actual):
                self.err("UNIT-ORDER",
                         f"module '{mid}' unit_order must contain every owned unit exactly once",
                         where)
            source_map = r.module_source_maps.get(mid, {})
            joins = [(e.get("source_id"), e.get("role"))
                     for e in source_map.get("sources", []) or [] if isinstance(e, dict)]
            if len(joins) != len(set(joins)):
                self.err("SOURCE-MAP-DUP",
                         f"module '{mid}' repeats the same source-role join", where)
        for uid, unit in r.units.items():
            where = self._rel(unit.path)
            current = unit.data.get("current_study_map")
            owned = [sm.id for sm in r.study_maps.values() if sm.unit_id == uid]
            if len(owned) > 1:
                self.err("UNIT-MAP-MULTIPLE",
                         f"unit '{uid}' has more than one current study map: {owned}", where)
            if current and owned != [current]:
                self.err("UNIT-MAP-CURRENT",
                         f"unit '{uid}' current_study_map does not match its physical study map", where)
            if not current and owned:
                self.err("UNIT-MAP-UNDECLARED",
                         f"unit '{uid}' has a study-map.yaml but does not declare it", where)

    def check_study_maps(self):
        for study_map in self.repo.study_maps.values():
            where = self._rel(study_map.path)
            data = study_map.data
            stages = data.get("stages", []) or []
            if not isinstance(stages, list):
                continue
            ids = [s.get("id") for s in stages if isinstance(s, dict)]
            if len(ids) != len(set(ids)):
                self.err("MAP-STAGE-DUP", "study-map stage ids must be unique", where)
            current = data.get("current_stage")
            if current not in ids:
                self.err("MAP-CURRENT", f"current_stage '{current}' does not identify a stage", where)
            active = [s.get("id") for s in stages if isinstance(s, dict)
                      and s.get("status") == "active"]
            if data.get("status") == "active" and active != [current]:
                self.err("MAP-ACTIVE",
                         "an active study map must have exactly one active current stage", where)
            if data.get("status") != "active" and len(active) > 0:
                self.err("MAP-ACTIVE",
                         "a non-active study map may not contain an active stage", where)
            for stage in stages:
                if not isinstance(stage, dict):
                    continue
                note_ref = stage.get("working_note")
                if note_ref:
                    target = self.repo.root / str(note_ref)
                    expected_unit = study_map.path.parent.resolve()
                    try:
                        target.resolve().relative_to(expected_unit)
                    except (ValueError, OSError):
                        self.err("MAP-NOTE-OWNER",
                                 f"working note escapes owning unit: '{note_ref}'", where)
                    if not target.is_file():
                        self.err("MAP-NOTE-MISSING", f"working note does not exist: '{note_ref}'", where)
                if stage.get("completed") and stage.get("status") != "complete":
                    self.err("MAP-COMPLETED-DATE",
                             f"stage '{stage.get('id')}' has a completion date but is not complete", where)
            stage_ids = set(ids)
            detour_ids: set[str] = set()
            for detour in data.get("detours", []) or []:
                did = detour.get("id")
                if did in detour_ids:
                    self.err("DETOUR-DUP", f"duplicate detour id '{did}'", where)
                detour_ids.add(did)
                for field in ("spawned_by_stage", "return_to_stage"):
                    if detour.get(field) not in stage_ids:
                        self.err("DETOUR-STAGE",
                                 f"detour '{did}' {field} does not resolve to a stage", where)

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

    def check_workspaces(self):
        r = self.repo
        for ws in r.active_workspaces():
            where = self._rel(ws.path)
            for heading in REQUIRED_WORKSPACE_SECTIONS:
                if ws.section(heading) is None:
                    self.err("WS-SECTION",
                             f"workspace '{ws.id}' is missing required body section '## {heading}'",
                             where)
        non_standing = [w for w in r.active_workspaces() if not w.standing]
        if len(non_standing) > 7:
            self.warn("WS-COUNT",
                      f"{len(non_standing)} non-standing active workspaces (target 3-7; finish or "
                      "archive something first)")
        # Neglect signal: active non-standing workspace untouched (per Git) for 21+ days
        for ws in non_standing:
            ts = self._git_last_commit_ts(ws.path.parent)
            if ts is None:
                continue
            days = (time.time() - ts) / 86400
            if days >= 21:
                self.warn("WS-NEGLECT",
                          f"workspace '{ws.id}' untouched for {int(days)} days (per Git)")

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

    def check_generated(self):
        gen = self.repo.root / "generated"
        if not gen.is_dir():
            return
        for f in sorted(gen.iterdir()):
            if f.name == "reports":
                continue
            if f.is_file() and f.name not in GENERATED_ALLOWED:
                self.err("GEN-UNKNOWN",
                         f"unexpected file in generated/: {f.name} (agent-computed artifacts "
                         "live in workspaces, never in generated/)")
        reports = gen / "reports"
        if reports.is_dir():
            for f in sorted(reports.iterdir()):
                if f.is_file() and not f.name.startswith(GENERATED_REPORT_PREFIXES):
                    self.err("GEN-UNKNOWN", f"unexpected file in generated/reports/: {f.name}")
        # Generated warning headers
        for f in sorted(gen.rglob("*.md")):
            head = f.read_text(encoding="utf-8", errors="replace")[:400]
            if "GENERATED" not in head:
                self.err("GEN-HEADER", f"generated file lacks a generated-file warning header",
                         self._rel(f))
        for f in sorted(gen.rglob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                self.err("GEN-JSON", "generated JSON does not parse", self._rel(f))
                continue
            if isinstance(data, dict) and "_generated" not in data:
                self.err("GEN-HEADER", "generated JSON lacks the '_generated' warning key",
                         self._rel(f))
        # Archived workspaces excluded from generated indexes
        archived_ids = [w.id for w in self.repo.archived_workspaces()]
        for name in ("concept-index.md", "source-index.md"):
            f = gen / name
            if f.exists():
                text = f.read_text(encoding="utf-8", errors="replace")
                for wid in archived_ids:
                    if wid in text:
                        self.err("GEN-ARCHIVED",
                                 f"archived workspace '{wid}' appears in generated/{name}")

    def check_learning_paths(self):
        """Ordered-stage invariants that JSON Schema cannot express cleanly."""
        for learning_path in self.repo.learning_paths.values():
            where = self._rel(learning_path.path)
            data = learning_path.data
            stages = data.get("stages", []) or []
            if not isinstance(stages, list):
                continue  # schema reports the structural error
            ids = [s.get("id") for s in stages if isinstance(s, dict)]
            if len(ids) != len(set(ids)):
                self.err("PATH-STAGE-DUP", "learning path stage ids must be unique", where)
            current = data.get("current_stage")
            if current not in ids:
                self.err("PATH-CURRENT",
                         f"current_stage '{current}' does not identify a stage", where)
            active = [s.get("id") for s in stages if isinstance(s, dict)
                      and s.get("status") == "active"]
            if data.get("status") == "active":
                if active != [current]:
                    self.err("PATH-ACTIVE",
                             "an active path must have exactly one active stage, equal to current_stage",
                             where)
            elif len(active) > 1:
                self.err("PATH-ACTIVE", "a path may not have multiple active stages", where)
            for stage in stages:
                if not isinstance(stage, dict):
                    continue
                note_path = stage.get("notes_path")
                if note_path:
                    target = self.repo.root / str(note_path)
                    try:
                        target.resolve().relative_to(learning_path.path.parent.parent.resolve())
                    except (ValueError, OSError):
                        self.err("PATH-NOTE-OWNER",
                                 f"stage notes_path escapes owning workspace: '{note_path}'",
                                 where)
            proposal = (data.get("shelving") or {}).get("proposal_path") \
                if isinstance(data.get("shelving") or {}, dict) else None
            if proposal:
                target = self.repo.root / str(proposal)
                try:
                    target.resolve().relative_to(learning_path.path.parent.parent.resolve())
                except (ValueError, OSError):
                    self.err("PATH-SHELVE-OWNER",
                             f"shelving proposal escapes owning workspace: '{proposal}'",
                             where)

    def check_external_urls(self):
        import urllib.request
        urls = set()
        for source in self.repo.sources.values():
            if source.get("url"):
                urls.add(source["url"])
        for tree in CANONICAL_TREES:
            base = self.repo.root / tree
            if not base.is_dir():
                continue
            for f in base.rglob("*.md"):
                if _in_garden(self.repo.root, f) or _in_quarantine(self.repo.root, f):
                    continue
                for target in MD_LINK_RE.findall(f.read_text(encoding="utf-8", errors="replace")):
                    if target.startswith(("http://", "https://")):
                        urls.add(target)
        for url in sorted(urls):
            try:
                req = urllib.request.Request(url, method="HEAD",
                                             headers={"User-Agent": "learning-os-validate/0.1"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status >= 400:
                        self.warn("URL-UNREACHABLE", f"{url} -> HTTP {resp.status}")
            except Exception as exc:  # noqa: BLE001 - report, never block
                self.warn("URL-UNREACHABLE", f"{url} -> {exc.__class__.__name__}")

    # ------------------------------------------------------- hygiene (ADR-004)
    def check_hygiene(self):
        """Self-announcing mess detection. Warnings only — nags, never blocks."""
        self._hygiene_stale_locks()
        self._hygiene_stale_views()
        self._hygiene_unfiled()
        self._hygiene_shadow_copies()

    def _hygiene_stale_locks(self):
        # The repository's own .git plus the container repo above it (if any).
        candidates = [self.repo.root / ".git" / "index.lock"]
        container = self.repo.root.parent.parent
        if (container / ".git").is_dir():
            candidates.append(container / ".git" / "index.lock")
        now = time.time()
        for lock in candidates:
            try:
                if lock.is_file() and now - lock.stat().st_mtime > STALE_LOCK_AGE_S:
                    self.warn("HYGIENE-LOCK",
                              "stale git index.lock (crashed git process) — commits are "
                              f"silently blocked until it is removed: rm '{lock}'")
            except OSError:
                continue

    def _hygiene_stale_views(self):
        manifest = self.repo.root / "generated" / "manifest.json"
        if not manifest.is_file():
            # Synthetic/portable trees without Git history are valid before
            # their first projection. A real checkout should always publish.
            if not self._git(["log", "-1", "--format=%H"]).strip():
                return
            self.warn("HYGIENE-VIEWS",
                      "generated/ views absent — run `make views` (they are disposable, "
                      "but the human-fallback path depends on them)")
            return
        try:
            from .genout import _source_fingerprint
            data = json.loads(manifest.read_text(encoding="utf-8"))
            projected = (data.get("_generated") or {}).get("source_fingerprint")
            current = _source_fingerprint(self.repo)
        except (OSError, json.JSONDecodeError):
            projected, current = None, "unreadable"
        if projected != current:
            self.warn("HYGIENE-VIEWS",
                      "generated/manifest.json is not the current authored snapshot — "
                      "run `make views`",
                      "generated/manifest.json")

    def _hygiene_unfiled(self):
        root = self.repo.root

        def flag(p: Path, hint: str):
            self.warn("HYGIENE-UNFILED",
                      f"loose Markdown file — {hint} (drop-anything home: work/inbox/)",
                      self._rel(p))

        for p in root.glob("*.md"):
            if p.name not in {"README.md", "CLAUDE.md", "AGENTS.md"}:
                flag(p, "repository root is not a filing location")
        for p in (root / "knowledge").glob("*.md"):
            flag(p, "notes belong in knowledge/notes/<domain>/")
        for p in (root / "knowledge" / "notes").glob("*.md"):
            flag(p, "note is outside a domain bucket")
        for p in (root / "work").glob("*.md"):
            if p.name != "COORDINATION.md":
                flag(p, "work/ root holds only COORDINATION.md")
        for tree in ("records", "sources"):
            for p in (root / tree).rglob("*.md"):
                flag(p, f"{tree}/ holds registries (YAML), not Markdown")
        active = root / "work" / "active"
        if active.is_dir():
            for ws in active.iterdir():
                if ws.is_dir():
                    for p in ws.glob("*.md"):
                        if p.name != "CONTEXT.md":
                            flag(p, "file beside CONTEXT.md — belongs in scratch/, "
                                    "inputs/ or outputs/")

    @staticmethod
    def _shadow_key(name: str) -> str:
        stem = name.rsplit(".", 1)[0].lower().replace("_", "-").replace(" ", "-")
        return stem.removeprefix("note-")

    def _hygiene_shadow_copies(self):
        container = self.repo.root.parent.parent
        canon: dict[str, tuple[str, Path]] = {}
        for note in self.repo.notes.values():
            canon[self._shadow_key(note.path.name)] = (
                note.meta.get("id", note.path.stem), note.path)
        for label, rel in SHADOW_ROOTS:
            shadow_root = container / rel
            if not shadow_root.is_dir():
                continue
            for p in shadow_root.rglob("*.md"):  # names + mtimes only, never content
                hit = canon.get(self._shadow_key(p.name))
                if hit is None:
                    continue
                note_id, note_path = hit
                canon_ts = note_path.stat().st_mtime
                commit_ts = self._git_last_commit_ts(note_path)
                if commit_ts:
                    canon_ts = max(canon_ts, commit_ts)
                if p.stat().st_mtime > canon_ts + SHADOW_MTIME_SLACK_S:
                    self.warn("HYGIENE-SHADOW",
                              f"shadow copy in {label}/ edited after canonical note "
                              f"'{note_id}' — the canon is the live copy; merge the "
                              f"delta there and re-freeze the shadow: {p}")

    # ------------------------------------------------------------------ git
    def _git(self, args: list[str]) -> str:
        try:
            out = subprocess.run(["git", *args], cwd=self.repo.root, capture_output=True,
                                 text=True, timeout=30)
            return out.stdout
        except Exception:  # noqa: BLE001
            return ""

    def _git_last_commit_ts(self, path: Path) -> float | None:
        out = self._git(["log", "-1", "--format=%ct", "--", str(path.relative_to(self.repo.root))])
        out = out.strip()
        return float(out) if out else None


def validate(repo: Repo, online: bool = False) -> list[Issue]:
    return Validator(repo, online=online).run()


def render_report(issues: list[Issue], generated_at: str) -> str:
    errors = [i for i in issues if i.severity == "E"]
    warnings = [i for i in issues if i.severity == "W"]
    lines = [
        "# Validation report",
        "",
        "> ⚠️ GENERATED file — do not edit. Rebuilt by `python tools/validate.py` "
        "from canonical inputs (knowledge/, sources/, records/, work/).",
        f"> Generated: {generated_at}",
        "",
        f"**Errors: {len(errors)} · Warnings: {len(warnings)}**",
        "",
    ]
    if errors:
        lines.append("## Errors")
        lines.append("")
        lines.extend(f"- {i}" for i in errors)
        lines.append("")
    if warnings:
        lines.append("## Warnings")
        lines.append("")
        lines.extend(f"- {i}" for i in warnings)
        lines.append("")
    if not issues:
        lines.append("No issues found.")
        lines.append("")
    return "\n".join(lines)
