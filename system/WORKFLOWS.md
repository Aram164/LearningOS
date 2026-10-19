# Learning OS v3 — Workflows (Consolidated v3.1)

## 1. Start a workspace

Procedure: [transcript](procedures/start-a-workspace.md).

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

Body sections — `Objective`, `Current Scope`, `Open Questions`, and `Next Action` are required; `Temporary Source Menu`, `Current Plan`, `Durable Notes`, and `Deferred` optional. Update `Next Action` only through the `workspace-next-action` capability envelope (§25c) — never by editing CONTEXT.md directly.

**Scope triage:** when the effort's topic expands into prerequisites and side-paths, label items *required now / helpful now / defer / reference only* (in `Current Scope` and on the source menu). Accepted "not now" decisions go under `Deferred` with one line of reasoning — a deferral is a recorded decision the system can replay, not a thought to re-have.

If the active count reaches 8+, the validator warns: finish or archive something first.

## 2. Capture temporary material

Procedure: [transcript](procedures/capture-temporary-material.md).

Put fragments, quotations awaiting processing, rough diagrams, temporary source lists, partial calculations, and lecture-specific checklists in workspace `scratch/` or `inputs/`. Temporary capture does not require canonical metadata.

When no workspace is obvious, drop anything into `work/inbox/` — no naming, no metadata. The operator routes inbox items to their deterministic destination (ARCHITECTURE §3.3); the inbox trends toward empty. The write itself goes through a `capture.create` envelope (§25c): the bare `capture --text` command is refused by design.

## 3. Create or evolve a durable note

Durable notes are created only through a gateway capability (§25c) — never by
saving the file directly. Pick the capability by what the note is:

- a source-chapter analysis → `note.analysis.save` (one) or
  `note.analysis.save_batch` (up to 20 under one receipt);
- a learner's recorded question → `atlas.question.save`;
- session scratch promoted in bulk at closure → shelving: `review.prepare`,
  then `review.apply` on explicitly approved items only;
- anything else durable → `note.create` below.

Procedure: [transcript](procedures/create-durable-note.md).

Do not require polish or completeness. A successor that replaces an earlier
note declares `supersedes` in the same `note.create` call, which deprecates
the predecessor atomically (workflow 15).

## 4. Add a concept

Procedure: [transcript](procedures/add-a-concept.md).

## 5. Add a concept relation

Procedure: [transcript](procedures/add-concept-relation.md).

## 6. Add or evaluate a source

Procedure: [transcript](procedures/add-or-evaluate-a-source.md).

Source evaluations are the canonical home of pedagogical judgments — including those narrated in crosswalk notes.

### 6a. Intake of new external learning material (formalized 2026-07-17)

The single path for EVERY new find — course, video, book, blog, paper, tool.
This replaces the legacy LEARNING-RESOURCES intake protocol; there is no other
list to also update.

