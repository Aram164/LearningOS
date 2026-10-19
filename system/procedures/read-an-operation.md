---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Read an operation (WORKFLOWS §28)

Executable transcript of the after-the-fact read surface: the empty
list, the unknown-id refusal, one committed write read back as a
list row and as a full diagnosis, one refused write read back as
`REFUSED`, and one request id reused across two keys. The writes
below are labeled setup scaffolding: the read surface needs
requests to explain, and the fixture starts with none. Sealing and
submitting use the universal §25c envelope path. The `make views`
settling step cannot target the fixture and stays uncovered.
`tests/test_procedures.py` runs it with Scrut; `<REPO>` comes from
the `LOS_REPO` environment variable the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## A fresh fixture lists no operations

```scrut
$ los operations
{"operations":[]}
```

## An unknown id is refused

```scrut {output_stream: stderr}
$ los operations --request-id request-no-such
los: INVALID_REQUEST: unknown request_id
[2]
```

## Setup: stage the first note body

```scrut
$ cat > "$TMPDIR/ops-first-body.md" <<'EOF'
> # First ops note
>
> The read surface needs a committed request.
> EOF
```

## Setup: seal the first note with derived guards

```scrut {output_stream: stderr}
$ BODY_SHA=$(sha256sum "$TMPDIR/ops-first-body.md" | cut -d' ' -f1) && $H/los-seal --capability note.create --payload "{\"note\": {\"id\": \"note-ops-first\", \"title\": \"First ops note\", \"path\": \"knowledge/notes/mathematics/note-ops-first.md\", \"concepts\": [\"concept-expected-value\"], \"contexts\": [\"workspace-demo\"]}, \"body_file\": \"$TMPDIR/ops-first-body.md\", \"body_file_sha256\": \"sha256:$BODY_SHA\"}" --key ops-first --request-id request-ops-first --guards auto --out "$TMPDIR/ops-first.json"
seal_envelope: guards auto: note-ops-first=0
```

## Setup: submit the first note

```scrut
$ los capability note.create --payload-file "$TMPDIR/ops-first.json"
{
  "schema_version": 2,
  "request_id": "request-ops-first",
  "idempotency_key": "ops-first",
  "capability": "note.create",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:6a74da41e00bdba6982ae1612f6b0c3409e92a811e5caaf4c920d3b12abe0e81",
  "result": {
    "ok": true,
    "note_id": "note-ops-first",
    "note_path": "knowledge/notes/mathematics/note-ops-first.md",
    "deprecated": [],
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "note-ops-first": 1
    },
    "snapshot_after": "sha256:6a74da41e00bdba6982ae1612f6b0c3409e92a811e5caaf4c920d3b12abe0e81",
    "replayed": false
  },
  "error": null
}
```

## Setup: the first note persisted with a receipt

```scrut
$ $H/los-assert-file knowledge/notes/mathematics/note-ops-first.md --sha256 bc45db014a6a1f39e6e1b4aee1f187a9aaae9a11af3690df42df89f3c44c9154
```

```scrut
$ $H/los-assert-receipt --last --capability note.create
```

