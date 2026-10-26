# Claim scaffolds can create immediately stale judgments

During the authorized overnight audit repair, the `c09fb16` source and regression fixtures confirmed this family. Scaffolds emitted coarse owner/ledger reads and plan imports failed to account for the committed lineage revision. Generate digest-only drafts and advance explicit lineage reads consistently.

Code: app/claim_admission.py; app/handlers/plan.py under `tools/learning_os/`. Regression evidence: test_phaseB_prospective_lineage.py under `tests/`; the task's retained red/green logs distinguish original and repaired behavior. Synthetic fixtures only; learner data is unchanged.

The proposed acceptance is the corresponding regressions passing while existing mutation, evidence, scope, and recovery guards continue to pass.

GitHub publication is blocked: automatic approval review rejected issue creation because it would export private repository findings without explicit user authorization. No issue exists. The ready-to-file body and full local evidence are retained in the overnight-audit-fixes-2026-10-25 workbench.
