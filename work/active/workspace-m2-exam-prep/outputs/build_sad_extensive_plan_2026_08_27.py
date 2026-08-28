#!/usr/bin/env python3
"""Build the reviewed SaD all-material lecture-plan artifacts.

This is a workbench generator, not a canonical writer.  It reads the current
module, applies only the evidence-backed source-route corrections documented in
the 2026-08-27 coverage audit, assembles one current-template study map for each
ordinary SaD lecture, and writes review artifacts under the owning workspace.
Canonical curriculum files are deliberately untouched; the generated module
plan must pass ``module-plan-import --check`` and the Gateway before it can be
applied.
"""

from __future__ import annotations

import copy
import hashlib
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import yaml


REPO = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
TOOLS = REPO / "tools"
sys.path.insert(0, str(TOOLS))

from assemble_lecture_study_maps import (  # noqa: E402
    _manifest,
    assembly_problems,
    build,
    concept_phrases,
)
from learning_os.contracts import (  # noqa: E402
    require_current_template,
    validate_contract,
)
from learning_os.genout.materials import _project_material_resource  # noqa: E402
from learning_os.loader import load_repo  # noqa: E402


MODULE_ID = "module-hu-m2-statistik-analysis"
WORKSPACE_ID = "workspace-m2-exam-prep"
DATE = "2026-08-27"
LECTURE_IDS = [f"unit-m2-sad-l{i:02d}" for i in range(1, 16)]
MAP_DIR = OUT / f"SaD-all-material-lecture-maps-L01-L15-{DATE}"
PLAN_PATH = OUT / f"SaD-extensive-all-material-plan-{DATE}.yaml"
AUDIT_PATH = OUT / f"SaD-extensive-source-coverage-audit-{DATE}.md"
OVERVIEW_PATH = OUT / f"SaD-extensive-learning-plan-overview-{DATE}.md"


def load_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected a mapping in {path}")
    return value


def dump_yaml(value: dict) -> str:
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=True, width=100)


def route(
    unit_id: str,
    title: str,
    fmt: str,
    angle: str,
    covers: Iterable[str],
    depth: str,
    scope: str,
    locator: str,
    angle_detail: str,
    *,
    vault_path: str | None = None,
) -> dict:
    value = {
        "unit_id": unit_id,
        "title": title,
        "format": fmt,
        "angle": angle,
        "covers": list(covers),
        "depth": depth,
        "scope": scope,
        "locator": locator,
        "angle_detail": angle_detail,
    }
    if vault_path:
        value["vault_path"] = vault_path
    return value


