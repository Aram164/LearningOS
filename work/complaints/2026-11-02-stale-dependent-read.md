# Dependent reads can accept an old publication after authored state changes

Workflow: a runner read depends on a committed write. Tested Core f076adc; the same readiness code is present on a38d07f. The new synthetic test_dependency_readiness_rejects_unpublished_authored_changes captures a real gateway write, confirms readiness, edits a fixture note without republishing, and checks readiness again. Expected: historical receipt completion remains true but stale publication refuses a current dependent read. Observed: readiness returned true and the focused regression failed. No live learner record was edited.

Owner: tools/learning_os/app/projection_readiness.py::dependency_ready. Both observations skipped current-state verification. The bounded fix retains the cheap hint and fresh transaction authority, but uses the existing full current-state identity check at final readiness. Acceptance: unpublished drift refuses, historical receipt completion survives, and latest/later-known-write, forged-receipt, receipt-path and settlement tests pass, followed by exact-pair hosted acceptance. Evidence: evidence/finish-readiness-red.log and finish-readiness-green.log in this campaign. External evidence is not assumed published. The repair is not yet hosted-accepted or landed.

Duplicate search found #51 (an earlier false refusal after two dependent writes) and #63 (receipt-path confinement); this is a distinct false acceptance of stale state. GitHub connector creation returned 403; filing uses the existing authenticated GitHub CLI.

Issue: https://github.com/Aram164/LearningOS/issues/93
