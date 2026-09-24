---
id: note-sad-l09-ue6-bootstrap-pp010-013
type: note
role: reference
title: 'SaD UE6 source angle: current bootstrap worked solution'
created: '2026-09-24'
state: rough
authorship: operator-drafted
semantic_review: unreviewed
material_analysis:
  resolution: resolved
  material: mathematics/probability-statistics/sad-ss26-lectures/exercise-slides/UE6.pdf
  source_id: source-sad-uebungen
  recorded_source_digest: 2b2a96c5f29ef93a17da4707754c1dc3edef44616a2a9213fb49da17125af68a
  live_source_digest: 2b2a96c5f29ef93a17da4707754c1dc3edef44616a2a9213fb49da17125af68a
  inspected_range:
    start: 10
    end: 13
  frozen_input_sha256: c9aaa2c99eab418c57c6c9ef45d26f7e6c5f85f590b2d2436bbfcb4b582bebcc
  frozen_input_bytes: 1507
  model: Codex GPT-6 2026-09
  built: '2026-09-24'
---

# SaD UE6: assessed bootstrap standard error and interval

Inspected UE6.pdf, physical pp. 10-13, with the current Blatt 4 Aufgabe 2 on Statistics_And_Data_Science.pdf p. 2. The UE6 pages are a worked solution to the current exercise, not a general bootstrap treatise.

- The example starts from five observed sugar measurements, 4,5,6,7,8, and supplies ten resamples of size five. Page 11 calculates ten bootstrap means, their mean 5.8, and an estimated standard error about 1.14 as the standard deviation of those ten means. The observed sample mean is 6; distinguish it from the mean of the ten bootstrap means.
- Page 12 sorts the ten means, removes one from each tail for an 80% central empirical interval, and reports [5,7]. This is a small teaching exercise with explicitly supplied resamples. It does not claim that ten resamples suffice for a stable production interval.
- Page 13 distinguishes spread of observations (sample standard deviation) from spread of the estimator across resamples (standard error). That is the repair target if the two are conflated.
- Source angle: the current course's exact calculation and explanation order, best used after an unaided attempt at Blatt 4 Aufgabe 2. It supports the L09 standard-error and bootstrap stages without asking the current L09 deck p. 45 to provide an algorithm it lacks.

Plan implication: keep the existing current-sheet and UE6 routes; make the bootstrap stage cite UE6 pp. 10-13 specifically, and state the ten-replicate teaching limit.
