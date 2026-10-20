"""What granularity does LearningOS actually adopt material at?

Aram's question about the 274 rows the scope rule reports where the
*source* was adopted by the module but no route declares it: are those
rows incomplete authoring, or a legitimate source-level workflow?

The answer is in the records: a unit's own ``source_selections`` is the
unit-level record of what that unit adopted (OPERATOR.md boundary 14's
"explicitly selected, reference-only, or deferred"), and a module's source
map holds the routes. This measures, for every row the rule reports, which
of those records — if any — already declares the material.

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

    scope: dict[str, dict] = {}
    for module_id, source_map in repo.module_source_maps.items():
        ids: set[str] = set()
        pairs: set[tuple[str, str]] = set()
        sources: set[str] = set()
        rich = 0
        legacy = 0
        for entry in source_map.get("sources", []) or []:
            if not isinstance(entry, dict):
                continue
            source_id = str(entry.get("source_id") or "")
            sources.add(source_id)
            for route in entry.get("unit_routes", []) or []:
                if not isinstance(route, dict):
                    legacy += 1
                    continue
                rich += 1
                projected = route_with_identity(module_id, source_id, route)
                route_id = projected.get("id")
                if isinstance(route_id, str):
                    ids.add(route_id)
                pairs.add((source_id, str(route.get("locator") or "")))
        scope[module_id] = {
            "ids": ids, "pairs": pairs, "sources": sources,
            "rich": rich, "legacy": legacy,
        }

    # What each unit declares for itself.
    selections: dict[str, set[str]] = {}
    scope_sources: dict[str, set[str]] = {}
    for unit_id, unit in repo.units.items():
        data = unit.data or {}
        selections[unit_id] = {
            str(row.get("source_id") or "")
            for row in data.get("source_selections", []) or []
            if isinstance(row, dict)
        }
        scope_sources[unit_id] = {
            str(row.get("source_id") or "")
            for row in data.get("scope_sources", []) or []
            if isinstance(row, dict)
        }

    buckets = collections.Counter()
    detail = collections.Counter()
    examples: list[dict] = []
    for smid, study_map in repo.study_maps.items():
        unit = repo.units.get(study_map.unit_id)
        module_id = str(unit.data.get("module_id") or "") if unit is not None else ""
        module = repo.modules.get(module_id) if module_id else None
        if module_id and (module and module.get("status") == "archived"):
            continue
        mod = scope.get(module_id, {})
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
                if isinstance(source_id, str) and \
                        (source_id, locator) in mod.get("pairs", set()):
                    continue
                if not isinstance(source_id, str):
                    buckets["no source named"] += 1
                    continue
                if source_id not in mod.get("sources", set()):
                    buckets["source never adopted by the module"] += 1
                    detail[("never adopted", module_id)] += 1
                    if len(examples) < 6:
                        examples.append({
                            "study_map": smid, "stage": stage.get("id"),
                            "module": module_id, "source": source_id,
                            "locator": locator,
                            "unit_selects_it": source_id in selections.get(
                                study_map.unit_id, set()),
                        })
                    continue
                # The module declared the source; the question is whether the
                # *unit* declared it too, in its own selections.
                selected = source_id in selections.get(study_map.unit_id, set())
                scoped = source_id in scope_sources.get(study_map.unit_id, set())
                if selected:
                    buckets["module adopted it; the unit selected it"] += 1
                    detail[("unit selected", module_id)] += 1
                elif scoped:
                    buckets["module adopted it; the unit scoped it"] += 1
                    detail[("unit scoped", module_id)] += 1
                else:
                    buckets["module adopted it; no unit record"] += 1
                    detail[("no unit record", module_id)] += 1

    out = {
        "buckets": dict(buckets),
        "by_module": {f"{k[0]} @ {k[1]}": v for k, v in detail.most_common()},
        "module_map_shapes": {
            module_id: {
                "rich_routes": s["rich"],
                "legacy_unit_routes": s["legacy"],
                "declared_sources": len(s["sources"]),
            }
            for module_id, s in scope.items()
            if s["rich"] or s["legacy"]
        },
        "never_adopted_examples": examples,
    }
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
