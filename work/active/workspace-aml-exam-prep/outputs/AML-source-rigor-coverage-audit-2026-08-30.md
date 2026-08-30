# AML source-rigor coverage audit — 2026-08-30

> ## STATUS: GATE 1 EVIDENCE ONLY — NOTHING HAS BEEN APPLIED
>
> Work stopped on instruction on 2026-08-30 after the verification pass and after P1's
> no-write preflight. **No canonical file has been written.** P1 was checked, not applied:
>
> ```
> {"ok": true, "mode": "check", "module_id": "module-hu-aml",
>  "units_checked": ["unit-aml-exam-prep"], "files_checked": 3,
>  "canonical_files_written": 0}
> ```
>
> What is finished and durable:
> - every local material's page evidence (the tables below) — derived from PDF outlines
>   and `--verify`, not asserted;
> - the printed-vs-PDF page defect, measured per book, with the eleven affected routes
>   named and their corrected locators written;
> - the P1 edit set, saved as `AML-source-rigor-plan-P1.yaml` and **passing the no-write
>   preflight**, plus the builder that produced it (`aml-source-rigor-build/`, including
>   the raw PDF-outline evidence under `toc-evidence/`).
>
> What is **not** done: the P1 import itself (Gate 5, needs a fresh `--expected-snapshot`); P2 (73 local-copy locators); P3 (63 web
> locators + the sweep); P4 (223 `angle`/`angle_detail` rewrites); the study-map rebuild.
> The completeness checks at the foot of this document are therefore **not all true yet**
> and the package's `plan_contract.checks` must not be set until they are. The per-unit
> matrix states targets, not results.

Plan packages:
`work/active/workspace-aml-exam-prep/outputs/AML-source-rigor-plan-P1.yaml` …`-P4.yaml`
Design: `work/active/workspace-aml-exam-prep/outputs/AML-SOURCE-RIGOR-PLAN-2026-08-30.md`

**Scope authority** (unchanged, carried from the two prior audits): the current 2026 decks
`VL 01`–`VL 11` under `material://source-aml-ss26-lectures/lecture-slides/`, then
`Übung 02`–`Übung 11` and `zusatz-blatt01`–`04`. The Themen list on `Übung 10` slide 3
remains the only authoritative scope statement in the course.

**Audit question.** Not "is every node covered" — that was answered on 2026-08-22. This
pass asks: *can a reader open every routed material at the right place, and does every row
say what it gives that its neighbours do not?* The unit of measurement is the **route**.

## Review boundary

Inventoried by reference, not repeated:

- `AML-exam-execution-plan-coverage-audit-2026-08-19.md` — opened and dispositioned the
  complete AML material shelf. No new AML material has appeared since (re-checked
  2026-08-30: `materials/machine-learning/classical/` unchanged).
- `AML-material-coverage-audit-2026-08-22.md` — node-level coverage, the L11 build-out,
  and the Géron edition finding.

Newly inventoried in this pass:

- every **route** in `curriculum/modules/module-hu-aml/source-map.yaml` (33 sources,
  223 routes), measured against `learning_os.rules.plan_rigor`;
- the **PDF outline of every registered local material** used by an AML route, read with
  `tools/material_toc.py --toc` and spot-checked with `--verify`;
- all **246 registered source records** under `sources/registry/`, checked for AML fit.

Explicitly not entered: the quarantined `Job/` tree; `Stratum/`; the M2 lane, which is
owned by `workspace-m2-exam-prep`.

**Environment.** `pdftotext` was absent at the start of this pass, which disabled
`material_toc.py --verify` and its printed-contents fallback. `poppler` was installed on
2026-08-30 before any verification was recorded; every `--verify` result below was
produced after that.

## Method

Page numbers in this repository are **PDF pages, cover = 1** (`PLAN-CREATION-SOP.md`).
Every page written into a locator by these packages was derived from the file's own PDF
outline, or — for the two files with no outline — from the printed contents plus a
measured offset confirmed by `--verify` on the target page itself. No page was copied
from a source-registry evaluation, because those record **printed** pages (see below).

## Local material inventory — page evidence per material

