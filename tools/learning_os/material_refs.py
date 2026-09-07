"""Lossless stage material references to the owning unit's source-map routes.

Authored maps may be compact; the loaded model and public manifest stay fully
expanded. An explicit field list preserves absence and stage-specific overrides.
There is no cross-unit fallback and no title-only identity resolution.
"""

from __future__ import annotations

import copy
import json

from .route_identity import ROUTE_ID_RE, route_with_identity

MATERIAL_FIELDS = {
    "label": "title", "source_id": "source_id", "locator": "locator",
    "angle": "angle", "angle_detail": "angle_detail", "url": "url",
    "vault_path": "vault_path",
}
PATCH_FIELDS = frozenset(MATERIAL_FIELDS.values()) - {"source_id"}


class MaterialReferenceError(ValueError):
    pass


def unit_routes(source_map: dict, module_id: str, unit_id: str) -> list[dict]:
    rows = []
    sources = source_map.get("sources", [])
    if not isinstance(sources, list):
        return rows
    for entry in sources:
        if not isinstance(entry, dict):
            continue
        routes = entry.get("unit_routes", [])
        if not isinstance(routes, list):
            continue
        for route in routes:
            if isinstance(route, dict) and route.get("unit_id") == unit_id:
                rows.append({
                    **route_with_identity(module_id, str(entry.get("source_id") or ""), route),
                    "source_id": entry.get("source_id"),
                })
    return rows


def matching_routes(resource: dict, routes: list[dict]) -> list[dict]:
    """Legacy candidates require all exact source, title and locator guards."""
    if resource.get("route_id"):
        return [r for r in routes if r["id"] == resource["route_id"]]
    if not all(resource.get(k) for k in ("source_id", "label", "locator")):
        return []
    return [r for r in routes if (
        r.get("source_id"), r.get("title"), r.get("locator")
    ) == (resource["source_id"], resource["label"], resource["locator"])]


def expand_map(data: dict, source_map: dict, module_id: str, unit_id: str) -> dict:
    expanded = copy.deepcopy(data)
    routes = unit_routes(source_map, module_id, unit_id)
    stages = expanded.get("stages", [])
    if not isinstance(stages, list):
        return expanded
    for stage in stages:
        if not isinstance(stage, dict):
            continue
        resources = stage.get("resources", [])
        if not isinstance(resources, list):
            continue
        for resource in resources:
            if not isinstance(resource, dict) or "material_ref" not in resource:
                continue
            ref = resource.pop("material_ref")
            if not isinstance(ref, dict) or set(ref) != {"route_id", "inherit"}:
                raise MaterialReferenceError("material_ref requires only route_id and inherit")
            rid, fields = ref["route_id"], ref["inherit"]
            if not isinstance(rid, str) or not ROUTE_ID_RE.fullmatch(rid):
                raise MaterialReferenceError("material_ref has an invalid route_id")
            if not isinstance(fields, list) or not fields or any(
                not isinstance(k, str) or k not in MATERIAL_FIELDS for k in fields
            ) or len(set(fields)) != len(fields):
                raise MaterialReferenceError("material_ref inherit must name unique material fields")
            matches = [r for r in routes if r["id"] == rid]
            if len(matches) != 1:
                raise MaterialReferenceError(f"material_ref {rid} is missing or ambiguous in {unit_id}")
            route = matches[0]
            if resource.get("route_id", rid) != rid:
                raise MaterialReferenceError("material_ref conflicts with the resource route_id")
            for field in fields:
                if field in resource:
                    raise MaterialReferenceError(f"material_ref cannot also override inherited {field}")
                owner_field = MATERIAL_FIELDS[field]
                if owner_field not in route:
                    raise MaterialReferenceError(f"material_ref {rid} has no {owner_field} to inherit")
                resource[field] = copy.deepcopy(route[owner_field])
            if resource.get("source_id", route.get("source_id")) != route.get("source_id"):
                raise MaterialReferenceError("material_ref conflicts with the resource source_id")
    return expanded


