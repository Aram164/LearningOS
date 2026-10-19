---
defaults:
  environment:
    TZ: Europe/Berlin
---

# End a session (WORKFLOWS §22)

Executable transcript of the procedure: the learner write it needs, then
save, review, commit and verify. `tests/test_procedures.py` runs it with
Scrut; `<REPO>` comes from the `LOS_REPO` environment variable the test
sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Read the stage-progress payload contract

These are gateway capabilities: `unit.source-selection.set`, `unit.note.append`,
`stage.progress.update`, `source.feedback.record`, `detour.create` (named
commands `unit-source-selection`, `unit-note`, `stage-progress`,
`source-feedback`, `detour-create`). Run bare, a named command never writes:
every canonical write refuses without a GatewayEnvelopeV2. Read the payload
schema, seal one envelope with `tools/seal_envelope.py --capability NAME
--payload @PAYLOAD.json --key UNIQUE-KEY --guards auto` — guard derivation
is the default path, WORKFLOWS §25c — then submit it:

```bash
.venv/bin/python tools/los.py capabilities stage.progress.update --json
.venv/bin/python tools/los.py capability stage.progress.update --payload-file ENVELOPE.json
```

Read the exact capability definition before sealing the stage write below.
The later submission checks its receipt and the changed canonical study map.

```scrut
$ los capabilities stage.progress.update --json | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(next(iter(d["commands"])), ",".join(d["payload_schema"]["properties"]["status"]["enum"]))'
stage.progress.update active,paused,complete,skipped,revisit
```

## Bind the snapshot for the stale write

```scrut
$ eval "$(los bootstrap --brief | $H/los-bind SNAP '$.snapshot_id')"
```

## Seal the note envelope against that snapshot

```scrut
$ $H/los-seal --capability unit.note.append --payload '{"unit_id": "unit-demo-l01", "title": "Stale attempt", "text": "Sealed before the stage write."}' --key end-a-session-stale-001 --request-id request-end-a-session-stale-001 --snapshot "$SNAP" --out "$TMPDIR/unit-note.json"
```

## Step 1: seal the stage-progress envelope

1. save pending stage work;
2. run `los session-end` without a commit message; it validates, regenerates,
   and shows session-owned files separately from unrelated changes;
3. review that exact list;
4. optionally rerun with `--commit-message` to commit exactly the files
   recorded in this session's ledger, and every `*.canvas` file is
   unconditionally excluded;
5. use `--push` only through the approved repository workflow.

```scrut {output_stream: stderr}
$ $H/los-seal --capability stage.progress.update --payload '{"unit_id": "unit-demo-l01", "stage_id": "stage-demo", "status": "complete"}' --key end-a-session-stage-001 --request-id request-end-a-session-stage-001 --guards auto --out "$TMPDIR/stage-progress.json"
seal_envelope: guards auto: study-map-demo-l01=0, unit-demo-l01=3
```

## The sealed envelope's sha256, before submission

```scrut
$ $H/los-assert-file "$TMPDIR/stage-progress.json" --sha256 f9272e5258a135b9eb968c1fc07bb7c2367c9a52565e1c164281ec76f51779aa
```

## Step 1: submit the stage-progress envelope

```scrut
$ los capability stage.progress.update --payload-file "$TMPDIR/stage-progress.json"
{
  "schema_version": 2,
  "request_id": "request-end-a-session-stage-001",
  "idempotency_key": "end-a-session-stage-001",
  "capability": "stage.progress.update",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:557c5a2bb512bc02ddd9ce1cdd8aeda9d8074e41b64d3ddfe1a671a288191a07",
  "result": {
    "ok": true,
    "unit_id": "unit-demo-l01",
    "stage_id": "stage-demo",
    "status": "complete",
    "map_status": "active",
    "current_stage": "stage-demo-pending",
    "observe_requirement": "req-demo-l01-demo",
    "observe_next": "los observe req-demo-l01-demo --activity <what-you-did> --result <correct|incorrect|partial|abandoned> --condition unfamiliar-example",
    "observe_conditions": [
      "unfamiliar-example"
    ],
    "observe_note": "keep only the conditions that actually held; an omitted one is read as unknown, never as met",
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "study-map-demo-l01": 1,
      "unit-demo-l01": 4
    },
    "snapshot_after": "sha256:557c5a2bb512bc02ddd9ce1cdd8aeda9d8074e41b64d3ddfe1a671a288191a07",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability stage.progress.update
```

## The canonical study map changed

