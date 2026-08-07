"""Material location, URI authority checks and safe locator projection."""

from __future__ import annotations

from ..loader import Repo
from pathlib import PurePosixPath

# --------------------------------------------------------------------- build
def _material_location(repo: Repo, ref) -> dict:
    """Resolve a ``material://`` URI to a path relative to the LearningOS root
    (the vault's parent) plus an existence flag. Interfaces get a path they can
    hand to the OS file opener; the resolution rule stays here."""
    if not ref or not str(ref).startswith("material://"):
        return {"material_path": None, "material_exists": False}
    target = repo.materials_root / str(ref)[len("material://"):]
    try:
        rel = target.resolve().relative_to(repo.learningos_root.resolve())
    except (ValueError, OSError):
        try:
            rel = target.relative_to(repo.learningos_root)
        except ValueError:
            return {"material_path": None, "material_exists": False}
    return {"material_path": str(rel), "material_exists": target.exists()}


_MATERIAL_RESOURCE_SUFFIXES = frozenset({
    ".ipynb",
    ".md",
    ".pdf",
    ".ppt",
    ".pptx",
})


def _material_uri_authority(ref) -> str | None:
    """Return the safe identity authority of a material URI."""
    if not isinstance(ref, str) or not ref.startswith("material://"):
        return None

    payload = ref[len("material://"):]

    if not payload or payload.startswith("/") or "\\" in payload:
        return None

    material_path = PurePosixPath(payload)

    if material_path.is_absolute() or any(
            part in {"", ".", ".."}
            for part in material_path.parts):
        return None

    return material_path.parts[0] if material_path.parts else None


def _safe_material_locator(value) -> str | None:
    """Accept only one safe, file-shaped POSIX locator."""
    if not isinstance(value, str):
        return None

    locator = value.strip()

    if (
        not locator
        or "\\" in locator
        or ";" in locator
        or "\n" in locator
    ):
        return None

    locator_path = PurePosixPath(locator)

    if locator_path.is_absolute() or any(
            part in {"", ".", ".."}
            for part in locator_path.parts):
        return None

    if locator_path.suffix.lower() not in _MATERIAL_RESOURCE_SUFFIXES:
        return None

    return locator_path.as_posix()


def _project_material_resource(repo: Repo, resource: dict) -> dict:
    """Add one core-resolved local target to a stage resource."""
    projected = dict(resource)

    if projected.get("material_path"):
        return projected

    material_uri = None
    vault_path = projected.get("vault_path")

    if isinstance(vault_path, str) and vault_path:
        if not vault_path.startswith("material://"):
            return projected
        if _material_uri_authority(vault_path):
            material_uri = vault_path
    else:
        locator = _safe_material_locator(projected.get("locator"))
        source = repo.sources.get(projected.get("source_id"))
        source_material = (
            source.get("material")
            if isinstance(source, dict)
            else None
        )
        authority = _material_uri_authority(source_material)

        if locator and authority:
            material_uri = f"material://{authority}/{locator}"

    if not material_uri:
        return projected

    projected["material_uri"] = material_uri
    projected.update(_material_location(repo, material_uri))
    return projected


def _materials_queue_rows(repo: Repo) -> list[str]:
    """Pending-human-decision piles under materials/ (human-operability #10).
    Shared by the coordination view and the reading room."""
    rows: list[str] = []
    materials = repo.root.parent / "materials"
    for qname in ("_unsorted", "_duplicates-for-review"):
        qdir = materials / qname
        if qdir.is_dir():
            n = sum(1 for f in qdir.rglob("*")
                    if f.is_file() and f.name != ".DS_Store")
            if n:
                rows.append(f"- `materials/{qname}/` — **{n} files** "
                            "awaiting a register-or-discard decision")
    return rows
