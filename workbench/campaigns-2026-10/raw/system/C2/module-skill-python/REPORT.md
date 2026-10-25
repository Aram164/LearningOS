# C2 report — `module-skill-python` (item L2-13, evidence only, 2026-10-24)

Session: GLM-5.3-Flash, same clone as L2-12 (`~/los-glm-C2-2026-10/repository`
at `a2e2d49d`, branch `takeover/complete-and-install-2026-10-23`, tree clean,
never pushed). Validator on the clone: **0 errors / 1468 warnings**. The
per-module warning classification below comes from
`generated/reports/validation-report.md` generated this session.

Scope: 3 units, 43 stages, 280 resources (74 read, 38 practise, 160
reference, 8 watch), **0 routes** — the source-map declares 4 sources, all
with empty `unit_routes`; all material binding lives in stage resources.

A structural fact that shapes every check: **no row in this module carries a
`locator`** (280/280 have none). Rows carry `label` + one of
`vault_path` (63 rows) or `url` (102 rows) or neither. Consequences: the
page-range check (B) and the section-vs-text check (C) are **vacuous** —
there are no page or section claims anywhere to verify — and the duplicate-
locator check (D) is moot for the same reason. What remains substantive is
A (does every vault_path resolve), the vault_path↔label↔material agreement,
provenance, and the warning triage.

## Checks

- **A (vault_path):** 63/63 resolve — 61 `material://source-python-depth-drills/…`
  files (README.md, SHELF.md, capstone.ipynb, stage-0…stage-8 `.md` + `.ipynb`)
  and 2 knowledge notes (`note-python-intermediate-roadmap.md`,
  `note-python-oop-scope-repair-plan.md`). No page-bearing PDF is pinned by
  any row (fluent-python / effective-python are declared optional-depth but
  no row pins them; slatkin is declared-but-unused by design — the
  source-map's `why` says the per-stage item mapping lives in the depth-drills
  SHELF, which exists and resolves).
- **A+ (rows point at their own material):** each depth stage's rows point at
  its OWN stage files — 0 cross-stage misattributions across the 21
  vault_path rows (the L2-12 polars failure mode is absent here). The
  capstone stage points at `capstone.ipynb` + `SHELF.md`; stage-0 carries the
  ladder `README.md` row.
- **C-equivalent (label claims vs material):** the note's ladder table
  specifies per-stage question counts; all nine verified against the
  notebooks by counting `Q<n>.<k>` headings — 20/19/19/20/20/17/18/15/14, **9/9
  exact** (e.g. stage 0 = Q0.1–Q0.20 with folded solutions, matching the row
  label "20 predict-then-run questions with folded solutions").
- **D (duplicates):** no routes, so the sibling-route rule is vacuous. One
  label repeats ×5 within `unit-python-oop-scope` ("Rules of the game —
  predict → run → explain; close the tab and rebuild") — one per repair
  session, template by design. Nothing resembling the September
  `(source_id, unit_id)` broadcast.

## Provenance

One commit total (`1d32c918`, the 2026-10-19 snapshot): nothing in the module
changed after the snapshot. All three study maps declare
`source_plan: note://…`, provenance `durable-note`, and the live maps match
their notes:

- `note-python-depth-drills.md` ("the nine-stage ladder"): ladder table lists
  stages 0–8 with per-stage Q counts, plus "Full order: 0 → … → 8 → capstone"
  — the map's 10 stages (0–8 + Capstone — rebuild blind) are exactly the
  note's design.
- `note-python-intermediate-roadmap.md`: **28/28 step headings map to the
  map's 28 stages with identical titles** (Step 1 — Baseline … Step 28);
  the note's other headings (Diagnostic index, Advanced tier,
  Stratum-specific steps, Resources) are supplementary prose, not stages.
- `note-python-oop-scope-repair-plan.md`: **5/5 sessions** with identical
  titles (Session 1 — Names, values, scope … Session 5 — The interpreter,
  demystified).

Verdict: **original design (authored durable notes), no damage.**

## Findings

**No defects.** 0 vault_path failures, 0 cross-stage misattributions, 0
page/section claims to falsify, 9/9 label-count claims verified, provenance
clean.

One observation (not a defect, recorded for the binding campaign): **13
sources are named by rows but absent from the module's source-map**
(`source-batchelder-names`, `source-python-tutor`, `source-realpython-legb`,
`source-powell-python-expert`, `source-corey-schafer-oop`,
`source-hettinger-super`, `source-numpy-subclassing-docs`,
`source-hunner-iterator-protocol`, `source-beazley-generator-tricks`,
`source-rhodes-python-patterns`, `source-kaptur-byterun`,
`source-guo-cpython-internals`, `source-tu-python-ml-course` — 21 rows, of
which 18 are non-reference and warned). The notes predate the source-map
registry discipline; adopting these sources or rewriting the rows as
anonymous URL rows is the critique-point-1 campaign's call, not a defect in
itself.

## Validator warnings (120, all RESOURCE-SCOPE-UNBOUND)

By reason (all real under the validator's rule; shape = the notes' design +
missing registry adoption, not damage):

- **64 `no-source`** (roadmap 58, oop-scope 6): non-reference rows with no
  `source_id` — template practise rows and url-only rows. The validator
  cannot check module adoption without a source.
- **38 `no-disposition`** (depth-drills 19, roadmap 19): rows naming the two
  *declared* sources (`source-python-depth-drills` 21 rows,
  `source-fluent-python` 16 non-reference rows, plus the
  `source-python-docs-classes-mro` row) with **no locator** — the warning
  prints `at ''` — and no unit disposition and no route to match. This
  module's distinctive warning shape: it is the locator-less rows, not a
  locator mismatch.
- **18 `undeclared-source`** (roadmap 10, oop-scope 8): rows naming the 13
  un-adopted sources above (3 reference rows exempt).

## Assumptions

- The 102 url-only rows were not fetched (no locator claims to verify; same
  scope decision as the L2-12 engineering-tools report).
- `source-python-tutor`/`source-rhodes-python-patterns` reference-row
  exemption arithmetic (21 rows − 3 reference = 18 warned) is derived from
  the collected rows plus the validator's documented `kind: reference`
  exemption (plan_rigor.py:569), not from re-running the checker.
- The Q-count check counts distinct `Q<n>.<k>` headings per stage notebook;
  sub-numbered variants inside a question would not be counted separately.
