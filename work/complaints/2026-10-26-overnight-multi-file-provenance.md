# Relative material paths and multi-file absence scopes fail provenance

During the authorized overnight audit repair, the `c09fb16` source and regression fixtures confirmed this family. Match exact source-relative paths; retain unique-basename behavior for bare filenames. Check every absence-scope clause against its own inspected material/pages. Ambiguous basenames and unread pages still refuse.

Code: derive/material_synthesis.py under `tools/learning_os/`. Regression evidence: test_material_slices.py under `tests/`; the task's retained red/green logs distinguish original and repaired behavior. Synthetic fixtures only; learner data is unchanged.

The proposed acceptance is the corresponding regressions passing while existing mutation, evidence, scope, and recovery guards continue to pass.

GitHub publication is blocked: automatic approval review rejected issue creation because it would export private repository findings without explicit user authorization. No issue exists. The ready-to-file body and full local evidence are retained in the overnight-audit-fixes-2026-10-25 workbench.
