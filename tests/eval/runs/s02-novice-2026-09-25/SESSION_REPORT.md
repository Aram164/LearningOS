# Session report — s02-novice-2026-09-25

- Plan / role: N — blind consumer, novice
- Blind: yes · Product revision: 200a36185fd5c693b4464ce0bdff4be5b89ce584 · World HEAD: 13ad2fcaa0e478afddba6451e29376ca00f0bc8e · Eval revision: 3a53589 (origin/claude/learningos-eval-benchmark-swapck)
- Started / finished: 2026-09-25T00:13:20Z / 2026-09-25T00:50:45Z (container clock; the agent's reasoning time is not fully reflected)

## What I set out to do

I acted as a technically capable first-time operator for the synthetic learner Noor. I ran plan N's nine scenarios in order (S00, S01, S02 Q01–Q12, S04, S06, S10, S14, S15, S26). I used the product's documented interfaces: AGENTS.md → system/OPERATOR.md → `los` read commands and gateway capabilities. At the same time I recorded what happened behind the curtain with `observe.py`. Every scenario that says `world: fresh` got a new build (all builds gave the same world HEAD). S04 and S06 continued in the S02 world.

## Scenario outcomes

| Scenario | Classification | One-line reason |
|---|---|---|
| S00 | PASS_WITH_FRICTION | Correct 5-line orientation in 8 calls, no writes. The default Python 3.11 is refused. `bootstrap --brief` is one minified JSON line that mixes past and future deadlines. |
| S01 | ROBUSTNESS_FAILURE | The repository is healthy (0 errors, baseline OK, no tracked change). But `make setup` failed and left a poisoned .venv; `make test-fast` took 10m51s and failed 34 tests (30 without TRACEPARENT); and the test run wrote phantom needs-attention operations into the learner's diagnostics. |
| S02 | PASS_WITH_FRICTION | Q01–Q12 answered with ids and quotes. Search is unranked literal substring matching. `related` misses the connections the questions depend on. No command reads stage working notes. |
| S04 | PASS_WITH_FRICTION | A09 filed verbatim into the OS L07 stage note through `stage.note.write`, with a receipt, after approval. The approval intent hash needed an implementation read. Afterwards `los operations` reported the committed write as AMBIGUOUS. |
| S06 | PASS_WITH_FRICTION | All three captures were recognised as duplicates. Two were not filed; one became a Garden seed with a receipt. Garden and inbox are not searchable, and there is no way to append to a seed or retire a processed inbox item. |
| S10 | PASS_WITH_FRICTION | "Where was I" answered precisely. The progress was recorded to the stage note on the first try, and the stage was not completed. `resume` and the workspace next action still don't reflect it. |
| S14 | PASS_WITH_FRICTION | I asked a clarifying question before acting, since "kernel" has four meanings here. The notes were already tidy. The only change was one metadata line, shown as a diff and applied byte-exact via `note.revise`. |
| S15 | PASS_WITH_FRICTION | Revised in place after the learner approved a full diff. The correction uses her own August reasoning, and the June paragraph is kept verbatim. The docs disagree on revise vs supersede. The approval is self-asserted by the operator. |
| S26 | PASS_WITH_FRICTION | Three goals in 5 calls, but only thanks to discovery already paid in S00/S04/S06. The capture needed a retry for an undocumented request-scoped revision key. |

## Failures (see failures.jsonl)

- **F-s01-test-trace-leak-01 (ROBUSTNESS_FAILURE).** README lists `make test-fast` as ordinary "quick feedback: synthetic fixtures, no checked-in repository load", so I expected it to leave the installation alone.
  - What happened: it wrote 135 trace lines into the learner's `operations/diagnostics/traces.jsonl`. `los operations` then showed a phantom `req-bad-payload` operation (AMBIGUOUS, needs_attention).
  - A re-run with TRACEPARENT unset added another 135 lines and at least 20 phantom AMBIGUOUS/needs_attention operations, one per capability. So the leak does not depend on the environment.
  - Repro: fresh world → `make setup PYTHON=python3.12` → `make test-fast` → `los operations`.
  - Could be my mistake if running tests inside a live installation is not intended use. Nothing in the docs says so.
- **F-s01-test-fast-red-02 (FUNCTIONAL_FAILURE).** Same README expectation.
  - Result: 34 failed / 2214 passed; with TRACEPARENT unset, 30 failed.
  - 17 failures are FileNotFoundError on another learner's `work/active/workspace-m2-exam-prep/...` files. The other 13 are in causal resolver, diagnostic store, recovery conflicts, gateway v2, format fixtures and abilities.
  - Four of the original 34 were caused by this environment's TRACEPARENT.
- **F-s01-setup-stale-venv-03 (USABILITY_FAILURE).** `make setup` uses python3 (3.11 here) and fails. The README's own fix, `make setup PYTHON=python3.12`, then fails the same way because the stale .venv is reused. Only `rm -rf .venv` recovers. Minimised and retried once.
- **F-s04-operations-merge-04 (FUNCTIONAL_FAILURE).** The agent environment exports a W3C `TRACEPARENT`. The product adopts it as the operation id.
  - Effect: `los operations` merges independent requests into one "operation" named after the first request. It reports a committed write (it has a receipt) as `AMBIGUOUS / reconcile-exact-request / needs_attention`.
  - Minimised in a scratch world: two refused envelopes merge under the inherited TRACEPARENT and separate without it.
  - Could be my mistake only in that I did not set TRACEPARENT; but any CI or agent environment that exports it will hit this.

## Friction that cost the most

1. **Building a gateway envelope** (S04, carried into S10/S14/S15/S26). `approval.subject_sha256 = intent_sha256(envelope)` is not defined in WORKFLOWS §25a step 4 or anywhere else the refusal points to.
   - Cost: one refused write, then 4 tool calls including reading `tools/learning_os/contracts/gateway.py`.
   - Request-scoped revision keys (`garden-request:<key>`, `capture-request:<key>`) are also undocumented, costing one retry each in S06 and S26.
   - Refused writes exit 0 (UNCONFIRMED) or 2 (INVALID_REQUEST).
2. **Setup and the test suite** (S00/S01). 2 failed setups, one manual `.venv` deletion, and 10m51s for a "quick" suite that ends red. The tests also polluted the learner's operations log.
3. **Retrieval** (S02). Multi-word queries return `[]`. Results carry no ranking, snippet or deprecated state. `related` never surfaced the notes that answer or correct each other.
   - Cost: about 10 extra search/read commands across 12 questions, plus direct `cat` of a stage working note, because no read command returns it and `resume` says "Evidence none" while that note holds the exact stopping point.

## What the product made easy

- Answering exam and grade questions from the owning module record (`inspect module-…`): exact dates, times, registration state, grade.
- `resume` and `plan-edit-context --stage-id`: the current stage with its objective, done-when and working-note path, in two calls.
- Gateway writes, once the envelope is right: atomic, snapshot-guarded, with a receipt holding sha256 before and after. Refusals are clean (no partial writes). INVALID_REQUEST messages name the exact missing revision key.
- `note-read` returns complete bodies with a content hash. Deprecated and correcting notes (p-values, virtual memory, batch norm) make "what did I believe before" answerable.
- Validator and warning baseline are fast (under 1 s) and stayed at 0 errors / no new signature after every write.

## Behind the curtain

- Receipts: S04 `transaction-20260925-003709-001` (stage.note.write), S06 `…004102-001` (garden.seed.create), S10 `…004247-001` (stage.note.write), S14 `…004555-001` (note.revise), S15 `…004739-001` (note.revise), S26 `…004911-001` (capture.create). Each world starts without an `operations/transactions/` ledger, so the first write creates untracked `idempotency.yaml` and `revisions.yaml`.
- Read-only commands populate a derived cache (`generated/derived-state/`: 118 files / 490 KB after S02). The brief/resume/inspect reads in S00 wrote nothing.
- Every process in this environment inherits TRACEPARENT `00-bff87904f6d407966d784832196f7e19-…`. All operations in all worlds therefore share trace id `bff87904…`, which drives the misleading `los operations` output (F-s04).
- Receipts keep hashes, not prior bytes. Recovering a revised note relies on Git; all scenario writes were left uncommitted, as none of plan N's scenarios asked for a commit.
- `make setup` installs pre-commit, post-commit and pre-push hooks into the world's `.git/hooks`.

## Uncertainties

- Whether the stage working note, the workspace `scratch/` or the inbox is the intended home for A09. WORKFLOWS §21 points to `scratch/`, but no capability writes there.
- Whether a second Garden seed was the "tidy" choice for A18.
- Whether revise-in-place or a successor note with `supersedes` was expected for S15. No gateway capability creates an ordinary successor note.
- Wall-clock minutes come from the container clock and understate the agent's reasoning time.
- Some S01 test failures may be timing-sensitive on this 4-core container.

## Deviations from the protocol

- Fresh worlds were built into sibling directories (`~/los-eval/s02-novice-2026-09-25-S02`, `-S10`, `-S14`, `-S15`, `-S26`) instead of resetting in place.
- The scripted learner's questions and answers were resolved inline in my own reasoning, immediately before each write.
- An interim record (commit b414c32) was pushed mid-run at the user's request.
- Approval hashes were computed by the operator for learner-approved writes; the user explicitly authorised this mid-run.
- Harness-only investigation outside any scenario: a scratch world for the trace-id repro, and a test re-run without TRACEPARENT.

## NOT TESTED

- Anything in the Obsidian UI (review.prepare / review.apply shelving declare `admission_channels: [ui]`). The S04/S06 shelving flows were done through CLI capabilities instead.
- `los session-end` and committing (not part of plan N).