def exercise_routes() -> list[dict]:
    """Exact current-sheet/tutorial routes, split by real file and topic."""
    base = "material://source-sad-ss26-lectures/exercise-slides/"
    sheet_detail = (
        "This is a current assessed sheet: attempt it before opening the tutorial solution. "
        "It is scope evidence because it shows the chair's own wording, data size and expected "
        "amount of working; it is not a replacement for the lecture derivation."
    )
    tutorial_detail = (
        "This is the current worked tutorial for the named task. Use it after an unaided attempt: "
        "its value is the course's calculation order and notation, while reading it first would "
        "turn an exam-relevant retrieval task into passive recognition."
    )
    rows: list[dict] = []

    def add(uid, title, locator, covers, angle, detail, file_name, *, depth="practice"):
        rows.append(route(
            uid, title, "exercise", angle, covers, depth, "current", locator, detail,
            vault_path=base + file_name,
        ))

    # L01-L02: the same first sheet/tutorial is intentionally routed to the
    # distinct concepts it actually practises.
    add(
        "unit-m2-sad-l01", "Blatt 1, Aufgabe 1 — data summaries in the opening dataset",
        "exercise-slides/Blatt1.pdf, pp. 1-2, Aufgabe 1",
        ["knowledge-sad-l01-data-questions", "knowledge-sad-l01-location", "knowledge-sad-l01-sampling-context"],
        "Turns the introductory dataset into an unaided frequency, location and interpretation task.",
        sheet_detail, "Blatt1.pdf",
    )
    add(
        "unit-m2-sad-l01", "UE2, slides 5-18 — feature and data-type walkthrough",
        "exercise-slides/UE2.pdf, slides 5-18",
        ["knowledge-sad-l01-data-questions", "knowledge-sad-l01-sampling-context"],
        "Shows how the course translates a raw table into features before any model is chosen.",
        tutorial_detail, "UE2.pdf",
    )
    add(
        "unit-m2-sad-l02", "Blatt 1, Aufgabe 1 — frequencies, median, mean and spread",
        "exercise-slides/Blatt1.pdf, pp. 1-2, Aufgabe 1",
        ["knowledge-sad-l02-scales", "knowledge-sad-l02-frequencies", "knowledge-sad-l02-location", "knowledge-sad-l02-dispersion"],
        "A compact by-hand check that the descriptive vocabulary can be turned into numbers.",
        sheet_detail, "Blatt1.pdf",
    )
    add(
        "unit-m2-sad-l02", "UE2, slides 5-18 — feature types and descriptive conventions",
        "exercise-slides/UE2.pdf, slides 5-18",
        ["knowledge-sad-l02-vocabulary", "knowledge-sad-l02-scales", "knowledge-sad-l02-frequencies", "knowledge-sad-l02-sampling"],
        "Supplies the lecturer's worked distinctions between feature types and the summaries allowed for each scale.",
        tutorial_detail, "UE2.pdf",
    )

    # L03: split the formerly bundled route, and add the current sheet and the
    # matching UE3 solutions that were present but invisible.
    add(
        "unit-m2-sad-l03", "Blatt 1, Aufgabe 2 — correlation and simple regression",
        "exercise-slides/Blatt1.pdf, p. 3, Aufgabe 2",
        ["knowledge-sad-l03-paired-data", "knowledge-sad-l03-covariance", "knowledge-sad-l03-interpretation", "knowledge-sad-l03-simple-regression"],
        "Asks for both the coefficient and its interpretation on a real price pair, the closest current exam-style L03 task.",
        sheet_detail, "Blatt1.pdf",
    )
    add(
        "unit-m2-sad-l03", "Blatt 1, Aufgabe 3 — multivariate regression",
        "exercise-slides/Blatt1.pdf, p. 4, Aufgabe 3",
        ["knowledge-sad-l03-multivariate", "knowledge-sad-l03-scaling-weights"],
        "Moves from the scalar line to a real feature matrix and prediction problem.",
        sheet_detail, "Blatt1.pdf",
    )
    add(
        "unit-m2-sad-l03", "UE2, slides 20-28 — covariance and Pearson correlation",
        "exercise-slides/UE2.pdf, slides 20-28",
        ["knowledge-sad-l03-paired-data", "knowledge-sad-l03-covariance", "knowledge-sad-l03-interpretation"],
        "Works the covariance-to-correlation normalization one line at a time in course notation.",
        tutorial_detail, "UE2.pdf",
    )
    add(
        "unit-m2-sad-l03", "UE2, slides 30-35 — regression prediction and RMSE",
        "exercise-slides/UE2.pdf, slides 30-35",
        ["knowledge-sad-l03-simple-regression", "knowledge-sad-l03-multivariate", "knowledge-sad-l03-scaling-weights"],
        "Connects fitted coefficients to predictions and an explicit residual error measure.",
        tutorial_detail, "UE2.pdf",
    )
    add(
        "unit-m2-sad-l03", "UE3, slides 5-14 — Blatt 1 regression solutions",
        "exercise-slides/UE3.pdf, slides 5-14",
        ["knowledge-sad-l03-covariance", "knowledge-sad-l03-interpretation", "knowledge-sad-l03-simple-regression", "knowledge-sad-l03-multivariate"],
        "Provides the official solution path for the two regression questions after the independent attempt.",
        tutorial_detail, "UE3.pdf",
    )
    add(
        "unit-m2-sad-l03", "Blatt 2, Aufgabe 3 — gradient descent and loss curve",
        "exercise-slides/blatt-02.pdf, p. 3, Aufgabe 3(a)-(b)",
        ["knowledge-sad-l03-gradient-descent", "knowledge-sad-l03-scaling-weights"],
        "The only current assignment that makes the optimizer and normalization executable rather than symbolic.",
        sheet_detail, "blatt-02.pdf",
    )
    add(
        "unit-m2-sad-l03", "UE3, slides 40-45 — gradient descent and normalization walkthrough",
        "exercise-slides/UE3.pdf, slides 40-45",
        ["knowledge-sad-l03-gradient-descent", "knowledge-sad-l03-scaling-weights"],
        "Explains why scaling changes the descent geometry and how the MSE curve diagnoses the update.",
        tutorial_detail, "UE3.pdf",
    )

    # Probability and counting.
    add(
        "unit-m2-sad-l04", "Blatt 2, Aufgaben 1-2 — probability, Bayes and Naive Bayes",
        "exercise-slides/blatt-02.pdf, pp. 1-2, Aufgaben 1-2",
        ["knowledge-sad-l04-events", "knowledge-sad-l04-axioms", "knowledge-sad-l04-conditional", "knowledge-sad-l04-bayes", "knowledge-sad-l04-independence", "knowledge-sad-l04-naive-bayes"],
        "Combines finite probability, dependence, Bayes inversion and a small classifier in the current assignment format.",
        sheet_detail, "blatt-02.pdf",
    )
    add(
        "unit-m2-sad-l04", "UE3, slides 15-38 — events, axioms and conditional probability",
        "exercise-slides/UE3.pdf, slides 15-38",
        ["knowledge-sad-l04-events", "knowledge-sad-l04-axioms", "knowledge-sad-l04-conditional", "knowledge-sad-l04-bayes", "knowledge-sad-l04-independence"],
        "Builds the event algebra and then works the medical-test style base-rate inversion visually.",
        tutorial_detail, "UE3.pdf",
    )
    add(
        "unit-m2-sad-l04", "UE4, slides 9-12 — Bayes and Naive Bayes solutions",
        "exercise-slides/UE4.pdf, slides 9-12",
        ["knowledge-sad-l04-conditional", "knowledge-sad-l04-bayes", "knowledge-sad-l04-naive-bayes"],
        "Shows exactly where the conditional-independence assumption enters the two-feature classifier.",
        tutorial_detail, "UE4.pdf",
    )
    add(
        "unit-m2-sad-l05", "Blatt 2, Aufgabe 1 — counting inside finite probability",
        "exercise-slides/blatt-02.pdf, p. 1, Aufgabe 1(a)-(e)",
        ["knowledge-sad-l05-decision-grid", "knowledge-sad-l05-variations", "knowledge-sad-l05-combinations", "knowledge-sad-l05-counting-probability"],
        "Hides the counting case inside cards, repeated dice and dependent portfolio events, which tests identification rather than formula recall.",
        sheet_detail, "blatt-02.pdf",
    )
    add(
        "unit-m2-sad-l05", "UE4, slides 4-8 — worked finite-counting solutions",
        "exercise-slides/UE4.pdf, slides 4-8",
        ["knowledge-sad-l05-decision-grid", "knowledge-sad-l05-variations", "knowledge-sad-l05-combinations", "knowledge-sad-l05-counting-probability"],
        "Makes the numerator/denominator counting decisions explicit for the current sheet's disguised cases.",
        tutorial_detail, "UE4.pdf",
    )

    # Random variables, distributions, Normal/CLT and estimation.
    add(
        "unit-m2-sad-l06", "Übungsblatt 3, Aufgabe 1 — PMF, transformation, expectation and variance",
        "exercise-slides/Übung-3.pdf, p. 1, Aufgabe 1(a)-(c)",
        ["knowledge-sad-l06-distribution-functions", "knowledge-sad-l06-transformations", "knowledge-sad-l06-expectation", "knowledge-sad-l06-variance-covariance"],
        "Compresses the four core random-variable operations into one exact current assignment.",
        sheet_detail, "Übung-3.pdf",
    )
    add(
        "unit-m2-sad-l06", "Übungsblatt 3, Aufgabe 3 — mixture moments and the LLN",
        "exercise-slides/Übung-3.pdf, p. 3, Aufgabe 3(a)-(d)",
        ["knowledge-sad-l06-expectation", "knowledge-sad-l06-variance-covariance", "knowledge-sad-l06-sample-mean", "knowledge-sad-l06-concentration"],
        "Turns expectation and the law of large numbers into a cumulative-mean simulation with a distribution change.",
        sheet_detail + " It assumes basic Python/pandas and is therefore a worked application, not the first explanation.", "Übung-3.pdf",
    )
    add(
        "unit-m2-sad-l06", "UE4, slides 18-34 — random variables, moments and LLN",
        "exercise-slides/UE4.pdf, slides 18-34",
        ["knowledge-sad-l06-random-variable", "knowledge-sad-l06-distribution-functions", "knowledge-sad-l06-transformations", "knowledge-sad-l06-expectation", "knowledge-sad-l06-variance-covariance", "knowledge-sad-l06-sample-mean", "knowledge-sad-l06-concentration"],
        "Uses one discrete and one mixed random variable to connect the definitions to empirical convergence.",
        tutorial_detail, "UE4.pdf",
    )
    add(
        "unit-m2-sad-l06", "UE5, slides 4-17 — official Blatt 3 solutions",
        "exercise-slides/UE5.pdf, slides 4-17",
        ["knowledge-sad-l06-distribution-functions", "knowledge-sad-l06-transformations", "knowledge-sad-l06-expectation", "knowledge-sad-l06-variance-covariance", "knowledge-sad-l06-concentration"],
        "Provides the complete official solution and implementation trace for Blatt 3 after it has been attempted.",
        tutorial_detail, "UE5.pdf",
    )
    add(
        "unit-m2-sad-l07", "Übungsblatt 3, Aufgabe 2 — identify four discrete distributions",
        "exercise-slides/Übung-3.pdf, p. 2, Aufgabe 2(a)-(d)",
        ["knowledge-sad-l07-model-selection", "knowledge-sad-l07-bernoulli-binomial", "knowledge-sad-l07-hypergeometric", "knowledge-sad-l07-geometric", "knowledge-sad-l07-poisson"],
        "Forces model selection from prose before any formula can be substituted.",
        sheet_detail, "Übung-3.pdf",
    )
    add(
        "unit-m2-sad-l07", "UE4, slides 36-49 — distribution conditions and worked cases",
        "exercise-slides/UE4.pdf, slides 36-49",
        ["knowledge-sad-l07-model-selection", "knowledge-sad-l07-bernoulli-binomial", "knowledge-sad-l07-hypergeometric", "knowledge-sad-l07-geometric", "knowledge-sad-l07-poisson", "knowledge-sad-l07-relationships"],
        "Puts the identifying conditions for Binomial, Hypergeometric, Geometric and Poisson side by side.",
        tutorial_detail, "UE4.pdf",
    )
    add(
        "unit-m2-sad-l07", "UE5, slides 8-11 — official discrete-distribution solutions",
        "exercise-slides/UE5.pdf, slides 8-11",
        ["knowledge-sad-l07-model-selection", "knowledge-sad-l07-bernoulli-binomial", "knowledge-sad-l07-hypergeometric", "knowledge-sad-l07-poisson", "knowledge-sad-l07-relationships"],
        "Checks the model-choice reasoning against the current sheet's official solution.",
        tutorial_detail, "UE5.pdf",
    )
    add(
        "unit-m2-sad-l08", "Blatt 4, Aufgaben 1 and 3 — Normal calculations and CLT simulation",
        "exercise-slides/Statistics_And_Data_Science.pdf, pp. 1 and 3, Aufgaben 1 and 3",
        ["knowledge-sad-l08-normal", "knowledge-sad-l08-standardization", "knowledge-sad-l08-transform-sum", "knowledge-sad-l08-clt", "knowledge-sad-l08-approximation"],
        "Pairs table-based Normal calculations with a simulation that reveals when the CLT approximation works.",
        sheet_detail + " The file's printed sheet number is absent; content identifies it as the current Blatt 4, and that naming uncertainty remains recorded.", "Statistics_And_Data_Science.pdf",
    )
    add(
        "unit-m2-sad-l08", "UE5, slides 20-38 — Normal, standardization and CLT walkthrough",
        "exercise-slides/UE5.pdf, slides 20-38",
        ["knowledge-sad-l08-normal", "knowledge-sad-l08-standardization", "knowledge-sad-l08-transform-sum", "knowledge-sad-l08-clt", "knowledge-sad-l08-approximation"],
        "Gives a visual, calculation-first bridge from z-scores to sample-mean normality.",
        tutorial_detail, "UE5.pdf",
    )
    add(
        "unit-m2-sad-l08", "UE6, slides 5-20 — official Blatt 4 Normal/CLT solutions",
        "exercise-slides/UE6.pdf, slides 5-20",
        ["knowledge-sad-l08-normal", "knowledge-sad-l08-standardization", "knowledge-sad-l08-clt", "knowledge-sad-l08-approximation"],
        "Supplies the current official numerical solutions and the code shape for the CLT experiment.",
        tutorial_detail, "UE6.pdf",
    )
    add(
        "unit-m2-sad-l09", "Blatt 4, Aufgabe 2 — point estimate, bootstrap and interval",
        "exercise-slides/Statistics_And_Data_Science.pdf, p. 2, Aufgabe 2",
        ["knowledge-sad-l09-estimator", "knowledge-sad-l09-properties", "knowledge-sad-l09-standard-error", "knowledge-sad-l09-z-interval", "knowledge-sad-l09-bootstrap"],
        "Makes the estimator/standard-error/interval chain concrete in one data-analysis task.",
        sheet_detail + " The generic filename is retained because the PDF itself has no recoverable sheet number.", "Statistics_And_Data_Science.pdf",
    )
    add(
        "unit-m2-sad-l09", "UE5, slides 40-77 — estimation, standard error and bootstrap intervals",
        "exercise-slides/UE5.pdf, slides 40-77",
        ["knowledge-sad-l09-estimator", "knowledge-sad-l09-properties", "knowledge-sad-l09-standard-error", "knowledge-sad-l09-z-interval", "knowledge-sad-l09-t-interval", "knowledge-sad-l09-bootstrap"],
        "Shows the whole inferential chain with one repeated dataset, including what the bootstrap is estimating.",
        tutorial_detail, "UE5.pdf",
    )
    add(
        "unit-m2-sad-l09", "UE6, slides 10-13 — official bootstrap confidence-interval solution",
        "exercise-slides/UE6.pdf, slides 10-13",
        ["knowledge-sad-l09-standard-error", "knowledge-sad-l09-z-interval", "knowledge-sad-l09-bootstrap"],
        "Provides the official short-form answer expected for the current interval question.",
        tutorial_detail, "UE6.pdf",
    )

    # Testing and the machine-learning half.
    add(
        "unit-m2-sad-l10", "Blatt 5, Aufgabe 1 — permutation test and t-test comparison",
        "exercise-slides/blatt-05.pdf, pp. 1-2, Aufgabe 1(a)-(d)",
        ["knowledge-sad-l10-test-model", "knowledge-sad-l10-tails-pvalue", "knowledge-sad-l10-errors-power", "knowledge-sad-l10-z-t", "knowledge-sad-l10-nonparametric"],
        "Makes the null/alternative, p-value decision and parametric/nonparametric comparison one coherent task.",
        sheet_detail, "blatt-05.pdf",
    )
    add(
        "unit-m2-sad-l10", "UE6, slides 23-38 — permutation and two-sample t tests",
        "exercise-slides/UE6.pdf, slides 23-38",
        ["knowledge-sad-l10-test-model", "knowledge-sad-l10-tails-pvalue", "knowledge-sad-l10-errors-power", "knowledge-sad-l10-z-t", "knowledge-sad-l10-nonparametric"],
        "Presents both procedures on matched questions, exposing which assumptions change and which decision logic does not.",
        tutorial_detail, "UE6.pdf",
    )
    add(
        "unit-m2-sad-l10", "UE7, slides 12-16 — official Blatt 5 testing solution",
        "exercise-slides/UE7.pdf, slides 12-16",
        ["knowledge-sad-l10-test-model", "knowledge-sad-l10-tails-pvalue", "knowledge-sad-l10-z-t", "knowledge-sad-l10-nonparametric"],
        "Shows the complete answer structure the current course accepts for a test decision.",
        tutorial_detail, "UE7.pdf",
    )
    add(
        "unit-m2-sad-l11", "Blatt 5, Aufgabe 3 — multiclass evaluation metrics",
        "exercise-slides/blatt-05.pdf, p. 4, Aufgabe 3(a)-(d)",
        ["knowledge-sad-l11-evaluation"],
        "Requires per-class confusion matrices plus micro/macro aggregation, the most calculation-heavy part of L11.",
        sheet_detail, "blatt-05.pdf",
    )
    add(
        "unit-m2-sad-l11", "UE6, slides 70-82 — classifier evaluation walkthrough",
        "exercise-slides/UE6.pdf, slides 70-82",
        ["knowledge-sad-l11-evaluation"],
        "Builds accuracy, precision, recall and F1 from the confusion matrix rather than presenting isolated formulas.",
        tutorial_detail, "UE6.pdf",
    )
    add(
        "unit-m2-sad-l11", "UE7, slides 22-30 — official multiclass-metrics solution",
        "exercise-slides/UE7.pdf, slides 22-30",
        ["knowledge-sad-l11-evaluation"],
        "Shows how the current course reports per-class and aggregate metrics when class priorities differ.",
        tutorial_detail, "UE7.pdf",
    )
    # L12 deliberately has no current sheet route: this is a real practice gap.
    add(
        "unit-m2-sad-l13", "UE7, slides 32-75 — similarity, distance and clustering bridge",
        "exercise-slides/UE7.pdf, slides 32-75",
        ["knowledge-sad-l13-metrics", "knowledge-sad-l13-minkowski", "knowledge-sad-l13-special-measures"],
        "Uses distance calculations inside k-means, making metric choice operational even though it is not a k-NN sheet.",
        tutorial_detail + " It does not practise kd-trees, M-trees or LSH, so those remain an explicit L13 gap.", "UE7.pdf",
    )
    add(
        "unit-m2-sad-l14", "UE4, slides 9-12 — categorical Naive Bayes worked example",
        "exercise-slides/UE4.pdf, slides 9-12",
        ["knowledge-sad-l14-nb-recap", "knowledge-sad-l14-smoothing"],
        "Rebuilds the two-feature categorical classifier and exposes the conditional-independence assumption before L14 extends it.",
        tutorial_detail + " It is a recap bridge: it does not cover Gaussian/count likelihoods or Bayesian networks.", "UE4.pdf",
    )
    add(
        "unit-m2-sad-l15", "Blatt 5, Aufgabe 2 — forward pass, softmax and cross-entropy",
        "exercise-slides/blatt-05.pdf, p. 3, Aufgabe 2(a)-(d)",
        ["knowledge-sad-l15-neuron", "knowledge-sad-l15-output", "knowledge-sad-l15-forward", "knowledge-sad-l15-training"],
        "The current by-hand neural-network task: matrix multiply, normalize outputs, calculate loss and interpret the decision rule.",
        sheet_detail, "blatt-05.pdf",
    )
    add(
        "unit-m2-sad-l15", "UE6, slides 39-68 — neurons, forward pass, softmax and loss",
        "exercise-slides/UE6.pdf, slides 39-68",
        ["knowledge-sad-l15-neuron", "knowledge-sad-l15-activation", "knowledge-sad-l15-output", "knowledge-sad-l15-forward", "knowledge-sad-l15-training"],
        "Works the network as explicit matrices before discussing training, preventing the architecture from becoming a black box.",
        tutorial_detail, "UE6.pdf",
    )
    add(
        "unit-m2-sad-l15", "UE7, slides 17-21 — official neural-network solution",
        "exercise-slides/UE7.pdf, slides 17-21",
        ["knowledge-sad-l15-output", "knowledge-sad-l15-forward", "knowledge-sad-l15-training"],
        "Provides the exact current solution for the forward/softmax/cross-entropy assignment.",
        tutorial_detail, "UE7.pdf",
    )
    return rows


