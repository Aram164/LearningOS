"""Exact, fail-closed write-scope matching for every transaction authority.

Capability declarations are path contracts, not string prefixes.  A prefix
check makes ``knowledge/garden/transcriptions-evil`` look like a descendant of
``knowledge/garden/transcriptions/`` and cannot distinguish ``*`` from ``**``.
This module gives public commands, migrations, and AI domain actions one shared
matcher and one path-boundary check.
"""

from __future__ import annotations

import os
from functools import cache
from pathlib import Path


class WriteScopeError(ValueError):
    """A target or scope declaration is unsafe or out of authority."""


def _segments(value: str, *, label: str, allow_glob: bool) -> tuple[str, ...]:
    if not isinstance(value, str) or not value.strip():
        raise WriteScopeError(f"{label} must be a non-empty relative path")
    if value != value.strip() or "\x00" in value or "\\" in value:
        raise WriteScopeError(f"{label} is malformed: {value!r}")
    if value.startswith("/") or "//" in value:
        raise WriteScopeError(f"{label} must be a normalized relative path: {value!r}")

    normalized = value.rstrip("/")
    parts = tuple(normalized.split("/"))
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise WriteScopeError(f"{label} must be a normalized relative path: {value!r}")
    if allow_glob:
        for part in parts:
            if any(token in part for token in "?[]"):
                raise WriteScopeError(
                    f"{label} supports only * and complete ** path segments: {value!r}"
                )
            if "*" in part and part not in {"*", "**"}:
                raise WriteScopeError(
                    f"{label} may use * and ** only as complete path segments: {value!r}"
                )
    return parts


def normalize_scope_pattern(pattern: str) -> str:
    """Validate and normalize one declared scope.

    A trailing slash is the historical domain-capability spelling for a
    descendant prefix.  Normalize it to ``/**`` so it has precise semantics.
    """
    trailing_prefix = pattern.endswith("/")
    parts = _segments(pattern, label="write scope", allow_glob=True)
    normalized = "/".join(parts)
    return f"{normalized}/**" if trailing_prefix else normalized


def normalize_relative_path(relative: str) -> str:
    return "/".join(
        _segments(relative, label="transaction target", allow_glob=False)
    )


def write_target(root: Path, raw_path: os.PathLike[str] | str) -> tuple[Path, str]:
    """Return a lexical in-root target and its safe relative path.

    Existing symlinks are refused even when they happen to resolve back inside
    the root.  Authority is granted to a stable repository path, never to the
    mutable destination of an indirection.
    """
    root = root.resolve()
    raw = os.fspath(raw_path)
    if not isinstance(raw, str):
        raw = os.fsdecode(raw)
    if "\x00" in raw or "\\" in raw:
        raise WriteScopeError(f"transaction target is malformed: {raw!r}")
    candidate = Path(raw)
    if candidate.as_posix() != raw:
        raise WriteScopeError(f"transaction target is not normalized: {raw!r}")
    if any(part in {".", ".."} for part in candidate.parts):
        raise WriteScopeError(f"transaction target is not normalized: {raw!r}")
    lexical = candidate if candidate.is_absolute() else root / candidate
    try:
        relative_path = lexical.relative_to(root)
    except ValueError as exc:
        raise WriteScopeError(f"transaction target escapes repository: {raw}") from exc
    relative = normalize_relative_path(relative_path.as_posix())

    cursor = root
    for part in relative_path.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise WriteScopeError(
                f"transaction target traverses symlink: {relative}"
            )
    try:
        lexical.resolve(strict=False).relative_to(root)
    except (OSError, ValueError) as exc:
        raise WriteScopeError(f"transaction target escapes repository: {relative}") from exc
    return lexical, relative


def scope_matches(relative: str, pattern: str) -> bool:
    """Match a safe relative file path against a declared scope.

    ``*`` consumes exactly one complete segment. ``**`` consumes zero or more
    complete segments. No platform-dependent globbing or filesystem
    enumeration is involved.
    """
    path_parts = _segments(relative, label="transaction target", allow_glob=False)
    pattern_parts = tuple(normalize_scope_pattern(pattern).split("/"))

    @cache
    def match(pattern_index: int, path_index: int) -> bool:
        if pattern_index == len(pattern_parts):
            return path_index == len(path_parts)
        token = pattern_parts[pattern_index]
        if token == "**":
            return match(pattern_index + 1, path_index) or (
                path_index < len(path_parts) and match(pattern_index, path_index + 1)
            )
        if token == "*":
            return path_index < len(path_parts) and match(
                pattern_index + 1, path_index + 1
            )
        return path_index < len(path_parts) and path_parts[path_index] == token \
            and match(pattern_index + 1, path_index + 1)

    return match(0, 0)


def require_write_scope(
    capability: str,
    relative: str,
    scopes: tuple[str, ...] | list[str],
) -> str:
    """Return the normalized path or raise a non-leaking scope refusal."""
    normalized = normalize_relative_path(relative)
    if not scopes:
        raise WriteScopeError(
            f"capability {capability} declares no write scope; refusing {normalized}"
        )
    if not any(scope_matches(normalized, pattern) for pattern in scopes):
        raise WriteScopeError(
            f"capability {capability} may not write {normalized}"
        )
    return normalized
