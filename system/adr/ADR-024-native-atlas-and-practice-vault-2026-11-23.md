# ADR-024: Native Atlas boards and a separate practice vault

Date: 2026-11-23. Status: accepted (experimental branch
`experimental/native-atlas-practice`). Extends: ADR-006, ADR-016, ADR-017.

## Context

The isolated engineering comparison (2026-11-23) found native JSON Canvas
saves layout reliably while reaching no individual card by keyboard, and a
React Flow prototype reached every card but activated no edge, lost keyboard
moves on reopen, and added about 2.1 MB of JavaScript. Advanced Canvas loaded
portals but refresh discarded portal state. LearnKit retained synthetic
reviews through re-export and restart, with append-only export preserving
existing files byte-for-byte.

## Decision

1. One native renderer. Core publishes deterministic JSON Canvas templates
   (`generated/atlas/`) and a Manifest 21 `atlas_boards` catalog; the UI owns
   editable working boards under `boards/` and a keyboard-complete list. No
   second visual renderer.
2. Relation lifecycle is stored data: optional `origin`, `status`,
   `pinned`, `status_reason`, `evidence_disputed` and up to eight PDF
   evidence bindings, with stored format 69. Only active edges traverse;
   retracted/vetoed edges remain in History. A pinned row accepts only an
   exact unpin; decorated rows are retracted, never hard-deleted.
3. Evidence state is derived, never asserted: disputed, stale, missing,
   verified, in that precedence. A label alone proves nothing.
4. Editable-board refresh is explicit and guarded; portals (Advanced Canvas)
   are an optional view over the same working files, never a second board.
5. Practice export, when it lands, is one-way and append-only into a
   separate LearnKit vault; Core never writes plugin state, schedules or
   review history. (P6, deferred at adoption time of this branch's first
   phases.)

## Consequences

Stored rows without the new fields stay byte-identical; defaults are
projected, not migrated. A failed board-refresh or portal gate blocks only
the affected feature; the list remains the fallback.
