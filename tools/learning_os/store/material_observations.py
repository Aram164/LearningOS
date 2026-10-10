"""Observation port for the two ported material-synthesis reads (PLAN step 2.7; D19).

``MaterialObservations`` names the five filesystem reads
``current_unit_material_basis`` and ``_analysis_ref_problem`` perform.
``LiveMaterialObservations`` bridges each method to the exact existing
implementation; tests substitute an in-memory fake. The snapshot stays with
the caller: ``load_repo`` results arrive as the ``repo`` argument.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from learning_os.material_analysis import observe_local_material
from learning_os.materials_resolution import route_material_checksum
from learning_os.revisions import artifact_revision


class MaterialObservations(Protocol):
    def revision(self, artifact_id: str) -> int: ...
    def is_file(self, path: Path) -> bool: ...
    def read_bytes(self, path: Path) -> bytes: ...
    def observe_material(self, material: str, recorded_digest: str) -> dict: ...
    def route_checksum(self, repo, route: dict, cache: dict | None = None) -> str: ...


class LiveMaterialObservations:
    def __init__(self, root: Path, cache: dict | None = None):
        self._root = root
        self._cache = cache

    def revision(self, artifact_id: str) -> int:
        return artifact_revision(self._root, artifact_id)

    def is_file(self, path: Path) -> bool:
        return path.is_file()

    def read_bytes(self, path: Path) -> bytes:
        return path.read_bytes()

    def observe_material(self, material: str, recorded_digest: str) -> dict:
        return observe_local_material(
            self._root.parent / "materials", material, recorded_digest,
            cache=self._cache)

    def route_checksum(self, repo, route: dict, cache: dict | None = None) -> str:
        return route_material_checksum(repo, route, cache)
