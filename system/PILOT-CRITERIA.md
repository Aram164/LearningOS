# Pilot Acceptance Criteria (frozen 2026-07-16, before the pilot ran)

The riskiest bet in v3 is that decomposed source evaluations + generated selector views can match the usefulness of the hand-crafted crosswalks and the Master Wiring. These criteria are frozen **before** the pilot to prevent sunk-cost acceptance.

## Method

Answer each question twice: (a) with the legacy documents, (b) with only the migrated v3 pilot (canonical files + generated views + retrieval workflow, legacy files closed). The pilot **passes a question** if the v3 answer is as complete and at least as fast — no opening of legacy files, no multi-hop hunting a legacy doc would have avoided.

## The five questions

**Q1 — Source selection with prerequisites (Master Wiring §1/§2, crosswalk L05 row).**
"I'm starting AML L05 (MLE → cross-entropy). What should I read first for intuition, what for the derivation, and what does SaD already cover so I don't relearn it?"
v3 must answer from: concept relations (`requires`/`derives` around `concept-maximum-likelihood`), source evaluations (first-learning vs. derivation roles), and the generated per-lecture selector view.

**Q2 — Reverse map for the second exam (Master Wiring §1.2).**
"For the SaD side: which AML lectures are twins of SaD 04–10 (probability → inference), and what order should I study the pipeline in?"
v3 must answer from concept relations + the generated views — the pipeline ordering must survive decomposition.

**Q3 — Context reconstruction (philosophy §3.5, the core promise).**
"Have I already worked through the regression connection between SaD and AML? Where, and what was I trying to answer at the time?"
v3 must surface the migrated Regression bridge note with its concepts, sources, and workspace context — without the user recalling any path.

**Q4 — Slide-verified corrections survive (Master Wiring §4).**
"Does AML L07 cover SVMs? Who owns NN regularization, and is batch norm in scope?"
The corrections (L07 has NO SVM; L09 owns NN regularization, NO batch norm) must be retrievable from canonical v3 artifacts — these hard-won facts must not evaporate in decomposition.

**Q5 — Role retrieval for exam prep (SaD crosswalk testing tier).**
"Best exercise and mock-exam material for the SaD half of M2, at Klausur level?"
v3 must answer by role+concept filtering (`exercise-bank`, `mock-exam`) plus source evaluations of the Klausur-tier externals — not by remembering folder names.

## Pass threshold

- **Pass:** 5/5 questions pass, and a spot-check confirms every judgment used in the answers exists in source records or relations (not only in the narrative crosswalk note).
- **Conditional:** 4/5 — fix the failing decomposition, re-test that question before Stage 2.
- **Fail:** ≤3/5 — stop; the evaluation model needs redesign before any full migration.
