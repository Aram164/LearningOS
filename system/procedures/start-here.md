---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Start here (OPERATOR)

Executable transcript of task-shaped entry: discover the capability
index, fetch one complete capability definition, start from the
open-question brief, follow one printed bare-argument expansion with
its snapshot pin, and read one named record, one unit brief, the
scan, and saved reasoning. An empty search names per-term hit counts
on stderr; `--json`
on an always-JSON read changes nothing; the study suggestion never
moves the resume pointer. `tests/test_procedures.py` runs it with
Scrut; `<REPO>` comes from the `LOS_REPO` environment variable the
test sets.

## Operating rules


Do not recursively discover the repository. Entry is task-shaped: start
with the read that answers the task. Use the project environment: run every
command below with `.venv/bin/python`, and if it does not exist run
`make setup` once first.

```bash
.venv/bin/python tools/los.py capabilities --compact --json
```

The capability index is discovery only. Before using a capability, fetch its
complete definition with `capabilities NAME --json`; command details include
the declared payload schema. The complete catalogue remains available through
`capabilities --json` when the task needs it.

<!-- los:macro {"text": ".venv/bin/python tools/los.py <expansion>", "transcript": "system/procedures/start-here.md"} -->
<!-- los:macro {"text": ".venv/bin/los <expansion>", "transcript": "system/procedures/start-here.md"} -->
Responses print follow-up reads as bare argument strings with no program
prefix. Run one as `.venv/bin/python tools/los.py <expansion>` (or
`.venv/bin/los <expansion>`); ALL-CAPS words are placeholders to fill from
the response. A printed `--expected-snapshot` pins the follow-up to the same
records — when it reports a conflict, re-read the parent first. On a read
that always prints JSON, `--json` is accepted and changes nothing; an
unknown flag answers with that subcommand's usage, not the whole list.

Pick one entry read; do not stack them:

- A named route → `plan-edit-context UNIT_ID --route-id ROUTE_ID`
  (or `--route-ids A B ...` for 1–20 routes of one unit in one
  snapshot-bound call), then `route-patch --check`. The route response
  already carries the snapshot and exact revision guards; do not read
  `bootstrap` or the unit brief first.
- A named stage → `plan-edit-context UNIT_ID --stage-id STAGE_ID` for edits
  (snapshot and revision guards); `inspect STAGE_ID` answers read-only
  questions with the projected row plus owners.
- Unit coverage, source-completeness, or unknown route/stage ids →
  `plan-edit-context UNIT_ID --brief` first (guards, id inventories,
  missing evidence, reusable analysis refs, preflight checks, runnable
  expands), then expand one route, stage, or the full `--audit` form
  only when the task needs complete bodies. The brief counts
  neighboring units sharing sources; add `--include-neighbors` only
  when cross-lecture reuse is the question.
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

- A named record → `inspect ID`, including structural sub-ids (curriculum
  and path stages, detours, project nodes, milestones — each answers with
  its owners). A named stage edit →
  `plan-edit-context UNIT_ID --stage-id STAGE_ID` for the guards. A named
  route → `plan-edit-context UNIT_ID --route-id ROUTE_ID` (or the
  `--route-ids` batch); the route response already carries the snapshot
  and revision guards. Reach for the unit `--brief` only for unit
  coverage, source-completeness, or unknown ids.
- A material question → saved context first (`material-context`), else one
  exact span (`material-span UNIT_ID ROUTE_ID`); never trawl. On
  `material-span`, a stage's narrower file or page selection uses
  `--stage STAGE_ID --resource-index N` (the zero-based canonical resource
  position; both selectors are required). On `material-context`, a lone
  `--concept` asks what explains it: notes match by their own tags or as
  route-direct evidence (same file, overlapping pages) for a route placed on a
  stage that tags the concept, named in `match.concept_via`; a shared source
  alone never joins. With `--unit`,
  default results are route-direct only; `--include-related` appends
  same-source notes labelled `related`, and `--material PATH` filters notes
  and assessments to one exact materials file. Analysis anchors preview
  bounded (purpose matches first) with exact totals; the response's
  `--include-anchors` continuation expands the same page's complete index
  under the same guards. Changed data refuses the saved expansion instead
  of silently switching pages: restart from offset 0 then.
