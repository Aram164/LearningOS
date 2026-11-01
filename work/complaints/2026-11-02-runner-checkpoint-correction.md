# Runner checkpoint can contradict the final outcome after a sync failure

Workflow: retain evidence of a committed runner step. Tested Core f2a93f4; the same reporting implementation is present on a38d07f. The new synthetic regression test_sync_failure_after_append_keeps_checkpoint_and_final_outcome_consistent injects one sync failure after a checkpoint append. The final row reports ARTIFACT_FAILED with its committed receipt, but the checkpoint still says ok. Expected: detached rows and append-only corrections preserve one coherent recovery history without erasing commitment. No lost or duplicated live write is claimed.

The bounded fix on codex/stable-release-finish-20261102 reconciles recorded rows, refuses finalization on persistent storage failure, and invalidates reads if their epoch cannot close. Existing reports remain retained; no automatic pruning or Task IR restoration is added. Acceptance: one-shot sync failure reconciles, persistent failure remains unfinalized, committed receipts cannot be erased, and exact-pair hosted gates pass. Local evidence: evidence/finish-reporting-red.log, finish-reporting-green.log and finish-reporting-recovery.log in this campaign; 105 owning tests plus seven targeted recovery cases passed. External evidence is not assumed published. At filing the repair is locally checked, not yet hosted-accepted or landed.

Duplicate search found #65 (retired Task IR persistence) and #88 (report-path policy), which describe distinct problems. GitHub connector creation returned 403; filing uses the existing authenticated GitHub CLI.

Issue: https://github.com/Aram164/LearningOS/issues/92
