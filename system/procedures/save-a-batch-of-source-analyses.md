---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Save a batch of source analyses (WORKFLOWS §25b)

Executable transcript of the drafts file: observe the source bytes,
draft the batch, prepare the staging dir and exact envelope, review
both, and submit the envelope unchanged. A second batch prepped
before the first submits goes stale; a tampered staging body is
refused by its content hash; a draft whose live bytes disagree with
recorded is refused at prep. `tests/test_procedures.py` runs it with
Scrut; `<REPO>` comes from the `LOS_REPO` environment variable the
test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Observe the source bytes before drafting

```scrut
$ MAT_SHA=$(sha256sum "$(dirname "$LOS_FX")/materials/source-demo-book/book.pdf" | cut -d' ' -f1) && echo "$MAT_SHA"
61b4d4e33f928a4f6801ae74b3e940e0cfac1285aa4a958d46ce0ae142b49ed6
```

## Draft the first batch: two notes, one drafts file

1. **Draft.** Write UTF-8 JSON:
   `{"notes": [{"id", "title", "path", "binding", "body"}]}` with bodies
   inline — 1 to 20 notes, no `frozen_input_*` fields (prep derives every
   hash from the body bytes). Body bytes are exactly the UTF-8 encoding of
   each body string: leading whitespace and CRLF survive verbatim.
   For a resolved local source, `binding.material` is a path relative to the
   `materials/` tree, without a `material://` scheme or a leading `materials/`.
   The drafter supplies `live_source_digest` equal to
   `recorded_source_digest` as bare 64-character hex for the observed bytes;
   prep derives only `frozen_input_*`. One note uses the same batch format.
   The boundary also accepts the read surface's own spellings and normalizes
   them before any check, always storing the canonical form: a
   `material://SOURCE_ID/REL` URI whose authority equals `binding.source_id`
   (resolved through the source's registered material folder), a leading
   `materials/` prefix, and `sha256:`-prefixed digests. Each `material-span`
   span already carries a ready `binding` block with exactly these canonical
   values; the draft adds only `inspected_range`.

   ```json
   {"notes": [{"id": "note-example-analysis", "title": "Example analysis",
     "path": "knowledge/notes/data-systems/note-example-analysis.md",
     "binding": {"resolution": "resolved", "source_id": "source-example-course",
       "material": "course/deck.pdf",
       "recorded_source_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
       "live_source_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
       "inspected_range": {"start": 1, "end": 3}},
     "body": "Analysis of the inspected pages.\n"}]}
   ```

   Replace the example source, path, range and digest with the source's
   registered material and the bytes actually observed before preparing.
   `inspected_range` is inclusive physical PDF pages (cover = page 1) for
   PDFs, or inclusive one-based physical file lines for Markdown and plain
   text. A heading such as "Section 1" is a locator, not line 1. For local
   text, `material-span UNIT_ID ROUTE_ID --extract` reports the line range
   actually displayed in its bounded excerpt. Cite only the lines inspected;
   a truncated excerpt does not attest to later lines.
   For a stage placement that narrows its parent route, add
   `--stage STAGE_ID --resource-index N` using the zero-based resource position
   from that stage's plan context. Core resolves the canonical placement under
   the same snapshot guard; callers never submit an arbitrary path or locator.
2. **Prepare.**
   `note-analysis-prepare --drafts drafts.json --out <dir>` with the
   staging dir outside the repository. Prep validates every draft,
   derives the hashes, dry-checks each note against current state (new
   vs replay, collisions, resolved-source observability), then stages
   `bodies/<note-id>.bin` plus `envelope.json` and prints the per-note
   report. It writes nothing canonical; `bodies/` is rebuilt every run.
3. **Review** the staged bodies and the envelope. This is the step the
   gateway cannot do for you.
4. **Submit** the exact envelope:

   ```bash
   .venv/bin/python tools/los.py capability note.analysis.save_batch --payload-file <out>/envelope.json
   ```

   Any canonical change between prep and submit surfaces as
   `STALE_SNAPSHOT` — re-run prep. Tampered or moved staging files are
   refused by the content hashes and intent binding, never silently
   accepted.

```scrut
$ cat > "$TMPDIR/batch1.json" <<EOF
> {"notes": [
>   {"id": "note-batch-alpha", "title": "Alpha analysis",
>    "path": "knowledge/notes/mathematics/note-batch-alpha.md",
>    "binding": {"resolution": "resolved", "source_id": "source-demo-book",
>      "material": "source-demo-book/book.pdf",
>      "recorded_source_digest": "$MAT_SHA",
>      "live_source_digest": "$MAT_SHA",
>      "inspected_range": {"start": 1, "end": 1}},
>    "body": "Alpha analysis of the inspected page.\n"},
>   {"id": "note-batch-beta", "title": "Beta analysis",
>    "path": "knowledge/notes/mathematics/note-batch-beta.md",
>    "binding": {"resolution": "resolved", "source_id": "source-demo-book",
>      "material": "source-demo-book/book.pdf",
>      "recorded_source_digest": "$MAT_SHA",
>      "live_source_digest": "$MAT_SHA",
>      "inspected_range": {"start": 1, "end": 1}},
>    "body": "Beta analysis of the inspected page.\n"}]}
> EOF
```

## Prepare the first batch

```scrut
$ los note-analysis-prepare --drafts "$TMPDIR/batch1.json" --out "$TMPDIR/stage1" | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["ok"]); print(d["expected_snapshot"]); print(json.dumps(d["expected_revisions"], sort_keys=True)); [print(n["note_id"], n["note_path"], n["predicted_new"], n["frozen_input_sha256"]) for n in d["notes"]]'
True
sha256:08fdd4d86bb9d12fbb4b804df720b02a980031c30cb9f7007c9b425b46ef43c5
{"note-batch-alpha": 0, "note-batch-beta": 0}
note-batch-alpha knowledge/notes/mathematics/note-batch-alpha.md True aeb4d9b96ff02421baa4e0651d4d25e3e830ebd12b4eea4f5e69ab7f5a6078d6
note-batch-beta knowledge/notes/mathematics/note-batch-beta.md True 472e7d8ca1f330aa3ec439018461903df5d505c85ff47175074fcee5a24a9070
```

## Review the staged bodies

```scrut
$ (cd "$TMPDIR/stage1" && ls && ls bodies)
bodies
envelope.json
note-batch-alpha.bin
note-batch-beta.bin
```

```scrut
$ cat "$TMPDIR/stage1/bodies/note-batch-alpha.bin"
Alpha analysis of the inspected page.
```

## Review the staged envelope

```scrut
$ cat "$TMPDIR/stage1/envelope.json" | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["capability"], d["channel"], d["expected_snapshot"]); [print(n["analysis"]["id"], n["analysis"]["path"], n["body_file_sha256"]) for n in d["payload"]["bundle"]["notes"]]'
note.analysis.save_batch operator sha256:08fdd4d86bb9d12fbb4b804df720b02a980031c30cb9f7007c9b425b46ef43c5
note-batch-alpha knowledge/notes/mathematics/note-batch-alpha.md sha256:aeb4d9b96ff02421baa4e0651d4d25e3e830ebd12b4eea4f5e69ab7f5a6078d6
note-batch-beta knowledge/notes/mathematics/note-batch-beta.md sha256:472e7d8ca1f330aa3ec439018461903df5d505c85ff47175074fcee5a24a9070
```

## Draft and prepare the second batch before the first submits

```scrut
$ cat > "$TMPDIR/batch2.json" <<EOF
> {"notes": [
>   {"id": "note-batch-gamma", "title": "Gamma analysis",
>    "path": "knowledge/notes/mathematics/note-batch-gamma.md",
>    "binding": {"resolution": "resolved", "source_id": "source-demo-book",
>      "material": "source-demo-book/book.pdf",
>      "recorded_source_digest": "$MAT_SHA",
>      "live_source_digest": "$MAT_SHA",
>      "inspected_range": {"start": 1, "end": 1}},
>    "body": "Gamma analysis of the inspected page.\n"}]}
> EOF
```

```scrut
$ los note-analysis-prepare --drafts "$TMPDIR/batch2.json" --out "$TMPDIR/stage2" | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["ok"]); print(d["expected_snapshot"]); print(json.dumps(d["expected_revisions"], sort_keys=True)); [print(n["note_id"], n["predicted_new"]) for n in d["notes"]]'
True
sha256:08fdd4d86bb9d12fbb4b804df720b02a980031c30cb9f7007c9b425b46ef43c5
{"note-batch-gamma": 0}
note-batch-gamma True
```

## Submit the first batch unchanged

```scrut
$ los capability note.analysis.save_batch --payload-file "$TMPDIR/stage1/envelope.json" | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); del d["request_id"]; del d["idempotency_key"]; print(json.dumps(d, indent=2, sort_keys=True))'
{
  "capability": "note.analysis.save_batch",
  "error": null,
  "ok": true,
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "replayed": false,
  "result": {
    "artifact_revisions": {
      "note-batch-alpha": 1,
      "note-batch-beta": 1
    },
    "created_note_ids": [
      "note-batch-alpha",
      "note-batch-beta"
    ],
    "note_paths": {
      "note-batch-alpha": "knowledge/notes/mathematics/note-batch-alpha.md",
      "note-batch-beta": "knowledge/notes/mathematics/note-batch-beta.md"
    },
    "ok": true,
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "replayed": false,
    "replayed_note_ids": [],
    "snapshot_after": "sha256:5e457d32ed80a9b7ca7eb3761b528e0867632c712fdf89f7ea526e47f25c0d68",
    "transaction_id": "transaction-20261001-090000-001"
  },
  "schema_version": 2,
  "snapshot_after": "sha256:5e457d32ed80a9b7ca7eb3761b528e0867632c712fdf89f7ea526e47f25c0d68",
  "transaction_id": "transaction-20261001-090000-001"
}
```

## Both analyses persisted with a receipt

```scrut
$ $H/los-assert-file knowledge/notes/mathematics/note-batch-alpha.md --sha256 5a65d0c2540e9c3ddfaa25060776f792740ba1310089526d691ae1eaeeb4d33b
```

```scrut
$ $H/los-assert-file knowledge/notes/mathematics/note-batch-beta.md --sha256 f0b3ecac5418502006bafe7289d89536e4866e168aaa37c0d2c066ab5a262758
```

```scrut
$ $H/los-assert-receipt --last --capability note.analysis.save_batch
```

## The receipt owns both analyses

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,os,yaml; ds=sorted(glob.glob("operations/transactions/transaction-*.yaml")); xs=[os.path.basename(x) for x in ds]; assert xs==["transaction-20200102-000000-001.yaml", "transaction-20261001-090000-001.yaml"], xs; d=yaml.safe_load(open(ds[-1])); assert d["capability"]=="note.analysis.save_batch", d["capability"]; w={x["path"]: x for x in d.get("writes") or []}; ea=w["knowledge/notes/mathematics/note-batch-alpha.md"]; eb=w["knowledge/notes/mathematics/note-batch-beta.md"]; assert ea["sha256_after"]=="5a65d0c2540e9c3ddfaa25060776f792740ba1310089526d691ae1eaeeb4d33b", ea; assert eb["sha256_after"]=="f0b3ecac5418502006bafe7289d89536e4866e168aaa37c0d2c066ab5a262758", eb; assert ea["created"] is True and eb["created"] is True, (ea, eb); print("owns", d["id"])'
owns transaction-20261001-090000-001
```

## Re-prepping the committed drafts predicts replay

```scrut
$ los note-analysis-prepare --drafts "$TMPDIR/batch1.json" --out "$TMPDIR/stage1b" | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["ok"]); print(json.dumps(d["expected_revisions"], sort_keys=True)); [print(n["note_id"], n["predicted_new"]) for n in d["notes"]]'
True
{"note-batch-alpha": 1, "note-batch-beta": 1}
note-batch-alpha False
note-batch-beta False
```

## Capture the pre-refusal state

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.store.fingerprint import canonical_fingerprint; from pathlib import Path; st={"fp": canonical_fingerprint(Path(".")), "rc": sorted(glob.glob("operations/transactions/transaction-*.yaml"))}; json.dump(st, open(os.environ["TMPDIR"]+"/fp-refuse-stale.json", "w")); print("captured", len(st["rc"]))'
captured 2
```

