---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Revise an existing plan (WORKFLOWS §25a)

Executable transcript of the bounded revision path: read the named
route with its snapshot and revision guards, preflight the field
change, apply it through a GatewayEnvelopeV2, and compact the maps
without editing content. The structural creation/import lane is
fixture-inexpressible here — the assembler refuses the batch and the
live map is a legacy template — and both stops are pinned below.
`tests/test_procedures.py` runs it with Scrut; `<REPO>` comes from
the `LOS_REPO` environment variable the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Read the named route with its guards

```scrut
$ los plan-edit-context unit-demo-l01 --route-id route-b2f1f80014860a929a3af0bc
{"schema_version":1,"snapshot_id":"sha256:fbfc72c8f5d2cf47382eed134b76a0d3033178512c64206221aebe108764538b","contract":"plan-edit-context","unit_id":"unit-demo-l01","module_id":"module-demo","artifact_revisions":{"module-demo":0,"study-map-demo-l01":0,"unit-demo-l01":3},"preflight":"route-patch UNIT_ID ROUTE_ID --changes JSON --check returns exact write guards","route":{"unit_id":"unit-demo-l01","id":"route-b2f1f80014860a929a3af0bc","title":"Demo book — expected-value derivation","format":"book","angle":"Derives the weighted sum and works a discrete example.","covers":["knowledge-demo-outcomes","knowledge-demo-expectation"],"depth":"derivation","scope":"current","locator":"lecture-01.pdf","source_id":"source-demo-book"},"uses":[{"stage_id":"stage-demo","resource_index":3,"scope_triage":null,"overrides":{}}],"patch_fields":["angle","angle_detail","locator","title","url","vault_path"],"patch_capability":"route.patch"}
```

## The unit brief names the route when the id is unknown

```scrut
$ los plan-edit-context unit-demo-l01 --brief | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["contract"], d["unit_id"]); print(d["inventory"]["route_ids"]); print(d["inventory"]["route_count"], d["inventory"]["stage_count"])'
plan-edit-context-brief unit-demo-l01
['route-b2f1f80014860a929a3af0bc']
1 2
```

## One batch read shares the guards and preserves order

```scrut
$ los plan-edit-context unit-demo-l01 --route-ids route-b2f1f80014860a929a3af0bc
{"schema_version":1,"snapshot_id":"sha256:fbfc72c8f5d2cf47382eed134b76a0d3033178512c64206221aebe108764538b","contract":"plan-edit-context-batch","unit_id":"unit-demo-l01","module_id":"module-demo","artifact_revisions":{"module-demo":0,"study-map-demo-l01":0,"unit-demo-l01":3},"preflight":"route-patch UNIT_ID ROUTE_ID --changes JSON --check returns exact write guards","requested_route_ids":["route-b2f1f80014860a929a3af0bc"],"routes":[{"route":{"unit_id":"unit-demo-l01","id":"route-b2f1f80014860a929a3af0bc","title":"Demo book — expected-value derivation","format":"book","angle":"Derives the weighted sum and works a discrete example.","covers":["knowledge-demo-outcomes","knowledge-demo-expectation"],"depth":"derivation","scope":"current","locator":"lecture-01.pdf","source_id":"source-demo-book"},"uses":[{"stage_id":"stage-demo","resource_index":3,"scope_triage":null,"overrides":{}}],"patch_fields":["angle","angle_detail","locator","title","url","vault_path"],"patch_capability":"route.patch"}]}
```

## The batch refuses atomically on an unknown id

```scrut {output_stream: stderr}
$ los plan-edit-context unit-demo-l01 --route-ids route-b2f1f80014860a929a3af0bc route-missing
los: route route-missing is missing or ambiguous in this unit
[2]
```

## Preflight the angle change

