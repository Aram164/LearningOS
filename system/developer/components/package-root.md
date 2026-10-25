# package-root

## Purpose

Expose package metadata from the declared project version.

## Owned paths

- `tools/learning_os/__init__.py`

## Entry points

- `tools/learning_os/__init__.py::_declared_version`

## Depends on and used by

<!-- system-map:begin name=edges -->
Depends on: none.

Used by: `derived-store`, `operation-handlers`, `projection`, `transactions`.
<!-- system-map:end -->

## Invariants

- Package metadata must not initialize application services or learner state. Pinning: `tests/test_code_reachability.py`.

## Pinning tests

- `tests/test_code_reachability.py`

## Binding ADRs

- `system/adr/ADR-018-operations-boundary-and-enforced-architecture-2026-10-03.md`
