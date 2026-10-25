# projection

## Purpose

Publish deterministic views and the producer-owned manifest from loaded state.

## Owned paths

- `tools/learning_os/derive/projection/*`
- `tools/learning_os/derive/projection/projection/*`

## Entry points

- `tools/learning_os/derive/projection/outputs.py::generate_all`
- `tools/learning_os/derive/projection/outputs.py::write_outputs`

## Depends on and used by

<!-- system-map:begin name=edges -->
Depends on: `contracts`, `derived-store`, `domain`, `learner-derivations`, `loading`, `materials`, `package-root`, `semantics`, `session-ledger`, `transactions`.

Used by: `ai-delivery`, `backup`, `learner-derivations`, `operation-handlers`, `operation-pipeline`, `validation`.
<!-- system-map:end -->

## Invariants

- Generated output must never become canonical input. Pinning: `tests/test_projection_fidelity.py`.

Projection changes remain producer-owned and must be mirrored in the UI contract lock in the same release.

## Pinning tests

- `tests/test_projection_fidelity.py`

## Binding ADRs

- `system/adr/ADR-018-operations-boundary-and-enforced-architecture-2026-10-03.md`
