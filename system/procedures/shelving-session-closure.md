---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Shelving and session closure (OPERATOR)

Executable transcript of shelving, then of closing the session without
committing: a stage note is written, a shelving proposal is prepared
from an explicit items file, the bare apply refuses without approval,
the selected item is applied through its envelope, the tree is
validated and regenerated, and `session-end` reviews before `--close`
ends the ownership window. `tests/test_procedures.py` runs it with
Scrut; `<REPO>` comes from the `LOS_REPO` environment variable the test
sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## The bare prepare never applies

```scrut {output_stream: stderr}
$ los shelving-prepare unit-demo-l01
los: INVALID_REQUEST: canonical writes must use GatewayEnvelopeV2; direct CLI application is disabled — apply it with `los capability review.prepare --payload-file ENVELOPE.json` (payload schema: `los capabilities review.prepare --json`; envelope: WORKFLOWS §25c)
[2]
```

## Record the reasoning to shelve

Shelving reads selected stage notes and attachments, preserves uncertainty and
wrong turns, proposes durable notes/Garden items and diffs, and waits for
explicit selected-item approval. After application, validate and regenerate.

```scrut {output_stream: stderr}
$ $H/los-seal --capability stage.note.write --payload '{"unit_id": "unit-demo-l01", "stage_id": "stage-demo", "text": "Log: the derivation finally clicked."}' --key shelve-note-001 --request-id request-shelve-note-001 --guards auto --out "$TMPDIR/shelve-note.json"
seal_envelope: guards auto: unit-demo-l01=3
```

## Submit the envelope

