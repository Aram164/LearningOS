---
id: note-sad-l09-resampling-p045
type: note
role: reference
title: 'SaD L09 source angle: resampling motivation, not a bootstrap procedure'
created: '2026-09-24'
state: rough
authorship: operator-drafted
semantic_review: unreviewed
material_analysis:
  resolution: resolved
  material: mathematics/probability-statistics/sad-ss26-lectures/lecture-slides/09_estimating.pdf
  source_id: source-sad-ss26-lectures
  recorded_source_digest: 6efc21415ff48916ead8bba9abac110996fdfea3bfa32373b730f276c24c5abc
  live_source_digest: 6efc21415ff48916ead8bba9abac110996fdfea3bfa32373b730f276c24c5abc
  inspected_range:
    start: 45
    end: 45
  frozen_input_sha256: c4836640a7a9e0686a1633c050ca2d60625332bf71c563840161d8f211f5d959
  frozen_input_bytes: 1143
  model: Codex GPT-6 2026-09
  built: '2026-09-24'
---

# SaD L09 source angle: resampling motivation, not a bootstrap procedure

Material inspected: 09_estimating.pdf, physical PDF p. 45. This analysis is limited to the final resampling slide.

- The page proposes repeating an experiment many times, computing the target property for each sample, and inspecting the resulting estimate distribution. It calls this resampling and stresses computational cost and usefulness beyond simple known univariate distributions.
- It does not specify drawing observations with replacement from the observed sample, the size or number of resamples, a bootstrap standard error, or construction of a confidence interval.
- Source angle: a conceptual exit from analytic interval formulas toward computation for a general property. It is orientation for the bootstrap stage, not the source of the bootstrap algorithm.

Plan implication: the current required-now deck placement in stage-sad-l09-bootstrap should say 'resampling motivation' and cite the current Blatt 4/UE6 task and an exact bootstrap reading for the with-replacement calculation and interval. The stage may retain the deck page as a short opening.
