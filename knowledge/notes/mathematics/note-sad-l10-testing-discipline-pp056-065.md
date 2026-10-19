---
id: note-sad-l10-testing-discipline-pp056-065
type: note
role: reference
title: 'SaD L10 source angle: permutation tests and testing discipline'
created: '2026-09-24'
state: rough
authorship: operator-drafted
semantic_review: unreviewed
material_analysis:
  resolution: resolved
  material: mathematics/probability-statistics/sad-ss26-lectures/lecture-slides/10_testing.pdf
  source_id: source-sad-ss26-lectures
  recorded_source_digest: c34f5fe24b0fb7568aba408b358a346c6c29d954288c6c55671ec62ea1ac47be
  live_source_digest: c34f5fe24b0fb7568aba408b358a346c6c29d954288c6c55671ec62ea1ac47be
  inspected_range:
    start: 56
    end: 65
  frozen_input_sha256: c5265fa6a1ff062036f3c87212642e2ff23e79880adb0db55639140c886955cf
  frozen_input_bytes: 1742
  model: Codex GPT-6 2026-09
  built: '2026-09-24'
---

# SaD L10 source angle: permutation tests and testing discipline

Material inspected: 10_testing.pdf, physical PDF pp. 56-65. The claim below is limited to these pages.

- Pages 56-58 introduce a two-group permutation test through a sleep-drug example, retaining observed values while reallocating group labels and comparing mean differences. This is an intuitive computational alternative to a rank test. Page 56 incorrectly calls the probability of a Type II error 'power'; that probability is beta, while power is 1-beta.
- Pages 60-61 move from a prespecified hypothesis to pitfalls: testing a data-selected subset, changing alpha after looking, or extending the sample until significance. The source angle is scientific testing discipline, not another test formula.
- Page 62 warns that repeated testing produces false positives and gestures at a correction. Its example says 20 expected p<0.05 results among 100 independent null tests, whereas 100*0.05=5. Its p'=p/m wording is unsafe if p denotes an observed p-value: the Bonferroni per-test threshold is alpha/m, equivalently an adjusted observed p-value of min(1,m*p_raw).
- Pages 63-65 give a p-hacking illustration, reproducibility warning, and preregistration rationale. These pages do not teach false discovery rate or Benjamini-Hochberg control.

Plan implication: describe the current deck's multiple-testing angle as false-positive inflation, a brief Bonferroni intuition, and preregistration/p-hacking. Attribute FWER versus FDR and the Benjamini-Hochberg procedure to a separately checked complementary route such as ISLP, and correct the ISLP route's statement that the lecture itself names false discoveries. Keep the page-56 power warning beside the nonparametric stage.
