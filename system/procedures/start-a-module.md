---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Start a module (WORKFLOWS §18)

Executable transcript of starting the demo module: the module record
exists as one partition with its registration already recorded, so a
second registration is refused rather than minted; no quarantined menu
awaits promotion; one workspace opens for the distinct effort; the
dependency is wired into coordination; and the tree is rebuilt and
validated with the documented commands. `tests/test_procedures.py` runs
it with Scrut; `<REPO>` comes from the `LOS_REPO` environment variable
the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## The module record exists as one partition

1. **Module record first.** Ensure the module has one partition at
   `curriculum/modules/<module-id>/module.yaml` and record registration
   (workflow 10). A merely prospective Master's choice stays quarantined; it is
   not an active `planned` module.
2. **Promote only adopted sources.** If a quarantined menu exists, register only
   resources selected for the confirmed active module. Build its module source
   map with roles, reasons, priority and unit routes; do not promote the whole
   prospective sea.
3. **Open the first workspace(s).** Create one workspace per distinct effort (workflow 1) — not one per module. A combined module examined under a single grade may still be one exam-prep workspace; an independent project gets its own. A course is not a continuous effort, so `standing: false`.
4. **Wire dependencies, if any.** If the new effort waits on or feeds another, record that in `COORDINATION.md` Dependencies (workflow 9). No exam dates here — they live in the owning academic module.
5. **Rebuild and validate** (`.venv/bin/python tools/generate.py`, then `.venv/bin/python tools/validate.py --compact`).

```scrut
$ los inspect module-demo | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["id"], d["title"])'
module-demo Demo Module
```

```scrut
$ ls curriculum/modules/
module-demo
```

## Its registration is already recorded

```scrut
$ los module-list | $LOS_REPO/.venv/bin/python -c 'import json,sys; print([(a["termin"], a["result"]) for m in json.load(sys.stdin) for a in m["attempts"]])'
[(1, 'withdrawn'), (2, 'registered')]
```

## A second registration is refused, never minted twice

```scrut {output_stream: stderr}
$ $H/los-seal --capability module.attempt.record --payload '{"module_id": "module-demo", "termin": 3, "date": "2026-10-12", "result": "registered"}' --key s18-reg --request-id request-s18-reg --guards auto --out "$TMPDIR/s18-reg.json"
seal_envelope: E MOD-REGISTERED: module 'module-demo' attempt[1] is 'registered' but is not the latest attempt [curriculum/modules/module-demo/module.yaml]; fix the payload and seal again
[2]
```

## No quarantined menu awaits promotion

```scrut
$ test ! -e curriculum/quarantine && echo "no quarantine to promote"
no quarantine to promote
```

```scrut
$ grep -n "role: spine" curriculum/modules/module-demo/source-map.yaml
5:  role: spine
```

## Open one workspace for the distinct effort

```scrut
$ mkdir -p work/active/workspace-probe-course/scratch work/active/workspace-probe-course/inputs work/active/workspace-probe-course/outputs && cat > work/active/workspace-probe-course/CONTEXT.md <<'EOF'
> ---
> id: workspace-probe-course
> type: workspace
> title: Probe course effort
> created: 2026-10-12
> status: active
> standing: false
> ---
> ## Objective
>
> Take the probe course.
>
> ## Current Scope
>
> The demo module only.
>
> ## Open Questions
>
> None.
>
> ## Next Action
>
> Attend the first lecture.
> EOF
```

## Wire the dependency into coordination

```scrut
$ eval "$(los inspect coordination | $H/los-bind COORD_SHA '$.content_sha256')" && echo "$COORD_SHA"
sha256:667bbd75392b1acdc610aa249aa5f2fe3d7659603901f415b36eda30fe2b4655
```

```scrut {output_stream: stderr}
$ $H/los-seal --capability coordination.section.revise --payload "{\"section\": \"Dependencies\", \"text\": \"workspace-probe-course waits on module-demo lectures.\", \"expected_content_sha256\": \"$COORD_SHA\"}" --key s18-dep --request-id request-s18-dep --guards auto --out "$TMPDIR/s18-dep.json"
seal_envelope: guards auto: coordination=0
```

```scrut
$ los capability coordination.section.revise --payload-file "$TMPDIR/s18-dep.json"
{
  "schema_version": 2,
  "request_id": "request-s18-dep",
  "idempotency_key": "s18-dep",
  "capability": "coordination.section.revise",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:58186326be6e399bedad1cabe20b2730731e197bbb2e5920edeaee971b5c5f7c",
  "result": {
    "ok": true,
    "section": "Dependencies",
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "coordination": 1
    },
    "snapshot_after": "sha256:58186326be6e399bedad1cabe20b2730731e197bbb2e5920edeaee971b5c5f7c",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability coordination.section.revise
```

## Rebuild and validate with the documented commands

```scrut
$ $LOS_REPO/.venv/bin/python $LOS_REPO/tools/generate.py --root "$LOS_FX" | grep -c "^wrote"
21
```

```scrut
$ $LOS_REPO/.venv/bin/python $LOS_REPO/tools/generate.py --root "$LOS_FX" | tail -n 2
wrote generated/source-index.md
wrote generated/study-plans.md
```

```scrut
$ $LOS_REPO/.venv/bin/python $LOS_REPO/tools/validate.py --root "$LOS_FX" --compact | grep -o "[0-9]* error(s), [0-9]* warning(s) — OK"
0 error(s), 9 warning(s) — OK
```
