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
deadline:              # non-exam operational deadline only; exam dates live in the owning academic module.yaml
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

**Source-completeness gate (mandatory):** before importing a plan, enumerate
every learning source named by its authoritative templates, bibliographies,
course artifacts, and preserved inputs. Every item must retain a reachable
locator and an explicit disposition: selected for a unit/stage,
`reference-only`, or deferred with a reason. A collection may preserve a large
bibliography, but its selected entries still need exact stage resources. Never
use the number of registered source IDs as evidence that the underlying source
inventory is complete; never silently drop a source because it is inconvenient
to model.

**This gate binds the operator, never the learner (added 2026-08-08).** It is
discharged once, at plan-creation time, and its output is the *plan*. It must
never be copied into a stage's `done_when` as a study task — a learner gate that
says "disposition every curated paper" converts the operator's bookkeeping into
hours of the learner's exam time, which is exactly the burden this system exists
to remove. Preserve every source in the plan; ask the learner only for the
sources the stage's objective actually needs. (Regression fixed in the AMLS
integrate stages, where all 13 carried this clause verbatim.)

**Wire on use (ADR-005):** whenever an already-registered source is actually
used, cited, or recommended in a session and still has no concept-linked
evaluation, add the minimal stub *then* — the concepts it serves, its roles,
one strengths line. A source without a concept link is invisible to concept
retrieval no matter how good it is. Debt is repaid at the moment of use, never
as a bulk backfill (bulk passes invent judgments); the current debt is listed
in `generated/reports/health.md`.

**Prospective Master's menus:** all prospective menus and their planning
context are quarantined under `curriculum/quarantine/masters-planning/`. They
are not current module use, bootstrap input, or default-search content. If the
Master's actually begins, promotion is deliberate: select a module, create its
active partition under the new program, register only adopted resources, build
units from confirmed scope, and validate.

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

