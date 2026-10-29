# Brief context reparses its already-loaded repository

Observed during Stage 7 at Core `b723696`: all three `plan-edit-context unit-demo-l01 --brief` synthetic runs load the repository twice, while full/stage-focused context load once. Source: `app/handlers/materials.py::_unit_audit` calls `validate_unit_material_synthesis` without its existing `repo` argument despite already receiving the loaded repository. The source validator explicitly supports that argument and observes material bytes separately.

Expected: reuse the read's repository snapshot while retaining live material freshness checks. Smallest repair: pass that repository; prove the audit output is identical and changed material still becomes stale on a later call. Retained driver/raw measurements and owning regression tests bound the evidence. No production latency or token/cost claim is inferred; filing follows verification.

Verified repair: all three after profiles load once. The brief stdout hash matches every before sample byte for byte (5,795 bytes), and material changes/deletion still make the audit stale. The full and focused context outputs and material-open counts also remain unchanged. See the Stage 7 retained comparison/outcome; full hosted acceptance remains Stage 8.

Reported after duplicate search: [Core issue #75](https://github.com/Aram164/LearningOS/issues/75).
