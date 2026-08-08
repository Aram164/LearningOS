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
- source-sad-ss26-lectures
- source-sad-uebungen
- source-sad-2025-recordings
- source-teschl-mathe-informatiker
- source-fahrmeir-statistik
- source-fahrmeir-arbeitsbuch
- source-blitzstein-hwang
- source-pitman-probability
- source-tijms-understanding-probability
- source-ross-first-course
- source-schaums-probability
- source-openintro-statistics
- source-dekking-mips
- source-mit-1805
- source-stat110
- source-mit-18650
- source-fau-klausur-ws1415
- source-sad-klausuren-extern
- source-statquest
- source-jbstatistics
- source-kurzes-tutorium-statistik
- source-brandon-foltz
- source-kelleher-fmlpda
- source-islp
- source-kroese-dsml
- source-cs229-notes
- source-cs229-2022-videos
- source-murphy-pml1
- source-csc411-notes
- source-aml-ss26-lectures
- source-cs4780-homeworks
- source-mit-6034-quizzes
- source-3b1b-neural-networks
- source-3b1b-linear-algebra
- source-eecs498
- source-rohrer-e2eml
- source-domingos-useful-things
- source-swanson-principles-probability
- source-analysis-skript
- source-professor-leonard
- source-3b1b-essence-of-calculus
- source-fritzsche-trainingsbuch
- source-analysis-drill-blaetter-extern
- source-analysis-klausuren-extern
- source-strang-calculus
- source-mit-18100a
- source-analysis-grundlagen-handouts
- source-ableitinger-musterloesungen
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
- unit-m2-sad-l06-l10
- unit-m2-analysis-exam-prep
---

# M2 exam prep — SaD + Analysis

## Objective

Pass module-hu-m2-statistik-analysis: ONE combined 3h Klausur covering both the
SaD (statistics + ML half) and Analysis components, one shared grade. The sitting
is deferred to the 2. Termin (deferral in COORDINATION; dates in
`curriculum/modules/module-hu-m2-statistik-analysis/module.yaml`) — the July time
pressure is off, but the merged-prep rule stands: interleave SaD stats clusters
with Analysis proof blocks, do not run two parallel tracks.

## Current Scope

Required now: run stage-m2-analysis-calibrate, then AN.0 alongside the current SaD N1/N2 work. During Phase A keep M2 steady; after the AMLS sitting advance AN.A-G while SaD progresses; after AML on 30.09 switch to AN.X and combined M2 mocks for the 09.10 sitting.

## Open Questions

- 2.-PZ Anmeldung (31.08–10.09): calendar reminder set?
- Where do the Analysis blocks slot around the AMLS sitting (last slot,
  confirmed) and the AML 2. Termin — sequencing decision pending (legacy Open
  Loop #2). With AMLS in late August, the M2 deep-prep window is September.

## Next Action

> **Two different pointers — do not conflate them.** The global resume pointer
> (`curriculum/resume.yaml`) reports the *last stage left open*:
> `unit-m2-sad-l04 / stage-event-spaces`. It is convenience state, not a
> recommendation (ARCHITECTURE §22). The planned next block below is the
> *decision* about what to do next. Both are correct; they answer different
> questions. An interface must label them separately — "Resume where you left
> off" vs "Planned next" — never both as "Continue".

**Planned next block:** start stage-m2-analysis-calibrate (60 min) — read the
script's course contract, take one cold WV sample, and create the five-class
error ledger. Then begin AN.0 with unser skript Chapters 1–2.

**Open thread to resume when convenient:** `unit-m2-sad-l04 /
stage-event-spaces` is still `active` and unfinished; close it out during the
steady SaD lane rather than leaving it dangling behind the Analysis start.

## Durable Notes

Analysis now has an executable script-led study map. unser skript.pdf is the scope and notation authority; current HU exercises come before external banks; intuition sources are capped detours; proofs are selective understanding repairs because the script says they need not be memorized.

## Deferred

- Full transcription of handwritten Teil-01/02/03 scans — do per cluster
  during prep so transcription doubles as review.
- Teschl & Teschl remains officially named but unresolved: no reachable
  local material or verified URL is currently registered.
- Swanson's *Principles of Probability* is explicitly excluded as
  off-syllabus formal-logic/measure-theory material.
