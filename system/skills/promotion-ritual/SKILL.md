---
name: promotion-ritual
description: Run the end-of-semester promotion ritual for Aram's degree knowledge system — freeze the semester's operational layer and promote its knowledge layer into Masters-Planning (module cards, concept index, degree wiring). Use when asked to "close the semester", "run the promotion ritual", or after final exams.
---

# End-of-Semester Promotion Ritual (~2–3 h)

Spec: `Masters-Planning/MASTERS-ARCHITECTURE.md` §6. Requires the semester folder connected. Work module by module; confirm exam results with Aram before filling grades.

## Steps

1. **Freeze the operational layer.** Final SEMESTER-STATUS update ("semester closed", date); append closing SESSION-LOG entry; move superseded plans to `archive/` (never delete; no redirect stubs).
2. **Fill Module Cards** (`Masters-Planning/module-cards/<MODULE-ID>.md`, template in `templates/`): scope actually covered incl. deviations, artifact paths + completeness flags, exam artifacts, grade, fed-by/feeds wires, 3-line retrospective. Flip frontmatter `status: stub → live`.
3. **CONCEPT-INDEX:** walk every tier-3 unit folder; one row per worked concept not yet indexed; upgrade depth flags (⚪→🟡→🟢). Index points INTO units — never copy content.
4. **DEGREE-WIRING:** add module→module edges the semester revealed; extend the incoming-edges table for next semester's modules.
5. **Promote resources:** new entries in the semester's LEARNING-RESOURCES → matching `MASTERS-*-RESOURCES.md` axis file.
6. **Frontmatter:** every new unit anchor + reference doc carries the §3.1 schema (anchor-file rule: one block per unit).
7. **Validate:** `python3 Masters-Planning/tools/check_system.py` green + (if installed) `lychee --offline .`.
8. **Register:** update `MASTERS-ARCHITECTURE.md` §8 semester registry; log the ritual in MASTERS-STATUS §5.

## Guardrails

Never invent grades, dates, or scope — ask. Semester content files are read-only during this ritual except the freeze edits in step 1.
