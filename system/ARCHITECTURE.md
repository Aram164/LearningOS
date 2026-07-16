# Learning OS v3 — Architecture (Consolidated v3.1)

> Consolidated 2026-07-16. Incorporates the Architecture Revisions §1–§16 and the final ownership-boundary review. This file is the single authoritative architecture; the original package and the revisions document are historical.

## 1. Purpose

Learning OS v3 is a long-lived, plain-file knowledge repository for deep technical learning.

Its primary purpose is to preserve and retrieve:

- what the user understood;
- which concepts that understanding concerns;
- which sources helped;
- how concepts relate;
- which modules were taken, attempted, and completed;
- what the user is currently working on.

The system must reduce organizational effort rather than create a second administrative workload.

It is not primarily:

- a note-taking application;
- a learning-management system;
- a database;
- a mastery-scoring system;
- or an ontology of every stage of cognition.

It *does* include a deliberately minimal operational layer (coordination + module records), because the alternative — operational facts leaking into notes and hand-maintained status files — is the drift disease this redesign eliminates.

**Operator independence:** this document defines *what the system is* — canonical artifacts, layout, ownership, lifetimes, routing, generated views, invariants. It assumes no particular operator. The current operator is Claude, whose behavior is defined solely in `CLAUDE.md`; any capable agent, application, or human could operate the repository from the same contracts.

---

## 2. Architectural model

### 2.1 Durable canonical knowledge

Exactly four canonical families:

1. **Notes**
2. **Concepts**
3. **Sources**
4. **Concept relations**

No additional canonical *knowledge* entity type without demonstrated recurring need.

### 2.2 Durable factual records

**Module records** (`records/modules.yaml`): administrative facts — institution, module identity, credits, examination attempts, grades. Facts, not knowledge; they never contain synthesis.

### 2.3 Operationally canonical

- `work/COORDINATION.md` — cross-workspace coordination facts (§10);
- **active workspaces** — one coherent learning effort each (§9).

Operationally canonical means: authoritative while active, but not part of the permanent knowledge model.

### 2.4 Preserved historical context

Completed workspaces are archived whole. Archived workspaces preserve context and provenance but are excluded from normal concept retrieval once durable notes exist. The frozen legacy tree is historical context.

### 2.5 Deterministically generated artifacts

Derived from canonical data; gitignored; may be deleted and rebuilt at any time:

- manifest;
- concept index;
- source index (including crosswalk selector views);
- module views;
- coordination view;
- backlinks;
- validation reports.

Generated artifacts must never become canonical inputs.

### 2.6 Agent-computed and disposable artifacts

Produced by the operator through reasoning, never canonical: study plans, source menus, contextual summaries, review suggestions, next-action recommendations, priority orderings, neglect warnings, temporary comparison tables.

---

## 3. Physical layout

### 3.1 Root

```text
LearningOS/
├── repository/     ← the authored repository (the operator's default search space)
├── materials/      ← books, slides, videos, PDFs, datasets (material:// root)
├── projects/       ← active code repositories (mlprov, amls-project, stratum, …)
└── legacy/         ← frozen pre-v3 tree after migration cutover
```

Code repositories are neither authored knowledge nor materials; `projects/` is their owned home. A repository is moved there only when the move is safe (paths, remotes, teammates); otherwise its location is documented and it is excluded from the knowledge search space. References use `github://` (remote) or `project://` (local) URIs.

**Placement decisions (2026-07-16):** `LearningOS/` lives beside the legacy `semestercontext/` folder. It may be scaffolded *inside* the legacy folder temporarily (tooling access) and relocated after cutover — the authored repository is a **fresh Git repository**, location-independent; legacy history stays with the legacy tree. `legacy/` may be a pointer to the frozen semestercontext rather than a physical move.

### 3.2 Authored repository

