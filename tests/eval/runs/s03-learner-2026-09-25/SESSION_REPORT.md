# Session report — s03-learner-2026-09-25

- Plan / role: L — blind consumer, serious learner
- Blind: yes · Product revision: 200a36185fd5 · World HEAD: 13ad2fcaa0e4 · Eval revision: 3a53589545d7
- Started / finished (container clock, UTC): 2026-09-25T00:14Z / 2026-09-25T00:56Z

## What I set out to do

I played the operator for a learner who wants new material connected to
everything she has learned before, meeting this LearningOS installation for
the first time. I used only documented interfaces, starting from `AGENTS.md`,
`system/OPERATOR.md` and `los --help`. I read implementation code only when
the docs ran out, and I recorded each such read as friction. Everything
behind the curtain was recorded with `observe.py`.

## Scenario outcomes

| Scenario | Classification | One-line reason |
|---|---|---|
| S02 | PASS_WITH_FRICTION | All 36 answered with evidence, no canonical change. Lookups by id or title were quick. Corpus-wide questions (Q29, Q34–Q36) needed a full manual read of all 116 notes, and Q27, Q28 and Q32 leaned mostly on my reading. Four causes: inbox and Garden have no query, `resume` omits the stage note, search is metadata-only by default, and `related` is thin. |
| S03 | PASS_WITH_FRICTION | 20 ranked lists. `related` on a note never returns another note, so I scripted a 2-hop traversal plus searches. 89 of 177 targets came only from my reading, including most cross-course links. |
| S04 | PASS_WITH_FRICTION | A09 was filed verbatim into the OS L07 deadlock stage note, after approval, with a receipt. The approval intent hash is undocumented, so I read `contracts/gateway.py`. The diagnostics then mislabelled the write (F-s03-diag-ambiguous-01). |
| S05 | PASS_WITH_FRICTION | Nine of ten captures were filed after one batch approval, each with a receipt: six into stage notes, three appended to existing notes via `note.revise`. The sourdough capture was not filed. No capability creates a new note from a capture, and `note.revise` has no preview. |
| S06 | PASS_WITH_FRICTION | Three duplicates were recognised by hand. Two were not filed (nothing lost). One became a cross-referenced Garden seed, because no capability can edit an existing seed or retire an inbox item. |
| S07 | PASS_WITH_FRICTION | Four earlier stuck points were matched to the new material and recorded with append-only revisions. The matching came entirely from my memory of the corpus: there is no open-question list, and the question capability has an undocumented payload. |
| S08 | PASS_WITH_FRICTION | The wrong note (note-hash-join-vs-sort-merge, 'hash join is always O(n + m)') was found in one search and corrected with an append-only revision. The original line is intact. Supersession was impossible because no capability creates a note. |
| S13 | PASS | Bayesian networks are not in retake scope (checked against the L05 slide text). The answer gives a required/helpful/defer/reference triage and a prerequisite inventory. Nothing changed. |

## Failures (failures.jsonl)

**F-s03-diag-ambiguous-01 (ROBUSTNESS_FAILURE)**
- **Expected:** `los operations` explains one request per request id.
- **What happened:** this container exports `TRACEPARENT`, and every `los`
  call adopted its trace id *and* span id as its own attempt. `los
  operations` therefore merged all 12 gateway requests of S04–S05 into a
  single "operation" filed under the first request id: 21 attempts,
  `canonical_outcome: AMBIGUOUS`, `needs_attention`, `ui_outcome: BLOCKED`.
  Every one of those writes actually committed with a correct receipt.
- **Minimal reproduction** (on a scratch copy of the world): two refused
  `capture.create` envelopes share one trace when `TRACEPARENT` is set, and
  get two distinct traces with `env -u TRACEPARENT`.
- **How it could be my mistake:** the variable comes from this evaluation
  environment. Reusing one idempotency key across my three S04 attempts also
  fed the first "ambiguous" reason.