def compact_map(data: dict, source_map: dict, module_id: str, unit_id: str) -> tuple[dict, set[str]]:
    """Link only exactly equal fields and retain every independent resource.

    Returns the routes whose ids the caller must persist in the same transaction.
    Existing references remain intact; this operation never rewrites wording.
    """
    compact = copy.deepcopy(data)
    routes = unit_routes(source_map, module_id, unit_id)
    used = set()
    def size(row):
        return len(json.dumps(row, ensure_ascii=False, separators=(",", ":")).encode())
    for stage in compact.get("stages", []) or []:
        if not isinstance(stage, dict):
            continue
        for index, resource in enumerate(stage.get("resources", []) or []):
            if not isinstance(resource, dict) or "material_ref" in resource:
                continue
            matches = matching_routes(resource, routes)
            if len(matches) != 1:
                continue
            route = matches[0]
            inherited = [k for k, v in resource.items() if k in MATERIAL_FIELDS
                         and MATERIAL_FIELDS[k] in route and v == route[MATERIAL_FIELDS[k]]]
            if not inherited:
                continue
            ref = {"route_id": route["id"], "inherit": inherited}
            candidate = {"material_ref": ref,
                         **{k: v for k, v in resource.items() if k not in inherited}}
            if size(candidate) >= size(resource):
                continue
            stage["resources"][index] = candidate
            used.add(route["id"])
    if expand_map(compact, source_map, module_id, unit_id) != expand_map(
        data, source_map, module_id, unit_id,
    ):
        raise MaterialReferenceError("material compaction changed the effective study map")
    return compact, used


def persist_route_ids(source_map: dict, module_id: str, wanted: set[str]) -> dict:
    output = copy.deepcopy(source_map)
    for entry in output.get("sources", []) or []:
        if not isinstance(entry, dict):
            continue
        for route in entry.get("unit_routes", []) or []:
            if isinstance(route, dict):
                rid = route_with_identity(module_id, str(entry.get("source_id") or ""), route)["id"]
                if rid in wanted:
                    route["id"] = rid
    return output


def preserve_map_refs(study_map, data: dict) -> dict:
    """Keep compact storage during progress/note/feedback saves.

    Only fields unchanged from the loaded effective resource keep inheritance.
    An edited field becomes an explicit override instead of being discarded.
    """
    authored = study_map.authored_data
    if authored is None:
        return data
    output = copy.deepcopy(data)
    raw_stages = {s.get("id"): s for s in authored.get("stages", []) if isinstance(s, dict)}
    old_stages = {s.get("id"): s for s in study_map.data.get("stages", []) if isinstance(s, dict)}
    for stage in output.get("stages", []):
        if not isinstance(stage, dict):
            continue
        raw = raw_stages.get(stage.get("id"), {}).get("resources", [])
        old = old_stages.get(stage.get("id"), {}).get("resources", [])
        for i, resource in enumerate(stage.get("resources", [])):
            if not isinstance(resource, dict) or "material_ref" in resource or i >= min(len(raw), len(old)):
                continue
            ref = raw[i].get("material_ref") if isinstance(raw[i], dict) else None
            previous = old[i]
            if not ref or not isinstance(previous, dict) or any(
                resource.get(k) != previous.get(k) for k in ("id", "route_id", "source_id")
            ):
                continue
            if not previous.get("route_id") and any(
                resource.get(k) != previous.get(k) for k in ("label", "locator")
            ):
                # An expanded replacement may reorder resources. Without an
                # explicit route identity, position and source alone cannot
                # establish that the new resource still has the same owner.
                continue
            fields = [k for k in ref["inherit"] if k in resource and resource[k] == previous[k]]
            if fields:
                stage["resources"][i] = {
                    "material_ref": {"route_id": ref["route_id"], "inherit": fields},
                    **{k: v for k, v in resource.items() if k not in fields},
                }
    return output
