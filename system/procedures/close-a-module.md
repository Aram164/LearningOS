---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Close a module (WORKFLOWS §19)

Executable transcript of closing the demo module after its final
sitting: the passing result and grade land on the attempt, the module
status flips to completed, the durable knowledge is confirmed in place,
the workspace completes, the dead deferral leaves coordination, nothing
outlives the module so no carry runs, and the tree is rebuilt and
validated. No approved capability writes the module status, so that one
edit runs only in this disposable transcript fixture.
`tests/test_procedures.py` runs it with Scrut; `<REPO>` comes from the
`LOS_REPO` environment variable the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Record the final sitting on the attempt

1. **Settle the record** in the owning partitioned academic `module.yaml` only
   (workflow 10). Record the final sitting or submission on the attempt
   (`result: passed`/`failed`). When the grade posts, record it and set
   `status: completed` (or `dropped` if abandoned) through `module.status.update`
   (`module-status-update`, envelope recipe §25c); while a grade is pending,
   preserve that administrative state explicitly.
2. **Confirm durable knowledge landed — before archiving.** For each of the module's workspaces, verify the understanding worth keeping is already a note under `knowledge/`; extend or create as needed (workflow 3; workflow 17 for handwritten pages). An archived workspace is frozen, so promotion happens first, never after.
3. **Complete each workspace** (workflow 11 for every workspace the module owns): durable links confirmed and `status: complete` through `workspace.complete` (`workspace-complete`, envelope recipe §25c). Completed workspaces stay in place; a workspace enters the separately reviewed archive migration only after its explicit path links are checked. Completion waits on step 2, not on the grade. Skip any `standing: true` effort — it is exempt and does not close with the module.
4. **Clear operational state.** Remove the module's now-dead entries from `COORDINATION.md` — resolved dependencies, satisfied deferrals, stale priorities and commitments (workflow 9). Coordination should not mention a closed module.
5. **Carry-over check.** If anything outlives the module — a second attempt not yet sat, thesis groundwork, an unfinished thread — route it through workflow 20 instead of archiving it away.
6. **Rebuild and validate.**

```scrut {output_stream: stderr}
$ $H/los-seal --capability module.attempt.record --payload '{"module_id": "module-demo", "termin": 2, "date": "2026-10-09", "result": "passed"}' --key s19-pass --request-id request-s19-pass --guards auto --out "$TMPDIR/s19-pass.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
seal_envelope: guards auto: module-demo=0
```

```scrut {interpolated: true}
$ los capability module.attempt.record --payload-file "$TMPDIR/s19-pass.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
{"schema_version":2,"request_id":"request-s19-pass","idempotency_key":"s19-pass","capability":"module.attempt.record","ok":true,"replayed":false,"transaction_id":"transaction-20261001-090000-001","receipt_path":"operations/transactions/transaction-20261001-090000-001.yaml","snapshot_after":"$LOS_FIXTURE_SNAPSHOT_2","result":{"ok":true,"module_id":"module-demo","attempt":{"termin":2,"date":"2026-10-09","result":"passed"},"transaction_id":"transaction-20261001-090000-001","receipt_path":"operations/transactions/transaction-20261001-090000-001.yaml","artifact_revisions":{"module-demo":1},"snapshot_after":"$LOS_FIXTURE_SNAPSHOT_2","replayed":false},"error":null}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability module.attempt.record
```

## Record the posted grade

```scrut {output_stream: stderr}
$ $H/los-seal --capability module.attempt.record --payload '{"module_id": "module-demo", "termin": 2, "date": "2026-10-09", "result": "passed", "grade": 1.0}' --key s19-grade --request-id request-s19-grade --guards auto --out "$TMPDIR/s19-grade.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
seal_envelope: guards auto: module-demo=1
```

```scrut {interpolated: true}
$ los capability module.attempt.record --payload-file "$TMPDIR/s19-grade.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
{"schema_version":2,"request_id":"request-s19-grade","idempotency_key":"s19-grade","capability":"module.attempt.record","ok":true,"replayed":false,"transaction_id":"transaction-20261001-090000-002","receipt_path":"operations/transactions/transaction-20261001-090000-002.yaml","snapshot_after":"$LOS_FIXTURE_SNAPSHOT_3","result":{"ok":true,"module_id":"module-demo","attempt":{"termin":2,"date":"2026-10-09","result":"passed","grade":1.0},"transaction_id":"transaction-20261001-090000-002","receipt_path":"operations/transactions/transaction-20261001-090000-002.yaml","artifact_revisions":{"module-demo":2},"snapshot_after":"$LOS_FIXTURE_SNAPSHOT_3","replayed":false},"error":null}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability module.attempt.record
```

## Set the module status to completed

```scrut {output_stream: stderr}
$ $H/los-seal --capability module.status.update --payload '{"module_id": "module-demo", "status": "completed"}' --key s19-status --request-id request-s19-status --guards auto --out "$TMPDIR/s19-status.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
seal_envelope: guards auto: module-demo=2
```

