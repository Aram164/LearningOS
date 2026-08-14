---
name: lecture-unit-builder
description: Build one lecture unit — knowledge map, complete material menu, and the durable reference/exercise-bank/mock-exam notes — for a university lecture, following Learning OS v3 (WORKFLOWS §23). Use when asked to "build the unit for lecture X", "process lecture NN", or create study notes for a specific lecture.
---

# Lecture Unit Builder (Learning OS v3)

Implements `system/WORKFLOWS.md` §23 for lecture `<NN>` of a module. Read §23 and
`system/CLAUDE.md` (the operating contract) before writing anything; every new or
revised module plan additionally follows `system/PLAN-CREATION-SOP.md`, whose
coverage audit, no-write preflight, snapshot guard and acceptance gates are
mandatory. This file owns only what is specific to the skill — the procedure
lives in §23 and must not be restated here, because a restated procedure is what
went stale last time.

## What this skill must get right

**Scope comes from the deck, never from a reading list.** Read the actual slides
under `LearningOS/materials/` (resolve via the module's source record /
`material://`). Never scope from textbook chapter titles or keyword-matched
readings. Documented traps: ISLP Ch 7 ≠ AML L04; AML L07 has **no** SVM. Match
readings to the lecture's actual scope plus its prior-lecture prerequisites.

**Check prior coverage before creating anything.** Search
`generated/concept-index.md` (rebuild if stale) and the `knowledge/concepts.yaml`
aliases — German terms work. A re-covered concept earns "revise via `<existing
note>`", not new study steps.

**The unit owns a knowledge map, not a schedule.** Its nodes name the ideas
taught and its `builds_on` edges expose prerequisite structure. Rich source
routes connect materials to those nodes carrying format, angle, covered nodes,
depth, scope status and exact locator. Priority in the source map is not an
order of study.

**Choose before sequencing.** Record only Aram's actual choices in
`source_selections` (`los unit-source-selection`). A `study-map.yaml` is optional
and personal — create one only when ordered progress tracking is wanted, and
never let it replace or truncate the complete menu.

**Three durable notes, one purpose each** (WORKFLOWS §3), under
`knowledge/notes/<domain>/` with full frontmatter (id `note-<module>-l<NN>-…`,
type note, role, concepts, sources, `contexts:` the exam-prep workspace):
lecture reference → `role: reference`, every claim traceable to slides or a
cited source; drills → `role: exercise-bank`, solved + unsolved, source-tagged,
clean Q/A separation; self-test → `role: mock-exam`, with solutions, difficulty
≥ the real exam. Only their stable IDs go on the unit.

**Register what the lecture introduced:** concepts (§4, English label + German
aliases), relations (§5), sources (§6a).

**Close the loop:** `python tools/validate.py` to 0 errors, 0 warnings, then
`python tools/generate.py`, then diff-review against the coverage audit.

## Quality bar

Verified against slides, not memory. If the deck is missing or unreadable, stop
and say so — never fabricate scope. Preserve Aram's own reasoning verbatim
wherever it enters a note (CLAUDE.md §3, §6). Never declare mastery: the
exercise bank and mock exam are the evidence trail, and their absence is
reported as absence.
