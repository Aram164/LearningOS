---
id: note-sad-l07-blitzstein-geom-convention-pp174-178
type: note
role: reference
title: 'Blitzstein L07 source angle: Geometric counting convention'
created: '2026-09-24'
state: rough
authorship: operator-drafted
semantic_review: unreviewed
material_analysis:
  resolution: resolved
  material: mathematics/probability-statistics/blitzstein-hwang/blitzstein.pdf
  source_id: source-blitzstein-hwang
  recorded_source_digest: 822330478af77872cf83f1ecd5f8a3b3e2b7796124a229af0a2aa53028525daf
  live_source_digest: 822330478af77872cf83f1ecd5f8a3b3e2b7796124a229af0a2aa53028525daf
  inspected_range:
    start: 174
    end: 178
  frozen_input_sha256: 3c9c4092e2d9614ec2c95ac19a330b1b137835ee1900fab59db7da8383258ddb
  frozen_input_bytes: 1419
  model: Codex GPT-6 2026-09
  built: '2026-09-24'
---

# Blitzstein L07 source angle: failure-count Geometric versus first-success trials

Inspected blitzstein.pdf, physical pp. 174-178, Chapter 4 §4.3. This note is limited to that section.

- Blitzstein defines X~Geom(p) as the number of failures before the first success, with support 0,1,... and mass P(X=k)=(1-p)^k p. Pages 175-176 derive its cumulative distribution and show the graph.
- Page 176 separately defines Y~FS(p), the number of trials including the successful one. Y=X+1. Page 177 derives E(X)=(1-p)/p and E(Y)=1/p. The distinction is mathematical, not a naming preference to suppress: the same word Geometric denotes the trial-count variable in the 2025 SaD deck and OpenIntro, but the failure-count variable here.
- Pages 177-178 generalize to waiting for r successes through Negative Binomial and a sum of independent Geometric failure counts. This is a useful derivation after the first-success case; it exceeds the current L07 deck's sketch and need not be an exam requirement.
- The source's distinct angle is an explicit convention translation plus derivation by a geometric series. It is not the source of the 2025 course's x=1 formula unless one shifts X by one.

Plan implication: keep the existing Blitzstein L07 menu route, but make any ordered-stage use state both support and variable definition. Do not silently transplant its E(X)=(1-p)/p into the course's trials-until-success convention.
