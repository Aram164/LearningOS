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
- `tools/learning_os/store/materials/reading_cards.py::ReadingStore`

## Depends on and used by

<!-- system-map:begin name=edges -->
Depends on: `contracts`, `domain`, `loading`, `transactions`.

Used by: `ai-action-store`, `ai-delivery`, `backup`, `cli-adapter`, `contracts`, `derived-store`, `learner-derivations`, `legacy-archive`, `masters-planning`, `operation-handlers`, `operation-pipeline`, `plan-gate`, `projection`, `semantics`, `session-ledger`, `transactions`, `validation`.
<!-- system-map:end -->

## Invariants

- A locator must bind its own source bytes; never widen an invalid requested window. Pinning: `tests/test_material_span.py`.
- The full-text material search index is a self-describing, disposable read-only artifact under `generated/material-search/` that validates live material bytes and reports text-cache freshness and corpus coverage on every query. Pinning: `tests/test_material_search.py`.
- Search hits are section groups. A page belongs to the PDF outline section that owns it, read from the digest-keyed `generated/material-outlines/` cache that `tools/material_outline.py` harvests; a document's pages without a section form one explicit unsectioned group with its reason. `limit` and `offset` count groups over one fixed candidate scan. A query equal to a registered concept label or alias also searches the concept's other names. Pinning: `tests/test_material_search.py`.

- The private reading memory (ADR-021) lives in `LearningOS/reading-memory/`, beside the checkout and outside Core Git, the materials inventory and the manifest. `reading_cards.py` owns it: owner-only files, every record validated against `system/schema/material-reading-card.schema.json`, every write under one lock and a journal. A study read persists an open entry before returning text for any PDF span no current card or settled dismissal of the same digest contains; a session holds at most four open entries, and overdue or adoptable entries refuse new spans while pending and covered spans stay readable. Pinning: `tests/test_material_reading_cards.py`, `tests/test_study_hooks.py`.

Plain Markdown and text quotations use `line_start` and `line_end`, one-based
and inclusive, on the exact `material://` file. A declared locator line span
also bounds the quote. PDF evidence keeps its page fields; timestamped
transcripts keep their window, video identity and grid checks and cannot use
line ranges. All forms bind the registered digest and reject changed bytes.

## Pinning tests

- `tests/test_material_span.py`
- `tests/test_material_search.py`
- `tests/test_material_reading_cards.py`
- `tests/test_study_hooks.py`
- `tests/test_study_launch.py`

## Binding ADRs

- `system/adr/ADR-018-operations-boundary-and-enforced-architecture-2026-10-03.md`
- `system/adr/ADR-020-derived-material-search-index-2026-11-08.md`
- `system/adr/ADR-021-private-reading-memory-2026-11-12.md`
