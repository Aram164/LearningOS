# C1 verification pass (L1-234, 2026-10-24)

GLM-5.3 verification of every C1 finding, in a fresh session, per the
campaign's verification-pass spec: re-run each test on `main`, try to refute
the diagnosis, mark CONFIRMED or REFUTED.

- **Clone:** fresh from GitHub (`Aram164/LearningOS`) at
  `~/los-glm-c1-verify-2026-10/repository`, own venv, base
  `d6c4779029e366718b71bda158d2aa8f9da1db39` (= `origin/main` at clone
  time). Nothing committed, nothing pushed.
- **Method:** all nine finding tests copied into the clone's `tests/`
  (registered in `tests/group_map.py` locally, `studyplan`/`gateway` as the
  batches had them), each run as the only pytest process, one file at a
  time. Refutation = reading the cited handler/validator/contract lines
  myself plus targeted probes where the diagnosis hinged on a behaviour the
  delivered test did not itself exercise (three probes, noted below).
- **Result: 9/9 CONFIRMED, 0 REFUTED.** Every test fails on base `main`
  for the documented reason. Per-finding detail below, then the test defects
  and citation corrections found during refutation.

| # | Batch / capability / slug | Reproduced on main | Verdict |
|---|---|---|---|
| 1 | C1-A `module.attempt.record` graded-attempt-dead-end | yes (exit 2, `MOD-GRADE`) | **CONFIRMED** |
| 2 | C1-A `module.create` legacy-identity-clash | yes (`--check` rc 0; apply probe rc 0) | **CONFIRMED** (low: unreachable in a green tree) |
| 3 | C1-B `review.apply` partial-apply-hides-remainder | yes (`assert 'shelving' in []`) | **CONFIRMED** |
| 4 | C1-C `note.revise` revise-voids-dedicated-guarantees | yes, both witnesses | **CONFIRMED** (witness-2 test has a precondition bug, see below) |
| 5 | C1-C `garden.seed.create` invisible-reserved-slug | yes (create rc 0, read refuses) | **CONFIRMED** (low: needs no-README garden or case-sensitive FS) |
| 6 | C1-D `capture.create` same-second-file-capture-overwrite | yes (third capture rc 0, bytes replaced) | **CONFIRMED** (latent: same-second collision practically unreachable in daily use) |
| 7 | C1-D `material.context` zero-limit-widened | yes (rc 0, items returned) | **CONFIRMED** |
| 8 | C1-E `backup.manifest` symlinked-subtree-silent-omit | yes (rc 0, no trace of subtree) | **CONFIRMED** (latent: no symlinked dir in the live tree today) |
| 9 | C1-E `coordination.section.revise` whole-document-reflow | yes (sibling lines changed) | **CONFIRMED** (minor: blank lines only) |

## 1. C1-A `module.attempt.record`: graded attempt dead end — CONFIRMED

Re-run: fails on `main` exactly as documented — steps 1–2 succeed, the
correction (termin 3, `result: "withdrawn"`, no grade) exits 2 with
`VALIDATION_FAILED` / `E MOD-GRADE … carries a grade but result is
'withdrawn'`, row unchanged.

Refutation attempts, all failed:
- **"Supply `grade: null` to clear it."** Impossible twice over: the
  handler reads `grade = req.get("grade")` and writes only
  `if grade is not None` (`app/handlers/admin.py:76,120-121`), so null and
  omitted are indistinguishable; and the request schema types `grade` as
  `number` (null is not valid JSON for it — Claude's C1-A verdict checked
  the schema; I read the handler path).
- **"Another capability can fix the row."** Grep over
  `app/handlers/*.py`: the only writer of `attempts` is `module_attempt`
  itself (`admin.py`, the `data["attempts"]` block). `module.sitting.update`
  touches only `examination.sittings[].withdrawal_deadline`.
- **"Complete the module first, then withdraw."** `MOD-GRADE`
  (`derive/validation/curriculum.py:21-27`) only tolerates the stale grade
  when `status == completed` — that path requires recording a *false*
  module status to express a true exam fact. Not a correction path.

Contract basis verified: `capabilities.yaml` `module.attempt.record`
invariants say "appends a new attempts row **or updates the row for the same
termin**" with "optional grade/notes" — the update half is unreachable for
any non-passed result once a grade exists. Citation correction (from
Claude's verdict, lines I did not re-check — the no-hand-edit rule is
CLAUDE.md hard rule 12, not OPERATOR boundary 16; boundary 16 covers plans):
the conclusion is unchanged.

