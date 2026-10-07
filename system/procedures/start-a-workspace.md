---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Start a workspace (WORKFLOWS §1)

Executable transcript of opening one workspace: create the skeleton
with its frontmatter and required sections, record one accepted
"not now" deferral with its reasoning, and move `Next Action` only
through the envelope — the bare command is refused and direct editing
stays out. `tests/test_procedures.py` runs it with Scrut; `<REPO>`
comes from the `LOS_REPO` environment variable the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Create the skeleton

```scrut
$ mkdir -p work/active/workspace-scope-triage/scratch work/active/workspace-scope-triage/inputs work/active/workspace-scope-triage/outputs
```

## Write CONTEXT.md with the required sections and one deferral

```scrut
$ cat > work/active/workspace-scope-triage/CONTEXT.md <<'EOF'
> ---
> id: workspace-scope-triage
> type: workspace
> title: Scope triage probe
> created: '2026-10-01'
> status: active
> standing: false
> concepts: []
> notes: []
> sources: []
> ---
>
> ## Objective
>
> Decide what this effort covers before studying it.
>
> ## Current Scope
>
> Required now: the scope question itself.
>
> ## Open Questions
>
> None yet.
>
> ## Next Action
>
> Draft the scope triage.
>
> ## Deferred
>
> - Defer moment-generating functions: helpful later, not now.
> EOF
```

## The skeleton is there

```scrut
$ $H/los-assert-file work/active/workspace-scope-triage/CONTEXT.md --sha256 cba54d4d08467aec8820122c4c58081ad7a676987bbafb844b3e401012e778be
```

```scrut
$ $H/los-assert-file work/active/workspace-scope-triage/scratch --exists
```

```scrut
$ $H/los-assert-file work/active/workspace-scope-triage/inputs --exists
```

```scrut
$ $H/los-assert-file work/active/workspace-scope-triage/outputs --exists
```

## The bare next-action command is refused

```scrut {output_stream: stderr}
$ los workspace-next-action workspace-scope-triage --next-action "Draft the scope triage now."
los: next-action update rejected by validation
canonical writes must use GatewayEnvelopeV2* (glob)
[2]
```

## Seal the Next Action move with derived guards

```scrut {output_stream: stderr}
$ $H/los-seal --capability workspace.next-action.update --payload '{"workspace_id": "workspace-scope-triage", "next_action": "Draft the scope triage now."}' --key scope-next-action --request-id request-scope-next-action --guards auto --out "$TMPDIR/scope-next-action.json"
seal_envelope: guards auto: workspace-scope-triage=0
```

## Submit the envelope

```scrut
$ los capability workspace.next-action.update --payload-file "$TMPDIR/scope-next-action.json"
{
  "schema_version": 2,
  "request_id": "request-scope-next-action",
  "idempotency_key": "scope-next-action",
  "capability": "workspace.next-action.update",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:0c6e406b20537c498c610f6c1deb39749b6528d9a2585ef3d3a31b465cbca872",
  "result": {
    "ok": true,
    "workspace_id": "workspace-scope-triage",
    "path": "work/active/workspace-scope-triage/CONTEXT.md",
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "workspace-scope-triage": 1
    },
    "snapshot_after": "sha256:0c6e406b20537c498c610f6c1deb39749b6528d9a2585ef3d3a31b465cbca872",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability workspace.next-action.update
```

## The Next Action moved, nothing else did

```scrut
$ $H/los-assert-file work/active/workspace-scope-triage/CONTEXT.md --sha256 c53de0447e5bc6f87ed9957ffcede5242eee62040c45faf60289d6cfc1c9891c
```

## The new workspace validates

```scrut
$ los validate | tail -n 1
0 error(s), 9 warning(s) — OK
```
