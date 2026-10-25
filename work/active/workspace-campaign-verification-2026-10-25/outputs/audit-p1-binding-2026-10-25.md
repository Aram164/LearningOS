# Coverage audit — ch03–ch07 stage-binding migration (L2-16, 2026-10-25)

Scope: rebind the 472 unbound non-reference stage resources of the five
Analysis chapter units to the routes declared for their own unit, as
unit-m2-analysis-ch01 and -ch02 already are. No route changes, no scope
changes, no stage or resource additions or removals, no renumbering. The
migration is acting on critique point 1 (boundary 17), authorised by Aram's
kickoff for item L2-16; prepared as `--check` only, never applied.

## Local

- The five study maps read whole from
  `curriculum/modules/module-hu-m2-statistik-analysis/units/unit-m2-analysis-ch03..ch07/study-map.yaml`;
  the source map read whole from `curriculum/modules/module-hu-m2-statistik-analysis/source-map.yaml`
  (97 sources, 600 routes).
- Every unbound non-reference row (ch03: 86, ch04: 69, ch05: 129, ch06: 127,
  ch07: 61; 472 total, matching CLAUDE-VERDICT.md) was matched against its
  unit's declared routes by exact (label, locator) equality. Each matched
  exactly one route; zero rows unmatched, zero ambiguous.
- The binding rule is the one ch01/ch02 already implement, verified
  mechanically: a stage binds a route exactly when the route's `covers` names
  the stage's knowledge id. ch01: 25 actual = 25 derived; ch02: 71 = 71.
  Applied to ch03–ch07 the same derivation places every one of the 472 rows
  on the stage it already sits on (row placement == covers placement, 0
  deviations), so no resource moves between stages.
- Field equality checked per row: `angle` and `angle_detail` equal the
  matched route's on all 472 rows; `vault_path` equals the route's on 349
  rows and is absent on both sides for the other 123. No row carries a value
  the route lacks, so every binding inherits
  [label, source_id, locator, angle, angle_detail] (+ vault_path where
  present) and the expanded effective map is unchanged except for the added
  `route_id`/`source_id`.
- Materials opened: the tree was validated through the module's own checks in
  the C2 session (all 318 vault_paths resolve, 0 page-range violations) and
  the C2-R re-check; no new material claims are introduced by this package.

## Linked

- All 97 sources and all 600 routes are carried forward untouched: the
  package contains no `source_map`, no `source_patches`, no route identity,
  covers or locator changes. Routes with `covers` but no stage row
  (route-an-ch03/04/05/06/07-henningdierks, route-an-ch03/05/06-wrathofmath —
  8 routes) remain unplaced; adding stage resources for them is a scope
  decision and is out of scope here.

## Completeness

- Every unbound teaching row of the five units is bound to a route declared
  for its own unit; after the package the module's 472
  RESOURCE-SCOPE-UNBOUND warnings of the ch03–ch07 family are gone and no
  resource's material, angle, kind or triage changes.
- Duplicates: the package introduces none — each row binds a distinct
  (stage, route) pair; the three template `angle_detail` pairs among sibling
  routes recorded by the C2 report (F4) are route-level history, untouched.
- Exclusions and unresolved gaps: the 14 potential (route, stage) pairs for
  the 8 never-placed routes named under Linked are excluded as new scope, not
  repair; the 9 prose rows of unit-m2-combined-exam-rehearsal are a separate
  confirmed family, packaged separately (P4).
- Checks: local_inventory_complete, linked_inventory_complete,
  materials_opened_and_content_checked, current_and_prior_scope_reconciled,
  duplicates_and_numbering_checked, exclusions_and_unresolved_gaps_recorded —
  all true as evidenced above.
