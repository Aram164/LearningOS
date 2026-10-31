---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Build a write envelope (WORKFLOWS §25c)

Executable transcript of the GatewayEnvelopeV2 construction recipe, using
the section's own worked capture (`capture.create`) end to end: read the
payload schema, bind the snapshot, watch the bare command refuse, seal
with derived guards, verify the intent hash, submit, replay the saved
envelope, and refuse a stale one. `tests/test_procedures.py` runs it with
Scrut; `<REPO>` comes from the `LOS_REPO` environment variable the test
sets.

The steps below are the wire format and its guarantees. To write, you do
not perform them by hand: `.venv/bin/python tools/seal_envelope.py
--capability NAME --payload JSON --key KEY --submit` reads the snapshot,
derives the guards, seals, submits and prints the gateway's result, plus one
`validation:` line from the commit's own validation. A retry with the same
key and payload replays the committed receipt. The executable example is
the `log:` path in [capture routing](capture-routing.md).

A payload that names a file in a byte-bound field (`file`, `body_file`,
`attachment`, …) needs no digest from you: the seal sets the field's
`…_sha256` to the file's current bytes and says so on stderr. A write that
needs review first is two calls. `--guards auto --check-out REC` writes the
check record: every validation error, any new warning signature, and the
planned writes. Use a fresh, attempt-specific `REC` outside the
repository, or under the checkout's gitignored `.venv/` scratch when the
harness confines writes to the checkout. Print the record in the same invocation as the check (append
`&& cat REC` to the check command, so a failed check keeps its failure
status and no stale record is shown) and inspect the proposed change, exact
target, and guards in that result. If the printed record is truncated or
incomplete, do not submit. After the review, in a separate invocation,
`--guards-from REC --submit` applies exactly what was reviewed, and refuses
if the file or the tree changed since. Never chain check and submit in one
invocation, and never treat a successful check exit as approval.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Step 1: the payload schema is the capability contract

1. **Payload schema.** `.venv/bin/python tools/los.py capabilities <name> --json`
   is the payload contract for capability `<name>`.
2. **Snapshot.** `.venv/bin/python tools/los.py bootstrap --compact` prints
   `snapshot_id` (`sha256:…`); that exact string is `expected_snapshot`.
   Any canonical change between reading it and submitting refuses the
   write as `STALE_SNAPSHOT` (exit 3) — re-read and re-seal.
3. **Revision guards.** `expected_revisions` maps every artifact the
   transaction touches to its current revision. The default path is the
   sealing helper's `--guards auto` (below): it derives the exact set
   with a gateway dry run that stops before any write, and reads the
   revisions under the same lock as the snapshot, so the sealed envelope
   commits on the first submission. The manual path — read
   `operations/transactions/revisions.yaml` (an artifact absent from the
   ledger has revision 0 — the legitimate no-recorded-revision baseline,
   backstopped by the snapshot guard; the ledger file itself does not
   exist until the first write commits, before that guard every touched
   artifact at 0), guess the set from the common shapes, and fix it from
   the refusal's `artifacts=[...]` — stays for envelopes built by hand.
   Two capabilities name their write
   target only inside the handler, so the caller cannot guard a path and
   guards the request instead: `capture.create` takes
   `capture-request:<idempotency-key>`, `garden.seed.create` takes
   `garden-request:<idempotency-key>`, both at revision 0 for a fresh
   key (`--guards auto` derives these from the sealing key). Common
   shapes: `stage.note.write` guards its unit;
   `stage.progress.update` and `stage.attachment.add` guard the unit and
   that unit's study map. A refusal names the exact expected set
   (`artifacts=[...]`) — copy it, re-read revisions, and re-seal. That
   refusal committed nothing and the corrected envelope is a new intent,
   so seal it under a fresh idempotency key (a request-scoped guard
   follows its key); reusing the refused key leaves the refusal flagged
   for reconciliation in `los operations`.