```text
repository/
├── README.md
├── CLAUDE.md
├── .gitignore                  ← ignores generated/*
│
├── system/
│   ├── PHILOSOPHY.md           ← user's intent document — read first, tiebreaker for ambiguity
│   ├── WHY-REDESIGN.md
│   ├── ARCHITECTURE.md
│   ├── VALIDATION.md
│   ├── WORKFLOWS.md
│   ├── MIGRATION.md
│   ├── ACCEPTANCE-TESTS.md
│   ├── BUILD-SPEC.md
│   ├── schema/                 ← JSON Schemas (canonical structure contracts)
│   └── adr/
│
├── knowledge/
│   ├── notes/
│   │   ├── mathematics/
│   │   ├── machine-learning/
│   │   ├── algorithms/         ← CS theory: algorithms, data structures, complexity
│   │   ├── data-systems/
│   │   ├── programming/
│   │   ├── systems/
│   │   └── cross-domain/
│   ├── attachments/            ← handwritten originals & images, one folder per note
│   ├── concepts.yaml
│   └── concept-relations.yaml
│
├── records/
│   └── modules.yaml
│
├── sources/
│   ├── sources.yaml
│   └── collections/
│
├── work/
│   ├── COORDINATION.md
│   ├── inbox/
│   └── active/
│
├── generated/                  ← gitignored, fully rebuildable
│   ├── manifest.json
│   ├── concept-index.md
│   ├── source-index.md
│   ├── module-view.md
│   ├── coordination-view.md
│   ├── backlinks.json
│   └── reports/
│
├── archive/
│   └── workspaces/<year>/
│
├── tools/
└── tests/
```

### 3.3 File-saving conventions

Where every artifact physically lands, and what it is named. The user should never have to make a filing decision; these rules make filing deterministic so the operator (or a plain script) can always do it.

| Artifact | Physical location | Filename rule |
|---|---|---|
| Durable note | `knowledge/notes/<bucket>/<note-id>.md` | filename = ID + `.md`, always |
| Handwritten originals, photos, diagrams | `knowledge/attachments/<note-id>/` | `page-01.jpg`, `page-02.jpg`, … |
| Concept registry | `knowledge/concepts.yaml` (partitionable to `knowledge/concepts/*.yaml`) | fixed |
| Relation registry | `knowledge/concept-relations.yaml` | fixed |
| Source registry | `sources/sources.yaml` (partitionable to `sources/registry/*.yaml`) | fixed |
| Source collections (reading lists) | `sources/collections/<name>.yaml` | kebab-case |
| Module records | `records/modules.yaml` | fixed |
| Coordination facts | `work/COORDINATION.md` | fixed |
| Quick capture (anything, unprocessed) | `work/inbox/` | any name; the operator routes |
| Workspace operational files | `work/active/<workspace-id>/{CONTEXT.md, scratch/, inputs/, outputs/}` | scratch is free-form |
| Archived workspace | `archive/workspaces/<year>/<workspace-id>/` | moved whole, unchanged |
| External material with a registered source | `LearningOS/materials/<source-id>/…` | `material://<source-id>/…` resolves here |
| External material not yet registered | `LearningOS/materials/_unsorted/` | temporary; registered then moved |
| Code repositories | `LearningOS/projects/<name>/` | untouched internally |
| Generated outputs | `generated/` | fixed names, gitignored |

**Rules:**

1. **A note's filename is always `<note-id>.md`.** IDs never change, so filenames never change; only the bucket folder may change on a move. Identity still lives in frontmatter — the filename is a derived convenience the validator enforces, never the identity itself.
2. **Buckets are the seven listed** (decision 2026-07-16: `algorithms/` added for CS-theory content — CLRS-style material fits neither mathematics nor programming). A new bucket requires an ADR; buckets are routing neighborhoods, never taxonomy.
3. **Attachments are canonical user artifacts**, not materials: handwritten scans and photos live *inside* the authored repository under `knowledge/attachments/<note-id>/`, are Git-tracked, and are referenced from the owning note's `attachments` frontmatter as repo-relative paths. Books, slide packs, and videos are never attachments — they are materials. The user may periodically prune old scans to reclaim space once transcriptions are reviewed; the operator never deletes originals on its own initiative.
4. **Materials are organized by source identity.** Every registered source with local files owns `materials/<source-id>/`; this makes every `material://` URI trivially resolvable and ties the registry to the disk. Unregistered dumps land in `materials/_unsorted/` until registered.
5. **`work/inbox/` is the zero-friction capture point.** Photos of handwritten pages, pasted links, fragments — no naming, no metadata required at capture time. Routing inbox items into workspaces, notes, or registries is the operator's job; the inbox should trend toward empty.
6. **Only Markdown and YAML belong under `knowledge/`** (plus images under `attachments/`). Binary files elsewhere in the authored tree are validator warnings.