## Setup: the receipt owns the setup note

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,os,yaml; ds=sorted(glob.glob("operations/transactions/transaction-*.yaml")); xs=[os.path.basename(x) for x in ds]; assert xs==["transaction-20200102-000000-001.yaml", "transaction-20261001-090000-001.yaml"], xs; d=yaml.safe_load(open(ds[-1])); assert d["capability"]=="note.create", d["capability"]; w={x["path"]: x for x in d.get("writes") or []}; e=w["knowledge/notes/mathematics/note-ops-first.md"]; assert e["sha256_after"]=="bc45db014a6a1f39e6e1b4aee1f187a9aaae9a11af3690df42df89f3c44c9154", e; assert e["created"] is True, e; print("owns", d["id"])'
owns transaction-20261001-090000-001
```

## The list now carries one row

```scrut
$ los operations | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); [print(o["request_id"], o["capability"], o["attempts"], o["replayed"], o["first_failure_stage"], o["canonical_outcome"], o["recovery_requirement"], o["needs_attention"]) for o in d["operations"]]'
request-ops-first note.create 1 False None COMMITTED none False
```

## The limit keeps the newest row

```scrut
$ los operations --limit 1 | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); [print(o["request_id"], o["capability"], o["canonical_outcome"]) for o in d["operations"]]'
request-ops-first note.create COMMITTED
```

## The committed request explains itself fully

```scrut
$ los operations --request-id request-ops-first | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); d["diagnosis"]["attempts"] = [{k: v for k, v in a.items() if k not in ("span", "replay_of")} for a in d["diagnosis"]["attempts"]]; print(json.dumps(d, indent=2, sort_keys=True))'
{
  "capability": "note.create",
  "diagnosis": {
    "attempts": [
      {
        "status": "ok"
      }
    ],
    "authoritative_evidence": [
      "receipt:operations/transactions/transaction-20261001-090000-001.yaml",
      "ledger:ops-first",
      "observed:sha256:6a74da41e00bdba6982ae1612f6b0c3409e92a811e5caaf4c920d3b12abe0e81"
    ],
    "canonical_outcome": "COMMITTED",
    "execution_outcome": "committed",
    "first_failure_stage": null,
    "projection_outcome": "published",
    "reasons": [
      "a committed receipt verified against its ledger entry, the live revision floor, and the capability catalog",
      "receipt observed in the projection: settled"
    ],
    "recovery_requirement": "none"
  },
  "facts": {
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "snapshot_after": "sha256:6a74da41e00bdba6982ae1612f6b0c3409e92a811e5caaf4c920d3b12abe0e81",
    "snapshot_before": "sha256:08fdd4d86bb9d12fbb4b804df720b02a980031c30cb9f7007c9b425b46ef43c5",
    "transaction_id": "transaction-20261001-090000-001"
  },
  "observed_snapshot": "sha256:6a74da41e00bdba6982ae1612f6b0c3409e92a811e5caaf4c920d3b12abe0e81",
  "request_id": "request-ops-first",
  "timeline": [
    {
      "detail": null,
      "stage": "Core admitted request",
      "state": "passed"
    },
    {
      "detail": null,
      "stage": "Approval",
      "state": "passed"
    },
    {
      "detail": "miss",
      "stage": "Replay lookup",
      "state": "passed"
    },
    {
      "detail": null,
      "stage": "Snapshot guard",
      "state": "passed"
    },
    {
      "detail": null,
      "stage": "Validation",
      "state": "passed"
    },
    {
      "detail": null,
      "stage": "Projection",
      "state": "passed"
    },
    {
      "detail": null,
      "stage": "Transaction committed",
      "state": "passed"
    },
    {
      "detail": null,
      "stage": "Receipt persisted",
      "state": "passed"
    }
  ],
  "ui_outcome": "SETTLED"
}
```

## Setup: stage the refused note body

```scrut
$ cat > "$TMPDIR/ops-refused-body.md" <<'EOF'
> # Refused ops note
>
> This body never lands.
> EOF
```

## Setup: seal the refused note against a spent snapshot

```scrut {output_stream: stderr}
$ BODY_SHA=$(sha256sum "$TMPDIR/ops-refused-body.md" | cut -d' ' -f1) && $H/los-seal --capability note.create --payload "{\"note\": {\"id\": \"note-ops-refused\", \"title\": \"Refused ops note\", \"path\": \"knowledge/notes/mathematics/note-ops-refused.md\", \"concepts\": [\"concept-expected-value\"], \"contexts\": [\"workspace-demo\"]}, \"body_file\": \"$TMPDIR/ops-refused-body.md\", \"body_file_sha256\": \"sha256:$BODY_SHA\"}" --key ops-refused --request-id request-ops-refused --snapshot sha256:0000000000000000000000000000000000000000000000000000000000000000 --guards auto --out "$TMPDIR/ops-refused.json"
seal_envelope: guards auto: note-ops-refused=0
```

## Setup: capture the pre-refusal state

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.store.fingerprint import canonical_fingerprint; from pathlib import Path; st={"fp": canonical_fingerprint(Path(".")), "rc": sorted(glob.glob("operations/transactions/transaction-*.yaml"))}; json.dump(st, open(os.environ["TMPDIR"]+"/fp-refuse-stale.json", "w")); print("captured", len(st["rc"]))'
captured 2
```

## Setup: submit the refused note

```scrut
$ los capability note.create --payload-file "$TMPDIR/ops-refused.json"
{
  "schema_version": 2,
  "request_id": "request-ops-refused",
  "idempotency_key": "ops-refused",
  "capability": "note.create",
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
      "expected": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
      "actual": "sha256:6a74da41e00bdba6982ae1612f6b0c3409e92a811e5caaf4c920d3b12abe0e81"
    }
  }
}
[3]
```

## Setup: the refused note wrote nothing canonical

```scrut
$ $H/los-assert-file knowledge/notes/mathematics/note-ops-refused.md --absent
```

