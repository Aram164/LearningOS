# LearningOS Operator Contract v2

This is the vendor-neutral entry point for every AI operator, local agent, and
interface. Platform-specific instructions may add mechanics but may not weaken
this contract.

It is the **declared** entry point, not merely the customary one:
`system/contracts/normative-corpus.yaml` names this file as `entrypoint`, and
the validator fails if that declaration points anywhere else, or at a document
that is not both current and binding.

## What binds, and what does not

`system/` holds several thousand lines of prose. Not all of it is rules. The
index at `system/contracts/normative-corpus.yaml` classifies every
`system/*.md` and `system/adr/*.md` file exactly once — class, status,
authority, owner, and its supersession edges — and `make check` fails if a
document is added without being classified, or if a retired document is still
marked binding.

Read it before treating any document under `system/` as law. In particular:
`authority: informative` documents (PHILOSOPHY, CRITIQUE-POINTS, SPEC-README)
create no obligation, and `authority: historical` documents (the frozen build
and migration records, every dated review) record what was true and are never
a current rule.

## What "clean" means

Validation success means **zero errors**. Warnings stay visible and never
block — `tools/validate.py` exits 0 with them, and the pre-commit hook lets
them through by design. What is not permitted is a *new* one:

```bash
python tools/warning_baseline.py --check
```

compares the current warning signatures against
`operations/validation-warning-baseline.yaml` — (code, path) with multiplicity,
so a total that stays level while one warning is traded for another is still a
failure. The warnings carried today are the measured content debt of
CRITIQUE-POINTS §1, deferred deliberately. A small named set of operational and
clock-derived advisories (`learning_os.rules.common.BASELINE_EXEMPT_WARNINGS`;
see `system/VALIDATION.md`) stays visible in every run but is exempt from this
gate by exact code, never by heuristic. A baseline-managed signature that
shrinks is a repair and passes; it is never restored merely to match the old
total.

Fail-closed is the design, not an accident: one validation error anywhere
in the tree blocks *every* canonical write, even an unrelated capture, and
reads refuse rather than silently omit what they cannot verify. The error
always names its file. Fix the defect; do not route around the guard.

## Start here

Do not recursively discover the repository. Entry is task-shaped: start
with the read that answers the task.

```bash
python tools/los.py capabilities --compact --json
```

The capability index is discovery only. Before using a capability, fetch its
complete definition with `capabilities NAME --json`; command details include
the declared payload schema. The complete catalogue remains available through
`capabilities --json` when the task needs it.

Pick one entry read; do not stack them:

- A named route → `plan-edit-context UNIT_ID --route-id ROUTE_ID`
  (or `--route-ids A B ...` for 1–20 routes of one unit in one
  snapshot-bound call), then `route-patch --check`. The route response
  already carries the snapshot and exact revision guards; do not read
  `bootstrap` or the unit brief first.
- A named stage → `plan-edit-context UNIT_ID --stage-id STAGE_ID`;
  `inspect STAGE_ID` does not resolve stages.
- Unit coverage, source-completeness, or unknown route/stage ids →
  `plan-edit-context UNIT_ID --brief` first (guards, id inventories,
  missing evidence, reusable analysis refs, preflight checks, runnable
  expands), then expand one route, stage, or the full `--audit` form
  only when the task needs complete bodies.
- An open "what should I work on?" / "what next?" → `bootstrap --brief`,
  then the named workspace plus `inspect WORKSPACE_ID`; use
  `inspect coordination` when priorities matter.

`bootstrap --brief` is the open-question entry: guards, resume, owed work,
deadlines, and runnable expands on one page. `--compact` pages the full
collections when the brief's expands are not enough. Start with one of
them, not both as routine startup; expand to the other later only when
the task needs it. Full `bootstrap` is an explicit bulk read, not routine
startup.

Decide which read answers the question before reading:

- A named record → `inspect ID`. A named stage →
  `plan-edit-context UNIT_ID --stage-id STAGE_ID`; `inspect STAGE_ID` does not
  resolve stages. A named route → `plan-edit-context UNIT_ID --route-id
  ROUTE_ID` (or the `--route-ids` batch); the route response already
  carries the snapshot and revision guards. Reach for the unit `--brief`
  only for unit coverage, source-completeness, or unknown ids.
- A material question → saved context first (`material-context`), else one
  exact span (`material-span UNIT_ID ROUTE_ID`); never trawl.
