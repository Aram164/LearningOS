---
id: note-06-random-variables-pp009-013
type: note
role: reference
title: L06 pp. 9–13 — CDF, discrete computation, limits
created: '2026-09-21'
state: rough
authorship: operator-drafted
semantic_review: unreviewed
material_analysis:
  resolution: resolved
  material: mathematics/probability-statistics/sad-ss26-lectures/lecture-slides/06_random_variables.pdf
  recorded_source_digest: 90935b8261356000cc8a545832a54f0869760169a13715a4c74af89c1ce2d1ca
  inspected_range:
    start: 9
    end: 13
  frozen_input_sha256: eea62cee24f9c39c5d6900d99adccedab78a0e86a727a221cfa63cde97368707
  frozen_input_bytes: 837
  source_id: source-sad-ss26-lectures
  live_source_digest: 90935b8261356000cc8a545832a54f0869760169a13715a4c74af89c1ce2d1ca
  model: muse-spark 2026-09
  built: '2026-09-20'
---

<!-- GENERATED file - do not edit; promoted by tools/material_summarize.py --promote -->

# L06 pp. 9–13 — CDF, discrete computation, limits

CDF definition (p. 9): F(x) = P(X ≤ x) for discrete or continuous X,
illustrated by X = sum of two dice (note: the bar chart is a histogram,
not a cdf). Point queries P(Temp = 17.65…) are meaningless for continuous
variables; P(Temp < 20) is meaningful. Discrete computation (p. 10):
F(x) = Σ_{xi ≤ x} pi. Worked (p. 11): X = number of sixes in three throws;
P(X ≥ 1) = 1 − (5/6)³ ≈ 0.421 via the complement, P(X ≥ 2) ≈ 0.071 by
summing P(X = 2) + P(X = 3). Limits (pp. 12–13): F rises monotonically
0 → 1; one-sided limits exist with right limit F(y) = P(X ≤ y) and left
limit P(X < y); for discrete variables the jump at each xi equals
P(X = xi) (Treppenfunktion).
