---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Revise an existing plan (WORKFLOWS §25a)

Executable transcript of plan revision at three scopes: the bounded
single-field patch (edit context, preflight, envelope apply, and the
identity-change refusal), the content-preserving compaction, and the
structural creation/import path (a module package, compact route
operations, and one unit map — each drafted outside the repository,
reviewed as a diff, preflighted from the CLI with zero canonical
writes, and applied through the gateway). The assembler refuses the
fixture batch, so the drafts below are edited copies; the closing
sections run a byte-identical copy of the hand-edit audit tool
against a disposable git history built from the fixture's real plan
and receipt files. `tests/test_procedures.py` runs it with Scrut;
`<REPO>` comes from the `LOS_REPO` environment variable the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## The assembler refuses the fixture batch

The whole-batch refusal is why the drafts below are edited copies:
the second unit's stage has no concept coverage.

```scrut
$ $LOS_REPO/.venv/bin/python $LOS_REPO/tools/assemble_lecture_study_maps.py --root "$LOS_FX" --out "$TMPDIR/asm-out"
unit-demo-l02: 1 stages, 1 resource rows
[2]
```

```scrut {output_stream: stderr}
$ $LOS_REPO/.venv/bin/python $LOS_REPO/tools/assemble_lecture_study_maps.py --root "$LOS_FX" --out "$TMPDIR/asm-out"
assembly preflight failed; no draft files were written
- unit-demo-l02 stage has no concept coverage: stage-demo-variance
[2]
```

## Start from the named route's edit context

```scrut
$ los plan-edit-context unit-demo-l01 --route-id route-b2f1f80014860a929a3af0bc | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["contract"], d["unit_id"]); print(d["route"]["id"], d["route"]["title"]); print(d["patch_capability"])'
plan-edit-context unit-demo-l01
route-b2f1f80014860a929a3af0bc Demo book — expected-value derivation
route.patch
```

## Preflight the bounded patch: concrete diff, zero writes

```scrut
$ los route-patch unit-demo-l01 route-b2f1f80014860a929a3af0bc --changes '{"angle": "Probe revision angle."}' --check | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["ok"], d["check"], d["canonical_files_written"]); print(json.dumps(d["changes"]["angle"], sort_keys=True)); print(d["affected_files"]); print(json.dumps(d["expected_revisions"], sort_keys=True))'
True True 0
{"after": "Probe revision angle.", "before": "Derives the weighted sum and works a discrete example."}
['curriculum/modules/module-demo/source-map.yaml', 'curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml']
{"module-demo": 0, "study-map-demo-l01": 0, "unit-demo-l01": 3}
```

## Seal the patch with derived guards

```scrut {output_stream: stderr}
$ $H/los-seal --capability route.patch --payload '{"unit_id": "unit-demo-l01", "route_id": "route-b2f1f80014860a929a3af0bc", "changes": {"angle": "Probe revision angle."}}' --key s25a-patch --request-id request-s25a-patch --guards auto --out "$TMPDIR/s25a-patch.json"
seal_envelope: guards auto: module-demo=0, study-map-demo-l01=0, unit-demo-l01=3
```

## Apply the patch through the gateway

```scrut
$ los capability route.patch --payload-file "$TMPDIR/s25a-patch.json"
{
  "schema_version": 2,
  "request_id": "request-s25a-patch",
  "idempotency_key": "s25a-patch",
  "capability": "route.patch",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:a9c72cf9e3b7931366d122d9b768c5424b0af2a878f7acf614e29dcac93fa107",
  "result": {
    "schema_version": 1,
    "unit_id": "unit-demo-l01",
    "route_id": "route-b2f1f80014860a929a3af0bc",
    "changes": {
      "angle": {
        "before": "Derives the weighted sum and works a discrete example.",
        "after": "Probe revision angle."
      }
    },
    "plan_sha256": "sha256:b34bbc807f64b2d5be4e9dc9c2d26cefa9254f1ff41b8e0521c0499ed567f963",
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
    "snapshot_after": "sha256:a9c72cf9e3b7931366d122d9b768c5424b0af2a878f7acf614e29dcac93fa107",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability route.patch
```

## The route carries the revised angle

```scrut
$ grep -n "Probe revision angle" curriculum/modules/module-demo/source-map.yaml
13:    angle: Probe revision angle.
```

## An identity change is refused: that needs the full plan path

