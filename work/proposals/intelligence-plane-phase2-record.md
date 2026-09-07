# Intelligence Plane — Phase 2 record (semantic lineage)

Parent proposal: `intelligence-plane-plan.md`. Prior phases: Phase 0
(record), Phase 1 (23 predicates, contract v2, 20 VOQs), Phase 1.5
(policy-query envelope).

## Storage decision (the Phase 2 open question)

Receipt-adjacent sidecar: `operations/transactions/lineage.yaml`, one
ledger file on the `revisions.yaml` precedent, schema-validated on load
(`system/contracts/semantic-lineage-ledger.schema.json`, exempt-listed in
`contract-register.yaml` like the other operations-governing schemas).
Rejected: generated projection — lineage must survive a rebuild, which is
its entire point. Rejected: canonical fields — the four-family limit
stands. The validator never enumerates the ledger (rules glob
`transaction-*.yaml` only), and `operations/` sits outside the manifest
fingerprint, so lineage writes never stale the views.

## What Phase 2 lands

- `tools/learning_os/semantics/lineage.py`: `ClaimLineage` + `DerivedFrom`
  records, pure transitions (`record_claim`, `refresh`, `contest`,
  `endorse`), the `impacted` impact query, emission constructors for the
  three high-value families (route-covers, scope-authority,
  dossier-freshness), and sidecar round-trip (`to_dict`/`from_dict`,
  `load_ledger`/`dump_ledger`).
- Staleness delegates to the `ClaimStale` predicate — one definition of
  stale. Contested claims report through `impacted` as-is and never clear
  on recompute; only `endorse` clears them.
- `tests/test_semantic_lineage.py`: exact stale-propagation on fixture
  change (readers stale, non-readers untouched), contract-move staleness,
  hash moves, contest/endorse lifecycle, schema refusal, id-rename
  refusal, missing-ledger-as-empty.
- Lineage section in `system/SEMANTIC-CONTRACT.md`; this record.

## Explicit non-changes

- No live ledger committed: backfill is lazy — the first real entries
  arrive with the Phase 3 detectors and Phase 6 envelope, judged
  one claim at a time.
- No contract-version bump: predicate truth tables untouched (still v2).
- No VOQ additions: the Phase 1 set stays a frozen benchmark.
- No canonical migration, no gateway change, no new write path, no
  hand-edit of rebuilt views. No critique-point action taken.

## Validation observed (2026-09-07 session)

`make check` zero errors; warning baseline OK; `make lint` incl. code
reachability (157/157) green; lineage suite plus contract-register suite
green; full suite green; views regenerated after the final authored
change (new contracts file moves the fingerprint).
