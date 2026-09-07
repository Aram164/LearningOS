# Learning OS v3 — Architecture (Consolidated v3.2)

> Consolidated 2026-07-16; module-first curriculum amendment adopted
> 2026-08-03. This file is the single authoritative architecture; earlier
> packages and the monolithic module registry are migration history.

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

**Partitioned module records**
(`curriculum/modules/<module-id>/module.yaml`): one authoritative record per
module. Academic modules own institution, credits, examination attempts and
grades; skill, project and foundation modules omit academic-only fields. Facts,
not knowledge; modules never contain durable synthesis.

**Curriculum operations** (`curriculum/`): programs/areas, modules, optional
components, units with lecture knowledge maps, module source maps with complete
material options, optional current study maps and stage work, and one resume
pointer. This is operationally canonical and Git-tracked. Durable knowledge
remains under `knowledge/`.

### 2.3 Operationally canonical

- `work/COORDINATION.md` — cross-workspace coordination facts (§10);
- **active workspaces** — one coherent learning effort each (§9).
- **module-owned units and optional study maps** — the study hierarchy;
  knowledge/material maps remain usable without an ordered script, and
  workspaces reference units explicitly and may coordinate several of them.

Operationally canonical means: authoritative while active, but not part of the permanent knowledge model.

### 2.4 Preserved historical context

Completed workspaces are archived whole. Archived workspaces preserve context and provenance but are excluded from normal concept retrieval once durable notes exist. The frozen legacy tree is historical context.

### 2.5 Deterministically generated artifacts

Derived from canonical data; gitignored; may be deleted and rebuilt at any time:

- manifest;
- concept index;
- source index (including crosswalk selector views);
- library view and generated collection views;
- domain atlas (the cross-domain map — ADR-005);
- module views;
- coordination view;
- dependency report and concept map;
- reading room (the human home page composing the other views — ADR-006);
- concept canvas (JSON Canvas of the relation registry — ADR-006);
- Nebula (the Garden lens — ADR-002);
- backlinks;
- health and validation reports.

Generated artifacts must never become canonical inputs.

### 2.6 Agent-computed and disposable artifacts

Produced by the operator through reasoning, never canonical: study plans, source menus, contextual summaries, review suggestions, next-action recommendations, priority orderings, neglect warnings, temporary comparison tables.

---

## 3. Physical layout

### 3.1 Root

<!-- root-tree:begin — GENERATED from system/contracts/perimeter.yaml.
     Do not hand-edit; run `python tools/tree_contract.py --write`. -->

```text
semestercontext/
├── AGENTS.md         role division for Codex and other agents
├── tools/            engineering orchestration; not a LearningOS product surface
├── LearningOS/       the umbrella for every LearningOS component (ADR-014)
│   ├── repository/   the authored repository of record
│   ├── obsidian-ui/  the independent interface repository
│   ├── materials/    books, slides, videos, datasets — addressable as material://
│   ├── projects/     active LearningOS-owned code repositories
│   ├── workbench/    disposable audits, strategy and scratch tooling (ADR-014)
│   ├── archive/      retired, recoverable, non-active artifacts
│   ├── legacy/       the frozen pre-v3 tree and the preserved former Job source (ADR-014)
│   ├── README.md
│   ├── CLAUDE.md     the Claude adapter, reachable from the umbrella
│   └── Plans
└── Stratum/          independent external Git repository; never traversed
```

<!-- root-tree:end -->

> **Placement update (2026-08-27, ADR-014):** `semestercontext/` has two visible
> roots: `LearningOS/` and `Stratum/`. The frozen pre-v3 tree is
> `LearningOS/legacy/`; the source retained after the ADR-013 Job migration is
> `LearningOS/legacy/Job/`. These are recovery/history shelves, not active
> authored data. `Stratum/` keeps its own remotes and worktree and remains
> external code context.

> **Amendment (2026-08-03, ADR-006):** interface layers may exist as further
> `LearningOS/` siblings — first: `obsidian-ui/` (the Obsidian desktop
> interface, its own repository and its own project). An interface layer lives
> entirely OUTSIDE `repository/`, owns presentation and interaction only, and
> consumes canonical state solely through the CLI (`tools/los.py`) and the
> `generated/` views. §17 is unchanged: the system never *depends* on
> Obsidian or any proprietary interface.

