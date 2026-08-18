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
- source-jurafsky-slp3
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
2. **L08–L11 — the real build, now complete.** These were the gap: L02–L07 had
   reference notes, exercise banks and mock exams; L08–L11 had none of the three.
   Complete material menus and knowledge maps exist for all of L01–L11, so this is
   building artifacts from a ready inventory, not scoping from scratch.
   **Order is L08 → L09 → L10**, because L08 is the forward pass and L09's
   backprop presupposes it — the deck itself defers backprop from L08 p53 to
   L09. (An earlier draft of this file said "L09 then L08" on AMLS-synergy
   grounds; that reason died with the AMLS shelving.)
   **All four are built as of 2026-08-15** — twelve notes, each page-anchored to
   its current 2026 deck, each carrying `authorship: operator-drafted`. **They are
   operator-built and not yet worked by Aram**; each becomes `mixed` when he adds
   his own reasoning, and none of them is evidence until he does.
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
   - **L11** (81pp) — `note-aml-l11-transformers`, `-exercise-bank`,
     `-mock-exam`. **Built 2026-08-15, the day the current deck arrived** (see
     the scope correction below). Scope findings: the deck builds attention
     **twice** (simplified sl. 27–34, then the real QKV head sl. 40–44, same
     running example); it contains **no RNN content**; and it is the **only
     lecture in the course with no Übung**, so its exercise bank has no
     lecturer-worked sheets behind it.
3. **The systematic L05→L11 review** and a closed-book mock against the real
   format. All eleven lectures now have artifacts to review — this is the next
   real block of work once the per-lecture loop reaches L11.

*Helpful now* — passive cross-wires from the parallel M2 track: SaD L11 supplies
workflow and metrics; SaD L15 is the deliberate warm-up for AML L08–L09. These
are genuinely bidirectional now that both tracks run at once.

> 🔄 **Scope correction — L11, 2026-08-15.** This file previously read: *"AML L11
> is a conditional prior-year RNN overview. The local 2026 archive currently stops
> at L10, so L11 must not become exam scope until a current deck or syllabus
> confirmation appears."* Aram supplied the missing material the same day and
> **both halves of that position are now wrong**:
>
> 1. **L11 is confirmed exam scope.** `exercise-slides/Übung 10.pdf` sl. 3 carries
>    the lecturer's own Themen list — eleven items, ending **"11. Transformers."**
>    That is the only authoritative scope statement in the course, and it is
>    affirmative.
> 2. **L11 is Transformers, not RNNs.** `lecture-slides/VL 11-transformers.pdf`
>    (81 sl., dated 2026-07-17) **replaced** the prior-year RNN lecture rather
>    than supplementing it. There is **no RNN/LSTM/GRU content in the 2026
>    course**; `older-lecture-slides/11-rnn_*.pdf` is superseded and must not be
>    used for scope.
>
> The conditional was correct to hold and correct to release — it released on
> slide evidence, not on assumption.
>
> 🚨 **L11 has no Übung.** The tutorial series ends at Übung 11 (CNNs,
> 2026-07-14) and the deck postdates it. Every other lecture was drilled in a
> Besprechung; this one never was. There are no lecturer-worked transformer
> problems anywhere in the course, which makes `note-aml-l11-exercise-bank` and
> `note-aml-l11-mock-exam` load-bearing in a way the L02–L10 banks are not.

*Exam format (from `Übung 10.pdf` sl. 2, the only place the lecturer states it):*
one **double-sided handwritten A4 sheet**, calculator, pen, possibly a ruler;
official photo ID + CampusCard. Zulassung was 21/42 points across the four
Übungsblätter. The 1. Termin ran **120 minutes**. ⚠️ Those are 1.-Termin figures —
the 2. Termin's slot in `curriculum/modules/module-hu-aml/module.yaml` is longer,
so **do not assume the duration carries over**. The actionable part is the cheat
sheet: build it as you study, from your mock errors, not the night before.

