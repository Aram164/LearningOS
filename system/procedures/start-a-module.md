---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Start a module (WORKFLOWS §18)

Executable transcript of starting the demo module mid-flight: the one
partition and its current registration check out with nothing new to
record, no quarantined menu exists to promote, the start opens its
workspace with course standing, wires the exam dependency, and
rebuilds and validates with the documented tools. `tests/test_procedures.py`
runs it with Scrut; `<REPO>` comes from the `LOS_REPO` environment
variable the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## The module has one partition with its registration current

```scrut
$ $H/los-assert-file curriculum/modules/module-demo/module.yaml --exists
```

```scrut
$ los inspect module-demo | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print([(a["termin"], a["result"]) for a in d["attempts"]])'
[(1, 'withdrawn'), (2, 'registered')]
```

## No quarantined menu exists to promote

```scrut
$ $H/los-assert-file curriculum/quarantine --absent
```

## Open the start workspace

```scrut
$ mkdir -p work/active/workspace-module-launch/scratch work/active/workspace-module-launch/inputs work/active/workspace-module-launch/outputs
```

```scrut
$ cat > work/active/workspace-module-launch/CONTEXT.md <<'EOF'
> ---
> id: workspace-module-launch
> type: workspace
> title: Module launch
> created: '2026-10-01'
> status: active
> standing: false
> concepts: []
> notes: []
> sources: []
> module_ids:
> - module-demo
> ---
>
> ## Objective
>
> Launch the demo module.
>
> ## Current Scope
>
> Registration, workspace, and dependencies.
>
> ## Open Questions
>
> None yet.
>
> ## Next Action
>
> Wire the exam dependency.
> EOF
```

## A course is not a continuous effort

```scrut
$ grep "^standing:" work/active/workspace-module-launch/CONTEXT.md
standing: false
```

```scrut
$ $H/los-assert-file work/active/workspace-module-launch/CONTEXT.md --sha256 5279c5bcafdafc0b22dbef472fd4bc15fa25bee36dddc55208fb1110f64ede1d
```

## Wire the exam dependency

```scrut
$ eval "$(los inspect coordination | $H/los-bind LAUNCH_SHA '$.content_sha256')" && echo "$LAUNCH_SHA"
sha256:667bbd75392b1acdc610aa249aa5f2fe3d7659603901f415b36eda30fe2b4655
```

```scrut {output_stream: stderr}
$ $H/los-seal --capability coordination.section.revise --payload "{\"section\": \"Dependencies\", \"text\": \"- Module launch blocks on the 2. Termin sitting (date lives in module-demo).\", \"expected_content_sha256\": \"$LAUNCH_SHA\"}" --key launch-dep --request-id request-launch-dep --guards auto --out "$TMPDIR/launch-dep.json"
seal_envelope: guards auto: coordination=0
```

```scrut
$ los capability coordination.section.revise --payload-file "$TMPDIR/launch-dep.json"
{
  "schema_version": 2,
  "request_id": "request-launch-dep",
  "idempotency_key": "launch-dep",
  "capability": "coordination.section.revise",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:1a10049c07c5561e8babcd8fb77d512647421e40a512ca7f196bc47675b2be48",
  "result": {
    "ok": true,
    "section": "Dependencies",
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "coordination": 1
    },
    "snapshot_after": "sha256:1a10049c07c5561e8babcd8fb77d512647421e40a512ca7f196bc47675b2be48",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability coordination.section.revise
```

## The dependency is wired

```scrut
$ $H/los-assert-file work/COORDINATION.md --sha256 801196c02d06b553118307724b3ae33aefa10ea9d04517a726aee34337d60d81
```

## Rebuild with the documented tool

```scrut
$ $LOS_REPO/.venv/bin/python $LOS_REPO/tools/generate.py --root "$LOS_FX" | grep -c "^wrote "
21
```

## Validate with the documented tool

```scrut
$ $LOS_REPO/.venv/bin/python $LOS_REPO/tools/validate.py --root "$LOS_FX" --compact | tail -n 1 | sed 's/ (.*//'
0 error(s), 9 warning(s) — OK
```
