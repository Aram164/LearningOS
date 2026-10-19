---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Review a stage's material angle (WORKFLOWS §29)

Executable transcript of attesting the relation between a route's
general description and one stage's narrowed placement: read both
texts, bind the route to its exact inspected file, draft the
replacement map outside the repository with a refinement review on one
row and a byte-evidenced correction on another, preflight the replace,
submit the content-bound envelope, and verify both reviews are current.
Changing the descriptions afterwards stales the reviews, and the stale
fingerprint is never merely refreshed. `tests/test_procedures.py` runs
it with Scrut; `<REPO>` comes from the `LOS_REPO` environment variable
the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Read the route's general description

```scrut
$ los plan-edit-context unit-demo-l01 --route-id route-b2f1f80014860a929a3af0bc | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["route"]["id"]); print(d["route"]["angle"])'
route-b2f1f80014860a929a3af0bc
Derives the weighted sum and works a discrete example.
```

## Read the stage's placed rows

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import yaml; d = yaml.safe_load(open("curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml")); s = [x for x in d["stages"] if x["id"] == "stage-demo"][0]; [print(r.get("id"), "|", r.get("label"), "|", r.get("locator")) for r in s["resources"]]'
resource-demo-book-ch01 | Demo Book §1 | §1
resource-demo-book-appendix | Demo Book Appendix | Appendix A
None | Demo companion video | None
resource-demo-route-mirror | Demo book — expected-value derivation | lecture-01.pdf
```

## Bind the route to its exact inspected file

A correction needs exact inspected bytes, so the route names its file
before anything is reviewed. The material-binding change carries exact-file
quotation evidence for its coverage judgment as well as the later angle review.

```scrut
$ los route-patch unit-demo-l01 route-b2f1f80014860a929a3af0bc --changes '{"vault_path": "material://source-demo-book/lecture-01.pdf"}' --claim-evidence '{"claim_id": "covers:route-b2f1f80014860a929a3af0bc", "evidence": [{"kind": "quote", "ref": "material://source-demo-book/lecture-01.pdf", "page": 1, "text": "Expected value, page 1 of 24: an outcome is a value a variable can take"}]}' --check | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["ok"], d["check"], d["canonical_files_written"])'
True True 0
```

```scrut {output_stream: stderr}
$ $H/los-seal --capability route.patch --payload '{"unit_id": "unit-demo-l01", "route_id": "route-b2f1f80014860a929a3af0bc", "changes": {"vault_path": "material://source-demo-book/lecture-01.pdf"}, "claim_evidence": {"claim_id": "covers:route-b2f1f80014860a929a3af0bc", "evidence": [{"kind": "quote", "ref": "material://source-demo-book/lecture-01.pdf", "page": 1, "text": "Expected value, page 1 of 24: an outcome is a value a variable can take"}]}}' --key s29-vault --request-id request-s29-vault --guards auto --out "$TMPDIR/s29-vault.json"
seal_envelope: guards auto: file:operations/transactions/lineage.yaml=0, module-demo=0, unit-demo-l01=3
```

```scrut
$ los capability route.patch --payload-file "$TMPDIR/s29-vault.json"
{
  "schema_version": 2,
  "request_id": "request-s29-vault",
  "idempotency_key": "s29-vault",
  "capability": "route.patch",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:8ba1f7c3115a998773450d9cc18d500add5a53f20ed3b5fe66e6c683e00fee99",
  "result": {
    "schema_version": 1,
    "unit_id": "unit-demo-l01",
    "route_id": "route-b2f1f80014860a929a3af0bc",
    "changes": {
      "vault_path": {
        "before": null,
        "after": "material://source-demo-book/lecture-01.pdf"
      }
    },
    "claim_anchors": [
      {
        "claim_id": "covers:route-b2f1f80014860a929a3af0bc",
        "classification": "anchored",
        "quotes": [
          {
            "ref": "material://source-demo-book/lecture-01.pdf",
            "text": "Expected value, page 1 of 24: an outcome is a value a variable can take",
            "page": 1,
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
            "place": "p1",
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
    "plan_sha256": "sha256:4a6d555c125b058d145b32edd860e417e65947bd62f675389cc4111eac78eafb",
    "affected_files": [
      "curriculum/modules/module-demo/source-map.yaml",
      "operations/transactions/lineage.yaml"
    ],
    "artifact_ids": [
      "file:operations/transactions/lineage.yaml",
      "module-demo",
      "unit-demo-l01"
    ],
    "expected_revisions": {
      "file:operations/transactions/lineage.yaml": 0,
      "module-demo": 0,
      "unit-demo-l01": 3
    },
    "ok": true,
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "file:operations/transactions/lineage.yaml": 1,
      "module-demo": 1,
      "unit-demo-l01": 4
    },
    "snapshot_after": "sha256:8ba1f7c3115a998773450d9cc18d500add5a53f20ed3b5fe66e6c683e00fee99",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability route.patch
```

## Observe the exact inspected bytes

```scrut
$ MAT_SHA=$(sha256sum "$(dirname "$LOS_FX")/materials/source-demo-book/lecture-01.pdf" | cut -d' ' -f1) && echo "$MAT_SHA"
395ded80ff4a721e2a91f400a3c6a3abd1f8d37e3c7f70b5ef42fa30d5264ea5
```

## Draft the replacement map outside the repository

The fingerprints come from the plan-rigor helper over the live route,
the drafted stage, and each drafted row.

```scrut
$ export MAT_SHA && $LOS_REPO/.venv/bin/python - <<'EOF'
> import os, sys, yaml
> sys.path.insert(0, os.environ["LOS_REPO"] + "/tools")
> from learning_os.derive.validation.plan_rigor import angle_review_fingerprint
> mat = os.environ["MAT_SHA"]
> sm = yaml.safe_load(open("curriculum/modules/module-demo/source-map.yaml"))
> route = None
> for entry in sm["sources"]:
>     for r in entry.get("unit_routes", []):
>         if r.get("id") == "route-b2f1f80014860a929a3af0bc":
>             route = {**r, "source_id": entry["source_id"]}
> stage = {"id": "stage-demo", "title": "Derive expected value",
>          "objective": "Derive and explain expected value."}
> res1 = {"route_id": "route-b2f1f80014860a929a3af0bc",
>         "source_id": "source-demo-book", "kind": "read", "locator": "§1",
>         "angle": "Work the discrete example first, then read the derivation."}
> fp1 = angle_review_fingerprint(route, stage, res1)
> res2 = {"route_id": "route-b2f1f80014860a929a3af0bc",
>         "source_id": "source-demo-book", "kind": "read", "locator": "Appendix A",
>         "angle": "Use the appendix table for the worked constants."}
> fp2 = angle_review_fingerprint(route, stage, res2)
> print("fp1:", fp1)
> print("fp2:", fp2)
> draft = {
>  "id": "study-map-demo-l01", "type": "study-map", "unit_id": "unit-demo-l01",
>  "status": "active", "current_stage": "stage-demo",
>  "source_plan": {"path": "work/active/workspace-demo/CONTEXT.md", "provenance": "operator"},
>  "detours": [], "shelving": {"state": "none"},
>  "stages": [
>   {"id": "stage-demo", "number": 1, "title": "Derive expected value", "status": "active",
>    "objective": "Derive and explain expected value.",
>    "done_when": ["Explain the derivation."], "exam_critical": False, "concepts": [],
>    "scope_triage": "required-now",
>    "resources": [
>     {"id": "resource-demo-book-ch01", "kind": "read", "label": "Demo Book §1",
>      "source_id": "source-demo-book", "locator": "§1",
>      "route_id": "route-b2f1f80014860a929a3af0bc",
>      "angle": "Work the discrete example first, then read the derivation.",
>      "angle_review": {"kind": "refinement", "reviewed_by": "probe-operator",
>       "reviewed_on": "2026-10-12",
>       "rationale": "The placement narrows the route to the worked example.",
>       "fingerprint": fp1}},
>     {"id": "resource-demo-book-appendix", "kind": "read", "label": "Demo Book Appendix",
>      "source_id": "source-demo-book", "locator": "Appendix A",
>      "route_id": "route-b2f1f80014860a929a3af0bc",
>      "angle": "Use the appendix table for the worked constants.",
>      "angle_review": {"kind": "correction", "reviewed_by": "probe-operator",
>       "reviewed_on": "2026-10-12",
>       "rationale": "The route understates the appendix table.",
>       "fingerprint": fp2,
>       "evidence": [{"material_uri": "material://source-demo-book/lecture-01.pdf",
>         "file_sha256": "sha256:" + mat, "locator": "physical PDF pp. 1"}]}},
>     {"kind": "watch", "label": "Demo companion video", "source_id": "source-demo-book"},
>     {"id": "resource-demo-route-mirror", "kind": "read",
>      "label": "Demo book — expected-value derivation",
>      "source_id": "source-demo-book", "locator": "lecture-01.pdf",
>      "angle": "Derives the weighted sum and works a discrete example."}],
>    "working_note": "curriculum/modules/module-demo/units/unit-demo-l01/stages/stage-demo/notes.md",
>    "attachments": [], "source_feedback": [],
>    "runtime_target": {"concept": "knowledge-demo-expectation",
>     "capability": {"kind": "explain", "operands": ["expectation"]},
>     "conditions": ["unfamiliar-example"], "evidence_spec": ["explain-reason"]}},
>   {"id": "stage-demo-pending", "number": 2, "title": "Apply expected value", "status": "pending",
>    "objective": "Apply expected value to a worked example.",
>    "done_when": ["Work the example."], "exam_critical": False, "concepts": [],
>    "scope_triage": "required-now",
>    "knowledge_node_id": "knowledge-demo-expectation",
>    "resources": [{"kind": "read", "label": "Demo Book §2", "source_id": "source-demo-book", "locator": "§2"}],
>    "working_note": "curriculum/modules/module-demo/units/unit-demo-l01/stages/stage-demo-pending/notes.md",
>    "attachments": [], "source_feedback": []}],
>  "plan_template_version": 1,
> }
> open(os.environ["TMPDIR"] + "/map-l01-replace.yaml", "w").write(yaml.safe_dump(draft, sort_keys=False))
> print("drafted map-l01-replace.yaml")
> EOF
fp1: sha256:b21056feaeec6fd635522b55207a8e95668bfaa41de9439152c3d37dbf850d0f
fp2: sha256:58df9cfa103de838dfb6fb11fdf4e25f7be525a95e1cb848bc098c2d1e9d0f01
drafted map-l01-replace.yaml
```

## Preflight the replacement and review its concrete diff

```scrut
$ los unit-map-import unit-demo-l01 --file "$TMPDIR/map-l01-replace.yaml" --replace --check | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["ok"], d["mode"], d["canonical_files_written"]); print(d["diff"]["replacement"], d["diff"]["stages_after"]); print(d["file_sha256"])'
True check 0
True ['stage-demo', 'stage-demo-pending']
sha256:31ac987f75414ab831ac92f8013ace3b607aa1dae035358c08fc51c2b4613f56
```

## Seal the replacement with derived guards

```scrut {output_stream: stderr}
$ MAP_SHA=$(sha256sum "$TMPDIR/map-l01-replace.yaml" | cut -d' ' -f1) && $H/los-seal --capability unit.map.import --payload "{\"unit_id\": \"unit-demo-l01\", \"file\": \"$TMPDIR/map-l01-replace.yaml\", \"file_sha256\": \"sha256:$MAP_SHA\", \"replace\": true}" --key s29-replace --request-id request-s29-replace --guards auto --out "$TMPDIR/s29-replace.json"
seal_envelope: guards auto: study-map-demo-l01=0, unit-demo-l01=4
```

```scrut
$ los capability unit.map.import --payload-file "$TMPDIR/s29-replace.json" | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["ok"], d["result"]["mode"], d["transaction_id"]); print(d["result"]["study_map_id"], d["result"]["diff"]["replacement"]); print(json.dumps(d["result"]["artifact_revisions"], sort_keys=True)); print(d["snapshot_after"])'
True apply transaction-20261001-090000-002
study-map-demo-l01 True
{"study-map-demo-l01": 1, "unit-demo-l01": 5}
sha256:554a117731a5cfd73fda91ea623558e564507e0ccf19cd4b7eec73ad4ddbe5a1
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability unit.map.import
```

## The map carries both reviews

```scrut
$ grep -n "kind: refinement" -A 3 curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml | head -n 8
32:      kind: refinement
33-      reviewed_by: probe-operator
34-      reviewed_on: '2026-10-12'
35-      rationale: The placement narrows the route to the worked example.
```

```scrut
$ grep -n "resource-demo-route-mirror" -A 1 curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml | head -n 4 && grep -n "runtime_target:" curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml
57:  - id: resource-demo-route-mirror
58-    kind: read
66:  runtime_target:
```

## Both reviews are current: neither stale nor unverified

```scrut
$ los validate | grep -c "ANGLE-REVIEW-STALE" || true
0
```

```scrut
$ los validate | grep -c "ANGLE-REVIEW-UNVERIFIED" || true
0
```

## Rebuild the generated outputs

```scrut
$ los generate
published generated/manifest.json (atomic contract snapshot)
```

## Changing a description is refused before it can stale the reviews

The warning gate sees both reviews going stale in the shadow state and
refuses the seal; the fingerprints are never merely refreshed.

```scrut
$ (set -o pipefail; $H/los-seal --capability route.patch --payload '{"unit_id": "unit-demo-l01", "route_id": "route-b2f1f80014860a929a3af0bc", "changes": {"angle": "Derives the weighted sum, reworded after review."}}' --key s29-stale --request-id request-s29-stale --guards auto --out "$TMPDIR/s29-stale.json" 2>&1 | cut -d'(' -f1 | sed 's/ $//')
seal_envelope: W NEW-OR-GROWN-WARNING: ANGLE-REVIEW-STALE at curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml: 0 → 2
[2]
```

## The refusal changed nothing: both reviews are still current

```scrut
$ los validate | grep -c "ANGLE-REVIEW-STALE" || true
0
```