## 2. C1-A `module.create`: legacy-registry identity clash — CONFIRMED

Re-run: fails on `main` — `--check` exits 0 (`ok:true`,
`expected_write_paths` naming the destination). **Probe (mine):** the V2
apply from the same fixture also succeeds (rc 0, `replayed: false`,
`curriculum/modules/module-legacy-clash/module.yaml` written), so both
halves of the finding's claim are reproduced, not just check mode.

Refutation attempts:
- **"`module.create` is the migration path; refusing legacy ids would make
  MODULE-MIGRATION-red trees unrepairable."** Rejected: the sanctioned
  migration is the dedicated retired tool `tools/migrations/curriculum_v2.py`
  ("preserves every durable note/source identity"), not an ad-hoc
  `module.create` package. Refusing would push the operator to the
  fact-preserving path.
- **"The registry is not a canonical identity."** Rejected:
  `_load_legacy_modules` loads `records/modules.yaml` into
  `repo.legacy_modules`, and in partitioned mode `load_modules`
  (`store/loading/curriculum.py:206-232`) registers only partitioned
  records — so the created duplicate shadows the legacy record's facts
  (e.g. its `attempts`) from every view, while `MODULE-MIGRATION`
  (`derive/validation/curriculum.py:79-83`) stays green because a duplicate
  satisfies coverage.
- **Honest reachability limit (also in the finding):** in any
  validation-green tree every legacy id is already covered, and for a
  covered id the *filesystem* half of the check refuses. The gap needs a
  tree with an uncovered legacy record (restored snapshots, partially
  migrated branches) — which is MODULE-MIGRATION-red to begin with. The
  declared refusal ("an existing canonical identity or file is refused")
  still has no registry half at all; `_creation_destination_problems`
  (`app/handlers/plan.py:940-957`) is filesystem-only, as cited.

Severity agrees with Claude's verdict: low, contract/code mismatch, already
filed as Aram164/LearningOS#27.

## 3. C1-B `review.apply`: partial apply hides the remainder — CONFIRMED

Re-run: fails on `main` — after applying `proposal-alpha` out of a two-item
packet, `shelving.items` still holds both items but the regenerated
manifest's `review_items` is `[]`.

Refutation attempt — **"unselected means declined, so dropping the queue row
is the designed semantics."** Rejected by **probe (mine)**: a later
`review.apply` with `selected=["proposal-beta"]`, submitted while
`state: applied`, **succeeds** (rc 0, `replayed: false`,
`note-probe-b.md` written). The system itself treats the remainder as
pending and appliable. So the two coherent designs are both violated at
once: the remainder is neither declined (late apply would refuse) nor
published (the queue row is gone), and the packet claims `state: applied`
while half its items are unwritten.

Mechanism verified in source: `shelving_apply` sets
`shelving["state"] = "applied"` unconditionally (`app/handlers/capture.py`,
the line after the per-item write loop) and never records per-item
application; `build_review_items` publishes a shelving row only while
`state == "proposed"` (`derive/projection/review.py`). Contract basis
verified: `capabilities.yaml` `review.apply` invariants "explicit approval",
"selected proposal is atomic". Claude's verdict additionally established UI
reachability (per-item checkboxes in `shelving-view.ts`) — I did not
re-check the UI; marked as Claude's finding, not mine.

## 4. C1-C `note.revise`: voids dedicated guarantees — CONFIRMED

Re-run: both witnesses fail on `main`. Witness 1 (question retarget) fails
as documented: `note.revise` exits 0 and the stored `atlas_question.target`
changes. Witness 2 (reference binding) initially failed at its *precondition*
(line 147) — a defect in the delivered test, not evidence; see "Test
defects" below. With the precondition comparison fixed in my copy (one
line), it fails at line 171 for the documented reason: after the revise,
`material_analysis` still claims `frozen_input_bytes`/`frozen_input_sha256`
over bytes the file no longer holds.

