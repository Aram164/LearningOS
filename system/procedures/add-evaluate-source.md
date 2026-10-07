---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Add or evaluate a source (WORKFLOWS §6)

Executable transcript of source intake and evaluation: search the
registry, register one web-native source through its reviewed
create, refuse evaluations at intake, record the concept-linked
evaluation afterwards, register a second source metadata-only and
attach its verified local bytes, curate both on a new collection
the validator resolves, then verify with the documented tools. The
download-placement branch needs a real fetch with its placement map,
video examination needs its live service, and the inventory make
target has no Makefile in the fixture, so the transcript covers the
url and attach placements the fixture provides.
`tests/test_procedures.py` runs it with Scrut; `<REPO>` comes from
the `LOS_REPO` environment variable the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Search the registry by title

```scrut
$ los search Schaum
[]
```

## Review the intake create

```scrut
$ los source-intake --record '{"records": [{"action": "create", "id": "source-schaum-probability", "partition": "sources.yaml", "title": "Schaum Probability", "type": "book", "url": "https://example.com/schaum-probability", "discovery": {"observed": "2026-09-23", "basis": [{"kind": "list-entry", "ref": "legacy/EXAMPLE-LIST.md#L10"}], "possible_use": "worked examples."}}]}' --check
{
  "ok": true,
  "check": true,
  "records": 1,
  "diff": [
    {
      "id": "source-schaum-probability",
      "action": "create",
      "partition": "sources.yaml",
      "fields": {
        "title": {
          "before": null,
          "after": "Schaum Probability"
        },
        "type": {
          "before": null,
          "after": "book"
        },
        "url": {
          "before": null,
          "after": "https://example.com/schaum-probability"
        },
        "discovery": {
          "before": null,
          "after": {
            "observed": "2026-09-23",
            "basis": [
              {
                "kind": "list-entry",
                "ref": "legacy/EXAMPLE-LIST.md#L10"
              }
            ],
            "possible_use": "worked examples."
          }
        }
      }
    }
  ],
  "diff_sha256": "sha256:b337da57d18609ac0f08ce91d7a4cc4a422fc71455e697ced697a806b0fb3827",
  "expected_revisions": {
    "source-schaum-probability": 0
  },
  "artifact_ids": [
    "source-schaum-probability"
  ]
}
```

## Bind the reviewed diff hash

```scrut
$ eval "$(los source-intake --record '{"records": [{"action": "create", "id": "source-schaum-probability", "partition": "sources.yaml", "title": "Schaum Probability", "type": "book", "url": "https://example.com/schaum-probability", "discovery": {"observed": "2026-09-23", "basis": [{"kind": "list-entry", "ref": "legacy/EXAMPLE-LIST.md#L10"}], "possible_use": "worked examples."}}]}' --check | $H/los-bind INTAKE_DIFF '$.diff_sha256')" && echo "$INTAKE_DIFF"
sha256:b337da57d18609ac0f08ce91d7a4cc4a422fc71455e697ced697a806b0fb3827
```

## Intake refuses evaluations

```scrut
$ los source-intake --record '{"records": [{"action": "create", "id": "source-schaum-eval", "partition": "sources.yaml", "title": "Schaum Eval", "type": "book", "discovery": {"observed": "2026-09-23", "basis": [{"kind": "list-entry", "ref": "legacy/EXAMPLE-LIST.md#L10"}], "possible_use": "Probe."}, "evaluations": [{"level": "introductory"}]}]}' --check
{"ok": false, "error": "source-schaum-eval: field 'evaluations' is outside the intake allowlist (evaluations, topics, material, routes, selections, notes, feedback and observations are never written through intake)"}
[2]
```

## Seal the intake with derived guards

