# materials

## Purpose

Resolve and observe registered material bytes, exact spans and evidence bindings.

## Owned paths

- `tools/learning_os/store/materials/*`
- `tools/learning_os/store/material_analysis.py`
- `tools/learning_os/store/material_observations.py`
- `tools/learning_os/store/observations.py`

## Entry points

- `tools/learning_os/store/materials/resolution.py::resolve_material_target`
- `tools/learning_os/store/materials/slices.py::build_unit_slices`
- `tools/learning_os/store/materials/search_index.py::execute_search`

## Depends on and used by

<!-- system-map:begin name=edges -->
Depends on: `domain`, `loading`, `transactions`.

Used by: `ai-action-store`, `ai-delivery`, `backup`, `contracts`, `derived-store`, `learner-derivations`, `legacy-archive`, `masters-planning`, `operation-handlers`, `operation-pipeline`, `plan-gate`, `projection`, `semantics`, `session-ledger`, `transactions`, `validation`.
<!-- system-map:end -->

## Invariants

- A locator must bind its own source bytes; never widen an invalid requested window. Pinning: `tests/test_material_span.py`.
- The full-text material search index is a self-describing, disposable read-only artifact under `generated/material-search/` that validates live material bytes and reports text-cache freshness and corpus coverage on every query. Pinning: `tests/test_material_search.py`.

## Pinning tests

- `tests/test_material_span.py`
- `tests/test_material_search.py`

## Binding ADRs

- `system/adr/ADR-018-operations-boundary-and-enforced-architecture-2026-10-03.md`
- `system/adr/ADR-020-derived-material-search-index-2026-11-08.md`
