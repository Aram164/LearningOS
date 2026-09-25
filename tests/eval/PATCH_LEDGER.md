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
