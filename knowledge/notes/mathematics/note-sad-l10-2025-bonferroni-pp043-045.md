---
id: note-sad-l10-2025-bonferroni-pp043-045
type: note
role: reference
title: 'SaD 2025 L10 source angle: Bonferroni rule and prespecified alpha'
created: '2026-09-24'
state: rough
authorship: operator-drafted
semantic_review: unreviewed
material_analysis:
  resolution: resolved
  material: mathematics/probability-statistics/sad-2025-recordings/10_statistical_significance.pdf
  source_id: source-sad-2025-recordings
  recorded_source_digest: 42c20aac9214565d8b02d1fc875cdc38e161c5e9b863ce41aa50ba7d5b68831d
  live_source_digest: 42c20aac9214565d8b02d1fc875cdc38e161c5e9b863ce41aa50ba7d5b68831d
  inspected_range:
    start: 43
    end: 45
  frozen_input_sha256: 98899e508c6d0cc142b2ea38115e967c350e91321f97909ab5d723101dcc1524
  frozen_input_bytes: 1209
  model: Codex GPT-6 2026-09
  built: '2026-09-24'
---

# SaD 2025 L10: explicit Bonferroni rule and prespecified alpha

Inspected 10_statistical_significance.pdf, physical pp. 43-45. This is a prior-year course deck, not the 2026 scope authority.

- Page 43 says to choose the significance level before testing and links post hoc changes to p-hacking. Pages 44-45 use many slight variants of a drug comparison to motivate accumulation of false rejections.
- Page 45 explicitly gives the Bonferroni procedure in German: divide alpha by the number of tested hypotheses. This is a clear per-test threshold rule, and it disambiguates the current 2026 deck p. 62's unsafe p'=p/m wording. Equivalently, an observed raw p-value may be multiplied by m and capped at one for comparison with the original alpha; do not divide an observed p-value by m.
- The prior-year pages give the expected-false-rejection intuition, but do not name FWER versus FDR or teach Benjamini-Hochberg. The current 2026 deck also does not teach FDR. ISLP Chapter 13 is the optional extension for that distinction.

Plan implication: keep the existing 2025 L10 menu route and use pp. 43-45 as a short, course-native correction aid in the multiple-testing stage. Keep FDR optional as Aram decided.
