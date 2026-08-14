---
name: promotion-ritual
description: Harvest the Garden — walk every idea in knowledge/garden/, promote the ripe ones into canonical notes, prune the dead, and let the rest gestate. Use when asked to "harvest the Garden", "run the promotion ritual", promote a specific garden note, or as step 2 of turning the semester.
---

# Promotion Ritual — Harvest the Garden (Learning OS v3)

Implements the **Harvest the Garden** routine in `system/CLAUDE.md` §14, with
`system/WORKFLOWS.md` §3 (create or evolve a note), §4–§6a (register concepts,
relations, sources) and §15 (deprecate or supersede) as the atomic steps. Read
§14 before running it; the six-step routine lives there and is not restated
here.

Promotion is deliberately **not** a `los` command — `tools/los.py` excludes it
by design as operator judgment. That judgment is this skill's whole content.

## The call to make, per garden note

The Garden (`knowledge/garden/`) is a nursery, not an attic. Every file gets one
of three honest verdicts:

- **Promote** — the idea has a coherent independent purpose. Prefer evolving an
  existing note where it already has a home (§8); create a new canonical note
  only when it stands on its own.
- **Keep gestating** — real, not ready. It stays, and it stays *named* in the
  harvest summary so it does not quietly rot.
- **Prune** — it was never canonical, so deletion needs no heavyweight approval,
  but always name which notes you are removing before removing them.

`generated/nebula.md` (rebuilt by `make views`) is the only lens on the Garden:
garden notes grouped by tag, annotated with harvest pressure — uncommitted and
oldest-touched first. Read it first; it is a disposable view, so never edit it.

## Hard constraints

**Promotion is a visible-review change** (CLAUDE.md §4): it assigns a role and
creates a canonical note. Propose full frontmatter (id, title, role, concepts,
sources, state) and the target `knowledge/notes/<domain>/` path, then get
approval per note or per batch before moving anything.

**The wording is Aram's.** Preserve it verbatim (§3, §6) — promotion adds
frontmatter and a home, never a rewrite, a polish, or a tidier conclusion.

**Register only what is genuinely new** (§4 concepts with German aliases, §5
relations, §6a sources). Wire on use; never bulk-backfill.

**Finish the loop.** `python tools/validate.py` to 0 errors, 0 warnings, then
`python tools/generate.py`. A promoted note now participates in the canon and
its garden file is gone from the working tree — its history stays in Git.

## Quality bar

Never promote to look productive: a thin note admitted to the canon costs more
than an idea left to mature. Never declare mastery — a promoted note carries
evidence trails or their documented absence. The tiebreaker is unchanged:
reduce organizational burden rather than create it.
