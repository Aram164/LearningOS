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
`contract_version: 2`. It contains programs, semesters, partitioned modules,
components, units, study maps, stages, source maps, joins, progress, resume
pointer, structured academic deadlines (registered attempts, available
sittings, and registration windows), and boundary-only quarantine records. Interfaces must not reconstruct
application state by parsing canonical Markdown or YAML. Use `list-*`,
`inspect`, `search`, and `related` for targeted reads.

## Product hierarchy

```text
program / area
└── module
    ├── optional stable components
    ├── module source map
    └── units
        ├── durable artifact references
        └── one current study map
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
   without an explicit Job task; it never appears in the manifest.
4. Master's Planning is Git-tracked under `curriculum/quarantine/`, excluded
   from normal loading and search, and represented only by a boundary record.
5. Academic administrative facts live only in the owning partitioned
   `curriculum/modules/<module-id>/module.yaml`; coordination decisions live
   only in `work/COORDINATION.md`.
6. Units own study maps and stage work. Workspaces coordinate efforts through
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

## Unit workflow

Choose a module and unit. The unit has at most one current study map. Work in
ordered stages while preserving independent state for every other unit.

```bash
python tools/los.py unit-note UNIT_ID --text "..." --stage-id STAGE_ID --expected-snapshot SNAPSHOT
python tools/los.py stage-progress UNIT_ID STAGE_ID complete --expected-snapshot SNAPSHOT
python tools/los.py source-feedback UNIT_ID STAGE_ID SOURCE_ID helpful --expected-snapshot SNAPSHOT
python tools/los.py detour-create UNIT_ID STAGE_ID --title "Gap" --classification required-now --expected-snapshot SNAPSHOT
```

`unit-note` appends one session-level section after the learner finishes the
relevant stages. `stage-note` remains a compatibility command for existing
stage-owned scratch files.

When confirmed lecture scope requires a module-wide batch (new units, current
study maps, source routing, and workspace joins), follow
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
