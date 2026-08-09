"""Single internal loader API for Learning OS v3 (BUILD-SPEC Step 3).

Supports consolidated AND partitioned registries (the logical model must not
depend on registry partitioning):
  - concepts:  knowledge/concepts.yaml            or knowledge/concepts/*.yaml
  - relations: knowledge/concept-relations.yaml   or knowledge/concept-relations/*.yaml
  - sources:   sources/sources.yaml               or sources/registry/*.yaml
  - collections: sources/collections/*.yaml       (one curated list per file)
  - programs:  curriculum/programs/*.yaml
  - modules:   curriculum/modules/<module-id>/module.yaml, with
               records/modules.yaml as a backward-compatible migration input
  - units:     curriculum/modules/<module-id>/units/<unit-id>/unit.yaml
  - study maps: one optional study-map.yaml beside each unit.yaml
  - module source maps: curriculum/modules/<module-id>/source-map.yaml
  - projects:  projects/registry/project-*.yaml
  - project relations: projects/relations/project-relations.yaml
  - project aliases: projects/aliases.yaml
  - notes:     knowledge/notes/**/*.md            (Markdown frontmatter)
  - garden:    knowledge/garden/**/*.md           (free-form, no schema — §14)
  - workspaces: work/active/*/CONTEXT.md, archive/workspaces/*/*/CONTEXT.md
  - learning paths: <workspace>/paths/path-*.yaml (operational, workspace-owned)
  - coordination: work/COORDINATION.md

One walk, one ``Repo``. ``load_repo`` below is the whole control flow: each
domain owns a module, and the sequence here is the only place the order between
domains is stated. The order is load-bearing in two places — modules must come
after their programs, and learning paths are discovered inside the workspace
walk — but everything else is grouped for reading, not for dependency.
"""

from __future__ import annotations

from pathlib import Path

from .curriculum import (
    load_modules, load_programs, load_quarantine_boundary, load_resume_pointer,
    load_thematic_groups,
)
from .knowledge import load_concepts, load_garden, load_notes, load_relations
from .library import load_collections, load_sources, load_topics
from .model import (
    Coordination, GardenNote, LearningPath, Note, Program, Project, Repo,
    StudyMap, Unit, Workspace, _register,
)
from .projects import load_project_aliases, load_project_relations, load_projects
from .vocabulary import (
    EVIDENCE_SCHEMES, FRONTMATTER_RE, GARDEN_TAG_RE, ID_RE, NOTE_ROLES,
    PATH_ID_RE, PREREQUISITE_RELATIONS, PROGRAM_ID_RE, PROJECT_ID_RE,
    PROJECT_RELATION_ID_RE, RELATION_SEMANTICS, RELATION_TYPES,
    STUDY_MAP_ID_RE, SYMMETRIC_RELATIONS, UNIT_ID_RE, _strip_code,
)
from .work import load_coordination, load_workspaces
from .yamlio import (
    LoaderError, _load_registry, _load_yaml, _normalize, _record_id,
    md_section, parse_frontmatter,
)

__all__ = [
    # model
    "Coordination", "GardenNote", "LearningPath", "Note", "Program", "Project",
    "Repo", "StudyMap", "Unit", "Workspace",
    # vocabulary
    "EVIDENCE_SCHEMES", "FRONTMATTER_RE", "GARDEN_TAG_RE", "ID_RE", "NOTE_ROLES",
    "PATH_ID_RE", "PREREQUISITE_RELATIONS", "PROGRAM_ID_RE", "PROJECT_ID_RE",
    "PROJECT_RELATION_ID_RE", "RELATION_SEMANTICS", "RELATION_TYPES",
    "STUDY_MAP_ID_RE", "SYMMETRIC_RELATIONS", "UNIT_ID_RE",
    # reading
    "LoaderError", "md_section", "parse_frontmatter",
    # domain loaders
    "load_collections", "load_concepts", "load_coordination", "load_garden",
    "load_modules", "load_notes", "load_programs", "load_project_aliases",
    "load_project_relations", "load_projects", "load_quarantine_boundary",
    "load_relations", "load_resume_pointer", "load_sources",
    "load_thematic_groups", "load_topics", "load_workspaces",
    # entry point
    "load_repo",
]


def load_repo(root: Path | str) -> Repo:
    root = Path(root).resolve()
    repo = Repo(root=root)

    load_concepts(repo, root)
    load_relations(repo, root)

    load_sources(repo, root)
    load_collections(repo, root)
    load_thematic_groups(repo, root)
    load_topics(repo, root)

    load_projects(repo, root)
    load_project_aliases(repo, root)
    load_project_relations(repo, root)

    load_programs(repo, root)
    load_modules(repo, root)
    load_resume_pointer(repo, root)
    load_quarantine_boundary(repo, root)

    load_notes(repo, root)
    load_garden(repo, root)

    load_workspaces(repo, root)
    load_coordination(repo, root)

    return repo
