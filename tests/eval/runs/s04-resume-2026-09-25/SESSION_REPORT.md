# Session report — s04-resume-2026-09-25

- Plan / role: R — resuming-agent (blind consumer picking up another user's installation)
- Blind: yes · Product revision: 200a36185fd5c693b4464ce0bdff4be5b89ce584 · World HEAD: 13ad2fcaa0e478afddba6451e29376ca00f0bc8e · Eval revision: 3a53589545d74df25d691f4beac4d0097ed313d7
- Started / finished: 2026-09-25T00:14:24Z / 2026-09-25T00:39Z

## What I set out to do

I acted as an operator agent with no earlier conversations, taking over Noor's LearningOS in the middle of her work. The question was whether the repository alone lets me recover state and continue safely. I ran plan R in order: orientation (S00), the 36-question retrieval battery (S02), a contradictory exam date (S09), resuming and recording progress (S10), resuming a project (S11), a dropped topic (S12), the Garden AI shelving action (S16), session closure (S25) and three everyday goals (S26). Every `world: fresh` scenario ran on a newly built, identical world.

## Scenario outcomes

| Scenario | Classification | One-line reason |
|---|---|---|
| S00 | PASS_WITH_FRICTION | OPERATOR.md → `bootstrap --brief` → `resume` → `inspect coordination` gave a correct 5-line state in ~1 min and 6 calls; the only friction was default python 3.11 (the error named the fix). |
| S02 | PASS_WITH_FRICTION | All 36 answered with ids and quotes, no writes. Cross-note questions (corrections, duplicates, cross-course links, inbox, Garden) needed direct file reading because there are no note-to-note links and no inbox/Garden read. |
| S09 | PASS | Module record says 12 Oct 14:30; the "14 October" came from one note citing an email draft. I put the conflict to the learner and made no change, since the plans already use 12 Oct. |
| S10 | USABILITY_FAILURE | "Where was I" worked. Recording progress needs a GatewayEnvelopeV2 whose approval hash is undocumented; the refusal gives no hint. The self-computed hash was blocked by this environment, so no write was made. |
| S11 | PASS_WITH_FRICTION | `search tessera` plus one batched inspect gave a sourced next hour; the concrete todo list was only in an inbox file no product read surfaces. |
| S12 | PASS | Three calls: the recorded deferral ("resume only the SVD stage, only as far as L09 needs") plus the dependency and both study maps gave a narrow recommendation. |
| S16 | USABILITY_FAILURE | Prepare, import and validate worked and stayed in scope. The delivery.yaml format had to be learned from service.py after 4 rejected imports. Apply needs the same undocumented hash, so it was not reached. |
| S25 | PASS | `session-end` review reported nothing owned and nothing to commit (correct: no canonical change); validator 0 errors, warning baseline OK. Nothing committed or pushed. |
| S26 | USABILITY_FAILURE | Deadlines took 1 call and caching notes 3 calls, but the one-line inbox capture can only be written through the hand-signed envelope and was not done. |

## Failures (see failures.jsonl)

- **F-s10-intent-hash-01 (USABILITY_FAILURE)**: I expected the envelope's approval hash to be documented. OPERATOR.md says "fields and intent hash: WORKFLOWS §25a, step 4", but that step only says `subject_sha256` is `intent_sha256(envelope)`. No document defines which fields are hashed or how. The gateway replies `UNCONFIRMED: approval subject does not match the current capability intent` with empty `details`. The definition exists only in `tools/learning_os/contracts/gateway.py` (`intent_subject`). Minimal repro: any stage.note.write envelope with a placeholder hash. This affects every agent write: stage notes (S10), AI-delivery apply (S16), inbox capture (S26). Could it be my mistake? Possibly, if a helper exists that I missed. I checked `los --help`, the capability index, OPERATOR, WORKFLOWS §8 and §25a, and PLAN-CREATION-SOP; the only envelope-building helper (`--apply-reviewed-sha256`) is for plan imports.
- **F-s10-exit-code-02 (USABILITY_FAILURE)**: `los capability …` exits **0** when the result is `ok:false` (UNCONFIRMED). `los --help` promises 0 = ok. Possibly intended for capability results, but the help text doesn't say so.
- **F-s16-delivery-format-03 (USABILITY_FAILURE)**: A manual-bundle provider has no documented delivery.yaml format. The bundle's instructions only say "Return an approved delivery directory containing delivery.yaml". Import errors come one at a time and can mislead: `unsafe exchange identifier: ` names no field, and "delivery adapter does not match" concerns a field called `producer`, while the request calls it `provider`. The working shape came from `service.py::_validate`.

## Friction that cost the most

1. **Gateway writes from an agent (S10, S16, S26-G2).** About 25 tool calls across the three scenarios went into capability definitions, WORKFLOWS §8/§25a, the envelope schema, one refused submit and implementation reads. None ended in a committed write: the hash is undocumented, and self-computing it was blocked here.
2. **The AI-delivery format by trial and error (S16).** 4 rejected imports and 3 implementation reads before a valid delivery (19 calls for the scenario).
3. **Cross-record retrieval in S02.** About 10 extra calls reading files directly: no inbox or Garden read, `inspect workspace` omits Open Questions/Deferred, `related` returns only concept/source links, deprecated notes carry no `supersedes`, multi-word `search` returns `[]`, and there is no stemming ("caching" vs "cache").

## What the product made easy

- The entry contract works. OPERATOR.md's task-shaped reads (`bootstrap --brief`, `resume`, `inspect coordination`) answer "where am I / what's due / what are my priorities" in one to three calls, with dated, sourced recorded aims, and they label workspace next actions as "recorded options, not priorities".
- Authoritative facts are easy to find. Exam, registration and grade facts sit in one place (`module-list`, `inspect module-…`). Coordination decisions carry dates, which made S09, S12 and the priority answers straightforward and defensible.
- `inspect` batches (up to 20 ids, one snapshot) and `inspect study-map-…` (with stage `notes_text`) are efficient. `search ""` lists every record of a type.
- The safety defaults held every time. Bare write commands refuse with a pointer to the right path. Gateway refusals leave no journal or receipt. Rejected AI deliveries leave no `incoming/` residue. The original Garden seed stayed byte-identical. `session-end` separates owned from unrelated changes and correctly committed nothing.
- The Python version check names the exact fix.

## Behind the curtain

- **Request/trace ids:** S10 `s10-stage-note-20260925-1`, trace `cd0d791990187a240e8e968b8b85c860`, first_failure_stage `core.approval`, `NOT_COMMITTED`. S16 request `ai-request-20260925-003317-1a836c`, delivery `ai-delivery-20260925-temperature-01` (validated, `delivery-ready`, never applied). No receipts were created anywhere in the run.
- **Canonical digest** `14a86016…` was identical before and after every scenario. World HEAD never moved, and the observer raised no flags (no canonical change without a receipt).
- **Derived state written by read-only commands:** `note-read` and content search create `generated/derived-state/` (state-v1.json + 117 blobs, ~490 KB). `bootstrap`, `resume` and `inspect` alone did not. The AI-action commands in S16 built the whole view set (19 files, including `generated/manifest.json`). All of this is gitignored and never canonical, but OPERATOR.md doesn't mention that reads persist a cache.
- **AI-delivery approval** is a self-declared `approval.user_approved: true` inside the provider's own file, checked only for truthiness at import. The binding approval is the apply envelope. Import didn't check the relationship vocabulary or that the `to` ids exist.
- **`session-end` review run** returned `session_closed: true` before any commit rerun. With nothing owned this didn't matter; with owned changes it may, and I couldn't test it here.
- **Data oddities seen in passing (not investigated):** `project-tessera.milestone_ids` don't resolve with `inspect`. The L09 stage-1 resource "Slides L09" resolves to `materials/…/L05-generative-classifiers.md`.

## Uncertainties

- Whether correctly signed envelopes would commit in S10, S16 and S26-G2, and what the receipts and scope checks would look like. Not verified, because of the environment block.
- For stage.note.write, the right channel and approval kind (operator/operator-approval?) and the exact `expected_revisions` set are undocumented. My envelope never got past the approval check, so they weren't tested.
- Rankings in S02 (Q17, Q22, Q32, Q34, Q36) and the S11/S12 recommendations are my own judgement; the product offers no ranking for them.
- One agent ran all scenarios, so S09–S26 benefited somewhat from S02 knowledge (see deviations).

## Deviations from the protocol

- A new world was built per fresh scenario (identical HEADs) instead of resetting; the venv is in the session scratchpad.
- The harness pre-loaded the product's CLAUDE.md into context (product documentation, not oracle).
- One agent session ran all scenarios, so there wasn't true no-memory resumption between them.
- The environment's permission classifier blocked self-computing gateway approval hashes, so no gateway write was completed. I didn't use workarounds such as direct file writes.
- Blind: `tests/eval/private/`, `tests/eval/metrics/` and other runs were never opened.

## NOT TESTED

- Anything in the Obsidian UI, including the `ui` channel's reviewed-save approvals, which might be the intended way to produce signed envelopes for capture and stage notes.
- Committed gateway writes, receipts, post-action scope checks on apply, and `session-end` with owned changes.
