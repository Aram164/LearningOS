---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Build a write envelope (WORKFLOWS §25c)

Executable transcript of the GatewayEnvelopeV2 construction recipe, using
the section's own worked capture (`capture.create`) end to end: read the
payload schema, bind the snapshot, watch the bare command refuse, seal
with derived guards, verify the intent hash, submit, replay the saved
envelope, and refuse a stale one. `tests/test_procedures.py` runs it with
Scrut; `<REPO>` comes from the `LOS_REPO` environment variable the test
sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Step 1: the payload schema is the capability contract

```scrut
$ los capabilities capture.create --json | $H/los-bind PAYLOAD_SCHEMA '$.payload_schema'
export PAYLOAD_SCHEMA='{"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "capabilities/capture.create.schema.json", "title": "payload for capability capture.create", "description": "Derived from the los CLI parser for this capability'"'"'s named command. Do not hand-edit; regenerate with tools/generate_capability_schemas.py.", "type": "object", "additionalProperties": false, "required": [], "properties": {"file": {"type": "string", "description": "copy this file into the inbox"}, "file_sha256": {"type": "string", "pattern": "^sha256:[a-f0-9]{64}$", "description": "SHA-256 of the exact file bytes approved for this capture"}, "text": {"type": "string", "description": "capture this text (else stdin)"}, "title": {"type": "string", "description": "optional title for text captures"}}, "oneOf": [{"required": ["file"], "not": {"required": ["text"]}}, {"required": ["text"], "not": {"required": ["file"]}}], "dependentRequired": {"file": ["file_sha256"], "file_sha256": ["file"]}}'
```

## Step 2: the snapshot comes from bootstrap

```scrut
$ eval "$(los bootstrap --compact | $H/los-bind SNAP '$.snapshot_id')" && echo "$SNAP"
sha256:9578da6071c49258a28817adeabd2f40d29945448a6fe97c38316b8b10cf4b1c
```

## The bare mutating command refuses by design

```scrut {output_stream: stderr}
$ los capture --text "hello"
canonical writes must use GatewayEnvelopeV2; direct CLI application is disabled — apply it with `los capability capture.create --payload-file ENVELOPE.json` (payload schema: `los capabilities capture.create --json`; envelope: WORKFLOWS §25c)
[2]
```

## Steps 2–5: seal with the snapshot and derived guards

```scrut {output_stream: stderr}
$ $H/los-seal --capability capture.create --payload '{"text": "Half-formed idea about the derivation."}' --key envelope-capture-a --request-id request-envelope-capture-a --snapshot "$SNAP" --guards auto --out "$TMPDIR/capture-a.json"
seal_envelope: guards auto: capture-request:envelope-capture-a=0
```

## The sealed envelope's sha256, before submission

```scrut
$ $H/los-assert-file "$TMPDIR/capture-a.json" --sha256 e3dc894291a9a9558a860ae9a48843fd86260ad7850e777c10b7b7cece594be5
```

## The envelope carries the bound snapshot

```scrut
$ cat "$TMPDIR/capture-a.json" | $H/los-bind EXPECTED '$.expected_snapshot'
export EXPECTED=sha256:9578da6071c49258a28817adeabd2f40d29945448a6fe97c38316b8b10cf4b1c
```

## Step 5: the approval subject is the intent hash

Section 25c defines the subject hash over the six intent fields (plus the
sealed session, when one is carried). The recipe, run against the sealed
envelope above:

```python
import hashlib, json
subject = {k: envelope[k] for k in (
    "schema_version", "capability", "channel",
    "expected_snapshot", "expected_revisions", "payload")}
if "session_id" in envelope:
    subject["session_id"] = envelope["session_id"]
approval = "sha256:" + hashlib.sha256(json.dumps(
    subject, sort_keys=True, separators=(",", ":"),
    ensure_ascii=False).encode("utf-8")).hexdigest()
```

```scrut
$ $LOS_REPO/.venv/bin/python -c "import hashlib,json,os; e=json.load(open(os.path.join(os.environ['TMPDIR'],'capture-a.json'))); s={k:e[k] for k in ('schema_version','capability','channel','expected_snapshot','expected_revisions','payload')}; h='sha256:'+hashlib.sha256(json.dumps(s,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest(); assert h==e['approval']['subject_sha256'],h; print(h)"
sha256:33cb96d881e67fb8a1b990ae1bae41392b14a07c6711c762e579b2298a3d308e
```

## Step 6: submit the envelope

