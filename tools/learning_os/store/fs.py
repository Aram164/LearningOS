"""Atomic text writes and owner-bounded byte reads."""

from __future__ import annotations

import contextlib
import os
from pathlib import Path

from learning_os.domain.failures import WriteRefused


def atomic_text(path: Path, content: str) -> None:
    """Temp file + os.replace, cleaning up after any failure.

    Every mutating command funnels through here, so an ordinary filesystem
    problem — target replaced by a directory, permission denied, full disk —
    must surface as an actionable refusal instead of a traceback that leaves a
    stray `.tmp` sibling behind.
    """
    tmp = path.with_name(f".{path.name}.tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(content, encoding="utf-8")
        os.replace(tmp, path)
    except OSError as exc:
        with contextlib.suppress(OSError):
            tmp.unlink(missing_ok=True)
        raise WriteRefused(f"cannot write {path}: {exc.strerror or exc}") from exc


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
