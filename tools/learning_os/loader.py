"""Single internal loader API for Learning OS v3 (BUILD-SPEC Step 3).

Supports consolidated AND partitioned registries (the logical model must not
depend on registry partitioning):
  - concepts:  knowledge/concepts.yaml            or knowledge/concepts/*.yaml
  - relations: knowledge/concept-relations.yaml   or knowledge/concept-relations/*.yaml
  - sources:   sources/sources.yaml               or sources/registry/*.yaml
  - collections: sources/collections/*.yaml       (one curated list per file)
  - modules:   records/modules.yaml
  - notes:     knowledge/notes/**/*.md            (Markdown frontmatter)
  - garden:    knowledge/garden/**/*.md           (free-form, no schema — §14)
  - workspaces: work/active/*/CONTEXT.md, archive/workspaces/*/*/CONTEXT.md
  - coordination: work/COORDINATION.md
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)

ID_RE = re.compile(r"^(note|concept|source|workspace|module)-[a-z0-9]+(?:-[a-z0-9]+)*$")

# Inline #tags in Garden notes (CLAUDE.md §14). Conservative: a tag starts with
# a lowercase letter (so ATX headings "# H", shebangs, "#1" issue refs and hex
# colours like #Fff are not tags) and may contain lowercase letters, digits,
# hyphens and underscores. It must not follow a word char, "#", "/" or "&" (so
# "##x", "path/#anchor" and HTML entities are skipped).
GARDEN_TAG_RE = re.compile(r"(?<![\w#/&])#([a-z][a-z0-9_-]*)")

# Strip fenced (``` … ```) and inline (`…`) code before pulling #tags, so a
# hashtag written as code — e.g. `#tags` in prose, or a `#include` in a snippet —
# is not mistaken for a tag.
_CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`[^`]*`")


def _strip_code(text: str) -> str:
    return _INLINE_CODE_RE.sub(" ", _CODE_FENCE_RE.sub(" ", text))


RELATION_TYPES = {
    "requires", "builds-on", "derives", "generalizes",
    "contrasts-with", "equivalent-to", "applies-in", "motivates",
}

# Direction and meaning of every relation type. Each edge is read "from <TYPE>
# to": `from` is the subject, `to` is the object. This is the single canonical
# statement of relation semantics (mirrored in the concept-relations schema
# description); tools that reason over the graph must follow it.
#   requires        from needs to as a hard prerequisite (learn `to` first)
#   builds-on       from extends/depends on to (softer prerequisite than requires)
#   derives         from is derived/obtained from to
#   generalizes     from is the more general case; to is the special case
#   contrasts-with  symmetric: from and to are usefully compared/opposed
#   equivalent-to   symmetric: from and to denote the same idea in different guises
#   applies-in      from is applied within the context/domain to
#   motivates       from provides the motivation for to
# `requires` and `builds-on` are the only prerequisite edges (they define study
# order — see tools/learning_os/genout.py PREREQ_TYPES). The remaining six are
# context, never prerequisites. `contrasts-with` and `equivalent-to` are
# symmetric in meaning; the others are directional.
RELATION_SEMANTICS = {
    "requires": "from needs to as a hard prerequisite",
    "builds-on": "from extends/depends on to (soft prerequisite)",
    "derives": "from is derived from to",
    "generalizes": "from is the general case, to the special case",
    "contrasts-with": "symmetric: usefully compared/opposed",
    "equivalent-to": "symmetric: same idea, different guise",
    "applies-in": "from is applied within the context/domain to",
    "motivates": "from provides the motivation for to",
}
PREREQUISITE_RELATIONS = ("requires", "builds-on")
SYMMETRIC_RELATIONS = ("contrasts-with", "equivalent-to")

NOTE_ROLES = {
    "synthesis", "reference", "derivation", "exercise-bank",
    "mock-exam", "implementation", "question", "crosswalk",
}

EVIDENCE_SCHEMES = (
    "note://", "source://", "concept://", "workspace://",
    "material://", "project://", "github://", "https://", "http://",
)


class LoaderError(Exception):
    """Raised when a file cannot be parsed at all (structural failure)."""


def _normalize(value):
    """YAML 1.1 auto-parses ISO dates; the schemas expect strings. Normalize
    recursively so the logical model is representation-independent."""
    import datetime as _dt
    if isinstance(value, (_dt.date, _dt.datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _normalize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize(v) for v in value]
    return value


def parse_frontmatter(text: str, path: Path) -> tuple[dict, str]:
    """Return (frontmatter dict, body) for a Markdown file."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as exc:  # pragma: no cover - surfaced as issue upstream
        raise LoaderError(f"{path}: invalid YAML frontmatter: {exc}") from exc
    if not isinstance(meta, dict):
        raise LoaderError(f"{path}: frontmatter is not a mapping")
    return _normalize(meta), text[m.end():]


