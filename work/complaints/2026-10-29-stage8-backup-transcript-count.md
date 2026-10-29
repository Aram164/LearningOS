# Backup procedure transcript expects 488 entries but exact-pair fixture contains 491

Workflow: Stage 8 hosted exact-pair acceptance; Core `455c4c165e6f5973a906d9a0457d1d9902980e9a` / UI `8e82f8a3311d05415edfb9b17c5517e652a3dd61`.

`pytest-shards (witness-1)` failed `tests/test_procedures.py::test_every_transcript_passes` at line 262. Scrut's `system/procedures/back-up-and-restore.md` drill has five mismatches: manifest summary, provenance count, full manifest count, restore checked count and tamper checked count all expect 488 but actually report 491. The restore itself reports `ok: true`, `issues: []`; the tampered material still produces the expected checksum mismatch and exit 1.

Source comparison with accepted Stage 4C adds two copied Core schema files and `src/features/unit/sequence.ts` in the UI backup root, consistent with the +3 count. This is evidence of stale count expectations, not evidence that restoring corrupted material succeeds.

Smallest follow-up: verify the complete declared backup inventory and restore/tamper assertions, then update only justified transcript expectations. Keep exact inventory/checksum checks. Reproduce with `tests/test_procedures.py::test_every_transcript_passes` under pinned Scrut 0.5.0. Acceptance requires the complete transcript and a new exact-pair gate to pass; no repair was performed during Stage 8.

Proof: [run](https://github.com/Aram164/LearningOS/actions/runs/40945395574), [job](https://github.com/Aram164/LearningOS/actions/runs/40945395574/job/123699314590); retained `stage8/witness-1.log`, `junit-verification.json` and digest-verified shard archives in the agility campaign. Environment: hosted Ubuntu, Python 3.14.4, Node 22. No original learner-vault changes or production actions.

Filed after duplicate search: https://github.com/Aram164/LearningOS/issues/76

Authorized repair follow-up: see `work/proposals/2026-10-29-agility-stage8-repair.md` and retained differential/procedure results under `workbench/agility-experiment/stage8-*`. The focused owning checks pass; final hosted acceptance belongs to the new exact-pair run.
