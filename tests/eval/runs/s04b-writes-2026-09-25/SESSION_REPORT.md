# Session report — s04b-writes-2026-09-25

- Plan / role: O — resuming-agent (an agent resuming another user's work, no memory of earlier conversations)
- Blind: yes · Product revision: 200a36185fd5c693b4464ce0bdff4be5b89ce584 · World HEAD: 13ad2fcaa0e478afddba6451e29376ca00f0bc8e · Eval revision: 658db28d0c389f7ac2e5cbf878d099d4d359ec67
- Started / finished: 2026-09-25T02:15:53Z / 2026-09-25T02:38:13Z

## What I set out to do

Run three write-bearing scenarios, each on a fresh world, as the learner's
operator: S10 (resume after a break, then record progress), S16 (AI shelving
action on a Garden seed with me as the manual-bundle provider) and S26 (three
ordinary goals, measured for friction). Every write went through the gateway
after the scripted learner approved the exact change. I recorded that approval
in the form the product asks of its operator: `intent_sha256` from the
product's own helper, and `approval.user_approved` in the S16 delivery.

## Scenario outcomes

| Scenario | Classification | One-line reason |
|---|---|---|
| S10 | PASS_WITH_FRICTION | `resume` answered "where was I?" and the approved stage-note write committed. The envelope needed an implementation read and one retry, and `resume` still shows the stale next action afterwards (F-s04b-writes-01). |
| S16 | PASS_WITH_FRICTION | On a second fresh world the whole manual-bundle flow committed inside its scopes. The seed isn't searchable, the delivery format is undocumented (3 blind imports, then a code read), and the first world was poisoned (F-s04b-writes-02). |
| S26 | PASS_WITH_FRICTION | All three goals done with no retries. Deadlines need manual window filtering, milestones don't resolve, the capture guard exists only in code, and title search misses most caching notes. |

## Failures (see failures.jsonl)

**F-s04b-writes-01 (S10, USABILITY_FAILURE): recorded progress doesn't reach `resume`.**
- *What I expected, and why:* CLAUDE.md §2 calls `los resume` the one-screen return to interrupted study. OPERATOR.md sends stage-specific learning to the stage note. So after recording progress on the resumed stage, the next `resume` should reflect it.
- *What happened:* `resume` output is identical before and after the committed write. The workspace Next-Action still says "work one stride-scheduling example by hand" — the example the learner just finished.
  - No capability advances a workspace next action.
  - The evidence ledger (`observe`) is closed because the stage has no authored requirement.
- *Reproduction:* `resume`, then `stage.note.write`, then `resume`, then diff the two outputs.
- *How it could be my mistake:* a status write or an observation might have changed `resume`. But `resume` itself reports no requirement for this stage, and the only status that fits the learner's answer, `active`, was already set.

**F-s04b-writes-02 (S16, ROBUSTNESS_FAILURE): a bad `--request-id` poisons the projection.**
- *What I expected, and why:* `ai-action-prepare --help` offers `--request-id` with no stated format. I expected a malformed id to be refused before anything was persisted.
- *What happened:* the command exited 2, but it had already written a 7-file request bundle with status `prepared`. From then on, `bootstrap --brief` and `search` exited 2 with a manifest-contract mismatch.
  - The error advises bumping the manifest contract and mirroring it into the UI, which is maintainer work.
  - `tools/validate.py` reports 0 errors.
  - There's no documented way to cancel the request.
  - `los operations` has no trace of it.
- *Reproduction:* four commands on a fresh world, listed in the record.
- *How it could be my mistake:* partly. The docs' example omits `--request-id`, and I chose a custom id for traceability. The harm is still out of proportion to a bad optional argument. I left the world untouched rather than hand-delete the bundle.

## Friction that cost the most

1. **The S16 delivery format:** 3 refused imports and 2 implementation-read calls. No schema exists for `delivery.yaml` in the bundle, in `system/schema`, or in AI-ACTIONS.md, which shows only an `operations:` fragment.
   - Import errors don't name the field. `unsafe exchange identifier: ` prints an empty value, and "delivery adapter does not match" doesn't say the field is `producer.adapter`, not `provider.adapter`.
   - An external provider given only the bundle couldn't produce a valid delivery.
2. **Recovering from the S16 poisoning:** a second world build plus about 8 damage-assessment calls.
3. **Envelope construction:** S10 took about 10 calls, 1 implementation file and 1 refused request.
   - `intent_sha256` is named in WORKFLOWS §25a, but its location and canonicalization appear only in `tools/learning_os/contracts/gateway.py`.
   - Which artifacts to guard is stated nowhere: the unit, not the study map, for a stage note; the not-yet-existing transcription for an AI delivery; `capture-request:<key>` for a capture.
   - OPERATOR.md and the CLI refusal both send the reader to §25a step 4, which says it doesn't apply to in-stage work.

## What the product made easy

- `los resume` answers "where was I?" on one screen: stage, sourced and dated recorded aims, and the exam countdown.
- `bootstrap --brief` answers "what's due" in one call.
- The capability index plus `capabilities NAME --json` give an exact payload schema for every write.
- Refusals from the gateway's revision check are precise (`missing=[…]`, `unexpected=[…]`) and write nothing. Both S10's and S16's revision refusals were fixed in one retry.
- Receipts are complete and legible: snapshot before and after, revision moves, per-file hashes, declared-write grants, approval subject.
- `los operations` explains a refused request down to its failing stage.
- AI-ACTIONS.md describes the prepare, import, validate and apply lifecycle and its guards clearly. The bundle is tightly bounded: exact target, checksum, snapshot precondition, capability allowlist.

## Behind the curtain

- Every canonical change in the three completed worlds is covered by a receipt. The observer raised no flags and found no inflight journals.
- **Approval:** `operator-approval` (S10, S26) and `approved-delivery` (S16) were accepted with `subject_sha256` equal to the receipt's `intent_sha256`.
  - The value is computable by whoever builds the envelope. The product verifies consistency, not that a human was present, which WORKFLOWS §8 acknowledges for the `ui` channel.
  - Both `stage.progress.update` and `capture.create` are declared `admission: direct-user-gesture`. §8 says agent-origin gestures fail closed, so `operator-approval` is the only agent route, and no doc says so directly.
- **S16 apply:** it wrote `operations/ai-actions/garden-state/…` under a `garden.update` grant the delivery never requested. That's within the action's documented effects. It also prepended a provenance frontmatter block to the transcription, so the canonical file isn't byte-identical to the SHA-256-approved artifact, though the approved body is unchanged (`evidence/S16-approved-vs-written.diff`).
- **`garden-state/`:** AI-ACTIONS.md calls `operations/ai-actions/` bookkeeping "kept out of the canonical tree", yet `garden-state/` isn't gitignored and the observer counts it as canonical. Only `requests/` and `deliveries/` are ignored.
- **Projection:** fresh worlds ship `generated/` empty, which is the source of the build's third warning, `HYGIENE-VIEWS`.
  - Read commands (`bootstrap`, `search`, `note-read`) don't write it.
  - S16's apply and S26's capture each rebuilt the whole projection (138 files, about 984 KB). S10's `stage.note.write` left only 20 files (494 KB).
- **Ledgers:** the first transaction in a world creates `operations/transactions/idempotency.yaml` and `revisions.yaml`, which the receipt's `writes` list doesn't name.
- **Search coverage:** Garden seeds and transcriptions are invisible to `inspect` and `search`, and project milestone ids don't resolve through `inspect`.

## Uncertainties

- **S10:** whether a reviewer expected a status write alongside the note. I judged `active`→`active` a no-op.
- **S16:** whether a `relationship.create` to `note-softmax-temperature` and `note-simulated-annealing` was expected. Its operation shape is undocumented, so I named the notes in prose instead.
- **S26:** the reference date for "next three weeks". The product clock says 2026-09-25, and the world timeline ends 2026-09-18.
- **Prior knowledge:** how much my earlier-session memory of this product shortened the envelope steps. It was loaded before the run; see the deviations in `run.json`.
- **Projection trigger:** which command materialized S10's partial projection.

## Deviations from the protocol

All six are listed in `run.json`. In short:
- **Worlds:** each scenario got its own fresh world in a per-scenario subdirectory. S16 was repeated once on a second fresh world after the first was poisoned, and the poisoned world is preserved.
- **Prior memory:** the agent's persistent memory from earlier, non-evaluation sessions on the real LearningOS repository was loaded, and two memory files about the gateway envelope were read before the run. No oracle material was involved.
- **Shared session:** the three scenarios shared one session, so S26's counts aren't cold-start numbers.
- **`~/los-eval` listing:** it showed entry names `oracle`, `repository` and `runs`. None was opened.

## NOT TESTED

- Whether the Obsidian UI surfaces Garden seeds, AI transcriptions, or the S10 stage-note progress.
- The UI-channel (`ui`) approval path for any of the writes.
