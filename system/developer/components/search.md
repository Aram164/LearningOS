# search

## Purpose

Build bounded searchable views over already-loaded knowledge (for full-text search over local PDF material pages, see [materials](materials.md)).

## Owned paths

- `tools/learning_os/derive/search/*`

## Entry points

- `tools/learning_os/derive/search/index.py::build_postings`

## Depends on and used by

<!-- system-map:begin name=edges -->
Depends on: `derived-store`.

Used by: `operation-handlers`.
<!-- system-map:end -->

## Invariants

- Search must preserve declared exclusions and stable record identity. Pinning: `tests/test_search_index.py`.

## Pinning tests

- `tests/test_search_index.py`

## Binding ADRs

- `system/adr/ADR-018-operations-boundary-and-enforced-architecture-2026-10-03.md`
- `system/adr/ADR-020-derived-material-search-index-2026-11-08.md`
