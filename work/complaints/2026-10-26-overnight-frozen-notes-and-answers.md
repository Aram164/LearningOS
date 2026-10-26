# General note writes alter frozen input bytes or allow invalid answers

During the authorized overnight audit repair, the `c09fb16` source and regression fixtures confirmed this family. Preserve approved frozen bytes and the raw body suffix during metadata changes and succession. Reject missing/self answer-note references through revision and general reference validation.

Code: app/handlers/notes.py; derive/validation/references.py under `tools/learning_os/`. Regression evidence: test_synthesis_analysis_refs.py; test_note_create.py under `tests/`; the task's retained red/green logs distinguish original and repaired behavior. Synthetic fixtures only; learner data is unchanged.

The proposed acceptance is the corresponding regressions passing while existing mutation, evidence, scope, and recovery guards continue to pass.

GitHub publication is blocked: automatic approval review rejected issue creation because it would export private repository findings without explicit user authorization. No issue exists. The ready-to-file body and full local evidence are retained in the overnight-audit-fixes-2026-10-25 workbench.
