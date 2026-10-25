# capture.create: a same-second file capture can overwrite an earlier capture's bytes

**Capability:** `capture.create` (handler `capture`, `tools/learning_os/app/handlers/capture.py:87`)
**Test:** `test_same_second_file_capture_overwrite.py` (clone path while hunting:
`tests/test_c1d_capture_file_collision.py`) — fails on base main `d6c47790`.

## Command

Three GatewayEnvelopeV2 `capture.create` calls, each copying a *different*
external file that shares the basename `notes.md`, with a frozen observation
clock (`LOS_OBSERVATIONS={"now": "2026-10-24T12:00:00"}`, the production
override for characterization — it stands in for three calls landing inside
one wall-clock second):

```python
approved_v2_call(root, capability="capture.create",
                 payload={"file": str(src_v1), "file_sha256": ...},
                 artifact_ids=[request_artifact_id("capture.create", key)],
                 idempotency_key=key)   # x3, bytes alpha/beta/gamma
```

## Observed (verbatim pytest tail)

```
E       AssertionError: the third same-second capture of 'notes.md' (rc=0) replaced the bytes of the second capture's file work/inbox/20261024-120000-notes.md; capture.create must never overwrite an earlier capture's bytes (the capability promises the original input is preserved, and the text branch loops for a free name to exactly that end)
E       assert (0 != 0 or b'gamma capture\n' == b'beta capture\n'
FAILED tests/test_c1d_capture_file_collision.py::test_same_second_file_capture_never_overwrites_an_earlier_capture
1 failed in 1.60s
```

The third capture exits 0 and `work/inbox/20261024-120000-notes.md` — the path
the second capture's receipt points at (`"captured": "work/inbox/20261024-120000-notes.md"`)
— now holds the *third* file's bytes.

## Expected

The third capture must refuse (a collision refusal, like every other writer in
this handler), or the second capture's file must still carry the second
capture's bytes.

- `capabilities.yaml`, `capture.create` invariants: "original input is
  preserved"; "external file input is bound to its exact bytes by SHA-256
  before use".
- The handler's own convention everywhere else: the text branch loops for a
  free name (`capture.py:124-127`), `garden.seed.create` loops
  (`capture.py:179-183`), `review.apply` refuses an existing destination
  (`capture.py:527-533`), `inbox.resolve` refuses an archive collision
  ("the archive never overwrites", `capture.py:700-711`).

## Root cause

`tools/learning_os/app/handlers/capture.py:109-111` — the file branch takes
exactly one fallback name and never re-checks it:

```python
target = inbox / src.name
if target.exists():
    target = inbox / f"{stamp}-{src.name}"
```

When `{stamp}-{src.name}` exists too, `target` keeps colliding and the proposal
writes over it. The transaction engine overwrites by design — `run.backups`
captures the current bytes and `_apply` replaces them
(`tools/learning_os/store/transactions.py:1752-1754, 1997-2005`), and inbox
files are not revision-tracked artifacts, so no revision or validator rule
refuses the replacement. The engine's compare-and-undo journal does keep an
after-image hash of the intended bytes, but nothing surfaces the divergence to
the operator; the second capture's receipt simply stops describing the file at
its path.

Reachability without the frozen clock: any two file captures sharing a
basename where the second call lands in the same clock second as the stamped
fallback of an earlier one — trivially reachable for in-process gateway hosts
and scripting loops (one commit is milliseconds; the receipts are
indistinguishable), and deterministic under `LOS_OBSERVATIONS` replay.

## Suggested fix

Give the file branch the same serial collision discipline as the text branch:
loop while the candidate exists, appending `-2`, `-3`, … (or fold the two
branches into one shared free-name helper). One line of intent — "a capture
never overwrites" — holds for both input kinds, and the engine's
existing backup/journal machinery needs no change.
