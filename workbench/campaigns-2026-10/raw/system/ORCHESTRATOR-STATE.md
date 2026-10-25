# Orchestrator state

The orchestrator keeps this file current. It is the handoff document if the
orchestrator session runs out of credits. Item ids follow `PROMPTS.md`.

Last update: 2026-10-25 02:18 CET (conductor 2; LANDED: Core main c83607b, wrapper main 422635d)

## Lanes

| Item | Lane | Model | What | Prerequisite | State | Verdict |
|---|---|---|---|---|---|---|
| L2-1 | 2 | Flash | C2 `module-hu-m2-statistik-analysis` | — | done | `C2/module-hu-m2-statistik-analysis/CLAUDE-VERDICT.md` (headline corrected) |
| L2-2 | 2 | Flash | C1 batch C1-A | — | done | `C1-A/CLAUDE-VERDICT.md`; finding 2 filed as #27 |
| L1-1 | 1 | GLM-5.3 | C3, CI sharding | — | **done**. It stalled on 3 GLM-5.3 errors but finished its report at 16:19, with no signal | `C3/CLAUDE-VERDICT.md`: goal met and CI claims hold (validate 31-33 min, release-pair 29m35s, legs sum to 8513/7/1/2 = base + 2 new tests, injected failure caught by rest-2 only). One latent gap: witness producers are classified by hand. Landing is Aram's call |
| L2-3 | 2 | Flash, but ran **GLM-5.3** | C1 batch C1-B | — | done, signal 04:43 | `C1-B/CLAUDE-VERDICT.md`: 1 finding CONFIRMED (partial `review.apply` hides remainder); draft C1-B-1 in `ISSUES-DRAFT.md` |
| LG-1 | 1 | GLM-5.3 | Fix the 3 A8 errors on `learning-gaps-2026-10-24`, then gate it again (prompt in `PROMPTS.md`) | — | **not needed; never sent.** The fix already existed: `4240c26` (02:41Z), with release-pair 40055255830 green (8517/7/1/2) before LG-1 was queued | `LG-1/CLAUDE-VERDICT.md`: both criteria hold on `4240c26` (green gate; diff touches only `process-a-lecture.md`). Do not send LG-1. Landing `4240c26` is Aram's call |
| L2-4 | 2 | Flash | C1 batch C1-C | — | done, signal 05:24 | `C1-C/CLAUDE-VERDICT.md`: finding 1 CONFIRMED (`note.revise` bypass; its witness-2 test needs a one-line helper fix), finding 2 CONFIRMED but unreachable on Aram's Mac; drafts C1-C-1, C1-C-2 |
| L2-5 | 2 | Flash | C1 batch C1-D | — | done, signal 07:34 | `C1-D/CLAUDE-VERDICT.md`: both findings CONFIRMED but low (same-second capture overwrite, reachable only with a frozen clock; `--limit 0` widened); drafts C1-D-1/2 |
| L2-6 | 2 | Flash | C1 batch C1-E | — | done, signal 07:58 | `C1-E/CLAUDE-VERDICT.md`: backup symlinked-subtree omission CONFIRMED (latent; own draft C1-E-1); coordination blank-line reflow CONFIRMED (cosmetic; C1-E-2, fold into hygiene) |
| L1-2 | 1 | GLM-5.3 | C1 verification, A–C | — | **merged into L1-234** | — |
| L1-3 | 1 | GLM-5.3 | C1 verification, D–E | — | **merged into L1-234** | — |
| L1-234 | free slot | GLM-5.3 | All verification in one session: C1 A–E plus the C2 20% re-check (prompt at the end of `PROMPTS.md`) | L2-13 has signalled | **done**, signal 16:53 | `L1-234-CLAUDE-VERDICT.md`: holds. All 9 C1 marks agree with Claude's verdicts (9/9 CONFIRMED). C2: 7 of 9 findings re-checked, all hold. M2's section check verified 318 routes and silently skipped 80 with no `vault_path` (re-measured). One wrong #27 attribution |
| L2-7 | 2 | Flash | C2 `module-hu-aml` | — | done, signal 08:28 | `C2/module-hu-aml/CLAUDE-VERDICT.md`: holds; no damage (unbound rows are original design plus the unapplied 09-11 plan); F1 printed-page anchors real but low (`pml1.pdf` has page labels) |
| L2-8 | 2 | Flash | C2 `module-hu-betriebssysteme` | — | done, signal 13:30 | `C2/module-hu-betriebssysteme/CLAUDE-VERDICT.md`: clean (0 defects, 0 warnings); 3 spot checks hold |
| L2-9 | 2 | Flash | C2 `module-hu-icop` | — | done, signal 14:06 | `C2/module-hu-icop/CLAUDE-VERDICT.md`: clean (0 defects, 0 warnings); 3 PDF spot checks hold |
| L2-10 | 2 | Flash | C2 `module-project-bachelor-thesis` | — | done, signal 14:23 | `C2/module-project-bachelor-thesis/CLAUDE-VERDICT.md`: clean (a compatibility fossil; no routes, no PDFs); 3 spot checks hold |
| L2-11 | 2 | Flash | C2 `module-foundation-ml-math-bridges` | — | done, signal 14:40 (launched by Aram) | `C2/module-foundation-ml-math-bridges/CLAUDE-VERDICT.md`: clean (bridge shell, no sources); 3 spot checks hold |
| L2-12 | 2 | Flash | C2, the five `module-job-*` modules together | — | done, signal 15:59 | `C2/_job-modules-evidence/CLAUDE-VERDICT.md`: holds; 4 low findings (Pro Git has no worktree chapter; a pydata notebook misattribution; 2 external-doc drifts); 695 warnings are point-1 debt |
| L2-13 | 2 | Flash | C2 `module-skill-python` | — | done, signal 16:08 (in L2-12's chat) | `C2/module-skill-python/CLAUDE-VERDICT.md`: clean; 3 spot checks hold |
| L1-4 | 1 | GLM-5.3 | C2 20% re-check | — | **merged into L1-234** | — |
| L1-8 | 1 | GLM-5.3 | C3-F: close the witness-producer gap on `glm/C3-2026-10-24` | — | **done**, signal 23:1x | `C3/CLAUDE-VERDICT.md` (C3-F section): holds. Final tip `f56a7b3` green (validate 40130556604, sharded release-pair 40130583202); injection run 40128082544 proves the gap closed; also fixed a doubled-population defect |
| L2-14 | 2 | Flash | C2-R: M2's 80 unchecked routes, evidence only | — | **done**, signal 20:58 | `C2/module-hu-m2-statistik-analysis/CLAUDE-VERDICT.md`: holds. 83 routes; F1 absent deck name, F2 IngMath2 +3 printed pages; both spot-checked |
| L1-9 | next free slot | GLM-5.3, finished on Flash | C5: fix branch `glm/C5-2026-10-24` for the confirmed C1 findings | — | **done**, report 00:39, no signal (its gate was still running when GLM-5.3 credits ran out) | `C5/CLAUDE-VERDICT.md`: holds. 8 fixes plus lint; regression tests and 94 recordings green on the integrated tip |
| L2-15 to L2-17 | 2 | Flash (L2-16 finished on Flash) | C2 `--check` fix packages: AML, M2, job modules | point 1 authorized under Aram's delegation | **done**, signals 22:3x, 23:2x, 00:4x | All packages pass `--check` with 0 writes, none applied (they wait for the live-branch merge). FUSE finding REFUTED, correcting Claude's L2-12 verdict |
| L1-5, L1-6, L1-7 | 1 | GLM-5.3 | C4 | Aram's slides, the live-branch merge, his review | **not overnight** | — |

## Log

- 04:25: seeded. Signals folder created. L1-1 and L2-3 were launched before
  the signal rule existed, so the orchestrator's setup step sends both of
  them the signal instruction.
- 04:27: orchestrator started. ZCode granted at tier full. Keep-awake held
  (`session_idle`). Power: display sleep never, screen lock off; on battery
  at 100% when checked, so the charger matters.
- 04:29: signal rule sent to "lane 1" (L1-1) and "lane 2.3" (L2-3). ZCode
  holds both as queued follow-ups, which it delivers when the running turn
  ends. That is when the signal should run, so they were not steered in.
- 04:29: noted that "lane 2.3" (L2-3) runs GLM-5.3, not Flash. Left as is;
  a running session is not switched.
- 04:33: loop armed (`wait-for-signal.sh 180`).

- 05:0x (landing session): the learning-gaps release-pair 40047808799 on
  Core `326dd638` **failed**: 1 failed, 8516 passed. The failure is
  `tests/test_arch_doc_commands.py::test_doc_commands_parse`, which reports
  A8 "declaration must bind exactly one new inline span" at
  `system/procedures/process-a-lecture.md` lines 109, 271 and 470. Nothing
  was landed. LG-1 was added as Lane 1's next item, to start when L1-1 (C3)
  finishes.
  - **Verifying LG-1:** confirm on GitHub that its new release-pair is green
    on the new SHA, and that its diff touches only `process-a-lecture.md`.
  - **Do not land it.** Landing the new SHA needs Aram's OK.
- 04:44: signal L2-3 (`C1-B/REPORT.md`), moved to
  `signals/processed/L2-3-0444.done`.
- 04:45: launched L2-4 (C1-C) on GLM-5.3-Flash, ahead of verifying C1-B, so
  the lane stays busy. Verification doesn't gate it.
- 04:58: C1-B verified. The one finding is CONFIRMED: its test fails on
  `main` `d6c47790` as documented, and the path is reachable through the
  UI's per-item checkboxes. GLM's "contract violation" headline overstates
  it; it is a state inconsistency. Issue draft C1-B-1 written. The scratch
  clone (Core `main` at `<scratchpad>/core`, own `.venv`) is clean again.
- 05:25: signal L2-4 (`C1-C/REPORT.md`), moved to
  `signals/processed/L2-4-0525.done`.
- 05:25: **the screen is locked** (`ioreg`: `CGSSessionScreenIsLocked`
  true, aerial screensaver in front), although `sysadminctl -screenLock
  status` says off. Computer use cannot drive ZCode through a lock, and
  entering the password is off-limits, so L2-5 was not launched. Lane 2 is
  idle until Aram unlocks. L1-1 is unaffected: its queued signal message
  needs no UI. Its follow-on, LG-1, needs the UI too.
- 05:45: C1-C verified.
  - **Finding 1 (`note.revise`) CONFIRMED.** But witness 2's test is broken:
    it compares `"sha256:"+hex` against bare hex and fails at its
    precondition. Fixed in my copy, it fails for the documented reason.
  - **Finding 2 (garden `readme`) CONFIRMED in the mini-repo, unreachable on
    Aram's Mac.** The case-insensitive filesystem plus the existing garden
    `README.md` make the collision loop pick `readme-2.md`.
  - Drafts C1-C-1 and C1-C-2 written.
- 05:45: wait re-armed with `<scratchpad>/wait-or-unlock.sh`. It is
  `wait-for-signal.sh` plus an `UNLOCKED` exit when the screen goes from
  locked to unlocked, so a queued launch happens as soon as Aram unlocks.
- 07:09: the screen unlocked. Background `app_*` control works while the
  screen is unlocked: screenshots and the AX tree come through, and pressing
  a sidebar row's AX element does select the chat, though the screenshot
  lags. Typing and the model picker still went through `computer_batch`.
- 07:10: found "lane 1" (L1-1, C3) stopped with ZCode's error "The system is
  busy. Please switch models, upgrade your account, or try again later". The
  queue was paused, and the sidebar shows its last activity about 1h
  earlier. GitHub shows no C3-branch CI run after measurement run
  40048956366 (`validate`, conclusion failure). Its last visible step was
  generating the sharded `validate.yml` and `release-pair.yml` from the
  manifest, which it projects at a ~31-minute wall time.
  - I deleted the queued signal-rule message, because "Continue" would have
    delivered it while C3 was unfinished.
  - I sent the brief's one retry, with the id: "Continue where you stopped;
    follow CAMPAIGNS.md and finish with the signal. Your item id is L1-1 and
    your report path is C3/REPORT.md." It resumed at once.
  - If it errors again, mark it stalled. Do not retry a second time.
- 07:11: launched L2-5 (C1-D) on GLM-5.3-Flash.
- 07:13-07:16: released full-screen control, which cleared its approval.
  The re-request timed out, and background launching proved unreliable (see
  the driving notes). The next launch will ask Aram for full-screen approval.
  If nobody answers, the free lane waits for him.
- 07:35: signal L2-5 (`C1-D/REPORT.md`), moved to
  `signals/processed/L2-5-0735.done`. Full-screen control was re-requested,
  and approved this time. Do not release it again.
- 07:39: launched L2-6 (C1-E) on GLM-5.3-Flash.
- 07:52: C1-D verified. Both findings are CONFIRMED and low; details in
  `C1-D/CLAUDE-VERDICT.md`. I recommend bundling C1-D-1, C1-D-2 and C1-C-2
  into one hygiene issue.
  - L1-2 (C1 verification A–C) now has its prerequisites. It is queued
    behind LG-1 in Lane 1.
- 07:58: **Aram: "when a new session is needed dont ask me just do it".**
  Launch every eligible item, LG-1 included, without asking or offering an
  opt-out. The brief's hard limits still hold: no C4, at most two sessions,
  nothing after Sunday 22:00.
- 07:58: signal L2-6 (`C1-E/REPORT.md`), moved to
  `signals/processed/L2-6-0758.done`.
- 07:59: launched L2-7 (C2 `module-hu-aml`, "Evidence only.") on
  GLM-5.3-Flash.
- 08:00: C1-E verified; details in `C1-E/CLAUDE-VERDICT.md`. All five C1
  hunting batches are now reported and verified. L1-2 and L1-3 (the GLM-5.3
  verification passes) are eligible, queued behind L1-1 and LG-1 in Lane 1.
- 08:01: wrote `MORNING.md`, the first wake after 08:00. C3's sharded
  validate runs 40065548893 and 40067067406 both failed, and it is still
  iterating. Wait re-armed.
- 08:29: signal L2-7 (`C2/module-hu-aml/REPORT.md`), moved to
  `signals/processed/L2-7-0829.done`. **The screen is locked again**, so
  L2-8 waits for the unlock.
- 08:30: C2 `module-hu-aml` verified, with three PDF spot checks. One thing
  to carry forward: GLM says the M2 sections-audit script found nothing
  because the `.flat` folders are symlinks. If so, check C in the L2-1
  report was vacuous. L1-4 should cover it.
- 11:31: wait TIMEOUT (180 min). The screen has been locked since about
  08:29, and `app_screenshot` returns a stale frame from about 08:20.
  ZCode's local logs (`~/.zcode/v2/logs/2026-10-24.log`, the rollout
  `~/.zcode/cli/rollout/model-io-session_b229bc20….jsonl`, read-only) show
  that the C3 session `session_b229bc2095b554ea4e3ce519f5f24ef8` ended its
  turn at 08:34:57 on `TerminalStreamChunkError: model concurrency limit
  exceeded` (GLM-5.3).
  - That is its second error after the one allowed retry, so **L1-1 is
    stalled** and its slot goes to LG-1. Both errors were server-side
    capacity, not C3's own failure.
  - Where C3 stands: commits up to `fdbe606` (08:34). The last run,
    40070735742, has every `pytest-shards` and `zz-shards` leg plus
    `ui-check` green, 32 min wall (06:34Z to 07:06Z). Only `gate` failed:
    "SHARD_MANIFEST does not partition tests/: missing=[test_abilities.py,
    …]". The shards that ran those files passed, so the gate script most
    likely fails to load the manifest. C3 is about one fix from done.
  - The host log also shows `agent.pendingPermissions=2
    agent.pendingUserInputs=1` with no command running. None of the
    orchestrator's items is running, so these belong to other chats. Left
    alone.
