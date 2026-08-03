# SaD + AML learning-material completeness audit — 2026-08-03

This is the review record behind:

- `SaD-L06-L15-module-plan.yaml`
- `../../workspace-aml-exam-prep/outputs/AML-L01-L11-gap-module-plan.yaml`

The executable truth is in the imported module source maps, unit records, and
study maps. This file records the inventory and the non-obvious dispositions so
that “not selected” is never confused with “not reviewed.”

## Local AML inventory reviewed

| Family | Count | Disposition |
|---|---:|---|
| Current lecture decks | 10 PDFs | L01–L10 are all individual current units. Newly built: L01, L08, L09, L10. Existing L02–L07 maps were used as the structural/content pattern. |
| Older lecture variants | 11 PDFs | L01–L10 are reference-only second explanations after the current deck. Older L11 RNN is the only L11 asset and therefore sits behind a mandatory current-scope check. |
| Linear-algebra primer | 1 PDF | L01 prerequisite diagnostic; targeted 3Blue1Brown repair only where the primer exposes a gap. |
| Bonus sheets | 4 PDFs | Bonus 1 routes to L02/L03; Bonus 2 to L03/L04; Bonus 3 to L05/L06; Bonus 4 Tasks 1–2 to L07 and Tasks 3–4 to L08. Existing local solution notes remain the keys. |
| Exercise slide decks | 7 PDFs | `Übung 02` → k-NN/Blatt 1; `Übung 03` → vectorization/linear regression; `Übung 04` → regression/nonlinear/regularization; `Übung 06` → logistic/GD/Blatt 3; `Übung 07` → perceptron + prior-sheet review. `TÜbung 04` and `Übung 05` are byte-identical logistic-regression geometry decks, not two missing topics. |
| Local Cornell CS4780 bank | 34 PDFs plus HTML/TeX/assets | All three local course-year families were inventoried. Topic routing: HW1 k-NN; HW2 perceptron; HW3 probability/MLE/MAP; HW4 logistic; HW6 regression/GD/ridge; HW7 kernels; HW8 trees/AdaBoost; HW9 NN/CNN/ReLU. Each unit selects only its topic and solution-backed variant. |
| Shared AML books named by `SOURCES.md` | 9 named families | ESL, ISLP, Géron, Kelleher, Murphy, CS229, and CSC411 are routed where relevant. Sutton–Barto is explicitly off the posted AML scope; Zacharski is retained only as an optional L02 data-mining alternative. |

### AML lecture-scope corrections retained

- L08 contains the multiclass metric-averaging block; books do not replace the
  deck/scikit-learn definitions.
- L09 contains L2/Frobenius weight decay, dropout, early stopping, double
  descent, vanishing/exploding gradients, and autograd; it does **not** contain
  batch normalization.
- L10 requires convolution/cross-correlation arithmetic, shape/parameter
  calculations, pooling, and LeNet/AlexNet/GoogLeNet/ResNet distinctions.
- The local current archive stops at L10. L11 is not called current or
  exam-critical based on the prior-year RNN deck alone.

## Local SaD inventory reviewed

| Family | Count | Disposition |
|---|---:|---|
| Current lecture decks | 15 PDFs | Every L01–L15 lecture now has an individual unit. L06–L10 were split into five executable maps; L11–L15 were added as separate maps. |
| Current exercise/sheet PDFs | 11 PDFs | All were opened and topic-classified. Sheet/deck numbering was not trusted. Exact routing is listed below. |
| Prior-year course PDFs | 19 PDFs | Twelve topic decks plus UE1–UE7. Used only on verified topic matches; 2025 numbering is never treated as the 2026 sequence. |
| Local solved external exams | 5 PDFs | FAU WS14/15 is the first full German exam. HS Harz, Köln, Leuphana, and Regensburg form the secondary gap-targeted bank. |
| Local statistics/probability books | Relevant registered shelf reviewed | Fahrmeir text/workbook, Blitzstein, Dekking, OpenIntro, Pitman, Ross, Tijms, Schaum, Kroese, and the ML-half Kelleher/ISLP/Murphy/CSC411 sources are routed by lecture. Swanson is explicitly excluded as off-syllabus formal logic/measure theory. |

### Exact 2026 SaD exercise routing