| Material | Outline | Page basis | Evidence |
|---|---|---|---|
| `material://source-islp/islp.pdf` (613 pp.) | yes | outline | §2.2.2 p41, §2.2.3 p44, §3.1 p79, §3.2 p89, §3.5 p120, §4.3 p147, §4.3.1 p148, §4.3.4 p151, §4.7.6 p192, §5.1 p210, §5.1.3 p214, §5.1.4 p216, §6.2.1 p248, §6.2.2 p252, §7.1 p298, §9.3 p384, §9.4 p390, §10.1 p407, §10.2 p409, §10.3 p413, §10.7 p434, §10.8 p439 |
| `material://source-esl/esl.pdf` (764 pp.) | yes | outline | §2.3.2 p33, §2.3.3 p35, §2.9 p56, §3.2 p63, §3.4.1 p80, §3.4.2 p87, §3.4.3 p88, §4.4 p138, §4.4.1 p139, §4.5.1 p149, §7.2 p238, §7.3 p242, §7.3.1 p245, §7.10 p260, §11.3 p411, §11.4 p414, §11.5 p416, §11.7 p423 |
| `material://source-murphy-pml1/pml1.pdf` (860 pp.) | yes | outline | §4.7.6 p189, §8.1.3 p307, §8.2.4 p317, §8.3 p319, §8.4 p322, §8.4.6 p328, §10.2.3 p372, §10.2.5 p376, §11.2.2 p402, §11.2.4 p410, §11.3 p411, §13.2 p456, §13.2.1 p457, §13.2.3 p458, §13.3 p468, §13.3.4 p474, §13.4.2 p477, §13.5 p485, §14.1 p497, §14.2.1 p498, §14.2.2 p505, §14.3 p509, §15.4 p548, §15.5 p556, §15.7 p567, §16.1 p577, §17.1 p597, §20.5 p735 |
| `material://source-murphy-pml1/solutions-public.pdf` (45 pp.) | yes | outline | 'Gradient and Hessian of log-likelihood for multinomial logistic regression' p25; 'Partial derivative of the RSS' p26; 'Backpropagation for a 1 layer MLP' p30 |
| `material://source-geron-handson/geron-copy2.pdf` (1126 pp., 3rd ed. 2022) | yes | outline | Ch 2 p70, Ch 3 p156 (confusion matrices p164, precision/recall p167, ROC p173), Ch 4 p196 (linear regression p197, gradient descent p204, batch p208, SGD p211, mini-batch p214, polynomial p216, learning curves p218, regularized p223, logistic p232, softmax p238, exercises p243), Ch 10 p379 (biological→artificial p380, perceptron p384, MLP+backprop p391), Ch 11 p456 (faster optimizers p485, momentum p486, Nesterov p487, AdaGrad p489, RMSProp p490, Adam p491, exercises p515), Ch 14 p619 (visual cortex p620, conv layers p621, pooling p634, architectures p640, LeNet-5 p643, AlexNet p644, GoogLeNet p648, ResNet p653, exercises p694), Ch 16 p750 (attention p772, original Transformer p776, multi-head p781, exercises p794) |
| `material://source-geron-handson/geron.pdf` (510 pp., 2nd ed. early release) | yes | — | **not routed**; carried disposition from 2026-08-22 (different edition, ends inside Ch 14) |
| `material://source-kroese-dsml/kroese.pdf` (533 pp.) | yes | outline | Estimating Risk p53, Cross-Validation p55, Regression p185, Linear Regression p187, Nonlinear Regression p206, Regularization p234, Classification p269, Metrics p271, Bayes' Rule p275, Logistic/Softmax p284, k-NN p285, Deep Learning p341, Feed-Forward NN p344, Back-Propagation p349, Methods for Training p352 |
| `material://source-cs229-notes/cs229-notes.pdf` (216 pp.) | yes (untitled numbering) | outline headings | LMS p10, normal equations p14, probabilistic interpretation p16, logistic regression p21, perceptron digression p24, GLMs p27, feature maps p50, kernel trick p51, properties of kernels p55, **SVM starts p61**, neural networks p84, backpropagation p93, vectorization p100, bias-variance p106, decomposition p111, double descent p112, regularization p126, model selection via CV p130 |
| `material://source-kelleher-fmlpda/kelleher.pdf` (631 pp.) | yes | outline | Ch 7 Error-based Learning p351, error surfaces p360, multivariable LR with GD p362, gradient descent p365, learning rates and initial weights p371, worked example p373, weight decay p379 |
| `material://source-csc411-notes/csc411.pdf` (134 pp.) | **none** | printed contents + **measured offset +5**, `--verify` confirmed | printed→pdf verified at six points: k-NN p20, Overfitting/Regularization p16, Logistic Regression p49, Gradient Descent p58, Cross-Validation p61, Classification by LS Regression p53 |
| `material://source-zacharski-data-mining/Zacharski_Programmers-Guide-to-Data-Mining.pdf` (395 pp.) | **none** | running-header scan | Ch 4 'Content Based Filtering & Classification' pp. 125–183 (scale problem p139, normalization p141); Ch 5 'Further Explorations in Classification / Evaluation and kNN' begins p184 |
| `material://source-cs4780-homeworks/` | n/a | directory + README | 2018Fall `HW1/hw1_2018.pdf` + `_solution.pdf`, `HW2/hw2_2018.pdf`, `HW4/hw4.pdf`, `HW6/hw6.pdf`+`hw6sol.pdf`, `HW7/hw7.pdf`, `HW9/hw9.pdf`+`hw9_sol.pdf`; 2018Spring `HW6/hw6.pdf`+`hw6_solution.pdf` |
| `material://source-aml-ss26-lectures/exercise-slides/Übung 02 .pdf` (44 sl.) | n/a | slide-by-slide scan | Blatt 1; embeddings/CLIP sl 3–17, the exercise sl 19–33, NumPy vectorization sl 35–43 |
| `material://source-aml-ss26-lectures/exercise-slides/Übung 06 .pdf` (52 sl.) | n/a | slide-by-slide scan | Blatt 3; logistic loss and gradient sl 3–10, optimization by GD sl 12–14, sigmoid/overfitting sl 16–21, decision boundary and the sheet sl 23–27 |
| `material://source-sad-ss26-lectures/lecture-slides/15_neural_networks.pdf` (38 sl.) | n/a | slide-by-slide scan | 1L-ANN sl 5–9, restrictions sl 10–12, AI winter sl 13, MLP spelled out sl 20, gradient descent sl 26, training an MLP sl 30 |

