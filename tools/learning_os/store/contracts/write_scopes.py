"""Exact, fail-closed write-scope matching for every transaction authority.

Capability declarations are path contracts, not string prefixes.  A prefix
check makes ``knowledge/garden/transcriptions-evil`` look like a descendant of
``knowledge/garden/transcriptions/`` and cannot distinguish ``*`` from ``**``.
This module gives public commands, migrations, and AI domain actions one shared
matcher and one path-boundary check.
"""

from __future__ import annotations

import os
from contextlib import ExitStack
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


def scoped_write_target(
    root: Path,
    raw_path: os.PathLike[str] | str,
    scopes: tuple[str, ...],
) -> Path:
    """Validate the actual path before passing it to a write primitive."""
    target, relative = write_target(root, raw_path)
    require_write_scope("filesystem writer", relative, scopes)
    return target


_REPO_MARKER_PATHS: tuple[tuple[str, ...], ...] = (
    ("system", "contracts", "capabilities.yaml"),
    ("system", "contracts", "tree-contract.yaml"),
    ("system", "contracts", "data-contract.yaml"),
)
_OS_TOP_SYMLINKS = frozenset({"var", "tmp", "etc"})


def _protected_repo_output_roots() -> frozenset[str]:
    from learning_os.store.fingerprint import DATA_ROOTS

    return frozenset((*DATA_ROOTS, "system", "operations"))


def _is_repo_root(path: Path) -> bool:
    try:
        return any((path / parts[0] / parts[1] / parts[2]).is_file() for parts in _REPO_MARKER_PATHS)
    except OSError:
        return False


def guard_tool_output_path(
    raw_path: os.PathLike[str] | str,
    *,
    repo_root: Path | None = None,
    allow_existing_dir: bool = False,
) -> Path:
    """Refuse caller-supplied output targets inside protected repository roots or symlinks.

    Rejects symlink components (including dangling target symlinks) and refuses
    targets that lexically or after resolution land inside ``DATA_ROOTS``,
    ``system/``, or ``operations/`` of any discovered or specified LearningOS
    repository, while permitting external scratch/temp/sibling destinations.
    """
    try:
        raw_os = os.fspath(raw_path)
    except TypeError as exc:
        raise WriteScopeError(f"tool output target must be a path: {raw_path!r}") from exc
    raw = raw_os if isinstance(raw_os, str) else os.fsdecode(raw_os)
    if not raw.strip() or "\x00" in raw:
        raise WriteScopeError(f"tool output target is malformed: {raw_path!r}")

    expanded = Path(os.path.expanduser(raw))
    lexical = Path(os.path.abspath(expanded))
    if lexical == lexical.parent:
        raise WriteScopeError(f"refusing filesystem root as tool output target: {raw_path!r}")

    if lexical.is_symlink():
        raise WriteScopeError(f"refusing symlink tool output target: {raw_path}")
    for ancestor in (lexical, *lexical.parents):
        if ancestor == ancestor.parent:
            break
        if len(ancestor.parts) == 2 and ancestor.parts[1] in _OS_TOP_SYMLINKS:
            continue
        if ancestor.is_symlink():
            raise WriteScopeError(
                f"refusing symlink component in tool output path: {ancestor}"
            )

    if not allow_existing_dir and lexical.exists() and lexical.is_dir():
        raise WriteScopeError(f"tool output target is an existing directory: {raw_path}")

    try:
        resolved = lexical.resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise WriteScopeError(f"cannot resolve tool output target {raw_path}: {exc}") from exc

    candidate_roots: list[Path] = []
    seen_roots: set[Path] = set()

    def _add_root(cand: Path) -> None:
        for view in (Path(os.path.abspath(cand.expanduser())),):
            if view not in seen_roots:
                seen_roots.add(view)
                candidate_roots.append(view)
            try:
                res = view.resolve(strict=False)
            except OSError:
                continue
            if res not in seen_roots:
                seen_roots.add(res)
                candidate_roots.append(res)

    if repo_root is not None:
        _add_root(repo_root)
    package_root = Path(__file__).resolve().parents[4]
    if _is_repo_root(package_root):
        _add_root(package_root)
    for probe in (lexical, *lexical.parents, resolved, *resolved.parents, Path.cwd(), *Path.cwd().parents):
        if _is_repo_root(probe):
            _add_root(probe)

    protected = _protected_repo_output_roots()
    for root_cand in candidate_roots:
        for target_view in (lexical, resolved):
            try:
                rel = target_view.relative_to(root_cand)
            except ValueError:
                continue
            if not rel.parts:
                raise WriteScopeError(
                    f"refusing tool output at repository root: {raw_path}"
                )
            if rel.parts[0] in protected:
                raise WriteScopeError(
                    f"refusing tool output inside protected root {rel.parts[0]}/: {raw_path}"
                )

    return lexical


_DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
_OS_DIRECTORY_ALIASES = frozenset({"tmp", "var", "etc"})


def open_guarded_directory(path: os.PathLike[str] | str, stack: ExitStack) -> int:
    """Open a directory for descriptor-relative writes, after the output guard.

    ``guard_tool_output_path`` first refuses protected repository roots and
    symlinked components. Every component is then opened with ``O_NOFOLLOW``
    from the filesystem root, after the approved macOS ``/tmp``, ``/var`` and
    ``/etc`` aliases, so a link substituted after the check is never followed.
    The returned descriptor and its ancestors close with ``stack``.
    """
    guarded = guard_tool_output_path(path, allow_existing_dir=True)
    absolute = Path(os.path.abspath(guarded))
    parts = absolute.parts[1:]
    if parts and parts[0] in _OS_DIRECTORY_ALIASES and Path("/", parts[0]).is_symlink():
        parts = ("private", *parts)
    fd = os.open(absolute.anchor, _DIRECTORY_FLAGS)
    stack.callback(os.close, fd)
    for part in parts:
        fd = os.open(part, _DIRECTORY_FLAGS, dir_fd=fd)
        stack.callback(os.close, fd)
    return fd
