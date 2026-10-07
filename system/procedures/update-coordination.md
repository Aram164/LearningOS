---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Update coordination (WORKFLOWS §9)

Executable transcript of revising one coordination section: read the
current digest, review the check diff, and apply the reviewed text
with the previous content hash through the envelope. A stale digest
is refused. Exam dates, workspace statuses, and workspace lists stay
out of the revised bytes; the attempt half of a stated operational
fact belongs to the module-event transcript. `tests/test_procedures.py`
runs it with Scrut; `<REPO>` comes from the `LOS_REPO` environment
variable the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Read the current content digest

```scrut
$ eval "$(los inspect coordination | $H/los-bind COORD_SHA '$.content_sha256')" && echo "$COORD_SHA"
sha256:667bbd75392b1acdc610aa249aa5f2fe3d7659603901f415b36eda30fe2b4655
```

## Review the check diff without a digest

```scrut
$ los coordination-section-revise Commitments --text "Ship the demo module plan." --check
{"ok": true, "section": "Commitments", "before": "(none)", "after": "Ship the demo module plan.", "expected_content_sha256": "sha256:667bbd75392b1acdc610aa249aa5f2fe3d7659603901f415b36eda30fe2b4655", "expected_snapshot": "sha256:a1f5b7e982c2422aa062ca45388337743ed3d47e16d7b161f7d1b656e948e400", "expected_revisions": {"coordination": 0}, "write_paths": ["work/COORDINATION.md"]}
```

## A stale digest is refused

```scrut {output_stream: stderr}
$ $H/los-seal --capability coordination.section.revise --payload '{"section": "Commitments", "text": "Ship the demo module plan.", "expected_content_sha256": "sha256:0000000000000000000000000000000000000000000000000000000000000000"}' --key coord-stale --request-id request-coord-stale --guards auto --out "$TMPDIR/coord-stale.json"
seal_envelope: los: placeholder content digest sha256:0000000000000000000000000000000000000000000000000000000000000000; the current content digest is sha256:667bbd75392b1acdc610aa249aa5f2fe3d7659603901f415b36eda30fe2b4655 (read it with `inspect coordination`); fix the payload and seal again
[2]
```

## Seal the revision with derived guards

```scrut {output_stream: stderr}
$ $H/los-seal --capability coordination.section.revise --payload "{\"section\": \"Commitments\", \"text\": \"Ship the demo module plan.\", \"expected_content_sha256\": \"$COORD_SHA\"}" --key coord-commit --request-id request-coord-commit --guards auto --out "$TMPDIR/coord-commit.json"
seal_envelope: guards auto: coordination=0
```

## Submit the revision

```scrut
$ los capability coordination.section.revise --payload-file "$TMPDIR/coord-commit.json"
{
  "schema_version": 2,
  "request_id": "request-coord-commit",
  "idempotency_key": "coord-commit",
  "capability": "coordination.section.revise",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "sha256:6110e49500e20c02cf2ea463fe39a0aa48a3c4965453260f9ad579c2fa97f35b",
  "result": {
    "ok": true,
    "section": "Commitments",
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "coordination": 1
    },
    "snapshot_after": "sha256:6110e49500e20c02cf2ea463fe39a0aa48a3c4965453260f9ad579c2fa97f35b",
    "replayed": false
  },
  "error": null
}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability coordination.section.revise
```

## The section carries the reviewed text

```scrut
$ $H/los-assert-file work/COORDINATION.md --sha256 5c20c95f5bcf31885ccd7f27971830187db355d74ea760d706571818960571ab
```
