# Intelligence Plane — Phase 1 record

Parent proposal: `intelligence-plane-plan.md`. Prior phase:
`intelligence-plane-phase0-record.md` (evaluator pattern proven with one
predicate; contract version 1).

## What Phase 1 lands

- **23 pure predicates** in `tools/learning_os/semantics/` (contract
  version 2 — registry membership changed, so the bump is the deliberate
  diff). Every predicate documents authoritative inputs and a fail-closed
  fallback; the table is duplicated in machine-readable form as
  `PREDICATES` and in prose in `system/SEMANTIC-CONTRACT.md`.
- **20 VOQ fixtures** under `tests/fixtures/verified_operator_questions/`
  (15 examples, 5 held out across five classes), each an executable
  question/procedure/expected triple.
- **Two suites**: `tests/test_semantic_contract.py` (registry cap, 80-case
  truth/fail-closed table, producer/evaluator agreement) and
  `tests/test_verified_operator_questions.py` (shape, split, examples
  green, held-out eval with reported score, no-leak across code, docs,
  examples, and the suite itself).
- This record.

## Explicit non-changes

- No canonical migration, no gateway change, no new JSON schema, no
  hand-edit of rebuilt views. Predicates read already-loaded records and
  projection rows; the only producer touch is Phase 0's delegation.
- No lineage sidecars (Phase 2), no detectors (Phase 3), no Task IR or
  telemetry (Phase 4), no dossier builder (Phase 5), no change envelope
  (Phase 6).
- No critique-point action taken.

## Validation observed (2026-09-07 session)

`make check` zero errors (baseline confirmed green before starting);
warning baseline OK; `make lint` incl. code reachability green;
`make test-fast` and the full suite pass except four tests that assert a
zero-error repository and fail on three pre-existing errors unrelated to
this phase (umbrella-root perimeter files outside the workspace; a
`GEN-INPUT` in the approved parent proposal). Regenerated views after the
final authored change.
