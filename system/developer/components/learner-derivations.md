# learner-derivations

## Purpose

Derive learner runtime, ability, route, semester and freshness context.

## Owned paths

- `tools/learning_os/derive/__init__.py`
- `tools/learning_os/derive/abilities.py`
- `tools/learning_os/derive/learning_runtime.py`
- `tools/learning_os/derive/routes.py`
- `tools/learning_os/derive/semesters.py`
- `tools/learning_os/derive/health.py`
- `tools/learning_os/derive/garden.py`
- `tools/learning_os/derive/masters_catalog.py`
- `tools/learning_os/derive/material_synthesis.py`
- `tools/learning_os/derive/ai_actions.py`

## Entry points

- `tools/learning_os/derive/learning_runtime.py::compile_requirement`

## Depends on and used by

<!-- system-map:begin name=edges -->
Depends on: `ai-action-store`, `contracts`, `domain`, `legacy-archive`, `loading`, `materials`, `projection`, `semantics`, `transactions`, `validation`.

Used by: `ai-delivery`, `masters-planning`, `operation-handlers`, `operation-pipeline`, `plan-gate`, `projection`, `semantics`, `validation`.
<!-- system-map:end -->

## Invariants

- Derived proposals must never declare mastery or move recorded progress. Pinning: `tests/test_learning_plan_contract.py`.

## Pinning tests

- `tests/test_learning_plan_contract.py`

## Binding ADRs

- `system/adr/ADR-018-operations-boundary-and-enforced-architecture-2026-10-03.md`
