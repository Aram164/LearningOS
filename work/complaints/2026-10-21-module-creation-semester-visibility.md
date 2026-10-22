# Module creation does not complete visible semester onboarding

Task: Aram could not find BS/OS and ICOP in Modules and asked to exercise the
new creation mechanism.

Observed: `los inspect module-hu-betriebssysteme module-hu-icop` returned two
enrolled records with `semester: wise-2026`. The live Obsidian Modules view
showed only SoSe 2026 and AML/M2. The owning program record still declared
SoSe 2026 current; `ManifestStore.currentSemesterModules()` in the sibling UI
therefore excluded the two WiSe records. After Aram explicitly approved
making WiSe current, correcting that program record and regenerating made
both module buttons appear in the live UI. Neither module has units yet.

`module.create` correctly refuses these already-existing identities and is
scoped to creating a module and its source map. Its capability does not
change program semesters. The capability catalogue offers no program or
semester update command. The separately approved metadata correction is
recorded in `migration/reports/2026-10-21-current-semester-correction.md`;
it is not a gateway-created module or a full semester closeout.

Inference: creation can succeed while the ordinary Modules destination still
hides the module. The missing onboarding feedback and program mutation path
add operator work; keeping semester changes separate does preserve Aram's
ownership of the term boundary.

Smallest improvement to investigate: creation preflight should explain
whether the module will appear in the current-semester view, and point to a
reviewed program-semester operation. Preserve existing-identity refusal,
exact-byte review, snapshot/revision guards, receipts, and explicit semester
decisions; do not silently roll the semester forward.

Filed on 2026-10-21: [LearningOS #2](https://github.com/Aram164/LearningOS/issues/2),
with the observed records and UI behavior, reproduction, scope limits, and
acceptance criteria. The visibility correction is applied; the onboarding
capability gaps remain open in that issue.