```scrut {interpolated: true}
$ los capability module.status.update --payload-file "$TMPDIR/s19-status.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
{"schema_version":2,"request_id":"request-s19-status","idempotency_key":"s19-status","capability":"module.status.update","ok":true,"replayed":false,"transaction_id":"transaction-20261001-090000-003","receipt_path":"operations/transactions/transaction-20261001-090000-003.yaml","snapshot_after":"$LOS_FIXTURE_SNAPSHOT_4","result":{"ok":true,"module_id":"module-demo","status":"completed","path":"curriculum/modules/module-demo/module.yaml","transaction_id":"transaction-20261001-090000-003","receipt_path":"operations/transactions/transaction-20261001-090000-003.yaml","artifact_revisions":{"module-demo":3},"snapshot_after":"$LOS_FIXTURE_SNAPSHOT_4","replayed":false},"error":null}
```

```scrut
$ $H/los-assert-receipt --last --capability module.status.update
```

```scrut
$ grep -n "status: completed" curriculum/modules/module-demo/module.yaml
8:status: completed
```

## Confirm the durable knowledge landed before archiving

```scrut
$ los inspect note-demo | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["id"], d["title"])'
note-demo Demo note
```

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import yaml; d = yaml.safe_load(open("work/active/workspace-demo/CONTEXT.md").read().split("---\n")[1]); print(d["notes"])'
['note-demo']
```

## Complete the module's workspace

```scrut {output_stream: stderr}
$ $H/los-seal --capability workspace.complete --payload '{"workspace_id": "workspace-demo"}' --key s19-complete-ws --request-id request-s19-complete-ws --guards auto --out "$TMPDIR/s19-complete-ws.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
seal_envelope: guards auto: workspace-demo=0
```

```scrut {interpolated: true}
$ los capability workspace.complete --payload-file "$TMPDIR/s19-complete-ws.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
{"schema_version":2,"request_id":"request-s19-complete-ws","idempotency_key":"s19-complete-ws","capability":"workspace.complete","ok":true,"replayed":false,"transaction_id":"transaction-20261001-090000-004","receipt_path":"operations/transactions/transaction-20261001-090000-004.yaml","snapshot_after":"$LOS_FIXTURE_SNAPSHOT_5","result":{"ok":true,"workspace_id":"workspace-demo","status":"complete","path":"work/active/workspace-demo/CONTEXT.md","transaction_id":"transaction-20261001-090000-004","receipt_path":"operations/transactions/transaction-20261001-090000-004.yaml","artifact_revisions":{"workspace-demo":1},"snapshot_after":"$LOS_FIXTURE_SNAPSHOT_5","replayed":false},"error":null}
```

```scrut
$ $H/los-assert-receipt --last --capability workspace.complete
```

## Clear the dead deferral from coordination

```scrut
$ grep "Demo module deferred" work/COORDINATION.md
- Demo module deferred to 2. Termin (date lives in records/modules.yaml)
```

```scrut
$ eval "$(los inspect coordination | $H/los-bind COORD_SHA '$.content_sha256')" && echo "$COORD_SHA"
sha256:667bbd75392b1acdc610aa249aa5f2fe3d7659603901f415b36eda30fe2b4655
```

```scrut {output_stream: stderr}
$ $H/los-seal --capability coordination.section.revise --payload "{\"section\": \"Deferrals\", \"text\": \"(none)\", \"expected_content_sha256\": \"$COORD_SHA\"}" --key s19-defer --guards auto --check-out "$TMPDIR/s19-defer-check.json" > /dev/null
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
seal_envelope: guards auto: coordination=0
```

Inspect the saved check report before approving the revision. Seal the approved draft with the report's guards.

```scrut
$ $H/los-seal --guards-from "$TMPDIR/s19-defer-check.json" --request-id request-s19-defer --out "$TMPDIR/s19-defer.json"
```

```scrut {interpolated: true}
$ los capability coordination.section.revise --payload-file "$TMPDIR/s19-defer.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
{"schema_version":2,"request_id":"request-s19-defer","idempotency_key":"s19-defer","capability":"coordination.section.revise","ok":true,"replayed":false,"transaction_id":"transaction-20261001-090000-005","receipt_path":"operations/transactions/transaction-20261001-090000-005.yaml","snapshot_after":"$LOS_FIXTURE_SNAPSHOT_6","result":{"ok":true,"section":"Deferrals","transaction_id":"transaction-20261001-090000-005","receipt_path":"operations/transactions/transaction-20261001-090000-005.yaml","artifact_revisions":{"coordination":1},"snapshot_after":"$LOS_FIXTURE_SNAPSHOT_6","replayed":false},"error":null}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability coordination.section.revise
```

## Carry-over check: nothing outlives the module

```scrut
$ los module-list | $LOS_REPO/.venv/bin/python -c 'import json,sys; print([(a["termin"], a["result"]) for m in json.load(sys.stdin) for a in m["attempts"]])'
[(1, 'withdrawn'), (2, 'passed')]
```

The final attempt is sat and passed with no further attempt ahead, so
nothing routes through the carry workflow.

## Rebuild and validate

```scrut
$ los generate
published generated/manifest.json (atomic contract snapshot)
```

```scrut
$ (set -o pipefail; los validate | tail -n 1)
0 error(s), 12 warning(s) — OK
```
