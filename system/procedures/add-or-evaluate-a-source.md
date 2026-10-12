---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Add or evaluate a source (WORKFLOWS §6)

Executable transcript of taking one paper from find to curated list:
search the registry by title, author, identifier and URL; register it
metadata-only through the intake gateway with discovery provenance;
refuse an intake that smuggles in an evaluation; place its bytes and
attach them with the live hash after the inventory; record the
evaluation; create the curated collection it belongs on (no approved
capability creates a collection, so that file edit runs only in this
disposable transcript fixture); revise one entry `why`; and rebuild.
`tests/test_procedures.py` runs it with Scrut; `<REPO>` comes from the
`LOS_REPO` environment variable the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Search the registry by title: the paper is new

```scrut
$ los search "Bare Essay"
[]
```

```scrut {output_stream: stderr}
$ los search "Bare Essay"
los: no record matches all 2 terms; per-term record hits: bare=0 essay=0
```

## Search by author, identifier and URL before registering

```scrut
$ los search "A. Author" | $LOS_REPO/.venv/bin/python -c 'import json,sys; print([r["id"] for r in json.load(sys.stdin)])'
['source-demo-book']
```

```scrut
$ los inspect source-demo-book | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["id"], d["title"], d["material"])'
source-demo-book Demo Book material://source-demo-book/book.pdf
```

```scrut
$ los search "https://example.com/bare-essay"
[]
```

The paper shares no title, author, identifier or URL with the
registered Demo Book, so a new record is registered instead of reusing
one.

## Review the metadata-only intake

```scrut
$ los source-intake --record '{"records": [{"action": "create", "id": "source-scenario-bare", "partition": "sources.yaml", "title": "Bare Essay", "type": "paper", "discovery": {"observed": "2026-10-01", "basis": [{"kind": "list-entry", "ref": "shelf/probe.md#L3"}], "possible_use": "Probe shelf."}}]}' --check
{
  "ok": true,
  "check": true,
  "records": 1,
  "diff": [
    {
      "id": "source-scenario-bare",
      "action": "create",
      "partition": "sources.yaml",
      "fields": {
        "title": {
          "before": null,
          "after": "Bare Essay"
        },
        "type": {
          "before": null,
          "after": "paper"
        },
        "discovery": {
          "before": null,
          "after": {
            "observed": "2026-10-01",
            "basis": [
              {
                "kind": "list-entry",
                "ref": "shelf/probe.md#L3"
              }
            ],
            "possible_use": "Probe shelf."
          }
        }
      }
    }
  ],
  "diff_sha256": "sha256:a610c3e12a216350d6d776c556f03726e00a9cfc8fbe254039d12a6f6c77e0bd",
  "expected_revisions": {
    "source-scenario-bare": 0
  },
  "artifact_ids": [
    "source-scenario-bare"
  ]
}
```

## Bind the intake diff

```scrut
$ eval "$(los source-intake --record '{"records": [{"action": "create", "id": "source-scenario-bare", "partition": "sources.yaml", "title": "Bare Essay", "type": "paper", "discovery": {"observed": "2026-10-01", "basis": [{"kind": "list-entry", "ref": "shelf/probe.md#L3"}], "possible_use": "Probe shelf."}}]}' --check | $H/los-bind INTAKE_DIFF '$.diff_sha256')" && echo "$INTAKE_DIFF"
sha256:a610c3e12a216350d6d776c556f03726e00a9cfc8fbe254039d12a6f6c77e0bd
```

## Seal the intake with derived guards

```scrut {output_stream: stderr}
$ $H/los-seal --capability source.intake.record --payload "{\"record\": {\"records\": [{\"action\": \"create\", \"id\": \"source-scenario-bare\", \"partition\": \"sources.yaml\", \"title\": \"Bare Essay\", \"type\": \"paper\", \"discovery\": {\"observed\": \"2026-10-01\", \"basis\": [{\"kind\": \"list-entry\", \"ref\": \"shelf/probe.md#L3\"}], \"possible_use\": \"Probe shelf.\"}}]}, \"expected_diff_sha256\": \"$INTAKE_DIFF\"}" --key s06-intake --request-id request-s06-intake --guards auto --out "$TMPDIR/s06-intake.json"
seal_envelope: guards auto: source-scenario-bare=0
```

## Submit the intake

