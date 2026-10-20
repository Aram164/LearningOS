"""Compare candidate scope rules on the live corpus.

The approved rule is route-level: a resource resolves when it names a route
of the module, or when its (source_id, locator) matches one of the module's
routes. The alternative is granularity-aware: a module whose source map
records adoption at route level (rich routes) is held to the locator, and a
module whose map records adoption at source level (legacy unit routes) is
held to the source.

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

    ids: dict[str, set[str]] = {}
    pairs: dict[str, set[tuple[str, str]]] = {}
    sources: dict[str, set[str]] = {}
    rich_sources: dict[str, set[str]] = {}
    for module_id, source_map in repo.module_source_maps.items():
        mid_ids: set[str] = set()
        mid_pairs: set[tuple[str, str]] = set()
        mid_sources: set[str] = set()
        mid_rich: set[str] = set()
        for entry in source_map.get("sources", []) or []:
            if not isinstance(entry, dict):
                continue
            source_id = str(entry.get("source_id") or "")
            mid_sources.add(source_id)
            for route in entry.get("unit_routes", []) or []:
                if not isinstance(route, dict):
                    continue
                mid_rich.add(source_id)
                projected = route_with_identity(module_id, source_id, route)
                route_id = projected.get("id")
                if isinstance(route_id, str):
                    mid_ids.add(route_id)
                mid_pairs.add((source_id, str(route.get("locator") or "")))
        ids[module_id] = mid_ids
        pairs[module_id] = mid_pairs
        sources[module_id] = mid_sources
        rich_sources[module_id] = mid_rich

    route_level = 0
    granularity = 0
    granularity_kind = collections.Counter()
    granularity_by_module = collections.Counter()
    both = 0

    for smid, study_map in repo.study_maps.items():
        unit = repo.units.get(study_map.unit_id)
        module_id = str(unit.data.get("module_id") or "") if unit is not None else ""
        module = repo.modules.get(module_id) if module_id else None
        if module_id and (module and module.get("status") == "archived"):
            continue
        if not module_id:
            continue
        mid_pairs = pairs.get(module_id, set())
        mid_sources = sources.get(module_id, set())
        mid_rich = rich_sources.get(module_id, set())
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
                route_level += 1
                # The granularity-aware reading: a source the module declared
                # but never gave a route to is adopted at source level.
                if isinstance(source_id, str) and source_id in mid_sources \
                        and source_id not in mid_rich:
                    continue
                granularity += 1
                granularity_kind[str(resource.get("kind"))] += 1
                granularity_by_module[module_id] += 1
                both += 1

    out = {
        "route_level_unbound": route_level,
        "granularity_aware_unbound": granularity,
        "granularity_aware_kind": dict(granularity_kind),
        "granularity_aware_by_module": dict(granularity_by_module.most_common()),
    }
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
