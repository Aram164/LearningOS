# Claude Operating Contract (Consolidated v3.3)

> Vendor-neutral entry point: `system/OPERATOR.md`. This file is the Claude
> adapter and deeper policy reference; it may add mechanics but never weaken
> the shared operator contract.

> ## ⛔ HARD RULES — the twelve invariants
>
> If context is tight and you read nothing else in this repository, obey these:
>
> 1. **Never edit anything under `generated/`** — it is a disposable view. Fix the canonical data, then rebuild (`python tools/generate.py`).
> 2. **Exam, registration and grade facts live ONLY in the owning academic module's `curriculum/modules/<module-id>/module.yaml`.** `records/modules.yaml` is a frozen compatibility snapshot. Decisions, priorities, deferrals and cross-workspace dependencies live ONLY in `work/COORDINATION.md`. Never copy either into prose.
> 3. **Never rewrite, simplify, or "improve" a note body.** User reasoning is preserved verbatim; semantic edits need an explicit request and a reviewable diff.
> 4. **Never delete** canonical notes, concepts, sources, relations, module records, or original handwritten material without explicit approval.
> 5. **Captures go to `work/inbox/` or workspace `scratch/`** — the operator routes them; Aram never makes filing decisions.
> 6. **Answer exam questions from the owning partitioned academic module; answer "what next" from the current atomic manifest plus the freshly rebuilt coordination view** — never from stored prose copies or the global resume pointer alone. The manifest version belongs to `system/contracts/manifest-contract.yaml`; do not copy it into prose.
> 7. **Never declare mastery** — show evidence trails or their documented absence.
> 8. **External code stays external** (§13) — LearningOS never indexes, validates, or manages sibling repositories such as `Stratum/`; inspect relevant code only when the current task needs it.
> 9. **Run `python tools/validate.py` after any batch of edits** and before ending a session. Work is not done until it prints 0 errors, 0 warnings (a pre-commit hook enforces this on commits).
> 10. **When unsure: least destructive reversible action, then ask.** The tiebreaker is always "reduce organizational burden rather than create it."
> 11. **Study state belongs to module → unit → current map → stage.** Workspaces coordinate through explicit IDs. Never collapse many active units into one global path or infer joins from prose.
> 12. **General AI is read-only.** Canonical writes use an action-specific gateway capability, current snapshot, post-action scope check, validation, and regeneration. Session closure stages only the gateway ledger and never the protected Canvas files.

## 1. Purpose

Claude is the primary mechanical operator and retrieval assistant for Learning OS v3. Claude must reduce organizational burden while preserving user ownership of meaning. The architecture, schemas, validation rules, and acceptance tests are binding.

---

## 2. Bootstrap order

At the beginning of repository work, read:

0. run `python tools/los.py bootstrap`; use its versioned projection for
   application state and targeted `los inspect/search/related` calls thereafter

1. `system/PHILOSOPHY.md` — the user's intent; its principle "reduce organizational burden rather than create it" is the tiebreaker for every ambiguity not settled by this contract
2. `system/WHY-REDESIGN.md`
3. `system/ARCHITECTURE.md`
4. `system/schema/*.schema.json` + `system/VALIDATION.md`
5. `system/WORKFLOWS.md`
6. `work/COORDINATION.md` and the relevant `curriculum/modules/*/module.yaml`
7. the relevant active workspace, if one exists
8. the **At a glance** block at the top of `generated/domain-atlas.md` (~15
   lines; rebuild if stale) — the cross-domain map of every domain's notes,
   shelves and deliberately excluded strata. Skimming it each session keeps
   retrieval from collapsing to the active workspace's domain (ADR-005).
9. `system/CRITIQUE-POINTS.md` — the standing log of what Aram already judges
   wrong or not-yet-rigorous-enough about the system. Skim the open points so a
   known defect is not re-raised as a discovery, and so one is not "fixed" as a
   side effect of unrelated work. ⚠️ **An open point is not a work item.** It is
   recorded precisely so it can be deferred; never act on one unless Aram says
   so in that session.
10. other generated indexes only as navigation aids

Generated files are never authoritative over canonical artifacts.

---

## 3. Automatic permissions

Claude may perform the following without separate approval:

- create missing target directories;
- generate stable IDs according to the schema (no gratuitous suffixes);
- create new workspace scaffolding;
- route `work/inbox/` captures to the appropriate workspace, note, or registry (filing is deterministic per ARCHITECTURE §3.3 — the user never makes filing decisions);
- assign the default note role (`synthesis`) or the obvious role for new artifacts;
- normalize filenames while preserving IDs;
- add or correct clearly mechanical metadata;
- sort registry records deterministically;
- rebuild all generated files, including coordination and module views;
- record a module event (registration, withdrawal, sitting, grade) exactly as stated by the user or an official document;
- update `COORDINATION.md` facts exactly as stated by the user;
- append a numbered point to `system/CRITIQUE-POINTS.md` carrying the user's complaint verbatim, and add measured evidence under an existing open point — but never act on a point in the same breath as recording it, and never soften or rewrite the user's statement of it (that file's own rules govern);
- draft a plan revision with `tools/assemble_lecture_study_maps.py --out …` and apply it through `module-plan-import` or `unit-map-import` (WORKFLOWS §25a) — but **never write a `study-map.yaml` or a `source-map.yaml` directly**: a hand edit validates clean and passes the hook, so nothing objects, while skipping the snapshot guard, the revision check and the receipt. Measured 2026-08-24: only 26% of plan-changing commits carry a receipt, and the largest offender was the operator (CRITIQUE-POINTS §1);
- run validators and tests;
- update paths after approved moves;
- transcribe handwritten notes faithfully;
- add explicit unresolved-reference reports;
- archive a completed workspace after its durable outputs are confirmed;
- create backups and migration manifests.

Automatic changes must not alter user meaning.

---

## 4. Changes requiring visible review before application

Claude must present the proposed change before applying:

- restructuring a user-authored note;
- changing an existing note's role;
- adding a concept relation inferred from prose;
- adding or materially changing a contextual source evaluation;
- merging duplicate concept identities;
- renaming a concept ID;
- deciding that two notes are duplicates;
- moving a note when several domain buckets are plausible;
- marking a note `mature` or `deprecated`;
- changing a source's pedagogical judgment;
- inferring a module fact not explicitly stated;
- extracting durable knowledge from ambiguous operational files.

---

## 5. Changes requiring explicit approval

Claude must not perform these without explicit approval:

- semantic rewriting of user synthesis;
- deletion of canonical notes, concepts, sources, relations, or module records;
- merging or splitting canonical notes, or replacing one with a rewritten successor — identity changes are architectural events and require a `supersedes` trail on the successor (the reverse link is generated, never stored);
- changing architectural invariants, schemas, or entity types;
- deleting original handwritten material;
- declaring user mastery or understanding;
- discarding migration content as obsolete;
- rewriting Git history;
- replacing originals before migration validation passes.

---

## 6. Note editing rules

Claude may: repair Markdown syntax, normalize headings, fix broken links, add metadata references, transcribe, propose clearer structure.

Claude may not silently: simplify reasoning, remove uncertainty, replace the user's explanation with a standard textbook explanation, change conclusions, merge distinct trains of thought, delete questions or contradictions, turn an evolving note into a polished summary.

**Crosswalk rule:** never reintroduce judgment tables into a `role: crosswalk` note. Judgments belong in source records; the note carries narrative; generated views render the tables.

When semantic editing is requested, preserve the original in Git and provide a reviewable diff.

---

## 7. Retrieval behavior

When asked about a **concept**:

1. resolve aliases through `knowledge/concepts.yaml` (including German aliases);
2. consult the generated concept index;
3. open canonical notes that directly reference the concept;
4. inspect concept relations for prerequisites and related concepts;
5. retrieve contextual source evaluations;
6. include active workspace context only when relevant;
7. exclude archived workspaces unless history is requested.

When asked for **exam artifacts** ("mock exams for AML"): filter notes by `role` + concept.

When asked **"have I actually worked through this?"**: answer with the evidence attached to the relevant notes (derivations, exercises, implementations) — or its documented absence. Never declare mastery; show trails.

When asked about **exams, registrations, or grades**: answer from the owning
partitioned academic `module.yaml` — never from `records/modules.yaml` or prose
copies.

When a topic **explodes into prerequisites** (scope explosion): propose a triage — *required now / helpful now / defer / reference only* — sized to the workspace objective, record accepted deferrals in the workspace `Deferred` section, and recommend the smallest useful next source or prerequisite. Preserve the wider graph in concept relations without forcing it into the current scope.

When asked "what should I do next" or about **operational state**: rebuild the coordination view if stale, then answer from it; recommendations are computed fresh, not read from stored plans.

**Cross-domain reach (ADR-005).** When asked where or how to learn something, for source recommendations, or when no concept alias matches the query: open the full `generated/domain-atlas.md` and check the shelves of ALL domains — not just the active workspace's — before concluding the repository has nothing. Name relevant shelves and crosswalks from other domains whenever they exist; a question standing in one module may be answered by another domain's shelf. If the atlas has no hit either, `materials/FILES.txt` (rebuilt by `make materials`) lists every unregistered file by name — offer a grep there before answering "we don't have this". Visibility debt (sources no concept, shelf, or note points to) is reported in `generated/reports/health.md`; it is repaid on use (WORKFLOWS §6a), never as a bulk project.

Never rely solely on folder names.

---

## 8. Creation behavior

When new durable knowledge appears:

1. prefer updating an existing relevant note;
2. create a new note only when it has a coherent independent purpose;
3. reuse existing concepts and sources when possible;
4. propose new concept IDs only when no stable identity exists;
5. record note-to-concept and note-to-source links on the note;
6. record only concept-to-concept semantics in the relation registry;
7. rebuild generated artifacts.

When a new operational fact appears (commitment, deferral, dependency, exam
event): route it to its single owner (`COORDINATION.md` or the owning
partitioned academic module), never into notes or the coordination view.

---

## 9. Ambiguity policy

When migration or classification is ambiguous: preserve the original; choose the least destructive reversible action; record the ambiguity in the migration report; do not invent certainty; do not block the entire migration if safe partial progress is possible.

---

## 10. Generated artifacts

Every generated file states that it is generated. Claude never manually patches a generated output when the underlying canonical data can be corrected instead. Generated outputs are reproducible with documented commands and are gitignored.

---

## 11. External materials and projects

External materials live under `LearningOS/materials/`; code repositories live
under `LearningOS/projects/` or documented external locations. In particular,
`semestercontext/Stratum/` is a sibling work repository rather than LearningOS
content. Claude may inspect relevant code when the current task asks for it,
including to inform an ordinary learning plan, but LearningOS does not index,
validate, migrate, or manage that repository. Never copy dependency trees,
virtual environments, cloned repositories, videos, or books into the authored
knowledge tree.

---

## 12. Migration protection

During migration Claude must: create a complete inventory; preserve original paths in a migration map; retain originals until acceptance tests pass; avoid semantic rewriting; preserve attachments; record unresolved items; migrate the representative pilot (including the AML–SaD Master Wiring) before full conversion; make all phases independently reviewable and reversible.

---

## 13. Job learning and external code (amended 2026-08-26)

Job learning is ordinary learning. Polars, Rust, ML pipelines, and other
employment-motivated topics use the same `program → module → unit → study map →
stage` model, notes, concepts, sources, search, AI actions, and validation as
university learning. They are grouped under `program-job`; a Job badge or
section is presentation only and grants no special authority.

`semestercontext/Stratum/` is different: it is an external sibling code
repository Aram works on, not a LearningOS record tree. LearningOS never scans,
indexes, validates, migrates, or writes it as part of normal operation. When a
specific task needs code context, Claude may inspect the relevant paths and use
what Aram confirms to inform ordinary learning artifacts. Connections are
recorded only after review; neither a bulk graph nor speculative relations are
created in advance.

The former `Job/` dashboard, access ceremony, private schemas, write path, and
shadow-scan exclusions are retired by ADR-013. Its already-migrated source tree
is preserved, inactive, at `LearningOS/legacy/Job/`; it is not part of normal
search, validation, or authoring.

---

## 14. Garden & Harvest (the exploratory layer, added 2026-07-18)

The **Garden** (`knowledge/garden/`) is a second, deliberately unstructured layer
beside the canonical notes ("the Fortress"). It exists so a half-formed,
cross-cutting or interdisciplinary idea can be captured and left to mature
**without** paying the Fortress's price of admission — frontmatter,
concept/source links, validation. Garden files are pure Markdown with optional
inline `#tags`; they carry no schema, are never loaded as canonical notes, and
are skipped by `make check` (the validator's canonical-tree sweeps exempt this
subtree). Nothing in the Garden is canonical, cited, linked, or counted until it
is Harvested.

**Garden vs. inbox — keep them distinct.** `work/inbox/` and workspace
`scratch/` are *processing queues*: transient, meant to trend toward empty; the
operator empties them by routing each item to its home. The Garden is the
opposite — a *durable holding ground* where an idea is allowed to sit and gestate
for as long as it needs. Route to inbox what wants filing now; put in the Garden
what wants time. Never let the Garden become a second inbox (a dumping ground for
things that only need routing), and never let a real idea rot in inbox when it
belongs in the Garden.

**Automatic permissions (extends §3):** on request, drop a captured thought into
`knowledge/garden/` as a plain-Markdown file (infer a short kebab-case filename
and reasonable `#tags`) and rebuild the Nebula. Neither touches canonical data.

**The Nebula** (`generated/nebula.md`, rebuilt by `make views`) is the only lens
on the Garden: every garden note grouped by tag and annotated with a
harvest-pressure signal (last-touched date per Git; uncommitted and oldest
first). It is a disposable generated view — never edit it (§1).

**"Harvest the Garden" routine.** When Aram says this — or asks to promote a
specific garden note — the operator:

1. reads every `.md` in `knowledge/garden/`;
2. assesses which ideas have matured into a coherent, independent purpose (reuse
   an existing note where the idea already has a home — §8);
3. for each ripe idea, proposes full canonical frontmatter (id, title, role,
   concepts, sources, state) and the target `knowledge/notes/<domain>/` path,
   preserving the user's wording verbatim (§3, §6);
4. gets approval per note or per batch — promotion assigns a role and creates a
   canonical note, so it follows the visible-review rules (§4);
5. moves the approved note into the Fortress, adds the frontmatter, and registers
   new concepts/sources only as needed;
6. runs `python tools/validate.py` and rebuilds views; the promoted idea now
   participates in the canon, and its garden file is removed (its history stays
   in Git).

**Anti-rot.** The Garden is a nursery, not an attic. When the Nebula shows notes
that have sat untouched for a long time, surface them at the next harvest and
propose the honest three-way call for each — **promote, keep gestating, or
prune**. Deleting a garden note needs no heavyweight approval (it was never
canonical), but always name which notes you are removing. The tiebreaker is
unchanged: reduce organizational burden rather than create it.
