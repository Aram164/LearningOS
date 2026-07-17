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
    RELATION_TYPES,
    Repo,
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
    "backlinks.json", ".gitkeep",
    ".DS_Store",  # OS metadata noise, gitignored — not an agent artifact
}
GENERATED_REPORT_PREFIXES = ("validation-report", "health")

CANONICAL_TREES = ("knowledge", "sources", "records", "work")

# File extensions that are legitimately authored text under knowledge/ (notes and
# registries). Anything else there (PDFs, slides, images) is a misplaced binary
# — see BINARY-IN-KNOWLEDGE. (Formerly the misleadingly named IMAGE_OK.)
KNOWLEDGE_TEXT_SUFFIXES = {".md", ".yaml", ".yml"}


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
            return "records/modules.yaml"
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
        self.check_files()
        self.check_workspaces()
        self.check_links()
        self.check_generated()
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
        self._schema_check("modules", {"modules": list(r.modules.values())},
                           "records/modules.yaml")
        for note in r.notes.values():
            self._schema_check("note", note.meta, self._rel(note.path))
        for ws in r.workspaces.values():
            self._schema_check("workspace", ws.meta, self._rel(ws.path))
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
                if wid not in r.workspaces:
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
            if ref[len("workspace://"):] not in r.workspaces:
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
                             "records/modules.yaml")

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
