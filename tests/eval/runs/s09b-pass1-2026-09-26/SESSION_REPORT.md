# Session report — s09b-pass1-2026-09-26

- Plan / role: F — friction-investigator (Pass 1 of 3)
- Blind: yes · Product revision: 8d1cc470d73a252bb7d87dc36c81e71e5db7c0d2 · World HEAD: a62b39169269ba26e13b7fbda9e3ad56367b1ef9 · Eval revision: 3c30d03e2c2c2805b4d52288e3d69f0e6ebd4bd1
- Started / finished: 2026-09-26T07:40:39Z / 2026-09-26T07:57:05Z

## What I set out to do

Plan F pass 1: S02 (Q06, Q07, Q13, Q15, Q27), S10, S26 against a fresh world
built from the frozen landed revision, acting as a first-time consumer agent.

## Scenario outcomes

| Scenario | Classification | One-line reason |
|---|---|---|
| S02 | PASS_WITH_FRICTION | 5/5 answered; milestone ids uninspectable, no inbox list cmd |
| S10 | PASS_WITH_FRICTION | where-was-I + 2 receipted writes; guard set found via refusal |
| S26 | PASS | 3/3 goals, 7 calls, no failures |

## Failures (see failures.jsonl)

No failures.jsonl: nothing rose to FUNCTIONAL/ROBUSTNESS/USABILITY/PERFORMANCE
failure. Friction items live in results/*.json.

## Friction that cost the most

1. Envelope ceremony for small writes (~4 min across S10's two writes; S26's
   capture was smooth only because S10 taught the recipe first in this pass).
2. Exact expected_revisions per capability undiscoverable up front
   (1 refused submit + reseal in S10).
3. Fresh-install `make setup` (~100s network install) dominates first-contact
   time; milestone/inbox discovery gaps added ~3 calls in S02.

## What the product made easy

Task-shaped entry (bootstrap/resume/inspect/search/note-read) answered 5
retrieval questions in 19 calls; refusal messages name the exact defect
(missing guard); reads serve fresh state immediately after writes; receipts
and request ids make every write attributable.

## Behind the curtain

3 commits, 1 INVALID_REQUEST refusal; snapshots 5e09→3bc4→1090 (S10),
5e09→5d6c (S26). resume.yaml changed without needing a guard. No unexpected
writes; no warnings/errors besides the one designed refusal.

## Uncertainties

- Idempotency-key reuse after a refused (uncommitted) attempt: untested.
- Guard model for resume.yaml writes: undocumented.
- Whether the gateway refreshes generated/ views post-commit: not checked via
  a product interface.
- Q27 routing and the S26 3-week frame involve operator judgment.

## Deviations from the protocol

See run.json: per-pass run dirs; one build per pass + sanctioned resets;
/tmp paths; setup once per pass; no failures.jsonl.

## NOT TESTED

Anything needing the Obsidian UI.
