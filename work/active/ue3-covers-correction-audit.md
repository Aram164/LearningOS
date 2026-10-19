# Coverage audit: UE3 route covers correction (single edge)

Scope: one `covers` edge on one route in `module-hu-m2-statistik-analysis`.
Route `route-78ae1df0aa949bb2a8a872dc` (UE3, slides 15-38) claims
`knowledge-sad-l04-bayes`; the reviewed dossier for `unit-m2-sad-l04`
records its diagnostic calculation as total probability *without* posterior
inversion over the inspected pages (UE3.pdf pp. 15-38 of 54). The genuine
Bayes-inversion chain in this unit lives on UE4
(`route-c355ecc8ea7599015a21abfe`, Bayes-Inversion P(J|B)=75/107). The edge
is therefore dropped; the route keeps its event/axiom/conditional/
independence coverage and its `concept-bayes-theorem` assessment tag
(framing vocabulary, not a mastery claim).

## Local

- `curriculum/modules/module-hu-m2-statistik-analysis/source-map.yaml`: one
  route edited, `covers` loses `knowledge-sad-l04-bayes` only. No other
  route, locator, scope, or depth touched.
- Admitting evidence: the unit's own published dossier,
  `curriculum/modules/module-hu-m2-statistik-analysis/units/unit-m2-sad-l04/material-synthesis.yaml`
  (contribution "ohne Posterior-Inversion", evidence UE3 pp. 15-21/25-29/
  31-33/34-38, `scope_of_absence` pp. 15-38 of 54).

## Linked

- Knowledge node `knowledge-sad-l04-bayes` remains covered in this unit by
  UE4 (total-probability to Bayes-inversion to Naive-Bayes chain) and Blatt 2
  routes; no node loses its last covering route in this package.
- No concept, note, source-registry, or workspace record is created,
  renamed, or re-pointed by this package.

## Completeness

- `local_inventory_complete`: the module source map was loaded whole; the
  diff is exactly one edge (verified by plan-import Phase B `changed` set).
- `linked_inventory_complete`: linked nodes checked against the unit
  knowledge maps; nothing orphaned.
- `materials_opened_and_content_checked`: UE3 pp. 15-38 inspected via the
  dossier's slice record (59/59 L04 deck pages across the dossier programme;
  UE3 claim scoped to pp. 15-38 of 54, stated in `scope_of_absence`).
- `current_and_prior_scope_reconciled`: route scope `current` unchanged;
  UE4 prior-year recording route untouched.
- `duplicates_and_numbering_checked`: no route added, removed, or renumbered.
- `exclusions_and_unresolved_gaps_recorded`: the uninspected UE3 pages
  (1-14, 39-54) stay outside every claim via `scope_of_absence`; the 404
  angle-divergence triage debt is baselined separately and untouched here.
