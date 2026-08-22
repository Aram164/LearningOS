# SaD plan coverage audit — 2026-08-21

Plan package: `work/active/workspace-m2-exam-prep/outputs/SaD-material-completeness-plan.yaml`

Scope authority: the fifteen current SoSe 2026 SaD decks under
`material://source-sad-ss26-lectures/lecture-slides/` plus the current Blatt/UE
exercise assets. Books, external banks and videos are explanation and practice
layers only and never define scope.

**Audit question.** Not "is the plan valid" — it already validated at 0 errors, 0
warnings — but the question Aram set: *does every stage house all the material
that advances understanding of the concepts that lecture actually discusses?*
The unit of measurement is therefore the **knowledge node**, not the lecture and
not the source count. A node served only by the deck that taught it has no second
angle; a node with no practice or implementation route cannot be worked, only read.

## Review boundary

Inventoried in full:

- `material://source-sad-ss26-lectures/lecture-slides/` — all 15 current decks, opened and read page by page
- `material://source-sad-ss26-lectures/exercise-slides/` — all 11 current exercise assets, listed by name
- `materials/machine-learning/classical/` — all 12 registered sources in the shelf, per its generated `SOURCES.md`
- `materials/mathematics/probability-statistics/` — all 16 registered sources in the shelf
- the module's existing `source-map.yaml` (61 sources, 253 rich routes) and all 19 unit records
- `sources/registry/machine-learning.yaml` and `sources/registry/mathematics.yaml` for source identity

Boundaries explicitly **not** entered: the quarantined `Job/` tree (CLAUDE.md §13);
`curriculum/quarantine/masters-planning/`; the Analysis component of M2, which is a
separate lane owned by `unit-m2-analysis-exam-prep`.

Not verified online: this audit ran without network access to the course page, so
no locator that resolves only on the web was re-checked today. The one URL-only
source in the ML half (`source-mit-6034-quizzes`, MIT OCW) keeps its existing
routes unchanged and is flagged below as unverified-this-pass.

## Method

Every locator added by this package was confirmed by opening the PDF and searching
the page range; the page numbers recorded below are the pages where the term
actually appears in the local copy. Three candidate routes were **dropped** after
the check contradicted the chapter title — they are listed under exclusions. No
route was written from a filename, a chapter title, or a memory of the book.

## Local material inventory — newly routed sources

Sources already present on the ML shelf, registered in the global registry, and
absent from this module's source map until now.

| Locator | Version | Format | Opened/inspected evidence | Actual contents | Duplicate relation | Disposition | Unit route | Lecture-specific angle |
|---|---|---|---|---|---|---|---|---|
| `material://source-geron-handson/geron.pdf` | early-release ebook, 510 pp | book | outline extracted; probes on pp. 60–61, 113–137, 217–240, 263–300, 139–180 | Ch 1 landscape + exercises; Ch 2 end-to-end pipeline; Ch 3 ROC p. 117 / confusion matrix p. 118 / AUC p. 126; Ch 4 normal equation p. 142; Ch 6 trees; Ch 7 stacking blender p. 236; Ch 9 DBSCAN p. 264 / silhouette p. 274; Ch 10–11 ANN | `geron-copy2.pdf` is a second copy in the same folder; not routed | complementary | `l03`, `l11`, `l12`, `l15`, `clustering` | implementation layer the module had nowhere |
| `material://source-zacharski-data-mining/Zacharski_Programmers-Guide-to-Data-Mining.pdf` | 1 ed., 395 pp | book | chapter starts confirmed at pp. 20, 76, 124, 184, 226, 297, 334; term probes | Ch 2 Manhattan p. 23 / Euclidean p. 24 / cosine p. 51; Ch 5 10-fold p. 187 / confusion matrix p. 193 / Kappa p. 203; Ch 6 Naive Bayes; Ch 7 bag-of-words; Ch 8 k-means p. 335 | unique | complementary | `l11`, `l13`, `l14`, `clustering` | hands-on Python counterpart to the ML half |
| `material://source-marsland-ml-algorithmic/Machine Learning_ An Algorithmic Perspective (2nd ed.) [Marsland 2014-10-08].pdf` | 2nd ed., 452 pp | book | outline extracted; probes on pp. 92–131, 270–301, 302–325, 342–379 | Ch 4 XOR p. 92 / back-propagation p. 95 / **universal approximation p. 107**; Ch 12 ID3 p. 271; Ch 13 AdaBoost p. 289 / bagging p. 294; Ch 16 Bayesian networks p. 343 / **Markov blanket p. 349** | unique | complementary | `l12`, `l14`, `l15`, `clustering` | only book home of Bayes nets and universality |
| `material://source-esl/esl.pdf` | 2nd ed., 764 pp | book | outline extracted with page targets; probe on pp. 478–502 | §7.10 CV p. 260; §7.11 bootstrap p. 268; §8.8 stacking p. 307; §9.2 trees p. 324; Ch 10 boosting p. 356; §13.3 k-NN p. 482; §13.5 editing/condensing p. 499; §14.3 cluster analysis p. 520; Ch 15 random forests p. 606 | unique | optional | `l11`, `l12`, `l13`, `clustering` | advanced-reference behind the summary slides |