## The second batch now submits stale

```scrut
$ (set -o pipefail; los capability note.analysis.save_batch --payload-file "$TMPDIR/stage2/envelope.json" | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); del d["request_id"]; del d["idempotency_key"]; print(json.dumps(d, indent=2, sort_keys=True))')
{
  "capability": "note.analysis.save_batch",
  "error": {
    "code": "STALE_SNAPSHOT",
    "details": {
      "actual": "sha256:5e457d32ed80a9b7ca7eb3761b528e0867632c712fdf89f7ea526e47f25c0d68",
      "expected": "sha256:08fdd4d86bb9d12fbb4b804df720b02a980031c30cb9f7007c9b425b46ef43c5"
    },
    "message": "canonical state changed since this request was approved",
    "retryable": true
  },
  "ok": false,
  "receipt_path": null,
  "replayed": false,
  "result": {},
  "schema_version": 2,
  "snapshot_after": null,
  "transaction_id": null
}
[3]
```

## The stale refusal added no receipt and moved no canonical byte

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.store.fingerprint import canonical_fingerprint; from pathlib import Path; st=json.load(open(os.environ["TMPDIR"]+"/fp-refuse-stale.json")); fp=canonical_fingerprint(Path(".")); rc=sorted(glob.glob("operations/transactions/transaction-*.yaml")); assert fp==st["fp"], (fp, st["fp"]); assert rc==st["rc"], (rc, st["rc"]); print("unchanged")'
unchanged
```

## Re-prep the second batch against the moved snapshot

```scrut
$ los note-analysis-prepare --drafts "$TMPDIR/batch2.json" --out "$TMPDIR/stage2b" | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["ok"]); print(d["expected_snapshot"]); [print(n["note_id"], n["predicted_new"]) for n in d["notes"]]'
True
sha256:5e457d32ed80a9b7ca7eb3761b528e0867632c712fdf89f7ea526e47f25c0d68
note-batch-gamma True
```

## Submit the re-prepped batch

```scrut
$ los capability note.analysis.save_batch --payload-file "$TMPDIR/stage2b/envelope.json" | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); del d["request_id"]; del d["idempotency_key"]; print(json.dumps(d, indent=2, sort_keys=True))'
{
  "capability": "note.analysis.save_batch",
  "error": null,
  "ok": true,
  "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
  "replayed": false,
  "result": {
    "artifact_revisions": {
      "note-batch-gamma": 1
    },
    "created_note_ids": [
      "note-batch-gamma"
    ],
    "note_paths": {
      "note-batch-gamma": "knowledge/notes/mathematics/note-batch-gamma.md"
    },
    "ok": true,
    "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
    "replayed": false,
    "replayed_note_ids": [],
    "snapshot_after": "sha256:bccf0fcfe5e44a2e9d609dd516cf433854622d44a2ceacfd55cc88ff0d3b927d",
    "transaction_id": "transaction-20261001-090000-002"
  },
  "schema_version": 2,
  "snapshot_after": "sha256:bccf0fcfe5e44a2e9d609dd516cf433854622d44a2ceacfd55cc88ff0d3b927d",
  "transaction_id": "transaction-20261001-090000-002"
}
```

## The third analysis persisted with a receipt

```scrut
$ $H/los-assert-file knowledge/notes/mathematics/note-batch-gamma.md --sha256 8c9801067ffa84ee61b7e5ccdadff96f383f115bb50b09f0159f3dbfdf86dbd5
```

```scrut
$ $H/los-assert-receipt --last --capability note.analysis.save_batch
```

## The receipt owns the third analysis

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,os,yaml; ds=sorted(glob.glob("operations/transactions/transaction-*.yaml")); xs=[os.path.basename(x) for x in ds]; assert xs==["transaction-20200102-000000-001.yaml", "transaction-20261001-090000-001.yaml", "transaction-20261001-090000-002.yaml"], xs; d=yaml.safe_load(open(ds[-1])); assert d["capability"]=="note.analysis.save_batch", d["capability"]; w={x["path"]: x for x in d.get("writes") or []}; e=w["knowledge/notes/mathematics/note-batch-gamma.md"]; assert e["sha256_after"]=="8c9801067ffa84ee61b7e5ccdadff96f383f115bb50b09f0159f3dbfdf86dbd5", e; assert e["created"] is True, e; print("owns", d["id"])'
owns transaction-20261001-090000-002
```

