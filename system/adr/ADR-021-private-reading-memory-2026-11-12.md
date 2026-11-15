# ADR-021: private reading memory and the reading-debt gate

Date: 2026-11-12. Status: accepted. Implements Plan C of the agent-first work
(`outputs/learningos-agent-first/PLAN-C-private-reading-cards.md` in the
`semestercontext` workspace, rev 2). Aram decided both binding points on
2026-11-12: "restore the gate" (reading debts are collected by the gateway and
the hooks, never left to a prompt) and "keep cards private".

## Decision

1. **A private store beside the repository.** Reading cards, reading entries,
   session records and settlement logs live in `LearningOS/reading-memory/`, a
   sibling of the Core checkout, created owner-only (directories 0700, files
   0600). Nothing from it enters Core Git, the materials inventory
   (`records/materials-manifest.yaml`), the published manifest or any receipt.
   It is not under `materials/`, because `tools/materials_manifest.py` walks every
   file there into a tracked inventory. It is its own backup root in
   `system/contracts/backup-roots.yaml`, inventoried while it exists.
2. **Records, not a cache.** Core writes these records and nothing rebuilds them,
   so their shapes are one stored-data schema,
   `system/schema/material-reading-card.schema.json`, inside the data-contract
   fingerprint. Every record validates before it is written. A card keeps the
   `material_analysis` binding concepts: a materials-relative `material` (where
   the bytes were last seen), the bare `recorded_source_digest` and a physical PDF
   `inspected_range`. It is keyed by digest and range, so moving a file keeps its
   cards.
3. **Effects: derived-write, outside canonical state.** `material.study-span` and
   `material.card.settle` declare effects `derived-write`. They write only the
   private store, never a canonical file, so they write no receipt. The store's
   own append-only `log/<session>.jsonl` records each save, dismissal and
   adoption, and card versions are kept, never overwritten. Every write runs
   under one `flock` and a journal, so a settlement's card version, closed entry
   and log line land as one update. `material.search` and `material.context` stay
   effects `read`: their study scope only reads the store.
4. **The gate.** A study read (`material.study-span`) computes the unchanged
   `material-span-v1` answer, nests it under `span` in `material-study-span-v1`,
   and before returning any text persists an open reading entry for every PDF
   span that no current card of the same digest contains, and that none of the
   caller's own settled dismissals contains (page containment). Saved cards
   provide reusable coverage for every caller; a dismissal closes the
   obligation for the dismissing session only — another session's dismissal
   never covers a later read, and settled dismissals of the range from any
   session are surfaced in the study answer as `prior-dismissal` memory, never
   as coverage. If the entry cannot be persisted, the read refuses. A session
   may hold four open entries; a new uncovered span refuses while the session
   holds an overdue entry or any ended or idle session's entries are
   adoptable. Pending spans, covered spans, search, context, settlement and
   adoption always stay available, and every refusal names the entries and the
   exact settle or adopt command. A clipped, truncated or non-PDF extraction,
   and a discontiguous `--pages` selection, return no text and open nothing.
5. **Session identity comes from the host launcher and broker.** `tools/study_launch.py`
   wraps study sessions under an OS-enforced macOS Seatbelt boundary
   (`/usr/bin/sandbox-exec`) paired with an unsandboxed AF_UNIX broker
   (`tools/learning_os/adapters/study_broker.py`) rather than client-side hook
   inspection (per `system/adr/ADR-022-sandboxed-study-isolation-2026-11-13.md`).
   The broker allocates the authoritative session UUID, injects `--session`,
   and rewrites `material-span --extract` into the study read, while Seatbelt
   read-denies raw page caches, external materials, promoted summaries, and
   `LearningOS/reading-memory/` and write-denies the repository and agent
   instruction files; `study_launch.py` records `session_end` in `finally:` on
   child exit. `tools/study_hooks.py` supplies only optional UX lifecycle hooks
   (`SessionStart`, `Stop`, `SubagentStop`, `SessionEnd`), and
   `system/contracts/perimeter.yaml` declares `LearningOS/.claude` as
   `optional: true`. On `Stop`, the UX hook prompts up to twice
   (`STOP_ASKS = 2`) before marking open entries overdue without blocking turns
   indefinitely; the hard gate fires at the next uncovered study read whenever
   open debt reaches four entries or an overdue/adoptable entry exists. Inactivity
   covers ungraceful exits: a session with no gateway call for two hours (the
   default threshold; a trial world injects a shorter one for deterministic G2
   runs) is adoptable without a recorded end. Adoption is the one agent-supplied
   session: it is accepted only for a session with a recorded end and no later
   call, or no gateway call for two hours.
6. **Unreviewed, never evidence.** Served cards say `review: unreviewed` and
   `coverage_evidence: false`; concept ids are checked when a card is served and
   dangling ones are marked. A card never counts as source-coverage evidence.

## Scope of the protection claim

The isolation boundary is the Seatbelt launcher (`tools/study_launch.py`) plus
host broker (`tools/learning_os/adapters/study_broker.py`) specified in
`system/adr/ADR-022-sandboxed-study-isolation-2026-11-13.md`; optional profiles
generated by `tools/study_hooks.py profile --out DIR` supply only UX lifecycle
nudges. Installing a profile or creating the private store in the live folder is
a separate operation, not part of this decision.

## Consequences

- The private store has no Git history; versions and the log stand in for it,
  and backups are its only copy. A crash mid-append can leave a torn last line
  in `log/<session>.jsonl`; every append first truncates the file to its last
  complete line, so replay never meets a partial line.
- A study read refuses a discontiguous `--pages` selection
  (`material.study-span.discontiguous`): the returned excerpt is one combined
  text, so only a read of one contiguous range gives its entry the exact
  digest of the pages it names. Read each contiguous range separately.
- Under the profile, Markdown and notebook materials are not readable as study
  reads (cards are keyed by PDF page range).
- Obsidian's `material-span` and the manifest are unchanged, so the UI needs no
  paired release for this decision.
