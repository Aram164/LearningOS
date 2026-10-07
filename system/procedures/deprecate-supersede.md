---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Deprecate or supersede (WORKFLOWS §15)

Executable transcript of retiring one note and one concept: an
unknown predecessor is refused, the successor carries the old id in
`supersedes`, the predecessor flips to deprecated, the old concept
gains its replacement pointer, and the reverse link appears only in
the rebuilt backlinks. `tests/test_procedures.py` runs it with
Scrut; `<REPO>` comes from the `LOS_REPO` environment variable the
test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Stage the successor body

```scrut
$ cat > "$TMPDIR/deprecate-body.md" <<'EOF'
> # Demo followup
>
> The setup question, revisited with the middle step resolved.
> EOF
```

## An unknown predecessor is refused

```scrut {output_stream: stderr}
$ BODY_SHA=$(sha256sum "$TMPDIR/deprecate-body.md" | cut -d' ' -f1) && $H/los-seal --capability note.create --payload "{\"note\": {\"id\": \"note-demo-followup\", \"title\": \"Demo followup\", \"path\": \"knowledge/notes/mathematics/note-demo-followup.md\", \"supersedes\": [\"note-nope\"]}, \"body_file\": \"$TMPDIR/deprecate-body.md\", \"body_file_sha256\": \"sha256:$BODY_SHA\"}" --key deprecate-bad --request-id request-deprecate-bad --guards auto --out "$TMPDIR/deprecate-bad.json"
seal_envelope: superseded note does not exist: 'note-nope'; fix the payload and seal again
[2]
```

## Seal the successor with derived guards

```scrut {output_stream: stderr}
$ BODY_SHA=$(sha256sum "$TMPDIR/deprecate-body.md" | cut -d' ' -f1) && $H/los-seal --capability note.create --payload "{\"note\": {\"id\": \"note-demo-followup\", \"title\": \"Demo followup\", \"path\": \"knowledge/notes/mathematics/note-demo-followup.md\", \"supersedes\": [\"note-demo\"]}, \"body_file\": \"$TMPDIR/deprecate-body.md\", \"body_file_sha256\": \"sha256:$BODY_SHA\"}" --key deprecate-good --request-id request-deprecate-good --guards auto --out "$TMPDIR/deprecate-good.json"
seal_envelope: guards auto: note-demo=0, note-demo-followup=0
```

## Submit the successor

```scrut
$ los capability note.create --payload-file "$TMPDIR/deprecate-good.json"
{
  "schema_version": 2,
  "request_id": "request-deprecate-good",
  "idempotency_key": "deprecate-good",
  "capability": "note.create",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:871bb33154511466f09c1e53968a85664a53b2f0c058c052887f0439c5837df1",
  "result": {
    "ok": true,
    "note_id": "note-demo-followup",
    "note_path": "knowledge/notes/mathematics/note-demo-followup.md",
    "deprecated": [
      "knowledge/notes/mathematics/note-demo.md"
    ],
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "note-demo": 1,
      "note-demo-followup": 1
    },
    "snapshot_after": "sha256:871bb33154511466f09c1e53968a85664a53b2f0c058c052887f0439c5837df1",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability note.create
```

## The successor landed

```scrut
$ $H/los-assert-file knowledge/notes/mathematics/note-demo-followup.md --sha256 5c1326bc07efa550cb59d2e1b91aee8b76854c1736f08f4dd1fba634974d1667
```

## The predecessor flipped to deprecated

```scrut
$ grep "^state:" knowledge/notes/mathematics/note-demo.md
state: deprecated
```

```scrut
$ $H/los-assert-file knowledge/notes/mathematics/note-demo.md --sha256 b86e630e810528b4be8869d074da1dabb15190f7a24a231ae1873da85562bd66
```

## The reverse link is not stored on the predecessor

```scrut
$ test -z "$(grep "note-demo-followup" knowledge/notes/mathematics/note-demo.md)" && echo unstored
unstored
```

## Deprecate the old concept id with its replacement

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import yaml; p = "knowledge/concepts.yaml"; d = yaml.safe_load(open(p)); [c.update({"deprecated": True, "replaced_by": "concept-expected-value"}) for c in d["concepts"] if c["id"] == "concept-variance"]; open(p, "w").write(yaml.safe_dump(d, sort_keys=False))'
```

## The registry carries the replacement pointer

```scrut
$ $H/los-assert-file knowledge/concepts.yaml --sha256 b427e03cb45d03481bf78a0e378861ececed0db59e3993a403f12e25373cebfc
```

## Rebuild generated outputs

```scrut
$ los generate
published generated/manifest.json (atomic contract snapshot)
```

## The reverse link is generated

```scrut
$ grep -c "note-demo-followup" generated/backlinks.json
1
```
