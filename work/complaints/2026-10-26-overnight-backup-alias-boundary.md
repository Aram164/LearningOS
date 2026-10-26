# Unvalidated backup alias metadata can escape the restored alias layer

During the authorized overnight audit repair, the `c09fb16` source and regression fixtures confirmed this family. Validate every alias name/target and reject a symlinked alias directory before changing any link. Traversal, absolute targets, and symlink escapes refuse while external files remain intact.

Code: app/backup_manifest.py under `tools/learning_os/`. Regression evidence: test_c1e_backup_symlinked_subtree.py under `tests/`; the task's retained red/green logs distinguish original and repaired behavior. Synthetic fixtures only; learner data is unchanged.

The proposed acceptance is the corresponding regressions passing while existing mutation, evidence, scope, and recovery guards continue to pass.

GitHub issue: [Unvalidated backup alias metadata can escape the restored alias layer](https://github.com/Aram164/LearningOS/issues/38). Publication was explicitly approved by Aram on 2026-10-26. The repair is on `codex/overnight-audit-fixes-20261025`; hosted CI must verify the final Core/UI pair before release acceptance.
