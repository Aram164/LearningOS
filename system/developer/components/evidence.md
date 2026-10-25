# evidence

## Purpose

Read evidence references and compare the declared content bindings.

## Owned paths

- `tools/learning_os/store/evidence.py`

## Entry points

- `tools/learning_os/store/evidence.py::verify_committed_evidence`
- `tools/learning_os/store/evidence.py::replay_for_request`

## Depends on and used by

<!-- system-map:begin name=edges -->
Depends on: `ai-action-store`, `contracts`, `domain`, `loading`, `transactions`.

Used by: `ai-delivery`, `diagnostics`, `operation-pipeline`, `transactions`, `validation`.
<!-- system-map:end -->

## Invariants

- A quotation or digest proves presence and identity, not semantic support. Pinning: `tests/test_evidence_staleness.py`.

## Pinning tests

- `tests/test_evidence_staleness.py`

## Binding ADRs

- `system/adr/ADR-018-operations-boundary-and-enforced-architecture-2026-10-03.md`