Two further sources gained routes without being new to the map:
`source-islp` (Ch 13 multiple testing pp. 563–602; §5.2 bootstrap p. 220) and
`source-cs4780-homeworks` (2018Fall/HW4 Problem 1 "Intuition for Naive Bayes",
solution present as `hw4_solution.pdf`), plus `source-kelleher-fmlpda` §6.7
exercise 3 (naive Bayes over normally distributed features, pp. 344–350).

## Linked web material inventory

Every URL-bearing source that carries a route into a SaD unit. No route in this
package depends on a URL: all 29 added routes point at local PDFs. The rows below
are the pre-existing web-locator routes, listed for completeness and carried
forward unchanged.

| URL | Named by | Format | Official/primary evidence | Verified on | Actual topic/locator | Disposition | Unit route | Lecture-specific angle |
|---|---|---|---|---|---|---|---|---|
| `https://ocw.mit.edu/courses/6-034-artificial-intelligence-fall-2010/` | `source-mit-6034-quizzes` | course | MIT OpenCourseWare course page | **not this pass — no network access** | ID3-by-hand, k-NN and neural-network tracing quizzes | complementary | `l12`, `l13`, `l15` | written-exam tracing format the current sheets lack |
| `http://guidetodatamining.com/` | `source-zacharski-data-mining` | website | author's book site | not this pass | companion site for the locally held PDF | complementary | routed via the local copy only | the local PDF is the routed artifact; the URL is provenance |
| StatQuest, jbstatistics, Brandon Foltz, 3Blue1Brown, Domingos, e2eml, CS229 videos | existing source records | video/website/paper | registered with URLs in `sources/registry/machine-learning.yaml` | not this pass | topic-matched selections | complementary/optional | unchanged | unchanged by this package |

Re-verification of these locators belongs to `validate.py --online`, which needs
network access this session did not have. No web-only claim was added or altered,
so nothing in this package depends on that check passing.

## Current exercise-asset inventory and the numbering gap

| Asset present | Disposition | Note |
|---|---|---|
| `Blatt1.pdf` | current | descriptive practice, routed to L01–L02 |
| `blatt-02.pdf` | current | probability/counting, routed to L03–L05 |
| `Übung-3.pdf`, `UE2.pdf`–`UE7.pdf` | current | tutorial decks, routed across L01–L15 and the clustering topic |
| `blatt-05.pdf` | current | testing, workflow and neural-network items |
| `Statistics_And_Data_Science.pdf` | current, name unresolved | generic filename; content matches the L08–L09 range and is routed there, but its sheet number is not recoverable from the file |
| **`Blatt3` / `Blatt4`** | **absent** | no such file exists in the material root |

`stage-m2-sad-calibrate` names `Blatt4/UE5` in its diagnostic locator. There is no
`Blatt4` anywhere under the material root. The most likely referent is
`Statistics_And_Data_Science.pdf`, but that is an inference from topic, not
evidence from the file, so it is recorded here as unresolved rather than silently
rewritten — per the SOP rule that a missing sheet is recorded, never filled by
mislabelling a nearby one.

## Explicit exclusions and unresolved gaps

