---
id: workspace-algo2-exam-prep
type: workspace
title: Algo 2 oral exam prep — AL track (October window)
created: '2026-07-17'
status: blocked
standing: false
concepts:
- concept-fast-multiplication
- concept-amortized-analysis
- concept-b-trees
- concept-fibonacci-heaps
- concept-splay-trees
- concept-cuckoo-hashing
- concept-shortest-paths
- concept-max-flow
- concept-bipartite-matching
- concept-computational-geometry
- concept-fft
- concept-stable-matching
- concept-asymptotic-analysis
- concept-recurrences-master-theorem
- concept-adt-dictionary
- concept-binary-search-trees
- concept-adt-priority-queue
- concept-hashing-chaining
- concept-graph-basics
- concept-complex-roots-of-unity
- concept-determinant-orientation
notes:
- note-algo2-phase0-prerequisites
- note-algo2-fast-multiplication
- note-algo2-fast-multiplication-exercise-bank
- note-algo2-fast-multiplication-viva-drill
- note-algo2-amortized-analysis
- note-algo2-amortized-analysis-exercise-bank
- note-algo2-amortized-analysis-viva-drill
- note-algo2-b-trees
- note-algo2-b-trees-exercise-bank
- note-algo2-b-trees-viva-drill
- note-algo2-fibonacci-heaps
- note-algo2-fibonacci-heaps-exercise-bank
- note-algo2-fibonacci-heaps-viva-drill
- note-algo2-splay-trees
- note-algo2-splay-trees-exercise-bank
- note-algo2-splay-trees-viva-drill
- note-algo2-cuckoo-hashing
- note-algo2-cuckoo-hashing-exercise-bank
- note-algo2-cuckoo-hashing-viva-drill
- note-algo2-shortest-paths
- note-algo2-shortest-paths-exercise-bank
- note-algo2-shortest-paths-viva-drill
- note-algo2-maximum-flow
- note-algo2-maximum-flow-exercise-bank
- note-algo2-maximum-flow-viva-drill
- note-algo2-bipartite-matching
- note-algo2-bipartite-matching-exercise-bank
- note-algo2-bipartite-matching-viva-drill
- note-algo2-stable-matching
- note-algo2-stable-matching-exercise-bank
- note-algo2-stable-matching-viva-drill
- note-algo2-computational-geometry
- note-algo2-computational-geometry-exercise-bank
- note-algo2-computational-geometry-viva-drill
- note-algo2-fft
- note-algo2-fft-exercise-bank
- note-algo2-fft-viva-drill
sources:
- source-algo2-hu-materials
- source-dms-grundwerkzeuge
- source-clrs
- source-ottmann-widmayer
- source-kleinberg-tardos
- source-pagh-cuckoo-hashing
- source-mit-6006
- source-mit-6046j
- source-open-data-structures
- source-tuwien-ad2-fibonacci
- source-cmu-15451-splay-notes
- source-sleator-tarjan-splay
- source-frankfurt-algo2-course
- source-visualgo
- source-wayne-kt-slides
- source-reducible-fft
- source-algo2-frankfurt-klausuren
- source-jeff-erickson-algorithms
- source-fiset-graph-theory
- source-kit-algorithmen2
program_ids:
- program-bachelors
module_ids:
- module-hu-algo2
unit_ids:
- unit-algo2-exam-prep
---

# Algo 2 exam prep — AL

> **Status 2026-07-25 — DROPPED from the autumn cycle (Aram).** Not sitting the
> 2.-PZ oral, not registering in the Anmeldung window, no study time allocated.
> Workspace `blocked` by decision, not by dependency. Module record stays
> `enrolled` in `curriculum/modules/module-hu-algo2/module.yaml` (no formal
> Abmeldung). Reversible — see the Deferrals entry in work/COORDINATION.md.
>
> **Everything below the Current Scope heading is the preserved reinstatement
> plan, not live work.** While this workspace is `blocked` it has no required
> actions of any kind — including no admin and no registration. Read the plan
> only if Aram reinstates the module.

## Objective

*(Reinstatement plan — not active.)* Pass the 30-minute oral exam (Zoom) in the
October window (dates and Anmeldung facts in
`curriculum/modules/module-hu-algo2/module.yaml`). Übungen are ungraded — all
value is in the exam. **48 h of exam-critical study by the rebuilt study map,
plus 2–8 h of Phase 0 depending on diagnostics** (the earlier "~40–50 h" estimate
was a guess; this one is staged and itemized).

## Current Scope

*Required now* — **nothing.** The module is dropped; there is no admin, no
registration and no study in scope. (Until 2026-08-08 this section still read
"book the Prüfungstermin", contradicting the drop decision above and the Next
Action below — removed in the semantic normalization pass, item 2.)

## Reinstatement Plan (preserved — inert while `blocked`)

