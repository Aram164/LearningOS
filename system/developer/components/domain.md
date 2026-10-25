# domain

## Purpose

Provide dependency-light semantic leaves, identifiers, refusals and record rules.

## Owned paths

- `tools/learning_os/domain/*`
- `tools/learning_os/domain/curriculum/*`

## Entry points

- `tools/learning_os/domain/ids.py::parse`

## Depends on and used by

<!-- system-map:begin name=edges -->
Depends on: none.

Used by: `ai-action-store`, `ai-delivery`, `cli-adapter`, `contracts`, `derived-store`, `diagnostics`, `evidence`, `learner-derivations`, `loading`, `masters-planning`, `materials`, `operation-handlers`, `operation-pipeline`, `plan-gate`, `projection`, `semantics`, `session-ledger`, `transactions`, `validation`.
<!-- system-map:end -->

## Invariants

- Domain must not import persistence or the application layers. Pinning: `tests/test_domain_failures.py`.

## Pinning tests

- `tests/test_domain_failures.py`

## Binding ADRs

- `system/adr/ADR-018-operations-boundary-and-enforced-architecture-2026-10-03.md`
