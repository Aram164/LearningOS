# contracts

## Purpose

Load and enforce declared shapes, capabilities, scopes and documentation authority.

## Owned paths

- `tools/learning_os/store/contracts/*`

## Entry points

- `tools/learning_os/store/contracts/normative_corpus.py::load`
- `tools/learning_os/store/contracts/task_scope.py::load_task_scope`

## Depends on and used by

<!-- system-map:begin name=edges -->
Depends on: `domain`, `materials`, `transactions`.

Used by: `ai-delivery`, `backup`, `cli-adapter`, `derived-store`, `diagnostics`, `evidence`, `learner-derivations`, `legacy-archive`, `masters-planning`, `operation-handlers`, `operation-pipeline`, `plan-gate`, `projection`, `semantics`, `session-ledger`, `transactions`, `validation`.
<!-- system-map:end -->

## Invariants

- Never guess a missing or malformed contract; fail with its owning path. Pinning: `tests/test_normative_corpus.py`.

## Pinning tests

- `tests/test_normative_corpus.py`

## Binding ADRs

- `system/adr/ADR-018-operations-boundary-and-enforced-architecture-2026-10-03.md`
