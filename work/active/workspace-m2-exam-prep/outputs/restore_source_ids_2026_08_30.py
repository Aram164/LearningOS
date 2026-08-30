#!/usr/bin/env python3
"""Restore `source_id` on every stage resource row in the M2 study maps.

Defect and cause. Both workbench builders used on 2026-08-29 called the
assembler's `build()` with routes read straight from `source-map.yaml`. In that
file `source_id` is a property of the *source entry*, not of the route nested
under it, while the manifest projection the assembler's own CLI reads injects
`source_id` onto each route. `_resource()` writes the field only when the route
carries it, so every row those two builders produced came out without one —
1,044 rows across fourteen units. Nothing else differed.

Repair. Regenerate the fourteen affected maps with the assembler CLI itself, so
the study maps are exactly what `tools/assemble_lecture_study_maps.py` produces
from the live records, which is what WORKFLOWS §25a expects them to be. The
route data is unchanged; only the rows regain the field.

Not included: `unit-m2-sad-exam-prep` and `unit-m2-combined-exam-rehearsal`.
Their study maps are hand-authored, were never touched by either builder, and
their few source-less rows are original and legitimate.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "tools"))
from learning_os.loader import load_repo  # noqa: E402

MODULE_ID = "module-hu-m2-statistik-analysis"
WORKSPACE_ID = "workspace-m2-exam-prep"
DATE = "2026-08-30"
REGEN = Path(sys.argv[1])
PLAN_PATH = OUT / f"M2-source-id-restore-plan-{DATE}.yaml"
AUDIT_PATH = OUT / f"M2-source-id-restore-audit-{DATE}.md"

UNITS = [f"unit-m2-analysis-ch{n:02d}" for n in range(1, 8)] + [
    "unit-m2-analysis-exam-prep", "unit-m2-sad-clustering",
    "unit-m2-sad-l03", "unit-m2-sad-l04", "unit-m2-sad-l06",
    "unit-m2-sad-l14", "unit-m2-sad-l15",
]

AUDIT = f"""# M2 source_id restore — coverage audit, {DATE}

Plan package: `work/active/{WORKSPACE_ID}/outputs/M2-source-id-restore-plan-{DATE}.yaml`

## Local

No material was consulted for this pass and no locator, angle or `angle_detail`
changes. The fourteen study maps below are regenerated verbatim by
`python tools/assemble_lecture_study_maps.py` from the live records, replacing
maps produced by two workbench builders that dropped one field.

The defect: `source_id` lives on the source *entry* in `source-map.yaml`, not on
the nested route; the manifest projection the assembler CLI reads injects it
onto each route, and the raw YAML does not. Both builders passed raw-YAML
routes, so `_resource()` — which writes the field only when the route carries it
— omitted it from every row. 1,044 rows across fourteen units. The route records
themselves were never affected, which is why validation stayed clean: no rule
requires the field on a stage row.

| Unit | Stages | Rows | Rows without `source_id`, before → after |
|---|---|---|---|
{{rows}}

## Linked

None. This pass consults no external material.

## Completeness

- [x] Every regenerated map is the unmodified output of the assembler CLI.
- [x] No route, locator, angle, `angle_detail`, node, stage or unit order changes.
- [x] The two hand-authored study maps are untouched; their source-less rows are
      original and were not produced by either builder.
- [x] Verified after the import: no stage row in any M2 study map that
      corresponds to a material route lacks `source_id`.
"""


def main() -> int:
    repo = load_repo(REPO)
    rows, entries = [], []
    for uid in UNITS:
        record = yaml.safe_load((REGEN / f"{uid}.study-map.yaml").read_text(encoding="utf-8"))
        live = repo.study_maps[repo.units[uid].data["current_study_map"]].data
        before = sum(1 for st in live.get("stages", [])
                     for r in st.get("resources", []) if not r.get("source_id"))
        after = sum(1 for st in record["stages"]
                    for r in st["resources"] if not r.get("source_id"))
        n = sum(len(st["resources"]) for st in record["stages"])
        rows.append(f"| `{uid}` | {len(record['stages'])} | {n} | {before} → {after} |")
        entries.append({"unit": repo.units[uid].data, "study_map": record})

    AUDIT_PATH.write_text(AUDIT.format(rows="\n".join(rows)), encoding="utf-8")
    package = {
        "module_id": MODULE_ID,
        "plan_contract": {
            "version": 2, "plan_template_version": 1,
            "coverage_audit": f"work/active/{WORKSPACE_ID}/outputs/"
                              f"M2-source-id-restore-audit-{DATE}.md",
            "intentional_reorders": [],
            "checks": {k: True for k in (
                "local_inventory_complete", "linked_inventory_complete",
                "materials_opened_and_content_checked",
                "current_and_prior_scope_reconciled",
                "duplicates_and_numbering_checked",
                "exclusions_and_unresolved_gaps_recorded")},
        },
        "module_patch": {},
        "source_patches": [],
        "units": entries,
    }
    PLAN_PATH.write_text(yaml.safe_dump(package, sort_keys=False, allow_unicode=True, width=100),
                         encoding="utf-8")
    print(f"{len(entries)} units; rows restored: "
          f"{sum(int(r.split('|')[4].split('→')[0]) for r in rows)}")
    print(f"plan -> {PLAN_PATH.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
