---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Complete and archive a workspace (WORKFLOWS §11)

Executable transcript of completing the second workspace: its durable
understanding lands in a new note, the workspace links it, a
dependency that names the workspace is set up and then cleared from
coordination, the status flips to complete, validation and rebuild
pass, and the workspace moves to the dated archive byte-identical.
No new evaluations are warranted, and the workspace is not standing.
`tests/test_procedures.py` runs it with Scrut; `<REPO>` comes from
the `LOS_REPO` environment variable the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Stage the durable-knowledge body

```scrut
$ cat > "$TMPDIR/archive-body.md" <<'EOF'
> # Second closure
>
> The second effort settled the setup question; the middle step stays uncertain.
> EOF
```

## Seal the durable note with derived guards

```scrut {output_stream: stderr}
$ BODY_SHA=$(sha256sum "$TMPDIR/archive-body.md" | cut -d' ' -f1) && $H/los-seal --capability note.create --payload "{\"note\": {\"id\": \"note-second-closure\", \"title\": \"Second closure\", \"path\": \"knowledge/notes/mathematics/note-second-closure.md\", \"concepts\": [\"concept-expected-value\"], \"sources\": [\"source-demo-book\"], \"contexts\": [\"workspace-second\"]}, \"body_file\": \"$TMPDIR/archive-body.md\", \"body_file_sha256\": \"sha256:$BODY_SHA\"}" --key archive-note --request-id request-archive-note --guards auto --out "$TMPDIR/archive-note.json"
seal_envelope: guards auto: note-second-closure=0
```

## Submit the durable note

```scrut
$ los capability note.create --payload-file "$TMPDIR/archive-note.json"
{
  "schema_version": 2,
  "request_id": "request-archive-note",
  "idempotency_key": "archive-note",
  "capability": "note.create",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:b8f8e7af3ebbd44b6be76c28a7560221a242b514198c689b714e8f32594efb4d",
  "result": {
    "ok": true,
    "note_id": "note-second-closure",
    "note_path": "knowledge/notes/mathematics/note-second-closure.md",
    "deprecated": [],
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "note-second-closure": 1
    },
    "snapshot_after": "sha256:b8f8e7af3ebbd44b6be76c28a7560221a242b514198c689b714e8f32594efb4d",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability note.create
```

## The durable note landed

```scrut
$ $H/los-assert-file knowledge/notes/mathematics/note-second-closure.md --sha256 c2497364126a817f2a87dfeaaeec4e8f9ca8aad45b27d910a5a02a650f5a8c7b
```

