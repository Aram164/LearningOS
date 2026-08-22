# AML plan coverage audit — 2026-08-22

Plan package: `work/active/workspace-aml-exam-prep/outputs/AML-material-completeness-plan.yaml`

Scope authority: the current 2026 decks `VL 01`–`VL 11` under
`material://source-aml-ss26-lectures/lecture-slides/`, followed by the current
`Übung 02`–`Übung 11` and Bonusblatt assets. The Themen list on Übung 10 slide 3
remains the course's explicit exam-scope evidence. Books and external courses are
explanation and practice layers only.

**Audit question.** The same one Aram set for SaD on 2026-08-21: *does every stage
house all the material that advances understanding of the concepts that lecture
actually discusses?* Measured the same way — the unit of measurement is the
**knowledge node**, not the lecture and not the source count. A node with no
practice- or implementation-depth route cannot be worked, only read.

This audit is a follow-on to the exhaustive
`AML-exam-execution-plan-coverage-audit-2026-08-19.md`, which opened and disposed
of the complete AML material shelf. No new AML material has appeared since. What
this pass adds is the node-level measurement that audit did not run, and the
routes that measurement showed were missing.

## The measurement, before

| Unit | Nodes | Routes | Nodes with no practice/implementation route | Nodes served by one depth |
|---|---|---|---|---|
| `unit-aml-l01` | 5 | 34 | 2 | 0 |
| `unit-aml-l02` | 6 | 51 | 0 | 0 |
| `unit-aml-l03` | 6 | 66 | 1 | 0 |
| `unit-aml-l04` | 6 | 68 | 0 | 0 |
| `unit-aml-l05` | 6 | 57 | 0 | 0 |
| `unit-aml-l06` | 7 | 64 | 3 | 0 |
| `unit-aml-l07` | 7 | 53 | 0 | 0 |
| `unit-aml-l08` | 6 | 78 | 1 | 0 |
| `unit-aml-l09` | 7 | 76 | 0 | 0 |
| `unit-aml-l10` | 6 | 72 | 1 | 0 |
| **`unit-aml-l11`** | **9** | **16** | **9 — every node** | **2** |
| `unit-aml-exam-prep` | 7 | 13 | 3 | 2 |
| **total** | **78** | **199** | **20** | **4** |

L11 carried sixteen routes where every other lecture carried 51–78, and its only
non-deck route was a URL. That is the whole finding: AML's problem was never
spread thin like SaD's 42, it was one lecture with nothing behind it.

## Review boundary

Inventoried in full for this pass:

- `materials/machine-learning/classical/` — all 13 entries, per the shelf's generated `SOURCES.md`
- both files in `geron-handson/`, opened and compared (see the duplicate finding below)
- `murphy-pml1/pml1.pdf` (860 pp.) and `murphy-pml1/solutions-public.pdf` (45 pp.)
- `cs229-notes/`, `csc411-notes/`, `kroese-dsml/`, `marsland-ml-algorithmic/` — probed for
  attention/transformer content
- `materials/mathematics/linear-algebra/` — the one registered source in the shelf
- the module's existing `source-map.yaml` (33 sources, 199 routes) and all 12 unit records

Explicitly not entered: the quarantined `Job/` tree (CLAUDE.md §13); the M2 lanes,
which are owned by `workspace-m2-exam-prep`.

## Method

Every locator added by this package was confirmed by opening the file and probing
the page. Printed page numbers are given where the book has them; the Géron
3rd-edition file is a reflowed ebook with no printed page numbers, so its
locators state PDF pages and name the section heading. Two candidate routes were
**dropped** when the probe contradicted them. No route was written from a
filename, a chapter title, or a memory of the book.

## Local material inventory — newly routed

