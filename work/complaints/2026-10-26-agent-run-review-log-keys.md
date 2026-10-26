# [P1] Experimental runner reuses one default idempotency key for every log

Affected workflow: experimental agent operator plans.

Two `kind: log` steps without `key`, containing different text, produced first-step success and second-step `IDEMPOTENCY_CONFLICT` in a real synthetic fixture. `_expand_log_step` supplies the constant `agent-run` for every missing key. The collision persists across plans. For identical text, the underlying exact-replay contract means a separately intended later capture would replay the earlier receipt instead of creating a new capture (inference from the verified key generation and sealing contract).

Expected: each independently intended write has its own stable retry identity; retrying the same plan preserves that identity. Require explicit per-write keys, or derive them from an explicit persistent plan identity plus step id. Do not generate fresh keys on each retry. Acceptance: two distinct keyless writes either refuse during whole-plan validation before any mutation, or both commit under distinct stable identities; rerunning the same plan replays both.

Environment and limits: review of the uncommitted `experiment/agent-operator-readiness-20261026` worktree on base `dad2d8f1f0843742b6b003db8228333650fc6038`, 2026-10-26. Tool SHA-256 `e5421c0a91b06c23bb21ff63e1542fbdd5c38463c31099847640d7cda1de2720`. The nine supplied focused tests pass; the write reproductions used disposable synthetic fixtures. No live learner write, source repair, commit, push, merge or full local gate was performed. Retained local evidence: `LearningOS/workbench/agent-operator-readiness-2026-10-26/review/reproduce.py` and `review/results.json`; affected code `tools/agent_run.py:273`.

Issue: https://github.com/Aram164/LearningOS/issues/50

## Local repair verified — 2026-10-26

Complete-plan validation now requires a unique explicit key on every log before any execution. Real fixture tests prove two independent logs commit, exact plan replay creates no extra receipts, and a changed intent still receives IDEMPOTENCY_CONFLICT.

38 runner checks and 102 workflow/architecture checks passed. Full hosted CI remains pending. Repair evidence: `LearningOS/workbench/agent-operator-readiness-2026-10-26/fixes/REPORT.md`; source SHA-256 `3c11a770c4a89c2d73b7d8947e6d11f842f30de01088fc1e9e519cb19a4bd44d`. Outcome issue: https://github.com/Aram164/LearningOS/issues/50
