# Final scope-fix report

The integration branch combines the cleanup review, the seven rebuilt fixes,
and the final scope follow-up. The source branch is
`fix/scope-authority-f01` at `2c804fb6`; the combined branch is
`integration/scope-and-cleanup-2026-10-20`. Its exact certified revision is
identified by the completed gate receipt, never inferred from this document.
The paired UI is `66ca47aa7cf3eb2201a6af939e54a05471fa8594`.

## Resulting behavior

- Stage teaching resources resolve against routes declared for their owning
  unit. Omitting a route id and spelling its source and locator cannot borrow
  a sibling unit's route. Reference rows retain their documented exemption.
- `RESOURCE-SCOPE-UNBOUND` remains a warning. Its message distinguishes an
  unnamed source, a source missing from the module, a missing unit
  disposition, and a missing route despite an existing disposition.
- The CLI refuses the application's `ui` provenance. The operator path stays
  available under the existing approval model.
- Resume displays the requirement id accepted by the write path. Note creation
  rejects a body carrying its own frontmatter. Fragment-bearing material
  references resolve the same file in the writer and validator.
- Master's promotion requires a named review and a digest-bound local document
  mentioning the evidence URL. This establishes attribution, not the truth of
  the claim or the URL's availability. A document containing only the URL
  satisfies that deliberately limited check. The data contract remains v56.

The original seven findings and their implementation decisions are recorded
in [FIXING-PLAN.md](FIXING-PLAN.md). The final follow-up is a separate commit;
it does not rewrite those seven commits again.

## Warning population

The final scope change retains all **1,462 warnings across 38 signatures**;
zero errors and no new or grown baseline signature were measured.

| Rows | Meaning |
|---|---|
| 1,101 | No source is named; module adoption cannot be checked. |
| 135 | The unit recorded the source's disposition, but no rich route exists. |
| 139 | The module declared the source; the unit recorded no disposition. |
| 69 | Rich routes exist, but the descriptive locator matches none. |
| 18 | The module never declared the source, all in `module-skill-python`. |

The 274 source-level cases remain warnings: disposition and route are
complementary records. Their messages now say which fact is missing; no
source-level exemption was introduced. See
[GRANULARITY-274.md](GRANULARITY-274.md) for the original measured analysis.

## Unit ownership and the corrected measurement

The earlier measurement called 685 source-and-locator matches fallback rows.
That included **684 compact `material_ref` bindings**, which the validator
resolves before reaching its fallback. The corrected script excludes those
bindings: **one row actually passes through the fallback**, and its own unit
owns the matching route. No current corpus row changes its warning status
under the ownership tightening.

The regression test constructs material declared solely for a sibling unit
and verifies that spelling the source and locator now warns. A second test
keeps shared material valid when the owning unit also declares it.
Reproduce the census with `tools/unit_ownership.py` in this directory.

## Fixture-pin repair and reproducibility

The first rebuilt push failed four checks because a delivery digest had been
computed before its delivery record's snapshot was updated. The final F-05
commit `9e762c3d` recomputes the digest and restores the two affected success
recordings. The first six rebuilt trees are unchanged; the final F-05 tree
includes this repair.

The published `tools/check_pins.py` now finds its checkout in both supported
locations and checks each case's own delivery and artifact pins, plus envelope
approval-subject digests. It no longer reuses the first digest from a whole
case file. An isolated probe detected a bad pin in a later sequence case and
changed artifact bytes, while preserving deliberate zero-digest refusals.
The current fixture check reports zero disagreements.

## Verification and completion authority

Completed before the final paired run:

- 50 scope tests passed, including ownership and diagnostic regressions.
- Eight affected scenario recordings were refreshed. Their 32 changed string
  fields contain scope diagnostics; exits and structured effects are unchanged.
- Lint, architectural code checks, type checking, and the warning baseline passed.
- Published ownership, granularity and fixture-pin scripts ran successfully.

Run `make system-check` on the clean final integration revision. It performs
lint, type checking, offline validation, warning-baseline comparison, the
whole pytest suite, the paired UI check, and the exact-pair stamp. A successful
run must leave both repository tips unchanged and both trees clean.

The execution records are in the external working directory
`LearningOS/workbench/fix-f01-2026-10-20/snapshots/`:
`final-system-check.log` and `final-system-check.json` contain the final
command, exact Core/UI revisions, exit code and clean-tree checks. The local
`.git/learningos-verified-pairs.jsonl` memo must agree. A running, interrupted
or failed command is not certification.

The older `snapshots/finish.log` stopped at 23% with SIGTERM and proves no
completed certification. The external canvas's original published evidence
measures `6265f473`; any new run must identify its own final revision and
actual results in its separate completion record.

## Remaining boundary

The catalog's `fact_state` format is unchanged: all 348 candidates were
unverified in the measured corpus. Changing that format remains a separate
migration. The scope warning is not promoted to an error. Learner content,
main-branch merging and live installation are outside this finalization.

Remote publication and CI are separate from local acceptance. No gate is
skipped for publication; completion requires the actual remote refs and CI
results, recorded with their exact revisions.