---

## 4. Canonical ownership rules

| Information | Canonical owner |
|---|---|
| Note prose and reasoning | The note |
| Note role, concept links, source links, attachments | Note metadata |
| Concept identity and aliases | `knowledge/concepts.yaml` |
| Concept → concept semantics | `knowledge/concept-relations.yaml` |
| Source identity | `sources/sources.yaml` |
| Contextual source evaluation (incl. crosswalk judgments) | The source record |
| Module identity, credits, components | `records/modules.yaml` |
| **Exam dates, registrations, withdrawals, sittings, grades** | `records/modules.yaml` (attempts) |
| Commitments and explicit priority decisions | `work/COORDINATION.md` |
| Cross-workspace dependencies and deferrals | `work/COORDINATION.md` |
| Current goal and scope of one effort | Active workspace `CONTEXT.md` |
| Workspace status (active / blocked / complete) | Workspace frontmatter |
| Non-exam operational deadline of one effort | Workspace frontmatter `deadline` |
| Temporary questions and plans | Active workspace |
| Reverse links, indexes, dashboards, coordination view | Generated outputs |
| Last physical modification | Git |
| Deliberate semantic review date | Note `reviewed` field |

A canonical fact has exactly one owner.

**The deadline rule:** exam dates exist canonically *only* in `records/modules.yaml`. A workspace `deadline` is for non-exam deadlines owned by that effort (project submissions, peer reviews). `COORDINATION.md` never restates either; the generated coordination view merges them.

---

## 5. Notes

### 5.1 Meaning

A note is an evolving synthesis artifact worth retrieving beyond the current workspace. It may be incomplete, uncertain, rough but durable, mature, mathematical, implementation-focused, cross-domain, or heavily synthetic. These are qualities, not storage classes.

### 5.2 Roles

Notes carry an optional `role` (default `synthesis`):

`synthesis` · `reference` · `derivation` · `exercise-bank` · `mock-exam` · `implementation` · `question` · `crosswalk`

Roles are retrieval hints, not storage classes. They must never map to separate directories, and exam artifacts (`exercise-bank`, `mock-exam`) are durable notes — never auto-archived workspace content.

### 5.3 Boundary between scratch and note

Workspace scratch is temporary. A durable note is created when the user decides: *this understanding is worth finding again outside the current workspace.* A note does not need to be polished before becoming canonical.

### 5.4 Protection

The operator may modify formatting and non-semantic metadata automatically. The operator must not silently change the meaning, reasoning, conclusions, or explanatory structure of user-owned synthesis.

### 5.5 Identity through evolution

A note may grow, gain sections, gain concept and source references, be internally reorganized, receive user-approved corrections, and mature — all under the same ID. Normal evolution never changes identity.

Operations that change a note's **conceptual identity** are architectural events, never automatic:

- splitting one note into several;
- merging several notes into one;
- replacing a note with a rewritten successor;
- re-scoping a note to a different conceptual purpose;
- discarding earlier reasoning or converting uncertainty into certainty.

Each requires explicit user approval and leaves an explicit trail: the successor note declares `supersedes: [note-old-id]`. The reverse link (superseded-by) is **generated**, not stored — reverse links never become canonical fields. Git preserves the historical text; the repository preserves the semantic identity.

---

## 6. Concepts

Concepts are stable retrieval identities. Records contain only: stable ID, preferred label, aliases, optional minimal disambiguation.

**Bilingual policy:** canonical labels are English; German (or other-language) terms are aliases (`Erwartungswert` → `concept-expected-value`). IDs remain ASCII.

