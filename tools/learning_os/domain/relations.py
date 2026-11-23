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


#: SHA-256 of material files, keyed by (path, device, inode, size, mtime_ns).
#: One publish asks for the same cited PDF once per board, concept card and
#: manifest row that shows it; without this every ask re-read and re-hashed
#: the whole file. Any change to the file changes its stat key, so a stale
#: digest is never served; entries for replaced files are simply unused.
_DIGESTS: dict[tuple[str, int, int, int, int], str] = {}


def material_file(materials_root: Path, rel: object) -> Path | None:
    """The regular, non-linked file ``rel`` names under materials, or None."""
    rel = str(rel or "")
    if not rel or Path(rel).is_absolute() or ".." in Path(rel).parts:
        return None
    candidate = materials_root / rel
    try:
        candidate.resolve().relative_to(materials_root.resolve())
    except (OSError, ValueError):
        return None
    if candidate.is_symlink() or not candidate.is_file():
        return None
    return candidate


def file_sha256(path: Path) -> str:
    """The file's SHA-256, read once per unchanged file."""
    stat = path.stat()
    key = (str(path), stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)
    digest = _DIGESTS.get(key)
    if digest is None:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        _DIGESTS[key] = digest
    return digest


def binding_file_state(repo_root: Path, materials_root: Path, binding: Mapping[str, object]) -> str:
    """``ok`` when the pinned file exists under materials with its digest."""
    candidate = material_file(materials_root, binding.get("material_relpath"))
    if candidate is None:
        return "stale"
    try:
        digest = file_sha256(candidate)
    except OSError:
        return "stale"
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
