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
5. Practice export is one-way and append-only into a separate LearnKit vault.
   Core records reviewed item proofs. LearnKit owns its plugin state,
   schedules and review history.

## Consequences

Stored rows without the new fields stay byte-identical; defaults are
projected, not migrated. A failed board-refresh or portal gate blocks only
the affected feature; the list remains the fallback.

## Amendment, 2026-11-23: the Atlas keeper and reviewed practice

Aram decided on 2026-11-22 that the Atlas is an agent-operated domain: the
agent writes relations with source evidence, and he vetoes or pins afterwards.
This amends ADR-017 decision 2 ("Aram is the author; the AI is a proposer")
for concept relations only. His notes, wording, questions, plans and
abilities keep every existing protection.

6. **The keeper writes under a standing delegation.** An agent running a
   bounded job applies `concept.relations.change` on the `system-task`
   channel only while `system/contracts/delegations/atlas-keeper.yaml` is
   `active` and today lies between its `granted` and `expires` dates, at most
   `max_operations` operations per batch. Authority comes from that recorded
   delegation and the deterministic checks, never from the model. Setting
   `status: suspended` stops every keeper write at once. Each keeper
   receipt records the `system-task` channel and its commit time; because
   the file is Git-tracked, that identifies the delegation in force only when
   it was committed before the write. An uncommitted edit is recorded
   nowhere until the receipt carries the digest (below).
7. **Every keeper claim is grounded.** An active keeper relation cites at
   least one evidence binding whose quote Core finds verbatim on the pinned
   page of a registered PDF. The keeper's additions are stamped `origin:
   pilot`; relations Aram adds in the app are stamped `origin: aram`.
8. **Aram's decisions are his.** The keeper never deletes (it retracts with a
   reason), never pins, vetoes or disputes evidence, never changes a row's
   origin, and never touches a row Aram authored or pinned. A vetoed edge
   returns only with evidence from a source not cited before (decision 2).
   The app shows who added each relation, beside Veto and Pin.
9. **Practice proofs bind what was reviewed.** A recorded verification's
   `artifact_sha256` must equal the item's current content hash as
   `practice.context` showed it; Core pins a source PDF's digest itself; a
   `source-matched` proof quotes the official answer, found verbatim on the
   pinned page when recorded and again on every read, so a hand-edited excerpt
   reads unverified and is not exported; and eligibility is decided per item, so one ambiguous item
   never blocks its siblings. `cross-checked` stays in the stored format, but
   Core refuses new records and reads existing ones as unverified until it
   stores the independent comparison a digest would name.

Not built here, and still to decide: the blind auditor and the automatic
demotion on measured precision (proposal D5), the triggers that start a
keeper run (D6), and the delegation's SHA-256 in each keeper receipt, which
needs a field in the closed v2 receipt metadata and so the next stored-format
version. Until then the delegation's `status` is the manual switch.
