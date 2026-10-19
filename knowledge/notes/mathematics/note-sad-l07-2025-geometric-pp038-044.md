---
id: note-sad-l07-2025-geometric-pp038-044
type: note
role: reference
title: 'SaD 2025 L07 source angle: geometric waiting time and convention'
created: '2026-09-24'
state: rough
authorship: operator-drafted
semantic_review: unreviewed
material_analysis:
  resolution: resolved
  material: mathematics/probability-statistics/sad-2025-recordings/07_discrete_distributions.pptx (1).pdf
  source_id: source-sad-2025-recordings
  recorded_source_digest: 3f16eb9a4e094fc2c9ed62fc93c3790e63a49709d865802dca7cb48af0b83aa8
  live_source_digest: 3f16eb9a4e094fc2c9ed62fc93c3790e63a49709d865802dca7cb48af0b83aa8
  inspected_range:
    start: 38
    end: 44
  frozen_input_sha256: 04997c9974819ed6f2f4e73d59603d0a3ee935651877a2368e37e8964a1a80c2
  frozen_input_bytes: 1378
  model: Codex GPT-6 2026-09
  built: '2026-09-24'
---

# SaD 2025 L07: geometric waiting time, with a correction

Inspected 07_discrete_distributions.pptx (1).pdf, physical pp. 38-44. This is the prior-year deck, not the current 2026 L07 scope authority.

- Pages 38-40 switch from a fixed number of trials (Binomial) to waiting until the first success. X counts trials including the successful one, so x starts at 1 and P(X=x)=(1-p)^(x-1)p. Page 41 gives the cumulative distribution; p. 42 poses a die-roll example. Page 44 contrasts Binomial, Geometric and Negative Binomial by stopping rule.
- This exact slice supplies a geometric formula and trial-count convention missing from the current L07 slide p. 14. OpenIntro §4.2 uses the same convention, whereas Blitzstein §4.3 reserves Geom for failures before the first success and calls the trial count First Success.
- Page 43's explanatory bullet for p=0.5 says E(X)=0.5 while saying two trials on average. For this deck's convention the correct mean is 1/p=2. Do not copy the printed 0.5.
- These pages do not establish a memorylessness formula. Do not attribute that property to this slice without another checked source.

Plan implication: narrow the existing 2025 L07 menu route to pp. 38-44 for a helpful geometric derivation, and use a source-specific stage angle that states the trial-count convention and p. 43 error. The current deck remains the primary scope source.
