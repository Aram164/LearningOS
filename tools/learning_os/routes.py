"""Stable material-route identity and exact reference resolution.

Canonical route ids are authored fields from data-contract v13 onward.  Older
rich routes remain readable: their projected id is derived deterministically
from the complete pre-v13 identity tuple, and the v13 migration persists that
same value.  Nothing resolves by title alone here; titles are learner-facing
prose and may change without changing the material being addressed.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass

from .loader import Repo

ROUTE_ID_RE = re.compile(r"^route-[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class RouteReference:
    """One rich module-source-map route with its owning identities."""

    route_id: str
    authored_id: bool
    module_id: str
    unit_id: str
    source_id: str
    locator: str
    route: dict


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


def iter_route_references(repo: Repo) -> Iterable[RouteReference]:
    """Yield rich routes only; legacy string edges remain readable separately."""

    for module_id in sorted(repo.module_source_maps):
        source_map = repo.module_source_maps[module_id]
        for entry in source_map.get("sources", []) or []:
            if not isinstance(entry, dict):
                continue
            source_id = entry.get("source_id")
            if not isinstance(source_id, str) or not source_id:
                continue
            for route in entry.get("unit_routes", []) or []:
                if not isinstance(route, dict):
                    continue
                projected = route_with_identity(module_id, source_id, route)
                yield RouteReference(
                    route_id=projected["id"],
                    authored_id=isinstance(route.get("id"), str)
                    and bool(route.get("id")),
                    module_id=module_id,
                    unit_id=str(route.get("unit_id") or ""),
                    source_id=source_id,
                    locator=str(route.get("locator") or ""),
                    route=route,
                )


def exact_selection_matches(
    routes: Iterable[RouteReference],
    *,
    unit_id: str,
    selection: dict,
) -> list[RouteReference]:
    """Resolve a selection using id plus immutable guards, or legacy guards.

    A v13 selection names ``route_id`` and repeats source/locator as drift
    guards.  A pre-v13 selection has only those guards; it resolves only when
    the pair is unique within the owning unit.
    """

    route_id = selection.get("route_id")
    source_id = selection.get("source_id")
    locator = selection.get("locator")
    return [
        route
        for route in routes
        if route.unit_id == unit_id
        and (not route_id or route.route_id == route_id)
        and route.source_id == source_id
        and route.locator == locator
    ]
