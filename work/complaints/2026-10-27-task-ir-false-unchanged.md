# Task IR refusal text can spoof a successful unchanged result

- Workflow: independent P1 acceptance review of route-patch preview classification.
- Tested state: Core `d707aaa` and the acceptance candidate, macOS/Python 3.14.4; no real learner data changed.
- Expected: an unknown unit must refuse; only verified set-like no-op evidence may produce `unchanged`.
- Observed: the reviewer used the unknown unit ID `unit-no material changes to apply` with a real synthetic route ID. The sealer's unknown-unit error included that text, so the adapter's substring check returned `unchanged` with success semantics. There was no valid scoped operation.
- Smallest repair: remove prose-based success classification. Run the existing explicit check path to obtain its structured write/delete lists; derive a route-patch no-op only from an admitted successful empty proposal. Retain the original check/seal/gateway mechanism, without generalizing no-op behavior to creates or appends.
- Acceptance evidence: `tests/test_task_ir.py::test_unknown_unit_cannot_spoof_an_unchanged_result_through_error_text` asserts refusal, unchanged canonical fingerprint and zero receipts; the legitimate unchanged-route test still passes. Final full-pair results are retained in the workbench acceptance report.
- GitHub: https://github.com/Aram164/LearningOS/issues/70
