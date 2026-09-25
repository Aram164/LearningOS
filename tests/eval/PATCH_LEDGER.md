# Repair ledger — S11–S12 (white-box repair, 2026-09-25)

Branch: `muse/eval-s11-repair-2026-09-25`, forked from S10 tip
`84bda98852e0505ba40d93e7e15dd3f716563edb`.
Product revision under repair: `200a36185fd5c693b4464ce0bdff4be5b89ce584`
(verified: no product-code drift between that revision and the fork point,
so all S10 code citations map directly onto this worktree).

Method per repair: re-verify code location in this worktree, failing
reproduction FIRST (worlds built with `--source-rev WORKTREE`, kept outside
the repository under `/tmp/s11-repro/`), smallest general fix at the root
cause, re-run, record before/after here. Oracle opened into a throwaway
directory, README + AUTHOR-NOTES §§8–13 read, plaintext removed at the end.

## S11.1 — Validator-blind projection breakage (JF-08 / JF-09 / JF-10)

One root-cause work item, three failing reproductions. Common shape:
schema-valid canonical state (or a single CLI option) that the validator
certifies clean but that breaks every projection-backed read and all writes,
with the error prescribing a maintainer contract bump.

World repro script (outside repo): `/tmp/s11-repro/repro_s11_1.sh`
- world0: built from unpatched WORKTREE → BEFORE
- world1: built from patched WORKTREE → AFTER

### JF-09 — documented `supersedes` path breaks the product

- Location (worktree): `tools/learning_os/genout/concepts.py`
  `build_backlinks_semantic` emitted `{"from", "kind"}` dicts into
  `note_incoming`; manifest contract v15 declares that slot
  `stringArrayMap` (`system/contracts/manifest-v15.schema.json`).
  Any `supersedes` entry or `note://` body mention broke
  generate/search/inspect/related/bootstrap + all writes.
- Fix: emitter now projects plain incoming-note ids (sorted, unique).
  No consumer of the `kind` field exists in the repo (verified by grep;
  only a test pin asserted the dict shape). Shadow node version bumped
  (`GENERATION_NODE_VERSION` 1→2) per its own bump rule.
- BEFORE (world0): validate 0 errors; `search`/`bootstrap` exit 2 with
  `{'from': 'note-lsm-trees', 'kind': 'superseded-by'} is not of type 'string'`.
- AFTER (world1): validate clean; `search`/`bootstrap` exit 0.
- Tests: `test_supersedes_and_mention_edges_stay_projectable`
  (tests/test_manifest_contract.py) — fails pre-fix (contract drift),
  passes post-fix. Updated `test_rich_fixture_exercises_every_branch`
  pin from dicts to id strings: the old asserts pinned emitter output
  that violates the product's own published contract, which is the bug;
  the test's branch-coverage purpose is unchanged. Made
  `test_producer_version_bump_rebuilds_only_its_node` relative
  (`spec.version + 1`) instead of the literal `2`, which collided with
  the deliberate node-version bump; same rebuild-on-bump assertion.

### JF-10 — schema and manifest disagree on `scope_sources`

- Location (worktree): `tools/learning_os/genout/projection/records_curriculum.py`
  `project_units` spreads stored unit data; `scope_sources` is optional
  in `system/schema/unit.schema.json` but required by manifest
  `$defs/projectedUnit`. A unit without it validated clean and broke
  every projection read (`'scope_sources' is a required property`).
- Fix: projector defaults a missing/falsy block to `[]`, matching every
  other `scope_sources` read site (`.get(...) or []`). Output bytes are
  unchanged whenever the block is present.
- BEFORE (world0): validate 0 errors; `bootstrap`/`search` exit 2.
- AFTER (world1): validate clean; `bootstrap`/`search` exit 0.
- Tests: `test_unit_without_scope_sources_stays_projectable` — fails
  pre-fix, passes post-fix.

### JF-08 — malformed prepare `--request-id` poisons all reads

- Location (worktree): `tools/learning_os/ai_actions/service.py`
  `prepare()` persisted the caller id verbatim, then the projection
  rejected it against `^ai-request-[a-z0-9]+(?:-[a-z0-9]+)*$`; the bundle
  stayed on disk and every projection read failed while validate stayed
  green (validator had zero coverage of `operations/ai-actions/requests/`).
