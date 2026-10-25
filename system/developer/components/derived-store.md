# derived-store

## Purpose

Persist disposable projections and caches under their dependency pins.

## Owned paths

- `tools/learning_os/store/derived/*`
- `tools/learning_os/store/validation_cache.py`
- `tools/learning_os/store/warning_baseline.py`

## Entry points

- `tools/learning_os/store/validation_cache.py::observe_pins`
- `tools/learning_os/store/validation_cache.py::read_cached_static_issues`

## Depends on and used by

<!-- system-map:begin name=edges -->
Depends on: `contracts`, `domain`, `loading`, `materials`, `package-root`, `session-ledger`, `transactions`.

Used by: `operation-handlers`, `operation-pipeline`, `plan-gate`, `projection`, `search`, `semantics`, `transactions`, `validation`.
<!-- system-map:end -->

## Invariants

- Stale or corrupt cache content is a miss, never authority for current state. Pinning: `tests/test_validation_cache.py`.

## Pinning tests

- `tests/test_validation_cache.py`

## Binding ADRs

- `system/adr/ADR-018-operations-boundary-and-enforced-architecture-2026-10-03.md`
