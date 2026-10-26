# Relative material paths and multi-file absence scopes fail provenance

During the authorized overnight audit repair, the `c09fb16` source and regression fixtures confirmed this family. Match exact source-relative paths; retain unique-basename behavior for bare filenames. Check every absence-scope clause against its own inspected material/pages. Ambiguous basenames and unread pages still refuse.

Code: derive/material_synthesis.py under `tools/learning_os/`. Regression evidence: test_material_slices.py under `tests/`; the task's retained red/green logs distinguish original and repaired behavior. Synthetic fixtures only; learner data is unchanged.

The proposed acceptance is the corresponding regressions passing while existing mutation, evidence, scope, and recovery guards continue to pass.

GitHub issue: [Relative material paths and multi-file absence scopes fail provenance](https://github.com/Aram164/LearningOS/issues/46). Publication was explicitly approved by Aram on 2026-10-26. The repair is on `codex/overnight-audit-fixes-20261025`; hosted CI must verify the final Core/UI pair before release acceptance.
