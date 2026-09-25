# Session report — s03-learner-2026-09-25 (INTERIM CHECKPOINT)

> Interim record written at the user's request mid-run. S02, S03 and S04 are
> complete; S05 is in progress (before-snapshot taken, arrivals triaged, no
> writes yet); S06, S07, S08 and S13 have not run. This file will be replaced
> by the final report.

- Plan / role: L — blind consumer, serious learner
- Blind: yes · Product revision: 200a36185fd5 · World HEAD: 13ad2fcaa0e4 · Eval revision: 3a53589545d7
- Started: 2026-09-25T00:14Z (container clock) · Checkpoint: ~00:45Z

## What I set out to do

Act as the learner's operator on a first encounter with this LearningOS
installation. Answer her retrieval questions, find connections, file new
material and record corrections using only the product's documented
interfaces. Record everything behind the curtain with `observe.py`.

## Scenario outcomes so far

| Scenario | Classification | One-line reason |
|---|---|---|
| S02 | PASS_WITH_FRICTION | All 36 answered with evidence and no canonical change. Queries by id or title were fast. Four corpus-wide questions (Q29, Q34–Q36) needed a full manual read, and Q27–Q28 and Q32 leaned mostly on my reading, because inbox and Garden have no query command, `resume` omits the stage note, search is metadata-only by default, and `related` is thin. |
| S03 | PASS_WITH_FRICTION | 20 ranked lists. `related` on a note never returns another note, so I scripted a 2-hop traversal plus searches. 89 of 177 targets came only from my reading, including most cross-course links. |
| S04 | PASS_WITH_FRICTION | A09 was filed verbatim into the OS L07 deadlock stage note via `stage.note.write` (receipt transaction-20260925-003900-001) after approval. The approval intent hash is undocumented, so I read `tools/learning_os/contracts/gateway.py`. `los operations` then labelled the committed write AMBIGUOUS. |
| S05 | in progress | — |
| S06, S07, S08, S13 | not yet run | — |

## Failures so far (failures.jsonl)

- **F-s03-diag-ambiguous-01** (AMBIGUOUS). `los operations` reports a
  committed, receipted write as `canonical_outcome: AMBIGUOUS`,
  `needs_attention`, `ui_outcome: BLOCKED`. It happens after two rejected
  attempts that shared the idempotency key. I may have caused it myself by
  reusing the key after correcting the envelope; the docs don't say whether
  that is allowed.

## Friction that cost the most (so far)

1. **Connection discovery.** `related NOTE` returns only the note's own
   concept, source and workspace ids. Neighbour notes needed ~60 scripted
   `related` calls plus 27 searches, and cross-domain links needed a full
   read of all 116 notes.
2. **Writing through the gateway.** `intent_sha256` is documented only by
   name. I had to read the implementation, and one submission failed on it.
   Which artifacts `expected_revisions` must cover is also undocumented per
   capability, though the error message names them.
3. **Missing write paths for inbox routing.** WORKFLOWS §21 sends a capture
   either to a workspace's `scratch/` or to a new durable note. No capability
   does either, so only stage notes, the inbox, the Garden and `note.revise`
   of an existing note are available.

## What the product made easy

- Single-record facts. Exam dates, grades, registrations and decisions come
  back authoritatively from `inspect`.
- `bootstrap --brief` is a good one-page entry point.
- Deprecated notes are kept and visible.
- Error messages for revision guards name the exact missing and unexpected
  artifacts.
- Receipts are complete: before/after hashes, revisions, intent hash and the
  grant.

## Behind the curtain

- Reads never change canonical state. The snapshot id is stable across reads.
- The S04 write left three new untracked ledger files under
  `operations/transactions/` and appended to `operations/diagnostics/traces.jsonl`.
- After the write, `inspect study-map-os-l07` shows the new stage-note text
  but `notes_updated: 2026-09-02` (the last git commit date, not the write).

## Deviations

See `run.json` → `deviations`.

## NOT TESTED

Obsidian UI (not available). Nothing in S02–S04 depended on it.