- **Afterwards:** I ran `los` with `TRACEPARENT` unset (a recorded deviation).
  Operations then read COMMITTED / NOT_COMMITTED correctly.

## Friction that cost the most

1. **Connection discovery has no product support.** `related NOTE` returns
   only the note's own concept, source and workspace ids. Neighbouring notes
   took ~60 scripted `related` calls and 27 searches. Cross-course links needed
   a full-corpus read (~110 KB, ~35k tokens). Across all 35 connection records
   (280 targets), 150 targets came from my reading. The rest came from
   product commands: 62 `related`, 44 `search`, 9 `search --content`,
   15 `inspect`. Garden seeds, inbox items, open questions and duplicates are
   invisible to search and `related`.
2. **The gateway write ceremony needs undocumented knowledge.**
   - `approval.subject_sha256 = intent_sha256(envelope)` is named but never
     specified. I read `tools/learning_os/contracts/gateway.py`; that cost 4
     calls and one failed submit.
   - `expected_revisions` keys differ per capability (unit id, note id, or
     `garden-request:<idempotency_key>`) and are documented nowhere. The
     INVALID_REQUEST messages do name them precisely, which cost one retry
     each in S04 and S06.
3. **Filing destinations are missing.**
   - WORKFLOWS §3/§17/§21 route a capture to a new durable note or to
     workspace `scratch/`, and §15 corrects a note by superseding it. No
     gateway capability does any of these. Shelving (`review.*`) is UI-gesture
     only and its item format is undocumented.
   - I could only reach stage notes (a "compatibility" capability), whole-note
     replacement (`note.revise`, with no diff or preview), the inbox and the
     Garden.
   - As a result, three captures and one correction were appended to the
     learner's existing notes instead of becoming their own notes.

## What the product made easy

- Authoritative facts. `inspect module-…` answered dates, grades and
  registrations immediately. The date conflict in the prose note
  (14 vs 12 October) was easy to show against the module record.
- `bootstrap --brief` is a good one-page entry point. `inspect study-map-…`
  returns the stage working notes.
- Corrections stay visible: deprecated notes are kept, and every write was
  append-only with an exact byte hash in its receipt.
- Revision-guard errors name the missing and unexpected artifacts, and every
  write was transactional with a complete receipt: before/after hashes,
  revisions, intent hash, grant.
- Validation stayed at 0 errors with no new warning signature after every
  batch.

## Behind the curtain

- Reads never changed canonical state, and the snapshot id was stable across
  reads.
- There were 14 committed gateway writes in total: S04 1, S05 9, S06 1,
  S07 2, S08 2. Every canonical change had a receipt, and `observe.py`
  raised no unreceipted-change flags.
- Transaction ledgers `operations/transactions/idempotency.yaml` and
  `revisions.yaml` appeared as untracked files after the first write.
- `inspect study-map-…` reports a stage note's `notes_updated` as the last git
  commit date, not the date of the gateway write.
- `note.revise` accepted `{note_id: 0}` as the revision guard and wrote exactly
  the approved bytes, leaving the frontmatter untouched. That means authorship
  still says `user` on notes that now contain appended third-party excerpts.
- The world repository was left with uncommitted changes, because no session
  end or commit was requested in plan L.

## Uncertainties

- Wall-clock minutes come from the container clock.
- Filing choices are judgement calls made without a note-creation capability:
  friend's and textbook excerpts were appended to user notes, with provenance
  headers.
- In S13, only the L05, L07 and L09 slide exports exist locally.

## Deviations from the protocol

See `run.json` → `deviations`. In short:
- interim checkpoints were pushed at the user's request;
- `TRACEPARENT` was unset from mid-S05;
- the user authorized me to compute approval hashes for writes the scripted
  learner had approved;
- S03's "fresh" world came from `git reset --hard` + `git clean -fd`;
- the model id is not recorded (repository-artifact policy).

## NOT TESTED

The Obsidian UI and everything admitted only through the UI channel
(`review.prepare`/`review.apply` shelving, `concept.relations.change`) —
not available here.
