# Intelligence Plane — Phase 10 record (truth maintenance retraction)

Parent proposal: `intelligence-plane-plan.md`. Prior phases: Phase 0
(record), Phase 1 (predicates, contract v2, VOQs), Phase 1.5
(policy-query envelope), Phase 2 (lineage sidecar), Phase 3 (goal
engine), Phase 4 (Task IR with static dispatch, as amended), Phase 5
(dossiers), Phase 6 (proof-carrying change).

## What Phase 10 lands

- `tools/learning_os/semantics/lineage.py`: forward-only assumption
  tracking. `DerivedFrom` gains `assumes` (claim ids this claim
  depended on); `record_claim` and all three emitters accept it,
  refusing blank entries and self-assumption. New status `withdrawn`
  joins `STATUSES`.
- `retraction_impact(lineages, claim_id)`: read-only blast-radius
  query — breadth-first over assumption edges, root first, neighbors
  sorted for determinism. Refuses unknown claim ids.
- `withdraw(lineages, claim_id)`: marks the full cascade withdrawn,
  preserving every other field and input order. Idempotent, and
  order-independent (A-then-B equals B-then-A). Sidecar only:
  canonical data untouched, nothing re-derived.
- Withdrawn is sticky: `refresh` keeps it (like `contested`),
  `endorse` and `contest` refuse it — return requires a fresh
  judgment. `impacted` reports withdrawn claims as-is (they need a
  human). Ledger schema gains optional `assumes` and the `withdrawn`
  enum; pre-Phase-10 records load unchanged and cascade only to
  themselves — no migration, by design.
- `tests/test_semantic_lineage.py`: seven retraction tests (cascade
  fixture A→X→Y→Z plus unrelated W; pre-invalidation impact query;
  idempotence and monotonicity; legacy shape; assumes round-trip;
  sticky-withdrawal refusals; assumption validation). Retraction
  section in `system/SEMANTIC-CONTRACT.md`; this record.

## Explicit non-changes

- No automatic re-derivation, no canonical writes, no gateway change,
  no new claim family, no contract-version bump (still v2), no VOQ
  additions. No critique-point action taken.

## Validation observed (2026-09-08 session)

`make check` zero errors; warning baseline OK; `make lint` incl. code
reachability green; lineage suite green (23 passed); full suite green
(1274 passed, 1 skipped); views regenerated after the final authored
change.
