# Single-unit revision: contradictory plan-contract versions

Task: improve existing ICOP material descriptions through `unit-plan-revise`.
Environment: Core `dad2d8f1f0843742b6b003db8228333650fc6038`, 2026-10-26.

Observed: `system/PLAN-CREATION-SOP.md`, Gate 3, says the package must
contain `plan_contract.version: 2` and describes the procedure as mandatory
for every new or revised plan. The compact single-unit example in
`system/procedures/revise-an-existing-plan.md` instead uses version 1.
Submitting the descriptive ICOP revision with version 2 to
`los unit-plan-revise unit-icop-l01-linear-programming --file REVISION.yaml --check`
returned `plan_contract.version must be 1 (see system/PLAN-CREATION-SOP.md)`.
No canonical files were written. Changing only that version to 1 passed this
contract check and reached the independent perimeter validation.

Impact: following the universal SOP instruction caused a rejected preflight;
the diagnostic referred back to the contradictory document. The refusal itself
preserved the contract and prevented any write.

Smallest improvement: clarify the version required by compact single-unit
revisions versus full module packages in Gate 3, and point the refusal at the
applicable distinction. Keep current schema validation and no-write preflight.
Acceptance: the documented compact unit example and full module example each
pass their respective contract check; a wrong version is still refused.

Evidence: external draft and review material are retained in
`LearningOS/workbench/icop-material-synthesis-2026-10-26/`. This observation
does not establish a defect in the version validator or authorize code changes.

Issue: [Single-unit revision: contradictory plan-contract versions](https://github.com/Aram164/LearningOS/issues/58).
