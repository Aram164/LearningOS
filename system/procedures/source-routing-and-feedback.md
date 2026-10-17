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

A deck position, not a printed label: file positions open at the page.

```scrut
$ los route-patch unit-demo-l01 route-b2f1f80014860a929a3af0bc --changes '{"locator": "physical PDF pp. 20-22"}' --check | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["ok"], d["check"], d["canonical_files_written"]); print(json.dumps(d["changes"]["locator"], sort_keys=True))'
True True 0
{"after": "physical PDF pp. 20-22", "before": "lecture-01.pdf"}
```

```scrut {output_stream: stderr}
$ $H/los-seal --capability route.patch --payload '{"unit_id": "unit-demo-l01", "route_id": "route-b2f1f80014860a929a3af0bc", "changes": {"locator": "physical PDF pp. 20-22"}}' --key s26-locator --request-id request-s26-locator --guards auto --out "$TMPDIR/s26-locator.json"
seal_envelope: guards auto: module-demo=0, study-map-demo-l01=0, unit-demo-l01=3
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
  "snapshot_after": "sha256:2fbab4c5fb6c6fdd4929c0c8101492a15bee3321d4fb8d77faf484b1074bf952",
  "result": {
    "schema_version": 1,
    "unit_id": "unit-demo-l01",
    "route_id": "route-b2f1f80014860a929a3af0bc",
    "changes": {
      "locator": {
        "before": "lecture-01.pdf",
        "after": "physical PDF pp. 20-22"
      }
    },
    "plan_sha256": "sha256:5b1502ca0d0b55a5b858268aae38420172e1c5096fc9f0ca1e281dc4b301a33b",
    "affected_files": [
      "curriculum/modules/module-demo/source-map.yaml",
      "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml",
      "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    ],
    "artifact_ids": [
      "module-demo",
      "study-map-demo-l01",
      "unit-demo-l01"
    ],
    "expected_revisions": {
      "module-demo": 0,
      "study-map-demo-l01": 0,
      "unit-demo-l01": 3
    },
    "ok": true,
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "module-demo": 1,
      "study-map-demo-l01": 1,
      "unit-demo-l01": 4
    },
    "snapshot_after": "sha256:2fbab4c5fb6c6fdd4929c0c8101492a15bee3321d4fb8d77faf484b1074bf952",
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
$ grep -n "physical PDF pp. 20-22" curriculum/modules/module-demo/source-map.yaml
19:    locator: physical PDF pp. 20-22
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
  "snapshot_after": "sha256:ce5f52d65705f7d18993c6d51502a18e8ef07f960962505da4614a7bc0ed2f38",
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
    "snapshot_after": "sha256:ce5f52d65705f7d18993c6d51502a18e8ef07f960962505da4614a7bc0ed2f38",
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
  "snapshot_after": "sha256:ef1c1d86a9f92b087a961e6c4332b9a090ec0b0e0039396d53619167274a233b",
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
    "snapshot_after": "sha256:ef1c1d86a9f92b087a961e6c4332b9a090ec0b0e0039396d53619167274a233b",
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