| Locator | Version | Format | Opened/inspected evidence | Actual contents | Duplicate relation | Disposition | Unit route | Lecture-specific angle |
|---|---|---|---|---|---|---|---|---|
| `material://source-geron-handson/geron-copy2.pdf` | **3rd ed., Oct 2022, 1126 pp.** | book | copyright page read ("THIRD EDITION", "October 2022: Third Edition"); full text extracted; Ch 16 sections and exercises located by heading | Ch 3 metrics (confusion matrix pdf p. 164, precision/recall p. 167, ROC p. 173); Ch 10 biological→artificial neurons p. 380; Ch 11 Faster Optimizers pp. 485–494; Ch 14 visual cortex p. 620, exercises p. 694; **Ch 16 attention p. 772, original Transformer p. 776, positional encodings pp. 779–780, multi-head and masking pp. 781–785, exercises pp. 794–795** | **not a duplicate of `geron.pdf`** — see below | complementary | `l01`, `l06`, `l08`, `l10`, `l11`, `exam-prep` | the executable layer for four nodes that had none, and the only local Transformer code |
| `material://source-murphy-pml1/pml1.pdf` | 1 ed., 860 pp. | book | TOC extracted with printed page targets; page offset fixed at +30 against a running header; every cited page probed for its term | §8.1.3 convexity and the Hessian test pp. 277–281; §8.3 Newton and BFGS pp. 289–291; §8.4.6 AdaGrad p. 299, RMSProp pp. 299–300, **Adam p. 300**, failure modes p. 301; §11.2.2 least squares as an NLL p. 372; §15.4 attention pp. 518–525; §15.5 Transformers pp. 526–532; §15.7 language models pp. 537–546; §20.5 word embeddings pp. 705–712 | unique | complementary | `l03`, `l06`, `l11`, `exam-prep` | the derivation layer the L06 and L11 decks assert without deriving |
| `material://source-murphy-pml1/solutions-public.pdf` | partial manual, 2021-09-25, 45 pp. | book | full contents listed by exercise number | §10.1 gradient **and Hessian** of the multinomial logistic log-likelihood; §11.3 partial derivative of the RSS; §13.1 backpropagation for a 1-layer MLP | companion to `pml1.pdf` | complementary | `l06` | the one solution-backed place where the convexity claim and the Newton update are computed rather than asserted |
| `material://source-lineare-algebra-archive/LA/` | mixed, HU and extern | exercise | folder listed; four solution-bearing files identified by name | solved Übungen, solved Übungsblatt, Klausur 31-07-23 with Lösungen, Probeklausur with Lösungsvorschlägen | unique | prerequisite | `l01` | the only registered material that can test the prerequisite the 36-page primer diagnoses |

### The Géron finding

`geron.pdf` and `geron-copy2.pdf` are **different editions of different lengths**,
not two copies of one file:

| | `geron.pdf` | `geron-copy2.pdf` |
|---|---|---|
| Edition | Second Edition, **Early Release** (2019) | **Third Edition** (October 2022) |
| Pages | 510 | 1126 |
| Last chapter present | Ch 14, and it stops mid-chapter | complete through Ch 19 |
| Attention / Transformers | **absent** | Ch 16 |

The 2026-08-21 SaD audit recorded `geron-copy2.pdf` as "a second copy in the same
folder; not routed" and routed the 510-page early release instead. That
disposition was wrong on the evidence available today — the copy left unrouted is
the complete, newer book. This package routes the 3rd edition for AML and names
the file explicitly in every locator.

**This affects the SaD lane too**, which is routed to the early release for Géron
Chapters 1–11. Correcting it there is a separate package and is not attempted
here; it is recorded as a carried item below.

## Linked web material inventory

| URL | Named by | Format | Official/primary evidence | Verified on | Actual topic/locator | Disposition | Unit route | Lecture-specific angle |
|---|---|---|---|---|---|---|---|---|
| `https://d2l.ai/chapter_attention-mechanisms-and-transformers/index.html` | existing `source-d2l` record | website | the book's own chapter index | **2026-08-22** | 11.1 Queries, Keys, and Values; 11.2 Attention Pooling; 11.3 Attention Scoring Functions; 11.5 Multi-Head Attention; 11.6 Self-Attention and Positional Encoding; 11.7 The Transformer Architecture — each ending in an Exercises subsection | complementary | `l11`, `exam-prep` | the only source on the menu with a worked exercise set behind every L11 node |
| `https://web.stanford.edu/~jurafsky/slp3/` | AML L11 slide 72 | book | authors' Stanford page | 2026-08-19, unchanged | Chapter 8 — Transformers | complementary | `l11` | carried forward unchanged |

