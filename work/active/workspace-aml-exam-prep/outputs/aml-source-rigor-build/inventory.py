"""Print the current AML route-rigor inventory for P2/P3 authoring.

Read-only helper: it uses the validator's own locator predicates so the phase
builders and the warning gate classify the same rows.
"""

from __future__ import annotations

import json
import sys
import argparse

import builder

sys.path.insert(0, str(builder.REPO))
from tools.learning_os.loader import load_repo
from tools.learning_os.rules.plan_rigor import (
    _ADDRESSED_FORMATS,
    _HEDGE_RE,
    _NAMED_ITEM_RE,
    _PAGE_NUMBER_RE,
    _PAGE_RE,
    _PAGED_FORMATS,
)


def locator_is_vague(route: dict) -> bool:
    locator = str(route.get("locator") or "").strip()
    if not locator:
        return False
    fmt = str(route.get("format") or "")
    if fmt in _PAGED_FORMATS:
        return not bool(_PAGE_NUMBER_RE.search(locator))
    if fmt in _ADDRESSED_FORMATS:
        return bool(_HEDGE_RE.search(locator)) or not bool(
            _PAGE_RE.search(locator) or _NAMED_ITEM_RE.search(locator)
        )
    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=("all", "local", "web"), default="all")
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()
    repo = load_repo(builder.REPO)
    source_map = builder.load_map()
    rows = []
    for entry in source_map["sources"]:
        source_id = entry["source_id"]
        source = repo.sources[source_id]
        registered_material = source.get("material")
        for route in entry.get("unit_routes") or []:
            if not locator_is_vague(route):
                continue
            target = route.get("vault_path") or registered_material
            local = isinstance(target, str) and target.startswith("material://")
            rows.append(
                {
                    "source_id": source_id,
                    "route_id": route["id"],
                    "unit_id": route["unit_id"],
                    "format": route.get("format"),
                    "locator": route.get("locator"),
                    "registered_material": registered_material,
                    "route_vault_path": route.get("vault_path"),
                    "url": route.get("url") or source.get("url"),
                    "local": local,
                }
            )
    selected = rows
    if args.kind == "local":
        selected = [row for row in rows if row["local"]]
    elif args.kind == "web":
        selected = [row for row in rows if not row["local"]]
    if args.compact:
        for row in selected:
            print("\t".join(str(row.get(key) or "") for key in (
                "source_id", "route_id", "unit_id", "format", "locator",
                "registered_material", "url",
            )))
    else:
        print(json.dumps(selected, indent=2, ensure_ascii=False))
    local = sum(row["local"] for row in rows)
    print(f"# vague={len(rows)} local={local} web={len(rows) - local}")


if __name__ == "__main__":
    main()
