# Learning OS v3 — Workflows (Consolidated v3.1)

## 1. Start a workspace

Create:

```text
work/active/<workspace-id>/
├── CONTEXT.md
├── scratch/
├── inputs/
└── outputs/
```

`CONTEXT.md` frontmatter:

```yaml
---
id: workspace-...
type: workspace
title: ...
created: YYYY-MM-DD
status: active
standing: false        # true only for continuous efforts (degree planning, job)
concepts: []
notes: []
sources: []
deadline:              # non-exam operational deadline only; exam dates live in modules.yaml
---
```

Body sections — `Objective`, `Current Scope`, `Open Questions`, and `Next Action` are required; `Temporary Source Menu`, `Current Plan`, `Durable Notes`, and `Deferred` optional.

**Scope triage:** when the effort's topic expands into prerequisites and side-paths, label items *required now / helpful now / defer / reference only* (in `Current Scope` and on the source menu). Accepted "not now" decisions go under `Deferred` with one line of reasoning — a deferral is a recorded decision the system can replay, not a thought to re-have.

If the active count reaches 8+, the validator warns: finish or archive something first.

## 2. Capture temporary material

Put fragments, quotations awaiting processing, rough diagrams, temporary source lists, partial calculations, and lecture-specific checklists in workspace `scratch/` or `inputs/`. Temporary capture does not require canonical metadata.

When no workspace is obvious, drop anything into `work/inbox/` — no naming, no metadata. The operator routes inbox items to their deterministic destination (ARCHITECTURE §3.3); the inbox trends toward empty.

## 3. Create or evolve a durable note

1. search for an existing note with the same purpose;
2. update it when appropriate;
3. otherwise assign a stable note ID (no gratuitous numeric suffix);
4. assign a role if not `synthesis` (`exercise-bank`, `mock-exam`, `crosswalk`, …);
5. save as `knowledge/notes/<bucket>/<note-id>.md` — filename is always the ID, bucket is the nearest reasonable domain;
6. attach relevant concept and source IDs;
7. preserve uncertainty and unfinished reasoning;
8. add the workspace ID as context when useful;
9. rebuild generated outputs.

Do not require polish or completeness.

## 4. Add a concept

1. search labels and aliases (both languages);
2. reuse an existing concept if semantically equivalent;
3. create a readable stable ID; label in English; add German terms as aliases;
4. add only short disambiguation if necessary — never a full explanation;
5. rebuild generated outputs.

## 5. Add a concept relation

1. confirm both concept IDs exist;
2. choose the narrowest of the eight supported types — if none fits, the relationship belongs in note prose;
3. add optional context if the relationship is conditional;
4. optionally cite a supporting note or source;
5. avoid duplicate edges;
6. rebuild generated outputs.

## 6. Add or evaluate a source

1. search the registry by title, author, identifier, and URL;
2. reuse the existing record when found;
3. add identity metadata and `material://` or URL location;
4. record evaluation globally or per concept: strengths, weaknesses, level, audience, prerequisites, useful sections;
5. avoid universal quality scores;
6. rebuild the source index.

Source evaluations are the canonical home of pedagogical judgments — including those narrated in crosswalk notes.

### 6a. Intake of new external learning material (formalized 2026-07-17)

The single path for EVERY new find — course, video, book, blog, paper, tool.
This replaces the legacy LEARNING-RESOURCES intake protocol; there is no other
list to also update.

1. **Register** the source (steps 1–5 above) in `sources/sources.yaml` or a
   `sources/registry/*.yaml` partition. One record per teaching object; the
   one-line "why it earns its place" goes into the evaluation, never into a
   note or plan file.
2. **Place the material:**
   - web-native (ALL videos, courses, blogs, interactive): `url` on the record
     — videos are never downloaded;
   - free downloadable file that is exam- or thesis-critical: pull into the
     materials topic tree via the PLACEMENT map + `tools/build_materials_tree.py`,
     record `material://<source-id>/…`;
   - campus-license or paid: leave URL-only until Aram pulls/decides.
3. **List it (optional):** if it belongs in a curated per-domain list, add an
   entry to the matching `sources/collections/<name>.yaml` (workflow 6b).
4. **Verify:** `python tools/validate.py` then `python tools/generate.py`.

