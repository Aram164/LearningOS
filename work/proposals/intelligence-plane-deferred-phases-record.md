# Intelligence Plane — deferred phases (shelved with gate evidence)

Parent proposal: `intelligence-plane-plan.md`. Decided 2026-09-08:
Phases 7, 8, 11 do not earn their complexity today; Phase 9 waits for
Phase 10 (now landed); Phase 12 is skipped. Each entry carries the
measurement that shelved it and the bar that re-opens it. Re-activation
needs Aram's explicit go-ahead in that session — a crossed bar is
evidence, not authorization.

## Phase 7 — incremental view rebuilds: SHELVED

Gate A (2026-09-08): full `make views` takes ~2s on 14 modules / 15MB
manifest. Optimizing a 2-second build with invalidation machinery (whose
bug class is serving stale rows as the read contract) is bloat.
Re-opens iff a timed full rebuild reaches ~60s. If built: reuse the
Phase 5 digest scheme, never a second hashing design; full rebuild
stays the fallback and the byte-identity test gates it.

## Phase 8 — cross-module semantic intelligence: SHELVED

Gate C audit (2026-09-08, probe kept outside the repo): 0 shared
concept titles across modules (no `ConceptOverlap` evidence); 44
shared sources, 19 with differing per-module roles — legitimate
module-relative roles (e.g. ISLP is `spine` in AML, `reference` in
SaD), not routing errors. `CrossModuleCoverageGap` unchecked: no
curriculum-structure baseline defines "should be covered."
Re-opens iff a future audit surfaces a real divergence (shared
concept with drifting coverage claims, or one source covering
contradictory nodes). First step then is a one-shot audit with
existing predicates, not permanent detectors.

## Phase 9 — blackboard scheduler: SHELVED until after Phase 10

Design objections stand (recorded 2026-09-08): "cheapest useful next
action" reintroduces cost-routing against the Phase 4 amendment and
must be reframed evidence-first with cost terms forbidden; early
termination must never skip challengers for canonical writes
(confidence is self-reported by the agent being skipped). Phase 10's
assumption graph now covers the "what is known" layer, so a revived
Phase 9 is a smaller coordination phase, not a from-scratch
blackboard. Re-opens iff multi-agent waste is demonstrated on live
tasks AND the reframed design is approved first.

## Phase 11 — fine-grained MVCC: SHELVED

Gate B (2026-09-08): zero `"Snapshot mismatch"` occurrences across
`records/` and `work/` — no concurrent-write pain exists, so the
global snapshot guard stands as correct and simple. Narrowed scope on
record: the Phase 6 envelope already carries `read_revisions` plus
per-write scopes, so this was always a freshness-check refinement,
not new envelope machinery. Re-opens iff real conflict-driven
replans appear in session history (count ephemerally — stored
measurement logs would recreate what the Phase 4 amendment removed).

## Phase 12 — formal protocol verification: SKIPPED

Not shelved with a bar — skipped by decision. Rationale: Python
bounded-exhaustive models were the recommended shape, but with
Phases 7/8/11 shelved and 9 deferred, the remaining protocol surface
(Phase 10 cascades) is covered by fixture tests asserting
completeness, monotonicity, and unrelated-claim safety. Revisit only
if a new admission/concurrency protocol lands.
