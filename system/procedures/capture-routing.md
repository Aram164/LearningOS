---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Capture routing (OPERATOR)

Executable transcript of the `log:` path: when the stage was explicitly
identified, the text is appended to that stage's working note through
`stage.note.write`; otherwise it goes to the inbox through
`capture.create`. Neither capture moves the resume pointer or implies
progress. `tests/test_procedures.py` runs it with Scrut; `<REPO>` comes
from the `LOS_REPO` environment variable the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## A logged line for an identified stage seals a stage-note envelope

```scrut {output_stream: stderr}
$ $H/los-seal --capability stage.note.write --payload '{"unit_id": "unit-demo-l01", "stage_id": "stage-demo", "text": "Log: the derivation finally clicked."}' --key log-stage-note-001 --request-id request-log-stage-note-001 --guards auto --out "$TMPDIR/log-stage-note.json"
seal_envelope: guards auto: unit-demo-l01=3
```

## Submit the envelope

```scrut
$ los capability stage.note.write --payload-file "$TMPDIR/log-stage-note.json"
{
  "schema_version": 2,
  "request_id": "request-log-stage-note-001",
  "idempotency_key": "log-stage-note-001",
  "capability": "stage.note.write",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:614338305a1c4cdfd8e1f68aba8859668c2025b62b9883ec2405b837e78dfe83",
  "result": {
    "ok": true,
    "unit_id": "unit-demo-l01",
    "stage_id": "stage-demo",
    "working_note": "curriculum/modules/module-demo/units/unit-demo-l01/stages/stage-demo/notes.md",
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "unit-demo-l01": 4
    },
    "snapshot_after": "sha256:614338305a1c4cdfd8e1f68aba8859668c2025b62b9883ec2405b837e78dfe83",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability stage.note.write
```

## The line landed in the stage working note

```scrut
$ $H/los-assert-file curriculum/modules/module-demo/units/unit-demo-l01/stages/stage-demo/notes.md --sha256 2075907701a7799cf602dd36721722000f68fff0a7a772034b1e716bc7a49599
```

## A logged line with no stage seals an inbox capture

```scrut {output_stream: stderr}
$ $H/los-seal --capability capture.create --payload '{"text": "Log: a stray thought with no stage yet."}' --key log-capture-001 --request-id request-log-capture-001 --guards auto --out "$TMPDIR/log-capture.json"
seal_envelope: guards auto: capture-request:log-capture-001=0
```

## Submit the envelope

```scrut
$ los capability capture.create --payload-file "$TMPDIR/log-capture.json"
{
  "schema_version": 2,
  "request_id": "request-log-capture-001",
  "idempotency_key": "log-capture-001",
  "capability": "capture.create",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-002",
  "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
  "snapshot_after": "sha256:78b9a8c5a0fab98a0452abd7a63e9556b9eb6b5ae7b4733ce66d4c255b4f1060",
  "result": {
    "ok": true,
    "captured": "work/inbox/20261001-090000-log-a-stray-thought-with-no-stage-yet.md",
    "transaction_id": "transaction-20261001-090000-002",
    "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
    "artifact_revisions": {
      "capture-request:log-capture-001": 1
    },
    "snapshot_after": "sha256:78b9a8c5a0fab98a0452abd7a63e9556b9eb6b5ae7b4733ce66d4c255b4f1060",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability capture.create
```

## The drop landed in the inbox

```scrut
$ $H/los-assert-file work/inbox/20261001-090000-log-a-stray-thought-with-no-stage-yet.md --sha256 f2fdae6823a4d213b2faed613cffa09661caef3b46d8703ee894097e674de2a5
```

## The resume pointer did not move

```scrut
$ $H/los-assert-file curriculum/resume.yaml --sha256 1360307adc4f3cf81ae20860966e3e53d87eb779bfed8284ca970314c58fd858
```

## The study map shows no progress either

```scrut
$ $H/los-assert-file curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml --sha256 506b0fdd350e11960069e09ffd099e7ac616076a8b3425557614e9167bbfe141
```
