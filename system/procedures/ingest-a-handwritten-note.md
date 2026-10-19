---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Ingest a handwritten note (WORKFLOWS §17)

Executable transcript of ingesting two photographed derivation pages:
the user drops the scans, the operator mints the owning note, moves the
originals to their canonical attachment paths, transcribes faithfully
through the note gateway, sets the transcription metadata and attachment
list through a revision, records the derivation evidence, and rebuilds.
The scans and the transcription below are synthetic fixture data
standing in for the user's own pages and reasoning; every command and
outcome runs for real. `tests/test_procedures.py` runs it with Scrut;
`<REPO>` comes from the `LOS_REPO` environment variable the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## The user drops two photographed pages

```scrut
$ mkdir -p work/inbox/handwritten-probe && printf 'synthetic-scan-bytes-page-01' > work/inbox/handwritten-probe/page-01.jpg && printf 'synthetic-scan-bytes-page-02' > work/inbox/handwritten-probe/page-02.jpg && ls work/inbox/handwritten-probe/
page-01.jpg
page-02.jpg
```

## No note yet owns this derivation

1. determine the owning note: extend an existing note or mint a new ID;
2. move the originals to `knowledge/attachments/<note-id>/page-01.jpg`, `page-02.jpg`, … — originals are canonical and Git-tracked, never deleted without explicit approval; a scan too large or private to publish is instead pinned in `system/contracts/local-attachments.yaml` and gitignored at the same path (local-only, still backed up);
3. transcribe faithfully into the note body — preserve the user's reasoning, uncertainty, wrong turns, and notation; never substitute a generic textbook explanation;
4. set `transcription: ai-assisted`, `authorship: user`, `semantic_review: unreviewed`;
5. list the attachment paths in the note's `attachments` frontmatter;
6. link concepts and sources; add workspace context;
7. rebuild generated outputs.

```scrut
$ los search probe-derivation --type note
[]
```

## Mint the owning note id and move the originals to it

```scrut
$ mkdir -p knowledge/attachments/note-probe-derivation && mv work/inbox/handwritten-probe/page-01.jpg work/inbox/handwritten-probe/page-02.jpg knowledge/attachments/note-probe-derivation/ && ls knowledge/attachments/note-probe-derivation/
page-01.jpg
page-02.jpg
```

## The originals are preserved byte-identical

```scrut
$ $H/los-assert-file knowledge/attachments/note-probe-derivation/page-01.jpg --sha256 5a8251231ef72e2ad982aff446b7ce7c2b44618118e6c34a68f7015a9cebe9e0
```

```scrut
$ $H/los-assert-file knowledge/attachments/note-probe-derivation/page-02.jpg --sha256 ebe48a5a4c7d9e2a5c0dbf4126c986372de14f8d05d2287f808eaf107221ede7
```

## Transcribe faithfully into the staged body

```scrut
$ cat > "$TMPDIR/transcription.md" <<'EOF'
> # Sample mean as an estimator — own derivation
>
> The average of the sample centers on the population mean; the spread
> shrinks with the root of the sample size. Unsure about the exact
> constant in front — revisit with the chapter.
> EOF
```

## Seal the creation with links to concepts, source and workspace

```scrut {output_stream: stderr}
$ BODY_SHA=$(sha256sum "$TMPDIR/transcription.md" | cut -d' ' -f1) && $H/los-seal --capability note.create --payload "{\"note\": {\"id\": \"note-probe-derivation\", \"title\": \"Sample mean as an estimator — own derivation\", \"path\": \"knowledge/notes/mathematics/note-probe-derivation.md\", \"role\": \"derivation\", \"concepts\": [\"concept-expected-value\"], \"sources\": [\"source-demo-book\"], \"contexts\": [\"workspace-demo\"]}, \"body_file\": \"$TMPDIR/transcription.md\", \"body_file_sha256\": \"sha256:$BODY_SHA\"}" --key s17-create --request-id request-s17-create --guards auto --out "$TMPDIR/s17-create.json"
seal_envelope: guards auto: note-probe-derivation=0
```

## Submit the creation

```scrut
$ los capability note.create --payload-file "$TMPDIR/s17-create.json"
{
  "schema_version": 2,
  "request_id": "request-s17-create",
  "idempotency_key": "s17-create",
  "capability": "note.create",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:b72c73154f5c13824669fe746334050ebf04efc5c7f7825a2577418fabeba6b1",
  "result": {
    "ok": true,
    "note_id": "note-probe-derivation",
    "note_path": "knowledge/notes/mathematics/note-probe-derivation.md",
    "deprecated": [],
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "note-probe-derivation": 1
    },
    "snapshot_after": "sha256:b72c73154f5c13824669fe746334050ebf04efc5c7f7825a2577418fabeba6b1",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability note.create
```

