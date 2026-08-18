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

> **Posture change (COORDINATION.md, Aram 2026-08-14): M2 runs substantially in
> parallel from now, not as a post-AML sprint.** AMLS is shelved, so the old
> "steady during Phase A, ramp after the AMLS sitting" sequencing has no pivot.
> The binding constraint is that the AML and M2 sittings are **nine days apart** —
> M2 must already be substantially prepared when AML is written. Treating M2 as
> the final stretch would compress it into exactly the cram that "study super
> well for Math-2" was meant to prevent.

*Required now — admin.* Register the combined M2 Klausur via AGNES inside the
2.-PZ Anmeldung window (dates: `curriculum/modules/module-hu-m2-statistik-analysis/module.yaml`
→ `registration_windows`). Non-negotiable and the only hard dated gate before
the exam. An action to do when the window opens, not a reminder to set.

*Required now — study.* Run `stage-m2-analysis-calibrate`, then AN.0, alongside
the current SaD lane. **Neither half is a fixed sequence any more (2026-08-15).**
Both SaD and Analysis now work the same way: open the unit's knowledge map,
compare the available materials by format and **angle**, and choose the source
that fits the current gap. The merged-prep rule stands — interleave SaD stats
clusters with Analysis proof blocks; do not run two parallel tracks *inside* M2.

> **Analysis overhaul, 2026-08-15.** `unit-m2-analysis-exam-prep` was the last
> prescriptive stage-script in a live track. It now carries a **10-node knowledge
> map** (AN.0 foundations → sequences → series → limits/continuity →
> exp-log/uniform → differentiation → Taylor → integration, plus
> proof-presentation as a cross-cutting skill and exam-transfer as the
> convergence point), and its sources moved from stage-keyed `source_selections`
> into **23 knowledge-node-keyed routes with an explicit `angle` each**.
> `source_selections` is now empty by design — it is *your* selection space, not
> the operator's prescription.
>
> **What that surfaced:** 22 sources were routed to the Analysis unit, but only
> 10 carried any description. The other 12 were bare unit-id strings — invisible
> to any selection decision. Five of those had rich evaluations sitting unused in
> their source records (Forster/Wessoly, Deitmar, Abbott, Grieser, Lebl); their
> angles are now drawn from those records. **Seven have no registered evaluation
> at all** and are listed with `scope: optional` and an angle that says so
> plainly, rather than a judgment invented by the operator (CLAUDE.md §4). They
> are visibility debt — repay on use, never in bulk (WORKFLOWS §6a).
>
> The 11-stage study map is **kept and still valid** as an optional ordered path
> (WORKFLOWS §7); it no longer claims to be the only route through the material.

Phasing while AML leads: advance AN.A–G and keep SaD progressing throughout
rather than holding them; after the AML 2. Termin, switch to AN.X and the
combined M2 mocks for the final nine days. (Both dates live in the owning module
records — `module-hu-aml`, `module-hu-m2-statistik-analysis` — and are never
restated here.)

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

**Planned next block:** start stage-m2-analysis-calibrate (60 min) — read the
script's course contract, take one cold WV sample, and create the five-class
error ledger. Then begin AN.0 with unser skript Chapters 1–2.

> 🆕 **Per-node plans written 2026-08-15 → [`inputs/AN_Node_Plans_INDEX.md`](inputs/AN_Node_Plans_INDEX.md).**
> One plan per knowledge-map node (ten), each stating which of the 23 routed
> sources to use **at which angle**, what artifact to produce, and how to
> self-test. Start with `AN_00_proof_presentation.md` — it is the calibrate stage
> and it sets the proof depth for the other 46 hours. These are **operational and
> expire with this workspace**; `source_selections` stays empty until you have
> actually used a source and it worked.
>
> **The number the plans surface:** AN.0–AN.X total **2,760 exam-critical
> minutes = 46 hours**, none of it started. AN.X alone is 540 min and needs
> contiguous sessions. Against a nine-day Phase C, AN.0–AN.G (≈37 h) has to be
> substantially done **before** the AML sitting, or AN.X — the only block that
> rehearses the combined SaD+Analysis format — is what gets sacrificed.

This is the first stage of the Analysis map and it is still `pending`; the map's
11 stages carry ~47.5 h. With AML leading on intensity, M2's job through
September is to get genuinely through AN.0→AN.G rather than to hold position.

**Admin, when the window opens:** register the combined M2 Klausur via AGNES
(see Current Scope). Dates live in the owning module record.

**SaD choice when returning to statistics:** L04 remains the open lecture, but
it has no forced current stage. Use its probability/Bayes knowledge graph to
identify the gap, then choose any current, book, video, website, or practice
option from the material menu. A source selection does not become a hidden
global sequence.

## Durable Notes

Analysis now has an executable script-led study map. unser skript.pdf is the scope and notation authority; current HU exercises come before external banks; intuition sources are capped detours; proofs are selective understanding repairs because the script says they need not be memorized.

SaD has one knowledge map per current lecture (L01–L15) plus the explicitly
labeled clustering topic. Each source route states its format, lecture-specific
angle, exact concept coverage, depth, scope, and locator. The former Mini Plans
and L06–L10 aggregate are retired; durable references and exercise banks remain
available as materials rather than mandatory steps.

## Deferred

- Full transcription of handwritten Teil-01/02/03 scans — do per cluster
  during prep so transcription doubles as review.
- Teschl & Teschl remains officially named but unresolved: no reachable
  local material or verified URL is currently registered.
- Swanson's *Principles of Probability* is explicitly excluded as
  off-syllabus formal-logic/measure-theory material.
