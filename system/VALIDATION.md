# Learning OS v3 — Validation Rules (Consolidated v3.1)

Structure is validated by `system/schema/*.schema.json` (canonical structural contracts). This file defines the **cross-file semantic rules** that JSON Schema cannot express. `tools/validate.py` enforces both. Severity: **E** = error (blocks acceptance), **W** = warning.

## What a passing run means

**Zero errors.** Warnings are visible and never block: `tools/validate.py`
exits 0 while reporting them, and the pre-commit hook is written to let them
through. That is deliberate — the warnings carried today are the measured
content debt of CRITIQUE-POINTS §1 (vague locators, missing angle detail), and
backfilling them is a decision Aram has deferred, not an oversight.

Deferring them cost the ability to tell a deferred warning from a new one.
`operations/validation-warning-baseline.yaml` restores it: every warning
signature — **(code, path) with its multiplicity** — is recorded, and
`python tools/warning_baseline.py --check` fails on a new signature or a grown
one. A signature rather than a total, because a total is gamed by trading one
warning for another.

Two exact, named sets are excluded from the baseline — `BASELINE_EXEMPT_WARNINGS`
in `learning_os.rules.common`, never a prefix, severity band, or path heuristic:

- **Environmental** (`ENVIRONMENTAL_WARNINGS`: `MATERIALS-OFFLINE`,
  `HYGIENE-VIEWS`, `HYGIENE-LOCK`, and the rest) describe the machine, not the
  content, and differ between one checkout and the next.
- **Dynamic advisory** (`DYNAMIC_ADVISORY_WARNINGS`: `WS-NEGLECT`,
  `INBOX-STALE`) are clock-derived: they can newly appear with no authored file
  changed, purely because days elapsed.

Both categories remain fully visible in normal `validate.py` output and normal
health reporting — exemption applies only to the baseline gate's regression
check. Every other warning code, including one not yet invented, is
baseline-managed by default: a new or grown signature fails
`warning_baseline.py --check` regardless of how sympathetic the cause. A
baseline-managed signature that *shrinks* is reported as a repair and passes;
it is never restored merely to match a prior total.

Adopting a new baseline is an explicit act with a stated reason
(`--update --note "…"`). An unexplained move is indistinguishable from a
silent regression.

## The normative corpus

- **E** `NORMATIVE-CORPUS-MISSING` — a `system/*.md` or `system/adr/*.md` file
  that `system/contracts/normative-corpus.yaml` does not classify.
- **E** `NORMATIVE-CORPUS-ORPHAN` — an index entry naming a file that does not exist.
- **E** `NORMATIVE-CORPUS-DUPLICATE` — one path indexed twice.
- **E** `NORMATIVE-CORPUS-EDGE` — a `supersedes`/`amends` edge to an unindexed path.
- **E** `NORMATIVE-CORPUS-CYCLE` — a supersession cycle; no rule in it resolves as current.
- **E** `NORMATIVE-CORPUS-STATUS` — retired by an edge but still `current`, or
  `superseded` with nothing superseding it.
- **E** `NORMATIVE-CORPUS-AUTHORITY` — a retired or frozen document still `binding`.
- **E** `NORMATIVE-CORPUS-NO-NOTICE` — a retired document whose own text never
  names what retired it. An agent that opens the file directly never sees the
  index, so the notice has to be in the document.
- **E** `NORMATIVE-CORPUS-ENTRYPOINT` — the declared entry point is missing,
  retired, or not binding.
- **E** `NORMATIVE-CORPUS-UNREADABLE` — the index or its schema cannot be read.

Errors rather than warnings: the failure mode is an agent reading a retired
rule as current, which is indistinguishable from the rule being wrong.

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
- **E** No cycle among `requires` / `builds-on` edges. Semantic relation types may cycle; only the strict subgraph defines learning order.
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
- **E** Only `curriculum/quarantine/index.yaml` is normally loaded from the
  Future Master's Planning boundary; its prospective content is absent from
  records, counts, indexes and generated manifest text. Job learning has no
  carve-out: `program-job` modules validate and project like every other module.
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

## Runtime review (§19.6, first slice)

A stage carrying runtime semantics (`runtime_target`, or any resource with an
`affordance`) must carry a `runtime_review` attestation naming the declared
reviewer and a fingerprint over the reviewed payload (`runtime-review-v1` +
stage id + `runtime_target` + sorted `(route_id, affordance)` pairs).

- **W** `RUNTIME-REVIEW-MISSING` — runtime semantics present, no attestation.
- **W** `RUNTIME-REVIEW-STALE` — the payload no longer matches the fingerprint;
  re-review and refresh it.

Warnings, never errors: the invariant is being introduced into existing
authored state. `reviewed_by` is a declared attestation, not authenticated
proof — the transaction history proves when the metadata was written, not the
cognitive act of review. Review provenance is not pedagogical validity: a
current attestation says the payload was reviewed and is unchanged, never that
the underlying activity validly elicits the claimed evidence.

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

Every hygiene finding *about the repository's contents* is **W** — they announce
mess the moment it exists so it never accumulates into an audit session; they
nag, never block. The exception is `GIT-HISTORY`, which is not a finding about
the contents but a statement that a check could not be made at all.

- **E** `GIT-HISTORY` — Git history could not be read, so a check that depends
  on it (`HYGIENE-VIEWS`, `WS-NEGLECT`) reached no conclusion. Raised by
  `learning_os.githistory`, which distinguishes a tree that genuinely has no
  history — an export, an unborn branch, an empty repository — from a Git that
  failed to answer. The first is still an ordinary empty result; only the second
  is this error. It is an error rather than a warning because the alternative is
  reporting a clean repository on the strength of a question nobody answered,
  and it is deliberately **not** in `DYNAMIC_ADVISORY_WARNINGS`: `WS-NEGLECT` is
  exempt from the warning baseline because it moves with the clock, and a failed
  read must never inherit that exemption.
- **W** `HYGIENE-LOCK` — a `.git/index.lock` older than 10 minutes (repository
  or container repo): a crashed git process is silently blocking all commits.
- **W** `HYGIENE-VIEWS` — `generated/manifest.json` absent or older than the
  last commit: the post-commit rebuild did not run (`make views`).
- **W** `HYGIENE-UNFILED` — a loose `.md` outside the legal drop zones
  (repository root beyond README/CLAUDE, `knowledge/` root, bucket-less
  `knowledge/notes/`, `work/` root beyond COORDINATION, `records/`/`sources/`,
  a workspace root beside CONTEXT.md). `work/inbox/`, workspace subfolders and
  the Garden are exempt by design.

Legacy and sibling code repositories are not hygiene roots. Legacy verification
is available only through the deliberate, exact-allowlist
`legacy.archive.inspect` workflow. External worktrees such as Stratum sit
outside LearningOS's canonical roots and are never traversed by validation.

## Generated outputs

- **E** `generated/` contains only the defined deterministic outputs; agent-computed artifacts (plans, source menus, summaries, recommendations) live in workspaces, never in `generated/`.
- **E** Regeneration after deleting `generated/` reproduces byte-identical outputs except timestamp fields.
- **E** Every generated file carries a generated-file warning header.
- **E** Manifest covers every canonical record; index entries resolve; backlinks equal the inverse of canonical forward references.

## Transaction and Project validation

Validation checks first-class Project records, project aliases, project
relationships, capability contracts, and append-only transaction receipts.
A project relationship must resolve to a supported projected target. A
transaction receipt must conform to readable Receipt v1 or authoritative
Receipt v2 and have a unique ID.
The revision ledger is operational metadata and is not interpreted as a
receipt.
