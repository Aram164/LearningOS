---
id: note-sad-l10-fahrmeir-bonferroni-pp445-446
type: note
role: reference
title: 'Fahrmeir L10 source angle: multiplicity and Bonferroni'
created: '2026-09-24'
state: rough
authorship: operator-drafted
semantic_review: unreviewed
material_analysis:
  resolution: resolved
  material: mathematics/probability-statistics/fahrmeir-statistik/statistik.pdf
  source_id: source-fahrmeir-statistik
  recorded_source_digest: f65389b9a2e65ba6178380fb7eb985c28003cf9d258036a80b1c77ebf1322c31
  live_source_digest: f65389b9a2e65ba6178380fb7eb985c28003cf9d258036a80b1c77ebf1322c31
  inspected_range:
    start: 445
    end: 446
  frozen_input_sha256: 31a429488e4060b35eec1bcb418f2ca852805efffbac0306f4288cb03baac07f
  frozen_input_bytes: 1283
  model: Codex GPT-6 2026-09
  built: '2026-09-24'
---

# Fahrmeir §10.3: multiplicity and the Bonferroni threshold

Inspected statistik.pdf, physical pp. 445-446. The section is §10.3 in Chapter 10, 'Multiple Testprobleme'; a current unplaced L10 route incorrectly calls PDF p. 446 'Kapitel 12'.

- Page 445 starts from a three-quality-feature decision in which any rejected null causes an overall bad classification. This makes the family of tests and the event 'at least one false rejection' explicit.
- Page 446 gives alpha_star=1-(1-alpha)^k for independent tests and tabulates alpha_star at alpha=0.05, including 0.994 for k=100. It then gives the per-test Bonferroni threshold alpha/k. The formula for independent tests illustrates inflation; Bonferroni's union-bound protection itself does not require independence.
- The source's angle is a two-page German numerical argument and correction, suitable for L10's core multiplicity intuition. It does not define FDR or teach Benjamini-Hochberg; ISLP Chapter 13 is a separately labeled optional extension.

Plan implication: correct the 'Kapitel 12' locator to §10.3, avoid a duplicate whole-chapter and one-page route if the broad route can point precisely to pp. 445-446, and use this verified slice to repair the current L10 deck p. 62 example and ambiguous p'=p/m instruction.