## Capture the pre-tamper-refusal state

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.store.fingerprint import canonical_fingerprint; from pathlib import Path; st={"fp": canonical_fingerprint(Path(".")), "rc": sorted(glob.glob("operations/transactions/transaction-*.yaml"))}; json.dump(st, open(os.environ["TMPDIR"]+"/fp-refuse-tamper.json", "w")); print("captured", len(st["rc"]))'
captured 3
```

## A tampered staging body is refused by its content hash

```scrut
$ cat > "$TMPDIR/batch3.json" <<EOF
> {"notes": [
>   {"id": "note-batch-tamper", "title": "Tamper analysis",
>    "path": "knowledge/notes/mathematics/note-batch-tamper.md",
>    "binding": {"resolution": "resolved", "source_id": "source-demo-book",
>      "material": "source-demo-book/book.pdf",
>      "recorded_source_digest": "$MAT_SHA",
>      "live_source_digest": "$MAT_SHA",
>      "inspected_range": {"start": 1, "end": 1}},
>    "body": "Tamper analysis of the inspected page.\n"}]}
> EOF
```

```scrut
$ los note-analysis-prepare --drafts "$TMPDIR/batch3.json" --out "$TMPDIR/stage3" | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["ok"], d["notes"][0]["note_id"])'
True note-batch-tamper
```

```scrut
$ printf 'tampered bytes\n' > "$TMPDIR/stage3/bodies/note-batch-tamper.bin" && (set -o pipefail; los capability note.analysis.save_batch --payload-file "$TMPDIR/stage3/envelope.json" | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); del d["request_id"]; del d["idempotency_key"]; print(json.dumps(d, indent=2, sort_keys=True))')
{
  "capability": "note.analysis.save_batch",
  "error": {
    "code": "INVALID_REQUEST",
    "details": {},
    "message": "approved batch item 0 body file changed before use; expected sha256:bcee335730b1d48089a73aeb2c21680ff208f4bf23eb54a96c962dd4deb6c8c3, found sha256:ef350dfee9133c1f380419ddf838ed53ecdbac2065791bc1cf74b054887efc5c. Review the new bytes and create a new approval.",
    "retryable": false
  },
  "ok": false,
  "receipt_path": null,
  "replayed": false,
  "result": {},
  "schema_version": 2,
  "snapshot_after": null,
  "transaction_id": null
}
[2]
```

## The refused tamper wrote nothing canonical

```scrut
$ $H/los-assert-file knowledge/notes/mathematics/note-batch-tamper.md --absent
```

## The tamper refusal added no receipt and moved no canonical byte

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.store.fingerprint import canonical_fingerprint; from pathlib import Path; st=json.load(open(os.environ["TMPDIR"]+"/fp-refuse-tamper.json")); fp=canonical_fingerprint(Path(".")); rc=sorted(glob.glob("operations/transactions/transaction-*.yaml")); assert fp==st["fp"], (fp, st["fp"]); assert rc==st["rc"], (rc, st["rc"]); print("unchanged")'
unchanged
```

