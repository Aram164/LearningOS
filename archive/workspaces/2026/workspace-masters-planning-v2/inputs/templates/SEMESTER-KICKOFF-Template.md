---
id: semester-kickoff-template
type: template
status: live
---

# SEMESTER-KICKOFF — Template (~1 h, run at the start of every semester)

> Instantiates the proven SoSe-2026 architecture for a new semester. Source pattern: `semestercontext/` root + `Plans/README.md` (3-tier). Degree hooks: `MASTERS-ARCHITECTURE.md` §3.

## 1. Create the semester system

- [ ] New semester folder (own Cowork project), containing:
  - `HANDOFF.md` — who/what/architecture; **no live state** (SoSe-26 lesson: state in HANDOFF drifts)
  - `<SEM>-STATUS.md` — THE BRAIN: dashboard, § 0.5 Open Loops, dependency map, progress tracker (step IDs), priority rules, active periods, neglect tracker, load planner, key dates
  - `SESSION-LOG.md` — separate from STATUS from day 1 (KW-27 lesson)
  - `CHAT-DIVISION.md` — one chat per module/area, step-ID prefix each
  - `LEARNING-RESOURCES.md` — tier 1, the only inbox for new material
  - `Plans/<domain>/<module>/` layout + `Plans/WIRING.md` + `Plans/README.md`
  - `tools/check_links.py` (copy)
- [ ] Assign step-ID prefixes (unique within semester; module IDs `<MODULE>-<Sem>` globally).

## 2. Wire into the degree system (the extension beyond SoSe 26)

- [ ] For each module: read its **incoming edges** in `DEGREE-WIRING.md` → list prerequisite Module Cards + CONCEPT-INDEX rows at the top of the module plan ("known content — revise, don't re-learn").
- [ ] Module plan Mini Plans: for any lecture re-covering an indexed concept, add "revise via <unit>" instead of new study steps.
- [ ] Register the semester in `MASTERS-ARCHITECTURE.md` §5.
- [ ] Verify module facts fresh (Moses/AGNES) — never from old notes (Ground-Truth rule).

## 3. Rituals to carry over (proven SoSe 26)

- Append to SESSION-LOG after every session; STATUS holds live state only.
- § 0.5 Open Loops checked every session; single list, resolved items dated.
- Tier flow: new material → tier 1; module planning → tier 2; studying → tier-3 units (Ultimate Reference + Mini Plan + Exercise Bank + Mock Exam). Single-study-script rule.
- Exam dates screenshot-verified; Rücktritt/Anmeldung deadlines into Key Dates immediately.
- Archive, never delete; no redirect stubs — fix links.

## 4. Conventions from day 1 (v2)

- New tier-3 units from `templates/LECTURE-UNIT-Template.md` — anchor frontmatter at creation, index row at completion.
- Validate early: `python3 Masters-Planning/tools/check_system.py` after the folder skeleton stands.

## 5. At semester end

Run the promotion ritual — `MASTERS-ARCHITECTURE.md` §6 / skill `promotion-ritual` (freeze, Module Cards, CONCEPT-INDEX, DEGREE-WIRING, resource promotion, frontmatter, validator green).
