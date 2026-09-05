"""Material location, URI authority checks and safe locator projection.

The rules themselves live in ``learning_os.materials_resolution`` so that the
dossier service and the authoring tools can ask the same question without
importing projection internals. This module keeps the private names the rest
of ``genout`` already imports.
"""

from __future__ import annotations

from ..loader import Repo
from ..materials_resolution import (
    MATERIAL_RESOURCE_SUFFIXES as _MATERIAL_RESOURCE_SUFFIXES,
)
from ..materials_resolution import (
    MATERIAL_SUFFIX_TOKEN as _MATERIAL_SUFFIX_TOKEN,
)
from ..materials_resolution import (
    PAGE_COUNT_SUFFIX as _PAGE_COUNT_SUFFIX,
)
from ..materials_resolution import (
    material_location as _material_location,
)
from ..materials_resolution import (
    material_uri_authority as _material_uri_authority,
)
from ..materials_resolution import (
    project_material_resource as _project_material_resource,
)
from ..materials_resolution import (
    safe_material_locator as _safe_material_locator,
)

__all__ = [
    "_MATERIAL_RESOURCE_SUFFIXES",
    "_MATERIAL_SUFFIX_TOKEN",
    "_PAGE_COUNT_SUFFIX",
    "_material_location",
    "_material_uri_authority",
    "_materials_queue_rows",
    "_project_material_resource",
    "_safe_material_locator",
]


def _materials_queue_rows(repo: Repo) -> list[str]:
    """Pending-human-decision piles under materials/ (human-operability #10).
    Shared by the coordination view and the reading room."""
    rows: list[str] = []
    materials = repo.root.parent / "materials"
    for qname in ("_unsorted", "_duplicates-for-review"):
        qdir = materials / qname
        if not qdir.is_symlink() and qdir.is_dir():
            n = sum(1 for f in qdir.rglob("*")
                    if not f.is_symlink() and f.is_file() and f.name != ".DS_Store")
            if n:
                rows.append(f"- `materials/{qname}/` — **{n} files** "
                            "awaiting a register-or-discard decision")
    return rows