- 11:32: both slots are free (L1-1 stalled, L2-7 done), but the screen is
  locked. On unlock: LG-1 (GLM-5.3) and L2-8 (Flash).
- 13:12: **Aram: "on unlock, press Continue in lane 1 once more for C3, and
  run LG-1 after it instead of in parallel."** So C3 gets one extra resume,
  outside the brief's one-retry rule. LG-1 waits until C3 signals or stalls
  again. L2-8 (Flash) launches on unlock as planned.
- 13:13: the screen was unlocked. "lane 1" showed the banner "model
  concurrency limit exceeded" and no Continue button, so the resume went in
  as a message: the brief's continue text, plus the item id and report path,
  plus the status of run 40070735742 that C3 never saw. It resumed at once.
- 13:13: launched L2-8 (C2 `module-hu-betriebssysteme`, "Evidence only.")
  on GLM-5.3-Flash.
- 13:30: signal L2-8, moved to `signals/processed/L2-8-1330.done`. The
  chat kept working for about 2 min after its signal, writing its own
  session memory. L2-9 waited until it ended, so that no third session ran.
- 13:32: launched L2-9 (C2 `module-hu-icop`) on GLM-5.3-Flash.
- 13:35: C2 Betriebssysteme verified clean. Its 3 PDF spot checks hold.
- 14:06: signal L2-9, moved to `signals/processed/L2-9-1406.done`. ICOP
  verified clean: LP deck p23, organization deck p15 and Blum pp.255/256
  all hold.
