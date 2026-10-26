# General note writes alter frozen input bytes or allow invalid answers

During the authorized overnight audit repair, the `c09fb16` source and regression fixtures confirmed this family. Preserve approved frozen bytes and the raw body suffix during metadata changes and succession. Reject missing/self answer-note references through revision and general reference validation.

Code: app/handlers/notes.py; derive/validation/references.py under `tools/learning_os/`. Regression evidence: test_synthesis_analysis_refs.py; test_note_create.py under `tests/`; the task's retained red/green logs distinguish original and repaired behavior. Synthetic fixtures only; learner data is unchanged.

The proposed acceptance is the corresponding regressions passing while existing mutation, evidence, scope, and recovery guards continue to pass.

GitHub issue: [General note writes alter frozen input bytes or allow invalid answers](https://github.com/Aram164/LearningOS/issues/41). Publication was explicitly approved by Aram on 2026-10-26. The repair is on `codex/overnight-audit-fixes-20261025`; hosted CI must verify the final Core/UI pair before release acceptance.
