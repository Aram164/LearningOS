# GLM prompts, in order, one lane each

**Rules**
- Run at most two ZCode sessions at once, one per lane.
- Start each prompt in a new ZCode session, with the model shown.
- Start the next item only after the previous one has reported. Send every
  report to Claude.
- If an item's prerequisite isn't met yet, take the next item and come back
  to it later.
- Hard stop: Sunday 22:00. The credits end Monday 02:00.

## Lane 1: GLM-5.3

**L1-1. C3, CI sharding.** Starts now.
```text
Read LearningOS/workbench/glm-campaigns-2026-10-24/CAMPAIGNS.md: the Ground rules, then campaign C3 only. Do C3. I authorize git push --no-verify for your own branch glm/C3-2026-10-24 only. Report and stop.
```

**L1-2. C1 verification, batches A–C.** Needs: C1-A, C1-B and C1-C have reported.
```text
Read LearningOS/workbench/glm-campaigns-2026-10-24/CAMPAIGNS.md: the Ground rules, then C1's verification pass for the findings in C1-A/, C1-B/ and C1-C/. Try to refute each one and mark it CONFIRMED or REFUTED with the reason. Push nothing. Report and stop.
```

**L1-3. C1 verification, batches D–E.** Needs: C1-D and C1-E have reported.
```text
Read LearningOS/workbench/glm-campaigns-2026-10-24/CAMPAIGNS.md: the Ground rules, then C1's verification pass for the findings in C1-D/ and C1-E/. Try to refute each one and mark it CONFIRMED or REFUTED with the reason. Push nothing. Report and stop.
```

**L1-4. C2 re-check.** Needs: all eight C2 items in Lane 2 have reported.
```text
Read LearningOS/workbench/glm-campaigns-2026-10-24/CAMPAIGNS.md: the Ground rules, then C2's 20% re-check: across every module report in C2/, sample 20% of the defects and re-verify each against the PDF itself. Mark each CONFIRMED or REFUTED. Push nothing. Report and stop.
```

**L1-5. C4 for Betriebssysteme.** Needs:
- the slides are in `LearningOS/materials/`;
- Claude has confirmed the live-branch merge;
- no other session is working in the live tree.
```text
Read LearningOS/workbench/glm-campaigns-2026-10-24/CAMPAIGNS.md: the Ground rules, then campaign C4 for module-hu-betriebssysteme only. You are the only session in the live Core tree. Stop at module-plan-import --check for every deck, write each package and its check result to C4/, and apply nothing. Report and stop.
```

**L1-6. C4 for ICOP.** Same prerequisites as L1-5.
```text
Read LearningOS/workbench/glm-campaigns-2026-10-24/CAMPAIGNS.md: the Ground rules, then campaign C4 for module-hu-icop only. You are the only session in the live Core tree. Stop at module-plan-import --check for every deck, write each package and its check result to C4/, and apply nothing. Report and stop.
```

**L1-7. C4 apply.** Only after you have reviewed the C4 packages. List the
ones you approve.
```text
Apply exactly these C4 packages, which I approve: <list the package files>. Apply each one through the gateway under its snapshot, run tools/validate.py --compact and tools/warning_baseline.py --check after each, and stop at the first failure. You are the only session in the live Core tree. Report and stop.
```

**LG-1. Fix the learning-gaps gate failure.** Added 2026-10-24 by the
landing session, and runs as Lane 1's next item.
```text
Read LearningOS/workbench/glm-campaigns-2026-10-24/CAMPAIGNS.md: the Ground rules only (including the finish signal). Then fix your own earlier branch learning-gaps-2026-10-24 in its existing clone ~/los-learning-gaps-2026-10/repository. Its release-pair run 40047808799 on Core 326dd638 failed exactly one test: tests/test_arch_doc_commands.py::test_doc_commands_parse, with A8 "declaration must bind exactly one new inline span" at system/procedures/process-a-lecture.md lines 109, 271 and 470. Each <!-- los:reference {...} --> declaration must match exactly one inline code span with the same text in the prose paragraph it annotates (see _prose_rows in tests/test_arch_doc_commands.py). Fix the prose so that each declared command appears once as an inline code span, or drop a declaration that annotates nothing. Change no other file. Run tests/test_arch_doc_commands.py, then the process-a-lecture transcript, then validate and ruff, one at a time. Commit, and push your branch with git push --no-verify (I authorize that for this branch only). Dispatch one release-pair on the new full SHA with ui_sha f7dbc1f7607157d5c1c2edb84a14e6a26ab89f94, and wait for it with one background gh run watch. Write the new SHA, the run ID and the verdict to LG-1/REPORT.md, signal, and stop. Do not land anything.
```

## Lane 2: GLM-5.3-Flash

**L2-1. C2 for M2.** Starts now; it covers what you are studying.
```text
Read LearningOS/workbench/glm-campaigns-2026-10-24/CAMPAIGNS.md: the Ground rules, then campaign C2 for module-hu-m2-statistik-analysis only. Evidence only. Report and stop.
```

**L2-2 to L2-6. The C1 hunting batches.** Send them one after another,
changing the batch name each time: L2-2 is `C1-A`, then `C1-B`, `C1-C`,
`C1-D`, and L2-6 is `C1-E`.
```text
Read LearningOS/workbench/glm-campaigns-2026-10-24/CAMPAIGNS.md: the Ground rules, then campaign C1, batch C1-A only (hunting, not the verification pass). Push nothing. Write your findings to C1-A/, report and stop.
```