**Correction to the `source-d2l` record.** Its `why` read *"Executable
neural-network and CNN reference for current L08-L10. Its RNN chapters are outside
the 2026 AML L11 scope."* True of Chapter 10, but Chapter 11 is the
attention-and-transformers chapter, and the whole book was excluded from L11 on
the strength of a neighbouring chapter. The `why` is rewritten to say what is
actually out of scope.

## Explicit exclusions and unresolved gaps

| Material/topic | Disposition | Evidence | Reason | Revisit condition |
|---|---|---|---|---|
| `cs229-notes.pdf` for the L11 nodes | **excluded** | probe: transformers appear only on pdf pp. 172–174, where the text says it will "treat the intermediate computation in transformer as a blackbox" | a blackbox treatment covers none of the attention, Q/K/V, positional or block nodes | if the notes are revised |
| `geron.pdf` (2nd-ed. early release) for any L11 node | **excluded** | copyright page and page count; the file ends inside Ch 14 | the edition has no attention chapter | n/a — the 3rd-edition file is routed instead |
| Marsland, Kroese, CSC411 for L11 | excluded | full-text probe: zero occurrences of "transformer" or "self-attention" in all three | pre-transformer texts | n/a |
| Géron 3rd ed. Ch 16 exercises 8–9 | partial | exercises page read in full | Q8 and Q9 are Reber-grammar and encoder–decoder **RNN** coding tasks, outside the 2026 scope; only Q5 and Q6 are on-node | n/a |
| Murphy Ch 15 exercises | **absent** | chapter runs 15.1–15.7 and ends without an Exercises section; the solution manual has no Ch 15 entry | Murphy is a derivation route for L11, not a practice route | n/a |
| L11 lecturer-worked exercises | **unresolved absence**, carried from 2026-08-19 | the exercise inventory ends with the CNN Übung 11 | no Transformer Übung exists; D2L Ch 11 is a substitute, not the course's own sheet | add only if a current lecturer-worked asset appears |
| L11 slides 73–81 "BONUS: Parallelizing" | scope ambiguous; learn-anyway | carried from 2026-08-19 | labelled Bonus but contains scaled matrix attention and causal masking | clarify with the lecturer; until then a low-cost safety node |
| Exact second-sitting duration | unresolved administrative detail | Übung 10 confirms 120 minutes for the first sitting only | a room slot is not proof of working time | rehearse 120 minutes until a notice says otherwise |
| `knowledge-aml-l11-language-task` | **gap, reference depth only** | Murphy §15.7 pp. 537–546 is the only route; it is a survey, not a drill | next-token prediction is stated by the deck and tested by the L11 mock, not by a book exercise | none needed unless the mock proves insufficient |
| `knowledge-aml-l03-probabilistic` | gap, derivation depth only | Murphy §11.2.2 p. 372 now routes; no solved drill exists locally | the deck itself marks this an optional bridge | none needed |
| `knowledge-aml-l01-history` | framing node | Géron Ch 10 p. 380 now supplies a second angle | a chronology drill is the wrong instrument; the deck presents it as a concept map | none needed |
| `knowledge-aml-exam-scope`, `-integration`, `-logistics` | framing and administrative nodes | — | the execution stages are themselves the instrument for these | none needed |
| SaD lane routed to the Géron early release | **carried, not fixed here** | the edition comparison above | out of this package's module boundary | a separate `module-hu-m2-statistik-analysis` package |

## Unit knowledge and material matrix