Learner evidence (Aram's own results) is append-only and takes the direct
path: `los observe <requirement> --activity exercise --result partial
--condition unfamiliar-example --note "..."`. The terminal session is the
approval — snapshot and revision guard are taken under the operator lock,
never asserted by the caller — because the author is the ground truth
about himself and the ledger carries a tested `--supersedes` correction
path.

**Conditions are claims, and an absent one is never a quiet yes.** A condition
can be recorded three ways and they are three different facts:
`--condition X` says X held, `--condition-not-met X` says X did not, and
saying neither leaves it *unknown*. The two lists are disjoint, and intake
refuses a record that claims both.

The interpreter reads a negative result four ways, and keeping them apart is
the point. Carrying every condition the target declares makes it a *failure of
this target*, which resets the successes before it. Naming one of them as
not met makes it *a different situation* — it bears on something else, so it
resets nothing and leaves nothing open. A different `requirement_sha256` makes
it *stale*, about a question that has since changed. Anything else is
**unresolved**: a report of difficulty against this target that does not say
whether the target's conditions held. An unresolved result withholds the
satisfied verdict and asks; it does not infer "unfamiliar", "uncued" or
"unassisted" from a missing flag, and it does not call the work fragile
either, because that would assert a breakdown nobody recorded.

**A difficulty resets the evidence basis; it never deletes the history.** The
successes that produced the previous conclusion stop counting toward it, and
the activities among them are *spent*: redoing one is consistent with the
difficulty rather than an answer to it. Settle a difficulty by superseding the
record with the conditions stated either way, or by recording **two distinct
qualified activities afterwards that were not already credited** — which
establishes a new basis without pretending the missing facts were ever known.
Recovering once does not make earlier credited activities available to establish
a new basis after a later difficulty.
The original report stays on the record, and the `demonstrated` reason then
names the exact later activities that justified moving on. Attempts that could
not count are listed rather than silently dropped. This applies to a qualified
failure as well as to an unresolved report: the defect is evidence that
predates the difficulty answering it, and that is the same either way.

`los observe` names the unstated conditions, both ways to state them, and the
exact `--supersedes` line; the session output carries the same sentence.
Until 2026-09-13 the unresolved case was discarded in silence — a partial
result filed through this very command without `--condition` flags left the
requirement reading `demonstrated`, `satisfied`, no next steps (audit
`workbench/audits/synthetic-learner-2026-09-12`, F02) — and until the review
that followed, repeating one already-credited activity cleared the report
(review `workbench/audits/repair-review-2026-09-13`, R1/D4).

Assessment proposals distinguish reviewed content from the learner's actual attempt.
A stage resource's `independent_evidence` review must match the current
`requirement_sha256` and `activity_sha256` returned by `runtime-session` in
`session.resource_reviews`. The activity binding hashes the exact local file
and its route identity, locator and authored prompt. A changed target, file or
scope requires review again. Both current-template and legacy maps accept the
same review shape. Unbound older records remain readable as practice.

For example, a reviewed resource carries `reviewed_by: codex`,
`reviewed_on: '2026-09-13'`, `verified_conditions: [unfamiliar-example,
no-explicit-clt-cue]` and the two exact SHA-256 values from the current proposal.
Those condition names mean the prompt *can support* such an attempt, not that
this learner was unfamiliar or unassisted. Record actual conditions separately.
A reviewed empty condition list is an explicit negative suitability verdict.

Without a current suitable assessment, `plan_status` is `blocked`, but usable
reading and practice remain in `steps`, labelled as practice. A required missing
asset disqualifies the whole assigned activity as assessment; its precise part
and source are named. It does not imply all paper work is impossible.

Use exact route IDs as observation activities when working on mapped tasks.
Recorded attempts establish familiarity; explicit prior exposure can also be
supplied as `--context-json '{"exposed_resources":["route-example-solutions"]}'`.
The runtime checks the material-owned `exposes_solutions_for` relationship
across those reports and the proposed steps, including structural replacements
in either direction. Merely opening a file records no reading or exposure.
The operator must carry forward reported exposure or record the actual attempt;
an unreported encounter remains unknown, never a verified lack of exposure.

`direct-user-gesture` is admitted for a closed, named set, and the test is
what the write *is*, not which process sent it: **the learner's own study
activity, or his own choice among material someone already authored** —
progress, his prose, his files, his experience of a resource, his questions,
his selections — bounded to one unit, stage or workspace and guarded by exact
artifact revisions.

A second, narrower set carries the same approval kind **only over the `ui`
channel**: the four workflows where the application shows the exact change
before a deliberate Save or Apply — `concept.relations.change` (ADR-017's
hand-authored connections), `review.prepare`, `review.apply`, and
`unit.map.import` after its no-write `--check` preflight. That Save is the
explicit approval those contracts already required. It is not a second
approval protocol and not an extra confirmation dialog, and the `ui` label is
provenance inside this trusted local application rather than proof a human was
present; the guards that actually protect canonical state — exact previous
rows, registry and artifact revisions, the snapshot, duplicate/endpoint/cycle
checks, exact-byte binding, the preflight — are unchanged. Choosing a file is
not approval to import it; running the preflight and then applying those exact
bytes is.

Everything else is admitted from no channel at all: module plans, route
patches, note revision and evidence, material synthesis, AI-action delivery,
identity migrations. Those keep the full GatewayEnvelopeV2 ceremony through an
approved operator request, and an agent-origin envelope claiming a gesture for
*any* capability — including the four reviewed-UI ones — fails closed.

Both sets live in `system/contracts/capabilities.yaml` (`admission:` and
`admission_channels:`) and `tools/learning_os/commands/capability.py`
(`GESTURE_ALLOWLIST`, `UI_REVIEWED_ALLOWLIST`); the contract describes the
policy, the Python sets enforce it, and `tests/test_observation_gesture.py`
fails when they disagree. An interface keeps its own copy — the Obsidian UI's
is `UI_GESTURE_CAPABILITIES`, checked against this one by its
`scripts/check-contract.mjs`. Refusals name the route back to a permitted
write rather than the approval kind: until 2026-09-13 the list held only the
three writers that existed when it was introduced, while the installed UI
drove eleven more through the same gesture, and four ordinary study actions
died in front of the learner with
`direct-user-gesture is not admitted for detour.create` (audit
`workbench/audits/synthetic-learner-2026-09-12`, F01); the reviewed-UI set was
added after that repair refused the Atlas connection editor a current ADR
requires (review `workbench/audits/repair-review-2026-09-13`, D1).

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

If the user states an operational fact in conversation ("I'm skipping M2,
writing the 2. Termin"), route it: the deferral to `COORDINATION.md`, the
attempt change to that academic module's partitioned `module.yaml`.

## 10. Record a module event

On registration, withdrawal (Rücktritt), sitting, or grade:

1. append or update the attempt in the owning academic module's `module.yaml` (`termin`, `date`, `result`, optional `grade`);
2. record known available sitting dates/ranges and Anmeldung windows as
   structured `examination.sittings` / `examination.registration_windows`
   facts in that same module; attempts still record what Aram actually chose;
3. update module `status` when warranted;
4. rebuild module and coordination views.

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
- `coordination-view.md` — exam spine (from partitioned academic modules) + workspace statuses/deadlines/next actions (from frontmatter) + coordination facts + materials-queue counts (`materials/_unsorted/`, `materials/_duplicates-for-review/`) + Git-derived neglect signals;
- `dependency-report.md`;
- `concept-map.md` — Mermaid rendering of the prerequisite graph (`requires` + `builds-on`), the visual twin of the dependency report;
- `backlinks.json`;
- `nebula.md` — the Garden lens (ADR-002) — and `domain-atlas.md` — the cross-domain map (ADR-005);
- `reading-room.md` — the human home page (ADR-006): exam spine, workspace next actions, recently changed notes, queues, and review-adoption counts, each a link into the deeper view. Interface layers open this file first;
- `concept-canvas.canvas` — JSON Canvas rendering of the relation registry (ADR-006): concept cards with note links, labelled colored edges, prerequisite-depth layout. Obsidian renders it natively; any JSON Canvas tool can read it;
- health report (`reports/health.md`, incl. review & evidence adoption);
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

1. **Module record first.** Ensure the module has one partition at
   `curriculum/modules/<module-id>/module.yaml` and record registration
   (workflow 10). A merely prospective Master's choice stays quarantined; it is
   not an active `planned` module.
2. **Promote only adopted sources.** If a quarantined menu exists, register only
   resources selected for the confirmed active module. Build its module source
   map with roles, reasons, priority and unit routes; do not promote the whole
   prospective sea.
3. **Open the first workspace(s).** Create one workspace per distinct effort (workflow 1) — not one per module. A combined module examined under a single grade may still be one exam-prep workspace; an independent project gets its own. A course is not a continuous effort, so `standing: false`.
4. **Wire dependencies, if any.** If the new effort waits on or feeds another, record that in `COORDINATION.md` Dependencies (workflow 9). No exam dates here — they live in the owning academic module.
5. **Rebuild and validate** (`python tools/generate.py`, then `python tools/validate.py`).

Check before creating: never open a workspace before its module record exists, and never mint a second record for a module already present.

## 19. Close a module

A module ending is larger than archiving one workspace (workflow 11): it settles the administrative record, may retire several workspaces, and confirms the durable knowledge survived. Use this only when the module is truly done; if a later attempt is still ahead, it is carrying, not closing — use workflow 20.

When a module is finished — its final attempt sat, or abandoned:

1. **Settle the record** in the owning partitioned academic `module.yaml` only
   (workflow 10). Record the final sitting or submission on the attempt
   (`result: passed`/`failed`). When the grade posts, record it and set
   `status: completed` (or `dropped` if abandoned); while a grade is pending,
   preserve that administrative state explicitly.
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
5. **An exam, registration, or grade fact** → the owning academic module's
   `module.yaml` (workflow 10) — never anywhere else.
6. **A concept or relation worth registering** → workflow 4 or workflow 5.

When an item is genuinely ambiguous, prefer capturing it into the most likely workspace's `scratch/` over guessing a canonical home (least destructive, then ask); Aram never makes the filing decision — the operator does. Rebuild generated outputs once any registry changed.

## 22. End a session

Any learning session that used guarded mutation commands ends deliberately:

1. save pending stage work;
2. run `los session-end` without a commit message; it validates, regenerates,
   and shows session-owned files separately from unrelated changes;
3. review that exact list;
4. optionally rerun with `--commit-message`; only the ephemeral gateway ledger
   is staged, and the three protected Canvas names are unconditionally removed;
5. use `--push` only through the approved repository workflow.

Do not commit on every keystroke. A session is not a canonical entity; its
ledger lives in temporary storage only long enough to guarantee exact staging.
If a commit or push fails, report it immediately and keep unrelated changes
isolated.

## 23. Process a lecture

The unit is the module-owned study object between module and stage. For
university lectures, **slides as taught are the scope authority**: never scope
from textbook chapter titles or keyword matches. A topic, milestone,
lecture-cluster, exam-block, or bridge uses the same unit interaction with its
own confirmed scope source. Every new or revised module plan follows
[`PLAN-CREATION-SOP.md`](PLAN-CREATION-SOP.md); its coverage audit, templates,
no-write preflight, snapshot guard, and acceptance gates are mandatory.

1. **Materials in.** Slides/recordings and every accompanying reading list or
   bibliography land in the materials tree via workflow 6a (`material://` on
   the module's source record); never into the authored tree. Run the mandatory
   source-completeness gate before scoping.
2. **Scope pass.** Read the deck; list the concepts actually taught; check
   the concept index for what is re-covered (re-covered → "revise via
   existing note", not new study steps).
3. **Coverage and granularity pass.** Complete the item-by-item local/web audit,
   reconcile current and prior-year materials by contents, and give every
   ordinary lecture its own unit and knowledge map. Connect every reviewed
   source through rich lecture routes carrying format, angle, coverage, depth,
   scope, and exact locator. Record duplicate, deferred, off-scope, and
   unresolved items rather than omitting them.
4. **Package and preflight.** Build from
   `system/templates/module-plan-import.template.yaml`; run
   `module-plan-import ... --check`; fix the package until the shadow validation
   passes with zero canonical writes, then apply once with the current snapshot.
5. **Durable artifacts as canonical notes** (workflow 3), one per purpose,
   linked to concepts and sources. Put only their stable note IDs on the unit:
   - the lecture reference → `role: reference`;
   - drills → `role: exercise-bank`;
   - a self-test → `role: mock-exam` (difficulty ≥ the real exam).
6. **Choose before sequencing.** Browse the complete material menu by format
   and explanatory angle. Record only the learner's actual choices in
   `source_selections`; source-map priority is not a mandatory order.
7. **Optional personal path.** Create `study-map.yaml` only when ordered
   progress tracking is useful. It may use only chosen material, must preserve
   its provenance, and never replaces or truncates the complete menu.
8. **Work stage by stage when a path exists.** Exact actions and locators, done-when criteria,
   exact resources, feedback and optional detours stay with the stage. Existing
   stage working notes and attachments remain compatibility inputs. The app's
   primary note action appends one learner-authored session section to the
   unit's `notes.md` after the relevant stages; the note is never required to
   complete a stage. Handwritten originals remain faithful until shelving.
9. **Shelve by review.** Optional stages may remain; apply only selected
   durable changes and preserve stage provenance.
10. **Validate, regenerate, test, and diff-review** against the coverage audit.

## 24. Turn the semester

Composite: the boundary ritual at a term's end (or before a new term's
registrations). Pure orchestration — every step is an existing workflow:

1. **Walk the term's partitioned academic modules**: each one is either
   truly done → close it (workflow 19), or something outlives it → carry it
   (workflow 20). No module skips this fork.
2. **Harvest the Garden** (CLAUDE.md §14): promote the ripe, prune the dead,
   let the rest gestate.
3. **Prune operational residue:** `COORDINATION.md` mentions no closed module
   (workflow 19 step 4); collections drop entries that served only the closed
   term (workflow 6b); the inbox is empty (workflow 21).
4. **Plan forward:** newly chosen modules enter via workflow 18 (record →
   promote menu → workspaces → dependencies).
5. **Rebuild, validate, commit, push** (workflow 22) — the semester turns in
   one reviewed commit.

## 25. The two-layer operating model (ADR-006)

Adopted 2026-08-03 (Aram). Day-to-day operation does not change with the
Obsidian layer installed:

1. **Aram operates as usual** — he talks to the operator, captures into the
   inbox, studies, decides. He never files, never rebuilds, never edits YAML.
2. **The operator writes** — canonical edits land in the repository under
   this document's workflows, and every session that touched canonical files
   ends with §22 (validate → commit → push). The post-commit hook rebuilds
   `generated/`.
3. **Obsidian presents and delegates** — it reads only the atomic manifest at
   the version declared by `system/contracts/manifest-contract.yaml`, and
   sends mutations to action-specific CLI commands with snapshot guards. It
   never parses or writes canonical YAML/Markdown. The app remains optional;
   plain files and CLI retain the whole system.

The freshness guarantee of layer 3 is exactly the session-end ritual of
layer 2. If a view looks stale, reload its manifest or press Rebuild; never
edit a generated file.

### Cross-layer contract change checklist

When a Core result is consumed by the interface, change it as one release:

1. declare the result and its producer-owned schema in
   `system/contracts/capabilities.yaml`;
2. validate the complete result before Core emits it;
3. mirror the schema in the UI and make the contract check compare the mirror
   with Core;
4. update the UI's stable typed contract and boundary decoder;
5. add producer refusal, decoder, and cross-repository drift tests.

Contract versions are data. Keep stable source module names and discover the
single versioned lock; do not put the current version in import paths.

## 25a. Revise an existing plan

This section owns the revision procedure; [PLAN-CREATION-SOP.md](PLAN-CREATION-SOP.md)
Gates 0–6 own the acceptance gates. §23 covers a lecture arriving. This covers
the far more common case: a plan that already exists and needs changing — a
locator sharpened, an angle written, a source routed to a stage it was missing
from, a stage's material menu extended.

For one existing material's title, locator, angle, angle detail, URL or vault
path, use the bounded `route.patch` capability. Read `plan-edit-context UNIT_ID
--route-id ROUTE_ID`, then run `route-patch UNIT_ID ROUTE_ID --changes JSON
--check`. To read several routes at once, pass `--route-ids` with 1 to 20
exact route ids: the batch shares the unit snapshot and revision guards,
preserves request order, and refuses atomically. The preflight returns the concrete field diff, affected files,
snapshot, and exact expected revisions. Apply those same changes through a
GatewayEnvelopeV2 for `route.patch`. Core retains full shadow validation,
warning checks, conflict guards, publication and receipts. It synchronizes
exact source-selection guards and identical legacy mirrors; explicit stage
overrides remain local. Changing a route's identity, scope, coverage, source,
or membership still requires the full plan path below.

Stored resources may carry `material_ref` with a route ID and an explicit
`inherit` field list. Core expands these for all learning views and preserves
them during progress, note, feedback and shelving saves. Work from compact
`plan-edit-context` output when revising a map; do not copy a full `inspect`
result into the authored plan. An intentionally different stage explanation
belongs in a local field, removed from the inheritance list.

Existing maps can be compacted without editing content using
`module-materials-compact MODULE_ID --check`. Review its affected paths and
plan hash, then apply `module.materials.compact` through the gateway with
that `plan_sha256`, snapshot and exact revision guards. Conversion must
reconstruct every effective map exactly; ambiguous or independent materials
remain inline. It does not replace the material-coverage audit for new plans.

For structural plan revisions, use the creation/import path:

For one existing lecture, `unit-plan-revise` accepts compact route operations
and the final study map; it uses this same governed import path internally.
The saved-preflight shortcut for both commands is specified in
`PLAN-CREATION-SOP.md` Gates 4–6: `--apply-reviewed-sha256` plus
`--review-report` dispatches the exact envelope prepared at review time,
without refreshing its snapshot, revisions or retry identity.

1. **Draft.** Regenerate the affected maps with
   `tools/assemble_lecture_study_maps.py --out <dir>` when the change is in the
   module source map, or edit a copy of the map when it is not. The assembler
   writes only to its out-directory and refuses the whole batch if any unit
   fails the template or the schema, so the draft is already checked before
   anyone reads it.
2. **Review** the draft as a diff against what is live. This is the step the
   gateway cannot do for you.
3. **Preflight from the CLI.** `module-plan-import MODULE_ID --file … --check`
   when the change touches a module's `source-map.yaml` or several units
   together; `unit-map-import UNIT_ID --file …` when it is one unit's
   `study-map.yaml`. Both take the id as a **positional**, not `--module-id`.
   `--check` runs the contract, ordering, routing and shadow-repository
   validation and reports `"canonical_files_written": 0`.
4. **Apply through the gateway**, never by writing the canonical file directly
   — either through the saved-preflight shortcut above or an explicit envelope:

   ```bash
   python tools/los.py capability module.plan.import --payload-file envelope.json
   ```

   `module-plan-import … --expected-snapshot` does **not** write. Every
   canonical write refuses when no gateway request is in context
   (`commands/support.py`: *"canonical writes must use GatewayEnvelopeV2;
   direct CLI application is disabled"*), so the bare CLI can preflight and
   nothing more. The envelope carries `schema_version: 2`, `request_id`,
   `idempotency_key`, `capability`, `channel`, `expected_snapshot` (from
   `los.py bootstrap --compact`), `expected_revisions` covering **exactly** every
   artifact the transaction touches — the module plus each unit in the
   package, no more and no fewer — an `approval` whose `subject_sha256` is
   `intent_sha256(envelope)`, and the payload. `approve` never appears in the
   payload; a `file` payload always carries its `file_sha256`.

   `module.plan.import` additionally requires a coverage audit under
   `work/active/` carrying the literal headings `## Local`, `## Linked` and
   `## Completeness`, with all six `plan_contract.checks` true. Start from
   `system/templates/plan-coverage-audit.template.md`.

   For work *inside* a stage — `stage-progress`, `stage-note`,
   `source-feedback`, `detour-create` — this section does not apply; that is
   not a plan revision.

Hand-editing a `study-map.yaml` or a `source-map.yaml` produces a file the
validator accepts and the pre-commit hook passes, so nothing will object — but
it skips the snapshot guard, the artifact-revision check, and the append-only
receipt, and afterwards nothing distinguishes it from a mediated write.
`tools/plan_write_audit.py` measures how much of the plan surface has changed
that way. A migration under `tools/migrations/` is the one legitimate exception,
and it is legitimate because it is recorded.

## 26. Source routing and feedback

Register one global source identity first. Add a module source-map entry only
for its role in that module. Add exact unit selections only for confirmed
scope, then put the smallest actionable watch/read/practise/reference locator
on a stage. Routing one source to two modules creates two joins, never a second
source record. Changing any of that afterwards is a plan revision and goes
through §25a.

Use `source-feedback` for lightweight personal evidence (`helpful`,
`too-advanced`, `wrong-perspective`, `useful-for-derivation`,
`useful-for-review`, or `skipped`). Feedback remains on that stage. If it
suggests a global evaluation change, prepare a separate reviewable proposal.

**Locator page grammar.** A locator that names pages says which numbering it
means, because a deck's printed slide number routinely differs from its
position in the file. Write `PDF pp. 20-22` or `physical PDF pp. 214–220` or
`physical pp. 14–19` when you mean positions in the file; interfaces open at
that page, or carry it as an instruction when the viewer cannot be positioned.
A bare `pp. 20-22`, a `§4.3` and `slides 5-20` are printed labels or section
numbers, and are deliberately *not* read as file positions: an interface that
guesses lands the learner confidently on the wrong page, which is worse than
landing on page 1. The consumer is `pageDestination` in the Obsidian UI's
`src/infrastructure/resource-target.ts`; until 2026-09-13 nothing carried the
page at all, and opening a stage's lecture showed page 1 of 38 (audit
`workbench/audits/synthetic-learner-2026-09-12`, F07).

**Two kinds of readiness.** That a material opens is not that its activity can
be done. A route whose task needs supplied files — a dataset to analyse, a code
template to fill in — declares them in `requires_assets`, each with the part it
belongs to and where the exact file comes from. The session then keeps the
route and names the parts that cannot be attempted, instead of reporting the
whole assignment ready: Blatt 4 Aufgabe 3(b) needs
`International_Education_Costs.csv` and an `aufgabe3.py` template from Moodle,
the source map had already recorded their absence in prose, and the proposal
still said ready (F06). Register the exact files through this workflow when you
have them; never substitute a different dataset or template for a named one.

## 27. Promote a future Master's module

Use only after the future program actually begins. Enter the boundary
deliberately, select a confirmed module, create/activate the program and
semester facts without invention, migrate that module's administrative facts,
register only adopted resources, create units from confirmed scope, add
explicit workspace joins, validate, regenerate, and review. The quarantined
originals and migration mapping remain Git-tracked. No bulk promotion is
allowed.
