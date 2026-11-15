---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Complete and archive a workspace (WORKFLOWS §11)

Executable transcript of completing the demo workspace in place: its
durable knowledge already landed as a linked note, no coordination
dependency references it, its status flips to complete, generated files
are rebuilt and validated, and it stays at its existing location (no
gateway capability archives a workspace). `tests/test_procedures.py`
runs it with Scrut; `<REPO>` comes from the `LOS_REPO` environment
variable the test sets.

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
6. set `status: complete` through `workspace.complete` (`workspace-complete`);
7. rebuild and validate generated files;
8. a workspace moves whole to `archive/workspaces/<year>/<workspace-id>/`
   only after its explicit path links are checked. Rewrite any
   `source_plan.path` values that point into the folder being moved through
   `unit.plan.revise`.

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
workspace.complete
workspace.next-action.update
```

## Seal and submit `workspace.complete`

```scrut {output_stream: stderr}
$ $H/los-seal --capability workspace.complete --payload '{"workspace_id": "workspace-demo"}' --key workspace-complete-demo --request-id request-workspace-complete-demo --guards auto --out "$TMPDIR/workspace-complete.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
seal_envelope: guards auto: workspace-demo=0
```

```scrut {interpolated: true}
$ los capability workspace.complete --payload-file "$TMPDIR/workspace-complete.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
{"schema_version":2,"request_id":"request-workspace-complete-demo","idempotency_key":"workspace-complete-demo","capability":"workspace.complete","ok":true,"replayed":false,"transaction_id":"transaction-20261001-090000-001","receipt_path":"operations/transactions/transaction-20261001-090000-001.yaml","snapshot_after":"$LOS_FIXTURE_SNAPSHOT_2","result":{"ok":true,"workspace_id":"workspace-demo","status":"complete","path":"work/active/workspace-demo/CONTEXT.md","transaction_id":"transaction-20261001-090000-001","receipt_path":"operations/transactions/transaction-20261001-090000-001.yaml","artifact_revisions":{"workspace-demo":1},"snapshot_after":"$LOS_FIXTURE_SNAPSHOT_2","replayed":false},"error":null}
```

```scrut
$ $H/los-assert-receipt --last --capability workspace.complete
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
0 error(s), 12 warning(s) — OK
```

## The completed workspace stays in place

```scrut
$ $H/los-assert-file work/active/workspace-demo/CONTEXT.md --exists
```

```scrut
$ $H/los-assert-file archive/workspaces/2026/workspace-demo --absent
```
