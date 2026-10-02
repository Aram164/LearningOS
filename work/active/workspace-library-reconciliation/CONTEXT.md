---
id: workspace-library-reconciliation
type: workspace
title: Library reconciliation — two-pass source intake
created: '2026-09-23'
status: complete
standing: false
---

# Library reconciliation (two-pass source intake)

## Objective

Say, occurrence by occurrence, where every link, local file name, source ID and
bare resource entry in the old resource lists went, instead of trusting a
registered-source count (OPERATOR rule 14). The workspace began with the
frozen baseline and occurrence review. Intake, projection, and catalogue
population now have separate post-intake proof below.

## Current Scope

- **Step 1, baseline (done).** `inputs/baseline-2026-09-23.yaml` records both
  repository heads, the contract versions, the bootstrap snapshot and the
  validation and warning-baseline state observed before any change.
- **Step 2, reconciliation (done; review frozen).** `inputs/declared-inputs.yaml`
  names every input by exact path: 24 origin files (the old central index, the
  six Master's lists and 17 workspace plan inputs) plus the registry,
  collections, Master's anchors, catalogue, materials manifest and migration
  resolvers they are checked against. All 61 files are hashed on every run.
  `outputs/dispositions.yaml` gives each of the 1090 occurrences exactly one of
  the seven dispositions and records the hashes it was reviewed against.
  `outputs/reconciliation-report.md` is generated from both.
- **Checker.** `tools/library_reconciliation.py` is read-only: it writes only
  inside this workspace and never touches canonical records. Tests:
  `tests/test_library_reconciliation.py`.
- **Scratch.** `scratch/` holds the decision files that `merge` combines, in
  this order, into the dispositions: `auto-decisions.yaml` (mechanical matches,
  reproducible with `suggest` from an empty dispositions file), one
  `decisions-*.yaml` per origin group (`lr`, the six `m-*` lists, `ws`), and
  `decisions-names.yaml` (named-but-unlinked objects). Merging them from an empty
  file and freezing reproduces `outputs/dispositions.yaml` byte for byte. The
  worklist is disposable.
- **Known boundary.** Items listed under "Boundary" in the report, including
  the uncurated `Ultimate-Index.md` and six unregistered `_unsorted` works,
  remain explicit decisions for a later intake. They are outside the 1090
  declared occurrences.

## Open Questions

The 151-link `Ultimate-Index.md` and six unregistered `_unsorted` teaching
objects remain explicitly outside this intake. Aram can decide whether to open
a later bounded pass for them; their exclusion is not a claim that they were
examined or admitted to active learning.

## Next Action

This pass is complete. When a later intake is authorized, use the frozen
review and the applied proof below as its baseline; reconcile newly declared
origins before any additional registration.

## Current verification

The independent decisions and required changes are recorded in
`LearningOS/workbench/source-intake-review-2026-09-23/REVIEW.md`. The frozen
pre-intake report stays in `outputs/reconciliation-report.md`. Check the
finished catalogue with
`python tools/library_reconciliation.py check --workspace work/active/workspace-library-reconciliation --applied --report`.
If an origin changes, review its affected occurrences before recording a new
baseline; never overwrite the original review to hide an intake mutation.

### Re-freeze 2026-09-23 (review R12)

Three `source-mlsysbook-vol1` URL occurrences moved alias→companion with
titles (`lr:203:u1`, `lr:343:u1`, `m-dataeng:90:u1`): parent pages covering both
volumes, not Vol 1 alone. `source-mlc-book` (`lr:205:u1`) and `source-stat110`
(`lr:96:u1`) were re-examined against their rows and records and stand as
alias. Decisions edited in `scratch/decisions-lr.yaml` and
`scratch/decisions-m-dataeng.yaml`, then merge (all 10 files, auto-decisions
first) → freeze → report; check is `ok: true` (alias-or-duplicate 48,
existing-active-source 524).

### R13 done 2026-09-23

`materials/_unsorted/` reconciled item by item in
`scratch/unsorted-reconciliation-2026-09-23.md`: 3 shelf/index docs, 3 tool
references and 7 module-bound legacy artifacts are explicitly non-source;
6 unregistered books/papers join the Boundary list (need Aram's decision
before any intake, excluded from step 8's completeness claim).

### Steps 6+8 executed 2026-09-23 (Muse, governed writes)

Step 6 (Master's catalogue): all 348 `new-masters-candidate` objects written
to `curriculum/quarantine/masters-planning/catalog.yaml` (revision 0) via
`masters-planning.catalog.update`, transaction-20260923-232956-001. 126
entries carry a landing `url`, 18 `identifiers`, 1 `child_titles`, 5
`possible_use` (only where a reviewed flag/note grounds one); 217 are
link-less list mentions (title/type + provenance). No URL refused by the
academic-only sanitizer (0 omissions).

Step 8 (registration): 4 creates + 44 corrects via `source.intake.record` in
3 batches of 20/20/8 (MAX_BATCH), transaction-20260923-233229-001,
transaction-20260923-233245-001, transaction-20260923-233258-001.
`source-ng-coursera`: landing corrected to the 2011 playlist, year 2011, the
2022 specialization kept as `identifiers.coursera-specialization-2022` (flag
lr:116:u1). Deliberately not stored: the kurzes-tutorium channel-id URL, the
rohrer `brandonrohrer.com/blog.html` URL and the stat110 hsites root (all
unverified per their flags), and the blitzstein-hwang Drive copy (personal;
the record already holds the local copy). 0 address conflicts.

The original review remains frozen: ordinary `check --report` now reports the
expected target changes and does not get re-frozen. The final target proof is
`outputs/applied-check.json`, generated by `report --applied` and verified by
`check --applied --report`. This second check requires every reviewed origin
to remain byte-identical, every new target to exist with its reviewed title,
type and origin references, and every non-redundant reviewed URL to be stored
on its target. It also pins the final target hashes in a separate report so
later changes are visible. Current result: 1090/1090 dispositioned, 0 findings,
0 stale origins; 4 new active sources and 348 Master's candidates present.
