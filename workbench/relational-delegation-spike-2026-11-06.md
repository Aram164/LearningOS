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

Oracle: the derived-store/validation-cache/search/compute test suites, run twice
in the clone. Baseline (production store): **224 passed**. With the spike swapped
in behind the same API surface: **199 passed, 25 failed — zero behavioral
failures**. Every failure is one of:

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

Authorized as optional/narrow; result recorded in
`workbench/spikes/route-guard-2026-11-06/` (see §6 of that directory's report
fragment in the spike commit) — throwaway, measured, no production edits.

## 6. Verification and honesty notes

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

1. Accept the measured correction: Role B's net-deletion case is ≈ line-neutral
   at the store boundary, ≈ −68 wc-l with the engine-side estimate — the Q4 GO
   now rests primarily on the measured dimension-4 ownership transfer rather
   than line count.
2. Decide whether that case justifies a Stage 5 assignment (which would include
   the engine-side rewrite this spike did not attempt), or whether Role B is
   retired with the measured evidence appended to the inventory.
3. Spike 2's route-guard unification result (same decision pattern: measured
   dedup value vs refactor cost, no SQL involved).
