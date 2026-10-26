# Lineage impact, evidence tags, session identity, and quiet totals disagree

During the authorized overnight audit repair, the `c09fb16` source and regression fixtures confirmed this family. Use effective DAG statuses for impacts; exclude blocking claim IDs from evidence-cause tags; seal the named session into review envelopes; count and render the same visible brief groups.

Code: derive/semantics/lineage.py; derive/semantics/goals.py; app/gateway.py; app/handlers/reads.py under `tools/learning_os/`. Regression evidence: test_semantic_lineage.py; test_claim_status_audits.py; test_gateway_v2.py; test_intelligence_scan.py under `tests/`; the task's retained red/green logs distinguish original and repaired behavior. Synthetic fixtures only; learner data is unchanged.

The proposed acceptance is the corresponding regressions passing while existing mutation, evidence, scope, and recovery guards continue to pass.

GitHub publication is blocked: automatic approval review rejected issue creation because it would export private repository findings without explicit user authorization. No issue exists. The ready-to-file body and full local evidence are retained in the overnight-audit-fixes-2026-10-25 workbench.
