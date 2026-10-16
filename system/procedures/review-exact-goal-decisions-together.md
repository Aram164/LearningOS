---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Review exact goal decisions together (WORKFLOWS §30)

Executable transcript of deciding several explicit goal ids as one
reviewed batch: preview the before/after decisions, refuse the
malformed batches, and apply the exact reviewed hash. The single-id
sidecar needs no hash; the batch refuses without it. Decisions land in the goal ledger through the transaction service (PLAN D8).
Each successful decision has a committed goal.decision.record receipt and
caller-session membership. The goal ledger remains outside CANONICAL_ROOTS;
previews and refusals leave both the ledger and receipt set unchanged.
Notes below are synthetic fixed inputs. `tests/test_procedures.py`
runs it with Scrut; `<REPO>` comes from the `LOS_REPO` environment
variable the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Preview one deferral with its revisit date

```scrut
$ los goal goal-demo-deferred --defer --note "Synthetic: revisit after the sitting." --revisit-on 2026-11-01 --check
{"ok": true, "check": true, "reviewed_sha256": "sha256:b2487f16d1387f582284fafc8dd587f21004442d8257e6bf9d54e0fe69770e0b", "goal_ids": ["goal-demo-deferred"], "state": "deferred", "changes": [{"goal_id": "goal-demo-deferred", "before": {"state": "deferred", "decided_at": "2026-09-20"}, "after": {"state": "deferred", "decided_at": "2026-10-01", "revisit_on": "2026-11-01", "note": "Synthetic: revisit after the sitting."}}]}
```

## The ledger is a non-canonical sidecar

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.store.fingerprint import CANONICAL_ROOTS; p="operations/goal-ledger.yaml"; assert not any(p==b or p.startswith(b+"/") for b in CANONICAL_ROOTS), CANONICAL_ROOTS; print("sidecar")'
sidecar
```

## Capture the pre-refusal state

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.store.fingerprint import canonical_fingerprint; from pathlib import Path; st={"fp": canonical_fingerprint(Path(".")), "rc": sorted(glob.glob("operations/transactions/transaction-*.yaml"))}; json.dump(st, open(os.environ["TMPDIR"]+"/fp-refuse-checks.json", "w")); print("captured", len(st["rc"]))'
captured 1
```

## An unknown id refuses before anything is written

```scrut {output_stream: stderr}
$ los goal goal-demo-deferred goal-nope --close --note "Synthetic batch." --check
los: INVALID_REQUEST: goal not found: goal-nope
[2]
```

## A near miss suggests the decidable ids

```scrut {output_stream: stderr}
$ los goal goal-demo-defered --close --note "Synthetic batch." --check
los: INVALID_REQUEST: goal not found: goal-demo-defered (did you mean: goal-demo-deferred, goal-demo-rejected?)
[2]
```

## Duplicate ids are refused

```scrut {output_stream: stderr}
$ los goal goal-demo-deferred goal-demo-deferred --close --note "Synthetic batch." --check
los: INVALID_REQUEST: supply distinct exact goal ids, each one whitespace-free token; patterns are refused
[2]
```

## Patterns are refused

```scrut {output_stream: stderr}
$ los goal goal-demo-deferred goal-* --close --note "Synthetic batch." --check
los: INVALID_REQUEST: supply distinct exact goal ids, each one whitespace-free token; patterns are refused
[2]
```

## A revisit date needs a deferral

```scrut {output_stream: stderr}
$ los goal goal-demo-deferred --close --note "Synthetic batch." --revisit-on 2026-11-01 --check
los: INVALID_REQUEST: --revisit-on requires --defer
[2]
```

## The preview refusals added no receipt and moved no canonical byte

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.store.fingerprint import canonical_fingerprint; from pathlib import Path; st=json.load(open(os.environ["TMPDIR"]+"/fp-refuse-checks.json")); fp=canonical_fingerprint(Path(".")); rc=sorted(glob.glob("operations/transactions/transaction-*.yaml")); assert fp==st["fp"], (fp, st["fp"]); assert rc==st["rc"], (rc, st["rc"]); print("unchanged")'
unchanged
```

## Capture the pre-apply state

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.store.fingerprint import canonical_fingerprint; from pathlib import Path; st={"fp": canonical_fingerprint(Path(".")), "rc": sorted(glob.glob("operations/transactions/transaction-*.yaml"))}; json.dump(st, open(os.environ["TMPDIR"]+"/fp-apply-single.json", "w")); print("captured", len(st["rc"]))'
captured 1
```