def prior_year_routes(existing: list[dict]) -> list[dict]:
    rows = [copy.deepcopy(row) for row in existing if row.get("unit_id") not in LECTURE_IDS]
    fixed = []
    for row in existing:
        uid = row.get("unit_id")
        if uid not in LECTURE_IDS or uid == "unit-m2-sad-l15":
            continue
        value = copy.deepcopy(row)
        locator = str(value.get("locator") or "")
        value["locator"] = re.sub(r"^sad-2025-recordings/", "", locator)
        fixed.append(value)
    rows.extend(fixed)
    rows.extend([
        route(
            "unit-m2-sad-l15", "2025 neural networks Part 1 — affine models, outputs and SGD",
            "course-material",
            "Spends a full session on the one-layer network, softmax outputs and gradient-descent setup that 2026 compresses.",
            ["knowledge-sad-l15-neuron", "knowledge-sad-l15-output", "knowledge-sad-l15-forward", "knowledge-sad-l15-training"],
            "advanced-reference", "prior-year", "14_neural_nets_part1.pdf, slides 8-89",
            "Part 1 is the slower course-level bridge from affine transformations to a trainable classifier. It is especially useful when matrix shapes or the distinction between logits and probabilities is the problem. It predates the current deck, so it elaborates but never defines 2026 scope.",
            vault_path="material://source-sad-2025-recordings/14_neural_nets_part1.pdf",
        ),
        route(
            "unit-m2-sad-l15", "2025 neural networks Part 2 — loss landscape, gradients and depth",
            "course-material",
            "Provides the course's most detailed treatment of cross-entropy, gradient computation, nonlinear depth and XOR.",
            ["knowledge-sad-l15-activation", "knowledge-sad-l15-output", "knowledge-sad-l15-forward", "knowledge-sad-l15-backprop", "knowledge-sad-l15-training", "knowledge-sad-l15-universality", "knowledge-sad-l15-outlook"],
            "advanced-reference", "prior-year", "15_neural_nets_part2.pdf, slides 2-223",
            "Part 2 follows one loss landscape through partial derivatives and weight updates before showing why hidden nonlinearities solve problems a one-layer classifier cannot. It is much longer than the current lecture: use only the section matching a recorded gap, and check terminology against the 2026 deck.",
            vault_path="material://source-sad-2025-recordings/15_neural_nets_part2.pdf",
        ),
    ])
    return rows


