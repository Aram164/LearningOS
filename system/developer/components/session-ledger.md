# session-ledger

## Purpose

Track session-owned touched files and closure boundaries separately from learner content.

## Owned paths

- `tools/learning_os/store/session_ledger.py`
- `tools/learning_os/store/session/*`

## Entry points

- `tools/learning_os/store/session_ledger.py::record_touched`
- `tools/learning_os/store/session_ledger.py::close_session_ledger`

## Depends on and used by

<!-- system-map:begin name=edges -->
Depends on: `contracts`, `domain`, `materials`.

Used by: `derived-store`, `operation-handlers`, `operation-pipeline`, `projection`, `semantics`, `validation`.
<!-- system-map:end -->

## Invariants

- Never claim unrelated dirty files or stage the internal session ledger. Pinning: `tests/test_session_ledger.py`.

## Pinning tests

- `tests/test_session_ledger.py`

## Binding ADRs

- `system/adr/ADR-018-operations-boundary-and-enforced-architecture-2026-10-03.md`
