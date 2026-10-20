"""Would a unit-aware scope rule flag anything the module-level rule passes?

The scope rule asks the module's question: does the module's source map
declare this source at this locator? A row that names a *route* is held to
the unit's question as well, because a route belongs to a unit
(`RESOURCE-ROUTE-OWNER`, an error). So the same material, spelled as a
route id, is refused across a unit boundary, and spelled as a source and a
locator, it is not.

This measures the size of that gap on the live corpus: for every row the
module-level rule passes through the (source, locator) path, whose route
does the matching route belong to?

Run from a Core checkout: ``.venv/bin/python <this file>``
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "repository"
sys.path.insert(0, str(ROOT / "tools"))

from learning_os.domain.route_identity import route_with_identity  # noqa: E402
from learning_os.store.loader import load_repo  # noqa: E402


def main() -> int:
    repo = load_repo(ROOT)

    # Per module: the (source, locator) pairs it declares, and the unit that
    # owns each of them.
    scope: dict[str, dict] = {}
    for module_id, source_map in repo.module_source_maps.items():
        pairs: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
        for entry in source_map.get("sources", []) or []:
            if not isinstance(entry, dict):
                continue
            source_id = str(entry.get("source_id") or "")
            for route in entry.get("unit_routes", []) or []:
                if not isinstance(route, dict):
                    continue
                projected = route_with_identity(module_id, source_id, route)
                unit_id = str(projected.get("unit_id") or "")
                pairs[(source_id, str(route.get("locator") or ""))].add(unit_id)
        scope[module_id] = {"pairs": {k: v for k, v in pairs.items()}}

    buckets: collections.Counter = collections.Counter()
    examples: list[dict] = []
    for smid, study_map in repo.study_maps.items():
        unit = repo.units.get(study_map.unit_id)
        module_id = str(unit.data.get("module_id") or "") if unit is not None else ""
        if not module_id:
            continue
        module = repo.modules.get(module_id)
        if module and module.get("status") == "archived":
            continue
        for stage in study_map.data.get("stages", []) or []:
            if not isinstance(stage, dict):
                continue
            for resource in stage.get("resources", []) or []:
                if not isinstance(resource, dict):
                    continue
                if resource.get("kind") == "reference":
                    continue
                if isinstance(resource.get("route_id"), str) and resource["route_id"]:
                    continue  # bound: references.py owns the ownership error
                source_id = resource.get("source_id")
                locator = str(resource.get("locator") or "")
                if not isinstance(source_id, str):
                    continue
                owners = scope.get(module_id, {}).get("pairs", {}).get(
                    (source_id, locator))
                if owners is None:
                    continue  # the module-level rule reports this row
                if study_map.unit_id in owners:
                    buckets["the row's own unit declares it"] += 1
                else:
                    buckets["only a sibling unit declares it"] += 1
                    if len(examples) < 8:
                        examples.append({
                            "study_map": smid,
                            "unit": study_map.unit_id,
                            "stage": stage.get("id"),
                            "source": source_id,
                            "locator": locator,
                            "declared_by": sorted(owners),
                        })

    print(json.dumps({
        "buckets": dict(buckets),
        "examples": examples,
    }, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
