---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Create or evolve a durable note (WORKFLOWS §3)

Executable transcript of durable-note routing: search first, revise
the existing note when it fits, otherwise create with a stable
suffix-free id and registered concept, source, and workspace context.
`reference` keeps its dedicated capability and is refused here; a
learner's question goes through its own save; the shelving branch is
the existing shelving transcript. `tests/test_procedures.py` runs it
with Scrut; `<REPO>` comes from the `LOS_REPO` environment variable
the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Search for an existing note with the same purpose

1. search for an existing note with the same purpose;
2. update it when appropriate, through `note.revise` after explicit approval —
   identity, path, and role stay stable;
3. otherwise assign a stable note ID (no gratuitous numeric suffix);
4. assign a role if not `synthesis` (`exercise-bank`, `mock-exam`,
   `crosswalk`, …); `reference` and `question` keep their dedicated
   capabilities and are refused by `note.create`;
5. stage the exact body bytes and apply them with a `note.create` envelope
   (§25c): the handler writes `knowledge/notes/<bucket>/<note-id>.md` —
   filename is always the ID, bucket is the nearest reasonable domain;
6. attach relevant concept and source IDs (each must already be registered);
7. preserve uncertainty and unfinished reasoning;
8. add the workspace ID as context when useful;
9. validate, then rebuild generated outputs.

```scrut
$ los search demo --type note | $LOS_REPO/.venv/bin/python -c 'import json,sys; print(sorted(r["id"] for r in json.load(sys.stdin)))'
['note-demo', 'note-demo-analysis']
```

## No note yet covers triangulation

```scrut
$ los search triangulation-memo --type note
[]
```

## Stage the revised bytes for the existing note

```scrut
$ cat > "$TMPDIR/durable-revised.md" <<'EOF'
> ---
> id: note-demo
> type: note
> title: Demo note
> created: 2026-07-16
> role: synthesis
> concepts: [concept-expected-value]
> sources: [source-demo-book]
> ---
>
> Body prose, revised with approval.
> EOF
```

## Seal the revision with derived guards

```scrut {output_stream: stderr}
$ REV_SHA=$(sha256sum "$TMPDIR/durable-revised.md" | cut -d' ' -f1) && $H/los-seal --capability note.revise --payload "{\"note_id\": \"note-demo\", \"file\": \"$TMPDIR/durable-revised.md\", \"file_sha256\": \"sha256:$REV_SHA\"}" --key durable-revise-demo --request-id request-durable-revise-demo --guards auto --out "$TMPDIR/durable-revise.json"
seal_envelope: guards auto: note-demo=0
```

## Submit the revision

```scrut
$ los capability note.revise --payload-file "$TMPDIR/durable-revise.json"
{
  "schema_version": 2,
  "request_id": "request-durable-revise-demo",
  "idempotency_key": "durable-revise-demo",
  "capability": "note.revise",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:4d77a9b9c34c2b5a41d4f8e3b6002b3d527b38a9b444293c786926723839e9ef",
  "result": {
    "ok": true,
    "note_id": "note-demo",
    "path": "knowledge/notes/mathematics/note-demo.md",
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "note-demo": 1
    },
    "snapshot_after": "sha256:4d77a9b9c34c2b5a41d4f8e3b6002b3d527b38a9b444293c786926723839e9ef",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability note.revise
```

## The revision landed, identity stable

```scrut
$ $H/los-assert-file knowledge/notes/mathematics/note-demo.md --sha256 579edc9db14e8618bb50944c678ec7702756fc0ef5f0b06036c662001bebc3eb
```

