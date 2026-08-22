# LearningOS Operator Contract v2

This is the vendor-neutral entry point for every AI operator, local agent, and
interface. Platform-specific instructions may add mechanics but may not weaken
this contract.

## Start here

Do not recursively discover the repository. Begin with:

```bash
python tools/los.py capabilities --json
python tools/los.py bootstrap
```

The stable read contract is the single atomic `generated/manifest.json`,
`contract_version: 5` — declared in `system/contracts/manifest-contract.yaml`
and enforced by the producer on every build, so the version announced and the
shape published cannot disagree. (This is not the canonical record format,
which is `data-contract.yaml` v5; the two version different things and move
independently.) It contains programs, semesters, partitioned modules,
components, units, study maps, stages, source maps, topics, joins, progress,
resume pointer, structured academic deadlines (registered attempts, available
sittings, and registration windows), and boundary-only quarantine records. Interfaces must not reconstruct
application state by parsing canonical Markdown or YAML. Use `list-*`,
`inspect`, `search`, and `related` for targeted reads.

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
3. `Job/` is outside LearningOS. Never read, scan, index, cite, or route it
   without an explicit Job task; it never appears in the manifest. The sole UI
   exception is the ephemeral `job-dashboard` query: deliberately opening Job
   confirms one read-only session against the bounded `Job/dashboard.yaml`
   catalogue. It cannot feed search, AI context, recommendations, or writes.
   The nested `Job/stratum/` checkout is immutable to the whole system: neither
   its worktree nor `.git/` metadata may be written. The only permitted access
   is an exact, option-free hash-and-path drift query with Git locks disabled.
4. Master's Planning is Git-tracked under `curriculum/quarantine/`, excluded
   from normal loading and search, and represented only by a boundary record.
5. Academic administrative facts live only in the owning partitioned
   `curriculum/modules/<module-id>/module.yaml`; coordination decisions live
   only in `work/COORDINATION.md`.
6. Units may own a personal study map and stage work after source choice.
   Knowledge maps and complete material menus do not require one. Workspaces coordinate efforts through
   explicit `program_ids`, `module_ids`, and `unit_ids`; they do not own the
   curriculum hierarchy.
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
13. Validate after authored changes. Acceptance requires 0 errors and 0 warnings.
14. Source completeness is mandatory. Every learning source named by an
    authoritative template, bibliography, plan, or course artifact must remain
    reachable and be explicitly selected, reference-only, or deferred with a
    reason. Registered-source counts never prove inventory completeness, and
    silent omission is forbidden.
15. Every newly authored curriculum or Job learning plan uses
    `plan_template_version: 1` and the shared numbered-stage/resource contract
    in `system/schema/learning-plan.schema.json`. Domain fields extend that
    contract; they never redefine it. Old plans are readable evidence, not
    creation templates.

## Unit workflow

Choose a module and unit. First inspect its knowledge map and complete material
menu, grouped by format and annotated with angle, depth, scope, and coverage.
Record actual choices in `source_selections`. If ordered tracking would help,
the unit may then have at most one current study map using only those choices.
Work in its stages while preserving independent state for every other unit.

```bash
python tools/los.py unit-source-selection UNIT_ID SOURCE_ID LOCATOR select --purpose "Why this angle fits"
python tools/los.py unit-note UNIT_ID --text "..." --stage-id STAGE_ID --expected-snapshot SNAPSHOT
python tools/los.py stage-progress UNIT_ID STAGE_ID complete --expected-snapshot SNAPSHOT
python tools/los.py source-feedback UNIT_ID STAGE_ID SOURCE_ID helpful --expected-snapshot SNAPSHOT
python tools/los.py detour-create UNIT_ID STAGE_ID --title "Gap" --classification required-now --expected-snapshot SNAPSHOT
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
--check` to pass before applying the same package with `--expected-snapshot`.
The gateway never deletes units or creates durable notes.

An explicitly reviewed semantic replacement of one existing durable note uses
`los note-revise NOTE_ID --file REVISED.md --approve --expected-snapshot
SNAPSHOT`. It preserves the note's ID, path, and role; moves, merges, splits,
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
`knowledge/garden/`. The operator, not the learner, handles filing.

Continue with `system/PHILOSOPHY.md`, `system/ARCHITECTURE.md`,
`system/WORKFLOWS.md`, and the platform adapter when applicable.
