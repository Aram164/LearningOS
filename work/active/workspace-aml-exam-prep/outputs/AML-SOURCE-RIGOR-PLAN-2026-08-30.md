# AML source-rigor plan — bringing `module-hu-aml` to the SaD standard

**Date:** 2026-08-30 · **Module:** `module-hu-aml` · **Workspace:** `workspace-aml-exam-prep`
**Governing contract:** `system/PLAN-CREATION-SOP.md`, `system/OPERATOR.md` rules 13–17
**Status:** design only. No canonical file is written by this document.

---

## 1. Understanding

Aram asked for the pass SaD received on 2026-08-24 — every source-to-lecture route
carrying an **exact locator**, a **lecture-specific one-line `angle`**, and a long
**`angle_detail`** — applied to AML, plus the sweep that puts a route on every
registered source that covers AML material and is currently routed nowhere.

AML's *breadth* pass is already done: `AML-material-coverage-audit-2026-08-22.md`
opened the shelf, measured coverage per knowledge node, and closed the L11 hole.
What has never run on AML is the *rigor* pass. The two are different jobs and the
second was explicitly deferred (`system/CRITIQUE-POINTS.md` §1: "AML, AMLS, Algo 2,
Python and the exam-prep units have not had this pass").

This plan designs that pass and hands the executor a checkable package sequence. It
does not apply it.

### One correction to the premise

The request assumes the AML gap is "missing detail". Measurement says it is worse
in one specific place: **eleven AML routes already carry page numbers and ten of
them point at the wrong pages** (§4.3 below). Those pass the validator, read as
authoritative, and are off by a fixed per-book offset. They are the first thing
this plan repairs, ahead of the empty ones — a wrong address is worse than a
missing one, which is the same reasoning the SOP gives for refusing to route a
source whose locator cannot be opened.

---

## 2. The gap, measured

Live numbers, taken 2026-08-30 from `warning_baseline.py --check` and a static
re-run of `learning_os.rules.plan_rigor` over both source maps.

| | `module-hu-aml` | `module-hu-m2-statistik-analysis` (SaD+Analysis) |
|---|---|---|
| Sources in the map | 33 | 89 |
| Rich routes | 223 | 486 |
| `ROUTE-ANGLE-DETAIL-MISSING` | **223 (100 %)** | **0** |
| `LOCATOR-VAGUE` | **136 (61 %)** | 42 (9 %) |
| Locators containing a page/section address | 87 (39 %) | 295 (61 %) |
| Routes bound to a `vault_path` | 3 | 277 |

**AML is 359 of the repository's 438 remaining warnings — 82 % of the entire
content debt.** The repo-wide total fell 535 → 438 when SaD was repaired; AML is
what is left.

Vague locators by unit:

| Unit | vague / total | Unit | vague / total |
|---|---|---|---|
| `unit-aml-l01` | 9 / 16 | `unit-aml-l07` | 10 / 18 |
| `unit-aml-l02` | 15 / 18 | `unit-aml-l08` | 15 / 24 |
| `unit-aml-l03` | 13 / 22 | `unit-aml-l09` | 19 / 25 |
| `unit-aml-l04` | 15 / 19 | `unit-aml-l10` | 12 / 22 |
| `unit-aml-l05` | 11 / 17 | `unit-aml-l11` | 2 / 12 |
| `unit-aml-l06` | 14 / 23 | `unit-aml-exam-prep` | 1 / 7 |

By availability: **73 of the 136** vague routes point at a source with a registered
local copy — repairable offline with `tools/material_toc.py`. **63** have no local
copy (web course, video series, paywalled book) and need a dated web verification.

By format: book 56 · video 22 · documentation 18 · course 15 · exercise 14 ·
website 5 · paper 4 · course-material 2.

### The one part of AML that is already at standard

`unit-aml-l11` (2 vague / 12) and `unit-aml-exam-prep` (1 / 7) were rebuilt on
2026-08-22 and their Géron routes are exemplary — `Ch 16 'Attention Mechanisms'
pdf p. 772` is verifiable and correct. Use those rows as the in-module reference
for what a finished AML route looks like. They still lack `angle_detail`.

---

## 3. Authorization

`system/OPERATOR.md` rule 17: an open `CRITIQUE-POINTS` entry is **not** a work
item, and acting on one requires Aram to say so in that session. This plan acts on
§1 ("Plan manipulation and material mapping"), whose 2026-08-24 entry records the
same instruction being given for SaD. **The request that produced this document is
that instruction for AML.** Complaint 1 of §1 (whether plan manipulation is
standardized) stays untouched and the point stays `open`; closing it is Aram's.

---

## 4. What is already settled, and what is not

### 4.1 Settled — do not redo

- **The complete material shelf is inventoried and dispositioned.**
  `AML-exam-execution-plan-coverage-audit-2026-08-19.md` opened and disposed of
  every file under the AML material roots.
- **Node-level coverage is measured and closed.** The 2026-08-22 audit took AML
  from 20 nodes with no practice/implementation route to 6, and from 199 to 223
  routes. Three remaining unserved nodes are named there with reasons
  (`l01-history`, `l03-probabilistic`, `l11-language-task`) and are framing or
  optional-bridge nodes, not gaps.
- **Scope authority is fixed:** current 2026 decks `VL 01`–`VL 11`, then
  `Übung 02`–`Übung 11` and the four Bonusblätter, with the Themen list on
  `Übung 10` slide 3 as the only authoritative scope statement.
- **L11 is Transformers, not RNNs.** `older-lecture-slides/11-rnn_*.pdf` is
  superseded and must never be routed as `current`.

Gate 1 of the SOP is therefore dischargeable for AML **by reference plus a delta
sweep**, not by a fresh inventory. The new coverage audit cites the 2026-08-19 and
2026-08-22 audits as its local-inventory evidence and adds only: (a) the registered
-source sweep of §7, (b) the locator verification log of §6.

### 4.2 Carried items this plan must resolve or restate

| Item | Origin | Disposition here |
|---|---|---|
| SaD lane routed to the Géron 2nd-ed. early release, which lacks Ch 16 | 2026-08-22 audit | out of module boundary — restate as carried, do not fix |
| `source-sutton-barto-rl` sits in the AML map with **0 routes** | measured 2026-08-30 | OPERATOR rule 14 breach: needs an explicit `reference-only` or `deferred` disposition, or removal |
| L11 has no course-owned exercise asset | 2026-08-19, carried | keep as a recorded absence; D2L Ch 11 is a substitute, not the course's sheet |
| Second-sitting duration unconfirmed | 2026-08-22 | unchanged; rehearse 120 min |

### 4.3 New finding — the page-number defect (verified 2026-08-30)

`system/PLAN-CREATION-SOP.md` fixes the convention: **page numbers are PDF pages,
cover = 1.** Printed page numbers are never used alone, because the offset differs
per book — which is the exact ambiguity an exact locator exists to remove.

Eleven AML routes carry page numbers. Checked against each PDF's own outline via
`tools/material_toc.py --toc`:

| Route locator says | Actual PDF page | Offset | Verdict |
|---|---|---|---|
| Murphy `§8.1.3 … pp. 277–281` (`l06`) | §8.1.3 begins **p307** | +30 | **wrong — printed pages** |
| Murphy `§8.3 … pp. 289–291` (`l06`) | §8.3 begins **p319** | +30 | **wrong** |
| Murphy `§8.4.6 … pp. 298–301` (`l06`) | §8.4.6 begins **p328** | +30 | **wrong** |
| Murphy `§11.2.2 … p. 372; §11.2.4 … p. 380` (`l03`) | **p402**; **p410** | +30 | **wrong** |
| Murphy `§15.4 … pp. 518–525` (`l11`) | §15.4 begins **p548** | +30 | **wrong** |
| Murphy `§15.5 … pp. 526–532` (`l11`) | §15.5 begins **p556** | +30 | **wrong** |
| Murphy `§15.7 … pp. 537–546` (`l11`) | §15.7 begins **p567** | +30 | **wrong** |
| Murphy `§20.5 … pp. 705–712` (`l11`) | §20.5 begins **p735** | +30 | **wrong** |
| Murphy aggregate (`exam-prep`) | all of the above | +30 | **wrong** |
| ISLP `§10.3, pp. 406–415` (`l10`) | §10.3 begins **p413** | +7 | **wrong** |
| Géron `Ch 16 … pdf p. 772` etc. (`l01`,`l06`,`l08`,`l10`,`l11`) | **p772** ✔ | 0 | correct |

The Géron rows are right because that ebook has no printed numbers, so PDF pages
were forced. Murphy and ISLP have printed numbers, and those are what was written
down. Same package, two conventions.

**The same defect is in the source registry.** `sources/registry/machine-learning.yaml`
carries printed pages throughout — ISLP `§4.3 (p.138)` is PDF **p147**; Kroese
`§7.2 (p.253)` is PDF **p271**; Murphy `Ch 8 (p.275)` is PDF **p305**. These are
the richest existing evidence for the repair, and **not one of their page numbers
may be copied into a locator without re-deriving it.**

**SaD is clean.** Spot-checked: Fahrmeir `§3.4 … pdf pp. 151-163` → outline says
§3.4 begins p151 ✔; §3.5 → p164 ✔; §3.6 → p168 ✔. The defect is AML's, introduced
on 2026-08-22, two days before the convention was written down.

The validator cannot see this: `LOCATOR-VAGUE` only asks whether *a* page number is
present. No rule change is proposed here — that would be acting on `CRITIQUE-POINTS`
uninvited — but §11 records it as a candidate.

### 4.4 Environment prerequisite — blocking

`tools/material_toc.py --verify` and its printed-TOC fallback shell out to
`pdftotext`, which **is not installed on this machine** (`pdftotext not found`;
poppler absent). `--toc` works, because it reads PDF bookmarks through `pypdf`.

Consequence: books with an embedded outline can be repaired today; books without
one cannot be verified at all. Measured:

| Local material | Outline rows | Repairable with `--toc` today |
|---|---|---|
| `esl.pdf` | 192 | yes |
| `kroese.pdf` | 128 | yes |
| `kelleher.pdf` | 115 | yes |
| `islp.pdf`, `pml1.pdf`, `geron-copy2.pdf` | full | yes |
| `cs229-notes.pdf` | 23 (unnumbered titles + pages) | yes, titles only |
| **`csc411.pdf`** | **none** | **no — blocked** |
| **`Zacharski_…pdf`** | **none** | **no — blocked** |

```bash
brew install poppler
```

Run this before Gate 1. It also restores `--verify`, which is what turns every
other locator in this plan from asserted to checked.

---

## 5. The standard this plan writes to

### 5.1 Locator, per format (SOP §"What exact means", applied to AML)

| Format | AML rule | Good | Bad (current) |
|---|---|---|---|
| `book` | numbered division **and PDF page range**, sub-parts named | `§2.9 Model Selection and the Bias–Variance Tradeoff, pdf pp. 56-60 (σ²/k variance term p. 57)` | `§2.9` |
| `course-material` | file **and** slide range | `lecture-slides/VL 06-gradient_descent.pdf, slides 35-45 (feature scaling)` | `lecture-slides/VL 06-gradient_descent.pdf` |
| `exercise` | file **and** Blatt/Aufgabe/slide | `exercise-slides/Übung 06 .pdf, Blatt 3 Aufgabe 1-3, slides 12-24` | `exercise-slides/Übung 06 .pdf` |
| `video` | quoted episode title, or numbered lecture | `'Gradient Descent, Step-by-Step' (StatQuest, 23 min)` | `Gradient Descent; Stochastic Gradient Descent` |
| `course` | named unit/week as the platform names it, + verification date | `Week 2 'Gradient Descent in Practice I — Feature Scaling' (verified 2026-08-30)` | `Optimization units` |
| `documentation`/`website` | quoted section heading | `'Optimization: Stochastic Gradient Descent', section 'Gradient Descent'` | `Optimization selections` |
| `paper` | section number and page | `§3 'Overfitting Has Many Faces', p. 79` | `Entire essay` |

Every hedge word — *selections, selected, topic-matched, relevant, appropriate,
matching, as needed, assorted, various, related* — is banned outright; the
validator's `_HEDGE_RE` reports them. **38 of the 136 vague AML locators contain
one.**

Three of the flagged rows are rule artifacts rather than bad addresses: the D2L
L11 route and the two Jurafsky Ch 8 routes are precise but trip `LOCATOR-VAGUE`
because `website`/`book` formats need a quoted title or a page. Quoting the
section titles clears them without changing the address.

### 5.2 `angle` — one line, and it must discriminate

`angle` answers: *what does this material do for this lecture that the other
options on this same lecture do not?* A sentence equally true of three other rows
on the same unit is not an angle.

The current AML text fails this most often by describing the **source**, not the
**edge**. Contrast pairs drawn from live rows:

| Unit | Current `angle` | Why it fails | Replacement |
|---|---|---|---|
| `l06` / MML | "The rigorous mathematics of descent directions, step size, momentum, conditioning, and convexity." | equally true of Murphy Ch 8 — the row does not say why you would open MML instead | "The only route that proves *why* the descent direction is the negative gradient; Murphy tells you the algorithm, MML tells you the geometry it comes from." |
| `l06` / MIT 6.036 | "Structured gradient-update and learning-rate practice rather than another long theoretical explanation." | true of every practice row on the unit | "The only autograded route on this lecture: it marks your learning-rate answer, so a divergent run is caught by the grader rather than by you re-reading the slide." |
| `l09` / StatQuest | "A visual conceptual pass over backward credit assignment before or after the algebraic layer rules." | "before or after" is not a judgement | "Twelve minutes that fix the direction of credit assignment before the four layer rules stop being symbols; it never reaches the vectorized form the deck examines." |
| `l02` / ESL §2.3.3 | *(covered by a combined five-section row)* | the crosswalk's single best L02↔L03 tie is buried in a section list | "Frames least squares and k-NN as the two ends of one flexibility axis — the one page that makes L02 and L03 the same question asked twice." |

The deck row is the exception: on every unit `source-aml-ss26-lectures` at
`scope: current` is the scope authority, and its angle should say what the deck
compresses or asserts without deriving, naming which other route repairs it — the
pattern the SaD L03 deck row already uses.

### 5.3 `angle_detail` — the long form, and it must add

Not a restatement. Four things, in this order, in prose:

1. **What the reader actually gets** — the worked example, the derivation, the drill.
2. **What it assumes** — the prerequisite that makes it hard to open cold.
3. **Where it departs from the taught deck** — notation, scope, method.
4. **When to choose something else** — its limit, named. *"Stops before Naive
   Bayes"* is as useful as anything it covers.

Worked example, `unit-aml-l06` ← `source-mml` Ch 7:

> Chapter 7 treats the update as a consequence rather than a recipe: the descent
> direction is derived from the first-order Taylor expansion, and the step-size and
> momentum discussion is a convergence argument, not a tuning tip. It assumes the
> matrix calculus of Chapters 2 and 5 — if the gradient of a quadratic form is not
> already automatic, read §5.1–5.3 first or the chapter will read as notation. It
> departs from the deck in that it never runs an optimizer on data; there is no
> loss curve and no learning-rate diagnostic anywhere in it. Choose Murphy Ch 8
> when you want the algorithm and its failure modes, Géron Ch 11 when you want the
> call, and this only when "why is it the *negative* gradient" is the question.
> Note also that MML has no k-NN and no logistic regression — do not follow it out
> of this lecture.

Three AML-specific rules for `angle_detail`:

- **Name the cross-module wire where one exists.** SaD 03's `k=(AᵀA)⁻¹Aᵀy` *is*
  AML L04's `w=(XᵀX)⁻¹Xᵀy`; SaD 08's MLE→MSE is the engine AML L05 re-runs with
  Bernoulli. These are recorded in `note-aml-sad-master-wiring` and
  `note-regression-sad-aml-islp-bridge` — reference them, never restate them.
- **Name SVM contamination.** AML L07 teaches **no SVM** (slide-verified). ISLP
  Ch 9, ESL Ch 12, Murphy 17, MML Ch 12, Kroese §7.7 and the CS229 SVM chapter all
  reach kernels through the margin. Every kernel route must say which part to skip.
- **Name the prior-year trap.** Any route touching L11 must state that the older
  RNN deck is superseded, and any RNN-era section of a book (ISLP §10.5, Murphy
  §15.2, D2L 11.4, Géron Ch 16 Q8–Q9) must be marked out of 2026 scope.

---

## 6. The mapping — per unit

Legend for the repair tables: **P** = repairable from the local PDF outline today ·
**W** = needs a dated web verification · **B** = blocked until poppler is installed.

Target locators below marked ✔ were derived on 2026-08-30 from the PDF's own
outline and are correct PDF pages. Everything else is a **target to verify**, not a
verified fact.

### 6.1 `unit-aml-l01` — Introduction & ML Problem Formulation

Nodes: `history` · `formulation` · `data` · `generalization` · `prerequisites`.
16 routes, 9 vague. This unit's problem is that six of its rows are orientation
reads that all sound alike.

**Angle spine — the discriminating sentence per row**

| Source | What only this row gives L01 |
|---|---|
| `aml-ss26-lectures` (deck) | the examinable concept map and the lecturer's dataset notation; everything else is commentary on it |
| `aml-ss26-lectures` (LA primer) | a 36-page **diagnostic**, not a lecture — its purpose is to fail you somewhere so you know where to go |
| `lineare-algebra-archive` | the only material that can *test* what the primer diagnoses — solved Übungen and a solved Klausur |
| `islp` Ch 2 | the U-shaped test-error picture, which is the one L01 idea that returns in L02, L04 and L09 |
| `domingos-useful-things` | the field's own account of why generalization is the whole problem — an essay, not a chapter, read once and never again |
| `geron-handson` Ch 2 | the workflow as executable code: the only row where "ML problem formulation" becomes a script |
| `geron-handson` Ch 10 | the historical chain as one causal story rather than a list of names |
| `rohrer-e2eml` Ch 3–4 | loss and the train/val/test split explained at the speed of someone who has never seen them |
| `kelleher-fmlpda` | the four-families taxonomy that SaD 12–15 is built on — this is the SaD bridge, not an AML read |
| `sad-ss26-lectures` L11 | the same content in the other exam's vocabulary; the metrics slides 23–38 are literally repeated in AML L08 |
| `3b1b-linear-algebra` | vectors and matrix multiplication as pictures, for the primer's failures only |
| `3b1b-neural-networks` #1 | a preview of where the course ends, to make L01's framing land |
| `mit-6036` intro unit | the only autograded row |
| `caltech-lfd` HW1 | the only row that asks a formal generalization question with a key |
| `kroese-dsml` intro | rigor tier; a statistician's phrasing of the same setup |

**Locator repair**

| Source | Current | Target | St |
|---|---|---|---|
| `islp` | `Chapter 2, especially §§2.1–2.2` | `§2.1 What Is Statistical Learning?, pdf pp. 20-36; §2.2 Assessing Model Accuracy, pdf pp. 37-48 (bias-variance §2.2.2 p. 41 ✔, classification setting §2.2.3 p. 44 ✔)` | P |
| `kroese-dsml` | `Introductory ML and evaluation selections` | resolve to Ch 1 + `Classification Metrics` pdf p. 271 ✔ | P |
| `mit-6036` | `Introduction and representations units` | name the OLL unit titles as the nav shows them + verification date | W |
| `3b1b-neural-networks` | `Video 1` | `'But what is a neural network?' (chapter 1, 19 min)` | W |
| `3b1b-linear-algebra` | `Targeted playlist chapters only` | `'Vectors' (ch 1), 'Linear combinations, span, and basis vectors' (ch 2), 'Matrix multiplication as composition' (ch 4)` | W |
| `geron-handson` Ch 2 | `Chapter 2 selected workflow sections` | `geron-copy2.pdf Ch 2, pdf pp. …` — named headings, no hedge | P |
| `caltech-lfd` | `Introductory homework selections` | `Homework 1, problems 1-8, with the posted solution key` | W |
| `kelleher-fmlpda` | `Introductory chapters` | `Ch 1 Machine Learning for Predictive Data Analytics, pdf pp. …` | P |
| `domingos-useful-things` | `Entire essay` | `§3 'Overfitting Has Many Faces' and §6 'Intuition Fails in High Dimensions'` + page | W |

---

### 6.2 `unit-aml-l02` — k-Nearest Neighbors

Nodes: `representation` · `algorithm` · `distance` · `dimensionality` ·
`bias-variance` · `validation`. **15 of 18 vague — the worst ratio in the module.**

**Angle spine**

| Source | What only this row gives L02 |
|---|---|
| deck | 2026 scope: vector embeddings, lazy-learning cost, Lp distances, sensitivity to irrelevant features |
| `Übung 02` (= Blatt 1) | the course's own k-NN tasks in the lecturer's marking notation |
| `zusatz-blatt01` | the bonus sheet, pre-solved |
| `esl` §2.3.2–2.3.3 | **the flexibility spectrum**: least squares and k-NN as one axis — the single best L02↔L03 tie in print |
| `esl` §2.9 | derives the k-NN variance term **σ²/k**, turning "variance ∝ 1/k" from slogan into formula |
| `esl` §7.2–7.3 | the rigorous `MSE = Bias² + Var + σ²` decomposition done for k-NN *and* linear regression, with a worked example |
| `esl` §7.10 | why k-fold works, rather than how to run it |
| `esl` §13.3 | applied k-NN with decision-boundary pictures |
| `islp` §2.2.2–2.2.3 | the gentle U-curve entry; §3.5 is the explicit k-NN-vs-regression comparison; §5.1 is the CV machinery for choosing k |
| `murphy-pml1` §16.1 | k-NN placed inside exemplar-based methods, with the curse of dimensionality argued; §4.7.6 adds the caveat the deck omits — the decomposition **does not hold for 0-1 loss** |
| `cs229-notes` | bias defined as "test error with infinite training data"; **has no k-NN at all** — this row is the bias-variance half only |
| `csc411-notes` | the compact second telling, one sitting |
| `kroese-dsml` | the statistician's phrasing of k-NN and CV |
| `cs231n-notes` | the only row that runs k-NN on images and shows a validation split as code |
| `statquest` | two short videos that separate bias from variance before any algebra |
| `cs4780-homeworks` HW1 | the exact curse-of-dimensionality drill, with solutions |
| `caltech-lfd` HW4/HW6 | formal validation and overfitting problems with keys |
| `domingos-useful-things` | the essay's dimensionality section |
| `zacharski-data-mining` | the friendliest possible first pass; below exam level |

**Locator repair** — the five-section ESL row and the four-section ISLP row must be
**split into one route per section**, because their angles differ (spectrum vs
variance term vs decomposition vs applied vs CV) and a single row cannot carry
five angles.

| Source | Current | Target | St |
|---|---|---|---|
| `esl` | `§§2.3.2–2.3.3, §2.9, §§7.2–7.3, §7.10, §13.3` | split into 5 routes: §2.3.2 pdf p. 33 ✔ / §2.3.3 pdf p. 35 ✔ / §2.9 pdf p. 56 ✔ / §7.2 pdf p. 238 ✔ + §7.3 pdf p. 242 ✔ (+§7.3.1 p. 245 ✔) / §7.10 pdf p. 260 ✔ / §13.3 | P |
| `islp` | `§§2.2.2–2.2.3, §3.5, §4.7.6, §5.1 including §5.1.4` | split into 3: §2.2.2 pdf p. 41 ✔ + §2.2.3 p. 44 ✔ / §3.5 pdf p. 120 ✔ / §5.1 pdf p. 210 ✔ (§5.1.3 p. 214 ✔, §5.1.4 p. 216 ✔); §4.7.6 pdf p. 192 ✔ is a *lab*, route it as `implementation` | P |
| `murphy-pml1` | `§16.1; §4.7.6` | `§16.1 K nearest neighbor (KNN) classification, pdf p. 577 ✔`; `§4.7.6`, pdf page to derive | P |
| `csc411-notes` | `§3.4 and §8.4` | **blocked** — no PDF outline; needs `--verify` after poppler | B |
| `kroese-dsml` | `§7.6 and §2.5.2` | `'K-Nearest Neighbors Classification' pdf p. 285 ✔`; §2.5.2 page to derive | P |
| `cs229-notes` | `§8.1 and §9.3` | outline is unnumbered: use `'Bias-variance tradeoff' pdf p. …` heading form | P |
| `cs229-2022-videos` | `Bias-variance and model-selection lecture` | `Lecture 10 — 'Bias-Variance, Regularization'` + schedule verification date | W |
| `mit-6036` | `Nearest-neighbour/model-selection units` | OLL unit titles as shown in the nav | W |
| `cs231n-notes` | `Image Classification: k-NN and validation` | quote the headings: `'Image Classification', sections 'Nearest Neighbor Classifier' and 'Validation sets for Hyperparameter tuning'` | W |
| `statquest` | `Bias and Variance; Cross Validation` | quote both titles exactly as published | W |
| `caltech-lfd` | `HW4 and HW6 selected problems` | name the problem numbers | W |
| `cs4780-homeworks` | `2017/2018 HW1 selected problems and solutions` | `2018Fall HW1, problems 1-3` + the local file path | P |
| `domingos-useful-things` | `Sections on dimensionality, representation, and generalization` | section numbers + pages | W |
| `zacharski-data-mining` | `Similarity and nearest-neighbour sections` | **blocked** — no outline | B |

---

### 6.3 `unit-aml-l03` — Linear Regression · 13 / 22 vague

Nodes: `problem` · `loss` · `solution` · `linear-algebra` · `vectorization` ·
`probabilistic`.

**Angle spine.** The discriminator on this lecture is *which object is derived*:
the estimator, the geometry, or the probabilistic justification.

| Source | What only this row gives L03 |
|---|---|
| deck | scope + the notation the exam marks in |
| `Übung 03`, `zusatz-blatt01/02` | the course's own regression tasks, with the Besprechung as the marking proxy |
| `cs229-notes` §LMS → normal equations → probabilistic | the one document that derives GD, the normal equation by matrix calculus, **and** why squared error is MLE under Gaussian noise, in the notation of the video spine |
| `murphy-pml1` §11.2.2 | least squares stated as a negative log-likelihood — the bridge L03's optional `probabilistic` node needs |
| `islp` §3.1–3.2 | the only route that adds *inference* — SE, CI, t-tests on β̂ — which is the SaD 09/10 layer, not AML's |
| `esl` §3.2 | the geometric/projection account |
| `mml` Ch 9 | regression as MLE with full matrix calculus; the MAP part is Ridge, so it pre-pays L04 |
| `csc411-notes` Ch 2 | derives GD for regression inline — the cheapest pre-L06 read |
| `kroese-dsml` | statistical cross-check |
| `3b1b-linear-algebra` | the picture under `(XᵀX)⁻¹Xᵀy`: matrix multiplication as composition, projection |
| `setosa-ols` *(not yet routed — see §7)* | the interactive residual-square widget: the only route where moving the line changes the loss in front of you |
| `bendersky-normal-equation` *(not yet routed)* | two independent derivations of the normal equation, side by side |
| `statquest` | R² and least squares as three short videos |
| `ng-coursera` Wk 1–2 | the gentler taught twin, same slides' vocabulary |
| `geron-handson` Ch 4 | the executable layer plus Appendix-A solutions |
| `caltech-lfd` HW2, `cs4780` HW6 | the two solved regression problem sets |
| `mit-6036` | autograded |
| `domingos-useful-things` | the overfitting framing |

**Locator repair**

| Source | Current | Target | St |
|---|---|---|---|
| `islp` | `§§3.1–3.3` | `§3.1 pdf p. 79 ✔, §3.2 pdf p. 89 ✔` (drop §3.3 or justify it — it is diagnostics, past the deck) | P |
| `esl` | `Chapter 3 selected sections` | `§3.2 Linear Regression Models and Least Squares, pdf pp. …` — hedge removal is mandatory | P |
| `murphy-pml1` | `Chapter 11 selected sections` | `§11.2 Least squares linear regression, pdf p. 401 ✔` | P |
| `murphy-pml1` | `§11.2.2 … p. 372; §11.2.4 … p. 380` | **wrong pages** → `§11.2.2 pdf p. 402 ✔; §11.2.4 pdf p. 410 ✔` | P |
| `kroese-dsml` | `Regression selections` | `'Linear Regression' pdf p. 187 ✔` | P |
| `mml` | `Chapter 9` | Ch 9 §§9.1–9.2 + pages; no local copy → cite the free PDF edition and date it | W |
| `cs229-notes` | `§§1.1–1.3` | `'LMS algorithm' pdf p. 10 ✔, 'The normal equations' pdf p. 14 ✔, 'Probabilistic interpretation' pdf p. 16 ✔` | P |
| `mit-6036` | `Regression units` | OLL unit titles | W |
| `statquest` | `Linear Regression; Least Squares; R-squared` | quote exact published titles | W |
| `3b1b-linear-algebra` | `Dot products, matrix multiplication, projections` | chapter numbers + titles | W |
| `geron-handson` | `Chapter 4 linear-regression sections and exercises` | `geron-copy2.pdf Ch 4 'Linear Regression' pdf p. …, Exercises pdf p. …` | P |
| `caltech-lfd` | `Homework 2 and solution key` | problem numbers | W |
| `ng-coursera` | `Regression lessons in Weeks 1–2` | exact lesson titles | W |
| `domingos-useful-things` | `Sections on generalization and overfitting` | section numbers + pages | W |

---

### 6.4 `unit-aml-l04` — Non-linear Regression · 15 / 19 vague

Nodes: `multivariate` · `normal-equation` · `basis` · `overfitting` · `ridge` · `lasso`.

**Angle spine.** Two halves — basis expansion and shrinkage — and most rows serve
only one. Say which.

| Source | What only this row gives L04 |
|---|---|
| deck | scope; and the fact that SaD 03's `k=(AᵀA)⁻¹Aᵀy` **is** this lecture's `w=(XᵀX)⁻¹Xᵀy` |
| `esl` §3.4.1–3.4.3 | the rigorous shrinkage treatment: the SVD view of ridge, and *why* the lasso is sparse |
| `islp` §7.1 + §6.2.1–6.2.2 | the diamond-vs-circle geometry; **§7.1 only** — splines and subset selection are past the deck |
| `cs229-notes` kernel-methods feature maps + regularization | `Jλ = J + λR(θ)` and the `θ ← (1−λη)θ − η∇J` derivation, which *is* the L09 weight-decay update |
| `csc411-notes` §3 + §3.2 | the single most on-scope match for the exact arc nonlinear → overfitting → regularization |
| `murphy-pml1` Ch 11 | ridge as MAP under a Gaussian prior |
| `mml` Ch 9 MAP part | the same statement done as mathematics |
| `kroese-dsml` `Regularization` | rigor tier, pdf p. 234 ✔ |
| `statquest` | the Ridge → Lasso → Elastic Net trilogy — the best video entry to shrinkage anywhere |
| `ng-coursera` Wk 3 | the taught twin |
| `geron-handson` Ch 4 | Ridge/Lasso as runnable calls with Appendix-A answers |
| `caltech-lfd` HW4/HW6, `cs4780` HW6/HW6-P3 | the two solved regularization sets, one of them weighted ridge |
| `mit-6036` | autograded feature/regularization units |
| `cs229-2022-videos` L10 | the taught bias-variance-regularization lecture |
| `domingos-useful-things` | feature engineering as the field's actual bottleneck |

**Locator repair** — all fifteen rows above the deck are vague. Highest-value first:
`esl §3.4.1 pdf p. 80 ✔, §3.4.2 pdf p. 87 ✔, §3.4.3 pdf p. 88 ✔` (and mark §3.4.4
LAR as beyond scope); `islp §6.2.1 pdf p. 248 ✔, §6.2.2 pdf p. 252 ✔, §7.1 pdf
p. 298 ✔`; `kroese 'Regularization' pdf p. 234 ✔`; `csc411` blocked until poppler.

---

### 6.5 `unit-aml-l05` — Logistic Regression · 11 / 17 vague

Nodes: `classification` · `boundary` · `sigmoid` · `likelihood` · `cross-entropy` ·
`gradient`.

The deck's own evaluation calls this the semester's deepest cross-wire: slides
40–62 run MLE → cross-entropy in full, and slides 5–9 are the three-step
construction. Every book row must be positioned against that derivation.

| Source | What only this row gives L05 |
|---|---|
| deck sl. 5–9 / 40–62 | the construction and the full derivation, in exam notation |
| `Übung 06` (= Blatt 3) | the course's own logistic tasks |
| `islp` §4.3 | odds and the logit — the interpretation layer the deck skips |
| `esl` §4.4 | the MLE fit, but by **Newton–Raphson/IRLS, not gradient descent** — say so, or the reader mis-maps it onto L06 |
| `murphy-pml1` §10.2.3–10.2.5 | the cleanest "cross-entropy from MLE → gradient → SGD" arc in print; §10.2.5 gives the perceptron as logistic with a hard threshold, which is the L05→L07 hinge |
| `cs229-notes` logistic + GLM | the log-likelihood gradient `(y−h)·x`, and the GLM answer to *why the sigmoid* — nothing else on the shelf answers that |
| `kroese-dsml` | logistic with its softmax generalization, pdf p. 284 ✔ |
| `csc411-notes` §8.6 | why you cannot just use linear regression for classification |
| `statquest` MLE video | re-watch with Bernoulli in mind — cross-wire #5 |
| `geron-handson` Ch 4 | logistic/softmax as code |
| `ng-coursera` Wk 3 | sigmoid, boundary, cost, taught |
| `cs4780` 2018Fall HW4 P3 | **the exact drill**: gradient of the logistic log-likelihood, with solution |
| `mit-6036` | autograded |
| `cs229-2022-videos` L3 (+L4 for GLMs) | the taught derivation |

Repairs: `islp §4.3 pdf p. 147 ✔ (§4.3.1 p. 148 ✔, §4.3.4 p. 151 ✔)`;
`esl §4.4 pdf p. 138 ✔ (§4.4.1 p. 139 ✔)`; `kroese pdf p. 284 ✔`;
`cs229-notes 'Logistic regression' pdf p. 21 ✔`; `Übung 06 .pdf` needs its Blatt
and Aufgabe numbers.

---

### 6.6 `unit-aml-l06` — Gradient Descent · 14 / 23 vague, **and 4 wrong-page rows**

Nodes: `gradient` · `batch-gd` · `rate-scaling` · `stochastic` · `convexity` ·
`optimizers` · `newton`.

This is the unit where the 2026-08-22 package did its best work and where the page
defect bites hardest — four of its rows are 30 pages off.

| Source | What only this row gives L06 |
|---|---|
| deck sl. 19 / 35–45 | linear and logistic gradients in one frame; the feature-scaling block |
| `murphy-pml1` §8.1.3 | the convexity condition the deck asserts, with the PSD-Hessian test that decides it |
| `murphy-pml1` §8.3 | the curvature-aware update, and the price of the Hessian (BFGS, trust regions) |
| `murphy-pml1` §8.4.6 | AdaGrad → RMSProp → Adam built in sequence from one moving-average idea, so bias correction stops being a formula |
| `murphy-pml1` solutions §10.1 | the one place the convexity claim and the Newton update are **computed** rather than asserted |
| `cs229-notes` LMS | batch GD and SGD derived from scratch in the video spine's notation |
| `mml` Ch 7 | why the direction is the negative gradient — geometry, not algorithm |
| `csc411-notes` §2 | GD derived inline for regression, in one sitting |
| `geron-handson` Ch 11 | each optimizer as a runnable call; **also double-pays the AMLS project** |
| `ng-coursera` GD in Practice I/II | feature scaling and learning-rate diagnosis, matching the slides almost line for line |
| `eecs498` L4 | SGD → momentum → AdaGrad → Adam → second-order: exactly the deck's outlook including Newton |
| `cs231n-notes` | the "walking downhill" framing plus a code-level SGD |
| `statquest` | two short videos on the update and on stochastic sampling |
| `3b1b-linear-algebra` | the dot-product picture under the gradient |
| `islp` §10.7 | **not a primary**: ISLP has no standalone GD chapter; a compact review only |
| `mit-6036` | the only autograded learning-rate practice |
| `distill-momentum` *(not yet routed — §7)* | the one interactive explanation of why momentum works |
| `3b1b-essence-of-calculus` *(not yet routed — §7)* | the derivative prerequisite, already used this way on SaD L03 |

**Page corrections (mandatory):**
`§8.1.3 pp. 277–281 → pdf pp. 307–311` · `§8.3 pp. 289–291 → pdf pp. 319–321` ·
`§8.4.6 pp. 298–301 → pdf pp. 328–331` · momentum `§8.2.4 pp. 287–288 → pdf
pp. 317–318` *(derive)* · `islp §10.7 → pdf p. 434 ✔`.

---

### 6.7 `unit-aml-l07` — Linear Classifiers · 10 / 18 vague

Nodes: `linear-geometry` · `perceptron` · `dual` · `xor` · `kernels` · `rbf` ·
`multiclass`.

**The defining constraint of this unit: the lecture teaches no SVM.** Every kernel
row must name the part to skip, or the reader walks into margin theory that is not
examined.

| Source | What only this row gives L07 |
|---|---|
| deck (94 sl.) | primal **and** dual perceptron, convergence, XOR, the 2-D kernel worked example, RBF, one-vs-rest |
| `Übung 07` | the perceptron tutorial in course notation |
| `zusatz-blatt04` Aufg. 1–2 | pre-solved perceptron work |
| `esl` §4.5.1 | Rosenblatt's algorithm **with the convergence result** — one of only two book homes for the actual algorithm, pdf p. 149 ✔ |
| `cs229-notes` perceptron digression + kernel methods | **the only source that develops feature maps → kernel trick → kernel properties without the SVM** — exactly the lecture's route (`'Feature maps' pdf p. 50 ✔`, `'LMS with the kernel trick' pdf p. 51 ✔`, `'Properties of kernels' pdf p. 55 ✔`; **stop before `'Support vector machines' pdf p. 61 ✔`**) |
| `murphy-pml1` §10.2.5 | the perceptron as logistic regression with a hard threshold — the cleanest link back to L05, pdf p. 376 ✔ |
| `islp` §9.4 | multiclass only; §9.3 is SVM and is enrichment at best (`§9.3 pdf p. 384 ✔`, `§9.4 pdf p. 390 ✔`) |
| `ng-coursera` Wk 7 Kernels I/II | **the landmark/similarity construction on deck slides 68–73 is Ng's** — the closest taught match that exists |
| `mit-6036` perceptron unit | autograded perceptron traces — the exam's own format |
| `cs4780` HW2 | perceptron problems across three semesters, solutions local; HW7 kernel parts only |
| `mit-6034-quizzes` | perceptron/gate problems in written-exam format |
| `statquest` | 'The Kernel Trick' as intuition |
| `3b1b-linear-algebra` | dot products and change of basis, under `w·x = 0` |
| `csc411-notes` | compact second telling |
| `mueller-kernel-tutorial` *(not yet routed — §7)* | a kernel introduction that is not a textbook chapter |

---

### 6.8 `unit-aml-l08` — Feedforward Neural Networks · 15 / 24 vague

Nodes: `xor-stacking` · `forward` · `activations` · `output` · `softmax` · `metrics`.

Two facts should shape every angle here: the deck's forward-pass worked example
**shares its numbers with L09's backprop example**, and the metrics block is a
literal repeat of SaD 11 plus new multi-class averaging.

| Source | What only this row gives L08 |
|---|---|
| deck sl. 41 / 43–51 / 60–80 | the proof that two linear layers collapse to one; output layers by task; the metrics block |
| `zusatz-blatt04` Aufg. 3–4 | pre-solved, and sitting in the L07 folder — easy to miss |
| `murphy-pml1` §13.2 | the XOR-solved-by-stacking story plus the definitive activation reference (saturation, why ReLU), pdf p. 456 ✔ |
| `cs229-notes` NN §7.1–7.2 + §7.4 | builds one neuron → multi-layer ReLU-first, exactly the deck's order; §7.4 is the vectorization over examples |
| `islp` §10.1–10.2 | forward pass **with explicit parameter counting** — an AML *and* SaD exam target (`§10.1 pdf p. 407 ✔`, `§10.2 pdf p. 409 ✔`) |
| `kroese-dsml` `Feed-Forward Neural Networks` pdf p. 344 ✔ | the forward pass in rigorous matrix notation — use it to check shapes |
| `kroese-dsml` metrics pdf p. 271 ✔ | the metrics half, stated statistically |
| `esl` §11.3–11.5 | the historical/statistical account (`§11.3 pdf p. 411 ✔`, `§11.4 p. 414 ✔`, `§11.5 p. 416 ✔`) |
| `geron-handson` Ch 3 | **the confusion-matrix chain run on real predictions** — pdf p. 164 ✔, precision/recall p. 167 ✔, ROC p. 173 ✔ |
| `3b1b-neural-networks` #1–2 | the picture before the algebra |
| `sad-ss26-lectures` L15 | the 'drop φ' slide: a 1-layer ANN with identity activation **is** multivariate linear regression, plus the parameter-counting formula |
| `kelleher-fmlpda` Ch 7 | error surfaces and learning rates in SaD's framing |
| `goodfellow-dl` Ch 6 | the canonical reference depth |
| `cs4780` HW9, `mit-6034` NN quizzes | forward-pass and net-tracing drills |
| `mit-6036` | autograded |
| `statquest` NN Pt. 1 | first exposure |
| `csc411-notes` §3.3, §8.3 | compact second telling — **blocked** |

---

### 6.9 `unit-aml-l09` — Backpropagation & Training · **19 / 25 vague, the worst count**

Nodes: `graph` · `chain-rule` · `backprop` · `regularization` · `stopping` ·
`gradient-health` · `autograd`.

The deck **owns** NN regularization (weight decay, dropout, early stopping, double
descent) — these live here, not in L04. It has **no batch normalization**; several
routed sources do, and every one must say so.

| Source | What only this row gives L09 |
|---|---|
| deck sl. 71–74 | the λ⁷ vanishing/exploding argument, and the worked example carried over from L08, closing in PyTorch |
| `murphy-pml1` §13.3–13.5 | **the only book that teaches backprop the way the deck does** — reverse-mode autodiff on a computation graph (§13.3.4 pdf p. 474 ✔); §13.5 pdf p. 485 ✔ covers all three regularizers under one roof |
| `cs229-notes` §7.3 + double descent | the closest written derivation of the four layer rules; the second double-descent treatment |
| `islp` §10.7–10.8 | **§10.8 pdf p. 439 ✔ is one of only two book treatments of double descent**, with the interpolation-threshold picture |
| `kroese-dsml` §9.3 | the four backward rules in rigorous matrix notation — the shape-checking route |
| `mml` §5.6 | the chain-rule mathematics *under* the rules, for "I can apply them but do not see why they hold" |
| `karpathy-micrograd` | builds computation graphs and `loss.backward()` from scratch — the deepest self-checking test on the shelf |
| `pytorch-tutorials` autograd | the autograd node as documentation |
| `3b1b-neural-networks` #3–4 | backprop and its calculus as pictures |
| `eecs498` L6 | computational graphs and the matrix-multiply example — taught the deck's way |
| `geron-handson` Ch 11 | training deep nets as code |
| `esl` §11.4–11.5 | the older statistical account of fitting and its issues |
| `goodfellow-dl` Ch 7–8 | reference depth on regularization and optimization |
| `d2l` | autodiff, weight decay and dropout with runnable code and exercises |
| `cs4780` HW9, `mit-6034` | backprop-tracing drills |
| `statquest` | the direction of credit assignment, in twelve minutes |
| `sad-ss26-lectures` L15 | the gentler backprop overview to read *before* the full machinery |
| `kelleher-fmlpda` Ch 7 | weight decay in the error-surface framing |
| `mit-ocw-nn-training`, `belkin-double-descent` *(not routed — §7)* | initialization/vanishing gradients; the primary paper behind §10.8 |

---

### 6.10 `unit-aml-l10` — Convolutional Neural Networks · 12 / 22 vague

Nodes: `motivation` · `convolution` · `shapes` · `pooling` · `network` ·
`architectures`. The deck is **unusually quiz-dense** — five in-deck quizzes — which
is a scope signal every practice row should exploit.

| Source | What only this row gives L10 |
|---|---|
| deck (70 sl.) | scope, and the five in-deck quizzes; closes on residual connections, which L11 reuses |
| `Übung 11` | the course's own CNN tasks |
| `murphy-pml1` §14.1–14.3 | **§14.3 pdf p. 509 ✔ is the deck's famous-architecture list one-to-one** (LeNet, AlexNet, GoogLeNet, ResNet); §14.2.1 has the full `(n+2p−f)/s+1` arithmetic. §14.2.4 batch norm is **not** in the deck |
| `islp` §10.3 | the gentle full CNN pass; **§10.3.4 data augmentation is the theory behind AMLS Task 1.3** (`§10.3 pdf p. 413 ✔`, `§10.3.1 p. 414 ✔`, `§10.3.2 p. 417 ✔`, `§10.3.4 p. 418 ✔`) |
| `geron-handson` Ch 14 | the visual-cortex answer to "why not flatten" (pdf p. 620 ✔) and the exercises that ask it back (pdf p. 694 ✔) |
| `cs231n-notes` | the standard written CNN reference, with exam-style parameter counting |
| `cs231n-2017-videos` **or** `eecs498` L7–L8 | pick one architecture track, not both |
| `esl` §11.7 pdf p. 423 ✔ | LeCun's 1989 ZIP-code nets — weight sharing being invented; twenty fun minutes, zero exam obligation |
| `rohrer-e2eml` Ch 14 | 1-D/2-D convolution arithmetic as a warm-up before any network |
| `goodfellow-dl` Ch 9 | reference depth |
| `d2l`, `pytorch-tutorials` | the runnable layer |
| `kroese-dsml`, `csc411-notes`, `cs229-notes` | **CS229 notes have no CNN treatment at all** — this row should be deleted or re-scoped, not repaired |
| `patrick-loeber-pytorch-cnn` *(not routed — §7)* | a CIFAR-10 build to compare against the project code |

**Note the deletion candidate.** `source-cs229-notes → unit-aml-l10` is currently
`CNN overview selections`. The registry's own evaluation says "No k-NN, no CNN."
A route whose locator cannot be opened is worse than an absence — remove it or
demote it with an honest angle.

---

### 6.11 `unit-aml-l11` — Transformers · 2 / 12 vague, but **4 wrong-page rows**

Already breadth-complete. Three jobs only:

1. Correct the four Murphy pages: `§15.4 pp. 518–525 → pdf pp. 548–555` ·
   `§15.5 pp. 526–532 → pdf pp. 556–562` · `§15.7 pp. 537–546 → pdf pp. 567–576` ·
   `§20.5 pp. 705–712 → pdf pp. 735–742`. (Starts ✔ from the outline; end pages to
   confirm.)
2. Quote the D2L section titles and give Jurafsky Ch 8 a page range, clearing the
   two artifact warnings without changing either address.
3. Write `angle_detail` for all twelve — including the standing warnings that the
   older RNN deck is superseded, that Géron Ch 16 Q8–Q9 are RNN tasks, and that
   D2L 11.4 is RNN-era.

**Breadth note.** L11 has 12 routes over **5 distinct sources**, against 13–23 on
every other lecture. The sweep in §7 should look hardest here: Jurafsky Ch 3
(n-gram LMs, the framing behind slides 4–9) is named in the registry and routed
nowhere.

---

### 6.12 `unit-aml-exam-prep` — 1 / 7 vague

Nodes: `scope` · `calibration` · `classical` · `neural` · `integration` ·
`error-control` · `logistics`. Its Murphy aggregate row inherits every page error
above and must be regenerated after the lecture rows are fixed, not before.

The strongest sweep candidate in the whole module lands here: **`source-berkeley-cs189`
— past exams with solutions**, registered and routed nowhere. The module has no
HU Altklausuren, so an external solved exam bank is worth more than another book.

---

## 7. The sweep — registered sources covering AML material that route nowhere

SaD's pass added **44 routes** from an audit of all registered sources against its
15 units. AML has never had that audit: its 2026-08-19 boundary was the AML
material shelf, and 2026-08-22 measured node coverage inside the 33 sources
already in the map.

**246 sources are registered. 33 are in the AML map. One of those 33
(`source-sutton-barto-rl`) carries zero routes.**

The candidates below are ranked by what they would add that nothing on the unit
currently does. Every row is an **ASSUMPTION about fit** — the registry record was
read, the material was not opened. Gate 1 must open each one before it is routed,
and any that does not survive the probe gets an exclusion row, not a quiet drop.

| Candidate source | Unit(s) | The angle it would fill | Priority |
|---|---|---|---|
| `source-berkeley-cs189` | `exam-prep`, L02–L09 | past ML exams **with solutions** — the module has no Altklausuren at all | **1** |
| `source-cs229-problem-sets` | L03–L09, `exam-prep` | the derivation drills and practice midterms the notes' chapters do not carry | **1** |
| `source-belkin-double-descent` | L09 | the primary paper behind ISLP §10.8; the deck teaches double descent and no route reaches its source | **1** |
| `source-3b1b-essence-of-calculus` | L06 (prerequisite) | the derivative meaning under the optimizer — already used exactly this way on SaD L03 | **1** |
| `source-setosa-ols` | L03 | the only interactive residual-square/leverage widget; already routed on SaD L03 | 2 |
| `source-bendersky-normal-equation` | L03, L04 | two side-by-side derivations of the normal equation; already routed on SaD L03 | 2 |
| `source-distill-momentum` | L06 | the one interactive account of why momentum works — the deck states it | 2 |
| `source-marsland-ml-algorithmic` (**local**) | L02, L07, L08, L10 | a local algorithmic-perspective text, probed in 2026-08-22 only for transformers and then left unrouted | 2 |
| `source-fortmann-roe-bias-variance` | L02 | the essay the legacy crosswalk named as the best short bias-variance read | 2 |
| `source-mueller-kernel-tutorial` | L07 | a kernel introduction that is not an SVM chapter — rare, and this lecture needs exactly that | 2 |
| `source-jurafsky-slp3` Ch 3 | L11 | n-gram language models: the framing behind slides 4–9; only Ch 8 is routed | 2 |
| `source-nielsen-nndl` | L08, L09 | the free web book that derives backprop with an interactive feel | 3 |
| `source-prince-udl` | L08–L11 | a current DL text; would need a scope decision against Goodfellow | 3 |
| `source-mit-18s096-matrix-calculus` | L03, L06, L09 | matrix calculus as its own subject, under the normal equation and the layer rules | 3 |
| `source-mit-1806` (Strang) | L01, L03 | the linear-algebra prerequisite as a taught course, not a primer | 3 |
| `source-patrick-loeber-pytorch-cnn` | L10 | a CIFAR-10 build to diff against the AMLS project code | 3 |
| `source-islp-community-solutions` | L02–L10 | answers for the ISLP exercises already routed with no key | 3 |
| `source-mitx-686x`, `source-google-ml-crash-course`, `source-sklearn-user-guide` | various | second practice/implementation rails; route only where a node is thin | 4 |
| `source-bishop-prml`, `source-mohri-foundations-ml`, `source-ssbd-understanding-ml`, `source-boyd-convex-optimization`, `source-nocedal-wright`, `source-schoelkopf-smola-lwk` | L02, L04, L06, L07 | graduate depth; each needs an explicit "past the exam" scope flag or it becomes a trap | 4 |
| `source-hinton-nnml`, `source-nyu-dl`, `source-mit-6s191`, `source-asimov-nn-zoo` | L08–L11 | alternative video rails; the module already has CS229 + 6.036 + EECS 498 and does not need a fourth | 5 — **deferred with reason** |
| `source-grad-cam`, `source-zeiler-fergus-occlusion`, `source-captum`, `source-timm`, `source-albumentations-docs`, `source-torchvision-transforms-docs` | — | interpretability and augmentation tooling; **AMLS project scope, not AML exam scope** | 5 — **out-of-scope row** |
| `source-sutton-barto-rl` | — | already in the AML map with 0 routes; RL is not in the 2026 deck | **needs a disposition**: `reference-only` with a reason, or removal |

Rule 14 requires every one of these to end with `selected`, `reference-only`, or
`deferred with a reason`. Silent omission is the failure mode this rule exists for.

---

## 8. Files affected

| Path | Change |
|---|---|
| `curriculum/modules/module-hu-aml/source-map.yaml` | the whole job: 223 routes gain `angle_detail`, 136 gain exact locators, ~11 get corrected pages, ~40 routes are added, ~2 removed, several split |
| `curriculum/modules/module-hu-aml/units/unit-aml-l0*/unit.yaml` | only where a split route needs a new `covers` target; **`source_selections` stays `[]`** |
| `curriculum/modules/module-hu-aml/units/*/study-map.yaml` | regenerated by `assemble_lecture_study_maps.py` after the map lands, so stage resources inherit the repaired locators |
| `sources/registry/machine-learning.yaml` | new source records only where the sweep adopts an unregistered candidate; **the printed-page numbers in existing `useful_sections` are a separate correction, deliberately not in scope here** |
| `work/active/workspace-aml-exam-prep/outputs/AML-source-rigor-coverage-audit-2026-08-30.md` | new, from `system/templates/plan-coverage-audit.template.md` |
| `work/active/workspace-aml-exam-prep/outputs/AML-source-rigor-plan-P{1..4}.yaml` | the four import packages |
| `operations/validation-warning-baseline.yaml` | shrinks; a shrinking signature is a repair and passes the gate |

Not touched: the build-output tree (OPERATOR rule 1 forbids editing it), `LearningOS/legacy/` (frozen), `Stratum/`,
`module-hu-m2-statistik-analysis` (the Géron-edition carry stays carried).

---

## 9. Steps

Four packages, in this order. Each is a separate `module-plan-import` with its own
preflight and snapshot; **none of them is a hand edit of `source-map.yaml`**
(rule 16). Splitting is deliberate: one 223-route package that fails preflight
gives one undiagnosable error, and the page-correction package must land before
anything is built on the pages it fixes.

### Gate 0 — contract and state (once, before P1)

```bash
brew install poppler
```

```bash
cd LearningOS/repository && .venv/bin/python tools/los.py capabilities --json
```

```bash
cd LearningOS/repository && .venv/bin/python tools/los.py bootstrap
```

Record `snapshot.snapshot_id`. Note the nested repository is currently dirty with
unrelated SaD and tooling work on `engineering-review-tier1` — preserve it; do not
stage it; `session-end` review is per-package, not per-plan.

### Gate 1 — the coverage audit (once, before P1)

Copy `system/templates/plan-coverage-audit.template.md` to
`work/active/workspace-aml-exam-prep/outputs/AML-source-rigor-coverage-audit-2026-08-30.md`.
It cites the 2026-08-19 and 2026-08-22 audits as its local-inventory evidence and
adds three new sections:

1. **The locator verification log.** One row per repaired locator: source, claimed
   division, PDF page derived from `--toc`, and the `--verify` result. Both books
   with no outline (`csc411.pdf`, `Zacharski_…pdf`) get a row saying which method
   was used.
2. **The page-convention correction.** The eleven rows of §4.3, before and after,
   with the offset stated per book.
3. **The registered-source sweep.** All 246 sources, dispositioned. Rows that are
   obviously off-domain may be dispositioned in named groups, but the group and its
   reason must appear.

The three `checks:` flags about inventory stay `true` only on the strength of the
cited audits plus this delta; the `materials_opened_and_content_checked` flag may
not be set until every newly routed candidate has actually been opened.

Working command for every book with an outline:

```bash
cd LearningOS/repository && .venv/bin/python tools/material_toc.py --toc material://source-islp/islp.pdf --depth 3
```

and, once poppler is installed, the check that makes it evidence:

```bash
cd LearningOS/repository && .venv/bin/python tools/material_toc.py --verify material://source-islp/islp.pdf --page 147 --expect "Logistic Regression"
```

### P1 — page corrections and artifact clearing (smallest, highest risk if delayed)

- The eleven `§4.3` rows: Murphy ×9 (L03, L06 ×3 incl. solutions manual, L11 ×4,
  exam-prep ×1) and ISLP §10.3.
- The three artifact warnings: D2L L11, Jurafsky L11 and exam-prep — quote titles,
  add pages.
- `source-sutton-barto-rl` disposition.
- The `cs229-notes → l10` deletion or honest re-scope.

Expect: `LOCATOR-VAGUE` on AML 136 → ~133; no `angle_detail` change yet.

### P2 — locators, the 73 local-copy rows

Repair every vague route whose source has a registered local material. Split the
multi-section ESL/ISLP rows (§6.2, §6.3) into one route per section, since a split
is what lets each fragment carry its own angle. `csc411.pdf` and Zacharski rows
depend on poppler; if it is unavailable they stay vague **with a recorded reason**
rather than being guessed.

Expect: `LOCATOR-VAGUE` on AML ~133 → ~60.

### P3 — locators, the 63 web rows, and the sweep

Every remaining vague route gets a dated web verification (open the primary page,
confirm the locator resolves and matches the claimed topic, record the date).
Priority-1 and -2 sweep candidates from §7 are opened and routed; priority-3 to -5
get their explicit dispositions.

Expect: `LOCATOR-VAGUE` on AML → 0 or a small named residue of sources with no
reachable primary; ~40 routes added.

### P4 — `angle` and `angle_detail` across all routes

The only package that touches every row. Work **unit by unit**, and for each unit
read all its rows together before writing any of them — an angle is a claim about
*difference*, and difference cannot be judged one row at a time. §5.2's discriminator
test is the acceptance criterion: if a sentence would be equally true of another row
on the same unit, it is not finished.

Expect: `ROUTE-ANGLE-DETAIL-MISSING` on AML 223 → 0. Repository total 438 → ~79.

### Per-package gates (4, 5, 6 of the SOP, unchanged)

```bash
cd LearningOS/repository && .venv/bin/python tools/los.py module-plan-import module-hu-aml --file work/active/workspace-aml-exam-prep/outputs/AML-source-rigor-plan-P1.yaml --check
```

Success reports `canonical_files_written: 0`. A failure is a rejected package:
read the first diagnostic completely, then fix the whole failure *class* at once.
Never patch canonical YAML to make a defective package pass.

```bash
cd LearningOS/repository && .venv/bin/python tools/los.py module-plan-import module-hu-aml --file work/active/workspace-aml-exam-prep/outputs/AML-source-rigor-plan-P1.yaml --expected-snapshot sha256:CURRENT
```

Then, after the last package, rebuild the study maps so stage resources inherit the
repaired locators:

```bash
cd LearningOS/repository && .venv/bin/python tools/assemble_lecture_study_maps.py --out work/active/workspace-aml-exam-prep/outputs/lecture-map-drafts --unit unit-aml-l06
```

Review each draft, then apply through `unit-map-import`.

---

## 10. Risks

| Risk | How it shows | Control |
|---|---|---|
| **The printed/PDF page confusion recurs.** It already happened once, in a package whose own audit claimed the offset was resolved. | A locator passes `LOCATOR-VAGUE` and lands the reader 30 pages early. Nothing in CI catches it. | Every page in P1–P3 is derived from `--toc` output pasted into the audit's verification log, then `--verify`-checked. A page that appears in no log row does not go in a package. |
| **`angle_detail` degenerates into a longer `angle`.** 223 rows is enough volume to invite it. | Hover text that repeats the one-liner; no limits named anywhere. | The §5.3 four-part structure is the acceptance test, and "when to choose something else" must be present in every one. Spot-check ten rows per unit against a sibling row. |
| **A big package fails preflight opaquely.** | One diagnostic, 223 candidate causes. | Four packages, smallest first. P1 is ~15 rows and proves the pipeline. |
| **Poppler stays unavailable.** | `csc411` and Zacharski rows cannot be verified at all. | They stay vague with a recorded reason. Do not guess a page; the SOP's own rule is that an unopenable locator is worse than an absence. |
| **Study maps drift from the repaired map.** | Stage resources still carry the old locators after P4. | The assembler rebuild is part of the plan, not an afterthought, and it refuses to write when concept edges are stale. |
| **The dirty tree.** The nested repo has uncommitted SaD and tooling work. | A `session-end` sweeps unrelated changes into an AML commit. | Run `session-end` with no commit message first and read the unrelated list, every package. |
| **Gateway defects.** `LEARNINGOS-CRITICAL-SYSTEM-AUDIT-FINDINGS-2026-08-29.md` records open replay/ownership defects. | Per Aram's instruction these are disregarded for planning. | But **do not use exact-replay** to re-apply a package while defect 1 is open; re-run the preflight and import against a fresh snapshot instead. |
| **Scope creep into SaD.** The Géron-edition error and the registry's printed pages both live next door. | An AML package quietly edits `module-hu-m2-statistik-analysis` or the registry. | Both are recorded as carried items. `module_patch` names AML units only. |

---

## 11. Verification

Per package, in order:

```bash
cd LearningOS/repository && make check && make views && make check
```

```bash
cd LearningOS/repository && .venv/bin/python -m pytest -q tests/test_curriculum_v2.py
```

```bash
cd LearningOS/repository && .venv/bin/python tools/warning_baseline.py --check
```

```bash
cd LearningOS/repository && .venv/bin/python tools/validate.py --online
```

The last one is required in P3, where web sources change.

**Acceptance is numeric and stated in advance:**

| Signature (AML source map) | Now | After P1 | After P2 | After P3 | After P4 |
|---|---|---|---|---|---|
| `LOCATOR-VAGUE` | 136 | ~133 | ~60 | 0 (+ named residue) | 0 |
| `ROUTE-ANGLE-DETAIL-MISSING` | 223 | 223 | 223 | ~263 (new routes) | **0** |
| Repository total warnings | 438 | — | — | — | **~79** |

A shrinking baseline signature is a repair and passes the gate; it is never
restored to match the old total. Update
`operations/validation-warning-baseline.yaml` only after P4, in one edit.

Then the review the SOP actually asks for: read the final diff **against the
coverage audit**, not against the package. Every reviewed material lands in the
intended unit menu with the correct angle and disposition; chosen material stays
distinguishable from merely available material; no lecture unit has collapsed into
a cluster; unrelated dirty-tree changes are untouched.

---

## 12. Out of scope

- **Applying anything.** This document is a design. No canonical file is written by it.
- **`CRITIQUE-POINTS` §1 complaint 1** (whether plan manipulation is standardized).
  The point stays `open`; closing it is Aram's.
- **The SaD Géron-edition correction.** Different module, carried since 2026-08-22.
- **Correcting the printed page numbers in `sources/registry/*.yaml`.** Real, and
  §4.3 documents it, but source-evaluation text and route locators are distinct
  ownership layers (rule 8). Doing both in one pass would make the diff unreadable.
- **A validator rule for wrong-but-present pages.** Would be acting on
  `CRITIQUE-POINTS` uninvited. Recorded here as a candidate: a `LOCATOR-UNVERIFIED`
  warning for any `book` route whose cited page is not confirmed by the material's
  own outline is mechanically checkable with the code that already exists.
- **AMLS, Algo 2 and the Python module**, which have the same debt at smaller scale
  (Algo 2: 17 vague + 20 missing detail).
- **Any change to `source_selections`.** Those are Aram's choices, and the SOP is
  explicit that they stay empty until he makes them.

---

## 13. Open questions for Aram

1. **Sweep depth.** SaD's pass added 44 routes. Priorities 1–2 in §7 are ~11
   sources / ~25 routes; priorities 1–3 are ~17 / ~40. Which line?
   *Recommendation: 1–3, matching SaD's depth.*
2. **`source-sutton-barto-rl`** — `reference-only` with "RL is not in the 2026
   deck", or remove it from the AML map entirely?
   *Recommendation: reference-only; removal loses the record that it was considered.*
3. **Graduate-depth sources** (Bishop, Mohri, Shalev-Shwartz, Boyd, Nocedal).
   Route them with an explicit "past the exam" flag, or defer them?
   *Recommendation: defer with a reason. The exam date is owned by
   `curriculum/modules/module-hu-aml/module.yaml`, and a depth row
   nobody will open is a trap dressed as coverage.*
4. **Package granularity.** Four packages, or one per lecture (twelve)?
   *Recommendation: four. Twelve preflights buys nothing once P1 has proved the
   pipeline.*
