# Session report — s07-abuse-2026-09-25

- Plan / role: X — abuse / failure investigator
- Blind: yes · Product revision: 200a36185fd5c693b4464ce0bdff4be5b89ce584 · World HEAD: 13ad2fcaa0e478afddba6451e29376ca00f0bc8e · Eval revision: 658db28d0c389f7ac2e5cbf878d099d4d359ec67
- Started / finished: 2026-09-25T02:12Z / 2026-09-25T11:06Z (about 8 h of that was idle, waiting for the user; roughly 95 active minutes)

## What I set out to do

Run plan X in order (S01, S17, S18, S19, S20, S21, S22, S24). Try hard to break the
installation inside my own evaluation worlds: kill writes and the recovery that follows
them, make derived state stale, delete it and corrupt it, feed malformed and edge-case
records, and repeat, reuse and race writes. Every write went through the product's
gateway (`los capability … --payload-file`). I sealed each approval with the product's
own `intent_sha256`, only for writes the probe procedures call for. I patched nothing.

## Scenario outcomes

| Scenario | Classification | One-line reason |
|---|---|---|
| S01 | PASS_WITH_FRICTION | Setup, check, warnings, status and views all green. `make test-fast` fails 18 tests tied to the owner's data, and it writes 135 trace spans into the learner's live operation log. |
| S17 | ROBUSTNESS_FAILURE | Recovery is sound: no PARTIAL state in 32 probe kills + 42 manual write kills, and recovery survives 17 kills of itself. But until a lock-taking command runs, `inspect`/`search` show the uncommitted write while `bootstrap`/`plan-edit-context` silently roll it back. |
| S18 | PASS_WITH_FRICTION | CLI reads always reflect the hand edit, and a write on the stale published snapshot fails closed. Views and the manifest stay stale; only `validate` warns, and the views' "Generated:" stamp cannot reveal it. |
| S19 | PASS | Rebuild after deleting all derived state is byte-identical (20 files). A contrived directory-in-place-of-manifest crashes `generate`. |
| S20 | FUNCTIONAL_FAILURE | Two schema-valid inputs certified clean by `make check` take search, inspect, bootstrap and writes down: a documented `supersedes:` edge, and a unit without the optional `scope_sources`. |
| S21 | PASS_WITH_FRICTION | Replay, conflict and `--replay-only` are correct with intact ledgers. `los operations` mislabels outcomes, and losing both untracked ledgers lets a reused key commit a duplicate. |
| S22 | PASS_WITH_FRICTION | 10 rounds × 3 simultaneous writes: exactly one winner per round, 20 `STALE_SNAPSHOT`, and no lost, duplicated or partial write. Retry works. No torn reads in 24 reads racing 12 writes. |
| S24 | PASS | Two builds in different directories: same HEAD, same trees, byte-identical derived state, also under another TZ and locale. |

## Failures (see failures.jsonl)

Ordered by what I judge most consequential.

**F-s07-06 — the documented supersession breaks the product (FUNCTIONAL).**
Expected: WORKFLOWS §15 prescribes `supersedes: [note-old-id]`; the note schema allows it,
and the validator accepts it. What happened: `make check` reports 0 errors, but
`generate`, `search`, `inspect`, `related` and `bootstrap --brief` exit 2. The published
manifest has a backlink `{from, kind: 'superseded-by'}` where contract v15 expects a
string. A capture then fails with INTERNAL_FAILURE and leaves a journal. The message tells
the consumer to run `manifest_contract.py --bump` and mirror the change into the UI repo.
Minimal: add one line `supersedes: [note-b-plus-tree-indexes]` to any note. Own
mistake? The line was written by hand, but no capability exists for supersession and
the workflow says to do exactly this.

**F-s07-07 — record schema and manifest contract disagree on `scope_sources` (FUNCTIONAL).**
Expected: `unit.schema.json` makes `scope_sources` optional, and "clean" means zero
validator errors. What happened: deleting the 4-line block leaves `make check` OK, but
every projection-backed read and the tested write fail with the same contract-bump
instructions. The message names `/units/8`, not the file. Own mistake? A hand edit of a
canonical record, which OPERATOR.md steers through capabilities. The validator still
calls it clean.

