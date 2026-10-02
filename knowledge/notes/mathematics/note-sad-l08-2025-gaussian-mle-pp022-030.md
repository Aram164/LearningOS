---
id: note-sad-l08-2025-gaussian-mle-pp022-030
type: note
role: reference
title: 'SaD 2025 L09 source angle for L08: Gaussian parameter MLE'
created: '2026-09-24'
state: rough
authorship: operator-drafted
semantic_review: unreviewed
material_analysis:
  resolution: resolved
  material: mathematics/probability-statistics/sad-2025-recordings/09_point_interval_estimation (1).pdf
  source_id: source-sad-2025-recordings
  recorded_source_digest: 2724787a60ce9f9d0b6b064335ee80a8b9428210426df3707a0a95a13f7b923f
  live_source_digest: 2724787a60ce9f9d0b6b064335ee80a8b9428210426df3707a0a95a13f7b923f
  inspected_range:
    start: 22
    end: 30
  frozen_input_sha256: b31c508a4f86ad60079d0d80bb5f1c75bbec440ffe3cf66bfbf6fff890f3b0c1
  frozen_input_bytes: 1548
  model: Codex GPT-6 2026-09
  built: '2026-09-24'
---

# SaD 2025 L09: a Gaussian-parameter MLE derivation useful in L08

Inspected 09_point_interval_estimation (1).pdf, physical pp. 22-30. These pages are in the prior-year L09 deck; the current 2026 L08 pp. 29-36 instead derives why Gaussian regression errors lead to squared-error fitting.

- Pages 22-25 hold observed data fixed while varying model parameters, then write the likelihood and log-likelihood for iid observations. Page 22's L(parameter | data) should be read as likelihood notation, not as a normalized posterior probability of the parameter.
- Pages 26-30 differentiate the Normal log-likelihood to estimate its mean and variance, and p. 30 warns that the variance MLE with denominator n can be biased. This is a compact same-course bridge from L08's likelihood principle to L09's estimator properties.
- Its angle differs from current L08: estimating the parameters of a univariate Normal distribution versus fitting regression coefficients under Gaussian error assumptions. It also differs from a generic definition of likelihood because it executes the derivative and exposes the n versus n-1 variance issue.
- This is optional supporting depth for L08, not evidence that the current 2026 lecture examines the full Normal variance-MLE derivation.

Plan implication: consider one cross-lecture route in the L08 complete menu to this precise prior-year slice, with L09 retaining its existing route. If used in the ordered L08 MLE stage, prefer it only for a learner needing the parameter-derivation bridge; do not expand core scope.