```scrut
$ $H/los-assert-file curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml --sha256 b0309b06ab7979bc0b18042ea5e92af36f0269ba45ccf0e92f03d477c625281e
```

## Step 2: the note sealed earlier now refuses as stale

```scrut
$ los capability unit.note.append --payload-file "$TMPDIR/unit-note.json"
{
  "schema_version": 2,
  "request_id": "request-end-a-session-stale-001",
  "idempotency_key": "end-a-session-stale-001",
  "capability": "unit.note.append",
  "ok": false,
  "replayed": false,
  "transaction_id": null,
  "receipt_path": null,
  "snapshot_after": null,
  "result": {},
  "error": {
    "code": "STALE_SNAPSHOT",
    "message": "canonical state changed since this request was approved",
    "retryable": true,
    "details": {
      "expected": "sha256:08fdd4d86bb9d12fbb4b804df720b02a980031c30cb9f7007c9b425b46ef43c5",
      "actual": "sha256:557c5a2bb512bc02ddd9ce1cdd8aeda9d8074e41b64d3ddfe1a671a288191a07"
    }
  }
}
[3]
```

## Step 3: review the session

End a learning session deliberately with `los session-end`. First run it with
no commit message to review session-owned and unrelated changes; the review
never closes the session, so the ledger survives for the commit run. Only the
files recorded in this session's ledger may be staged — the ledger itself
lives in the git dir and is never staged. The protected Canvas files are
always excluded. Commit and optional push occur only after explicit
confirmation. To end the ownership window without committing, rerun with
`--close`: it deletes only this session's ledger.

```scrut
$ los session-end
{"ok":true,"touched":["curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml","curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml","curriculum/resume.yaml","operations/transactions/idempotency.yaml","operations/transactions/revisions.yaml","operations/transactions/transaction-20261001-090000-001.yaml"],"owned_changes":[" M curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"," M curriculum/resume.yaml"," M operations/transactions/revisions.yaml","?? operations/transactions/idempotency.yaml","?? operations/transactions/transaction-20261001-090000-001.yaml"],"unrelated_changes":["?? operations/diagnostics/traces.jsonl"],"committed":false,"pushed":false,"validation":"0 error(s), 9 warning(s) — OK; warning list: generated/reports/validation-report.md","ownership_conflicts":[],"session_id":"channel:operator","client":null,"stale_paths":[],"stale_hours":24,"other_sessions":{},"session_closed":false}
```

## Step 3 rerun: the review shows the same list

A bare review never closes the session, so running it twice shows the
same list.

```scrut
$ los session-end
{"ok":true,"touched":["curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml","curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml","curriculum/resume.yaml","operations/transactions/idempotency.yaml","operations/transactions/revisions.yaml","operations/transactions/transaction-20261001-090000-001.yaml"],"owned_changes":[" M curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"," M curriculum/resume.yaml"," M operations/transactions/revisions.yaml","?? operations/transactions/idempotency.yaml","?? operations/transactions/transaction-20261001-090000-001.yaml"],"unrelated_changes":["?? operations/diagnostics/traces.jsonl"],"committed":false,"pushed":false,"validation":"0 error(s), 9 warning(s) — OK; warning list: generated/reports/validation-report.md","ownership_conflicts":[],"session_id":"channel:operator","client":null,"stale_paths":[],"stale_hours":24,"other_sessions":{},"session_closed":false}
```

## Step 4: commit the session

```scrut
$ los session-end --commit-message "end-a-session transcript commit"
{"ok":true,"touched":["curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml","curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml","curriculum/resume.yaml","operations/transactions/idempotency.yaml","operations/transactions/revisions.yaml","operations/transactions/transaction-20261001-090000-001.yaml"],"owned_changes":[" M curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"," M curriculum/resume.yaml"," M operations/transactions/revisions.yaml","?? operations/transactions/idempotency.yaml","?? operations/transactions/transaction-20261001-090000-001.yaml"],"unrelated_changes":["?? operations/diagnostics/traces.jsonl"],"committed":true,"pushed":false,"validation":"0 error(s), 9 warning(s) — OK; warning list: generated/reports/validation-report.md","ownership_conflicts":[],"session_id":"channel:operator","client":null,"stale_paths":[],"stale_hours":24,"other_sessions":{},"session_closed":true}
```

## Step 5: the commit exists

```scrut
$ git -C "$LOS_FX" log --format=%s -1
end-a-session transcript commit
```

## Step 5: the session ledger is gone

```scrut
$ test -z "$(find "$LOS_FX/.git/learningos" -name '*-touched.json')"
```
