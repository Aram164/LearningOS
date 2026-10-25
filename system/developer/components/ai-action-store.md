# ai-action-store

## Purpose

Persist bounded AI request/delivery state and exact artifact bindings.

## Owned paths

- `tools/learning_os/store/ai_actions/*`

## Entry points

- `tools/learning_os/store/ai_actions/binding.py::read_bound_delivery`

## Depends on and used by

<!-- system-map:begin name=edges -->
Depends on: `domain`, `loading`, `materials`, `transactions`.

Used by: `ai-delivery`, `evidence`, `learner-derivations`, `validation`.
<!-- system-map:end -->

## Invariants

- AI state is not permission to rewrite arbitrary learner records. Pinning: `tests/test_ai_actions.py`.

## Pinning tests

- `tests/test_ai_actions.py`

## Binding ADRs

- `system/adr/ADR-018-operations-boundary-and-enforced-architecture-2026-10-03.md`
