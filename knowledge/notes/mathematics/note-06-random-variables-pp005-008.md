---
id: note-06-random-variables-pp005-008
type: note
role: reference
title: L06 pp. 5–8 — Random variables and discrete variables
created: '2026-09-21'
state: rough
authorship: operator-drafted
semantic_review: unreviewed
material_analysis:
  resolution: resolved
  material: mathematics/probability-statistics/sad-ss26-lectures/lecture-slides/06_random_variables.pdf
  recorded_source_digest: 90935b8261356000cc8a545832a54f0869760169a13715a4c74af89c1ce2d1ca
  inspected_range:
    start: 5
    end: 8
  frozen_input_sha256: be66edb2951c5b5a8c184dd73716459909167be381627c474dab1b2163b4ed6f
  frozen_input_bytes: 1113
  source_id: source-sad-ss26-lectures
  live_source_digest: 90935b8261356000cc8a545832a54f0869760169a13715a4c74af89c1ce2d1ca
  model: muse-spark 2026-09
  built: '2026-09-20'
---

<!-- GENERATED file - do not edit; promoted by tools/material_summarize.py --promote -->

# L06 pp. 5–8 — Random variables and discrete variables

Motivation (p. 5): samples estimate population means, but judging the
estimate needs formalism; the central concept is the random variable.
Roadmap (p. 6): RVs model populations, leading to distributions, expected
values (generalized means), variance, and first coarse sample-vs-population
bounds; tighter bounds come later from named distributions.

Definition (p. 7): a random variable is a function X: Ω → ℝ assigning each
outcome of a random experiment a real number; examples are height of a
person, daily temperature, illness probability. Discrete case: three fair
dice throws, X = sum, X ∈ {3,…,18}; interest lies in P(X = x).

Discrete RVs (p. 8): X is discrete when its image is finite or countably
infinite, with pi = P(X = xi). Point probabilities are meaningless for
continuous variables (individual values are infinitesimally rare).
Worked: X = sum of three dice; P(X = 8) by counting ordered triples over
6³; P(X < 5) = 4/216 ≈ 0.0185.
