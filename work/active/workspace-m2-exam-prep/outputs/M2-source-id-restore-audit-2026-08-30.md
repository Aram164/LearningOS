# M2 source_id restore — coverage audit, 2026-08-30

Plan package: `work/active/workspace-m2-exam-prep/outputs/M2-source-id-restore-plan-2026-08-30.yaml`

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
| `unit-m2-analysis-ch01` | 3 | 25 | 25 → 0 |
| `unit-m2-analysis-ch02` | 8 | 71 | 71 → 0 |
| `unit-m2-analysis-ch03` | 6 | 86 | 86 → 0 |
| `unit-m2-analysis-ch04` | 4 | 69 | 69 → 0 |
| `unit-m2-analysis-ch05` | 7 | 129 | 129 → 0 |
| `unit-m2-analysis-ch06` | 7 | 127 | 127 → 0 |
| `unit-m2-analysis-ch07` | 3 | 61 | 61 → 0 |
| `unit-m2-analysis-exam-prep` | 3 | 16 | 16 → 0 |
| `unit-m2-sad-clustering` | 5 | 30 | 30 → 0 |
| `unit-m2-sad-l03` | 7 | 70 | 70 → 0 |
| `unit-m2-sad-l04` | 7 | 92 | 92 → 0 |
| `unit-m2-sad-l06` | 7 | 99 | 99 → 0 |
| `unit-m2-sad-l14` | 7 | 54 | 54 → 0 |
| `unit-m2-sad-l15` | 8 | 115 | 115 → 0 |

## Linked

None. This pass consults no external material.

## Completeness

- [x] Every regenerated map is the unmodified output of the assembler CLI.
- [x] No route, locator, angle, `angle_detail`, node, stage or unit order changes.
- [x] The two hand-authored study maps are untouched; their source-less rows are
      original and were not produced by either builder.
- [x] Verified after the import: no stage row in any M2 study map that
      corresponds to a material route lacks `source_id`.
