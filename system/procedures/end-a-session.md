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

## Bind the snapshot for the stale write

```scrut
$ eval "$(los bootstrap --brief | $H/los-bind SNAP '$.snapshot_id')"
```

## Seal the note envelope against that snapshot

```scrut
$ $H/los-seal --capability unit.note.append --payload '{"unit_id": "unit-demo-l01", "title": "Stale attempt", "text": "Sealed before the stage write."}' --key end-a-session-stale-001 --request-id request-end-a-session-stale-001 --snapshot "$SNAP" --out "$TMPDIR/unit-note.json"
```

## Step 1: seal the stage-progress envelope

```scrut {output_stream: stderr}
$ $H/los-seal --capability stage.progress.update --payload '{"unit_id": "unit-demo-l01", "stage_id": "stage-demo", "status": "complete"}' --key end-a-session-stage-001 --request-id request-end-a-session-stage-001 --guards auto --out "$TMPDIR/stage-progress.json"
seal_envelope: guards auto: study-map-demo-l01=0, unit-demo-l01=3
```

## The sealed envelope's sha256, before submission

```scrut
$ $H/los-assert-file "$TMPDIR/stage-progress.json" --sha256 6914b91a7b2f94b9eb51b1d0deb007e00edfc9b928a0dae9cdc64a8d2c391ef9
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
  "snapshot_after": "sha256:7b13031aef344da7a0eabae73799808314e2ecefc943850c4c5c145ae3596b9c",
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
    "snapshot_after": "sha256:7b13031aef344da7a0eabae73799808314e2ecefc943850c4c5c145ae3596b9c",
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
      "expected": "sha256:ac0eddef5a3c78e2abcc20ba5941b2ba613d600b9125e10d827683c5628c60bc",
      "actual": "sha256:7b13031aef344da7a0eabae73799808314e2ecefc943850c4c5c145ae3596b9c"
    }
  }
}
[3]
```

## Step 3: review the session

```scrut
$ los session-end
{
  "ok": true,
  "touched": [
    "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml",
    "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml",
    "curriculum/resume.yaml",
    "operations/transactions/idempotency.yaml",
    "operations/transactions/revisions.yaml",
    "operations/transactions/transaction-20261001-090000-001.yaml"
  ],
  "owned_changes": [
    " M curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml",
    " M curriculum/resume.yaml",
    " M operations/transactions/revisions.yaml",
    "?? operations/transactions/idempotency.yaml",
    "?? operations/transactions/transaction-20261001-090000-001.yaml"
  ],
  "unrelated_changes": [
    "?? operations/diagnostics/traces.jsonl"
  ],
  "committed": false,
  "pushed": false,
  "validation": "0 error(s), 9 warning(s) * (glob)
  "ownership_conflicts": [],
  "session_id": "channel:operator",
  "client": null,
  "stale_paths": [],
  "stale_hours": 24,
  "other_sessions": {},
  "session_closed": false
}
```

## Step 3 rerun: the review shows the same list

A bare review never closes the session, so running it twice shows the
same list.

```scrut
$ los session-end
{
  "ok": true,
  "touched": [
    "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml",
    "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml",
    "curriculum/resume.yaml",
    "operations/transactions/idempotency.yaml",
    "operations/transactions/revisions.yaml",
    "operations/transactions/transaction-20261001-090000-001.yaml"
  ],
  "owned_changes": [
    " M curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml",
    " M curriculum/resume.yaml",
    " M operations/transactions/revisions.yaml",
    "?? operations/transactions/idempotency.yaml",
    "?? operations/transactions/transaction-20261001-090000-001.yaml"
  ],
  "unrelated_changes": [
    "?? operations/diagnostics/traces.jsonl"
  ],
  "committed": false,
  "pushed": false,
  "validation": "0 error(s), 9 warning(s) * (glob)
  "ownership_conflicts": [],
  "session_id": "channel:operator",
  "client": null,
  "stale_paths": [],
  "stale_hours": 24,
  "other_sessions": {},
  "session_closed": false
}
```

## Step 4: commit the session

```scrut
$ los session-end --commit-message "end-a-session transcript commit"
{
  "ok": true,
  "touched": [
    "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml",
    "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml",
    "curriculum/resume.yaml",
    "operations/transactions/idempotency.yaml",
    "operations/transactions/revisions.yaml",
    "operations/transactions/transaction-20261001-090000-001.yaml"
  ],
  "owned_changes": [
    " M curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml",
    " M curriculum/resume.yaml",
    " M operations/transactions/revisions.yaml",
    "?? operations/transactions/idempotency.yaml",
    "?? operations/transactions/transaction-20261001-090000-001.yaml"
  ],
  "unrelated_changes": [
    "?? operations/diagnostics/traces.jsonl"
  ],
  "committed": true,
  "pushed": false,
  "validation": "0 error(s), 9 warning(s) * (glob)
  "ownership_conflicts": [],
  "session_id": "channel:operator",
  "client": null,
  "stale_paths": [],
  "stale_hours": 24,
  "other_sessions": {},
  "session_closed": true
}
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
