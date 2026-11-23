# practice

## Purpose

The practice verification sidecar and its one-way LearnKit export: loading
`knowledge/practice-index.yaml`, item eligibility, and append-only card
delivery (ADR-024).

## Owned paths

- `tools/learning_os/store/practice.py`
- `tools/learning_os/store/practice_export.py`

## Entry points

- `tools/learning_os/domain/practice.py::extract_items`
- `tools/learning_os/domain/practice.py::content_sha256`
- `tools/learning_os/store/practice.py::note_items`
- `tools/learning_os/store/practice.py::verified_binding`
- `tools/learning_os/store/practice_export.py::init_vault`
- `tools/learning_os/store/practice_export.py::build_plan`
- `tools/learning_os/store/practice_export.py::apply_plan`

## Depends on and used by

<!-- system-map:begin name=edges -->
Depends on: `contracts`, `domain`, `loading`, `materials`, `transactions`.

Used by: `operation-handlers`, `projection`.
<!-- system-map:end -->

## Invariants

- The sidecar never stores solution text; rows bind content digests and source bindings only (pinned by `tests/test_practice_verification.py`).
- Export is create-only and append-only; an existing reviewed card is never rewritten (pinned by `tests/test_practice_export.py`).

## Pinning tests

- `tests/test_practice_verification.py`
- `tests/test_practice_export.py`

## Binding ADRs

- `system/adr/ADR-024-native-atlas-and-practice-vault-2026-11-23.md`
