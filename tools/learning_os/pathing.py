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


def resolve_symlinks_inside(root: Path, path: Path, *, strict: bool = True) -> Path:
    """Resolve links only after proving each lexical target stays in *root*.

    ``Path.resolve`` discovers an escape only after walking the target. That is
    too late for privacy boundaries. Reading the link value first lets the
    materials subsystem support its in-tree ``.flat`` aliases without ever
    touching a sibling target.
    """
    authority = Path(os.path.abspath(os.fspath(root)))
    candidate = Path(path)
    lexical = candidate if candidate.is_absolute() else authority / candidate
    lexical = Path(os.path.abspath(os.fspath(lexical)))
    try:
        relative = lexical.relative_to(authority)
    except ValueError as exc:
        raise PathBoundaryError(f"path escapes {authority}: {path}") from exc
    if any(part in {"", ".", ".."} for part in relative.parts):
        raise PathBoundaryError(f"path is not normalized under {authority}: {path}")

    pending = deque(relative.parts)
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
        try:
            target_relative = normalized.relative_to(authority)
        except ValueError as exc:
            raise PathBoundaryError(
                f"symlink target escapes {authority}: {cursor}"
            ) from exc
        pending = deque((*target_relative.parts, *pending))
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
