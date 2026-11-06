# Relational delegation — Stage 2.5 spike report (2026-11-06)

Status: measured-spike deliverable on branch `research/relational-delegation-2026-11-06`,
authorized by the Gate 2 decision (2026-11-06): "authorize the redefined Stage-2.5
(Role B spike + optional guard-only spike, venv allowed in-clone, production files
untouched, stop and report measured numbers)". This report replaces the two most
uncertain ESTIMATE figures in Deliverable 2 with measurements and states one
correction the measurements force. Companion documents: the Stage 1 inventory and
Stage 2 pilot design (unchanged; their ESTIMATE labels stand — this report
supersedes their numbers where they disagree).

## 1. What was built

Labelled spike directory `workbench/spikes/roleb-sqlite-2026-11-06/` (throwaway;
never imported by production code; committed on this branch only):

| File | wc -l | code lines (non-doc, non-blank, non-comment) | Role |
|---|---|---|---|
| `spike_store_sqlite.py` | 377 | 265 | the SQLite-backed store behind the existing `store.py` API surface (280/193 before the repair rounds; 343/~238 after round 2; final after the secure-temp round 3) |
| `spike_swap.py` | 57 | 34 | pytest plugin: installs the spike as `learning_os.store.derived.store` (sys.modules + package attrs + rebind of already-imported modules) |
| `spike_behavior.py` | 311 | 254 | 47 scenarios: the oracle tests' format-pinned scenarios ported to the DB medium, plus the adversarial rounds (identity, foreign stores, corruption, planted temp symlink) |

Production files under `tools/` were not edited. The venv (`.venv/`, gitignored,
Python 3.12) was created in the clone as authorized; dependencies PyYAML,
jsonschema, pypdf, pytest installed. Design decisions in the spike, mapped to
the brief's §6.4 contract: hash verification retained on every lookup (the
reviewer caveat: policy SQLite does not absorb); corrupt DB on a read path is a
miss, never an error; write paths rebuild-or-refuse (one recreate attempt, then
`TransactionFailure` — verified against a read-only parent); versioned schema +
root fingerprint verified on open, mismatch rebuilds (sound: node keys are
content-addressed); publication is one transaction; path-safety checks retained;
no WAL (no measured concurrency need).

One harness bug found and fixed during the spike, worth recording because it is
a swap-harness lesson, not a store defect: importing the package `__init__`
transitively imports `engine.py`, which binds the real store functions before
the facade lands — the plugin therefore rebinds every already-imported module
whose attributes are identity-identical to the real functions.

## 2. Parity evidence

Oracle: the derived-store/validation-cache/search/compute test suites, run
against the unmodified production baseline and then against the **final
repaired spike** (secure-temp round included) swapped in behind the same API
surface — one consolidated run in this worktree against the repair-round-3
commit, whose numbers are the only ones quoted anywhere in this document.
Baseline: **224 passed**. Swapped: **199 passed, 25 failed** (the fresh run
reproduces the consolidated numbers exactly).

**Stated plainly: full migration parity is NOT established by this spike.**
What is established: all 25 failures are classified one-to-one in Appendix C,
and our evidence says each is format-only — the failing assertion surface is
the physical file path or file bytes (two failures are subprocess-boundary
artifacts of the swap harness), never diagnostic ordering, attribution, or
presence, which are pinned end-to-end by the suites that pass unmodified
(`tests/test_scenarios.py` recorded sequences byte-identical; all behavioral
engine/store suites green). The reviewer judges the classification; until
that judgment lands, treat parity as not established. Every failure is one of:

1. **File-format pinning (23 tests).** The test hand-crafts the physical layout
   the DB replaces: writes `state-v1.json` by hand (`test_corrupt_cache_rebuilds_quietly`,
   `test_wrong_schema_version_is_a_miss`, `test_misshapen_entries_are_skipped_selectively`,
   `test_stored_state_carries_the_generated_header`, `test_missing_blob_is_a_miss`,
   the two `test_search_index.py` self-heal tests), overwrites or removes blob
   files (`test_tampered_blob_is_a_miss`, `test_symlinked_blob_is_a_miss`,
   `test_missing_blob_rebuilds_quietly`, `test_compute_once` corrupt sidecar,
   `test_search_index` tampered/missing), asserts blob-file existence after
   sweep/invalidate (six `test_derived_state.py` sweep/staging tests), or counts
   `_atomic_write` file writes (`test_evaluate_many_publishes_one_index_write`).
   Each has a DB-equivalent scenario in `spike_behavior.py` that passes.