| Asset | Actual content | Unit route |
|---|---|---|
| `Blatt1.pdf` | features/data/descriptive foundations | L01–L02 |
| `blatt-02.pdf` | probability foundations plus course tasks | L03–L05 as existing maps/crosswalk specify |
| `Übung-3.pdf` | random variables and discrete distributions | L06–L07 |
| `Statistics_And_Data_Science.pdf` (Blatt 4) | Normal distribution, estimation, CLT | L08–L09 |
| `blatt-05.pdf` | permutation test, neural-network forward/softmax/loss, multiclass metrics | L10, L15, L11 |
| `UE2.pdf` | features, correlation, linear regression | L01–L03 |
| `UE3.pdf` | probability and gradient descent | L04–L05 plus regression/GD bridge |
| `UE4.pdf` | random variables and discrete distributions | L06–L07 |
| `UE5.pdf` | Normal, estimation, SE, confidence intervals | L08–L09 |
| `UE6.pdf` | hypothesis tests and classification | L10 and L14 |
| `UE7.pdf` | Blatt-5 solutions, metrics, NN, clustering/k-means, full exam-question inventory | L10, L11, L15, and new auxiliary clustering unit |

### Non-matches and recovered gap

- 2025 L12 is clustering; 2026 L12 is trees. They are not merged.
- 2025 L11 instance-based and L13 similarity decks support current L13, not
  current L11 Data Science Introduction.
- No current tree-specific or k-NN-specific exercise sheet exists; solution-
  backed Cornell/MIT practice fills those exercise gaps without inventing a
  course sheet.
- Clustering was a genuine missed plan: current UE7 teaches method families and
  a full k-means trace, while the prior-year L12 deck supplies same-topic depth.
  It now has `unit-m2-sad-clustering`.

## Linked/official web shelves reviewed and routed

| Shelf | Use and disposition |
|---|---|
| MIT 18.05 | Probability/inference notes and solution-backed exams for SaD L04–L10. |
| MIT 18.650 | Optional rigor only: MLE L4–5 → SaD L08/L09; testing L7–12 → L10; later regression/Bayes/GLM material remains optional. |
| Harvard Stat 110 | Optional Units 3–6 and distribution handout for SaD L06–L08; never a parallel full course. |
| OpenIntro | Gentle probability/distribution/inference pass before Fahrmeir's German notation layer. |
| Stanford CS229 notes/videos | Topic-matched derivations; exact kernel-without-SVM source for AML L07; selected NN/CNN/RNN support only. |
| Cornell CS4780 | Official course structure was checked against the local solution bank; routes listed above. |
| MIT 6.036 / 6.034 | Structured ML learning and solution-backed tracing; selected by lecture only. |
| UMich EECS 498 and Stanford CS231n | Optional FC/CNN/RNN depth; L10 uses the CNN/architecture portions only. |
| scikit-learn evaluation docs | Authoritative micro/macro/weighted metric definitions for SaD L11 and AML L08. |
| PyTorch official tutorials | L09 autograd and L10 CNN implementation connection; not a replacement for hand derivations. |
| MML companion | Ch 5/7 mathematical safety net; deliberately not used as a k-NN/logistic first source. |
| StatQuest, 3Blue1Brown, jbstatistics, Kurzes Tutorium, Brandon Foltz, Daniel Jung, numiqo | Exact topic clips are retained in L06–L10/L14/L15 and AML L08–L09 maps or in the preserved L06–L10 synthesis note. They are gap-targeted refreshers, never linear playlists. |

## Routing reconciliation found by the standardized preflight

The first run of the new no-write source-routing gate found material that was
already selected in unit stages but absent from the corresponding module route.
No canonical file had to be rolled back. The plan packages and canonical source
maps now explicitly include these joins:

- SaD: 3Blue1Brown Linear Algebra for L01/L03; early-lecture routes for
  StatQuest, jbstatistics, Kurzes Tutorium, Kelleher, ISLP, and CS229; the
  L06–L10 synthesis route for MIT 18.05; and explicit prior-year routes for
  L11/L12/L14 where non-match/reference dispositions use the 2025 archive.
- AML: ISLP for L06, CS229 notes for L02/L04, and 3Blue1Brown Linear Algebra for
  L03/L06/L07.

This distinction matters: a source can be globally registered and even appear
in a stage while still being missing from the module-to-unit routing layer.

## Completeness invariants applied

1. Current deck/UE scope wins over book or prior-year numbering.
2. Every registered source is either routed to a unit or has an explicit
   reference/candidate/exclusion reason.
3. Optional courses are cherry-picked by verified topic, never assigned as a
   second full course.
4. Duplicate files count once conceptually but remain recorded.
5. Missing current evidence is labeled; it is never silently backfilled from an
   older semester and called current.
