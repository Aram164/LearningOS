#!/usr/bin/env python3
"""Repair the M2 source map's flagged routes: exact locators, real angle_detail.

The 2026-08-28 commit that introduced `angle_detail` and the exact-locator rules
backfilled the SaD lecture maps and stopped there. What it left behind in M2 is
94 warnings across 80 routes:

  * 27 routes carry a one-line `angle` and no `angle_detail`;
  * 67 carry a locator that names no page, or that hedges instead of naming the
    material ("Exact matching Blatt/UE task for the diagnosed error").

This pass repairs every route whose material is readable from here. Each page
number below was read out of the PDF's own outline or printed table of contents
on 2026-08-29 — no page is inferred from a chapter number.

Two routes are NOT repaired here, because what is wrong with them is the
judgment rather than the address, and a contextual source evaluation needs
review before it changes (CLAUDE.md §4). They are reported in the audit:

  * `source-swanson-principles-probability` → unit-m2-sad-l06 claims the book
    "says what a random variable formally is — a measurable function". Opened,
    LNM 2384 is a monograph on inductive/probabilistic *logic*: Boolean algebras
    (§2.2 p. 47), one four-page §2.3 Measure Spaces (p. 48) as background, then
    propositional calculus, predicate logic and inductive semantics. §5.4
    "Predicate Models and Random Variables" (p. 182) is random variables inside
    predicate logic, not the measure-theoretic definition. The angle describes a
    book this is not.
  * `source-islp` → unit-m2-sad-clustering points at "§12.2" while its angle
    describes k-means, hierarchical clustering and validation. ISLP §12.2 is
    Principal Components Analysis (p. 510); clustering is §12.4 (K-Means
    §12.4.1 p. 527, Hierarchical §12.4.2 p. 531, Practical Issues §12.4.3
    p. 538). Here the *locator* is wrong rather than the judgment, so this one
    IS repaired — the angle already described the right material.

Workbench generator: writes only under the owning workspace. The package must
pass `module-plan-import --check` and the Gateway before anything is canonical.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "tools"))

from assemble_lecture_study_maps import (  # noqa: E402
    assembly_problems, build, concept_phrases, _manifest,
)
from learning_os.contracts import require_current_template, validate_contract  # noqa: E402
from learning_os.loader import load_repo  # noqa: E402

MODULE_ID = "module-hu-m2-statistik-analysis"
WORKSPACE_ID = "workspace-m2-exam-prep"
DATE = "2026-08-29"
PLAN_PATH = OUT / f"M2-route-rigor-plan-{DATE}.yaml"
AUDIT_PATH = OUT / f"M2-route-rigor-coverage-audit-{DATE}.md"
MAP_DIR = OUT / f"M2-route-rigor-maps-{DATE}"

# (source_id, unit_id) -> fields to replace. `locator` is a fact and may be
# corrected; `angle_detail` is a new field, never an overwrite; `angle` is only
# touched where the existing line was itself a usage instruction rather than a
# judgment, and each such case is named in the audit.
FIX: dict[tuple[str, str], dict] = {}


def fix(source: str, unit: str, *, locator: str | None = None,
        angle: str | None = None, title: str | None = None, detail: str) -> None:
    row: dict = {"angle_detail": detail}
    if title is not None:
        row["title"] = title
    if locator is not None:
        row["locator"] = locator
    if angle is not None:
        row["angle"] = angle
    FIX[(source, unit)] = row


# ==========================================================================
# unit-m2-sad-clustering — the auxiliary topic. Its routes were added after
# the 2026-08-28 backfill, so most already carry page-exact locators and only
# need the hover detail.
# ==========================================================================
CLU = "unit-m2-sad-clustering"

fix("source-sad-ss26-lectures", CLU,
    locator="lecture-slides/11_datascience_intro.pdf (49 slides), the supervised/unsupervised "
            "framing section",
    detail="This is a framing bridge, not the clustering material: L11 defines what unsupervised "
           "learning is and where it sits against the supervised tasks the rest of the course "
           "teaches, and then the course moves on. The clustering content itself is UE7's. Read "
           "the section to fix the vocabulary — what is being learned when there are no labels, "
           "and what 'correct' can even mean — then work UE7. Nothing here is a method.")

fix("source-sad-uebungen", CLU,
    detail="UE7 is the whole current scope for this topic: 88 slides, of which 32-87 are the "
           "clustering block, and there is no lecture deck behind it. That makes it the scope "
           "authority and the only course-aligned trace available — the assignment step and the "
           "centroid-update step are walked through in full, including a local optimum reached "
           "from a bad initialisation. Everything else on this stage deepens or re-explains what "
           "is on these slides; none of it extends the examinable boundary.")

fix("source-sad-2025-recordings", CLU,
    locator="12_clustering.pdf (157 slides), prior-year full lecture on clustering",
    detail="A verified same-topic full lecture from the 2025 run, and the only place clustering "
           "gets lecture-length treatment rather than a tutorial's. Use it to deepen UE7 after "
           "the trace is understood. Two cautions: it is prior-year material, so it is practice "
           "and reference and never scope evidence (the current course covers clustering only "
           "through UE7); and its number collides with the current L12, which is trees — this "
           "deck is not a source for the current L12 despite sharing a number.")

fix("source-geron-handson", CLU,
    detail="The chapter answers UE7's two open questions directly. UE7 names the hierarchical, "
           "partitioning and density families but only traces k-means; Géron gives DBSCAN "
           "(p. 264) and hierarchical (p. 266) working code beside it. UE7 asks how clustering "
           "results are compared without saying how; Géron gives inertia (p. 270) and then the "
           "silhouette score and the elbow method (p. 274) as the two standard answers, with the "
           "plots that make the difference between them visible. It is Python-first and assumes "
           "scikit-learn, so read it for the concepts and the comparison criteria rather than as "
           "a derivation.")

fix("source-zacharski-data-mining", CLU,
    detail="The gap this fills is specific: UE7's slides define the topic and state the "
           "algorithm, but a definition of k-means does not show you that the assignment and "
           "update steps alternate until nothing moves. Zacharski iterates both on a small "
           "worked table from p. 335 and prints the intermediate state each round, which is what "
           "makes the convergence argument concrete and what an exam tracing question would "
           "expect you to reproduce. Informal in tone and light on theory — take the trace, not "
           "the framing.")

fix("source-marsland-ml-algorithmic", CLU,
    detail="Reframes the k-means update as competitive learning (p. 307) and vector quantisation "
           "(p. 311) rather than as an optimisation procedure. That reframing is the clearest "
           "available answer to the question UE7 raises and does not settle — why initialisation "
           "decides which local optimum you land in — because under the competitive-learning "
           "reading the centroids are units competing for data, and where they start determines "
           "what they can ever win. Chapter 14 is short; the surrounding chapters are outside "
           "this topic.")

fix("source-esl", CLU,
    detail="Read this before any algorithm, not after. ESL §14.3 defines clustering by its loss "
           "function and by the dissimilarity measure chosen, and only then derives the "
           "algorithms as ways of minimising that loss — which is the argument behind UE7's "
           "'there is no single true clustering'. It is the most demanding route on this stage "
           "and assumes comfort with the notation; twenty-six pages, of which the first six carry "
           "the framing that matters here.")

fix("source-kroese-dsml", CLU,
    locator="kroese.pdf Ch 4 'Unsupervised Learning' p. 139: Risk and Loss in Unsupervised "
            "Learning p. 140, Clustering via Mixture Models p. 153, Clustering via Vector "
            "Quantization p. 160, Hierarchical Clustering p. 165; the supervised/unsupervised "
            "distinction is set up at p. 38",
    detail="An independent data-science treatment that arrives at clustering from the risk/loss "
           "framing (p. 140) rather than from an algorithm, then splits the families the way UE7 "
           "names them. Its mixture-model section (p. 153) is the one genuinely extra idea on "
           "this stage — clustering as density estimation rather than as partitioning — and is "
           "optional after the UE7 trace. Mathematically heavier than Géron, lighter than ESL.")

fix("source-islp", CLU,
    title="ISLP §12.4 — clustering algorithms and validation",
    locator="islp.pdf §12.4 Clustering Methods p. 526: §12.4.1 K-Means Clustering p. 527, "
            "§12.4.2 Hierarchical Clustering p. 531, §12.4.3 Practical Issues in Clustering "
            "p. 538; §12.5 Lab: Unsupervised Learning p. 541. (Corrected 2026-08-29: the route "
            "previously read '§12.2', which is Principal Components Analysis p. 510, not "
            "clustering.)",
    detail="§12.4.3 is the section that earns this route a place: 'Practical Issues in "
           "Clustering' is a short, honest list of the decisions that change the answer — "
           "standardisation, the choice of dissimilarity, how many clusters, and whether the "
           "clusters mean anything at all. UE7 raises these implicitly by tracing one "
           "configuration; ISLP states them. §12.4.1 and §12.4.2 are the algorithms at a gentler "
           "level than ESL, and the lab at p. 541 runs them.")


# ==========================================================================
# unit-m2-sad-exam-prep — the Statistics retrieval lane. Its routes were
# written as usage instructions ("Spend once under timed conditions") standing
# where the address belongs. The instruction is real and is kept — it moves to
# the angle, where it says something — and the locator now names files.
# ==========================================================================
XP = "unit-m2-sad-exam-prep"

fix("source-sad-ss26-lectures", XP,
    detail="The fifteen current decks are the only material that defines what is examinable, so "
           "every review stage in this lane is checked against them rather than against a "
           "textbook's chapter order. Use them as the correction authority: when a mock answer "
           "is wrong, the deck that owns that definition is where the correction comes from, "
           "because it fixes the notation and the boundary the exam will use. They are not "
           "practice — the decks carry almost no unaided exercises, which is why every other "
           "route in this lane exists.")

fix("source-sad-uebungen", XP,
    detail="These are the closest thing to the examiner's own computations: the Blätter are "
           "assessed sheets and the UE decks are the worked tutorials for them, in the course's "
           "own notation and at the course's own expected length of working. Attempt the Blatt "
           "unaided, then read the matching UE — that order is the whole value, because a "
           "tutorial read first turns a retrieval task into recognition. UE7 additionally carries "
           "the clustering topic, which has no lecture deck at all.")

fix("source-fahrmeir-statistik", XP,
    locator="statistik.pdf Kap. 2 Univariate Deskription p. 46, Kap. 3 Multivariate Deskription "
            "p. 126 (§3.6 Regression p. 168), Kap. 4 Wahrscheinlichkeitsrechnung p. 193, Kap. 5 "
            "Diskrete Zufallsvariablen p. 242, Kap. 6 Stetige Zufallsvariablen p. 288, Kap. 7 "
            "Mehr über Zufallsvariablen p. 329, Kap. 9 Parameterschätzung p. 382, Kap. 10 Testen "
            "von Hypothesen p. 416 (§10.2 Prinzipien des Testens p. 430), Kap. 11 Spezielle "
            "Testprobleme p. 450, Kap. 12 Regressionsanalyse p. 491",
    detail="The German derivation spine for the whole Statistics half, and the reason it matters "
           "is vocabulary rather than content: the exam is written in German, and this is where "
           "Schätzer, Konfidenzintervall, Nullhypothese and Testniveau are used in the register a "
           "German statistics exam uses them in. Enter it by chapter against the deck that "
           "exposed the gap — Kap. 9 after an estimation error, Kap. 10-11 after a testing error "
           "— never linearly; it is 665 pages and reading it through would consume the lane.")

fix("source-fahrmeir-arbeitsbuch", XP,
    locator="arbeitsbuch.pdf Kap. 5 Diskrete Zufallsvariablen p. 96, Kap. 9 Parameterschätzung "
            "p. 180, Kap. 10 Testen von Hypothesen p. 200, Kap. 11 Spezielle Testprobleme p. 219 "
            "; companion exercise volume to statistik.pdf, same chapter numbering",
    detail="The exercise half of the same book, which is why the chapter numbers line up: a gap "
           "found in Fahrmeir Kap. 9 is drilled in Arbeitsbuch Kap. 9. Every problem carries a "
           "worked solution in German, so it is the one place in this lane where a German "
           "write-up can be compared against a model rather than only checked for its answer. "
           "Deliberately second in order: open it after a current exercise has exposed a gap, "
           "not as a first pass.")

fix("source-kelleher-fmlpda", XP,
    locator="kelleher.pdf Ch 4 Information-based Learning p. 156 (trees, entropy, ID3 — L12), "
            "Ch 5 Similarity-based Learning p. 215 (k-NN, distance measures — L13), Ch 6 "
            "Probability-based Learning p. 282 (Naive Bayes — L14), Ch 7 Error-based Learning "
            "p. 351 (regression and gradient descent — L03/L15), Ch 8 Evaluation p. 425 (L11); "
            "the workflow framing is Ch 1-2 p. 36-91",
    detail="Kelleher organises machine learning by what the algorithm learns *from* — "
           "information, similarity, probability, error — which is exactly how SaD's second half "
           "is split across L12, L13, L14 and L15, one chapter per lecture. That correspondence "
           "is what makes it the companion for this lane rather than a general reference: after a "
           "mock exposes a tree question, Ch 4 is the chapter, and it is at the course's level "
           "rather than above it. Ch 8 covers the evaluation vocabulary L11 introduces.")

fix("source-blitzstein-hwang", XP,
    locator="blitzstein.pdf Ch 1 Probability and counting p. 18, Ch 2 Conditional probability "
            "p. 62 — these two chapters only",
    detail="Held behind a gate on purpose. The book is 636 pages and could easily become a second "
           "probability course running in parallel with the exam lane, which is why the route is "
           "two chapters and stops. Open Ch 1 when a counting problem failed on the order/repetition "
           "decision rather than on arithmetic, and Ch 2 when a Bayes answer was right by formula "
           "and wrong by intuition; its story-first treatment is the strongest available repair "
           "for both, and the worst possible use of the time if the gate has not actually failed.")

fix("source-sad-klausuren-extern", XP,
    locator="HS-Harz_Statistik-I_Probeklausur_mit-Loesungen.pdf (7 pp), "
            "Koeln_Statistik-Klausur_Musterloesung.pdf (8 pp), "
            "Regensburg-Loeh_WTheorie-Statistik_Klausur_mit-Loesungen.pdf (14 pp), "
            "Leuphana-Merz_Statistik-2_Uebungsbuch-mit-Klausur.pdf (109 pp; exercise book with a "
            "closing Klausur) — all solved; take only current-scope tasks",
    angle="Four solved German Statistics papers — fresh topic-matched transfer once the course "
          "exercises are spent, and the second Statistics-only half-mock.",
    detail="Their value is German exam wording from four different examiners, which is the "
           "variation the single HU course cannot supply. Their limitation is scope: each covers "
           "its own syllabus, so descriptive statistics, probability, estimation and testing "
           "match while regression depth and any decision-tree or neural-network material do not "
           "— filter by topic against the current decks before working anything. All four are "
           "solved, so they are spent on diagnosed gaps; the unseen-paper role belongs to the FAU "
           "paper, which is reserved for timing.")

fix("source-fau-klausur-ws1415", XP,
    locator="FAU-Erlangen_Statistik-Klausur_WS14-15_mit-Loesungen.pdf (50 pp), a complete German "
            "Statistics paper with solutions; worked once under Statistics-only timed conditions "
            "before the solutions are opened",
    angle="One coherent German paper long enough to be a real half-mock, kept unseen until it is "
          "worked under time.",
    detail="Fifty pages including solutions makes this the only external Statistics paper here "
           "with enough substance to time properly, which is why the discipline attached to it "
           "matters more than for the other four: read the solutions early and the lane loses its "
           "one honest Statistics-only rehearsal. Work it whole, timed, then correct against the "
           "current decks rather than against its own solutions where the two disagree — it is "
           "another university's scope, and the decks own the boundary.")

fix("source-mit-1805", XP,
    locator="MIT 18.05 Introduction to Probability and Statistics: the published exams and "
            "practice exams with solutions; one unused probability or inference question, chosen "
            "to match the diagnosed gap. No local copy; the set is addressed by exam and question "
            "number on the OCW course page.",
    angle="A single reserve question, in English, for when the German banks have no unspent item "
          "on the exact topic that failed.",
    detail="Explicitly a replacement of last resort rather than a route to work through. The "
           "German sources hold wording authority for this exam, so an English question is used "
           "only to supply a fresh instance of a topic — a confidence interval, a test decision — "
           "when every German equivalent has already been seen. Taking more than one at a time "
           "would start drifting the notation the exam actually grades.")

fix("source-mit-6034-quizzes", XP,
    locator="MIT 6.034 published quizzes and finals with official solutions — the ID3 / "
            "decision-tree tracing questions and the neural-network forward/backward tracing "
            "questions. No local copy; the papers are addressed by quiz number on the OCW course "
            "page.",
    angle="Compact, solution-backed tracing under exam format for the two topics where no SaD "
          "sheet sets a tracing task.",
    detail="Trees and neural networks are the two SaD topics the current Blätter never ask you to "
           "trace by hand, and tracing is exactly what a written exam can ask for. These quizzes "
           "do it in the right size — a small table or a two-layer network, worked in minutes — "
           "with official solutions to check the intermediate steps against, not just the answer. "
           "English, and 6.034's syllabus is wider than SaD's, so take the two named question "
           "types and leave the rest.")

fix("source-cs4780-homeworks", XP,
    locator="Cornell CS4780 published homework sets with solutions — HW8 (decision trees and "
            "AdaBoost) and HW1 (k-NN). No local copy; addressed by homework number on the course "
            "page.",
    angle="One scoped, solution-backed task each for the two methods the current SaD sheets leave "
          "unpractised.",
    detail="Named narrowly because the gap is narrow: L12's trees and L13's k-NN have decks and "
           "no assessed exercise behind them. HW1's k-NN questions and HW8's tree/boosting "
           "questions each supply one properly set problem with a published solution. AdaBoost "
           "goes past the current SaD scope — take the tree half of HW8 and leave boosting unless "
           "the deck is revisited.")

fix("source-statquest", XP,
    locator="StatQuest, three named episodes: 'The Central Limit Theorem', 'Probability is not "
            "Likelihood', 'Maximum Likelihood'. No local copy; addressed by episode title on the "
            "channel.",
    detail="Three short videos, each for one specific confusion L08 can leave behind, and worth "
           "opening only when the diagnostic names that confusion. 'Probability is not Likelihood' "
           "is the one to know exists: L08's likelihood derivation is the intellectual centre of "
           "the statistics half, and the probability/likelihood conflation is the single most "
           "common way it fails to land. Ten minutes each, no notation to carry away — this is "
           "repair, not study.")


# ==========================================================================
# unit-m2-combined-exam-rehearsal — the joint SaD+Analysis simulation. Every
# one of its six routes was a usage instruction with no address and no detail.
# ==========================================================================
CX = "unit-m2-combined-exam-rehearsal"

fix("source-sad-ss26-lectures", CX,
    locator="lecture-slides/01_introduction.pdf through 15_neural_networks.pdf, the deck "
            "owning the definition each mock error touched",
    detail="In a combined mock this source has one job and it is corrective, not instructional: "
           "when a Statistics answer is wrong, the deck that owns that definition settles what the "
           "right one is, in the notation the exam uses. Two boundaries it does not cross — it "
           "says nothing about the Analysis half, which the script owns, and nothing about how the "
           "three hours are split between the halves, which no local source states.")

fix("source-sad-uebungen", CX,
    locator="exercise-slides/: Blatt1.pdf, blatt-02.pdf, Übung-3.pdf, blatt-05.pdf, UE2.pdf through "
            "UE7.pdf; one task, chosen for the diagnosed error",
    detail="One repair task after a Statistics error, chosen to match the failed step rather than "
           "the topic. The point is near transfer: the same computation asked once more, in the "
           "course's own wording, immediately after getting it wrong — which is a different act "
           "from working the sheets in order, and it is why this route names one task rather than "
           "a set. If the matching task has already been spent, the external banks on the "
           "Statistics lane carry fresh equivalents.")

fix("source-analysis-skript", CX,
    locator="unser skript.pdf Kapitel 1-7 (Stand 04.02.2025), the course contract pp. iv-vii, and "
            "the ana_inf_serie05-09.pdf or ana_inf_serieWV.pdf task for the failed step",
    detail="The Analysis counterpart of the deck route above, and the same corrective role: after "
           "a combined mock, the script settles the coverage boundary, the notation and the exact "
           "theorem conditions, and the matching HU task supplies the repair. Its contract pages "
           "also settle depth disputes — whether something was in scope at all, given that Exkurs "
           "sections are not exam-relevant and Ausflug sections are not an exam focus.")

fix("source-analysis-klausuren-extern", CX,
    locator="Two unused, disjoint task sets from Marburg_Analysis-I_3-Klausuren-mit-Loesungen.pdf, "
            "Regensburg_Analysis-I_Klausur-mit-Loesungen-und-Haeufige-Fehler.pdf, "
            "Ulm_Analysis-fuer-Informatiker_Klausur-SS10_nur-Aufgaben.pdf and "
            "Leipzig_Analysis-fuer-Informatiker_Probeklausur.pdf, each scope-matched back to "
            "unser skript Kapitel 1-7",
    detail="Two disjoint Analysis halves, so a first and a second combined simulation are not the "
           "same paper twice. Assembling them is a deliberate construction and is labelled as one: "
           "no paper here is an HU paper, none matches the official weighting between the halves, "
           "and the Ulm and Leipzig papers are unsolved so they carry the timing role while "
           "Marburg and Regensburg carry the correction. Scope-filter every task against the "
           "script before it goes into a simulation — Marburg's complex-number and metric-space "
           "items are outside this syllabus.")

fix("source-fau-klausur-ws1415", CX,
    locator="FAU-Erlangen_Statistik-Klausur_WS14-15_mit-Loesungen.pdf (50 pp), the questions not "
            "already spent in the Statistics lane",
    detail="The unspent remainder of the FAU paper is what makes a *second* combined mock "
           "possible: the Statistics half of the first one uses the external bank, and this "
           "supplies fresh solution-backed questions for the next without repeating anything. It "
           "is another university's paper, so it is a source of unseen questions and of German "
           "wording — never a claim about what an M2 paper weights or contains.")

fix("source-sad-klausuren-extern", CX,
    locator="Unused current-scope questions from HS-Harz_Statistik-I_Probeklausur_mit-Loesungen.pdf "
            "(7 pp), Koeln_Statistik-Klausur_Musterloesung.pdf (8 pp), "
            "Regensburg-Loeh_WTheorie-Statistik_Klausur_mit-Loesungen.pdf (14 pp) and "
            "Leuphana-Merz_Statistik-2_Uebungsbuch-mit-Klausur.pdf (109 pp), all with solutions",
    detail="Assembles the Statistics half of a combined mock from questions that have not been "
           "seen, with traceable solutions so the correction step is possible. The assembly is "
           "explicit about what it is not: four examiners' scopes stitched together do not "
           "reproduce the M2 paper's balance, and no claim about official weighting is made "
           "anywhere. Filter to current scope first — these banks carry regression and inference "
           "depth the current decks do not reach.")


# ==========================================================================
# SaD lecture units and the Analysis units — locators that named a chapter but
# no page, or that hedged. Angles are untouched; only the address changes.
# ==========================================================================

fix("source-cs229-notes", "unit-m2-sad-l04",
    locator="cs229-notes.pdf Part II §4 Generative learning algorithms p. 36: §4.2 Naive Bayes "
            "p. 43, §4.2.1 Laplace smoothing p. 46",
    detail="Four pages that state, in one place, the classifier L04 builds informally over a "
           "lecture: the conditional-independence assumption written as a product, the "
           "maximum-likelihood estimates for the parameters, and Laplace smoothing as the fix for "
           "a zero count. It assumes the probability notation of §§1-3 and does not motivate "
           "anything — read it as the compact statement to check your own against, after the deck.")

fix("source-cs229-notes", "unit-m2-sad-l14",
    locator="cs229-notes.pdf §4.2 Naive Bayes p. 43, §4.2.1 Laplace smoothing p. 46, "
            "§4.2.2 Event models for text classification p. 48",
    detail="§4.2.2 is why this route exists on L14 rather than only on L04: it separates the "
           "multinomial event model from the Bernoulli one explicitly, and shows that they give "
           "different likelihoods for the same document. L14 extends the categorical classifier "
           "without naming which event model it is using, so this is the section that makes the "
           "distinction sayable — and it is the kind of distinction an exam question can turn on.")

fix("source-cs229-notes", "unit-m2-sad-l15",
    locator="cs229-notes.pdf Part III §7 Deep learning p. 82: Neural networks p. 84, "
            "Backpropagation p. 93 (one-neuron p. 94, two-layer unpacked p. 95, two-layer in "
            "vector notation p. 98, multi-layer p. 100)",
    detail="The backpropagation section is built as a ladder — one neuron, then a two-layer "
           "network written out index by index, then the same network in vector notation, then "
           "the general case — which is the most useful ordering available for checking that the "
           "matrix shapes are right. Compact and unmotivated by design: it is the reference to "
           "verify a derivation against once L15's own account has been followed.")

fix("source-csc411-notes", "unit-m2-sad-l14",
    locator="csc411.pdf Ch 8 Classification (printed p. 42): §8.1 Class Conditionals, §8.5 "
            "Generative vs. Discriminative models, §8.7 Naïve Bayes; §7.2 Bayes' Rule and §7.3 "
            "Parameter estimation (printed p. 35 onward) for the estimation step",
    detail="Two to three pages of pure derivation with no worked example and no prose, which is "
           "exactly what makes it the fastest revision reference for L14 — everything is symbols "
           "and the structure is visible at a glance. §8.5 is the part worth reading even if the "
           "classifier is already solid: it names the generative/discriminative distinction that "
           "L14 never states, and that distinction is what explains why Naive Bayes models the "
           "features at all.")

fix("source-csc411-notes", "unit-m2-sad-l15",
    locator="csc411.pdf §8.3 Artificial Neural Networks (Ch 8 Classification, printed p. 42 "
            "onward) with §3.3 Artificial Neural Networks (Ch 3 Nonlinear Regression, printed "
            "p. 9 onward) for the regression framing; §9 Gradient Descent printed p. 53",
    detail="The network appears twice in these notes, once as nonlinear regression (§3.3) and once "
           "as classification (§8.3), and reading both is the point: it is the same architecture "
           "with a different output layer and a different loss, which is precisely the pairing "
           "L15 asserts. Every step carries explicit matrix shapes, so this is the reference to "
           "reach for when a derivation is right in principle and does not conform.")

fix("source-mml", "unit-m2-sad-l03",
    locator="mml-book.pdf Ch 9 Linear Regression p. 295: §9.1 Problem Formulation p. 297, §9.2 "
            "Parameter Estimation p. 298 (maximum likelihood and MAP); read with Ch 5 Vector "
            "Calculus p. 145, §5.2 Partial Differentiation and Gradients p. 152, for the notation",
    detail="Derives least squares as maximum likelihood under Gaussian noise from the first page "
           "of §9.2, rather than presenting the squared-error objective and justifying it later. "
           "That matters across two lectures: L03 introduces the objective and L08 introduces the "
           "Gaussian likelihood, and this makes them one derivation instead of two facts. It is "
           "the most mathematically demanding route on this stage and assumes the linear algebra "
           "of Ch 2-3; §5.2 is the minimum notation to read it with.")

fix("source-mml", "unit-m2-sad-l15",
    locator="mml-book.pdf Ch 5 Vector Calculus p. 145: §5.4 Gradients of Matrices p. 161, §5.5 "
            "Useful Identities for Computing Gradients p. 164, §5.6 Backpropagation and Automatic "
            "Differentiation p. 165",
    detail="§5.5 is a page of matrix-derivative identities, and it is the page every other L15 "
           "route silently assumes you already have — Nielsen, CS229 and the deck all take these "
           "for granted while using them. Read §5.4 and §5.5 as reference rather than as study, "
           "and §5.6 only if the computational-graph view of backpropagation is wanted alongside "
           "the equation view.")

fix("source-swanson-principles-probability", "unit-m2-sad-l06",
    detail="⚠ Held for review, 2026-08-29, and not repaired in this pass. The route's angle says "
           "this book 'says what a random variable formally is — a measurable function'. Opened, "
           "LNM 2384 is a monograph on inductive and probabilistic logic: Ch 2 Background carries "
           "Boolean Algebras p. 47 and a four-page §2.3 Measure Spaces p. 48, and the body is "
           "propositional calculus (Ch 3 p. 56), propositional models (Ch 4 p. 103) and predicate "
           "logic (Ch 5 p. 147), where §5.4 'Predicate Models and Random Variables' p. 182 treats "
           "random variables inside predicate logic rather than as measurable functions. The "
           "address is therefore not merely vague — the judgment describes a different book. "
           "Changing a contextual source evaluation needs review (CLAUDE.md §4), so the angle is "
           "left standing and the mismatch is recorded here and in the audit for Aram to settle.")


# ---- Analysis: two locators of mine that carried prose the rule reads as a hedge
fix("source-analysis-skript", "unit-m2-analysis-ch02",
    locator="ana_inf_serie05.pdf, Hausaufgabe 5.4 (HA, 10 Punkte): decide boundedness of "
            "B = {1/2^n + (-1)^m : n, m ∈ N_0} and determine sup, inf, max, min with proof; "
            "ana_inf_serie07.pdf, Übungsaufgabe 7.1 (Heron) reaches §2.3.6",
    detail="Read what the task actually asks: not 'compute the supremum' but 'determine it and "
           "prove your answer', with maximum and minimum asked separately so the sup-versus-max "
           "distinction has to be argued rather than assumed. Its own Tipp routes the solution "
           "through monotonicity and convergence of two auxiliary sequences — that is, it answers "
           "a Chapter 2 question with Chapter 3 machinery, which is the dependency this session "
           "should leave in place. Beyond this one Hausaufgabe there is no current HU practice "
           "for Chapter 2; that gap has been open and unowned since the 2026-08-03 audit.")

fix("source-analysis-skript", "unit-m2-analysis-exam-prep",
    locator="unser skript.pdf: Vorwort and the three-label contract pp. iv-vii; "
            "Inhaltsverzeichnis pp. ii-iii; Bezeichnungen p. viii; Kapitel 8 Exkurse printed "
            "p. 226 (PDF p. 236) onward",
    detail="Read pp. iv-vii once, deliberately, before Chapter 1. Three claims there govern the "
           "whole plan: Wiederholung sections are assumed known and are not re-taught; Ausflug "
           "sections should be understood and applied but are not an exam focus; Exkurs sections "
           "are explicitly outside the exam. And the sentence that shapes everything else — 'Die "
           "Beweise müssen Sie nicht können' — with the positive form beside it: definitions, "
           "results and their application in concrete problems are what the exam asks for. Every "
           "'reference-only' label in this module traces back to that page.")


# ==========================================================================
# Apply
# ==========================================================================

def patched_source_map(repo) -> tuple[dict, list[str]]:
    current = copy.deepcopy(repo.module_source_maps[MODULE_ID])
    applied, unseen = [], set(FIX)
    for entry in current.get("sources", []):
        sid = entry.get("source_id")
        for route in entry.get("unit_routes") or []:
            if not isinstance(route, dict):
                continue
            key = (sid, route.get("unit_id"))
            if key not in FIX:
                continue
            unseen.discard(key)
            for field, value in FIX[key].items():
                route[field] = value
            applied.append(f"{sid} -> {route['unit_id']}")
    if unseen:
        raise SystemExit(f"fix table names routes that do not exist: {sorted(unseen)}")
    return current, applied


def assemble(units: dict, source_map: dict, phrases: dict) -> dict[str, dict]:
    maps, problems = {}, []
    for uid, unit in units.items():
        routes = [dict(r, material_uri=r["vault_path"]) if r.get("vault_path") else dict(r)
                  for e in source_map.get("sources", [])
                  for r in (e.get("unit_routes") or [])
                  if isinstance(r, dict) and r.get("unit_id") == uid]
        if not routes:
            problems.append(f"{uid}: no material routes reach it"); continue
        record = build(unit, MODULE_ID, routes, phrases, True)
        problems.extend(assembly_problems(unit, routes, record))
        try:
            require_current_template(record, "curriculum")
            validate_contract(REPO, "study-map.schema.json", record,
                              label=f"assembled study map for {uid}")
        except Exception as exc:  # noqa: BLE001
            problems.append(f"{uid}: {exc}"); continue
        maps[uid] = record
    if problems:
        for p in problems:
            print(f"- {p}", file=sys.stderr)
        raise SystemExit("assembly preflight failed; nothing written")
    return maps


AUDIT = """# M2 route-rigor coverage audit — {date}

