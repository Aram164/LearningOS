# M2 route-rigor coverage audit — 2026-08-29

Plan package: `work/active/workspace-m2-exam-prep/outputs/M2-route-rigor-plan-2026-08-29.yaml`

Scope: the M2 source map only. No unit is created, renamed or reordered; no
knowledge node changes. This pass repairs route *addresses* and writes the
`angle_detail` field that the 2026-08-28 rules require, for the routes that
commit left behind when it backfilled the SaD lecture maps and stopped.

## Local material inventory

Every page number written by this pass was read on 2026-08-29 from the PDF's own
outline or its printed table of contents. No page is inferred from a chapter
number, and no route was re-addressed from a filename.

| Source | Opened evidence | What the locator now names |
|---|---|---|
| `cs229-notes.pdf` (216 pp) | outline | §4 Generative learning p. 36, §4.2 Naive Bayes p. 43, §4.2.1 Laplace p. 46, §4.2.2 event models p. 48, §7 Deep learning p. 82, Backpropagation p. 93 |
| `csc411.pdf` (134 pp) | printed contents, pp. 2-3 | Ch 8 Classification printed p. 42 (§8.3 ANNs, §8.5 generative vs discriminative, §8.7 Naïve Bayes), §7.2-7.3 printed p. 35, §3.3 printed p. 9, §9 printed p. 53 |
| `mml-book.pdf` (417 pp) | outline | Ch 5 Vector Calculus p. 145 (§5.2 p. 152, §5.4 p. 161, §5.5 p. 164, §5.6 p. 165), Ch 9 Linear Regression p. 295 (§9.1 p. 297, §9.2 p. 298) |
| `statistik.pdf` (665 pp) | outline | Kap. 2 p. 46, 3 p. 126 (§3.6 p. 168), 4 p. 193, 5 p. 242, 6 p. 288, 7 p. 329, 9 p. 382, 10 p. 416 (§10.2 p. 430), 11 p. 450, 12 p. 491 |
| `arbeitsbuch.pdf` (306 pp) | outline | Kap. 5 p. 96, 9 p. 180, 10 p. 200, 11 p. 219 |
| `kelleher.pdf` (631 pp) | outline | Ch 4 p. 156, Ch 5 p. 215, Ch 6 p. 282, Ch 7 p. 351, Ch 8 p. 425, Ch 1-2 p. 36-91 |
| `blitzstein.pdf` (636 pp) | outline | Ch 1 p. 18, Ch 2 p. 62 |
| `kroese.pdf` (533 pp) | outline | Ch 4 Unsupervised Learning p. 139 (risk/loss p. 140, mixture models p. 153, vector quantization p. 160, hierarchical p. 165), p. 38 |
| `islp.pdf` (613 pp) | outline | §12.4 Clustering Methods p. 526 (§12.4.1 p. 527, §12.4.2 p. 531, §12.4.3 p. 538), §12.5 lab p. 541 |
| `lecture-slides/11_datascience_intro.pdf` | page count | 49 slides, supervised/unsupervised framing section |
| `exercise-slides/UE7.pdf` | page count | 88 slides, clustering block slides 32-87 |
| `exercise-slides/` Blatt+UE set | page counts | Blatt1 4 pp, blatt-02 3 pp, Übung-3 3 pp, blatt-05 4 pp, UE2 61 pp, UE3 54 pp, UE4 69 pp, UE5 77 pp, UE6 82 pp, UE7 88 pp |
| `12_clustering.pdf` (2025) | page count | 157 slides, prior-year full clustering lecture |
| `FAU-Erlangen_Statistik-Klausur_WS14-15_mit-Loesungen.pdf` | page count | 50 pp, solved |
| sad-klausuren-extern (4 files) | page counts | HS-Harz 7 pp, Köln 8 pp, Regensburg-Löh 14 pp, Leuphana-Merz 109 pp |
| `esl.pdf`, `geron.pdf`, `Zacharski…pdf`, `Marsland…pdf` | outline | locators were already page-exact; only `angle_detail` was added |

