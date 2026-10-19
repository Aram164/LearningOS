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
path uses. Usage comes from the current map's resource references, rather
than optional selection metadata (M-03 resolved 2026-10-10).
`tests/test_procedures.py` runs it
with Scrut; `<REPO>` comes from the `LOS_REPO` environment variable the
test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Run bare, a named command never writes

Choose a module and unit. First inspect its knowledge map and complete material
menu, grouped by format and annotated with angle, depth, scope, and coverage.
Record actual choices in `source_selections`. If ordered tracking would help,
the unit may then have at most one current study map using only those choices.
Work in its stages while preserving independent state for every other unit.

```scrut {output_stream: stderr}
$ los unit-source-selection unit-demo-l02 source-demo-book lecture-02.pdf remove
los: INVALID_REQUEST: canonical writes must use GatewayEnvelopeV2; direct CLI application is disabled — apply it with `los capability unit.source-selection.set --payload-file ENVELOPE.json` (payload schema: `los capabilities unit.source-selection.set --json`; envelope: WORKFLOWS §25c)
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
  "snapshot_after": "sha256:1058b40994ebcf3ecd15a552f45da97c6a65ff8d112e5ef402d29c7a8ac44b75",
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
    "snapshot_after": "sha256:1058b40994ebcf3ecd15a552f45da97c6a65ff8d112e5ef402d29c7a8ac44b75",
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
  "snapshot_after": "sha256:2285d95f09dd05f4a2dc02e34a0cacfb1077825be77aadb2ae255c0258a0c3fc",
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
    "snapshot_after": "sha256:2285d95f09dd05f4a2dc02e34a0cacfb1077825be77aadb2ae255c0258a0c3fc",
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
seal_envelope: selection must match one rich material route on this unit (source-demo-book · lecture-02.pdf); fix the payload and seal again
[2]
```

## The wired removal is refused while deriving guards

`unit-demo-l01` has a study map whose stage uses the selected material.
The same guard refuses both automatic sealing and submission of an envelope
constructed explicitly (the latter is checked by `tests/test_mismatches.py`).

```scrut {output_stream: stderr}
$ $H/los-seal --capability unit.source-selection.set --payload '{"unit_id": "unit-demo-l01", "source_id": "source-demo-book", "locator": "lecture-01.pdf", "action": "remove"}' --key sel-remove-l01 --request-id request-sel-remove-l01 --guards auto --out "$TMPDIR/sel-wired.json"
seal_envelope: this choice is used by the current study path; remove it from those stages before removing the choice; fix the payload and seal again
[2]
```

## No refused envelope was produced

```scrut
$ test ! -f "$TMPDIR/sel-wired.json"
```

## The previous successful receipt remains the newest

```scrut
$ $H/los-assert-receipt --last --capability unit.source-selection.set
```
