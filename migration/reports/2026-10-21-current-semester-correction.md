# Current-semester correction for BS and ICOP

Aram approved this exact scope on 2026-10-21: "Yes, make WiSe 2026/27 current",
in response to making that semester current while retaining the AML/M2 exam
records and existing study work unchanged.

The owning record is `curriculum/programs/program-bachelors.yaml`. SoSe 2026
is now `previous`; WiSe 2026/27 (`semester-wise-2026`) is `current`. Its short
form matches the existing modules' `semester: wise-2026` values. The Modules
view filters through `ManifestStore.currentSemesterModules()` in the sibling
UI, so the old current-semester record excluded both newly enrolled modules.

This is an explicitly approved program-metadata correction, not a completed
WORKFLOWS section 24 semester closeout. No module outcomes, registrations,
grades, workspaces, notes, source maps, or study maps were changed. The
capability catalogue has no program/semester mutation capability; this
authored configuration edit has no gateway transaction receipt. This report
records its authorization and scope rather than claiming a governed creation.

The existing module identities were preserved. `module.create` was exercised
separately with their actual creation packages; the live existing destinations
refused creation. Full probe outputs are retained under
`LearningOS/workbench/module-creation-probe-2026-10-21/`. The sibling UI's
installed code already supported this semester selection; no UI installation
or code change was needed.

Verification observed in the live Obsidian `repository` vault: Modules now
shows `WiSe 2026/27`, `2 enrolled modules`, and buttons for Betriebssysteme
(BS) and Introduction to Combinatorial Optimization (ICOP). Each has `0 units`.
Canonical validation reports zero errors and 1462 existing warnings, with no
new warning signature. The creation capability's focused suite passed all
16 tests. Separate findings about semester visibility and an incomplete-copy
preflight are retained in the two dated `work/complaints/` notes.

The real-package probe completed successfully for both modules on a disposable
copy of Core commit `480869d24bd3`. Preflight named exactly the module record
and source map, application wrote those two files with a `module.create`
receipt and artifact revision 1, an identical retry replayed the same
transaction, and a new creation check for the existing identity refused.
Created records matched the live records semantically; SHA-256 checks proved
the four live module/source-map files stayed byte-identical throughout.
`summary.json`, both copied receipts, and each check/apply/replay output are
retained in the probe directory. The copied receipts belong to that disposable
repository, not the live vault's transaction history.

Assessment: the creation primitive behaves safely in these checks. Semester
onboarding remains incomplete: creation does not warn that a module is outside
the current semester's visible list, and there is no governed program-semester
update operation. An uninitialized disposable archive also exposed a preflight
success followed by a safe apply refusal; the complaint records the precise
setup limitation. No Core/UI implementation was changed to address those gaps.