def external_exam_routes(existing: list[dict]) -> list[dict]:
    """Replace collection-wide guesses with verified file/page/task routes."""
    rows = [copy.deepcopy(row) for row in existing if row.get("unit_id") not in LECTURE_IDS]
    base = "material://source-sad-klausuren-extern/"
    rows.extend([
        route(
            "unit-m2-sad-l02", "HS Harz pp. 2-5 — descriptive statistics under exam timing",
            "exercise", "A short German paper with boxplot, mean, median and dispersion computations plus worked answers.",
            ["knowledge-sad-l02-frequencies", "knowledge-sad-l02-location", "knowledge-sad-l02-dispersion"],
            "practice", "complementary",
            "HS-Harz_Statistik-I_Probeklausur_mit-Loesungen.pdf, pp. 2-5, Aufgabenteile I-III",
            "The four-page descriptive block is mechanically close to L02 and small enough to time. Its value is answer economy and German exam phrasing; it does not cover sampling design or Simpson's paradox.",
            vault_path=base + "HS-Harz_Statistik-I_Probeklausur_mit-Loesungen.pdf",
        ),
        route(
            "unit-m2-sad-l03", "HS Harz pp. 6-7 — Kendall association and linear regression",
            "exercise", "Pairs an association measure with a fitted line and R² interpretation on one dataset.",
            ["knowledge-sad-l03-paired-data", "knowledge-sad-l03-interpretation", "knowledge-sad-l03-simple-regression"],
            "practice", "complementary",
            "HS-Harz_Statistik-I_Probeklausur_mit-Loesungen.pdf, pp. 6-7, Aufgabenteile IV-V",
            "This is the strongest external L03 item because the prompt, computation and interpretation are visible together and the solution is printed immediately below. Kendall's tau itself is outside the current lecture; use that part only as an association contrast, then work the linear-regression section in full.",
            vault_path=base + "HS-Harz_Statistik-I_Probeklausur_mit-Loesungen.pdf",
        ),
        route(
            "unit-m2-sad-l03", "University of Cologne pp. 7-8 — multivariate regression interpretation",
            "solutions", "Shows coefficient interpretation, prediction and an interaction extension in a real multivariate model.",
            ["knowledge-sad-l03-multivariate", "knowledge-sad-l03-scaling-weights"],
            "advanced-reference", "complementary",
            "Koeln_Statistik-Klausur_Musterloesung.pdf, pp. 7-8, Aufgabe 5(c)-(d)",
            "Parts (c)-(d) are useful L03 transfer: substitute a feature vector, compare a dummy coefficient and propose an interaction term. Parts (a)-(b) use t tests and confidence intervals, which require L10; they are deliberately excluded from the L03 task.",
            vault_path=base + "Koeln_Statistik-Klausur_Musterloesung.pdf",
        ),
        route(
            "unit-m2-sad-l04", "Leuphana-Merz pp. 5-10 — probability and conditional-probability drills",
            "exercise", "A dense German exercise block for finite probability, conditioning and Bayes before the later inference chapters.",
            ["knowledge-sad-l04-events", "knowledge-sad-l04-axioms", "knowledge-sad-l04-conditional", "knowledge-sad-l04-bayes", "knowledge-sad-l04-independence"],
            "practice", "complementary",
            "Leuphana-Merz_Statistik-2_Uebungsbuch-mit-Klausur.pdf, pp. 5-10, Aufgabenblatt 1",
            "The block supplies more authentic German stems than the course sheet while remaining at the same foundational level. Select only the event/conditioning items; later pages in this 109-page book belong to estimation and testing and are routed separately.",
            vault_path=base + "Leuphana-Merz_Statistik-2_Uebungsbuch-mit-Klausur.pdf",
        ),
        route(
            "unit-m2-sad-l05", "Leuphana-Merz pp. 5-10 — combinatorial probability items",
            "exercise", "Uses counting as the hidden first step of a probability problem rather than naming the formula.",
            ["knowledge-sad-l05-decision-grid", "knowledge-sad-l05-combinations", "knowledge-sad-l05-counting-probability"],
            "practice", "complementary",
            "Leuphana-Merz_Statistik-2_Uebungsbuch-mit-Klausur.pdf, pp. 5-10, Aufgabenblatt 1 counting items",
            "This is identification practice: decide the finite sample space and the relevant count before computing a probability. It does not replace the lecture's complete order/replacement decision grid, so use it only after that grid can be reproduced.",
            vault_path=base + "Leuphana-Merz_Statistik-2_Uebungsbuch-mit-Klausur.pdf",
        ),
        route(
            "unit-m2-sad-l06", "Leuphana-Merz pp. 5-10 — random-variable and moment items",
            "exercise", "Adds short expectation and variance calculations in German exam notation.",
            ["knowledge-sad-l06-distribution-functions", "knowledge-sad-l06-expectation", "knowledge-sad-l06-variance-covariance"],
            "practice", "complementary",
            "Leuphana-Merz_Statistik-2_Uebungsbuch-mit-Klausur.pdf, pp. 5-10, Aufgabenblatt 1 random-variable items",
            "Use these for speed only after PMF/CDF and moment definitions are stable. The book's theoretical framing is broader than L06, so the locator intentionally limits the route to the first exercise block.",
            vault_path=base + "Leuphana-Merz_Statistik-2_Uebungsbuch-mit-Klausur.pdf",
        ),
        route(
            "unit-m2-sad-l06", "Regensburg-Löh pp. 2-5 — rigorous probability-space reference",
            "exam", "Shows the measure-theoretic formulation behind random variables and convergence, far beyond the course's computational level.",
            ["knowledge-sad-l06-random-variable", "knowledge-sad-l06-distribution-functions", "knowledge-sad-l06-concentration"],
            "advanced-reference", "optional",
            "Regensburg-Loeh_WTheorie-Statistik_Klausur_mit-Loesungen.pdf, pp. 2-5, Aufgaben 1-2",
            "This is not normal L06 practice: sigma-algebras and proof questions assume a rigorous probability course. It is retained so the owned file is visible and can answer a formal-definition question, but it should never displace Fahrmeir, Blitzstein or the current exercises.",
            vault_path=base + "Regensburg-Loeh_WTheorie-Statistik_Klausur_mit-Loesungen.pdf",
        ),
        route(
            "unit-m2-sad-l07", "Leuphana-Merz pp. 11-16 — discrete distribution selection",
            "exercise", "A mixed block where Binomial, Hypergeometric and Poisson models must be identified from context.",
            ["knowledge-sad-l07-model-selection", "knowledge-sad-l07-bernoulli-binomial", "knowledge-sad-l07-hypergeometric", "knowledge-sad-l07-geometric", "knowledge-sad-l07-poisson", "knowledge-sad-l07-relationships"],
            "practice", "complementary",
            "Leuphana-Merz_Statistik-2_Uebungsbuch-mit-Klausur.pdf, pp. 11-16, Aufgabenblatt 2",
            "Unlike a chapter-end single-distribution drill, this block mixes families and therefore tests the L07 decision step. Check each parameterization against the 2026 deck because notation varies across German courses.",
            vault_path=base + "Leuphana-Merz_Statistik-2_Uebungsbuch-mit-Klausur.pdf",
        ),
        route(
            "unit-m2-sad-l08", "Leuphana-Merz pp. 11-16 — Normal and sampling-distribution items",
            "exercise", "Connects standardized Normal calculations to sums and sample statistics in a compact solved block.",
            ["knowledge-sad-l08-normal", "knowledge-sad-l08-standardization", "knowledge-sad-l08-transform-sum", "knowledge-sad-l08-clt", "knowledge-sad-l08-approximation"],
            "practice", "complementary",
            "Leuphana-Merz_Statistik-2_Uebungsbuch-mit-Klausur.pdf, pp. 11-16, Aufgabenblatt 2 Normal/CLT items",
            "The benefit is transfer between distribution recognition and calculation. It is not the source for L08 likelihood or MLE; those nodes remain with the deck, MIT 18.650 and the dedicated derivation sources.",
            vault_path=base + "Leuphana-Merz_Statistik-2_Uebungsbuch-mit-Klausur.pdf",
        ),
        route(
            "unit-m2-sad-l08", "Regensburg-Löh pp. 6-8 — LLN/CLT proof reference",
            "exam", "Provides a rigorous statement-and-proof view of convergence laws that the course uses computationally.",
            ["knowledge-sad-l08-clt", "knowledge-sad-l08-approximation"],
            "advanced-reference", "optional",
            "Regensburg-Loeh_WTheorie-Statistik_Klausur_mit-Loesungen.pdf, pp. 6-8, convergence tasks",
            "This route is deliberately reference-only. It can clarify assumptions and modes of convergence, but its proof burden is outside the SaD exam and would be harmful as ordinary preparation.",
            vault_path=base + "Regensburg-Loeh_WTheorie-Statistik_Klausur_mit-Loesungen.pdf",
        ),
        route(
            "unit-m2-sad-l09", "Leuphana-Merz pp. 17-27 — estimation and confidence intervals",
            "exercise", "A full progression from sample functions and point estimates to mean, variance and proportion intervals.",
            ["knowledge-sad-l09-estimator", "knowledge-sad-l09-properties", "knowledge-sad-l09-standard-error", "knowledge-sad-l09-z-interval", "knowledge-sad-l09-t-interval"],
            "practice", "complementary",
            "Leuphana-Merz_Statistik-2_Uebungsbuch-mit-Klausur.pdf, pp. 17-27, Aufgabenblätter 3-4",
            "Page 23 begins Aufgabenblatt 4 on interval estimation and visibly distinguishes known-sigma, estimated-sigma and proportion regimes. This is the strongest local external practice for selecting the correct interval, but it does not cover the bootstrap.",
            vault_path=base + "Leuphana-Merz_Statistik-2_Uebungsbuch-mit-Klausur.pdf",
        ),
        route(
            "unit-m2-sad-l10", "Leuphana-Merz pp. 28-40 — parametric, two-sample and goodness-of-fit tests",
            "exercise", "Supplies full German test write-ups across several test families, with solutions.",
            ["knowledge-sad-l10-test-model", "knowledge-sad-l10-tails-pvalue", "knowledge-sad-l10-errors-power", "knowledge-sad-l10-z-t", "knowledge-sad-l10-ci-duality", "knowledge-sad-l10-chi-square", "knowledge-sad-l10-nonparametric"],
            "practice", "complementary",
            "Leuphana-Merz_Statistik-2_Uebungsbuch-mit-Klausur.pdf, pp. 28-40, Aufgabenblätter 5-6",
            "This is the widest local testing bank: one- and two-sample tests plus goodness-of-fit/chi-square work. Use the problems to practise test selection and complete written decisions; skip procedures not named in the 2026 L10 deck.",
            vault_path=base + "Leuphana-Merz_Statistik-2_Uebungsbuch-mit-Klausur.pdf",
        ),
        route(
            "unit-m2-sad-l10", "University of Cologne pp. 7-8 — coefficient t-test and confidence interval",
            "solutions", "Shows how inference is written around a fitted multivariate regression coefficient.",
            ["knowledge-sad-l10-test-model", "knowledge-sad-l10-tails-pvalue", "knowledge-sad-l10-z-t", "knowledge-sad-l10-ci-duality"],
            "practice", "complementary",
            "Koeln_Statistik-Klausur_Musterloesung.pdf, pp. 7-8, Aufgabe 5(a)-(b)",
            "The same model routed to L03 becomes an L10 inference task here: formulate H0, calculate a t statistic and construct a confidence interval. It is a good bridge between regression interpretation and test mechanics, but regression-slope inference is an extension beyond the core L03 scope.",
            vault_path=base + "Koeln_Statistik-Klausur_Musterloesung.pdf",
        ),
    ])
    return rows


