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

## Capture the pre-refusal state

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.fingerprint import canonical_fingerprint; from pathlib import Path; st={"fp": canonical_fingerprint(Path(".")), "rc": sorted(glob.glob("operations/transactions/transaction-*.yaml"))}; json.dump(st, open(os.environ["TMPDIR"]+"/fp-refuse-bare.json", "w")); print("captured", len(st["rc"]))'
captured 1
```

## The bare attempt command is refused

```scrut {output_stream: stderr}
$ los module-attempt module-demo --termin 2 --date 2026-10-09 --result sat
canonical writes must use GatewayEnvelopeV2* (glob)
[2]
```

## The refusal added no receipt and moved no canonical byte

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.fingerprint import canonical_fingerprint; from pathlib import Path; st=json.load(open(os.environ["TMPDIR"]+"/fp-refuse-bare.json")); fp=canonical_fingerprint(Path(".")); rc=sorted(glob.glob("operations/transactions/transaction-*.yaml")); assert fp==st["fp"], (fp, st["fp"]); assert rc==st["rc"], (rc, st["rc"]); print("unchanged")'
unchanged
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
  "snapshot_after": "sha256:a4ea347d0d09168b0f8853666deda4e37ceafd7760fe372161a0039abcb44c0e",
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
    "snapshot_after": "sha256:a4ea347d0d09168b0f8853666deda4e37ceafd7760fe372161a0039abcb44c0e",
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

## The receipt owns the attempt

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,os,yaml; ds=sorted(glob.glob("operations/transactions/transaction-*.yaml")); xs=[os.path.basename(x) for x in ds]; assert xs==["transaction-20200102-000000-001.yaml", "transaction-20261001-090000-001.yaml"], xs; d=yaml.safe_load(open(ds[-1])); assert d["capability"]=="module.attempt.record", d["capability"]; w={x["path"]: x for x in d.get("writes") or []}; e=w["curriculum/modules/module-demo/module.yaml"]; assert e["sha256_after"]=="280b1e75761a6f4808d916dbd8973bc94038b4d851a40e7ff56c8895efa6af6b", e; assert e["created"] is False, e; print("owns", d["id"])'
owns transaction-20261001-090000-001
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
  "snapshot_after": "sha256:99cb44f99b79084f2a3b3ffd5f7cbe55fd2b7194c46d09ce3ebd1fd2b06f932d",
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
    "snapshot_after": "sha256:99cb44f99b79084f2a3b3ffd5f7cbe55fd2b7194c46d09ce3ebd1fd2b06f932d",
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

## The receipt owns the deadline

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,os,yaml; ds=sorted(glob.glob("operations/transactions/transaction-*.yaml")); xs=[os.path.basename(x) for x in ds]; assert xs==["transaction-20200102-000000-001.yaml", "transaction-20261001-090000-001.yaml", "transaction-20261001-090000-002.yaml"], xs; d=yaml.safe_load(open(ds[-1])); assert d["capability"]=="module.sitting.update", d["capability"]; w={x["path"]: x for x in d.get("writes") or []}; e=w["curriculum/modules/module-demo/module.yaml"]; assert e["sha256_after"]=="184e3220ef394972361bbb38b0935f9d8d8ac0f6e3ee111cdaf41f1e7fe5cbc4", e; assert e["created"] is False, e; print("owns", d["id"])'
owns transaction-20261001-090000-002
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