def _load_yaml(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise LoaderError(f"{path}: invalid YAML: {exc}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise LoaderError(f"{path}: top level must be a mapping")
    return _normalize(data)


def _load_registry(
    consolidated: Path, partition_dir: Path, key: str
) -> tuple[list, list[Path], list[tuple[Path, str]]]:
    """Load a registry from its consolidated file and/or partition directory.

    Defensive (never assumes document shape): a malformed file or item is
    reported as a failure and skipped instead of crashing the load or letting
    non-mapping records into the model.
    """
    records: list = []
    origins: list[Path] = []
    failures: list[tuple[Path, str]] = []
    candidates: list[Path] = []
    if consolidated.exists():
        candidates.append(consolidated)
    if partition_dir.is_dir():
        candidates.extend(sorted(partition_dir.glob("*.yaml")))
    for f in candidates:
        try:
            data = _load_yaml(f)
        except LoaderError as exc:
            failures.append((f, str(exc)))
            continue
        items = data.get(key, [])
        if items is None:
            items = []
        if not isinstance(items, list):
            failures.append((f, f"{f}: '{key}' must be a list"))
            continue
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                failures.append((f, f"{f}: {key}[{i}] is not a mapping — skipped"))
                continue
            records.append(item)
            origins.append(f)
    return records, origins, failures


def _record_id(rec: dict) -> str | None:
    """The record's id if it is a non-empty string, else None (reject empties)."""
    rid = rec.get("id")
    if isinstance(rid, str) and rid.strip():
        return rid
    return None


def md_section(body: str, heading: str) -> str | None:
    """Return the text of a `## <heading>` body section, if present.

    Single implementation of Markdown ``## heading`` section extraction, shared
    by Workspace, Coordination, and the validator (previously duplicated in
    three places). A section runs from its heading to the next `## ` heading or
    end of document.
    """
    pattern = re.compile(
        rf"^##\s+{re.escape(heading)}\s*$(.*?)(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(body)
    return m.group(1).strip() if m else None


@dataclass
class Note:
    id: str
    path: Path
    meta: dict
    body: str


@dataclass
class GardenNote:
    """A free-form note in knowledge/garden/ (CLAUDE.md §14). Deliberately has
    NO schema, NO required frontmatter, and is invisible to the validator and to
    repo.notes. `tags` are the inline #tags pulled from the body. Nothing here is
    canonical until it is Harvested into knowledge/notes/."""
    path: Path
    body: str
    tags: list[str] = field(default_factory=list)

    @property
    def slug(self) -> str:
        return self.path.stem

    @property
    def title(self) -> str:
        """First Markdown H1, else first non-empty line, else the filename."""
        for line in self.body.splitlines():
            s = line.strip()
            if s.startswith("# "):
                return s[2:].strip()
        for line in self.body.splitlines():
            s = line.strip()
            if s:
                return s.lstrip("#").strip() or self.slug
        return self.slug


@dataclass
class Workspace:
    id: str
    path: Path
    meta: dict
    body: str
    archived: bool = False

    @property
    def standing(self) -> bool:
        return bool(self.meta.get("standing", False))

    @property
    def status(self) -> str:
        return str(self.meta.get("status", ""))

    def section(self, heading: str) -> str | None:
        """Return the text of a `## <heading>` body section, if present."""
        return md_section(self.body, heading)


@dataclass
class Coordination:
    path: Path
    meta: dict
    body: str

    def section(self, heading: str) -> str | None:
        return md_section(self.body, heading)


@dataclass
class Repo:
    root: Path
    concepts: dict[str, dict] = field(default_factory=dict)
    concept_origins: dict[str, Path] = field(default_factory=dict)
    relations: list[dict] = field(default_factory=list)
    sources: dict[str, dict] = field(default_factory=dict)
    source_origins: dict[str, Path] = field(default_factory=dict)
    collections: dict[str, dict] = field(default_factory=dict)
    collection_origins: dict[str, Path] = field(default_factory=dict)
    modules: dict[str, dict] = field(default_factory=dict)
    notes: dict[str, Note] = field(default_factory=dict)
    garden_notes: list[GardenNote] = field(default_factory=list)
    workspaces: dict[str, Workspace] = field(default_factory=dict)
    coordination: Coordination | None = None
    duplicate_ids: list[tuple[str, str, Path]] = field(default_factory=list)
    parse_failures: list[tuple[Path, str]] = field(default_factory=list)

    # -- convenience -------------------------------------------------------
    @property
    def learningos_root(self) -> Path:
        """LearningOS/ root (parent of the repository)."""
        return self.root.parent

    @property
    def materials_root(self) -> Path:
        # materials/.flat/ holds one source-<id> symlink per source folder,
        # maintained by tools/build_materials_tree.py; when present it is the
        # resolution root so material:// URIs stay id-based while the physical
        # layout is the human topic tree (amendment of Jul 17 2026).
        materials = self.learningos_root / "materials"
        flat = materials / ".flat"
        return flat if flat.is_dir() else materials

    @property
    def projects_root(self) -> Path:
        return self.learningos_root / "projects"

    def active_workspaces(self) -> list[Workspace]:
        return [w for w in self.workspaces.values() if not w.archived]

    def archived_workspaces(self) -> list[Workspace]:
        return [w for w in self.workspaces.values() if w.archived]


def _register(repo: Repo, family: dict, rec_id: str, record, origin: Path, family_name: str):
    if rec_id in family:
        repo.duplicate_ids.append((family_name, rec_id, origin))
        return
    family[rec_id] = record


def load_repo(root: Path | str) -> Repo:
    root = Path(root).resolve()
    repo = Repo(root=root)

    # Concepts (consolidated or partitioned)
    records, origins, failures = _load_registry(
        root / "knowledge" / "concepts.yaml", root / "knowledge" / "concepts", "concepts"
    )
    repo.parse_failures.extend(failures)
    for rec, origin in zip(records, origins):
        cid = _record_id(rec)
        if cid is None:
            repo.parse_failures.append(
                (origin, f"{origin}: concept record with missing or empty id — skipped"))
            continue
        _register(repo, repo.concepts, cid, rec, origin, "concept")
        repo.concept_origins.setdefault(cid, origin)

    # Relations (consolidated or partitioned)
    records, _, failures = _load_registry(
        root / "knowledge" / "concept-relations.yaml",
        root / "knowledge" / "concept-relations",
        "relations",
    )
    repo.parse_failures.extend(failures)
    repo.relations = records

    # Sources (consolidated or partitioned)
    records, origins, failures = _load_registry(
        root / "sources" / "sources.yaml", root / "sources" / "registry", "sources"
    )
    repo.parse_failures.extend(failures)
    for rec, origin in zip(records, origins):
        sid = _record_id(rec)
        if sid is None:
            repo.parse_failures.append(
                (origin, f"{origin}: source record with missing or empty id — skipped"))
            continue
        _register(repo, repo.sources, sid, rec, origin, "source")
        repo.source_origins.setdefault(sid, origin)

    # Source collections (curated reading lists): one collection per file,
    # identity = kebab-case filename stem (ARCHITECTURE §3.3)
    collections_dir = root / "sources" / "collections"
    if collections_dir.is_dir():
        for f in sorted(collections_dir.glob("*.yaml")):
            try:
                doc = _load_yaml(f)
            except LoaderError as exc:
                repo.parse_failures.append((f, str(exc)))
                continue
            entries = doc.get("entries")
            if entries is not None and not isinstance(entries, list):
                repo.parse_failures.append(
                    (f, f"{f}: 'entries' must be a list — collection skipped"))
                continue
            repo.collections[f.stem] = doc
            repo.collection_origins[f.stem] = f

    # Modules
    modules_file = root / "records" / "modules.yaml"
    if modules_file.exists():
        try:
            data = _load_yaml(modules_file)
        except LoaderError as exc:
            repo.parse_failures.append((modules_file, str(exc)))
            data = {}
        items = data.get("modules", [])
        if items is None:
            items = []
        if not isinstance(items, list):
            repo.parse_failures.append(
                (modules_file, f"{modules_file}: 'modules' must be a list"))
            items = []
        for i, rec in enumerate(items):
            if not isinstance(rec, dict):
                repo.parse_failures.append(
                    (modules_file, f"{modules_file}: modules[{i}] is not a mapping — skipped"))
                continue
            mid = _record_id(rec)
            if mid is None:
                repo.parse_failures.append(
                    (modules_file,
                     f"{modules_file}: module record with missing or empty id — skipped"))
                continue
            _register(repo, repo.modules, mid, rec, modules_file, "module")

    # Notes
    notes_dir = root / "knowledge" / "notes"
    if notes_dir.is_dir():
        for f in sorted(notes_dir.rglob("*.md")):
            try:
                meta, body = parse_frontmatter(f.read_text(encoding="utf-8"), f)
            except LoaderError as exc:
                repo.parse_failures.append((f, str(exc)))
                continue
            if "id" in meta and _record_id(meta) is None:
                repo.parse_failures.append(
                    (f, f"{f}: note frontmatter id is empty or not a string — skipped"))
                continue
            nid = str(meta.get("id", f.stem))
            note = Note(id=nid, path=f, meta=meta, body=body)
            _register(repo, repo.notes, nid, note, f, "note")

    # Garden (exploratory layer — CLAUDE.md §14). Free-form Markdown in
    # knowledge/garden/: NO frontmatter schema, NOT registered as notes, and
    # skipped by the validator (see rules.py _in_garden). We only read the body
    # and pull inline #tags so the Nebula view can group them. README, dot- and
    # underscore-files are treated as meta and excluded from the idea list.
    garden_dir = root / "knowledge" / "garden"
    if garden_dir.is_dir():
        for f in sorted(garden_dir.rglob("*.md")):
            if f.name.startswith((".", "_")) or f.stem.lower() == "readme":
                continue
            text = f.read_text(encoding="utf-8", errors="replace")
            tags = sorted(set(GARDEN_TAG_RE.findall(_strip_code(text))))
            repo.garden_notes.append(GardenNote(path=f, body=text, tags=tags))

    # Workspaces: active + archived. Active workspaces sit exactly one level
    # under work/active/ (a workspace is a single directory). Archived
    # workspaces may be filed under an arbitrary bucketing (by year, by
    # year/quarter, …), so their CONTEXT.md is discovered at any depth rather
    # than assuming a fixed archive/workspaces/<year>/<ws>/ layout.
    for base, archived in ((root / "work" / "active", False),
                           (root / "archive" / "workspaces", True)):
        if not base.is_dir():
            continue
        found = base.rglob("CONTEXT.md") if archived else base.glob("*/CONTEXT.md")
        for f in sorted(found):
            try:
                meta, body = parse_frontmatter(f.read_text(encoding="utf-8"), f)
            except LoaderError as exc:
                repo.parse_failures.append((f, str(exc)))
                continue
            if "id" in meta and _record_id(meta) is None:
                repo.parse_failures.append(
                    (f, f"{f}: workspace frontmatter id is empty or not a string — skipped"))
                continue
            wid = str(meta.get("id", f.parent.name))
            ws = Workspace(id=wid, path=f, meta=meta, body=body, archived=archived)
            _register(repo, repo.workspaces, wid, ws, f, "workspace")

    # Coordination
    coord_file = root / "work" / "COORDINATION.md"
    if coord_file.exists():
        try:
            meta, body = parse_frontmatter(coord_file.read_text(encoding="utf-8"), coord_file)
            repo.coordination = Coordination(path=coord_file, meta=meta, body=body)
        except LoaderError as exc:
            repo.parse_failures.append((coord_file, str(exc)))

    return repo
