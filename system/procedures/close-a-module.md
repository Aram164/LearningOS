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

```scrut {output_stream: stderr}
$ $H/los-seal --capability module.attempt.record --payload '{"module_id": "module-demo", "termin": 2, "date": "2026-10-09", "result": "passed"}' --key s19-pass --request-id request-s19-pass --guards auto --out "$TMPDIR/s19-pass.json"
seal_envelope: guards auto: module-demo=0
```

```scrut
$ los capability module.attempt.record --payload-file "$TMPDIR/s19-pass.json"
{
  "schema_version": 2,
  "request_id": "request-s19-pass",
  "idempotency_key": "s19-pass",
  "capability": "module.attempt.record",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:a224db865bf4e4be1c44d6dbb67a01d3106613a52c73933b47de6c8f229f54d1",
  "result": {
    "ok": true,
    "module_id": "module-demo",
    "attempt": {
      "termin": 2,
      "date": "2026-10-09",
      "result": "passed"
    },
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "module-demo": 1
    },
    "snapshot_after": "sha256:a224db865bf4e4be1c44d6dbb67a01d3106613a52c73933b47de6c8f229f54d1",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability module.attempt.record
```

## Record the posted grade

```scrut {output_stream: stderr}
$ $H/los-seal --capability module.attempt.record --payload '{"module_id": "module-demo", "termin": 2, "date": "2026-10-09", "result": "passed", "grade": 1.0}' --key s19-grade --request-id request-s19-grade --guards auto --out "$TMPDIR/s19-grade.json"
seal_envelope: guards auto: module-demo=1
```

```scrut
$ los capability module.attempt.record --payload-file "$TMPDIR/s19-grade.json"
{
  "schema_version": 2,
  "request_id": "request-s19-grade",
  "idempotency_key": "s19-grade",
  "capability": "module.attempt.record",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-002",
  "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
  "snapshot_after": "sha256:5b7909b63f4f954b9d55771a525c4400ae70f741595054a5c86952bbccd21ece",
  "result": {
    "ok": true,
    "module_id": "module-demo",
    "attempt": {
      "termin": 2,
      "date": "2026-10-09",
      "result": "passed",
      "grade": 1.0
    },
    "transaction_id": "transaction-20261001-090000-002",
    "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
    "artifact_revisions": {
      "module-demo": 2
    },
    "snapshot_after": "sha256:5b7909b63f4f954b9d55771a525c4400ae70f741595054a5c86952bbccd21ece",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability module.attempt.record
```

## Set the module status to completed

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import yaml; p = "curriculum/modules/module-demo/module.yaml"; d = yaml.safe_load(open(p)); d["status"] = "completed"; open(p, "w").write(yaml.safe_dump(d, sort_keys=False)); print("status", d["status"])'
status completed
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

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import yaml; p = "work/active/workspace-demo/CONTEXT.md"; t = open(p).read(); head, rest = t.split("---\n")[1:3]; d = yaml.safe_load(head); d["status"] = "complete"; open(p, "w").write("---\n" + yaml.safe_dump(d, sort_keys=False) + "---\n" + rest); print("completed", d["id"])'
completed workspace-demo
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
$ $H/los-seal --capability coordination.section.revise --payload "{\"section\": \"Deferrals\", \"text\": \"(none)\", \"expected_content_sha256\": \"$COORD_SHA\"}" --key s19-defer --request-id request-s19-defer --guards auto --out "$TMPDIR/s19-defer.json"
seal_envelope: guards auto: coordination=0
```

```scrut
$ los capability coordination.section.revise --payload-file "$TMPDIR/s19-defer.json"
{
  "schema_version": 2,
  "request_id": "request-s19-defer",
  "idempotency_key": "s19-defer",
  "capability": "coordination.section.revise",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-003",
  "receipt_path": "operations/transactions/transaction-20261001-090000-003.yaml",
  "snapshot_after": "sha256:234f8f9dd5200ea56dfd8d59e2b47deef94944a15f8f4248e4788021a88c2f5a",
  "result": {
    "ok": true,
    "section": "Deferrals",
    "transaction_id": "transaction-20261001-090000-003",
    "receipt_path": "operations/transactions/transaction-20261001-090000-003.yaml",
    "artifact_revisions": {
      "coordination": 1
    },
    "snapshot_after": "sha256:234f8f9dd5200ea56dfd8d59e2b47deef94944a15f8f4248e4788021a88c2f5a",
    "replayed": false
  },
  "error": null
}
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
0 error(s), 9 warning(s) — OK
```
