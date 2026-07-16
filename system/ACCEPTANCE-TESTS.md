# Learning OS v3 — Acceptance Tests (Consolidated v3.1)

The rebuild is complete only when every critical test passes or is explicitly waived with a documented reason.

## A. Structure

- [ ] Target directory tree exists, including `records/`, `knowledge/attachments/`, and `system/schema/`.
- [ ] Spec files are present under `system/`, headed by `PHILOSOPHY.md`; JSON Schemas under `system/schema/`.
- [ ] Note filenames equal their frontmatter IDs (`<note-id>.md`).
- [ ] `generated/` is gitignored and isolated.
- [ ] Materials root and projects root are documented.
- [ ] Dependency trees and virtual environments are outside the authored knowledge search space.

## B. Canonical ownership

- [ ] Every canonical information category has exactly one owner.
- [ ] Notes own note-to-concept and note-to-source links.
- [ ] Concept registry owns identities and aliases; relation registry contains only concept-to-concept edges.
- [ ] Source registry owns source identity and evaluations.
- [ ] `records/modules.yaml` owns all module facts; **no exam date, registration, withdrawal, or grade appears canonically anywhere else** (grep-testable against COORDINATION.md and notes frontmatter).
- [ ] `COORDINATION.md` contains only commitments, explicit priorities, cross-workspace dependencies, and deferrals — no workspace lists, statuses, or computed recommendations.
- [ ] Workspaces own active operational state.
- [ ] No generated file is used as a canonical input.

## C. IDs and references

- [ ] IDs are unique within each family (notes, concepts, sources, workspaces, modules) and conform to the pattern with family prefix.
- [ ] Numeric suffixes are collision-only; gratuitous suffixes are flagged.
- [ ] Moving a note does not change its ID.
- [ ] Every note concept/source reference resolves; every relation endpoint resolves.
- [ ] Every evidence reference is syntactically valid.
- [ ] Every material URI is either resolvable or reported.
- [ ] Dependencies in COORDINATION.md reference resolvable workspace IDs.

## D. Notes

- [ ] User-authored prose is preserved; no note was silently semantically rewritten.
- [ ] Rough but durable notes are allowed; scratch is not auto-canonicalized.
- [ ] `role` values conform to the vocabulary; default is `synthesis`.
- [ ] Exercise banks and mock exams are durable notes retrievable by role + concept.
- [ ] Crosswalk notes carry narrative only; judgment tables are flagged (warning).
- [ ] Handwritten originals live under `knowledge/attachments/<note-id>/`, Git-tracked, referenced from the owning note's frontmatter.
- [ ] Notes may reference multiple concepts and sources; folder placement is not required for retrieval.
- [ ] No mandatory `updated` field exists.

## E. Concepts

- [ ] Concepts contain identities and aliases, not explanations.
- [ ] Labels are English; German terms resolve as aliases.
- [ ] Alias collisions are reported.
- [ ] Deprecated concepts remain resolvable.

## F. Sources

- [ ] Duplicate source identities are reconciled or reported.
- [ ] Contextual evaluations are preserved and may target specific concepts.
- [ ] Source materials remain externally referenced.
- [ ] Registry can be partitioned without semantic changes.

## G. Workspaces and coordination

- [ ] Active workspace scaffolds validate; required body sections present.
- [ ] Standing workspaces validate and are exempt from archival expectations.
- [ ] Active workspace count 8+ produces a warning.
- [ ] Completed workspaces archive whole; archived workspaces are excluded from normal indexes.
- [ ] Durable outputs remain under `knowledge/`.

## H. Modules

- [ ] `modules.yaml` validates against its schema.
- [ ] An attempt sequence of registered → withdrawn → registered (2. Termin) is representable and renders correctly in the module view.
- [ ] A Kombimodul (one grade, multiple components) is representable.
- [ ] Module views are generated, never hand-maintained.

## I. Generated artifacts