**L2-7 to L2-13. The remaining C2 modules.** Send them one after another,
changing the module name:
- L2-7: `module-hu-aml`
- L2-8: `module-hu-betriebssysteme`
- L2-9: `module-hu-icop`
- L2-10: `module-project-bachelor-thesis`
- L2-11: `module-foundation-ml-math-bridges`
- L2-12: `the five module-job-* modules together`
- L2-13: `module-skill-python`
```text
Read LearningOS/workbench/glm-campaigns-2026-10-24/CAMPAIGNS.md: the Ground rules, then campaign C2 for module-hu-aml only. Evidence only. Report and stop.
```

**Optional, your call:** to have C2 also prepare fixes, replace "Evidence
only." in any C2 prompt with:

```text
I authorize acting on critique point 1: prepare --check fix packages in your clone, never apply.
```

## Compressed plan, Saturday 2026-10-24 15:40 (orchestrator, on Aram's request)

Aram asked for fewer phases. The changes:
- **L2-13 is folded into L2-12's chat.** It was sent at 15:39 as a queued
  follow-up, so it reuses the session and clone. There is no separate
  launch.
- **L1-2, L1-3 and L1-4 are merged into one GLM-5.3 session, L1-234.** It
  runs in the slot Lane 2 frees once L2-13 has signalled, in parallel with
  Lane 1's C3, then LG-1. There are still never more than two sessions.

**L1-234. All verification, in one session.** Needs: L2-13 has signalled
(every C2 report exists). Model: GLM-5.3.
```text
Read LearningOS/workbench/glm-campaigns-2026-10-24/CAMPAIGNS.md: the Ground rules, then do both verification passes in this one session, in order. (1) C1's verification pass for every finding in C1-A/, C1-B/, C1-C/, C1-D/ and C1-E/: re-run each test on main in your own clone, try to refute the diagnosis, and mark it CONFIRMED or REFUTED with the reason; write C1-VERIFY.md. (2) C2's 20% re-check: across every module report in C2/, sample 20% of the defects and re-verify each against the PDF itself; mark each CONFIRMED or REFUTED; also say whether the M2 report's section check actually searched the materials (see the method note in C2/module-hu-aml/REPORT.md section 5); write C2/RECHECK.md. Push nothing. Report and stop. Your item id is L1-234 and your report path is C1-VERIFY.md.
```

## Next blocks, Saturday 2026-10-24 19:10 (orchestrator, for Aram to paste)

The specs are under "Next blocks" in `CAMPAIGNS.md`. At most two sessions
at once. Launch nothing after Sunday 22:00.

**Now, Lane 1. L1-8: C3-F, close the witness-producer gap.** Model: GLM-5.3.
```text
Read LearningOS/workbench/glm-campaigns-2026-10-24/CAMPAIGNS.md: the Ground rules, then the block C3-F only (under "Next blocks"). Do C3-F. I authorize git push --no-verify for your own branch glm/C3-2026-10-24 only, and dispatching that branch's own sharded release-pair.yml. Land nothing. Report and stop. Your item id is L1-8 and your report path is C3/FOLLOWUP.md.
```

**Now, Lane 2. L2-14: C2-R, M2's 80 unchecked routes.** Model: GLM-5.3-Flash.
```text
Read LearningOS/workbench/glm-campaigns-2026-10-24/CAMPAIGNS.md: the Ground rules, then campaign C2 and the block C2-R only (under "Next blocks"). Do C2-R. Evidence only. Push nothing. Report and stop. Your item id is L2-14 and your report path is C2/module-hu-m2-statistik-analysis/RECHECK-80.md.
```

**Next free slot. L1-9: C5, a fix branch for the confirmed C1 findings.**
Model: GLM-5.3.
```text
Read LearningOS/workbench/glm-campaigns-2026-10-24/CAMPAIGNS.md: the Ground rules, then the block C5 only (under "Next blocks"). Do C5. I authorize git push --no-verify for your own branch glm/C5-2026-10-24 only. Land nothing. Report and stop. Your item id is L1-9 and your report path is C5/REPORT.md.
```

**Queued (critique point 1 authorized under Aram's 19:22 delegation). L2-15
to L2-17: C2 fix packages.** One session at a time, because all three share
the C2 clone.
- **Targets:**
  - L2-15: `module-hu-aml`, on Flash;
  - L2-16: `module-hu-m2-statistik-analysis`, on **GLM-5.3**, after L2-14.
    Mapping 472 rows onto stages is design work.
  - L2-17: `the five module-job-* modules together`, on Flash. Its folder
    is `C2/_job-modules-evidence/`.
- **What the prompt changes per target:** the module, the folder, the item
  id, and the report path.
```text
Read LearningOS/workbench/glm-campaigns-2026-10-24/CAMPAIGNS.md: the Ground rules, then campaign C2 for module-hu-aml only. I authorize acting on critique point 1: prepare --check fix packages in your C2 clone, never apply. Fix only the defects that C2/module-hu-aml/CLAUDE-VERDICT.md and L1-234-CLAUDE-VERDICT.md confirm, and write each package with its --check result to C2/module-hu-aml/packages/. Push nothing. Report and stop. Your item id is L2-15 and your report path is C2/module-hu-aml/PACKAGES.md.
```
