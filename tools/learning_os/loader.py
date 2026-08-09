"""The loader's public surface (BUILD-SPEC Step 3).

The walk itself lives in ``learning_os.loading``: one module per domain over a
shared model, with the order between domains stated once in
``loading/__init__.py``. This module stays the import site every other tool
already uses — ``from learning_os.loader import load_repo`` — so where a record
is read from remains an internal detail of the loader, not a fact spread across
the callers.

See ``learning_os.loading`` for the registry layouts and for which module owns
which part of the tree.
"""

from __future__ import annotations

from .loading import (  # noqa: F401  (re-exported public surface)
    EVIDENCE_SCHEMES,
    FRONTMATTER_RE,
    GARDEN_TAG_RE,
    ID_RE,
    NOTE_ROLES,
    PATH_ID_RE,
    PREREQUISITE_RELATIONS,
    PROGRAM_ID_RE,
    PROJECT_ID_RE,
    PROJECT_RELATION_ID_RE,
    RELATION_SEMANTICS,
    RELATION_TYPES,
    STUDY_MAP_ID_RE,
    SYMMETRIC_RELATIONS,
    UNIT_ID_RE,
    Coordination,
    GardenNote,
    LearningPath,
    LoaderError,
    Note,
    Program,
    Project,
    Repo,
    StudyMap,
    Unit,
    Workspace,
    load_repo,
    md_section,
    parse_frontmatter,
)

__all__ = [
    "EVIDENCE_SCHEMES", "FRONTMATTER_RE", "GARDEN_TAG_RE", "ID_RE", "NOTE_ROLES",
    "PATH_ID_RE", "PREREQUISITE_RELATIONS", "PROGRAM_ID_RE", "PROJECT_ID_RE",
    "PROJECT_RELATION_ID_RE", "RELATION_SEMANTICS", "RELATION_TYPES",
    "STUDY_MAP_ID_RE", "SYMMETRIC_RELATIONS", "UNIT_ID_RE",
    "Coordination", "GardenNote", "LearningPath", "LoaderError", "Note",
    "Program", "Project", "Repo", "StudyMap", "Unit", "Workspace",
    "load_repo", "md_section", "parse_frontmatter",
]