Code repositories are neither authored knowledge nor materials; `projects/` is their owned home. A repository is moved there only when the move is safe (paths, remotes, teammates); otherwise its location is documented and it is excluded from the knowledge search space. References use `github://` (remote) or `project://` (local) URIs.

**Placement history (2026-07-16):** LearningOS was initially scaffolded inside
the legacy semester tree for tooling access. ADR-014 completes that cutover by
shelving the frozen tree inside the LearningOS umbrella while keeping the
authored repository and interface as independent Git repositories.

### 3.2 Authored repository

<!-- tree:begin — GENERATED from system/contracts/tree-contract.yaml.
     Do not hand-edit; run `python tools/tree_contract.py --write`. -->

```text
repository/
├── system/                normative prose, contracts, schemas, skills and templates
│   ├── *.md               15 documents — indexed in system/contracts/normative-corpus.yaml
│   ├── adr/               decision records — indexed in the same file
│   ├── contracts/         machine-checked declarations — see contract-register.yaml
│   ├── schema/            stored-record schemas — fingerprinted by data-contract.yaml
│   ├── skills/            agent procedures, one SKILL.md per skill
│   └── templates/         authoring forms — deliberately outside the normative corpus
├── knowledge/             canonical notes and the concept registries
│   ├── notes/             one folder per domain; buckets grow with authoring
│   ├── attachments/       handwritten originals and images, one folder per note
│   └── garden/            the exploratory layer (ADR-002); no schema, never canonical
├── curriculum/            programs, modules, units, study maps and stages
│   ├── programs/          active areas and quarantine boundaries
│   ├── modules/           module.yaml, source-map.yaml and units/<unit-id>/ beneath each
│   └── quarantine/        excluded content, boundary index only
├── records/               frozen compatibility inputs and the materials manifest
├── sources/               the source registry and its collections
│   ├── registry/          partitioned source records
│   └── collections/       shelves and topic packs
├── projects/              first-class Projects — registry and relations
│   ├── registry/          one record per project
│   └── relations/         project-to-record relations, authored not inferred
├── operations/            the transaction ledger and everything the gateway writes
│   ├── transactions/      one receipt per applied transaction
│   ├── gateway-requests/  request envelopes
│   ├── ai-actions/        AI action state; requests and deliveries are gitignored
│   └── migrations/        applied-migration provenance
├── migration/             migration state, preserved originals and reports
│   ├── backups/           pre-migration copies, retained
│   ├── reports/           what each migration did
│   ├── adr-007/           originals preserved through the ADR-007 library retaxonomy
│   └── curriculum-v2/     the module-first conversion — map, report and originals
├── work/                  the coordination layer and its queues
│   ├── inbox/             the drop-anything home; the operator routes what lands here
│   └── active/            one folder per active workspace, each with a CONTEXT.md
├── archive/               completed workspaces, retained and never deleted
│   └── workspaces/        one folder per year
├── generated/             gitignored, rebuildable; shape declared by manifest-contract.yaml
├── bases/                 installed Obsidian Bases shelves (ADR-006); gitignored
├── tools/                 the operator CLI and the learning_os package; see tools/README.md
└── tests/                 the test suite and its frozen format fixtures
```

<!-- tree:end -->

### 3.3 File-saving conventions

Where every artifact physically lands, and what it is named. The user should never have to make a filing decision; these rules make filing deterministic so the operator (or a plain script) can always do it.

| Artifact | Physical location | Filename rule |
|---|---|---|
| Durable note | `knowledge/notes/<bucket>/<note-id>.md` | filename = ID + `.md`, always |
| Handwritten originals, photos, diagrams | `knowledge/attachments/<note-id>/` | `page-01.jpg`, `page-02.jpg`, … |
| Concept registry | `knowledge/concepts.yaml` (partitionable to `knowledge/concepts/*.yaml`) | fixed |
| Relation registry | `knowledge/concept-relations.yaml` | fixed |
| Source registry | `sources/sources.yaml` (partitionable to `sources/registry/*.yaml`) | fixed |
| Source collections (catalogues or topic packs) | `sources/collections/<name>.yaml` | kebab-case; `collection_kind` distinguishes broad catalogues from narrow packs |
| Thematic navigation groups | `curriculum/thematic-groups.yaml` | fixed registry; stable IDs and explicit display order |
| Program/area record | `curriculum/programs/<program-id>.yaml` | filename = program ID |
| Module record | `curriculum/modules/<module-id>/module.yaml` | one partition per module |
| Module source map | `curriculum/modules/<module-id>/source-map.yaml` | fixed inside module |
| Unit | `curriculum/modules/<module-id>/units/<unit-id>/unit.yaml` | one owning module |
| Optional current study map | beside its unit as `study-map.yaml` | at most one current map per unit; absent until an ordered path is wanted |
| Stage work | `<unit>/stages/<stage-id>/{notes.md,attachments/}` | stage-owned and Git-tracked |
| Unit session note | `<unit>/notes.md` + `<unit>/attachments/unit-note-*` | append-only learner note created after one or more stages; stage files remain compatibility inputs until migration |

