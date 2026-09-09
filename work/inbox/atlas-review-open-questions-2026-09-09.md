# Atlas review — open questions (2026-09-09)

Pending decisions from the extensive Domain atlas review. Nothing here is
canonical: each item points at its owner file, where the answer lands once
decided. Branch `atals-fix`; merge or drop after resolution.

## 1. Session-start glance: restore or formally retire?

ADR-005 promised every session starts with the whole domain map in view.
That mechanism is gone: the current bootstrap (`system/OPERATOR.md` →
`bootstrap --compact`, built by `compact_bootstrap` in
`tools/learning_os/commands/reads.py`) emits programs/modules/units plus
resume pointer and counts, but no domain map. `system/CLAUDE.md` consults
the atlas only on trigger (lookup bullet, §7 cross-domain reach).

Recon: the `bootstrap-summary` contract is pinned nowhere — no Core test,
no UI decoder — so a ~7-line domain-count block is technically trivial
and breaks no contract. The cost is purely context spent every session.

- Option A: restore the glance in `compact_bootstrap` (kills the
  re-confinement risk ADR-005 was written against).
- Option B: record an ADR accepting trigger-only reach (saves context,
  keeps the risk explicitly).

Leaving it implicit is the worst option — that is the current state.

## 2. `exam-practice-banks` belongs to which domain?

The new `Atlas shelf placement` signal in the health report
names the 33-entry `exam-practice-banks` shelf as unmapped: it renders
under cross-domain today. The math bookshelf description points its drill
volumes there, suggesting mathematics, but shelf placement is a
classification call.

Resolution: add the shelf to `ATLAS_COLLECTION_DOMAIN` in
`tools/learning_os/genout/atlas.py` with the decided domain, rebuild
(`python tools/generate.py`), confirm the health signal goes quiet.

## 3. Push queue is blocked by another session's dirt

Core `main` is ahead of origin with the Phase 1–5 stack, the entrypoint
fix, and the atlas review fixes — plus the UI repo has `9793b5c`.
Pushing is refused by the pre-push hook (clean-tree rule), not by any
verification failure: `make system-check` passes with the dirt present.

Blocking dirt (all pre-existing, none from the atlas work):

- `curriculum/modules/module-hu-m2-statistik-analysis/source-map.yaml`
- `operations/transactions/idempotency.yaml`
- `operations/transactions/revisions.yaml`
- `tests/test_phaseB_prospective_lineage.py`
- `tools/learning_os/commands/module.py`
- `operations/transactions/lineage.yaml` (untracked)
- `operations/transactions/transaction-20260908-213610-001.yaml` (untracked)
- `work/active/workspace-m2-exam-prep/outputs/L09-MIT-bootstrap-evidence-2026-09-08.md` (untracked)

Resolution: the owning session commits or shelves these; then push both
repos. The timestamped transaction file suggests the owner is active —
coordinate before touching.
