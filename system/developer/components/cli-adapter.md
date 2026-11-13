# cli-adapter

## Purpose

Parse CLI requests and render operation outcomes without owning semantic rules.

## Owned paths

- `tools/learning_os/adapters/*`

## Entry points

- `tools/learning_os/adapters/cli_entry.py::run`
- `tools/learning_os/adapters/study_broker.py::StudyBroker`

## Depends on and used by

<!-- system-map:begin name=edges -->
Depends on: `contracts`, `diagnostics`, `domain`, `loading`, `materials`, `operation-pipeline`.

Used by: none.
<!-- system-map:end -->

## Invariants

- Keep parsing separate from canonical writes. Pinning: `tests/test_cli.py`.
- Keep the study broker (`StudyBroker`) strictly default-deny on `ALLOWED_LOS_COMMANDS` and `ALLOWED_CAPABILITIES`, pinning `--root`, `LOS_OBSERVATIONS`, and authoritative study sessions. Pinning: `tests/test_study_broker.py`.

## Pinning tests

- `tests/test_cli.py`
- `tests/test_study_broker.py`

## Binding ADRs

- `system/adr/ADR-018-operations-boundary-and-enforced-architecture-2026-10-03.md`
