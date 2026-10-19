---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Maintain a crosswalk (WORKFLOWS §16)

Executable transcript of crosswalk upkeep: the crosswalk note itself
carries narrative only, the judgment change lands on the source
record through its reviewed revision, the rebuilt index surfaces the
amendment, and a judgment table smuggled into the note trips the
validator's warning. `tests/test_procedures.py` runs it with Scrut;
`<REPO>` comes from the `LOS_REPO` environment variable the test
sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Stage the crosswalk narrative

1. narrative changes (why a source suits a lecture, sequencing advice) → edit the crosswalk note;
2. judgment changes (strengths, weaknesses, level, per-concept usefulness) → edit the source records;
3. rebuild the source index; confirm the generated selector view reflects the change;
4. the validator warns if a crosswalk note accumulates judgment tables — that content belongs in source records.

```scrut
$ cat > "$TMPDIR/crosswalk-body.md" <<'EOF'
> # Demo crosswalk
>
> This note maps the demo readings to each other. The Demo Book opens
> the topic; the lectures follow it.
> EOF
```

## Seal the crosswalk note with derived guards

```scrut {output_stream: stderr}
$ BODY_SHA=$(sha256sum "$TMPDIR/crosswalk-body.md" | cut -d' ' -f1) && $H/los-seal --capability note.create --payload "{\"note\": {\"id\": \"note-demo-crosswalk\", \"title\": \"Demo crosswalk\", \"path\": \"knowledge/notes/mathematics/note-demo-crosswalk.md\", \"role\": \"crosswalk\", \"sources\": [\"source-demo-book\"]}, \"body_file\": \"$TMPDIR/crosswalk-body.md\", \"body_file_sha256\": \"sha256:$BODY_SHA\"}" --key crosswalk-create --request-id request-crosswalk-create --guards auto --out "$TMPDIR/crosswalk-create.json"
seal_envelope: guards auto: note-demo-crosswalk=0
```

## Submit the crosswalk note

```scrut
$ los capability note.create --payload-file "$TMPDIR/crosswalk-create.json"
{
  "schema_version": 2,
  "request_id": "request-crosswalk-create",
  "idempotency_key": "crosswalk-create",
  "capability": "note.create",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:dd21b38ecedf0d41d5ec0c4a95b426a9dead6cd55fc0de2963fb3603c7b84d12",
  "result": {
    "ok": true,
    "note_id": "note-demo-crosswalk",
    "note_path": "knowledge/notes/mathematics/note-demo-crosswalk.md",
    "deprecated": [],
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "note-demo-crosswalk": 1
    },
    "snapshot_after": "sha256:dd21b38ecedf0d41d5ec0c4a95b426a9dead6cd55fc0de2963fb3603c7b84d12",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability note.create
```

## The crosswalk note landed

```scrut
$ $H/los-assert-file knowledge/notes/mathematics/note-demo-crosswalk.md --sha256 cb0758d8605c4b042289733cdc72d4cd5b3b02a364ebff60d267d42f7fd55da0
```

