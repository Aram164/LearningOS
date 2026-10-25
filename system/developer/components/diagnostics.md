# diagnostics

## Purpose

Record bounded disposable operation traces and diagnostic evidence.

## Owned paths

- `tools/learning_os/store/diagnostics/*`

## Entry points

- `tools/learning_os/store/diagnostics/tracer.py::begin_attempt`

## Depends on and used by

<!-- system-map:begin name=edges -->
Depends on: `contracts`, `domain`, `evidence`, `loading`, `transactions`.

Used by: `cli-adapter`, `operation-handlers`, `operation-pipeline`, `transactions`.
<!-- system-map:end -->

## Invariants

- Diagnostics must not become a second canonical state store. Pinning: `tests/test_diagnostic_store.py`.

## Pinning tests

- `tests/test_diagnostic_store.py`

## Binding ADRs

- `system/adr/ADR-018-operations-boundary-and-enforced-architecture-2026-10-03.md`
