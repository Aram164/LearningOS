# Deferred items — shelved questions and follow-ups (2026-09-08)

Source: items parked during L07/L08/L09 audit-repair passes and Phase A/B
cost-reduction work. None of these authorize canonical mutation; each needs
its own investigation before any repair envelope is built. Status: OPEN.

## L08 weak edges (from 2026-09-08 audit report, default no action)

1. L08 Pitman p.255 edge — NOT_FOUND + id-only map row; needs rescan + id-name alignment.
2. L08 Grinstead & Snell edge — WEAK_VERBATIM_NOT_FOUND; needs rescan, single-source pp.133-143.
3. L08 OpenIntro edge — WEAK_VERBATIM_NOT_FOUND (pp.166-167 scanned clean); likely dropped with nb01 fallback if needed.
4. L08 Tijms edge — WEAK_VERBATIM_NOT_FOUND; needs digitization rescan.
5. L08 JB-Statistics edge — WEAK_VERBATIM_NOT_FOUND; needs native doc re-pull.
6. L08 Dekking §4.2 transform-sum edge — WEAK_EXACT_NOT_FOUND; needs rescan or weakened claim.
7. L08 Regensburg edge — WEAK claim text with only 1 of 4 sources resolving; needs source-axis rewrite.

## L09 parked questions (from 2026-09-08 audit, default no action)

8. L09 Blatt-4 slot-machines edge — NOT_FOUND; needs rescan or drop.
9. L09 UE 5 sample-space edge — NOT_FOUND; needs rescan or drop.
10. L09 single-video-t edge (topic t) — video-only, no citable second; needs second stat source or downgrade to companion.
11. L09 Stage 7 as `exam_critical` — needs exam-answerability evidence from UE/Blatt; do NOT set without it.
12. Leuphana pp.11-16 collision — L09q2 (Gegenereignisse) and L09t collide; check PDF bytes pp.11-16, re-extract, merge or split.

## Stages 6/7 coverage gap

13. Stages 6 and 7 have zero `exam_critical` assignments — needs UE/Blatt evidence sweep before any promotion.

## Cost-reduction follow-ups

14. Phase A2: batch reads (`reads.resolve_many`) — needs benchmark + digest-mismatch rate first.
15. Stage-scoped map read (`unit.map.read --stage 5` projection using existing `topic_refs`) — needs agreement this is read-path-only.
16. Phase C: dossier serving + intent-evidence conflict path + semantic-diff read-receipt settle (`--reads-from`) — needs full proposal write-up, not started.
17. Phase D: detectors, page-text cache, prefetch — needs full proposal write-up, not started.
18. Phase-6 packages: duplicate `transaction_id` upstream of lineage — decided acceptable (packages validate independently); needs re-test at Phase B scope.

## Study-map hygiene (carried, unowned)

19. L09 orphan slash-alias rows + renamed-file row naming (`unit.map.import` warnings) — needs map-owner decision.
20. Duplicate unit aliases in `study-maps/m2-sad-unit-map.yaml` — needs map-owner decision.
21. `data-bias` Stage 7 `exam_critical` map-vs-package skew — needs map-owner decision.
