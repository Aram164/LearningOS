# F-01 fixing pass — outcome

**Date:** 2026-10-20
**Branch:** `fix/scope-authority-f01` in `LearningOS/repository`
**Base:** the certified pair, Core `40d8afe` / UI `66ca47aa`
**Plan:** `LearningOS/workbench/fix-f01-2026-10-20/FIXING-PLAN.md`
**Decisions:** Aram took all four recommendations the plan queued in §6, plus
the plan's own recommendations for §6/1–3 and §6/6.

## The branch

Seven commits on the certified pair, one per finding, each with its own
test — the brief asks for A, B and C to be shipped separately ("the canvas
review was wrong twice before"), and the first pass bundled them into one
WIP commit. The WIP commit is gone; the work it carried is redistributed.

```
d6f1fbbd fix(core): F-02 — the resume screen names the requirement the write path accepts
f63b50fb fix(core): F-03 — a note body may not carry its own frontmatter
8ec34a02 fix(core): F-04 — the two material resolvers agree on a fragment
c16afdb9 fix(core): F-01 B — the CLI cannot mint the app's own provenance
910390e2 fix(core): F-01 C — workflows 23, 24 and 27 are a stop-and-ask
c2b4f026 fix(core): F-01 A — a stage resource must resolve to material its module adopted
6265f473 fix(core): F-05 — the promotion's verification must name a content-bound artifact
```

The work now lives in the **primary** checkout (`LearningOS/repository`),
not in the isolated clone the first pass used — the clone is a copy of the
certified pair, and the primary is the one with `../materials` and
`../obsidian-ui` mounted, so the whole gate can run there. The clone's
branch was updated to match.

**Pushed:** `origin/fix/scope-authority-f01` at `6265f473` (7 commits on
`40d8afe`). `origin/main` is untouched — merging it is Aram's call. The
pre-push hook recognised the stamped release pair (Core `6265f473` + UI
`66ca47aa`) and skipped re-running the full gate.

### The gate, run on the final tree

```
make check        0 error(s), 1462 warning(s) — OK
make warnings     OK — zero errors, no new warning signature
make lint         All checks passed! / code architecture: PASS
make typecheck    Success: no issues found in 7 source files
npm --prefix ../obsidian-ui run check     all assertions passed
pytest            7960 passed, 3 skipped, 2 xfailed
pytest (at F-01 A) 1130 passed, 2 xfailed   — the intermediate commit is green too
```

---

## What shipped

| Item | Change | Where |
|---|---|---|
| **A** — the scope rule | `RESOURCE-SCOPE-UNBOUND` warning: a stage resource must resolve to material its own module's source map declares | `tools/learning_os/derive/validation/plan_rigor.py` |
| **B** — the CLI cannot mint the app's provenance | `--channel ui` → exit 2 | `tools/seal_envelope.py` |
| **C** — the stop-and-ask | boundary 18 (done in the first pass) + a "Start here" row (this pass) | `system/OPERATOR.md` |
| **F-02** — the resume label | the "Requirement" line carries the requirement id | `tools/learning_os/app/handlers/resume.py` (first pass) |
| **F-03** — the frontmatter refusal | `note.create` refuses a body carrying its own frontmatter | `tools/learning_os/app/handlers/notes.py` (first pass; message aligned to the brief here) |
| **F-04** — the two resolvers agree | the fragment is stripped in the validator's resolver; the write path is untouched | `tools/learning_os/derive/validation/references.py`; `store/materials/resolution.py` reverted |
| **F-05** — the unchecked "official-academic" claim | each `verification.evidence[]` must name a local, content-bound verification artifact | `system/schema/master-planning-promotion.schema.json`, `tools/learning_os/app/admin/masters_planning.py` |

## The corrections the first pass needed

1. **The `material_ref.route_id` hole is closed.** The loaded study map is
   *expanded* — `material_ref` is popped and its inherited fields are copied
   onto the resource (`domain/material_refs.expand_map`) — so the route binding
   a compact row declared survives only in the authored bytes. The rule now
   reads it there, paired by stage id and resource index (the same
   correspondence `domain.material_refs.preserve_map_refs` uses).
   Measured: 1,538 authored rows use `material_ref`, 862 of them with no
   top-level `route_id`.
2. **`kind: reference` is exempt** (374 → 409 rows on the live corpus). The
   exemption rests on the row's meaning, not on `scope_triage`, which the
   writer of the row also sets.
3. **The refusal wording** now carries the brief's acceptance substring
   verbatim: *"the 'ui' channel is the application's own provenance"*.
4. **F-04 is back on the brief's side**: the fragment is stripped in the
   validator, not refused by the write path. A page fragment is meaningful —
   the Obsidian UI's `resource-target.ts` splits the path on `[?#]` — and the
   corpus carries no fragment today, so both sides are behaviour-preserving.

## The measured population

Measured on the live corpus at Core `40d8afe` (script:
`measure_scope.py`):

```
stage resources                                     3618
  with route_id                                      826
  with material_ref.route_id (authored)              862
  with no route binding at all                     1930
```

Of the 1,930 rows with no route binding, after the `kind: reference`
exemption, 1,462 are reported. Broken down by *why*:

| bucket | rows | what it is |
|---|---|---|
| no source at all (a prose locator) | 1,098 | a pointer to the stage's own work, not to adopted material |
| **a source the module never adopted** | **21** | **the actual F-01 defect** — every one in `module-skill-python` |
| the source is declared at source level only | 274 | adopted, but the module's map records no route for it |
| the source has routes and the locator matches none | 69 | the "descriptive locator" style difference |

The first pass's 1,869-warning baseline is now 1,462 warnings / 38
signatures (`tools/warning_baseline.py --update`, in the same change).

## What the rule does *not* do

* It is a **warning**, not an error. The error flip is Aram's, and the plan
  records the corpus migration (`material_ref.route_id` +
  `tools/assemble_lecture_study_maps.py`) as its precondition.
* It does not report a **top-level** `route_id` that names nothing or
  another unit's route: `references.py` already owns those as errors
  (`REF-ROUTE`, `RESOURCE-ROUTE-OWNER`), and the scope rule does not report
  the same thing twice.
* It does not check a row that names **no material** against the map beyond
  the locator: a row with no `source_id` names nothing to adopt.

## Acceptance criteria, measured

```bash
# 1. the scope hole is closed (warning first)
#    los-canvas/canvas/probes/probe_scope_gap.py, run against this checkout
#    (run_scope_probe.py borrows the probe unchanged and points it here)
#    before: validate exit 0, no warning
#    after:  the new warning fires
```

```
source registered: True
module-demo declares: ['source-demo-book']
probe source in module map: False
map import: 0
stage landed: True
VALIDATE exit: 0 | errors: []
```

and the same world, checked against its own baseline:

```
warning-baseline: 15 warning(s) across 8 signature(s); baseline 13 across 8
  NEW  RESOURCE-SCOPE-UNBOUND at .../unit-demo-l01/study-map.yaml: 4 → 5
  NEW  STAGE-NODE-UNLINKED   at .../unit-demo-l01/study-map.yaml: 1 → 2
```

The `RESOURCE-SCOPE-UNBOUND` line is the probe's off-map stage. The
`STAGE-NODE-UNLINKED` line is the probe's own stage naming no knowledge node
— pre-existing behaviour, not this change.

```bash
# 2. the CLI can no longer mint the app's provenance
.venv/bin/python tools/seal_envelope.py --root . --capability garden.seed.create \
    --payload '{"text":"x"}' --key k --channel ui --out /tmp/e.json
#    exit 2, "the 'ui' channel is the application's own provenance"

# 4. the operator path is untouched
.venv/bin/python tools/seal_envelope.py --root . --capability garden.seed.create \
    --payload '{"text":"x"}' --key k2 --channel operator --out /tmp/e2.json
#    exit 0
```

Both measured: exit 2 with the brief's substring, and exit 0.

## The transcript churn, and why it was unavoidable

35 procedure transcripts and 211 scenario recordings changed. Two causes,
both mechanical:

1. **The world's fingerprint moved.** `canonical_fingerprint` covers
   `system/schema` and `system/contracts`, and the procedure world copies both
   from the live tree. F-05's approved record-shape change touches the
   promotion schema and the data contract, so every transcript and every
   recording that pins a snapshot hash pins a new one — 69 distinct digests
   across the churn (the world's fingerprint, its revision, the derived
   envelope and intent hashes, and the backup manifest's aggregate).
2. **The demo world carries four more warnings.** The scope rule reports the
   demo stage's four stage resources (three on `stage-demo`, one on
   `stage-demo-pending`): the demo module declares its book at *unit* level,
   so its rows name places the map does not declare at route level. The
   fixture's measured baselines adopt them
   (`tests/repo_builders.py`, `tests/scenarios/recorded/…`), and the
   transcripts' expected warning counts follow: 9 → 13, 10 → 14.

Because the two causes land in different commits, the churn is split by
cause: the digests go with F-05, the counts with Part A, and each commit's
transcripts and recordings match the world as it stands at that commit
(`workbench/fix-f01-2026-10-20/split_by_cause.py`).

Two sealed-envelope hash assertions broke with the fingerprint move
(`build-write-envelope.md`, `end-a-session.md`); their pinned digests were
recomputed and the assertions still pass — no check was weakened. The
trailing whitespace `scrut update` introduced ("> " where the file had
">") was stripped back, so `git diff --check` stays clean.

## Residual, deliberately not fixed

**The catalog's `fact_state` is still a free-text assertion.** The Master's
Planning catalog records a candidate source's facts as
`{status, as_of, evidence: [<free strings>]}`, and the promotion's
`_require_current_fact_state` accepts any non-empty list of strings. The
brief names this as "equally self-asserted" to the promotion's own
`verification` block, and it is the same weakness one level down.

It is left open on purpose: the plan's W7 scoped F-05 to the promotion
package's `verification.evidence[]`, and closing the catalog side would be a
**second record-shape change**, in a schema that carries 348 candidate
sources, through a different write path (`masters-planning.catalog.update`).
All 348 are `unverified` today, so nothing in the corpus depends on it.

The mechanism would be the same one, if Aram wants it: the catalog schema's
`factState.evidence` items would accept the same `verifier` object beside the
existing strings, and a `verified-current` row would have to carry one whose
artifact exists, hashes to the recorded digest, and names the row's URL.

## The other residual, stated plainly

**The rule flags 274 rows whose material the module *did* adopt.** Six live
modules (`module-hu-amls`, four `module-job-*`, `module-skill-python`) record
adoption at *source* level, not at route level: their source maps declare
`unit_routes: ["unit-demo-l01"]` rather than rich routes. The rule asks for a
route and cannot find one, and its message ("the module's source map declares
no route for it; adopt the material in the module's map") is accurate but
does not say that the material itself is adopted.

A granularity-aware variant — judge a source the module declares at source
level at source level — was measured: it removes those 274 rows and lands on
1,188 warnings. It was **not** taken, because the plan approved the
route-level rule, and narrowing a rule that was just approved is a decision
for Aram, not for the fixer. It is the obvious next refinement if the
warning set proves too noisy to read.

The same variant is what would make the synthetic fixtures clean; they are
adopted in the fixtures' measured baselines instead
(`tests/repo_builders.py`, `tests/scenario_fixtures.py`), which is the same
act the live repository performs over its own content debt.