- Fix (two halves):
  1. `prepare()` validates a caller-supplied id via new
     `ai_actions/support.py:check_request_id` BEFORE anything is
     persisted; refusal is `DeliveryValidationError` (CLI exit 1, the
     same code as every other prepare-time refusal) with the pattern in
     the message. Minted ids match by construction and skip the check.
     `--request-id` help text now states the pattern.
  2. New validator check `AI-REQUEST-ID` (`rules/projects.py`, wired in
     `rules/core.py`) names any already-persisted bundle whose id cannot
     publish, plus `AI-REQUEST-BUNDLE` for unparseable/non-mapping
     bundles. Both codes are new; the real repo has no request bundles,
     so `make check` there is unaffected.
- BEFORE (world0): prepare exit 2 AND bundle persisted; `bootstrap`/
  `search` exit 2 afterwards; validate 0 errors.
- AFTER (world1): prepare exit 1, nothing persisted, reads stay up;
  hand-planted bad bundle → `E AI-REQUEST-ID … [operations/ai-actions/
  requests/my-request-1/request.yaml]`, 1 error.
- Tests: `test_prepare_refuses_a_request_id_the_manifest_cannot_publish`
  (incl. schema-pattern sync assert), 
  `test_validator_names_a_persisted_bundle_with_a_bad_request_id` (bad id
  flagged, fixed id clean) — both fail pre-fix, pass post-fix.

### S11.1 gate results

- World repro: BEFORE 3 pass / 7 fail → AFTER 10 pass / 0 fail.
- New tests: 4 fail on unpatched `tools/`, 4 pass patched.
- Full files: test_ai_actions.py + test_incremental_generation.py (51 passed);
  test_manifest_contract.py (20 passed, incl. above);
  test_generation.py + test_manifest_derived.py + test_manifest_shadow.py +
  test_manifest_adversarial.py (153 passed).
- Real repo: `validate.py --compact` 0 errors; `warning_baseline.py --check`
  OK (no new signature); `ruff check tools/ tests/` clean.
- Determinism: shadow/byte-identity suites above green; node-version bump
  invalidates only the backlinks shadow node, which rebuilds identically.

## S11.2 — Write-path honesty (JF-11 / JF-13)

World repro scripts (outside repo): `/tmp/s11-repro/repro_s11_2_jf11.py`,
`/tmp/s11-repro/repro_s11_2_jf13.py`, run against a scratch world built
with `--source-rev WORKTREE`.

