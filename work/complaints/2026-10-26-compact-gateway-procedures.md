# Compact gateway output broke executable procedures

While finishing PR #48, the review identified the failed exact-pair run at `cc16675`: [40274722194](https://github.com/Aram164/LearningOS/actions/runs/40274722194). `tests/test_procedures.py::test_every_transcript_passes` expected indented JSON but the gateway intentionally emitted compact JSON on pipes. The first-failure cutoff obscured the remaining migration surface.

Expected: executable procedures match the wire layout while retaining their decoded values, receipt checks and canonical-file witnesses. Independent per-document Scrut runs identified 59 gateway responses in 26 documents. A route-patch example additionally lacked the newly returned unfilled evidence scaffold. Three route-patch scenario recordings still pinned coarse evidence reads that the claim repair intentionally removes.

Reproduce with `pytest -q tests/test_procedures.py::test_every_transcript_passes` at `cc16675`, Scrut 0.5.0 and the paired UI checkout available. The repair updates expected output and retains the gateway audit checks. Acceptance requires all procedure/agent-entry tests and the final exact Core/UI pair to pass. Synthetic fixtures only; no live installation is involved.

GitHub issue: [#49](https://github.com/Aram164/LearningOS/issues/49). The exact PR-base recording recount is 581 layout-only, seven semantic changes and two new recordings (590 total), correcting the earlier intermediate-migration count.