4. **Identities.** `request_id` and `idempotency_key` are caller-chosen
   (1–128 chars, `^[A-Za-z0-9][A-Za-z0-9._:-]*$`). An exact retry of the
   *same* approved intent resubmits the saved sealed envelope unchanged —
   same key **and** same `request_id` — and replays the receipt instead of
   writing twice. Never re-seal a retry: the ledger binds each key to the
   request that committed it, so a re-sealed envelope under a used key is
   refused, as `IDEMPOTENCY_CONFLICT` when its intent differs (a live
   snapshot read after the commit already differs) or fail-closed naming
   the recorded request id when only the id differs. Mint a fresh
   `request_id` together with a fresh key for every new attempt (step 3's
   corrected envelope is one): reused ids merge their explanations in
   `los operations`.

   Name the session every write in one agent session shares **before the
   first write**: seal `session_id` in each envelope (`seal_envelope.py
   --session-id <id>`) when the harness runs every command in a fresh
   shell where an export never persists, or export `LOS_SESSION_ID=<id>`
   once when the shell persists. Resolution is explicit `--session-id`
   flag, then the sealed envelope, then `LOS_SESSION_ID`, then the
   channel default — `bootstrap --brief` prints the identity in effect
   as `session_identity`. `session-end` closes exactly that identity's
   ledger (§22).
5. **Approval.** `channel` is `operator` and `approval.kind` is
   `operator-approval` on the operator path; the review preparers
   (`module-plan-import --check`, `unit-plan-revise --check`,
   `note-analysis-prepare`) seal the same approval kind with the
   caller's channel — the active gateway request's channel, else
   `operator` — so the reviewed write joins the caller's session ledger
   (`direct-user-gesture` is admitted only for a closed UI-originated
   allowlist).
   `approval.subject_sha256` must equal `intent_sha256(envelope)`,
   computed as below **after** every other field is final — any later
   edit invalidates it and the write is refused as `UNCONFIRMED`.
   The approval subject is the operator's assertion that the learner
   approved this exact intent, guarded by the snapshot/revision checks —
   not cryptographic proof that a human was present.
6. **Submit.** `.venv/bin/python tools/los.py capability <name> --payload-file
   envelope.json`. Exit 0 commits (or replays); exit 2 refuses; exit 3
   is an optimistic-concurrency conflict, and the status alone does not say
   which: the V2 `code` field names it (`STALE_SNAPSHOT` when the snapshot
   moved, `REVISION_CONFLICT` when a revision guard or the reviewed package
   hash mismatches). Re-read the named state and re-seal.

```scrut
$ los capabilities capture.create --json | $H/los-bind PAYLOAD_SCHEMA '$.payload_schema'
export PAYLOAD_SCHEMA='{"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "capabilities/capture.create.schema.json", "title": "payload for capability capture.create", "description": "Derived from the los CLI parser for this capability'"'"'s named command. Do not hand-edit; regenerate with tools/generate_capability_schemas.py.", "type": "object", "additionalProperties": false, "required": [], "properties": {"file": {"type": "string", "description": "copy this file into the inbox"}, "file_sha256": {"type": "string", "pattern": "^sha256:[a-f0-9]{64}$", "description": "SHA-256 of the exact file bytes approved for this capture"}, "text": {"type": "string", "description": "capture this text (else stdin)"}, "title": {"type": "string", "description": "optional title for text captures"}}, "oneOf": [{"required": ["file"], "not": {"required": ["text"]}}, {"required": ["text"], "not": {"required": ["file"]}}], "dependentRequired": {"file": ["file_sha256"], "file_sha256": ["file"]}}'
```

## Step 2: the snapshot comes from bootstrap

```scrut {interpolated: true}
$ eval "$(los bootstrap --compact | $H/los-bind SNAP '$.snapshot_id')" && echo "$SNAP"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
$LOS_FIXTURE_SNAPSHOT_1
```

## The bare mutating command refuses by design

```scrut {output_stream: stderr}
$ los capture --text "hello"
los: INVALID_REQUEST: canonical writes must use GatewayEnvelopeV2; direct CLI application is disabled — apply it with `los capability capture.create --payload-file ENVELOPE.json` (payload schema: `los capabilities capture.create --json`; envelope: WORKFLOWS §25c)
[2]
```

## Steps 2–5: seal with the snapshot and derived guards

