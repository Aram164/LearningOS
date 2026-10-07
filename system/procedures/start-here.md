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

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
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
3 3 lineage-stale
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