```scrut {output_stream: stderr}
$ los route-patch unit-demo-l01 route-b2f1f80014860a929a3af0bc --changes '{"source_id": "source-demo-book"}' --check
los: INVALID_REQUEST: changes must contain nonempty text for declared material fields only
[2]
```

## Preflight the content-preserving compaction

```scrut
$ los module-materials-compact module-demo --check | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["ok"], d["check"], d["canonical_files_written"]); print(d["plan_sha256"]); print(d["affected_files"]); print(json.dumps(d["expected_revisions"], sort_keys=True))'
True True 0
sha256:74fb4986cb287354311feea050fcdc0b8940c9d8ca3ecdc930f0d149c9909e93
['curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml']
{"module-demo": 1, "study-map-demo-l01": 1, "unit-demo-l01": 4}
```

## Seal the compaction with its plan hash

```scrut
$ eval "$(los module-materials-compact module-demo --check | $H/los-bind COMPACT_PLAN '$.plan_sha256')" && echo "$COMPACT_PLAN"
sha256:74fb4986cb287354311feea050fcdc0b8940c9d8ca3ecdc930f0d149c9909e93
```

```scrut {output_stream: stderr}
$ $H/los-seal --capability module.materials.compact --payload "{\"module_id\": \"module-demo\", \"plan_sha256\": \"$COMPACT_PLAN\"}" --key s25a-compact --request-id request-s25a-compact --guards auto --out "$TMPDIR/s25a-compact.json"
seal_envelope: guards auto: module-demo=1, study-map-demo-l01=1, unit-demo-l01=4
```

```scrut
$ los capability module.materials.compact --payload-file "$TMPDIR/s25a-compact.json"
{
  "schema_version": 2,
  "request_id": "request-s25a-compact",
  "idempotency_key": "s25a-compact",
  "capability": "module.materials.compact",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-002",
  "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
  "snapshot_after": "sha256:2eb7147f5155b668071986528d228ac247495c7450fd340b411fbfdf7e3d3f60",
  "result": {
    "schema_version": 1,
    "module_id": "module-demo",
    "map_bytes_saved": 2,
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
    "snapshot_after": "sha256:2eb7147f5155b668071986528d228ac247495c7450fd340b411fbfdf7e3d3f60",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability module.materials.compact
```

## Draft the module package outside the repository

```scrut
$ cat > "$TMPDIR/package.yaml" <<'EOF'
> module_id: module-demo
> plan_contract:
>   version: 2
>   plan_template_version: 1
>   coverage_audit: work/active/workspace-demo/outputs/demo-coverage-audit.md
>   checks:
>     local_inventory_complete: true
>     linked_inventory_complete: true
>     materials_opened_and_content_checked: true
>     current_and_prior_scope_reconciled: true
>     duplicates_and_numbering_checked: true
>     exclusions_and_unresolved_gaps_recorded: true
> module_patch:
>   title: Reviewed demo module
> units: []
> EOF
```

## Preflight the module package from the CLI

```scrut
$ los module-plan-import module-demo --file "$TMPDIR/package.yaml" --check | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["ok"], d["mode"]); print(d["package_sha256"]); print(d["affected_files"]); print(json.dumps(d["expected_revisions"], sort_keys=True))'
True check
sha256:3fa14a571e7e2bc0255f12f604ecef674cd854d5a70b0d9ed35b7f4825b5943b
['curriculum/modules/module-demo/module.yaml']
{"module-demo": 2}
```

## Seal the module import with derived guards

```scrut {output_stream: stderr}
$ PKG_SHA=$(sha256sum "$TMPDIR/package.yaml" | cut -d' ' -f1) && $H/los-seal --capability module.plan.import --payload "{\"module_id\": \"module-demo\", \"file\": \"$TMPDIR/package.yaml\", \"file_sha256\": \"sha256:$PKG_SHA\"}" --key s25a-imp --request-id request-s25a-imp --guards auto --out "$TMPDIR/s25a-imp.json"
seal_envelope: guards auto: module-demo=2
```

```scrut
$ los capability module.plan.import --payload-file "$TMPDIR/s25a-imp.json"
{
  "schema_version": 2,
  "request_id": "request-s25a-imp",
  "idempotency_key": "s25a-imp",
  "capability": "module.plan.import",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-003",
  "receipt_path": "operations/transactions/transaction-20261001-090000-003.yaml",
  "snapshot_after": "sha256:2c7442e0c1cb5004479d9b6d5c9a5b267a76f36cad2d9227f7e96b6a74a90a37",
  "result": {
    "ok": true,
    "mode": "apply",
    "module_id": "module-demo",
    "units_written": [],
    "files_written": 1,
    "transaction_id": "transaction-20261001-090000-003",
    "receipt_path": "operations/transactions/transaction-20261001-090000-003.yaml",
    "artifact_revisions": {
      "module-demo": 3
    },
    "snapshot_after": "sha256:2c7442e0c1cb5004479d9b6d5c9a5b267a76f36cad2d9227f7e96b6a74a90a37",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability module.plan.import
```

