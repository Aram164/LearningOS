# Legacy route identities disappear during plan edits and rigor checks

During the authorized overnight audit repair, the `c09fb16` source and regression fixtures confirmed this family. Resolve deterministic identities in route indexes, collision checks, update/removal, and validation. Persist the identity of a changed legacy route before editing its identity inputs.

Code: domain/plan_import.py; derive/validation/plan_rigor.py under `tools/learning_os/`. Regression evidence: test_unit_plan_revision.py; test_plan_rigor.py under `tests/`; the task's retained red/green logs distinguish original and repaired behavior. Synthetic fixtures only; learner data is unchanged.

The proposed acceptance is the corresponding regressions passing while existing mutation, evidence, scope, and recovery guards continue to pass.

GitHub issue: [Legacy route identities disappear during plan edits and rigor checks](https://github.com/Aram164/LearningOS/issues/44). Publication was explicitly approved by Aram on 2026-10-26. The repair is on `codex/overnight-audit-fixes-20261025`; hosted CI must verify the final Core/UI pair before release acceptance.
