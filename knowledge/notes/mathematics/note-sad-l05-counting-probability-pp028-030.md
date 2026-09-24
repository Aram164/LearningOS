---
id: note-sad-l05-counting-probability-pp028-030
type: note
role: reference
title: 'SaD L05 source angle: counting becomes probability'
created: '2026-09-24'
state: rough
authorship: operator-drafted
semantic_review: unreviewed
material_analysis:
  resolution: resolved
  material: mathematics/probability-statistics/sad-ss26-lectures/lecture-slides/05_combinatorics.pdf
  source_id: source-sad-ss26-lectures
  recorded_source_digest: 583f5cccee4c67e2cc9a215f4674aeaae7e37b555acf06ab1d8aa08d65344566
  live_source_digest: 583f5cccee4c67e2cc9a215f4674aeaae7e37b555acf06ab1d8aa08d65344566
  inspected_range:
    start: 28
    end: 30
  frozen_input_sha256: 28cfca99e04ac0366ff4d5f4dbcf96bf4da64235ee1ce0f97e3a7e12a38257d8
  frozen_input_bytes: 1409
  model: Codex GPT-6 2026-09
  built: '2026-09-24'
---

# SaD L05 source angle: counting becomes probability

Material inspected: 05_combinatorics.pdf, physical PDF pp. 28-30. This is a bounded analysis of that slice, not a review of every route in L05.

- Page 28 turns counting into a probability numerator/denominator question. Its sparse compartment example needs the outcome space stated before computing a ratio.
- Page 29 attempts an exact-match lottery probability, but switches between five and six drawn balls. It uses C(49,5) as the denominator after saying six are drawn and C(6,1) for the wrong ball, although 43 of 49 balls are nonwinning. Do not copy that numerical setup.
- Page 30 gives the coherent hypergeometric construction: choose k1 from n1 successes and k-k1 from n-n1 failures, divided by all C(n,k) unordered draws. For six chosen numbers among 49, with six winning numbers and exactly five matches, the corresponding count is C(6,5)C(43,1)/C(49,6).
- Source angle: the lecture first teaches six counting cases, then reuses unordered combinations to model without-replacement probability. It is a bridge from the L05 decision grid to L07's hypergeometric distribution, not a separate worked set of reliable lottery numbers.

Plan implication: keep the page-29 warning adjacent to this route and use page 30 for the actual formula. The current L05 counting-probability stage already carries this correction; preserve it during any cleanup.