2. **Process boundary (2 tests).** `test_status_memoizes_and_reuses_cache_byte_identical`
   and `test_validate_offline_writes_cache_with_header_and_pins` spawn `los` /
   `validate` subprocesses; the spike swap lives in the pytest process only, so
   the child wrote a JSON cache the in-process DB read cannot see. A real Stage 5
   ships the store in production code and all processes use it — this is a
   harness limitation, not a store defect.

Footnote (counting regimes): an earlier in-research run measured 199/25 with
the harness bug of §1 (engine wrote JSON while tests read the DB), and a
Stage 5 worktree mid-state measured 200/24 (its production store and
engine-side changes make the two subprocess tests pass naturally and flip
one removed-machinery pin). The consolidated run above supersedes both; no
other numbers are quoted.

The behavioral contract held everywhere it was reachable through the API:
all `evaluate`/`evaluate_many` reuse, batch-merge-over-concurrent-entry,
failure-publishes-nothing, staging-defers-until-commit, invalidate semantics,
warm/cold receipt-cache equality (`test_compute_once` warm/revalidate pass under
the swap), search cold/warm agreement, `LOS_NO_CACHE` bypass. `spike_behavior.py`
prints **28/28 PASS**, covering: read-path never creates; empty publish and
no-op invalidate create nothing; missing/tampered/forged/unparseable blob rows
are misses (hash verification retained); corrupt DB file reads as a miss and
rebuilds on write; unrecoverable corruption refuses with `TransactionFailure`;
wrong schema version and relocated-root fingerprint rebuild on write / miss on
read; symlinked derived-state dir and symlinked DB file refused; identical
values share one blob row; sweep counts match the file store's semantics.

## 3. The measured ledger — and one correction it forces

| Quantity | Value | Status |
|---|---|---|
| Production `store.py` superseded by the spike module | 308 wc-l / 189 code → **377 wc-l / 265 code** | **measured: +69 wc-l / +76 code — NOT line-neutral.** Atomic rebuild, secure temp creation, and retained path safety are new machinery (brief §4: each new obligation is machinery charged against the savings — measured) |
| Retained policy inside the spike module (path safety 13, hash verify 4, blob-string parity 2, identity binding 2) | ≈ 21 code lines | measured — the reviewer caveat honored, not absorbed |
| Engine-side deletions (states cache −12, deferred-index batching −14, commit-staging plumbing −14) | ≈ −40 wc-l | **still ESTIMATE — engine untouched by this spike** |
| `__init__.py` re-export shrink | ≈ 0 (not −25 as estimated) | measured correction: the same-API-surface approach preserves the re-exported names, so the estimated −25 does not materialize unless the API itself shrinks |
| Micro-benchmark (in-process, 200 stores + 200 lookups + 100 read_states + 1 sweep, 50-key values) | JSON: 133–140 / 20–21 / 6–7 ms; SQLite: 149–157 / 44–45 / 11–12 ms | measured, informal: ≈1.1–2× slower per op, sub-second at this scale; the spike opens a connection per call (a real integration holds one per session, which would narrow the gap); no material regression claim needed at S23's loader-dominated scale |

**Correction the measurements force (final, after repair rounds 2–3):**
Deliverable 2's Role B net of ≈ −160 L ESTIMATE does not survive measurement.
The final repaired store is **+69 wc-l / +76 code lines larger than the JSON
store it replaces** (377/265 vs 308/189) — the brief's own §4 prediction
playing out in measured form: the atomic-rebuild protocol, secure temp
creation, and the path-safety policy SQLite does not absorb are new
machinery, each charged against the savings. The deletion side of the D1
ledger assumed engine-side and `__init__` simplifications that either remain
unproven (engine ≈ −40, ESTIMATE) or were based on an API-shrinking design
this spike did not test (≈ −25 → ≈ 0). The honest statement: **the store
slice is a measured line INCREASE; the only remaining deletion is the
engine-side ESTIMATE, and the robustness-vs-simplicity trade is exactly what
the Stage 5 GO/NO-GO must price on these numbers.** This supersedes the
"line-neutral" phrasing in pilot §13, which described the pre-repair store.