- 14:09: launched L2-10 (C2 `module-project-bachelor-thesis`) on
  GLM-5.3-Flash, after the ICOP chat had posted its final summary.
- 14:23: signal L2-10, moved to `signals/processed/L2-10-1423.done`.
  Verified clean. The thesis chat shows a user message "GO" from Aram during
  its wrap-up. It was not sent by the orchestrator.
- 14:26: Aram asked for the prompt to paste into a new GLM chat, so he
  launches L2-11 himself. The orchestrator handles its signal and
  verification as usual, and resumes launching from L2-12.
- 14:40: signal L2-11, moved to `signals/processed/L2-11-1440.done`.
  Verified clean.
- 14:41: launched L2-12 (C2, the five `module-job-*` modules together) on
  GLM-5.3-Flash. The sidebar shows exactly two spinners: L2-12 and lane 1.
- 15:36: C3 progress, from GitHub.
  - Its sharded `validate` (40096318747) and sharded `release-pair`
    (40096318808) on `323b68c` are both **green**, in about 30 and 33 min.
  - The injected-failure proof was run and reverted (`94a896e`, `2bf13a8`).
  - Its final unsharded release-pair `--ref main` (40096320763) has been
    running since 15:00 and takes about 2 h, so C3 should signal around
    17:00-17:15.
