"""Generated-view builders.

Everything under ``generated/`` is produced here. The package boundary is the
stable surface: callers import from ``learning_os.genout`` and do not need to
know which module builds which view, so views can be regrouped without
touching call sites.

Split from a single 2,429-line module; the builders were moved verbatim.
"""

from __future__ import annotations

from .atlas import ATLAS_COLLECTION_DOMAIN, ATLAS_DOMAINS, build_domain_atlas
from .canvas import build_concept_canvas
from .common import (
    LECTURE_KEY_RE, SELECTOR_ROLES, mermaid_node_ids, stable_generated_at,
)
from .concepts import (
    PREREQ_TYPES, build_backlinks, build_concept_index, build_concept_map,
    build_dependency_report,
)
from .coordination import adoption_counts, build_coordination_view, build_health
from .garden import build_nebula
from .manifest import build_manifest
from .materials import _project_material_resource
from .modules_view import _exam_spine, build_module_view
from .reading_room import build_reading_room
from .library import build_library
from .sources import build_collection_view, build_source_index
from .outputs import generate_all, write_outputs

# Imported by rules.py and ai_actions.py to compare a projection against the
# repository it claims to describe.
from .projection import source_fingerprint

__all__ = [
    "ATLAS_COLLECTION_DOMAIN", "ATLAS_DOMAINS", "LECTURE_KEY_RE", "PREREQ_TYPES",
    "SELECTOR_ROLES", "_exam_spine", "_project_material_resource",
    "source_fingerprint", "adoption_counts", "build_backlinks",
    "build_collection_view", "build_concept_canvas", "build_concept_index",
    "build_concept_map", "build_coordination_view", "build_dependency_report",
    "build_domain_atlas", "build_health", "build_manifest", "build_module_view",
    "build_library", "build_nebula", "build_reading_room", "build_source_index", "generate_all",
    "mermaid_node_ids", "stable_generated_at", "write_outputs",
]
