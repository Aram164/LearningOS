# C5 report: one gated fix branch for the confirmed C1 findings (L1-9)

Branch `glm/C5-2026-10-24`, pushed from a fresh GitHub clone at
`~/los-glm-C5-2026-10/repository` (base `origin/main` `d6c47790`). Nine
commits: one per finding, plus one lint follow-up the first release-pair run
forced. Nothing landed; `main` untouched; no issues filed; no closing
keywords in any commit message.

**Release-pair:** run [40148452560](https://github.com/Aram164/LearningOS/actions/runs/40148452560)
on core `555b581a4af0bba5237cb8a3b76f85f4c1c74c9d` × UI `f7dbc1f7607157d5c1c2edb84a14e6a26ab89f94`.
Counts: see "CI" at the bottom. Two earlier dispatches failed at gates my
local pytest runs could not see:
[40138998182](https://github.com/Aram164/LearningOS/actions/runs/40138998182)
(core `a98c9e0e`) at `make lint` — three unused/unsorted imports in my copied
test files, fixed in e1a305a;
[40139293836](https://github.com/Aram164/LearningOS/actions/runs/40139293836)
(core `e1a305aa`) at the pre-push hook's paired-boundary ratchet — the copied
backup test built a synthetic UI with the literal `parent / "obsidian-ui"`,
which the hook's scanner reads as a live-sibling access; fixed in `555b581`
by passing `--ui-root` explicitly, the `test_vnext_boundaries` pattern.

| # | Finding | Commit | Test file |
|---|---|---|---|
| 1 | #27 `module.attempt.record` graded dead end | `e973c6e` | `tests/test_c1a_graded_attempt_dead_end.py` |
| 2 | C1-B-1 `review.apply` partial apply | `3f4f61a` | `tests/test_c1b_shelving_partial_apply.py` |
| 3 | C1-C-1 `note.revise` guarantees | `f4ecaf8` | `tests/test_c1c_revise_voids_dedicated_guarantees.py` |
| 4 | C1-C-2 garden reserved slug | `8e8acce` | `tests/test_c1c_garden_reserved_slug.py` |
| 5 | C1-D-1 same-second file capture | `f01311e` | `tests/test_c1d_same_second_file_capture.py` |
| 6 | C1-D-2 `material.context --limit 0` | `98109e3` | `tests/test_c1d_zero_limit_refused.py` |
| 7 | C1-E-1 backup symlinked subtree | `4a310c6` | `tests/test_c1e_backup_symlinked_subtree.py` |
| 8 | C1-E-2 coordination reflow | `a98c9e0` | `tests/test_c1e_coordination_no_reflow.py` |
| — | lint follow-up (imports only) | `e1a305a` | — |
| — | paired-boundary scanner fix (test only) | `555b581` | — |

Every regression test was copied from the workbench, registered in
`tests/group_map.py`, and shown failing before its fix and passing after, in
this clone, on this branch's own history.

---

## 1. `module.attempt.record` — a graded termin can be corrected (issue #27)

**Commit `e973c6e`** — fix as the issue proposes.

- **Files:** `tools/learning_os/app/handlers/admin.py` (an update restates the
  row: an omitted `grade` now removes the previous one, as `date`/`result`
  are already overwritten), `tools/learning_os/derive/validation/curriculum.py`
  (MOD-GRADE admits exactly `grade: 5.0` on `result: failed`), test file, group
  map.
- **Before (on this branch's base):** step 3 of the workbench reproduction
  exits 2 — `E MOD-GRADE: module 'module-demo' attempt[2] carries a grade but
  result is 'withdrawn' and module is not completed` — and the row stays
  `passed`/2.3.
- **After:** the correction commits (`result: withdrawn`, no `grade` key
  survives), and a new second test pins the issue's part 2: `failed` + 5.0
  commits; `failed` + 4.0 and `sat` + 5.0 still refuse with MOD-GRADE.
- **Focused tests:** `test_curriculum_v2.py` (89 passed, 1 skipped),
  `test_validation.py` (69), `module.attempt.record` scenario recordings
  (8, no recording changed — no recorded case updates a graded row).

## 2. `review.apply` — a partial apply keeps the remainder on the queue

**Commit `3f4f61a`** — decided semantics: unselected items stay pending.

- **Files:** `tools/learning_os/app/handlers/capture.py` (`shelving_apply` now
  removes the applied items from `shelving.items` and sets
  `state: "proposed"` while any remain, `"applied"` only when the packet
  empties), test file, group map, **two re-recorded scenario cases**.
- **Before:** after applying one of two items, `assert 'shelving' in []` —
  the packet claimed `state: applied`, both items still listed and
  `selected: true`, and the manifest's `review_items` was empty.
- **After:** the packet stays on the decision surface until the remainder is
  applied. I additionally verified the decided shape end to end (not part of
  the copied test): after a partial apply the study map reads
  `state: proposed, items: [proposal-beta]`; after applying the remainder,
  `state: applied` with an empty `items` list (schema has no `minItems`); a
  re-apply of the removed item now refuses at `unknown-selected` (its
  destination-exists check would also have caught it before).
- **Re-recorded:** `review.apply::{apply-selected, exact-replay}` — the
  study-map bytes change with the packet semantics; the recording diffs are
  exactly the study-map sha and its derived digests, nothing else.
- **Focused tests:** `test_curriculum_v2.py` (89), `review.apply` scenario
  recordings (12).

## 3. `note.revise` — the question and reference guarantees hold

**Commit `f4ecaf8`** — decided fix: uphold `ARCHITECTURE.md` §5.7; witness 2's
`sha256:` precondition bug fixed first, as instructed.

- **Files:** `tools/learning_os/app/handlers/notes.py` (two new guards after
  the role check: a question's `atlas_question.target` must be unchanged —
  `note.revise.target-change`; a note carrying `material_analysis` must keep
  its binding and its frozen tail bytes — `note.revise.binding-change`),
  test file (helper now tolerates an optional `sha256:` prefix against the
  schema's bare-hex `frozen_input_sha256`), group map, **two new A9 witness
  cases** `note.revise::{target-change, binding-change}` with casedata and
  recordings.
- **Before:** witness 1 — the retargeting revise exits 0 and the stored
  target changes; witness 2 (precondition fixed) — the revise exits 0 and
  `material_analysis` claims bytes the body no longer holds.
- **After:** both witnesses pass; the revise refuses (rc 2) at the new typed
  sites. Rewording a question (same target) and frontmatter edits of
  reference notes stay allowed.
- **Two existing tests updated** (they pinned the old general-path behavior):
  `test_synthesis_analysis_refs.py::test_note_edit_after_approval_stales_dossier`
  now stales the dossier with a governed frontmatter (title) edit instead of
  a body append, and a sibling test pins the new body refusal. The dossier
  freshness machinery is unchanged and still fully exercised: any legal
  revise changes the note's bytes, revision and digest.
- **Focused tests:** `test_note_create.py` (15), `test_gateway_v2.py` (73),
  `test_material_analysis_save.py` (43), `test_atlas_authoring.py` (6),
  `test_synthesis_analysis_refs.py` (17), `test_observation_gesture.py` (17),
  `test_write_payload_clarity.py` (32), `test_arch_request_schemas.py` (18),
  all `note*` scenario recordings (205), and the A9 site check for the two
  new sites (witnessed from their own cases, run in one session).

## 4. `garden.seed.create` — no stem the reader skips

**Commit `8e8acce`** — decided fix: suffix, not refuse (the finding draft's
typed-refusal suggestion is superseded by the C5 table).

- **Files:** `tools/learning_os/app/handlers/capture.py` (a slug the reader
  skips — `readme` is the only one the slug grammar can produce — gets the
  collision loop's `-2` suffix before the loop), test file, group map.
- **Before:** the create receipts `knowledge/garden/readme.md`; the stable-id
  read refuses: `los: INVALID_REQUEST: note not found: garden-note-readme`.
- **After:** the seed is written as `readme-2.md` and read back by the stable
  id the system itself derives.
- **Focused tests:** `test_garden_seed.py` (7), `test_garden_projection.py`
  (4), `garden.seed.create` scenario recordings (8, unchanged — no recorded
  title maps to a reserved stem).

## 5. `capture.create` — the file branch loops for a free name

**Commit `f01311e`** — decided fix: the file branch loops with a serial, as
the text branch does.

- **Files:** `tools/learning_os/app/handlers/capture.py` (fallback name now
  loops `{stamp}-{stem}-{serial}{suffix}` while it exists), test file, group
  map.
- **Before (frozen clock):** the third capture exits 0 and replaces the
  second capture's receipted bytes (`second_file.read_bytes() != bodies[2]`).
- **After:** the third capture writes `{stamp}-notes-2.md`; the second
  capture's file keeps its exact bytes.
- **Focused tests:** `capture.create` scenario recordings (9, unchanged),
  `test_transactions.py` (51), `test_inbox_resolve.py` (11).

## 6. `material.context` — `--limit 0` reaches the bad-window refusal

**Commit `98109e3`** — decided fix: zero reaches the existing refusal.

- **Files:** `tools/learning_os/app/handlers/materials.py` (an explicit limit
  passes through verbatim; only an absent limit takes the default page of
  20), test file, group map. The schema's missing `minimum: 1` is left for
  whoever lands a contract-adjacent edit, as the verdict scoped it.
- **Before:** `--limit 0` returns the full 20-item page (rc 0).
- **After:** rc 2 at `material.context.bad-window` ("limit between 1 and 20").
- **One existing test updated:** `test_material_context.py::
  test_assessment_items_carry_live_dossier_freshness` revised a reference
  note's body to stale its dossier — the same pin C1-C-1 removed; it now
  uses a title edit (see finding 3).
- **Focused tests:** `test_material_context.py` (35),
  `test_material_context_boundaries.py` (6), `test_bounded_reads.py` (52),
  `material.context` scenario recordings (16, unchanged).

## 7. `backup.manifest` — a symlinked subtree is refused

**Commit `4a310c6`** — decided fix: refuse, as the module already does for
unreadable directories and a symlinked declared tree.

- **Files:** `tools/learning_os/app/backup_manifest.py` (in `_admitted_paths`,
  after the excluded-name prune, any remaining symlinked directory raises
  `BackupManifestError`), test file, group map, and **one re-shaped boundary
  test** — see the flag below.
- **Before:** the manifest exits 0, schema-valid, with the subtree absent and
  unrecorded (`assert covered or marked` fails with both False).
- **After:** `backup-manifest` refuses: "declared backup tree contains a
  symlinked directory: …/records/archive" (exit 2 via the CLI's
  `BackupManifestError` row).
- **ATTENTION — design contradiction resolved in favor of the C5 decision.**
  `test_vnext_boundaries.py::
  test_backup_manifest_preserves_absence_and_symlink_exclusions` pinned the
  *implicit* symlinked subtree as a deliberate silent exclusion (its comment
  contrasted it with the refused explicit declaration). The C5 decision —
  refuse, per the module's own no-silent-omission rule — overrides that pin,
  so I re-shaped the test rather than narrowing the fix: the file-symlink
  exclusion and the genuinely-absent-tree preservation are asserted
  unchanged; the subtree case now asserts the new refusal; the explicit
  declaration's own "traverses a symlink" refusal keeps a dedicated fixture
  (a link at the core root, outside every walked tree, so the declaration
  check is what fires). Live-tree impact of the new refusal: none measured —
  the Core tree's only symlink is the root file `CLAUDE.md`, and
  `materials/.flat` is pruned by name before the check (ASSUMPTION beyond
  the C1-E verdict's read-only measurement: the UI checkout has no
  symlinked directories).
- **Focused tests:** `test_recovery_conflicts.py` (42),
  `test_vnext_boundaries.py` (79 passed, 6 skipped), `test_health_vnext.py`
  (25), `test_ops_pipeline.py` (117), `test_scenarios_health_shim.py` (4).

## 8. `coordination.section.revise` / `workspace.next-action.update` — no reflow

**Commit `a98c9e0`** — decided fix: `replace_h2_section` leaves every other
section byte-identical.

- **Files:** `tools/learning_os/domain/render.py` (the replacement is spliced
  into the line list between heading lines, fences accounted for; the
  edited section's range gets heading + one blank + trimmed content + the
  blank before the next heading, or the file's newline artifact when last;
  preamble and all other sections keep their exact bytes), test file, group
  map.
- **Before:** editing Commitments in a hand-shaped COORDINATION.md (Priorities
  with no blank after its heading) rewrote the Priorities section.
- **After:** Priorities' parsed lines are byte-identical; the splice
  reproduces `serialise`'s bytes on already-normalised documents, so all 19
  `coordination.section.revise` + `workspace.next-action.update` recordings
  replay unchanged (verified).
- **Focused tests:** `test_render.py` (11), `test_coordination_revision.py`
  (18), `test_workspace_next_action.py` (7), `test_code_reachability.py` (19).

---

## Finding left out of the branch

**C1-A `module.create` legacy-identity clash — decided out; fix proposal.**
The C5 table rules it out: the contract invariant's wording is what should
change, and that means a `system/contracts/capabilities.yaml` edit, which
this branch must not make (the unlanded `learning-gaps-2026-10-24` branch
already edits two contract files; a second edit would move the fixture
snapshot and collide at landing).

Proposal for whoever next touches the contract file: reword the
`module.create` invariant at `system/contracts/capabilities.yaml:399` from
"an existing canonical identity or file is refused" to say the destination
check is the filesystem's — e.g. "an existing module file or directory is
refused; a legacy-registry id is a frozen compatibility snapshot, not a
live identity" — and, in the same commit, refuse
`module_id in ctx.repo().legacy_modules` in `_creation_destination_problems`
(`tools/learning_os/app/handlers/plan.py:940-957`) only if the intent is the
stricter reading. The reproduction test stands ready in the workbench at
`C1-A/module.create/legacy-identity-clash/test_legacy_identity_clash.py`
(fails on `d6c47790`; register under `studyplan`). Either half alone is
coherent; both together are redundant.

## Deviations from the C5 table, and why

- **C1-C-2, suffix instead of refusal:** the table's decided fix ("the
  writer never produces a stem the reader skips. Suffix it") overrides the
  workbench finding's typed-refusal suggestion. No new refusal site, so no
  A9 witness needed.
- **C1-C-1 and C1-D-2 each required updating one existing test** that pinned
  the pre-fix behavior (both staled dossiers by body-revising analysed
  notes through `note.revise`). Both updates keep the machinery they
  exercised fully covered; the new boundary has its own test in each file.
- **C1-E-1 required re-shaping a boundary test** that had pinned the silent
  exclusion as deliberate — flagged above; this is the one place the branch
  changes something a previous session may have intended as a design
  decision, and it deserves Aram's eyes at landing.

## Verification summary

- Eight regression tests: all fail on the branch base, all pass at the tip.
- Focused existing test files, one pytest process at a time, per commit —
  19 files, ~750 tests, all green (counts per finding above).
- Recording discipline: two recordings re-recorded where the decided
  behavior changes them (`review.apply`), two added as new A9 witnesses
  (`note.revise`), all other touched-capability recordings replay
  byte-identical.
- One full re-check I did NOT run locally, per the ground rules: the entire
  suite. That is what the release-pair gate below is for.

## CI

- Run [40138998182](https://github.com/Aram164/LearningOS/actions/runs/40138998182)
  (core `a98c9e0e`): **failed** at `make lint` — 3 import-order/unused-import
  errors in the two C1 test files; fixed by `e1a305a`. Lesson recorded:
  run `.venv/bin/ruff check` before pushing, not only pytest.
- Run [40139293836](https://github.com/Aram164/LearningOS/actions/runs/40139293836)
  (core `e1a305aa`): **failed** after the full ~2h06 gate at
  `test_pre_push_hook.py::test_paired_marks_cover_every_live_ui_reader` — the
  hook's scanner pattern-matches `parent / "obsidian-ui"` in any test file as
  a live-sibling access, and my copied backup test built its synthetic UI
  with exactly that shape. Fixed by `555b581` (synthetic UI in tmp, passed
  as `--ui-root`; the literal also removed from the test's own docstring).
  Lesson recorded: the paired-boundary ratchet and the prose scanner read
  test-file *text*, so a copy that mentions UI paths can fail CI without
  ever importing the live checkout.
- Run [40148452560](https://github.com/Aram164/LearningOS/actions/runs/40148452560)
  (core `555b581a`): **SUCCESS** (2026-10-25 00:53:27Z → 02:33:17Z, 1h39m50s
  on the unsharded main workflow). Counts: **8530 passed, 7 skipped, 1
  deselected, 2 xfailed in 1:38:15** (the pytest leg of the paired gate);
  validator 0 errors / 1471 warnings; warning baseline clean (1462 across 38
  signatures, none new). Before dispatching, the scanner-heavy validation
  files were run locally as a sweep (1921 passed, 1 skipped across
  arch/hygiene/move-map/mismatch/warning-baseline/pre-push-hook), so both
  known static-scanner classes were covered. The population is 23 tests
  above the 8507-count reference at `eb087e3a` that C3 recorded — my 10 new
  tests (8 regression files' tests + 2 scenario witnesses) plus the tests
  that landed on main between `eb087e3a` and `d6c47790`; C3's sum-equals-
  collection proof is unaffected since this run is unsharded.

**The branch is gated and ready; landing is Aram's call.**