What measurement *strengthens*: the qualitative core of the Role B case. The
hand-reasoned machinery — five corruption→miss paths in `read_state`, five in
`lookup`, blobs-first/state-last choreography, RMW merge, "crash-safe by
construction" GC — became schema constraints, one transaction, one PK upsert,
and one `DELETE ... NOT IN` in the spike, and every behavioral test that
exercises those invariants through the API passes unchanged. That is dimension-4
ownership transfer, demonstrated, not argued. Whether a +69 wc-l / +76 code
line store replacement plus an ≈ −40 L engine ESTIMATE justifies adopting
SQLite for `generated/`-level cache state is now an honest reviewer judgment
between "dimension-4 win, measured" and "no dimension-1 win at this
boundary".

### Durable costs, scored on all six dimensions

The ledger above scores the store body only. Delegating the store also
carries permanent costs a full comparison must charge — scored here so
"simpler" is judged on all six dimensions of the brief's §9, not line count
alone:

- **SQL schema maintenance**: the `_SCHEMA` DDL, its versioned `meta`
  identity rows, and the schema-version bump discipline are a permanent
  second schema surface beside the stored-record schemas.
- **Migration/rebuild logic kept forever**: the build-to-temp → verify →
  rename protocol (and its `.rebuild` temp discipline) is permanent
  machinery the JSON layout never needed at this scope; it exists precisely
  so the rebuild is atomic.
