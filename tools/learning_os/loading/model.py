"""The logical model one ``load_repo`` walk produces.

``Repo`` is the shared result every domain loader contributes to, so it lives
here rather than inside any one of them. It is a description of what the
repository contains, never of where the bytes came from — the only
path-shaped members are origins, kept so a validator can point at the file it
is complaining about.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .yamlio import md_section


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
class LearningPath:
    """A temporary, ordered route through one subtopic.

    Learning paths are operational state owned by a workspace. They are not a
    second knowledge graph: stage notes remain scratch until the operator and
    learner approve a shelving proposal.
    """
    id: str
    path: Path
    data: dict
    workspace_id: str
    archived: bool = False

    @property
    def title(self) -> str:
        return str(self.data.get("title", self.id))

    @property
    def status(self) -> str:
        return str(self.data.get("status", ""))

    @property
    def current_stage(self) -> str:
        return str(self.data.get("current_stage", ""))


@dataclass
class Program:
    """A top-level academic program, active area, or boundary card."""
    id: str
    path: Path
    data: dict


@dataclass
class Unit:
    """A module-owned lecture, topic, cluster, milestone, exam block, or bridge."""
    id: str
    path: Path
    data: dict
    module_id: str


@dataclass
class StudyMap:
    """The single current ordered study script owned by one curriculum unit."""
    id: str
    path: Path
    data: dict
    module_id: str
    unit_id: str


@dataclass
class Project:
    """A first-class thesis, research, software, writing, or other project."""
    id: str
    path: Path
    data: dict


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
    thematic_groups: dict[str, dict] = field(default_factory=dict)
    thematic_groups_path: Path | None = None
    topics: dict[str, dict] = field(default_factory=dict)
    topics_path: Path | None = None
    projects: dict[str, Project] = field(default_factory=dict)
    project_origins: dict[str, Path] = field(default_factory=dict)
    project_aliases: dict[str, str] = field(default_factory=dict)
    project_aliases_path: Path | None = None
    project_relations: list[dict] = field(default_factory=list)
    project_relations_path: Path | None = None
    programs: dict[str, Program] = field(default_factory=dict)
    modules: dict[str, dict] = field(default_factory=dict)
    module_origins: dict[str, Path] = field(default_factory=dict)
    legacy_modules: dict[str, dict] = field(default_factory=dict)
    module_source_maps: dict[str, dict] = field(default_factory=dict)
    module_source_map_origins: dict[str, Path] = field(default_factory=dict)
    units: dict[str, Unit] = field(default_factory=dict)
    study_maps: dict[str, StudyMap] = field(default_factory=dict)
    resume_pointer: dict | None = None
    resume_pointer_path: Path | None = None
    quarantined_workspace_ids: set[str] = field(default_factory=set)
    notes: dict[str, Note] = field(default_factory=dict)
    garden_notes: list[GardenNote] = field(default_factory=list)
    workspaces: dict[str, Workspace] = field(default_factory=dict)
    learning_paths: dict[str, LearningPath] = field(default_factory=dict)
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
        """External project working trees addressed by ``project://`` URIs."""
        return self.learningos_root / "projects"

    @property
    def project_registry_root(self) -> Path:
        """Canonical first-class project records inside the repository."""
        return self.root / "projects"

    def active_workspaces(self) -> list[Workspace]:
        return [w for w in self.workspaces.values() if not w.archived]

    def archived_workspaces(self) -> list[Workspace]:
        return [w for w in self.workspaces.values() if w.archived]

    def active_learning_paths(self) -> list[LearningPath]:
        return [p for p in self.learning_paths.values() if not p.archived]

    def current_study_maps(self) -> list[StudyMap]:
        return list(self.study_maps.values())


def _register(repo: Repo, family: dict, rec_id: str, record, origin: Path, family_name: str):
    if rec_id in family:
        repo.duplicate_ids.append((family_name, rec_id, origin))
        return
    family[rec_id] = record
