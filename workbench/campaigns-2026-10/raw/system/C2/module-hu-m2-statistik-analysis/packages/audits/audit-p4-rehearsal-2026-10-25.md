# Coverage audit — combined-exam-rehearsal prose rows (L2-16, 2026-10-25)

Scope: bind the 9 unbound teaching rows of unit-m2-combined-exam-rehearsal to
the routes declared for that unit, confirmed by C2 REPORT F2 (9 × "the unit's
source disposition is recorded, but no route for this unit matches this
source and locator") and CLAUDE-VERDICT.md ("all 481 real"). `--check` only,
never applied.

## Local

- The unit's study map read whole; the source map read whole. The unit has
  exactly one declared route per source across its four sources with rows
  (source-analysis-skript → route-686945337831d30097efd0a5,
  source-sad-ss26-lectures → route-eb5c6b1b09ac69064d94ade3,
  source-sad-uebungen → route-bba83db0dc9d9f588c11fe61,
  source-sad-klausuren-extern → route-1db639dec976a8c8a14a9bbc,
  source-analysis-klausuren-extern → route-b52242711bc5df661f001fa7,
  source-fau-klausur-ws1415 → route-16b01eb7e461c69ae61e851a): 6 routes, 9
  unbound rows, every row's source_id unambiguous.
- Each row's prose locator is a stage-specific re-description of its route's
  declared locator (the C2 report's reading; re-confirmed row by row this
  session). The binding inherits `source_id` only and keeps every
  stage-specific label, locator, angle and angle_detail verbatim as
  overrides, so the effective teaching content is unchanged.

## Linked

- All six routes carried forward untouched; no source map in the package, no
  route or source edits anywhere else in the module.

## Completeness

- All 9 RESOURCE-SCOPE-UNBOUND warnings of the unit are resolved by binding;
  no row's material claim changes.
- Duplicates: none introduced (each row binds the one route its source
  declares; two rows per route occur only where two stages genuinely draw on
  the same source, matching the routes' own two-mock design).
- Known deviation, recorded: the unit's routes carry coarse covers
  (knowledge-m2-joint-blueprint, knowledge-m2-joint-simulation) that predate
  the mock-one/mock-two/repair stage split, so the ch01/ch02 covers-derived
  placement rule does not reproduce these nine placements mechanically. The
  binding rests on the validator's own remediation for this exact warning
  ("bind the resource to a declared route for this unit") and on one-route-
  per-source uniqueness; no covers are edited.
- Exclusions: none. Unresolved gaps: none.
- Checks: local_inventory_complete, linked_inventory_complete,
  materials_opened_and_content_checked, current_and_prior_scope_reconciled,
  duplicates_and_numbering_checked, exclusions_and_unresolved_gaps_recorded —
  all true as evidenced above.