```scrut
$ los route-patch unit-demo-l01 route-b2f1f80014860a929a3af0bc --changes '{"angle": "Derives the weighted sum with a worked discrete example for revision."}' --check
{"schema_version":1,"snapshot_id":"sha256:fbfc72c8f5d2cf47382eed134b76a0d3033178512c64206221aebe108764538b","unit_id":"unit-demo-l01","route_id":"route-b2f1f80014860a929a3af0bc","changes":{"angle":{"before":"Derives the weighted sum and works a discrete example.","after":"Derives the weighted sum with a worked discrete example for revision."}},"plan_sha256":"sha256:9a1a49f78a445a973197d2806b22e9d3369bc095584c7953a72c8ed7e18fbca5","affected_files":["curriculum/modules/module-demo/source-map.yaml","curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"],"artifact_ids":["module-demo","study-map-demo-l01","unit-demo-l01"],"expected_revisions":{"module-demo":0,"study-map-demo-l01":0,"unit-demo-l01":3},"ok":true,"check":true,"canonical_files_written":0,"next":{"apply_via":"GatewayEnvelopeV2","capability":"route.patch","payload":{"unit_id":"unit-demo-l01","route_id":"route-b2f1f80014860a929a3af0bc","changes":{"angle":"Derives the weighted sum with a worked discrete example for revision."}},"expected_snapshot":"sha256:fbfc72c8f5d2cf47382eed134b76a0d3033178512c64206221aebe108764538b","expected_revisions":{"module-demo":0,"study-map-demo-l01":0,"unit-demo-l01":3},"apply_how":"direct CLI application is disabled; submit a GatewayEnvelopeV2 with this capability, payload, expected_snapshot and expected_revisions"}}
```

## The bare CLI prefights and nothing more

```scrut
$ (set -o pipefail; los route-patch unit-demo-l01 route-b2f1f80014860a929a3af0bc --changes '{"angle": "x"}' | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["ok"]); print(d["errors"][0].split(" — ")[0])')
False
canonical writes must use GatewayEnvelopeV2; direct CLI application is disabled
[2]
```

## An identity change is not a bounded patch

```scrut {output_stream: stderr}
$ los route-patch unit-demo-l01 route-b2f1f80014860a929a3af0bc --changes '{"scope": "exam"}' --check
los: changes must contain nonempty text for declared material fields only
[2]
```

## Seal the angle change with derived guards

```scrut {output_stream: stderr}
$ $H/los-seal --capability route.patch --payload '{"unit_id": "unit-demo-l01", "route_id": "route-b2f1f80014860a929a3af0bc", "changes": {"angle": "Derives the weighted sum with a worked discrete example for revision."}}' --key route-revise-angle --request-id request-route-revise-angle --guards auto --out "$TMPDIR/route-revise.json"
seal_envelope: guards auto: module-demo=0, study-map-demo-l01=0, unit-demo-l01=3
```

## Apply the angle change

```scrut
$ los capability route.patch --payload-file "$TMPDIR/route-revise.json"
{
  "schema_version": 2,
  "request_id": "request-route-revise-angle",
  "idempotency_key": "route-revise-angle",
  "capability": "route.patch",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:368f623ee146d3aae4811979e77f9d165ee455ee571c068c3e8914fe372b4ae4",
  "result": {
    "schema_version": 1,
    "unit_id": "unit-demo-l01",
    "route_id": "route-b2f1f80014860a929a3af0bc",
    "changes": {
      "angle": {
        "before": "Derives the weighted sum and works a discrete example.",
        "after": "Derives the weighted sum with a worked discrete example for revision."
      }
    },
    "plan_sha256": "sha256:9a1a49f78a445a973197d2806b22e9d3369bc095584c7953a72c8ed7e18fbca5",
    "affected_files": [
      "curriculum/modules/module-demo/source-map.yaml",
      "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
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
    "snapshot_after": "sha256:368f623ee146d3aae4811979e77f9d165ee455ee571c068c3e8914fe372b4ae4",
    "replayed": false
  },
  "error": null
}
```

## The patch landed in both maps with a receipt

```scrut
$ $H/los-assert-file curriculum/modules/module-demo/source-map.yaml --sha256 0bffdcb90cdec31c462904e03ad32b55d4740084f6e080c12646f1308391b399
```

```scrut
$ $H/los-assert-file curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml --sha256 056af021662ec7a38a501a9a72ec6a4549aa64f87eef2d4544dbd6ec2651c060
```

```scrut
$ $H/los-assert-receipt --last --capability route.patch
```

## The route now reads back the revised angle

```scrut
$ los plan-edit-context unit-demo-l01 --route-id route-b2f1f80014860a929a3af0bc | $LOS_REPO/.venv/bin/python -c 'import json,sys; print(json.load(sys.stdin)["route"]["angle"])'
Derives the weighted sum with a worked discrete example for revision.
```

## Preflight the compaction