```scrut
$ los capability source.intake.record --payload-file "$TMPDIR/s06-intake.json"
{
  "schema_version": 2,
  "request_id": "request-s06-intake",
  "idempotency_key": "s06-intake",
  "capability": "source.intake.record",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:54ea9fae14453ebf7bdca456df7ac564c6cead45f99c1b6f575da6e5eee732dc",
  "result": {
    "ok": true,
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "source-scenario-bare": 1
    },
    "snapshot_after": "sha256:54ea9fae14453ebf7bdca456df7ac564c6cead45f99c1b6f575da6e5eee732dc",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability source.intake.record
```

## An intake carrying an evaluation is refused

```scrut {output_stream: stderr}
$ los source-intake --record '{"records": [{"action": "create", "id": "source-scenario-eval", "partition": "sources.yaml", "title": "Eval Essay", "type": "paper", "evaluations": [{"level": "introductory"}], "discovery": {"observed": "2026-10-01", "basis": [], "possible_use": "x"}}]}' --check
los: INVALID_REQUEST: source-scenario-eval: field 'evaluations' is outside the intake allowlist (evaluations, topics, material, routes, selections, notes, feedback and observations are never written through intake)
[2]
```

## Observe the placed bytes and the fixture inventory

The essay PDF was pulled into the materials topic tree; the fixture
supplies it at `source-scenario-bare/attached.pdf` with its generated
manifest (the inventory tool itself is bound to the live materials
tree, outside any fixture).

```scrut
$ MAT_SHA=$(sha256sum "$(dirname "$LOS_FX")/materials/source-scenario-bare/attached.pdf" | cut -d' ' -f1) && echo "$MAT_SHA"
61b4d4e33f928a4f6801ae74b3e940e0cfac1285aa4a958d46ce0ae142b49ed6
```

```scrut
$ $H/los-assert-file records/materials-manifest.yaml --exists
```

## The materials plan wants no moves

```scrut
$ $LOS_REPO/.venv/bin/python $LOS_REPO/tools/build_materials_tree.py --materials-root "$(dirname "$LOS_FX")/materials" | grep -E "moves \(|to \(re\)write"
  moves (0)
  SOURCES.md files to (re)write: 0
```

## Review the attach

```scrut
$ cat > "$TMPDIR/attach-record.yaml" <<EOF
> id: source-scenario-bare
> material: material://source-scenario-bare/attached.pdf
> material_sha256: $MAT_SHA
> EOF
```

```scrut
$ eval "$(los source-revise --file "$TMPDIR/attach-record.yaml" --check | $H/los-bind ATTACH_DIFF '$.diff_sha256')" && echo "$ATTACH_DIFF"
sha256:2f478959e6ecde768db3beffe4aa953f658c82c8a00714cc3704afde1cc9248a
```

## Seal the attach with derived guards

```scrut {output_stream: stderr}
$ $H/los-seal --capability source.record.revise --payload "{\"record\": {\"id\": \"source-scenario-bare\", \"material\": \"material://source-scenario-bare/attached.pdf\", \"material_sha256\": \"$MAT_SHA\"}, \"expected_diff_sha256\": \"$ATTACH_DIFF\"}" --key s06-attach --request-id request-s06-attach --guards auto --out "$TMPDIR/s06-attach.json"
seal_envelope: guards auto: source-scenario-bare=1
```

## Submit the attach

```scrut
$ los capability source.record.revise --payload-file "$TMPDIR/s06-attach.json"
{
  "schema_version": 2,
  "request_id": "request-s06-attach",
  "idempotency_key": "s06-attach",
  "capability": "source.record.revise",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-002",
  "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
  "snapshot_after": "sha256:be0077be94a86efd62bc8bf2d899cf20f5f5195e2f391be5d596301c66142aed",
  "result": {
    "ok": true,
    "transaction_id": "transaction-20261001-090000-002",
    "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
    "artifact_revisions": {
      "source-scenario-bare": 2
    },
    "snapshot_after": "sha256:be0077be94a86efd62bc8bf2d899cf20f5f5195e2f391be5d596301c66142aed",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability source.record.revise
```

## Record the evaluation in its explicit final form

```scrut
$ eval "$(los source-revise --record '{"id": "source-scenario-bare", "evaluations": [{"level": "introductory", "roles": ["first-learning"], "strengths": ["short and exact"], "concepts": ["concept-expected-value"]}]}' --check | $H/los-bind EVAL_DIFF '$.diff_sha256')" && echo "$EVAL_DIFF"
sha256:875f78222b721f37e24ca30af4b597c88cfd562df9a283540bc0447df1ab38ec
```

