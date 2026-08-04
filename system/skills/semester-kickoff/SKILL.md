---
name: semester-kickoff
description: Bootstrap a new semester's planning system from Aram's proven architecture — brain files, domain-based plan folders, step-ID prefixes, and wiring into the degree-level knowledge system (Masters-Planning). Use at the start of a semester or when asked to "set up the new semester".
---

# Semester Kickoff (~1 h)

Spec: `Masters-Planning/templates/SEMESTER-KICKOFF-Template.md`. Ask Aram first: module list (verified in Moses/AGNES — never from old notes), exam forms/dates if known, workload constraints.

## Steps

1. **Skeleton:** semester folder with `HANDOFF.md` (no live state!), `<SEM>-STATUS.md` (dashboard, §0.5 Open Loops, dependency map, progress tracker, priority rules, neglect tracker, load planner, key dates), `SESSION-LOG.md` (separate from day 1), `CHAT-DIVISION.md`, `LEARNING-RESOURCES.md`, `Plans/<domain>/<module>/` + `Plans/WIRING.md` + `Plans/README.md`, `tools/` (copy `check_system.py`).
2. **Step-ID prefixes** per module (unique in semester); module IDs `<MODULE>-<Sem>` globally.
3. **Wire backwards (the degree step):** for each module, read its incoming edges in `Masters-Planning/DEGREE-WIRING.md` §2; open the module plan with the prerequisite Module Cards + CONCEPT-INDEX rows ("known content — revise, don't re-learn"); add "revise via" pointers to Mini Plans for indexed concepts.
4. **Register** the semester in `Masters-Planning/MASTERS-ARCHITECTURE.md` §8.
5. **Rituals active from day 1:** session-log append; Open Loops checked every session; tier flow (material→tier 1, planning→tier 2, studying→tier-3 units via `lecture-unit-builder`); exam dates screenshot-verified with Rücktritt deadlines in Key Dates.
6. **Validate:** `python3 Masters-Planning/tools/check_system.py`.

## Guardrails

Never invent module data (Ground-Truth rule). Never copy live state into HANDOFF (it drifts). Keep the old semester system frozen — link to it, don't edit it.
