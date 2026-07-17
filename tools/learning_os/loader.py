"""Single internal loader API for Learning OS v3 (BUILD-SPEC Step 3).

Supports consolidated AND partitioned registries (the logical model must not
depend on registry partitioning):
  - concepts:  knowledge/concepts.yaml            or knowledge/concepts/*.yaml
  - relations: knowledge/concept-relations.yaml   or knowledge/concept-relations/*.yaml
  - sources:   sources/sources.yaml               or sources/registry/*.yaml
  - collections: sources/collections/*.yaml       (one curated list per file)
  - modules:   records/modules.yaml
  - notes:     knowledge/notes/**/*.md            (Markdown frontmatter)
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

RELATION_TYPES = {
    "requires", "builds-on", "derives", "generalizes",
    "contrasts-with", "equivalent-to", "applies-in", "motivates",
}

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


def _load_registry(consolidated: Path, partition_dir: Path, key: str) -> tuple[list, list[Path]]:
    """Load a registry from its consolidated file and/or partition directory."""
    records: list = []
    origins: list[Path] = []
    candidates: list[Path] = []
    if consolidated.exists():
        candidates.append(consolidated)
    if partition_dir.is_dir():
        candidates.extend(sorted(partition_dir.glob("*.yaml")))
    for f in candidates:
        data = _load_yaml(f)
        items = data.get(key, [])
        if not isinstance(items, list):
            raise LoaderError(f"{f}: '{key}' must be a list")
        for item in items:
            records.append(item)
            origins.append(f)
    return records, origins


@dataclass
class Note:
    id: str
    path: Path
    meta: dict
    body: str


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
        pattern = re.compile(
            rf"^##\s+{re.escape(heading)}\s*$(.*?)(?=^##\s|\Z)",
            re.MULTILINE | re.DOTALL,
        )
        m = pattern.search(self.body)
        return m.group(1).strip() if m else None


@dataclass
class Coordination:
    path: Path
    meta: dict
    body: str

    def section(self, heading: str) -> str | None:
        pattern = re.compile(
            rf"^##\s+{re.escape(heading)}\s*$(.*?)(?=^##\s|\Z)",
            re.MULTILINE | re.DOTALL,
        )
        m = pattern.search(self.body)
        return m.group(1).strip() if m else None


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
    records, origins = _load_registry(
        root / "knowledge" / "concepts.yaml", root / "knowledge" / "concepts", "concepts"
    )
    for rec, origin in zip(records, origins):
        cid = str(rec.get("id", ""))
        _register(repo, repo.concepts, cid, rec, origin, "concept")
        repo.concept_origins.setdefault(cid, origin)

    # Relations (consolidated or partitioned)
    records, _ = _load_registry(
        root / "knowledge" / "concept-relations.yaml",
        root / "knowledge" / "concept-relations",
        "relations",
    )
    repo.relations = records

    # Sources (consolidated or partitioned)
    records, origins = _load_registry(
        root / "sources" / "sources.yaml", root / "sources" / "registry", "sources"
    )
    for rec, origin in zip(records, origins):
        sid = str(rec.get("id", ""))
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
            repo.collections[f.stem] = doc
            repo.collection_origins[f.stem] = f

    # Modules
    modules_file = root / "records" / "modules.yaml"
    if modules_file.exists():
        data = _load_yaml(modules_file)
        for rec in data.get("modules", []) or []:
            mid = str(rec.get("id", ""))
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
            nid = str(meta.get("id", f.stem))
            note = Note(id=nid, path=f, meta=meta, body=body)
            _register(repo, repo.notes, nid, note, f, "note")

    # Workspaces: active + archived
    for base, archived in ((root / "work" / "active", False),
                           (root / "archive" / "workspaces", True)):
        if not base.is_dir():
            continue
        pattern = "*/CONTEXT.md" if not archived else "*/*/CONTEXT.md"
        for f in sorted(base.glob(pattern)):
            try:
                meta, body = parse_frontmatter(f.read_text(encoding="utf-8"), f)
            except LoaderError as exc:
                repo.parse_failures.append((f, str(exc)))
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
