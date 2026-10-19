---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Capture temporary material (WORKFLOWS §2)

Executable transcript of temporary capture: a fragment for the active
workspace lands in its `scratch/` with no envelope, while an inbox drop
with no obvious workspace goes through a `capture.create` envelope — the
bare command is refused by design. `tests/test_procedures.py` runs it
with Scrut; `<REPO>` comes from the `LOS_REPO` environment variable the
test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## A workspace fragment needs no envelope

```scrut
$ printf '%s\n' 'Partial calculation: E[X] = sum_x x * p(x).' > work/active/workspace-demo/scratch/fragment.md
```

## The fragment is there

```scrut
$ $H/los-assert-file work/active/workspace-demo/scratch/fragment.md --exists
```

## The bare capture command is refused by design

```scrut {output_stream: stderr}
$ los capture --text "hello"
los: INVALID_REQUEST: canonical writes must use GatewayEnvelopeV2; direct CLI application is disabled — apply it with `los capability capture.create --payload-file ENVELOPE.json` (payload schema: `los capabilities capture.create --json`; envelope: WORKFLOWS §25c)
[2]
```

## Seal the inbox capture with derived guards

```scrut {output_stream: stderr}
$ $H/los-seal --capability capture.create --payload '{"text": "Unrouted fragment for later triage."}' --key temp-capture-001 --request-id request-temp-capture-001 --guards auto --out "$TMPDIR/temp-capture.json"
seal_envelope: guards auto: capture-request:temp-capture-001=0
```

## Submit the envelope

```scrut
$ los capability capture.create --payload-file "$TMPDIR/temp-capture.json"
{
  "schema_version": 2,
  "request_id": "request-temp-capture-001",
  "idempotency_key": "temp-capture-001",
  "capability": "capture.create",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:ca6f9bdc8d842ce3f68aecb862f0051263947219e827d45200f6f23bc4599322",
  "result": {
    "ok": true,
    "captured": "work/inbox/20261001-090000-unrouted-fragment-for-later-triage.md",
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "capture-request:temp-capture-001": 1
    },
    "snapshot_after": "sha256:ca6f9bdc8d842ce3f68aecb862f0051263947219e827d45200f6f23bc4599322",
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
$ $H/los-assert-file work/inbox/20261001-090000-unrouted-fragment-for-later-triage.md --sha256 3fe8504066a30feeb94e22c4d1d8f404ab0560022e4c0b179745b10d3a732a6a
```

## The inbox lists the new drop

```scrut
$ los inbox-list
[{"id":"20261001-090000-unrouted-fragment-for-later-triage.md","type":"inbox-item","title":"20261001-090000-unrouted-fragment-for-later-triage.md","path":"work/inbox/20261001-090000-unrouted-fragment-for-later-triage.md","status":null,"state":null,"deprecated":null,"age_days":0},{"id":"note-drop.md","type":"inbox-item","title":"note-drop.md","path":"work/inbox/note-drop.md","status":null,"state":null,"deprecated":null,"age_days":3},{"id":"pack/one.md","type":"inbox-item","title":"one.md","path":"work/inbox/pack/one.md","status":null,"state":null,"deprecated":null,"age_days":0},{"id":"pack/two.md","type":"inbox-item","title":"two.md","path":"work/inbox/pack/two.md","status":null,"state":null,"deprecated":null,"age_days":0}]
```