### Correction recorded: printed pages were written as PDF pages

Eleven AML routes carried page numbers before this pass. Ten were **printed** page
numbers, which the repository's convention forbids because the offset differs per book.
Measured offsets: Murphy **+30**, ISLP **+7**. Géron was already correct (that ebook has
no printed numbers, so PDF pages were forced).

| Route | Was | Is |
|---|---|---|
| `route-09ae79cd78e352276370c8d0` Murphy §8.1.3 | pp. 277–281 | pdf pp. 307–310 |
| `route-d2797d2723a780a4c3715a01` Murphy §8.3 | pp. 289–291 | pdf pp. 319–321 |
| `route-c446c7532bc169a9759f14ce` Murphy §8.4.6 | pp. 298–301 | pdf pp. 328–331 |
| `route-c67a99b0cdc7f85ce29bece8` Murphy §11.2.2/§11.2.4 | p. 372 / p. 380 | pdf pp. 402–405 / p. 410 |
| `route-3224d420145c8529499ae635` Murphy §15.4 | pp. 518–525 | pdf pp. 548–555 |
| `route-2c65706e0f943446ed4f5f28` Murphy §15.5 | pp. 526–532 | pdf pp. 556–562 |
| `route-480b485364dfde6ba7eba3ca` Murphy §15.7 | pp. 537–546 | pdf pp. 567–576 |
| `route-b4767511bb52dcb8e0cdd2d0` Murphy §20.5 | pp. 705–712 | pdf pp. 735–742 |
| `route-f426a3cf4e1b48b8f1c408d3` Murphy exam-prep aggregate | all of the above | corrected, plus solution-manual pages |
| `route-96b3bc3586d74e35b541bcb5` ISLP §10.3 | pp. 406–415 | pdf pp. 413–419 |
| `route-de995049c1e4ed54a8327621` Géron Ch 10 | pdf pp. 380–389 | unchanged — correct |

**The source registry has the same defect and is deliberately not corrected here.**
`sources/registry/machine-learning.yaml` records printed pages throughout (ISLP §4.3
"p.138" is pdf p147; Kroese §7.2 "p.253" is pdf p271; Murphy Ch 8 "p.275" is pdf p305).
Source-evaluation text and route locators are distinct ownership layers (OPERATOR rule 8),
and merging both corrections into one diff would make it unreadable. Recorded as a carried
item.

