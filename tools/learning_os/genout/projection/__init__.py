"""The projectors ``build_manifest`` assembles.

One module per domain, mirroring ``learning_os.loading``: what a domain loader
reads in, its projector writes out. The assembly order and the published shape
stay in ``genout/manifest.py`` — this package holds only the per-domain rules,
so a change to how a source is rendered never means reading the whole payload.
"""

from __future__ import annotations

from .grouping import (
    ordered_thematic_group_ids,
    project_thematic_groups,
    project_topics,
    source_thematic_groups,
)
from .indexes import build_indexes
from .lifecycle import module_lifecycle
from .records_curriculum import (
    project_module_source_maps,
    project_modules,
    project_programs,
    project_study_maps,
    project_unit_material_syntheses,
    project_units,
    unit_note_sections,
)
from .records_knowledge import project_concepts, project_notes
from .records_library import project_collections, project_sources
from .records_projects import (
    project_project_aliases,
    project_project_relationships,
    project_projects,
    unit_to_project_ids,
)
from .records_work import project_coordination, project_learning_paths, project_workspaces
from .stages import project_stages
from .tallies import build_counts, build_progress

__all__ = [
    "build_counts", "build_indexes", "build_progress", "module_lifecycle",
    "ordered_thematic_group_ids", "project_collections", "project_concepts",
    "project_coordination", "project_learning_paths", "project_module_source_maps",
    "project_modules", "project_notes", "project_programs",
    "project_project_aliases", "project_project_relationships", "project_projects",
    "project_sources", "project_stages", "project_study_maps",
    "project_unit_material_syntheses",
    "project_thematic_groups", "project_topics", "project_units",
    "source_thematic_groups", "unit_note_sections",
    "unit_to_project_ids", "project_workspaces",
]
