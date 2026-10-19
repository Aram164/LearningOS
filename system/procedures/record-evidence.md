---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Record evidence (WORKFLOWS §8)

Executable transcript of learner evidence intake on both paths: the
direct `observe` command for a stage carrying a `runtime_target` (the
terminal session is the approval, so no envelope), and the untargeted
ledger envelope for a stage without one. Unknown requirements refuse
with suggestions; a stage without a target is named. The fixture's
targeted requirement is `req-demo-l01-demo` on `stage-demo`; the
untargeted stage is `stage-demo-pending`. `tests/test_procedures.py`
runs it with Scrut; `<REPO>` comes from the `LOS_REPO` environment
variable the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## The direct path needs no envelope

```scrut
$ los observe req-demo-l01-demo --workspace workspace-demo --activity exercise --result correct --condition unfamiliar-example --note "Worked the example cleanly."
{"ok":true,"observation_id":"observation-c5e7a09bdfe01c727161dcf3aef8fbe4","workspace_id":"workspace-demo","transaction_id":"transaction-20261001-090000-001","receipt_path":"operations/transactions/transaction-20261001-090000-001.yaml","artifact_revisions":{"workspace-demo":1},"snapshot_after":"sha256:148c99537f111b6e25995446e4cbb04033727923aa19bd9b3d7228f671a725f9","replayed":false}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability learner.observation.append
```

## The observation landed in the workspace ledger

```scrut
$ $H/los-assert-file work/active/workspace-demo/observations.jsonl --sha256 52810523494d31d7007378d649067845fedf42258d41d7fe3692dd5e3d7ae946
```

## A mistyped requirement suggests the real one

```scrut {output_stream: stderr}
$ los observe req-demo-l01-demb --activity exercise --result correct
los: INVALID_REQUEST: unknown requirement: req-demo-l01-demb (did you mean: req-demo-l01-demo?)
[2]
```

## A stage without a target is named, never "unknown requirement"

```scrut {output_stream: stderr}
$ los observe stage-demo-pending --activity exercise --result correct
los: INVALID_REQUEST: stage stage-demo-pending (unit unit-demo-l01) has no requirement target; record the result without credit via `stage-result --workspace WORKSPACE --unit unit-demo-l01 --stage stage-demo-pending --activity ACTIVITY --result RESULT`, or author a target with `unit-plan-revise unit-demo-l01 --file REVISION.yaml --check` adding a runtime_target stage patch (WORKFLOWS §8)
[2]
```

## The untargeted ledger needs an envelope

The bare command refuses without one; its first clause differs from the
message §25c quotes for the class (M-01 in
`tests/architecture/mismatches.yaml`).

```scrut {output_stream: stderr}
$ los stage-result --workspace workspace-demo --unit unit-demo-l01 --stage stage-demo-pending --activity exercise --result correct
los: INVALID_REQUEST: stage results require GatewayEnvelopeV2; direct CLI application is disabled
[2]
```

## Seal the untargeted result with derived guards

```scrut {output_stream: stderr}
$ $H/los-seal --capability learner.stage-result.append --payload '{"workspace": "workspace-demo", "unit": "unit-demo-l01", "stage": "stage-demo-pending", "activity": "exercise", "result": "correct", "condition": ["unfamiliar-example"], "note": "No target yet; recorded without credit."}' --key stage-result-001 --request-id request-stage-result-001 --guards auto --out "$TMPDIR/stage-result.json"
seal_envelope: guards auto: workspace-demo=1
```

## Submit the envelope

```scrut
$ los capability learner.stage-result.append --payload-file "$TMPDIR/stage-result.json"
{
  "schema_version": 2,
  "request_id": "request-stage-result-001",
  "idempotency_key": "stage-result-001",
  "capability": "learner.stage-result.append",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-002",
  "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
  "snapshot_after": "sha256:e2abb9d1dddff1888e963c26d19d10418b0695a042df48744089e72f3d667a14",
  "result": {
    "ok": true,
    "stage_result_id": "stage-result-5f47ee7619671e2e6dfc38582fca09a0",
    "workspace_id": "workspace-demo",
    "unit": "unit-demo-l01",
    "stage": "stage-demo-pending",
    "credit": "none",
    "transaction_id": "transaction-20261001-090000-002",
    "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
    "artifact_revisions": {
      "workspace-demo": 2
    },
    "snapshot_after": "sha256:e2abb9d1dddff1888e963c26d19d10418b0695a042df48744089e72f3d667a14",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability learner.stage-result.append
```

## The row landed in the workspace ledger

```scrut
$ $H/los-assert-file work/active/workspace-demo/stage-results.jsonl --sha256 19ba94e9086771c86aa4e0775332de37fdb2883fae4a275591096caeb5deb450
```