## Open Questions

- *(Resolved 2026-08-14 — the Anmeldung is no longer a question. It moved to
  Current Scope as a required action.)*
- Day-to-day interleaving with the parallel M2 track: the two sittings are nine
  days apart, so M2 cannot wait for AML to be written. What split holds through
  September — alternating days, or AML-heavy weeks with M2 anchor sessions?
  Open because it is a working-rhythm decision, not a planning gap.
- *(Resolved 2026-08-15 — all four lectures got the full set.)*
- *(Resolved 2026-08-15 — the `authorship` schema gap is closed.* The enum now
  carries a fourth value, `operator-drafted`, and all twelve L08–L11 notes use it.
  The earlier `external` workaround is retired.)
- The prior-year L08/L09/L10 decks have not been diffed against the 2026 ones.
  ~20 minutes each if you want certainty that no topic moved in or out. **L11
  needs no diff** — the prior-year deck is a different lecture (RNN), not a
  variant of the same one.
- **Is the L11 "Bonus: Parallelizing" section (sl. 73–81) examinable?** The
  agenda labels it Bonus, but it holds the canonical
  `A = softmax(mask(QKᵀ/√d_k))V` and causal masking that most courses examine
  directly. Treated as **learn-anyway** in the notes — four formulas, low cost —
  but the label is the lecturer's and has not been clarified.

## Next Action

> **Pointer refreshed 2026-08-15.** This section previously read "Open
> `unit-aml-l07` … choose one explanation source and one practice source" — the
> build had already moved four lectures past it. The building phase is over; what
> follows is the working phase.

**The build is done. L02–L11 all have reference + exercise bank + mock — thirty
notes, one per Thema 2–11.** Nothing further needs constructing for this exam.

**Start the per-lecture working loop at L07** (its artifacts were built 08-14 and
never worked), then **L08 → L09 → L10 → L11 in order.** Per lecture:

1. read the reference against the deck;
2. work the exercise bank;
3. sit the mock closed-book (75 min);
4. **let the misses choose your sources** from that lecture's routed menu
   (L08: 22 routes, L09: 24, L10: 19);
5. add whatever you had to look up to the **A4 cheat sheet** — it is built from
   accumulated errors, which is why it starts now and not in late September.

Order matters: L09's backprop presupposes L08's forward pass, L10's degradation
problem presupposes L09's vanishing gradients, and L11's block reuses both L08's
FFN and L10's residual connections. **L11 last is not optional** — it is the only
lecture that depends on three others.

**One structural caution for L11.** It has no Übung, so steps 2–3 carry the full
diagnostic load there. If the mock goes badly, the fallback is
`source-jurafsky-slp3` Ch. 8 — the deck's own named further reading, and the one
external source guaranteed to match its notation.

**One verification worth doing** (L09 exercise bank C6): run the deck's own
PyTorch snippet and check `.grad` against the hand-computed gradients. It
confirms both the arithmetic and the autograd understanding in one step.

**Admin, when the window opens:** register the 2. Termin via AGNES (see Current
Scope). Dates live in `curriculum/modules/module-hu-aml/module.yaml`.

## Durable Notes

AML now has individual knowledge maps and complete material menus for L01–L11.
**L01–L11 are all grounded in current 2026 decks** as of 2026-08-15, when the
L11 Transformers deck and Übung 08–11 were shelved into
`material://source-aml-ss26-lectures`. The prior-year RNN deck is retained in
`older-lecture-slides/` as superseded material, not as L11 scope. Every
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
- *(Retired 2026-08-15)* "L11 RNN execution is deferred until 2026 scope is
  confirmed." Confirmation arrived — and inverted the item. The 2026 L11 is
  Transformers, is confirmed scope by the Themen list, and is built. There is no
  RNN work to defer because there is no RNN in the course.
- Sutton & Barto remains visible but off-scope for posted AML L01–L10;
  Zacharski is an optional L02 alternative, not a neural-network source.