Concept records do not contain full explanations, mastery state, manually maintained backlinks, semester ownership, lecture ownership, or duplicated note content. Concept content lives in notes.

---

## 7. Sources

A source is an evaluated teaching object, not merely a file or bibliographic record. A source record contains identity, title, author or organization, type, material location or URL, and contextual evaluations.

Evaluations are contextual: the same source may be excellent for intuition, poor for first exposure, authoritative but pedagogically difficult, or strong for derivations but weak for implementation.

**Crosswalk canonicality:** contextual pedagogical judgments are canonical *only* in source records. A crosswalk note (`role: crosswalk`) narrates and motivates them but is never the sole carrier of an evaluation. Generated per-lecture and per-concept views render the judgments; crosswalk knowledge must never require manual duplication.

The registry may be partitioned into multiple files without changing semantics.

---

## 8. Concept relations

Only explicit concept-to-concept semantic relationships belong in the relation registry. Exactly eight types:

`requires` · `builds-on` · `derives` · `generalizes` · `contrasts-with` · `equivalent-to` · `applies-in` · `motivates`

There is deliberately no `related-to`. Use the narrowest applicable type; if none fits, the relationship belongs in note prose, not the registry.

Note-to-concept and note-to-source relationships remain on notes. Reverse links are generated.

---

## 9. Workspaces

### 9.1 Granularity

A workspace is one **independently completable learning effort**:

```text
workspace-aml-l05
workspace-analysis-exam-prep
workspace-mlprov-wrapper
workspace-stratum-column-selectors
```

Active count: target 3–7; the validator warns at 8+.

### 9.2 Standing workspaces

Continuous efforts with no completion point (degree planning, job) set `standing: true`. They are exempt from completion and archival expectations but are validated normally and count against the cap.

### 9.3 Layout

```text
work/active/<workspace-id>/
├── CONTEXT.md
├── scratch/
├── inputs/
└── outputs/
```

`CONTEXT.md` owns: workspace identity, objective, current scope, relevant concepts, active questions, temporary source menu, current plan, links to durable notes, next action.

### 9.4 Completion

1. durable notes are created or updated;
2. warranted source evaluations and concept relations are added;
3. dependencies referencing the workspace are cleared from `COORDINATION.md`;
4. generated outputs are rebuilt;
5. the workspace moves unchanged to `archive/workspaces/<year>/`.

Do not rewrite an archived workspace to make it tidy.

---

## 10. Coordination layer

`work/COORDINATION.md` is the single long-lived operational document. It owns **only facts nothing else can own**:

- commitments (agreed deliverables to people — when not exam dates);
- explicit priority decisions ("mlprov before AMLS theory until Jul 15");
- cross-workspace dependencies ("workspace-amls-exam-prep blocked by workspace-aml-l07");
- deferrals and waivers ("M2 deferred to 2. Termin, Fr 09.10").

It must **not** contain:

- exam dates or sittings (owned by `records/modules.yaml`);
- workspace statuses or lists (owned by workspace frontmatter; merged views are generated);
- computed recommendations, priority orderings, or neglect warnings (agent-computed, disposable).

The dashboard is `generated/coordination-view.md`, assembled from: the exam spine in `modules.yaml`, statuses/deadlines/next actions from workspace frontmatter, the facts in `COORDINATION.md`, and neglect signals computed from Git timestamps.

**Rationale:** the v2 brain drifted because it manually restated facts owned elsewhere. The coordination layer stays drift-proof only if it remains a small facts file, never a dashboard.

---

## 11. Module records

`records/modules.yaml` owns administrative reality:

- institution, module code, title, credits, semester;
- status: `planned` / `enrolled` / `completed` / `dropped`;
- examination type;
- optional `components` for combined modules (Kombimodul: one grade, several courses);
- an `attempts` list — `{termin, date, result: registered|withdrawn|passed|failed, grade}`;
- final grade.

Attempts are first-class because withdrawal (Rücktritt) and second sittings are normal events, not exceptions. Module dashboards are generated views over this registry.

---

## 12. Questions and evidence