## Capture the pre-prep-refusal state

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.store.fingerprint import canonical_fingerprint; from pathlib import Path; st={"fp": canonical_fingerprint(Path(".")), "rc": sorted(glob.glob("operations/transactions/transaction-*.yaml"))}; json.dump(st, open(os.environ["TMPDIR"]+"/fp-refuse-prep.json", "w")); print("captured", len(st["rc"]))'
captured 3
```

## A draft whose live bytes disagree is refused at prep

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import json,os; p = os.path.join(os.environ["TMPDIR"], "batch3.json"); d = json.load(open(p)); d["notes"][0]["id"] = "note-batch-baddigest"; d["notes"][0]["path"] = "knowledge/notes/mathematics/note-batch-baddigest.md"; d["notes"][0]["binding"]["live_source_digest"] = "0" * 64; json.dump(d, open(os.path.join(os.environ["TMPDIR"], "batch4.json"), "w"))'
```

```scrut {output_stream: stderr}
$ los note-analysis-prepare --drafts "$TMPDIR/batch4.json" --out "$TMPDIR/stage4"
los: INVALID_REQUEST: draft 0: resolved bindings must show live bytes equal to recorded
[2]
```

## The prep refusal added no receipt and moved no canonical byte

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.store.fingerprint import canonical_fingerprint; from pathlib import Path; st=json.load(open(os.environ["TMPDIR"]+"/fp-refuse-prep.json")); fp=canonical_fingerprint(Path(".")); rc=sorted(glob.glob("operations/transactions/transaction-*.yaml")); assert fp==st["fp"], (fp, st["fp"]); assert rc==st["rc"], (rc, st["rc"]); print("unchanged")'
unchanged
```

## Validate the saved batches

```scrut
$ los validate | tail -n 1
0 error(s), 9 warning(s) — OK
```
