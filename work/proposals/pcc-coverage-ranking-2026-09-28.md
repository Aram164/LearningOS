# PCC coverage ranking — which write paths need envelopes, in which order

Date: 2026-09-28. Parent: `intelligence-plane-plan.md` Phase 6; contract:
`system/SEMANTIC-CONTRACT.md` ("Proof-carrying change", "Asymmetric
admission"). Source of the capability inventory: `system/contracts/capabilities.yaml`.

The contract is explicit that PCC today is library machinery plus one
bounded integration — not a universal wrapper. This note ranks every
write path by the semantic risk an unbound agent write carries, so the
next envelope work starts at the top and the never-list stays deliberate.

## Covered today

- `module.plan.import`: Phase B preflight + atomic lineage persistence for
  changed route-`covers` edges (per-claim evidence or refuse). Partial by
  design: structural changes in the same import ride the preflight and
  snapshot guard, not claim binding.

## Never needs envelopes (producer is the ground truth)

`GESTURE_ALLOWLIST` (any channel) — the learner's own record: `learner.observation.append`,
`atlas.question.save`, `capture.create`, `garden.seed.create`, `unit.note.append`,
`unit.source-selection.set`, `stage.progress.update`, `stage.attachment.add`,
`source.feedback.record`, `detour.create`, `detour.resolve`.
`UI_REVIEWED_ALLOWLIST` (`ui` channel only) — the app showed the exact change
before Save/Apply: `concept.relations.change`, `review.prepare`, `review.apply`,
`unit.map.import`, `learner.ability-observation.append`, `ability.candidate.append`.

Mechanical, scratch, and administrative paths (no semantic judgment flows
through them): `path.note.write`, `path.progress.update`, `path.attachment.add`,
`workspace.next-action.update`, `stage.note.write` (compatibility),
`project.create`, `project.update`, `legacy.archive.lock.publish`,
`masters-planning.catalog.update`, `masters-planning.comparison.publish`,
`legacy.job-learning.migrate`, `route.identity.migrate`,
`module.materials.compact` (lossless, reviewed-hash-bound),
`source.intake.record` (metadata-only, approval-bound diff),
`ai-action.delivery.apply` (approved-delivery authority, atomic receipt).

## Ranked TODO (agent-envelope paths into semantic state)

1. **`unit.plan.revise` — first.** Same blast radius as `module.plan.import`
   (routes, covers edges) and it *writes* `operations/transactions/lineage.yaml`,
   but has no Phase B evidence binding. It is the one unbound writer to the
   sidecar. Extending the Phase B preflight to this path closes the largest
   hole with existing machinery.
2. **`unit.material-synthesis.publish` — second, pending one question.** It
   writes whole-dossier route assessments (semantic judgments) under
   whole-dossier approval — but dossier freshness is a lineage claim family,
   and nothing here shows publish emitting lineage records. If it does not,
   dossiers are judged claims without trail. Confirm, then bind or record why not.
3. **`note.revise` — third.** Explicitly reviewed semantic replacement of
   durable notes: existing meaning changes under agent authorship. Approval
   exists; evidence/read-set binding does not.
4. **`route.patch` — fourth.** Bounded to declared descriptive material
   fields with full shadow validation, so the blast radius is small — but it
   is the highest-frequency agent write path into routes, and frequency is
   its own risk.
5. **`note.create`, `note.analysis.save`, `note.analysis.save_batch`,
   `note.evidence.add` — last.** Additive and byte-preserving with
   handler-owned review defaults; nothing existing changes meaning. Envelope
   value here is provenance completeness, not risk.

## Recommendation

Do 1 next (Phase B extension, same pattern as the import path). Fold 2's
question into that work — if publish emits no lineage, that is a second
finding, not a second project. 3–5 are ordered backlog, each a bounded
preflight integration; no new envelope machinery is needed for any of them.
