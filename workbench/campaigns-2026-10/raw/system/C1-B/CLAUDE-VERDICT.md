# Claude's verdict on C1-B (2026-10-24, overnight orchestrator)

C1-B reported one finding. Its header says GLM-5.3-Flash, but the ZCode chat
("lane 2.3") ran on GLM-5.3.

The reproduction test was re-run on Core `main` `d6c47790`, in Claude's
scratch clone, registered under `studyplan` in `tests/group_map.py`. It fails
as documented, with `assert 'shelving' in []` after a one-of-two partial
apply. The test copy and the `group_map` edit were removed afterwards.

## 1. A partial `review.apply` drops the remainder from the review queue

**CONFIRMED as a state inconsistency. Moderate-to-low severity. No data
damage.**

**What I checked:**
- `tools/learning_os/app/handlers/capture.py:543` sets
  `shelving["state"] = "applied"` unconditionally, whatever the selection.
  It writes no per-item record of what was applied.
- `tools/learning_os/derive/projection/review.py:79` publishes a shelving row
  only while `state == "proposed"`. So any partial apply removes the packet
  from `review_items`.
- **Reachable from the UI.** `obsidian-ui/src/views/shelving-view.ts:245-247`
  gives each item its own checkbox, and "Approve selected changes" sends only
  the checked ids. A partial apply is an ordinary learner gesture, not a
  misuse of the API.
- **Not reached in Aram's tree yet.** All 73 shelving blocks under the live
  `curriculum/` read `state: none`.

**Why it is a defect, not a design choice:** whichever semantics was meant,
the current behaviour is inconsistent.
- **If unselected means "declined":** the remainder should be gone or
  refused. But GLM observed that a later apply of `proposal-beta` succeeds.
- **If unselected means "still pending":** the packet should stay on the
  queue. It disappears instead, and the map claims `applied`.

The contract (`capabilities.yaml`, `review.apply`: "explicit approval",
"selected proposal is atomic") does not decide between the two readings, so
the fix must pick one and state it. GLM's headline, "contract violation",
overstates this. Its measurements are right.

**One more facet, read but not run (ASSUMPTION):** `syncSelection`
(`shelving-view.ts:168-196`) preselects every item whose `selected` is not
`false`, and the handler never clears that flag. If the view still renders
the packet after a partial apply, it preselects the applied item too.
"Approve" would then refuse atomically with `unsafe or existing shelving
destination` until the learner unticks that item.

**Fix:** keep `state: proposed` while unapplied items remain, and mark the
applied items per item. Or make the remainder explicitly declined and refuse
its later apply. Either way, say which in the `review.apply` invariants.
Small change. Not urgent, since no live packet has been shelved yet.

**Issue draft:** `ISSUES-DRAFT.md`, entry C1-B-1. No duplicate found: the
`gh issue list` searches for "shelving", "review.apply" and "review_items"
return only #21, which is unrelated.

## Not verified

The report's "attacked and held" section. Its **read**-labelled items are
GLM's code reading, and the C1 verification pass (L1-2) owns them.
