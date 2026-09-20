"""Content digests for derived-state inputs.

Modification times are never identity here: authored files may be edited
directly, so every digest is over bytes. Inadmissible symlinks contribute
link identity without reading the target, mirroring fingerprint.py; a file
that is simply absent digests distinctly from one that cannot be admitted.
"""

from __future__ import annotations

import hashlib
import os
from collections.abc import Sequence
from pathlib import Path, PurePosixPath

from ..pathing import PathBoundaryError, read_bytes_inside
from .model import DerivedError


def digest_bytes(data: bytes) -> str:
    """Hex SHA-256 of in-memory bytes."""
    return hashlib.sha256(data).hexdigest()


def digest_file(root: Path, path: Path) -> str:
    """Digest one file's bytes under ``root``.

    Three states digest distinctly: readable content, an inadmissible or
    unreadable link (its link value, never its target), and absence.
    """
    digest = hashlib.sha256()
    try:
        digest.update(read_bytes_inside(root, path))
    except (OSError, PathBoundaryError):
        if not path.is_symlink() and not path.exists():
            digest.update(b"<missing>\0")
        else:
            # Same contribution as canonical_fingerprint: the link moves the
            # guard without the external target being read.
            digest.update(b"<inadmissible-symlink>\0")
            if path.is_symlink():
                try:
                    digest.update(os.readlink(path).encode("utf-8"))
                except OSError:
                    digest.update(b"<unreadable>")
    digest.update(b"\0")
    return digest.hexdigest()


def _checked_relative_root(relative_root: str) -> PurePosixPath:
    relative = PurePosixPath(relative_root)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise DerivedError(f"derived tree root escapes its root: {relative_root!r}")
    return relative


def digest_tree(root: Path, relative_root: str) -> str:
    """Digest a rooted subtree: sorted relative paths plus file contents.

    Same walk shape as canonical_fingerprint: dot-prefixed paths are
    skipped, entries are ordered deterministically, and a missing or empty
    tree contributes nothing (both project to "no records" downstream).
    """
    relative = _checked_relative_root(relative_root)
    base = root.joinpath(*relative.parts) if relative.parts else root
    digest = hashlib.sha256()
    if not base.exists() and not base.is_symlink():
        return digest.hexdigest()
    if base.is_file() or base.is_symlink():
        entries = [base]
    else:
        entries = sorted(path for path in base.rglob("*") if path.is_file() or path.is_symlink())
    for path in entries:
        rel = path.relative_to(root)
        if any(part.startswith(".") for part in rel.parts):
            continue
        digest.update(rel.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(digest_file(root, path).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def digest_paths(root: Path, paths: Sequence[str]) -> str:
    """Digest a fixed list of repo-relative paths in canonical order."""
    digest = hashlib.sha256()
    for rel in sorted(PurePosixPath(path).as_posix() for path in paths):
        relative = _checked_relative_root(rel)
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(digest_file(root, root.joinpath(*relative.parts)).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def digest_producer_files(root: Path, paths: Sequence[str]) -> str:
    """Digest the implementation files a node's value depends on.

    Unlike data inputs, a missing or inadmissible producer file is a
    programming bug — a mistyped producer path would otherwise track
    nothing and silently reuse stale values — so it fails closed.
    """
    digest = hashlib.sha256()
    for rel in sorted(PurePosixPath(path).as_posix() for path in paths):
        relative = _checked_relative_root(rel)
        target = root.joinpath(*relative.parts)
        try:
            content = read_bytes_inside(root, target)
        except (OSError, PathBoundaryError) as exc:
            raise DerivedError(f"derived producer file is not readable: {rel}") from exc
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(content)
        digest.update(b"\0")
    return digest.hexdigest()
