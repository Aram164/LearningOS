# validation

## Purpose

Validate loaded records and repository contracts, preserving explicit error ownership.

## Owned paths

- `tools/learning_os/derive/validation/*`

## Entry points

- `tools/learning_os/derive/validation/core.py::Validator.run`

## Depends on and used by

<!-- system-map:begin name=edges -->
Depends on: `ai-action-store`, `contracts`, `derived-store`, `domain`, `evidence`, `learner-derivations`, `loading`, `materials`, `projection`, `semantics`, `session-ledger`, `transactions`.

Used by: `ai-delivery`, `backup`, `learner-derivations`, `operation-pipeline`, `plan-gate`.
<!-- system-map:end -->

## Invariants

- Do not mutate canonical records or call the transaction service. Pinning: `tests/test_validation.py`.

## Pinning tests

- `tests/test_validation.py`

## Binding ADRs

- `system/adr/ADR-018-operations-boundary-and-enforced-architecture-2026-10-03.md`
