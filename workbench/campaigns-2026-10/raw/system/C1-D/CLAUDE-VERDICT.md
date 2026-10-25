# Claude's verdict on C1-D (2026-10-24, overnight orchestrator)

C1-D reported two findings. Both tests were re-run on Core `main`
`d6c47790`, in Claude's scratch clone, registered under `gateway`. Both fail
for the documented reason. The copies and the `group_map` edit were removed
afterwards.

Neither finding is urgent. Both are real code defects with one-line fixes,
and neither is practically reachable in Aram's use.

## 1. A file capture can overwrite another capture made in the same second

**CONFIRMED at code level. Low severity. Practically unreachable.**

**What I checked:**
- **The bug.** `handlers/capture.py:109-111` takes one fallback name,
  `{stamp}-{src.name}`, and never checks it again. The text branch a few
  lines below loops `while target.exists()`.
- **The stamp.** It is `observations.now()` to the second
  (`capture.py:92`).
- **Why it overwrites.** The transaction engine writes over an existing path
  by design, and inbox files carry no revision guard. So the third capture
  replaces the second capture's bytes. Confirmed by the test.

**Reachability.** The overwrite needs two file captures with the same
basename to commit within the **same clock second**, while the plain name is
already taken.
- Captures are serialized under the operator lock (C1-B, `app/pipeline.py:241`).
- Each commit runs a full validation, about 3 s on live data per #21. So
  sequential captures cannot share a second.
- GLM's "in-process gateway hosts" case is an ASSUMPTION it did not
  demonstrate. The UI goes through the same gateway commit.
- The test reaches it only by freezing the clock with `LOS_OBSERVATIONS`. In
  production, that override exists for characterization and replay.

So this is real, deterministic under replay, and not reachable in daily use.

**Fix:** reuse the text branch's serial loop for files. One line.

## 2. `material.context` turns `--limit 0` into a page of 20

**CONFIRMED. Minor.**

`handlers/materials.py:1204-1206` passes `req.get("limit") or 20` to
`_window_values`, so an explicit 0 never reaches the 1..20 range check.

Note that the request schema (`material.context.schema.json:175-177`) states
"1 to 20" only in its description, with no `minimum`. So neither the schema
nor the handler refuses 0. The fix belongs in the handler, as GLM suggests,
and could add `minimum: 1` to the schema. A schema edit moves contract
fixtures, so that part belongs with whoever lands the fix.

No caller passes 0 today: the CLI default is 5. The cost is a declared
refusal site that never fires.

## Issues

Drafts C1-D-1 and C1-D-2 are in `ISSUES-DRAFT.md`.

**Recommendation:** file these two together with C1-C-2 as one low-priority
hygiene issue, "write and read guards that disagree", rather than as three
issues.

No duplicates were found for "capture overwrite", "capture.create",
"material.context", "limit 0" or "inbox collision". The hits, #3, #7, #19 and
#20, are unrelated.

## Not verified

The "attacked and held" section. The C1 verification pass (L1-3) owns it.
