"""Material identity and exact path resolution, shared by every reader.

One rule decides what a ``material://`` URI names, and every caller — the
manifest projection, the dossier service, and the authoring tools — asks this
module rather than re-deriving it. Two derivations of the same rule is how
``tools/material_toc.py`` came to answer a request for ``source-x/b/chapter.pdf``
with ``source-x/a/chapter.pdf``: it scanned the tree and matched a basename,
so a locator could be "verified" against a file nobody asked for.

The module deliberately depends on nothing but the loader model and the path
boundary. It is imported by ``genout.materials`` (which re-exports it under the
private names its own package already used) and by ``material_synthesis``,
which therefore no longer reaches into projection internals for identity.
"""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

from .pathing import PathBoundaryError, resolve_symlinks_inside

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .loader import Repo

MATERIAL_SCHEME = "material://"

MATERIAL_RESOURCE_SUFFIXES = frozenset({
    ".ipynb",
    ".md",
    ".pdf",
    ".ppt",
    ".pptx",
})

PAGE_COUNT_SUFFIX = re.compile(
    r"(?:\s+\(\d+\s+(?:pages?|pp\.?|slides?)\)|,\s*\d+\s+(?:pages?|pp\.?|slides?))\s*$",
    re.IGNORECASE,
)

MATERIAL_SUFFIX_TOKEN = re.compile(
    r"\.(?:ipynb|md|pdf|pptx?)(?=$|[\s,;+()])",
    re.IGNORECASE,
)


def material_uri_authority(ref) -> str | None:
    """Return the safe identity authority of a material URI."""
    if not isinstance(ref, str) or not ref.startswith(MATERIAL_SCHEME):
        return None

    payload = ref[len(MATERIAL_SCHEME):]

    if not payload or payload.startswith("/") or "\\" in payload:
        return None

    material_path = PurePosixPath(payload)

    if material_path.is_absolute() or any(
            part in {"", ".", ".."}
            for part in material_path.parts):
        return None

    return material_path.parts[0] if material_path.parts else None


def safe_material_locator(value) -> str | None:
    """Accept only one safe, file-shaped POSIX locator."""
    if not isinstance(value, str):
        return None

    locator = PAGE_COUNT_SUFFIX.sub("", value.strip())

    if (
        not locator
        or "\\" in locator
        or ";" in locator
        or "\n" in locator
        or len(MATERIAL_SUFFIX_TOKEN.findall(locator)) != 1
    ):
        return None

    locator_path = PurePosixPath(locator)

    if locator_path.is_absolute() or any(
            part in {"", ".", ".."}
            for part in locator_path.parts):
        return None

    if locator_path.suffix.lower() not in MATERIAL_RESOURCE_SUFFIXES:
        return None

    return locator_path.as_posix()


def resolve_material_target(
    ref: str,
    *,
    resolution_root: Path,
    boundary_root: Path,
) -> Path:
    """Resolve one ``material://`` URI to the exact file it names.

    ``resolution_root`` is where a URI payload starts (``materials/.flat`` when
    the id alias tree exists, otherwise ``materials/``); ``boundary_root`` is
    the authority every symlink hop must stay inside. The complete relative
    path is used — never only its final component — so two files with the same
    basename under different folders remain two different materials.

    Raises ``PathBoundaryError`` when the URI is unsafe or escapes the
    boundary, and ``FileNotFoundError`` when nothing exists at that exact path.
    """
    if material_uri_authority(ref) is None:
        raise PathBoundaryError(f"not a safe material URI: {ref}")
    payload = ref[len(MATERIAL_SCHEME):]
    resolved = resolve_symlinks_inside(
        Path(boundary_root), Path(resolution_root) / payload, strict=False
    )
    if not resolved.exists():
        raise FileNotFoundError(
            f"no material at the exact path named by {ref}: {resolved}"
        )
    return resolved


def material_location(repo: Repo, ref) -> dict:
    """Resolve a ``material://`` URI to a path relative to the LearningOS root
    (the vault's parent) plus an existence flag. Interfaces get a path they can
    hand to the OS file opener; the resolution rule stays here."""
    if material_uri_authority(ref) is None:
        return {"material_path": None, "material_exists": False}
    target = repo.materials_root / str(ref)[len(MATERIAL_SCHEME):]
    try:
        resolved = resolve_symlinks_inside(
            repo.learningos_root / "materials", target, strict=False
        )
        rel = resolved.relative_to(repo.learningos_root.resolve())
    except (PathBoundaryError, ValueError, OSError):
        return {"material_path": None, "material_exists": False}
    return {"material_path": str(rel), "material_exists": resolved.exists()}


def project_material_resource(repo: Repo, resource: dict) -> dict:
    """Add one core-resolved local target to a stage resource."""
    projected = dict(resource)

    if projected.get("material_path"):
        return projected

    material_uri = None
    vault_path = projected.get("vault_path")

    if isinstance(vault_path, str) and vault_path:
        if not vault_path.startswith(MATERIAL_SCHEME):
            return projected
        if material_uri_authority(vault_path):
            material_uri = vault_path
    else:
        locator = safe_material_locator(projected.get("locator"))
        source = repo.sources.get(projected.get("source_id"))
        source_material = (
            source.get("material")
            if isinstance(source, dict)
            else None
        )
        authority = material_uri_authority(source_material)

        if locator and authority:
            material_uri = f"material://{authority}/{locator}"

    if not material_uri:
        return projected

    projected["material_uri"] = material_uri
    projected.update(material_location(repo, material_uri))
    return projected
