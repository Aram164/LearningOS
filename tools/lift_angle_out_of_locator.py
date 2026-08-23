#!/usr/bin/env python3
"""Move the angle out of `locator` and into `angle` on assembled study maps.

Until 2026-08-23 `tools/assemble_lecture_study_maps.py` concatenated a route's
angle onto the end of its locator after an em dash. The assembler no longer does
that, but the study maps already on disk still carry the fused string. Running
the assembler again would fix them — this script exists for the case where that
is not possible (it needs the full toolchain, Python 3.12+), and because it is
non-destructive and inspectable in a way a full regeneration is not.

For every study map whose `source_plan.path` is a module source map, each
resource row is matched back to its route by `source_id` + label/title, and the
route's `locator`, `angle` and `angle_detail` are copied onto the row. A row
whose route cannot be found is left exactly as it is and reported.

    python tools/lift_angle_out_of_locator.py [--dry-run]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def route_index(source_map: dict) -> dict[tuple[str, str, str], dict]:
    index: dict[tuple[str, str, str], dict] = {}
    for entry in source_map.get("sources") or []:
        sid = entry.get("source_id")
        for route in entry.get("unit_routes") or []:
            if isinstance(route, dict) and route.get("title"):
                index[(sid, route["unit_id"], route["title"])] = route
    return index


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    changed_files = 0
    changed_rows = 0
    unmatched: list[str] = []

    for map_path in sorted(REPO.glob("curriculum/modules/*/units/*/study-map.yaml")):
        data = load(map_path)
        plan_path = ((data.get("source_plan") or {}).get("path") or "")
        if not plan_path.endswith("source-map.yaml"):
            continue
        source_map_file = REPO / plan_path
        if not source_map_file.is_file():
            continue
        index = route_index(load(source_map_file))
        unit_id = data.get("unit_id")
        touched = False

        for stage in data.get("stages") or []:
            for resource in stage.get("resources") or []:
                if not isinstance(resource, dict):
                    continue
                key = (resource.get("source_id"), unit_id, resource.get("label"))
                route = index.get(key)
                if route is None:
                    unmatched.append(f"{map_path.parent.name}: {key[0]} / {key[2]}")
                    continue
                for field in ("locator", "angle", "angle_detail"):
                    value = route.get(field)
                    if value and resource.get(field) != value:
                        resource[field] = value
                        touched = True
                        changed_rows += 1
                    elif not value and field in resource and field != "locator":
                        del resource[field]
                        touched = True

        if touched:
            changed_files += 1
            if not args.dry_run:
                map_path.write_text(
                    yaml.safe_dump(data, sort_keys=False, allow_unicode=True,
                                   width=108, default_flow_style=False),
                    encoding="utf-8",
                )

    print(f"{'would update' if args.dry_run else 'updated'} "
          f"{changed_rows} resource rows in {changed_files} study maps")
    if unmatched:
        print(f"{len(unmatched)} rows had no matching route and were left alone:")
        for row in unmatched[:20]:
            print(f"   {row}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
