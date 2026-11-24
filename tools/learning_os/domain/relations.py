"""Concept-relation lifecycle and evidence defaults (P1, IMPLEMENTATION-PLAN §P1).

Stored rows stay byte-identical by default: missing optional fields are
projected with these defaults, never bulk-migrated into the registry.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Mapping
from typing import NotRequired, TypedDict


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
    """Whether a row carries P1 decoration that forbids hard deletion.

    Decided by value, not by key presence, so it matches the UI's
    ``isDecorated`` exactly: a row that was pinned and then unpinned stores
    ``pinned: false`` and is as removable as one that was never pinned.
    """
    return (row.get("status", "active") != "active"
            or row.get("pinned") is True
            or bool(row.get("evidence"))
            or row.get("evidence_disputed") is True
            or bool(str(row.get("status_reason") or "").strip())
            or row.get("origin") == "aram")


def normalize_quote(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text).split())


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