| Unit | Nodes | Routes before → after | Nodes with no practice/implementation before → after | Nodes served by one depth before → after | Remaining unserved |
|---|---|---|---|---|---|
| `unit-aml-l01` | 5 | 34 → 36 | 2 → **1** | 0 → 0 | `l01-history` (framing) |
| `unit-aml-l02` | 6 | 51 → 51 | 0 → 0 | 0 → 0 | none |
| `unit-aml-l03` | 6 | 66 → 67 | 1 → **1** | 0 → 0 | `l03-probabilistic` (optional bridge) |
| `unit-aml-l04` | 6 | 68 → 68 | 0 → 0 | 0 → 0 | none |
| `unit-aml-l05` | 6 | 57 → 57 | 0 → 0 | 0 → 0 | none |
| `unit-aml-l06` | 7 | 64 → 71 | 3 → **0** | 0 → 0 | none |
| `unit-aml-l07` | 7 | 53 → 53 | 0 → 0 | 0 → 0 | none |
| `unit-aml-l08` | 6 | 78 → 79 | 1 → **0** | 0 → 0 | none |
| `unit-aml-l09` | 7 | 76 → 76 | 0 → 0 | 0 → 0 | none |
| `unit-aml-l10` | 6 | 72 → 76 | 1 → **0** | 0 → 0 | none |
| `unit-aml-l11` | 9 | 16 → 38 | 9 → **1** | 2 → 0 | `l11-language-task` (reference depth) |
| `unit-aml-exam-prep` | 7 | 13 → 19 | 3 → **3** | 2 → 2 | the three framing nodes |
| **total** | **78** | **199 → 223** | **20 → 6** | **4 → 2** | |

## What changed, in one line per unit

| Unit | Added |
|---|---|
| `unit-aml-l01` | Géron 3rd ed. Ch 10 — the landmark chain as one causal story; the LA archive — solved drills for a failed primer check |
| `unit-aml-l03` | Murphy §11.2.2 — the squared-error objective introduced as a negative log-likelihood |
| `unit-aml-l06` | Murphy §8.1.3 convexity and the Hessian test; §8.3 Newton and BFGS; §8.4.6 AdaGrad→RMSProp→Adam derived in sequence; solution manual §10.1 with the gradient and Hessian computed; Géron 3rd ed. Ch 11 with each optimizer as a runnable call |
| `unit-aml-l08` | Géron 3rd ed. Ch 3 — the confusion-matrix chain run on real predictions |
| `unit-aml-l10` | Géron 3rd ed. Ch 14 — the visual-cortex answer to "why not flatten", and the exercises that ask it back |
| `unit-aml-l11` | Murphy §15.4 attention, §15.5 the block assembled, §15.7 the training objective, §20.5 where embeddings come from; Géron 3rd ed. Ch 16 tokenization, embeddings, attention, the original Transformer, multi-head and masking, exercises 5–6; D2L Ch 11 with exercises after every section |
| `unit-aml-exam-prep` | Murphy, Géron 3rd ed. and D2L Ch 11 routed at exam level so the execution stages can name them; stages became menus and lost `estimate_minutes` |

## Completeness sign-off

- [x] Every file under each declared local root has an inventory row or is covered by its shelf's generated `SOURCES.md` listing.
- [x] The one newly routed web source was opened and verified on 2026-08-22.
- [x] Materials were opened; every page number in this package came from a probe of the local PDF, and two candidate sources were dropped when the probe contradicted them.
- [x] Current and prior scope reconciled: the superseded RNN deck keeps its 2026-08-19 out-of-scope disposition and no added route claims `current`.
- [x] Suspected duplicates checked — and the check overturned a prior disposition: the two Géron files are different editions, recorded above.
- [x] Every added route carries unit, title, format, lecture-specific angle, covers, depth, scope and an exact locator.
- [x] Every rich route names only knowledge nodes declared by its own unit — checked programmatically, 0 unresolved.
- [x] Learner choices: `source_selections` remains `[]` on all eleven lecture units. Only `unit-aml-exam-prep` gained selections, and only because its stages name those sources.
- [x] Exercise gaps and unreachable material are explicit above, not silently filled.
- [x] Every ordinary lecture keeps its own unit; the exam block stays auxiliary.

## What this audit does not claim

It does not claim the lane is finished. It claims that after this package every
AML lecture except three named nodes has material behind each concept it teaches
at a depth you can work rather than only read, and that the one lecture with
nothing behind it now has a derivation layer, an implementation layer and an
exercise set. Whether that material is *good* is a judgement recorded in source
evaluations, not here. No evidence of mastery is asserted anywhere in this
document.
