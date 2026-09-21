---
id: note-06-random-variables-pp034-042
type: note
role: reference
title: L06 pp. 34–42 — Variance, scaling, uniform and exponential moments
created: '2026-09-21'
state: rough
authorship: operator-drafted
semantic_review: unreviewed
material_analysis:
  resolution: resolved
  material: mathematics/probability-statistics/sad-ss26-lectures/lecture-slides/06_random_variables.pdf
  recorded_source_digest: 90935b8261356000cc8a545832a54f0869760169a13715a4c74af89c1ce2d1ca
  inspected_range:
    start: 34
    end: 42
  frozen_input_sha256: 43ebe8ec6f1932a453b89e65e78cd326d49334b84f7b1b2f5376d6329317201f
  frozen_input_bytes: 1021
  source_id: source-sad-ss26-lectures
  live_source_digest: 90935b8261356000cc8a545832a54f0869760169a13715a4c74af89c1ce2d1ca
  model: muse-spark 2026-09
  built: '2026-09-20'
---

<!-- GENERATED file - do not edit; promoted by tools/material_summarize.py --promote -->

# L06 pp. 34–42 — Variance, scaling, uniform and exponential moments

Definition (p. 34): Var(X) = σ² = E[(X−μ)²] in sum and integral form, σ
the standard deviation; sample/population correspondence table (p. 35).
Second-moment identity (p. 36): full derivation of
Var(X) = E[X²] − μ² via linearity. Two-dice example (pp. 37–38):
E(Z) = 7 by linearity; Var(Z) = E[Z²] − 49 = 54.83 − 49 = 5.83, reusing
Z's own probabilities for Z². Affine scaling (p. 39): proof of
Var(aX+b) = a²Var(X); the offset shifts expectation only. Uniform
moments (pp. 40–41): E = (a+b)/2, Var = (b−a)²/12; the "Slope is 1"
annotation is wrong as written — the uniform density has height
1/(b−a) and slope zero, 1/(b−a) is the CDF's slope — while the
integration itself normalizes correctly. Exponential moments (p. 42):
E = 1/k, Var = 1/k² (proof by reference), repeating the p. 20
density-labeled-as-F(x) notation.