```scrut
$ los capability stage.note.write --payload-file "$TMPDIR/shelve-note.json"
{
  "schema_version": 2,
  "request_id": "request-shelve-note-001",
  "idempotency_key": "shelve-note-001",
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

## Stage the explicit proposal items outside the repo

```scrut
$ printf '%s' '[{"id": "proposal-derivation-note", "kind": "durable-note", "title": "Shelved derivation", "destination": "knowledge/notes/mathematics/note-shelved-derivation.md", "rationale": "The stage note records the derivation clicking; worth finding again.", "content": "---\nid: note-shelved-derivation\ntype: note\ntitle: Shelved derivation\ncreated: 2026-10-01\nrole: synthesis\n---\n\n# Shelved derivation\n\nThe derivation finally clicked.\n"}]' > "$TMPDIR/shelve-items.json"
```

## Bind the items sha for the content-bound read

```scrut
$ ITEMS_SHA=$($LOS_REPO/.venv/bin/python -c 'import hashlib,os; print(hashlib.sha256(open(os.path.join(os.environ["TMPDIR"],"shelve-items.json"),"rb").read()).hexdigest())') && echo "$ITEMS_SHA"
2e55f464fd051d0bf69234d012aec45a0fdc445c4d1846ad02b8ec0291f37481
```

## Seal the prepare against the items file

The envelope binds the scratch items path, so its bytes are not pinned;
the submission below carries the weight.

```scrut {output_stream: stderr}
$ $H/los-seal --capability review.prepare --payload "{\"unit_id\": \"unit-demo-l01\", \"items_file\": \"$TMPDIR/shelve-items.json\", \"items_file_sha256\": \"sha256:$ITEMS_SHA\"}" --key shelve-prepare-001 --request-id request-shelve-prepare-001 --guards auto --out "$TMPDIR/shelve-prepare.json"
seal_envelope: guards auto: study-map-demo-l01=0, unit-demo-l01=4
```

## Submit the envelope

```scrut
$ los capability review.prepare --payload-file "$TMPDIR/shelve-prepare.json"
{
  "schema_version": 2,
  "request_id": "request-shelve-prepare-001",
  "idempotency_key": "shelve-prepare-001",
  "capability": "review.prepare",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-002",
  "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
  "snapshot_after": "sha256:b26ec323d4ca8aeccee54b10701c98028aedc8ac1554d473ed5b97d6a4964063",
  "result": {
    "ok": true,
    "unit_id": "unit-demo-l01",
    "proposal_path": "curriculum/modules/module-demo/units/unit-demo-l01/shelving-proposal.md",
    "state": "proposed",
    "transaction_id": "transaction-20261001-090000-002",
    "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
    "artifact_revisions": {
      "study-map-demo-l01": 1,
      "unit-demo-l01": 5
    },
    "snapshot_after": "sha256:b26ec323d4ca8aeccee54b10701c98028aedc8ac1554d473ed5b97d6a4964063",
    "replayed": false
  },
  "error": null
}
```

## The proposal packet names the stage note

```scrut
$ $H/los-assert-file curriculum/modules/module-demo/units/unit-demo-l01/shelving-proposal.md --sha256 ee4fb744c4e5891f1207f883447c8695e234326585986d403483ef8436ca1559
```

## The bare apply refuses without approval

```scrut {output_stream: stderr}
$ los shelving-apply unit-demo-l01 --selected proposal-derivation-note
los: INVALID_REQUEST: shelving apply requires --approve and explicit selected proposal IDs
[2]
```

## Seal the apply of the explicitly selected item

```scrut {output_stream: stderr}
$ $H/los-seal --capability review.apply --payload '{"unit_id": "unit-demo-l01", "selected": ["proposal-derivation-note"]}' --key shelve-apply-001 --request-id request-shelve-apply-001 --guards auto --out "$TMPDIR/shelve-apply.json"
seal_envelope: guards auto: proposal-derivation-note=0, study-map-demo-l01=1, unit-demo-l01=5
```

## Submit the envelope

```scrut
$ los capability review.apply --payload-file "$TMPDIR/shelve-apply.json"
{
  "schema_version": 2,
  "request_id": "request-shelve-apply-001",
  "idempotency_key": "shelve-apply-001",
  "capability": "review.apply",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-003",
  "receipt_path": "operations/transactions/transaction-20261001-090000-003.yaml",
  "snapshot_after": "sha256:d8b3f8607a5ac219fffaddf33af920365b937d2dc36da90fb44e7f0e0a49e627",
  "result": {
    "ok": true,
    "unit_id": "unit-demo-l01",
    "applied": [
      "proposal-derivation-note"
    ],
    "transaction_id": "transaction-20261001-090000-003",
    "receipt_path": "operations/transactions/transaction-20261001-090000-003.yaml",
    "artifact_revisions": {
      "proposal-derivation-note": 1,
      "study-map-demo-l01": 2,
      "unit-demo-l01": 6
    },
    "snapshot_after": "sha256:d8b3f8607a5ac219fffaddf33af920365b937d2dc36da90fb44e7f0e0a49e627",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability review.apply
```

## The durable note exists with the approved bytes

```scrut
$ $H/los-assert-file knowledge/notes/mathematics/note-shelved-derivation.md --sha256 75e6f946b24b4ba8256dcba9d08d1c8c6ffe7da5fe6f5a5ca7f12d3b228bf3f6
```

## After application, validate

```scrut
$ los validate | tail -n 1
0 error(s), 9 warning(s) — OK
```

## And regenerate

```scrut
$ los generate
published generated/manifest.json (atomic contract snapshot)
```

## Review the session

```scrut
$ los session-end
{"ok":true,"touched":["curriculum/modules/module-demo/units/unit-demo-l01/shelving-proposal.md","curriculum/modules/module-demo/units/unit-demo-l01/stages/stage-demo/notes.md","curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml","knowledge/notes/mathematics/note-shelved-derivation.md","operations/transactions/idempotency.yaml","operations/transactions/revisions.yaml","operations/transactions/transaction-20261001-090000-001.yaml","operations/transactions/transaction-20261001-090000-002.yaml","operations/transactions/transaction-20261001-090000-003.yaml"],"owned_changes":[" M curriculum/modules/module-demo/units/unit-demo-l01/stages/stage-demo/notes.md"," M curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"," M operations/transactions/revisions.yaml","?? curriculum/modules/module-demo/units/unit-demo-l01/shelving-proposal.md","?? knowledge/notes/mathematics/note-shelved-derivation.md","?? operations/transactions/idempotency.yaml","?? operations/transactions/transaction-20261001-090000-001.yaml","?? operations/transactions/transaction-20261001-090000-002.yaml","?? operations/transactions/transaction-20261001-090000-003.yaml"],"unrelated_changes":["?? operations/diagnostics/traces.jsonl"],"committed":false,"pushed":false,"validation":"0 error(s), 9 warning(s) — OK; warning list: generated/reports/validation-report.md","ownership_conflicts":[],"session_id":"channel:operator","client":null,"stale_paths":[],"stale_hours":24,"other_sessions":{},"session_closed":false}
```

## Close the ownership window without committing

```scrut
$ los session-end --close
{"ok":true,"touched":["curriculum/modules/module-demo/units/unit-demo-l01/shelving-proposal.md","curriculum/modules/module-demo/units/unit-demo-l01/stages/stage-demo/notes.md","curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml","knowledge/notes/mathematics/note-shelved-derivation.md","operations/transactions/idempotency.yaml","operations/transactions/revisions.yaml","operations/transactions/transaction-20261001-090000-001.yaml","operations/transactions/transaction-20261001-090000-002.yaml","operations/transactions/transaction-20261001-090000-003.yaml"],"owned_changes":[" M curriculum/modules/module-demo/units/unit-demo-l01/stages/stage-demo/notes.md"," M curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"," M operations/transactions/revisions.yaml","?? curriculum/modules/module-demo/units/unit-demo-l01/shelving-proposal.md","?? knowledge/notes/mathematics/note-shelved-derivation.md","?? operations/transactions/idempotency.yaml","?? operations/transactions/transaction-20261001-090000-001.yaml","?? operations/transactions/transaction-20261001-090000-002.yaml","?? operations/transactions/transaction-20261001-090000-003.yaml"],"unrelated_changes":["?? operations/diagnostics/traces.jsonl"],"committed":false,"pushed":false,"validation":"0 error(s), 9 warning(s) — OK; warning list: generated/reports/validation-report.md","ownership_conflicts":[],"session_id":"channel:operator","client":null,"stale_paths":[],"stale_hours":24,"other_sessions":{},"session_closed":true}
```

## The session ledger is gone

```scrut
$ test -z "$(find "$LOS_FX/.git/learningos" -name '*-touched.json')"
```