| Material/topic | Disposition | Evidence | Reason | Revisit condition |
|---|---|---|---|---|
| Marsland Ch 13 for `l12-stacking` | excluded | probe pp. 288–301: `stacking` NOT FOUND, `out-of-bag` NOT FOUND | chapter covers boosting, bagging, random forests and mixtures of experts but not stacking | n/a — Géron Ch 7 p. 236 covers it instead |
| Marsland Ch 14 for hierarchical clustering | excluded | probe pp. 302–325: `hierarchical` and `dendrogram` NOT FOUND | chapter is k-means as competitive learning and SOM only | route claims only `clustering-kmeans` and `clustering-initialization` |
| Ottmann–Widmayer Kap. 8 for kd-trees | excluded | probe pp. 487–570: `k-d-Baum` NOT FOUND; only `Bereichsanfrage` p. 500, `Bereichssuche` p. 553 | range search is not the deck's kd/M-tree/LSH content; cross-domain reach per ADR-005 was attempted and failed | if a data-structures source covering kd-trees is registered |
| `knowledge-sad-l13-exact-indexing`, `knowledge-sad-l13-lsh` | **unresolved gap** | L13 slides 24–31 (kd-trees, k-means trees, M-trees, LSH); no registered source covers them beyond ESL §13.5's cost argument | eight taught slides with no book, no exercise and no external bank in the whole registry | register a similarity-search or multidimensional-index source |
| `knowledge-sad-l13-metrics` | gap, low severity | deck slide 32 defines the metric axioms; Kelleher §5.2.2 restates them; §5.8 exercises use Euclidean only | axiom checking is a definition drill the exam-prep stage already demands in `stage-m2-sad-s11` | none needed |
| `source-mit-6034-quizzes` | unverified this pass | URL source (MIT OCW); no network access during this audit | existing routes to L12/L13/L15 left untouched | re-check with `validate.py --online` |
| `geron-copy2.pdf` | duplicate | second file in `geron-handson/` | same title, not routed; `geron.pdf` is the routed copy | none |
| Géron Ch 1 exercise solutions | partial | p. 61 reads "Solutions to these exercises are available in ???" | early-release copy has an unresolved cross-reference | answers must be checked against the chapter body |

## Unit knowledge and material matrix

Per lecture: knowledge nodes, routes before → after this package, and how many
nodes still lack any practice- or implementation-depth material.

| Unit | Nodes | Routes before → after | Nodes with no practice/implementation before → after | Nodes served only by one depth before → after | Remaining unserved nodes |
|---|---|---|---|---|---|
| `unit-m2-sad-clustering` | 5 | 5 → 9 | 5 → **0** | 0 → 0 | none |
| `unit-m2-sad-l01` | 7 | 10 → 10 | 1 → **1** | 1 → 1 | `l01-course-map` |
| `unit-m2-sad-l02` | 7 | 10 → 10 | 2 → **2** | 1 → 1 | `l02-vocabulary`, `l02-simpson` |
| `unit-m2-sad-l03` | 7 | 12 → 13 | 2 → **0** | 0 → 0 | none |
| `unit-m2-sad-l04` | 7 | 19 → 19 | 1 → **1** | 1 → 1 | `l04-framing` |
| `unit-m2-sad-l05` | 7 | 18 → 18 | 2 → **2** | 1 → 1 | `l05-repetition`, `l05-identities` |
| `unit-m2-sad-l06` | 7 | 18 → 18 | 2 → **2** | 0 → 0 | `l06-random-variable`, `l06-sample-mean` |
| `unit-m2-sad-l07` | 6 | 20 → 20 | 1 → **1** | 0 → 0 | `l07-relationships` |
| `unit-m2-sad-l08` | 7 | 19 → 19 | 1 → **1** | 0 → 0 | `l08-likelihood` |
| `unit-m2-sad-l09` | 7 | 15 → 16 | 2 → **1** | 1 → 1 | `l09-data-bias` |
| `unit-m2-sad-l10` | 8 | 15 → 16 | 2 → **1** | 2 → 1 | `l10-ci-duality` |
| `unit-m2-sad-l11` | 7 | 6 → 13 | 6 → **0** | 0 → 0 | none |
| `unit-m2-sad-l12` | 7 | 10 → 14 | 4 → **0** | 1 → 0 | none |
| `unit-m2-sad-l13` | 7 | 7 → 10 | 4 → **3** | 1 → 1 | `l13-metrics`, `l13-exact-indexing`, `l13-lsh` |
| `unit-m2-sad-l14` | 7 | 11 → 16 | 4 → **0** | 2 → 0 | none |
| `unit-m2-sad-l15` | 8 | 17 → 20 | 3 → **1** | 1 → 0 | `l15-outlook` |
| **total** | **111** | **212 → 241** | **42 → 16** | **12 → 7** | |

### Reading the remaining sixteen

Eleven are **framing or definition nodes where a drill is the wrong instrument** —
`l01-course-map` (the descriptive→inference→ML roadmap), `l02-vocabulary`,
`l04-framing`, `l15-outlook` (the CNN/RNN/Transformer preview), `l05-repetition`
and `l05-identities`, `l06-random-variable`, `l07-relationships`, `l08-likelihood`,
`l09-data-bias`, `l02-simpson`. Each already carries course-aligned and derivation
material; what they need is recall, and the exam-prep stages already demand it.

