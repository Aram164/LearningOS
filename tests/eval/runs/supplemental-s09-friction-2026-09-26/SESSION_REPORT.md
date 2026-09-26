# Session report — supplemental-s09-friction-2026-09-26

- Plan / role: F — friction-investigator (agent-friction investigator)
- Blind: yes · Product revision: 200a36185fd5c693b4464ce0bdff4be5b89ce584 · World HEAD: 13ad2fcaa0e478afddba6451e29376ca00f0bc8e · Eval revision: d5a6e3c365f9901a9db2a5acb24256322e056d2a
- Started / finished: 2026-09-26T02:14:17Z / 2026-09-26T05:35:53Z. The session paused on an agent usage limit after all nine scenario runs had finished; the pause is inside this span but outside every scenario's timing.

> **Post-hoc supplemental evidence.** This run was collected on 2026-09-26, after the campaign's other sessions
> had finished. It is not part of the original blinded sequence and does not change the campaign's run ledger,
> where session 9 stays recorded as omitted. The eval base was pinned to d5a6e3c: the session worktree was
> created from that commit, and no other branch or later commit of the LearningOS repository was looked at.

## What I set out to do

Plan F repeats three ordinary goals and counts what they cost: S02 (Q06, Q07, Q13, Q15, Q27), S10 (resume, then
record progress) and S26 (what's due, an inbox note, notes on caching). As clarified in the kickoff message, the
plan ran as three passes of S02 → S10 → S26, and every scenario run got a newly built world, nine builds in all. Each
`EVAL-WORLD.json` showed the pinned product revision and world HEAD.

Pass 1 is the cold measurement (first contact). Passes 2 and 3 are warm: same session, product documents not
re-read, and every answer re-derived from that pass's fresh world rather than recalled. Tool calls are my Bash
invocations as the learner's operator; harness calls are counted separately in each result.

## Scenario outcomes

| Run | Classification | Calls | Seconds | Retries | Impl. reads | One-line reason |
|---|---|---|---|---|---|---|
| S02-r1 | PASS_WITH_FRICTION | 21 | 271 | 1 | 1 (Makefile) | All five answered with evidence; 10 calls of orientation/setup first, inbox and working note read as files |
| S02-r2 | PASS_WITH_FRICTION | 4 | 35 | 0 | 0 | Same answers, same evidence; `make setup` and file reads recur per world |
| S02-r3 | PASS_WITH_FRICTION | 4 | 30 | 0 | 0 | As r2; outputs byte-identical across passes |
| S10-r1 | AMBIGUOUS | 16 | 310 | 0 | 1 (gateway.py) | "Where was I" in 2 calls; the progress write was refused by my agent environment, not by LearningOS |
| S10-r2 | AMBIGUOUS | 2 | 13 | 0 | 0 | "Where was I" identical; write not attempted (refusal covers the outcome) |
| S10-r3 | AMBIGUOUS | 2 | 14 | 0 | 0 | As r2 |
| S26-r1 | AMBIGUOUS | 11 | 107 | 0 | 0 | Goals 1 and 3 done with friction (6 + 3 calls); goal 2 stopped at the approval value |
| S26-r2 | AMBIGUOUS | 3 | 29 | 1 (own) | 0 | Goals 1 and 3 identical (2 + 1 calls; one own shell error); goal 2 not attempted |
| S26-r3 | AMBIGUOUS | 2 | 22 | 0 | 0 | Goals 1 and 3 in 1 + 1 calls; goal 2 not attempted |

Per pass: 48 calls / 688 s (cold), then 9 calls / 77 s, then 8 calls / 66 s. The warm costs are those of a
read path that is short once known. The cold costs are almost all discovery.

The S02 answers are in `answers.jsonl` (pass 1) and in each `results/S02-rN.json` → `scenario_record.answers`.
They are identical across passes.

## Failures (see failures.jsonl)

**F-supplemental-s09-friction-001 (AMBIGUOUS, S02).**
- **Expected:** `project-tessera` lists `milestone_ids` [milestone-tessera-parser, milestone-tessera-optimizer].
  OPERATOR.md says "a named record → `inspect ID`", so I expected these ids to resolve, or at least a refusal
  saying why they don't.
- **Actual:** `los inspect milestone-tessera-optimizer` prints `los: record not found` on stderr, exit 2. The same
  happens for the project's own structure node ids (`step-tessera-*`).
- **Reproduction:** minimized and reproduced in a second fresh world (`evidence/F-milestone-inspect-repro.txt`).
- **Could be my mistake:** milestones may deliberately not be records. Then the only defect is a reference that looks
  resolvable, plus an error that doesn't say why.

No other LearningOS failure was observed. The blocked writes are not LearningOS failures. The refusal came from my
agent environment (see Deviations), so the gateway's behaviour on them is unobserved.

## Friction that cost the most

1. **Learning the write path for an in-stage write (S10-r1): 13 calls and about 4 minutes, and the envelope was
   still unsubmitted.**
   - Recording "I finished part of a stage" has no structured home. `stage.progress.update` carries only a status,
     `stage.note.write` is marked "compatibility capability only", and `learner.observation.append` needs a
     requirement that the stage lacks.
   - OPERATOR.md sends stage writes to "WORKFLOWS §25a, step 4" for the envelope fields and intent hash, but that
     step says it "does not apply" to stage-progress and stage-note.
   - `approval.subject_sha256 = intent_sha256(envelope)` is named but defined in no document or schema. The
     definition exists only in `tools/learning_os/contracts/gateway.py` (2 implementation reads).
   - Which `approval.kind` applies is only in WORKFLOWS prose; the capability output omits `admission` for
     stage.note.write.
   - Which artifacts `expected_revisions` must list for a stage write is undocumented.
   - For `capture.create`, the request-scoped guard `capture-request:<idempotency_key>` is documented nowhere (grep of
     system/, README, AGENTS: no match).
2. **First contact and setup (S02-r1): 10 calls before the first question-specific read.**
   - About 656 lines of entry contract: AGENTS.md → OPERATOR.md (336 lines), plus the Claude adapter CLAUDE.md
     (307 lines), which overlaps it.
   - The documented `python tools/los.py …` fails because there is no `python` on PATH. The tools need a per-clone
     `.venv` from `make setup`, which only README's command section mentions. That recurs once in every fresh world.
   - Verifying what `make setup` writes (README: a hook goes "into the sibling UI checkout when it is present") took
     a Makefile read.
3. **State the reads do not serve.**
   - No command lists inbox items, workspace bodies, or the stage working note that holds "Stopped at step 4" and
     the NEXT line, which `resume` omits. Q27 alone took 7 question-specific calls in pass 1.
   - The Garden is not searchable, and its generated lens does not exist in a fresh world.
   - Goal 1 of S26 needed 5 extra calls in pass 1 to find workspace deadlines. `bootstrap --compact` pages no
     workspaces, there is no workspace-list command, and an undocumented empty-query search
     (`search '' --type workspace`) was the only listing.
   - Search is literal: "caching" misses "cache", and concept aliases (`buffer pool`, `memoization`) don't expand
     queries.
   - In the warm passes, 2 of S02's 4 calls are still file reads.

## What the product made easy

- **`bootstrap --brief`** is a good one-page entry: the resume pointer (with "confirmed = where study stopped, not a
  recommendation"), every academic deadline with time and registration state, the inbox count, and recorded
  workspace options with their sources. It answered most of Q07, Q15 and S26 goal 1 by itself.
- **Batched `inspect`** reads up to 20 ids under one snapshot, including `coordination` with dated decisions and the
  module's examination record. One call covered Q07 and Q15.
- **`plan-edit-context --stage-id`** returns objective, done-when, working-note path, snapshot and revision guards in
  one read.
- **Determinism and stability.** Nine identical worlds, the same snapshot id everywhere, and `bootstrap --brief`,
  `inspect`, stage reads and `resume` outputs byte-identical across passes.
- **Safe defaults.**
  - Reads never touched canonical state.
  - The bare write command refused with exit 2 and named the route back.
  - `make setup` took about 5 s and writes only ignored files and the world's own `.git/hooks`
    (`../obsidian-ui` only if present).

## Behind the curtain

- **No writes anywhere.** Zero receipts and zero `los operations` entries; no canonical change in any of the nine
  runs; HEAD never moved (all `observations/*-diff.json` carry no flags).
- **Reads compute the projection in memory.** `generated/` stays at `.gitkeep`, and no manifest is written by any read.
- **One read writes a derived cache.** On first use, `search QUERY --type note --content` writes 118 files (490,130
  bytes) under `generated/derived-state/` (per-note `search.note:*` blobs plus `state-v1.json`). The cache is
  gitignored, and the file itself says to delete the directory to reset it. `bootstrap --compact`, `related` and
  `note-read` write nothing (`evidence/derived-state-probe.txt`). This is the only derived change the observer saw
  (S26-r1).
- **`make setup` side effects:** ignored `.venv/`, `tools/learningos_core.egg-info/` and `__pycache__/`, plus
  pre-commit, post-commit and pre-push hooks in the world's `.git/hooks`.
- **Write-path facts, from documents and one implementation read, not observed:** the intent subject covers
  schema_version, capability, channel, expected_snapshot, expected_revisions and payload. It excludes request_id and
  idempotency_key, so a retry keeps its approval valid.

## Uncertainties

- Whether the gateway would have accepted the S10 envelope (channel `operator`, `operator-approval`, guards
  module/study-map/unit = 0). The same goes for the S26 capture (`direct-user-gesture`, request-scoped guard).
- Whether milestones are meant to be inspectable (the failure above).
- Per-question tool counts in S02 are an attribution; the first two calls of each pass served several questions.
- Measured seconds are dominated by agent inference; product commands themselves returned in about a second.
- Whether the memory index in context primed my search for an envelope schema (see Deviations).

## Deviations from the protocol

All are also in `run.json` → `deviations`.

- **Post-hoc supplemental run** (see the box above).
- **Harness clarifications from the kickoff:** three passes, a fresh world per scenario run, `results/Sxx-rN.json`
  naming, and pass-1 answers only in `answers.jsonl`.
- **Harness venv** in the session scratchpad with python3.12, not `/tmp/evalenv`.
- **Agent-environment refusal.** In S10-r1 the Claude Code auto-mode classifier refused the step that computed
  `approval.subject_sha256` for the learner-approved stage-note write and submitted the envelope ("Permission for
  this action was denied by the Claude Code auto mode classifier. Reason: [Security Weaken]."). This happened although
  the kickoff authorized computing approval values for writes the scripted learner approved. Per CONSUMER-PROTOCOL §2
  it was recorded as friction and not worked around. The denial covers the outcome, so it was not re-attempted for
  S10-r2/r3 or for any S26 inbox capture. No write scenario was completed.
- **Memory index in context.**
  - Claude Code auto-loaded the user's memory index. No memory file was opened.
  - Its entries named a gateway write path with a channel enum, worktree hook behaviour, and a repository-topology
    sibling-name rule.
  - Effect: I knew in advance that envelopes and a channel enum exist, which may have primed my search for the
    envelope schema. It did not change which scenario commands I ran.
  - One index entry predicted the commit problem below ("pre-commit needs a worktree .venv").
- **Commit made with `--no-verify`, on the owner's instruction.**
  - The eval repository's pre-commit hook blocked the first commit attempt:
    `/opt/homebrew/opt/python@3.14/bin/python3.14: No module named ruff` / `COMMIT BLOCKED: static checks failed`.
    With no `.venv` in the session worktree, the hook falls back to the system `python3`, which has no `ruff`.
  - Following the hook's own interpreter preference and README, I created an ignored project venv in the session
    worktree (`python3 -m venv .venv && .venv/bin/python -m pip install -e '.[dev]'`). No tracked file changed.
  - The owner then instructed "bypass the check with --no-verify", so this directory was committed with
    `git commit --no-verify`. The pre-commit checks (`ruff check tools tests`, `tools/validate.py --compact`) did not
    run on this commit.
- **Root AGENTS.md** (auto-loaded) also names OPERATOR.md as the operator contract; the world's AGENTS.md does too, so
  the reading order was unaffected.
- **Agent state:** pass 1 is the only cold measurement, and S10-r1 and S26-r1 were already warm for reads.
- **Timing and today's date.** Timing runs from inside a scenario's first call to the end of its last. "Today" is the
  system date 2026-09-26; the world's timeline ends on 2026-09-18.
- **Two read-only observer probes** ran after S26-r3 closed.
- **Own errors,** not product friction: a zsh `=====` expansion in harness reads, and one unquoted variable in
  S26-r2, counted as a retry.

## NOT TESTED

- The Obsidian interface (plan F does not need it).
- Every gateway write in plan F: `stage.note.write` in S10 and `capture.create` in S26 goal 2. That covers
  transaction, receipt, approval admission, idempotency and post-write validation; all were blocked by the
  agent-environment refusal before submission.