## Decide the single deferral without a hash

```scrut
$ los goal goal-demo-deferred --defer --note "Synthetic: revisit after the sitting." --revisit-on 2026-11-01
{"ok": true, "state": "deferred", "goal_id": "goal-demo-deferred", "revisit_on": "2026-11-01"}
```

## The deferral landed in the goal ledger

```scrut
$ $H/los-assert-file operations/goal-ledger.yaml --sha256 0df6bbeb7215c8e22c20cf93b5d76541c384c353d996773c17102d5098edc533
```

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import yaml; d = yaml.safe_load(open("operations/goal-ledger.yaml")); g = d["decisions"]["goal-demo-deferred"]; print(g["state"], g["decided_at"], g["revisit_on"], g["note"])'
deferred 2026-10-01 2026-11-01 Synthetic: revisit after the sitting.
```

## The single apply has its exact receipt and session membership

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,hashlib,json,os,sys,yaml; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.store.fingerprint import canonical_fingerprint; from learning_os.store.session_ledger import session_ledger as _session_ledger; from pathlib import Path; st=json.load(open(os.environ["TMPDIR"]+"/fp-apply-single.json")); root=Path("."); assert canonical_fingerprint(root)==st["fp"]; rc=sorted(glob.glob("operations/transactions/transaction-*.yaml")); added=sorted(set(rc)-set(st["rc"])); assert len(added)==1 and set(st["rc"])<=set(rc), (rc,st["rc"]); d=yaml.safe_load(open(added[0])); assert d["capability"]=="goal.decision.record" and d["status"]=="committed"; w=d["writes"]; assert len(w)==1 and w[0]["path"]=="operations/goal-ledger.yaml" and w[0]["sha256_after"]=="0df6bbeb7215c8e22c20cf93b5d76541c384c353d996773c17102d5098edc533"; assert d["artifact_revisions"]=={"file:operations/goal-ledger.yaml":{"before":0,"after":1}}; s=json.load(open(_session_ledger(root,"channel:operator"))); assert s["session_id"]=="channel:operator"; expected={"operations/goal-ledger.yaml","operations/transactions/revisions.yaml","operations/transactions/idempotency.yaml",added[0]}; assert set(s["paths"])==expected, s["paths"]; assert all(row["sha256"]==hashlib.sha256(Path(path).read_bytes()).hexdigest() for path,row in s["paths"].items()); print("canonical unchanged; goal receipt and session verified")'
canonical unchanged; goal receipt and session verified
```

## Preview the closing batch

```scrut
$ los goal goal-demo-deferred goal-demo-rejected --close --note "Synthetic: close both together." --check
{"ok": true, "check": true, "reviewed_sha256": "sha256:2ebf1e0a838bd72ebf65539b9520a0ba5f4aaba3e6a8ca329048bb7fabf7b3f2", "goal_ids": ["goal-demo-deferred", "goal-demo-rejected"], "state": "closed", "changes": [{"goal_id": "goal-demo-deferred", "before": {"state": "deferred", "decided_at": "2026-10-01", "revisit_on": "2026-11-01", "note": "Synthetic: revisit after the sitting."}, "after": {"state": "closed", "decided_at": "2026-10-01", "note": "Synthetic: close both together."}}, {"goal_id": "goal-demo-rejected", "before": {"state": "rejected", "decided_at": "2026-09-20"}, "after": {"state": "closed", "decided_at": "2026-10-01", "note": "Synthetic: close both together."}}]}
```