## The module carries the reviewed title

```scrut
$ grep -n "Reviewed demo module" curriculum/modules/module-demo/module.yaml
6:title: Reviewed demo module
```

## Preflight the compact route operation

```scrut
$ los unit-plan-revise unit-demo-l01 --record '{"unit_id": "unit-demo-l01", "plan_contract": {"version": 1, "plan_template_version": 1, "coverage_audit": "work/active/workspace-demo/outputs/demo-coverage-audit.md", "checks": {"local_inventory_complete": true, "linked_inventory_complete": true, "materials_opened_and_content_checked": true, "current_and_prior_scope_reconciled": true, "duplicates_and_numbering_checked": true, "exclusions_and_unresolved_gaps_recorded": true}}, "route_changes": {"update": [{"route_id": "route-b2f1f80014860a929a3af0bc", "fields": {"angle_detail": "A reviewed detailed probe angle."}}]}}' --check | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["ok"], d["mode"]); print(d["affected_files"]); print(json.dumps(d["expected_revisions"], sort_keys=True))'
True check
['curriculum/modules/module-demo/source-map.yaml']
{"module-demo": 3}
```

## Seal the unit revision with derived guards

```scrut {output_stream: stderr}
$ $H/los-seal --capability unit.plan.revise --payload '{"unit_id": "unit-demo-l01", "record": {"unit_id": "unit-demo-l01", "plan_contract": {"version": 1, "plan_template_version": 1, "coverage_audit": "work/active/workspace-demo/outputs/demo-coverage-audit.md", "checks": {"local_inventory_complete": true, "linked_inventory_complete": true, "materials_opened_and_content_checked": true, "current_and_prior_scope_reconciled": true, "duplicates_and_numbering_checked": true, "exclusions_and_unresolved_gaps_recorded": true}}, "route_changes": {"update": [{"route_id": "route-b2f1f80014860a929a3af0bc", "fields": {"angle_detail": "A reviewed detailed probe angle."}}]}}}' --key s25a-rev --request-id request-s25a-rev --guards auto --out "$TMPDIR/s25a-rev.json"
seal_envelope: guards auto: module-demo=3
```

```scrut
$ los capability unit.plan.revise --payload-file "$TMPDIR/s25a-rev.json"
{
  "schema_version": 2,
  "request_id": "request-s25a-rev",
  "idempotency_key": "s25a-rev",
  "capability": "unit.plan.revise",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-004",
  "receipt_path": "operations/transactions/transaction-20261001-090000-004.yaml",
  "snapshot_after": "sha256:ec8d7e1ec190a76fc19e27ea436e4b7c41a2e8b2f4cdd105d1f1e51bd05ebbd3",
  "result": {
    "ok": true,
    "mode": "apply",
    "module_id": "module-demo",
    "units_written": [
      "unit-demo-l01"
    ],
    "files_written": 1,
    "transaction_id": "transaction-20261001-090000-004",
    "receipt_path": "operations/transactions/transaction-20261001-090000-004.yaml",
    "artifact_revisions": {
      "module-demo": 4
    },
    "snapshot_after": "sha256:ec8d7e1ec190a76fc19e27ea436e4b7c41a2e8b2f4cdd105d1f1e51bd05ebbd3",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability unit.plan.revise
```

## The route carries the reviewed detail

```scrut
$ grep -n "reviewed detailed probe angle" curriculum/modules/module-demo/source-map.yaml
20:    angle_detail: A reviewed detailed probe angle.
```

## Draft the unit map outside the repository

```scrut
$ cat > "$TMPDIR/map-l02.yaml" <<'EOF'
> id: study-map-demo-l02
> type: study-map
> plan_template_version: 1
> unit_id: unit-demo-l02
> status: ready
> current_stage: stage-variance
> source_plan:
>   path: work/active/workspace-demo/CONTEXT.md
>   provenance: operator
> detours: []
> stages:
> - id: stage-variance
>   number: 1
>   title: Variance
>   status: pending
>   objective: Build working fluency in Variance.
>   done_when:
>   - Explain and apply Variance without notes.
>   exam_critical: false
>   concepts: []
>   scope_triage: required-now
>   resources: []
>   working_note: curriculum/modules/module-demo/units/unit-demo-l02/stages/stage-variance/notes.md
>   attachments: []
>   source_feedback: []
> shelving:
>   state: none
> EOF
```