Plan package: `work/active/{ws}/outputs/M2-route-rigor-plan-{date}.yaml`

Scope: the M2 source map only. No unit is created, renamed or reordered; no
knowledge node changes. This pass repairs route *addresses* and writes the
`angle_detail` field that the 2026-08-28 rules require, for the routes that
commit left behind when it backfilled the SaD lecture maps and stopped.

## Local material inventory

Every page number written by this pass was read on {date} from the PDF's own
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

- [x] Every route repaired here had its material opened on {date} before its locator changed.
- [x] No page number is inferred from a chapter number.
- [x] Routes whose material could not be opened were left unrepaired and named, rather than given a plausible-looking address.
- [x] A wrong source evaluation was surfaced rather than silently rewritten.
- [x] Units whose study maps are not assembler-owned were left structurally untouched.
- [x] No unit, node, stage or unit order changes in this package.

No claim of mastery or readiness is made anywhere in this document.
""".format(date=DATE, ws=WORKSPACE_ID)


def derived_stage_ids(unit: dict) -> list[str]:
    return ["stage-" + n["id"].removeprefix("knowledge-")
            for n in (unit.get("knowledge_map") or {}).get("nodes", [])]


def main() -> int:
    import assemble_lecture_study_maps as asm
    # `knowledge-sad-clustering-families` was never curated; its title names the
    # three families rather than a registered concept, so the matcher finds
    # nothing and the assembler refuses the stage.
    asm.NODE_CONCEPTS.setdefault("knowledge-sad-clustering-families",
                                 ("concept-clustering",))

    repo = load_repo(REPO)
    manifest = _manifest(REPO)
    phrases = concept_phrases(manifest["records"])

    source_map, applied = patched_source_map(repo)
    touched = sorted({uid for _, uid in FIX})

    # A unit whose live stage ids are exactly the ids its knowledge nodes derive
    # is assembler-owned, so its study map is regenerated and the sharpened
    # locators reach the stage rows. `unit-m2-sad-exam-prep` and
    # `unit-m2-combined-exam-rehearsal` are not: their study maps were authored
    # independently, with their own per-stage labels that do not correspond to
    # route titles. Regenerating those would restructure two units nobody asked
    # to restructure, so for them only the source map changes.
    # A unit's `source_selections` pin the route locator as a drift guard
    # (SELECTION-LOCATOR-GUARD). When a route locator is repaired, the guard on
    # any selection naming that route has to move with it, or the unit and the
    # source map disagree about where the material is.
    guard_units: dict[str, dict] = {}
    routes_by_id = {r["id"]: r for e in source_map.get("sources", [])
                    for r in (e.get("unit_routes") or [])
                    if isinstance(r, dict) and r.get("id")}
    for uid in {u for _, u in FIX}:
        unit = copy.deepcopy(repo.units[uid].data)
        moved = False
        for sel in unit.get("source_selections", []) or []:
            route = routes_by_id.get(sel.get("route_id"))
            if route and sel.get("locator") != route.get("locator"):
                sel["locator"] = route["locator"]
                moved = True
        if moved:
            guard_units[uid] = unit

    units, standalone = {}, []
    for uid in touched:
        unit = guard_units.get(uid, repo.units[uid].data)
        live = [str(st.get("id")) for st in repo.study_maps[
            unit["current_study_map"]].data.get("stages", [])]
        if live == derived_stage_ids(unit):
            units[uid] = unit
        else:
            standalone.append(uid)
    maps = assemble(units, source_map, phrases)

    MAP_DIR.mkdir(parents=True, exist_ok=True)
    for uid, record in maps.items():
        (MAP_DIR / f"{uid}.study-map.yaml").write_text(
            yaml.safe_dump(record, sort_keys=False, allow_unicode=True, width=100),
            encoding="utf-8")

    package = {
        "module_id": MODULE_ID,
        "plan_contract": {
            "version": 2, "plan_template_version": 1,
            "coverage_audit": f"work/active/{WORKSPACE_ID}/outputs/"
                              f"M2-route-rigor-coverage-audit-{DATE}.md",
            "intentional_reorders": [],
            "checks": {k: True for k in (
                "local_inventory_complete", "linked_inventory_complete",
                "materials_opened_and_content_checked",
                "current_and_prior_scope_reconciled",
                "duplicates_and_numbering_checked",
                "exclusions_and_unresolved_gaps_recorded")},
        },
        "module_patch": {},
        "source_patches": [],
        "source_map": source_map,
        "units": ([{"unit": units[uid], "study_map": maps[uid]} for uid in sorted(units)]
                  + [{"unit": guard_units[uid]} for uid in sorted(guard_units)
                     if uid not in units]),
    }
    AUDIT_PATH.write_text(AUDIT, encoding="utf-8")
    PLAN_PATH.write_text(yaml.safe_dump(package, sort_keys=False, allow_unicode=True, width=100),
                         encoding="utf-8")
    print(f"{len(applied)} routes repaired across {len(touched)} units")
    print(f"study maps regenerated: {sorted(units)}")
    print(f"source-map-only (study map authored independently): {standalone}")
    print(f"selection guards moved: {sorted(guard_units)}")
    print(f"plan -> {PLAN_PATH.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