## The receipt owns the revised bytes

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,os,yaml; ds=sorted(glob.glob("operations/transactions/transaction-*.yaml")); xs=[os.path.basename(x) for x in ds]; assert xs==["transaction-20200102-000000-001.yaml", "transaction-20261001-090000-001.yaml"], xs; d=yaml.safe_load(open(ds[-1])); assert d["capability"]=="note.revise", d["capability"]; w={x["path"]: x for x in d.get("writes") or []}; e=w["knowledge/notes/mathematics/note-demo.md"]; assert e["sha256_after"]=="579edc9db14e8618bb50944c678ec7702756fc0ef5f0b06036c662001bebc3eb", e; assert e["created"] is False, e; print("owns", d["id"])'
owns transaction-20261001-090000-001
```

## Stage the new note body

```scrut
$ cat > "$TMPDIR/durable-body.md" <<'EOF'
> # Triangulation memo
>
> Three routes agree on the setup, but the middle step is still uncertain.
> EOF
```

## Seal the creation with derived guards

```scrut {output_stream: stderr}
$ BODY_SHA=$(sha256sum "$TMPDIR/durable-body.md" | cut -d' ' -f1) && $H/los-seal --capability note.create --payload "{\"note\": {\"id\": \"note-triangulation-memo\", \"title\": \"Triangulation memo\", \"path\": \"knowledge/notes/mathematics/note-triangulation-memo.md\", \"concepts\": [\"concept-expected-value\"], \"sources\": [\"source-demo-book\"], \"contexts\": [\"workspace-demo\"]}, \"body_file\": \"$TMPDIR/durable-body.md\", \"body_file_sha256\": \"sha256:$BODY_SHA\"}" --key durable-create-memo --request-id request-durable-create-memo --guards auto --out "$TMPDIR/durable-create.json"
seal_envelope: guards auto: note-triangulation-memo=0
```

## Submit the creation

```scrut
$ los capability note.create --payload-file "$TMPDIR/durable-create.json"
{
  "schema_version": 2,
  "request_id": "request-durable-create-memo",
  "idempotency_key": "durable-create-memo",
  "capability": "note.create",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-002",
  "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
  "snapshot_after": "sha256:b1abf682b855c75057c95affed3152985427055f067707fd5c6817ac97b31abf",
  "result": {
    "ok": true,
    "note_id": "note-triangulation-memo",
    "note_path": "knowledge/notes/mathematics/note-triangulation-memo.md",
    "deprecated": [],
    "transaction_id": "transaction-20261001-090000-002",
    "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
    "artifact_revisions": {
      "note-triangulation-memo": 1
    },
    "snapshot_after": "sha256:b1abf682b855c75057c95affed3152985427055f067707fd5c6817ac97b31abf",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability note.create
```

## The note landed under its id

```scrut
$ $H/los-assert-file knowledge/notes/mathematics/note-triangulation-memo.md --sha256 9d5801aa6fa163553ccbccac9e4e8e304ca3e499313fd7e5e34ee30ddd935c26
```

## The receipt owns the created note

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,os,yaml; ds=sorted(glob.glob("operations/transactions/transaction-*.yaml")); xs=[os.path.basename(x) for x in ds]; assert xs==["transaction-20200102-000000-001.yaml", "transaction-20261001-090000-001.yaml", "transaction-20261001-090000-002.yaml"], xs; d=yaml.safe_load(open(ds[-1])); assert d["capability"]=="note.create", d["capability"]; w={x["path"]: x for x in d.get("writes") or []}; e=w["knowledge/notes/mathematics/note-triangulation-memo.md"]; assert e["sha256_after"]=="9d5801aa6fa163553ccbccac9e4e8e304ca3e499313fd7e5e34ee30ddd935c26", e; assert e["created"] is True, e; print("owns", d["id"])'
owns transaction-20261001-090000-002
```

## Capture the pre-refusal state

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.store.fingerprint import canonical_fingerprint; from pathlib import Path; st={"fp": canonical_fingerprint(Path(".")), "rc": sorted(glob.glob("operations/transactions/transaction-*.yaml"))}; json.dump(st, open(os.environ["TMPDIR"]+"/fp-refuse-reference.json", "w")); print("captured", len(st["rc"]))'
captured 3
```

## Reference keeps its dedicated capability

```scrut {output_stream: stderr}
$ BODY_SHA=$(sha256sum "$TMPDIR/durable-body.md" | cut -d' ' -f1) && $H/los-seal --capability note.create --payload "{\"note\": {\"id\": \"note-triangulation-ref\", \"title\": \"Triangulation ref\", \"path\": \"knowledge/notes/mathematics/note-triangulation-ref.md\", \"role\": \"reference\"}, \"body_file\": \"$TMPDIR/durable-body.md\", \"body_file_sha256\": \"sha256:$BODY_SHA\"}" --key durable-create-ref --request-id request-durable-create-ref --guards auto --out "$TMPDIR/durable-ref.json"
seal_envelope: role 'reference' keeps its dedicated capability; use note.analysis.save; fix the payload and seal again
[2]
```

## The refusal added no receipt and moved no canonical byte

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.store.fingerprint import canonical_fingerprint; from pathlib import Path; st=json.load(open(os.environ["TMPDIR"]+"/fp-refuse-reference.json")); fp=canonical_fingerprint(Path(".")); rc=sorted(glob.glob("operations/transactions/transaction-*.yaml")); assert fp==st["fp"], (fp, st["fp"]); assert rc==st["rc"], (rc, st["rc"]); print("unchanged")'
unchanged
```

## A learner question goes through its own save

```scrut {output_stream: stderr}
$ $H/los-seal --capability atlas.question.save --payload '{"question": {"id": "note-variance-order", "title": "Does variance need expectation first?", "text": "The registry says variance builds on expectation. What breaks if the order flips?", "target": {"concepts": ["concept-variance"]}}}' --key durable-question --request-id request-durable-question --guards auto --out "$TMPDIR/durable-question.json"
seal_envelope: guards auto: note-variance-order=0
```

## Submit the question

```scrut
$ los capability atlas.question.save --payload-file "$TMPDIR/durable-question.json"
{
  "schema_version": 2,
  "request_id": "request-durable-question",
  "idempotency_key": "durable-question",
  "capability": "atlas.question.save",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-003",
  "receipt_path": "operations/transactions/transaction-20261001-090000-003.yaml",
  "snapshot_after": "sha256:c7b25f6b7375f1b61ce8309ba43ed870e0cca7dcbc9a0e85df9f932d38b5e91f",
  "result": {
    "ok": true,
    "note_id": "note-variance-order",
    "note_path": "knowledge/notes/questions/note-variance-order.md",
    "transaction_id": "transaction-20261001-090000-003",
    "receipt_path": "operations/transactions/transaction-20261001-090000-003.yaml",
    "artifact_revisions": {
      "note-variance-order": 1
    },
    "snapshot_after": "sha256:c7b25f6b7375f1b61ce8309ba43ed870e0cca7dcbc9a0e85df9f932d38b5e91f",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability atlas.question.save
```

## The question landed as its own note

```scrut
$ $H/los-assert-file knowledge/notes/questions/note-variance-order.md --sha256 859bb57f24d7ed25d9b048fa150309c7edfb1f02e93e902f0b83ec8708734064
```

## The receipt owns the saved question

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,os,yaml; ds=sorted(glob.glob("operations/transactions/transaction-*.yaml")); xs=[os.path.basename(x) for x in ds]; assert xs==["transaction-20200102-000000-001.yaml", "transaction-20261001-090000-001.yaml", "transaction-20261001-090000-002.yaml", "transaction-20261001-090000-003.yaml"], xs; d=yaml.safe_load(open(ds[-1])); assert d["capability"]=="atlas.question.save", d["capability"]; w={x["path"]: x for x in d.get("writes") or []}; e=w["knowledge/notes/questions/note-variance-order.md"]; assert e["sha256_after"]=="859bb57f24d7ed25d9b048fa150309c7edfb1f02e93e902f0b83ec8708734064", e; assert e["created"] is True, e; print("owns", d["id"])'
owns transaction-20261001-090000-003
```

## Stage one source analysis body

```scrut
$ cat > "$TMPDIR/durable-analysis-body.md" <<'EOF'
> # Deck analysis
>
> The deck introduces the setup on pages one to three.
> EOF
```

## Seal the single analysis with derived guards

```scrut {output_stream: stderr}
$ ABODY_SHA=$(sha256sum "$TMPDIR/durable-analysis-body.md" | cut -d' ' -f1) && ABODY_BYTES=$(wc -c < "$TMPDIR/durable-analysis-body.md" | tr -d ' ') && $H/los-seal --capability note.analysis.save --payload "{\"analysis\": {\"id\": \"note-deck-analysis\", \"title\": \"Deck analysis\", \"path\": \"knowledge/notes/mathematics/note-deck-analysis.md\", \"binding\": {\"resolution\": \"unresolved\", \"material\": \"demo/deck.pdf\", \"recorded_source_digest\": \"abababababababababababababababababababababababababababababababab\", \"inspected_range\": {\"start\": 1, \"end\": 3}, \"frozen_input_sha256\": \"$ABODY_SHA\", \"frozen_input_bytes\": $ABODY_BYTES}}, \"body_file\": \"$TMPDIR/durable-analysis-body.md\", \"body_file_sha256\": \"sha256:$ABODY_SHA\"}" --key durable-analysis --request-id request-durable-analysis --guards auto --out "$TMPDIR/durable-analysis.json"
seal_envelope: guards auto: note-deck-analysis=0
```

## Submit the analysis

```scrut
$ los capability note.analysis.save --payload-file "$TMPDIR/durable-analysis.json"
{
  "schema_version": 2,
  "request_id": "request-durable-analysis",
  "idempotency_key": "durable-analysis",
  "capability": "note.analysis.save",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-004",
  "receipt_path": "operations/transactions/transaction-20261001-090000-004.yaml",
  "snapshot_after": "sha256:3ab37c75a64674ddea50fbafc50898bc27fda0b1a036375fa6b4b5094ec3f65e",
  "result": {
    "ok": true,
    "replayed": false,
    "note_id": "note-deck-analysis",
    "note_path": "knowledge/notes/mathematics/note-deck-analysis.md",
    "transaction_id": "transaction-20261001-090000-004",
    "receipt_path": "operations/transactions/transaction-20261001-090000-004.yaml",
    "artifact_revisions": {
      "note-deck-analysis": 1
    },
    "snapshot_after": "sha256:3ab37c75a64674ddea50fbafc50898bc27fda0b1a036375fa6b4b5094ec3f65e"
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability note.analysis.save
```

## The analysis landed as a reference note

```scrut
$ $H/los-assert-file knowledge/notes/mathematics/note-deck-analysis.md --sha256 37714a7eb7c58ed9b7509ed71f276e5ac3f81e446691435f5d9d59ca5610f1e4
```

## The receipt owns the saved analysis

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,os,yaml; ds=sorted(glob.glob("operations/transactions/transaction-*.yaml")); xs=[os.path.basename(x) for x in ds]; assert xs==["transaction-20200102-000000-001.yaml", "transaction-20261001-090000-001.yaml", "transaction-20261001-090000-002.yaml", "transaction-20261001-090000-003.yaml", "transaction-20261001-090000-004.yaml"], xs; d=yaml.safe_load(open(ds[-1])); assert d["capability"]=="note.analysis.save", d["capability"]; w={x["path"]: x for x in d.get("writes") or []}; e=w["knowledge/notes/mathematics/note-deck-analysis.md"]; assert e["sha256_after"]=="37714a7eb7c58ed9b7509ed71f276e5ac3f81e446691435f5d9d59ca5610f1e4", e; assert e["created"] is True, e; print("owns", d["id"])'
owns transaction-20261001-090000-004
```

## Validate, then rebuild generated outputs

```scrut
$ los validate | tail -n 1
0 error(s), 9 warning(s) — OK
```

```scrut
$ los generate
published generated/manifest.json (atomic contract snapshot)
```