> 🆕 **Rebuilt 2026-08-16 (Aram's request).** The plan below replaces the legacy
> `A→B→{C,D,E,F}→G→H→I; J, K` lettering, which no longer mapped to anything
> checkable. **A complete learning suite now exists** — 38 notes, matching the
> shape used for AML and M2. Building it did **not** reactivate the module; this
> workspace, the unit and the study map all remain `paused`/`blocked` together.

**What now exists (all `authorship: operator-drafted`, none worked by Aram):**

- **`note-algo2-phase0-prerequisites`** — nine prerequisite phases (0.1–0.9),
  each named by a deck's own *Erinnerung*/*Wiederholung* slide, each a
  **diagnostic first**: pass and skip. Worst case 8 h if everything fails,
  realistically 2–3 h concentrated in **0.7 (complex roots of unity)** and
  **0.9 (speaking aloud)**.
- **Twelve topic units**, one per lecture, each with a page-anchored **reference**,
  an **exercise bank**, and a **viva drill**. The third artifact is deliberately
  *not* a written mock: this exam is a **30-minute Zoom oral**, so each drill
  carries a five-minute summary, follow-up question trees, board-work timings, and
  a verbatim ~90-second version.
- **`unit-algo2-exam-prep`** now carries a **14-node knowledge map**;
  `study-map-algo2-exam-prep` has 14 staged blocks totalling **2,880 minutes = 48
  hours** of exam-critical work.

**The order is constrained, not free:**

1. **Phase 0 diagnostics first** — they price the reinstatement.
2. **T02 amortized analysis before T04 and T05** — both decks list it as assumed
   on their slide 2, and both headline bounds are amortized.
3. **T08 max flow before T09 bipartite matching** — the matching deck's own Übung
   is the flow reduction.
4. **T01 before T12** — the FFT lecture closes the question Karatsuba opened, and
   that bookend is the best available answer to "what did this course do?"
5. **Oral delivery last and separately** — 300 min, and the one thing that cannot
   be done by reading.

**Two material gaps, recorded rather than reconstructed:** the **Organisation
deck** (1st lecture, 8 April) is not held, and there are **no HU Übungsblätter**
for any topic except stable matching. Übungen are ungraded, but this leaves the
oral with no examiner-calibrated practice — which is exactly why the viva drills
carry the diagnostic load.

*Reference only* — the legacy Chat9 plan (copy in `inputs/`, Moodle-verified
per-topic literature).

## The October collision — decision input, not a recommendation

> **Recorded 2026-08-16 at Aram's request. This is the fact the suite exists to
> inform; it is stated plainly and left undecided.**

**The ordering — dates live only in the owning `module.yaml` files and are
deliberately not restated here:**

| Order | Sitting | Owning record |
|---|---|---|
| 1st | **AML Klausur** | `curriculum/modules/module-hu-aml/module.yaml` |
| 2nd | **Algo 2 oral window** (30 min, Zoom, by arrangement) | `curriculum/modules/module-hu-algo2/module.yaml` |
| 3rd | **M2 Klausur** | `curriculum/modules/module-hu-m2-statistik-analysis/module.yaml` |

**The Algo 2 oral window falls inside the nine-day gap between AML and M2.**

That gap is not free time. `work/COORDINATION.md` reserves it explicitly:

> *"Phase C — AML written → the M2 Klausur: M2 all-in (nine days). Everything
> flips to M2… **This is a finish, not a start** — it only works if Phase A and B
> actually kept M2 moving."*

**What is actually in that window today:**

- **M2 Analysis: ~46 exam-critical hours, none started.** All nine SaD/Analysis
  knowledge-map nodes are unbegun; the Analysis half of a combined one-grade
  Klausur holds a single note, a source crosswalk. `AN.X` alone — the only block
  that rehearses the combined SaD+Analysis format — is 540 min and needs
  contiguous sessions.
- **Algo 2: ~48 exam-critical hours** by the study map above, plus 2–8 h of
  Phase 0, against **twelve topics** examined orally.
- Both would have to be carried while AML (Sept 30) is still the nearest exam.

**The admin gate is the same for all three** — the 2.-PZ Anmeldung window
(`registration_windows` in each owning `module.yaml`). Algo 2 registers via AGNES
*and* books a slot in the Prüfungs-Moodle. **Once that window closes the option is
gone for this cycle**, so the decision falls due well before the exam does.

**Two things that make Algo 2 cheaper than it looks:**

- the suite is **built** — the 48 h is study, not construction;
- the decks name their own Literatur and every named book is held locally, so
  there is no source-hunting overhead.

**Two that make it more expensive:**

- **no Übungsblätter** and **no past papers from this examiner** — the Frankfurt
  exams are another university and a written format;
- an oral cannot be routed around: a soft prerequisite becomes the question.

**Not resolved here.** Reinstating means setting this workspace,
`unit-algo2-exam-prep` and `study-map-algo2-exam-prep` back to `active`
**together** (the validator enforces this), and registering inside the Anmeldung
window. Aram decides.

## Open Questions

*(All dormant — they only matter on reinstatement.)*

- **Does the 8 July FFT session's `[15-end]` really cover 53 slides?** Every other
  session in the course covers 6–21. Either that lecture was unusually long or
  later FFT material was never delivered. Confirm before treating all 67 slides as
  scope — it is the only unresolved scope question in the module.
- **Is the Organisation deck (8 April) recoverable?** It is the one scheduled item
  with no local file, and it is where exam-format and organizational detail would
  normally live.
- Kap. 10–12 literature not posted on Moodle yet (legacy Open Loop #6). **Largely
  superseded 2026-08-16** — each deck's slide 2 names its own Literatur, and all
  named books are held locally.
- Slot booking: which day in the 5–8 October window? **Now materially coupled to
  the M2 date** — see the collision above.

## Next Action

None — dropped from the autumn cycle (Aram, 2026-07-25). No registration, no
slot booking, no study. To reinstate: set this workspace, `unit-algo2-exam-prep`
and `study-map-algo2-exam-prep` back to `active` **together** (they were moved to
`paused` on 2026-08-08 so no layer could claim this work was ready while another
said it was dropped — a validator invariant now enforces that), register/book in
the Anmeldung window, and resume the AL.X study chain below.

## Deferred

- *(Retired 2026-08-16)* "All AL study blocks until the AMLS sitting is written
  (decision KW 24, reconfirmed 2026-07-17)." **Void** — AMLS was dropped on
  2026-08-15 and no sitting was taken, so the event this deferral waited on does
  not occur. Algo 2 study is not deferred behind anything; it is simply not
  scheduled, because the module is dropped.
