# plan-gate

## Purpose

Preflight reviewed plan packages and bind proposed learning changes to their evidence.

## Owned paths

- `tools/learning_os/app/_plan_gate.py`

## Entry points

- `tools/learning_os/app/_plan_gate.py::plan_apply_gate`
- `tools/learning_os/app/_plan_gate.py::module_plan_check_report`

## Depends on and used by

<!-- system-map:begin name=edges -->
Depends on: `contracts`, `derived-store`, `domain`, `learner-derivations`, `loading`, `masters-planning`, `materials`, `operation-pipeline`, `semantics`, `transactions`, `validation`.

Used by: `operation-handlers`.
<!-- system-map:end -->

## Invariants

- A green preflight never substitutes for the required human review. Pinning: `tests/test_unit_plan_revision.py`.

## Pinning tests

- `tests/test_unit_plan_revision.py`

## Binding ADRs

- `system/adr/ADR-018-operations-boundary-and-enforced-architecture-2026-10-03.md`
