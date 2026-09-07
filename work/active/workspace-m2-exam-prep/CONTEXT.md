---
id: workspace-m2-exam-prep
type: workspace
title: M2 Klausur prep — SaD + Analysis (Kombimodul, merged track)
created: '2026-07-16'
status: active
standing: false
concepts:
- concept-descriptive-statistics
- concept-probability
- concept-combinatorics
- concept-random-variable
- concept-normal-distribution
- concept-maximum-likelihood
- concept-statistical-estimation
- concept-hypothesis-testing
- concept-decision-trees
- concept-naive-bayes
- concept-neural-network
notes:
- note-sad-l02-descriptive-basics
- note-sad-l02-exercise-bank
- note-sad-source-crosswalk
- note-sad-hypothesis-testing-handwritten
- note-regression-sad-aml-islp-bridge
sources:
- source-3b1b-bayes-theorem
- source-3b1b-essence-of-calculus
- source-3b1b-linear-algebra
- source-3b1b-neural-networks
- source-abbott-understanding-analysis
- source-ableitinger-musterloesungen
- source-aml-ss26-lectures
- source-analysis-drill-blaetter-extern
- source-analysis-grundlagen-handouts
- source-analysis-klausuren-extern
- source-analysis-skript
- source-bendersky-normal-equation
- source-berkeley-cs189
- source-bishop-prml
- source-blitzstein-hwang
- source-brandon-foltz
- source-caltech-lfd
- source-cs229-2022-videos
- source-cs229-notes
- source-cs229-problem-sets
- source-cs4780
- source-cs4780-homeworks
- source-csc411-notes
- source-d2l
- source-deitmar-uebungsbuch
- source-dekking-mips
- source-domingos-useful-things
- source-eecs498
- source-esl
- source-fahrmeir-arbeitsbuch
- source-fahrmeir-statistik
- source-fau-klausur-ws1415
- source-forster-wessoly
- source-fortmann-roe-bias-variance
- source-fritzsche-trainingsbuch
- source-geron-handson
- source-goodfellow-dl
- source-google-ml-crash-course
- source-grieser-analysis1
- source-grinstead-snell
- source-islp
- source-islp-community-solutions
- source-jbstatistics
- source-jurafsky-slp3
- source-karpathy-micrograd
- source-kelleher-fmlpda
- source-kroese-dsml
- source-kurzes-tutorium-statistik
- source-labs-schreyer-mathe-informatiker
- source-lebl-basic-analysis
- source-marsland-ml-algorithmic
- source-mfnf-analysis1
- source-mit-1805
- source-mit-18100a
- source-mit-18650
- source-mit-6034-quizzes
- source-mit-6036
- source-mit-6041sc
- source-mml
- source-murphy-pml1
- source-ng-coursera
- source-nielsen-nndl
- source-ohlbach-eisinger-beweise
- source-openintro-statistics
- source-pitman-probability
- source-prince-udl
- source-professor-leonard
- source-rohrer-e2eml
- source-ross-elementary-analysis
- source-ross-first-course
- source-sad-2025-recordings
- source-sad-klausuren-extern
- source-sad-ss26-lectures
- source-sad-uebungen
- source-schaums-probability
- source-setosa-ols
- source-sklearn-user-guide
- source-stat110
- source-statquest
- source-stewart-calculus
- source-strang-calculus
- source-swanson-principles-probability
- source-teschl-mathe-informatiker
- source-thomas-calculus
- source-tijms-understanding-probability
- source-velleman-how-to-prove-it
- source-zacharski-data-mining
- source-zedstatistics
program_ids:
- program-bachelors
module_ids:
- module-hu-m2-statistik-analysis
unit_ids:
- unit-m2-sad-l01
- unit-m2-sad-l02
- unit-m2-sad-l03
- unit-m2-sad-l04
- unit-m2-sad-l05
- unit-m2-sad-l06
- unit-m2-sad-l07
- unit-m2-sad-l08
- unit-m2-sad-l09
- unit-m2-sad-l10
- unit-m2-sad-l11
- unit-m2-sad-l12
- unit-m2-sad-l13
- unit-m2-sad-l14
- unit-m2-sad-l15
- unit-m2-sad-clustering
- unit-m2-sad-exam-prep
- unit-m2-analysis-exam-prep
- unit-m2-combined-exam-rehearsal
---

