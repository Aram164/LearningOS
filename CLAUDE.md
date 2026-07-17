# Claude Operating Contract (Consolidated v3.1)

## 1. Purpose

Claude is the primary mechanical operator and retrieval assistant for Learning OS v3. Claude must reduce organizational burden while preserving user ownership of meaning. The architecture, schemas, validation rules, and acceptance tests are binding.

---

## 2. Bootstrap order

At the beginning of repository work, read:

1. `system/PHILOSOPHY.md` — the user's intent; its principle "reduce organizational burden rather than create it" is the tiebreaker for every ambiguity not settled by this contract
2. `system/WHY-REDESIGN.md`
3. `system/ARCHITECTURE.md`
4. `system/schema/*.schema.json` + `system/VALIDATION.md`
5. `system/WORKFLOWS.md`
6. `work/COORDINATION.md` and `records/modules.yaml`
7. the relevant active workspace, if one exists
8. generated indexes only as navigation aids

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

When asked about **exams, registrations, or grades**: answer from `records/modules.yaml` — never from prose copies.

When a topic **explodes into prerequisites** (scope explosion): propose a triage — *required now / helpful now / defer / reference only* — sized to the workspace objective, record accepted deferrals in the workspace `Deferred` section, and recommend the smallest useful next source or prerequisite. Preserve the wider graph in concept relations without forcing it into the current scope.

When asked "what should I do next" or about **operational state**: rebuild the coordination view if stale, then answer from it; recommendations are computed fresh, not read from stored plans.

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

When a new operational fact appears (commitment, deferral, dependency, exam event): route it to its single owner (`COORDINATION.md` or `modules.yaml`), never into notes or the coordination view.

---

## 9. Ambiguity policy

When migration or classification is ambiguous: preserve the original; choose the least destructive reversible action; record the ambiguity in the migration report; do not invent certainty; do not block the entire migration if safe partial progress is possible.

---

## 10. Generated artifacts

Every generated file states that it is generated. Claude never manually patches a generated output when the underlying canonical data can be corrected instead. Generated outputs are reproducible with documented commands and are gitignored.

---

## 11. External materials and projects

External materials live under `LearningOS/materials/`; code repositories under `LearningOS/projects/` or documented external locations. Claude accesses them only when a canonical source or note refers to them, or when the user explicitly requests broader search. Never copy dependency trees, virtual environments, cloned repositories, videos, or books into the authored knowledge tree.

---

## 12. Migration protection

During migration Claude must: create a complete inventory; preserve original paths in a migration map; retain originals until acceptance tests pass; avoid semantic rewriting; preserve attachments; record unresolved items; migrate the representative pilot (including the AML–SaD Master Wiring) before full conversion; make all phases independently reviewable and reversible.

---

## 13. Job quarantine (Aram's standing instruction, 2026-07-17)

The folder **`Job/`** (sibling of `LearningOS/` at the semestercontext root —
or wherever it lives after a folder move; it carries its own README marker)
is **outside the default search space**. It holds the BIFOLD/DEEM job:
the stratum repository, the job workspace, skrub notes, papers, onboarding
plans.

- Do **not** read, scan, index, cite or route anything into or out of `Job/`
  during normal operation — not for retrieval, not for generation, not for
  validation sweeps.
- Access it **only** when Aram explicitly commands it in the conversation
  ("scan the job folder", "look at stratum", "work on the job workspace").
  The permission lasts for that task only.
- Job knowledge deliberately does not appear in the registries or generated
  views while quarantined. If job-relevant durable knowledge should enter the
  canon, Aram says so explicitly.
