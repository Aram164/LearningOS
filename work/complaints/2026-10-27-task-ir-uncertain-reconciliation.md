# Task IR cannot reconcile an already committed write after its response is lost

- Workflow: requested P1 recovery-boundary assessment using a disposable synthetic material fixture.
- Tested state: Core `3541789` plus the isolated evidence/checksum repair; the apply recovery branches are unchanged. macOS/Python 3.14.4; no actual learner data changed.
- Expected: retain the original request, idempotency key and sealed envelope; reconcile the existing transaction and report its receipt without a fresh write.
- Observed: wrap `default_seal_submit` so it completes a real synthetic route patch and then raises `TimeoutError`. `apply_task` reports `uncertain`; calling it again returns `uncertain` without receipt reconciliation. There is exactly one receipt and one adapter dispatch. Calling the underlying seal submission with the original check, payload, key and request ID reports `replayed: true`, the same transaction ID, and still one receipt.
- Proof: `../assessment_probe.py` and `../assessment-integration.log` in the workbench. Output: first/second status `uncertain`, dispatch count 1, receipt count 1, underlying exact replay true, same transaction true. Code inspection also shows persisted `dispatched` is returned without reconciliation after an abrupt process exit; that abrupt-exit case has not been executed here.
- Impact: the adapter safely avoids blind redispatch but strands recoverable committed outcomes. Its current test proves non-redispatch, not completed recovery.
- Smallest improvement: use the existing receipt/retained-envelope recovery mechanism for uncertain/dispatched states, preserve exact identity, and define explicit operator action when evidence cannot establish an outcome. No second journal or resealing protocol.
- Acceptance: adapter-level lost-response, abrupt-exit, missing-receipt, conflicting-intent and exact-replay cases prove one transaction, one receipt, preserved identities, and truthful unresolved outcomes. This is deferred acceptance work.
- GitHub: https://github.com/Aram164/LearningOS/issues/68

- Acceptance follow-up: repaired in the separate P1 acceptance increment. The candidate Task IR suite passed 73 cases, with an independent review reporting no unresolved blockers. Final head/pair/hosted evidence is retained in `LearningOS/workbench/task-ir-p1-experiment/P1-ACCEPTANCE-REPORT.md`; hosted acceptance is not inferred from the local run.
