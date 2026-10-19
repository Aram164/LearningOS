---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Start a workspace (WORKFLOWS §1)

Executable transcript of opening one workspace: create the skeleton with
the documented frontmatter, observe that an unspecified `deadline:`
fails validation (M-09 in `tests/architecture/mismatches.yaml` pins the
observed refusal; the decided Phase 5.2 correction omits it), validate
clean without the line, trip the eight-active-workspace warning, and
update `Next Action` through its capability envelope — never by editing
`CONTEXT.md` directly. `tests/test_procedures.py` runs it with Scrut;
`<REPO>` comes from the `LOS_REPO` environment variable the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Create the skeleton with the documented frontmatter

```scrut
$ mkdir -p work/active/workspace-probe/scratch work/active/workspace-probe/inputs work/active/workspace-probe/outputs && cat > work/active/workspace-probe/CONTEXT.md <<'EOF'
> ---
> id: workspace-probe
> type: workspace
> title: Probe workspace
> created: 2026-10-12
> status: active
> standing: false
> concepts: []
> notes: []
> sources: []
> deadline:
> ---
> ## Objective
>
> Probe.
>
> ## Current Scope
>
> Required now: the skeleton. Defer: none yet.
>
> ## Open Questions
>
> None.
>
> ## Next Action
>
> Do the probe thing.
>
> ## Deferred
>
> - Second workspace: not now, one probe is enough.
> EOF
```

## Capture the pre-validation state

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.store.fingerprint import canonical_fingerprint; from pathlib import Path; st={"fp": canonical_fingerprint(Path(".")), "rc": sorted(glob.glob("operations/transactions/transaction-*.yaml"))}; json.dump(st, open(os.environ["TMPDIR"]+"/fp-s01-validate.json", "w")); print("captured", len(st["rc"]))'
captured 1
```

## An unspecified deadline fails validation (M-09)

The skeleton above keeps the `deadline:` line the doc shows with no
non-exam deadline supplied; the validator refuses the null, and the
decided correction (M-09) is to omit the line.

```scrut
$ (set -o pipefail; los validate | tail -n 1)
1 error(s), 10 warning(s) — FAIL
[1]
```

```scrut
$ los validate | grep "SCHEMA"
E SCHEMA: workspace: None is not of type 'string' (at deadline) [work/active/workspace-probe/CONTEXT.md]
```

## Validation wrote nothing

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.store.fingerprint import canonical_fingerprint; from pathlib import Path; st=json.load(open(os.environ["TMPDIR"]+"/fp-s01-validate.json")); fp=canonical_fingerprint(Path(".")); rc=sorted(glob.glob("operations/transactions/transaction-*.yaml")); assert fp==st["fp"], (fp, st["fp"]); assert rc==st["rc"], (rc, st["rc"]); print("unchanged")'
unchanged
```

## Omit the unspecified deadline

```scrut
$ cat > work/active/workspace-probe/CONTEXT.md <<'EOF'
> ---
> id: workspace-probe
> type: workspace
> title: Probe workspace
> created: 2026-10-12
> status: active
> standing: false
> concepts: []
> notes: []
> sources: []
> ---
> ## Objective
>
> Probe.
>
> ## Current Scope
>
> Required now: the skeleton. Defer: none yet.
>
> ## Open Questions
>
> None.
>
> ## Next Action
>
> Do the probe thing.
>
> ## Deferred
>
> - Second workspace: not now, one probe is enough.
> EOF
```

## The skeleton validates clean

```scrut
$ (set -o pipefail; los validate | tail -n 1)
0 error(s), 10 warning(s) — OK
```

## Eight active workspaces trip the warning

```scrut
$ for w in north east south west central; do mkdir -p work/active/workspace-probe-$w/scratch work/active/workspace-probe-$w/inputs work/active/workspace-probe-$w/outputs; printf -- '---\nid: workspace-probe-%s\ntype: workspace\ntitle: Probe %s\ncreated: 2026-10-12\nstatus: active\n---\n\n## Objective\n\nProbe %s.\n\n## Current Scope\n\nSmall.\n\n## Open Questions\n\nNone.\n\n## Next Action\n\nProbe.\n' "$w" "$w" "$w" > work/active/workspace-probe-$w/CONTEXT.md; done && ls work/active | wc -l | tr -d ' '
8
```

```scrut
$ los validate | grep "WS-COUNT"
W WS-COUNT: 8 non-standing active workspaces (target 3-7; finish or archive something first)
```

## Seal the Next Action update with derived guards

```scrut {output_stream: stderr}
$ $H/los-seal --capability workspace.next-action.update --payload '{"workspace_id": "workspace-probe", "next_action": "Probe the next thing."}' --key ws-na-001 --request-id request-ws-na-001 --guards auto --out "$TMPDIR/ws-na.json"
seal_envelope: guards auto: workspace-probe=0
```

## Submit the update

```scrut
$ los capability workspace.next-action.update --payload-file "$TMPDIR/ws-na.json"
{
  "schema_version": 2,
  "request_id": "request-ws-na-001",
  "idempotency_key": "ws-na-001",
  "capability": "workspace.next-action.update",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:e7b08c32190ee58ca4a1f43539cdeb09c61070fbbe4c34b477fffb956e939563",
  "result": {
    "ok": true,
    "workspace_id": "workspace-probe",
    "path": "work/active/workspace-probe/CONTEXT.md",
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "workspace-probe": 1
    },
    "snapshot_after": "sha256:e7b08c32190ee58ca4a1f43539cdeb09c61070fbbe4c34b477fffb956e939563",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability workspace.next-action.update
```

## The workspace carries the new Next Action

```scrut
$ grep -A 2 "## Next Action" work/active/workspace-probe/CONTEXT.md
## Next Action

Probe the next thing.
```
