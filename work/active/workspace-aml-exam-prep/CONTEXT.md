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
- concept-softmax
- concept-convolutional-networks
- concept-residual-connection
- concept-transformer
- concept-attention
- concept-contextual-embedding
- concept-embedding
- concept-tokenization
- concept-positional-encoding
- concept-layer-normalization
- concept-language-modelling
notes:
- note-aml-l07-linear-classifiers
- note-aml-l07-exercise-bank
- note-aml-l07-mock-exam
- note-aml-l08-feedforward-networks
- note-aml-l08-exercise-bank
- note-aml-l08-mock-exam
- note-aml-l09-backpropagation
- note-aml-l09-exercise-bank
- note-aml-l09-mock-exam
- note-aml-l10-cnn
- note-aml-l10-exercise-bank
- note-aml-l10-mock-exam
- note-aml-l11-transformers
- note-aml-l11-exercise-bank
- note-aml-l11-mock-exam
- note-aml-bonusblatt04-solutions
- note-aml-sad-master-wiring
sources:
- source-3b1b-linear-algebra
- source-3b1b-neural-networks
- source-aml-ss26-lectures
- source-caltech-lfd
- source-cs229-2022-videos
- source-cs229-notes
- source-cs231n-2017-videos
- source-cs231n-notes
- source-cs4780-homeworks
- source-csc411-notes
- source-d2l
- source-domingos-useful-things
- source-eecs498
- source-esl
- source-geron-handson
- source-goodfellow-dl
- source-islp
- source-jurafsky-slp3
- source-karpathy-micrograd
- source-kelleher-fmlpda
- source-kroese-dsml
- source-lineare-algebra-archive
- source-mit-6034-quizzes
- source-mit-6036
- source-mml
- source-murphy-pml1
- source-ng-coursera
- source-pytorch-tutorials
- source-rohrer-e2eml
- source-sad-ss26-lectures
- source-statquest
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
- unit-aml-exam-prep
---

# AML exam prep — 2. Termin

## Objective

Pass the AML Klausur at the recorded second sitting. Keep the eleven lecture units as the content map and use `unit-aml-exam-prep` as the single execution lane: cold calibration, evidence-routed repair, L08→L11 dependency work, a handwritten A4 sheet, two mixed mocks, and a final taper. Administrative facts remain solely in `curriculum/modules/module-hu-aml/module.yaml`.

## Current Scope

**Execution phase — AML primary, M2 anchored (Aram, 2026-08-19).** The content build is complete. Progress now lives in `study-map-aml-exam-prep`; lecture notes and source menus are inputs, not evidence by themselves. Start with the cold L01–L11 calibration, let misses choose repair depth, work L08→L09→L10→L11 in dependency order, then run mixed transfer and mock-driven repair.

Use four AML study sessions plus two M2 anchor sessions per week through the L08–L11 build. During final AML integration, mocks and repair, use five AML sessions plus two short M2 anchors. After the AML sitting, switch to M2-only preparation until the M2 sitting recorded by its owning module. This cadence resolves the former day-to-day interleaving question without merging the two plans.

**Administration:** register the AML second sitting in AGNES during the registration window recorded in `curriculum/modules/module-hu-aml/module.yaml`, and take the sitting time and room from that same owner. Übung 10 confirms a 120-minute first-sitting baseline; until a current second-sitting notice says otherwise, mixed mocks use 120 minutes and the room slot is not treated as proof of working time.

**Scope correction:** L11 is the current 81-slide Transformers lecture and is confirmed by the Übung 10 Themen list. The older RNN/GRU/LSTM deck is superseded and removed from the current L11 menu. L11 still has no lecturer-worked Übung; its exercise bank and mock carry the diagnostic load.

**Material completeness pass (2026-08-22).** Measured per knowledge node, twenty of seventy-eight had no practice- or implementation-depth material; after `AML-material-completeness-plan.yaml` six remain, and all six are framing or optional-bridge nodes. L11 went from nine unworkable nodes to one. `estimate_minutes` is gone from all ten execution stages: the dated windows above and the closed-book test lengths inside each stage's `done_when` are the only times that remain.

## Open Questions

- What is the exact working duration of the second sitting? The confirmed 120-minute first-sitting format remains the rehearsal baseline until a current notice appears.
- Are L11 slides 73–81, labelled “BONUS: Parallelizing,” examinable? They remain learn-anyway safety material because they contain scaled matrix attention and causal masking.

## Next Action

Start `stage-aml-calibration` now: 120 minutes closed book across the Übung 10 L01–L11 Themen list. Use only unopened representative questions, create the six-class error ledger, and mark every later cluster full-pass, repair-only or cold-skip from evidence. Do not read the references first. Also place an AGNES registration-window check, sourced from `curriculum/modules/module-hu-aml/module.yaml`, on the execution checklist.

## Durable Notes

L02–L11 each have a reference, exercise bank and 75-minute per-lecture mock. L08–L11 remain `operator-drafted` until Aram works them and adds his own calculations or reasoning. L11 is now grounded in the 2026 Transformers deck; its old RNN identity and RNN-specific routes are retired. The auxiliary exam unit owns execution evidence and does not replace the lecture knowledge maps.

## Deferred

- Optional books, videos and external courses stay out of the schedule unless a recorded miss selects one exact lecture route.
- The older RNN/GRU/LSTM material is outside the 2026 AML exam scope.
- A fixed new full-course mock note is not created yet; the two mixed stages assemble fresh papers from still-unseen per-lecture and course-exercise items.
- L01 receives a ten-minute definition/formulation gate in calibration rather than a new three-note artifact suite.