# M2 exam prep — SaD + Analysis

## Objective

Prepare Statistik und Datenanalyse and Analysis as two independent learning modules with separate scope, stages, progress, and subject-only mocks. The single combined three-hour sitting and shared grade are handled only by `unit-m2-combined-exam-rehearsal`; the administrative facts remain solely in the owning M2 module record.

## Current Scope

**Two independent subject lanes, one joint exam bridge (Aram, 2026-08-19).** Statistics and Analysis no longer form one merged study sequence. `unit-m2-sad-exam-prep` owns SaD.0→SaD.X; `unit-m2-analysis-exam-prep` owns calibrate→AN.X. Both may progress in parallel, but neither stage contains first-pass work from the other subject. Only after both subject-only transfer gates are met does `unit-m2-combined-exam-rehearsal` run the coverage blueprint, two full three-hour mocks, evidence-routed repair, and final taper.

Every subject stage starts from a cold gate or uses the module-wide diagnostic. A clean gate permits a recorded skip; a failed gate chooses the smallest repair source. Current course material remains authority, exercises come before external banks, and optional books/videos are capped gap tools rather than second courses.

**Administration remains shared:** registration, sitting, withdrawal, and grade facts are read only from `curriculum/modules/module-hu-m2-statistik-analysis/module.yaml`.

## Open Questions

- *(Resolved 2026-08-14 — the Anmeldung is no longer a question. It moved to
  Current Scope as a required action.)*
- *(Resolved 2026-08-14 — legacy Open Loop #2.)* The Analysis blocks no longer
  slot "around the AMLS sitting"; that sitting is shelved. September is now a
  shared AML/M2 window rather than an M2 deep-prep window, which is why M2 runs
  substantially in parallel instead of waiting.
- Day-to-day split with the parallel AML track through September — alternating
  days, or AML-heavy weeks with M2 anchor sessions? A working-rhythm decision,
  tracked identically in `workspace-aml-exam-prep`; decide once, for both.

## Next Action

Run two separate calibration sessions: (1) `stage-m2-sad-calibrate` for 90 minutes across the five SaD clusters, producing the SaD error ledger and full-pass/repair-only/cold-skip decisions; (2) `stage-m2-analysis-calibrate` for 60 minutes using the script contract and one cold WV sample. Do not start the joint unit yet. After calibration, advance the weakest SaD cluster and AN.0 as independent sessions.

## Durable Notes

The current SaD L01-L15 knowledge maps and material menus remain intact. The new SaD exam-prep map synthesizes them without replacing lecture units. Useful legacy material is preserved through existing canonical references and the new cold gates: L01-L05 method checks, the L06-L10 probability→inference chain, and Analysis block diagnostics. The blanket legacy rule to work every proof was not retained because the current script explicitly prioritizes definitions, theorem conditions/results, and application; proof work is error-ledger repair.

Analysis remains script-led and now ends with two Analysis-only half-mocks. Statistics ends with two Statistics-only half-mocks. Full mixed performance belongs only to the joint bridge.

## Deferred

- Full transcription of handwritten Statistics scans — use only when a live stage makes a scan relevant, so transcription doubles as review.
- Teschl & Teschl remains unresolved; no stage is allowed to block on it.
- Analysis Chapter 8 and all script sections explicitly labeled Exkurs remain post-exam depth.
- Optional full courses and proof-heavy books remain reference-only unless a recorded stage error selects one exact section.
- No official current combined M2 past paper is registered. Joint mocks must remain source-traceable assemblies and must label their time/point split provisional.
