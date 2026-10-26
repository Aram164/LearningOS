# Deletion rows can falsely fail created-directory contiguity

During the authorized overnight audit repair, the `c09fb16` source and regression fixtures confirmed this family. Apply forward-directory contiguity to file writes, preserving the independent membership, forward-write, and pre-state checks. An absent deletion below another newly created directory now admits correctly.

Code: store/transactions.py under `tools/learning_os/`. Regression evidence: test_transaction_faults.py under `tests/`; the task's retained red/green logs distinguish original and repaired behavior. Synthetic fixtures only; learner data is unchanged.

The proposed acceptance is the corresponding regressions passing while existing mutation, evidence, scope, and recovery guards continue to pass.

GitHub issue: [Deletion rows can falsely fail created-directory contiguity](https://github.com/Aram164/LearningOS/issues/42). Publication was explicitly approved by Aram on 2026-10-26. The repair is on `codex/overnight-audit-fixes-20261025`; hosted CI must verify the final Core/UI pair before release acceptance.
