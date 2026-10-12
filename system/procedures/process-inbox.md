---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Process the inbox (WORKFLOWS §21)

Executable transcript of the inbox loop for one drop: list the inbox,
read the drop through the product, seal an `inbox.resolve` envelope with
the drop's SHA-256 and its destination, and resolve it — the drop moves
byte-identical to the archive. A changed drop refuses. The routed
destination here is the existing durable note `note-demo`.
`tests/test_procedures.py` runs it with Scrut; `<REPO>` comes from the
`LOS_REPO` environment variable the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Read the inbox through the product, never by catting files

```scrut
$ los inbox-list
[{"age_days":3,"deprecated":null,"id":"note-drop.md","path":"work/inbox/note-drop.md","state":null,"status":null,"title":"note-drop.md","type":"inbox-item"},{"age_days":0,"deprecated":null,"id":"pack/one.md","path":"work/inbox/pack/one.md","state":null,"status":null,"title":"one.md","type":"inbox-item"},{"age_days":0,"deprecated":null,"id":"pack/two.md","path":"work/inbox/pack/two.md","state":null,"status":null,"title":"two.md","type":"inbox-item"}]
```

## Read the drop for its sha256

```scrut
$ los inbox-read note-drop.md
{"schema_version":1,"snapshot_id":"sha256:9578da6071c49258a28817adeabd2f40d29945448a6fe97c38316b8b10cf4b1c","contract":"inbox-content","item":"note-drop.md","path":"work/inbox/note-drop.md","content_sha256":"sha256:cff485a0c38476920bff529d70a47c19fddb0380750b9a0152521d7eb9b6c81d","offset":0,"offset_unit":"unicode_characters","total_characters":26,"start_line":1,"content":"# Dropped note\n\nUnrouted.\n","next_offset":null}
```

## Bind the drop sha for the envelope

```scrut
$ eval "$(los inbox-read note-drop.md | $H/los-bind DROP_SHA '$.content_sha256')" && echo "$DROP_SHA"
sha256:cff485a0c38476920bff529d70a47c19fddb0380750b9a0152521d7eb9b6c81d
```

## Seal the resolve with the drop sha and its destination

```scrut {output_stream: stderr}
$ $H/los-seal --capability inbox.resolve --payload "{\"name\": \"note-drop.md\", \"drop_sha256\": \"$DROP_SHA\", \"routed_to\": [\"note-demo\"]}" --key inbox-resolve-001 --request-id request-inbox-resolve-001 --guards auto --out "$TMPDIR/inbox-resolve.json"
seal_envelope: guards auto: file:archive/inbox/2026/note-drop.md=0, file:work/inbox/note-drop.md=0
```

## Submit the envelope

```scrut
$ los capability inbox.resolve --payload-file "$TMPDIR/inbox-resolve.json"
{
  "schema_version": 2,
  "request_id": "request-inbox-resolve-001",
  "idempotency_key": "inbox-resolve-001",
  "capability": "inbox.resolve",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:7bc6cf7417b93e76d5a0ff4717223783a56cb8d3bcf2d5be4fb4ba93c36074ef",
  "result": {
    "ok": true,
    "resolved": "note-drop.md",
    "archived": [
      "archive/inbox/2026/note-drop.md"
    ],
    "routed_to": [
      "note-demo"
    ],
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "file:archive/inbox/2026/note-drop.md": 1,
      "file:work/inbox/note-drop.md": 1
    },
    "snapshot_after": "sha256:7bc6cf7417b93e76d5a0ff4717223783a56cb8d3bcf2d5be4fb4ba93c36074ef",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability inbox.resolve
```

## The drop moved byte-identical to the archive

```scrut
$ $H/los-assert-file archive/inbox/2026/note-drop.md --sha256 cff485a0c38476920bff529d70a47c19fddb0380750b9a0152521d7eb9b6c81d
```

## The inbox no longer holds the drop

```scrut
$ $H/los-assert-file work/inbox/note-drop.md --absent
```

## A changed drop refuses at seal time

```scrut {output_stream: stderr}
$ $H/los-seal --capability inbox.resolve --payload '{"name": "pack/one.md", "drop_sha256": "sha256:0000000000000000000000000000000000000000000000000000000000000000", "routed_to": ["note-demo"]}' --key inbox-resolve-002 --request-id request-inbox-resolve-002 --guards auto --out "$TMPDIR/inbox-resolve-stale.json"
seal_envelope: inbox drop changed since read: pack/one.md (re-read it with `inbox-read pack/one.md` and re-seal); fix the payload and seal again
[2]
```
