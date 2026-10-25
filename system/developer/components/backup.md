# backup

## Purpose

Enumerate and verify the declared backup boundary with explicit exclusions.

## Owned paths

- `tools/learning_os/app/backup_manifest.py`

## Entry points

- `tools/learning_os/app/backup_manifest.py::build_backup_manifest`
- `tools/learning_os/app/backup_manifest.py::verify_backup_manifest`

## Depends on and used by

<!-- system-map:begin name=edges -->
Depends on: `contracts`, `loading`, `materials`, `projection`, `validation`.

Used by: `operation-handlers`, `operation-pipeline`.
<!-- system-map:end -->

## Invariants

- Never silently omit an unreadable or symlinked declared subtree. Pinning: `tests/test_c1e_backup_symlinked_subtree.py`.

## Pinning tests

- `tests/test_c1e_backup_symlinked_subtree.py`

## Binding ADRs

- `system/adr/ADR-018-operations-boundary-and-enforced-architecture-2026-10-03.md`