- **DB-medium test replacements carried permanently**: the 23 format pins
  become permanent DB-medium tests (Appendix C's replacements) in addition
  to the behavioral suite — a verification-burden line (dimension 5), not a
  saving.
- **Failure-class ownership split across two layers**: identity and
  path-safety refusals stay Python; byte corruption and missing rows become
  SQL-medium misses. The ownership table in
  `system/developer/components/derived-store.md` is the contract that keeps
  that split honest (dimension 4's bookkeeping).

The measured result stands, restated against the final code: the store
replacement is **+69 wc-l / +76 code lines**, with the engine-side ≈ −40 L
still ESTIMATE — the original −160 L prediction has not materialized at the
store boundary, and whether the engine-side rewrite changes that is the open
question a measured Stage 5 decision must answer. The durable costs above
are the reason the number moved: robustness obligations are machinery, and
the ledger charges them.

## 4. What a real Stage 5 would inherit from this spike

- Rewrite list: the 23 file-format-pinning tests (Appendix C rows 1–23; the
  spike's behavior script contains the DB-medium scenario corpus they port
  to) and the 2 subprocess-boundary tests (rows 24–25) become in-process once
  the store ships in production code.
- Engine-side work needed for the remaining ≈ −40 L: session cache removal
  (B-tree lookups need no amortization), deferred-index batching removal (each
  publish is one transaction), `commit_staging` persistence half (COMMIT).
- The `ledger_only`/receipt chain, identity.py digests, model.py node keys are
  untouched and stay, as inventoryed in D1 §K5.

## 5. Spike 2 — route-guard unification

Authorized as optional/narrow; measured result in
`workbench/spikes/route-guard-2026-11-06/REPORT.md`: parity **98/98** including
the recorded-sequence oracle, but the measured ledger is a **+62 wc-l net
increase** (672 → 734; 65 removed, 127 added) — with byte-exact message parity
the unification costs more scaffolding than the bare `if` conditions it
replaces, so its value is dimension-2 only (one implementation of the drift-prone guard
comparison replacing the three validator guard blocks and the references.py
legacy-matcher call site; `derive/routes.py` `exact_selection_matches`
remains for the projection caller `records_curriculum.py:141`, and adopting
the helper there is a separate future decision — see the guard spike
REPORT.md scope correction). The pilot's ≈ −19 L net estimate for the guard
collapse does not survive measurement.

## 6. Repair round (2026-11-06, review round 2)

An independent review of the committed bundle confirmed three spike defects;
all three are repaired in the labelled spike (this directory), and Stage 5
approval stays blocked until the repair is reviewed. Production files were
not touched; the Stage 5 branch (`stage5/derived-store-sqlite-2026-11-06`,
6 commits) remains parked unmerged **and inherits defects 1–2** — its repair
is part of the unblocked Stage 5 work, not this round.

1. **Destructive SQL through the unguarded read path** — the sweep executed
   `DELETE` + `commit()` on a `_open_for_read` connection with no identity
   check, and the read open skipped the `generated/`-symlink refusal and the
   containment check, so a symlinked `generated/` could reach another root's
   store and the sweep deleted rows there. Repaired: `_open_for_read` now
   applies both checks (refuse → miss); the sweep's deleting branch runs
   only through `_open_for_write` with an explicit `_identity_ok` re-check
   before the `DELETE`; a dry run keeps the read path; a corrupt database is
   a zero-shaped miss on a dry run and a `TransactionFailure` refusal on a
   real sweep; a sweep never creates the store.
2. **Non-atomic rebuild** — identity mismatch did an in-place
   `executescript("DELETE …")` and the corrupt path did
   `unlink()` → recreate. Repaired: `_rebuild_database` builds the
   replacement in a same-directory temp file, binds identity, verifies, then
   `os.replace()`s onto the live path. No in-place clears; no
   unlink-before-recreate. The old database survives untouched until the
   atomic rename; a build/verify failure raises `TransactionFailure` and
   removes the temp; a crash before the rename leaves the old database plus
   an orphaned `.rebuild` temp collected by the next attempt.
3. **Vacuous assertion** — `spike_behavior.py` ended one check in `or True`
   (the real check existed two lines down). Repaired: the check now asserts
   the real property on its own root.

Adversarial scenarios added for the three reproduced failures, each asserting
refusal **or** miss **and** that the foreign/mismatched database was not
modified: invalid schema version (reads refuse, DB byte-identical after
reads, write rebuilds), symlinked `derived-state/` at a foreign store (read
miss, write and sweep refused with `TransactionFailure`, foreign store
byte-identical after every attempt), corrupt DB file (reads are misses that
leave the corrupt file byte-identical, write rebuilds atomically, no
`.rebuild` temp left). Behavior script re-run: **43/43 scenarios pass**
(28 original — one now honest — plus 15 adversarial checks). The
consolidated swapped-suite run against the repaired spike: **199 passed,
25 failed** (§2, Appendix C).

Parity wording corrected per the same review: the "zero behavioral failures"
claim is replaced by the plain statement in §2 plus the per-failure evidence
in Appendix C. Two documentation corrections are applied in §5 (guard
unification scope) and §7 (NO-GO reconciliation; engine-side ≈ −40 L marked
ESTIMATE).

### Repair round 3 (2026-11-06): the secure-temp protocol

A further review reproduced a NEW blocker against the round-2 repair: a
dangling symlink planted at the fixed temp name `state-v1.db.rebuild`
bypassed `tmp.exists()` (it follows the link), `sqlite3.connect(tmp)` then
followed it and created/wrote an external file, and `os.replace(tmp, db)`
renamed the symlink itself onto the live store path — a store hijack.
Confirmed in source at the consolidation commit.

Repaired with the complete protocol, not a spot patch: the rebuild temp is
created with `tempfile.mkstemp` in the store's own directory (exclusive,
unpredictable, created by us — a pre-planted symlink cannot occupy the
name), lstat-verified as a plain regular file with link count 1 before
connect, re-verified after the build together with the `generated/` and
destination symlink state and the temp's own bound identity, and only then
`os.replace`d onto the live path (the rename does not follow a destination
symlink). Failure points unchanged: any refusal leaves the old database
untouched; a crash before the rename leaves an unpredictable orphan temp.

Regression test from the reproduced attack, added to the adversarial
section: a dangling symlink planted at the historical fixed name, a forced
rebuild, then assertions that the store rebuilt and serves, the planted
symlink was never followed or replaced, the external target was never
created, and the live store is a plain regular file. Fresh runs against the
final code: behavior suite **47/47**; swapped oracle suite **199 passed,
25 failed** (Appendix C stands unchanged). Ledger recalculated against the
final code: **+69 wc-l / +76 code lines** vs the 308/189 JSON store —
stated plainly in §3, not softened.

## 6a. Verification and honesty notes

Everything above is reproducible from the clone:

```
# baseline (green)
PYTHONPATH=tools .venv/bin/pytest tests/test_derived_state.py \
  tests/test_derived_engine.py tests/test_validation_cache.py \
  tests/test_search_index.py tests/test_compute_once.py \
  tests/test_context_dossiers.py tests/test_module_surface.py -q        # 224 passed
# spike swap
PYTHONPATH="tools:workbench/spikes/roleb-sqlite-2026-11-06" \
  .venv/bin/pytest -p spike_swap <same files> -q                        # 199 passed, 25 failed (fresh run on the final code; Appendix C)
# DB-equivalent corruption/rebuild/identity scenarios
PYTHONPATH="tools:workbench/spikes/roleb-sqlite-2026-11-06" \
  .venv/bin/python workbench/spikes/roleb-sqlite-2026-11-06/spike_behavior.py   # 47/47 (final code, incl. adversarial rounds)
```

Expected-output comments in this section are commit-relative: they state
what the branch tip at the spike-repair commit produces — re-run before
trusting them on a later revision.

Two baseline environment facts, documented so they are not mistaken for
findings: the two `test_module_surface.py` failures seen without
`PYTHONPATH=tools` in the environment are subprocess-import tests needing that
variable (CI provides it); `tests/test_module_surface.py` is included in both
runs above and passes in both. Micro-benchmarks are informal single-machine
samples, not the Stage-3 gate bound. No test was claimed passed that did not
run and pass; nothing under `tools/` was edited; the worktree is clean apart
from this spike directory and this report.

## 7. What the reviewer is asked to decide

**Resolved 2026-11-06 by owner override (Gate 2.5):** Role B proceeds to
Stage 5; the guard unification is adopted at +62 L. See the pilot
deliverable §13. The questions below are retained as the record of what
this spike asked.

**Scope reconciliation (review round 2):** the Stage 1 NO-GO for SQL on
reference validation stands and covers exactly the reference-validation SQL
arm; the Gate 2.5 override concerns the Role-B derived-store (Stage 5) and
the Python guard unification, and the post-Role-B queue's
reference-validation entry is a *future, separately gated* decision — no SQL
arm for references is implied by the override. The engine-side ≈ −40 L
figure remains an ESTIMATE throughout (engine untouched by the spike); the
store-side numbers are the measured ones.

1. Accept the measured correction: Role B's net-deletion case is ≈ line-neutral
   at the store boundary, ≈ −68 wc-l with the engine-side estimate — the Q4 GO
   now rests primarily on the measured dimension-4 ownership transfer rather
   than line count.
2. Decide whether that case justifies a Stage 5 assignment (which would include
   the engine-side rewrite this spike did not attempt), or whether Role B is
   retired with the measured evidence appended to the inventory.
3. Spike 2's route-guard unification result (same decision pattern: measured
   dedup value vs refactor cost, no SQL involved).


