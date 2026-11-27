"""Shared durable filesystem primitives, git env sanitizers, and non-symlink walkers."""

from __future__ import annotations

import contextlib
import ctypes
import errno
import fcntl
import os
import secrets
import sys
from collections.abc import Callable, Iterator, Mapping, Sequence
from pathlib import Path

from learning_os.domain.failures import WriteRefused

#: Git environment overrides that can silently hijack subprocess git target
#: selection across checkouts (worktree, index, object/common dir).
GIT_ENV_OVERRIDE_VARS: frozenset[str] = frozenset({
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_COMMON_DIR",
})

_TEMP_ATTEMPTS = 32
_LINUX_AT_FDCWD = -100
_LINUX_RENAME_NOREPLACE = 1
_DARWIN_RENAME_EXCL = 0x00000004


def clean_git_env(
    base: Mapping[str, str] | None = None,
    *,
    extra: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Copy environment with Git repository/index override variables stripped."""
    source = os.environ if base is None else base
    env = {
        key: value
        for key, value in source.items()
        if key not in GIT_ENV_OVERRIDE_VARS
    }
    if extra:
        env.update(extra)
    return env


def sync_fd(fd: int) -> None:
    """Flush OS and hardware write caches for one open descriptor.

    On macOS, ``F_FULLFSYNC`` is mandatory to push bytes past drive caches and
    is never downgraded to plain ``os.fsync``.
    """
    os.fsync(fd)
    fullfsync = getattr(fcntl, "F_FULLFSYNC", None)
    if fullfsync is not None:
        fcntl.fcntl(fd, fullfsync)


def sync_directory(path: Path) -> None:
    """Make one directory's entries durable; a missing directory is done."""
    try:
        descriptor = os.open(path, os.O_RDONLY)
    except FileNotFoundError:
        return
    try:
        sync_fd(descriptor)
    finally:
        os.close(descriptor)


def create_ancestors_and_track(parent: Path) -> list[Path]:
    """Ensure ``parent`` exists while recording every newly created directory."""
    created: list[Path] = []
    cursor = parent
    while not cursor.exists() and not cursor.is_symlink():
        if cursor.parent == cursor:
            break
        created.append(cursor)
        cursor = cursor.parent
    parent.mkdir(parents=True, exist_ok=True)
    return created


def sync_directory_and_created_ancestors(
    parent: Path,
    created: Sequence[Path],
) -> None:
    """Sync the target parent directory and the parent of every new ancestor."""
    sync_directory(parent)
    for ancestor in created:
        sync_directory(ancestor.parent)


def rename_noreplace(source: Path, destination: Path) -> None:
    """Atomically move a path to a vacant name, even if a directory competes."""
    source_arg = os.fsencode(source)
    destination_arg = os.fsencode(destination)
    libc = ctypes.CDLL(None, use_errno=True)
    try:
        if sys.platform == "darwin":
            rename = libc.renamex_np
            rename.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint)
            arguments = (source_arg, destination_arg, _DARWIN_RENAME_EXCL)
        elif sys.platform == "linux":
            rename = libc.renameat2
            rename.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
                               ctypes.c_char_p, ctypes.c_uint)
            arguments = (_LINUX_AT_FDCWD, source_arg, _LINUX_AT_FDCWD,
                         destination_arg, _LINUX_RENAME_NOREPLACE)
        else:
            raise AttributeError(sys.platform)
    except AttributeError as exc:
        raise OSError(errno.ENOTSUP, "atomic no-replace rename is unavailable",
                      source, None, destination) from exc

    # ctypes does not emit the standard Python filesystem audit event.
    sys.audit("os.rename", os.fspath(source), os.fspath(destination), -1, -1)
    if rename(*arguments) != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), source, None, destination)


def _assert_no_symlinks_under_boundary(path: Path, boundary: Path) -> None:
    try:
        lexical_rel = path.relative_to(boundary)
    except ValueError as exc:
        raise ValueError(f"path escapes boundary {boundary}: {path}") from exc
    cursor = boundary
    for part in lexical_rel.parts[:-1]:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError(f"refusing symlink directory component: {cursor}")
    if path.is_symlink():
        raise ValueError(f"refusing symlink target: {path}")
    nearest = path.parent
    while not nearest.exists() and nearest != boundary and nearest.parent != nearest:
        nearest = nearest.parent
    if nearest.exists():
        try:
            nearest.resolve(strict=True).relative_to(boundary.resolve(strict=True))
        except (OSError, ValueError) as exc:
            raise ValueError(f"parent escapes boundary {boundary}: {path}") from exc


def exclusive_temp_path(
    target: Path,
    *,
    mode: int = 0o666,
) -> tuple[int, Path]:
    """Atomically open a unique non-symlink temp file alongside ``target``."""
    if target.is_symlink():
        raise OSError(f"refusing symlink target: {target}")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    for _ in range(_TEMP_ATTEMPTS):
        token = f"{os.getpid()}{secrets.randbelow(1_000_000_000):09d}"
        candidate = target.with_name(f".{target.name}.tmp-{token}")
        try:
            fd = os.open(candidate, flags, mode)
            return fd, candidate
        except FileExistsError:
            continue
    raise FileExistsError(f"could not allocate exclusive temp file for {target}")