```scrut {output_stream: stderr}
$ $H/los-seal --capability source.intake.record --payload "{\"record\": {\"records\": [{\"action\": \"create\", \"id\": \"source-schaum-probability\", \"partition\": \"sources.yaml\", \"title\": \"Schaum Probability\", \"type\": \"book\", \"url\": \"https://example.com/schaum-probability\", \"discovery\": {\"observed\": \"2026-09-23\", \"basis\": [{\"kind\": \"list-entry\", \"ref\": \"legacy/EXAMPLE-LIST.md#L10\"}], \"possible_use\": \"worked examples.\"}}]}, \"expected_diff_sha256\": \"$INTAKE_DIFF\"}" --key source-intake-schaum --request-id request-source-intake-schaum --guards auto --out "$TMPDIR/source-intake-schaum.json"
seal_envelope: guards auto: source-schaum-probability=0
```

## Submit the intake

```scrut
$ los capability source.intake.record --payload-file "$TMPDIR/source-intake-schaum.json"
{
  "schema_version": 2,
  "request_id": "request-source-intake-schaum",
  "idempotency_key": "source-intake-schaum",
  "capability": "source.intake.record",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:c70002d692d95f441bf50fa71868df487ecc88ad74af0fbb2d33f9a5684221ac",
  "result": {
    "ok": true,
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "source-schaum-probability": 1
    },
    "snapshot_after": "sha256:c70002d692d95f441bf50fa71868df487ecc88ad74af0fbb2d33f9a5684221ac",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability source.intake.record
```

## The registry carries the source

```scrut
$ $H/los-assert-file sources/sources.yaml --sha256 ea99aefefe015d7deb8bb78a9a25e89d1c45c26654f068602eaba6ec9f7f9374
```

## Review the evaluation revision

```scrut
$ los source-revise --record '{"id": "source-schaum-probability", "evaluations": [{"level": "introductory", "roles": ["first-learning"], "strengths": ["worked examples with solutions"], "concepts": ["concept-expected-value"]}]}' --check | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["ok"], d["check"], d.get("diff_sha256", d.get("expected_diff_sha256")))'
True True sha256:3efff78a8f564cc2d09fc1df728f0c91451a96c2934295a48361daf1ff4a92c5
```

## Bind the evaluation diff hash

```scrut
$ eval "$(los source-revise --record '{"id": "source-schaum-probability", "evaluations": [{"level": "introductory", "roles": ["first-learning"], "strengths": ["worked examples with solutions"], "concepts": ["concept-expected-value"]}]}' --check | $H/los-bind EVAL_DIFF '$.diff_sha256')" && echo "$EVAL_DIFF"
sha256:3efff78a8f564cc2d09fc1df728f0c91451a96c2934295a48361daf1ff4a92c5
```

## Seal the evaluation with derived guards

```scrut {output_stream: stderr}
$ $H/los-seal --capability source.record.revise --payload "{\"record\": {\"id\": \"source-schaum-probability\", \"evaluations\": [{\"level\": \"introductory\", \"roles\": [\"first-learning\"], \"strengths\": [\"worked examples with solutions\"], \"concepts\": [\"concept-expected-value\"]}]}, \"expected_diff_sha256\": \"$EVAL_DIFF\"}" --key source-eval-schaum --request-id request-source-eval-schaum --guards auto --out "$TMPDIR/source-eval-schaum.json"
seal_envelope: guards auto: source-schaum-probability=1
```

## Submit the evaluation

```scrut
$ los capability source.record.revise --payload-file "$TMPDIR/source-eval-schaum.json"
{
  "schema_version": 2,
  "request_id": "request-source-eval-schaum",
  "idempotency_key": "source-eval-schaum",
  "capability": "source.record.revise",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-002",
  "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
  "snapshot_after": "sha256:3c499e3b142e811d560e59745c08a02f69e213ffba9f8c0e4f975c3ee8b4b190",
  "result": {
    "ok": true,
    "transaction_id": "transaction-20261001-090000-002",
    "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
    "artifact_revisions": {
      "source-schaum-probability": 2
    },
    "snapshot_after": "sha256:3c499e3b142e811d560e59745c08a02f69e213ffba9f8c0e4f975c3ee8b4b190",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability source.record.revise
```

