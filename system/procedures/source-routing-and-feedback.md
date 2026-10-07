---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Source routing and feedback (WORKFLOWS §26)

Executable transcript of recording lightweight personal evidence
on a stage: the bare CLI refuses, the sealed envelope commits, and
the judgment stays on that stage. Registering the source identity
is §6 and changing the routing afterwards is §25a; both are linked
procedures, not steps here. `tests/test_procedures.py` runs it with
Scrut; `<REPO>` comes from the `LOS_REPO` environment variable the
test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Capture the pre-refusal state

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.fingerprint import canonical_fingerprint; from pathlib import Path; st={"fp": canonical_fingerprint(Path(".")), "rc": sorted(glob.glob("operations/transactions/transaction-*.yaml"))}; json.dump(st, open(os.environ["TMPDIR"]+"/fp-refuse-bare.json", "w")); print("captured", len(st["rc"]))'
captured 1
```

## The bare CLI refuses the write

```scrut
$ los source-feedback unit-demo-l01 stage-demo source-demo-book helpful --note "The derivation landed." >"$TMPDIR/fb-bare.txt" 2>&1; echo "exit=$?"; sed 's/ — .*//' "$TMPDIR/fb-bare.txt"
exit=2
canonical writes must use GatewayEnvelopeV2; direct CLI application is disabled
```

## The refusal added no receipt and moved no canonical byte

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.fingerprint import canonical_fingerprint; from pathlib import Path; st=json.load(open(os.environ["TMPDIR"]+"/fp-refuse-bare.json")); fp=canonical_fingerprint(Path(".")); rc=sorted(glob.glob("operations/transactions/transaction-*.yaml")); assert fp==st["fp"], (fp, st["fp"]); assert rc==st["rc"], (rc, st["rc"]); print("unchanged")'
unchanged
```

## Seal the feedback with derived guards

```scrut {output_stream: stderr}
$ $H/los-seal --capability source.feedback.record --payload '{"unit_id": "unit-demo-l01", "stage_id": "stage-demo", "source_id": "source-demo-book", "feedback": "helpful", "note": "The derivation landed."}' --key stage-feedback --request-id request-stage-feedback --guards auto --out "$TMPDIR/feedback.json"
seal_envelope: guards auto: study-map-demo-l01=0, unit-demo-l01=3
```

## Record the feedback

```scrut
$ los capability source.feedback.record --payload-file "$TMPDIR/feedback.json"
{
  "schema_version": 2,
  "request_id": "request-stage-feedback",
  "idempotency_key": "stage-feedback",
  "capability": "source.feedback.record",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:a59b1cd3c487e8ba84aa58074a380788020e88f1498c99ef0dc5c020048fa8f2",
  "result": {
    "ok": true,
    "unit_id": "unit-demo-l01",
    "stage_id": "stage-demo",
    "feedback": {
      "source_id": "source-demo-book",
      "feedback": "helpful",
      "recorded": "2026-10-01",
      "note": "The derivation landed."
    },
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "study-map-demo-l01": 1,
      "unit-demo-l01": 4
    },
    "snapshot_after": "sha256:a59b1cd3c487e8ba84aa58074a380788020e88f1498c99ef0dc5c020048fa8f2",
    "replayed": false
  },
  "error": null
}
```

## The feedback persisted with a receipt

```scrut
$ $H/los-assert-file curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml --sha256 472e0f82e0e6fcceade927c95b355e7e9bf14eefa36f073e303a4d6ecb56ab52
```

```scrut
$ $H/los-assert-receipt --last --capability source.feedback.record
```

## The receipt owns the recorded feedback

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,os,yaml; ds=sorted(glob.glob("operations/transactions/transaction-*.yaml")); xs=[os.path.basename(x) for x in ds]; assert xs==["transaction-20200102-000000-001.yaml", "transaction-20261001-090000-001.yaml"], xs; d=yaml.safe_load(open(ds[-1])); assert d["capability"]=="source.feedback.record", d["capability"]; w={x["path"]: x for x in d.get("writes") or []}; e=w["curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"]; assert e["sha256_after"]=="472e0f82e0e6fcceade927c95b355e7e9bf14eefa36f073e303a4d6ecb56ab52", e; assert e["created"] is False, e; print("owns", d["id"])'
owns transaction-20261001-090000-001
```

## The judgment stays on that stage

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import yaml; d = yaml.safe_load(open("curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml")); s = [x for x in d["stages"] if x["id"] == "stage-demo"][0]; print(s["id"]); [print(f["source_id"], f["feedback"], f["recorded"], f["note"]) for f in s["source_feedback"]]'
stage-demo
source-demo-book helpful 2026-10-01 The derivation landed.
```

## Capture the pre-seal-refusal state

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.fingerprint import canonical_fingerprint; from pathlib import Path; st={"fp": canonical_fingerprint(Path(".")), "rc": sorted(glob.glob("operations/transactions/transaction-*.yaml"))}; json.dump(st, open(os.environ["TMPDIR"]+"/fp-refuse-seal.json", "w")); print("captured", len(st["rc"]))'
captured 2
```

## Feedback for an unknown source is refused at seal time

```scrut {output_stream: stderr}
$ $H/los-seal --capability source.feedback.record --payload '{"unit_id": "unit-demo-l01", "stage_id": "stage-demo", "source_id": "source-missing", "feedback": "helpful"}' --key stage-feedback-bad --request-id request-stage-feedback-bad --guards auto --out "$TMPDIR/feedback-bad.json"
seal_envelope: los: source not found: source-missing; fix the payload and seal again
[2]
```

## The seal refusal added no receipt and moved no canonical byte

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.fingerprint import canonical_fingerprint; from pathlib import Path; st=json.load(open(os.environ["TMPDIR"]+"/fp-refuse-seal.json")); fp=canonical_fingerprint(Path(".")); rc=sorted(glob.glob("operations/transactions/transaction-*.yaml")); assert fp==st["fp"], (fp, st["fp"]); assert rc==st["rc"], (rc, st["rc"]); print("unchanged")'
unchanged
```

## Validate the recorded feedback

```scrut
$ los validate | tail -n 1
0 error(s), 9 warning(s) — OK
```
