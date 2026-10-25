# Claude's verdict on C2 `module-hu-aml` (2026-10-24, overnight orchestrator)

**Verdict: the report holds.** GLM claims no damage, and the provenance
supports that. It reports one real, minor inconsistency (F1), which matters
less than the report says. Every check was read-only against the live tree
and `LearningOS/materials/`.

## Damage and broadcast claims

There are none: the report finds no broadcast shape and no damage. I checked
its main provenance claim (F2), that the 31 `RESOURCE-SCOPE-UNBOUND` rows are
original design plus an unapplied improvement:
- The live `unit-aml-exam-prep/study-map.yaml` has **0** `material_ref`
  bindings. Its `source_plan` is still
  `AML-exam-execution-plan-2026-08-19.yaml`.
- `AML-exam-plan-final-2026-09-11-r2.yaml` exists in the workspace
  `outputs/` and carries `route_id` bindings, 46 matches.
- The only transaction under `operations/transactions/` from 09-11 to 09-20
  that names `unit-aml-exam-prep` is `transaction-20260920-034916-001`, the
  node-linkage backfill.

So the bound plan was never applied. This is unmigrated debt under critique
point 1, not damage. **CONFIRMED.**

## Three spot checks against the PDFs

1. **F1: printed page numbers in the exam-prep rows. CONFIRMED, with a
   correction.**
   - The live row reads `§11.2.2 p. 372 …; §11.2.4 goodness of fit p. 380`
     (study-map line 111).
   - In `murphy-pml1/pml1.pdf` (860 pp.), PDF p.402 begins "372 Chapter 11.
     Linear Regression", and PDF p.372 is "Chapter 10. Logistic Regression
     10.2.3". The +30 offset is real.
   - Line 171's "§8.3 pp. 289–291" checks out too: PDF p.319 begins
     "8.3. Second-order methods 289".
   - **What GLM missed:** `pml1.pdf` carries **PDF page labels**, and the
     label of PDF p.402 is "372". These rows have no `material://` link, so a
     reader types the page into a viewer. A label-aware viewer (pdf.js in
     Obsidian, Preview) opens the right page for "p. 372". GLM's "lands 30
     pages early" applies only to navigation by physical index.
   - So it is a real inconsistency with the repository's PDF-page convention,
     with **low** practical impact. If it is fixed, write both numbers ("p. 372
     (pdf p. 402)"), not just the converted one.
2. **F3: the compressed locator. CONFIRMED.** Route
   `route-b3c9cda951cabf0f92743436` reads `exercise-slides/Übung 02-11.pdf
   and bonus-exercises/zusatz-blatt01-04.pdf`. The folder holds
   `Übung 02 .pdf` … `Übung 11.pdf` (with stray spaces in 02 and 06) and
   `zusatz-blatt01.pdf` … `zusatz-blatt04.pdf`. No single file matches. GLM
   rightly calls this an observation and original shape, not damage.
3. **F2: the provenance chain.** Checked as described above.

## Worth carrying forward

- **The M2 report's section check may have found nothing to check.** In its
  method notes, GLM says `materials/.flat`'s folders are symlinks, so
  `Path.rglob` finds nothing without `recurse_symlinks=True`. It says the M2
  sections-audit script "silently matched nothing on this machine for the
  same reason". If true, the M2 report's (L2-1) check C was vacuous, not
  clean.
  - I did not re-run the M2 script: ASSUMPTION.
  - The L1-4 re-check should cover M2's section claims with this in mind.
    The later C2 sessions use this session's fixed scripts.
- The 31 warnings were triaged as all real (9 + 22, reconciled to 46 rows
  with the 15 exempt ones explained). That is a measurement; I did not re-run
  the validator.

## For Aram

Nothing here needs a fix now. F1 and F2 both fall under critique point 1,
whose fix is reserved to you. No issue draft: this is personal-data plan
debt, not a Core defect.

## Fix packages (conductor 2, Sun 2026-10-25 02:30)

`PACKAGES.md` (L2-15) holds three packages: F1 (the printed-page anchors,
written with both numbers, as this verdict asked), F2 (17 bindings), and
the two combined.
- All three pass `--check` with 0 canonical writes.
- Each touches only `unit-aml-exam-prep/study-map.yaml`.
- None is applied. They wait for the live-branch merge (decision 7).
