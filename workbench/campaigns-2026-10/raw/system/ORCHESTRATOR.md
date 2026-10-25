# Overnight orchestrator for the GLM campaigns

This is the brief for a fresh Claude session. Aram is asleep while it runs.

You run the two GLM lanes until Aram wakes:
1. Wait for a GLM session's finish signal.
2. Verify its report.
3. Start the lane's next item in ZCode, using computer use.

Read these first, in order:
1. `CAMPAIGNS.md`: the ground rules every GLM session follows, and what each
   campaign is.
2. `PROMPTS.md`: the exact prompt for every item.
3. `ORCHESTRATOR-STATE.md`: what is running, done and queued. You keep it
   current.

Before your first computer-use action, read the `anthropic-skills:computer-use`
skill.

All paths are relative to
`/Users/aramaljanadi/Desktop/semestercontext/LearningOS/workbench/glm-campaigns-2026-10-24/`
unless they say otherwise.

## Boundaries

**Another Claude session owns these, the "landing session".** Do none of
them:
- landing GLM's `learning-gaps-2026-10-24` branch;
- fast-forwarding any `main`;
- re-running CI on `main`;
- merging into Aram's live branch;
- filing or closing issues.

**Never:**
- push or merge;
- touch the live trees `LearningOS/repository/` and `LearningOS/obsidian-ui/`
  for anything but reading;
- touch Obsidian or the vault;
- approve a ZCode permission prompt;
- run a third GLM session at once;
- change system settings;
- run a full test suite or `make system-check` locally.

**You may:**
- read anything;
- write in the campaign folder (verdicts, state, drafts);
- keep a scratch clone of Core `main`, cloned from GitHub into your
  scratchpad with its own venv, and run single test files there;
- drive ZCode (`dev.zcode.app`): open chats, pick a model, send messages.

## Setup, while Aram is still awake

He has to approve dialogs during setup.

1. **Computer use.** Load the tools (`ToolSearch` query `computer-use`, 30
   results). Run `request_access` for ZCode. If ZCode comes back with a tier
   that blocks typing, stop and tell Aram that the overnight plan cannot run.
   He then launches the prompts himself in the morning.
2. **Keep the Mac awake.** Call `mcp__ccd_host__request_keep_awake`; load it
   through `ToolSearch` first. Tell Aram that computer use fails on a locked
   screen. Preventing the lock is his setting to change; you do not touch it.
3. **Learn ZCode's UI** with screenshots:
   - how to open a new chat in the **semestercontext** workspace (the sidebar
     has `+ New` and a `semestercontext` group);
   - where to choose the model: **GLM-5.3** for Lane 1, **GLM-5.3-Flash**
     for Lane 2;
   - how to send a message.
4. **Give the two running sessions the signal rule.** They started before it
   existed. Find each chat in the sidebar: L1-1's first message reads
   "… campaign C3 only", and L2-3's reads "… campaign C1, batch C1-B only".
   Send this to the C3 chat:

   > When C3 is finished and your report is written, as your very last action run the finish-signal command from the Ground rules in CAMPAIGNS.md, with item id L1-1 and report path C3/REPORT.md. Change nothing else about your work.

   Send the same to the C1-B chat, with item id `L2-3` and report path
   `C1-B/REPORT.md`.

   If a chat cannot take a message while it is working, wait until its turn
   ends, then send.
5. **Show Aram it works.** Let him see a screenshot of a sent message. Log
   the setup in `ORCHESTRATOR-STATE.md`, then start the loop.

## The loop

1. Start `sh wait-for-signal.sh 180` with `run_in_background: true`, then
   end your turn. Never poll, and never sleep in the foreground. Its exit
   wakes you.
2. **On `SIGNAL <id>: <content>` lines**, handle each signal in turn:
   1. Move `signals/<id>.done` to `signals/processed/<id>-<HHMM>.done`.
   2. Verify the report, as in **Verification** below.
   3. Update `ORCHESTRATOR-STATE.md`: state, verdict, and a log line.
   4. Launch the next eligible item, as in **Launching** below.

   Then restart the wait. A `BLOCKED:` signal means: record the reason, don't
   retry, and give the lane its next item.