- A new video → title/description and course/playlist membership for provisional
  intake. Examine with Gemini Notebook only when selected for use, verify
  against exact video timestamps, then save the bounded analysis; see
  `system/WORKFLOWS.md` §6a.
- An open "what should I work on?" / "what next?" → `bootstrap --brief`
  (the open-question entry above), then the named workspace plus
  `inspect WORKSPACE_ID`; use `inspect coordination` when priorities matter.
  The brief reports where study stopped and recorded workspace options; neither
  chooses the next priority for Aram.
- What changed, what wants a decision → `intelligence-scan --brief --json`:
  five ranked groups plus totals, the agent entry path. The full queue only
  for explicit bulk review; inspect a named route or unit first.
- Coordination decisions and workspace next actions are recorded evidence.
  Show their source and decision date when present, then compare them with
  current status, deadlines, and newer decisions. Ask Aram when they conflict
  or his current intent remains unclear. `resume` shows up to two sourced,
  dated recorded-aim excerpts beside its stage; they are context, not a new
  learner choice.
- A detector candidate is a signal, never an instruction. `los goal <id>
  --reject|--defer|--close` records Aram's explicit decision; do not choose
  a disposition on his behalf.

Task-shaped entry preserves complete material access through `inspect ID`.
Its `domain_atlas` glance summarizes all projected notes and shelves across
domains, independently of pagination; open the domain atlas for the full map
(run `make views` first on a fresh install — `generated/` starts empty).
Read several known records with `inspect ID1 ID2 ...` (at most 20) to share one
fresh projection; the batch preserves requested order, includes a snapshot,
and refuses missing IDs or changes during the read. Use `note-read` for note
bodies — durable notes and garden seeds alike, by stable id. Ask governance
questions through `semantic PREDICATE --input k=v`
(`semantic --list` names the 23 registered predicates;
`semantic --recipe CLASS` shows the worked example procedures for one
question class, examples only) instead of
re-deriving meaning from scattered YAML.
For plan editing, start with the focused read: `--route-id ROUTE_ID`
(or the `--route-ids` batch) for one material and its stage-specific
overrides, `--stage-id STAGE_ID` for one stage's own flags and placements
instead of the whole map. Each carries its snapshot and revision guards.
Read several known routes with `--route-ids A B ...` (1 to 20 distinct
routes of one unit, in order) to share one snapshot and load; the batch
preserves requested order and refuses missing, duplicate, or out-of-bounds
ids without a partial payload. Shared descriptions occur once. Start with
`plan-edit-context UNIT_ID --brief` only for unit coverage,
source-completeness, or unknown ids: guards, id inventories, missing
evidence, reusable analysis refs, preflight checks, and runnable expand
commands.
The brief's `unit_audit.synthesis.replacement_required_if_evidential_routes_change`
reports whether an existing dossier needs replacement if a proposed route change
alters evidence; `fresh` reports the dossier's current validity separately.
The actual revision preflight decides whether the proposed change is evidential.
Universe questions still need the full unit context. Before changing
material details, run `route-patch UNIT_ID ROUTE_ID --changes JSON --check`,
then apply the same changes through `route.patch` with the returned
snapshot and exact revision guards. Full plan imports are for structure,
ordering, scope, or resource membership changes.
Continue a summary page with its returned offset and snapshot. Read saved
reasoning with `note-read NOTE_ID` (bounded Unicode-character segments) and
search beyond note summaries with `search QUERY --type note --content`.
Read a stage's working-note content from its parent map: `inspect
STUDY_MAP_ID` carries every stage's `notes_text` (`inspect STAGE_ID` does
not resolve stages). The `notes_updated` on those stages is the note file's
last-commit date, not the write date — uncommitted gateway writes do not
move it. Read inbox drops with `inbox-read NAME` (bounded segments of one
`work/inbox/` file by name; binary drops refuse). `search` without
`--content` matches records, garden seeds, and inbox filenames, so all
three are discoverable without reading files.
Continuation reads require the previous response's `--expected-snapshot`;
changed content is a restart, never a silently mixed result.

The stable read contract is the single atomic `generated/manifest.json`. Its
current version is declared in `system/contracts/manifest-contract.yaml` and
enforced by the producer on every build, so the version announced and the shape
published cannot disagree. This is separate from the canonical record format,
whose current version is declared in `system/contracts/data-contract.yaml`.
They version different things and move independently. The manifest contains
programs, semesters, partitioned modules,
components, units, study maps, stages, source maps, topics, joins, progress,
resume pointer, structured academic deadlines (registered attempts, available
sittings, and registration windows), and the Future Master's Planning boundary. Interfaces must not reconstruct
application state by parsing canonical Markdown or YAML. Use `list-*`,
`inspect`, `search`, and `related` for targeted reads. `search` without
`--content` conjoins whitespace-separated substrings per row — every term
must occur somewhere in the row — unranked and without snippets, so short
stems collide and natural phrasing often returns nothing; that coarseness
is the design, not a defect. `related ID` walks one hop over the record's
own declared edges plus the manifest's backlink tables, and it is not
symmetric: a workspace lists a note when either side declares the link,
but the note lists the workspace only when the note itself declares it,
so membership in one direction never implies the reverse edge.

## Product hierarchy

```text
program / area
└── module
    ├── optional stable components
    ├── module source map (complete lecture-material options)
    └── units
        ├── lecture knowledge map
        ├── learner source selections
        ├── durable artifact references
        └── optional current study map
            └── ordered stages
