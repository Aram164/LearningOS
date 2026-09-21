---
id: note-06-random-variables-pp044-050
type: note
role: reference
title: 'L06 pp. 44–50 — Chebyshev: motivation, inequality, examples'
created: '2026-09-21'
state: rough
authorship: operator-drafted
semantic_review: unreviewed
material_analysis:
  resolution: resolved
  material: mathematics/probability-statistics/sad-ss26-lectures/lecture-slides/06_random_variables.pdf
  recorded_source_digest: 90935b8261356000cc8a545832a54f0869760169a13715a4c74af89c1ce2d1ca
  inspected_range:
    start: 44
    end: 50
  frozen_input_sha256: 6dc63da1b9e595c5a7fba691fdda0e05ce19ae7d5e008f9a1d142da5512dda8e
  frozen_input_bytes: 1142
  source_id: source-sad-ss26-lectures
  live_source_digest: 90935b8261356000cc8a545832a54f0869760169a13715a4c74af89c1ce2d1ca
  model: muse-spark 2026-09
  built: '2026-09-20'
---

<!-- GENERATED file - do not edit; promoted by tools/material_summarize.py --promote -->

# L06 pp. 44–50 — Chebyshev: motivation, inequality, examples

Motivation (p. 44): assessing observations against known μ and σ² —
outliers, errors, conformance; framed loosely as "how likely was x
created by X", for arbitrary distributions but not sharp. Inequality
(p. 45): P(|X−μ| ≥ c) ≤ σ²/c², proved for the discrete case by
restricting the sum to |xi−μ| ≥ c and extending it to the full
variance. Intuition (p. 46): mass concentrates near μ; the bound only
bites for small variance, saturating at 1 otherwise. Dice example
(p. 47): throwing 1 (2.5 from μ = 3.5) bounds at ≈ 0.46 against the
true 1/6 — then the key correction: the bound covers distance to the
mean (here {1, 6}), not a concrete value; symmetry halves it to 0.23.
Biomarker example (pp. 48–49): healthy μ = 14.5, σ² = 2.3 gives ≤ 19%
at b = 18 and ≤ 4% at b = 22, versus < 3.8% and < 0.1% under a normal
model — distribution knowledge sharpens enormously. Outlook (p. 50):
comparing healthy/ill distributions is hypothesis testing, later.
