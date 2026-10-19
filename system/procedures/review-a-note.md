---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Review a note (WORKFLOWS §13)

Executable transcript of one semantic review: the approved reasoning
update lands with the review date set and the uncertainty preserved,
then the outputs rebuild. `tests/test_procedures.py` runs it with
Scrut; `<REPO>` comes from the `LOS_REPO` environment variable the
test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Stage the approved revision with the review date

```scrut
$ cat > "$TMPDIR/review-revised.md" <<'EOF'
> ---
> id: note-demo
> type: note
> title: Demo note
> created: 2026-07-16
> role: synthesis
> reviewed: 2026-10-01
> concepts: [concept-expected-value]
> sources: [source-demo-book]
> ---
>
> Body prose, reviewed with approval. The middle step stays uncertain.
> EOF
```

## Seal the revision with derived guards

```scrut {output_stream: stderr}
$ REV_SHA=$(sha256sum "$TMPDIR/review-revised.md" | cut -d' ' -f1) && $H/los-seal --capability note.revise --payload "{\"note_id\": \"note-demo\", \"file\": \"$TMPDIR/review-revised.md\", \"file_sha256\": \"sha256:$REV_SHA\"}" --key review-demo --request-id request-review-demo --guards auto --out "$TMPDIR/review-demo.json"
seal_envelope: guards auto: note-demo=0
```

## Submit the revision

```scrut
$ los capability note.revise --payload-file "$TMPDIR/review-demo.json"
{
  "schema_version": 2,
  "request_id": "request-review-demo",
  "idempotency_key": "review-demo",
  "capability": "note.revise",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:7ac266e1d629b60d8999a72718a0b5bfe8e5fd80f60bee2aea0d5c2af30c0112",
  "result": {
    "ok": true,
    "note_id": "note-demo",
    "path": "knowledge/notes/mathematics/note-demo.md",
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "note-demo": 1
    },
    "snapshot_after": "sha256:7ac266e1d629b60d8999a72718a0b5bfe8e5fd80f60bee2aea0d5c2af30c0112",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability note.revise
```

## The review landed with its date

```scrut
$ grep "^reviewed:" knowledge/notes/mathematics/note-demo.md
reviewed: 2026-10-01
```

```scrut
$ $H/los-assert-file knowledge/notes/mathematics/note-demo.md --sha256 b9fc3883b694b2e8ce5583efe144e12664ad6c6d44c8cc5828fa7586693a5cb1
```

## The receipt owns the reviewed bytes

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,os,yaml; ds=sorted(glob.glob("operations/transactions/transaction-*.yaml")); xs=[os.path.basename(x) for x in ds]; assert xs==["transaction-20200102-000000-001.yaml", "transaction-20261001-090000-001.yaml"], xs; d=yaml.safe_load(open(ds[-1])); assert d["capability"]=="note.revise", d["capability"]; w={x["path"]: x for x in d.get("writes") or []}; e=w["knowledge/notes/mathematics/note-demo.md"]; assert e["sha256_after"]=="b9fc3883b694b2e8ce5583efe144e12664ad6c6d44c8cc5828fa7586693a5cb1", e; assert e["created"] is False, e; print("owns", d["id"])'
owns transaction-20261001-090000-001
```

## Rebuild generated outputs

```scrut
$ los generate
published generated/manifest.json (atomic contract snapshot)
```
