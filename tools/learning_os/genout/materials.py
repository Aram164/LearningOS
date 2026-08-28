"""Material location, URI authority checks and safe locator projection."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from ..loader import Repo
from ..pathing import PathBoundaryError, resolve_symlinks_inside


# --------------------------------------------------------------------- build
def _material_location(repo: Repo, ref) -> dict:
    """Resolve a ``material://`` URI to a path relative to the LearningOS root
    (the vault's parent) plus an existence flag. Interfaces get a path they can
    hand to the OS file opener; the resolution rule stays here."""
    if _material_uri_authority(ref) is None:
        return {"material_path": None, "material_exists": False}
    target = repo.materials_root / str(ref)[len("material://"):]
    try:
        resolved = resolve_symlinks_inside(
            repo.learningos_root / "materials", target, strict=False
        )
        rel = resolved.relative_to(repo.learningos_root.resolve())
    except (PathBoundaryError, ValueError, OSError):
        return {"material_path": None, "material_exists": False}
    return {"material_path": str(rel), "material_exists": resolved.exists()}


_MATERIAL_RESOURCE_SUFFIXES = frozenset({
    ".ipynb",
    ".md",
    ".pdf",
    ".ppt",
    ".pptx",
})

_PAGE_COUNT_SUFFIX = re.compile(
    r"(?:\s+\(\d+\s+(?:pages?|pp\.?|slides?)\)|,\s*\d+\s+(?:pages?|pp\.?|slides?))\s*$",
    re.IGNORECASE,
)

_MATERIAL_SUFFIX_TOKEN = re.compile(
    r"\.(?:ipynb|md|pdf|pptx?)(?=$|[\s,;+()])",
    re.IGNORECASE,
)


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

    locator = _PAGE_COUNT_SUFFIX.sub("", value.strip())

    if (
        not locator
        or "\\" in locator
        or ";" in locator
        or "\n" in locator
        or len(_MATERIAL_SUFFIX_TOKEN.findall(locator)) != 1
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
        if not qdir.is_symlink() and qdir.is_dir():
            n = sum(1 for f in qdir.rglob("*")
                    if not f.is_symlink() and f.is_file() and f.name != ".DS_Store")
            if n:
                rows.append(f"- `materials/{qname}/` — **{n} files** "
                            "awaiting a register-or-discard decision")
    return rows