- A new video → title/description and course/playlist membership for provisional
  intake. Examine with Gemini Notebook only when selected for use, verify
  against exact video timestamps, then save the bounded analysis; see
  `system/WORKFLOWS.md` §6a.
- An open "what should I work on?" / "what next?" → `bootstrap --brief`
  (the open-question entry above), then the named workspace plus
  `inspect WORKSPACE_ID`; use `inspect coordination` when priorities matter.
  The brief reports where study stopped and recorded workspace options; neither
  chooses the next priority for Aram.
- `resume --study` offers the nearest recorded exam's study path — its single
  active map's current stage, or a bounded menu when zero or several maps are
  active (select one with `resume --study --unit UNIT_ID`) — including one
  required resource locator when present. It labels registration state and
  never moves the learner's resume pointer.
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
  a disposition on his behalf. Only a goal in the current scan, or already in
  the ledger, is decidable; the decision joins the caller's session and
  `session-end` commits it. `--defer --revisit-on YYYY-MM-DD` hides a goal
  only until that date; its return to the scan is a candidate, not approval.

Task-shaped entry preserves complete material access through `inspect ID`.
The `domain_atlas` glance on `bootstrap --brief` and `bootstrap --compact`
summarizes all projected notes and shelves across domains, independently of
pagination; open the generated domain atlas for the full map only when the
targeted reads are insufficient (on a fresh install run `make setup` first,
then `make views` — `generated/` starts empty).
Read several known records with `inspect ID1 ID2 ...` (at most 20) to share one
fresh projection; the batch preserves requested order, includes a snapshot,
and refuses missing IDs or changes during the read. Use `note-read` for note
bodies — durable notes and garden seeds alike, by stable id. Ask governance
questions through `semantic PREDICATE --input k=v`
(`semantic --list` names the registered predicates;
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
search beyond note summaries with `search QUERY --type note --content`
(frontmatter values match, keys do not; bodies match verbatim).
Read a stage's working-note content with `inspect STAGE_ID`: it resolves
the stage and carries its `notes_text`. `inspect STUDY_MAP_ID` is for the
whole map. The `notes_updated` on a stage is the note file's
last-commit date, not the write date — uncommitted gateway writes do not
move it. List inbox drops with `inbox-list`, then read one with
`inbox-read NAME` (bounded segments of one `work/inbox/` file by name;
binary drops refuse). `search` without
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
`inspect`, `search`, and `related` for targeted reads. Discover units
with exact filters through `unit-list --compact --module-id MODULE_ID`,
select an ID, then `inspect ID` for detail; continuations repeat the
filters with the returned offset and snapshot. `search` without
`--content` conjoins whitespace-separated substrings per row — every term
must occur in the row's values; field names never match — unranked and
without snippets, so short stems collide and natural phrasing often
returns nothing. An empty answer
names per-term hit counts on stderr, so the eliminating term is visible.
An empty query lists every row instead of matching: `search "" --type
workspace` is the workspace list, and the same holds for every other
record family, garden seeds, and inbox filenames (up to `--limit`).
`related ID`
walks one hop over the record's own declared edges plus the manifest's
backlink tables in both directions, so membership in one direction always
implies the reverse edge. Results rank by connection strength (more
distinct edges first), then recorded stage use-evidence per source
(positive first, mismatch last, as in material-context), then stable id;
each result names the edges that produced it in `via`. A concept answers
the units whose stages tag it, and a unit its stages' concepts, each edge
reasoned by its stage (`stage-concept:<stage-id>` in `via`). Existing analyses
of a source answer here too: `related SOURCE_ID` lists the notes
analysing it (labelled `analyses` in `via`); `material-context` stays the
need-shaped query path. Page a long
metadata result with `search QUERY --type TYPE --page` and continue with
the returned `--offset` and `--expected-snapshot`; the plain array
response keeps its existing shape for explicit bulk reads, and when
`--limit` cuts it one stderr line names the shown/total counts with the
`--offset` continuation. Discover
abilities through the bounded `ability-context` horizon first —
`--limit`/`--offset` with the previous `--expected-snapshot` past the
first page — and expand one known ID with `ability-context ABILITY_ID`:
`--brief` for state and connection checks (bounded correction/conflict
examples with exact totals), `--section evidence` for the complete
observation ledger, per-stage expansions for materials.


## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Check the warning baseline

```bash
.venv/bin/python tools/warning_baseline.py --check
```

The command runs against the same disposable world as the entry reads.

```scrut
$ (set -o pipefail; $LOS_REPO/.venv/bin/python $LOS_REPO/tools/warning_baseline.py --root "$LOS_FX" --check | tail -n 1)
warning-baseline: OK — zero errors, no new warning signature.
```

## Discover the capability index

```scrut
$ los capabilities --compact --json | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["contract_version"], d["capability_contract_version"], d["cli_protocol"], "unit.source-selection.set" in d["commands"], "operator.bootstrap" in d["queries"])'
2 2 6 True True
```

## Fetch one complete definition with its payload schema

```scrut
$ los capabilities note.create --json | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); c = d["commands"]["note.create"]; print(c["handler"], c["cli_command"], ",".join(c["writes"]), ",".join(c["payload_records"]["note"]["accepted"]), ",".join(c["payload_records"]["note"]["required"]))'
note_create note-create knowledge/notes/** id,title,path,role,concepts,sources,contexts,supersedes id,title,path
```

## Start from the open-question brief

```scrut
$ los bootstrap --brief | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["counts"]["notes"], d["counts"]["workspaces_active"], ",".join(d["owed_study_maps"]), d["pointer_state"], len(d["domain_atlas"]))'
2 2 unit-demo-l02 confirmed 7
```

## Follow one printed expansion with its snapshot pin

```scrut
$ eval "$(los bootstrap --brief | $H/los-bind SNAP '$.snapshot_id')" && los plan-edit-context unit-demo-l02 --brief --expected-snapshot "$SNAP" | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["unit_id"], d["contract"])'
unit-demo-l02 plan-edit-context-brief
```

## Read one named record

```scrut
$ los inspect unit-demo-l01 | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["id"], d["title"], d["revision"], d["module_id"])'
unit-demo-l01 Expected value 3 module-demo
```

## Read one named stage with its working-note content

```scrut
$ los inspect stage-demo | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["id"], d["module_id"], repr(d["stage"]["notes_text"]), d["stage"]["notes_updated"])'
stage-demo module-demo '' 2026-10-01
```

## Read the unit list, then the chosen record

```scrut
$ los unit-list --compact --module-id module-demo | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["total"], sorted(u["id"] for u in d["items"]))'
2 ['unit-demo-l01', 'unit-demo-l02']
```

## Read what wants a decision

```scrut
$ los intelligence-scan --brief --json | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["total_goals"], d["total_groups"], d["groups"][0]["detector"])'
2 2 lineage-stale
```

## Search beyond note summaries, then read the saved reasoning

```scrut
$ los search expected --type note | $LOS_REPO/.venv/bin/python -c 'import json,sys; print(sorted(r["id"] for r in json.load(sys.stdin)))'
['note-demo', 'note-demo-analysis']
```

```scrut
$ los note-read note-demo | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["note_id"], d["total_characters"], d["next_offset"])'
note-demo 162 None
```

## An empty answer names per-term hit counts

```scrut
$ los search zzzqqq-no-hit --type note
[]
```

```scrut {output_stream: stderr}
$ los search zzzqqq-no-hit --type note
los: no record matches all 1 term; per-term record hits: zzzqqq-no-hit=0
```

## On an always-JSON read, --json changes nothing

```scrut
$ los inspect unit-demo-l01 > "$TMPDIR/start-here-plain.json" && los inspect unit-demo-l01 --json > "$TMPDIR/start-here-json.json" && cmp "$TMPDIR/start-here-plain.json" "$TMPDIR/start-here-json.json" && echo identical
identical
```

## The study suggestion never moves the resume pointer

```scrut
$ A=$(sha256sum curriculum/resume.yaml) && los resume --study > /dev/null && B=$(sha256sum curriculum/resume.yaml) && test "$A" = "$B" && echo pointer-stable
pointer-stable
```

## Read one ability through the bounded horizon

```scrut
$ los ability-context ability-demo-derive --brief | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["focus"], d["ability"]["id"], d["brief"])'
ability-demo-derive ability-demo-derive True
```

## Ask a governance question through the semantic surface

```scrut
$ los semantic --list | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(len(d))'
26
```