```scrut {output_stream: stderr}
$ $H/los-seal --capability capture.create --payload '{"text": "Half-formed idea about the derivation."}' --key envelope-capture-a --request-id request-envelope-capture-a --snapshot "$SNAP" --guards auto --out "$TMPDIR/capture-a.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
seal_envelope: guards auto: capture-request:envelope-capture-a=0
```

## The sealed envelope's sha256, before submission

```scrut {interpolated: true}
$ $H/los-assert-file "$TMPDIR/capture-a.json" --sha256 "$LOS_FIXTURE_FILE_1"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
```

## The envelope carries the bound snapshot

```scrut {interpolated: true}
$ cat "$TMPDIR/capture-a.json" | $H/los-bind EXPECTED '$.expected_snapshot'
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
export EXPECTED=$LOS_FIXTURE_SNAPSHOT_1
```

## Step 5: the approval subject is the intent hash

```python
import hashlib, json
subject = {k: envelope[k] for k in (
    "schema_version", "capability", "channel",
    "expected_snapshot", "expected_revisions", "payload")}
if "session_id" in envelope:
    subject["session_id"] = envelope["session_id"]
approval = "sha256:" + hashlib.sha256(json.dumps(
    subject, sort_keys=True, separators=(",", ":"),
    ensure_ascii=False).encode("utf-8")).hexdigest()
```

```bash
SNAP=$(.venv/bin/python tools/los.py bootstrap --compact \
  | .venv/bin/python -c 'import json,sys; print(json.load(sys.stdin)["snapshot_id"])')
# envelope.json: schema_version 2, request_id "request-<key>",
# idempotency_key "<key>", capability "capture.create", channel "operator",
# expected_snapshot "$SNAP",
# expected_revisions {"capture-request:<key>": 0},
# approval {"kind": "operator-approval", "subject_sha256": <intent hash>},
# payload {"text": "…"}
.venv/bin/python tools/los.py capability capture.create --payload-file envelope.json
```

Section 25c defines the subject hash over the six intent fields (plus the
sealed session, when one is carried). The recipe, run against the sealed
envelope above:

```python
import hashlib, json
subject = {k: envelope[k] for k in (
    "schema_version", "capability", "channel",
    "expected_snapshot", "expected_revisions", "payload")}
if "session_id" in envelope:
    subject["session_id"] = envelope["session_id"]
approval = "sha256:" + hashlib.sha256(json.dumps(
    subject, sort_keys=True, separators=(",", ":"),
    ensure_ascii=False).encode("utf-8")).hexdigest()
```

```scrut {interpolated: true}
$ $LOS_REPO/.venv/bin/python -c "import hashlib,json,os; e=json.load(open(os.path.join(os.environ['TMPDIR'],'capture-a.json'))); s={k:e[k] for k in ('schema_version','capability','channel','expected_snapshot','expected_revisions','payload')}; h='sha256:'+hashlib.sha256(json.dumps(s,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest(); assert h==e['approval']['subject_sha256'],h; print(h)"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
$LOS_FIXTURE_INTENT_1
```

## Step 6: submit the envelope

```scrut {interpolated: true}
$ los capability capture.create --payload-file "$TMPDIR/capture-a.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
{"schema_version":2,"request_id":"request-envelope-capture-a","idempotency_key":"envelope-capture-a","capability":"capture.create","ok":true,"replayed":false,"transaction_id":"transaction-20261001-090000-001","receipt_path":"operations/transactions/transaction-20261001-090000-001.yaml","snapshot_after":"$LOS_FIXTURE_SNAPSHOT_2","result":{"ok":true,"captured":"work/inbox/20261001-090000-half-formed-idea-about-the-derivation.md","transaction_id":"transaction-20261001-090000-001","receipt_path":"operations/transactions/transaction-20261001-090000-001.yaml","artifact_revisions":{"capture-request:envelope-capture-a":1},"snapshot_after":"$LOS_FIXTURE_SNAPSHOT_2","replayed":false},"error":null}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability capture.create
```

## The drop landed in the inbox