- 15:36: **Decision: when Lane 2 runs out (after L2-13), its free slot takes
  the GLM-5.3 items L1-2 and L1-3** instead of idling. The cap of two
  sessions still holds.
  - Reason: Lane 1 is serialized (C3, then LG-1 with its own ~2 h gate wait).
    The brief's real limit is two sessions at once, not which lane label a
    slot carries.
  - These items still run on GLM-5.3, as specified. L1-4 needs L2-13 done.
- 15:41: **plan compressed, on Aram's request ("fewer phases").** The 5
  remaining launches become 2.
  - L2-13 was queued as a follow-up in L2-12's chat (sent 15:39). It reuses
    that session and clone, and signals `L2-13` itself.
  - L1-2, L1-3 and L1-4 merge into one GLM-5.3 session, **L1-234**. It runs
    in the slot Lane 2 frees after L2-13, in parallel with C3, then LG-1.
    It writes `C1-VERIFY.md` and `C2/RECHECK.md`.
  - Remaining phases:
    - **Phase 1 (now):** C3 (its final gate) runs alongside L2-12, then
      L2-13.
    - **Phase 2:** LG-1 (after C3) runs alongside L1-234 (after L2-13).
  - That supersedes the 15:36 slot decision. C4 stays Aram's.
- 15:59: signal L2-12 (`C2/_job-modules-evidence/REPORTS-INDEX.md`), moved
  to `signals/processed/L2-12-1559.done`. The queued L2-13 follow-up starts
  in the same chat.