- [ ] Deleting `generated/` removes no canonical knowledge; one documented command rebuilds everything.
- [ ] Repeated generation is deterministic except timestamps.
- [ ] Generated files contain a generated warning and are gitignored.
- [ ] `generated/` contains only deterministic outputs; agent-computed artifacts live in workspaces.
- [ ] Manifest includes every canonical artifact; indexes resolve every listed record.
- [ ] Backlinks match canonical forward references.
- [ ] The source index reproduces per-lecture and per-concept selector views with first-learning / review / implementation recommendations.
- [ ] The coordination view merges modules.yaml exam spine + workspace frontmatter + COORDINATION facts + Git-derived neglect signals.
- [ ] Validation report distinguishes errors from warnings.

## J. Migration

- [ ] Original repository is backed up; every legacy authored file appears in the inventory with an old-to-new mapping or documented exclusion.
- [ ] The pilot included the AML–SaD Master Wiring and was reviewed before Stage 2.
- [ ] Handwritten originals are preserved.
- [ ] SESSION-LOG and operational files were checked for hidden durable knowledge.
- [ ] Module facts (attempts, Rücktritte, grades) were extracted into modules.yaml.
- [ ] Old concept-index depth glyphs were not treated as canonical proof.
- [ ] Legacy wiring was not copied blindly into the relation registry.
- [ ] Crosswalk judgments were extracted to source records; generated selector views verified against originals.
- [ ] External materials and code projects are separated or explicitly exempted; no active project was broken.
- [ ] Legacy validators are retired; final migration report exists.

## K. Claude behavior

- [ ] Root `CLAUDE.md` reflects the frozen operating contract; Claude bootstraps without the legacy architecture.
- [ ] Claude retrieves a concept through aliases (including German).
- [ ] Claude retrieves notes, sources, and relations together; filters exam artifacts by role.
- [ ] Claude answers exam-date questions from `modules.yaml` and refuses to duplicate the fact elsewhere.
- [ ] Claude answers "have I worked through this?" by showing evidence entries, never by declaring mastery.
- [ ] Claude proposes required-now/helpful-now/defer/reference-only triage on scope explosion and records deferrals in the workspace `Deferred` section.
- [ ] Claude routes inbox captures without asking the user filing questions.
- [ ] Claude computes next-action recommendations fresh rather than reading stored plans.
- [ ] Claude asks for approval before semantic note rewrites, splits, merges, or replacements.
- [ ] Claude corrects canonical inputs rather than patching generated outputs.

## L. Scenario tests

### Scenario 1 — New cross-domain note
One note covering mathematics and ML: multiple concept references, reasonable bucket, retrievable from both concepts, no duplicate needed.

### Scenario 2 — Contextual source judgment
One book strong for derivations, weak for first exposure: one source record, contextual evaluation preserved, source index displays it, no scalar rating.

### Scenario 3 — Workspace completion
Durable notes remain active; temporary context archived; archived workspace absent from default retrieval; COORDINATION dependencies cleared; generated outputs valid.

### Scenario 4 — File move
ID unchanged; references resolve; generated paths update; Git history understandable.

### Scenario 5 — Generated reset
Delete `generated/`, rebuild: all outputs return, nothing canonical lost, validation passes.

### Scenario 6 — Handwritten transcription
Original preserved; transcription marked `ai-assisted`; reasoning not normalized into textbook prose; semantic review status explicit.

### Scenario 7 — Exam attempt lifecycle
Record: registered for 1. Termin → withdrawn (Rücktritt) → registered for 2. Termin. Pass: one module record; attempts ordered and complete; module and coordination views update; the dates appear canonically nowhere else.

### Scenario 8 — Crosswalk decomposition (pilot: Master Wiring)
Pass: concept relations extracted to the registry; judgments to source records; narrative preserved in a `role: crosswalk` note; generated selector view reproduces the original table's information; no judgment exists only in the note.

---

## Completion threshold

Cutover only when: all critical structural, ownership, reference, module, generated-artifact, and preservation tests pass; remaining failures are documented; no unresolved failure risks semantic loss; the user has reviewed the pilot and final migration reports.