**F-s07-03 — reads expose uncommitted writes after a crash (ROBUSTNESS).**
Expected: "committed atomically" (README), and `inspect`/`search` are the sanctioned
reads. What happened: after `stage.progress.update` (→ paused) is SIGKILLed between the
file rewrite and the receipt, `inspect unit-os-l02`, `inspect study-map-os-l02` and
`search scheduling` report *paused*. `plan-edit-context` and `bootstrap --brief` roll
the journal back and report *active*, after which `inspect` also says *active*. `validate`
(0 errors) and `status` never mention the pending journal. Minimal: kill at 0.5 s, then
`inspect`. Own mistake? The kill is deliberate abuse, but any process death produces
it, and nothing is lost permanently.

**F-s07-08 — refusals misreported as retryable INTERNAL_FAILURE with an orphan journal (ROBUSTNESS).**
Expected: `VALIDATION_FAILED` exists in the envelope schema and is what case b got
(retryable false, no journal). What happened: with a frontmatter parse error elsewhere,
or with F-06/F-07 present, any write returns INTERNAL_FAILURE, retryable true, "rollback
incomplete for: <projection publication>". Each attempt leaves
`.inflight/<txn>/intent.json` even though the process exited normally. `los operations`
advises "reconcile-exact-request", yet that request fails again while the defect exists
and gets STALE_SNAPSHOT once it is fixed.

**F-s07-11 — idempotency depends on two untracked ledgers that are never reconciled (ROBUSTNESS).**
With `idempotency.yaml` and `revisions.yaml` both gone, which is what a `git clean -fd`
before committing leaves, re-submitting a committed key re-sealed on the fresh snapshot
commits a duplicate capture. Two receipts now carry `idem-s21-k1`, and `validate`
reports 0 errors. With only the idempotency ledger gone, `--replay-only` claims "no
committed receipt exists" although the receipt file is on disk. Own mistake? It requires
losing both files; the revisions ledger alone still blocks the duplicate.

**F-s07-01 — `make test-fast` writes into the learner's live operation log (ROBUSTNESS).**
README calls it "synthetic fixtures, no checked-in repository load". Afterwards `los
operations` lists 45 fabricated requests (`req-capture.create`, `req-bad-payload`, …),
all AMBIGUOUS and needs_attention.

**F-s07-10 — `los operations` labels are misleading (USABILITY).**
Every successful CLI write shows `ui_outcome: BLOCKED`, `needs_attention: true`
("no observation is on record"), and nothing documents how to settle it. A definite
IDEMPOTENCY_CONFLICT is shown as AMBIGUOUS, "exact request stays recoverable". Two writes
sharing a request_id collapse into one explanation.

**F-s07-04 — the views' "Generated:" stamp is the last-commit time (USABILITY).**
The README's human fallback says to judge staleness by it. The stamp is identical before
and after regenerating different content.

**F-s07-09 — any pre-existing defect blocks every write, including inbox capture (AMBIGUOUS).**
A parse error additionally blocks search, inspect and bootstrap repository-wide. This is
fail-closed by design and the file is always named, but the refusal never says the
defect is pre-existing and unrelated to the request.

**F-s07-02 — 18 test-fast failures on the owner's own files (AMBIGUOUS).**
`test_pilot_replay.py` reads the owner's workspace drafts, and a `real_repo` test is not
marked full_repo. Triggered by the synthetic world swapping learner data.

**F-s07-05 — manifest path replaced by a directory → `generate`/`validate`/`status` tracebacks (ROBUSTNESS, contrived).**
The documented repair (`make views`) cannot fix it; only a manual `rmdir` does.

## Friction that cost the most

