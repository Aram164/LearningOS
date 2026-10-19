---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Source routing and feedback (WORKFLOWS §26)

Executable transcript of routing one source to its stage and recording
lightweight evidence on it: the global identity is registered once, the
module join carries its role, the unit selection pins the confirmed
scope to the exact route, the smallest actionable locator goes on the
route in page grammar, and two feedback records land on the stage while
a third source stays refused. Changing any of the routed shape
afterwards is a plan revision. `tests/test_procedures.py` runs it with
Scrut; `<REPO>` comes from the `LOS_REPO` environment variable the test
sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## One global source identity, registered once

```scrut
$ los inspect source-demo-book | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["id"], d["title"], d["material"])'
source-demo-book Demo Book material://source-demo-book/book.pdf
```

## The module join carries its role in that module

```scrut
$ grep -n "source_id: source-demo-book" -A 3 curriculum/modules/module-demo/source-map.yaml | head -n 8
4:- source_id: source-demo-book
5-  role: spine
6-  why: Scoped demo reading.
7-  priority: 0
```

```scrut
$ grep -n "id: route-b2f1f80014860a929a3af0bc" curriculum/modules/module-demo/source-map.yaml
10:    id: route-b2f1f80014860a929a3af0bc
```

## The unit selection pins the confirmed scope to the exact route

```scrut
$ grep -n "source_selections:" -A 4 curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml
13:source_selections:
14-- source_id: source-demo-book
15-  route_id: route-b2f1f80014860a929a3af0bc
16-  locator: lecture-01.pdf
17-  purpose: Current derivation
```

## Place the smallest actionable locator in page grammar

A deck position, not a printed label: file positions open at the page. Keep
the file identity in the locator and attach the exact quotation at that place
when rejudging coverage for the material change.

```scrut
$ los route-patch unit-demo-l01 route-b2f1f80014860a929a3af0bc --changes '{"locator": "lecture-01.pdf, PDF pp. 20-22"}' --claim-evidence '{"claim_id": "covers:route-b2f1f80014860a929a3af0bc", "evidence": [{"kind": "quote", "ref": "material://source-demo-book/lecture-01.pdf", "page": 21, "text": "Worked example part 1 of 4: a biased coin pays two on heads"}]}' --check | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["ok"], d["check"], d["canonical_files_written"]); print(json.dumps(d["changes"]["locator"], sort_keys=True))'
True True 0
{"after": "lecture-01.pdf, PDF pp. 20-22", "before": "lecture-01.pdf"}
```

```scrut {output_stream: stderr}
$ $H/los-seal --capability route.patch --payload '{"unit_id": "unit-demo-l01", "route_id": "route-b2f1f80014860a929a3af0bc", "changes": {"locator": "lecture-01.pdf, PDF pp. 20-22"}, "claim_evidence": {"claim_id": "covers:route-b2f1f80014860a929a3af0bc", "evidence": [{"kind": "quote", "ref": "material://source-demo-book/lecture-01.pdf", "page": 21, "text": "Worked example part 1 of 4: a biased coin pays two on heads"}]}}' --key s26-locator --request-id request-s26-locator --guards auto --out "$TMPDIR/s26-locator.json"
seal_envelope: guards auto: file:operations/transactions/lineage.yaml=0, module-demo=0, study-map-demo-l01=0, unit-demo-l01=3
```

```scrut
$ los capability route.patch --payload-file "$TMPDIR/s26-locator.json"
{
  "schema_version": 2,
  "request_id": "request-s26-locator",
  "idempotency_key": "s26-locator",
  "capability": "route.patch",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:840f25a37725e13cf9c4cd2a687dcd14a67f7bda23fe04bd4808b8c94be303d1",
  "result": {
    "schema_version": 1,
    "unit_id": "unit-demo-l01",
    "route_id": "route-b2f1f80014860a929a3af0bc",
    "changes": {
      "locator": {
        "before": "lecture-01.pdf",
        "after": "lecture-01.pdf, PDF pp. 20-22"
      }
    },
    "claim_anchors": [
      {
        "claim_id": "covers:route-b2f1f80014860a929a3af0bc",
        "classification": "anchored",
        "quotes": [
          {
            "ref": "material://source-demo-book/lecture-01.pdf",
            "text": "Worked example part 1 of 4: a biased coin pays two on heads",
            "page": 21,
            "page_end": null,
            "window": null,
            "node": "",
            "matched": true
          }
        ],
        "bindings": [
          {
            "material": "material://source-demo-book/lecture-01.pdf",
            "manifest": "source-demo-book/lecture-01.pdf",
            "sha256": "395ded80ff4a721e2a91f400a3c6a3abd1f8d37e3c7f70b5ef42fa30d5264ea5",
            "place": "p21",
            "language": "en"
          }
        ]
      }
    ],
    "claims": [
      {
        "claim_id": "covers:route-b2f1f80014860a929a3af0bc",
        "before": "stale",
        "after": "rejudged",
        "warning": "",
        "next": ""
      }
    ],
    "plan_sha256": "sha256:b9f78241d3f717544d1b2bcdb7ae0c36b05c492ee845924132c94522bb6f8346",
    "affected_files": [
      "curriculum/modules/module-demo/source-map.yaml",
      "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml",
      "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml",
      "operations/transactions/lineage.yaml"
    ],
    "artifact_ids": [
      "file:operations/transactions/lineage.yaml",
      "module-demo",
      "study-map-demo-l01",
      "unit-demo-l01"
    ],
    "expected_revisions": {
      "file:operations/transactions/lineage.yaml": 0,
      "module-demo": 0,
      "study-map-demo-l01": 0,
      "unit-demo-l01": 3
    },
    "ok": true,
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "file:operations/transactions/lineage.yaml": 1,
      "module-demo": 1,
      "study-map-demo-l01": 1,
      "unit-demo-l01": 4
    },
    "snapshot_after": "sha256:840f25a37725e13cf9c4cd2a687dcd14a67f7bda23fe04bd4808b8c94be303d1",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability route.patch
```

