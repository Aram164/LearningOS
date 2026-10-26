# [P2] Cluster preview emits an unsupported expansion command

Affected workflow: experimental agent operator plans.

The real brief scan already returns ranked groups with member counts and samples. The runner emits `intelligence-scan --cluster CLUSTER_ID`, but the request schema and parser contain no `--cluster`. Executing the generated form exits 2 with `unrecognized arguments: --cluster example`. The preview discards the upstream `full_result` and omitted-result metadata. Its `bulk_template` contains only one goal placeholder, so it does not itself implement a bulk decision path.

Expected: preserve an executable route to the full result, and retain omitted counts so a brief page cannot appear exhaustive. If cluster selection is desired, expose it through the declared query contract before emitting that command. Acceptance: execute every emitted expansion against a real fixture, recover complete membership, and preserve explicit human decision/review requirements for any bulk action. Do not automatically close or reject learner decisions.

Environment and limits: review of the uncommitted `experiment/agent-operator-readiness-20261026` worktree on base `dad2d8f1f0843742b6b003db8228333650fc6038`, 2026-10-26. Tool SHA-256 `e5421c0a91b06c23bb21ff63e1542fbdd5c38463c31099847640d7cda1de2720`. The nine supplied focused tests pass; the write reproductions used disposable synthetic fixtures. No live learner write, source repair, commit, push, merge or full local gate was performed. Retained local evidence: `LearningOS/workbench/agent-operator-readiness-2026-10-26/review/reproduce.py` and `review/results.json`; affected code `tools/agent_run.py:209`.

Issue: https://github.com/Aram164/LearningOS/issues/55

## Local repair verified — 2026-10-26

Cluster mode requests the existing brief JSON query, retains totals/omission counts and emits a supported full-scan expand_argv plus a quoted command. The nonexistent --cluster command and misleading bulk template were removed. Real fixture tests execute the expansion and recover all seeded members; no learner decision action was added.

38 runner checks and 102 workflow/architecture checks passed. Full hosted CI remains pending. Repair evidence: `LearningOS/workbench/agent-operator-readiness-2026-10-26/fixes/REPORT.md`; source SHA-256 `3c11a770c4a89c2d73b7d8947e6d11f842f30de01088fc1e9e519cb19a4bd44d`. Outcome issue: https://github.com/Aram164/LearningOS/issues/55
