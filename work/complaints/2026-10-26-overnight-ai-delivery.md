# AI delivery loses session ledger files, failure provenance, and input guards

During the authorized overnight audit repair, the `c09fb16` source and regression fixtures confirmed this family. Use standard transaction touched attribution; propagate post-commit, publication-uncertain, projection, and incomplete-rollback failures; require transcription artifacts at validation; bind continuations to unchanged target/material state while allowing unrelated edits.

Code: app/ai_actions/service.py; app/commit.py under `tools/learning_os/`. Regression evidence: test_ai_actions.py; test_material_slices.py under `tests/`; the task's retained red/green logs distinguish original and repaired behavior. Synthetic fixtures only; learner data is unchanged.

The proposed acceptance is the corresponding regressions passing while existing mutation, evidence, scope, and recovery guards continue to pass.

GitHub publication is blocked: automatic approval review rejected issue creation because it would export private repository findings without explicit user authorization. No issue exists. The ready-to-file body and full local evidence are retained in the overnight-audit-fixes-2026-10-25 workbench.
