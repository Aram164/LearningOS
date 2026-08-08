---
id: workspace-aml-exam-prep
type: workspace
title: AML Klausur prep — 2. Termin track (Blocks K–M + N-style review)
created: '2026-07-16'
status: active
standing: false
concepts:
- concept-perceptron
- concept-kernel-trick
- concept-xor-problem
- concept-neural-network
- concept-backpropagation
- concept-logistic-regression
- concept-cross-entropy
- concept-gradient-descent
notes:
- note-aml-l07-linear-classifiers
- note-aml-l07-exercise-bank
- note-aml-l07-mock-exam
- note-aml-bonusblatt04-solutions
- note-aml-sad-master-wiring
sources:
- source-aml-ss26-lectures
- source-islp
- source-esl
- source-murphy-pml1
- source-csc411-notes
- source-kroese-dsml
- source-mml
- source-cs229-notes
- source-cs229-2022-videos
- source-mit-6036
- source-eecs498
- source-cs231n-notes
- source-cs231n-2017-videos
- source-statquest
- source-3b1b-neural-networks
- source-3b1b-linear-algebra
- source-karpathy-micrograd
- source-rohrer-e2eml
- source-geron-handson
- source-caltech-lfd
- source-ng-coursera
- source-cs4780-homeworks
- source-mit-6034-quizzes
- source-pytorch-tutorials
- source-kelleher-fmlpda
- source-domingos-useful-things
- source-sad-ss26-lectures
- source-goodfellow-dl
- source-d2l
- source-sutton-barto-rl
- source-zacharski-data-mining
program_ids:
- program-bachelors
module_ids:
- module-hu-aml
unit_ids:
- unit-aml-l01
- unit-aml-l02
- unit-aml-l03
- unit-aml-l04
- unit-aml-l05
- unit-aml-l06
- unit-aml-l07
- unit-aml-l08
- unit-aml-l09
- unit-aml-l10
- unit-aml-l11
---

# AML exam prep — 2. Termin

## Objective

Pass the AML Klausur at the 2. Termin (module-hu-aml; 1. Termin skipped per the
plan of record — dates and attempt state in
`curriculum/modules/module-hu-aml/module.yaml`). Work through the remaining
Foundations fast path: F.D1/D5 loose ends, then Blocks I→K→L→M (L05–L11), using
the per-lecture units as study scripts where they exist.

## Current Scope

> **Phase A posture (COORDINATION.md, Aram 2026-07-25): synergy lane, not
> parked.** AMLS is the primary track until its sitting, but AMLS
> content is understood on top of AML foundations, so the AML concepts AMLS
> rests on are studied *together with AMLS now* — the shared hours serve both
> exams. What is deferred is AML **exam-specific** prep, not AML learning.
> (Until 2026-08-08 this section still read "parked until after the AMLS
> sitting", the pre-07-25 rule that COORDINATION.md explicitly superseded.)

*Required now* — the AML foundations AMLS builds on, pulled in on demand from
the AMLS track rather than run as a separate lecture sequence. Concretely:
computation graphs → backprop (unit-aml-l09) behind AMLS L03/L04 rewriting and
fusion; the forward pass and activation material (unit-aml-l08) behind AMLS
hardware and distributed-execution decks. Study these from the AML units when
AMLS reaches them — do not schedule them as their own block yet.

*Helpful now* — passive cross-wires during M2: SaD L11 supplies workflow
and metrics; SaD L15 is the deliberate warm-up for AML L08–L09.

*Defer* — AML **exam-specific** preparation until after the AMLS sitting: the
L07 Mini Plan run, the closed-book mock, and the systematic L05→L11 sweep.
Their plans are ready; this does not move their calendar priority.

*Reference only* — AML L11 is a conditional prior-year RNN plan. The local
2026 archive currently stops at L10, so L11 must not become exam scope
until a current deck or syllabus confirmation appears.

## Open Questions

- 2.-PZ Anmeldung (31.08–10.09) for the 2. Termin — set the reminder.
- Fine-grained sequencing: AMLS sits in the last August slot (confirmed
  2026-07-17), so serious AML hours start right after it — how do they interleave
  with M2 prep through September?

## Next Action

**Now (synergy):** when the AMLS track reaches computation graphs and rewriting
(AMLS L03/L04), study `unit-aml-l09` alongside it rather than skimming the AMLS
deck alone — that is the single highest-shared-value AML block in Phase A.

**After the AMLS sitting, exam-specific prep begins:** run the L07 Mini Plan
(`inputs/AML_L07_Mini_Plan.md`), self-test with `note-aml-l07-mock-exam`
(75 min, closed book), then the L08–L10 sweep. (The sitting date lives in
`curriculum/modules/module-hu-amls/module.yaml` — never restated here.)

## Durable Notes

AML now has individual current study maps for L01–L11. L01 and L08–L10
are grounded in current 2026 decks. L11 preserves the older RNN material
behind a mandatory scope-check stage. The source map includes every local
course asset family, the complete local CS4780 bank, shared books, official
web courses/docs, and explicit off-scope shelf dispositions.

## Deferred

- The systematic L08–L10 sweep remains after L07 and the AMLS sitting; only the
  missing planning work has been completed now. This does not block pulling
  L08/L09 material in early as AMLS synergy (see Current Scope).
- L11 RNN execution is deferred until 2026 scope is confirmed.
- Sutton & Barto remains visible but off-scope for posted AML L01–L10;
  Zacharski is an optional L02 alternative, not a neural-network source.
