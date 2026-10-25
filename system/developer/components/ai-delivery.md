# ai-delivery

## Purpose

Prepare and apply bounded AI deliveries over exact requests and reviewed artifacts.

## Owned paths

- `tools/learning_os/app/ai_actions/*`

## Entry points

- `tools/learning_os/app/ai_actions/service.py::AIActionService`

## Depends on and used by

<!-- system-map:begin name=edges -->
Depends on: `ai-action-store`, `contracts`, `domain`, `evidence`, `learner-derivations`, `loading`, `materials`, `operation-pipeline`, `projection`, `semantics`, `transactions`, `validation`.

Used by: `operation-handlers`.
<!-- system-map:end -->

## Invariants

- A provider response must never authorize its own canonical mutation. Pinning: `tests/test_ai_actions.py`.

## Pinning tests

- `tests/test_ai_actions.py`

## Binding ADRs

- `system/adr/ADR-018-operations-boundary-and-enforced-architecture-2026-10-03.md`