Refutation attempts:
- **"The reviewed envelope is the approval; anything approved goes."**
  Rejected: `ARCHITECTURE.md` §5.7 states the design the general path must
  uphold — the `reference` and `question` roles keep their dedicated
  capabilities "so provenance bindings and question wording can never be
  bypassed by the general path". The dedicated front door enforces it:
  `atlas.py` refuses a target change ("the original question target is
  preserved", site `atlas.question.save.retarget-refused`), matching the
  contract invariant "learner wording and original target are preserved".
  `note_revise` (`app/handlers/notes.py:186-199`) checks only id, type and
  role; everything else is written verbatim.
- **"A downstream net catches the stale facts."** Rejected: grep over
  `derive/validation/` for `atlas_question` / `material_analysis` — zero
  hits, confirming the finding's claim.
- **"The binding is a creation-time snapshot."** Rejected by the schema's
  own words: `note.schema.json` `material_analysis.frozen_input_bytes` —
  "the note body is exactly the file's last N bytes". A standing claim
  about the live file.

## 5. C1-C `garden.seed.create`: invisible reserved slug — CONFIRMED

Re-run: fails on `main` — the create succeeds and receipts
`knowledge/garden/readme.md`, then `note-read garden-note-readme` (the
stable id the system's own `garden_id` derives for that file) refuses with
"note not found".

Refutation attempts:
- **"The reader admits it somewhere else."** Rejected:
  `load_garden` (`store/loading/knowledge.py`) skips any file whose stem
  lower-cases to `readme` (and dot/underscore names), so the seed is absent
  from `repo.garden_notes` — the single source for `note.content`'s garden
  branch, `note.search --type garden-note`, and the Nebula projection.
- **"The writer cannot actually produce the slug."** Rejected:
  `_seed_slug` (`app/handlers/capture.py:53-71`) is purely mechanical
  (`re.sub` over the title) with no reserved-name check; "README" →
  `readme`.
- Reachability limit (Claude's verdict, not re-measured by me): in Aram's
  live tree the garden already has a `README.md` and macOS APFS is
  case-insensitive, so the collision loop writes `readme-2.md`, which the
  reader admits. The defect needs a garden without a README or a
  case-sensitive filesystem — the mini-repo shape. Real asymmetry, low
  severity.

## 6. C1-D `capture.create`: same-second file capture overwrite — CONFIRMED

Re-run: fails on `main` under the frozen clock
(`LOS_OBSERVATIONS={"now": …}`) — the third capture exits 0 and the second
capture's receipted file `work/inbox/20261024-120000-notes.md` now holds the
third capture's bytes.

Refutation attempts:
- **"The engine refuses the overwrite."** Rejected empirically by the test
  itself (bytes replaced, rc 0); the file branch takes exactly one fallback
  name and never re-checks it (`app/handlers/capture.py:109-111`
  — `target = inbox / src.name; if target.exists(): target = inbox /
  f"{stamp}-{src.name}"`), while the text branch loops
  `while target.exists()` with a serial, and every other writer in the
  handler refuses an existing destination. Contract basis verified:
  `capture.create` invariants "original input is preserved" / SHA-256 byte
  binding.
- **"Same-second collisions are unreachable."** Partially sustained — this
  is Claude's reachability verdict (operator lock + ~3 s commits per
  capture make sequential same-second commits practically unreachable; the
  in-process-host scenario is an assumption): the finding's own honest
  scoping says the clock freeze stands in for same-second arrivals, which
  are realistic under replay/characterization and fast hosts. Latent, not
  daily-use. I did not re-measure commit times.

## 7. C1-D `material.context`: `--limit 0` widened to 20 — CONFIRMED

Re-run: fails on `main` — `--limit 0` exits 0 and returns items
(`total=1` in the fixture) instead of refusing.

Refutation attempts:
- **"Zero means 'default'."** Rejected: the request schema itself
  (`system/schema/requests/material.context.schema.json`, property `limit`)
  says "page size from 1 to 20 items", and the shared window rule the
  handler calls next (`app/handlers/_shared.py`, `window_values`) refuses
  anything outside `1..maximum`. The declared refusal site
  (`material.context.bad-window`) is unreachable for zero because
  `req.get("limit") or 20` (`app/handlers/materials.py:1205`) substitutes
  the maximum before the check — a falsy-zero truthiness bug, exactly as
  diagnosed. `inbox.content` reads its limit verbatim and refuses zero; the
  asymmetry is real.
- Note (Claude's): the schema states 1..20 only in its description (no
  `minimum`), so the schema alone also lets 0 through — the fix belongs in
  the handler. Verified consistent with what I read.

## 8. C1-E `backup.manifest`: symlinked subtree silently omitted — CONFIRMED

Re-run: fails on `main` — `backup-manifest --stdout` exits 0 over a declared
`records/` tree containing `records/archive -> ../../outside-stash/`
(regular file inside), the manifest is schema-valid with 222 entries, and
nothing anywhere records the skipped subtree (the one `archive` hit is the
unrelated declared tree `archive/workspaces`).

Refutation attempt — **"the contract says 'never follows symlinks', so
omission is compliant."** The letter does permit not *following*; what it
does not permit is *silence*. The module's own established principle
contradicts the silent skip: a declared-but-unreadable directory refuses
(`_refuse_unreadable` via `onerror`), a declared tree that is itself a
symlink refuses (`_inside`), and the known symlink farm is recorded as
explicit alias data (`_materials_aliases`). `_admitted_paths`
(`app/backup_manifest.py:295-307`) walks with `followlinks=False` and
`_admit_file` (174-192) returns False for symlinks — neither raises nor
records for the in-tree symlinked-subdirectory case, and the restore
verifier shares the same walk, so a restore also verifies green. A backup
inventory that quietly answers incompletely is the failure mode the module
exists to prevent. The test is fix-agnostic (refuse / cover / record all
pass), so the verdict does not depend on choosing the fix shape.

Reachability (Claude's, read-only): no symlinked directory exists in the
live Core tree today (the only symlink is the root `CLAUDE.md` file); the
materials `.flat` farm is recorded as aliases. Latent.

## 9. C1-E `coordination.section.revise`: whole-document reflow — CONFIRMED

Re-run: fails on `main` — the apply exits 0 and commits; the untouched
Priorities section's parsed lines change from `['(none)', '']` to
`['', '(none)', '']` because `serialise`
(`tools/learning_os/domain/render.py:84-103`) forces exactly one blank line
after every heading and trims every section's edges, and
`replace_h2_section` (render.py:106-117) routes the whole document through
it — the function's own docstring says "leaving its neighbours untouched".

Refutation attempt — **"blank lines are presentation, not content."**
Weighed and rejected as a defence: the contract invariant
(`capabilities.yaml`, `coordination.section.revise`) says "frontmatter and
**other section content** are preserved" with no normalisation carve-out;
the reviewed diff presents a single-section replacement; and the same
mechanism underlies `workspace.next-action.update`, whose invariant reads
"only the Next Action section content changes". The existing
`test_coordination_revision.py:52-54` compares siblings with `.strip()`,
which is precisely why the suite never saw it. Severity minor, as the
finding itself states (no text changes, only blank lines; 5 of 6 live
coordination/CONTEXT files are already in normalised form — Claude's
measurement, not re-run by me).

## Test defects and citation corrections (for whoever lands fixes)

1. **C1-C witness-2 test bug (must fix before the test goes into an
   issue):** `test_revise_voids_dedicated_guarantees.py` stores
   `frozen_input_sha256` as bare hex (schema-compliant — the schema pattern
   is `^[0-9a-f]{64}$`) but its helper `_binding_describes_body` compares
   against `"sha256:" + hex`, so the *precondition* at line 147 fails on the
   untouched note. With the comparison fixed to accept bare hex (one line,
   done in my clone only), the test fails at line 171 for the documented
   reason. Found independently by me and by Claude's C1-C verdict; the
   finding's diagnosis is unaffected.
2. **C1-A graded-attempt citation:** the no-hand-edit rule is CLAUDE.md
   hard rule 12, not OPERATOR boundary 16 (boundary 16 covers plans).
   Claude's correction; conclusion unchanged.
3. **C1-E issue-number citations:** the "#25" and "#31" in the
   backup.manifest finding are history numbers from code comments in
   `backup_manifest.py`, not GitHub issues. Claude's correction.

## What this pass did not do

- No fixes written, no issues filed, nothing committed or pushed (campaign
  rule). The `tests/group_map.py` registration and the one-line witness-2
  precondition fix exist only in my clone.
- Live-tree reachability measurements (garden README/APFS, capture commit
  timing, symlink census, coordination normalisation census) are Claude's
  verdicts, read but not re-measured here; each is marked as such above.
- The batches' "attacked and held" sections were not re-hunted (owned by the
  batch sessions and their verdicts).
