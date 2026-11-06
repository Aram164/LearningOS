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
| `spike_store_sqlite.py` | 280 | 193 | the SQLite-backed store behind the existing `store.py` API surface |
| `spike_swap.py` | 57 | 34 | pytest plugin: installs the spike as `learning_os.store.derived.store` (sys.modules + package attrs + rebind of already-imported modules) |
| `spike_behavior.py` | 212 | 174 | 28 DB-equivalent corruption/rebuild/identity/path-safety/sweep scenarios (the oracle tests' format-pinned scenarios, ported to the DB medium) |

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
against the unmodified production baseline and then against the spike swapped
in behind the same API surface. Baseline: **224 passed**. Swapped: **200
passed, 24 failed** (measured in the Stage 5 worktree mid-state with the
rebind-fixed harness; the earlier in-research run reported 199/25, where one
extra failure was an artifact of the harness bug documented in §1 — the
engine wrote JSON while tests read the DB).

**Stated plainly: full migration parity is NOT established by this spike.**
What is established: all 24 failures are classified below, and our evidence
says each is format-only — the failing assertion surface is the physical file
path or file bytes, never diagnostic ordering, attribution, or presence,
which are pinned end-to-end by the suites that pass unmodified
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
| Production `store.py` superseded by the spike module | 308 wc-l → 280 wc-l; 189 code → 193 code | **measured: line-neutral at the store API boundary (−28 wc-l, +4 code)** |
| Retained policy inside the spike module (path safety 13, hash verify 4, blob-string parity 2, identity binding 2) | ≈ 21 code lines | measured — the reviewer caveat honored, not absorbed |
| Engine-side deletions (states cache −12, deferred-index batching −14, commit-staging plumbing −14) | ≈ −40 wc-l | **still ESTIMATE — engine untouched by this spike** |
| `__init__.py` re-export shrink | ≈ 0 (not −25 as estimated) | measured correction: the same-API-surface approach preserves the re-exported names, so the estimated −25 does not materialize unless the API itself shrinks |
| Micro-benchmark (in-process, 200 stores + 200 lookups + 100 read_states + 1 sweep, 50-key values) | JSON: 133–140 / 20–21 / 6–7 ms; SQLite: 149–157 / 44–45 / 11–12 ms | measured, informal: ≈1.1–2× slower per op, sub-second at this scale; the spike opens a connection per call (a real integration holds one per session, which would narrow the gap); no material regression claim needed at S23's loader-dominated scale |

**Correction the measurements force:** Deliverable 2's Role B net of ≈ −160 L
ESTIMATE (range −110…−195) does not survive measurement. Behind the *same API
surface*, the store replacement is line-neutral; the deletion side of the D1
ledger assumed engine-side and `__init__` simplifications that either remain
unproven (engine ≈ −40) or were based on an API-shrinking design this spike did
not test (≈ −25 → ≈ 0). The honest measured statement: **net ≈ −28 wc-l measured
for the store slice alone; ≈ −68 wc-l if the engine-side ESTIMATE also lands —
at or beyond the pessimistic edge of the published range, and only if a later
assignment actually rewrites the engine plumbing.** The Gate 2 prediction
("budget the true net nearer the pessimistic end") is confirmed; the Q4 verdict
(YES, net deletion) survives only via the engine-side estimate and the
dimension-4 argument.

What measurement *strengthens*: the qualitative core of the Role B case. The
hand-reasoned machinery — five corruption→miss paths in `read_state`, five in
`lookup`, blobs-first/state-last choreography, RMW merge, "crash-safe by
construction" GC — became schema constraints, one transaction, one PK upsert,
and one `DELETE ... NOT IN` in the spike, and every behavioral test that
exercises those invariants through the API passes unchanged. That is dimension-4
ownership transfer, demonstrated, not argued. Whether a ~line-neutral store
replacement plus an ≈ −40 L engine simplification justifies adopting SQLite for
`generated/`-level cache state is now an honest reviewer judgment between
"dimension-4 win, measured" and "no dimension-1 win at this boundary".

## 4. What a real Stage 5 would inherit from this spike

- Rewrite list: the 23 format-pinning tests (port to DB-medium equivalents —
  `spike_behavior.py` already contains 28 such scenarios) and the 2 subprocess
  tests become in-process once the store ships in production code.
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
(28 original — one now honest — plus 15 adversarial checks).

Parity wording corrected per the same review: the "zero behavioral failures"
claim is replaced by the plain statement in §2 plus the per-failure evidence
in Appendix C. Two documentation corrections are applied in §5 (guard
unification scope) and §7 (NO-GO reconciliation; engine-side ≈ −40 L marked
ESTIMATE).

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
  .venv/bin/pytest -p spike_swap <same files> -q                        # 199 passed, 25 failed (classified)
# DB-equivalent corruption/rebuild/identity scenarios
PYTHONPATH="tools:workbench/spikes/roleb-sqlite-2026-11-06" \
  .venv/bin/python workbench/spikes/roleb-sqlite-2026-11-06/spike_behavior.py   # 28/28
```

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


## Appendix C — per-failure classification of the 24 swapped-suite failures

Evidence basis: the Stage 5 worktree mid-state run (rebind-fixed harness) at
`60da966` + spike store: 200 passed / 24 failed. For every failure, the
failing assertion surface is the physical medium (file path, file bytes, or
file-write counting) — never diagnostic code, message text, attributed path,
ordering, or presence, which are pinned by the suites that pass unmodified
(`tests/test_scenarios.py` recorded sequences byte-identical; all behavioral
engine/store/validation/search suites green). Each DB-medium equivalent that
replaces a format pin is named; all pass.

| # | Test (file) | Failing surface | Format-only because | DB-medium replacement (passing) |
|---|---|---|---|---|
| 1 | test_store_replaces_and_orphans_old_blob (derived_state:263) | `(derived_dir / blob).exists()` | asserts blob FILE existence; sweep/orphan semantics themselves asserted via API first and passed | test_store_replaces_and_orphans_old_blob (row query) |
| 2 | test_stored_state_carries_the_generated_header (derived_state:271) | reads `state-v1.json` bytes | pins the JSON header location, not the warning's existence | same test (meta `generator` row) |
| 3 | test_misshapen_entries_are_skipped_selectively (derived_state:339) | hand-written JSON rows | the selective-skip semantics passed via API; the fixture medium was JSON | same test (hand-tampered rows) |
| 4 | test_tampered_blob_is_a_miss (derived_state) | overwrites blob FILE then expects miss | tamper vector is a file path; hash-verify semantics pinned by API tests | same test (UPDATE bytes row) |
| 5 | test_symlinked_blob_is_a_miss (derived_state) | symlinks a blob FILE | symlink vector is path-based; impossible in one DB file | test_symlinked_db_file_is_a_miss (symlinked DB refused) |
| 6 | test_invalidate_drops_the_entry_and_keeps_the_blob (derived_state:395) | blob FILE existence after invalidate | keep-the-orphan semantics asserted via API first and passed | same test (row query) |
| 7 | test_sweep_deletes_only_unreferenced_blobs (derived_state:495) | blob FILE existence after sweep | count asserts (deleted/kept) passed; only the file surface failed | same test (row queries) |
| 8 | test_sweep_crash_between_blob_and_state_keeps_referenced (derived_state) | hand-written orphan blob FILE | crash-orphan semantics asserted via API first and passed | same test (orphan row) |
| 9 | test_commit_staging_collects_superseded_blobs (derived_state) | blob FILE list after commit | collect-superseded semantics asserted via API first and passed | same test (row queries) |
| 10 | test_sweep_dry_run_reports_without_deleting (derived_state) | blob FILE existence after dry run | dry-run report counts passed; file surface failed | same test (row query) |
| 11 | test_sweep_skips_symlinks_and_non_blob_names (derived_state) | creates non-blob FILE + symlink, asserts skipped==2 | file-namespace policy; DB rows are store-owned so reclaim replaces skip | test_sweep_reclaims_hand_tampered_rows |
| 12 | test_unpublished_stage_is_a_collectable_orphan (derived_state) | empty blobs DIR listing after sweep | collect-orphan semantics asserted via API first and passed | same test (row query) |
| 13 | test_corrupt_cache_rebuilds_quietly (engine:204) | writes `state-v1.json` garbage, expects rebuild | corruption vector is a file the DB never reads; rebuild-on-corruption itself is proven on the DB medium | same test (corrupt DB file bytes) |
| 14 | test_missing_blob_rebuilds_quietly (engine:213) | unlinks blob FILES | missing-blob vector is a file path; rebuild-on-miss pinned by API tests | same test (DELETE blob rows) |
| 15 | test_one_session_reads_the_state_index_once (engine:323) | counts `read_state` calls == 1 | pins the removed session cache's read pattern, not an API contract | test_session_never_bulk_reads_the_state_index (zero bulk reads) |
| 16 | test_evaluate_many_publishes_one_index_write (engine:496) | counts `_atomic_write` file writes == 1 | one-publication-per-batch property itself proven via API; the counting medium was file writes | same test (counts publish calls == 1) |
| 17 | test_evaluate_many_all_hits_writes_nothing (engine) | reads `state-v1.json` bytes before/after | all-hit write-nothing property proven via API statuses; medium was file bytes | same test (DB rows before/after) |
| 18 | test_evaluate_many_no_cache_publishes_nothing (engine) | reads `state-v1.json` bytes before/after | same as 17 | same test (DB rows before/after) |
| 19 | test_status_memoizes_and_reuses_cache_byte_identical (validation_cache:51) | subprocess wrote JSON cache, in-process swap read DB | process boundary of the swap harness; store ships in production code in a real migration | passes naturally once the store ships (verified in the Stage 5 worktree) |
| 20 | test_validate_offline_writes_cache_with_header_and_pins (validation_cache:288) | same subprocess boundary | same as 19 | passes naturally once the store ships |
| 21 | test_garbage_cache_misses_discards_and_leaves_no_phantom (validation_cache:153) | overwrites blob FILE, expects miss | tamper vector is a file path | same test (UPDATE bytes row) |
| 22 | test_tampered_blob_rebuilds_and_heals (search) | overwrites blob FILE | tamper vector is a file path; heal-after-miss pinned by API tests | same test (UPDATE bytes row) |
| 23 | test_missing_blob_rebuilds_and_heals (search) | unlinks blob FILE | missing-blob vector is a file path | same test (DELETE blob rows) |
| 24 | test_wrongly_shaped_postings_self_heals / test_wrongly_shaped_segment_self_heals (search ×2) | forges blob FILE + rewrites `state-v1.json` entry | forge vector is file-based; wrong-shape refusal + self-heal proven on the DB medium | same tests (UPDATE node row + INSERT forged blob row) |
| 25 | test_corrupt_receipt_sidecar_falls_back_to_the_full_pass (compute_once) | overwrites blob FILE | fallback-on-corruption pinned by API tests; vector was a file path | same test (UPDATE bytes row) |

Grouped: 22 file-format pins (rows 1–18, 21–25), 1 removed-machinery pin
(row 15 — the session cache the assignment removed), 1 file-write-count
medium (row 16, counted in 22), 2 process-boundary tests (rows 19–20; they
pass naturally once the store ships — verified). No failure involves
diagnostic ordering, attribution, or presence.