## The route carries the file-position locator

```scrut
$ grep -n "lecture-01.pdf, PDF pp. 20-22" curriculum/modules/module-demo/source-map.yaml
19:    locator: lecture-01.pdf, PDF pp. 20-22
```

## Record lightweight personal evidence on the stage

```scrut {output_stream: stderr}
$ $H/los-seal --capability source.feedback.record --payload '{"unit_id": "unit-demo-l01", "stage_id": "stage-demo", "source_id": "source-demo-book", "feedback": "helpful"}' --key s26-fb --request-id request-s26-fb --guards auto --out "$TMPDIR/s26-fb.json"
seal_envelope: guards auto: study-map-demo-l01=1, unit-demo-l01=4
```

```scrut
$ los capability source.feedback.record --payload-file "$TMPDIR/s26-fb.json"
{
  "schema_version": 2,
  "request_id": "request-s26-fb",
  "idempotency_key": "s26-fb",
  "capability": "source.feedback.record",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-002",
  "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
  "snapshot_after": "sha256:6ef527242fad5e036ba39e4eb6496e30fd9ed7ea1e728604eaafe61d5b0ed421",
  "result": {
    "ok": true,
    "unit_id": "unit-demo-l01",
    "stage_id": "stage-demo",
    "feedback": {
      "source_id": "source-demo-book",
      "feedback": "helpful",
      "recorded": "2026-10-01"
    },
    "transaction_id": "transaction-20261001-090000-002",
    "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
    "artifact_revisions": {
      "study-map-demo-l01": 2,
      "unit-demo-l01": 5
    },
    "snapshot_after": "sha256:6ef527242fad5e036ba39e4eb6496e30fd9ed7ea1e728604eaafe61d5b0ed421",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability source.feedback.record
```

## Record evidence against one resource with a note

```scrut {output_stream: stderr}
$ $H/los-seal --capability source.feedback.record --payload '{"unit_id": "unit-demo-l01", "stage_id": "stage-demo", "source_id": "source-demo-book", "feedback": "useful-for-derivation", "resource_id": "resource-demo-book-ch01", "note": "Clear derivation."}' --key s26-fb2 --request-id request-s26-fb2 --guards auto --out "$TMPDIR/s26-fb2.json"
seal_envelope: guards auto: study-map-demo-l01=2, unit-demo-l01=5
```

```scrut
$ los capability source.feedback.record --payload-file "$TMPDIR/s26-fb2.json"
{
  "schema_version": 2,
  "request_id": "request-s26-fb2",
  "idempotency_key": "s26-fb2",
  "capability": "source.feedback.record",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-003",
  "receipt_path": "operations/transactions/transaction-20261001-090000-003.yaml",
  "snapshot_after": "sha256:5b5fddf9e71f8cac6746ba54c7922fafab72204bbfea5ec4b3fbd8073cad0de9",
  "result": {
    "ok": true,
    "unit_id": "unit-demo-l01",
    "stage_id": "stage-demo",
    "feedback": {
      "source_id": "source-demo-book",
      "feedback": "useful-for-derivation",
      "recorded": "2026-10-01",
      "resource_id": "resource-demo-book-ch01",
      "note": "Clear derivation."
    },
    "transaction_id": "transaction-20261001-090000-003",
    "receipt_path": "operations/transactions/transaction-20261001-090000-003.yaml",
    "artifact_revisions": {
      "study-map-demo-l01": 3,
      "unit-demo-l01": 6
    },
    "snapshot_after": "sha256:5b5fddf9e71f8cac6746ba54c7922fafab72204bbfea5ec4b3fbd8073cad0de9",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability source.feedback.record
```

## Feedback remains on that stage

```scrut
$ grep -n "source_feedback:" -A 6 curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml | head -n 14
42:  source_feedback:
43-  - source_id: source-demo-book
44-    feedback: helpful
45-    recorded: '2026-10-01'
46-  - source_id: source-demo-book
47-    feedback: useful-for-derivation
48-    recorded: '2026-10-01'
--
76:  source_feedback: []
```

## An unregistered source is refused

```scrut {output_stream: stderr}
$ $H/los-seal --capability source.feedback.record --payload '{"unit_id": "unit-demo-l01", "stage_id": "stage-demo", "source_id": "source-nope", "feedback": "helpful"}' --key s26-bad --request-id request-s26-bad --guards auto --out "$TMPDIR/s26-bad.json"
seal_envelope: source not found: source-nope; fix the payload and seal again
[2]
```

## The routed plans validate and regenerate

```scrut
$ (set -o pipefail; los validate | tail -n 1)
0 error(s), 8 warning(s) — OK
```

```scrut
$ los generate
published generated/manifest.json (atomic contract snapshot)
```
