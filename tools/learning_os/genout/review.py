"""Concrete decision records for the Review surface.

Review is not a dashboard reconstructed by an interface. Core decides which
facts currently require a learner decision and publishes stable records with
an explicit reason and action target.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from ..loader import Repo


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def _path_id(category: str, relative: str) -> str:
    digest = hashlib.sha256(
        relative.encode("utf-8")
    ).hexdigest()[:12]
    return f"review-{category}-{digest}"


def _inbox_title(path: Path) -> str:
    if path.suffix.lower() not in {
        ".md",
        ".txt",
        ".rst",
        ".org",
    }:
        return path.name

    try:
        text = path.read_text(
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return path.name

    for line in text.splitlines():
        value = line.strip()
        if value.startswith("# "):
            return value[2:].strip() or path.name

    for line in text.splitlines():
        value = line.strip()
        if value:
            return value.lstrip("#").strip()[:120] or path.name

    return path.name


def build_review_items(
    repo: Repo,
    units: list[dict],
    study_maps: list[dict],
) -> list[dict]:
    """Return Core-owned decisions in deterministic display order."""
    rows: list[dict] = []
    unit_by_id = {
        row.get("id"): row
        for row in units
        if row.get("id")
    }

    # Shelving is an explicit proposed durable-state transition.
    for study_map in sorted(
        study_maps,
        key=lambda row: str(row.get("id", "")),
    ):
        shelving = study_map.get("shelving") or {}

        if shelving.get("state") != "proposed":
            continue

        unit = unit_by_id.get(
            study_map.get("unit_id")
        ) or {}

        proposals = [
            item
            for item in shelving.get("items", []) or []
            if isinstance(item, dict)
        ]

        rows.append(
            {
                "id": (
                    "review-shelving-"
                    + str(study_map["id"])
                ),
                "category": "shelving",
                "title": (
                    f"Shelve {unit.get('title') or study_map['unit_id']}"
                ),
                "context": (
                    shelving.get("summary")
                    or f"{len(proposals)} proposed durable change(s)."
                ),
                "reason": (
                    "A shelving proposal is ready. "
                    "Choose which proposed changes become durable."
                ),
                "target": {
                    "kind": "study-map",
                    "id": study_map["id"],
                    "unit_id": study_map.get("unit_id"),
                    "module_id": study_map.get("module_id"),
                    "revision": study_map.get("revision", 0),
                    "proposal_ids": [
                        item["id"]
                        for item in proposals
                        if item.get("id")
                    ],
                },
            }
        )

    # Inbox means captured but deliberately not yet routed.
    inbox = repo.root / "work" / "inbox"

    if inbox.is_dir():
        for path in sorted(
            candidate
            for candidate in inbox.rglob("*")
            if candidate.is_file()
            and not any(
                part.startswith(".")
                for part in candidate.relative_to(inbox).parts
            )
        ):
            relative = path.relative_to(
                repo.root
            ).as_posix()

            rows.append(
                {
                    "id": _path_id(
                        "inbox",
                        relative,
                    ),
                    "category": "inbox",
                    "title": _inbox_title(path),
                    "context": relative,
                    "reason": (
                        "This capture is still unrouted. "
                        "A human placement decision is required."
                    ),
                    "target": {
                        "kind": "inbox-item",
                        "path": relative,
                        "revision": _sha256(path),
                    },
                }
            )

    # Planning is concrete only when the unit says it needs a study map.
    for unit in sorted(
        units,
        key=lambda row: str(row.get("id", "")),
    ):
        if unit.get("status") != "needs-map":
            continue

        rows.append(
            {
                "id": (
                    "review-planning-"
                    + str(unit["id"])
                ),
                "category": "planning",
                "title": (
                    f"Plan {unit.get('title') or unit['id']}"
                ),
                "context": unit.get("scope") or "",
                "reason": (
                    "This unit needs a study map "
                    "before structured study can continue."
                ),
                "target": {
                    "kind": "unit",
                    "id": unit["id"],
                    "module_id": unit.get("module_id"),
                    "revision": unit.get("revision", 0),
                },
            }
        )

    # Garden is intentionally absent here by default. Age, Git timestamps,
    # and mere existence are pressure/order signals, not evidence that an idea
    # is mature. A future explicit Core review-eligibility action may add
    # category='garden' records without teaching the UI a heuristic.

    return rows
