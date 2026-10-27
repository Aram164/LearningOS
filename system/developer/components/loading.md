# loading

## Purpose

Load authored records and expand declared references into repository read models.

## Owned paths

- `tools/learning_os/store/__init__.py`
- `tools/learning_os/store/loader.py`
- `tools/learning_os/store/loading/*`
- `tools/learning_os/store/codec.py`
- `tools/learning_os/store/layout.py`
- `tools/learning_os/store/fs.py`

## Entry points

- `tools/learning_os/store/loading/__init__.py::load_repo`

## Depends on and used by

<!-- system-map:begin name=edges -->
Depends on: `domain`.

Used by: `ai-action-store`, `ai-delivery`, `backup`, `cli-adapter`, `derived-store`, `diagnostics`, `evidence`, `learner-derivations`, `masters-planning`, `materials`, `operation-handlers`, `operation-pipeline`, `plan-gate`, `projection`, `semantics`, `transactions`, `validation`.
<!-- system-map:end -->

## Invariants

- Never infer ownership from prose or cross an external sibling boundary. Pinning: `tests/test_curriculum_v2.py`.

The loader expands references within
the same module and unit, refusing missing or ambiguous routes and overlapping
inherited/local fields. Runtime consumers and the manifest declared in
`system/contracts/manifest-contract.yaml` retain their complete expanded
shape. Editing context exposes the compact shape with its route
definitions once; ordinary state saves preserve that storage form.

## Pinning tests

- `tests/test_curriculum_v2.py`

## Binding ADRs

- `system/adr/ADR-018-operations-boundary-and-enforced-architecture-2026-10-03.md`
