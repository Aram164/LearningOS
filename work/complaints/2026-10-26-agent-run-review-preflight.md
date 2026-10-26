# [P2] Runner treats an invalid validation invocation as a clean preflight

Affected workflow: experimental agent operator plans.

`executor(["validate", "--compact"], root)` exits 2 with empty stdout and `unrecognized arguments: --compact`. `los validate --help` exposes only `--online`; compact is a flag on `tools/validate.py`, not this CLI verb. The runner discards the exit code and stderr, caches an empty list and executes the step. A harmless preflighted inspect step demonstrated the continued execution. The gateway remains the canonical-write guard; this finding does not establish a guard bypass.

Expected: use the supported validation invocation and treat failure to obtain a trustworthy validation result as a diagnostic failure, never a clean result. Preserve errors without a path too. Acceptance: integration cases for real validation errors, unrelated versus scoped diagnostics, validator usage/environment failure, and pathless errors; no write proceeds on the basis of a failed preflight. Cached diagnostics must also have a defined invalidation rule after canonical state changes.

Environment and limits: review of the uncommitted `experiment/agent-operator-readiness-20261026` worktree on base `dad2d8f1f0843742b6b003db8228333650fc6038`, 2026-10-26. Tool SHA-256 `e5421c0a91b06c23bb21ff63e1542fbdd5c38463c31099847640d7cda1de2720`. The nine supplied focused tests pass; the write reproductions used disposable synthetic fixtures. No live learner write, source repair, commit, push, merge or full local gate was performed. Retained local evidence: `LearningOS/workbench/agent-operator-readiness-2026-10-26/review/reproduce.py` and `review/results.json`; affected code `tools/agent_run.py:353`.

Issue: https://github.com/Aram164/LearningOS/issues/52

## Local repair verified — 2026-10-26

Each opted-in preflight now calls the supported validate verb afresh. Nonzero environment/usage failures, missing or inconsistent summaries, and pathless validation errors block execution. Scope classification retains all errors. Real fixture tests prove an unrelated defect prevents sealing and a second preflight runs again after the first write; gateway validation remains enabled.

38 runner checks and 102 workflow/architecture checks passed. Full hosted CI remains pending. Repair evidence: `LearningOS/workbench/agent-operator-readiness-2026-10-26/fixes/REPORT.md`; source SHA-256 `3c11a770c4a89c2d73b7d8947e6d11f842f30de01088fc1e9e519cb19a4bd44d`. Outcome issue: https://github.com/Aram164/LearningOS/issues/52