## Appendix C — per-failure classification of the 25 swapped-suite failures

Evidence basis: the consolidated run against the repaired spike in this
worktree (spike-repair commit, 2026-11-06): baseline 224 passed / swapped
199 passed, 25 failed. One row per failed test. For every failure, the
failing assertion surface is the physical medium (file path, file bytes, or
file-write counting) — never diagnostic code, message text, attributed path,
ordering, or presence, which are pinned by the suites that pass unmodified
(`tests/test_scenarios.py` recorded sequences byte-identical; all behavioral
engine/store/validation/search suites green). Each DB-medium replacement
named in the last column is part of the Stage 5 test-port plan and passes
there.

| # | Test (file) | Failing surface | Format-only because | DB-medium replacement (passing) |
|---|---|---|---|---|
| 1 | test_store_replaces_and_orphans_old_blob (derived_state) | `(derived_dir / blob).exists()` | asserts blob FILE existence; the orphan/sweep semantics themselves asserted via API first and passed | row query on the blobs table |
| 2 | test_stored_state_carries_the_generated_header (derived_state) | reads `state-v1.json` bytes | pins the JSON header location, not the warning's existence | meta `generator` row assertion |
| 3 | test_misshapen_entries_are_skipped_selectively (derived_state) | hand-written JSON row fixture | selective-skip semantics asserted via API first and passed; the fixture medium was JSON | hand-tampered rows |
| 4 | test_tampered_blob_is_a_miss (derived_state) | overwrites a blob FILE | tamper vector is a file path; hash-verify semantics pinned by API tests | UPDATE of the blob row's bytes |
| 5 | test_symlinked_blob_is_a_miss (derived_state) | symlinks a blob FILE | the symlink vector is path-based; impossible for one DB file | symlinked-DB-file refusal test |
| 6 | test_invalidate_drops_the_entry_and_keeps_the_blob (derived_state) | blob FILE existence after invalidate | keep-the-orphan semantics asserted via API first and passed | row query on the blobs table |
| 7 | test_sweep_deletes_only_unreferenced_blobs (derived_state) | blob FILE existence after sweep | count asserts (deleted/kept) passed; only the file surface failed | row queries on the blobs table |
| 8 | test_sweep_crash_between_blob_and_state_keeps_referenced (derived_state) | hand-written orphan blob FILE | crash-orphan semantics asserted via API first and passed | hand-inserted orphan row |
| 9 | test_commit_staging_collects_superseded_blobs (derived_state) | blob FILE list after commit | collect-superseded semantics asserted via API first and passed | row queries on the blobs table |
| 10 | test_sweep_dry_run_reports_without_deleting (derived_state) | blob FILE existence after dry run | dry-run report counts passed; the file surface failed | row query on the blobs table |
| 11 | test_sweep_skips_symlinks_and_non_blob_names (derived_state) | non-blob FILE + symlink, asserts skipped == 2 | file-namespace policy; DB rows are store-owned, so reclaim replaces skip | test_sweep_reclaims_hand_tampered_rows |
| 12 | test_unpublished_stage_is_a_collectable_orphan (derived_state) | empty blobs DIR listing after sweep | collect-orphan semantics asserted via API first and passed | row query on the blobs table |
| 13 | test_corrupt_cache_rebuilds_quietly (engine) | writes `state-v1.json` garbage, expects rebuild | corruption vector is a file the DB never reads; rebuild-on-corruption itself is proven on the DB medium | corrupt DB file bytes test |
| 14 | test_missing_blob_rebuilds_quietly (engine) | unlinks blob FILES | missing-blob vector is a file path; rebuild-on-miss pinned by API tests | DELETE of blob rows |
| 15 | test_evaluate_many_publishes_one_index_write (engine) | counts `_atomic_write` file writes == 1 | the one-publication-per-batch property itself is proven via API; the counting medium was file writes | publish-call counting == 1 |
| 16 | test_evaluate_many_all_hits_writes_nothing (engine) | reads `state-v1.json` bytes before/after | all-hit write-nothing property proven via API statuses; the medium was file bytes | DB rows before/after |
| 17 | test_evaluate_many_no_cache_publishes_nothing (engine) | reads `state-v1.json` bytes before/after | same as row 16 | DB rows before/after |
| 18 | test_garbage_cache_misses_discards_and_leaves_no_phantom (validation_cache) | overwrites a blob FILE | tamper vector is a file path | UPDATE of the blob row's bytes |
| 19 | test_tampered_blob_rebuilds_and_heals (search) | overwrites a blob FILE | tamper vector is a file path; heal-after-miss pinned by API tests | UPDATE of the blob row's bytes |
| 20 | test_missing_blob_rebuilds_and_heals (search) | unlinks a blob FILE | missing-blob vector is a file path | DELETE of blob rows |
| 21 | test_wrongly_shaped_postings_self_heals (search) | forges blob FILE + rewrites `state-v1.json` entry | forge vector is file-based; wrong-shape refusal and self-heal proven on the DB medium | UPDATE node row + forged blob row |
| 22 | test_wrongly_shaped_segment_self_heals (search) | forges blob FILE + rewrites `state-v1.json` entry | same as row 21 | UPDATE node row + forged blob row |
| 23 | test_corrupt_receipt_sidecar_falls_back_to_the_full_pass (compute_once) | overwrites a blob FILE | fallback-on-corruption pinned by API tests; the vector was a file path | UPDATE of the blob row's bytes |
| 24 | test_status_memoizes_and_reuses_cache_byte_identical (validation_cache) | subprocess wrote JSON cache; in-process swap read the DB | process boundary of the swap harness, not a store defect | passes naturally once the store ships in production code |
| 25 | test_validate_offline_writes_cache_with_header_and_pins (validation_cache) | same subprocess boundary | same as row 24 | passes naturally once the store ships in production code |

Grouped: **23 file-format pins** (rows 1–23) and **2 process-boundary
artifacts** (rows 24–25) = 25, matching §2 exactly. No failure involves
diagnostic ordering, attribution, or presence: `tests/test_scenarios.py`
(recorded sequences, byte-identical) and the behavioral suites pin those and
pass unmodified.
