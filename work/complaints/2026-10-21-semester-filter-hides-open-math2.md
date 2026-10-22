# The module list hides open courses from earlier semesters

Aram's correction, verbatim:

> i dont think modules appearing on the modue list should be semester dependent i wanted math2 i.e statistik and analysis to stay

Observed on 2026-10-21 with Core `480869d24bd3359c122017e1b5f6bdc2e31b3525`
and UI `ad9541744fb9324843c9fcb8fc20e6bfe9d0c16d`: the live Obsidian Modules
page showed WiSe 2026/27 and only BS and ICOP. Core still reported Math2
(`module-hu-m2-statistik-analysis`) and AML enrolled under SoSe 2026. Their
records had not been closed or removed. Changing the current semester hid
them because the UI's `ManifestStore.currentSemesterModules()` filtered by
semester; Home's Continue elsewhere used the same selector.

This is a UI presentation defect under the clarified intent. The earlier
semester-setting correction exposed OS and ICOP but did not satisfy keeping
all open academic modules visible. Core issue #2 records the earlier
onboarding diagnosis; its proposed visibility warning does not replace the
UI correction required here.

The scoped UI change uses `openAcademicModules()` for both surfaces, removes
semester-specific list copy, and retains the existing exclusion of completed,
dropped and archived courses. Semester facts, exam records and study work are
preserved. UI `DESIGN.md` records that semester is context rather than a gate
on module visibility.

Proof: the fixture regression keeps earlier-semester Statistics & Analysis
alongside Operating Systems, Combinatorial Optimization and Advanced ML. It
checks Home continuation, course detail and Back navigation. The store test
also changes or removes the current-semester record without changing the
visible open courses. The complete `npm run check` passed, including contract,
installer, UI, source-graph and deterministic-build checks. Its local output
is `/private/tmp/los-cross-semester-ui-check.log`.

Acceptance: in the live Modules list, Math2, AML, BS and ICOP appear together,
and opening Math2 still reaches its separate Statistik and Analysis units.
Installation and live verification are tracked separately from fixture proof.

Filed: [UI #2](https://github.com/Aram164/learningos-obsidian-ui/issues/2),
with the pre-change live observation, clarified intent, fixture evidence and
acceptance criteria. Core issue #2 remains a separate onboarding-capability
finding; the UI fix does not depend on a semester-setting change.
