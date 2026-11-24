"""Core-owned Garden identity and projection.

Garden files are free-form Markdown. Their existence, identity, title, tags,
and revision are Core facts and must remain available even if the optional
AI-action subsystem is absent or its enrichment state is malformed.

AI state may enrich a Garden row, but it never owns the row itself.
"""

from __future__ import annotations

import hashlib
import os
import re
import stat
from pathlib import Path

import yaml

from learning_os.domain.snapshot import Repo


def _slug(value: str) -> str:
    return (
        re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        or "garden-seed"
    )


def garden_id(garden_root: Path, path: Path) -> str:
    """Stable sibling-independent identity for one Garden note."""
    rel = path.relative_to(garden_root).with_suffix("").as_posix()
    base = f"garden-note-{_slug(rel)}"

    if "/" in rel:
        base += "-" + hashlib.sha256(
            rel.encode("utf-8")
        ).hexdigest()[:8]

    return base


def _state(root: Path, target_id: str) -> dict:
    """Best-effort optional AI enrichment.

    A broken or symlinked optional sidecar must not make the underlying Garden
    artifact disappear from the Core projection or read outside ``garden-state``.
    """
    if not target_id or "/" in target_id or "\\" in target_id or target_id in {".", ".."}:
        return {}
    state_dir = root / "operations" / "ai-actions" / "garden-state"
    if state_dir.is_symlink() or not state_dir.is_dir():
        return {}
    path = state_dir / f"{target_id}.yaml"
    if path.is_symlink():
        return {}
    try:
        resolved_dir = state_dir.resolve(strict=True)
        resolved = path.resolve(strict=True)
        resolved.relative_to(resolved_dir)
    except (OSError, ValueError):
        return {}

    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(resolved, flags)
    except OSError:
        return {}
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            return {}
        with os.fdopen(fd, "r", encoding="utf-8") as handle:
            fd = -1
            value = yaml.safe_load(handle.read()) or {}
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return {}
    finally:
        if fd >= 0:
            os.close(fd)

    return value if isinstance(value, dict) else {}


def _revision(path: Path) -> str:
    return "sha256:" + hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def project_garden_entries(repo: Repo) -> list[dict]:
    """Project every Garden seed from the loader's authoritative file walk."""
    garden_root = repo.root / "knowledge" / "garden"
    rows: list[dict] = []
    seen: dict[str, str] = {}

    for note in sorted(
        repo.garden_notes,
        key=lambda item: item.path.as_posix(),
    ):
        target_id = garden_id(
            garden_root,
            note.path,
        )
        relative = note.path.relative_to(
            repo.root
        ).as_posix()

        previous = seen.get(target_id)
        if previous is not None:
            raise ValueError(
                "Garden identity collision: "
                f"{previous} and {relative} both resolve to "
                f"{target_id}"
            )

        seen[target_id] = relative

        state = _state(
            repo.root,
            target_id,
        )

        rows.append(
            {
                "id": target_id,
                "type": "garden-note",
                "title": state.get("title") or note.title,
                "path": relative,
                "state": state.get("state", "seed"),
                "revision": _revision(note.path),
                "tags": list(note.tags),
                "transcription_path": state.get(
                    "transcription_path"
                ),
                "last_ai_request_id": state.get(
                    "last_ai_request_id"
                ),
            }
        )

    return rows
