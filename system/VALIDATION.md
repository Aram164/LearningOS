# Learning OS v3 — Validation Rules (Consolidated v3.1)

Structure is validated by `system/schema/*.schema.json` (canonical structural contracts). This file defines the **cross-file semantic rules** that JSON Schema cannot express. `tools/validate.py` enforces both. Severity: **E** = error (blocks acceptance), **W** = warning.

## Identity

- **E** IDs unique within each family (note, concept, source, workspace,
  program, module, component, unit, study map, stage, detour).
- **E** Every ID matches its entity-family prefix and lowercase kebab-case
  contract; component, unit, map, stage and detour references resolve.
- **E** An ID never changes when its file moves or is renamed.
- **W** Numeric suffix present without a collision counterpart (gratuitous suffix).

## References

- **E** Every note `concepts` entry resolves in the concept registry.
- **E** Every note `sources` entry resolves in the source registry.
- **E** Every relation `from`/`to` resolves; endpoints are distinct.
- **E** Every `supersedes` / `replaced_by` target resolves.
- **E** Workspace IDs cited in COORDINATION.md dependencies resolve to active workspaces.
- **E** Evidence refs use a valid URI scheme (`note://`, `source://`, `concept://`, `workspace://`, `material://`, `project://`, `github://`, or https URL).
- **W** `material://` or `project://` URI does not resolve on disk (reported, not fatal — media may be offline).

## Registries

- **E** No duplicate relation edges (same from/type/to).
- **E** Relation `type` is one of the eight supported types (no `related-to`).
- **W** Alias collision: one alias maps to multiple concepts.
- **W** Two source records share title+author or identical URL/identifier (duplicate candidates).
- **E** Concept records contain no body/explanation fields beyond short description.
- **E** Every `sources/collections/*.yaml` file validates against `collections.schema.json`; filename is kebab-case; every entry's `source` resolves to a registered source.
- **E** Every thematic-group reference on a module, source or collection resolves in `curriculum/thematic-groups.yaml`.
- **E** Every `topic-pack` collection has one explicit non-empty `purpose`; file order remains its manual item order.
- **W** A source is listed more than once within the same collection.

## Ownership boundaries

- **E** No canonical file references anything under `generated/` as an input.
- **E** No file under `generated/` is tracked by Git.
- **E** COORDINATION.md contains no ISO date equal to any partitioned academic
  module attempt date (exam-date duplication), and no `status:` restatements of
  workspace state.
- **W** A `role: crosswalk` note contains Markdown tables whose headers match evaluation vocabulary (strengths/weaknesses/level/best-for) — judgments belong in source records.
- **E** Academic module attempt dates are chronologically ordered per module;
  `grade` only on `passed` attempts or completed modules; `result: registered`
  only on the latest attempt. Academic-only fields are not required on skill,
  project, or foundation modules.

## Curriculum v2

- **E** Exactly one program is the active default Bachelor's program; Skills
  and Thesis/Projects are non-semester active areas.
- **E** Partitioned module records are complete against the frozen legacy
  registry during migration; once a partition exists, it is authoritative.
- **E** Every module's `unit_order` contains all and only its units, once each,
  and agrees with the numeric `order` on those units.
- **E** Every component ID is stable and owned by the same module as its units.
- **E** Every unit has one owning module, a valid kind/status, resolvable scope
  sources and artifacts, and at most one current study map.
- **E** Every current map points back to its unit/module, has ordered unique
  stages, and names exactly one current active/paused stage when operational.
- **E** Stage working notes and attachments remain inside the owning unit's
  stage folder. Source actions use registered source IDs and exact locators
  where selection is required.
- **E** Detours name an originating stage, classification, and return stage;
  open required-now detours pause their origin rather than silently replacing
  it.
- **E** Module source maps use global source IDs, declared roles, valid unit
  routes, and do not duplicate global evaluations.
- **E** V2 workspaces declare `program_ids`, `module_ids`, and `unit_ids`;
  relationships are not inferred from titles or prose.
- **E** The resume pointer, if present, resolves to one map/unit/stage but has
  no filtering semantics.
- **E** Only `curriculum/quarantine/index.yaml` is normally loaded. Master's
  content and all Job content are absent from records, counts, indexes and
  generated manifest text.
- **E** Shelving apply accepts explicit existing proposal IDs and approved
  destinations only. General AI has no write capability.
- **E** Session closure stages only its temporary action ledger and always
  excludes every `.canvas` file, regardless of the default name Obsidian assigns.

## Plan rigour (CRITIQUE-POINTS 1, 2026-08-24)

A plan can satisfy every rule above and still not tell you where to start or why
this source rather than that one. These checks are about the *content* of a
route, and the definitions they enforce are in `PLAN-CREATION-SOP.md`.

