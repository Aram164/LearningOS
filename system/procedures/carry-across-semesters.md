---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Carry across semesters (WORKFLOWS §20)

Executable transcript of the successor choice: the old arc closes
with its own durable note and archives, the successor workspace
opens, its opening note supersedes the old arc's closing note, the
shared canon note stays linked — never copied — in both arcs, and
the succession lands as a coordination dependency. Continue and
split are the uncovered conditional branches. `tests/test_procedures.py`
runs it with Scrut; `<REPO>` comes from the `LOS_REPO` environment
variable the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Record the shared note's bytes before anything moves

```scrut
$ $H/los-assert-file knowledge/notes/mathematics/note-demo.md --sha256 5bfb18040cdeba3b47d06700b13c0edf6ebcac90d085e6fc78cfe8565261d276
```

## Stage the old arc's closing body

```scrut
$ cat > "$TMPDIR/carry-closing-body.md" <<'EOF'
> # Second arc closing
>
> The second arc settled the setup question.
> EOF
```

## Seal the closing note with derived guards

```scrut {output_stream: stderr}
$ BODY_SHA=$(sha256sum "$TMPDIR/carry-closing-body.md" | cut -d' ' -f1) && $H/los-seal --capability note.create --payload "{\"note\": {\"id\": \"note-second-closing\", \"title\": \"Second arc closing\", \"path\": \"knowledge/notes/mathematics/note-second-closing.md\", \"concepts\": [\"concept-expected-value\"], \"contexts\": [\"workspace-second\"]}, \"body_file\": \"$TMPDIR/carry-closing-body.md\", \"body_file_sha256\": \"sha256:$BODY_SHA\"}" --key carry-closing --request-id request-carry-closing --guards auto --out "$TMPDIR/carry-closing.json"
seal_envelope: guards auto: note-second-closing=0
```

## Submit the closing note

```scrut
$ los capability note.create --payload-file "$TMPDIR/carry-closing.json"
{
  "schema_version": 2,
  "request_id": "request-carry-closing",
  "idempotency_key": "carry-closing",
  "capability": "note.create",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:624d80ac1e6f6577f9953c4f600556f98abf749757b5c4a87dd2e915aa972465",
  "result": {
    "ok": true,
    "note_id": "note-second-closing",
    "note_path": "knowledge/notes/mathematics/note-second-closing.md",
    "deprecated": [],
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "note-second-closing": 1
    },
    "snapshot_after": "sha256:624d80ac1e6f6577f9953c4f600556f98abf749757b5c4a87dd2e915aa972465",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability note.create
```

## The closing note landed

```scrut
$ $H/los-assert-file knowledge/notes/mathematics/note-second-closing.md --sha256 ff0699689fc01dca9bbd8c9c6db2591963eecc64b0e84e65994ef56720755192
```