## Setup: the refusal added no receipt and moved no canonical byte

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.store.fingerprint import canonical_fingerprint; from pathlib import Path; st=json.load(open(os.environ["TMPDIR"]+"/fp-refuse-stale.json")); fp=canonical_fingerprint(Path(".")); rc=sorted(glob.glob("operations/transactions/transaction-*.yaml")); assert fp==st["fp"], (fp, st["fp"]); assert rc==st["rc"], (rc, st["rc"]); print("unchanged")'
unchanged
```

## The refused request explains itself as refused

```scrut
$ los operations --request-id request-ops-refused | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); d["diagnosis"]["attempts"] = [{k: v for k, v in a.items() if k not in ("span", "replay_of")} for a in d["diagnosis"]["attempts"]]; print(json.dumps(d, indent=2, sort_keys=True))'
{
  "capability": "note.create",
  "diagnosis": {
    "attempts": [
      {
        "status": "error"
      }
    ],
    "authoritative_evidence": [
      "response:STALE_SNAPSHOT",
      "observed:sha256:6a74da41e00bdba6982ae1612f6b0c3409e92a811e5caaf4c920d3b12abe0e81"
    ],
    "canonical_outcome": "NOT_COMMITTED",
    "execution_outcome": "refused",
    "first_failure_stage": "core.snapshot_guard",
    "projection_outcome": "skipped",
    "reasons": [
      "every counted attempt ended in a definitive refusal (STALE_SNAPSHOT): the write cannot have committed",
      "definitive refusal: nothing to reconcile"
    ],
    "recovery_requirement": "none"
  },
  "facts": {
    "receipt_path": null,
    "snapshot_after": null,
    "snapshot_before": null,
    "transaction_id": null
  },
  "observed_snapshot": "sha256:6a74da41e00bdba6982ae1612f6b0c3409e92a811e5caaf4c920d3b12abe0e81",
  "request_id": "request-ops-refused",
  "timeline": [
    {
      "detail": null,
      "stage": "Core admitted request",
      "state": "passed"
    },
    {
      "detail": null,
      "stage": "Approval",
      "state": "passed"
    },
    {
      "detail": "miss",
      "stage": "Replay lookup",
      "state": "passed"
    },
    {
      "detail": null,
      "stage": "Snapshot guard",
      "state": "failed"
    }
  ],
  "ui_outcome": "REFUSED"
}
```

## The list stays newest first

```scrut
$ los operations | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); [print(o["request_id"], o["canonical_outcome"]) for o in d["operations"]]'
request-ops-refused NOT_COMMITTED
request-ops-first COMMITTED
```

## Setup: two notes share one request id

```scrut
$ cat > "$TMPDIR/ops-reuse-one-body.md" <<'EOF'
> # Reuse one
>
> First key under the shared id.
> EOF
```

```scrut
$ cat > "$TMPDIR/ops-reuse-two-body.md" <<'EOF'
> # Reuse two
>
> Second key under the shared id.
> EOF
```

```scrut {output_stream: stderr}
$ BODY_SHA=$(sha256sum "$TMPDIR/ops-reuse-one-body.md" | cut -d' ' -f1) && $H/los-seal --capability note.create --payload "{\"note\": {\"id\": \"note-ops-reuse-one\", \"title\": \"Reuse one\", \"path\": \"knowledge/notes/mathematics/note-ops-reuse-one.md\", \"concepts\": [\"concept-expected-value\"], \"contexts\": [\"workspace-demo\"]}, \"body_file\": \"$TMPDIR/ops-reuse-one-body.md\", \"body_file_sha256\": \"sha256:$BODY_SHA\"}" --key ops-reuse-one --request-id request-ops-reused --guards auto --out "$TMPDIR/ops-reuse-one.json"
seal_envelope: guards auto: note-ops-reuse-one=0
```

```scrut
$ los capability note.create --payload-file "$TMPDIR/ops-reuse-one.json" | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["ok"], d["transaction_id"])'
True transaction-20261001-090000-002
```

```scrut {output_stream: stderr}
$ BODY_SHA=$(sha256sum "$TMPDIR/ops-reuse-two-body.md" | cut -d' ' -f1) && $H/los-seal --capability note.create --payload "{\"note\": {\"id\": \"note-ops-reuse-two\", \"title\": \"Reuse two\", \"path\": \"knowledge/notes/mathematics/note-ops-reuse-two.md\", \"concepts\": [\"concept-expected-value\"], \"contexts\": [\"workspace-demo\"]}, \"body_file\": \"$TMPDIR/ops-reuse-two-body.md\", \"body_file_sha256\": \"sha256:$BODY_SHA\"}" --key ops-reuse-two --request-id request-ops-reused --guards auto --out "$TMPDIR/ops-reuse-two.json"
seal_envelope: guards auto: note-ops-reuse-two=0
```

```scrut
$ los capability note.create --payload-file "$TMPDIR/ops-reuse-two.json" | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["ok"], d["replayed"], d["transaction_id"])'
True False transaction-20261001-090000-003
```

```scrut
$ $H/los-assert-file knowledge/notes/mathematics/note-ops-reuse-one.md --sha256 389deb815b400cebdd73e6ebedc81d871d8b8b9868f518700e5b0baec7fa8c5e
```

```scrut
$ $H/los-assert-file knowledge/notes/mathematics/note-ops-reuse-two.md --sha256 7719575deadef9915aaa2b78ad0f10e7ea7918db5db01f488a89e0a133366e65
```

## Setup: the second receipt owns the first reused note

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,os,yaml; ds=sorted(glob.glob("operations/transactions/transaction-*.yaml")); d=yaml.safe_load(open([x for x in ds if x.endswith("transaction-20261001-090000-002.yaml")][0])); assert d["capability"]=="note.create", d["capability"]; w={x["path"]: x for x in d.get("writes") or []}; e=w["knowledge/notes/mathematics/note-ops-reuse-one.md"]; assert e["sha256_after"]=="389deb815b400cebdd73e6ebedc81d871d8b8b9868f518700e5b0baec7fa8c5e", e; assert e["created"] is True, e; print("owns", d["id"])'
owns transaction-20261001-090000-002
```

