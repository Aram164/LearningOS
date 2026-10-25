# Core code map

LearningOS keeps learner-authored state in ordinary files and derives a bounded
read surface over it. It lets a human, an AI operator and the Obsidian UI share
that state without granting an interface its own writer or its own interpretation
of record ownership. Product ownership remains in `system/ARCHITECTURE.md`.

## Where to change what

Start at `tools/los.py`. The adapters parse; the app pipeline admits and
coordinates; handlers own operation families. Derivations compute views and
judgments over loaded state; store owns loading, contracts and persistence;
domain holds semantic leaves. Follow one component below instead of reading
every package. `tools/README.md` classifies the separate executable tools.

<!-- system-map:begin name=index -->
- `ai-action-store` — Persist bounded AI request/delivery state and exact artifact bindings.
- `ai-delivery` — Prepare and apply bounded AI deliveries over exact requests and reviewed artifacts.
- `backup` — Enumerate and verify the declared backup boundary with explicit exclusions.
- `cli-adapter` — Parse CLI requests and render operation outcomes without owning semantic rules.
- `contracts` — Load and enforce declared shapes, capabilities, scopes and documentation authority.
- `derived-store` — Persist disposable projections and caches under their dependency pins.
- `diagnostics` — Record bounded disposable operation traces and diagnostic evidence.
- `domain` — Provide dependency-light semantic leaves, identifiers, refusals and record rules.
- `evidence` — Read evidence references and compare the declared content bindings.
- `learner-derivations` — Derive learner runtime, ability, route, semester and freshness context.
- `legacy-archive` — Read the frozen legacy boundary and its declared allowlisted evidence.
- `loading` — Load authored records and expand declared references into repository read models.
- `masters-planning` — Prepare bounded administrative operations over quarantined future planning records.
- `materials` — Resolve and observe registered material bytes, exact spans and evidence bindings.
- `operation-handlers` — Translate each operation family into read results or bounded write proposals.
- `operation-pipeline` — Admit, lock, dispatch and settle one operation through the shared application boundary.
- `package-root` — Expose package metadata from the declared project version.
- `plan-gate` — Preflight reviewed plan packages and bind proposed learning changes to their evidence.
- `projection` — Publish deterministic views and the producer-owned manifest from loaded state.
- `search` — Build bounded searchable views over already-loaded knowledge.
- `semantics` — Interpret evidence through predicates, policy, lineage, dossiers and proposals.
- `session-ledger` — Track session-owned touched files and closure boundaries separately from learner content.
- `transactions` — Own atomic canonical commits, artifact revisions, before-images and receipts.
- `validation` — Validate loaded records and repository contracts, preserving explicit error ownership.
<!-- system-map:end -->

## Boundaries that must survive a change

`pyproject.toml` declares `A1 layers (PLAN D17)`, `A1 transaction writer access
(PLAN A2, D4)` and `A1 transaction service protected (PLAN A1, D14)`.
Import-linter enforces those contracts; map arrows explain static dependencies.
Derivations must never become canonical writers. Only the application may call
the transaction service. A handler builds a bounded proposal; it must never
invent an unguarded persistence path. Interfaces use the CLI, never Python internals.

`tests/architecture/` owns refusal-site, ownership and ratchet inventories.
ADR-018 explains those gates; ADR-019 records this documentation split.
The import graph may contain reciprocal component dependencies inside one layer;
that does not imply a cycle among individual Python modules.

## Cross-cutting concerns

Concurrency binds snapshots and artifact revisions, retries bind exact intent,
and a successful canonical write has one append-only receipt. Diagnostics are
disposable evidence, not canonical truth. Source evidence and material identity
remain distinct from a semantic judgment of coverage. Follow FLOWS for the
order of work and the component pages for tests and constraints.

This overview is intentionally stable. Only the component index and dependencies
are regenerated. Do not expand it into a function catalogue.