## Link the closing note from the old arc

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import yaml; p = "work/active/workspace-second/CONTEXT.md"; raw = open(p).read(); head, sep, body = raw.partition("---\n\n"); meta = yaml.safe_load(head); meta["notes"].append("note-second-closing"); open(p, "w").write("---\n" + yaml.safe_dump(meta, sort_keys=False) + "---\n\n" + body)'
```

## No dependency names the old arc

```scrut
$ test -z "$(grep "workspace-second" work/COORDINATION.md)" && echo no-deps
no-deps
```

## Complete the old arc

```scrut
$ sed -i '' 's/^status: active$/status: complete/' work/active/workspace-second/CONTEXT.md && grep "^status:" work/active/workspace-second/CONTEXT.md
status: complete
```

## Validate, then rebuild

```scrut
$ los validate | tail -n 1
0 error(s), 10 warning(s) — OK
```

```scrut
$ los generate
published generated/manifest.json (atomic contract snapshot)
```

## Archive the old arc

```scrut
$ mkdir -p archive/workspaces/2026 && mv work/active/workspace-second archive/workspaces/2026/workspace-second
```

```scrut
$ $H/los-assert-file archive/workspaces/2026/workspace-second/CONTEXT.md --sha256 32f0594099dd092c7cdbb0bfc2d5fd225f2a141e9680c58afba5c35ad643f2f5
```

```scrut
$ $H/los-assert-file work/active/workspace-second --absent
```

## Open the successor arc

```scrut
$ mkdir -p work/active/workspace-carry-forward/scratch work/active/workspace-carry-forward/inputs work/active/workspace-carry-forward/outputs
```

```scrut
$ cat > work/active/workspace-carry-forward/CONTEXT.md <<'EOF'
> ---
> id: workspace-carry-forward
> type: workspace
> title: Carry forward
> created: '2026-10-01'
> status: active
> standing: false
> concepts: []
> notes:
> - note-demo
> sources: []
> ---
>
> ## Objective
>
> Continue the second arc past the term line.
>
> ## Current Scope
>
> The opening question only.
>
> ## Open Questions
>
> None yet.
>
> ## Next Action
>
> Draft the opening note.
> EOF
```

```scrut
$ $H/los-assert-file work/active/workspace-carry-forward/CONTEXT.md --sha256 f2649aba8c681aa69a485fe46ca9c429b429d172cc353beba6568d20f5f6a9ff
```

## Stage the opening body

```scrut
$ cat > "$TMPDIR/carry-opening-body.md" <<'EOF'
> # Carry opening
>
> The successor arc reopens the setup question past the term line.
> EOF
```

## Seal the opening note with its supersedes lineage

```scrut {output_stream: stderr}
$ BODY_SHA=$(sha256sum "$TMPDIR/carry-opening-body.md" | cut -d' ' -f1) && $H/los-seal --capability note.create --payload "{\"note\": {\"id\": \"note-carry-opening\", \"title\": \"Carry opening\", \"path\": \"knowledge/notes/mathematics/note-carry-opening.md\", \"concepts\": [\"concept-expected-value\"], \"contexts\": [\"workspace-carry-forward\"], \"supersedes\": [\"note-second-closing\"]}, \"body_file\": \"$TMPDIR/carry-opening-body.md\", \"body_file_sha256\": \"sha256:$BODY_SHA\"}" --key carry-opening --request-id request-carry-opening --guards auto --out "$TMPDIR/carry-opening.json"
seal_envelope: guards auto: note-carry-opening=0, note-second-closing=1
```

## Submit the opening note

```scrut
$ los capability note.create --payload-file "$TMPDIR/carry-opening.json"
{
  "schema_version": 2,
  "request_id": "request-carry-opening",
  "idempotency_key": "carry-opening",
  "capability": "note.create",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-002",
  "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
  "snapshot_after": "sha256:12e1bf0333a494b1ba5ede6709ebcb9ad412529ce1e780475cd05ebcbaf1e08d",
  "result": {
    "ok": true,
    "note_id": "note-carry-opening",
    "note_path": "knowledge/notes/mathematics/note-carry-opening.md",
    "deprecated": [
      "knowledge/notes/mathematics/note-second-closing.md"
    ],
    "transaction_id": "transaction-20261001-090000-002",
    "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
    "artifact_revisions": {
      "note-carry-opening": 1,
      "note-second-closing": 2
    },
    "snapshot_after": "sha256:12e1bf0333a494b1ba5ede6709ebcb9ad412529ce1e780475cd05ebcbaf1e08d",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability note.create
```

## The opening note landed

```scrut
$ $H/los-assert-file knowledge/notes/mathematics/note-carry-opening.md --sha256 98c70cd732339880b147cf669aaf97323f4b9224752d6ced19fdab62f7604559
```

## The shared note never moved

```scrut
$ $H/los-assert-file knowledge/notes/mathematics/note-demo.md --sha256 5bfb18040cdeba3b47d06700b13c0edf6ebcac90d085e6fc78cfe8565261d276
```

## Record the succession as a dependency

```scrut
$ eval "$(los inspect coordination | $H/los-bind CARRY_SHA '$.content_sha256')" && echo "$CARRY_SHA"
sha256:667bbd75392b1acdc610aa249aa5f2fe3d7659603901f415b36eda30fe2b4655
```

```scrut {output_stream: stderr}
$ $H/los-seal --capability coordination.section.revise --payload "{\"section\": \"Dependencies\", \"text\": \"- workspace-carry-forward continues the term arc.\", \"expected_content_sha256\": \"$CARRY_SHA\"}" --key carry-dep --request-id request-carry-dep --guards auto --out "$TMPDIR/carry-dep.json"
seal_envelope: guards auto: coordination=0
```

```scrut
$ los capability coordination.section.revise --payload-file "$TMPDIR/carry-dep.json"
{
  "schema_version": 2,
  "request_id": "request-carry-dep",
  "idempotency_key": "carry-dep",
  "capability": "coordination.section.revise",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-003",
  "receipt_path": "operations/transactions/transaction-20261001-090000-003.yaml",
  "snapshot_after": "sha256:ffd2783491ecb5adb648ac61d16d7cb66fb99b25ec275e37aeb3e37e16a4a046",
  "result": {
    "ok": true,
    "section": "Dependencies",
    "transaction_id": "transaction-20261001-090000-003",
    "receipt_path": "operations/transactions/transaction-20261001-090000-003.yaml",
    "artifact_revisions": {
      "coordination": 1
    },
    "snapshot_after": "sha256:ffd2783491ecb5adb648ac61d16d7cb66fb99b25ec275e37aeb3e37e16a4a046",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability coordination.section.revise
```

## The succession is recorded

```scrut
$ $H/los-assert-file work/COORDINATION.md --sha256 99f6de3fa22ba17c5471b0d1cafd7dce4b2513c88774037ef81af92e359e7202
```

## Validate the carried state

```scrut
$ los validate | tail -n 1
0 error(s), 9 warning(s) — OK
```
