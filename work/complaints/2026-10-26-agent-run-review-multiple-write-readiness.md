# [P2] Readiness blocks a read after two successful dependent writes

Affected workflow: experimental agent operator plans.

On a real synthetic fixture, write A committed, write B depended on A and committed, then an inspect step with `depends_on: [A, B]` returned retryable `NOT_READY` for A. Both writes and their receipts succeeded. The projection now describes B, so equality with A's `snapshot_after` cannot become true through waiting. The single-write control completed successfully.

Expected: define whether dependency means completion of prior effects or an exact historical snapshot. For completion semantics, support a later proven state that includes both effects without trusting arbitrary unequal hashes. If exact snapshots are intended, return a terminal conflict instead of encouraging retries forever. Acceptance: real two-write fixture, subsequent dependent read, replay after later writes, and concurrent intervening state changes have explicit tested outcomes; stale or unrelated projections still refuse.

Environment and limits: review of the uncommitted `experiment/agent-operator-readiness-20261026` worktree on base `dad2d8f1f0843742b6b003db8228333650fc6038`, 2026-10-26. Tool SHA-256 `e5421c0a91b06c23bb21ff63e1542fbdd5c38463c31099847640d7cda1de2720`. The nine supplied focused tests pass; the write reproductions used disposable synthetic fixtures. No live learner write, source repair, commit, push, merge or full local gate was performed. Retained local evidence: `LearningOS/workbench/agent-operator-readiness-2026-10-26/review/reproduce.py` and `review/results.json`; affected code `tools/agent_run.py:138`.

Issue: https://github.com/Aram164/LearningOS/issues/51

## Local repair verified — 2026-10-26

Dependencies now mean successful receipted completion. Gateway submissions check completion and retain their own current guards; dependent reads require a projection matching a successful known write. Real fixture tests cover two writes plus a dependent read, exact multi-write replay, and refusal/reload after an unknown later write. A write hint cannot exempt a read from readiness.

38 runner checks and 102 workflow/architecture checks passed. Full hosted CI remains pending. Repair evidence: `LearningOS/workbench/agent-operator-readiness-2026-10-26/fixes/REPORT.md`; source SHA-256 `3c11a770c4a89c2d73b7d8947e6d11f842f30de01088fc1e9e519cb19a4bd44d`. Outcome issue: https://github.com/Aram164/LearningOS/issues/51

## Follow-up: predecessor projection refusal

The previous repair accepted any known write snapshot. A and B had retained receipts but the projection still described A; writes_ready(root, [A, B], [A, B]) incorrectly returned ready. The follow-up restricts candidates to the latest required write's execution position or a later known completion. The predecessor probe fails against the retained before-source; B and a later C remain accepted. Evidence: `LearningOS/workbench/agent-operator-readiness-2026-10-26/followup/red.log`. Issue #51 remains the owning readiness report.
