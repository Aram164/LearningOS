---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Unit workflow (OPERATOR)

Executable transcript of the learner's choice list: run bare, a named
command never writes, so a `unit.source-selection.set` envelope removes
and re-selects a choice on `unit-demo-l02`. A choice naming a route the
unit does not expose is refused, and so is removing a choice the study
path uses — except that the study-path guard keys on recorded `stage_ids`
and the wired choice carries none (M-03 in
`tests/architecture/mismatches.yaml`). `tests/test_procedures.py` runs it
with Scrut; `<REPO>` comes from the `LOS_REPO` environment variable the
test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Run bare, a named command never writes

```scrut {output_stream: stderr}
$ los unit-source-selection unit-demo-l02 source-demo-book lecture-02.pdf remove
canonical writes must use GatewayEnvelopeV2; direct CLI application is disabled — apply it with `los capability unit.source-selection.set --payload-file ENVELOPE.json` (payload schema: `los capabilities unit.source-selection.set --json`; envelope: WORKFLOWS §25c)
[2]
```

## Seal the removal with derived guards

```scrut {output_stream: stderr}
$ $H/los-seal --capability unit.source-selection.set --payload '{"unit_id": "unit-demo-l02", "source_id": "source-demo-book", "locator": "lecture-02.pdf", "action": "remove"}' --key sel-remove-l02 --request-id request-sel-remove-l02 --guards auto --out "$TMPDIR/sel-remove.json"
seal_envelope: guards auto: unit-demo-l02=0
```

## Submit the envelope

```scrut
$ los capability unit.source-selection.set --payload-file "$TMPDIR/sel-remove.json"
{
  "schema_version": 2,
  "request_id": "request-sel-remove-l02",
  "idempotency_key": "sel-remove-l02",
  "capability": "unit.source-selection.set",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:3cd982e05a018a422cee05bd73ef01354499ebbafd98604719ad9ff77947cbaf",
  "result": {
    "ok": true,
    "unit_id": "unit-demo-l02",
    "source_id": "source-demo-book",
    "locator": "lecture-02.pdf",
    "selected": false,
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "unit-demo-l02": 1
    },
    "snapshot_after": "sha256:3cd982e05a018a422cee05bd73ef01354499ebbafd98604719ad9ff77947cbaf",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability unit.source-selection.set
```

## The choice list changed

```scrut
$ $H/los-assert-file curriculum/modules/module-demo/units/unit-demo-l02/unit.yaml --sha256 c06a0d182e5b0675f9b92a397b3bfd033d1bbfb9b702c859d8db51e36eeef06e
```

## Seal the re-selection with derived guards

```scrut {output_stream: stderr}
$ $H/los-seal --capability unit.source-selection.set --payload '{"unit_id": "unit-demo-l02", "source_id": "source-demo-book", "locator": "lecture-02.pdf", "action": "select", "purpose": "Follow-up derivation"}' --key sel-select-l02 --request-id request-sel-select-l02 --guards auto --out "$TMPDIR/sel-select.json"
seal_envelope: guards auto: unit-demo-l02=1
```

## Submit the envelope

```scrut
$ los capability unit.source-selection.set --payload-file "$TMPDIR/sel-select.json"
{
  "schema_version": 2,
  "request_id": "request-sel-select-l02",
  "idempotency_key": "sel-select-l02",
  "capability": "unit.source-selection.set",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-002",
  "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
  "snapshot_after": "sha256:4d71a399bd856b39c0b30b2fc074ad39539dcbf1a2b76b756b9b2424f25f6aa5",
  "result": {
    "ok": true,
    "unit_id": "unit-demo-l02",
    "source_id": "source-demo-book",
    "locator": "lecture-02.pdf",
    "selected": true,
    "transaction_id": "transaction-20261001-090000-002",
    "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
    "artifact_revisions": {
      "unit-demo-l02": 2
    },
    "snapshot_after": "sha256:4d71a399bd856b39c0b30b2fc074ad39539dcbf1a2b76b756b9b2424f25f6aa5",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability unit.source-selection.set
```

## The choice list carries the restored choice

```scrut
$ $H/los-assert-file curriculum/modules/module-demo/units/unit-demo-l02/unit.yaml --sha256 dcf9ea53d7adc946b30d34d9199ad18612903d2cd2cf036979e7dc41a0bbd530
```

## A route the unit does not expose is refused

```scrut {output_stream: stderr}
$ $H/los-seal --capability unit.source-selection.set --payload '{"unit_id": "unit-demo-l01", "source_id": "source-demo-book", "locator": "lecture-02.pdf", "action": "select"}' --key sel-cross-l01 --request-id request-sel-cross-l01 --guards auto --out "$TMPDIR/sel-cross.json"
seal_envelope: los: selection must match one rich material route on this unit (source-demo-book · lecture-02.pdf); fix the payload and seal again
[2]
```

## Seal the wired removal

`unit-demo-l01` has a study map whose stage uses the selected material,
so this removal is the one the contract says is refused.

```scrut {output_stream: stderr}
$ $H/los-seal --capability unit.source-selection.set --payload '{"unit_id": "unit-demo-l01", "source_id": "source-demo-book", "locator": "lecture-01.pdf", "action": "remove"}' --key sel-remove-l01 --request-id request-sel-remove-l01 --guards auto --out "$TMPDIR/sel-wired.json"
seal_envelope: guards auto: unit-demo-l01=3
```

## The wired removal commits (M-03)

Observed: the removal commits instead of refusing, because the guard
fires only on recorded `stage_ids` and the choice carries none. Recorded
as M-03 in `tests/architecture/mismatches.yaml`; this case pins the
observed commit until the conductor's decision lands.

```scrut
$ los capability unit.source-selection.set --payload-file "$TMPDIR/sel-wired.json"
{
  "schema_version": 2,
  "request_id": "request-sel-remove-l01",
  "idempotency_key": "sel-remove-l01",
  "capability": "unit.source-selection.set",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-003",
  "receipt_path": "operations/transactions/transaction-20261001-090000-003.yaml",
  "snapshot_after": "sha256:030d537669a26b7ff79ffe7d8d1e195e79fdc12af4c528e931641d921b08777d",
  "result": {
    "ok": true,
    "unit_id": "unit-demo-l01",
    "source_id": "source-demo-book",
    "locator": "lecture-01.pdf",
    "selected": false,
    "transaction_id": "transaction-20261001-090000-003",
    "receipt_path": "operations/transactions/transaction-20261001-090000-003.yaml",
    "artifact_revisions": {
      "unit-demo-l01": 4
    },
    "snapshot_after": "sha256:030d537669a26b7ff79ffe7d8d1e195e79fdc12af4c528e931641d921b08777d",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability unit.source-selection.set
```
