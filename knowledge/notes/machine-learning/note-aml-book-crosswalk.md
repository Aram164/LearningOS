---
id: note-aml-book-crosswalk
type: note
title: "AML L02–L10 — Book/Video/Testing Crosswalk (narrative & reading orders)"
created: "2026-06-26"
role: crosswalk
state: evolving
authorship: mixed
concepts: [concept-k-nearest-neighbors, concept-linear-regression, concept-basis-functions,
  concept-logistic-regression, concept-gradient-descent, concept-perceptron,
  concept-kernel-trick, concept-neural-network, concept-backpropagation,
  concept-convolutional-networks, concept-recurrent-networks]
sources: [source-islp, source-esl, source-murphy-pml1, source-csc411-notes,
  source-kroese-dsml, source-mml, source-cs229-notes, source-cs229-2022-videos,
  source-mit-6036, source-eecs498, source-statquest, source-3b1b-neural-networks,
  source-karpathy-micrograd, source-rohrer-e2eml, source-geron-handson,
  source-caltech-lfd, source-ng-coursera, source-cs4780-homeworks,
  source-mit-6034-quizzes, source-aml-ss26-lectures]
contexts: [workspace-aml-exam-prep]
---

> **Migration note (2026-07-17, Stage 2):** decomposed from
> `Plans/ML/foundations/AML/my notes/AML_Book-Concept-Crosswalk_L02-L10.md`
> (legacy tree, created KW 26, extended KW 27). The per-lecture judgment tables
> (sections/pages/scope flags for all seven book sources, the video layer, the
> testing layer) live canonically as evaluations on the source records; the
> generated source index renders the per-lecture selector. This note keeps the
> narrative: headline findings, reading orders, and the caveats that made the
> crosswalk trustworthy.

# AML L02–L10 — Book crosswalk (narrative)

Every section number and page was extracted from the **local PDF TOCs and
verified, not guessed** (KW 26–27); video lecture numbers were verified against
the actual course schedules ("topic-match, don't trust numbering" — Aram's
standing rule after the CS229 incident).

## Headline findings (the judgments that saved the most time)

For **L06 (gradient descent)** the real book matches are Murphy Ch 8, MML Ch 7
and the CS229 notes §1.1 — ISLP, ESL, Kroese and Toronto treat GD as a footnote.
**MML has no k-NN and no logistic regression** (classification via SVM) — don't
go there for L02/L05. **ESL §2.3.3** is a hidden gem tying L02 to L03 (least
squares and k-NN as ends of one flexibility spectrum). The **kernel trick
without SVM exists in exactly one book source: CS229 Ch 5** — every other book
reaches kernels only through the SVM, which AML L07 does not teach. The
**perceptron algorithm** lives in exactly two book places (ESL §4.5.1, CS229
§2.2), with Murphy §10.2.5 as the cleanest link back to L05. For **L10 (CNNs)**
only ISLP §10.3 and Murphy Ch 14 are real sources — and Murphy §14.3 is the
lecture's famous-architecture list one-to-one.

## Reading orders that work

The classic ladder is **ISLP §X → ESL §Y** (same authors: gentle then rigorous —
ESL is a depth layer, never a first read). The **MLE → cross-entropy → gradient
→ SGD spine** reads best end-to-end in **Murphy Ch 10 + Ch 8 together** (do this
when studying L05→L06). The **NN spine (L07→L08→L09)**: CS229 §2.2+Ch 5 → ISLP
§10.1–10.2 + Murphy §13.2 → Murphy §13.3–13.5 + ISLP §10.7–10.8, with MML §5.6
as the math safety net and SaD 15 sandwiched per the Master Wiring. For L08 do
the worked forward pass by hand **once** — L09 reuses the exact numbers. For L10
verify the output-size formula on the lecture's examples (6×6/f=3, then
28×28/f=5/s=1/p=0 → 24×24).

## Caveats that must not get lost

Page numbers are from the local PDF editions; section numbers are stable, page
numbers drift (offsets verified KW 27: Murphy printed = PDF − 30; ISLP − 7;
ESL − 19; CS229 − 1). The **Übung-deck gotcha** (repo-verified): exercise-slide
*filenames ≠ sheet order* — `Übung 02` = Blatt 1 (k-NN), `Übung 04` = Blatt 2,
`Übung 06` = Blatt 3, `Übung 07` = perceptron tutorial. **Slide-verified
negatives:** L07 has no SVM; L09 has no batch norm; micro/macro/weighted metric
averaging (L08) is in **no book** — lecture + sklearn docs only. External
kernel/margin problem sets are mostly SVM-scope — take only what the lecture
teaches. The 2026 L11 (RNN) deck was not yet posted; its book map (ISLP §10.5,
Murphy §15.2) is preliminary — verify when it drops.

## The video spine

Spine = **CS229 2022** (Ma & Ré — NOT Ng; Ng's run is the 2018 mirror) + **MIT
6.036** (auto-graded); everything else (EECS 498, 3B1B, StatQuest, Rohrer,
Karpathy, Ng-Coursera) is pulled per lecture, never watched linearly. The
CS229-2022 ⇄ AML lecture map is recorded on the source record. 6.036 unit names
are cited from documentation and still need click-verification on first login.
