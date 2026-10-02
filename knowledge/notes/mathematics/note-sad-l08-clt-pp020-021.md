---
id: note-sad-l08-clt-pp020-021
type: note
role: reference
title: 'SaD L08 source angle: a no-proof CLT for sums and means'
created: '2026-09-24'
state: rough
authorship: operator-drafted
semantic_review: unreviewed
material_analysis:
  resolution: resolved
  material: mathematics/probability-statistics/sad-ss26-lectures/lecture-slides/08_normal_distribution.pdf
  source_id: source-sad-ss26-lectures
  recorded_source_digest: 050801b9c8a41a3b2508f456b7444ef699844f7494dd66f2863dfe9b04328e20
  live_source_digest: 050801b9c8a41a3b2508f456b7444ef699844f7494dd66f2863dfe9b04328e20
  inspected_range:
    start: 20
    end: 21
  frozen_input_sha256: f726c73d20fb4acb07c61bfbbc9efedb452f31d4a444bb85510c93e64afecdb1
  frozen_input_bytes: 1249
  model: Codex GPT-6 2026-09
  built: '2026-09-24'
---

# SaD L08 source angle: a no-proof CLT for sums and means

Material inspected: 08_normal_distribution.pdf, physical PDF pp. 20-21. This analysis is limited to the theorem and its immediate interpretation.

- Page 20 states an IID finite-mean, finite-variance central limit theorem for a standardized sum, explicitly without proof. The original Xi need not be Normal. It also includes a loose practical remark that independence and identical distribution may be unnecessary if no term dominates; that remark is not a general theorem and needs separate conditions before reuse.
- Page 21 translates the standardized result into approximate Normal distributions for the sum and sample mean, with mean n*mu and mu and variance n*sigma^2 and sigma^2/n respectively.
- Source angle: standardize an aggregate to explain why an average has approximately Normal sampling fluctuations. These pages do not introduce the law of large numbers or demonstrate a formal LLN-versus-CLT comparison; L06 supplies the LLN side.

Plan implication: replace the L08 CLT stage's generic deck angle with this specific contribution and keep the LLN comparison attributed to L06 or a verified complementary source. Do not present the deck's broad non-IID remark as a theorem.