Method note (applies to all later stages): `python <world>/tools/*.py`
shadows `learning_os` with the world's older copy via `sys.path[0]`, while
repo scripts use the editable install (== worktree code). All world probes
therefore invoke the REPO's `tools/los.py` / `tools/validate.py` with
`--root <world>`; before/after isolation is by worktree state on identical
world data (before runs taken with the stage's edits absent).

### JF-11 — write-time defects misreported + orphan journals

- Location (worktree): `tools/learning_os/transactions.py` `commit()` /
  `rollback()`, `tools/learning_os/commands/capability.py`
  `_classify_failure` / `_projection_error`.
- Mechanism (verified): with a pre-existing canonical defect (E PARSE,
  manifest breakage), the write fails at `core.validation` /
  `core.projection`, canonical unwind provably restores pre-state, then
  projection re-publication fails *over that pre-state* (it cannot
  publish either) and the old code reported `rollback incomplete for:
  <projection publication>` + kept the crash journal, forcing
  INTERNAL_FAILURE retryable:true. The "incomplete rollback" was false:
  nothing of the write remained.
- Fix: `rollback()` now splits re-publication failure three ways —
  (a) `OSError` (operational: read-only `generated/`, disk full) keeps
  the old path (journal stays, INTERNAL_FAILURE; pinned by existing
  tests); (b) content failure over a tree still equal to the
  transaction's pre-state (fingerprint check) proves a pre-existing
  defect: journal removed, refusal reports the defect; (c) content
  failure with a concurrent foreign change (fingerprint moved) keeps
  crash semantics (journal stays, unknown outcome).
  Reporting: validation-stage case appends fixed classifier-neutral
  wording (`... rolled back completely but the restored pre-state cannot
  be re-published (<Type>); the defect pre-exists this write`) so the
  existing prose classifier yields VALIDATION_FAILED retryable:false
  (case-(b) parity); projection-stage case raises `ProjectionFailure`
  with new `pre_existing_defect=True`, mapped by `_projection_error` to
  VALIDATION_FAILED retryable:false with typed details. The defect's own
  prose is deliberately not embedded (it could trip earlier classifier
  tokens); the original exception already names the defect.
- BEFORE (probes A: E PARSE note; B: legacy-poison bundle): exit 2,
  INTERNAL_FAILURE retryable:true + orphan `.inflight` journal, both.
- AFTER: exit 2, VALIDATION_FAILED retryable:false, no journal, both;
  world repro 0/6 → 6/6.
- Tests: `test_validation_failure_with_unpublishable_prestate_leaves_no_orphan`,
  `test_projection_failure_over_unpublishable_prestate_is_typed_pre_existing`,
  `test_republication_failure_with_concurrent_change_stays_unknown`
  (tests/test_transactions.py); `test_projection_error_maps_pre_existing_defect_to_validation_failed`,
  `test_gateway_v2_classifies_unpublishable_prestate_as_validation_failed`
  (tests/test_gateway_v2.py). All fail pre-fix except the last, which
  pins the classifier-neutrality of the new wording through the
  intentionally-untouched `_classify_failure` (world repro is its
  failing-first evidence). Existing OSError/race tests
  (`..._broken_rollback_is_typed_incomplete`,
  `..._refuses_a_changed_canonical_snapshot`,
  `..._drops_projection_when_republish_fails`, typed-provenance) pass
  unchanged — no test expectation was altered for JF-11.

### JF-13 — ledgers are the sole idempotency memory

- Minimum implemented (detection):
  1. `check_transaction_receipts` now flags two committed receipts
     sharing one `request.idempotency_key`
     (`TRANSACTION-RECEIPT duplicate idempotency key`, naming both).
  2. Same check loads `operations/transactions/idempotency.yaml` and
     reports `TRANSACTION-IDEMPOTENCY` when it is unreadable/malformed
     (mirrors the existing revisions handling; a missing file stays
     fine). Covers the L2 silence.
- Rebuild from receipts: INTENTIONALLY DEFERRED. Assessed against the
  "demonstrably small, safe, supported" bar and found wanting:
  `revisions.yaml` also carries gateway quarantine tokens (not
  receipt-derived; a naive rebuild drops them), the reverted-ledger case
  needs merge-not-rebuild semantics with duplicate refusal, and any
  reconcile-time hook widens the every-lock-acquisition failure surface.
  No rebuild was implemented; no replay path was touched.
- Honest residual: the L4 duplicate commit itself is NOT prevented —
  after both-ledger loss + key reuse the second write still commits.
  What changed: the resulting state is now loud (validator E on the
  duplicate pair) instead of silent, enabling diagnosis and hand repair.
  Replay with intact ledgers is byte-for-byte unchanged (control probe).
- BEFORE (world): probe A (L4 analog) duplicate commits, validate
  0 errors; probe B (L2 analog) validate 0 errors; control C green.
- AFTER: A → `E TRANSACTION-RECEIPT duplicate idempotency key ...`;
  B → `E TRANSACTION-IDEMPOTENCY ...`; C unchanged (exact replay
  ok+replayed, validate clean). World repro 2/4 → 4/4.
- Tests: `test_duplicate_idempotency_key_across_receipts_is_error`,
  `test_unreadable_idempotency_ledger_is_error_but_missing_is_fine`
  (tests/test_validation.py) — both fail pre-fix, pass post-fix.

### S11.2 gate results

- World repros: JF-11 0/6 → 6/6; JF-13 2/4 → 4/4.
- New tests: 7 pass post-fix; 5 fail pre-fix, 2 pin preserved behavior
  (`concurrent_change_stays_unknown`, `classifies_unpublishable_prestate`;
  world repros are their failing-first evidence).
- Full files: test_transactions.py + test_recovery_conflicts.py
  (73 passed); test_gateway_v2.py + test_validation.py (98 passed);
  test_capability_receipts.py + test_ui_gateway_recovery.py (37 passed,
  6 skipped); test_causal_resolver.py + test_evidence_parity.py +
  test_operations.py (42 passed, 1 skipped).
- Real repo: `validate.py --compact` 0 errors (no false positives from
  the new checks); `warning_baseline.py --check` OK;
  `ruff check tools/ tests/` clean.

## S11.3 — First-run traps (JF-01 / JF-05 / JF-07)

### JF-01 — setup cannot recover from its own first failure

- Mechanism (verified): `make setup PYTHON=<old>` builds a 3.11 venv,
  then fails at `pip install` (requires-python >=3.12). The retry
  `make setup PYTHON=<new>` runs `python -m venv` over the existing
  tree, which exits 0 while silently keeping 3.11 — so the retry fails
  identically. Only hand-deleting `.venv` recovered.
- Fix (Makefile `setup` target): reuse the existing venv only when its
  interpreter major.minor equals `PYTHON`'s; otherwise remove the stale
  tree and rebuild (covers half-built trees with no `bin/python` too).
  Same-interpreter re-runs stay fast (reuse); switching `PYTHON`
  rebuilds, which is what the override promises. Runtime echos state
  reuse vs rebuild.
- BEFORE (scratch clone `/tmp/s11-repro/jf01-before`): first setup exit
  2 (`requires a different Python: 3.11.15 not in '>=3.12'`); retry with
  3.12 exit 2, identical error, venv still 3.11.15.
- AFTER (patched Makefile in the same half-built clone): retry exit 0,
  `removing stale .venv (rebuilding with Python 3.12.13)`, `setup
  complete`; recovered venv validates the repo clean
  (`0 error(s) — OK`); second re-run reuses (`reusing .venv`), exit 0.
- Tests: `setup` added to `test_make_entrypoints_parse` (pins the
  shell-heavy target parses — a quoting slip breaks every fresh clone).
  No functional pytest: a real `make setup` needs network (~minutes) and
  the repo has no shell harness; the scratch-clone before/after above is
  the evidence of record.

### JF-05 — no agent can build a write envelope from the docs

- Gaps (verified): approval hash named but algorithm only in
  `contracts/gateway.py`; `capture-request:`/`garden-request:` guards in
  zero documents; README's `capture --text` refused (exit 2) with no
  bridge; refusal `details: {}` undocumented.
- Fix: new WORKFLOWS `§25c. Build a write envelope (GatewayEnvelopeV2)`
  — complete recipe: payload schema source, snapshot source
  (`bootstrap --compact` `snapshot_id`, verified equal to the canonical
  fingerprint), revision guards incl. the request-scoped prefix map and
  the revision-0 baseline, identity rules (key reuse vs
  IDEMPOTENCY_CONFLICT, fresh request_id per attempt), approval kinds
  (`operator-approval` + `operator` channel; gesture is a closed UI
  allowlist) with the one-line approval meaning (operator assertion
  guarded by snapshot/revision checks, not proof of human presence),
  submit + exit codes, the exact intent-hash algorithm (six subject
  fields, canonical JSON form, `sha256:` hex) with a copy-paste Python
  snippet, refusal shape (`details: {}` normal on UNCONFIRMED/prose
  refusals; only typed projection/commit outcomes carry stage details),
  and a worked capture. Bridges: §25a step 4 and §2 point at §25c;
  README's capture line now routes through the envelope; OPERATOR.md
  capture routing points at §25c.
- BEFORE: doc-gap probe 0/5 (all facts absent; README command exit 2).
- AFTER: 5/5; a from-docs-only envelope (stdlib + CLI, zero
  implementation imports — `/tmp/s11-repro/prove_jf05_docs.py`)
  committed on the scratch world (exit 0, fresh receipt).
- Tests: docs are verified by the gap probe + sufficiency proof, not by
  pytest (no doc-content harness exists; the §25a literal-example test
  still passes unchanged).

### JF-07 — manual-bundle delivery format undocumented

- Gaps (verified): no delivery schema anywhere; import refused one field
  per round; adapter error named neither `producer` (delivery side) nor
  `provider` (request side).
- Fix, three parts:
  1. New AI-ACTIONS.md `Delivery bundle format` section: every
     `delivery.yaml` field with provenance (what must equal/copy the
     request), the `producer`/`provider` asymmetry stated explicitly,
     per-capability operation shapes, aggregation behavior, and a
     complete minimal example. Verified accurate: `approved_at`
     documented as conventional (never read by code), `producer.provider`
     as uncompared (only `adapter` is).
  2. `service._validate` aggregates all shape problems into one
     `DeliveryValidationError` (per-operation `operations[i]` locations;
     capped at twelve + omission count per the house pattern); live
     freshness guards still fail fast. Staging names a missing delivery
     `id` (`delivery.yaml must carry a non-empty id`, was the cryptic
     `unsafe exchange identifier: ''`) and `_validate` names a missing
     `request_id`.
  3. Adapter message now names both sides: `delivery producer.adapter
     … does not match prepared request provider.adapter …`.
- BEFORE (world probes): multi-defect delivery → single `delivery type
  must be ai-action-delivery`; provider-shaped delivery → fieldless
  `delivery adapter does not match prepared request`; schema terms
  absent from AI-ACTIONS.md. 0/3.
- AFTER: one import round reports all six shape problems with locations;
  adapter error names both fields; docs present. 3/3. A from-docs-only
  delivery (`/tmp/s11-repro/prove_jf07_docs.py`) imports and validates
  (exit 0/0).
- Tests: `test_import_reports_every_shape_problem_in_one_round`,
  `test_adapter_mismatch_names_both_sides_of_the_asymmetry`,
  `test_missing_delivery_identities_name_their_fields`
  (tests/test_ai_actions.py) — all fail pre-fix, pass post-fix. No
  existing test pinned the old messages.

### S11.3 gate results

- JF-01 scratch clone: retry exit 2 → 0; recovered venv validates clean.
- JF-05 gap probe 0/5 → 5/5; from-docs envelope committed.
- JF-07 world probes 0/3 → 3/3; from-docs delivery imports + validates.
- Full test_ai_actions.py (28 passed); §25a literal-example test +
  entrypoints parse pass; `validate.py --compact` 0 errors;
  `warning_baseline.py --check` OK; `ruff check tools/ tests/` clean.
- Note: `test_tree_contract.py::test_every_top_level_directory_on_disk_is_declared`
  fails identically on clean HEAD (`bases/` absent from this worktree) —
  pre-existing environment artifact, carried to the S12.6 JF-02 triage.

## S12.4 — Diagnostics honesty (JF-04 / JF-03 / JF-19 / JF-21)

### JF-04 — TRACEPARENT adopted as operation identity

- Mechanism (verified): `tracer.operation()` returned the propagated
  context wholesale and `span_start("attempt")` reused its span id, so
  every process under one ambient trace logged one operation; `los
  operations` groups by trace id and merged them (wrong outcome,
  wrong attention).
- Fix: `operation()` always mints a fresh per-process operation
  (trace + span), carrying the propagated pair as `parent` linkage only
  (stable per process, re-derived if the env value changes);
  `TraceContext` gains `parent`; transient records carry
  `parent_op`/`parent_span`; the store persists `parent_trace_id` /
  `parent_span_id` (additive; old readers ignore it) and reads pass
  them through. Correlation preserved, identity per process.
- BEFORE (world, ambient TRACEPARENT, two writes): 1 operation with
  2 attempts under the ambient trace; 0/28 records with parent linkage.
- AFTER: 2 operations (fresh traces), 1 attempt each, 28/28 records
  parented. World repro 1/4 → 4/4.
- Tests: new `test_shared_parent_trace_does_not_merge_operations`
  (fails pre-fix, passes post-fix). Intent-preserving rewrites of three
  tests that pinned the adjudicated adoption:
  `test_child_receives_the_intended_context` (capability record still
  shows the received parent; phases now assert fresh ids + parent
  linkage), `test_concurrent_operations_cannot_cross_contexts`
  (per-attempt distinct ops + shared parent linkage — stronger
  isolation than before), `test_s6_resolves_committed_from_persisted_store`
  (attempt selection by parent trace instead of adopted identity; S6
  verdict unchanged). The old asserts encoded the confirmed defect
  (adoption merges unrelated requests); the tests' intents (context
  receipt, isolation, S6 resolution) are preserved.