## Setup: the third receipt owns the second reused note

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,os,yaml; ds=sorted(glob.glob("operations/transactions/transaction-*.yaml")); xs=[os.path.basename(x) for x in ds]; assert xs==["transaction-20200102-000000-001.yaml", "transaction-20261001-090000-001.yaml", "transaction-20261001-090000-002.yaml", "transaction-20261001-090000-003.yaml"], xs; d=yaml.safe_load(open(ds[-1])); assert d["capability"]=="note.create", d["capability"]; w={x["path"]: x for x in d.get("writes") or []}; e=w["knowledge/notes/mathematics/note-ops-reuse-two.md"]; assert e["sha256_after"]=="7719575deadef9915aaa2b78ad0f10e7ea7918db5db01f488a89e0a133366e65", e; assert e["created"] is True, e; print("owns", d["id"])'
owns transaction-20261001-090000-003
```

## The reused id names every distinct request

```scrut
$ los operations --request-id request-ops-reused | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); d["diagnosis"]["attempts"] = [{k: v for k, v in a.items() if k not in ("span", "replay_of")} for a in d["diagnosis"]["attempts"]]; print(json.dumps(d, indent=2, sort_keys=True))'
{
  "capability": "note.create",
  "diagnosis": {
    "attempts": [
      {
        "status": "ok"
      },
      {
        "status": "ok"
      }
    ],
    "authoritative_evidence": [
      "receipt:operations/transactions/transaction-20261001-090000-002.yaml",
      "ledger:ops-reuse-one",
      "observed:sha256:2cf781d72483d8af6c2425073285093c8d2aba2abdfb8f3e5558983e2f985156"
    ],
    "canonical_outcome": "COMMITTED",
    "execution_outcome": "committed",
    "first_failure_stage": null,
    "projection_outcome": "published",
    "reasons": [
      "a committed receipt verified against its ledger entry, the live revision floor, and the capability catalog",
      "receipt observed in the projection: settled",
      "request_id reused across 2 idempotency keys; this explanation covers ops-reuse-one only \u2014 also: ops-reuse-two (ok transaction-20261001-090000-003)"
    ],
    "recovery_requirement": "none"
  },
  "facts": {
    "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
    "snapshot_after": "sha256:5b274cb2af2046900a8a6d132c36d1610a8c8740436d5f25f96ddb766ac14b65",
    "snapshot_before": "sha256:6a74da41e00bdba6982ae1612f6b0c3409e92a811e5caaf4c920d3b12abe0e81",
    "transaction_id": "transaction-20261001-090000-002"
  },
  "observed_snapshot": "sha256:2cf781d72483d8af6c2425073285093c8d2aba2abdfb8f3e5558983e2f985156",
  "request_id": "request-ops-reused",
  "timeline": [
    {
      "detail": null,
      "stage": "Core admitted request",
      "state": "passed"
    },
    {
      "detail": null,
      "stage": "Approval",
      "state": "passed"
    },
    {
      "detail": "miss",
      "stage": "Replay lookup",
      "state": "passed"
    },
    {
      "detail": null,
      "stage": "Snapshot guard",
      "state": "passed"
    },
    {
      "detail": null,
      "stage": "Validation",
      "state": "passed"
    },
    {
      "detail": null,
      "stage": "Projection",
      "state": "passed"
    },
    {
      "detail": null,
      "stage": "Transaction committed",
      "state": "passed"
    },
    {
      "detail": null,
      "stage": "Receipt persisted",
      "state": "passed"
    }
  ],
  "ui_outcome": "SETTLED"
}
```

## Validate the read surface

```scrut
$ los validate | tail -n 1
0 error(s), 9 warning(s) — OK
```
