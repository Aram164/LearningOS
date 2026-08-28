"""Core-owned Garden identity and projection.

Garden files are free-form Markdown. Their existence, identity, title, tags,
and revision are Core facts and must remain available even if the optional
AI-action subsystem is absent or its enrichment state is malformed.

AI state may enrich a Garden row, but it never owns the row itself.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import yaml

from .loader import Repo


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

    A broken optional sidecar must not make the underlying Garden artifact
    disappear from the Core projection.
    """
    path = (
        root
        / "operations"
        / "ai-actions"
        / "garden-state"
        / f"{target_id}.yaml"
    )

    if not path.is_file():
        return {}

    try:
        value = yaml.safe_load(
            path.read_text(encoding="utf-8")
        ) or {}
    except (OSError, yaml.YAMLError):
        return {}

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