def atomic_write_bytes_exclusive(
    path: Path,
    content: bytes,
    *,
    boundary: Path | None = None,
    durable: bool = True,
    mode: int = 0o666,
    error_factory: Callable[[str], Exception] = WriteRefused,
) -> None:
    """Write ``content`` to ``path`` via O_EXCL|O_NOFOLLOW temp + atomic replace."""
    try:
        if path.is_symlink():
            raise error_factory(f"cannot write through symlink {path}")
        if boundary is not None:
            try:
                _assert_no_symlinks_under_boundary(path, boundary)
            except ValueError as exc:
                raise error_factory(str(exc)) from exc
        else:
            cursor = path.parent
            while not cursor.exists() and cursor.parent != cursor:
                if cursor.is_symlink():
                    raise error_factory(f"cannot traverse symlink ancestor {cursor}")
                cursor = cursor.parent
        created = create_ancestors_and_track(path.parent)
        fd, tmp = exclusive_temp_path(path, mode=mode)
    except OSError as exc:
        if error_factory is OSError:
            raise
        raise error_factory(f"cannot write {path}: {exc.strerror or exc}") from exc

    handle = None
    try:
        try:
            handle = os.fdopen(fd, "wb")
        except BaseException:
            os.close(fd)
            raise
        with handle:
            view = memoryview(content)
            written = 0
            while written < len(view):
                written += handle.write(view[written:])
            handle.flush()
            if durable:
                sync_fd(handle.fileno())
        os.replace(tmp, path)
        if durable:
            sync_directory_and_created_ancestors(path.parent, created)
    except OSError as exc:
        with contextlib.suppress(OSError):
            tmp.unlink(missing_ok=True)
        if error_factory is OSError:
            raise
        raise error_factory(f"cannot write {path}: {exc.strerror or exc}") from exc
    except BaseException:
        with contextlib.suppress(OSError):
            tmp.unlink(missing_ok=True)
        raise


def atomic_write_text_exclusive(
    path: Path,
    content: str,
    *,
    boundary: Path | None = None,
    durable: bool = True,
    mode: int = 0o666,
    encoding: str = "utf-8",
    error_factory: Callable[[str], Exception] = WriteRefused,
) -> None:
    """Encode ``content`` and write via :func:`atomic_write_bytes_exclusive`."""
    atomic_write_bytes_exclusive(
        path,
        content.encode(encoding),
        boundary=boundary,
        durable=durable,
        mode=mode,
        error_factory=error_factory,
    )


def atomic_text(path: Path, content: str) -> None:
    """Temp file + os.replace, cleaning up after any failure.

    A filesystem refusal surfaces as ``WriteRefused`` and never leaves a stray
    temp sibling behind.
    """
    atomic_write_text_exclusive(path, content, error_factory=WriteRefused)


def iter_non_symlink_files(
    base: Path,
    *,
    allow_root_symlink: bool = False,
) -> Iterator[Path]:
    """Yield sorted regular non-symlink files under ``base`` (Python 3.12+ safe).

    Uses ``os.walk(..., followlinks=False)`` and filters symlinks explicitly so
    it never relies on Python 3.13-only ``Path.rglob`` keyword flags.
    """
    if not base.exists() or (not allow_root_symlink and base.is_symlink()) or not base.is_dir():
        return
    for dirpath, dirnames, filenames in os.walk(base, followlinks=False):
        current = Path(dirpath)
        dirnames[:] = sorted(
            name for name in dirnames if not (current / name).is_symlink()
        )
        for name in sorted(filenames):
            candidate = current / name
            if not candidate.is_symlink() and candidate.is_file():
                yield candidate


def iter_files_and_top_symlinks(
    base: Path,
    *,
    allow_root_symlink: bool = False,
) -> tuple[list[Path], list[Path]]:
    """Walk ``base`` without following directory symlinks.

    Returns ``(regular_files, symlink_paths)`` in sorted order. Symlinked
    directories are recorded in ``symlink_paths`` and never descended into.
    """
    if not allow_root_symlink and base.is_symlink():
        return [], [base]
    if not base.is_dir():
        return [], []
    files: list[Path] = []
    symlinks: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(base, followlinks=False):
        current = Path(dirpath)
        next_dirs: list[str] = []
        for name in sorted(dirnames):
            candidate = current / name
            if candidate.is_symlink():
                symlinks.append(candidate)
            else:
                next_dirs.append(name)
        dirnames[:] = next_dirs
        for name in sorted(filenames):
            candidate = current / name
            if candidate.is_symlink():
                symlinks.append(candidate)
            elif candidate.is_file():
                files.append(candidate)
    files.sort()
    symlinks.sort()
    return files, symlinks


def bytes_inside_owner(root, path, owner, *, escape, symlink):
    """Read bytes admitted by one owner directory; symlinks always refuse.

    The one admission rule for note, garden, and inbox reads: the resolved
    target must sit below the owner, and no path component may be a link —
    even one that would resolve in-tree. Only the refusal wording differs
    per surface.
    """
    try:
        path.resolve(strict=True).relative_to(owner.resolve(strict=True))
    except (ValueError, OSError) as exc:
        raise WriteRefused(escape) from exc
    if any(part.is_symlink() for part in (path, *path.parents) if part != root.parent):
        raise WriteRefused(symlink)
    return path.read_bytes()


def note_bytes(root, note):
    return bytes_inside_owner(
        root, note.path, root / "knowledge" / "notes",
        escape="note path escapes its knowledge owner",
        symlink="note read refuses symlinks")