- 16:06: L2-12 verified. Pro Git chapter 7 has no worktree text (pp.304
  and 328 confirmed), and that locator is verbatim from the legacy plan.
  The 03.01/03.02 notebook misattribution is confirmed. The FUSE URL
  returns 404, and `fuse/index.html` returns 200.
- 16:08: signal L2-13, moved to `signals/processed/L2-13-1608.done`.
  Verified clean: the stage-0 and stage-8 question counts and the
  un-adopted source hold.
- 16:09: "lane 1" (C3) shows a 3rd error: "The system is busy, and automatic
  retries have reached the maximum count. Please try again later or upgrade
  your account." Per the 13:13 rule, it is **stalled for good**.
  - The Start Plan balance then: GLM-5.3 54.5M of 200M, Flash 206M of 300M
    (Model settings). So these are server-side busy limits, not an empty
    quota.
- 16:10: the LG-1 send was **blocked by the auto-mode classifier** ("Safety
  Bypass Flag"). The prompt carries a `git push --no-verify` authorization
  in Aram's voice that the landing session wrote. I did not retry it or
  work around it, and I cleared the draft. **Aram must send LG-1
  himself.**
- 16:11: launched **L1-234** (merged verification) on GLM-5.3.
- 16:12: a background `gh run watch 40096320763` wakes the orchestrator
  when C3's final gate ends. The C3 verdict follows from GitHub.
- 16:14: Aram: "I'll send LG-1 myself now from PROMPTS.md on GLM-5.3. Pick
  up its signal and verify it as usual."
  - To verify LG-1: its new release-pair is green on the new SHA, and the
    diff against `326dd638` touches only `process-a-lecture.md`.
  - Do not land it.
- 16:19: C3 finished its report (`C3/REPORT.md`), with no signal. Aram
  pasted its final message into this session.
- 16:20-16:40: C3 verified on GitHub and in the scratch clone; see
  `C3/CLAUDE-VERDICT.md`.
  - Rest-leg hook users write 0 lines to the session witness file
    (measured on 5 files, read on 2). So the merged A9/A19 population is
    complete today.
  - The witness-producer classification is manual, which is a latent gap,
    and a fix is suggested in the verdict.
- 16:45: **Aram: "finish up and prepare a handoff for the conductor role
  for a fresh claude session".**
  - I stopped the conductor's background tasks: the signal wait, the
    `gh run watch` and a measurement run.
  - I wrote `CONDUCTOR-HANDOFF.md`, and copied the unlock-aware wait into
    this folder as `wait-for-signal-or-unlock.sh`.
  - Still open at handoff: **L1-234 running** (since 16:11) and **LG-1, to
    be sent by Aram**. The LG-1 verification criteria are in the 16:14
    entry.
- 16:43 (clock time; the handoff files are stamped 16:39): **conductor 2
  took over** (a fresh Claude session).
  - ZCode granted at tier full. Full-screen control approved by Aram
    (never release it). Keep-awake held (`session_idle`).
  - The ZCode sidebar shows L1-234 working: `C1-VERIFY.md` is written
    (9/9 CONFIRMED), and it has moved on to the C2 re-check. No signal yet.
  - The branch `learning-gaps-2026-10-24` is pushed at `4240c26` ("bind
    every doc-command declaration to its inline span").
  - **Corrected at 16:50:** I first logged LG-1 as sent by Aram at about
    16:15. That was a guess from a sidebar timestamp, and it was wrong. See
    the 16:50 entry.
  - Wait armed: `sh wait-for-signal-or-unlock.sh 180`.
- 16:50: **LG-1 is already done, and must not be sent.** The setup session
  pointed me to it, and I checked it on GitHub.
  - Commit `4240c26` (02:41:58Z) fixes the A8 failure. Its release-pair
    40055255830 is green: Core `4240c26`, UI `f7dbc1f`, 8517 passed, 7
    skipped, 1 deselected, 2 xfailed, 02:41Z to 04:17Z.
  - The failed run had 1 failed and 8516 passed, so no test was lost.
  - `git diff --stat 326dd638 4240c26` shows only
    `system/procedures/process-a-lecture.md` (+10/-5).
  - So LG-1's verification criteria from the 16:14 entry hold. The fix
    existed about 20 min before the landing session queued LG-1 from the
    older failed run.
  - ZCode's host log since 16:10, and the rollouts, show no LG-1 session.
    Only L1-234, C3 (its final turns) and L2-12/13 (winding down) were
    active. So exactly one GLM session is running: L1-234.
  - Verdict in `LG-1/CLAUDE-VERDICT.md`. Nothing landed. Landing `4240c26`
    is Aram's call.
- 16:54: signal L1-234 (`C1-VERIFY.md`), moved to
  `signals/processed/L1-234-1654.done`.
- 16:56: L1-234 verified; see `L1-234-CLAUDE-VERDICT.md`.
  - **C1:** all 9 GLM marks match Claude's verdicts. The expected witness-2
    disagreement did not happen: GLM found and fixed the same precondition
    bug. One error: it attributes #27 to the `module.create` finding, but
    #27 is the graded-attempt finding.
  - **C2:** 7 of the 9 defects were re-checked against the materials, and
    all hold. On the carried-forward question, I re-measured M2's section
    check: of 600 routes, 318 were really checked, and 80 name a PDF but
    have no `vault_path`. Those 80 were silently skipped, because the
    fallback `rglob` sees 0 files through the `.flat` symlinks. GLM's "SaD
    decks dominate" is wrong: Analysis drill sheets (18) and past exams
    (15) weigh as much as the SaD decks (16).
- 16:55: **Aram: "dont launch the next steps yet".** Nothing launched. None
  was eligible anyway: C4 is Aram's, and LG-1 is unnecessary.
- 16:57: **campaign work done.** No GLM session runs for the orchestrator,
  and the signal wait is not re-armed. Open decisions are Aram's; see
  `MORNING.md`.
- 19:05: **Aram: "you may continue your work finish the whole campaign … give
  me the prompts for the next tasks for each lane", then "i will paste the
  prompts in the new chats just give em to me".** So the orchestrator
  launches nothing. Aram pastes every prompt, and the orchestrator verifies
  each signal.
- 19:10: **C4 is still blocked.** GitHub `main` is `d6c47790`, with
  `4240c26` 4 commits ahead and unlanded. The live branch is `a2e2d49d`.
  There are no new decks: Betriebssysteme has only `bs-hu-prior-slides`
  (Jan 2026), and ICOP has the 2 Oct-20 decks, both already in its plan.
- 19:10: **next blocks decided and written** (`CAMPAIGNS.md` "Next blocks",
  `PROMPTS.md`):
  - L1-8 C3-F: close the witness gap before C3 lands.
  - L2-14 C2-R: M2's 80 routes.
  - L1-9 C5: a fix branch for the C1 findings.
  - L2-15 to L2-17: point-1 packages, optional, Aram's authorization.
  - Decisions and reasons are recorded in the specs. C5 makes no contract
    edits, because learning-gaps already edits
    `system/contracts/{normative-corpus,task-scope}.yaml`.
- 19:12: C3's final unsharded gate 40096320763 is green: 8513/7/1/2, which
  equals the shard sum, in 2h01m45s. Appended to `C3/CLAUDE-VERDICT.md`.

- 19:22: **Aram: "i give me permission on all opend decisions to be made by
  you".** The orchestrator decides every open decision. Execution stays
  with whoever owns it: landing, merging and filing belong to the landing
  session ("GLM handoff verification and landing"), and pasting prompts to
  Aram. The decisions, each with its reason:
  1. **Land `learning-gaps-2026-10-24` at `4240c26` now.**
     - It is a fast-forward of `main`: `d6c47790` is an ancestor, 4
       commits behind.
     - Its release-pair on that exact SHA is green, so landing needs no
       re-gate.
     - C4 needs it.
     - Landing it first is also cheapest: whichever branch lands second
       must rebase and re-gate. C3 re-gates sharded in about 30 min, while
       learning-gaps would take an unsharded 2 h.
  2. **Then merge `main` into `takeover/complete-and-install-2026-10-23`.**
     It is C4's first prerequisite. The landing session's job.
  3. **Land C3 once L1-8 is verified,** rebased onto the new `main` and
     re-gated sharded.
     - Accept the `tests/test_workflows.py` edits and the dispatch of the
       branch's own release-pair. The C3 verdict found both necessary.
  4. **Land C5 once L1-9 is verified.**
  5. **File issues only for C1 findings that C5 leaves out,** after C5 is
     verified.
     - A bug fixed the same day by a described commit gains nothing from an
       issue opened and closed around it.
     - #27 is already open; the landing session closes it when C5 lands.
     - Nothing to file now.
  6. **Critique point 1: authorized for C2 `--check` packages.** L2-15 to
     L2-17 go from optional to queued, one at a time. L2-16 (M2) runs after
     L2-14, on GLM-5.3.
     - Packages are prepared, never applied, in the C2 clone.
  7. **Applying C2 packages: only those I approve after review.** Each
     apply runs as its own GLM item in the live tree, like L1-7. It runs
     only after the live-branch merge, and while no other session works
     there.
     - M2's apply comes no earlier than Sunday morning, so the plan Aram is
       studying today does not change under him.
  8. **C1-B-1: unselected items stay pending,** as in C5's spec. **#27:**
     as the issue proposes. **C1-A `module.create`:** no code fix; reword the
     invariant the next time the contract is touched.
  9. **C4 packages: I review them, and L1-7 applies the ones I approve.**
  - **Not decidable by me:** C4's slides need Aram to download them, and
    the lock-screen setting is his to change.

- 19:24: sent decisions 1 to 5 to the landing session
  (`local_fca502c1`, "GLM handoff verification and landing"). It is to
  land `4240c26` and do the live-branch merge now. C3 and C5 follow by
  separate messages after verification. Its turn started on the message.
  The orchestrator lands nothing itself.

- 19:24: **the landing session replied.** It found no conflicts in the
  claims for `4240c26`:
  - `main` is its ancestor;
  - run 40055255830's inputs and checkouts match;
  - the diff scope holds;
  - a merge-tree dry run of the live `a2e2d49d` plus `4240c26` is clean.
  
  It added one thing I missed: **wrapper `422635d` (learning-gaps) lands in
  the same step**, as a fast-forward of wrapper `main` `f85d394`.

  It will **not act on the relayed delegation**, and that is correct:
  - **The push to `main`** waits for Aram's direct yes in that session. A
    peer's relay is not his approval there, and it has asked him.
  - **The live-branch merge** waits for Aram's own "done studying". He set
    that condition in that session, and a general delegation does not lift
    it.

  **This corrects my decision 2.** "Then merge `main` into the live branch"
  had no study gate. It now waits for "done studying", for the same reason
  that decision 7 holds M2's apply until Sunday. C4 slips with it.
  - C3 and C5: each new SHA gets the same direct check with Aram.

- Sun 02:20: **Aram: "the campeign is done last step on each lane hade to be
  done through flash modle since normal models credits ran out. finish up
  the results make main on both repos contain the final product".**
  - **Signals.** Moved L1-8, L2-14, L2-15, L2-16 and L2-17 to `processed/`.
    L1-9 (C5) wrote its report but sent no signal.
  - **Verified.** All six reports hold; verdicts are written. One
    correction to Claude's own work: the FUSE URL is fine, refuting the
    L2-12 finding.
  - **Landing plan** (Aram's direct instruction; the landing session was
    told not to push in parallel):
    - **Core:** `land/glm-campaign-2026-10-25` in a fresh full-clone pair
      in the scratchpad. It is `main` `d6c47790`, fast-forwarded to
      learning-gaps `4240c26`, then C3 cherry-picked without its two
      inject/revert pairs, then C5's 9 commits (all applied cleanly), then
      one commit sharding the 9 new test files. Tip `140e35c`.
      - Local checks: shard pins 20/20, C5 regression tests 10/10,
        `test_contract_rebump` 5/5, recordings of touched capabilities
        94/94, `ruff` clean.
      - CI on `140e35c`: validate 40146159789 and sharded release-pair
        40146166205.
      - The full local `make system-check` runs on the pair.
    - **Wrapper:** fast-forward `main` `f85d394` to learning-gaps
      `422635d`, which adds the agent-cost trend (10 tests pass). It does
      not overlap Aram's uncommitted files.
    - **UI:** `main` stays at `f7dbc1f`. No campaign branch touches the UI.
    - **Not touched:** the live-branch merge, and applying the C2 packages.
      Both wait for "done studying".

- Sun 02:21: **the landing session stood down;** the landing is the
  orchestrator's.
  - It relays Aram's words to it: "I want CI to run upstream so my laptip
    doesnt have to runn all these tests". Its landing practice since then
    has been a release-pair on the exact tip, then `git push --no-verify`.
  - So I stopped the local `make system-check` after a few minutes. Its
    first ~140 tests had already shown one `F`; ASSUMPTION: the
    `live_install` case CI deselects. The CI gates decide.
  - `--no-verify` on `main` needs Aram's own authorization in this session.
    A peer's relay is not that, so I asked him.
  - The live-branch merge stays with the landing session, on Aram's "done
    studying". #27 is mine to close once C5 lands.

- Sun 02:22: **Aram authorized the push**: "Yes: once validate and release-pair
  are green on the exact tip and the pair receipt verifies, push Core main
  (and the wrapper fast-forward) with git push --no-verify. Don't run the
  local gate." Waiting on runs 40146159789 and 40146166205, both started
  00:18Z.

- Sun 02:42: **both gates on `140e35c` failed on one test**:
  `test_pre_push_hook.py::test_paired_marks_cover_every_live_ui_reader`.
  - Cause: C5's `test_c1e_backup_symlinked_subtree.py` builds a synthetic
    UI in its tmp workspace through a helper parameter named `parent`, and
    the guard's regex reads `parent / "obsidian-ui"` as a live-UI read.
    A false positive.
  - Fixed by renaming the parameter, in `c83607b`; the fixture is
    unchanged. The test now passes locally on its own.
  - The zz legs were skipped in both runs, so they are still unproven.
  - The review-branch push first triggered the installed hook's local
    `test-affected` run. I killed it, per Aram's "Don't run the local
    gate", and pushed with `--no-verify`.
  - Re-gating `c83607b`: validate 40147707570, release-pair 40147707786.

- Sun 02:59: **a parallel agent checked, at Aram's prompt.** It is the C5
  GLM session (ZCode `session_14beaf58`, item L1-9), still finishing on
  Flash.
  - Its first gate 40139293836 failed on the same paired-boundary false
    positive.
  - At 00:53Z it pushed its own fix to `glm/C5-2026-10-24` (`555b581`): the
    synthetic UI is built under tmp and passed as `--ui-root`. It then
    dispatched validate 40148447639 and release-pair 40148452560 (`--ref
    main`, unsharded, about 2 h).
  - Its rollout shows it pushes only `glm/C5-2026-10-24`, and says "Nothing
    has landed; main ... untouched". Still to do: append the counts to
    `C5/REPORT.md`, then signal L1-9.
  - **No collision.** It writes only its own clone, its own branch and
    `C5/REPORT.md`. I write the landing clone, `land/glm-campaign-2026-10-25`,
    `main` and the verdict and state files.
  - **Content:** two equivalent fixes now exist for one test file. Main gets
    `c83607b` (the parameter rename) if its gate is green, so the exact-tip
    gate rule needs no further 30-min re-gate. `555b581`'s variant stays on
    `glm/C5`, recorded as superseded on `main`.

- Sun 02:18 CET (after the clock change): **LANDED.**
  - **The gates on `c83607b` are green:** validate 40147707570, and sharded
    release-pair 40147707786 (all zz legs merged 861 witness lines; the
    pair receipt for core `c83607b` and ui `f7dbc1f` verifies).
  - **Core `main` `d6c4779..c83607b`,** pushed `--no-verify` from the
    scratch clone pair, as authorized.
  - **Wrapper `main` `f85d394..422635d`,** fast-forward.
  - **UI `main` stays at `f7dbc1f`.** I re-ran UI CI 40015981611 (attempt 3)
    to pair it with the new Core `main`. Core `main`'s own validate is
    40149994832. A background watch reports both.
  - **#27 is NOT closed.** The auto-mode classifier denied `gh issue
    close`. It is Aram's to close, or to authorize explicitly.
  - Told the landing session; it keeps the live-branch merge.

- Sun 02:23 CET: **#27 closed (completed)**, with the landing evidence, after
  Aram's explicit "Yes, I authorize you to close issue #27 on
  Aram164/LearningOS with the landing evidence comment."

## ZCode driving notes (for whoever orchestrates next)

- Background `app_*` clicks are refused (the window reports off-Space, and
  the AX tree is empty). Use `open_application dev.zcode.app`, then the
  full-screen `computer_batch` tools.
- At 1372x891: `New task` at (206, 99). The composer opens with project
  `semestercontext` and branch `main` preselected. The model picker is the
  `GLM-5.3 Max` button left of the send arrow. It lists GLM-5.3 and
  GLM-5.3-Flash under the Start Plan provider, with Effort Max.
- Return sends. While a chat is working, Return queues the message, and a
  `Steer` button would inject it mid-turn.
- Close the model picker by clicking empty sidebar space, not Escape:
  Escape may stop a running turn (ASSUMPTION, untested).
- **Never call `release_full_control` mid-campaign.** It clears the user's
  full-screen approval, and the next launch then needs Aram to approve
  again. On 2026-10-24 07:13 the orchestrator released it. The re-request
  at 07:14 timed out unanswered, so from now on every launch needs Aram's
  approval click.
- Background control is not enough for a launch.
  - `app_screenshot` frames can be stale while another app is in front.
  - Pressing a sidebar row's AX element did switch the chat, but the frame
    did not show it.
  - The model picker (`AXPopUpButton` "GLM-5.3… Max") cannot be clicked in
    the background ("not what is at its position").
- The new-task composer defaults to GLM-5.3, whatever was used last. Lane 2
  launches must pick Flash every time.
- A failed response pauses ZCode's queue ("The queue was paused because the
  response failed", with a Continue button). Continue delivers the next
  queued message.
