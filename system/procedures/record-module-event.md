---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Record a module event (WORKFLOWS §10)

Executable transcript of settling one sitting: the bare attempt
command is refused, the sat attempt lands through its envelope, the
known withdrawal deadline lands on its sitting, the module status
stays enrolled while the grade is pending, and the module and
coordination views rebuild over the event. `tests/test_procedures.py`
runs it with Scrut; `<REPO>` comes from the `LOS_REPO` environment
variable the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## The bare attempt command is refused

```scrut {output_stream: stderr}
$ los module-attempt module-demo --termin 2 --date 2026-10-09 --result sat
canonical writes must use GatewayEnvelopeV2* (glob)
[2]
```

## Seal the attempt with derived guards

```scrut {output_stream: stderr}
$ $H/los-seal --capability module.attempt.record --payload '{"module_id": "module-demo", "termin": 2, "date": "2026-10-09", "result": "sat"}' --key module-attempt-sat --request-id request-module-attempt-sat --guards auto --out "$TMPDIR/module-attempt-sat.json"
seal_envelope: guards auto: module-demo=0
```

## Submit the attempt

```scrut
$ los capability module.attempt.record --payload-file "$TMPDIR/module-attempt-sat.json"
{
  "schema_version": 2,
  "request_id": "request-module-attempt-sat",
  "idempotency_key": "module-attempt-sat",
  "capability": "module.attempt.record",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:3c45b9556a792805e15dee406349a146cbb6e074e8fe9353b07d1fc5529a34ff",
  "result": {
    "ok": true,
    "module_id": "module-demo",
    "attempt": {
      "termin": 2,
      "date": "2026-10-09",
      "result": "sat"
    },
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "module-demo": 1
    },
    "snapshot_after": "sha256:3c45b9556a792805e15dee406349a146cbb6e074e8fe9353b07d1fc5529a34ff",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability module.attempt.record
```

## The owning module carries the attempt

```scrut
$ $H/los-assert-file curriculum/modules/module-demo/module.yaml --sha256 280b1e75761a6f4808d916dbd8973bc94038b4d851a40e7ff56c8895efa6af6b
```

## Seal the sitting deadline with derived guards

```scrut {output_stream: stderr}
$ $H/los-seal --capability module.sitting.update --payload '{"module_id": "module-demo", "termin": 2, "withdrawal_deadline": "2026-09-30"}' --key module-sitting-deadline --request-id request-module-sitting-deadline --guards auto --out "$TMPDIR/module-sitting-deadline.json"
seal_envelope: guards auto: module-demo=1
```

## Submit the sitting deadline

```scrut
$ los capability module.sitting.update --payload-file "$TMPDIR/module-sitting-deadline.json"
{
  "schema_version": 2,
  "request_id": "request-module-sitting-deadline",
  "idempotency_key": "module-sitting-deadline",
  "capability": "module.sitting.update",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-002",
  "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
  "snapshot_after": "sha256:549e21991853c299999f8b7d3b578ca211604eb14b1447346ce9729e713314a4",
  "result": {
    "ok": true,
    "module_id": "module-demo",
    "termin": 2,
    "withdrawal_deadline": "2026-09-30",
    "transaction_id": "transaction-20261001-090000-002",
    "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
    "artifact_revisions": {
      "module-demo": 2
    },
    "snapshot_after": "sha256:549e21991853c299999f8b7d3b578ca211604eb14b1447346ce9729e713314a4",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability module.sitting.update
```

## The owning module carries the deadline

```scrut
$ $H/los-assert-file curriculum/modules/module-demo/module.yaml --sha256 184e3220ef394972361bbb38b0935f9d8d8ac0f6e3ee111cdaf41f1e7fe5cbc4
```

## The status stays enrolled while the grade is pending

```scrut
$ grep "^status:" curriculum/modules/module-demo/module.yaml
status: enrolled
```

## Rebuild the module and coordination views

```scrut
$ los generate
published generated/manifest.json (atomic contract snapshot)
```

```scrut
$ $H/los-assert-file generated/module-view.md --exists
```

```scrut
$ $H/los-assert-file generated/coordination-view.md --exists
```

## The rebuilt module view carries the sat attempt

```scrut
$ grep -c "sat" generated/module-view.md
1
```