```scrut {output_stream: stderr}
$ $H/los-seal --capability source.record.revise --payload "{\"record\": {\"id\": \"source-scenario-bare\", \"evaluations\": [{\"level\": \"introductory\", \"roles\": [\"first-learning\"], \"strengths\": [\"short and exact\"], \"concepts\": [\"concept-expected-value\"]}]}, \"expected_diff_sha256\": \"$EVAL_DIFF\"}" --key s06-eval --request-id request-s06-eval --guards auto --out "$TMPDIR/s06-eval.json"
seal_envelope: guards auto: source-scenario-bare=2
```

```scrut
$ los capability source.record.revise --payload-file "$TMPDIR/s06-eval.json"
{
  "schema_version": 2,
  "request_id": "request-s06-eval",
  "idempotency_key": "s06-eval",
  "capability": "source.record.revise",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-003",
  "receipt_path": "operations/transactions/transaction-20261001-090000-003.yaml",
  "snapshot_after": "sha256:687488a006b97d8de7f23c8e402c205311ca80b37b3d34805bf5f7b40e8b7805",
  "result": {
    "ok": true,
    "transaction_id": "transaction-20261001-090000-003",
    "receipt_path": "operations/transactions/transaction-20261001-090000-003.yaml",
    "artifact_revisions": {
      "source-scenario-bare": 3
    },
    "snapshot_after": "sha256:687488a006b97d8de7f23c8e402c205311ca80b37b3d34805bf5f7b40e8b7805",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability source.record.revise
```

## Create the curated collection it belongs on

```scrut
$ cat > sources/collections/probe-essays.yaml <<'EOF'
> title: Probe essays
> entries:
> - source: source-scenario-bare
>   group: Probe
>   why: The bare essay under test.
> EOF
```

## The collection validates clean

```scrut
$ (set -o pipefail; los validate | tail -n 1)
0 error(s), 10 warning(s) — OK
```

## Revise one entry why through its gateway

```scrut
$ eval "$(los collection-entry-revise --record '{"collection": "probe-essays", "source": "source-scenario-bare", "why": "The bare essay, examined."}' --check | $H/los-bind ENTRY_DIFF '$.diff_sha256')" && echo "$ENTRY_DIFF"
sha256:2282313ea24c7f43af808416941f8b45aee64af28ce53b58c25356ecad4f0c55
```

```scrut {output_stream: stderr}
$ $H/los-seal --capability collection.entry.revise --payload "{\"record\": {\"collection\": \"probe-essays\", \"source\": \"source-scenario-bare\", \"why\": \"The bare essay, examined.\"}, \"expected_diff_sha256\": \"$ENTRY_DIFF\"}" --key s06-entry --request-id request-s06-entry --guards auto --out "$TMPDIR/s06-entry.json"
seal_envelope: guards auto: collection:probe-essays=0
```

```scrut
$ los capability collection.entry.revise --payload-file "$TMPDIR/s06-entry.json"
{
  "schema_version": 2,
  "request_id": "request-s06-entry",
  "idempotency_key": "s06-entry",
  "capability": "collection.entry.revise",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-004",
  "receipt_path": "operations/transactions/transaction-20261001-090000-004.yaml",
  "snapshot_after": "sha256:530bd7b4f05523d9a620741b55e8eb19fd0eafeb82e51cc43de49c9fd3f42096",
  "result": {
    "ok": true,
    "transaction_id": "transaction-20261001-090000-004",
    "receipt_path": "operations/transactions/transaction-20261001-090000-004.yaml",
    "artifact_revisions": {
      "collection:probe-essays": 1
    },
    "snapshot_after": "sha256:530bd7b4f05523d9a620741b55e8eb19fd0eafeb82e51cc43de49c9fd3f42096",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability collection.entry.revise
```

## Rebuild the source index

```scrut
$ los generate
published generated/manifest.json (atomic contract snapshot)
```

## The index and the rendered collection carry the paper

```scrut
$ grep -n "Bare Essay" generated/source-index.md | head -n 3
13:**B:** [Bare Essay](#bare-essay)
28:### Bare Essay
54:- **Bare Essay** (`source-scenario-bare`) — roles: first-learning — level: introductory — short and exact
```

```scrut
$ grep -n "examined" generated/collections/probe-essays.md
9:  - The bare essay, examined.
```
