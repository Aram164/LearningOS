---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Complete and archive a workspace (WORKFLOWS §11)

Executable transcript of completing the path-owning demo workspace in
place: its durable knowledge already landed as a linked note, no
coordination dependency references it, its status flips to complete,
generated files are rebuilt and validated, and it stays at its existing
location — the path schema and ownership validator do not support
relocating its notes, attachments and shelving references (M-05 in
`tests/architecture/mismatches.yaml` pins the refused move; no gateway
capability archives a workspace). `tests/test_procedures.py` runs it
with Scrut; `<REPO>` comes from the `LOS_REPO` environment variable the
test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## The durable knowledge already landed as a linked note

1. identify durable knowledge created or changed;
2. update or create notes;
3. add warranted source evaluations and concept relations;
4. ensure the workspace links to final durable notes;
5. clear dependencies referencing this workspace from `COORDINATION.md`;
6. set `status: complete`;
7. rebuild and validate generated files;
8. a workspace without learning paths may move whole to
   `archive/workspaces/<year>/<workspace-id>/`, after checking explicit path
   links. A workspace that owns learning paths stays at its existing location
   with `status: complete`: the path schema and ownership validator do not
   support relocating its notes, attachments and shelving references to the
   archive. Never attempt an unchanged move or hand-repair those pointers.

```scrut
$ los inspect note-demo | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["id"], d["title"])'
note-demo Demo note
```

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import yaml; d = yaml.safe_load(open("work/active/workspace-demo/CONTEXT.md").read().split("---\n")[1]); print(d["notes"])'
['note-demo']
```

## No coordination dependency references the workspace

```scrut
$ grep -c "workspace-demo" work/COORDINATION.md || echo "no workspace reference to clear"
0
no workspace reference to clear
```

## No gateway capability archives a workspace

```scrut
$ los capabilities | grep -o "workspace[a-z.-]*" | sort -u
workspace.next-action.update
```

## Set status complete

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import yaml; p = "work/active/workspace-demo/CONTEXT.md"; t = open(p).read(); head, rest = t.split("---\n")[1:3]; d = yaml.safe_load(head); d["status"] = "complete"; open(p, "w").write("---\n" + yaml.safe_dump(d, sort_keys=False) + "---\n" + rest); print("completed", d["id"])'
completed workspace-demo
```

```scrut
$ grep -n "status: complete" work/active/workspace-demo/CONTEXT.md
6:status: complete
```

## Rebuild and validate the generated files

```scrut
$ los generate
published generated/manifest.json (atomic contract snapshot)
```

```scrut
$ (set -o pipefail; los validate | tail -n 1)
0 error(s), 13 warning(s) — OK
```

## The path-owning workspace stays in place (M-05)

```scrut
$ $H/los-assert-file work/active/workspace-demo/CONTEXT.md --exists
```

```scrut
$ $H/los-assert-file archive/workspaces/2026/workspace-demo --absent
```
