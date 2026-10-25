# masters-planning

## Purpose

Prepare bounded administrative operations over quarantined future planning records.

## Owned paths

- `tools/learning_os/app/admin/*`

## Entry points

- `tools/learning_os/app/admin/masters_planning.py::masters_planning_dashboard`
- `tools/learning_os/app/admin/masters_planning.py::prepare_master_promotion`

## Depends on and used by

<!-- system-map:begin name=edges -->
Depends on: `contracts`, `domain`, `learner-derivations`, `loading`, `materials`, `transactions`.

Used by: `operation-handlers`, `plan-gate`.
<!-- system-map:end -->

## Invariants

- Quarantined planning must stay outside ordinary curriculum loading. Pinning: `tests/test_master_promotion.py`.

## Pinning tests

- `tests/test_master_promotion.py`

## Binding ADRs

- `system/adr/ADR-018-operations-boundary-and-enforced-architecture-2026-10-03.md`