Two are **arithmetic nodes that would benefit from a drill and have none**:
`l06-sample-mean` and `l10-ci-duality`. Both are load-bearing for the inference
chain and both are worth a purpose-built exercise-bank entry rather than a new source.

Three are **genuine unserved scope**: `l13-metrics`, `l13-exact-indexing`, `l13-lsh`.
The indexing pair is the real one — eight taught slides with nothing behind them.

## What changed, in one line per unit

| Unit | Added |
|---|---|
| `unit-m2-sad-clustering` | Geron Ch 9 - k-means plus the density family and cluster evaluation; Zacharski Ch 8 - k-means and hierarchical clustering traced step by step; Marsland Ch 14 - k-means as competitive learning; ESL 14.3 - cluster analysis as an objective, not an algorithm |
| `unit-m2-sad-l03` | Geron Ch 4 - the normal equation and gradient descent side by side |
| `unit-m2-sad-l09` | ISLP 5.2 - the bootstrap as a resampling estimate of standard error |
| `unit-m2-sad-l10` | ISLP Ch 13 - the multiple-testing slide worked out with labs and exercises |
| `unit-m2-sad-l11` | Geron Ch 1 - the ML vocabulary with failure cases attached; Geron Ch 2 - the pipeline executed end to end; Geron Ch 3 - the evaluation metrics of L11 as drills; Geron Ch 1 exercises - the L11 vocabulary tested back; Geron Ch 4 - the loss functions L11 names in one line; Zacharski Ch 5 - evaluating a classifier by hand; ESL Ch 7 - what cross-validation and the bootstrap actually estimate |
| `unit-m2-sad-l12` | Geron Ch 6 - trees you can grow and prune; Geron Ch 7 - the three ensemble families side by side; Marsland Ch 12-13 - ID3 and the ensembles as algorithms; ESL - the ensemble chapters behind the L12 summary slide |
| `unit-m2-sad-l13` | Zacharski Ch 2 - the distance measures of L13 computed on real vectors; Zacharski Ch 5 - k-NN aggregation and imbalance in practice; ESL Ch 13 - nearest neighbours and the cost of searching them |
| `unit-m2-sad-l14` | Zacharski Ch 6 - Naive Bayes with the zero-frequency failure exposed; Zacharski Ch 7 - the bag-of-words model behind Multinomial Bayes; Marsland Ch 16 - Bayesian networks and the Markov blanket; Cornell CS4780 HW4 - solution-backed Naive Bayes problems; Kelleher Ch 6 exercises - Gaussian Naive Bayes worked on data |
| `unit-m2-sad-l15` | Geron Ch 10 - MLP shapes and outputs made concrete; Geron Ch 11 - the training choices L15 lists as tricks; Marsland Ch 3-4 - from the single neuron to backprop and universality |

## Completeness sign-off

- [x] Every file under each declared local root has an inventory row or is covered by its shelf's generated `SOURCES.md` listing.
- [x] Every link named by the newly routed material has a row; the one URL-only source is flagged unverified-this-pass.
- [x] Materials were opened; every page number in this package came from a text probe of the local PDF, and three candidate routes were dropped when the probe contradicted the chapter title.
- [x] Current and prior-year scope reconciled: the 2025 recordings keep `scope: prior-year` and no added route claims `current`.
- [x] Suspected duplicates checked: `geron-copy2.pdf` recorded as a duplicate and left unrouted.
- [x] Every added route carries unit, title, format, lecture-specific angle, covers, depth, scope and an exact locator.
- [x] Every rich route names only knowledge nodes declared by its own unit — checked programmatically, 0 unresolved.
- [x] Learner choices untouched: `source_selections` remains `[]` on every lecture unit; this package extends the menu, never the choice.
- [x] Exercise gaps and unreachable material are explicit above, not silently filled.
- [x] Every ordinary lecture has its own row in the matrix; the clustering topic is auxiliary and marked as such.

## What this audit does not claim

It does not claim the plan is finished. It claims that after this package every
lecture in the ML half of the course, and every lecture in the statistics half
except the eleven framing nodes and the three named gaps, has material behind each
concept it teaches at a depth you can work rather than only read. Whether that
material is *good* is a judgement recorded in source evaluations, not here — and
no evidence of mastery is asserted anywhere in this document.