## Preflight the unit map from the CLI

```scrut
$ los unit-map-import unit-demo-l02 --file "$TMPDIR/map-l02.yaml" --check | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["ok"], d["mode"], d["canonical_files_written"]); print(d["file_sha256"]); print(json.dumps(d["expected_revisions"], sort_keys=True))'
True check 0
sha256:a57d3fbba9289d145fa4e7a52ea906b011531f38cc0278121f867cb12eff14d4
{"study-map-demo-l02": 0, "unit-demo-l02": 0}
```

## Seal the unit map import with derived guards

```scrut {output_stream: stderr}
$ MAP_SHA=$(sha256sum "$TMPDIR/map-l02.yaml" | cut -d' ' -f1) && $H/los-seal --capability unit.map.import --payload "{\"unit_id\": \"unit-demo-l02\", \"file\": \"$TMPDIR/map-l02.yaml\", \"file_sha256\": \"sha256:$MAP_SHA\"}" --key s25a-map --request-id request-s25a-map --guards auto --out "$TMPDIR/s25a-map.json"
seal_envelope: guards auto: study-map-demo-l02=0, unit-demo-l02=0
```

```scrut
$ los capability unit.map.import --payload-file "$TMPDIR/s25a-map.json"
{
  "schema_version": 2,
  "request_id": "request-s25a-map",
  "idempotency_key": "s25a-map",
  "capability": "unit.map.import",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-005",
  "receipt_path": "operations/transactions/transaction-20261001-090000-005.yaml",
  "snapshot_after": "sha256:fc8aea7181e334d023a6092d1f7a52d00600b38571bd62f0aff4367a0a346351",
  "result": {
    "ok": true,
    "mode": "apply",
    "unit_id": "unit-demo-l02",
    "study_map_id": "study-map-demo-l02",
    "diff": {
      "replacement": false,
      "unit_status": "ready",
      "stages_after": [
        "stage-variance"
      ],
      "content_changes": [
        {
          "stage_id": "stage-variance",
          "field": "concepts",
          "before": null,
          "after": []
        },
        {
          "stage_id": "stage-variance",
          "field": "done_when",
          "before": null,
          "after": [
            "Explain and apply Variance without notes."
          ]
        },
        {
          "stage_id": "stage-variance",
          "field": "exam_critical",
          "before": null,
          "after": false
        },
        {
          "stage_id": "stage-variance",
          "field": "number",
          "before": null,
          "after": 1
        },
        {
          "stage_id": "stage-variance",
          "field": "objective",
          "before": null,
          "after": "Build working fluency in Variance."
        },
        {
          "stage_id": "stage-variance",
          "field": "resources",
          "before": null,
          "after": []
        },
        {
          "stage_id": "stage-variance",
          "field": "scope_triage",
          "before": null,
          "after": "required-now"
        },
        {
          "stage_id": "stage-variance",
          "field": "title",
          "before": null,
          "after": "Variance"
        }
      ],
      "map_changes": [
        {
          "field": "plan_template_version",
          "before": null,
          "after": 1
        },
        {
          "field": "source_plan",
          "before": null,
          "after": {
            "path": "work/active/workspace-demo/CONTEXT.md",
            "provenance": "operator"
          }
        },
        {
          "field": "type",
          "before": null,
          "after": "study-map"
        },
        {
          "field": "unit_id",
          "before": null,
          "after": "unit-demo-l02"
        }
      ]
    },
    "transaction_id": "transaction-20261001-090000-005",
    "receipt_path": "operations/transactions/transaction-20261001-090000-005.yaml",
    "artifact_revisions": {
      "study-map-demo-l02": 1,
      "unit-demo-l02": 1
    },
    "snapshot_after": "sha256:fc8aea7181e334d023a6092d1f7a52d00600b38571bd62f0aff4367a0a346351",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability unit.map.import
```

## The unit carries its first study map

```scrut
$ $H/los-assert-file curriculum/modules/module-demo/units/unit-demo-l02/study-map.yaml --exists
```

## The revised plans validate and regenerate

```scrut
$ (set -o pipefail; los validate | tail -n 1)
0 error(s), 9 warning(s) — OK
```

