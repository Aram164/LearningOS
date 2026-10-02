# Retiring the paywalled Ng course from AML — 2026-09-16

`source-ng-coursera` is the only enrolment-walled source in this module. Four
routes depended on it, all at intuition depth. A per-node check found every claim
already covered by free routes **on the same unit**, most of them by Andrew Ng's
own Stanford lectures and notes, which are free:

- L03 `problem`/`loss`/`solution`/`vectorization` — CS229 notes, CS229 2022
  videos, MIT 6.036, StatQuest, Caltech, Setosa. Intuition depth survives on all
  four nodes.
- L04 `basis`/`overfitting`/`ridge`/`lasso` — CS229 notes and the CS229 2022
  lecture cover the identical four nodes; ISLP, StatQuest and Caltech also.
- L05 `classification`/`sigmoid`/`cross-entropy` — CS229, MIT 6.036, StatQuest,
  ISLP. `boundary` was the one node with **no intuition-depth survivor**.
- L06 `batch-gd`/`rate-scaling`/`stochastic` — CS229, MIT 6.036, StatQuest,
  CS231n notes, 3Blue1Brown.

So the four Coursera routes are removed, and only `knowledge-aml-l05-boundary`
needed a replacement.

## Replacement

`knowledge-aml-l05-boundary` — Herman Kamper (Stellenbosch University),
"Logistic regression 3: The decision boundary and weight vector". High
confidence: the boundary is derived as the locus where the sigmoid of
w-transpose-x equals 0.5, i.e. where the score is zero, and the weight vector is
shown to be orthogonal to it. That is the node's geometry — separator, score
sign, threshold — rather than the sigmoid story alone.

A StatQuest logistic-regression video was considered first and **rejected**: it
teaches the S-curve and log-odds and never treats the separator geometry, so it
would not have earned the node.

## Local

One caption transcript under `BASE/transcripts/` with its line-level verdict under
`BASE/recheck/`; every quoted citation re-verified at its timestamp. The
survivor counts below come from a per-node scan of this module's own source map.

## Linked

The replacement URL was verified live 2026-09-16 — see `BASE/VERIFIED-URLS.txt`.
It routes under a new registry record, `source-kamper-logreg`, which ships in the
same change because the gateway cannot create registry records.

## Completeness

Boundaries of this package: one source retired with its 4 routes, 1 route added.
All fifteen node claims carried by the retired routes were checked individually
for surviving same-depth coverage before removal; fourteen survive on free routes
already present on the same unit, and the fifteenth is refilled here. Study-map
stages that referenced the retired routes are repointed in the paired
`unit.map.import` writes; no stage is left holding a dangling `route_id`.

## Checks

URL verified live 2026-09-16 (`VERIFIED-URLS.txt`). Transcript and line-level
verdict under `BASE/`; every quoted citation re-verified at its timestamp. No
other route, locator or cover in this module is touched.