## The registry carries the evaluation

```scrut
$ $H/los-assert-file sources/sources.yaml --sha256 c750adc390d58cc1e985cce7144632a5880ef21f3c4aa7e37cb2aae8637c575c
```

## Register the attach target metadata-only

```scrut
$ eval "$(los source-intake --record '{"records": [{"action": "create", "id": "source-scenario-bare", "partition": "sources.yaml", "title": "Scenario Bare", "type": "book", "discovery": {"observed": "2026-09-23", "basis": [{"kind": "list-entry", "ref": "legacy/EXAMPLE-LIST.md#L10"}], "possible_use": "Attach target."}}]}' --check | $H/los-bind BARE_DIFF '$.diff_sha256')" && echo "$BARE_DIFF"
sha256:002b66f6706277282d70f1deeaac29ca124f28d8b1207ea360f849a3fb2a1bc2
```

```scrut {output_stream: stderr}
$ $H/los-seal --capability source.intake.record --payload "{\"record\": {\"records\": [{\"action\": \"create\", \"id\": \"source-scenario-bare\", \"partition\": \"sources.yaml\", \"title\": \"Scenario Bare\", \"type\": \"book\", \"discovery\": {\"observed\": \"2026-09-23\", \"basis\": [{\"kind\": \"list-entry\", \"ref\": \"legacy/EXAMPLE-LIST.md#L10\"}], \"possible_use\": \"Attach target.\"}}]}, \"expected_diff_sha256\": \"$BARE_DIFF\"}" --key source-intake-bare --request-id request-source-intake-bare --guards auto --out "$TMPDIR/source-intake-bare.json"
seal_envelope: guards auto: source-scenario-bare=0
```

```scrut
$ los capability source.intake.record --payload-file "$TMPDIR/source-intake-bare.json"
{
  "schema_version": 2,
  "request_id": "request-source-intake-bare",
  "idempotency_key": "source-intake-bare",
  "capability": "source.intake.record",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-003",
  "receipt_path": "operations/transactions/transaction-20261001-090000-003.yaml",
  "snapshot_after": "sha256:1d27dcbbed30636a390abfd825943eb1d2e8a389991a9f19169fb676c756e18b",
  "result": {
    "ok": true,
    "transaction_id": "transaction-20261001-090000-003",
    "receipt_path": "operations/transactions/transaction-20261001-090000-003.yaml",
    "artifact_revisions": {
      "source-scenario-bare": 1
    },
    "snapshot_after": "sha256:1d27dcbbed30636a390abfd825943eb1d2e8a389991a9f19169fb676c756e18b",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability source.intake.record
```

## Read the verified local bytes

```scrut
$ MAT_SHA=$(sha256sum "$(dirname "$LOS_FX")/materials/source-scenario-bare/attached.pdf" | cut -d' ' -f1) && echo "$MAT_SHA"
61b4d4e33f928a4f6801ae74b3e940e0cfac1285aa4a958d46ce0ae142b49ed6
```

## Review the attach revision

```scrut
$ MAT_SHA=$(sha256sum "$(dirname "$LOS_FX")/materials/source-scenario-bare/attached.pdf" | cut -d' ' -f1) && los source-revise --record "{\"id\": \"source-scenario-bare\", \"material\": \"material://source-scenario-bare/attached.pdf\", \"material_sha256\": \"$MAT_SHA\"}" --check > "$TMPDIR/source-attach-check.json" && $LOS_REPO/.venv/bin/python -c 'import json,os; d = json.load(open(os.path.join(os.environ["TMPDIR"], "source-attach-check.json"))); print(d["ok"], d["check"])'
True True
```

```scrut
$ eval "$(cat "$TMPDIR/source-attach-check.json" | $H/los-bind ATTACH_DIFF '$.diff_sha256')" && echo "$ATTACH_DIFF"
sha256:2f478959e6ecde768db3beffe4aa953f658c82c8a00714cc3704afde1cc9248a
```

