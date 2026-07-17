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