**Degree-planning menus:** the per-module resource menus for FUTURE TU modules
live in `work/active/workspace-degree-planning/inputs/MASTERS-*-RESOURCES.md`
(prospective picks, not registry material). Only their cross-module anchor
tier is registered (`registry/degree-anchors.yaml` + the degree-module-anchors
collection). **When a module is actually chosen, promote its full menu**: walk
that module's section, register each resource per the steps above, and start a
module collection.

### 6b. Maintain a source collection (curated reading list)

Collections live at `sources/collections/<name>.yaml` (kebab-case filename =
identity; schema: `system/schema/collections.schema.json`) and are rendered to
`generated/collections/<name>.md`.

1. a collection is an ordered, optionally grouped list of `source:` references
   plus a one-line `why` — the entry's role *in this list* (spine vs
   supplement, when to reach for it);
2. judgments about the source itself stay in the source record's evaluations —
   collections reference, never re-own (same rule as crosswalk notes);
3. a source may appear in several collections;
4. create a new collection only for a durable curated list (per-domain
   lecture-series, explainers, for-later shelves) — never for operational
   to-watch queues, which belong to workspaces;
5. the validator enforces that every entry resolves to a registered source.

## 7. Handle questions

Temporary → workspace `Open Questions`; durable local → section in a note; durable cross-cutting → standalone note (`role: question`) only if it merits independent retrieval. No question registry.

## 8. Record evidence

Use note metadata or prose references:

```yaml
evidence:
  - type: derivation
    ref: note://note-logistic-loss-derivation
  - type: implementation
    ref: github://owner/repo/path
```

No evidence registry.

## 9. Update coordination

When a commitment, explicit priority decision, cross-workspace dependency, or deferral changes:

1. edit `work/COORDINATION.md` — facts only, stated plainly;
2. never copy exam dates, workspace statuses, or workspace lists into it;
3. rebuild `generated/coordination-view.md`.

If the user states an operational fact in conversation ("I'm skipping M2, writing the 2. Termin"), route it: the deferral to `COORDINATION.md`, the attempt change to `records/modules.yaml`.

## 10. Record a module event

On registration, withdrawal (Rücktritt), sitting, or grade:

1. append or update the attempt in `records/modules.yaml` (`termin`, `date`, `result`, optional `grade`);
2. update module `status` when warranted;
3. rebuild module and coordination views.

Never record these facts anywhere else.

## 11. Complete and archive a workspace

1. identify durable knowledge created or changed;
2. update or create notes;
3. add warranted source evaluations and concept relations;
4. ensure the workspace links to final durable notes;
5. clear dependencies referencing this workspace from `COORDINATION.md`;
6. set `status: complete`;
7. rebuild and validate generated files;
8. move to `archive/workspaces/<year>/<workspace-id>/` unchanged.

Standing workspaces (`standing: true`) are exempt from this workflow.

## 12. Generate indexes and reports

One documented command produces, from canonical inputs only:

- `manifest.json`;
- `concept-index.md` — with a letter-grouped table of contents;
- `source-index.md` — with a letter-grouped table of contents, including per-lecture and per-concept selector views with first-learning / review / implementation recommendations;
- `module-view.md`;
- `coordination-view.md` — exam spine (from modules.yaml) + workspace statuses/deadlines/next actions (from frontmatter) + coordination facts + materials-queue counts (`materials/_unsorted/`, `materials/_duplicates-for-review/`) + Git-derived neglect signals;
- `dependency-report.md`;
- `concept-map.md` — Mermaid rendering of the prerequisite graph (`requires` + `builds-on`), the visual twin of the dependency report;
- `backlinks.json`;
- validation report.

Generated files state that they are generated, name the generator version and canonical inputs, and are gitignored.

## 13. Review a note

A semantic review is deliberate: update reasoning as explicitly approved; set `reviewed`; preserve meaningful uncertainty; rebuild generated outputs. File modification is not semantic review.

## 14. Move or rename a note

Preserve the ID; repair explicit path links; keep ID-based references unchanged; rebuild generated artifacts; validate. Path changes never alter identity.

## 15. Deprecate or supersede

Prefer preservation over deletion:

```yaml
state: deprecated
supersedes:
  - note-old-id
```

Concepts: `deprecated: true` + `replaced_by`. Generated indexes mark deprecated records but do not erase them.

## 16. Maintain a crosswalk