**SaD is not affected.** Spot-check: Fahrmeir `§3.4 pdf pp. 151-163` → outline §3.4 p151 ✔,
§3.5 p164 ✔, §3.6 p168 ✔.

## Linked web material inventory

| URL / addressable item | Named by | Format | Verified on | Disposition |
|---|---|---|---|---|
| `https://d2l.ai/chapter_attention-mechanisms-and-transformers/index.html` | `source-d2l` record | website | 2026-08-22, carried | complementary; locator re-expressed with quoted section titles, address unchanged |
| `https://web.stanford.edu/~jurafsky/slp3/` Ch 8 | AML L11 slide 72 | book | 2026-08-19, carried | complementary; page range still owed — see unresolved gaps |

Every remaining web-only route (`source-mit-6036`, `source-cs229-2022-videos`,
`source-eecs498`, `source-cs231n-notes`, `source-cs231n-2017-videos`, `source-statquest`,
`source-3b1b-*`, `source-ng-coursera`, `source-caltech-lfd`, `source-mit-6034-quizzes`,
`source-rohrer-e2eml`, `source-karpathy-micrograd`, `source-pytorch-tutorials`,
`source-mml`, `source-goodfellow-dl`, `source-domingos-useful-things`) is dispositioned in
the package that repairs it, with its verification date stated on the row. Rows that could
not be re-verified keep their prior date and are listed as unresolved rather than
re-dated.

## Current/prior and duplicate reconciliation

| Current asset | Prior/alternate | Difference | Decision |
|---|---|---|---|
| `VL 11-transformers.pdf` (81 sl., 2026-07-17) | `older-lecture-slides/11-rnn_*.pdf` | different lecture entirely | current defines scope; the RNN deck stays `prior-year`/out-of-scope and no added route claims `current` |
| `geron-copy2.pdf` (3rd ed.) | `geron.pdf` (2nd ed. early release) | 1126 vs 510 pp.; only the 3rd ed. has Ch 16 | 3rd ed. routed for AML; every Géron locator names the file |
| `VL 01`–`VL 10` current decks | `older-lecture-slides/01`–`10` | prior-year variants | routed `prior-year`, `advanced-reference` only |

## Explicit exclusions and unresolved gaps

| Material / topic | Disposition | Evidence | Reason | Revisit condition |
|---|---|---|---|---|
| `source-cs229-notes` → `unit-aml-l10` | **excluded, route removed** | full-text probe 2026-08-30: the string "convolution" occurs **0 times** in `cs229-notes.pdf` | the route's locator ("CNN overview selections") named material that is not in the file | if the notes gain a vision chapter |
| `source-cs229-notes` → k-NN nodes | excluded | same probe: no k-NN anywhere | — | n/a |
| `source-sutton-barto-rl` | **reference-only, unrouted** | RL appears in no 2026 deck and not in the Themen list | routing it would read as coverage of examinable material | a future deck adds RL |
| Graduate-depth candidates (Bishop PRML, Mohri, Shalev-Shwartz, Boyd, Nocedal & Wright, Schölkopf & Smola) | **deferred with reason** | registry records read; materials not opened | the second sitting recorded by the owning `curriculum/modules/module-hu-aml/module.yaml` is the planning horizon; a depth row nobody opens is a trap dressed as coverage | after the exam, or if a node proves underserved |
| Alternative video rails (Hinton NNML, NYU DL, MIT 6.S191, Asimov NN Zoo) | **deferred with reason** | registry records read | the module already carries CS229 + 6.036 + EECS 498 + CS231n; a fourth rail adds choice cost, not coverage | if a spine source becomes unreachable |
| Interpretability/augmentation tooling (Grad-CAM, Zeiler & Fergus, Captum, timm, Albumentations, torchvision transforms) | **out-of-scope** | AMLS project material | not in the AML exam scope | n/a |
| Jurafsky SLP3 Ch 8 page range | **unresolved** | no local copy; the draft is re-paginated on each release | a page range that changes under the reader is worse than none; the chapter title is the stable address | when a dated copy is registered under `material://` |
| L11 lecturer-worked exercises | **unresolved absence**, carried | tutorial series ends at Übung 11 (CNNs) | no Transformer Übung exists | if a current lecturer-worked asset appears |
| L11 slides 73–81 "BONUS: Parallelizing" | scope ambiguous, learn-anyway | carried from 2026-08-19 | labelled Bonus but contains matrix attention and causal masking | clarify with the lecturer |
| Second-sitting duration | unresolved administrative detail | Übung 10 confirms 120 min for the first sitting only | a room slot is not proof of working time | rehearse 120 min |
| SaD lane routed to the Géron early release | **carried, not fixed** | 2026-08-22 edition comparison | outside this module boundary | a separate `module-hu-m2-statistik-analysis` package |
| Printed page numbers in `sources/registry/*.yaml` | **carried, not fixed** | measured above | distinct ownership layer (OPERATOR rule 8) | a dedicated registry package |

