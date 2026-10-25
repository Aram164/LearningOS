# transactions

## Purpose

Own atomic canonical commits, artifact revisions, before-images and receipts.

## Owned paths

- `tools/learning_os/store/transactions.py`
- `tools/learning_os/store/revisions.py`
- `tools/learning_os/store/fingerprint.py`
- `tools/learning_os/store/digests.py`
- `tools/learning_os/store/manifest_identity.py`

## Entry points

- `tools/learning_os/store/transactions.py::TransactionService.commit`
- `tools/learning_os/store/transactions.py::reconcile_inflight_transactions`

## Depends on and used by

<!-- system-map:begin name=edges -->
Depends on: `contracts`, `derived-store`, `diagnostics`, `domain`, `evidence`, `loading`, `materials`, `package-root`.

Used by: `ai-action-store`, `ai-delivery`, `contracts`, `derived-store`, `diagnostics`, `evidence`, `learner-derivations`, `masters-planning`, `materials`, `operation-handlers`, `operation-pipeline`, `plan-gate`, `projection`, `semantics`, `validation`.
<!-- system-map:end -->

## Invariants

- Only the application may invoke this writer; rollback must restore the complete bounded set. Pinning: `tests/test_transactions.py`.

Every declared canonical mutation now passes through `TransactionService`.
The service applies one bounded write set, checks artifact-level expected
revisions, validates the resulting repository, republishes disposable views,
and records exactly one append-only receipt under
`operations/transactions/`. A failed stage rolls the complete write set back.
Interfaces discover the executable catalogue in
`system/contracts/capabilities.yaml`; they do not invent write paths.

Artifact revisions are coordination tokens, not replacements for Git history.
Revision zero is implicit for authored records that have not yet been changed
through the transaction service.

## Pinning tests

- `tests/test_transactions.py`

## Binding ADRs

- `system/adr/ADR-018-operations-boundary-and-enforced-architecture-2026-10-03.md`