## The receipt owns the crosswalk note

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,os,yaml; ds=sorted(glob.glob("operations/transactions/transaction-*.yaml")); xs=[os.path.basename(x) for x in ds]; assert xs==["transaction-20200102-000000-001.yaml", "transaction-20261001-090000-001.yaml"], xs; d=yaml.safe_load(open(ds[-1])); assert d["capability"]=="note.create", d["capability"]; w={x["path"]: x for x in d.get("writes") or []}; e=w["knowledge/notes/mathematics/note-demo-crosswalk.md"]; assert e["sha256_after"]=="cb0758d8605c4b042289733cdc72d4cd5b3b02a364ebff60d267d42f7fd55da0", e; assert e["created"] is True, e; print("owns", d["id"])'
owns transaction-20261001-090000-001
```

## Stage the narrative edit

```scrut
$ cat > "$TMPDIR/crosswalk-narrative.md" <<'EOF'
> ---
> id: note-demo-crosswalk
> type: note
> title: Demo crosswalk
> created: 2026-10-01
> role: crosswalk
> sources: [source-demo-book]
> ---
>
> # Demo crosswalk
>
> This note maps the demo readings to each other. The Demo Book opens
> the topic; the lectures follow it. Read the book first, then lecture one.
> EOF
```

## Seal the narrative revision with derived guards

```scrut {output_stream: stderr}
$ REV_SHA=$(sha256sum "$TMPDIR/crosswalk-narrative.md" | cut -d' ' -f1) && $H/los-seal --capability note.revise --payload "{\"note_id\": \"note-demo-crosswalk\", \"file\": \"$TMPDIR/crosswalk-narrative.md\", \"file_sha256\": \"sha256:$REV_SHA\"}" --key crosswalk-narrative --request-id request-crosswalk-narrative --guards auto --out "$TMPDIR/crosswalk-narrative.json"
seal_envelope: guards auto: note-demo-crosswalk=1
```

## Submit the narrative revision

```scrut
$ los capability note.revise --payload-file "$TMPDIR/crosswalk-narrative.json"
{
  "schema_version": 2,
  "request_id": "request-crosswalk-narrative",
  "idempotency_key": "crosswalk-narrative",
  "capability": "note.revise",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-002",
  "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
  "snapshot_after": "sha256:8a85f9fed15784cd6abb8abe1c24c1512d142ad263a47cbe6424811de70dc929",
  "result": {
    "ok": true,
    "note_id": "note-demo-crosswalk",
    "path": "knowledge/notes/mathematics/note-demo-crosswalk.md",
    "transaction_id": "transaction-20261001-090000-002",
    "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
    "artifact_revisions": {
      "note-demo-crosswalk": 2
    },
    "snapshot_after": "sha256:8a85f9fed15784cd6abb8abe1c24c1512d142ad263a47cbe6424811de70dc929",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability note.revise
```

## The narrative landed

```scrut
$ $H/los-assert-file knowledge/notes/mathematics/note-demo-crosswalk.md --sha256 2dd4e3746b2f148ab86e1090dc30e8dc7eb8b12b96b86c35be3b0ef42187d1f3
```

## The receipt owns the narrative

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,os,yaml; ds=sorted(glob.glob("operations/transactions/transaction-*.yaml")); xs=[os.path.basename(x) for x in ds]; assert xs==["transaction-20200102-000000-001.yaml", "transaction-20261001-090000-001.yaml", "transaction-20261001-090000-002.yaml"], xs; d=yaml.safe_load(open(ds[-1])); assert d["capability"]=="note.revise", d["capability"]; w={x["path"]: x for x in d.get("writes") or []}; e=w["knowledge/notes/mathematics/note-demo-crosswalk.md"]; assert e["sha256_after"]=="2dd4e3746b2f148ab86e1090dc30e8dc7eb8b12b96b86c35be3b0ef42187d1f3", e; assert e["created"] is False, e; print("owns", d["id"])'
owns transaction-20261001-090000-002
```

## Review the judgment revision on the source record

```scrut
$ eval "$(los source-revise --record '{"id": "source-demo-book", "evaluations": [{"level": "introductory", "roles": ["first-learning"], "strengths": ["clear intuition", "worked variance examples"], "concepts": ["concept-expected-value"]}]}' --check | $H/los-bind CROSS_DIFF '$.diff_sha256')" && echo "$CROSS_DIFF"
sha256:5cf4f53f2b78917c2c821605236cb675c32bead66dec3d73a7f3519798303260
```

## Seal the judgment with derived guards

```scrut {output_stream: stderr}
$ $H/los-seal --capability source.record.revise --payload "{\"record\": {\"id\": \"source-demo-book\", \"evaluations\": [{\"level\": \"introductory\", \"roles\": [\"first-learning\"], \"strengths\": [\"clear intuition\", \"worked variance examples\"], \"concepts\": [\"concept-expected-value\"]}]}, \"expected_diff_sha256\": \"$CROSS_DIFF\"}" --key crosswalk-judgment --request-id request-crosswalk-judgment --guards auto --out "$TMPDIR/crosswalk-judgment.json"
seal_envelope: guards auto: source-demo-book=0
```

## Submit the judgment

```scrut
$ los capability source.record.revise --payload-file "$TMPDIR/crosswalk-judgment.json"
{
  "schema_version": 2,
  "request_id": "request-crosswalk-judgment",
  "idempotency_key": "crosswalk-judgment",
  "capability": "source.record.revise",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-003",
  "receipt_path": "operations/transactions/transaction-20261001-090000-003.yaml",
  "snapshot_after": "sha256:7851690e6032655af2cc2e955ca529f33bd0b26f1e524c033755fad4e102ff15",
  "result": {
    "ok": true,
    "transaction_id": "transaction-20261001-090000-003",
    "receipt_path": "operations/transactions/transaction-20261001-090000-003.yaml",
    "artifact_revisions": {
      "source-demo-book": 1
    },
    "snapshot_after": "sha256:7851690e6032655af2cc2e955ca529f33bd0b26f1e524c033755fad4e102ff15",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability source.record.revise
```

## The source record carries the amended evaluation

```scrut
$ $H/los-assert-file sources/sources.yaml --sha256 c23027dc4edb9de11bdb80304adbc270c3e45d6b8d55352a8f2b3e12a13fa398
```

## The receipt owns the amended record

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,os,yaml; ds=sorted(glob.glob("operations/transactions/transaction-*.yaml")); xs=[os.path.basename(x) for x in ds]; assert xs==["transaction-20200102-000000-001.yaml", "transaction-20261001-090000-001.yaml", "transaction-20261001-090000-002.yaml", "transaction-20261001-090000-003.yaml"], xs; d=yaml.safe_load(open(ds[-1])); assert d["capability"]=="source.record.revise", d["capability"]; w={x["path"]: x for x in d.get("writes") or []}; e=w["sources/sources.yaml"]; assert e["sha256_after"]=="c23027dc4edb9de11bdb80304adbc270c3e45d6b8d55352a8f2b3e12a13fa398", e; assert e["created"] is False, e; print("owns", d["id"])'
owns transaction-20261001-090000-003
```

## Rebuild the source index

```scrut
$ los generate
published generated/manifest.json (atomic contract snapshot)
```

## The rebuilt index surfaces the amendment

```scrut
$ grep -c "worked variance examples" generated/source-index.md
1
```

## The consuming search surfaces the amended source

```scrut
$ los search "worked variance" | $LOS_REPO/.venv/bin/python -c 'import json,sys; print(sorted(r["id"] for r in json.load(sys.stdin)))'
['source-demo-book']
```

## A judgment table in the note trips the warning

```scrut
$ cat > "$TMPDIR/crosswalk-table.md" <<'EOF'
> ---
> id: note-demo-crosswalk
> type: note
> title: Demo crosswalk
> created: 2026-10-01
> role: crosswalk
> sources: [source-demo-book]
> ---
>
> # Demo crosswalk
>
> This note maps the demo readings to each other.
>
> | Source | Strengths |
> | --- | --- |
> | Demo Book | clear intuition |
> EOF
```

```scrut {output_stream: stderr}
$ REV_SHA=$(sha256sum "$TMPDIR/crosswalk-table.md" | cut -d' ' -f1) && $H/los-seal --capability note.revise --payload "{\"note_id\": \"note-demo-crosswalk\", \"file\": \"$TMPDIR/crosswalk-table.md\", \"file_sha256\": \"sha256:$REV_SHA\"}" --key crosswalk-table --request-id request-crosswalk-table --guards auto --out "$TMPDIR/crosswalk-table.json"
seal_envelope: guards auto: note-demo-crosswalk=2
```

```scrut
$ los capability note.revise --payload-file "$TMPDIR/crosswalk-table.json"
{
  "schema_version": 2,
  "request_id": "request-crosswalk-table",
  "idempotency_key": "crosswalk-table",
  "capability": "note.revise",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-004",
  "receipt_path": "operations/transactions/transaction-20261001-090000-004.yaml",
  "snapshot_after": "sha256:0f819cf1fcaa586f9137db709565654c0261f95fc81c5c546059bd4b619f2608",
  "result": {
    "ok": true,
    "note_id": "note-demo-crosswalk",
    "path": "knowledge/notes/mathematics/note-demo-crosswalk.md",
    "transaction_id": "transaction-20261001-090000-004",
    "receipt_path": "operations/transactions/transaction-20261001-090000-004.yaml",
    "artifact_revisions": {
      "note-demo-crosswalk": 3
    },
    "snapshot_after": "sha256:0f819cf1fcaa586f9137db709565654c0261f95fc81c5c546059bd4b619f2608",
    "replayed": false
  },
  "error": null
}
```

## The table revision persisted with its receipt

```scrut
$ $H/los-assert-file knowledge/notes/mathematics/note-demo-crosswalk.md --sha256 b6dad8de790219ca982dc078c0e631cd4a20faa21d69418d1b364286a18cdb58
```

## The receipt owns the table bytes

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,os,yaml; ds=sorted(glob.glob("operations/transactions/transaction-*.yaml")); xs=[os.path.basename(x) for x in ds]; assert xs==["transaction-20200102-000000-001.yaml", "transaction-20261001-090000-001.yaml", "transaction-20261001-090000-002.yaml", "transaction-20261001-090000-003.yaml", "transaction-20261001-090000-004.yaml"], xs; d=yaml.safe_load(open(ds[-1])); assert d["capability"]=="note.revise", d["capability"]; w={x["path"]: x for x in d.get("writes") or []}; e=w["knowledge/notes/mathematics/note-demo-crosswalk.md"]; assert e["sha256_after"]=="b6dad8de790219ca982dc078c0e631cd4a20faa21d69418d1b364286a18cdb58", e; assert e["created"] is False, e; print("owns", d["id"])'
owns transaction-20261001-090000-004
```

```scrut
$ los validate | grep -c "CROSSWALK-TABLE"
1
```

## Move the judgment back out

```scrut {output_stream: stderr}
$ REV_SHA=$(sha256sum "$TMPDIR/crosswalk-narrative.md" | cut -d' ' -f1) && $H/los-seal --capability note.revise --payload "{\"note_id\": \"note-demo-crosswalk\", \"file\": \"$TMPDIR/crosswalk-narrative.md\", \"file_sha256\": \"sha256:$REV_SHA\"}" --key crosswalk-restore --request-id request-crosswalk-restore --guards auto --out "$TMPDIR/crosswalk-restore.json"
seal_envelope: guards auto: note-demo-crosswalk=3
```

```scrut
$ los capability note.revise --payload-file "$TMPDIR/crosswalk-restore.json"
{
  "schema_version": 2,
  "request_id": "request-crosswalk-restore",
  "idempotency_key": "crosswalk-restore",
  "capability": "note.revise",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-005",
  "receipt_path": "operations/transactions/transaction-20261001-090000-005.yaml",
  "snapshot_after": "sha256:7851690e6032655af2cc2e955ca529f33bd0b26f1e524c033755fad4e102ff15",
  "result": {
    "ok": true,
    "note_id": "note-demo-crosswalk",
    "path": "knowledge/notes/mathematics/note-demo-crosswalk.md",
    "transaction_id": "transaction-20261001-090000-005",
    "receipt_path": "operations/transactions/transaction-20261001-090000-005.yaml",
    "artifact_revisions": {
      "note-demo-crosswalk": 4
    },
    "snapshot_after": "sha256:7851690e6032655af2cc2e955ca529f33bd0b26f1e524c033755fad4e102ff15",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability note.revise
```

## The restored bytes match the narrative state

```scrut
$ $H/los-assert-file knowledge/notes/mathematics/note-demo-crosswalk.md --sha256 2dd4e3746b2f148ab86e1090dc30e8dc7eb8b12b96b86c35be3b0ef42187d1f3
```

## The receipt owns the restored bytes

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,os,yaml; ds=sorted(glob.glob("operations/transactions/transaction-*.yaml")); xs=[os.path.basename(x) for x in ds]; assert xs==["transaction-20200102-000000-001.yaml", "transaction-20261001-090000-001.yaml", "transaction-20261001-090000-002.yaml", "transaction-20261001-090000-003.yaml", "transaction-20261001-090000-004.yaml", "transaction-20261001-090000-005.yaml"], xs; d=yaml.safe_load(open(ds[-1])); assert d["capability"]=="note.revise", d["capability"]; w={x["path"]: x for x in d.get("writes") or []}; e=w["knowledge/notes/mathematics/note-demo-crosswalk.md"]; assert e["sha256_after"]=="2dd4e3746b2f148ab86e1090dc30e8dc7eb8b12b96b86c35be3b0ef42187d1f3", e; assert e["created"] is False, e; print("owns", d["id"])'
owns transaction-20261001-090000-005
```

## The warning is gone with the table

```scrut
$ los validate | grep -c "CROSSWALK-TABLE" || true
0
```
