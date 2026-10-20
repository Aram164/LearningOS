"""Per-module breakdown of the pair-unresolved stage resources.

For every stage resource that the (source_id, locator) pair rule does not
resolve, report: the owning module, whether the module declares the
resource's source at all, whether the module gives that source a rich route,
and the row's kind. This is the fact base for choosing the rule's shape.

Run from a Core checkout:  ``.venv/bin/python <this file>``
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "repository" / "tools"))

from learning_os.domain.route_identity import route_with_identity  # noqa: E402
from learning_os.store.loader import load_repo  # noqa: E402


def main() -> int:
    root = Path(__file__).resolve().parents[2] / "repository"
    repo = load_repo(root)

    declared: dict[str, set[str]] = {}
    rich: dict[str, set[str]] = {}
    pairs: dict[str, set[tuple[str, str]]] = {}
    route_count: dict[str, int] = {}
    for module_id, source_map in repo.module_source_maps.items():
        mid_declared: set[str] = set()
        mid_rich: set[str] = set()
        mid_pairs: set[tuple[str, str]] = set()
        count = 0
        for entry in source_map.get("sources", []) or []:
            if not isinstance(entry, dict):
                continue
            source_id = str(entry.get("source_id") or "")
            mid_declared.add(source_id)
            for route in entry.get("unit_routes", []) or []:
                if not isinstance(route, dict):
                    continue
                count += 1
                mid_rich.add(source_id)
                mid_pairs.add((source_id, str(route.get("locator") or "")))
        declared[module_id] = mid_declared
        rich[module_id] = mid_rich
        pairs[module_id] = mid_pairs
        route_count[module_id] = count

    per_module: dict[str, collections.Counter] = collections.defaultdict(
        collections.Counter)
    for smid, study_map in repo.study_maps.items():
        unit = repo.units.get(study_map.unit_id)
        module_id = str(unit.data.get("module_id") or "") if unit is not None else ""
        module = repo.modules.get(module_id) if module_id else None
        if module_id and (module and module.get("status") == "archived"):
            continue
        if not module_id:
            continue
        mid_pairs = pairs.get(module_id, set())
        for stage in study_map.data.get("stages", []) or []:
            if not isinstance(stage, dict):
                continue
            for resource in stage.get("resources", []) or []:
                if not isinstance(resource, dict):
                    continue
                if resource.get("kind") == "reference":
                    continue
                if isinstance(resource.get("route_id"), str) and resource["route_id"]:
                    continue
                source_id = resource.get("source_id")
                locator = str(resource.get("locator") or "")
                pair = (source_id, locator) if isinstance(source_id, str) else None
                if pair is not None and pair in mid_pairs:
                    continue
                source = str(source_id)
                is_declared = source in declared.get(module_id, set())
                has_rich = source in rich.get(module_id, set())
                if not is_declared:
                    bucket = "source-not-declared"
                elif has_rich:
                    bucket = "source-declared-with-rich-route"
                else:
                    bucket = "source-declared-source-level-only"
                per_module[module_id][bucket] += 1
                per_module[module_id]["kind:" + str(resource.get("kind"))] += 1

    out = {
        "module": {
            module_id: {
                "rich_routes": route_count.get(module_id, 0),
                "declared_sources": len(declared.get(module_id, set())),
                "buckets": dict(counter),
            }
            for module_id, counter in sorted(per_module.items())
        },
    }
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
