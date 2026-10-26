---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Agent plans (OPERATOR)

Executable transcript of the multi-step agent route: a plan with a stable
`session_id`, one fixture capture with an explicit retry key, and a
dependent read that waits for the capture's receipted projection through
the shared readiness service. A single focused read remains a direct
`los` call; this runner is the transport for declared multi-step work,
never a way to skip discovery or review. `tests/test_procedures.py`
runs it with Scrut; `<REPO>` comes from the `LOS_REPO` environment
variable the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Discover the capture capability first

```scrut
$ los capabilities capture.create --json > /dev/null && echo discovered
discovered
```

## Author the plan outside canonical data

```scrut
$ printf '%s' '{"session_id":"agent-plans-transcript-001","on_error":"stop","steps":[{"id":"cap","kind":"log","key":"agent-plan-capture-001","text":"Synthetic fixture capture."},{"id":"boot","argv":["bootstrap","--brief"],"depends_on":["cap"]}]}' > "$LOS_FX/agent-plan.json" && echo authored
authored
```

## Run the plan and summarize its report

```scrut
$ $LOS_REPO/.venv/bin/python $LOS_REPO/tools/agent_run.py "$LOS_FX/agent-plan.json" --root "$LOS_FX" | $LOS_REPO/.venv/bin/python -c "import json,sys; r=json.load(sys.stdin); print(f\"schema={r['schema_version']} ok={r['totals']['ok']}/{r['totals']['steps']}\")"
schema=2 ok=2/2
```

## The newest receipt names the capture capability

```scrut
$ $H/los-assert-receipt --last --capability capture.create
```
