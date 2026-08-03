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

## Addendum (2026-08-03, later same day) — gate lifted, v0.1 shipped

Aram lifted the Phase-D gate ("forget about M2 now, I want the whole thing
working perfectly now") — the *sequencing* note above is superseded; the exam
facts and COORDINATION priorities themselves are untouched. Shipped the same
day from `obsidian-ui/` (v0.1.0):

- **Plugin** `learningos-ui` — single-file `main.js`, no build system:
  reading room auto-opens; capture modal → `work/inbox/`; rebuild/validate/
  status via `los.py`; status-bar validation state + next-exam countdown
  (countdowns are legal UI — the determinism rule binds generated files, not
  live displays); concept-canvas command.
- **Shelves** — Obsidian Bases definitions (notes ×7 views, garden,
  workspaces), installed to `repository/bases/`.
- **Safety config** — managed keys merged into `.obsidian/app.json`:
  `alwaysUpdateLinks:false`, Markdown links, attachments→`work/inbox/`,
  local trash, archive/venv excluded from search.
- **Core side** — new generated view `concept-canvas.canvas` (JSON Canvas of
  the relation registry, prerequisite-depth layout, colored typed edges).

**Boundary clarifications (binding):** interface furniture lives in the vault
only at gitignored paths — `.obsidian/`, `/bases/`, `/.trash/` — installed
and owned by `obsidian-ui/install.py`, which never edits core-tracked files.
Direct creation of NEW files in `work/inbox/` by an interface is equivalent
to `los.py capture` and equally blessed: the inbox is the designated
judgment-free write surface (ARCHITECTURE §3.3.5); routing stays with the
operator. Everything else remains CLI-or-nothing.

## Addendum (2026-08-03, third) — custody settled, v0.3 shipped

**Custody.** `LearningOS/obsidian-ui/` is a **local-only git repository: no
GitHub remote, not folded into this repo, and outside `semestercontext`**
(whose `.gitignore` covers all of `LearningOS/`). Aram's decision. The
separation this ADR establishes is a *code* boundary, not a hosting one — it
survives without a second GitHub repo, and the interface layer is
reconstructible from the core plus a plugin folder, so it does not need
independent backup. Revisit only if the interface acquires collaborators.

**Why v0.3.** v0.2's dashboard was never seen: it auto-opened only when no
file was restored, and Obsidian always restores one, so the vault presented as
a folder of markdown — the exact failure mode the 2026-07-16 review warned
about ("an interface nobody uses is a dead second interface"). v0.3 makes the
dashboard the guaranteed, pinned home view, collapses the sidebars at launch,
and adds a Node test suite that `install.py` runs before writing anything.
Every app behaviour is a toggle in plugin settings. No boundary change: reads
still come from `los.py status --json`, `generated/`, and vault metadata; the
only write is still `work/inbox/`; the test suite now asserts that against the
plugin source.

## Addendum (2026-08-03, fourth) — the manifest is the interface contract

Aram, on v0.3: *"navigability and usability are really bad, everything is just
a dump of links … the endgoal [is] removing usability constraints from the OS
in favour of robustness and efficacy and perfecting the UI-App interface."*
Adopted as a division of labour, and it settles a question this ADR left open:

**The core may be optimised for robustness and correctness at the cost of
being pleasant to browse. All usability constraints move to the interface
layer.** Generated Markdown remains the plain-text fallback and the
non-Obsidian surface; it is no longer required to be a good browsing
experience. Correspondingly, "hard to find" is now a bug in `obsidian-ui/`,
never a reason to reshape canonical data.

That only works if the interface can see everything without re-deriving it, so
`generated/manifest.json` is promoted from "complete machine projection" to
**the interface contract**. Added this day:

- workspaces: `objective`, `next_action` (parsed core-side — the UI was
  regexing `CONTEXT.md`, which is a rule reimplementation and now forbidden)
- sources: `url`, `material`, `material_path` + `material_exists`
  (`material://` resolution through the `.flat` farm is a business rule and
  stays here), `authors`, `organization`, `year`, `identifiers`, `roles`, and
  `evaluations` incl. `useful_sections` and their `concepts`
- notes: `domain`, `summary`
- top level: `exam_spine` (same source of truth as `los.py status`) and
  review/evidence adoption in `counts` — *superseded, see the fifth addendum:
  `exam_spine` was replaced by `academic_deadlines`*

**Binding rule:** if an interface needs a fact, it comes from the manifest. If
the manifest lacks it, the fix is core-side generation, never parsing in the
UI. The interface must render fully with the CLI unavailable — the CLI is for
mutations (`generate`, `validate`, `capture`) and the validation badge only.
`obsidian-ui/tests/` asserts both halves against the plugin source.

**`materials/INDEX.html` is retired.** The 2.4 MB self-contained catalogue was
a second implementation of "how do I find a source", separately built and
separately styled. Its job — search, facets, evaluations, open online, open
the local copy — is now the Obsidian Source Explorer's, reading the manifest
fields above. `tools/build_materials_index.py` keeps the builder behind
`--html` as a fallback and now deletes a stale `INDEX.html`; `README.md` and
`FILES.txt` remain the plain-text/grep surfaces.

**Vault furniture** grows one managed file: core-plugin states
(`obsidian-ui/vault-config/core-plugins.json`, merged like `app.json`, only
named keys touched). Web Viewer on so registered URLs open in-app; Daily Notes
off because it silently creates a second inbox against ARCHITECTURE §3.3.5;
the link graph off because it shows file links rather than the relation
registry — a competing graph, which the anti-goals forbid.

## Addendum (2026-08-03, fifth) — one fact, one shape in the contract

A review of the shipped app found the manifest carrying two keys with no live
consumer, both duplicating something it already published. The contract now
states the rule that was only implicit: **where a projection could be expressed
two ways, the manifest carries exactly one.** An index beside an ordered list is
not a duplicate; a second shape for the same access path is.

**`exam_spine` is retired from `generated/manifest.json`.** It listed only
attempts with `result: registered` — a strict subset of `academic_deadlines`,
in a different shape, carrying a third copy of `examination.notes`. Interfaces
read `academic_deadlines`, which additionally covers available sittings that
have no attempt yet and grouped registration windows.

`_exam_spine()` survives as the internal helper behind the "Exam spine" table in
`coordination-view.md` / `reading-room.md` and behind `los.py status --json`.
The CLI status payload keeps its `exam_spine` field: it is a separate surface
with its own consumers and its own test (`tests/test_cli.py`), and it answers a
narrower question — *what am I actually registered for* — that the helper models
exactly. Retiring a manifest key is not retiring the concept.

**`stages` becomes a declared index, not spare data.** The flat array (every
stage with `study_map_id`, `unit_id`, `module_id` added) exists so an interface
can resolve a stage from an ID alone without walking `study_maps`. The nested
`study_maps[].stages` remains the ordering authority — a rail needs the ordered
list. The UI now uses each for its own job.

**New structured examination facts.** `examination.sittings` and
`examination.registration_windows` (schema'd, validated for duplicates and
inverted ranges) let the core project dates that exist *before* an attempt does.
Correlating a sitting with an attempt to derive `registration_state` is a
business rule and lives in `_academic_deadlines()`, never in an interface.
Their restatement in `examination.notes` was trimmed the same day: prose keeps
only what the structured fields cannot hold — verification provenance, plan of
record, and institutional logistics.

**Versioning note.** `contract_version` stays `2`. The two layers ship together
in one review, there is exactly one consumer of the manifest, and it was updated
in the same pass; a bump would signal a compatibility story that does not exist
here. The next removal that lands *without* a matching UI change must bump.