def fau_routes(existing: list[dict]) -> list[dict]:
    """Keep only verified lecture placements and correct the L03 claim."""
    rows = [copy.deepcopy(row) for row in existing if row.get("unit_id") not in LECTURE_IDS]
    file_uri = (
        "material://source-fau-klausur-ws1415/"
        "FAU-Erlangen_Statistik-Klausur_WS14-15_mit-Loesungen.pdf"
    )
    rows.extend([
        route(
            "unit-m2-sad-l01", "FAU pp. 4 and 22 — origin/base-rate table with solution",
            "exercise", "An authentic German base-rate item showing the amount of working that receives marks.",
            ["knowledge-sad-l01-classification", "knowledge-sad-l01-base-rates"],
            "practice", "complementary",
            "FAU-Erlangen_Statistik-Klausur_WS14-15_mit-Loesungen.pdf, p. 4 Aufgabe 1(3)-(4), solution p. 22",
            "The orange-origin table asks for posterior/origin reasoning in the form that makes sensitivity-versus-posterior mistakes visible. It is a calibration item after L01, not a new explanation of Bayes.",
            vault_path=file_uri,
        ),
        route(
            "unit-m2-sad-l02", "FAU pp. 3 and 22 — descriptive-statistics block with solution",
            "exercise", "Shows exactly how briefly median, quartiles, range, mean and skewness are reported in a real German solution.",
            ["knowledge-sad-l02-frequencies", "knowledge-sad-l02-location", "knowledge-sad-l02-dispersion"],
            "practice", "complementary",
            "FAU-Erlangen_Statistik-Klausur_WS14-15_mit-Loesungen.pdf, p. 3 Aufgabe 1(1), solution p. 22",
            "This is useful for timing and answer economy rather than conceptual depth. Work the orange table cold, then compare only the form and amount of the published answer.",
            vault_path=file_uri,
        ),
        route(
            "unit-m2-sad-l03", "FAU pp. 35 and 48 — covariance/correlation formula completion",
            "exercise", "A very short R-formula completion that checks whether covariance is normalized by both variances correctly.",
            ["knowledge-sad-l03-covariance"],
            "practice", "complementary",
            "FAU-Erlangen_Statistik-Klausur_WS14-15_mit-Loesungen.pdf, p. 35 Aufgabe 2(8), solution p. 48",
            "The former route incorrectly promised a solved compute-and-interpret correlation item. The actual task is narrower: complete Kor=function(Kova,v1,v2). It is retained honestly as formula recall; it does not practise scatterplot interpretation or a regression fit.",
            vault_path=file_uri,
        ),
        route(
            "unit-m2-sad-l04", "FAU pp. 4 and 22 — total probability, Bayes and independence",
            "exercise", "Tests conditional probability as a table calculation rather than a definition recital.",
            ["knowledge-sad-l04-conditional", "knowledge-sad-l04-bayes", "knowledge-sad-l04-independence"],
            "practice", "complementary",
            "FAU-Erlangen_Statistik-Klausur_WS14-15_mit-Loesungen.pdf, p. 4 Aufgabe 1(3)-(4), solution p. 22",
            "The same orange-origin item is routed here for its formal Bayes and independence steps. It confirms the German notation and the compact published answer after the course sheet has established the method.",
            vault_path=file_uri,
        ),
        route(
            "unit-m2-sad-l07", "FAU pp. 5 and 22 — Binomial model and quantile",
            "exercise", "Requires both a point probability and a cumulative/quantile decision for a named Binomial variable.",
            ["knowledge-sad-l07-model-selection", "knowledge-sad-l07-bernoulli-binomial", "knowledge-sad-l07-relationships"],
            "practice", "complementary",
            "FAU-Erlangen_Statistik-Klausur_WS14-15_mit-Loesungen.pdf, p. 5 Aufgabe 1(5), solution p. 22",
            "The distribution is named, so this is calculation and quantile practice rather than model identification. It is best used after mixed-distribution tasks, as a speed check.",
            vault_path=file_uri,
        ),
        route(
            "unit-m2-sad-l10", "FAU pp. 20/45 and 25/50 — one-sided correlation test",
            "exercise", "A real test of whether a population correlation exceeds 0.8, including hypotheses, statistic and decision.",
            ["knowledge-sad-l10-test-model", "knowledge-sad-l10-tails-pvalue", "knowledge-sad-l10-errors-power", "knowledge-sad-l10-z-t"],
            "practice", "complementary",
            "FAU-Erlangen_Statistik-Klausur_WS14-15_mit-Loesungen.pdf, p. 20 Aufgabe 4(8), repeated p. 45; solutions pp. 25 and 50",
            "This item was previously misused as L03 support, but bivariate-normal assumptions and a correlation hypothesis test make it L10 work. Use it to practise a complete one-sided decision; the specialized correlation-test formula may be beyond the exact 2026 formula sheet.",
            vault_path=file_uri,
        ),
    ])
    return rows


def material_files_for_source(repo, source_id: str) -> list[tuple[str, Path]]:
    source = repo.sources[source_id]
    material = source.get("material")
    if not isinstance(material, str) or not material.startswith("material://"):
        return []
    target = repo.materials_root / material.removeprefix("material://")
    if target.is_file():
        return [(material, target.resolve())]
    if not target.is_dir():
        return []
    values = []
    for path in sorted(target.rglob("*")):
        if not path.is_file() or path.name in {".DS_Store", "SOURCES.md", "README.md", "FILES.txt", "INDEX.html"}:
            continue
        rel = path.relative_to(target)
        values.append((material.rstrip("/") + "/" + rel.as_posix(), path.resolve()))
    return values


def add_single_file_targets(source_map: dict, repo) -> None:
    """Make local one-file books openable without weakening page locators."""
    for entry in source_map.get("sources", []):
        sid = entry.get("source_id")
        if sid not in repo.sources:
            continue
        files = [row for row in material_files_for_source(repo, sid)
                 if row[1].suffix.lower() in {".pdf", ".md", ".ipynb", ".ppt", ".pptx"}]
        if len(files) != 1:
            continue
        uri, _path = files[0]
        for item in entry.get("unit_routes", []) or []:
            if isinstance(item, dict) and item.get("unit_id") in LECTURE_IDS:
                item.setdefault("vault_path", uri)


def patched_source_map(repo) -> dict:
    path = REPO / "curriculum/modules" / MODULE_ID / "source-map.yaml"
    source_map = load_yaml(path)
    for entry in source_map["sources"]:
        sid = entry.get("source_id")
        existing = entry.get("unit_routes", []) or []
        if sid == "source-sad-uebungen":
            kept = [copy.deepcopy(row) for row in existing if row.get("unit_id") not in LECTURE_IDS]
            entry["unit_routes"] = [*exercise_routes(), *kept]
        elif sid == "source-sad-2025-recordings":
            entry["unit_routes"] = prior_year_routes(existing)
        elif sid == "source-sad-klausuren-extern":
            entry["unit_routes"] = external_exam_routes(existing)
        elif sid == "source-fau-klausur-ws1415":
            entry["unit_routes"] = fau_routes(existing)
    add_single_file_targets(source_map, repo)
    return source_map


def lecture_routes(source_map: dict) -> dict[str, list[dict]]:
    result = {uid: [] for uid in LECTURE_IDS}
    for entry in source_map.get("sources", []):
        for raw in entry.get("unit_routes", []) or []:
            if not isinstance(raw, dict) or raw.get("unit_id") not in result:
                continue
            value = copy.deepcopy(raw)
            value["source_id"] = entry["source_id"]
            value["source_role"] = entry.get("role")
            value["source_why"] = entry.get("why")
            value["source_priority"] = entry.get("priority")
            result[raw["unit_id"]].append(value)
    return result


def assemble_maps(repo, source_map: dict) -> dict[str, dict]:
    manifest = _manifest(REPO)
    phrases = concept_phrases(manifest["records"])
    routes = lecture_routes(source_map)
    maps: dict[str, dict] = {}
    problems: list[str] = []
    for uid in LECTURE_IDS:
        unit = repo.units[uid].data
        projected = []
        for raw in routes[uid]:
            value = _project_material_resource(repo, raw)
            # The study-map assembler names this field ``material_uri`` and
            # writes it as the learner-facing ``vault_path``.
            if raw.get("vault_path") and not value.get("material_uri"):
                value["material_uri"] = raw["vault_path"]
            projected.append(value)
        record = build(unit, MODULE_ID, projected, phrases, True)
        problems.extend(assembly_problems(unit, projected, record))
        require_current_template(record, "curriculum")
        validate_contract(REPO, "study-map.schema.json", record,
                          label=f"assembled study map for {uid}")
        maps[uid] = record
    if problems:
        raise ValueError("\n".join(problems))
    return maps