1. narrative changes (why a source suits a lecture, sequencing advice) → edit the crosswalk note;
2. judgment changes (strengths, weaknesses, level, per-concept usefulness) → edit the source records;
3. rebuild the source index; confirm the generated selector view reflects the change;
4. the validator warns if a crosswalk note accumulates judgment tables — that content belongs in source records.

## 17. Ingest a handwritten note

The user drops photos/scans into `work/inbox/` (or a workspace `inputs/`) and says what they are. The operator does everything else:

1. determine the owning note: extend an existing note or mint a new ID;
2. move the originals to `knowledge/attachments/<note-id>/page-01.jpg`, `page-02.jpg`, … — originals are canonical and Git-tracked, never deleted without explicit approval;
3. transcribe faithfully into the note body — preserve the user's reasoning, uncertainty, wrong turns, and notation; never substitute a generic textbook explanation;
4. set `transcription: ai-assisted`, `authorship: user`, `semantic_review: unreviewed`;
5. list the attachment paths in the note's `attachments` frontmatter;
6. link concepts and sources; add workspace context;
7. rebuild generated outputs.

**Worked example** — three photographed pages deriving cross-entropy from maximum likelihood, taken during workspace `workspace-aml-l05`:

```text
knowledge/notes/machine-learning/note-cross-entropy-mle.md   ← transcription + metadata
knowledge/attachments/note-cross-entropy-mle/page-01.jpg     ← originals, preserved
knowledge/attachments/note-cross-entropy-mle/page-02.jpg
knowledge/attachments/note-cross-entropy-mle/page-03.jpg
```

```yaml
---
id: note-cross-entropy-mle
type: note
title: Cross-entropy as negative log-likelihood — own derivation
created: 2026-07-16
role: derivation
state: rough
authorship: user
transcription: ai-assisted
semantic_review: unreviewed
concepts: [concept-cross-entropy, concept-maximum-likelihood]
sources: [source-aml-ss26-lectures, source-bishop-prml]
attachments:
  - knowledge/attachments/note-cross-entropy-mle/page-01.jpg
  - knowledge/attachments/note-cross-entropy-mle/page-02.jpg
  - knowledge/attachments/note-cross-entropy-mle/page-03.jpg
contexts: [workspace-aml-l05]
evidence:
  - type: derivation
    ref: note://note-cross-entropy-mle
---
```

A year later, "cross-entropy" retrieves this note through either concept, shows the original handwriting, and the `derivation` evidence answers "did I ever actually derive this?" — without the user remembering any path.

---

*Workflows 18–21 are the composite lifecycle layer (added 2026-07-18). Each orchestrates the atomic workflows above around a higher-level unit (a module, an effort that outlives a term, the inbox as a batch). They introduce no new entities, schemas, invariants, facts, or owners — only ordered pointers to existing workflows and the single owners those facts already have. If one of these ever seems to need a new rule of its own, that rule belongs in the atomic workflow or the architecture, not here.*

## 18. Start a module

Modules and workspaces are deliberately decoupled: one module may spawn several workspaces (the Kombimodul M2 = SaD + Analysis under one grade; a course with a separate exam-prep effort and project effort). When a course begins, or a previously prospective module is actually chosen:

1. **Module record first.** Ensure the module exists in `records/modules.yaml` and record the registration (workflow 10); set `status: enrolled`. A merely prospective choice is `status: planned` with no attempt. This registry is the sole owner of the administrative facts — never restate them in a workspace or here.
2. **Promote the source menu.** If a degree-planning menu exists for the module, walk its section and register each resource, starting a module collection — the "when a module is actually chosen, promote its full menu" path of workflow 6a, plus workflow 6b. Prospective picks become registered sources only at this point.
3. **Open the first workspace(s).** Create one workspace per distinct effort (workflow 1) — not one per module. A combined module examined under a single grade may still be one exam-prep workspace; an independent project gets its own. A course is not a continuous effort, so `standing: false`.
4. **Wire dependencies, if any.** If the new effort waits on or feeds another, record that in `COORDINATION.md` Dependencies (workflow 9). No exam dates here — they live in `modules.yaml`.
5. **Rebuild and validate** (`python tools/generate.py`, then `python tools/validate.py`).

Check before creating: never open a workspace before its module record exists, and never mint a second record for a module already present.

## 19. Close a module

