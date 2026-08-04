---
name: lecture-unit-builder
description: Build a complete tier-3 lecture unit (Ultimate Reference + Mini Plan + Exercise Bank + Mock Exam) for a university lecture, following Aram's degree-wide knowledge architecture. Use when asked to "build the unit for lecture X", "process lecture NN", or create study notes for a specific lecture.
---

# Lecture Unit Builder

Build one tier-3 unit for lecture `<NN>` of module `<MODULE-ID>` (e.g. `AML-SoSe26`). Format spec: `Masters-Planning/templates/LECTURE-UNIT-Template.md`. Requires the semester folder (`semestercontext/` or successor) connected.

## Procedure

1. **Scope first.** Read the actual lecture slides (only source of truth for scope). Read the module's source crosswalk row for lecture NN (📒🎥🧪 layers). Never scope from textbook chapter titles — lecture as taught wins (documented trap: ISLP Ch 7 ≠ AML L04; L07 has NO SVM).
2. **Check prior knowledge.** Search `Masters-Planning/CONCEPT-INDEX.md` for every major concept in the lecture. Re-covered concept → the Mini Plan gets "revise via `<existing unit>`", not new study steps.
3. **Create the folder** `lectNN <topic>/` in the module's notes location, then the 4 files per the template:
   - Ultimate Reference (anchor, with full frontmatter: id `<MODULE-ID>-LNN`, type unit, concepts slugs, depth full)
   - Mini Plan (the ONLY study script for this lecture — single-study-script rule; cite specific sections/videos from the crosswalk)
   - Exercise Bank (solved + unsolved, source-tagged, clean Q/A separation for later Anki export)
   - Mock Exam (with solutions, difficulty ≥ real exam)
4. **Wire it in (2 min, mandatory):** add/upgrade CONCEPT-INDEX rows (🟢); point the module plan's block table at the unit; cross-link Mini Plans both ways for revised concepts.
5. **Validate:** `python3 Masters-Planning/tools/check_system.py` — must be green.

## Quality bar

Verified against slides, not memory. Every claim in the Ultimate Reference traceable to slides or a cited source. If the lecture deck is missing/unreadable, stop and say so — never fabricate scope.
