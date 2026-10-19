# Intelligence Plane — Phase 5 record (materialized context dossiers)

Parent proposal: `intelligence-plane-plan.md`. Prior phases: Phase 0
(record), Phase 1 (23 predicates, contract v2, 20 VOQs), Phase 1.5
(policy-query envelope), Phase 2 (lineage sidecar), Phase 3 (goal
engine), Phase 4 (Task IR, telemetry, static router).

## What Phase 5 lands

- `tools/learning_os/semantics/dossiers.py`: pure dossier builder with
  one hash per dependency (knowledge map, source map, routes, evidence,
  semantic- plus operator-contract versions), addressed as
  `context://<unit-id>/semantic-dossier@<digest16>`. Same inputs always
  produce the same key; a meaning change invalidates exactly like a
  content change.
- Minimal content-addressed cache under the rebuilt views
  (`dossiers/` beneath them; digest in the filename, so a stale bundle
  cannot shadow a fresh one):
  `store_dossier`/`load_dossier`, where load recomputes every hash and
  refuses poison loudly. Freshness delegates to the `DossierFresh`
  predicate — one definition of fresh.
- `tests/test_context_dossiers.py`: identical-key cache hit,
  single-dependency invalidation on a route change, poison and garbage
  refusal, byte-identical canonical sentinel after build plus store.
- Dossiers section in `system/SEMANTIC-CONTRACT.md`; this record.

## Explicit non-changes

- No validator change: dossiers inherit the existing no-hand-edit path
  (rebuilt views are never an input to canonical files); no canonical
  file references them.
- No serving harness: the key scheme is the reuse path Muse/Claude/Astra
  will request against; who serves it is operator wiring, not semantics.
- No contract-version bump (still v2), no VOQ additions, no prefetching
  or eviction policy (the cache is exact-keyed; both arrive only with
  measured reuse).
- No canonical migration, no gateway change, no new write path, no
  hand-edit of rebuilt views. No critique-point action taken.

## Validation observed (2026-09-07 session)

`make check` zero errors; warning baseline OK; `make lint` incl. code
reachability (160/160) green; dossier suite green; full suite green;
views regenerated after the final authored change.
