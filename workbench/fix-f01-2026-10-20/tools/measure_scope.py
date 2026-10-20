"""Measure the stage-resource scope population on the live corpus.

The loaded study map is *expanded*: ``material_ref`` is popped and its
inherited fields are copied onto the resource (``domain/material_refs.py``
``expand_map``). The authored spelling survives only in
``StudyMap.authored_data``, so the scope rule has to read it there.

Three candidate resolution rules are compared:

* ``pair``   -- (source_id, locator) matches a route of the module;
* ``triple`` -- (source_id, label, locator) matches a route of the module
  (this is ``domain/material_refs.matching_routes``, the machinery the brief
  names);
* ``route``  -- the resource names a route id of the module, spelled either at
  the top level or in the authored ``material_ref``.

Run from a Core checkout:  ``.venv/bin/python <this file>``
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path


def core_root() -> Path:
    """The Core checkout this script measures.

    The script lives in the fixing workbench, beside the Core checkout, and
    is published inside a Core checkout under ``workbench/``. So the root is
    found, not assumed: the nearest ancestor that *is* a Core checkout, or
    else the nearest ancestor with a Core checkout named ``repository``
    beside it.
    """
    here = Path(__file__).resolve()
    for candidate in here.parents:
        if (candidate / "system" / "OPERATOR.md").is_file():
            return candidate
    for candidate in here.parents:
        sibling = candidate / "repository"
        if (sibling / "system" / "OPERATOR.md").is_file():
            return sibling
    raise SystemExit("no Core checkout found above this script")


ROOT = core_root()
sys.path.insert(0, str(ROOT / "tools"))

from learning_os.domain.route_identity import route_with_identity  # noqa: E402
from learning_os.store.loader import load_repo  # noqa: E402


def module_index(repo):
    """Per module: its route ids, its (source, locator) pairs, its routes."""
    ids: dict[str, set[str]] = {}
    pairs: dict[str, set[tuple[str, str]]] = {}
    triples: dict[str, set[tuple[str, str, str]]] = {}
    routes: dict[str, list[dict]] = {}
    sources: dict[str, set[str]] = {}
    for module_id, source_map in repo.module_source_maps.items():
        mid_ids: set[str] = set()
        mid_pairs: set[tuple[str, str]] = set()
        mid_triples: set[tuple[str, str, str]] = set()
        mid_routes: list[dict] = []
        mid_sources: set[str] = set()
        for entry in source_map.get("sources", []) or []:
            if not isinstance(entry, dict):
                continue
            source_id = str(entry.get("source_id") or "")
            mid_sources.add(source_id)
            for route in entry.get("unit_routes", []) or []:
                if not isinstance(route, dict):
                    continue
                projected = route_with_identity(module_id, source_id, route)
                route_id = projected.get("id")
                if isinstance(route_id, str):
                    mid_ids.add(route_id)
                locator = str(route.get("locator") or "")
                title = str(route.get("title") or "")
                mid_pairs.add((source_id, locator))
                mid_triples.add((source_id, title, locator))
                mid_routes.append({**projected, "source_id": source_id})
        ids[module_id] = mid_ids
        pairs[module_id] = mid_pairs
        triples[module_id] = mid_triples
        routes[module_id] = mid_routes
        sources[module_id] = mid_sources
    return ids, pairs, triples, routes, sources


def main() -> int:
    root = ROOT
    repo = load_repo(root)
    ids, pairs, triples, routes, sources = module_index(repo)

    total = 0
    authored_with_material_ref = 0
    authored_material_ref_route_only = 0
    authored_material_ref_foreign = 0
    alignment_mismatch = []
    expanded_with_route_id = 0
    expanded_without_route_id = 0
    bound_by_pair = 0
    bound_by_triple = 0
    bound_by_route = 0
    pair_only = 0
    triple_only = 0
    neither = 0
    neither_kind = collections.Counter()
    neither_source_not_adopted = 0
    neither_detail = collections.Counter()
    neither_examples = []
    route_only_detail = []

    for smid, study_map in repo.study_maps.items():
        unit = repo.units.get(study_map.unit_id)
        module_id = str(unit.data.get("module_id") or "") if unit is not None else ""
        module = repo.modules.get(module_id) if module_id else None
        archived = bool(module and module.get("status") == "archived")
        mid_ids = ids.get(module_id, set())
        mid_pairs = pairs.get(module_id, set())
        mid_triples = triples.get(module_id, set())
        mid_sources = sources.get(module_id, set())

        expanded_rows = []
        expanded_stage_ids = []
        for stage in study_map.data.get("stages", []) or []:
            if not isinstance(stage, dict):
                continue
            for resource in stage.get("resources", []) or []:
                if isinstance(resource, dict):
                    expanded_rows.append((stage.get("id"), resource))
                    expanded_stage_ids.append(stage.get("id"))
        authored_rows = []
        authored_stage_ids = []
        for stage in (study_map.authored_data or {}).get("stages", []) or []:
            if not isinstance(stage, dict):
                continue
            for resource in stage.get("resources", []) or []:
                if isinstance(resource, dict):
                    authored_rows.append((stage.get("id"), resource))
                    authored_stage_ids.append(stage.get("id"))
        if len(authored_rows) != len(expanded_rows) or \
                authored_stage_ids != expanded_stage_ids:
            alignment_mismatch.append(
                {"study_map": smid, "authored": len(authored_rows),
                 "expanded": len(expanded_rows),
                 "authored_stages": authored_stage_ids,
                 "expanded_stages": expanded_stage_ids})

        for index, (stage_id, resource) in enumerate(expanded_rows):
            total += 1
            authored = authored_rows[index][1] if index < len(authored_rows) else {}
            ref = authored.get("material_ref")
            ref_route_id = None
            if isinstance(ref, dict):
                authored_with_material_ref += 1
                ref_route_id = ref.get("route_id")
                if isinstance(ref_route_id, str):
                    if not authored.get("route_id"):
                        authored_material_ref_route_only += 1
                    if ref_route_id not in mid_ids and not archived:
                        authored_material_ref_foreign += 1
                        route_only_detail.append({
                            "study_map": smid, "stage": stage_id,
                            "material_ref_route_id": ref_route_id,
                            "module_id": module_id, "kind": resource.get("kind"),
                        })

            top_route_id = resource.get("route_id")
            has_route = isinstance(top_route_id, str) and top_route_id
            if has_route:
                expanded_with_route_id += 1
                if top_route_id in mid_ids:
                    bound_by_route += 1
                # references.py owns the verdict for a top-level route id
                # (REF-ROUTE / RESOURCE-ROUTE-OWNER are errors there).
                continue
            expanded_without_route_id += 1

            source_id = resource.get("source_id")
            locator = str(resource.get("locator") or "")
            label = str(resource.get("label") or "")
            pair = (source_id, locator) if isinstance(source_id, str) else None
            triple = (source_id, label, locator) if isinstance(source_id, str) else None
            is_pair = pair in mid_pairs
            is_triple = triple in mid_triples
            if is_pair:
                bound_by_pair += 1
            if is_triple:
                bound_by_triple += 1
            if is_pair and not is_triple:
                pair_only += 1
            if is_triple and not is_pair:
                triple_only += 1
            if is_pair or is_triple:
                continue
            if ref_route_id is not None and ref_route_id in mid_ids:
                # Bound by its authored route; the inherited fields drifted.
                bound_by_route += 1
                continue
            neither += 1
            neither_kind[str(resource.get("kind"))] += 1
            if isinstance(source_id, str) and source_id not in mid_sources:
                neither_source_not_adopted += 1
                neither_detail[(module_id, source_id)] += 1
                if len(neither_examples) < 10:
                    neither_examples.append({
                        "study_map": smid, "stage": stage_id,
                        "source_id": source_id, "locator": locator,
                        "kind": resource.get("kind"),
                    })

    out = {
        "stage_resources": total,
        "authored_with_material_ref": authored_with_material_ref,
        "authored_material_ref_without_top_level_route_id":
            authored_material_ref_route_only,
        "authored_material_ref_naming_a_foreign_route": authored_material_ref_foreign,
        "authored_material_ref_foreign_examples": route_only_detail[:10],
        "authored_expanded_alignment_mismatches": alignment_mismatch,
        "expanded_with_top_level_route_id": expanded_with_route_id,
        "expanded_without_top_level_route_id": expanded_without_route_id,
        "bound_by_route_id": bound_by_route,
        "bound_by_pair": bound_by_pair,
        "bound_by_triple": bound_by_triple,
        "pair_resolves_but_triple_does_not": pair_only,
        "triple_resolves_but_pair_does_not": triple_only,
        "unresolved_by_both": neither,
        "unresolved_by_both_kind": dict(neither_kind),
        "unresolved_and_source_never_adopted": neither_source_not_adopted,
        "unresolved_and_source_never_adopted_detail": {
            f"{m}/{s}": n for (m, s), n in neither_detail.most_common(20)},
        "unresolved_examples": neither_examples,
    }
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
