# Intelligence Plane — hardening record (review-driven, items 1–6)

Parent proposal: `intelligence-plane-plan.md`. Trigger: Aram's review
of the Phase 0–6 plus Phase 10 implementation, which found the
architectural direction very good but not yet safe to build on. Verdict
carried out here: stop feature development, repair correctness holes
first. No new numbered phase; each item committed and pushed
independently (see log).

## 1. Task IR rewrite correctness (`tasks.py`)

Steps carry `id`, `depends_on`, and a kind-fixed `effect`
(pure | judgment | mutation) — purity is refused, never self-asserted.
`validate_ir` refuses empty/duplicate ids, dangling/self/cyclic
dependencies, and effect mismatches. Rewrites prove order-preservation:
pushdown is dependency-constrained topo-sort (deterministic apply stays
after model review); dedup collapses pure reads only, remapping dropped
dependencies onto the survivor; cheapest-evidence-first refuses any
acquisition-touching dependency; late materialization verifies its
candidate order and refuses breaking moves.

## 2. Admission against trusted context (`changes.py`)

The envelope carries claims only — approval, lineage verdicts, and
digests removed; smuggling trust has no field to ride in on.
`admit(envelope, context)` checks session authorization, capability
approval, scope grounding against the capability contract (verbatim
pattern or concrete path inside it; wider globs fail closed), target
scopes, freshness, snapshot, harness-resolved evidence, and live-ledger
lineage. No production callers existed, so the signature change was
contained to semantics plus tests.

## 3. Postconditions read post-apply state (`changes.py`)

Fixed envelope-time `inputs` replaced by a required `selector` naming
the harness observation. `verify_postconditions(envelope, live)`
derives predicate inputs from the post-apply world; a promised
RepoClean passes only when the actual repository validates clean, and
an unobserved selector raises instead of passing.

## 4. Dossier evidence is content-addressed (`dossiers.py`)

Evidence travels as locator→digest mappings resolved by the caller via
the materials manifest checksums — the builder still never walks the
repository. Same URI with changed bytes invalidates exactly the
evidence hash. Old list-shaped caches refuse loudly on load.

## 5. Lineage assumption integrity (`lineage.py`)

`check_assumptions()` runs on every ledger load: dangling references
refuse as LINEAGE-ASSUMPTION-MISSING, cycles as
LINEAGE-ASSUMPTION-CYCLE — before real lineage accumulates. Runtime
cascade functions needed no changes (visited-set traversal already
terminates; dangling edges never fire from a real root).

## 6. Read-only intelligence scan (`scan.py`, `intelligence-scan`)

OBSERVE → INTERPRET → PROPOSE → Aram decides queue entry. One command,
no daemon, no writes: git-recency changes joined to nodes/sources,
lineage staleness against the revision ledger, derived study-map
obligations — through the existing Phase-3 detectors plus two
scan-level emitters, human and `--json` output. Critique points
excluded by boundary 17; count-based detectors stay caller-fed (no
observable source, and building one would be telemetry); dossier
freshness waits on a live-key registry.

## Explicit non-changes

- No Phase 7/8/9/11/12 work (see the deferred-phases record — still
  shelved). No canonical schema change, no contract-version bump
  (still v2), no gateway change, no new write path, no hand-edit of
  rebuilt views. No critique-point action taken.

## Validation observed (2026-09-08 session)

Per item: `make check` zero errors; warning baseline OK; `make lint`
incl. code reachability green (163/163 with the scan modules);
targeted suites green; full suite green (1300 passed, 1 skipped final);
views regenerated after each final authored change. Committed per item,
pushed per item.
