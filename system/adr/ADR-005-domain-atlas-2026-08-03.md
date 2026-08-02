# ADR-005 — Domain atlas: cross-domain reach without new canon (2026-08-03)

**Status:** accepted · **Context:** Aram reported that the operator's scope
feels *confined*: standing in one module's workspace, Claude rarely surfaces
sources or notes from other domains, even though the repository holds 228
registered sources across 17 curated shelves. He asked whether the layers
(v3 domains, legacy tree, Masters-Planning remnants, materials topic tree)
could be standardized for perfect navigability — without bloating the system.

## Diagnosis (survey of 2026-08-03)

The architecture was not the problem — concepts already join notes and
contextual source evaluations across domains (the concept-index entry for
*gradient descent* pulls math, ML, and drill sources together). Three real
gaps produced the confinement:

1. **Uneven wiring depth.** ML/Math are densely concept-wired; programming,
   systems, algorithms, data-systems barely. Measured at adoption: 205/228
   sources sit on a shelf, but only **82/228 carry a concept-linked
   evaluation** — the join concept retrieval actually uses. An unwired source
   is invisible no matter how good it is.
2. **No small global map in the bootstrap.** Session start read coordination +
   modules + workspace; nothing ever put the other domains' shelves in view.
   The big indexes (concept-index ~2,100 lines) are grep targets, not maps.
3. **Deliberately excluded strata were unmapped.** The Foundations archive
   (234 unregistered files), the ~200 prospective degree-menu rows, and the
   frozen legacy tree are *correctly* outside retrieval — but no file the
   operator reads even named them, so their existence could never be offered.

## Decision

Four moves, chosen from explicit alternatives (option labels from the design
discussion); **no new canonical entity, no schema change, no legacy rework**:

1. **(1C)** A generated view `generated/domain-atlas.md` — per domain: note
   counts by role, crosswalk hubs, shelves with entry counts and their
   *canonical* `description:` fields (harvested, never authored in the view),
   plus a "deliberately excluded strata" section with live counts. Built by
   `tools/learning_os/genout.py::build_domain_atlas`; the shelf→domain map is
   view-level presentation (same pattern as the materials indexer), with a
   `cross-domain` fallback so new shelves are never dropped.
2. **(2D)** Hybrid bootstrap: the atlas opens with an **At a glance** block
   (~15 lines) read at every session start (CLAUDE.md §2 item 8); the full
   atlas is opened on trigger — source/learning-path questions, or no concept
   match (CLAUDE.md §7 "Cross-domain reach").
3. **(3C)** Wiring debt is measured in `generated/reports/health.md` (not the
   atlas): evaluations / concept-wired / shelf / note-referenced counts and
   the "least visible" list grouped by registry file. Debt is repaid **on
   use** — WORKFLOWS §6a "wire on use": minimal stub = concepts + roles + one
   strengths line. Bulk backfill is explicitly rejected (it invents
   judgments; stage2b deferred evaluations deliberately).
4. **(4C)** `materials/FILES.txt` (emitted by `make materials`): names-only,
   grep-able listing of every *unregistered* file, so "do I own something on
   X?" is answerable without registering 234 archive files. Registered
   sources are deliberately absent; promotion stays WORKFLOWS §6a.

## Alternatives rejected

- **Hand-authored DOMAINS.md** — the v2 drift disease: a manually maintained
  dashboard restating facts owned elsewhere; it would rot.
- **Bulk-registering the Foundations archive** — 234 unevaluated records
  polluting a registry defined as *evaluated teaching objects*.
- **Restructuring or retro-standardizing legacy / Masters-Planning** — frozen
  history stays frozen; it is now *mapped* (one atlas line each), not migrated.
- **Wiring-debt counts in the atlas itself** — nags every session and invites
  a completion game; a signal belongs with the other maintenance signals.

## Consequences

- Every session starts with the whole map in view for ~15 lines of context;
  cross-domain mentions become contractual (§7), not accidental.
- The canonical surface is unchanged: same four knowledge families, same
  schemas, same workflows. Everything added is disposable and regenerable.
- The 82/228 concept-wiring number gives "confined scope" a measurable,
  passively shrinking definition — no backlog, no bulk project.
- Touched: `tools/learning_os/genout.py`, `tools/build_materials_index.py`,
  `system/CLAUDE.md` §2+§7, `system/WORKFLOWS.md` §6a, `system/ARCHITECTURE.md`
  §2.5, `README.md`. Tests cover the new outputs in `tests/test_generation.py`.
