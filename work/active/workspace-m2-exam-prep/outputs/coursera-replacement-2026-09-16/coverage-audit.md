# Retiring the paywalled Ng course from SaD — 2026-09-16

`source-ng-coursera` is the only source in this module behind an enrolment wall.
Its own route text admitted it: "Open goes to the course syllabus, not an
individual lesson. Access to videos or labs may require enrollment."

Two routes depended on it, and a per-node check of what else already covers their
claims showed the paywall buying nothing that free material does not already
supply at the same depth:

- `knowledge-sad-l03-gradient-descent` — 10 other routes, 3 at intuition depth
  (3Blue1Brown, Kelleher, StatQuest).
- `knowledge-sad-l03-scaling-weights` — 13 others, 2 at intuition depth.
- `knowledge-sad-l03-simple-regression` — 20 others, 3 at intuition depth.
- `knowledge-sad-l11-generalization` — 12 others, 3 at intuition depth.
- `knowledge-sad-l11-resampling` — 11 others, **none at intuition depth**.
- `knowledge-sad-l11-evaluation` — 11 others, **none at intuition depth**.

So the L03 route is removed as pure redundancy, and the two L11 nodes that would
have lost their only intuition-depth route are refilled with free material read
firsthand before it was routed.

## Replacements

- `knowledge-sad-l11-resampling` — StatQuest cross validation. Recorded
  **medium, not high**: it works data-role separation, the leakage argument and
  block rotation, but the node also names the bootstrap and the word does not
  appear once in the transcript.
- `knowledge-sad-l11-evaluation` — StatQuest ROC and AUC. High: the threshold
  sweep, ROC as a summary of per-threshold confusion matrices, AUC, and why
  precision beats the false-positive rate under class imbalance.

## Also in this change

The OpenIntro L02 route's `angle_detail` still ended "…contingency tables, which
is where Simpson's paradox lives", pointing a learner at §2.2 for a topic that
book never mentions. The `covers` claim was correctly dropped on 2026-09-15 after
a full-text search found zero occurrences of "Simpson" in all 422 pages; the
sentence was left behind. It is removed here so the prose and the claim agree.

## Local

Two caption transcripts under `BASE/transcripts/`, with line-level verdicts under
`BASE/recheck/`. All 13 quoted citations across both packages were re-verified
mechanically against their transcript at the cited timestamp: 13/13 matched. The
OpenIntro claim rests on a full-text extraction of the operator's own PDF (0
occurrences of "Simpson" in 422 pages, checked 2026-09-15 and unchanged).

## Linked

Both replacement URLs verified live 2026-09-16 — see `BASE/VERIFIED-URLS.txt`.
Both route under the existing `source-statquest` registry record; no new source
is needed for this module.

## Completeness

Boundaries of this package: one source retired with its 2 routes, 2 routes added,
1 `angle_detail` corrected. Six (source, unit) claims were checked for surviving
coverage before the removal; the four that keep intuition-depth coverage are
listed above with their counts, and the two that would not are refilled here.
Study-map stages that referenced the retired routes are repointed in the paired
`unit.map.import` writes; no stage is left holding a dangling `route_id`.
Remaining gap recorded and not papered over: the bootstrap half of
`knowledge-sad-l11-resampling` is still carried only by derivation-depth routes.

## Checks

Both replacement URLs verified live 2026-09-16 (`VERIFIED-URLS.txt`). Transcripts
under `BASE/transcripts/`, line-level verdicts under `BASE/recheck/`; all 13
quoted citations re-verified against their transcript at the cited timestamp,
13/13. No other route, locator or cover in this module is touched.