## Capture the pre-apply-refusal state

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.store.fingerprint import canonical_fingerprint; from pathlib import Path; st={"fp": canonical_fingerprint(Path(".")), "rc": sorted(glob.glob("operations/transactions/transaction-*.yaml"))}; json.dump(st, open(os.environ["TMPDIR"]+"/fp-refuse-apply.json", "w")); print("captured", len(st["rc"]))'
captured 2
```

## A changed proposal refuses without a write

```scrut {output_stream: stderr}
$ los goal goal-demo-deferred goal-demo-rejected --close --note "Synthetic: close both together." --reviewed-sha256 sha256:0000000000000000000000000000000000000000000000000000000000000000
los: INVALID_REQUEST: batch apply needs the exact --check reviewed-sha256; changed ledger or decisions require a fresh review
[3]
```

## The refused apply wrote nothing, ledger included

```scrut
$ $H/los-assert-file operations/goal-ledger.yaml --sha256 0df6bbeb7215c8e22c20cf93b5d76541c384c353d996773c17102d5098edc533
```

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.store.fingerprint import canonical_fingerprint; from pathlib import Path; st=json.load(open(os.environ["TMPDIR"]+"/fp-refuse-apply.json")); fp=canonical_fingerprint(Path(".")); rc=sorted(glob.glob("operations/transactions/transaction-*.yaml")); assert fp==st["fp"], (fp, st["fp"]); assert rc==st["rc"], (rc, st["rc"]); print("unchanged")'
unchanged
```

## Capture the pre-batch-apply state

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.store.fingerprint import canonical_fingerprint; from pathlib import Path; st={"fp": canonical_fingerprint(Path(".")), "rc": sorted(glob.glob("operations/transactions/transaction-*.yaml"))}; json.dump(st, open(os.environ["TMPDIR"]+"/fp-apply-batch.json", "w")); print("captured", len(st["rc"]))'
captured 2
```

## Apply the reviewed batch into the session

```scrut
$ los goal goal-demo-deferred goal-demo-rejected --close --note "Synthetic: close both together." --reviewed-sha256 sha256:2ebf1e0a838bd72ebf65539b9520a0ba5f4aaba3e6a8ca329048bb7fabf7b3f2 --session-id session-goal-batch
{"ok": true, "state": "closed", "goal_ids": ["goal-demo-deferred", "goal-demo-rejected"]}
```

## Both closures landed in the goal ledger

```scrut
$ $H/los-assert-file operations/goal-ledger.yaml --sha256 d91597aecf699167c6ada305f12b4cc7ffad7be8b5e62cfc50d8721a5148980d
```

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import yaml; d = yaml.safe_load(open("operations/goal-ledger.yaml")); [print(g, d["decisions"][g]["state"], d["decisions"][g]["decided_at"]) for g in ("goal-demo-deferred", "goal-demo-rejected")]'
goal-demo-deferred closed 2026-10-01
goal-demo-rejected closed 2026-10-01
```

## The batch apply has its exact receipt and session membership

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,hashlib,json,os,sys,yaml; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.store.fingerprint import canonical_fingerprint; from learning_os.store.session_ledger import session_ledger as _session_ledger; from pathlib import Path; st=json.load(open(os.environ["TMPDIR"]+"/fp-apply-batch.json")); root=Path("."); assert canonical_fingerprint(root)==st["fp"]; rc=sorted(glob.glob("operations/transactions/transaction-*.yaml")); added=sorted(set(rc)-set(st["rc"])); assert len(added)==1 and set(st["rc"])<=set(rc), (rc,st["rc"]); d=yaml.safe_load(open(added[0])); assert d["capability"]=="goal.decision.record" and d["status"]=="committed"; w=d["writes"]; assert len(w)==1 and w[0]["path"]=="operations/goal-ledger.yaml" and w[0]["sha256_after"]=="d91597aecf699167c6ada305f12b4cc7ffad7be8b5e62cfc50d8721a5148980d"; assert d["artifact_revisions"]=={"file:operations/goal-ledger.yaml":{"before":1,"after":2}}; s=json.load(open(_session_ledger(root,"session-goal-batch"))); assert s["session_id"]=="session-goal-batch"; expected={"operations/goal-ledger.yaml","operations/transactions/revisions.yaml","operations/transactions/idempotency.yaml",added[0]}; assert set(s["paths"])==expected, s["paths"]; assert all(row["sha256"]==hashlib.sha256(Path(path).read_bytes()).hexdigest() for path,row in s["paths"].items()); print("canonical unchanged; goal receipt and session verified")'
canonical unchanged; goal receipt and session verified
```

## Validate the decided goals

```scrut
$ los validate | tail -n 1
0 error(s), 10 warning(s) — OK
```