Procedure: [intake transcript](procedures/add-or-evaluate-a-source.md#review-the-metadata-only-intake).

**Video intake and examination.** At intake, use only the title, publisher,
description and known course or playlist structure to place a provisional
record. A course or playlist is one source with its known videos as titled
child links; a standalone video is its own source. Do not transcribe a backlog.
When a video is selected for actual study, use Gemini Notebook to extract and
examine its content, then verify the relevant claims against the exact video
and timestamps before approving a durable analysis. Save what it covers, what
the learner should use and the evidence through the existing material-analysis
path; correct the provisional shelf if that examination changes the judgment.
The caption-import maintenance tool is not the examination path for this intake.

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

Procedure: [transcript](procedures/record-evidence.md).

Learner evidence (Aram's own results) is append-only and takes the direct
path: `los observe <requirement> --activity exercise --result partial
--condition unfamiliar-example --note "..."`. The terminal session is the
approval — snapshot and revision guard are taken under the operator lock,
never asserted by the caller — because the author is the ground truth
about himself and the ledger carries a tested `--supersedes` correction
path.

Most stages have no requirement target yet: evidence intake is
target-bound, and only a stage carrying a `runtime_target` block produces
a requirement. For those stages `observe` refuses by naming the stage —
never "unknown requirement", which is reserved for a mistyped id (with
suggestions) — and points here. Record the result without credit through
the untargeted ledger instead: seal a `learner.stage-result.append`
envelope (§25c) with the workspace, unit, stage, activity, enumerated
result, and optional assistance, conditions and note. The row lands in
the workspace's `stage-results.jsonl`, shows in `resume` and
`plan-edit-context --stage-id` labelled "no credit", and grants no
ability or requirement credit. When a target is later authored for the
stage — `unit-plan-revise UNIT --file REVISION.yaml --check` with a
`runtime_target` stage patch, then the reviewed apply — those rows stay
visible as context only; they are never retro-credited.

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

<!-- los:reference {"kind": "command", "text": "los observe"} -->
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
channel**: the workflows where the application shows the exact change
before a deliberate Save or Apply — `concept.relations.change` (ADR-017's
hand-authored connections), `review.prepare`, `review.apply`,
`unit.map.import` after its no-write `--check` preflight, and the two
append-only ability records confirmed from Review:
`learner.ability-observation.append`, whose confirmation pointer names the app
request, and `ability.candidate.append`, which carries no evidence. That Save is the
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
*any* capability — including the reviewed-UI ones — fails closed.

Ability IDs are stable. Rename the title without changing the ID. To retire an
identity, retain its registry row with `lifecycle: retired`; its observations
stay readable, but it cannot receive new observations or candidates and cannot
support a current ability through a bridge. Do not delete or reuse the ID.

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

Procedure: [transcript](procedures/update-coordination.md).

If the user states an operational fact in conversation ("I'm skipping M2,
writing the 2. Termin"), route it: the deferral to `COORDINATION.md`, the
attempt change to that academic module's partitioned `module.yaml`.

## 10. Record a module event

On registration, withdrawal (Rücktritt), sitting, or grade:

Procedure: [transcript](procedures/record-module-event.md).

Never record these facts anywhere else.

## 11. Complete and archive a workspace

Procedure: [transcript](procedures/complete-and-archive-a-workspace.md).

No gateway capability currently archives a workspace. Archival requires a
separately reviewed migration; completion in place preserves its evidence.

Standing workspaces (`standing: true`) are exempt from this workflow.

## 12. Generate indexes and reports

Procedure: [transcript](procedures/generate-indexes-reports.md).

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
- health report (`reports/health.md`, incl. review & evidence adoption).

Run `los validate` separately to produce `reports/validation-report.md` after
successful validation. Generation does not produce that report.

Generated files state that they are generated, name the generator version and canonical inputs, and are gitignored.

## 13. Review a note

Procedure: [transcript](procedures/review-a-note.md).

A semantic review is deliberate: update reasoning as explicitly approved; set `reviewed`; preserve meaningful uncertainty; rebuild generated outputs. File modification is not semantic review.

## 14. Move or rename a note

Procedure: [transcript](procedures/move-or-rename-a-note.md).

Preserve the ID; repair explicit path links; keep ID-based references unchanged; rebuild generated artifacts; validate. Path changes never alter identity.

## 15. Deprecate or supersede

Procedure: [transcript](procedures/deprecate-or-supersede.md).

Prefer preservation over deletion. A successor is an ordinary `note.create`
call whose record declares `supersedes: [note-old-id, …]`; every listed
predecessor must exist and is marked `state: deprecated` in the same
transaction. The reverse link is generated, never stored (ARCHITECTURE §5.5).

Concepts: `deprecated: true` + `replaced_by`. Generated indexes mark deprecated records but do not erase them.

## 16. Maintain a crosswalk

Procedure: [transcript](procedures/maintain-crosswalk.md).

## 17. Ingest a handwritten note

The user drops photos/scans into `work/inbox/` (or a workspace `inputs/`) and says what they are. The operator does everything else:

Procedure: [transcript](procedures/ingest-a-handwritten-note.md).

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

Procedure: [transcript](procedures/start-a-module.md).

Check before creating: never open a workspace before its module record exists, and never mint a second record for a module already present.

## 19. Close a module

A module ending is larger than archiving one workspace (workflow 11): it settles the administrative record, may retire several workspaces, and confirms the durable knowledge survived. Use this only when the module is truly done; if a later attempt is still ahead, it is carrying, not closing — use workflow 20.

When a module is finished — its final attempt sat, or abandoned:

Procedure: [transcript](procedures/close-a-module.md).

Do not archive before knowledge is promoted (step 2); doing so strands it.

## 20. Carry work across semesters

Procedure: [transcript](procedures/carry-work-across-semesters.md).

Some efforts outlive a module or a semester: a second exam attempt, thesis preparation, a long project, an unfinished thread. This is decision logic over existing atomic workflows, so a workspace neither becomes immortal nor fragments. When an effort must continue past its module's or semester's end, choose exactly one:

- **Continue the same workspace** when the objective is unchanged and merely unfinished — a `standing: true` effort (degree planning, job), or an exam-prep workspace whose next attempt is still ahead. Nothing moves. Standing workspaces (ARCHITECTURE §9.2) never archive on a semester boundary.
- **Complete and open a successor** when the objective has meaningfully shifted or the old context is spent. Complete the old workspace, keeping it in place if it owns learning paths (workflow 11); create the new one (workflow 1); record the lineage with `supersedes:` on the successor (workflow 15). Durable notes are shared canon already — do not copy them; the successor links the same note IDs.
- **Split** when one workspace has grown two distinct objectives, or the active-count cap (8, workflow 1) forces a division. Open the second workspace (workflow 1), move the relevant `scratch/`/`inputs/`, and note the split in each `CONTEXT.md`.

Record any resulting cross-effort dependency in `COORDINATION.md` (workflow 9). Across all three choices the knowledge layer is invariant — only workspaces, the operational containers, start, stop, or divide.

Worked case: AML's 1. Termin was withdrawn and the 2. Termin (2026-09-30) is still ahead, so `workspace-aml-exam-prep` *continues* (first option); nothing archives until that sitting is written and the module closes via workflow 19.

## 21. Process the inbox

Routing destinations are already deterministic (ARCHITECTURE §3.3); this is the loop that applies them, not a new routing policy. It invents no destinations — each item is pointed at the workflow that already owns it. `work/inbox/` is the zero-friction capture point and should trend toward empty. Process it by taking each item in turn and routing it to its single deterministic destination:

Procedure: [transcript](procedures/process-inbox.md).

When an item is genuinely ambiguous, prefer capturing it into the most likely workspace's `scratch/` over guessing a canonical home (least destructive, then ask); Aram never makes the filing decision — the operator does. Rebuild generated outputs once any registry changed.

Read the inbox through the product, never by catting files: `inbox-list`
names every drop, `search` matches inbox filenames, and `inbox-read NAME`
returns bounded segments of one drop (binary drops refuse — they have no
text read).

Routing is only half the loop: once a drop has reached its destination,
resolve it through `inbox.resolve`, naming where it went. Seal the
envelope (§25c) with the drop's SHA-256 — `inbox-read` reports it as
`content_sha256` — and a non-empty `routed_to` list (note id, workspace
path, source id, receipt id, …). The drop moves byte-identical to
`archive/inbox/YYYY/`; a changed drop refuses, and the receipt names both
endpoints plus `routed_to`. A drop folder resolves whole, or file by
file: `inbox-read FOLDER` lists its files and reports the whole-folder
digest as `drop_sha256`. `inbox-list` reports each file's age, and
`INBOX-STALE` flags each file recursively by its own age.

Agent friction notes are not inbox drops: they live directly in
`work/complaints/` (see its README), so the inbox stays for learner
captures.

## 22. End a session

Any learning session that used guarded mutation commands ends deliberately:

Procedure: [transcript](procedures/end-a-session.md).

A bare review never closes the session: the ledger survives, so step 4 stages
exactly the reviewed list, and running the review twice shows the same list.
To end the ownership window without committing, rerun with `--close` instead:
it deletes only this session's ledger and reports `session_closed: true`.
`--close` with `--commit-message` is a usage error.

Do not commit on every keystroke. A session is not a canonical entity; its
ledger lives in the checkout's private state directory (`<git-dir>/learningos/`,
never committed) only long enough to guarantee exact staging. The ledger
itself is never staged: only the files it records are.
If a commit or push fails, report it immediately and keep unrelated changes
isolated.

Every gateway transaction records its session: the ledger is keyed per
session, and `session-end` lists and commits only its own rows. Name the
session before any write as §25c step 4 describes — a sealed `session_id`,
or `LOS_SESSION_ID` when the shell persists — and the closing `session-end`
(same identity) claims exactly it. Sessions that name
nothing still separate by channel: UI writes (`channel: ui`) never enter an
agent session's ledger, and vice versa. Rows from other sessions are
reported under `other_sessions` with their age and are never staged; rows
older than 24 hours are reported as stale and need `--include-stale` to
stage. An explicit `--close` deletes only its own session's ledger.

## 23. Process a lecture

Execution boundary: [declared fixture limitation](procedures/INDEX.yaml).

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
   what is re-covered with `search` and `related` over the taught concepts
   (re-covered → "revise via existing note", not new study steps; the
   generated concept index is the bulk fallback).
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

Execution boundary: [declared fixture limitation](procedures/INDEX.yaml).

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
path, use the bounded `route.patch` capability. Start from
`plan-edit-context UNIT_ID --route-id ROUTE_ID` for the named route — the
route response already carries the snapshot and revision guards — then run
`route-patch UNIT_ID ROUTE_ID --changes JSON --check`. Reach for the unit
`--brief` only when the route id is unknown or the task needs unit
coverage. To read several routes at once, pass `--route-ids` with 1 to 20
exact route ids: the batch shares the unit snapshot and revision guards,
preserves request order, and refuses atomically. The preflight returns the concrete field diff, affected files,
snapshot, and exact expected revisions. Apply those same changes through a
GatewayEnvelopeV2 for `route.patch`. Core retains full validation,
warning checks, conflict guards, publication and receipts, enforced inside
the transaction on the staged state. It synchronizes
exact source-selection guards and identical legacy mirrors; explicit stage
overrides remain local. Changing a route's identity, scope, coverage, source,
or membership still requires the full plan path below.

Stored resources may carry `material_ref` with a route ID and an explicit
`inherit` field list. Core expands these for all learning views and preserves
them during progress, note, feedback and shelving saves. Work from focused
`plan-edit-context` output when revising a map; do not copy a full `inspect`
result into the authored plan. An intentionally different stage explanation
belongs in a local field, removed from the inheritance list.

Existing maps can be compacted without editing content using
`module-materials-compact MODULE_ID --check`. Review its affected paths and
plan hash, then apply `module.materials.compact` through the gateway with
that `plan_sha256`, snapshot and exact revision guards. Conversion must
reconstruct every effective map exactly; ambiguous or independent materials
remain inline. It does not replace the material-coverage audit for new plans.

The focused route response carries a sibling `claim` status; full unit context
has a route-keyed `claims` map and the brief has bounded counts/actionable rows.
Stage-focused reads do not read claims. Dossier status is live metadata outside
its cached content. Preflight `claims` impact is advisory: it names stale claims
and the next rejudgment command without adding an acknowledgment gate.

Changes to coverage or locator/vault/URL/source-material identity require
per-claim evidence, including `route-patch --claim-evidence JSON`. Keep
quotation-bearing drafts outside Core. Use exact material URIs and explicit PDF
pages or transcript windows; a local claim cannot be downgraded to remote by
removing its binding. Unchanged stale/contested/audit-defective claims may carry
fresh evidence through `unit-plan-revise` without fabricating a content edit.
Fresh unchanged and unrecorded unchanged claims retain the backfill refusal.

For structural plan revisions, use the creation/import path:

Procedure: [transcript](procedures/revise-an-existing-plan.md).

For one existing lecture, `unit-plan-revise` accepts compact route operations
and the final study map; it uses this same governed import path internally.
The saved-preflight shortcut for both commands is specified in
`PLAN-CREATION-SOP.md` Gates 4–6: `--apply-reviewed-sha256` plus
`--review-report` dispatches the exact envelope prepared at review time,
without refreshing its snapshot, revisions or retry identity. When the
reviewed draft is large, `unit-plan-revise … --check --report-out
/scratch/check.json` saves the complete report — the object of review,
apply, and recovery — and prints a compact summary without the sealed
envelope. Bare `--check` output is unchanged; `--report-out` is refused
with apply, `--staged-basis`, in-repository targets, and existing files.

Hand-editing a `study-map.yaml` or a `source-map.yaml` produces a file the
validator accepts and the pre-commit hook passes, so nothing will object — but
it skips the snapshot guard, the artifact-revision check, and the append-only
receipt, and afterwards nothing distinguishes it from a mediated write.
`tools/plan_write_audit.py` measures how much of the plan surface has changed
that way. A migration under `tools/migrations/` is the one legitimate exception,
and it is legitimate because it is recorded.

## 25b. Save a batch of source analyses

One drafts file produces one reviewable staging dir plus the exact
gateway envelope; review both, then submit the envelope unchanged.

Procedure: [transcript](procedures/save-a-batch-of-source-analyses.md).

## 25c. Build a write envelope (GatewayEnvelopeV2)

Every canonical write is submitted as an explicit envelope; the bare
mutating commands (`capture --text`, `note-revise`, …) refuse with exit 2
and explain that GatewayEnvelopeV2 is required and direct CLI application is
disabled (`note-revise NOTE_ID --file REVISED.md` without `--approve` is
refused, and with `--approve` the direct CLI write is disabled; a revision is
applied through a sealed GatewayEnvelopeV2 for `note.revise` — see
[build a write envelope](procedures/build-write-envelope.md)). The first clause may name the action (for example, stage results or
inbox resolve); the common transaction refusal starts with "canonical writes
must use GatewayEnvelopeV2". This is by design, never by accident. This section is the complete
construction recipe — nothing else is needed.

Procedure: [transcript](procedures/build-write-envelope.md).

**Intent hash.** The approval subject covers exactly six fields —
`schema_version`, `capability`, `channel`, `expected_snapshot`,
`expected_revisions`, `payload` — plus `session_id` when the envelope
carries one, and deliberately excludes `request_id`, `idempotency_key`,
and `approval` (request identities are not intent). The sealed session
is intent because it routes the transaction's ledger rows. Canonical
form: `json.dumps(subject, sort_keys=True, separators=(",", ":"),
ensure_ascii=False)` encoded UTF-8, SHA-256 hex, prefixed `sha256:`.
In Python:

Procedure: [intent-hash example](procedures/build-write-envelope.md#step-5-the-approval-subject-is-the-intent-hash).

**Refusal shape.** A refusal answers `ok: false` with
`error: {code, message, retryable, details}`. The code comes from the
refusal's type, never from its message text. `retryable` marks whether the
same approved intent may be attempted again under a fresh envelope
(step 4): a stale guard may, a defective request may not. `details` is
`{}` on most refusals — only the typed subsystem outcomes
(snapshot-guard conflicts, projection, commit, crash-recovery conflicts)
carry machine-readable details. An empty `details` is normal, not a
missing diagnosis: the `message` names the defect.

**Worked capture.** Inbox capture (`§2`) via the envelope route:

Procedure: [capture transcript](procedures/build-write-envelope.md#step-6-submit-the-envelope).

**Sealing helper.** `.venv/bin/python tools/seal_envelope.py --capability NAME
--payload JSON-or-@FILE --key KEY --guards auto` reads the snapshot live,
derives the exact guard set, and emits the sealed envelope above (to
stdout, or `--out` a scratch path — never inside the repo). It performs
steps 2, 3, 4 and 5, minting a fresh `request_id` per run — so seal once
per attempt and keep the output: a retry resubmits that saved envelope,
never a re-sealed one (step 4). The derived guard set is printed on
stderr for the approval record. An explicit `--revision ART=REV` stays
and wins over the derived entry when given. Submit the output via step 6.

## 26. Source routing and feedback

Procedure: [transcript](procedures/source-routing-and-feedback.md).

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

Execution boundary: [declared fixture limitation](procedures/INDEX.yaml).

Use only after the future program actually begins. Enter the boundary
deliberately, select a confirmed module, create/activate the program and
semester facts without invention, migrate that module's administrative facts,
register only adopted resources, create units from confirmed scope, add
explicit workspace joins, validate, regenerate, and review. The quarantined
originals and migration mapping remain Git-tracked. No bulk promotion is
allowed.

## 28. Read an operation (`los operations`)

Procedure: [transcript](procedures/read-an-operation.md).

This is the only surface that explains a write request after the fact.
`los operations` lists recent causal operations (newest first, `--limit`
up to 50); `los operations --request-id ID` explains one request with a
full diagnosis, timeline, and receipt facts. An unknown id writes to stderr
and exits 2: `los: INVALID_REQUEST: unknown request_id` (without `--json`), or
`{"error": {"code": "INVALID_REQUEST", "message": "unknown request_id", "retryable": false, "details": {"reason": "NOT_FOUND"}}}`
(with exit 2 and `details.reason` set to `"NOT_FOUND"`) when `--json` is supplied.

The diagnosis carries three outcomes plus what must still happen:

- `execution_outcome` — what the instrumentation observed
  (`committed`, `rolled-back`, `refused`, `transport-lost`, `unknown`).
  Deliberately the weakest: `rolled-back` means rollback *appeared* to
  complete, which never proves the write is absent.
- `canonical_outcome` — what the canonical store definitely did:
  `COMMITTED` (a receipt verified through the strict resolver),
  `NOT_COMMITTED` (every counted attempt ended in a definitive no-commit
  refusal — `INVALID_REQUEST`, `UNKNOWN_CAPABILITY`, `STALE_SNAPSHOT`,
  `REVISION_CONFLICT`, `OUT_OF_SCOPE`, `AMBIGUOUS_MIGRATION`,
  `VALIDATION_FAILED`, `PROJECTION_FAILED`, `UNCONFIRMED`, the full list in
  `DEFINITIVE_NO_COMMIT_CODES` — or every counted attempt ended in a lone
  `IDEMPOTENCY_CONFLICT`, which retires the request through its own
  resolver rule: the key is bound to a different intent), or `AMBIGUOUS`
  (the evidence cannot decide — an honest answer that keeps the
  recovery record open).
- `projection_outcome` — what re-publication did (`published`,
  `failed`, `skipped`, `unknown`).
- `recovery_requirement` — what must still happen: `none` (settled or
  definitively absent), `verify-observation` (receipt exists, no
  projection observation yet — run `make views` to settle it), or
  `reconcile-exact-request` (ambiguous outcome — reconcile that exact
  request). `needs_attention` is true exactly when this is not `none`.

Settlement rule: a commit settles while the live manifest is at or past
it — the manifest's receipt is at or after the write's — with reason
"live manifest is past this commit". A behind or unknown manifest keeps
`verify-observation`; regenerating views (`make views`) is the
documented settling step. The learner-facing `ui_outcome` is `SETTLED`
(committed, nothing owed), `REFUSED` (definitively absent, nothing
owed), or `BLOCKED` (anything else).

Request ids are caller-chosen and not unique: when one id was reused
across distinct idempotency keys, the explanation names every distinct
request instead of silently covering only the first. `failure_stage`
names the first stage known to have failed (`core.admission`,
`core.snapshot_guard`, `core.revision_guard`, `core.approval`,
`core.replay`, `core.validation`, `core.commit`, `core.receipt`,
`core.projection`, `ui.*`), or null when the operation settled.

## 29. Review a stage's material angle

Procedure: [transcript](procedures/review-a-stage-material-angle.md).

A route describes a material's general contribution; a placement may narrow
that purpose for one stage. Preserve that distinction after reviewing both
texts. The optional resource `angle_review` records `kind: refinement`, the
actual reviewer, date, rationale, and `angle_review_fingerprint` from
`learning_os.derive.validation.plan_rigor`. It is canonical operator evidence; the manifest
continues to publish the descriptions under its existing interface contract.
A refinement attests only to the relationship between those descriptions.

Use `kind: correction` for an actual source-content correction. Cite exact
inspected `material_uri`, `file_sha256`, and physical-page locator in `evidence`.
An exact-file route accepts evidence only from its targets; a broad route
requires an exact file within its source's declared material authority. Remote
unobserved sources cannot supply local byte evidence. Changing the descriptions,
route, stage purpose, placement, or cited source bytes makes the review stale.
Never refresh only its fingerprint to silence the warning.

Draft outside the repository, run `unit-map-import UNIT --file MAP --replace
--check`, review its concrete diff, and submit the content-bound
`unit.map.import` envelope described in §25c. This carries forward learner
state; it grants no ability, evidence credit, or mastery.

## 30. Review exact goal decisions together

Procedure: [transcript](procedures/review-exact-goal-decisions-together.md).

`los goal ID --authorize|--reject|--defer|--close` remains the single-decision sidecar path.
For several explicit IDs, pass each ID as its own argument and add `--check`.
The preview lists every before/after decision and its `reviewed_sha256`.
Apply those same arguments with `--reviewed-sha256` after Aram approves them.
The hash covers the exact IDs, decision, note, revisit date, and existing ledger;
a changed proposal or ledger refuses without a write. Patterns and duplicate
IDs are refused. Only decidable IDs are accepted: a goal in the current scan,
or already in the ledger (a goal that stopped being detected can still be
closed or re-decided); unknown IDs refuse with did-you-mean suggestions
before anything is written, so a batch is all-or-nothing. Detector names,
urgency tiers, and group proximity never grant authority to decide other
goals. `--revisit-on` remains a future date used only with `--defer`; no
batch runs automatically. The decision joins the caller's session ledger —
`session-end` lists and commits it — resolved as explicit `--session-id`,
then `LOS_SESSION_ID`, then the channel.

Authorization records intent and leaves the finding visible; reject needs a
nonempty `--note`. For an audit, prepare the authorization YAML outside Core:
`pool` is the complete currently eligible sorted list of `{claim_id, basis}`
pairs; `pool_sha256` is its full digest; `seed` is 64 lowercase hex digits from
system randomness; `algorithm` is `python-mt19937-shuffle-v1`; `sample` is the
30 pairs returned by the recorded seeded shuffle. The pure reference helpers
are in `tools/learning_os/derive/semantics/claim_audits.py`.

Run `goal AUDIT_ID --authorize --audit-file FILE --check`, review the exact
pool/seed/sample and returned hash, then apply those same arguments with
`--reviewed-sha256`. Audit apply requires that hash even for one ID. Never draw
again because a sample is inconvenient. Assign a reviewer from a different
judging session. Overclaim means a covered node is not taught at the locator;
underclaim is not an audit defect. The reviewer records the actual reviewed
sample, defects, reviewer identity, report path and full report digest in a
closure file, then uses `--close --audit-file FILE --check` and the same reviewed
apply procedure. Preserve report bytes for provenance. Reject/defer decisions
do not erase authorization, results or defects. Historical closure uses the
frozen basis pairs, not the current population. Repair each defective claim
through the admitted plan path; only changed bases can produce the next pool.

## 31. Back up and restore

Procedure: [transcript](procedures/back-up-and-restore.md).

The materials tree lives outside git, so for it the backup is the only
protection. A backup carries three roots in full, exactly as
`system/contracts/backup-roots.yaml` allowlists them:

- Core's canonical data (knowledge, sources, records, projects, work,
  curriculum data, transaction ledgers, contracts and schemas) — never
  Core's code, which git already versions; the manifest records the commit
  the data belongs with instead;
- the Obsidian UI checkout in full (sources, tests, contracts, scripts,
  vault config, and the shipped plugin assets `plugin-assets.json`
  declares; the plugin's `plugin/build-info.json` must exist, generated by
  `npm run stage-plugin` or `npm run build` in obsidian-ui);
- the materials tree in full.

Cadence: back up before each exam period and after each materials import.
