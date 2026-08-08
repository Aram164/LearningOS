---
id: coordination
type: coordination
---

# Coordination

## Commitments

- Bachelor thesis "Exploring & optimizing MLE agents for medical use cases" scoped 2026-07-20; workspace-thesis-mle-medical created (landscape survey + exploration/optimization plan in its outputs/). No registration or deadline facts yet — when the thesis is formally registered those go in `curriculum/modules/module-project-bachelor-thesis/module.yaml`. Priority resolved 2026-07-25 (Aram): the exam spine takes precedence through the autumn cluster, with thesis research woven into any slack, and the thesis becomes the primary effort after the M2 Klausur — see Priorities below.

## Priorities

Planning decision 2026-07-25 (revised same day per Aram's notes), covering the run to the autumn exam cluster. Work is a fixed ~2 days/week; the other ~5 days carry study. **The exams are the super-priority — AMLS, AML and M2 (Algo 2 dropped, see Deferrals).** Thesis research is woven into every gap, never at the cost of the next exam, and becomes the primary effort once M2 is written.

Guiding move (Aram, 2026-07-25): **AMLS and AML are studied as one synergy track.** AMLS sits first, but its content is best understood on top of the AML foundations, so the AML concepts AMLS builds on are learned *together* with AMLS rather than parked — the shared study serves both exams. Dedicated AML exam-specific prep (mocks, L07 Mini Plan) intensifies after the AMLS sitting; M2 runs as its own strong parallel track the whole way, because "study super well for Math-2" is an explicit goal, not a Phase-C scramble.

Phased focus (every exam date, sitting and registration window lives in the owning `curriculum/modules/<module-id>/module.yaml` — never here, never in `records/modules.yaml`):

1. **Phase A — now → the AMLS sitting: AMLS-primary (AML-synergy) + M2 steady.** Drive workspace-amls-exam-prep (S.X track) as the imminent exam, pulling in the AML foundations it rests on (e.g. computation graphs → backprop, AML L09) so AMLS is understood deeply and AML is already warm. In parallel, keep a steady M2 track running (AN.0 refresh + SaD L02 onward). Thesis reading fills slack.
2. **Admin gate — the 2.-PZ Anmeldung window (window in each owning `module.yaml`):** register AML and M2 for the 2. Prüfungszeitraum. (Algo 2 not registered — dropped.) Non-negotiable window.
3. **Phase B — after the AMLS sitting → the AML 2. Termin: AML-primary + M2 ramps.** With the AML base already warm from Phase A, do AML exam-specific prep (L07 Mini Plan + closed-book mock). M2 ramps toward full intensity. Thesis in gaps.
4. **Phase C — AML written → the M2 Klausur: M2 all-in.** After the AML 2. Termin, everything flips to M2 for the final stretch — a strong finish built on the steady track, not a cram.
5. **Phase D — after the M2 Klausur: thesis becomes primary.** Exam spine clear; the thesis research phase (WiSe 26/27) moves to the front. Formal registration + deadlines go in `curriculum/modules/module-project-bachelor-thesis/module.yaml` when known.

## Dependencies

- workspace-amls-exam-prep ⇄ workspace-aml-exam-prep are studied as one synergy track (Aram, 2026-07-25): the AML foundations AMLS builds on are learned alongside AMLS in Phase A; AML exam-specific prep (mocks, L07 Mini Plan) intensifies after the AMLS sitting. Supersedes the earlier hard "AML parked until AMLS is written".

## Deferrals

- M2 Klausur deferred to 2. Termin (decision 2026-07-16; Rücktritt executed, confirmed 2026-07-17; the date lives in `curriculum/modules/module-hu-m2-statistik-analysis/module.yaml`)
- AML Klausur deferred to 2. Termin (plan of record since KW 24; Rücktritt executed, confirmed 2026-07-17; attempt state and dates live in `curriculum/modules/module-hu-aml/module.yaml`)
- AMLS exam moved off the first sitting; the LAST course-run slot chosen 2026-07-17 (registered attempt and date live in `curriculum/modules/module-hu-amls/module.yaml`)
- Algo 2 dropped from the autumn cycle (Aram, 2026-07-25): not sitting the 2.-PZ oral, not registering in the Anmeldung window, no study time allocated. The module record stays `enrolled` in `curriculum/modules/module-hu-algo2/module.yaml` (no formal Abmeldung recorded); workspace-algo2-exam-prep set to `blocked`. Reversible — say the word to reinstate it or to record a formal withdrawal.
