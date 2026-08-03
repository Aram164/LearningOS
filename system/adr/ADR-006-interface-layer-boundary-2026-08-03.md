# ADR-006 — Interface layer boundary (core kernel vs. Obsidian desktop)

**Status:** accepted 2026-08-03 (Aram: "obsidian is supposed to be like the
hardware utilizing LearningOS in a user-friendly way … tracked by a different
project than this one … LearningOS is purely robustness and architecture and
the obsidian structure is the user's interface").
**Context:** Aram's plan document *LearningOS-Obsidian-Architecture.md*
(2026-08-03) proposes Obsidian as the human desktop over LearningOS. The
operator's review of it against the v3 contract found: the kernel/interface
split is sound; the schema work it proposes already exists (note fields
`reviewed`/`state`/`evidence`, source-evaluation `roles`); its CLI and
reading-room ideas are cheap and valuable in-core; its plugin work is a
separate software project that COORDINATION's exam priorities exclude before
the M2 Klausur. This ADR fixes the boundary so both layers can evolve
independently. Input doc filed with the UI project
(`LearningOS/obsidian-ui/inputs/`).

## Decision — two layers, one contract

**LearningOS core (this repository)** owns canonical data, schemas,
validation, business rules, generated views, and the machine gateway. It is
purely robustness and architecture. It contains no interface code, ever.

**Interface layers** (first: the Obsidian UI, `LearningOS/obsidian-ui/`, its
own repository and its own Claude project) own presentation and interaction
only. Their tracking, improvement, and success criteria live in their own
project, not here.

**The contract surface** — everything an interface may touch:

1. `python tools/los.py` — `status --json` · `validate` · `generate` ·
   `capture`. The CLI *delegates* to the canonical tools; there is exactly one
   implementation of every rule. `capture` is the single write command because
   it is judgment-free (bytes into `work/inbox/`; routing stays with the
   operator per CLAUDE.md §3–§5).
2. `generated/` views, read-only — entry point `generated/reading-room.md`
   (the human home page, new in this ADR); complete machine projection
   `generated/manifest.json`.

Nothing else. No parsing-and-rewriting of YAML registries, no direct writes to
canonical files, no reimplementation of validation in another language.

## Boundary rules

**Core-side (enforced here):**

- No plugin source, `node_modules`, build systems, or app workspace state in
  this repository; `.obsidian/` is gitignored (a locally *installed* compiled
  plugin under `.obsidian/plugins/` is untracked by construction).
- Notes remain editor-agnostic Markdown: no Obsidian-only meaning, no
  required wikilinks (verbatim-preservation and plain-file invariants
  unchanged, ARCHITECTURE §16.15, §17).
- `ARCHITECTURE.md` §3.1 amended: interface layers are `LearningOS/` siblings
  outside `repository/`.

**UI-side (recorded here, enforced there — the UI project's contract must
restate them):**

- Develop against a fixture vault, never the live repository.
- All mutations go through the CLI; generated files are treated as disposable;
  never rename, move, or rewrite canonical notes or registries.
- Safety configuration ships with the UI project's installer, since
  `.obsidian/` is untracked here: link auto-update OFF (renames would fight
  the filename-= -ID rule), no drag-in attachments, `generated/` and
  `archive/` excluded from recency surfaces (they churn on every commit).
- Installation into the live vault requires explicit confirmation.

## Relationship to prior decisions

- **Supersedes (narrows) human-operability review #13** ("read-only vault —
  default: don't"): the core now defines a *socket*; whether and when a vault
  plugs in is the UI project's decision. The external review's (2026-07-16)
  dead-interface diagnosis stands as that project's failure mode: an interface
  nobody uses gets deleted, not maintained.
- **ARCHITECTURE §17 unchanged:** no dependence on Obsidian. The repository
  must remain fully operable with a text editor, Git, and the four `make`
  words.
- **COORDINATION priorities unchanged:** UI-project build work starts Phase D
  (after the M2 Klausur) at the earliest. Nothing about this ADR allocates
  study-phase time to plugin development.

## Rejected now (from the plan document)

- **Zotero as PDF custodian** — `materials/` (source-owned folders,
  `material://` URIs, PLACEMENT map) stays the single custodian; dual homes
  are the drift disease. A `zotero_key` identifier on source records is
  acceptable later if a bibliographic need appears.
- **Source-perspective schema change** — the evaluation `roles` vocabulary
  already carries it; extend the vocabulary, not the schema.
- **New review/evidence subsystem** — the note fields exist; the gap is
  adoption, now surfaced in `reports/health.md` (adopt on touch, never bulk).
- **QMD retrieval** — deferred until a real retrieval gap appears; if
  adopted: cache-only, gitignored, excluding `Job/`, `legacy/`, `archive/`,
  `generated/`, `.obsidian/`.

## Implementation log (2026-08-03, this session)

- `tools/los.py` CLI (status/--json, validate, generate, capture) + `make
  status` + README gateway note + tests.
- `generated/reading-room.md` builder (composes coordination view, nebula,
  health, recent notes, queues; Git-dated, deterministic, no countdowns) —
  whitelisted in `GENERATED_ALLOWED`, listed in WORKFLOWS §12.
- Health report: "Review & evidence adoption" section (reviewed/evidence
  counts, changed-since-review, state distribution).
- `.gitignore`: `.obsidian/`. ARCHITECTURE §2.5 + §3.1 amendments.
- `LearningOS/obsidian-ui/` seeded: README + boundary CLAUDE.md + the input
  plan under `inputs/` — a stub for the separate project, deliberately not a
  Git repository yet (that is the UI project's first act).