Shared stage material descriptions are owned by the existing module source-map
route. A stored study-map resource can name `material_ref: {route_id, inherit}`
instead of repeating selected fields. The explicit field list preserves absent
fields and stage-specific overrides; priority, action kind, resource identity,
feedback and progress stay stage-owned. The loader expands references within
the same module and unit, refusing missing or ambiguous routes and overlapping
inherited/local fields. Runtime consumers and manifest v9 retain their complete
expanded shape. Editing context exposes the compact shape with its route
definitions once; ordinary state saves preserve that storage form.
| Legacy module snapshot | `records/modules.yaml` | compatibility/migration only |
| Coordination facts | `work/COORDINATION.md` | fixed |
| Quick capture (anything, unprocessed) | `work/inbox/` | any name; the operator routes |
| Workspace operational files | `work/active/<workspace-id>/{CONTEXT.md, scratch/, inputs/, outputs/}` | scratch is free-form |
| Archived workspace | `archive/workspaces/<year>/<workspace-id>/` | moved whole, unchanged |
| External material with a registered source | `LearningOS/materials/<area>/…/<slug>/` (topic tree) | `material://<source-id>/…` resolves via `materials/.flat/source-<id>` symlinks |
| External material not yet registered | `LearningOS/materials/_unsorted/` | temporary; registered then moved |
| Code repositories | `LearningOS/projects/<name>/` | untouched internally |
| Generated outputs | `generated/` | fixed names, gitignored |

**Rules:**

1. **A note's filename is always `<note-id>.md`.** IDs never change, so filenames never change; only the bucket folder may change on a move. Identity still lives in frontmatter — the filename is a derived convenience the validator enforces, never the identity itself.
2. **Buckets are the seven listed** (decision 2026-07-16: `algorithms/` added for CS-theory content — CLRS-style material fits neither mathematics nor programming). A new bucket requires an ADR; buckets are routing neighborhoods, never taxonomy.
3. **Attachments are canonical user artifacts**, not materials: handwritten scans and photos live *inside* the authored repository under `knowledge/attachments/<note-id>/`, are Git-tracked, and are referenced from the owning note's `attachments` frontmatter as repo-relative paths. Books, slide packs, and videos are never attachments — they are materials. The user may periodically prune old scans to reclaim space once transcriptions are reviewed; the operator never deletes originals on its own initiative.
4. **Materials are identified by source, placed by topic** (amended 2026-07-17, user decision). Every registered source with local files owns exactly one folder, physically located in the human topic tree (`ML/`, `Math/`, `CS-Theory/`, `Books/` shared library, `Programming/`, `Degree/`). Identity remains id-based: `materials/.flat/` carries one `source-<id>` symlink per source folder so every `material://<source-id>/…` URI resolves unchanged; registry records never encode physical positions. The tree, `.flat/`, and per-module `SOURCES.md` lists are maintained solely by `tools/build_materials_tree.py` (PLACEMENT map = single source of truth; moving a folder = edit map, re-run). Unregistered dumps land in `materials/_unsorted/` until registered.
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
| Thematic group identity and display order | `curriculum/thematic-groups.yaml` |
| Module thematic placement | Owning partitioned `module.yaml` (`thematic_group_ids`) |
| Source thematic placement | Explicit source metadata plus canonical module/collection relationships, resolved once in the generated manifest |
| Collection kind, thematic placement, order and topic-pack purpose | Owning `sources/collections/<name>.yaml` |
| Module identity, kind, area, unit order, components | Owning partitioned `module.yaml` |
| **Exam dates, registrations, withdrawals, sittings, grades** | Academic module's `module.yaml` (`attempts`) |
| Unit scope, component, status, current map, artifact references | Owning `unit.yaml` |
| Module-specific source roles and unit routes | Owning `source-map.yaml` |
| Ordered stage work, feedback, detours, shelving state | Owning `study-map.yaml` + stage folder |
| Global resume convenience | `curriculum/resume.yaml` |
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

