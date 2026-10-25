# legacy-archive

## Purpose

Read the frozen legacy boundary and its declared allowlisted evidence.

## Owned paths

- `tools/learning_os/store/legacy_archive.py`

## Entry points

- `tools/learning_os/store/legacy_archive.py::inspect_legacy_archive`

## Depends on and used by

<!-- system-map:begin name=edges -->
Depends on: `contracts`, `materials`.

Used by: `learner-derivations`, `operation-handlers`, `operation-pipeline`.
<!-- system-map:end -->

## Invariants

- Legacy history must never become the current canonical writer. Pinning: `tests/test_legacy_exit_review.py`.

## Pinning tests

- `tests/test_legacy_exit_review.py`

## Binding ADRs

- `system/adr/ADR-018-operations-boundary-and-enforced-architecture-2026-10-03.md`
