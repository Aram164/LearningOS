---
id: note-06-random-variables-pp015-023
type: note
role: reference
title: L06 pp. 15–23 — Continuous variables, density, worked examples
created: '2026-09-21'
state: rough
authorship: operator-drafted
semantic_review: unreviewed
material_analysis:
  resolution: resolved
  material: mathematics/probability-statistics/sad-ss26-lectures/lecture-slides/06_random_variables.pdf
  recorded_source_digest: 90935b8261356000cc8a545832a54f0869760169a13715a4c74af89c1ce2d1ca
  inspected_range:
    start: 15
    end: 23
  frozen_input_sha256: a9c48a5e07e3ae248c1eba4923d825c282f5b03690e312bbf033e982fe72a341
  frozen_input_bytes: 1379
  source_id: source-sad-ss26-lectures
  live_source_digest: 90935b8261356000cc8a545832a54f0869760169a13715a4c74af89c1ce2d1ca
  model: muse-spark 2026-09
  built: '2026-09-20'
---

<!-- GENERATED file - do not edit; promoted by tools/material_summarize.py --promote -->

# L06 pp. 15–23 — Continuous variables, density, worked examples

Setup (p. 15): discrete CDFs sum probabilities; for continuous variables
the deck assumes throughout that the cdf is continuous (stetig) and
differentiable. The pdf is f = F′. Caution: the F(X) integral printed on
this page runs to +∞ where it must end at x; p. 17 gives the correct
∫_{-∞}^{x} form next to the discrete sum. Slope-as-jump analogy (p. 16).
Overview diagram (p. 18): experiment → variable → probability function /
density → cdf, both branches. PDF facts (p. 19): f ≥ 0, total mass 1,
P(X = x) = 0 (so P(X ≤ x) = P(X < x) and only intervals matter),
P(a ≤ X ≤ b) = F(b) − F(a). Uniform and exponential (p. 20): uniform CDF
(x−a)/(b−a) is printed without its = 1 branch above b, and the
exponential "F(x)" = λe^{−kx} is density-shaped — read it as a density
valid for λ = k > 0, whose CDF is 1 − e^{−kx}. Bus example (p. 21):
discrete-minutes model F(x) = 0.1(x+1) giving P(X ≤ 3) = 0.4 — note the
printed F(4) argument is a slip for F(3) — versus the continuous-U(0,10)
reading F(x) = x/10 with 0.3/0.6; know which model the question asks for.
Component lifetime (pp. 22–23): Exp CDF 1 − e^{−x} at k = λ = 1 with
P(X < 1) = 0.63 and P(1 < X < 2) = 0.23.