**Thematic navigation rule:** thematic groups are routing neighborhoods, not a
second concept ontology. The registry owns group identity/order; modules and
collections declare membership explicitly. Source placement is projected by
the core from direct source metadata and those canonical relationships. A UI
reads the resolved IDs and never guesses from titles, paths or identifiers.

**Collection-kind rule:** a `catalogue` is a broad Library source view. A
`topic-pack` is a narrow, manually ordered collection with one explicit
`purpose`; it is not a source type and must not clone a complete module source
set.

**The deadline rule:** exam dates exist canonically *only* in the owning
academic module's `module.yaml`. A workspace `deadline` is for non-exam
deadlines owned by that effort (project submissions, peer reviews).
`COORDINATION.md` never restates either; generated views merge them.

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

- exam dates or sittings (owned by the academic module's `module.yaml`);
- workspace statuses or lists (owned by workspace frontmatter; merged views are generated);
- computed recommendations, priority orderings, or neglect warnings (agent-computed, disposable).

The dashboard is `generated/coordination-view.md`, assembled from: the exam
spine in partitioned academic modules, statuses/deadlines/next actions from
workspace frontmatter, the facts in `COORDINATION.md`, and neglect signals
computed from Git timestamps.

**Rationale:** the v2 brain drifted because it manually restated facts owned elsewhere. The coordination layer stays drift-proof only if it remains a small facts file, never a dashboard.

---

## 11. Module records

Each `curriculum/modules/<module-id>/module.yaml` owns that module's
administrative reality:

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

## 14A. Module-first curriculum model

The default active program is the current Bachelor's. Skills,
Thesis/Projects, and Job are active non-semester areas. Job learning uses
ordinary modules under `program-job`; its badge or section is presentation, not
a data boundary. Master's Planning is prospective and operationally
quarantined. Archive preserves completed semesters and work.

Module `kind` is `academic`, `skill`, `project`, or `foundation`. Only academic
modules may be required to carry institution, code, credits, semester, and
examination facts. Components are structured records with stable IDs; the
combined M2 module therefore owns one examination while SaD and Analysis units
route to separate component IDs.

A unit is a `lecture`, `topic`, `lecture-cluster`, `milestone`, `exam-block`, or
`bridge`. It owns scope, ordering, state, its lecture knowledge map, actual
learner source selections, an optional current-map reference, and stable IDs of
durable artifacts. The state vocabulary is
`needs-map`, `not-started`, `ready`, `active`, `paused`, `ready-to-shelve`, and
`complete`. A clustered unit is valid; the model must not invent individual
lectures when the preserved plan intentionally spans several.

A unit does not require a study map. Its knowledge map and complete material
menu remain useful before any study order is chosen. When the learner wants an
ordered, progress-tracked path, the unit may have at most one current study
map. Git preserves prior forms rather than a pile of competing active scripts.
The optional map owns ordered stages, its
current stage, source-plan provenance, explicit prerequisite detours with a
return stage, and shelving proposal state. A stage owns its objective, state,
done-when evidence, exact source actions/locators, scope triage, working note,
attachments, source-use feedback, and completion date. There is deliberately no
canonical session entity.

Source relationships have four distinct owners:

1. the global source record owns identity, location, authorship and contextual
   pedagogical evaluations;
2. the module source map owns why/when a source is used in that module, its
   role and priority; each rich unit route owns one lecture-specific material
   option—format, angle, covered knowledge nodes, depth, scope status, and exact
   locator;
3. the unit owns the learner's actual selections against the complete menu;
4. an optional stage owns the small watch/read/practise/reference action and
   locator for an ordered personal path.

The lecture knowledge map is not a timetable. Its stable nodes describe the
ideas taught and its `builds_on` edges expose prerequisite structure. Rich
source routes connect materials to those nodes. Interfaces group these options
by format and show their different angles; they do not infer one preferred
sequence from source priority. A study map is a personal operational projection
over chosen options, never the authority for which materials exist.

**Resource-level scope triage (data contract v2, 2026-08-08).** A stage resource
may carry its own optional `scope_triage`, drawn from the same four-value
vocabulary as the stage's: `required-now`, `helpful-now`, `deferred`,
`reference-only`. Without it, every resource inside a `required-now` stage reads
as equally mandatory — the lecture deck, the second-opinion video, the optional
depth paper and the preserved bibliography all look the same, so a well-stocked
stage becomes a wall of sources and the triage the architecture already believes
in stops at the stage boundary. With it, one stage renders as *do this / if you
get stuck / depth, not now / preserved*. The field is optional on purpose:
absent means unranked, which is what every v1 record carries, and an unranked
resource must never be treated as deprioritized. Ranking a resource is a
presentation decision about *this stage*; it never edits the source's own
pedagogical evaluation, which stays owned by the source record (owner 1 above).

Stage feedback is personal use evidence. It never silently changes the global
evaluation. A later evaluation change is an approval-gated proposal.

Workspaces retain their independent lifecycle and coordinate curriculum work
with explicit `program_ids`, `module_ids`, and `unit_ids`. Naming and prose are
never used to infer v2 relationships. The current resume pointer is generated
as a convenience and cannot hide any module, unit, or map.

`curriculum/quarantine/index.yaml` is the only normally loadable record at the
Master's boundary. The loader, validator's normal scan, manifest, bootstrap,
active counts, recommendations, and default search exclude quarantined content.
Promotion begins only when the future program actually starts: select the
module deliberately, migrate its administrative facts into an active program,
register only adopted resources, create units from confirmed scope, validate,
and regenerate. Nothing is promoted merely because it was prospective.

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
9. Exam dates, registrations, withdrawals, and grades exist canonically only
   in the owning academic module's partitioned `module.yaml`.
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
20. Every unit belongs to exactly one module; an optional component belongs to
    that same module.
21. A unit's knowledge map and complete material menu do not require a study
    map. If a unit has a current study map, it has at most one, and that map's
    current stage is one of its own ordered stages.
22. The resume pointer is optional convenience state and never filters the
    curriculum. It reports the last stage left open — *where you stopped* — and
    is never, on its own, an answer to *what to do next*. An interface that
    labels both with one word ("Continue") destroys a distinction the core is
    careful to keep: show "Resume where you left off" and "Planned next"
    separately, and let them disagree, because they legitimately do.
22a. `unit_order` is an ordering, not a claim that every entry is the same kind
    of thing. Each unit carries `kind` (`lecture`, `topic`, `lecture-cluster`,
    `milestone`, `exam-block`, `bridge`), the manifest projects it, and
    interfaces must render it. Non-`lecture` kinds are shown as what they are or
    grouped apart — never silently presented as another lecture and never
    silently dropped, because a unit that no surface lists is a unit that does
    not exist.
23. Workspace-to-module/unit joins are explicit in v2; interfaces never infer
    them from names or prose.
24. Future Master's Planning content never enters the normal manifest; only its
    declared boundary record may appear. Job learning is ordinary canonical
    learning under `program-job` and participates in the normal manifest,
    search, recommendations, AI actions, and inter-module concept system.
    Sibling code repositories such as Stratum remain external: they are never
    indexed or validated and are inspected only when the current task needs
    exact code context. Cross-module relations are recorded after learner
    confirmation, never pre-populated speculatively.
25. Interface writes use action-specific, snapshot-checked gateway commands;
    no interface writes canonical files directly.
26. A learning-session commit stages only its action ledger. Unrelated files,
    including untracked Canvas files, are never absorbed.

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

## Gate B — transactional canonical writes

Every declared canonical mutation now passes through `TransactionService`.
The service applies one bounded write set, checks artifact-level expected
revisions, validates the resulting repository, republishes disposable views,
and records exactly one append-only receipt under
`operations/transactions/`. A failed stage rolls the complete write set back.
Interfaces discover the executable catalogue in
`system/contracts/capabilities.yaml`; they do not invent write paths.

Artifact revisions are coordination tokens, not replacements for Git history.
Revision zero is implicit for authored records that have not yet been changed
through the transaction service.

## First-class Projects

Projects live under `projects/registry/` and are independent from curriculum
modules. A project may have no fixed structure, a linear structure, parallel
workstreams, or nested steps. Project relationships are explicit records under
`projects/relations/`; aliases preserve old deep links during compatibility
gates. The current manifest-v5 projection exposes Projects together with
Core-owned Review and Garden state. Projection changes remain producer-owned
and must be mirrored in the UI contract lock in the same release.
