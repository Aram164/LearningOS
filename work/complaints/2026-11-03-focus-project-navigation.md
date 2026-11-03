# 2026-11-03 — Focus project entry and selected-area feedback disagree

**Status:** retained observation; GitHub filing blocked on 3 November 2026. Search of the owning UI repository found no matching unresolved report. The connected GitHub integration returned 403 `Resource not accessible by integration`; the alternate local GitHub account reports an invalid token, and the browser requires sign-in. No issue was created. The complete ready-to-file body is linked below; no credentials or sharing settings were changed.

**Task and exact step.** During the authorized live Focus visibility/navigation/order audit, step 02 selected a study area inside Learn; steps 19 and 20 activated the identically labelled Thesis & projects controls in the sidebar and Learn page.

**Observation and impact.** The page selected its study area while the corresponding sidebar area remained unselected. The sidebar project control opened the general Modules catalogue; Learn's project control opened one existing project module. The same label therefore required extra inspection to learn where it led. Expected: matching project entry labels have one predictable destination and persistent, accurate area feedback. The appropriate collection design is a proposal, not an observed fact.

**Evidence.** Audit O1–O2 and steps 02/19/20 (`LearningOS/workbench/focus-ux-audit-2026-11-03/AUDIT.md`); step 02 (`LearningOS/workbench/focus-ux-audit-2026-11-03/screenshots/02-learn.png`), step 19 (`LearningOS/workbench/focus-ux-audit-2026-11-03/screenshots/19-projects-sidebar-destination.png`), step 20 (`LearningOS/workbench/focus-ux-audit-2026-11-03/screenshots/20-projects-learn-destination.png`). Ready-to-file issue body (`LearningOS/workbench/focus-ux-audit-2026-11-03/issue-drafts/01-project-navigation.md`).

**Environment and limits.** Live Focus Light, Obsidian 1.15.0, desktop, observed 3 November 2026. Source context supplied by the primary auditor was UI `2bf4f69422767054fb40c5835546be3e7548b429` and Core `850d82fd4e3a3766e1afe942d8e85f991ed10de6`, clean before notes. Diagnostics step 23 (`LearningOS/workbench/focus-ux-audit-2026-11-03/screenshots/23-diagnostics.png`) reports a different UI build: these source revisions are not asserted as the installed runtime. Zero/multiple project cases and keyboard/current-state announcements were not tested live. No learner state changed.

**Value and safety preserved.** General module access and direct module entry are both useful and did not write data. The observed cost is ambiguous location and destination, not lost records or invalid canonical membership.

**Smallest investigation and acceptance.** Reuse existing navigation to unify project entry behavior and show the actual selected area. On a synthetic fixture, both labels must lead consistently; zero/one/multiple project cases must be explicit; keyboard/current-state cues must be accurate; complete curriculum reachability and guarded mutations must remain intact. Do not infer a new project data model from this complaint.

**Retention route.** [OPERATOR reporting](../../system/OPERATOR.md#report-observed-problems) and [complaints README](README.md) govern this retained evidence. Preserve the note and append the filed URL once access is restored. The Figma refinement is a design proposal and does not repair the installed UI.
