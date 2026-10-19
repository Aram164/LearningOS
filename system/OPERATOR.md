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
owned `AGENTS.md`, `README.md`, `system/*.md`, `system/adr/*.md`, and
`system/skills/*/SKILL.md` file exactly once — class, status,
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

The [warning-baseline check](procedures/start-here.md#check-the-warning-baseline)
compares the current warning signatures against
`operations/validation-warning-baseline.yaml` — (code, path) with multiplicity,
so a total that stays level while one warning is traded for another is still a
failure. The warnings carried today are the measured content debt of
CRITIQUE-POINTS §1, deferred deliberately. A small named set of operational and
clock-derived advisories (`learning_os.domain.validation.BASELINE_EXEMPT_WARNINGS`;
see `system/VALIDATION.md`) stays visible in every run but is exempt from this
gate by exact code, never by heuristic. A baseline-managed signature that
shrinks is a repair and passes; it is never restored merely to match the old
total.

Fail-closed: one validation error anywhere
in the tree blocks *every* canonical write, even an unrelated capture, and
reads refuse rather than silently omit what they cannot verify. The error
always names its file. Fix the defect; do not route around the guard.

## Start here

| Task | Entry read | Executable procedure |
|---|---|---|
| Discover capabilities | `capabilities --compact --json`, then `capabilities NAME --json` | [Discover and expand](procedures/start-here.md#discover-the-capability-index) |
| Edit a known material route | `plan-edit-context UNIT_ID --route-id ROUTE_ID` or `--route-ids A B` | [Revise a plan](procedures/revise-an-existing-plan.md#start-from-the-named-routes-edit-context) |
| Edit a known stage | `plan-edit-context UNIT_ID --stage-id STAGE_ID` | [Enter through the stage](procedures/bootstrap-order.md#enter-through-the-named-stage) |
| Unit coverage, source completeness, or unknown IDs | `plan-edit-context UNIT_ID --brief` | [Choose the focused context](procedures/start-here.md#follow-one-printed-expansion-with-its-snapshot-pin) |
| Open work or priority question | `bootstrap --brief`, then `inspect WORKSPACE_ID` and relevant coordination | [Read operational state](procedures/retrieval-behavior.md#orient-operational-questions-from-the-brief) |
| Known record or stage note | `inspect ID`, including a batch of known IDs | [Read one record](procedures/start-here.md#read-one-named-record), [read one stage note](procedures/start-here.md#read-one-named-stage-with-its-working-note-content) |
| Note body or saved reasoning | `note-read NOTE_ID` | [Read saved reasoning](procedures/start-here.md#search-beyond-note-summaries-then-read-the-saved-reasoning) |
| Material or concept explanation | `material-context`, then an exact `material-span` when needed | [Retrieve explanations](procedures/retrieval-behavior.md#read-what-explains-it) |
| Resume recorded study | `resume` or `resume --study` | [Resume without moving state](procedures/start-here.md#the-study-suggestion-never-moves-the-resume-pointer) |
| Changes awaiting a decision | `intelligence-scan --brief --json` | [Read the decision queue](procedures/start-here.md#read-what-wants-a-decision) |
| Ability evidence | `ability-context` horizon, then a known ability | [Read a bounded ability](procedures/start-here.md#read-one-ability-through-the-bounded-horizon) |
| Governance question | `semantic --list`, then `semantic PREDICATE --input k=v` | [Ask the semantic surface](procedures/start-here.md#ask-a-governance-question-through-the-semantic-surface) |

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
    or grown warning signature (`.venv/bin/python tools/warning_baseline.py --check`).
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

## Procedures

<!-- los:generated name=procedure-index -->
| Source | Procedure | Execution |
|---|---|---|
| [system/OPERATOR.md](OPERATOR.md) | Start here | [Transcript](procedures/start-here.md) |
| [system/OPERATOR.md](OPERATOR.md) | Procedures | [Transcript](procedures/unit-workflow.md) |
| [system/OPERATOR.md](OPERATOR.md) | Capture routing | [Transcript](procedures/capture-routing.md) |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 1. Start a workspace | [Transcript](procedures/start-a-workspace.md) |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 2. Capture temporary material | [Transcript](procedures/capture-temporary-material.md) |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 3. Create or evolve a durable note | [Transcript](procedures/create-durable-note.md) |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 4. Add a concept | [Transcript](procedures/add-a-concept.md) |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 5. Add a concept relation | [Transcript](procedures/add-concept-relation.md) |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 6. Add or evaluate a source | [Transcript](procedures/add-or-evaluate-a-source.md) |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 8. Record evidence | [Transcript](procedures/record-evidence.md) |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 9. Update coordination | [Transcript](procedures/update-coordination.md) |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 10. Record a module event | [Transcript](procedures/record-module-event.md) |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 11. Complete and archive a workspace | [Transcript](procedures/complete-and-archive-a-workspace.md) |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 12. Generate indexes and reports | [Transcript](procedures/generate-indexes-reports.md) |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 13. Review a note | [Transcript](procedures/review-a-note.md) |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 14. Move or rename a note | [Transcript](procedures/move-or-rename-a-note.md) |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 15. Deprecate or supersede | [Transcript](procedures/deprecate-or-supersede.md) |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 16. Maintain a crosswalk | [Transcript](procedures/maintain-crosswalk.md) |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 17. Ingest a handwritten note | [Transcript](procedures/ingest-a-handwritten-note.md) |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 18. Start a module | [Transcript](procedures/start-a-module.md) |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 19. Close a module | [Transcript](procedures/close-a-module.md) |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 20. Carry work across semesters | [Transcript](procedures/carry-work-across-semesters.md) |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 21. Process the inbox | [Transcript](procedures/process-inbox.md) |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 22. End a session | [Transcript](procedures/end-a-session.md) |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 23. Process a lecture | Untranscribable: needs real as-taught decks/recordings as scope authority plus the full plan-creation package; fixture has only the demo book; affected steps: materials-in, scope pass, package and preflight |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 24. Turn the semester | Untranscribable: composites workflow 19 and a real term boundary with human Garden judgments and push; fixture has no remote; affected steps: close/carry fork, harvest, push |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 25a. Revise an existing plan | [Transcript](procedures/revise-an-existing-plan.md) |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 25b. Save a batch of source analyses | [Transcript](procedures/save-a-batch-of-source-analyses.md) |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 25c. Build a write envelope (GatewayEnvelopeV2) | [Transcript](procedures/build-write-envelope.md) |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 26. Source routing and feedback | [Transcript](procedures/source-routing-and-feedback.md) |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 27. Promote a future Master's module | Untranscribable: needs a future program that has actually begun, with confirmed modules and quarantined originals; affected steps: boundary entry, module selection, migration |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 28. Read an operation (`los operations`) | [Transcript](procedures/read-an-operation.md) |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 29. Review a stage's material angle | [Transcript](procedures/review-a-stage-material-angle.md) |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 30. Review exact goal decisions together | [Transcript](procedures/review-exact-goal-decisions-together.md) |
| [system/WORKFLOWS.md](WORKFLOWS.md) | 31. Back up and restore | [Transcript](procedures/back-up-and-restore.md) |
| [system/CLAUDE.md](CLAUDE.md) | 2. Bootstrap order | [Transcript](procedures/bootstrap-order.md) |
| [system/CLAUDE.md](CLAUDE.md) | 7. Retrieval behavior | [Transcript](procedures/retrieval-behavior.md) |
<!-- /los:generated -->

### Unit workflow

Procedure: [the governed stage write](procedures/end-a-session.md#read-the-stage-progress-payload-contract).

`unit-source-selection` accepts only a rich material route already exposed on
that unit. It changes the learner's choice list, not the source map or the
complete menu. Removing a choice already wired into a study path is refused.

`unit-note` appends one session-level section after the learner finishes the
relevant stages. `stage-note` remains a compatibility command for existing
stage-owned scratch files.

An explicitly reviewed semantic replacement of one existing durable note uses
the `note.revise` capability. Running `note-revise NOTE_ID --file REVISED.md`
without `--approve` is refused, and with `--approve` the direct CLI write is
disabled; a revision is applied through a sealed GatewayEnvelopeV2 for
`note.revise` (see [write envelopes](procedures/build-write-envelope.md)). It
preserves the note's ID, path, and role; moves, merges, splits, and role
changes remain outside this capability.

A stage owns its working note, attachments, exact resources, source-use
feedback, and optional detour relationship. A detour records its originating
stage and return stage; there is no canonical session entity.

Procedure: [unit workflow](procedures/unit-workflow.md).

### Shelving and session closure

Procedure: [shelving and session closure](procedures/shelving-session-closure.md).

## Capture routing

Stage-specific learning belongs in its stage note. Unrelated quick capture goes
to `work/inbox/`. A deliberately half-formed idea that should gestate goes to
`knowledge/garden/`. The operator, not the learner, handles filing. Every one
of these writes goes through a GatewayEnvelopeV2 built per WORKFLOWS §25c.
When Aram starts a message with `log:`, treat the following text as an explicit
request to capture it verbatim. If the stage was explicitly identified in the
current conversation, append it to that stage's working note through
`stage.note.write`; otherwise use `capture.create` for the inbox. Report the
destination and receipt. The capture does not imply progress or mastery and
does not move the resume pointer.

Agent friction — an agent's own observation about navigating or changing
LearningOS — is not a learner capture: record it directly in
`work/complaints/` (see its README), never in the inbox. A routed inbox
drop leaves through `inbox.resolve`, naming where it went (WORKFLOWS
§21); the inbox trends toward empty.

Read the applicable platform adapter, then the task-relevant sections of
`system/ARCHITECTURE.md`, `system/WORKFLOWS.md`, and the schemas/contracts they
reference before acting. Consult `system/PHILOSOPHY.md` for unresolved intent.
All binding rules still apply; expand the reading scope whenever the task
crosses an ownership or workflow boundary. A routine lookup does not require
loading every schema, historical review, or unrelated workflow into context.

Procedure: [capture routing](procedures/capture-routing.md); [write envelopes](procedures/build-write-envelope.md).
