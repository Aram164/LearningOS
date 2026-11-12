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
   span that no current card or settled dismissal of the same digest contains
   (page containment). If the entry cannot be persisted, the read refuses. A
   session may hold four open entries; a new uncovered span refuses while the
   session holds an overdue entry or any ended or idle session's entries are
   adoptable. Pending spans, covered spans, search, context, settlement and
   adoption always stay available, and every refusal names the entries and the
   exact settle or adopt command. A clipped, truncated or non-PDF extraction
   returns no text and opens nothing.
5. **Session identity comes from the harness.** `tools/study_hooks.py` runs as
   the study profile's Claude Code hooks. `PreToolUse` injects `--session` from
   its own input, refuses an agent-supplied session, rewrites `material-span
   --extract` into the study read, keeps Bash to an allowlist and keeps file tools
   out of every tree that holds raw page text or the store. `Stop` asks twice,
   then marks the turn's open entries overdue and records the end. Adoption is
   the one agent-supplied session: it is accepted only for a session with a
   recorded end or no gateway call for two hours.
6. **Unreviewed, never evidence.** Served cards say `review: unreviewed` and
   `coverage_evidence: false`; concept ids are checked when a card is served and
   dangling ones are marked. A card never counts as source-coverage evidence.

## Scope of the protection claim

The claim covers a study profile installed as `LearningOS/.claude/settings.json`,
for the tools and invocation forms its tests exercise. A session started
anywhere else gets no capture. Installing a profile or creating the store in the
live folder is a separate operation, not part of this decision.

## Consequences

- The private store has no Git history; versions and the log stand in for it,
  and backups are its only copy.
- Under the profile, Markdown and notebook materials are not readable as study
  reads (cards are keyed by PDF page range).
- Obsidian's `material-span` and the manifest are unchanged, so the UI needs no
  paired release for this decision.
