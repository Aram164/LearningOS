"""Pure route identity shared by loading, projection and governed edits."""

from __future__ import annotations

import hashlib
import json
import re

ROUTE_ID_RE = re.compile(r"^route-[a-z0-9]+(?:-[a-z0-9]+)*$")


def deterministic_route_id(
    module_id: str,
    source_id: str,
    route: dict,
) -> str:
    """Return the v13 migration id for a pre-v13 rich route.

    The hash input is canonical JSON rather than a concatenated display label,
    so separators inside authored text cannot create accidental aliases.  Once
    persisted, the id is never recomputed when prose changes.
    """

    identity = {
        "module_id": module_id,
        "source_id": source_id,
        "unit_id": str(route.get("unit_id") or ""),
        "title": str(route.get("title") or ""),
        "locator": str(route.get("locator") or ""),
        "url": str(route.get("url") or ""),
        "vault_path": str(route.get("vault_path") or ""),
    }
    encoded = json.dumps(
        identity,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"route-{hashlib.sha256(encoded).hexdigest()[:24]}"


def route_with_identity(module_id: str, source_id: str, route: dict) -> dict:
    """Copy a rich route and ensure its stable public id is present."""

    route_id = route.get("id")
    if not isinstance(route_id, str) or not route_id:
        route_id = deterministic_route_id(module_id, source_id, route)
    return {**route, "id": route_id}
