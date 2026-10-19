---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Add a concept relation (WORKFLOWS §5)

Executable transcript of registering one relation edge: confirm both
endpoint ids, add the narrowest fitting type with its condition and a
supporting note, and refuse the duplicate. `tests/test_procedures.py`
runs it with Scrut; `<REPO>` comes from the `LOS_REPO` environment
variable the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Confirm both concept ids exist

1. confirm both concept IDs exist;
2. choose the narrowest supported type — if none fits, the relationship belongs in note prose;
3. add optional context if the relationship is conditional;
4. optionally cite a supporting note or source;
5. avoid duplicate edges;
6. rebuild generated outputs.

```scrut
$ los inspect concept-variance concept-expected-value | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print([(r["id"], r["title"]) for r in d["records"]])'
[('concept-variance', 'Variance'), ('concept-expected-value', 'Expected value')]
```

## Seal the edge with derived guards

The narrowest fitting type is `requires`; the condition and the
supporting note ride along.

```scrut {output_stream: stderr}
$ $H/los-seal --capability concept.relations.change --payload '{"change": {"operations": [{"action": "add", "new": {"from": "concept-variance", "type": "requires", "to": "concept-expected-value", "context": "When variance is learned as a second moment.", "source": "note-demo"}}]}}' --key relation-requires --request-id request-relation-requires --guards auto --out "$TMPDIR/relation-requires.json"
seal_envelope: guards auto: registry-concept-relations=0
```

## Submit the envelope

```scrut
$ los capability concept.relations.change --payload-file "$TMPDIR/relation-requires.json"
{
  "schema_version": 2,
  "request_id": "request-relation-requires",
  "idempotency_key": "relation-requires",
  "capability": "concept.relations.change",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:ad2e953300fac8038590dfc59431e1d150b4ea0a2fda4acbf8a34821412ad163",
  "result": {
    "ok": true,
    "operation_count": 1,
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "registry-concept-relations": 1
    },
    "snapshot_after": "sha256:ad2e953300fac8038590dfc59431e1d150b4ea0a2fda4acbf8a34821412ad163",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability concept.relations.change
```

## The registry carries the edge

```scrut
$ $H/los-assert-file knowledge/concept-relations.yaml --sha256 6842ac9c446e6219cf39d800af1781006c6e8bd2d9e8a2a5dfb0226c6f170dba
```

## The receipt owns the edge

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,os,yaml; ds=sorted(glob.glob("operations/transactions/transaction-*.yaml")); xs=[os.path.basename(x) for x in ds]; assert xs==["transaction-20200102-000000-001.yaml", "transaction-20261001-090000-001.yaml"], xs; d=yaml.safe_load(open(ds[-1])); assert d["capability"]=="concept.relations.change", d["capability"]; w={x["path"]: x for x in d.get("writes") or []}; e=w["knowledge/concept-relations.yaml"]; assert e["sha256_after"]=="6842ac9c446e6219cf39d800af1781006c6e8bd2d9e8a2a5dfb0226c6f170dba", e; assert e["created"] is False, e; print("owns", d["id"])'
owns transaction-20261001-090000-001
```

## Capture the pre-refusal state

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.store.fingerprint import canonical_fingerprint; from pathlib import Path; st={"fp": canonical_fingerprint(Path(".")), "rc": sorted(glob.glob("operations/transactions/transaction-*.yaml"))}; json.dump(st, open(os.environ["TMPDIR"]+"/fp-refuse-duplicate.json", "w")); print("captured", len(st["rc"]))'
captured 2
```

## The duplicate edge is refused during seal-time preflight

```scrut {output_stream: stderr}
$ $H/los-seal --capability concept.relations.change --payload '{"change": {"operations": [{"action": "add", "new": {"from": "concept-variance", "type": "requires", "to": "concept-expected-value"}}]}}' --key relation-duplicate --request-id request-relation-duplicate --guards auto --out "$TMPDIR/relation-duplicate.json"
seal_envelope: E REL-DUP: duplicate relation edge ('concept-variance', 'requires', 'concept-expected-value') [knowledge/concept-relations.yaml]; fix the payload and seal again
[2]
```

## The refused preflight produced no envelope

```scrut
$ $H/los-assert-file "$TMPDIR/relation-duplicate.json" --absent
```

## The refused duplicate changed nothing

```scrut
$ $H/los-assert-file knowledge/concept-relations.yaml --sha256 6842ac9c446e6219cf39d800af1781006c6e8bd2d9e8a2a5dfb0226c6f170dba
```

## The refusal added no receipt and moved no canonical byte

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.store.fingerprint import canonical_fingerprint; from pathlib import Path; st=json.load(open(os.environ["TMPDIR"]+"/fp-refuse-duplicate.json")); fp=canonical_fingerprint(Path(".")); rc=sorted(glob.glob("operations/transactions/transaction-*.yaml")); assert fp==st["fp"], (fp, st["fp"]); assert rc==st["rc"], (rc, st["rc"]); print("unchanged")'
unchanged
```

## Rebuild generated outputs

```scrut
$ los generate
published generated/manifest.json (atomic contract snapshot)
```