```scrut
$ los capability capture.create --payload-file "$TMPDIR/capture-a.json"
{
  "schema_version": 2,
  "request_id": "request-envelope-capture-a",
  "idempotency_key": "envelope-capture-a",
  "capability": "capture.create",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:81d722491992936a0850f86b477e9c78e8c0086cfbe3258bc3eddd8529ebb0e3",
  "result": {
    "ok": true,
    "captured": "work/inbox/20261001-090000-half-formed-idea-about-the-derivation.md",
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "capture-request:envelope-capture-a": 1
    },
    "snapshot_after": "sha256:81d722491992936a0850f86b477e9c78e8c0086cfbe3258bc3eddd8529ebb0e3",
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
$ $H/los-assert-file work/inbox/20261001-090000-half-formed-idea-about-the-derivation.md --sha256 e1d085adb9fd26761396362a7cf61f23f69681fc6bd6f9664272c3909cc58fcb
```

## Step 4: resubmitting the saved envelope replays it

```scrut
$ los capability capture.create --payload-file "$TMPDIR/capture-a.json"
{
  "schema_version": 2,
  "request_id": "request-envelope-capture-a",
  "idempotency_key": "envelope-capture-a",
  "capability": "capture.create",
  "ok": true,
  "replayed": true,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:81d722491992936a0850f86b477e9c78e8c0086cfbe3258bc3eddd8529ebb0e3",
  "result": {
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "capture-request:envelope-capture-a": 1
    },
    "snapshot_after": "sha256:81d722491992936a0850f86b477e9c78e8c0086cfbe3258bc3eddd8529ebb0e3",
    "replayed": true,
    "captured": "work/inbox/20261001-090000-half-formed-idea-about-the-derivation.md"
  },
  "error": null
}
```

## A second envelope, sealed against the new snapshot

```scrut {output_stream: stderr}
$ $H/los-seal --capability capture.create --payload '{"text": "A second capture that moves the snapshot."}' --key envelope-capture-b --request-id request-envelope-capture-b --guards auto --out "$TMPDIR/capture-b.json"
seal_envelope: guards auto: capture-request:envelope-capture-b=0
```

## A third envelope, sealed while the second is still current

```scrut {output_stream: stderr}
$ $H/los-seal --capability capture.create --payload '{"text": "A third capture, sealed too early."}' --key envelope-capture-c --request-id request-envelope-capture-c --guards auto --out "$TMPDIR/capture-c.json"
seal_envelope: guards auto: capture-request:envelope-capture-c=0
```

## Submitting the second capture moves the snapshot

```scrut
$ los capability capture.create --payload-file "$TMPDIR/capture-b.json"
{
  "schema_version": 2,
  "request_id": "request-envelope-capture-b",
  "idempotency_key": "envelope-capture-b",
  "capability": "capture.create",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-002",
  "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
  "snapshot_after": "sha256:caae16b5ccc26bb6908bc06550e69c35697ff3c8001c526bc3fdf530511b530f",
  "result": {
    "ok": true,
    "captured": "work/inbox/20261001-090000-a-second-capture-that-moves-the-snapshot.md",
    "transaction_id": "transaction-20261001-090000-002",
    "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
    "artifact_revisions": {
      "capture-request:envelope-capture-b": 1
    },
    "snapshot_after": "sha256:caae16b5ccc26bb6908bc06550e69c35697ff3c8001c526bc3fdf530511b530f",
    "replayed": false
  },
  "error": null
}
```

## The third envelope now refuses as stale

```scrut
$ los capability capture.create --payload-file "$TMPDIR/capture-c.json"
{
  "schema_version": 2,
  "request_id": "request-envelope-capture-c",
  "idempotency_key": "envelope-capture-c",
  "capability": "capture.create",
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
      "expected": "sha256:81d722491992936a0850f86b477e9c78e8c0086cfbe3258bc3eddd8529ebb0e3",
      "actual": "sha256:caae16b5ccc26bb6908bc06550e69c35697ff3c8001c526bc3fdf530511b530f"
    }
  }
}
[3]
```

## A second bare command refuses with its own first clause

`inbox-resolve` refuses without an envelope, as §25c requires, but its
message starts `inbox resolve requires` where §25c quotes `canonical
writes must use` (M-02 in `tests/architecture/mismatches.yaml`).

```scrut {output_stream: stderr}
$ los inbox-resolve note-drop.md --drop-sha256 sha256:cff485a0c38476920bff529d70a47c19fddb0380750b9a0152521d7eb9b6c81d --routed-to note-demo
los: INVALID_REQUEST: inbox resolve requires GatewayEnvelopeV2; direct CLI application is disabled
[2]
```
