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
  "snapshot_after": "sha256:55ca91fdbbaf71fb268d0de99e254dd92c9e249bf3cd18aec7312626d3fac501",
  "result": {
    "ok": true,
    "operation_count": 1,
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "registry-concept-relations": 1
    },
    "snapshot_after": "sha256:55ca91fdbbaf71fb268d0de99e254dd92c9e249bf3cd18aec7312626d3fac501",
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

## The duplicate edge is refused

```scrut {output_stream: stderr}
$ $H/los-seal --capability concept.relations.change --payload '{"change": {"operations": [{"action": "add", "new": {"from": "concept-variance", "type": "requires", "to": "concept-expected-value"}}]}}' --key relation-duplicate --request-id request-relation-duplicate --guards auto --out "$TMPDIR/relation-duplicate.json"
seal_envelope: guards auto: registry-concept-relations=1
```

```scrut
$ los capability concept.relations.change --payload-file "$TMPDIR/relation-duplicate.json"
{
  "schema_version": 2,
  "request_id": "request-relation-duplicate",
  "idempotency_key": "relation-duplicate",
  "capability": "concept.relations.change",
  "ok": false,
  "replayed": false,
  "transaction_id": null,
  "receipt_path": null,
  "snapshot_after": null,
  "result": {},
  "error": {
    "code": "INVALID_REQUEST",
    "message": "transaction failed canonical validation: E REL-DUP: duplicate relation edge ('concept-variance', 'requires', 'concept-expected-value') [knowledge/concept-relations.yaml]",
    "retryable": false,
    "details": {}
  }
}
[2]
```

## The refused duplicate changed nothing

```scrut
$ $H/los-assert-file knowledge/concept-relations.yaml --sha256 6842ac9c446e6219cf39d800af1781006c6e8bd2d9e8a2a5dfb0226c6f170dba
```

## Rebuild generated outputs

```scrut
$ los generate
published generated/manifest.json (atomic contract snapshot)
```
