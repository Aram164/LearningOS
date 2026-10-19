# Coverage audit — knowledge_node_id backfill, 14 units (2026-09-20)

Revision scope: add `knowledge_node_id` to the 72 stages currently
warning STAGE-NODE-UNLINKED, per the reviewed decision table
`work/active/node-linkage-backfill-2026-09-20/outputs/decisions.yaml`.
Map-only change in every unit: no route changes, no scope changes,
no renumbering, no learner-state edits. Applied as one
unit-plan-revise revision per unit; this file is the completed audit
each revision references.

## Local

- 14 study maps read whole (stages, objectives, resources) from
  `curriculum/modules/*/units/<unit>/study-map.yaml`:
  unit-m2-sad-exam-prep (15 stages), unit-algo2-exam-prep (14),
  unit-aml-exam-prep (10), unit-m2-combined-exam-rehearsal (5),
  and 9 unit-job-polars-* units (2–4 stages each).
- 14 unit files read for their knowledge maps
  (`units/<unit>/unit.yaml`, `knowledge_map.nodes`): node ids and
  labels verified against every decided key — each key names a node
  of its own unit (asserted mechanically by the splice script).
- Judgment calls (5): M2 s06 stays distributions-side; AML mocks sit
  under integration and taper under error-control; rehearsal repair
  joins switching ("only switching/time errors remain joint");
  polars-01 joins divergence-axes (taught outcome, not the version
  pin). Rationale recorded in decisions.yaml notes. Nodes with no
  stage (aml scope/logistics, polars version-contract) are map-level
  context; the check is per-stage only, so no warning remains.

## Linked

- No `route_changes` in any of the 14 revisions: every linked route
  is carried forward untouched by the revise machinery (verified per
  unit in preflight: routes before == routes after, placements and
  triage unchanged, learner state preserved).
- Route `covers` namespaces already overlap the exam-prep node ids
  (spot-checked: s01 placements cover knowledge-sad-exam-*), so
  linking is not expected to detonate latent orphans; the validator
  is re-run after the backfill and any revealed RESOURCE-NODE-ORPHAN
  is adjudicated before sign-off (see orphan log, same directory).

## Completeness

- All 72 warnings mapped 1:1 to a decided key; the splice script
  asserts exact-once anchors, YAML validity, key presence, and node
  membership per unit. Amended maps live in `maps/` next to the
  decision table; each unit's `--check` diff is reviewed for
  content-changes == knowledge_node_id additions only.
- No exclusions; no unresolved gaps. Orphan adjudication (existing 9
  plus any revealed) is tracked separately and blocks the final
  commit, not each unit revision.
- Checks: local_inventory_complete, linked_inventory_complete,
  materials_opened_and_content_checked, current_and_prior_scope_reconciled,
  duplicates_and_numbering_checked, exclusions_and_unresolved_gaps_recorded —
  all true as evidenced above ("materials" here are the unit
  knowledge maps and study maps, all opened and read).
