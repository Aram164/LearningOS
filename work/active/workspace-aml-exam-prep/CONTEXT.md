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
`curriculum/modules/module-hu-aml/module.yaml`). Use each lecture unit as a
knowledge and material overview: inspect the available angles, choose the
sources that fit the current gap, and only then create a personal study path.

## Current Scope

> **Phase A posture (COORDINATION.md, Aram 2026-08-14): AML is the primary
> track.** AMLS is shelved to next year, so the synergy lane that governed this
> workspace is void — AML foundations were being pulled in *because* AMLS needed
> them, and there is no AMLS track to pull from. **Nothing about AML is deferred
> behind another exam any more.** AML is simply the nearest sitting.
> (Change history: this section read "parked until after the AMLS sitting" until
> 2026-08-08, then "synergy lane" until 2026-08-14.)

*Required now — admin.* Register the 2. Termin via AGNES inside the 2.-PZ
Anmeldung window (dates: `curriculum/modules/module-hu-aml/module.yaml` →
`registration_windows`). Non-negotiable and the only hard dated gate before the
exam; missing it forfeits the sitting. Not a reminder to set — an action to do
when the window opens.

*Required now — study.* AML exam-specific preparation, which starts immediately:

1. **L07** — make the material choice and run the practice session, then
   self-test with `note-aml-l07-mock-exam` (75 min, closed book).
2. **L08–L10 — the real build.** These were the gap: L02–L07 had reference notes,
   exercise banks and mock exams; L08–L10 had none of the three. Complete
   material menus and knowledge maps exist for all of L01–L11, so this is
   building artifacts from a ready inventory, not scoping from scratch.
   **Order is L08 → L09 → L10**, because L08 is the forward pass and L09's
   backprop presupposes it — the deck itself defers backprop from L08 p53 to
   L09. (An earlier draft of this file said "L09 then L08" on AMLS-synergy
   grounds; that reason died with the AMLS shelving.)
   **All three are built as of 2026-08-15** — nine notes, each page-anchored to
   its current 2026 deck, each carrying `authorship: external` because the schema
   has no "operator-drafted" value (see Open Questions). **They are operator-built
   and not yet worked by Aram**; each becomes `mixed` when he adds his own
   reasoning, and none of them is evidence until he does.
   - **L08** (81pp) — `note-aml-l08-feedforward-networks`,
     `-exercise-bank`, `-mock-exam`. Scope finding: the deck **stops at the
     forward pass** (backprop deferred on p53), and the **metrics block is ~a
     quarter of the deck**.
   - **L09** (74pp) — `note-aml-l09-backpropagation`, `-exercise-bank`,
     `-mock-exam`. Reuses L08's running example plus a loss node. **No batch
     normalization.** Three in-deck quiz slides (p12, p48, p53).
   - **L10** (70pp) — `note-aml-l10-cnn`, `-exercise-bank`, `-mock-exam`. **Five
     in-deck quiz slides** (p16, p34, p36, p51, p57) — the highest density in the
     course, drilled first in the bank.
   - **L11 — not buildable and deliberately not built.** No current 2026 deck
     exists; only the prior-year RNN slides. Building artifacts would violate the
     slide-scope rule.
3. **The systematic L05→L11 review** and a closed-book mock against the real
   format, once L08–L10 have artifacts to review.

*Helpful now* — passive cross-wires from the parallel M2 track: SaD L11 supplies
workflow and metrics; SaD L15 is the deliberate warm-up for AML L08–L09. These
are genuinely bidirectional now that both tracks run at once.

*Reference only* — AML L11 is a conditional prior-year RNN overview. The local
2026 archive currently stops at L10, so L11 must not become exam scope
until a current deck or syllabus confirmation appears. It is excluded from the
L08–L11 build above until that confirmation exists.

## Open Questions

- *(Resolved 2026-08-14 — the Anmeldung is no longer a question. It moved to
  Current Scope as a required action.)*
- Day-to-day interleaving with the parallel M2 track: the two sittings are nine
  days apart, so M2 cannot wait for AML to be written. What split holds through
  September — alternating days, or AML-heavy weeks with M2 anchor sessions?
  Open because it is a working-rhythm decision, not a planning gap.
- *(Resolved 2026-08-15 — all three lectures got the full set.)*
- **Schema gap: `authorship` has no "operator-drafted" value.** The enum is
  `user | mixed | external`; the nine new L08–L10 notes are recorded as
  `external` (their substance is the lecturer's deck) with a build-note banner
  carrying the nuance. Under the current philosophy — operator builds the menu
  and the artifacts, Aram selects and works them — operator-drafted notes are
  routine, so the enum probably wants a fourth value. **Schema changes need
  Aram's explicit approval (CLAUDE.md §5); proposed, not done.**
- The prior-year L08/L09/L10 decks have not been diffed against the 2026 ones.
  ~20 minutes each if you want certainty that no topic moved in or out.

## Next Action

**Open `unit-aml-l07`:** choose one explanation source and one practice source
for each uncovered knowledge node, then self-test with `note-aml-l07-mock-exam`
(75 min, closed book). This was the deferred-until-after-AMLS action; it is now
simply the next action.

**Then work L08 → L09 → L10, in that order.** All nine artifacts now exist, so
the loop per lecture is: read the reference against the deck → work the exercise
bank → sit the mock closed-book (75 min) → **let the misses choose your sources**
from that lecture's routed menu (L08: 22 routes, L09: 24, L10: 19). That is the
selection step this workspace exists for; the artifacts are the diagnostic that
makes the choice informed rather than arbitrary.

Order matters: L09's backprop presupposes L08's forward pass, and L10's
degradation problem presupposes L09's vanishing gradients.

**One verification worth doing** (L09 exercise bank C6): run the deck's own
PyTorch snippet and check `.grad` against the hand-computed gradients. It
confirms both the arithmetic and the autograd understanding in one step.

**Admin, when the window opens:** register the 2. Termin via AGNES (see Current
Scope). Dates live in `curriculum/modules/module-hu-aml/module.yaml`.

## Durable Notes

AML now has individual knowledge maps and complete material menus for L01–L11.
L01–L10 are grounded in current 2026 decks. L11 preserves the older RNN
material as visibly prior-year, pending current scope confirmation. Every
material route states its format, learning angle, covered knowledge nodes,
depth, scope status, and locator. The source map includes every local course
asset family, the complete local CS4780 bank, shared books, official web
courses/docs, and explicit off-scope shelf dispositions. Personal study maps
remain optional and are created only after sources are chosen.

## Deferred

- *(Retired 2026-08-14)* "The systematic L08–L10 sweep remains after L07 and the
  AMLS sitting." Void — there is no AMLS sitting to wait for, and L08–L10 are now
  required-now work (see Current Scope). The material inventory and semantic
  mapping being complete is what makes that feasible.
- L11 RNN execution is deferred until 2026 scope is confirmed.
- Sutton & Barto remains visible but off-scope for posted AML L01–L10;
  Zacharski is an optional L02 alternative, not a neural-network source.
