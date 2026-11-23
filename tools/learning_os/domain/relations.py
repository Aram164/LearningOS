"""Concept-relation lifecycle and evidence defaults (P1, IMPLEMENTATION-PLAN §P1).

Stored rows stay byte-identical by default: missing optional fields are
projected with these defaults, never bulk-migrated into the registry.
"""

from __future__ import annotations

import hashlib
import unicodedata
from pathlib import Path

RELATION_DEFAULTS = {
    "origin": "pilot",
    "status": "active",
    "pinned": False,
    "evidence_disputed": False,
    "evidence": [],
}


def enriched_relation(row: dict) -> dict:
    """A copy of ``row`` with every optional P1 field present."""
    out = dict(row)
    for key, default in RELATION_DEFAULTS.items():
        out.setdefault(key, list(default) if isinstance(default, list) else default)
    return out


def is_active(row: dict) -> bool:
    return row.get("status", "active") == "active"


def is_decorated(row: dict) -> bool:
    """Whether a row carries P1 decoration that forbids hard deletion."""
    return any(key in row for key in RELATION_DEFAULTS) or "status_reason" in row


def normalize_quote(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text).split())


def binding_file_state(repo_root: Path, materials_root: Path, binding: dict) -> str:
    """``ok`` when the pinned file exists under materials with its digest."""
    rel = str(binding.get("material_relpath", ""))
    if not rel or Path(rel).is_absolute() or ".." in Path(rel).parts:
        return "stale"
    candidate = materials_root / rel
    try:
        candidate.resolve().relative_to(materials_root.resolve())
    except (OSError, ValueError):
        return "stale"
    if candidate.is_symlink() or not candidate.is_file():
        return "stale"
    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    return "ok" if digest == binding.get("file_sha256") else "stale"


def evidence_state(row: dict, binding_states: list[str] | None = None) -> str:
    """Precedence: disputed > stale > missing > verified (§P1 step 6)."""
    if row.get("evidence_disputed"):
        return "disputed"
    evidence = row.get("evidence") or []
    if not evidence:
        return "missing"
    if binding_states and any(state != "ok" for state in binding_states):
        return "stale"
    return "verified"


def relation_evidence_state(repo, row: dict) -> str:
    evidence = row.get("evidence") or []
    if not evidence:
        return "disputed" if row.get("evidence_disputed") else "missing"
    states = [
        binding_file_state(repo.root, repo.materials_root, binding)
        for binding in evidence
    ]
    return evidence_state(row, states)
