# SaD gap-fill coverage audit — 2026-09-16

Scope: the weakest knowledge nodes in `module-hu-m2-statistik-analysis` after the
2026-09-15 video package, chosen from a canonical scan of every SaD lecture unit
rather than from the prior audit's summary. Three nodes were **deck-only** (no
non-deck route at all); the rest were either near-deck-only or carried video
coverage that the 2026-09-15 recheck had downgraded to low.

Every claim below was verified firsthand: videos by fetched caption transcript
read line by line, books by full-text extraction of the local PDF. No claim rests
on a title, a table of contents, or an index entry.

## Local

11 caption transcripts under `BASE/transcripts/` (10 new, plus `L2KMttDm3aY.md`
already held from the 2026-09-15 package and reused unchanged). Line-level
verdicts under `BASE/recheck/`. All 41 quoted citations in those verdicts were
re-checked mechanically against their transcripts at the cited timestamp: 41/41
matched. Book claims were verified against the operator's own PDFs in
`LearningOS/materials/`; page numbers are PDF pages per `system/PLAN-CREATION-SOP.md`.

## Linked

All 11 video URLs and both Mining-of-Massive-Datasets URLs verified live
2026-09-16 — see `BASE/VERIFIED-URLS.txt` for the response of each.

Channel-to-source mapping: StatQuest (2) and jbstatistics (4) route under existing
registry sources. Four sources are new and carry registry records in this same
change: CrashCourse Statistics, minutephysics, PsychExamReview, and the free
Mining of Massive Datasets book (Leskovec/Rajaraman/Ullman, mmds.org). The two MIT
segments are **RES.6-012 Introduction to Probability (Spring 2018, Tsitsiklis,
CC BY-NC-SA)**, confirmed from the videos' own descriptions — deliberately *not*
filed under the existing `source-mit-6041sc`, which is a different course.

## Completeness

20 new routes across 10 units. No route is a replacement: every one is additive,
and no existing route, locator or cover was modified by this package.

Deck-only nodes closed:

- `knowledge-sad-l01-course-map` — CrashCourse Statistics #1.
- `knowledge-sad-l04-framing` — PsychExamReview framing effect, plus Tijms p.16.
- `knowledge-sad-l13-lsh` — Mining of Massive Datasets ch.3 §3.4. **No book the
  operator owns teaches LSH**: Kelleher's index entry points at a page with no
  hashing content, Murphy mentions it only in passing, and CSC411 states outright
  that it does not cover it. The free MMDS chapter is therefore the only real
  treatment available and is the primary route for this node.

Low-confidence video coverage replaced by material that actually works the thing:

- L06 `concentration` — the prior route invoked the LLN without ever stating a
  bound. MIT L18.3 states and proves the Chebyshev inequality; L18.4 derives the
  weak law *from* Chebyshev, so the pair closes both halves of the node.
- L07 `poisson`, `relationships`, `hypergeometric`, `model-selection` — all four
  were downgraded because one overview video defines the families but never
  computes. The replacements evaluate the Poisson PMF to 0.163, derive the
  binomial→Poisson limit by substitution and apply it, and evaluate the
  hypergeometric PMF to 0.01354 / 0.166490.
- L01 `distributions`, `sampling-context` — histogram construction with the
  bin-width tradeoff, and population-versus-sample with the reason sampling is
  necessary.

## Honest limits

- `sv_KXSiorFk` (L07 `model-selection`) is recorded **medium, not high**. The
  video states at [00:20] that it does no calculations; it is assumption-to-family
  judgment only, which is the node's subject but stops short of a computed rule.
- `knowledge-sad-l02-simpson` gained an intuition route but remains thin at two
  non-deck routes. Its book coverage is Blitzstein Ex 2.8.3 alone, because
  OpenIntro was falsified for Simpson on 2026-09-15 (0 occurrences in 422 pages)
  and Tijms' six "Simpson" hits are all the O.J. Simpson trial, not the paradox.
- `L2KMttDm3aY` is routed to L07 while already routed to L05. This is deliberate
  cross-unit reuse of one video through two different nodes, not a reassignment;
  the L05 route is untouched.
- Nodes still carrying no video and no intuition-depth route after this package
  are recorded as remaining gaps, not as covered: L01 `data-questions`,
  L10 `multiple` (book-only by choice — the fills are ISLP ch.13 and Fahrmeir),
  L12 `stacking`, L14 `bayes-net`/`markov`, L15 `outlook`.
