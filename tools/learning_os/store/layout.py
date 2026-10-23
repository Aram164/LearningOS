"""Filesystem admission helpers shared by readers, projectors, and writers."""

from __future__ import annotations

import os
from collections import deque
from pathlib import Path


class PathBoundaryError(ValueError):
    """A path did not resolve inside the authority root that admitted it."""


def resolved_inside(root: Path, path: Path, *, strict: bool = True) -> Path:
    """Resolve *path* and require its final target to remain below *root*."""
    authority = Path(root).resolve()
    try:
        resolved = Path(path).resolve(strict=strict)
    except OSError as exc:
        raise PathBoundaryError(f"cannot resolve {path}: {exc.strerror or exc}") from exc
    try:
        resolved.relative_to(authority)
    except ValueError as exc:
        raise PathBoundaryError(
            f"resolved path escapes {authority}: {path} -> {resolved}"
        ) from exc
    return resolved


def _authority_parts(path: Path, authority: Path) -> tuple[str, ...] | None:
    """``path``'s parts below ``authority``, whichever spelling it uses, or None.

    The authority's own spelling and its resolved spelling are trusted:
    the caller admitted that directory. Any other spelling has to be a
    prefix of ``path`` carrying the authority's name that resolves to the
    same directory. Only such a prefix is resolved, never anything beneath
    it, so a target outside is still refused without being walked.
    """
    try:
        return path.relative_to(authority).parts
    except ValueError:
        pass
    real = Path(os.path.realpath(authority))
    try:
        return path.relative_to(real).parts
    except ValueError:
        pass
    names = {authority.name, real.name}
    for prefix in path.parents:
        if prefix.name in names and Path(os.path.realpath(prefix)) == real:
            return path.relative_to(prefix).parts
    return None


def resolve_symlinks_inside(root: Path, path: Path, *, strict: bool = True) -> Path:
    """Resolve links only after proving each lexical target stays in *root*.

    ``Path.resolve`` discovers an escape only after walking the target. That is
    too late for privacy boundaries. Reading the link value first lets the
    materials subsystem support its in-tree ``.flat`` aliases without ever
    touching a sibling target.

    One directory can have two spellings: macOS reaches the same tree as
    ``/var/...`` and ``/private/var/...``. A path or absolute link target
    spelled the other way is still inside (#17); see ``_authority_parts``.
    """
    authority = Path(os.path.abspath(os.fspath(root)))
    candidate = Path(path)
    lexical = candidate if candidate.is_absolute() else authority / candidate
    lexical = Path(os.path.abspath(os.fspath(lexical)))
    relative_parts = _authority_parts(lexical, authority)
    if relative_parts is None:
        raise PathBoundaryError(f"path escapes {authority}: {path}")
    if any(part in {"", ".", ".."} for part in relative_parts):
        raise PathBoundaryError(f"path is not normalized under {authority}: {path}")

    pending = deque(relative_parts)
    cursor = authority
    hops = 0
    while pending:
        cursor = cursor / pending.popleft()
        try:
            is_link = cursor.is_symlink()
        except OSError as exc:
            raise PathBoundaryError(
                f"cannot inspect path component {cursor}: {exc.strerror or exc}"
            ) from exc
        if not is_link:
            continue
        hops += 1
        if hops > 64:
            raise PathBoundaryError(f"too many symlink hops under {authority}: {path}")
        try:
            link_value = Path(os.readlink(cursor))
        except OSError as exc:
            raise PathBoundaryError(
                f"cannot read symlink {cursor}: {exc.strerror or exc}"
            ) from exc
        target = link_value if link_value.is_absolute() else cursor.parent / link_value
        normalized = Path(os.path.abspath(os.fspath(target)))
        target_parts = _authority_parts(normalized, authority)
        if target_parts is None:
            raise PathBoundaryError(f"symlink target escapes {authority}: {cursor}")
        pending = deque((*target_parts, *pending))
        cursor = authority

    if strict and not cursor.exists():
        raise PathBoundaryError(f"path does not exist under {authority}: {path}")
    return cursor


def read_text_inside(
    root: Path,
    path: Path,
    *,
    encoding: str = "utf-8",
    errors: str = "strict",
) -> str:
    return resolved_inside(root, path).read_text(encoding=encoding, errors=errors)


def read_bytes_inside(root: Path, path: Path) -> bytes:
    return resolved_inside(root, path).read_bytes()
