---
id: note-sad-l09-2025-bootstrap-pp068-088
type: note
role: reference
title: 'SaD 2025 L09 source angle: bootstrap algorithm and intervals'
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
    start: 68
    end: 88
  frozen_input_sha256: 69115736306d5fd59fd9d95f07d45cc7eb982d41282cf236e88997b65ba67804
  frozen_input_bytes: 1684
  model: Codex GPT-6 2026-09
  built: '2026-09-24'
---

# SaD 2025 L09: the bootstrap algorithm and two interval routes

Inspected 09_point_interval_estimation (1).pdf, physical pp. 68-88. This prior-year deck complements the current 2026 L09 ending on p. 45, which only motivates resampling.

- Page 71 explicitly samples n observations with replacement from the one observed sample, computes a statistic for each of B resamples, and takes the 2.5th and 97.5th percentiles of the bootstrap estimates for a 95% percentile interval. Pages 72-81 animate the repeated-sample construction, including the possibility of drawing an extreme value repeatedly.
- Pages 82-87 give a second route: estimate the center and standard deviation of the bootstrap estimates and form a Normal-based interval, or trim the tails of their empirical distribution. These are two interval constructions and should not be collapsed into one rule.
- Page 88 warns that its five-value toy sample is too small for dependable inference and flags outliers and dependent observations as limitations. The source's broad claim that bootstrap works for every distribution and estimator should be read with those restrictions, not as a universal guarantee.
- The angle is algorithm and visual mechanics in the same course's previous run. The current Blatt 4, Aufgabe 2, and UE6 pp. 10-13 are closer to current assessed practice and use ten supplied bootstrap replicates for an 80% interval.

Plan implication: keep this route in the complete L09 menu, with pp. 68-88 as a narrow helper after the current sheet. Attribute percentile construction to p. 71 and distinguish the Normal-based alternative on pp. 82-87. Do not claim current L09 p. 45 contains the bootstrap recipe.
