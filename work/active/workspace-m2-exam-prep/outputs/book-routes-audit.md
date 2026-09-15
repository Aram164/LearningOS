# Book-routes audit — firsthand reads behind book-routes-plan.yaml

All passages below were extracted from the library PDFs and read in full by the
operator on 2026-09-16. Page cites give printed pages with PDF file pages.

## New routes

- L01 base-rates ← Fahrmeir Bsp 4.24–4.25 + Satz von Bayes, printed pp. 216–219
  (PDF pp. 230–233). 98% sens / 97% spec / 0.001 prevalence → 0.032 posterior,
  computed by formula AND by frequency tree (98 of 3095). Sens/Spec/a-priori
  vocabulary included.
- L01 base-rates ← Blitzstein Ex 2.3.9, printed pp. 56–57 (PDF pp. 73–74).
  Fred/conditionitis, 1% prevalence, 95% accuracy → 16% posterior, 10,000-person
  tree. English twin of the Fahrmeir story.
- L02 simpson ← Blitzstein Ex 2.8.3, printed pp. 76–78 (PDF pp. 93–95).
  Hibbert-vs-Nick reversal worked, LOTP weighted-average explanation, formal
  condition box. Continues into prosecutor/defense fallacies (L04 context).
- L03 multivariate ← Fahrmeir §12.2.3, printed pp. 509–511 (PDF pp. 519–521).
  Y = Xβ + ε, normal equations X′Xβ̂ = X′Y, Var(β̂ⱼ) = σ²vⱼ, design-matrix
  construction, numeric-inversion warning (bridge to gradient descent).

## Local

Four library PDFs opened from the materials tree and read in the cited
chapters in full (see passages above): fahrmeir-statistik/statistik.pdf,
blitzstein-hwang/blitzstein.pdf, dekking-mips/dekking.pdf (Ch 15 §§15.2–15.5
plus full-text search), openintro-statistics/openintro.pdf (whole-book
full-text search for the Simpson check).

## Linked

No external links in this package — all four routes point at local library
files already registered in the sources registry. Nothing to verify live.

## Completeness

Four new routes (L01 base-rates ×2, L02 simpson, L03 multivariate) plus two
in-place corrections (Dekking sampling cover, OpenIntro simpson cover).
Deliberate exclusion: Tijms Ch 6 (not firsthand-read; node already covered
twice). No other scope touched.

## Corrections to existing routes

- route-61c0f7bd88ab5c8d2e2e23f4 (Dekking, L02): FULL-TEXT SEARCH of §§15.2–15.5
  finds zero convergence/Glivenko/sampling-method statements — §15.4 teaches Fn
  construction only. knowledge-sad-l02-sampling cover removed, angle corrected.
- route-a225112e34dbc25aa40a9926 (OpenIntro, L02): FULL-TEXT SEARCH of the whole
  book finds zero "Simpson" and no reversal example (confounding discussed, never
  the paradox). knowledge-sad-l02-simpson cover removed, angle corrected.

## Deliberately excluded

- Tijms Ch 6 base-rate material: cited by the sweep but not firsthand-read;
  two independent witnesses (Fahrmeir + Blitzstein) already cover the node.
  Left as an unresolved gap, not silently dropped.