### JF-03 — test spans pollute the checked-in operations view

- Mechanism (verified): `test_capability_dispatch._run_capability` and
  one `test_capability_catalog` case drive the real CLI without
  `--root` (they assert on the real capability catalog), binding the
  trace store to the real root; `make test-fast` wrote exactly the
  S00-counted 135 spans to `operations/diagnostics/traces.jsonl`.
- Fix: autouse conftest fixture snapshots the real `traces.jsonl`
  around every test (byte-restore: unlink-if-created else
  truncate-to-size, rmdir-if-emptied) and unbinds the process-global
  store afterwards. The two tests keep running against the real
  catalog — assertions unchanged, side effects isolated. Mini-root
  store assertions are untouched (their roots are never the real one).
- BEFORE: the two files pass 66/66 and leak 135 spans.
- AFTER: 66/66, zero bytes left behind (dir removed too).
- Tests: `test_suite_leaves_the_real_diagnostic_store_untouched`
  replays the leak path in a nested pytest and asserts byte-identity;
  fails on unfixed conftest (nested run appends spans), passes with it.

### JF-19 — operations mislabels settled outcomes (F-s07-10)

Three sub-fixes, one per minimized repro:
1. Settlement: a commit settled only while the live manifest showed
   its exact snapshot, so every CLI write read BLOCKED until views
   regenerated and all but the latest stayed that way permanently.
   New rule: COMMITTED + live manifest at-or-past the commit (both
   snapshots chained to receipts, manifest receipt at-or-after the
   write's — `manifest_covers_receipt`, pure and unit-tested) settles
   with reason "live manifest is past this commit"; a behind/unknown
   manifest keeps verify-observation (the real projection-behind
   signal, with `make views` as the documented settling step).
2. Conflicts: a lone IDEMPOTENCY_CONFLICT (every counted attempt)
   now resolves NOT_COMMITTED/none via `_conflict_proves_no_commit`,
   ordered before the contradiction branches (the ledger row is the
   other intent's evidence). The S9–S11 multi-attempt guard is shared
   and still withholds proof for ambiguous earlier attempts.
   `IDEMPOTENCY_CONFLICT` also joins `DEFINITIVE_NO_COMMIT_CODES`;
   the UI mirror (`contracts/gateway-v2.ts`) needs the same addition
   — recorded here as a required cross-repo sync; the drift-failing
   parity test skips in this worktree (sibling absent) and will fail
   until the UI lands it, which is the designed forcing function.
3. Reused ids: `describe_operation` appends an explicit note when the
   matched records span 2+ idempotency keys (covered key + every
   other key with outcome/tx), instead of silently naming only the
   first transaction. Response shape unchanged (additive reason).
- BEFORE (world): superseded COMMITTED → verify-observation/attention;
  conflict → AMBIGUOUS + reconcile-exact-request; shared-id
  explanation names tx1 only. 1/5.
- AFTER: all settled/named correctly. 5/5.
- Tests: `test_manifest_covers_receipt_positions_the_live_manifest`,
  `test_superseded_commit_settles_without_exact_observation`,
  `test_idempotency_conflict_proves_no_commit_for_its_attempt` (incl.
  multi-attempt guard + contradiction-ordering legs),
  `test_reused_request_id_names_every_distinct_request` (end-to-end,
  two CLI writes) — all fail pre-fix, pass post-fix. The S1–S14
  ground-truth gate is unchanged (all 14 verdicts identical).
- Docs: the operations-surface reference (statuses, recovery
  requirements, settlement rule) confirmed missing by JF-19 is written
  in S12.5 with the other documentation residues.

### JF-21 — reads disagree after a kill

- Mechanism (verified, F-s07-03 replicated): query reads (single-ID
  inspect/search/related) call bare `_fresh_manifest` with no lock,
  while batch inspect/bootstrap/plan reads take the operator lock
  (which reconciles on acquisition). After a SIGKILL mid-commit the
  interfaces report different states.
- Fix: `_fresh_manifest` takes `_operator_lock` itself — the single
  choke point for all 11 projection-read call sites (query, reads,
  unit, module, project). Re-entrant for callers already holding the
  lock; uncontended flock + empty-journal scan cost is negligible
  next to a full manifest build. Every projection read now observes
  post-recovery transaction-consistent state. Reconcile/commit/replay
  logic untouched: the 94-kill atomicity and idempotency properties
  keep their exact code paths (strengthened isolation, no weakened
  property). `validate`/`status` still report on-disk state directly
  (out of the adjudicated scope, which names single-ID/batch/bootstrap).
- BEFORE (world, real SIGKILL at 0.5s): single inspect → paused
  (uncommitted), batch → active, bootstrap snapshot == pre-state.
- AFTER: single/batch/bootstrap all pre-state. World repro 2/3 → 3/3.
- Tests: `test_reads_agree_on_pre_state_after_a_crash` (planted torn
  file + v2 journal, no receipt; asserts single/batch/bootstrap +
  healed bytes) — fails pre-fix (single shows paused), passes post-fix.

### S12.4 gate results

- World repros: JF-04 1/4 → 4/4; JF-19 1/5 → 5/5; JF-21 2/3 → 3/3;
  JF-03 135 leaked spans → 0 (66/66 pass both ways).
- New tests: 7, all fail pre-fix and pass post-fix (the conftest
  one fails on unfixed conftest as shown), plus 3 intent-preserving
  rewrites of tests that pinned the JF-04 adoption.
- Full files: test_trace_context.py (14 passed, 1 skipped);
  test_diagnostic_store.py + test_causal_resolver.py +
  test_evidence_parity.py + test_operations.py (64 passed, 1 skipped);
  test_recovery_conflicts.py + test_bounded_reads.py +
  test_search_index.py (103 passed); test_transactions.py +
  test_gateway_v2.py + test_capability_dispatch.py +
  test_capability_catalog.py (165 passed).
- Real repo: `validate.py --compact` 0 errors;
  `warning_baseline.py --check` OK; `ruff check tools/ tests/` clean;
  `operations/diagnostics/` absent after the suites (JF-03 holds).
- Known cross-repo follow-up: UI `DEFINITIVE_NO_COMMIT_CODES` must add
  IDEMPOTENCY_CONFLICT (parity test enforces).

## S12.5 — Read gaps + doc residues (JF-14 / JF-17 / JF-23)

World repro script (outside repo): `/tmp/s11-repro/repro_s12_5_reads.py`,
run against `/tmp/s11-repro/world-s12_5` (built with
`--source-rev WORKTREE` from the S12.4 tip; probes invoke the repo's
`tools/los.py` with `--root`, before/after by worktree state).

### JF-14 — Garden, inbox, and stage-note reads

Three legs, three different answers — verified separately:

1. Stage notes: already reachable, no code change. `inspect
   STUDY_MAP_ID` carries every stage's `notes_text` (verified: a
   gateway-written note appears in `inspect` and matches metadata
   search in the world repro). The defect was discoverability; the
   repair is docs (OPERATOR read routing, below).
2. Garden: entries were already projected (top-level `garden_entries`,
   contract v15) with stable ids, but invisible to every read. Fix,
   with zero manifest bytes changed (no contract bump — the
   versioned shape is untouched, so no UI mirror is owed):
   metadata `search` also matches `garden_entries`, and `note-read`
   resolves `garden-note-*` ids lazily on a durable-note miss (same
   `note-content` envelope, snapshot guard, symlink refusal; the
   durable path is untouched, including its parse-only-notes
   budget).
3. Inbox: new `inbox-read` query + CLI command — bounded UTF-8
   segments of one `work/inbox/` file by inbox-relative name.
   Refuses missing names, absolute/`..` names, symlinks, and
   non-UTF-8 drops (binary captures have no text read); guarded by
   the canonical snapshot (`work/` is a canonical root). Metadata
   `search` matches inbox filenames only, never bytes
   (binary-safe); discovery lists non-dot files (the same rule as
   the inbox count) while an exact name reads dot-files too.
   Catalog: `note.content` invariants widened, new `inbox.content`
   query; brief-bootstrap expands gain `inbox_read`.
- Deliberately NOT done: no `garden-note`/`inbox-item` record types
  in manifest `records[]`. That reshapes the published v15
  contract, and the repo's own rule requires the UI mirror in the
  SAME change ("a bump that lands alone is the bug this file was
  written to prevent"); the UI sibling is absent from this
  worktree, so a v16 bump cannot land correctly. The `los`-query
  surfacing above serves discovery + content with the contract
  bytes identical.
- BEFORE (world): 4/14 — garden/inbox invisible everywhere,
  `note-read` refuses garden ids, no `inbox-read` command.
- AFTER: 14/14.
- Tests: `test_search_surfaces_garden_seeds_and_inbox_filenames`,
  `test_note_read_resolves_a_garden_seed`,
  `test_inbox_read_serves_text_and_refuses_binary_escape_and_missing`
  (tests/test_bounded_reads.py) — all fail pre-fix, pass post-fix.

### JF-17 — `resume` shows recorded stage progress

- Mechanism (verified): `resume` renders requirement-linked
  observations only, and forces `observations` empty when the stage
  has no authored requirement — so after a `stage.note.write` the
  screen reads "none recorded" even though the write succeeded.
- Fix: `cmd_resume` computes bounded stage-note facts
  (`working_note`, line count, last-commit `updated`, trailing
  800-char excerpt) via `_stage_note_facts` (boundary-checked,
  best-effort: missing/unreadable file is 0 lines, an escaping
  path is None — resume names no defects, the validator does); a
  new optional `stage-note` dossier section carries them (the
  digest moves with the note, like every section); the render
  gains `Stage note N lines recorded (path, updated …)` plus the
  last 3 non-empty lines, `nothing recorded yet` when empty, and a
  `Next` line naming `stage-note` when no requirement exists.
- BEFORE (world): no `Stage note` line, no `stage-note` JSON
  section. AFTER: both, with the written marker in the excerpt.
- Tests: `test_stage_note_section_moves_the_digest_and_refuses_non_mappings`,
  `test_resume_shows_recorded_stage_note_without_a_requirement`
  (tests/test_resume_dossier.py) — fail pre-fix, pass post-fix.
- Honest residual (not repaired): no capability advances the
  workspace Next Action — a missing write needing Aram's design
  call, recorded here, not implemented.

### JF-23 — small read-surface items

- (a) `notes_updated`: docs only. OPERATOR now states it is the
  note file's last-commit date, unmoved by uncommitted writes. No
  code change: commit-date sourcing is the determinism
  architecture (byte-identical rebuilds); wall-clock mtime would
  fight it, and the schema file cannot carry the note (any byte
  change breaks `schema_sha256` → contract bump).
- (b) `atlas.question.save` payload: new single-source module
  `contracts/atlas_question.py` (`QUESTION_FIELDS` +
  `question_schema()`), the handler imports the field set
  (replacing its inline copy), a non-dict `target` is refused
  instead of crashing with `AttributeError` on the new-note
  path, the registry gains
  `("atlas.question.save", "question")`, and capability schemas
  were regenerated (only this file of 39 changed). The nested
  shape mirrors the handler, never stricter: required `id` only
  (title/text/target are conditionally required by repository
  state, which the schema cannot see); target/state/answer-note
  internals stay structural with `note.schema.json` cited, so no
  second enforcement copy exists.
- (c) Search rows gain `state` + `deprecated` keys (additive;
  null when the record lacks them) — note lifecycle state and
  concept deprecation are now visible in discovery output.
- (d) Revision 0: already documented in WORKFLOWS §25c ("the
  legitimate no-recorded-revision baseline, backstopped by the
  snapshot guard") — verified present, cited, no new prose.
- Tests: `test_atlas_question_payload_schema_types_its_fields`,
  `test_atlas_question_save_refuses_a_non_object_target`
  (tests/test_atlas_authoring.py),
  `test_search_rows_carry_state_and_deprecated`
  (tests/test_bounded_reads.py) — all fail pre-fix, pass post-fix.

### Documentation residues (JF-12 / JF-15 / JF-16 / JF-24 + JF-19)

- JF-19 operations reference (promised in S12.4): new WORKFLOWS
  §28 — list/explain forms, the three outcomes + recovery
  requirements, the at-or-past settlement rule with `make views`
  as the settling step, request-id reuse, failure stages. Every
  claim verified against `conventions.py` / `resolver.py` /
  `commands/operations.py` (incl. `projection_outcome` values and
  newest-first ordering).
- JF-12: OPERATOR "What 'clean' means" states the fail-closed
  design (one error anywhere blocks every write; reads refuse
  rather than omit).
- JF-15: OPERATOR states `related` is one-directional
  (documented, not symmetrized — verified against the backlink
  builder: a workspace lists a note when either side declares the
  link, the note lists it only from its own declarations).
- JF-16: README (2 spots) + OPERATOR atlas line say "build views
  first" on a fresh install.
- JF-24: OPERATOR states search semantics (AND-substrings,
  unranked, no snippets — the design, not a defect).
- JF-14: OPERATOR read routing (stage-note path via parent-map
  inspect, garden `note-read`, `inbox-read`, search coverage);
  WORKFLOWS §21 gains the inbox read line.
- Verification: 9-statement presence probe, all PRESENT; the §25a
  literal-example test passes unchanged (new §28 sits past the
  `## 26.` split).

### S12.5 gate results

- World repro: 4/14 → 14/14.
- New tests: 8, all fail pre-fix and pass post-fix (verified via
  stash of `tools/` + `system/`).
- Full files: test_bounded_reads.py + test_resume_dossier.py +
  test_resume_pointer.py + test_atlas_authoring.py +
  test_capability_catalog.py + test_capability_dispatch.py +
  test_agent_efficiency.py + test_cli.py + test_search_index.py
  (200 passed); test_curriculum_v2.py + test_plan_resume.py +
  test_material_context.py + test_evidence_staleness.py (85 passed,
  1 skipped).
- Real repo: `validate.py --compact` 0 errors;
  `warning_baseline.py --check` OK; `ruff check tools/ tests/`
  clean.