## Set the transcription metadata and attachment list

```scrut
$ cat > "$TMPDIR/transcription-rev.md" <<'EOF'
> ---
> id: note-probe-derivation
> type: note
> title: Sample mean as an estimator — own derivation
> created: 2026-10-12
> role: derivation
> authorship: user
> transcription: ai-assisted
> semantic_review: unreviewed
> concepts: [concept-expected-value]
> sources: [source-demo-book]
> attachments:
> - knowledge/attachments/note-probe-derivation/page-01.jpg
> - knowledge/attachments/note-probe-derivation/page-02.jpg
> contexts: [workspace-demo]
> ---
>
> # Sample mean as an estimator — own derivation
>
> The average of the sample centers on the population mean; the spread
> shrinks with the root of the sample size. Unsure about the exact
> constant in front — revisit with the chapter.
> EOF
```

```scrut {output_stream: stderr}
$ REV_SHA=$(sha256sum "$TMPDIR/transcription-rev.md" | cut -d' ' -f1) && $H/los-seal --capability note.revise --payload "{\"note_id\": \"note-probe-derivation\", \"file\": \"$TMPDIR/transcription-rev.md\", \"file_sha256\": \"sha256:$REV_SHA\"}" --key s17-rev --request-id request-s17-rev --guards auto --out "$TMPDIR/s17-rev.json"
seal_envelope: guards auto: note-probe-derivation=1
```

```scrut
$ los capability note.revise --payload-file "$TMPDIR/s17-rev.json"
{
  "schema_version": 2,
  "request_id": "request-s17-rev",
  "idempotency_key": "s17-rev",
  "capability": "note.revise",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-002",
  "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
  "snapshot_after": "sha256:856c7645f4d5ff7dff80cbe088da7128402ed669654c2ab1de3b2027a05120ae",
  "result": {
    "ok": true,
    "note_id": "note-probe-derivation",
    "path": "knowledge/notes/mathematics/note-probe-derivation.md",
    "transaction_id": "transaction-20261001-090000-002",
    "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
    "artifact_revisions": {
      "note-probe-derivation": 2
    },
    "snapshot_after": "sha256:856c7645f4d5ff7dff80cbe088da7128402ed669654c2ab1de3b2027a05120ae",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability note.revise
```

## Record the derivation evidence

```scrut {output_stream: stderr}
$ $H/los-seal --capability note.evidence.add --payload '{"note_id": "note-probe-derivation", "evidence_type": "derivation", "ref": "note://note-probe-derivation"}' --key s17-ev --request-id request-s17-ev --guards auto --out "$TMPDIR/s17-ev.json"
seal_envelope: guards auto: note-probe-derivation=2
```

```scrut
$ los capability note.evidence.add --payload-file "$TMPDIR/s17-ev.json"
{
  "schema_version": 2,
  "request_id": "request-s17-ev",
  "idempotency_key": "s17-ev",
  "capability": "note.evidence.add",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-003",
  "receipt_path": "operations/transactions/transaction-20261001-090000-003.yaml",
  "snapshot_after": "sha256:7a84c80245f2ffdd60521a6ae02edcb9180849e1739fa3523492da82dcb41565",
  "result": {
    "ok": true,
    "note_id": "note-probe-derivation",
    "path": "knowledge/notes/mathematics/note-probe-derivation.md",
    "evidence": {
      "type": "derivation",
      "ref": "note://note-probe-derivation"
    },
    "evidence_count": 1,
    "scheme": "note",
    "transaction_id": "transaction-20261001-090000-003",
    "receipt_path": "operations/transactions/transaction-20261001-090000-003.yaml",
    "artifact_revisions": {
      "note-probe-derivation": 3
    },
    "snapshot_after": "sha256:7a84c80245f2ffdd60521a6ae02edcb9180849e1739fa3523492da82dcb41565",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability note.evidence.add
```

## The note validates clean

```scrut
$ (set -o pipefail; los validate | tail -n 1)
0 error(s), 9 warning(s) — OK
```

## Rebuild the generated outputs

```scrut
$ los generate
published generated/manifest.json (atomic contract snapshot)
```

## The note retrieves through its concept with its metadata

```scrut
$ los inspect note-probe-derivation | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["id"], d["authorship"], d["transcription"], d["semantic_review"], len(d["attachments"]))'
note-probe-derivation user ai-assisted unreviewed 2
```

```scrut
$ los search "estimator derivation" --type note | $LOS_REPO/.venv/bin/python -c 'import json,sys; print(sorted(r["id"] for r in json.load(sys.stdin)))'
['note-probe-derivation']
```
