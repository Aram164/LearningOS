# cli-adapter

## Purpose

Parse CLI requests and render operation outcomes without owning semantic rules.

## Owned paths

- `tools/learning_os/adapters/*`

## Entry points

- `tools/learning_os/adapters/cli_entry.py::run`

## Depends on and used by

<!-- system-map:begin name=edges -->
Depends on: `contracts`, `diagnostics`, `domain`, `loading`, `operation-pipeline`.

Used by: none.
<!-- system-map:end -->

## Invariants

- Keep parsing separate from canonical writes. Pinning: `tests/test_cli.py`.

## Pinning tests

- `tests/test_cli.py`

## Binding ADRs

- `system/adr/ADR-018-operations-boundary-and-enforced-architecture-2026-10-03.md`