- **E** `LOCATOR-ANGLE-FUSED` — no locator carries the angle appended after an
  em dash. The angle is a field (`angle`); the fused form was the pre-2026-08-24
  representation and must not return. Detected as a sentence-shaped tail
  carrying no page, section or file reference, so a legitimately titled locator
  (`Lecture 2 — Linear Regression`) does not trip it.
- **W** `LOCATOR-VAGUE` — a book or paper route names a chapter but no page
  range; or a route of any format hedges ("selections", "topic-matched",
  "relevant") instead of naming the material.
- **W** `ROUTE-ANGLE-MISSING` — a rich route declares no `angle`.
- **W** `ROUTE-ANGLE-DETAIL-MISSING` — a route has a one-line `angle` but no
  `angle_detail` for the hover.
- **W** `ROUTE-NO-TARGET` — a route names no `locator`, `url` or `vault_path`.

These are warnings and not errors on purpose. The backfill is incremental
(WORKFLOWS §6a repays visibility debt on use, never in bulk), and a rule that
blocked every commit until 2,268 rows were rewritten would be switched off
rather than satisfied. The counts are the point: they are the measured size of
the debt, reported in `generated/study-plans.md`.

## Operating contract

- The operating contract is a single canonical file, `system/CLAUDE.md`. Root `CLAUDE.md` and the `LearningOS/` project-root entry are symlinks to it, so the copies cannot drift — the former hand-maintained `CLAUDE-SYNC` warning is retired (2026-07-17).
- **E** Living operator instructions never copy the current data or manifest
  contract number. They point to the producer-owned declaration, while dated
  ADRs and contract history remain free to name historical versions.

## Files

- **E** A note's filename equals `<id>.md`; a mismatch between filename and frontmatter ID is an error.
- **E** Every `attachments` entry resolves to a file under `knowledge/attachments/<note-id>/`.
- **W** A folder under `knowledge/attachments/` has no owning note referencing it (orphaned attachments).
- **W** Binary files under `knowledge/` outside `attachments/` (books/slides belong in materials).
- **W** Items in `work/inbox/` older than 14 days (unrouted capture — the inbox should trend toward empty).

## Workspaces

- **E** Required body sections present (Objective, Current Scope, Open Questions, Next Action).
- **E** Archived workspaces are excluded from generated concept/source indexes.
- **W** More than 7 non-standing active workspaces.
- **W** Active non-standing workspace untouched (per Git) for 21+ days (neglect signal — surfaced in the coordination view).

## Links

- **E** Internal Markdown links (relative paths, `note://` etc.) resolve.
- Online-only (`--online` flag): **E** external URL unreachable after HEAD and bounded-GET checks.
- Online-only (`--online` flag): **W** external URL is access-controlled (`401`, `403`, or `429`) and cannot be verified automatically.

External checks never slow or block ordinary offline validation. The deliberate
online gate blocks confirmed link rot while keeping authentication and rate
limits advisory.

## Hygiene sweep (ADR-004, 2026-08-03)

All hygiene findings are **W** — they announce mess the moment it exists so it
never accumulates into an audit session; they nag, never block.

- **W** `HYGIENE-LOCK` — a `.git/index.lock` older than 10 minutes (repository
  or container repo): a crashed git process is silently blocking all commits.
- **W** `HYGIENE-VIEWS` — `generated/manifest.json` absent or older than the
  last commit: the post-commit rebuild did not run (`make views`).
- **W** `HYGIENE-UNFILED` — a loose `.md` outside the legal drop zones
  (repository root beyond README/CLAUDE, `knowledge/` root, bucket-less
  `knowledge/notes/`, `work/` root beyond COORDINATION, `records/`/`sources/`,
  a workspace root beside CONTEXT.md). `work/inbox/`, workspace subfolders and
  the Garden are exempt by design.
- **W** `HYGIENE-SHADOW` — a same-named `.md` under a shadow root
  (`legacy/Plans/`, `Job/workspace-job-deem/inputs/`) modified *after* the
  canonical note: live drift into a frozen copy. Filename + mtime comparison
  only — content is never read (narrow §13 carve-out, ADR-004).

## Generated outputs

- **E** `generated/` contains only the defined deterministic outputs; agent-computed artifacts (plans, source menus, summaries, recommendations) live in workspaces, never in `generated/`.
- **E** Regeneration after deleting `generated/` reproduces byte-identical outputs except timestamp fields.
- **E** Every generated file carries a generated-file warning header.
- **E** Manifest covers every canonical record; index entries resolve; backlinks equal the inverse of canonical forward references.

## Transaction and Project validation

Validation checks first-class Project records, project aliases, project
relationships, capability contracts, and append-only transaction receipts.
A project relationship must resolve to a supported projected target. A
transaction receipt must conform to schema version 1 and have a unique ID.
The revision ledger is operational metadata and is not interpreted as a
receipt.
