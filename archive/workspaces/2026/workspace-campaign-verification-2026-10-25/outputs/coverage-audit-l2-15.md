# Coverage audit — unit-aml-exam-prep fix packages (L2-15, 2026-10-24)

Prepared in the C2 clone (`~/los-glm-C2-2026-10/repository`, branch
`takeover/complete-and-install-2026-10-23` at `a2e2d49d`) under Aram's
authorization to act on critique point 1 by preparing `module-plan-import
--check` packages only — nothing here is applied. Evidence base:
`C2/module-hu-aml/REPORT.md` (L2-7) as confirmed by
`C2/module-hu-aml/CLAUDE-VERDICT.md` and `L1-234-CLAUDE-VERDICT.md`.

## Local

Scope of the two packages: `curriculum/modules/module-hu-aml/units/unit-aml-exam-prep/study-map.yaml`
only — 10 stages, 46 resource rows. No source-map route is added, updated or
removed (`route_changes` empty); all 9 exam-prep routes already declared on
2026-09-11 are reused as-is.

- Package F1 (printed-page anchors): full resources arrays for
  `stage-aml-foundations-repair`, `stage-aml-linear-optimization-repair`,
  `stage-aml-neural-transformer-loop`; in each, only the `source-murphy-pml1`
  row's `locator` changes (printed page now also carries its PDF page, per the
  verdict's "write both numbers"). 6 locator substitutions, each asserted to
  hit exactly once. 14/14 sub-anchors re-verified against `pml1.pdf` (860 pp.)
  in this clone on 2026-10-24: pdf p.402/410/307/319/328/331/548/549/551/556/
  557/558/559/562 each print the claimed printed number in its own header.
- Package F2 (unbound rows): full resources arrays for the 9 stages holding at
  least one bindable row; 17 of the 31 `RESOURCE-SCOPE-UNBOUND` rows gain
  `material_ref` bindings to their material's own declared route, inheriting
  only `angle` and `angle_detail` (each row keeps its reviewed label, source_id
  and locator as an explicit stage-specific override). Every binding was
  asserted against the target row's source_id and locator head before writing,
  and checked against the route's declared span in the source map.

## Linked

Every bound row's route and the material it declares:

- `route-9be11f4c735b1fab72ff7fd5` — lecture-slides VL 01–11 (6 rows: the VL
  deck rows of stages 2/3/4, the integration-stage deck row, and the two
  mock-stage VL rows).
- `route-b3c9cda951cabf0f92743436` — exercise-slides Übung 02–11 +
  bonus-exercises/zusatz-blatt01-04 (6 rows: calibration, foundations Übung
  02–07, Übung 08, Übung 09–11, mock-1-repair unused items).
- `route-5f890476996a6d9847807cc6` — Übung 10 slides 2–3 (3 rows: mock-one
  first-sitting rules, mock-two sitting conditions).
- `route-53277505603f22eedc9d81b7` — Géron Ch 3/11/14/16 pdf spans (2 rows: the
  Ch 11 optimizers row, the Ch 14 + Ch 16 row; both rows' named pages lie
  inside the route's declared spans).
- `route-9b89cb595b8b44604cd30acf` — D2L Ch 11 sections 11.1/11.3/11.5/11.6/
  11.7 with Exercises (3 rows: neural-arc row and the two conditional repair
  rows, whose section sets are exactly the route's).

`materials/` was read in place, read-only, through the clone's mounted symlink;
nothing wrote to the materials tree.

## Completeness

Disposition of all 46 rows, so nothing is silently dropped:

- 17 rows bound by package F2 (listed above).
- 3 rows edited by package F1 (the `source-murphy-pml1` rows). The two
  packages are both cut against base `a2e2d49d` and overlap on the three F1
  stages' full resources arrays, so neither applies cleanly after the other
  unchanged: apply one, then re-cut the other against the resulting map — or
  use the prepared combined package, which carries both edits in one batch.
- 1 row already route-equivalent without a binding (Übung 10 slides 2–3,
  calibration stage — its (source_id, locator) equals
  `route-5f890476996a6d9847807cc6`'s pair, so the validator already passes it).
- 8 rows are `kind: reference` pointers, exempt from the scope check by design.
- 17 rows remain unbound and stay byte-identical; each needs a decision no
  package should make for Aram:
  - 9 knowledge-note menu rows (mock/artifact menus) name vault notes, not
    materials; no exam-prep route can carry them. The unapplied 2026-09-11 r2
    plan kept the same rows unbound.
  - `Primer_Linear_Algebra.pdf` (calibration) is named by no exam-prep route.
  - geron Ch 4 'Training Models' (foundations) is outside
    `route-53277505603f22eedc9d81b7`'s declared span, so binding it there would
    mis-declare; it needs its own route.
  - The two "owning module record plus Übung 10 slide 2" rows (final repair,
    taper) name `module.yaml` as material; no route carries a vault record.
  - "Unused Übung/Bonusblatt and per-lecture mock items" (final repair) names
    two banks, one of which (the mocks) has no route.

The six checks below are attested on the L2-7 measurements re-verified for the
touched rows in this clone: local/linked inventories above; materials content
checked (F1 anchors re-verified in the PDF today; every bound row's files and
sections lie inside its route's verified span); current and prior scope
reconciled against the 08-19/08-22 originals and the unapplied 09-11 r2 plan;
duplicates and numbering checked (0 duplicate locator strings among exam-prep
routes and stage rows, L2-7 check D, re-run unchanged); exclusions recorded in
the residue list above.
