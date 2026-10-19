---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Carry work across semesters (WORKFLOWS §20)

Executable transcript of the three carry choices: the exam-prep
workspace whose next attempt is still ahead continues with nothing
moving; the spent workspace completes in place and opens a successor
whose predecessor link lives in its body, because a `supersedes:`
frontmatter field is refused by the workspace schema (M-10 in
`tests/architecture/mismatches.yaml` pins the observed refusal; the
decided Phase 5.2 correction links the predecessor in the body); and a
split moves scratch to a second workspace with the split noted in each.
A cross-effort dependency lands in coordination through its envelope.
`tests/test_procedures.py` runs it with Scrut; `<REPO>` comes from the
`LOS_REPO` environment variable the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Continue: the next attempt is still ahead, so nothing moves

```scrut
$ los module-list | $LOS_REPO/.venv/bin/python -c 'import json,sys; print([(a["termin"], a["result"]) for m in json.load(sys.stdin) for a in m["attempts"]])'
[(1, 'withdrawn'), (2, 'registered')]
```

```scrut
$ $H/los-assert-file work/active/workspace-demo/CONTEXT.md --sha256 f7f0a5ad8934e7a2f86c1c91f304954bf07c58899aa0c98d98394076097a3422
```

```scrut
$ grep -n "status: active" work/active/workspace-demo/CONTEXT.md
6:status: active
```

## Complete-and-successor: complete the spent workspace in place

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import yaml; p = "work/active/workspace-second/CONTEXT.md"; t = open(p).read(); head, rest = t.split("---\n")[1:3]; d = yaml.safe_load(head); d["status"] = "complete"; open(p, "w").write("---\n" + yaml.safe_dump(d, sort_keys=False) + "---\n" + rest); print("completed", d["id"])'
completed workspace-second
```

```scrut
$ grep -n "status: complete" work/active/workspace-second/CONTEXT.md
6:status: complete
```

## Open the successor

```scrut
$ mkdir -p work/active/workspace-probe-heir/scratch work/active/workspace-probe-heir/inputs work/active/workspace-probe-heir/outputs && cat > work/active/workspace-probe-heir/CONTEXT.md <<'EOF'
> ---
> id: workspace-probe-heir
> type: workspace
> title: Probe heir
> created: 2026-10-12
> status: active
> notes:
> - note-demo
> ---
> ## Objective
>
> Carry the probe forward.
>
> ## Current Scope
>
> What the old workspace left unfinished.
>
> ## Open Questions
>
> None.
>
> ## Next Action
>
> Resume the probe.
> EOF
```

Durable notes are shared canon already: the successor links the same
note IDs instead of copying them.

## A supersedes frontmatter field is refused (M-10)

```scrut
$ cp work/active/workspace-probe-heir/CONTEXT.md "$TMPDIR/heir-clean.md" && $LOS_REPO/.venv/bin/python -c 'import yaml; p = "work/active/workspace-probe-heir/CONTEXT.md"; t = open(p).read(); head, rest = t.split("---\n")[1:3]; d = yaml.safe_load(head); d["supersedes"] = ["workspace-second"]; open(p, "w").write("---\n" + yaml.safe_dump(d, sort_keys=False) + "---\n" + rest); print("supersedes added")'
supersedes added
```

```scrut
$ (set -o pipefail; los validate | tail -n 1)
1 error(s), 10 warning(s) — FAIL
[1]
```

```scrut
$ los validate | grep "supersedes"
E SCHEMA: workspace: Additional properties are not allowed ('supersedes' was unexpected) (at root) [work/active/workspace-probe-heir/CONTEXT.md]
```

## Link the predecessor in the successor body instead

```scrut
$ cp "$TMPDIR/heir-clean.md" work/active/workspace-probe-heir/CONTEXT.md && printf '\nSuccessor of workspace-second.\n' >> work/active/workspace-probe-heir/CONTEXT.md && tail -n 3 work/active/workspace-probe-heir/CONTEXT.md
Resume the probe.

Successor of workspace-second.
```

```scrut
$ (set -o pipefail; los validate | tail -n 1)
0 error(s), 10 warning(s) — OK
```

## Split: move the relevant scratch and note it in each

```scrut
$ echo "split half" > work/active/workspace-demo/scratch/split-candidate.txt && mv work/active/workspace-demo/scratch/split-candidate.txt work/active/workspace-probe-heir/scratch/split-candidate.txt && ls work/active/workspace-probe-heir/scratch/
split-candidate.txt
```

```scrut
$ printf '\nSplit on 2026-10-12: scratch moved to workspace-probe-heir.\n' >> work/active/workspace-demo/CONTEXT.md && printf '\nSplit on 2026-10-12: scratch received from workspace-demo.\n' >> work/active/workspace-probe-heir/CONTEXT.md && tail -n 1 work/active/workspace-demo/CONTEXT.md && tail -n 1 work/active/workspace-probe-heir/CONTEXT.md
Split on 2026-10-12: scratch moved to workspace-probe-heir.
Split on 2026-10-12: scratch received from workspace-demo.
```

```scrut
$ (set -o pipefail; los validate | tail -n 1)
0 error(s), 10 warning(s) — OK
```

## Record the cross-effort dependency in coordination

```scrut
$ eval "$(los inspect coordination | $H/los-bind COORD_SHA '$.content_sha256')" && echo "$COORD_SHA"
sha256:667bbd75392b1acdc610aa249aa5f2fe3d7659603901f415b36eda30fe2b4655
```

```scrut {output_stream: stderr}
$ $H/los-seal --capability coordination.section.revise --payload "{\"section\": \"Dependencies\", \"text\": \"workspace-probe-heir waits on workspace-demo scratch.\", \"expected_content_sha256\": \"$COORD_SHA\"}" --key s20-dep --request-id request-s20-dep --guards auto --out "$TMPDIR/s20-dep.json"
seal_envelope: guards auto: coordination=0
```

```scrut
$ los capability coordination.section.revise --payload-file "$TMPDIR/s20-dep.json"
{
  "schema_version": 2,
  "request_id": "request-s20-dep",
  "idempotency_key": "s20-dep",
  "capability": "coordination.section.revise",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:63361fd36775cba316e3d403836468f2807649f25d970426cd2be1b4852073e4",
  "result": {
    "ok": true,
    "section": "Dependencies",
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "coordination": 1
    },
    "snapshot_after": "sha256:63361fd36775cba316e3d403836468f2807649f25d970426cd2be1b4852073e4",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability coordination.section.revise
```