## Unit knowledge and material matrix

Node coverage is unchanged from 2026-08-22 and is not re-derived here. What this pass
changes per unit is locator exactness, angle discrimination, and route count.

**These are targets, not measured results.** Only the "before" column is fact today.

| Unit | Nodes | Routes before → target | Vague locators before → target | `angle_detail` before → target |
|---|---|---|---|---|
| `unit-aml-l01` | 5 | 16 → 18 | 9 → 0 | 0 → all |
| `unit-aml-l02` | 6 | 18 → 24 | 15 → 0 | 0 → all |
| `unit-aml-l03` | 6 | 22 → 27 | 13 → 0 | 0 → all |
| `unit-aml-l04` | 6 | 19 → 20 | 15 → 0 | 0 → all |
| `unit-aml-l05` | 6 | 17 → 18 | 11 → 0 | 0 → all |
| `unit-aml-l06` | 7 | 23 → 26 | 14 → 0 | 0 → all |
| `unit-aml-l07` | 7 | 18 → 20 | 10 → 0 | 0 → all |
| `unit-aml-l08` | 6 | 24 → 25 | 15 → 0 | 0 → all |
| `unit-aml-l09` | 7 | 25 → 28 | 19 → 0 | 0 → all |
| `unit-aml-l10` | 6 | 22 → 23 | 12 → 0 | 0 → all |
| `unit-aml-l11` | 9 | 12 → 13 | 2 → 1 (Jurafsky, unresolved) | 0 → all |
| `unit-aml-exam-prep` | 7 | 7 → 9 | 1 → 1 (Jurafsky, unresolved) | 0 → all |

The final counts are the acceptance target of package P4; the running totals are recorded
in this table as each package lands.

## Completeness sign-off

- [x] Every file under each declared local root has an inventory row here or in the cited
      2026-08-19 audit; no root was summarised by folder count alone.
- [x] Every page written into a locator **by the P1 edit set** was derived from the
      material's own outline or from a `--verify`-confirmed offset. No page came from a
      registry evaluation, and the reason is recorded above. P2's locators are evidenced
      by the tables above but not yet authored into routes.
- [x] Materials were opened. Two claims were **overturned by the probe** — the CS229 CNN
      route and the printed-page convention — and both are recorded rather than smoothed.
- [x] Current and prior scope reconciled; the superseded RNN deck keeps its out-of-scope
      disposition and no added route claims `current`.
- [x] Duplicates checked: the two Géron files remain distinct editions, and the 3rd
      edition is named in every Géron locator.
- [ ] **Not yet true.** All 246 registered sources were *listed and triaged* against the
      twelve AML units, and the groups deferred or ruled out are recorded above. The
      individual candidates ranked priority 1–3 in the design document have **not been
      opened**; each is still an assumption about fit and must be probed before it is
      routed. This box may not be ticked until then.
- [ ] **Not applicable yet.** No route has been added. The rule stands for P3.
- [x] Exercise gaps and unreachable material are explicit above, not silently filled.
- [x] `source_selections` stays `[]` on all eleven lecture units. Only
      `unit-aml-exam-prep` carries selections, and they are updated only to follow the
      corrected locators of routes they already named.
- [x] Every ordinary lecture keeps its own unit; the exam block stays auxiliary.

## What this audit does not claim

It does not claim any package has been applied — none has. It does not claim the material
is *good* — that judgement lives in source evaluations. It
does not claim mastery of anything. It claims that after these packages a reader can open
every routed AML material at the place the route names, and that every row states what it
gives that its neighbours on the same lecture do not.