3. **On `TIMEOUT`**, take a screenshot of ZCode and check each running
   item's chat:
   - **Finished, but no signal:** treat it as done. Find its report and
     handle it as a signal.
   - **Waiting on a permission prompt:** do not approve it. Mark it
     `stalled: needs Aram`, and give the free slot to the next eligible item.
   - **Errored or crashed:** send `Continue where you stopped; follow
     CAMPAIGNS.md and finish with the signal.` once only. If it fails again,
     mark it stalled.
   - **Still working:** restart the wait.

## Launching

- **Two GLM sessions at most.** Count the running items in the state file.
- **Lane 1 runs GLM-5.3, Lane 2 runs GLM-5.3-Flash.**
- **Order:** take the lane's next item in the order of the state table that
  is queued and whose prerequisite holds.
  - If Lane 1 has nothing eligible, it takes the next queued **C2** item from
    Lane 2's list and runs it on GLM-5.3, so that both slots stay busy. Only
    C2 items may be borrowed.
- **To launch:**
  1. Open a new chat in the semestercontext workspace and select the model.
  2. Paste the prompt from `PROMPTS.md` verbatim. In the two template prompts
     (`C1-A` and `module-hu-aml`), substitute the batch or module.
  3. Append ` Your item id is <ID>.`
  4. Send it, take a screenshot to confirm it started, and log the time.
- **Never launch** L1-5, L1-6 or L1-7 (C4): they need Aram.
- **Launch nothing after Sunday 22:00 Berlin time.** Clocks go back on Sunday
  at 03:00.

## Verification

Keep it proportionate: your credits cost far more than GLM's. Aim for about
15 minutes per report.

GLM measures well but sometimes diagnoses with confidence and gets it wrong.
Tonight it called a CI pairing problem the cause of two failures, called
`main` divergent, and called original plan structure "broadcast damage".
Trust its measurements more than its headlines.

**C1 hunting reports (C1-B to C1-E).** For each finding:
1. Copy its test into your scratch clone's `tests/`. Register the file name,
   without `tests/`, in `tests/group_map.py`, in the group that fits.
2. Run only that file. It must fail on `main`, for the reason the finding
   documents.
3. Read the root cause it cites at `file:line`.
4. Decide whether this is a real contract violation or a misused API, and
   whether it can actually happen in Aram's tree.

Write CONFIRMED, REFUTED or UNSURE with reasons to `<batch>/CLAUDE-VERDICT.md`.

For each CONFIRMED finding, draft the issue text in `ISSUES-DRAFT.md`. First
search for duplicates with
`gh issue list --repo Aram164/LearningOS --state all --search "<keywords>"`.
**File nothing.** Remove your test copies and the `group_map` edit afterwards.

**C1 verification passes (L1-2, L1-3).** Compare GLM's marks with yours.
Re-check every disagreement yourself, and record it in the verdict.

**C2 module reports.**
- Check any claim of damage, broadcast or a wrong locator against the
  module's original generated plans in `work/active/<workspace>/outputs/`.
  Read the live tree only. A shape that matches the original is original
  design or unmigrated debt, not damage.
- Spot-check three concrete page or locator claims against the PDFs in
  `LearningOS/materials/`, read-only. Normalise ligatures before searching.
- Write `CLAUDE-VERDICT.md` beside the report.

**C3.**
- Read the report.
- On GitHub, confirm that the branch's sharded CI is green, and that the
  shard counts add up to the unsharded count. At `d6c47790` that count is
  8511 passed, 7 skipped, 1 deselected and 2 xfailed (release-pair run
  40035927006).
- Confirm that the A9/A19 population tests still see the whole population.
- Write a verdict only. Landing is Aram's call.

**L1-4.** Compare its results with the C2 verdicts.

## Morning

The first time you wake after 08:00 Berlin time, or as soon as both lanes are
idle with nothing eligible, write `MORNING.md` in the campaign folder. It
lists:
- every item: its state and a one-line verdict;
- the issue drafts that are ready to file;
- the decisions only Aram can make, among them C2 fix packages under critique
  point 1, landing C3, and C4's slides;
- anything stalled, and why.

If items are still running, keep the wait loop going.