```

Many modules, units, and study maps may be active. The global resume pointer is
only a shortcut to the last active stage; it never replaces or hides the tree.
Skills and projects use modules and units without false academic metadata.

## Hard boundaries

1. Never edit `generated/`; change authored input, validate, and regenerate.
2. Preserve user wording. Semantic rewriting, note identity changes, deletion,
   inferred concept relations, and pedagogical judgments require visible review.
3. `semestercontext/Stratum/` is an external sibling code repository, not
   LearningOS data. LearningOS never indexes, validates, migrates, or manages
   it. An agent may inspect relevant paths when the current task explicitly
   needs code context; repository work happens directly in Stratum only when
   requested. No LearningOS query, manifest build, validator, or AI action
   traverses it automatically.
4. Master's Planning is Git-tracked under `curriculum/quarantine/`, excluded
   from normal loading and search, and represented only by a boundary record.
5. Academic administrative facts live only in the owning partitioned
   `curriculum/modules/<module-id>/module.yaml`; coordination decisions live
   only in `work/COORDINATION.md`.
6. Every unit of an active or enrolled module owes a study map. A knowledge map
   and a complete material menu say what a lecture covers and what may be used;
   they are not an ordered path and do not discharge the obligation. A unit that
   is complete or archived, or one whose module is dropped or archived, is owed
   nothing. The producer answers this per unit as `needs_study_map`, derived
   from the records rather than declared, so the count, the badge and the Review
   queue cannot disagree. Workspaces coordinate efforts through explicit
   `program_ids`, `module_ids`, and `unit_ids`; they do not own the curriculum
   hierarchy.
7. Durable notes remain globally canonical under `knowledge/`; units reference
   Ultimate References, Exercise Banks, Mock Exams, and other artifacts by ID.
8. Source identity/evaluation, module role, unit selection, and stage action are
   distinct ownership layers. Stage feedback is use evidence, not an automatic
   rewrite of a global source evaluation.
9. Shelving is approval-gated. Apply only explicitly selected proposal items.
10. Never declare mastery. Report evidence or its absence.
11. General AI conversation is read-only. Writes use an action-specific gateway
    capability and must remain inside its module/unit/stage scope.
12. Every app mutation carries the current manifest snapshot. On conflict,
    reload rather than overwrite.
13. Validate after authored changes. Acceptance requires zero errors and no new
    or grown warning signature (`python tools/warning_baseline.py --check`).
    Baseline-exempt operational and clock-derived advisories stay visible and
    never block; see "What 'clean' means" above.
14. Source completeness is mandatory. Every learning source named by an
    authoritative template, bibliography, plan, or course artifact must remain
    reachable and be explicitly selected, reference-only, or deferred with a
    reason. Registered-source counts never prove inventory completeness, and
    silent omission is forbidden.
15. Every newly authored learning plan uses
    `plan_template_version: 1` and the shared numbered-stage/resource contract
    in `system/schema/learning-plan.schema.json`. Domain fields extend that
    contract; they never redefine it. Old plans are readable evidence, not
    creation templates.
16. A plan is created **and revised** through the declared capabilities —
    `module.plan.import` for a module's source map and its units,
    `unit.plan.revise` for one existing unit's reviewed material revision,
    `unit.map.import` for one unit's study map, or `route.patch` for one
    existing route's descriptive material fields — never by writing the canonical
    file directly. Drafting happens outside the repository
    (`tools/assemble_lecture_study_maps.py --out …`), review happens on the
    draft, and the gateway applies it under a snapshot guard with an
    append-only receipt. A hand edit is not a faster version of this path: it
    produces a file the validator accepts while skipping every guarantee the
    path exists for, and leaves nothing behind to say it happened. Migrations
    under `tools/migrations/` are the one exception, because they are recorded.
    `module.materials.compact` is the governed, lossless conversion to shared
    material references; it requires the reviewed preflight plan hash. It
    preserves every expanded map and commits stable route IDs with the references.
17. `system/CRITIQUE-POINTS.md` is an append-only log of unresolved judgments
    about the system itself. **An open point is not a work item.** It is
    recorded precisely so it can be deferred, and acting on one — fixing it,
    or "improving" it as a side effect of unrelated work — requires Aram to say
    so in that session. Appending a point verbatim and adding measured evidence
    to an open one are always allowed; closing one is his alone.

## Unit workflow

Choose a module and unit. First inspect its knowledge map and complete material
menu, grouped by format and annotated with angle, depth, scope, and coverage.
Record actual choices in `source_selections`. If ordered tracking would help,
the unit may then have at most one current study map using only those choices.
Work in its stages while preserving independent state for every other unit.

These are gateway capabilities: `unit.source-selection.set`, `unit.note.append`,
`stage.progress.update`, `source.feedback.record`, `detour.create` (named
commands `unit-source-selection`, `unit-note`, `stage-progress`,
`source-feedback`, `detour-create`). Run bare, a named command never writes:
every canonical write refuses without a GatewayEnvelopeV2. Read the payload
schema, then submit one envelope (fields and intent hash: WORKFLOWS §25a,
step 4):

```bash
python tools/los.py capabilities stage.progress.update --json
python tools/los.py capability stage.progress.update --payload-file ENVELOPE.json
```

`unit-source-selection` accepts only a rich material route already exposed on
that unit. It changes the learner's choice list, not the source map or the
complete menu. Removing a choice already wired into a study path is refused.

`unit-note` appends one session-level section after the learner finishes the
relevant stages. `stage-note` remains a compatibility command for existing
stage-owned scratch files.

When confirmed lecture scope requires a module-wide batch (new units, knowledge
maps, complete rich source routing, optional study maps, and workspace joins), follow
[`PLAN-CREATION-SOP.md`](PLAN-CREATION-SOP.md). Complete its material-coverage
audit, build from the canonical template, and require the no-write gate
`.venv/bin/python tools/los.py module-plan-import MODULE_ID --file PLAN.yaml
--check` to pass before applying the same package through the
`module.plan.import` capability (WORKFLOWS §25a).
For several existing units, the same command accepts the compact
`unit_revisions[]` shape in `system/templates/module-plan-revise.template.yaml`;
it assembles unchanged records internally and keeps the same guarded import.
`module-plan-import` never deletes units and never creates durable notes; the
capabilities that do create durable notes are `note.analysis.save` (one source
analysis), `note.analysis.save_batch` (up to 20 source analyses atomically),
and `atlas.question.save` (learner questions).

An explicitly reviewed semantic replacement of one existing durable note uses
the `note.revise` capability (named command `note-revise NOTE_ID --file
REVISED.md`). It preserves the note's ID, path, and role; moves, merges, splits,
and role changes remain outside this capability.

A stage owns its working note, attachments, exact resources, source-use
feedback, and optional detour relationship. A detour records its originating
stage and return stage; there is no canonical session entity.

## Shelving and session closure

Shelving reads selected stage notes and attachments, preserves uncertainty and
wrong turns, proposes durable notes/Garden items and diffs, and waits for
explicit selected-item approval. After application, validate and regenerate.

End a learning session deliberately with `los session-end`. First run it with
no commit message to review session-owned and unrelated changes. Only the
ephemeral session ledger may be staged. The protected Canvas files are always
excluded. Commit and optional push occur only after explicit confirmation.

## Capture routing

Stage-specific learning belongs in its stage note. Unrelated quick capture goes
to `work/inbox/`. A deliberately half-formed idea that should gestate goes to
`knowledge/garden/`. The operator, not the learner, handles filing. Every one
of these writes goes through a GatewayEnvelopeV2 built per WORKFLOWS §25c.

Read the applicable platform adapter, then the task-relevant sections of
`system/ARCHITECTURE.md`, `system/WORKFLOWS.md`, and the schemas/contracts they
reference before acting. Consult `system/PHILOSOPHY.md` for unresolved intent.
All binding rules still apply; expand the reading scope whenever the task
crosses an ownership or workflow boundary. A routine lookup does not require
loading every schema, historical review, or unrelated workflow into context.
