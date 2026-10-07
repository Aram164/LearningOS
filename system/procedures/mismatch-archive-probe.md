---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Archive mismatch probe (PARTIAL evidence for M-05, final id)

> **PARTIAL mismatch evidence — NOT complete procedure coverage.** This probe
> exists only to pin the observed behavior behind mismatch M-05 (recorded as
> provisional M-06 before S10 acceptance): an unchanged archive move of a
> path-owning workspace fails validation, and the repaired pointer fails the
> schema instead. It is not a learner workflow, it satisfies no INDEX row —
> the WORKFLOWS §11 row stays untranscribable with no transcript — and its
> fixture moves must never be read as approved writes: no capability moves
> or archives a workspace. Every mutation below is explicitly labeled setup:
> it builds the invalid archived state the validation check then observes.
> `tests/test_procedures.py` runs it with Scrut; `<REPO>` comes from the
> `LOS_REPO` environment variable the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Setup: move the path-owning workspace unchanged

This move is test setup of the invalid archived state, not an approved
learner write: no workspace archive capability exists.

```scrut
$ mkdir -p archive/workspaces/2026 && mv work/active/workspace-demo archive/workspaces/2026/workspace-demo
```

## The move preserved the bytes

```scrut
$ $H/los-assert-file archive/workspaces/2026/workspace-demo/CONTEXT.md --sha256 f7f0a5ad8934e7a2f86c1c91f304954bf07c58899aa0c98d98394076097a3422
```

```scrut
$ $H/los-assert-file work/active/workspace-demo --absent
```

## Capture the pre-validation state

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.fingerprint import canonical_fingerprint; from pathlib import Path; st={"fp": canonical_fingerprint(Path(".")), "rc": sorted(glob.glob("operations/transactions/transaction-*.yaml"))}; json.dump(st, open(os.environ["TMPDIR"]+"/fp-mismatch-validate.json", "w")); print("captured", len(st["rc"]))'
captured 1
```

## The unchanged move fails validation (M-05)

```scrut
$ (set -o pipefail; los validate | tail -n 1)
1 error(s), 10 warning(s) — FAIL
[1]
```

```scrut
$ los validate | grep -c "PATH-NOTE-OWNER"
1
```

```scrut
$ los validate | grep "PATH-NOTE-OWNER"
E PATH-NOTE-OWNER: stage notes_path escapes owning workspace: 'work/active/workspace-demo/paths/stage-demo-path-notes.md' [archive/workspaces/2026/workspace-demo/paths/path-demo.yaml]
```

## Validation wrote nothing

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.fingerprint import canonical_fingerprint; from pathlib import Path; st=json.load(open(os.environ["TMPDIR"]+"/fp-mismatch-validate.json")); fp=canonical_fingerprint(Path(".")); rc=sorted(glob.glob("operations/transactions/transaction-*.yaml")); assert fp==st["fp"], (fp, st["fp"]); assert rc==st["rc"], (rc, st["rc"]); print("unchanged")'
unchanged
```

## Setup: point the notes at the archive (second invalid state)

Setup again: this edit builds the repaired-pointer state the validator
then rejects against the schema. It is not an approved write.

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import yaml; p = "archive/workspaces/2026/workspace-demo/paths/path-demo.yaml"; d = yaml.safe_load(open(p)); [s.update({"notes_path": s["notes_path"].replace("work/active/workspace-demo", "archive/workspaces/2026/workspace-demo")}) for s in d["stages"] if s.get("notes_path")]; open(p, "w").write(yaml.safe_dump(d, sort_keys=False))'
```

## Capture the second pre-validation state

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.fingerprint import canonical_fingerprint; from pathlib import Path; st={"fp": canonical_fingerprint(Path(".")), "rc": sorted(glob.glob("operations/transactions/transaction-*.yaml"))}; json.dump(st, open(os.environ["TMPDIR"]+"/fp-mismatch-validate2.json", "w")); print("captured", len(st["rc"]))'
captured 1
```

## The repaired pointer fails the schema instead

```scrut
$ (set -o pipefail; los validate | tail -n 1)
1 error(s), 10 warning(s) — FAIL
[1]
```

```scrut
$ los validate | grep -c "SCHEMA"
1
```

## The second validation wrote nothing either

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.fingerprint import canonical_fingerprint; from pathlib import Path; st=json.load(open(os.environ["TMPDIR"]+"/fp-mismatch-validate2.json")); fp=canonical_fingerprint(Path(".")); rc=sorted(glob.glob("operations/transactions/transaction-*.yaml")); assert fp==st["fp"], (fp, st["fp"]); assert rc==st["rc"], (rc, st["rc"]); print("unchanged")'
unchanged
```
