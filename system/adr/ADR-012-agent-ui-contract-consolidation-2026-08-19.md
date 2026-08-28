# ADR-012 — Agent-UI / Agent-OS contract consolidation

- **Status:** accepted
- **Date:** 2026-08-19
- **Scope:** public read contracts, canonical mutation receipts, and UI mirrors

> **Amended by ADR-013 (2026-08-26):** the producer-owned Job dashboard/plan
> contracts and structured Job workspace decisions below are retired. The
> manifest, transaction, stable-module-name, shared-reader, rollback, and
> fingerprint decisions remain active.

## Context

The 2026-08-18 engineering review found several places where an architectural
rule was written down but not represented by one executable boundary:

- the UI's stable manifest types lived in a module whose filename embedded the
  current contract version;
- the confidential Job dashboard had a named result but no producer-owned
  schema or checked UI mirror;
- Job workspace fields were inferred from Markdown headings;
- AI delivery application reimplemented canonical write, rollback, publication,
  and receipt behaviour beside the shared transaction service;
- the generic capability gateway repeated the public command registry.

Those parallel representations could drift while every individual component
still appeared locally valid.

## Decision

1. **One public capability catalogue.** `system/contracts/capabilities.yaml` is
   the only public command/query registry. Query declarations may point to their
   producer-owned JSON Schema.
2. **One canonical transaction boundary.** AI delivery application uses
   `TransactionService`. The AI request's completed state is a
   transaction-owned write carrying the same transaction ID. The only receipt
   is the standard append-only receipt under `operations/transactions/`,
   governed by `transaction-receipt.schema.json`.
3. **Producer-owned Job contracts.** Core emits `job-dashboard-v2` only after
   validating the complete response against `job-dashboard.schema.json`.
   Structured plan writes and reads validate against `job-plan.schema.json`.
   The UI holds an exact, CI-checked mirror of the dashboard schema.
4. **Structured workspace data.** `Job/dashboard.yaml` owns the workspace read
   record. The linked Markdown remains an openable human document, never an
   implicit API defined by heading names.
5. **Stable UI module names.** UI imports `contracts/manifest`; version remains
   contract data in `MANIFEST_CONTRACT_VERSION` and in the single discovered
   `manifest-v<N>.lock.json` mirror.
6. **Shared boundary readers.** UI feature decoders use the common projection
   reader toolkit. Feature modules retain only domain-specific normalization.
7. **Honest rollback reporting.** If restoration itself fails, the transaction
   reports every unrestored path and does not claim a clean rollback.
8. **Layered fingerprint ownership.** Canonical and loaded-repository digest
   functions live in `learning_os.fingerprint`; validation does not depend on
   generated-view modules, and `genout` exports no private helpers.

## Consequences

- Core and UI contract changes must land together. `npm run contract:check`
  compares the Job schema mirror byte-for-meaning and discovers the manifest
  lock without a versioned source-code path.
- Adding or changing a public Job response field starts in the Core schema and
  producer, then updates the UI mirror, typed contract, decoder, and fixtures.
- AI-specific provenance belongs in standard receipt `metadata`; it does not
  justify an AI-only receipt store or a second transaction implementation.
- Human prose may change headings without silently changing the Job API.
- Legacy Job plan v1 remains readable, while all new structured plan writes are
  strict v2 records.
