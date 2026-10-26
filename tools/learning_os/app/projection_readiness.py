"""Shared projection/receipt observation (D07).

Cheap polling reads only the identity sidecar and manifest stamp; final
readiness validates stamps through the manifest identity owner. A sidecar
alone is a hint, never authority. Two modes: agent dependency (strict
latest-required-known-write) and UI settlement (historical receipt +
valid current projection).
"""
from __future__ import annotations

import json
from pathlib import Path


def _stamps(root: Path) -> tuple[str | None, str | None]:
    try:
        manifest = json.loads((root / "generated/manifest.json").read_text(encoding="utf-8"))
        identity = json.loads((root / "generated/manifest.identity.json").read_text(encoding="utf-8"))
        return manifest["_generated"]["snapshot_id"], identity["snapshot_id"]
    except (OSError, ValueError, KeyError, TypeError):
        return None, None


def observe(root: Path) -> dict[str, object]:
    stamp, identity_stamp = _stamps(Path(root))
    published = stamp is not None and stamp == identity_stamp
    return {"snapshot_id": stamp if published else None,
            "published": published,
            "reason": "ready" if published else "projection-publication-pending"}


def receipt_completed(root: Path, receipt_path: str | None, snapshot_after: str | None) -> bool:
    if not receipt_path or not snapshot_after:
        return False
    path = (Path(root) / receipt_path).resolve()
    return path.is_relative_to(Path(root).resolve()) and path.is_file()


def dependency_ready(root: Path, required: list[dict[str, str | None]], known: list[dict[str, str | None]]) -> tuple[bool, str]:
    """Strict agent mode: current projection at/after latest required write."""
    for item in required:
        if not receipt_completed(root, item.get("receipt_path"), item.get("snapshot_after")):
            return False, "receipt-missing-or-unbound"
    if not required:
        return True, "ready"
    positions = {r.get("snapshot_after"): i for i, r in enumerate(known)
                 if receipt_completed(root, r.get("receipt_path"), r.get("snapshot_after"))}
    sigs = {r.get("snapshot_after") for r in required}
    if not sigs.issubset(positions):
        return False, "required-write-not-known"
    latest = max(positions[s] for s in sigs)
    allowed = {r.get("snapshot_after") for r in known[latest:]
               if receipt_completed(root, r.get("receipt_path"), r.get("snapshot_after"))}
    obs = observe(root)
    if not obs["published"]:
        return False, str(obs["reason"])
    if obs["snapshot_id"] not in allowed:
        return False, "projection-not-current"
    return True, "ready"


def settlement_ready(root: Path, receipt_path: str | None, snapshot_after: str | None) -> dict[str, object]:
    """UI mode: historical receipt completed + current valid projection."""
    done = receipt_completed(root, receipt_path, snapshot_after)
    obs = observe(root)
    return {"write_completed": done, "current_snapshot_id": obs["snapshot_id"],
            "settled": bool(done and obs["published"])}
