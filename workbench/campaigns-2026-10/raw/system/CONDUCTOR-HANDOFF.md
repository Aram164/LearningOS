# Conductor handoff: GLM campaigns, Saturday 2026-10-24, 16:45

This is for a fresh Claude session taking over the orchestrator ("conductor")
role. The first conductor stood down at about 16:45. Its background watchers
are stopped, so it will not act alongside you.

All paths are relative to this folder:
`/Users/aramaljanadi/Desktop/semestercontext/LearningOS/workbench/glm-campaigns-2026-10-24/`.

## Read first, in this order

1. `ORCHESTRATOR.md`: your brief, covering the boundaries, the loop,
   launching and verification. It governs. This file only says where things
   stand.
2. `ORCHESTRATOR-STATE.md`:
   - **the lanes table**, the live truth for every item;
   - **the log**, which records each of Aram's decisions with its time;
   - **"ZCode driving notes"** at the end. Read them before your first
     click.
3. `PROMPTS.md`: every prompt. The **"Compressed plan"** section at the end
   supersedes L1-2, L1-3 and L1-4.
4. `CAMPAIGNS.md`: the ground rules the GLM sessions follow.
5. `MORNING.md`: the summary written for Aram. Keep it current.
6. `ISSUES-DRAFT.md`: issue drafts. **File nothing.**

Then read the `anthropic-skills:computer-use` skill before your first click.

## Where things stand

| Item | State | What you do |
|---|---|---|
| **L1-234**, all verification (GLM-5.3) | **running** since 16:11 | Wait for its signal. It writes `C1-VERIFY.md` (the report path in its signal) and `C2/RECHECK.md`. |
| **LG-1**, the learning-gaps A8 fix | **Aram sends it himself.** It was not yet visible in ZCode at 16:37. | Wait for its signal, then verify. |
| C3 (L1-1) | done; verdict in `C3/CLAUDE-VERDICT.md` | Optional: append the outcome of the redundant main-ref gate 40096320763 to that verdict. |
| Every C1 hunting batch, every C2 module | done and verified; verdicts in each folder's `CLAUDE-VERDICT.md` | Nothing. |
| C4 (L1-5 to L1-7) | not started | **Never launch.** It needs Aram's slides, the live-branch merge and his review. |

Nothing else is queued. Once L1-234 and LG-1 are verified, the campaign
work the orchestrator can do is finished.

## Your loop from here

1. Arm the wait in the background, then end your turn:
   `sh wait-for-signal-or-unlock.sh 180`. That is `wait-for-signal.sh` plus
   an `UNLOCKED` exit when a locked screen unlocks.
2. **On `SIGNAL L1-234`:**
   1. Move the signal to `signals/processed/`.
   2. Compare GLM's C1 marks in `C1-VERIFY.md` with the verdicts in
      `C1-A/` … `C1-E/CLAUDE-VERDICT.md`, and re-check every disagreement
      yourself.
      - Expect one: in `C1-C`'s `note.revise` finding, the witness-2 test
        has a digest-prefix bug. Without a fix it fails at its
        precondition (line 147). GLM may mark it refuted for that reason.
        The claim itself holds; see `C1-C/CLAUDE-VERDICT.md`.
   3. Compare `C2/RECHECK.md` with the C2 verdicts. Note its answer on
      whether M2's section check ever searched the materials (see
      `C2/module-hu-aml/CLAUDE-VERDICT.md`, "Worth carrying forward").
3. **On `SIGNAL LG-1`.** The criteria are in `ORCHESTRATOR-STATE.md`
   (16:14 log entry):
   1. Its new release-pair run is green on the new SHA.
   2. The diff against `326dd638` touches only
      `system/procedures/process-a-lecture.md`.
   3. **Do not land it.**
4. **On `TIMEOUT`,** follow `ORCHESTRATOR.md`.
   - A red dot on a chat in ZCode's sidebar means an error banner.
   - Never approve a permission prompt.
5. When nothing is left, update `MORNING.md` and the state file, and tell
   Aram.

**Your own scratch clone.** Clone Core `main` from GitHub into *your*
scratchpad, with its own venv. The first conductor's clone was in its own
session scratchpad.

## Aram's standing decisions this session

All are logged with times in `ORCHESTRATOR-STATE.md`.

- **"When a new session is needed don't ask me just do it."** Launch
  eligible items without asking or offering an opt-out. The brief's hard
  limits still bind:
  - at most two GLM sessions at once;
  - no C4;
  - nothing launched after Sunday 22:00 Berlin (clocks go back Sunday
    03:00);
  - the credits end Monday 02:00.
- **LG-1 runs after C3, not in parallel.** C3 is done, so this is
  satisfied.
- **The compressed plan** (15:41): L2-13 folded into L2-12's chat, and
  L1-2, L1-3 and L1-4 merged into L1-234.
- **Prompts that grant push authorization in Aram's voice are his to
  send.** The auto-mode classifier blocked the conductor's send of LG-1
  ("Safety Bypass Flag"). Do not retry or work around that. Hand him the
  prompt.

## Hard-won operational facts

The details are in the state file's driving notes.

- **Full-screen control.**
  - Launches need `computer_batch`. Background `app_*` control cannot open
    the model picker, and its screenshots go stale.
  - Full-screen control needs Aram's approval once per session: call
    `request_full_control` while he is awake.
  - **Never call `release_full_control`.** It clears the approval.
- **A locked screen stops every launch.** The Mac locked twice overnight.
  `wait-for-signal-or-unlock.sh` wakes you when it unlocks. Never touch the
  password.
- **GLM-5.3 had capacity errors on Saturday.** "System is busy" and "model
  concurrency limit exceeded" each stalled C3. Retry once with the brief's
  continue text, plus the item id and report path. After that, mark the
  item stalled.
  - Balance at 16:09: GLM-5.3 54.5M of 200M for the day, Flash 206M of 300M.
    Check it under ZCode Model settings, Start Plan.
- **GLM sessions keep working about 2 minutes after they signal**, writing
  their own memory. To stay at two sessions, wait for their final summary
  before launching the next one.
- **The new-task composer defaults to GLM-5.3.** Pick Flash explicitly for
  Flash items.
- **Queued messages.** Return while a chat is working queues the message
  for the end of its turn. "Steer" injects it mid-turn instead.
- **ZCode's local logs** can tell a stalled chat from a working one without
  the screen. They are read-only:
  - `~/.zcode/v2/logs/<date>.log` (`turn-ended`, `pendingPermissions`);
  - `~/.zcode/cli/rollout/model-io-session_<id>.jsonl` (the last model
    error).

## Update, Saturday 20:22 (conductor 2)

The state has moved on since the table above. The live truth is
`ORCHESTRATOR-STATE.md`: its lanes table, and its log from 16:43 on.

- **Verified:** L1-234 and LG-1.
- **Aram pastes every prompt himself, one session per lane.** The order is
  in `LANE-QUEUE.md`:
  - Lane 1: L1-8, then L1-9.
  - Lane 2: L2-14, then L2-15, L2-17 and L2-16.
- **The conductor never launches anything.** It arms
  `sh wait-for-signal-or-unlock.sh 180`, verifies each signal by
  `ORCHESTRATOR.md`, and writes a `CLAUDE-VERDICT.md`. The specs for the
  new blocks are in `CAMPAIGNS.md` under "Next blocks".
- **Aram delegated every open decision to the orchestrator at 19:22.** The
  decisions are logged there. The landing session still asks Aram directly
  before any push to `main`, and before the merge into the live branch,
  which also waits for his "done studying".
