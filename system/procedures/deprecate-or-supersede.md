---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Deprecate or supersede (WORKFLOWS §15)

Executable transcript of replacing one note and one concept: the
successor note is an ordinary creation whose record declares
`supersedes`, which deprecates the predecessor atomically; the concept
half marks `deprecated` with `replaced_by` (no approved capability
writes the concept registry, so that edit runs only in this disposable
transcript fixture). Generated indexes mark both as deprecated without
erasing them. `tests/test_procedures.py` runs it with Scrut; `<REPO>`
comes from the `LOS_REPO` environment variable the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Stage the successor body

```scrut
$ cat > "$TMPDIR/successor-body.md" <<'EOF'
> # Worked variance, revised
>
> The setup now carries the exact page range.
> EOF
```

## Seal the successor with its supersedes declaration

```scrut {output_stream: stderr}
$ BODY_SHA=$(sha256sum "$TMPDIR/successor-body.md" | cut -d' ' -f1) && $H/los-seal --capability note.create --payload "{\"note\": {\"id\": \"note-worked-variance-v2\", \"title\": \"Worked variance, revised\", \"path\": \"knowledge/notes/mathematics/note-worked-variance-v2.md\", \"concepts\": [\"concept-variance\"], \"supersedes\": [\"note-demo\"]}, \"body_file\": \"$TMPDIR/successor-body.md\", \"body_file_sha256\": \"sha256:$BODY_SHA\"}" --key s15-create --request-id request-s15-create --guards auto --out "$TMPDIR/s15-create.json"
seal_envelope: guards auto: note-demo=0, note-worked-variance-v2=0
```

## Submit the successor

```scrut
$ los capability note.create --payload-file "$TMPDIR/s15-create.json"
{
  "schema_version": 2,
  "request_id": "request-s15-create",
  "idempotency_key": "s15-create",
  "capability": "note.create",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:4c1ecebc2eb773924098580a5e43467ead96feef3753b2046e9bea18e988cbfa",
  "result": {
    "ok": true,
    "note_id": "note-worked-variance-v2",
    "note_path": "knowledge/notes/mathematics/note-worked-variance-v2.md",
    "deprecated": [
      "knowledge/notes/mathematics/note-demo.md"
    ],
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "note-demo": 1,
      "note-worked-variance-v2": 1
    },
    "snapshot_after": "sha256:4c1ecebc2eb773924098580a5e43467ead96feef3753b2046e9bea18e988cbfa",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability note.create
```

## The predecessor is deprecated in the same transaction

```scrut
$ grep -n "state: deprecated" knowledge/notes/mathematics/note-demo.md
11:state: deprecated
```

## The successor landed under its id

```scrut
$ $H/los-assert-file knowledge/notes/mathematics/note-worked-variance-v2.md --sha256 2aff74c86da76b02cb3f7bb17a379370885faadfd66029b5616c7c8148358ede
```

## The receipt owns both the creation and the deprecation

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,os,yaml; ds=sorted(glob.glob("operations/transactions/transaction-*.yaml")); xs=[os.path.basename(x) for x in ds]; assert xs==["transaction-20200102-000000-001.yaml", "transaction-20261001-090000-001.yaml"], xs; d=yaml.safe_load(open(ds[-1])); assert d["capability"]=="note.create", d["capability"]; w={x["path"]: x for x in d.get("writes") or []}; assert w["knowledge/notes/mathematics/note-worked-variance-v2.md"]["created"] is True, w; assert w["knowledge/notes/mathematics/note-demo.md"]["created"] is False, w; print("owns", d["id"])'
owns transaction-20261001-090000-001
```

## An unknown predecessor is refused

```scrut {output_stream: stderr}
$ BODY_SHA=$(sha256sum "$TMPDIR/successor-body.md" | cut -d' ' -f1) && $H/los-seal --capability note.create --payload "{\"note\": {\"id\": \"note-worked-variance-v3\", \"title\": \"v3\", \"path\": \"knowledge/notes/mathematics/note-worked-variance-v3.md\", \"supersedes\": [\"note-nope\"]}, \"body_file\": \"$TMPDIR/successor-body.md\", \"body_file_sha256\": \"sha256:$BODY_SHA\"}" --key s15-bad --request-id request-s15-bad --guards auto --out "$TMPDIR/s15-bad.json"
seal_envelope: superseded note does not exist: 'note-nope'; fix the payload and seal again
[2]
```

## Deprecate the concept with its replacement

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import yaml; p = "knowledge/concepts.yaml"; d = yaml.safe_load(open(p)); d["concepts"].append({"id": "concept-sample-variance", "label": "Sample variance", "aliases": ["Stichprobenvarianz"]}); [c.update({"deprecated": True, "replaced_by": "concept-sample-variance"}) for c in d["concepts"] if c["id"] == "concept-variance"]; open(p, "w").write(yaml.safe_dump(d, sort_keys=False)); print("deprecated concept-variance")'
deprecated concept-variance
```

## The deprecation validates clean

```scrut
$ (set -o pipefail; los validate | tail -n 1)
0 error(s), 10 warning(s) — OK
```

## Rebuild the generated outputs

```scrut
$ los generate
published generated/manifest.json (atomic contract snapshot)
```

## The indexes mark the deprecated records without erasing them

```scrut
$ grep -n "deprecated" generated/concept-index.md
12:**V:** [Variance](#variance-deprecated)
39:## Variance *(deprecated)*
```

## The reverse link is generated, never stored

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import json; d = json.load(open("generated/backlinks.json")); print(d["note_incoming"]["note-demo"])'
['note-worked-variance-v2']
```

```scrut
$ grep -c "note-worked-variance-v2" knowledge/notes/mathematics/note-demo.md || echo "predecessor holds no forward pointer"
0
predecessor holds no forward pointer
```