1. **Constructing the first envelope (S17):** 4 submissions and 6 tool calls. WORKFLOWS
   §25a lists the fields but not the channel enum, the approval shape, or the
   intent-hash algorithm. The first error ("not valid under any of the given schemas")
   names no field. I needed the envelope schema file plus
   `tools/learning_os/contracts/gateway.py`. After that, the product's error messages
   (the missing `capture-request:<key>` revision; the approval mismatch) were precise.
2. **`make test-fast` in S01:** a 331 s run ending in 18 failures that belong to another
   person's data. Two implementation files read to understand them, plus the trace-store
   side effect.
3. **Establishing what an INTERNAL_FAILURE "rollback incomplete" left behind (S20):**
   4–5 tool calls per case (git status, journal contents, `los operations`, retries) to
   show that canonical files were restored and only a journal remained.

## What the product made easy

- Snapshot and revision guards fail closed with actionable details: STALE_SNAPSHOT
  names expected and actual; REVISION_CONFLICT names the artifact; an idempotency
  conflict is explicit.
- Crash recovery: journal-first writes, idempotent recovery, and a retry of the same
  envelope after a kill commits exactly once.
- Concurrency: no lost or duplicated write in 30 racing writes; batch `inspect` is
  snapshot-consistent under concurrent writes.
- Derived state is genuinely disposable and deterministic, byte-identical across
  rebuilds, directories and TZ/locale. CLI reads never depend on `generated/`.
- The validator names file, record and rule for every defect it knows about (PARSE,
  REF-CONCEPT, WS-SECTION, UNIT-MAP-UNDECLARED).
- Replay needs no current snapshot, and `--replay-only` verifies without writing.

## Behind the curtain

- Transaction mechanics seen from outside: `.inflight/<txn>/intent.json` plus
  `backup-N`, then files, then the receipt, `idempotency.yaml` and `revisions.yaml`.
  `capture.create` guards a request-scoped artifact `capture-request:<idempotency_key>`
  at revision 0. `curriculum/resume.yaml` is rewritten by `stage.progress.update` but is
  not an expected_revisions artifact.
- Recovery triggers: `los generate`, `plan-edit-context`, `bootstrap --brief` and any
  capability submission. Not triggered by `status`, `validate`, `inspect`, `search`,
  `resume`, `operations` or `intelligence-scan`.
- `stage.progress.update` to *paused* on one stage also sets the unit and the study map
  to paused. A no-op update (paused→paused) commits a receipt and bumps both revisions
  although every file is byte-identical.
- The diagnostic trace store (`operations/diagnostics/traces.jsonl`, gitignored) survives
  `git reset`/`git clean -fd`. After resets, `los operations` mixes attempts from states
  that no longer exist; in S17 it reported a request as committed that the current tree
  never committed.
- A binary capture keeps its basename; a second file with the same name gets a timestamp
  prefix, so nothing is overwritten. Inbox files are not search records.
- `status` prints "validation: 1 error(s) · N warning(s), visible and nonblocking", which
  reads as if the error were nonblocking too.

## Uncertainties

- Whether the owner's real repository contains any `supersedes` edge or a unit without
  `scope_sources`. If so, their `generate` would already fail; if not, these paths are
  simply unexercised by the product's own data and tests.
- Crash behaviour under power loss (fsync ordering) rather than SIGKILL.
- Whether the Obsidian UI's reads trigger recovery, and whether its "observation" step is
  what clears `BLOCKED`/`needs_attention`.
- Lock fairness under contention heavier than 3 writers.

## Deviations from the protocol

See `run.json` → `deviations`. In short: a separate fresh world per scenario (S20 cases
reset in place); an 8-hour idle gap waiting for the user; approval values computed with
the product's own `intent_sha256`; extra probes recorded inside their scenarios; the S22
race used back-to-back Popen. Blindness: I saw only the directory names `~/los-eval/oracle`
and `runs` and other sessions' branch names, and opened none of them.

## NOT TESTED

- Everything that depends on the Obsidian UI: the UI's reading of `generated/manifest.json`
  (stale in S18, unpublishable in S20 e/f); UI observation and acknowledgement of
  operations; UI behaviour after crashes.
- `make system-check` / `make stress` (they need the sibling UI checkout).