A module ending is larger than archiving one workspace (workflow 11): it settles the administrative record, may retire several workspaces, and confirms the durable knowledge survived. Use this only when the module is truly done; if a later attempt is still ahead, it is carrying, not closing — use workflow 20.

When a module is finished — its final attempt sat, or abandoned:

1. **Settle the record** in `records/modules.yaml` only (workflow 10). Record the final sitting or submission on the attempt (`result: passed`/`failed`). When the grade posts, record it and set `status: completed` (or `dropped` if abandoned); while the grade is still pending the module stays `enrolled` — archival below does not wait on it.
2. **Confirm durable knowledge landed — before archiving.** For each of the module's workspaces, verify the understanding worth keeping is already a note under `knowledge/`; extend or create as needed (workflow 3; workflow 17 for handwritten pages). An archived workspace is frozen, so promotion happens first, never after.
3. **Archive each workspace whole** (workflow 11 for every workspace the module owns): durable links confirmed, `status: complete`, moved to `archive/workspaces/<year>/`. Archival waits on step 2, not on the grade. Skip any `standing: true` effort — it is exempt and does not close with the module.
4. **Clear operational state.** Remove the module's now-dead entries from `COORDINATION.md` — resolved dependencies, satisfied deferrals, stale priorities and commitments (workflow 9). Coordination should not mention a closed module.
5. **Carry-over check.** If anything outlives the module — a second attempt not yet sat, thesis groundwork, an unfinished thread — route it through workflow 20 instead of archiving it away.
6. **Rebuild and validate.**

Do not archive before knowledge is promoted (step 2); doing so strands it.

## 20. Carry work across semesters

Some efforts outlive a module or a semester: a second exam attempt, thesis preparation, a long project, an unfinished thread. This is decision logic over existing atomic workflows, so a workspace neither becomes immortal nor fragments. When an effort must continue past its module's or semester's end, choose exactly one:

- **Continue the same workspace** when the objective is unchanged and merely unfinished — a `standing: true` effort (degree planning, job), or an exam-prep workspace whose next attempt is still ahead. Nothing moves. Standing workspaces (ARCHITECTURE §9.2) never archive on a semester boundary.
- **Archive and open a successor** when the objective has meaningfully shifted or the old context is spent. Archive the old workspace (workflow 11); create the new one (workflow 1); record the lineage with `supersedes:` on the successor (workflow 15). Durable notes are shared canon already — do not copy them; the successor links the same note IDs.
- **Split** when one workspace has grown two distinct objectives, or the active-count cap (8, workflow 1) forces a division. Open the second workspace (workflow 1), move the relevant `scratch/`/`inputs/`, and note the split in each `CONTEXT.md`.

Record any resulting cross-effort dependency in `COORDINATION.md` (workflow 9). Across all three choices the knowledge layer is invariant — only workspaces, the operational containers, start, stop, or divide.

Worked case: AML's 1. Termin was withdrawn and the 2. Termin (2026-09-30) is still ahead, so `workspace-aml-exam-prep` *continues* (first option); nothing archives until that sitting is written and the module closes via workflow 19.

## 21. Process the inbox

Routing destinations are already deterministic (ARCHITECTURE §3.3); this is the loop that applies them, not a new routing policy. It invents no destinations — each item is pointed at the workflow that already owns it. `work/inbox/` is the zero-friction capture point and should trend toward empty. Process it by taking each item in turn and routing it to its single deterministic destination:

1. **Durable understanding** (a worked derivation, a synthesis worth finding again) → a note under `knowledge/` (workflow 3); handwritten photos or scans → workflow 17.
2. **Temporary material** tied to an active effort (fragments, a rough source list, lecture-specific checklists) → that workspace's `scratch/` or `inputs/` (workflow 2).
3. **A new learning resource** (course, video, book, blog, paper, tool) → register it (workflow 6a); add to a curated list if it belongs on one (workflow 6b).
4. **An operational fact** (commitment, priority, dependency, deferral) → `COORDINATION.md` (workflow 9).
5. **An exam, registration, or grade fact** → `records/modules.yaml` (workflow 10) — never anywhere else.
6. **A concept or relation worth registering** → workflow 4 or workflow 5.

When an item is genuinely ambiguous, prefer capturing it into the most likely workspace's `scratch/` over guessing a canonical home (least destructive, then ask); Aram never makes the filing decision — the operator does. Rebuild generated outputs once any registry changed.
