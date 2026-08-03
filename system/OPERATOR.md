# LearningOS Operator Contract v1

This is the vendor-neutral entry point for every AI operator (Codex, Claude,
local agents, and future Obsidian integrations). Platform-specific instruction
files may add mechanics, but they may not weaken this contract.

## Start here

Run these commands instead of discovering the repository by recursively
reading it:

```bash
python tools/los.py capabilities --json
python tools/los.py bootstrap
```

The stable read contract is `generated/manifest.json`, currently
`contract_version: 1`. Interfaces and agents read that single atomic snapshot;
they do not parse canonical Markdown/YAML to reconstruct application state.
Use `search`, `inspect`, and `related` through `tools/los.py` for targeted reads.

## Hard boundaries

1. Never edit `generated/`; change authored input and run `los generate`.
2. Preserve user wording. Semantic rewriting, note identity changes, deletion,
   inferred concept relations, and pedagogical judgments require visible review.
3. `Job/` is quarantined. Do not read, scan, index, cite, or route it unless the
   user explicitly authorizes that task. Job never appears in the core manifest.
4. Exam facts belong only in `records/modules.yaml`; coordination facts belong
   only in `work/COORDINATION.md`.
5. Learning paths are temporary operational state owned by a workspace. They do
   not become durable knowledge merely because a stage is complete.
6. Shelving is approval-gated: propose destinations, metadata, links, and diffs;
   do not change canonical notes until the learner approves the proposal.
7. Never declare mastery. Report the evidence trail or its absence.
8. Validate after authored changes. Stop on errors; surface warnings.

## Learning-path workflow

One subtopic is represented by `work/active/<workspace>/paths/path-*.yaml`.
Work in the ordered stages while allowing a stage to be skipped or revisited.
The current stage owns its working note in the same workspace. Use the gateway:

```bash
python tools/los.py path-note PATH_ID STAGE_ID --replace --text "..."
python tools/los.py path-progress PATH_ID STAGE_ID complete
```

Pass `--expected-snapshot` from the manifest when operating through an app. A
conflict means another authored change occurred; reload instead of overwriting.

When asked to "shelve" a path:

1. inspect the path and every stage note;
2. preserve the learner's original wording, uncertainty, and corrections;
3. propose zero or more durable notes and/or Garden items, with destinations,
   roles, concepts, sources, attachments, and any concept relations;
4. show a reviewable diff and keep ambiguous material in workspace scratch;
5. wait for explicit approval;
6. apply only approved changes, validate, regenerate, and then archive the path.

## Capture routing

Stage-specific learning belongs in its stage note. An unrelated quick capture
goes to `work/inbox/`. A deliberately half-formed idea that should gestate goes
to `knowledge/garden/`. The operator, not the user, handles later filing.

For deeper architectural and semantic rules, continue with
`system/PHILOSOPHY.md`, `system/ARCHITECTURE.md`, `system/WORKFLOWS.md`, and the
platform adapter `system/CLAUDE.md` where applicable.