```scrut
$ los module-materials-compact module-demo --check
{"schema_version":1,"snapshot_id":"sha256:368f623ee146d3aae4811979e77f9d165ee455ee571c068c3e8914fe372b4ae4","module_id":"module-demo","map_bytes_saved":50,"referenced_routes":1,"plan_sha256":"sha256:74fb4986cb287354311feea050fcdc0b8940c9d8ca3ecdc930f0d149c9909e93","affected_files":["curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"],"artifact_ids":["module-demo","study-map-demo-l01","unit-demo-l01"],"expected_revisions":{"module-demo":1,"study-map-demo-l01":1,"unit-demo-l01":4},"ok":true,"check":true,"canonical_files_written":0}
```

## Seal the compaction with derived guards

```scrut {output_stream: stderr}
$ $H/los-seal --capability module.materials.compact --payload '{"module_id": "module-demo", "plan_sha256": "sha256:74fb4986cb287354311feea050fcdc0b8940c9d8ca3ecdc930f0d149c9909e93"}' --key module-compact --request-id request-module-compact --guards auto --out "$TMPDIR/module-compact.json"
seal_envelope: guards auto: module-demo=1, study-map-demo-l01=1, unit-demo-l01=4
```

## Apply the compaction

```scrut
$ los capability module.materials.compact --payload-file "$TMPDIR/module-compact.json"
{
  "schema_version": 2,
  "request_id": "request-module-compact",
  "idempotency_key": "module-compact",
  "capability": "module.materials.compact",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-002",
  "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
  "snapshot_after": "sha256:ed8ae6650211b385bb2b684b88594a6414251a270cfd83eb0cc1b16c4e15bc54",
  "result": {
    "schema_version": 1,
    "module_id": "module-demo",
    "map_bytes_saved": 50,
    "referenced_routes": 1,
    "plan_sha256": "sha256:74fb4986cb287354311feea050fcdc0b8940c9d8ca3ecdc930f0d149c9909e93",
    "affected_files": [
      "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
    ],
    "artifact_ids": [
      "module-demo",
      "study-map-demo-l01",
      "unit-demo-l01"
    ],
    "expected_revisions": {
      "module-demo": 1,
      "study-map-demo-l01": 1,
      "unit-demo-l01": 4
    },
    "ok": true,
    "transaction_id": "transaction-20261001-090000-002",
    "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
    "artifact_revisions": {
      "module-demo": 2,
      "study-map-demo-l01": 2,
      "unit-demo-l01": 5
    },
    "snapshot_after": "sha256:ed8ae6650211b385bb2b684b88594a6414251a270cfd83eb0cc1b16c4e15bc54",
    "replayed": false
  },
  "error": null
}
```

## The compacted map persisted with a receipt

```scrut
$ $H/los-assert-file curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml --sha256 84b6e4477efcd2a4e88d3619eb15dde5d2ca885b5b4f349f1ddd4a657cd46a58
```

```scrut
$ $H/los-assert-receipt --last --capability module.materials.compact
```

## Validate the revised plan

```scrut
$ los validate | tail -n 1
0 error(s), 9 warning(s) — OK
```

## The structural lane stops here: the assembler refuses the batch

```scrut {output_stream: stderr}
$ $LOS_REPO/.venv/bin/python $LOS_REPO/tools/assemble_lecture_study_maps.py --root "$LOS_FX" --out "$TMPDIR/asm-25a" --unit unit-demo-l01
assembly preflight failed; no draft files were written
- unit-demo-l01 stage has no concept coverage: stage-demo-outcomes
- unit-demo-l01 stage has no concept coverage: stage-demo-expectation
[2]
```

## The structural lane stops here: the live map is a legacy template

```scrut
$ cp curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml "$TMPDIR/study-map-copy.yaml" && $LOS_REPO/.venv/bin/python -c 'import io,os; p = os.path.join(os.environ["TMPDIR"], "study-map-copy.yaml"); t = io.open(p, encoding="utf-8").read().replace("label: Demo Book \u00a72", "label: Demo Book \u00a72 (revised)", 1); io.open(p, "w", encoding="utf-8").write(t)'
```

```scrut
$ los unit-map-import unit-demo-l01 --file "$TMPDIR/study-map-copy.yaml" --replace --check >"$TMPDIR/import-out.txt" 2>&1; echo "exit=$?"; cat "$TMPDIR/import-out.txt"
exit=2
los: study map creation contract failed: plan_template_version must be 1; legacy plans are readable but cannot be used as creation templates; stage numbers must be sequential in authored order: expected [1, 2], got [None, None]
```
