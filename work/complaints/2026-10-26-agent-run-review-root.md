# [P2] Runner root selection is not passed to the CLI execution boundary

Affected workflow: experimental agent operator plans.

Invoking the real runner with `--root` pointing to a standard synthetic fixture containing `note-demo`, and asking `inspect note-demo`, returned `record not found`. The same fixture is built by `tests/conftest.py::build_mini_repo`. The runner changes cwd but parses argv without setting the namespace root. `adapters/cli.py::invoke` defaults to the executing source tree, not cwd. A fixture with a copied implementation tree masks the defect. The log subprocess additionally assumes the selected data root contains `tools/seal_envelope.py` and does not pass its `--root` explicitly.

Expected: selected data root controls capability discovery, every read, validation, sealing and readiness. Keep executable code location separate from selected data location. Acceptance: use the ordinary fixture without copying implementation code; prove reads and supported log writes reach only that root. No live canonical write was attempted in this review.

Environment and limits: review of the uncommitted `experiment/agent-operator-readiness-20261026` worktree on base `dad2d8f1f0843742b6b003db8228333650fc6038`, 2026-10-26. Tool SHA-256 `e5421c0a91b06c23bb21ff63e1542fbdd5c38463c31099847640d7cda1de2720`. The nine supplied focused tests pass; the write reproductions used disposable synthetic fixtures. No live learner write, source repair, commit, push, merge or full local gate was performed. Retained local evidence: `LearningOS/workbench/agent-operator-readiness-2026-10-26/review/reproduce.py` and `review/results.json`; affected code `tools/agent_run.py:254`.

Issue: https://github.com/Aram164/LearningOS/issues/53

## Local repair verified — 2026-10-26

Executing tools are taken from the runner implementation directory; the selected data root is passed explicitly to every CLI and seal invocation. Per-step root overrides are refused before execution. Real subprocess reads, inbox captures, and stage notes work on ordinary fixtures without copied implementation code.

38 runner checks and 102 workflow/architecture checks passed. Full hosted CI remains pending. Repair evidence: `LearningOS/workbench/agent-operator-readiness-2026-10-26/fixes/REPORT.md`; source SHA-256 `3c11a770c4a89c2d73b7d8947e6d11f842f30de01088fc1e9e519cb19a4bd44d`. Outcome issue: https://github.com/Aram164/LearningOS/issues/53

## Parsed-argument boundary follow-up

Argparse accepted `--roo` and `--r` as root flags, escaping the original exact-token filter. Two-fixture regressions demonstrated that the old runner could read the other root. Execution now verifies the parsed, resolved root before dispatch. Session identity and writer classification are also enforced at the parsed-command boundary, and user plans cannot invoke the private seal marker. Evidence: `LearningOS/workbench/agent-operator-readiness-2026-10-26/followup/parsed-boundaries-red.log` and `session-boundary-red.log`; the expanded runner suite passes 63 cases.
