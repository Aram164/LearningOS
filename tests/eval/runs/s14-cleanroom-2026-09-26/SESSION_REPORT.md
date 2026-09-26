# Session report — s14-cleanroom-2026-09-26

- Plan / role: O (Plan N + Plan C) — clean-room-final-consumer, first contact with the final revision
- Blind: yes · Product revision: eec74eb1b1b22f13fb5fb94c043484956b175423 · World HEAD: 00becd4796c09e42199c9dd0d0f75ed5b99c4185 · Eval revision: eec74eb1b1b22f13fb5fb94c043484956b175423
- Started / finished: 2026-09-26T01:09:23Z / 2026-09-26T01:57:00Z

## What I set out to do

Clean-room consumer evaluation of the final repaired product revision: build the
required worlds outside the repo (`--source-rev WORKTREE`, seed 20260924),
verify deterministic reconstruction, then execute Plan N (S00, S01, S02/Q01–Q12,
S04, S06, S10, S14, S15, S26) plus Plan C (S03, S27) exactly per the public
consumer protocol — learning the product only through its documented
interfaces, recording outcomes, friction, and any consumer-visible failure.
No repairs, no product changes.

## Scenario outcomes

| Scenario | Classification | One-line reason |
|---|---|---|
| S00 | PASS_WITH_FRICTION | Five-line answer delivered, but `make views` fails pre-setup on a fresh install |
| S01 | PASS | Setup exit 0, views build, 0 errors, baseline matches, zero tracked changes |
| S02 | PASS_WITH_FRICTION | Q01–Q12 answered with evidence; content search needs writable derived-state; stages not directly inspectable |
| S03 | PASS_WITH_FRICTION | C01–C20 recorded; `related` returns links not ranked candidates, so manual triangulation per probe |
| S04 | PASS_WITH_FRICTION | A09 captured + filed as durable note with receipt; note-creation mechanism ambiguous across docs |
| S06 | PASS | 3 duplicates preserved losslessly in inbox with receipts, no duplicate records |
| S10 | PASS | Resumption sourced; stride progress appended via stage.note.write, stage left active |
| S14 | PASS | Clarified before writing; cosmetic cross-links only, after diff approval |
| S15 | PASS | Rewrite approved via shown diff first; original reasoning kept in-note + git history |
| S26 | PASS | 3/3 goals, 5 calls; only nit is unstemmed search |
| S27 | PASS | A01–A30 probed (A24 honestly empty); world verified unchanged |

## Failures (see failures.jsonl)

No failures.jsonl: no FUNCTIONAL/ROBUSTNESS/USABILITY/PERFORMANCE failure was
observed that survived the "retry once if a reasonable user would" rule. Every
write path exercised (capture.create ×5, stage.note.write, note.revise ×3)
committed on the first attempt with a receipt, and every `make check` ended at
0 errors. Friction items that cost real effort are recorded per scenario
instead; the largest are below.

## Friction that cost the most

1. **Connection discovery has no ranked related-notes command** (S03, ~75 min
   for 20 probes): `related` returns the note's own linked concepts/sources,
   so each probe needed a full query-note read plus 1–3 single-term searches
   plus candidate reads. Multi-term search silently returns [] under AND
   semantics, which had to be discovered by probing.
2. **Shelving-path ambiguity for a friend's capture** (S04, ~6 extra doc
   reads): `review.prepare`/`shelving-prepare` targets curriculum units,
   `capture.create` targets the inbox, and WORKFLOWS §3 describes direct
   operator filing of knowledge notes — while OPERATOR.md's "capabilities
   that create durable notes" list excludes the §3 path that fits an
   anecdote. Resolved via capture receipt + §3 filing; no defect claimed.
3. **Fresh-install ordering** (S00/S01): README's prescribed first step
   (`make views`) fails before `make setup`, and `generated/` starts empty,
   so orientation must fall back to bootstrap JSON plus workspace reads.

Smaller: `los inspect` does not resolve stage ids (read via parent study
map); note-read pagination needs `--expected-snapshot`; search has no
stemming (`caching` misses `cache` notes); `make check` before regenerating
reports transient HYGIENE-VIEWS.

## What the product made easy

- The envelope recipe (WORKFLOWS §25c) is complete and exact: snapshot,
  revision guards, intent hash, approval kinds — all six envelopes across
  three capabilities committed first try, and the refusal-shape docs meant
  no guessing was ever needed (no refusal occurred).
- Reads are uniform and predictable: `bootstrap --brief`, `resume --json`,
  `search`/`--content`, `note-read`, `inspect` composed into every
  retrieval and connection answer without implementation reading.
- Scripted-approval mechanics are honest: the intent hash covers exactly
  the change shown, and receipts/ids made every write auditable.
- Deterministic world builds: two independent builds agreed byte-for-byte
  (HEAD `00becd4…`, empty observer diff).

## Behind the curtain

- Receipts: 9 transactions total (S04 ×1, S06 ×3, S10 ×1, S14 ×2, S15 ×1,
  S26 ×1), all `ok: true`, none replayed; idempotency/revision ledgers
  updated accordingly; unit-os-l02 revision 0 → 1 on the stage write.
- Snapshots advanced per transaction; every scenario diff carried zero
  observer flags (no receiptless canonical change, no inflight journals).
- Derived state: search/derived-state caches appear under `generated/` on
  reads (20 view files + 118 cache files); all git-ignored; `git status`
  in the world stayed clean except for scenario-intended writes.
- No implementation files (`tools/**`, `tests/**`) were read in any
  scenario; `implementation_knowledge_needed: false` throughout.

## Uncertainties

- Whether direct operator filing of knowledge notes (WORKFLOWS §3) is the
  intended path for captures like A09, given OPERATOR.md's narrower
  "capabilities that create durable notes" list. Chose §3; recorded.
- Whether `related` is *supposed* to rank related notes (I treated its
  concept/source listing as complete and triangulated manually).
- S26 "next three weeks" counted from the world's as_of (2026-09-18):
  StatLearn Oct 6 inside, OS oral Oct 12 just outside; reported both with
  explicit dates rather than cutting one off.

## Deviations from the protocol

See `run.json` → `deviations` (7 items): combined N+C recorded as plan O; A09
after-shelving record embedded in S04.json (one-record-per-probe rule);
product_revision recorded as the exact base SHA behind WORKTREE; one
top-level `~/los-eval/` name listing (no contents opened); world commands
run outside the managed sandbox (environment necessity, not product
behavior); fresh resets kept ignored `.venv`/`generated/`; no oracle
contact whatsoever. `blind: true` throughout.

## NOT TESTED

Anything needing the Obsidian UI (none of the N+C scenarios required it).
No scenario was marked NOT TESTED for environment reasons.