```scrut
$ $H/los-assert-file work/inbox/20261001-090000-half-formed-idea-about-the-derivation.md --sha256 e1d085adb9fd26761396362a7cf61f23f69681fc6bd6f9664272c3909cc58fcb
```

## Step 4: resubmitting the saved envelope replays it

```scrut {interpolated: true}
$ los capability capture.create --payload-file "$TMPDIR/capture-a.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
{"schema_version":2,"request_id":"request-envelope-capture-a","idempotency_key":"envelope-capture-a","capability":"capture.create","ok":true,"replayed":true,"transaction_id":"transaction-20261001-090000-001","receipt_path":"operations/transactions/transaction-20261001-090000-001.yaml","snapshot_after":"$LOS_FIXTURE_SNAPSHOT_2","result":{"transaction_id":"transaction-20261001-090000-001","receipt_path":"operations/transactions/transaction-20261001-090000-001.yaml","artifact_revisions":{"capture-request:envelope-capture-a":1},"snapshot_after":"$LOS_FIXTURE_SNAPSHOT_2","replayed":true,"captured":"work/inbox/20261001-090000-half-formed-idea-about-the-derivation.md"},"error":null}
```

## A second envelope, sealed against the new snapshot

```scrut {output_stream: stderr}
$ $H/los-seal --capability capture.create --payload '{"text": "A second capture that moves the snapshot."}' --key envelope-capture-b --request-id request-envelope-capture-b --guards auto --out "$TMPDIR/capture-b.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
seal_envelope: guards auto: capture-request:envelope-capture-b=0
```

## A third envelope, sealed while the second is still current

```scrut {output_stream: stderr}
$ $H/los-seal --capability capture.create --payload '{"text": "A third capture, sealed too early."}' --key envelope-capture-c --request-id request-envelope-capture-c --guards auto --out "$TMPDIR/capture-c.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
seal_envelope: guards auto: capture-request:envelope-capture-c=0
```

## Submitting the second capture moves the snapshot

```scrut {interpolated: true}
$ los capability capture.create --payload-file "$TMPDIR/capture-b.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
{"schema_version":2,"request_id":"request-envelope-capture-b","idempotency_key":"envelope-capture-b","capability":"capture.create","ok":true,"replayed":false,"transaction_id":"transaction-20261001-090000-002","receipt_path":"operations/transactions/transaction-20261001-090000-002.yaml","snapshot_after":"$LOS_FIXTURE_SNAPSHOT_3","result":{"ok":true,"captured":"work/inbox/20261001-090000-a-second-capture-that-moves-the-snapshot.md","transaction_id":"transaction-20261001-090000-002","receipt_path":"operations/transactions/transaction-20261001-090000-002.yaml","artifact_revisions":{"capture-request:envelope-capture-b":1},"snapshot_after":"$LOS_FIXTURE_SNAPSHOT_3","replayed":false},"error":null}
```

## The third envelope now refuses as stale

```scrut {interpolated: true}
$ los capability capture.create --payload-file "$TMPDIR/capture-c.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
{"schema_version":2,"request_id":"request-envelope-capture-c","idempotency_key":"envelope-capture-c","capability":"capture.create","ok":false,"replayed":false,"transaction_id":null,"receipt_path":null,"snapshot_after":null,"result":{},"error":{"code":"STALE_SNAPSHOT","message":"canonical state changed since this request was approved","retryable":true,"details":{"expected":"$LOS_FIXTURE_SNAPSHOT_2","actual":"$LOS_FIXTURE_SNAPSHOT_3"}}}
[3]
```

## A second bare command refuses with its own first clause

`inbox-resolve` refuses without an envelope, as §25c requires, but its
message starts `inbox resolve requires` where §25c quotes `canonical
writes must use` (M-02 in `tests/architecture/mismatches.yaml`).

```scrut {output_stream: stderr}
$ los inbox-resolve note-drop.md --drop-sha256 sha256:cff485a0c38476920bff529d70a47c19fddb0380750b9a0152521d7eb9b6c81d --routed-to note-demo
los: INVALID_REQUEST: inbox resolve requires GatewayEnvelopeV2; direct CLI application is disabled
[2]
```