## Seal the attach with derived guards

```scrut {output_stream: stderr}
$ MAT_SHA=$(sha256sum "$(dirname "$LOS_FX")/materials/source-scenario-bare/attached.pdf" | cut -d' ' -f1) && $H/los-seal --capability source.record.revise --payload "{\"record\": {\"id\": \"source-scenario-bare\", \"material\": \"material://source-scenario-bare/attached.pdf\", \"material_sha256\": \"$MAT_SHA\"}, \"expected_diff_sha256\": \"$ATTACH_DIFF\"}" --key source-attach-bare --request-id request-source-attach-bare --guards auto --out "$TMPDIR/source-attach-bare.json"
seal_envelope: guards auto: source-scenario-bare=1
```

## Submit the attach

```scrut
$ los capability source.record.revise --payload-file "$TMPDIR/source-attach-bare.json"
{
  "schema_version": 2,
  "request_id": "request-source-attach-bare",
  "idempotency_key": "source-attach-bare",
  "capability": "source.record.revise",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-004",
  "receipt_path": "operations/transactions/transaction-20261001-090000-004.yaml",
  "snapshot_after": "sha256:0bc5890272804a12aeab2dbb4edbf3c90b5c6484c2327ae94b0cc00e18fab5e7",
  "result": {
    "ok": true,
    "transaction_id": "transaction-20261001-090000-004",
    "receipt_path": "operations/transactions/transaction-20261001-090000-004.yaml",
    "artifact_revisions": {
      "source-scenario-bare": 2
    },
    "snapshot_after": "sha256:0bc5890272804a12aeab2dbb4edbf3c90b5c6484c2327ae94b0cc00e18fab5e7",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability source.record.revise
```

## The registry carries the attached material

```scrut
$ $H/los-assert-file sources/sources.yaml --sha256 a9e94a8d3ed218d34c383f50d1699033b9ea97de1339c8074c59b7c281cd523d
```

## Curate both sources on a new collection

```scrut
$ cat > sources/collections/probe-shelf.yaml <<'EOF'
> title: Probe shelf
> collection_kind: catalogue
> entries:
> - source: source-schaum-probability
>   group: Worked
>   why: Worked probability examples with solutions.
> - source: source-scenario-bare
>   group: Worked
>   why: The attach-journey reading.
> EOF
```

## The collection is there

```scrut
$ $H/los-assert-file sources/collections/probe-shelf.yaml --sha256 1320a1bbfcede0238c5329b9d8a1fc8f7b9639266a8f0fb51434ac387887cd57
```

## The validator enforces that entries resolve

```scrut
$ cat > sources/collections/probe-bad.yaml <<'EOF'
> title: Probe bad shelf
> collection_kind: catalogue
> entries:
> - source: source-nope
>   group: Worked
>   why: Nothing resolves here.
> EOF
```

```scrut
$ set -o pipefail; los validate | tail -n 1
1 error(s), 10 warning(s) — FAIL
[1]
```

## Drop the bad shelf and re-validate

```scrut
$ rm sources/collections/probe-bad.yaml && los validate | tail -n 1
0 error(s), 10 warning(s) — OK
```

## Verify with the documented tools

```scrut
$ $LOS_REPO/.venv/bin/python $LOS_REPO/tools/validate.py --root "$LOS_FX" --compact | tail -n 1 | sed 's/ (.*//'
0 error(s), 10 warning(s) — OK
```

```scrut
$ $LOS_REPO/.venv/bin/python $LOS_REPO/tools/generate.py --root "$LOS_FX" | grep -c "^wrote "
22
```

## The rebuilt source index carries the new source

```scrut
$ grep -c "Schaum Probability" generated/source-index.md
3
```

## The collection rendered

```scrut
$ grep -c "Schaum Probability" generated/collections/probe-shelf.md
1
```
