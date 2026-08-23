# Critique Points

> **What this file is.** A standing, append-only log of things Aram judges wrong,
> weak, or not-yet-rigorous-enough about Learning OS — raised when noticed,
> **resolved later, deliberately not now**. Its whole purpose is to let a
> critique be recorded and then *dropped* from working memory, so that noticing
> a defect never costs a detour.
>
> **What this file is not.** Not a decision record (those are `system/adr/`),
> not a dated review (`system/adr/*-review-*.md`), not a study deferral
> (`work/COORDINATION.md` owns those, and only those). A point here is an
> *unresolved judgment about the system itself*.

## Rules

1. **Append only.** New points go at the bottom with the next number. Never
   renumber, never delete — a point that turns out to be wrong is closed with
   `Status: withdrawn` and the reason, because the reasoning is the record.
2. **Do not act on an open point** unless Aram says so in that session. Adding
   evidence to an open point is always allowed; fixing it is not.
3. **The operator may sharpen, never soften.** Claude may add measurements,
   file references and counts under *Evidence* to make a point resolvable. It
   may not rewrite Aram's statement of the complaint, and may not argue the
   point away in place — a disagreement goes under *Operator note*, below the
   evidence, clearly marked.
4. **Closing a point requires Aram.** When closed, keep the original text and
   append `Status: resolved <date>` with what changed and where.
5. Each point carries: the complaint verbatim, *Evidence* (what is measurably
   true today), *Blast radius* (what would have to change), and *Status*.

---

## 1. Plan manipulation may not be standardized or well designed, and the plans themselves are not rigorous about source angle and exact locations

**Raised:** 2026-08-23 (Aram) · **Status:** open · **Do not act.**

> "i am not sure whether plan manipulation is standardized and as smart
> designed as possible. and the learning plans for different lectures are not
> highlighting the angle of each source at all. page numbers and exact chapter
> numbers are missing sometimes. so this must be much more rigorous."

Three complaints in one, kept together because they may share a cause:

1. **Plan manipulation** — is there one designed way to create and change a
   plan, and is it the *right* design, or is it several paths that merely
   happen to produce a valid file?
2. **Angle is not surfaced** — a learner reading a stage cannot see *why this
   source, from this angle* at a glance.
3. **Locators are not exact** — chapter numbers and page ranges are missing
   often enough that a stage does not tell you where to actually start reading.

### Evidence (measured 2026-08-23 across all 50 study maps, 2,268 resource rows)

- **Shape is standardized; content is not.** Every one of the 50 study maps
  carries `plan_template_version: 1`. So the template gate is real and it is
  holding — but it constrains *structure*, not whether a locator is usable.
- **Two authoring paths produce materially different plans.**
  `tools/assemble_lecture_study_maps.py` joins the unit knowledge map to the
  module source map, so every route's `angle` gets carried into the stage.
  Hand-authored and imported maps carry no angle at all. The split is clean:
  **27 of 50 units have an angle on every row; 23 have rows with none.** All of
  AMLS L01–L13, `unit-algo2-exam-prep` (60/60), `unit-python-intermediate-roadmap`
  (202/230), `unit-m2-analysis-exam-prep` (125/135) and every `*-exam-prep` unit
  are in the second group. **690 of 2,268 rows (30%) carry no angle.**
- **Where the angle does exist, it is not a field.** The assembler concatenates
  it onto the end of `locator` after an em dash. Nothing downstream can render
  "angle" as its own thing, sort by it, or check that it is present —
  the 30% figure above had to be measured by string-searching for `" — "`,
  which is itself the defect.
- **Locators are vague at scale.** **1,904 of 2,268 locator heads (84%)**
  contain no page, `pp.`, or `S.` marker. Representative live rows:
  `"Chapter 9"`, `"Chapter 2 selections"`, `"Estimation selections"`,
  `"Descriptive-statistics selections"`, `"Local solved bank; estimation questions"`.
  "Chapter 9" of a 700-page book is not a locator, it is a direction.

### Blast radius

- `system/schema/module-source-map.schema.json` — `angle` is required on a rich
  route but `locator` is a free string with no exactness requirement, and the
  legacy plain-string route form is still legal.
- `system/schema/study-map.schema.json` + `tools/assemble_lecture_study_maps.py`
  — a first-class `angle` field on a resource row, instead of concatenation.
- `system/PLAN-CREATION-SOP.md` — would have to say what makes a locator
  acceptable, and the validator would have to enforce it.
- Every hand-authored map in the 23 units listed above would need backfilling,
  which is the expensive half and the reason this is not a now-task.
- Interacts with `plan-standardization-review-2026-08-22.md` §2 ("the
  structural core is right and the enforcement is half-applied") — this point
  is arguably the content-side instance of that same verdict.

### Operator note

Point 2 is narrower than stated but real: the angle *is* present on the
assembler-built lecture maps (SaD and AML), so "not at all" holds for the
hand-authored 23 units rather than for all of them. It is invisible everywhere
regardless, because it lives inside the locator string rather than in a field
of its own — so the complaint lands either way.

### Work done under this point — 2026-08-24, on Aram's instruction

Aram authorised acting on complaints 2 and 3 in the session of 2026-08-24
("organize the learning map such that every possible source in the shelf is
listed where it counts, the exact chapter numbers are listed, the angle it
covers is described well"). **Complaint 1 — whether plan manipulation is
standardized and well designed — was not addressed and stays open.** The point
therefore remains `open`; closing it is Aram's.

What changed:

- **Angle is a field.** `angle` and `angle_detail` are properties of a resource
  row (`learning-plan.schema.json`, `study-map.schema.json`) and of a source-map
  route (`module-source-map.schema.json`). The assembler no longer concatenates
  the angle onto `locator`; `tools/lift_angle_out_of_locator.py` un-fused the
  3,885 rows already on disk. Data contract bumped v11 → v12, new format fixture
  frozen at `tests/fixtures/formats/v12/`.
- **The defect cannot return.** `LOCATOR-ANGLE-FUSED` is an error, so a locator
  carrying a sentence-shaped angle fails validation. `LOCATOR-VAGUE`,
  `ROUTE-ANGLE-MISSING` and `ROUTE-ANGLE-DETAIL-MISSING` are warnings, counted
  rather than blocking (`VALIDATION.md`, "Plan rigour").
- **What "exact" means is now written down.** `PLAN-CREATION-SOP.md` defines an
  acceptable locator per format, fixes PDF pages as the page convention, and
  forbids hedges. `tools/material_toc.py` reads a local material's own contents
  and verifies a claimed page against the file, so a locator is checkable rather
  than merely asserted.
- **SaD is done end to end.** All 234 existing SaD lecture routes rewritten with
  an exact locator, a one-line angle and a long `angle_detail`; every book page
  range verified against the PDF where a copy is registered. 44 routes added
  from an audit of all 243 registered sources against the 15 SaD units — sources
  that cover SaD material and were routed nowhere. SaD lecture routes with no
  `angle_detail`: 0.
- **It is visible.** `generated/study-plans.md` enumerates every stage with its
  full option set, each row showing kind, exact locator and angle, with
  `angle_detail` on hover.

What is still open beyond complaint 1: 49 SaD locators remain `LOCATOR-VAGUE`,
almost all of them books with no registered copy (Grinstead & Snell, MML, D2L,
Prince, Goodfellow, Bishop, Nielsen, Jurafsky) where a page range cannot be
verified against a file. Repository-wide the counts are 546 warnings, of which
311 are `ROUTE-ANGLE-DETAIL-MISSING` outside SaD — AML, AMLS, Algo 2, Python and
the exam-prep units have not had this pass.
