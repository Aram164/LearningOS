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

Snapshot values are owned by ``learning_os.domain.snapshot``, vocabulary by
``learning_os.domain.vocabulary`` and ``md_section`` by
``learning_os.domain.markdown``; import them there.
"""

from __future__ import annotations

import contextvars
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from learning_os.domain.snapshot import Repo
from learning_os.store.loading.curriculum import (
    load_modules,
    load_programs,
    load_quarantine_boundary,
    load_resume_pointer,
    load_thematic_groups,
)
from learning_os.store.loading.knowledge import (
    load_abilities,
    load_concepts,
    load_garden,
    load_notes,
    load_relations,
)
from learning_os.store.loading.library import load_collections, load_sources, load_topics
from learning_os.store.loading.projects import (
    load_project_aliases,
    load_project_relations,
    load_projects,
)
from learning_os.store.loading.work import load_coordination, load_workspaces
from learning_os.store.loading.yamlio import LoaderError, parse_frontmatter

__all__ = [
    # reading
    "LoaderError", "parse_frontmatter",
    # domain loaders
    "load_collections", "load_concepts", "load_coordination", "load_garden",
    "load_modules", "load_notes", "load_programs", "load_project_aliases",
    "load_project_relations", "load_projects", "load_quarantine_boundary",
    "load_relations", "load_resume_pointer", "load_sources",
    "load_thematic_groups", "load_topics", "load_workspaces",
    # entry point
    "load_repo",
]


_REPO_LOADS: contextvars.ContextVar[list[int] | None] = contextvars.ContextVar("repo_loads", default=None)


@contextmanager
def count_repo_loads() -> Iterator[list[int]]:
    counter = [0]
    token = _REPO_LOADS.set(counter)
    try:
        yield counter
    finally:
        _REPO_LOADS.reset(token)


def load_repo(root: Path | str) -> Repo:
    counter = _REPO_LOADS.get()
    if counter is not None:
        counter[0] += 1
    root = Path(root).resolve()
    repo = Repo(root=root)

    load_concepts(repo, root)
    load_abilities(repo, root)
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
