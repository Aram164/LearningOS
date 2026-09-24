---
id: note-sad-l07-distribution-boundary-pp013-014
type: note
role: reference
title: 'SaD L07 source angle: distribution extensions are only sketches'
created: '2026-09-24'
state: rough
authorship: operator-drafted
semantic_review: unreviewed
material_analysis:
  resolution: resolved
  material: mathematics/probability-statistics/sad-ss26-lectures/lecture-slides/07_discrete_distributions.pdf
  source_id: source-sad-ss26-lectures
  recorded_source_digest: ce20eefdeef992947165feb47227afd9e7f95091cbafc9a3c5f3ce274b4851f0
  live_source_digest: ce20eefdeef992947165feb47227afd9e7f95091cbafc9a3c5f3ce274b4851f0
  inspected_range:
    start: 13
    end: 14
  frozen_input_sha256: abcbc72a91c7cb77392bd014fafb52a19b9275d13b8474bbfc341800e283fc8d
  frozen_input_bytes: 1208
  model: Codex GPT-6 2026-09
  built: '2026-09-24'
---

# SaD L07 source angle: distribution extensions are only sketches

Material inspected: 07_discrete_distributions.pdf, physical PDF pp. 13-14. This is a bounded analysis of the extension slides.

- Page 13 sketches the multinomial extension from two outcome classes to several. It gives a probability expression and marginal expectation/variance, without a worked selection exercise.
- Page 14 contrasts a fixed number of trials with a waiting time until k successes under a negative-binomial heading. The page does not state the Geometric probability mass function, the convention for counting trials versus failures, or memorylessness. It is context for a Geometric lesson, not that lesson itself.
- The same page labels a fixed-n interval-of-success-counts question as a Beta distribution. The described count event is a binomial probability range; do not teach the label as a definition of the continuous Beta distribution.

Plan implication: keep the deck reference-only in the Geometric stage, as the current map already does. Attribute the Geometric formula and memoryless property to a verified complementary source, and replace the generic deck-stage wording with the negative-binomial sketch angle.
