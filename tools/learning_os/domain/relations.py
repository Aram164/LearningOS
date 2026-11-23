"""Concept-relation lifecycle and evidence defaults (P1, IMPLEMENTATION-PLAN §P1).

Stored rows stay byte-identical by default: missing optional fields are
projected with these defaults, never bulk-migrated into the registry.
"""

from __future__ import annotations

import hashlib
import unicodedata
from collections.abc import Mapping
from pathlib import Path
from typing import NotRequired, TypedDict

from learning_os.domain.snapshot import Repo


class EvidenceBinding(TypedDict):
    source_id: str
    material_relpath: str
    file_sha256: str
    page: int
    quote: NotRequired[str]


RelationRow = TypedDict("RelationRow", {
    "from": str,
    "to": str,
    "type": str,
    "context": NotRequired[str],
    "source": NotRequired[str],
    "status_reason": NotRequired[str],
    "origin": NotRequired[str],
    "status": NotRequired[str],
    "pinned": NotRequired[bool],
    "evidence_disputed": NotRequired[bool],
    "evidence": NotRequired[list[EvidenceBinding]],
})


RELATION_DEFAULT_FIELDS = (
    "origin", "status", "pinned", "evidence_disputed", "evidence",
)


def enriched_relation(row: RelationRow) -> RelationRow:
    """A copy of ``row`` with every optional P1 field present."""
    out = row.copy()
    out.setdefault("origin", "pilot")
    out.setdefault("status", "active")
    out.setdefault("pinned", False)
    out.setdefault("evidence_disputed", False)
    out.setdefault("evidence", [])
    return out


def is_active(row: Mapping[str, object]) -> bool:
    return row.get("status", "active") == "active"


def is_decorated(row: Mapping[str, object]) -> bool:
    """Whether a row carries P1 decoration that forbids hard deletion."""
    return any(key in row for key in RELATION_DEFAULT_FIELDS) or "status_reason" in row


def normalize_quote(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text).split())


def binding_file_state(repo_root: Path, materials_root: Path, binding: Mapping[str, object]) -> str:
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


def evidence_state(row: Mapping[str, object], binding_states: list[str] | None = None) -> str:
    """Precedence: disputed > stale > missing > verified (§P1 step 6)."""
    if row.get("evidence_disputed"):
        return "disputed"
    evidence = row.get("evidence") or []
    if not evidence:
        return "missing"
    if binding_states and any(state != "ok" for state in binding_states):
        return "stale"
    return "verified"


def relation_evidence_state(repo: Repo, row: RelationRow) -> str:
    evidence = row.get("evidence") or []
    if not evidence:
        return "disputed" if row.get("evidence_disputed") else "missing"
    states = [
        binding_file_state(repo.root, repo.materials_root, binding)
        for binding in evidence
    ]
    return evidence_state(row, states)
