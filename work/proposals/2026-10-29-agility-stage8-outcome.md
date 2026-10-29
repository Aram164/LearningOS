# Stage 8 — initial failed attempt and repair record

**Initial attempt verdict: not accepted.** [Release-pair run 40945395574](https://github.com/Aram164/LearningOS/actions/runs/40945395574), attempt 1, completed with `failure`. It was dispatched once with the requested existing workflow, then monitored using `gh run watch --exit-status`; the watcher exited 1. No implementation changes, speculative fixes or reruns followed the failure.

Exact tested pair:

- Core: `455c4c165e6f5973a906d9a0457d1d9902980e9a`.
- UI: `8e82f8a3311d05415edfb9b17c5517e652a3dd61`.
- Workflow definition/run head equals that Core SHA. All six exact-checkout/clean-worktree assertions passed: five pytest jobs and the UI job. The UI log independently records both exact checkout revisions. Hosted environment: Ubuntu, Python 3.14.4, Node 22.

## Job and artifact results

| Job | Result | Hosted pytest result |
|---|---|---|
| ui-check | passed | Full `npm run check`, including production contract checks |
| pytest-shards (rest-1) | passed | 1,900 passed, 4 skipped/expected failures |
| pytest-shards (rest-2) | passed | 1,780 passed, 2 skipped/expected failures |
| pytest-shards (rest-0) | failed | 3,083 passed, 1 failed |
| pytest-shards (witness-0) | failed | 1,140 passed, 4 failed |
| pytest-shards (witness-1) | failed | 72 passed, 1 failed, 2 expected failures |
| zz-shards | skipped | Population witness matrix did not run |
| gate | skipped | No full-population proof, final static gate or pair receipt |

The five downloaded JUnit ZIPs match their GitHub SHA-256 digests, artifact run ID and Core head. They contain **7,975 passed, 6 failed and 8 skipped/expected-failure cases**. These 7,989 cases are the suite-phase artifacts, not a certified complete-suite population: the zz jobs and final collection comparison never ran. Final metadata lists ten artifacts (five JUnit, five witness populations), with **no `learningos-pair-*` artifact**. Therefore a final release receipt, shipped bundle hashes and final receipt verification are unavailable; none is claimed.

## Exact failures and diagnosis

1. [witness-1, job 123699314590](https://github.com/Aram164/LearningOS/actions/runs/40945395574/job/123699314590): `tests/test_procedures.py::test_every_transcript_passes`, line 262. `system/procedures/back-up-and-restore.md` has five Scrut output mismatches, expecting **488** inventory/checked entries but observing **491**. Successful restore reports `ok: true` and no issues; the deliberate tamper still reports `checksum-mismatch` and exit 1. Compared with Stage 4C, two copied Core schema files and one UI source file were added inside the declared backup roots, consistent with +3 entries. The transcript's inventory expectations need review. [Issue #76](https://github.com/Aram164/LearningOS/issues/76).
2. [rest-0, job 123699314605](https://github.com/Aram164/LearningOS/actions/runs/40945395574/job/123699314605): `tests/test_system_audit_2026_09_05.py::test_dossier_projection_loads_the_repository_once_and_hashes_once`, line 528. Expected one observed shared-deck hash; observed **0**. Source inspection shows its spy wraps `materials_resolution.sha256_bytes`, while streamed material hashing now uses `hashlib.file_digest`. That spy no longer observes the file-hashing path. This is not proof of zero hashes or proof of correct per-build reuse; retain the invariant and test the actual boundary. [Follow-up on #74](https://github.com/Aram164/LearningOS/issues/74#issuecomment-6508221067).
3. [witness-0, job 123699314569](https://github.com/Aram164/LearningOS/actions/runs/40945395574/job/123699314569): `tests/test_scenarios_effects.py::test_scenario_effects[ai-action.delivery.apply::apply-garden-shelve]` and `[ai-action.delivery.apply::exact-replay]` disagree with their recordings at `operations/ai-actions/requests/KEY1/request.yaml` before/after hashes and corresponding receipt/stdout. Before: recorded `2b47eb2494b21d476caa725d630111818b6369e67a5cb5c7e254170735a2feee`, actual `a724b1df547b0d02e5080a5d5ea321d786ed54a70c1a9d32a6c56fc3b4980644`. After: recorded `ddf2bb2b9e01776fffe36ff443c75e64421a6ce919d3308c5532a075fae8284f`, actual `2e65277fbbfa416b5244666192543bbddcc57b83277682917d46993349ce18de`. The cause is not isolated; recordings must not be refreshed without verifying the changed request bytes and bindings. [Issue #77](https://github.com/Aram164/LearningOS/issues/77).
4. The same witness-0 job fails `[lineage.restamp::check-all]` and `[lineage.restamp::check-all-cli]`: recorded `judgment_commit` is `9a271b3aa17e903ca91bbc4cb22d7d7834e9cd86`, actual `67f4f3087c6307c924a0c041f7f7b6a948d03cb8`. The harness commits real fixture trees, but the particular causal change is not isolated. Preserve commit/lineage identity verification while investigating. [Issue #78](https://github.com/Aram164/LearningOS/issues/78).

## Integrity and preservation evidence actually obtained

Digest-verified hosted JUnit cases include 149 passing transaction/fault/gateway cases, 44 migration/project lifecycle cases, 53 structural-edit cases, 108 temporary/runtime cases, 44 efficiency/cache cases and 89 selected contract/format/release-receipt cases. The selected groups have no skipped or failed cases; they do not override the six failures or missing population gate. UI production contract checks pass against this exact Core. Stored format remains v62 and manifest v16; no final pair receipt exists to certify the built artifact.

Independent **read-only** source verification rechecked the existing experimental migration `transaction-20261029-041530-001`: receipt schema/marker/reviewed-plan identity, all 12 recorded write hashes (including deletion), retained before-image hashes, 12 unchanged source/absence pins, all 93 mapped scalar values, the original parsed workspace body prefix and exactly three revision increments. Git tree inventories prove **2,084 tracked learner/transaction files unchanged from accepted Stage 4C** across curriculum, knowledge, sources, records, projects, operations, active workspaces and coordination. All seven protected original-checkout hashes still match. No migration was rerun.

Evidence is retained beside the experimental checkout under `../stage8/`: `watch.log`, `run-final.json`, `checkout-verification.json`, `artifacts-final.json`, all five `junit-*.zip`, `junit-verification.json`, `hosted-test-cases.json`, `ui-check.log`, `witness-0.log`, `witness-1.log`, `rest-0.log`, `preservation-verification.json` and its read-only verifier. The three failed-job logs retain complete errors and diffs. Issues were searched for duplicates before filing/updating.

## Remaining limitations and stop condition

Stage 8 is incomplete and failed for this exact pair. The population witness shards, final gate, final warning-baseline/static results and pair artifact/receipt must be obtained in a later authorized repaired-pair run before acceptance. No live installation or material-stress acceptance is claimed; no production migration, merge or original learner-vault write occurred. Source commits stay pinned; only this outcome and observed-problem reporting notes are pending locally, uncommitted and unpushed. The original learner checkout remains untouched.

A temporary automatic-approval usage limit interrupted a status read; it later permitted the required final metadata, failed-job logs and JUnit retrieval. The final verdict uses completed-run evidence, not that earlier interruption. No further optimization or implementation is authorized by this verification report.

## Authorized repair continuation

Aram subsequently requested fixing all failures and completing readiness. The repair plan is [Stage 8 repair](2026-10-29-agility-stage8-repair.md). Historical contract inputs reproduce all four old scenario recordings exactly; current inputs change only the AI request snapshot and real fixture commit. The four selected recordings are refreshed without any broad normalization. The hashing audit observes actual material reads and proves one read per build plus re-observation and dossier invalidation on a later read. The five backup counts are 491, and the newly exposed bootstrap catalogue count is 21 queries / 48 commands. Production behavior and the UI revision are unchanged.

Focused evidence: all 28 audit/efficiency tests, all 21 affected AI-delivery/restamp scenario cases, and all 38 independent procedure transcripts pass. Every transcript retains its existing audit/render checks. Ruff, maintained mypy, system map and architecture/reachability checks pass. Full hosted acceptance must still run on the newly published exact pair; this initial failed run is never reused as acceptance. The final run, downloaded artifacts and independent verification are retained beside the experiment under `stage8-repair/`; its final outcome document is written after the run so the certified source pair can stay clean and unchanged.