## Linked and unresolved material

| Source | Why the address stays inexact |
|---|---|
| MIT 18.05, MIT 6.034 quizzes, Cornell CS4780 homeworks, StatQuest | No local copy. The locator now names the exact paper/episode set and the addressing scheme (quiz number, episode title) instead of hedging, but a page or timestamp cannot be given from here. |
| Professor Leonard, 3Blue1Brown, zedstatistics, CS229 2022 videos, Stat 110, MIT 6.036, MIT 6.041SC, Berkeley CS189, Ng/Coursera, CS229 problem sets, ISLP community solutions | **Not repaired in this pass.** These are video or interactive courses with no local file; the rule accepts a quoted item title as an address, but writing one would mean asserting an episode or lecture title that cannot be verified from here. Left as recorded visibility debt, to be repaid on first use (WORKFLOWS §6a). |
| Grinstead & Snell, Jurafsky SLP3, D2L, Nielsen, Bishop, Goodfellow, Prince | **Not repaired in this pass.** Freely published books whose official PDFs would give real page numbers, but no local copy exists and the pagination differs between editions. Fetching the official contents is the correct repair and is a separate step. |

## Two routes held for review, not repaired

| Route | What is wrong | Why it is not fixed here |
|---|---|---|
| `source-swanson-principles-probability` → `unit-m2-sad-l06` | The angle says the book "says what a random variable formally is — a measurable function". LNM 2384 is a monograph on inductive/probabilistic logic: Boolean algebras §2.2 p. 47, a four-page §2.3 Measure Spaces p. 48, then propositional calculus p. 56, propositional models p. 103, predicate logic p. 147 with §5.4 "Predicate Models and Random Variables" p. 182. The judgment describes a different book. | Changing a contextual source evaluation needs visible review (CLAUDE.md §4). The angle is left standing and the mismatch recorded. |
| `source-islp` → `unit-m2-sad-clustering` | Pointed at "§12.2", which is Principal Components Analysis p. 510, while its angle describes k-means, hierarchical clustering and validation. | **Repaired** — here the locator was wrong and the judgment was right, and a locator is a fact. Now §12.4, p. 526-541. |

## Current and prior scope reconciliation

| Item | Decision |
|---|---|
| `unit-m2-sad-exam-prep` and `unit-m2-combined-exam-rehearsal` study maps | Authored independently of the routes — their per-stage labels do not correspond to route titles. Their source-map routes are repaired; their study maps are deliberately left untouched, because regenerating them from the knowledge map would rename every stage and restructure two units this pass was not asked to restructure. |
| Eight assembler-owned units | Study maps regenerated so the sharpened locators and the new `angle_detail` reach the stage rows the interface renders. |
| `12_clustering.pdf` (2025) vs current L12 | Prior-year deck, same file number as the current trees lecture. Recorded in its angle_detail: practice and reference only, never scope evidence, and not a source for current L12. |

## Explicit exclusions and unresolved gaps

| Item | Disposition |
|---|---|
| 39 routes on video/interactive/online-book sources | unresolved — named above with the reason; repaid on use |
| AML (359 warnings) and algo2 (37) | out of scope for this pass by instruction; the same repair, one lane over |
| Swanson evaluation | open, awaiting review |

## Completeness

- [x] Every route repaired here had its material opened on 2026-08-29 before its locator changed.
- [x] No page number is inferred from a chapter number.
- [x] Routes whose material could not be opened were left unrepaired and named, rather than given a plausible-looking address.
- [x] A wrong source evaluation was surfaced rather than silently rewritten.
- [x] Units whose study maps are not assembler-owned were left structurally untouched.
- [x] No unit, node, stage or unit order changes in this package.

No claim of mastery or readiness is made anywhere in this document.
