# Legacy route identities disappear during plan edits and rigor checks

During the authorized overnight audit repair, the `c09fb16` source and regression fixtures confirmed this family. Resolve deterministic identities in route indexes, collision checks, update/removal, and validation. Persist the identity of a changed legacy route before editing its identity inputs.

Code: domain/plan_import.py; derive/validation/plan_rigor.py under `tools/learning_os/`. Regression evidence: test_unit_plan_revision.py; test_plan_rigor.py under `tests/`; the task's retained red/green logs distinguish original and repaired behavior. Synthetic fixtures only; learner data is unchanged.

The proposed acceptance is the corresponding regressions passing while existing mutation, evidence, scope, and recovery guards continue to pass.

GitHub publication is blocked: automatic approval review rejected issue creation because it would export private repository findings without explicit user authorization. No issue exists. The ready-to-file body and full local evidence are retained in the overnight-audit-fixes-2026-10-25 workbench.
