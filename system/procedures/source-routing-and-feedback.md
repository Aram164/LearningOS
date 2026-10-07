---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Source routing and feedback (WORKFLOWS §26)

Executable transcript of recording lightweight personal evidence
on a stage: the bare CLI refuses, the sealed envelope commits, and
the judgment stays on that stage. Registering the source identity
is §6 and changing the routing afterwards is §25a; both are linked
procedures, not steps here. `tests/test_procedures.py` runs it with
Scrut; `<REPO>` comes from the `LOS_REPO` environment variable the
test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## The bare CLI refuses the write

```scrut
$ los source-feedback unit-demo-l01 stage-demo source-demo-book helpful --note "The derivation landed." >"$TMPDIR/fb-bare.txt" 2>&1; echo "exit=$?"; sed 's/ — .*//' "$TMPDIR/fb-bare.txt"
exit=2
canonical writes must use GatewayEnvelopeV2; direct CLI application is disabled
```

## Seal the feedback with derived guards

```scrut {output_stream: stderr}
$ $H/los-seal --capability source.feedback.record --payload '{"unit_id": "unit-demo-l01", "stage_id": "stage-demo", "source_id": "source-demo-book", "feedback": "helpful", "note": "The derivation landed."}' --key stage-feedback --request-id request-stage-feedback --guards auto --out "$TMPDIR/feedback.json"
seal_envelope: guards auto: study-map-demo-l01=0, unit-demo-l01=3
```

## Record the feedback

```scrut
$ los capability source.feedback.record --payload-file "$TMPDIR/feedback.json"
{
  "schema_version": 2,
  "request_id": "request-stage-feedback",
  "idempotency_key": "stage-feedback",
  "capability": "source.feedback.record",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:f148c792a38525a75d18e3f12ed9777ab1a7bce4fedf5e9fbc25c35225b96098",
  "result": {
    "ok": true,
    "unit_id": "unit-demo-l01",
    "stage_id": "stage-demo",
    "feedback": {
      "source_id": "source-demo-book",
      "feedback": "helpful",
      "recorded": "2026-10-01",
      "note": "The derivation landed."
    },
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "study-map-demo-l01": 1,
      "unit-demo-l01": 4
    },
    "snapshot_after": "sha256:f148c792a38525a75d18e3f12ed9777ab1a7bce4fedf5e9fbc25c35225b96098",
    "replayed": false
  },
  "error": null
}
```

## The feedback persisted with a receipt

```scrut
$ $H/los-assert-file curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml --sha256 472e0f82e0e6fcceade927c95b355e7e9bf14eefa36f073e303a4d6ecb56ab52
```

```scrut
$ $H/los-assert-receipt --last --capability source.feedback.record
```

## The judgment stays on that stage

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import yaml; d = yaml.safe_load(open("curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml")); s = [x for x in d["stages"] if x["id"] == "stage-demo"][0]; print(s["id"]); [print(f["source_id"], f["feedback"], f["recorded"], f["note"]) for f in s["source_feedback"]]'
stage-demo
source-demo-book helpful 2026-10-01 The derivation landed.
```

## Feedback for an unknown source is refused at seal time

```scrut {output_stream: stderr}
$ $H/los-seal --capability source.feedback.record --payload '{"unit_id": "unit-demo-l01", "stage_id": "stage-demo", "source_id": "source-missing", "feedback": "helpful"}' --key stage-feedback-bad --request-id request-stage-feedback-bad --guards auto --out "$TMPDIR/feedback-bad.json"
seal_envelope: los: source not found: source-missing; fix the payload and seal again
[2]
```

## Validate the recorded feedback

```scrut
$ los validate | tail -n 1
0 error(s), 9 warning(s) — OK
```