## Link the final note from the workspace

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import yaml; p = "work/active/workspace-second/CONTEXT.md"; raw = open(p).read(); head, sep, body = raw.partition("---\n\n"); meta = yaml.safe_load(head); meta["notes"].append("note-second-closure"); open(p, "w").write("---\n" + yaml.safe_dump(meta, sort_keys=False) + "---\n\n" + body)'
```

```scrut
$ cat >> work/active/workspace-second/CONTEXT.md <<'EOF'
>
> ## Durable Notes
>
> - note-second-closure
> EOF
```

## The workspace links its final note

```scrut
$ $H/los-assert-file work/active/workspace-second/CONTEXT.md --sha256 5cdb7a94e137f847e56fc76aba23062de5a49982d17299f85eef5bc244ffc63f
```

## Set up a dependency that names the workspace

```scrut
$ eval "$(los inspect coordination | $H/los-bind DEP_SHA '$.content_sha256')" && echo "$DEP_SHA"
sha256:667bbd75392b1acdc610aa249aa5f2fe3d7659603901f415b36eda30fe2b4655
```

```scrut {output_stream: stderr}
$ $H/los-seal --capability coordination.section.revise --payload "{\"section\": \"Dependencies\", \"text\": \"- workspace-second feeds the demo write-up.\", \"expected_content_sha256\": \"$DEP_SHA\"}" --key archive-dep-add --request-id request-archive-dep-add --guards auto --out "$TMPDIR/archive-dep-add.json"
seal_envelope: guards auto: coordination=0
```

```scrut
$ los capability coordination.section.revise --payload-file "$TMPDIR/archive-dep-add.json"
{
  "schema_version": 2,
  "request_id": "request-archive-dep-add",
  "idempotency_key": "archive-dep-add",
  "capability": "coordination.section.revise",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-002",
  "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
  "snapshot_after": "sha256:1aa12299b7007ad7037795a31eddd252a15cf0ed2c0acb5424740ab818ac6509",
  "result": {
    "ok": true,
    "section": "Dependencies",
    "transaction_id": "transaction-20261001-090000-002",
    "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
    "artifact_revisions": {
      "coordination": 1
    },
    "snapshot_after": "sha256:1aa12299b7007ad7037795a31eddd252a15cf0ed2c0acb5424740ab818ac6509",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability coordination.section.revise
```

## Clear the dependency back out

```scrut
$ eval "$(los inspect coordination | $H/los-bind DEP_SHA2 '$.content_sha256')" && echo "$DEP_SHA2"
sha256:fbe6f680491976f7c44a7d09b16fb1fbef2df2e99d1218a2d4d03ad36e8562e2
```

```scrut {output_stream: stderr}
$ $H/los-seal --capability coordination.section.revise --payload "{\"section\": \"Dependencies\", \"text\": \"(none)\", \"expected_content_sha256\": \"$DEP_SHA2\"}" --key archive-dep-clear --request-id request-archive-dep-clear --guards auto --out "$TMPDIR/archive-dep-clear.json"
seal_envelope: guards auto: coordination=1
```

```scrut
$ los capability coordination.section.revise --payload-file "$TMPDIR/archive-dep-clear.json"
{
  "schema_version": 2,
  "request_id": "request-archive-dep-clear",
  "idempotency_key": "archive-dep-clear",
  "capability": "coordination.section.revise",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-003",
  "receipt_path": "operations/transactions/transaction-20261001-090000-003.yaml",
  "snapshot_after": "sha256:f1161eb00faa0572c9b0ea921e582ed202d7f4095e06b39c81a29f8c5b48cfbe",
  "result": {
    "ok": true,
    "section": "Dependencies",
    "transaction_id": "transaction-20261001-090000-003",
    "receipt_path": "operations/transactions/transaction-20261001-090000-003.yaml",
    "artifact_revisions": {
      "coordination": 2
    },
    "snapshot_after": "sha256:f1161eb00faa0572c9b0ea921e582ed202d7f4095e06b39c81a29f8c5b48cfbe",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability coordination.section.revise
```

## No dependency names the workspace anymore

```scrut
$ grep -c "workspace-second" work/COORDINATION.md || true
0
```

## Flip the status to complete

```scrut
$ sed -i '' 's/^status: active$/status: complete/' work/active/workspace-second/CONTEXT.md && grep "^status:" work/active/workspace-second/CONTEXT.md
status: complete
```

## The completed workspace validates

```scrut
$ los validate | tail -n 1
0 error(s), 10 warning(s) — OK
```

## Rebuild generated outputs

```scrut
$ los generate
published generated/manifest.json (atomic contract snapshot)
```

## The workspace is not standing

```scrut
$ grep -c "standing: true" work/active/workspace-second/CONTEXT.md || true
0
```

## Move it to the dated archive

```scrut
$ mkdir -p archive/workspaces/2026 && mv work/active/workspace-second archive/workspaces/2026/workspace-second
```

## The archived copy is byte-identical

```scrut
$ $H/los-assert-file archive/workspaces/2026/workspace-second/CONTEXT.md --sha256 11735caef01d386884e7180472fcae51c1789ea1e68296e601c7336093c251fa
```

## The active path is gone

```scrut
$ $H/los-assert-file work/active/workspace-second --absent
```