**Questions** are a content pattern, not a default canonical entity: temporary → workspace section; durable local → section inside a note; cross-cutting durable → standalone note (`role: question`) only when it merits independent retrieval.

**Evidence** is a metadata convention, not a registry. A note may reference derivations, implementations, exercises, exams, or external code via `evidence` entries.

**Evidence, not mastery.** The user's working definition of understanding — *can derive it, can explain it, can apply it flexibly* — maps directly onto evidence types: `derivation`, `exercise`/`exam`, `implementation`. The system never scores or declares understanding (file existence proves nothing), but when asked "have I actually worked through this?" it answers by *showing the evidence attached to the relevant notes* — or its absence. That is the honest response to metacognitive uncertainty: verifiable trails instead of claimed mastery.

---

## 13. Identity

Stable IDs are independent of paths and filenames.

```text
note-cross-entropy
concept-maximum-likelihood
source-bishop-prml
workspace-aml-l05
module-hu-m2-statistik-analysis
```

IDs are lowercase, ASCII, hyphen-separated, stable after creation, unique within their entity family, and prefixed by family (`note-`, `concept-`, `source-`, `workspace-`, `module-`).

**Numeric suffixes are collision-only:** `note-cross-entropy`, then `note-cross-entropy-02` on collision. The validator flags gratuitous suffixes. Moving a file must not change its ID — and since a note's filename is always `<id>.md` (§3.3), only its bucket folder ever changes.

---

## 14. Generated versus computed outputs

**Deterministic (gitignored):** manifest, indexes, module views, coordination view, backlinks, validation and health reports. Reproducible from canonical inputs with one documented command; deterministic up to an embedded generation timestamp; never edited manually; never used as canonical inputs.

**Agent-computed and disposable:** plans, recommendations, rankings, summaries, source menus. Never canonical unless explicitly promoted by the user.

**The rule:** a deterministic artifact is reproduced by *rules* and lives only under `generated/`. An agent-computed artifact is produced by *interpretation* and lives only inside workspaces, or is regenerated on demand — never under `generated/`. Neither is ever canonical. The two must never share a label or a directory.

---

## 15. Multi-chat model

Chats are transient; workspaces are persistent. A chat operates on one primary workspace, but a workspace may span many conversations. Workspace identity, not chat identity, is canonical.

---

## 16. Architectural invariants

1. A canonical fact has exactly one owner.
2. Generated files are never edited manually and never serve as canonical inputs.
3. Folder placement is never the sole carrier of meaning.
4. Stable identity does not depend on location; suffixes are collision-only.
5. Notes may reference any number of concepts and sources.
6. Concepts are identities, not note containers.
7. Only concept-to-concept semantic edges belong in the relation registry; there is no `related-to`.
8. Source evaluations are contextual and canonical only in source records; crosswalk notes carry narrative, never the sole copy of a judgment.
9. Exam dates, registrations, withdrawals, and grades exist canonically only in `records/modules.yaml`.
10. `COORDINATION.md` contains only facts not owned or derivable elsewhere.
11. Note roles are metadata, never directory structure; exam artifacts are durable notes.
12. The operator may automate mechanics but never silently changes user meaning.
13. External materials and code projects remain outside the authored repository.
14. New entity types require demonstrated recurring need.
15. The system remains usable through plain files without a particular application.
16. Git remains the history of semantic evolution; `generated/` is gitignored.
17. Migration must preserve original content before normalization.
18. A note's identity survives normal evolution; identity changes (split, merge, replacement, re-scoping) are explicit, approved events with a supersession trail.
19. The repository defines what the system is; operator-specific behavior lives only in the operator contract (`CLAUDE.md` for Claude).

---

## 17. Explicit non-goals

Learning OS v3 will not implement:

- goals, pursuits, or sessions as independent entities;
- questions or evidence as mandatory registries;
- generic universal relationship records;
- semantic change records separate from Git;
- mastery scoring;
- one note per concept;
- mandatory module or semester ownership of notes;
- mandatory `updated` timestamps;
- a database or server;
- dependence on Obsidian or another proprietary interface.
