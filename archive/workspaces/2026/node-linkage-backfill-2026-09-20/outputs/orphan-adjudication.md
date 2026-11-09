# Coverage audit — orphan adjudication, 10 placements (2026-09-20)

Revision scope: resolve 9 RESOURCE-NODE-ORPHAN warnings plus 1 latent
orphan revealed by the node backfill (exam-prep s13), across 6 units.
Eight are deliberate scaffolding recorded with the new
`node_scaffold_note` resource field (plan_rigor honors non-blank
notes; both resource schemas allow the field); one redundant
placement is removed; one wrong route linkage is dropped. No route
changes, no scope changes, no renumbering. Applied as one
unit-plan-revise revision per unit; this file is the completed audit
each revision references.

## Local

- 6 study maps read whole, with the exact placement rows, stage
  objectives, and sibling placements:
  unit-m2-sad-l02 (EDF row redundant ×3 elsewhere; sampling row
  removed), unit-m2-sad-l04 (UE3 total-probability denominator),
  unit-m2-sad-l06 (StatQuest row stapled to the wrong video route),
  unit-m2-sad-l07 (3 contrast-only references; deck has no
  Geometric lesson), unit-m2-sad-l12 (2 deferral pointers),
  unit-m2-sad-exam-prep (Kelleher Ch 7 optimization groundwork,
  explicitly not neural per §7.6 p.416).
- L04's map carries the co-active session's uncommitted expansion;
  the one-line note edit reads live bytes so their content carries
  forward, and snapshot guards fail closed on any race.
- The L06 video row keeps label/url/locator/angle_detail and loses
  only the wrong route_id + material_ref; schema sanctions routeless
  independent resources ("Independent resources remain valid without
  it"), and preflight arbitrates.

## Linked

- No `route_changes` in any revision: no covers are extended
  (extending would claim teaching the routes explicitly disavow),
  and no placements move across stages. The L02 removal drops one
  redundant row; placements_before/after is reviewed per unit
  (4→3 on the sampling stage only, all else equal).
- 8 notes use the recorded-scaffolding path the warning text
  prescribes; note texts derive from the placements' own angles.

## Completeness

- The unit-m2-sad-exam-prep revision additionally carries that unit's
  15 backfill keys (`knowledge_node_id` per decisions.yaml, same
  directory); keys and note apply atomically because the keys reveal
  the s13 orphan. All other revisions in this package are notes,
  one removal, and one unlink only.
- All 10 warnings mapped 1:1 to a fix; the splice script asserts
  stage-scoped exact-once anchors and YAML validity per unit.
  Amended maps live in `maps/` next to the backfill set; each
  unit's `--check` diff is reviewed before apply.
- No exclusions; no unresolved gaps. Post-apply the validator must
  show 0 STAGE-NODE-UNLINKED and 0 RESOURCE-NODE-ORPHAN, or the
  commit does not happen.
- Commit note: unit-m2-sad-l04/study-map.yaml is intentionally LEFT
  UNCOMMITTED — its diff interleaves the co-active L04 expansion
  (49 hunks) with this package's one-line note, and separating them
  by hunk surgery risks that session's work. The note is applied in
  the worktree (validator-green) and rides with their commit; the
  revision input and receipt below are the audit trail of what the
  gateway consumed.
- Checks: local_inventory_complete, linked_inventory_complete,
  materials_opened_and_content_checked, current_and_prior_scope_reconciled,
  duplicates_and_numbering_checked, exclusions_and_unresolved_gaps_recorded —
  all true as evidenced above.
