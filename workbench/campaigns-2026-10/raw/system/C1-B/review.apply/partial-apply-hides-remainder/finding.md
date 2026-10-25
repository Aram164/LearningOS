# Finding: a partial `review.apply` hides the unapplied remainder

- **Capability:** `review.apply` (CLI `shelving-apply`), written by
  `review.prepare` (`shelving-prepare`).
- **Batch:** C1-B (families `review`, and the study-map it acts on).
- **Base:** `d6c4779029e366718b71bda158d2aa8f9da1db39` (GitHub `origin/main`).
- **Reproduction:** `tests/test_c1b_shelving_partial_apply.py` in the clone
  (registered in `tests/group_map.py`, group `studyplan`); fails on base.

## The command

```
los capability review.prepare   --payload-file <envelope with two-item items_file>
los capability review.apply     --payload-file <envelope with selected=["proposal-alpha"]>
```

## What I observed, verbatim

1. After `review.prepare` with two items, the study map carries
   `shelving: {state: proposed, items: [proposal-alpha, proposal-beta], …}`
   and `generated/manifest.json` → `review_items` categories are `['shelving']`.
2. After `review.apply` with only `proposal-alpha` selected (rc 0, receipt
   written, `note-probe-a.md` created):

   ```
   shelving state: applied
   items: ['proposal-alpha', 'proposal-beta']        # both items remain, both still selected: true
   review categories AFTER PARTIAL apply: []          # manifest review_items
   ```

3. A later `review.apply` with `selected=["proposal-beta"]`, submitted while
   `state` is already `applied`, **succeeds** (rc 0, ok true) — so the system
   itself treats the remainder as still pending and appliable.
4. Re-applying `proposal-alpha` correctly refuses:
   `los: unsafe or existing shelving destination: knowledge/notes/mathematics/note-probe-a.md`.

The failing pytest on base main:

```
E       AssertionError: after a partial review.apply, the unapplied proposal item
E       (['proposal-alpha', 'proposal-beta']) is still in the packet and appliable, but the
E       manifest's review_items no longer lists the shelving packet
E       assert 'shelving' in []
```

## What I expected, and who says so

- `system/OPERATOR.md` boundary 9: "Shelving is approval-gated. Apply only
  explicitly selected proposal items." Partial apply is the designed case, not
  an error path.
- `system/contracts/capabilities.yaml` (`review.apply`): invariants "explicit
  approval" and "selected proposal is atomic" — the unit of application is the
  selected set, so an unselected item is neither applied nor declined.
- `tools/learning_os/derive/projection/review.py` (module docstring): "Core
  decides which facts currently require a learner decision and publishes
  stable records with an explicit reason and action target." An item the
  system still accepts for application (observed in 3) is a fact awaiting a
  decision; after the partial apply it is published nowhere.
- `system/schema/study-map.schema.json`: the shelving `state` enum ends at
  `applied`; a packet whose items are half-written claiming `applied` is a
  false record of the packet's own state.

Expected: while unapplied items remain in the packet, the decision surface
(`review_items`) still lists the shelving packet — or the packet records the
remainder as declined and refuses its later application. The current middle
(silent, appliable, invisible) is the one reading the contracts rule out.

## Root cause

`tools/learning_os/app/handlers/capture.py:543` — `shelving_apply` sets
`shelving["state"] = "applied"` unconditionally, even when the packet still
contains unselected items; `tools/learning_os/derive/projection/review.py:79`
(`if shelving.get("state") != "proposed": continue`) then drops the queue row.
No per-item applied record is written either (`selected` flags are not
updated), so the map cannot say which items were applied — only filesystem
existence can.

## Suggested fix

In `shelving_apply`, set `state = "applied"` only when every item in the
packet has been applied; while unapplied items remain, keep the packet at
`proposed` (recording the applied subset per item — for example flipping the
existing per-item `selected` flag to an `applied: true` marker — so the queue
row and the packet agree on what is left). Alternatively, if the intended
semantics are that unselected means declined, remove the unselected items at
apply time and refuse their later application — but then the currently
accepted late apply of the remainder (observed in 3) must also refuse, and
that behaviour change should be stated in the capability contract.

## Limits

No canonical corruption: the tree stays validation-clean throughout, and the
destination-exists check blocks double application. The defect is a lost
decision-surface record (and a false `applied` flag), not data damage.
Severity: moderate.
