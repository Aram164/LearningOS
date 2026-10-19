# Coverage audit — unit-m2-sad-l06 revision (2026-09-20)

Revision scope: five locator/angle corrections on the L06 deck resource of
stages 1–4 (findings F1–F5 of the L06 angle-verification pilot). No route
changes, no scope changes, no renumbering.

## Local

- `study-map-m2-sad-l06` (plan_template_version 1, 7 stages, ids
  stage-sad-l06-{random-variable,distribution-functions,transformations,
  expectation,variance-covariance,sample-mean,concentration}, numbers 1–7):
  read whole (1428 lines) from
  `curriculum/modules/module-hu-m2-statistik-analysis/units/unit-m2-sad-l06/study-map.yaml`.
- `lecture-slides/06_random_variables.pdf` opened via the text cache
  (`material-text`), physical PDF pp. 1–65 read end to end; triage grades
  7/7 accept on first-promoted chapter summaries (see pilot record).
- Übung sheets 3 and 4 (SS26) cross-checked for the practice cross-refs
  (Blatt 3 Aufgabe 1(a–c), Blatt 4 slides 18–34).

## Linked

- All 26 linked routes are carried forward untouched (no `route_changes`):
  route-0374705a29ffc770fc54d9b5, route-17d9d905adfee01ec54791b3,
  route-1eef53180bda2e4604a22a8b, route-25ae05c5bd133243f7bf98aa,
  route-2da0864f340f4e794158cc61, route-30bde2200182449152e8a76a,
  route-37cd5e058977f4aa2f38ee19, route-50eef5af02021332775370be,
  route-571bc192e073618471ea3070, route-64aa48498fe151c8b1c69305,
  route-676e8ea98543e3a7b4f466aa, route-6c6e7ac821cf1bae2d53a9a8,
  route-72c1b94d7d00068b9f8e041c, route-765e4fe569b646edb22ebb28,
  route-a2e6fc0559d93d22efbe732a, route-a336d6454947c097344796b8,
  route-bf37d8f974813af543f007f3, route-dc5505c84e252627c48530c2,
  route-e5bf24802d93851f78b83c03, route-e6e54c18328cf55e09658980,
  route-e7975557941ab093de08152e, route-e802263b373da3ed751ef42c,
  route-ed70c98ed67d50954e43222f, route-faf05b9239ca317a12713779,
  route-sad-l06-covariance, route-sad-l06-transformations.
- Pilot evidence: `work/active/workspace-m2-exam-prep/outputs/sad-l06-angle-verification-2026-09-20.md`
  (grades, confirmed angles, findings F1–F6).

## Completeness

- F1: stage 3 deck locator `pp. 28-30,39` → `pp. 28-31,38` (p. 39 belongs to
  the variance derivation; the Z→Z² worked table is p. 38).
- F2: stage 1 deck locator `pp. 5-8,18` → `pp. 5-8,18-19` (the P=0 claim is
  made on p. 19).
- F3: stage 2 angle_detail p. 21 reworded to carry both models explicitly
  (discrete-minutes as stated: P(X≤3)=0.4, P(X>4)=0.5 with the printed F(4)
  a slip for F(3); continuous-U(0,10) reading: F(x)=x/10, P(X≤3)=0.3,
  P(X>4)=0.6). Approved by Aram 2026-09-20 ("apply and agreed").
- F4: stage 3 LOTUS wording corrected (formula unnamed on p. 28) and the
  many-to-one sentence anchored to pp. 31/38.
- F5: stage 4 deck locator `pp. 26-32` → `pp. 24,26-32` (p. 24 defines the
  independence the E[XY] lemma uses).
- F6 (Chebyshev c>0/min-cap): deliberate no-change, documented in the pilot
  record §Findings; stage 7 text already guards both.
- Stages 5–7 resources untouched; no exclusions beyond F6; no unresolved gaps.
- Checks: local_inventory_complete, linked_inventory_complete,
  materials_opened_and_content_checked, current_and_prior_scope_reconciled,
  duplicates_and_numbering_checked, exclusions_and_unresolved_gaps_recorded —
  all true as evidenced above.