def source_titles(repo) -> dict[str, str]:
    return {sid: str(value.get("title") or sid) for sid, value in repo.sources.items()}


def unit_node_titles(repo, uid: str) -> dict[str, str]:
    return {
        str(node["id"]): str(node.get("title") or node["id"])
        for node in (repo.units[uid].data.get("knowledge_map") or {}).get("nodes", [])
    }


def layer_for(row: dict) -> str:
    if row.get("scope") == "current" or row.get("source_role") == "course-material":
        return "1. Current scope and current practice"
    if row.get("source_role") in {"spine", "first-exposure", "derivation"}:
        return "2. Books and independent derivations"
    if row.get("source_role") in {"intuition", "implementation", "practice"}:
        return "3. Visual, implementation and additional practice"
    return "4. University courses, prior-year, exam and advanced reference"


def md_escape(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def compact_unit(uid: str) -> str:
    return uid.removeprefix("unit-m2-sad-").upper()


def overview_markdown(repo, source_map: dict, maps: dict[str, dict]) -> str:
    titles = source_titles(repo)
    routes = lecture_routes(source_map)
    old_rows = 0
    new_rows = 0
    for uid in LECTURE_IDS:
        old = repo.study_maps[repo.units[uid].data["current_study_map"]].data
        old_rows += sum(len(stage.get("resources", [])) for stage in old.get("stages", []))
        new_rows += sum(len(stage.get("resources", [])) for stage in maps[uid]["stages"])
    source_ids = {row["source_id"] for values in routes.values() for row in values}
    route_count = sum(len(values) for values in routes.values())
    lines = [
        f"# Statistics and Data Science — extensive learning plan ({DATE})",
        "",
        "This is the learner-facing overview of the complete SaD lecture sequence. The fifteen 2026 lecture decks remain the scope authority. Every other item is an explained option: current exercises are required practice; books, videos, other university courses, implementations, prior-year decks and solved exams are selected by the angle they provide. Availability is never confused with learner selection.",
        "",
        "## Plan architecture",
        "",
        f"- **15 lecture units**, each with one ordered stage per authored knowledge node.",
        f"- **{len(source_ids)} source families** and **{route_count} lecture-specific source routes** in the complete menu.",
        f"- **{new_rows} concept-stage resource appearances**, up from {old_rows}; the increase is the material that existed in the source map but was absent from the lecture maps.",
        "- Every route below includes an exact locator, a one-line angle, and the longer judgment: what it gives, what it assumes, and where it stops.",
        "- `required-now` means current course scope/practice. `helpful-now` is a selectable second angle. `reference-only` is prior-year or advanced material that should be opened only for a recorded gap.",
        "",
        "## Sequence at a glance",
        "",
        "| Lecture | Topic | Knowledge stages | Source routes | Stage resource rows |",
        "|---|---|---:|---:|---:|",
    ]
    for uid in LECTURE_IDS:
        unit = repo.units[uid].data
        lines.append(
            f"| `{compact_unit(uid)}` | {md_escape(unit.get('title'))} | "
            f"{len(maps[uid]['stages'])} | {len(routes[uid])} | "
            f"{sum(len(stage.get('resources', [])) for stage in maps[uid]['stages'])} |"
        )
    lines.extend([
        "",
        "## How to use a lecture map",
        "",
        "1. Read the current deck for the stage and reproduce the stage objective without notes.",
        "2. Attempt the exact current sheet item before reading the matching UE solution.",
        "3. Choose one second explanation whose angle matches the actual problem: intuition, derivation, implementation, extra drill, or deeper reference.",
        "4. Use solved external exams late and timed. A prior-year deck can clarify a terse slide but never expands current scope.",
        "5. Record misses against the stage; do not run every optional book or full university course end to end.",
        "",
    ])
    for uid in LECTURE_IDS:
        unit = repo.units[uid].data
        nodes = unit_node_titles(repo, uid)
        lines.extend([
            f"## {compact_unit(uid)} — {unit.get('title')}",
            "",
            f"**Lecture purpose.** {md_escape((unit.get('knowledge_map') or {}).get('summary'))}",
            "",
            "**Concept progression.**",
            "",
        ])
        for stage in maps[uid]["stages"]:
            node = next(
                row for row in (unit.get("knowledge_map") or {}).get("nodes", [])
                if row["id"] == "knowledge-" + stage["id"].removeprefix("stage-")
            )
            deps = [nodes.get(dep, dep) for dep in node.get("builds_on", []) or []]
            dep_text = f" Builds on: {', '.join(deps)}." if deps else ""
            lines.append(
                f"{stage['number']}. **{stage['title']}** — {stage['objective']}{dep_text}"
            )
        grouped: dict[str, list[dict]] = defaultdict(list)
        for item in routes[uid]:
            grouped[layer_for(item)].append(item)
        lines.extend(["", "**Complete source menu.**", ""])
        for layer in sorted(grouped):
            lines.extend([f"### {layer}", ""])
            for item in grouped[layer]:
                covered = [nodes.get(cid, cid) for cid in item.get("covers", [])]
                lines.extend([
                    f"- **{titles.get(item['source_id'], item['source_id'])} — {item['title']}**",
                    f"  - Use: `{item.get('format')}` · depth `{item.get('depth')}` · scope `{item.get('scope')}`",
                    f"  - Exact locator: `{md_escape(item.get('locator'))}`",
                    f"  - Covers: {', '.join(covered)}",
                    f"  - Angle: {md_escape(item.get('angle'))}",
                    f"  - Why this angle matters: {md_escape(item.get('angle_detail'))}",
                ])
                if item.get("vault_path"):
                    lines.append(f"  - Local target: `{item['vault_path']}`")
                if item.get("url"):
                    lines.append(f"  - Web target: {item['url']}")
            lines.append("")
        no_current_practice = not any(
            row.get("source_id") == "source-sad-uebungen" for row in routes[uid]
        )
        if no_current_practice:
            lines.extend([
                "**Explicit practice gap.** No current SaD sheet directly practises this lecture. The external/other-university problem routes are therefore visible, but none is mislabeled as current course evidence.",
                "",
            ])
    lines.extend([
        "## What is deliberately not forced into the sequence",
        "",
        "The full menu is available on every matching concept stage, but the plan does not preselect all books or ask for a second full course. Measure-theoretic probability (Swanson and the Regensburg paper), full CS229/18.650 depth, reinforcement learning, general linear-algebra archives, and unrelated mathematics-prep collections remain reference-only or out of direct SaD scope. Their dispositions are recorded in the coverage audit rather than silently omitted.",
        "",
    ])
    return "\n".join(lines)


def pdf_pages(path: Path) -> int | None:
    if path.suffix.lower() != ".pdf":
        return None
    result = subprocess.run(
        ["pdfinfo", str(path)], text=True, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, check=False,
    )
    if result.returncode:
        return None
    match = re.search(r"^Pages:\s+(\d+)\s*$", result.stdout, re.MULTILINE)
    return int(match.group(1)) if match else None


def inventory_rows(repo, source_map: dict) -> list[dict]:
    routes = lecture_routes(source_map)
    source_ids = sorted({row["source_id"] for values in routes.values() for row in values})
    manifest = load_yaml(REPO / "records/materials-manifest.yaml")
    manifest_files = manifest.get("files", {})
    rows: list[dict] = []
    seen: set[Path] = set()
    for sid in source_ids:
        src_routes = [row for values in routes.values() for row in values if row["source_id"] == sid]
        for uri, path in material_files_for_source(repo, sid):
            if path in seen:
                continue
            seen.add(path)
            rel = path.relative_to((repo.learningos_root / "materials").resolve()).as_posix()
            info = manifest_files.get(rel, {}) if isinstance(manifest_files, dict) else {}
            digest = str(info.get("sha256") or "")
            if not digest:
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
            matching = [
                row for row in src_routes
                if path.name in str(row.get("locator") or "")
                or uri == row.get("vault_path")
            ]
            rows.append({
                "source_id": sid,
                "uri": uri,
                "path": path,
                "relative": rel,
                "suffix": path.suffix.lower().removeprefix(".") or "file",
                "size": int(info.get("size") or path.stat().st_size),
                "sha256": digest,
                "pages": pdf_pages(path),
                "matching_routes": matching,
                "all_routes": src_routes,
            })
    duplicate_groups: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        duplicate_groups[row["sha256"]].append(row)
    for row in rows:
        group = duplicate_groups[row["sha256"]]
        row["duplicates"] = [other["uri"] for other in group if other is not row]
    return rows


def all_urls(value: object) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for child in value.values():
            found.extend(all_urls(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(all_urls(child))
    elif isinstance(value, str) and value.startswith(("https://", "http://")):
        found.append(value)
    return list(dict.fromkeys(found))


def audit_markdown(repo, source_map: dict, maps: dict[str, dict]) -> str:
    titles = source_titles(repo)
    routes = lecture_routes(source_map)
    inventory = inventory_rows(repo, source_map)
    source_ids = sorted({row["source_id"] for values in routes.values() for row in values})
    route_count = sum(len(values) for values in routes.values())
    new_rows = sum(
        len(stage.get("resources", []))
        for record in maps.values() for stage in record.get("stages", [])
    )
    old_rows = 0
    for uid in LECTURE_IDS:
        old = repo.study_maps[repo.units[uid].data["current_study_map"]].data
        old_rows += sum(len(stage.get("resources", [])) for stage in old.get("stages", []))
    source_entries = {entry["source_id"]: entry for entry in source_map["sources"]}
    lines = [
        f"# SaD extensive plan coverage audit — {DATE}",
        "",
        f"Plan package: `work/active/{WORKSPACE_ID}/outputs/{PLAN_PATH.name}`",
        "",
        "Scope authority: the fifteen current SoSe 2026 lecture decks under `material://source-sad-ss26-lectures/lecture-slides/`, with the current Blatt/UE assets as the closest assessment evidence. Every book, video, other-university course, prior-year deck and external exam is an explanation/practice layer and cannot enlarge current scope.",
        "",
        "Review boundary: all locally held files belonging to every source routed to L01-L15; all registered URLs carried by those source records; the complete current module source map; all fifteen unit knowledge maps and current study maps; the 2025 same-course deck collection; the current sheet/tutorial collection; the probability/statistics book shelf; the classical-ML shelf; Cornell CS4780 local homeworks; FAU and the four-file external German exam bank. The quarantined `Job/` tree and prospective Masters Planning quarantine were not entered.",
        "",
        "## Audit result",
        "",
        f"- {len(source_ids)} source families carry {route_count} lecture-specific routes into the fifteen ordinary lectures.",
        f"- {len(inventory)} distinct locally held files are accounted for below; duplicates remain separate rows and share a hash group.",
        f"- The rebuilt maps contain {new_rows} concept-stage resource appearances, compared with {old_rows} before rebuild.",
        "- Every ordinary lecture route has a one-line angle and a longer angle detail. Every new local route names one real file and an item/page or slide range.",
        "- Learner selections remain empty. This work expands and repairs the available menu; it does not claim that every optional source should be consumed.",
        "",
        "## Local material inventory",
        "",
        "One row per distinct physical file reached through a source routed to L01-L15. Supporting images/CSS/TeX inside the Cornell homework archive are listed rather than silently ignored; they are collection support, not separate learning routes. Page counts and hashes come from the opened local files and the 2026-08-26 materials manifest.",
        "",
        "| Local material URI | Source | Format/evidence | Actual contents or collection role | Duplicate/version relation | Disposition | Unit route | Lecture-specific angle |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for item in inventory:
        sid = item["source_id"]
        source = repo.sources[sid]
        source_entry = source_entries[sid]
        evidence = (
            f"{item['pages']} PDF pages; SHA-256 `{item['sha256'][:12]}…`"
            if item["pages"] is not None
            else f"{item['suffix']}; {item['size']} bytes; SHA-256 `{item['sha256'][:12]}…`"
        )
        matching = item["matching_routes"]
        if matching:
            contents = "; ".join(row["title"] for row in matching[:3])
            unit_text = ", ".join(sorted({compact_unit(row["unit_id"]) for row in matching}))
            angle = " ".join(row.get("angle", "") for row in matching[:2])
        else:
            contents = f"Supporting/alternate file inside {source.get('title')}; not independently selected as a lecture route"
            unit_text = "collection support"
            angle = source_entry.get("why", "")
        duplicates = (
            "same hash as " + ", ".join(f"`{uri}`" for uri in item["duplicates"][:3])
            if item["duplicates"] else "unique within reviewed SaD inventory"
        )
        if sid == "source-sad-ss26-lectures":
            disposition = "current scope authority"
        elif sid == "source-sad-uebungen":
            disposition = "current practice"
        elif sid == "source-sad-2025-recordings":
            disposition = "duplicate" if item["duplicates"] else "prior-year reference"
        elif sid == "source-swanson-principles-probability":
            disposition = "optional, far beyond scope"
        elif matching:
            disposition = source_entry.get("role", "complementary")
        else:
            disposition = "collection support / not separately routed"
        lines.append(
            "| `{uri}` | `{sid}` — {title} | {evidence} | {contents} | {duplicates} | {disp} | {units} | {angle} |".format(
                uri=md_escape(item["uri"]), sid=sid, title=md_escape(source.get("title")),
                evidence=md_escape(evidence), contents=md_escape(contents),
                duplicates=md_escape(duplicates), disp=md_escape(disposition),
                units=md_escape(unit_text), angle=md_escape(angle),
            )
        )

    lines.extend([
        "",
        "## Linked web material inventory",
        "",
        "Every URL carried by a source routed to an ordinary lecture. The repository-wide online verifier was run with network access on 2026-08-27. MIT 18.05, MIT 18.650 and Stanford CS229 were also opened directly; Harvard Stat 110 returned access control rather than a dead link. A URL can be reachable while a particular route still remains optional.",
        "",
        "| URL | Named by | Format | Official/primary evidence | Verified on | Actual topic/locator | Disposition | Unit route | Lecture-specific angle |",
        "|---|---|---|---|---|---|---|---|---|",
    ])
    for sid in source_ids:
        source = repo.sources[sid]
        urls = all_urls(source)
        if not urls:
            continue
        src_routes = [row for values in routes.values() for row in values if row["source_id"] == sid]
        unit_text = ", ".join(sorted({compact_unit(row["unit_id"]) for row in src_routes}))
        route_topics = "; ".join(row["title"] for row in src_routes[:4])
        angles = " ".join(row.get("angle", "") for row in src_routes[:2])
        for url in urls:
            if "stat110" in url or "projects.iq.harvard.edu/stat110" in url:
                verified = "2026-08-27 — HTTP 403/access-controlled, not dead"
            elif url in {
                "https://ocw.mit.edu/courses/18-05-introduction-to-probability-and-statistics-spring-2022/",
                "https://ocw.mit.edu/courses/18-650-statistics-for-applications-fall-2016/",
                "https://cs229.stanford.edu/",
            }:
                verified = "2026-08-27 — opened directly and reachable"
            else:
                verified = "2026-08-27 — registry-wide online pass"
            official = "official course/publisher/author page" if any(
                domain in url for domain in [
                    "mit.edu", "stanford.edu", "cornell.edu", "berkeley.edu", "caltech.edu",
                    "microsoft.com", "google.com", "scikit-learn.org", "coursera.org",
                    "harvard.edu", "openintro.org", "deeplearningbook.org",
                ]
            ) else "registered author/project/channel page"
            lines.append(
                f"| [{md_escape(url)}]({url}) | `{sid}` — {md_escape(source.get('title'))} | "
                f"{md_escape(source.get('type') or 'web')} | {official} | {verified} | "
                f"{md_escape(route_topics)} | {md_escape(source_entries[sid].get('role'))} | "
                f"{unit_text} | {md_escape(angles)} |"
            )

    lines.extend([
        "",
        "## Source-family disposition ledger",
        "",
        "This is the compact answer to “did every possessed source get considered?” Each family is present because it has at least one L01-L15 route; route-level detail lives in the learning-plan overview.",
        "",
        "| Source | Role | Why it exists in this module | Lecture routes | Units |",
        "|---|---|---|---:|---|",
    ])
    for sid in source_ids:
        entry = source_entries[sid]
        src_routes = [row for values in routes.values() for row in values if row["source_id"] == sid]
        units = ", ".join(sorted({compact_unit(row["unit_id"]) for row in src_routes}))
        lines.append(
            f"| `{sid}` — {md_escape(titles[sid])} | {entry.get('role')} | "
            f"{md_escape(entry.get('why'))} | {len(src_routes)} | {units} |"
        )

    lines.extend([
        "",
        "## Current/prior and duplicate reconciliation",
        "",
        "| Current asset | Prior/alternate asset | Content match/difference | Authority decision | Route |",
        "|---|---|---|---|---|",
        "| L04 `04_probability.pdf` | 2025 `04_probability_with_notes (1).pdf` | Same probability spine; prior file preserves spoken-note context and different examples | 2026 defines scope; 2025 is reference-only | L04 |",
        "| L05 `05_combinatorics.pdf` | 2025 `05_random_variables.pdf` | Numbering changed; the prior file contains the finite-probability/counting bridge despite its filename | aligned by inspected topic, never number | L05 |",
        "| L06 `06_random_variables.pdf` | 2025 `06_expected_values.pptx-1.pdf` | 2025 gives expectation a whole deck, slower than the combined 2026 treatment | prior-year depth only | L06 |",
        "| L07 `07_discrete_distributions.pdf` | 2025 `07_discrete_distributions.pptx (1).pdf` | Same families, different examples and notation | current formulas win | L07 |",
        "| L08 `08_normal_distribution.pdf` | 2025 `08_normal_distribution_no_notes.pdf` | Same Normal/CLT core; no spoken-note advantage | lower-priority prior-year alternative | L08 |",
        "| L09 `09_estimating.pdf` | 2025 `09_point_interval_estimation (1).pdf` | Prior deck contains additional interval examples | current notation wins | L09 |",
        "| L10 `10_testing.pdf` | 2025 `10_statistical_significance.pdf` | Same inferential core, organized around meaning of significance rather than procedure | second framing only | L10 |",
        "| L13 `13_similarity_based.pdf` | 2025 `13_similarity_based_part3.pdf` | Prior year spread the topic across more sessions and elaborates indexing | useful reference because books under-cover indexing | L13 |",
        "| L15 `15_neural_networks.pdf` | 2025 Parts 1 (89 pp) and 2 (223 pp) | Two sessions versus one; much more loss/gradient/nonlinearity detail | open only the matching section after current pass | L15 |",
        "| Current UE2-UE7 copies | prior-year UE2-UE7 copies | Byte-identical pairs by SHA-256 | current copies are routed; prior copies are recorded duplicates | L01-L15 as mapped |",
        "",
        "## Explicit exclusions and unresolved gaps",
        "",
        "| Material/topic | Disposition | Evidence | Reason | Revisit condition |",
        "|---|---|---|---|---|",
        "| FAU L03 former 'solved compute-and-interpret' claim | corrected | rendered/extracted PDF p. 35 task 8 and solution p. 48 | actual item is a short covariance/correlation R-formula completion | no revisit; corrected route is in this package |",
        "| FAU routes formerly placed on L05 and L09 | removed from those lectures | full 50-page page/task scan | no verified combinatorics-only or confidence-interval item matching the former claims | restore only with an exact page/task that matches current scope |",
        "| Regensburg-Löh probability/statistics exam | optional advanced reference | pp. 2-14 contain sigma-algebras, proofs, convergence, LLN/CLT | substantially more theoretical than SaD; not normal practice | only for a formal-definition/convergence gap |",
        "| Leuphana-Merz 109-page collection | item-level only | pp. 5-40 inspected and split by exercise block | a whole-book locator would mix probability, estimation and testing | later pages can feed exam-prep only after item review |",
        "| `Statistics_And_Data_Science.pdf` sheet number | unresolved name, content routed | 3-page PDF opened; Normal/estimation/CLT content matches Blatt 4 sequence | printed filename/title does not recover 'Blatt 4' | rename only with authoritative Moodle metadata |",
        "| Current Blatt 3/Blatt 4 filenames | numbering gap recorded | no files literally named Blatt3 or Blatt4 under the source root | nearby files must not be silently relabeled | revisit if official originals arrive |",
        "| L12 current course exercise | genuine gap | no current Blatt/UE item directly exercises trees/ensembles | other-university and book exercises are visible but not mislabeled as current | fill if a current sheet appears |",
        "| L13 exact indexing and LSH practice | genuine gap | current deck teaches kd/M-trees and LSH; no current sheet and little book coverage | existing prior-year/MIT/CS sources explain but do not give a matched current drill | add only a verified similarity-search problem source |",
        "| Swanson, *Principles of Probability* | reference-only/outside normal path | local book is formal logic and measure theory, not an elementary probability text | title alone would misleadingly suggest an L04-L08 spine | open only for a formal L06 definition |",
        "| Cornell CS4780 images, CSS and TeX support files | collection support | 2017/2018 homework directory inventoried file-by-file | needed to render/understand the held homework set, but not independent learning resources | none |",
        "| Linear-algebra archives, generic mathematics prep/vorkurs, Sutton-Barto RL | out of direct SaD scope | global registry/source review | either prerequisites already covered by targeted routes or topics not taught in L01-L15 | route only if the current deck or a diagnosed prerequisite demands it |",
        "| Vershynin HDP, MIT 18.06/matrix calculus, MIT 6.S191, CS231n, Hinton/NYU deep learning, PyTorch and MITx 6.86 links | reviewed but not routed | registered URL/source comparison | duplicate much stronger existing angles or go beyond the short L11-L15 survey; adding them would make the menu noisier without closing a node gap | revisit for an advanced ML module, not this exam plan |",
        "",
        "## Unit knowledge and material matrix",
        "",
        "| Unit | Knowledge nodes and dependencies | Current authority/practice | Books | Videos/websites/courses | External/prior/advanced | Source routes | Stage rows | Coverage gap |",
        "|---|---|---|---|---|---|---:|---:|---|",
    ])
    for uid in LECTURE_IDS:
        unit = repo.units[uid].data
        nodes = (unit.get("knowledge_map") or {}).get("nodes", [])
        node_text = "; ".join(
            f"{node['title']}" + (
                " <- " + ", ".join(dep.removeprefix("knowledge-sad-") for dep in node.get("builds_on", []))
                if node.get("builds_on") else ""
            ) for node in nodes
        )
        values = routes[uid]
        current = [row["title"] for row in values if row.get("scope") == "current"]
        books = [row["title"] for row in values if row.get("format") == "book"]
        web = [row["title"] for row in values if row.get("format") in {"video", "website", "course", "documentation", "code", "paper"}]
        other = [row["title"] for row in values if row.get("scope") in {"prior-year", "optional"} or row.get("source_role") == "exam-preparation"]
        gaps = []
        if not any(row["source_id"] == "source-sad-uebungen" for row in values):
            gaps.append("no current course exercise")
        if uid == "unit-m2-sad-l13":
            gaps.append("no matched kd/M-tree/LSH drill")
        lines.append(
            f"| `{compact_unit(uid)}` | {md_escape(node_text)} | {md_escape('; '.join(current))} | "
            f"{md_escape('; '.join(books))} | {md_escape('; '.join(web))} | "
            f"{md_escape('; '.join(other))} | {len(values)} | "
            f"{sum(len(stage.get('resources', [])) for stage in maps[uid]['stages'])} | "
            f"{md_escape('; '.join(gaps) or 'none')} |"
        )

    lines.extend([
        "",
        "## Completeness sign-off",
        "",
        "- [x] Every distinct file under every local source routed to L01-L15 has an inventory row, including duplicate and support files.",
        "- [x] Every URL carried by those source records has a linked-inventory row.",
        "- [x] Current decks, exercises, the selected book sections and local exams were opened/content-checked; no route correction came from a filename alone.",
        "- [x] Current and prior-year scope was reconciled by topic and content, not lecture number.",
        "- [x] Suspected duplicates were checked by SHA-256; current/prior UE2-UE7 byte-identical pairs remain visible.",
        "- [x] Every route has a disposition, format, lecture, exact locator, one-line angle and long-form angle detail.",
        "- [x] Every route names only knowledge nodes declared by its own lecture; assembly validation enforces this.",
        "- [x] Learner choices remain separate from the complete menu; no optional source is preselected.",
        "- [x] Exercise gaps, theoretical overreach, support assets and inaccessible/access-controlled links are explicit.",
        "- [x] Every ordinary lecture has an individual map and matrix row; the auxiliary clustering unit does not replace any lecture.",
        "",
        "## Completeness boundary and canonical status",
        "",
        "This audit establishes a complete, reviewable SaD L01-L15 menu. It does not claim mastery or require every source to be consumed. The generated package is not canonical until the repository's module-plan preflight and Gateway transaction accept it. Data-contract v13 route identity migration remains separately governed; this plan does not invent route IDs or weaken that guard.",
        "",
    ])
    return "\n".join(lines)


def plan_package(repo, source_map: dict, maps: dict[str, dict]) -> dict:
    module_path = REPO / "curriculum/modules" / MODULE_ID / "module.yaml"
    module = load_yaml(module_path)
    workspace = repo.workspaces[WORKSPACE_ID]
    routed_source_ids = {
        row["source_id"]
        for rows in lecture_routes(source_map).values()
        for row in rows
    }
    workspace_sources = list(workspace.meta.get("sources", []))
    for entry in source_map.get("sources", []):
        source_id = entry["source_id"]
        if source_id in routed_source_ids and source_id not in workspace_sources:
            workspace_sources.append(source_id)
    units = []
    for uid in LECTURE_IDS:
        unit_path = REPO / "curriculum/modules" / MODULE_ID / "units" / uid / "unit.yaml"
        units.append({"unit": load_yaml(unit_path), "study_map": maps[uid]})
    return {
        "module_id": MODULE_ID,
        "plan_contract": {
            "version": 2,
            "plan_template_version": 1,
            "coverage_audit": f"work/active/{WORKSPACE_ID}/outputs/{AUDIT_PATH.name}",
            "intentional_reorders": [],
            "checks": {
                "local_inventory_complete": True,
                "linked_inventory_complete": True,
                "materials_opened_and_content_checked": True,
                "current_and_prior_scope_reconciled": True,
                "duplicates_and_numbering_checked": True,
                "exclusions_and_unresolved_gaps_recorded": True,
            },
        },
        "module_patch": {"unit_order": list(module.get("unit_order", []))},
        "source_patches": [],
        "source_map": source_map,
        "units": units,
        "workspace_updates": [{
            "id": WORKSPACE_ID,
            "sources": workspace_sources,
            "unit_ids": list(workspace.meta.get("unit_ids", [])),
        }],
    }


def main() -> int:
    repo = load_repo(REPO)
    source_map = patched_source_map(repo)
    maps = assemble_maps(repo, source_map)
    MAP_DIR.mkdir(parents=True, exist_ok=True)
    for uid, record in maps.items():
        (MAP_DIR / f"{uid}.study-map.yaml").write_text(
            dump_yaml(record), encoding="utf-8"
        )
    OVERVIEW_PATH.write_text(
        overview_markdown(repo, source_map, maps), encoding="utf-8"
    )
    AUDIT_PATH.write_text(
        audit_markdown(repo, source_map, maps), encoding="utf-8"
    )
    package = plan_package(repo, source_map, maps)
    PLAN_PATH.write_text(dump_yaml(package), encoding="utf-8")

    routes = lecture_routes(source_map)
    print(f"wrote {len(maps)} lecture maps to {MAP_DIR.relative_to(REPO)}")
    print(f"wrote overview: {OVERVIEW_PATH.relative_to(REPO)}")
    print(f"wrote coverage audit: {AUDIT_PATH.relative_to(REPO)}")
    print(f"wrote plan package: {PLAN_PATH.relative_to(REPO)}")
    print(f"lecture routes: {sum(len(value) for value in routes.values())}")
    print(
        "stage resource rows:",
        sum(len(stage.get("resources", []))
            for record in maps.values() for stage in record["stages"]),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