```scrut
$ los generate
published generated/manifest.json (atomic contract snapshot)
```

## Copy the hand-edit audit into a disposable pair

`tools/plan_write_audit.py` anchors the inspected repository to its
own file location, so a byte-identical copy audits wherever it is
placed. The helper copies only the entrypoint and refuses any
destination outside the transcript `TMPDIR`.

```scrut
$ mkdir -p "$TMPDIR/audit-pair/repo" && export AUDIT_REPO="$(realpath "$TMPDIR/audit-pair/repo")" && $H/los-anchored-copy plan_write_audit "$AUDIT_REPO"
sha256:d58cbf1bdd8de190aea7e3497287afd89c8dfb815b6ba42c792ebc14488ef286 tools/plan_write_audit.py
```

## Commit the fixture's real plans and receipts

The first commit carries every plan record and every transaction
receipt the gateway wrote above; the second is a labeled fixture
hand-edit with no receipt, the control the audit must catch. Only
the plan tree and the receipts copy over — the diagnostics traces
beside them vary per run. Identity and dates are fixed, but the two
file-import envelopes carry their draft's absolute run-temporary
path, so their intent hashes — and the receipts and ledger rows
recording them — vary per run, and the commit hashes vary with them.
Subjects, dates and counts pin the history instead.

```scrut
$ mkdir -p "$AUDIT_REPO/operations" && cp -R curriculum "$AUDIT_REPO/curriculum" && cp -R operations/transactions "$AUDIT_REPO/operations/transactions" && git -C "$AUDIT_REPO" init --quiet -b main . && git -C "$AUDIT_REPO" config user.name Fixture && git -C "$AUDIT_REPO" config user.email fixture@local && git -C "$AUDIT_REPO" add -A && GIT_AUTHOR_DATE="2026-10-01T09:00:00+02:00" GIT_COMMITTER_DATE="2026-10-01T09:00:00+02:00" git -C "$AUDIT_REPO" commit --quiet -m "gateway plan revisions with receipts"
```

```scrut
$ printf '%s\n' '# fixture hand-edit: an unmediated plan touch for the audit demo' >> "$AUDIT_REPO/curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml" && git -C "$AUDIT_REPO" add -A && GIT_AUTHOR_DATE="2026-10-02T09:00:00+02:00" GIT_COMMITTER_DATE="2026-10-02T09:00:00+02:00" git -C "$AUDIT_REPO" commit --quiet -m "hand-edit one study map without a receipt"
```

## The fixture history holds one mediated and one bare plan commit

```scrut
$ git -C "$AUDIT_REPO" log --format=%s
hand-edit one study map without a receipt
gateway plan revisions with receipts
```

## Audit the fixture history with the copied entrypoint

Nine files sit under `operations/transactions/`: the five new
receipts, the three fixture records, and the gateway idempotency
ledger the applies wrote.

```scrut
$ $LOS_REPO/.venv/bin/python $AUDIT_REPO/tools/plan_write_audit.py
commits that changed a plan record : 2
  carrying a transaction receipt   : 1 (50%)
  with no receipt in the same commit: 1

receipts on disk                   : 9

Run with --list to see which commits those were.

A commit without a receipt is not automatically a defect — migrations
under tools/migrations/ and the assembler's reviewed drafts are
legitimate. What the number measures is how much of the plan surface
changed outside the one path that leaves evidence.
```

```scrut
$ $LOS_REPO/.venv/bin/python $AUDIT_REPO/tools/plan_write_audit.py --list | sed -E "s/^  [0-9a-f]{7,} ([0-9]{4}-[0-9]{2}-[0-9]{2}) /  <hash> \1 /"
commits that changed a plan record : 2
  carrying a transaction receipt   : 1 (50%)
  with no receipt in the same commit: 1

receipts on disk                   : 9

off-gateway commits, newest first:
  <hash> 2026-10-02 hand-edit one study map without a receipt

A commit without a receipt is not automatically a defect — migrations
under tools/migrations/ and the assembler's reviewed drafts are
legitimate. What the number measures is how much of the plan surface
changed outside the one path that leaves evidence.
```

## The audit bound to the fixture repository

```scrut
$ grep '^REPO =' $AUDIT_REPO/tools/plan_write_audit.py && [ "$(git -C "$AUDIT_REPO" rev-parse --show-toplevel)" = "$AUDIT_REPO" ] && echo "audit history lives under the pair"
REPO = Path(__file__).resolve().parents[1]
audit history lives under the pair
```
