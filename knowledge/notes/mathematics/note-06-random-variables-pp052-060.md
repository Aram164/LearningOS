---
id: note-06-random-variables-pp052-060
type: note
role: reference
title: L06 pp. 52–60 — Sample mean, IID, law of large numbers
created: '2026-09-21'
state: rough
authorship: operator-drafted
semantic_review: unreviewed
material_analysis:
  resolution: resolved
  material: mathematics/probability-statistics/sad-ss26-lectures/lecture-slides/06_random_variables.pdf
  recorded_source_digest: 90935b8261356000cc8a545832a54f0869760169a13715a4c74af89c1ce2d1ca
  inspected_range:
    start: 52
    end: 60
  frozen_input_sha256: 009b7ee070c921d9f95a7d6b328713df1d92112b99fbe8a6294af26dab33647c
  frozen_input_bytes: 1226
  source_id: source-sad-ss26-lectures
  live_source_digest: 90935b8261356000cc8a545832a54f0869760169a13715a4c74af89c1ce2d1ca
  model: muse-spark 2026-09
  built: '2026-09-20'
---

<!-- GENERATED file - do not edit; promoted by tools/material_summarize.py --promote -->

# L06 pp. 52–60 — Sample mean, IID, law of large numbers

Question (p. 52): what a size-n sample tells about X — mean, variance,
shape — e.g. voters, customers, therapy effects. IID as modeling
assumption (pp. 53–54): same experiment, independent copies; in
practice only approximated by removing known confounders (drug trials,
vaccines, ML train/serve skew, transfer learning). Sample mean lemma
(p. 55): X̄ = (1/n)ΣXi is random with E[X̄] = μ (linearity) and
Var(X̄) = σ²/n — the variance half needs zero cross-covariances and
the squared 1/n² factor, which the slide's one-line proof does not
show. Ten-dice table (p. 56): two realized experiments (means 2.9,
3.3) separating each Xi, realized xi, and random X̄; Var(Xi) = 2.92
versus Var(X̄) = 0.292. LLN (p. 57): lim P(|X̄−μ| < ε) = 1 for every
ε > 0. Stochastic — not plain — convergence (p. 58): a late long
strange run stays possible; probability 0 in the limit, never the
path. Proof (p. 59): Chebyshev on X̄ with σ²/n. Empirics (p. 60):
Hauptsatz pointwise empirical-CDF convergence per x — not the
uniform Glivenko–Cantelli statement.
