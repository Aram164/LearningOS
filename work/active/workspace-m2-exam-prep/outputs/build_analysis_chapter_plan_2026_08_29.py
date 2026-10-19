#!/usr/bin/env python3
"""Build the chapter-per-session Analysis plan package.

Until now the Analysis half of M2 lived in one unit
(`unit-m2-analysis-exam-prep`) carrying eleven hand-written stages, while the
Statistics half runs as fifteen lecture units whose study maps are assembled
from the module source map and therefore carry a per-resource `angle` and
`angle_detail`. This generator gives Analysis the same shape, with the script's
own chapters as the session boundary:

    unit-m2-analysis-ch01 .. ch07   one unit per chapter of `unser skript.pdf`
    unit-m2-analysis-exam-prep      re-scoped to calibration + timed transfer

One stage per script section (or section group), and every material route is
re-cut so it names the chapter it actually serves, at the page it starts on.
Section titles and page numbers come from the script's own Inhaltsverzeichnis
(PDF pp. 2-3); every other locator was read out of the source PDF itself on
2026-08-29, not inferred from a filename.

This is a workbench generator, not a canonical writer. It writes only under the
owning workspace; the package must pass `module-plan-import --check` and the
Gateway before anything reaches `curriculum/`.
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
    assembly_problems,
    build,
    concept_phrases,
    _manifest,
)
from learning_os.contracts import (  # noqa: E402
    require_current_template,
    validate_contract,
)
from learning_os.loader import load_repo  # noqa: E402

MODULE_ID = "module-hu-m2-statistik-analysis"
COMPONENT_ID = "component-m2-analysis"
WORKSPACE_ID = "workspace-m2-exam-prep"
DATE = "2026-08-29"
OLD_UNIT = "unit-m2-analysis-exam-prep"
CHAPTER_UNITS = [f"unit-m2-analysis-ch{n:02d}" for n in range(1, 8)]
ANALYSIS_UNITS = CHAPTER_UNITS + [OLD_UNIT]

MAP_DIR = OUT / f"Analysis-chapter-maps-{DATE}"
PLAN_PATH = OUT / f"Analysis-chapter-plan-{DATE}.yaml"
AUDIT_PATH = OUT / f"Analysis-chapter-coverage-audit-{DATE}.md"
OVERVIEW_PATH = OUT / f"Analysis-chapter-plan-overview-{DATE}.md"

# The script prints front matter in roman numerals, so an arabic printed page
# sits ten pages into the PDF. Every script locator below gives the printed
# page and the PDF page, because the reader needs one and the viewer the other.
PDF_OFFSET = 10


def sk(printed: int) -> str:
    return f"printed p. {printed} (PDF p. {printed + PDF_OFFSET})"


def dump_yaml(value) -> str:
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=True, width=100)


# --------------------------------------------------------------------------
# The chapters, as the script itself divides them.
#
# `sections` is the script's own numbering; `label` marks the course contract's
# three depths — Wiederholung (assumed known), Ausflug (overview understanding,
# not an exam focus) and Exkurs (explicitly not exam-relevant, script p. vii).
# --------------------------------------------------------------------------

N = "knowledge-m2-analysis"

CHAPTERS = [
    {
        "unit_id": "unit-m2-analysis-ch01",
        "order": 101,
        "title": "Analysis Kapitel 1 — Wiederholung: Grundlagen",
        "pages": (1, 6),
        "scope": (
            "Script Chapter 1 'Wiederholung – Grundlagen', printed pp. 1-6 (PDF pp. 11-16). "
            "The whole chapter carries the Wiederholung label, which under the course contract "
            "(script p. vii) means the content is assumed known and is not re-taught in the "
            "lecture — so this session is a checked repair pass, not a first exposure. It owns "
            "the induction technique every later chapter reuses."
        ),
        "summary": (
            "The chapter fixes the number sets, the induction principle and the standard "
            "inequalities the rest of the script argues with. Nothing here is new material by "
            "the course's own account; what makes it a session is that a gap in induction or "
            "in the Bernoulli/triangle inequalities surfaces later as a failed convergence "
            "proof, where it is far more expensive to find."
        ),
        "nodes": [
            (f"{N}-ch01-zahlenmengen", "Zahlenmengen und Notation (§1.1)",
             "The number sets N, Z, Q, R and the notation the script uses for them, together "
             "with the logical and set symbols fixed in the Bezeichnungen section. This is the "
             "vocabulary every later definition is written in.", []),
            (f"{N}-ch01-induktion", "Vollständige Induktion (§1.2)",
             "The induction principle and its schema: base case, hypothesis, step. The script "
             "assumes it from M1, and it is the one Chapter 1 technique that reappears as an "
             "exam task in its own right and inside recursive-sequence arguments.",
             [f"{N}-ch01-zahlenmengen"]),
            (f"{N}-ch01-beziehungen", "Wichtige Beziehungen in der Analysis (§1.3)",
             "The standard inequalities and identities the later chapters apply without comment "
             "— triangle inequality, Bernoulli, binomial theorem, geometric sum. They are the "
             "estimation toolkit every epsilon argument reaches for.",
             [f"{N}-ch01-induktion"]),
        ],
    },
    {
        "unit_id": "unit-m2-analysis-ch02",
        "order": 102,
        "title": "Analysis Kapitel 2 — Die reellen Zahlen",
        "pages": (7, 40),
        "scope": (
            "Script Chapter 2 'Die reellen Zahlen', printed pp. 7-40 (PDF pp. 17-50). §2.1 is "
            "Wiederholung; §§2.2-2.3 are the load-bearing content, with completeness (§2.3.3) "
            "the axiom every limit in the script ultimately rests on; §2.4 'Darstellung reeller "
            "Zahlen im Rechner' is an Ausflug and is held at overview depth."
        ),
        "summary": (
            "Chapter 2 turns R from a set you compute in into an ordered, complete field — and "
            "completeness is the single hinge of the whole script: without it suprema need not "
            "exist, monotone bounded sequences need not converge, and Chapters 3 to 7 have "
            "nothing to stand on. The Ausflug on machine numbers is the chapter's CS payoff and "
            "the reason the module is called 'Analysis und ihre Bezüge zur Informatik'."
        ),
        "nodes": [
            (f"{N}-ch02-koerperaxiome", "Wiederholung – Körperaxiome (§2.1)",
             "The field axioms and the consequences drawn from them. Labelled Wiederholung: "
             "assumed from M1.2, restated here only to fix notation.", []),
            (f"{N}-ch02-anordnung", "Anordnung von R (§2.2)",
             "The order axioms and the rules for manipulating inequalities. Every later estimate "
             "is an inequality argument, so fluency here is what makes epsilon arguments "
             "writable.", [f"{N}-ch02-koerperaxiome"]),
            (f"{N}-ch02-intervalle-betrag", "Intervalle und Betragsfunktion (§2.3.1)",
             "Interval notation and the absolute value as a distance, including the triangle "
             "inequality in the form the convergence definition uses.",
             [f"{N}-ch02-anordnung"]),
            (f"{N}-ch02-supremum-infimum", "Supremum und Infimum von Mengen (§2.3.2)",
             "Bounded sets, upper and lower bounds, supremum and infimum, and the difference "
             "between a supremum and a maximum. The distinction is a standing exam question and "
             "the reason Serie 05's Hausaufgabe 5.4 exists.",
             [f"{N}-ch02-intervalle-betrag"]),
            (f"{N}-ch02-vollstaendigkeitsaxiom", "Das Vollständigkeitsaxiom (§2.3.3)",
             "The completeness axiom in the script's supremum form. It is the axiom that "
             "separates R from Q and the one every convergence theorem later cites, directly or "
             "through Bolzano-Weierstraß.", [f"{N}-ch02-supremum-infimum"]),
            (f"{N}-ch02-folgerungen", "Folgerungen aus dem Vollständigkeitsaxiom (§2.3.4)",
             "What completeness immediately buys: the Archimedean property and the density of Q "
             "in R. These are the steps that let an epsilon argument choose an N at all.",
             [f"{N}-ch02-vollstaendigkeitsaxiom"]),
            (f"{N}-ch02-potenzen-wurzeln", "Potenzen und Wurzeln reeller Zahlen (§§2.3.5-2.3.6)",
             "Powers with integer and rational exponents, and the existence of n-th roots as the "
             "first genuine payoff of completeness — an existence proof rather than a "
             "calculation. Serie 07's Heron task is its computational counterpart.",
             [f"{N}-ch02-folgerungen"]),
            (f"{N}-ch02-maschinenzahlen", "Ausflug – Darstellung reeller Zahlen im Rechner (§2.4)",
             "Floating-point machine numbers, rounding error and machine arithmetic: why a "
             "complete ordered field cannot be represented exactly and what breaks when you "
             "pretend otherwise. Ausflug depth — understand and apply the core claims; not an "
             "exam focus.", [f"{N}-ch02-potenzen-wurzeln"]),
        ],
    },
    {
        "unit_id": "unit-m2-analysis-ch03",
        "order": 103,
        "title": "Analysis Kapitel 3 — Folgen und Konvergenz",
        "pages": (41, 79),
        "scope": (
            "Script Chapter 3 'Folgen und Konvergenz', printed pp. 41-79 (PDF pp. 51-89). The "
            "largest exam-bearing chapter and the one with the most current HU practice: Serien "
            "05, 06 and 07 and Hausaufgabe WV1.1 are all Chapter 3. §3.2 (Landau-Notation) and "
            "§3.4 are Exkurse; §3.3 (lineare Rekursionsgleichungen) and §3.8 (Berechnung der "
            "Quadratwurzel) are Ausflüge that the HU sheets nevertheless examine."
        ),
        "summary": (
            "Chapter 3 is the spine: it defines convergence, supplies every criterion for "
            "deciding it, and is the chapter the rest of the script reduces to. Series are "
            "sequences of partial sums, function limits are defined through sequences, and "
            "continuity and the derivative are function limits — so a gap here reappears four "
            "times. The chapter also carries the two Informatik excursions the module is named "
            "for: Landau notation and linear recurrences."
        ),
        "nodes": [
            (f"{N}-ch03-folgen", "Folgen (§3.1)",
             "Sequences as functions on N, explicit and recursive definition, boundedness and "
             "monotonicity. The vocabulary every later criterion is stated in.", []),
            (f"{N}-ch03-rekursionen", "Ausflug – Lineare Rekursionsgleichungen (§§3.3-3.4)",
             "Setting up a recurrence from a process and solving the linear homogeneous case. "
             "§3.3 is an Ausflug and §3.4 an Exkurs, but Serie 05's Türme-von-Hanoi task is "
             "exactly this, so the modelling half is examined even though the solution theory is "
             "not.", [f"{N}-ch03-folgen"]),
            (f"{N}-ch03-konvergenzkriterien", "Konvergenzkriterien für Folgen (§3.5)",
             "The epsilon-N definition of convergence and the criteria that avoid it: monotone "
             "and bounded, Cauchy, subsequences and accumulation points, Bolzano-Weierstraß. "
             "Choosing the criterion is the graded skill, not knowing the list.",
             [f"{N}-ch03-folgen"]),
            (f"{N}-ch03-rechenregeln", "Rechnen mit konvergenten Folgen (§3.6)",
             "The limit laws for sums, products and quotients, the sandwich argument, and the "
             "standard manipulations — dividing by the dominant power, rationalising a difference "
             "of roots — that turn a limit into a computation.",
             [f"{N}-ch03-konvergenzkriterien"]),
            (f"{N}-ch03-bestimmte-divergenz", "Bestimmt divergente Folgen (§3.7)",
             "Divergence to plus or minus infinity as a positive statement rather than the mere absence "
             "of a limit, and the arithmetic that survives it.",
             [f"{N}-ch03-rechenregeln"]),
            (f"{N}-ch03-quadratwurzel", "Ausflug – Berechnung der Quadratwurzel (§3.8)",
             "The Heron iteration as a monotone bounded recursive sequence whose limit is the "
             "root: the chapter's own worked example of convergence proving something the field "
             "axioms cannot construct. Serie 07's Aufgabe 7.1.",
             [f"{N}-ch03-konvergenzkriterien"]),
        ],
    },
]

CHAPTERS += [
    {
        "unit_id": "unit-m2-analysis-ch04",
        "order": 104,
        "title": "Analysis Kapitel 4 — Reihen",
        "pages": (80, 97),
        "scope": (
            "Script Chapter 4 'Reihen', printed pp. 80-97 (PDF pp. 90-107). Current HU practice "
            "is Serie 08 (Aufgaben 8.1-8.3) and Hausaufgabe WV1.3, which asks one single series "
            "to be settled four different ways. §4.4 (Umordnungen) is an Ausflug; §4.5 "
            "(Produktreihen) is an Exkurs and outside the exam."
        ),
        "summary": (
            "A series is the sequence of its partial sums, so Chapter 4 adds no new notion of "
            "convergence — it adds a decision procedure. The examinable skill is picking the "
            "right criterion and stating its hypotheses correctly, which is exactly what WV1.3 "
            "drills by demanding the same series be handled with the ratio, root, comparison and "
            "Leibniz criteria in turn."
        ),
        "nodes": [
            (f"{N}-ch04-reihen", "Reihen (§4.1)",
             "Series as sequences of partial sums, the necessary null-sequence condition, and the "
             "two series whose sums can actually be computed: geometric and telescoping.", []),
            (f"{N}-ch04-konvergenzkriterien", "Konvergenzkriterien für Reihen (§4.2)",
             "Comparison (Majoranten/Minoranten), ratio, root and Leibniz criteria, each with its "
             "hypotheses and its inconclusive case. The exam failure mode is method choice, not "
             "missing knowledge of the list.", [f"{N}-ch04-reihen"]),
            (f"{N}-ch04-absolute-konvergenz", "Absolute Konvergenz (§4.3)",
             "Absolute versus conditional convergence, and why the distinction is not pedantry: "
             "it is the hypothesis the rearrangement result turns on.",
             [f"{N}-ch04-konvergenzkriterien"]),
            (f"{N}-ch04-umordnungen", "Ausflug – Umordnungen (§4.4)",
             "The Riemann rearrangement phenomenon: a conditionally convergent series can be "
             "reordered to any value. Ausflug depth — know the statement and what it costs.",
             [f"{N}-ch04-absolute-konvergenz"]),
        ],
    },
    {
        "unit_id": "unit-m2-analysis-ch05",
        "order": 105,
        "title": "Analysis Kapitel 5 — Differentialrechnung I",
        "pages": (98, 136),
        "scope": (
            "Script Chapter 5 'Differentialrechnung I', printed pp. 98-136 (PDF pp. 108-146). "
            "Despite the title the chapter contains no derivatives: it is function limits, "
            "continuity, the theorems on compact intervals, the exponential and logarithm, and "
            "uniform convergence. Current HU practice reaches §5.5 and stops there — Serie 08.4, "
            "Serie 09 and Hausaufgaben WV1.2 and WV1.4. §5.8 (Potenzreihen) is an Exkurs."
        ),
        "summary": (
            "Chapter 5 carries the definition of a limit of a function through sequences, which "
            "is why Chapter 3 had to come first, and then spends itself on continuity and its "
            "three consequences on a closed bounded interval: the intermediate value theorem, "
            "the extreme value theorem, and the existence of a continuous inverse. It is the last "
            "chapter with current HU exercises, and the theorems here are the ones the external "
            "Klausuren ask to be stated with complete hypotheses."
        ),
        "nodes": [
            (f"{N}-ch05-funktionsgrenzwerte", "Grenzwerte bei Funktionen (§5.1)",
             "The limit of a function at an accumulation point, defined both directly and through "
             "the sequence criterion. Serie 08.4 asks for one limit proved both ways, which is "
             "the clearest signal of what the course wants here.", []),
            (f"{N}-ch05-einseitige-grenzwerte", "Uneigentliche und einseitige Grenzwerte (§5.2)",
             "One-sided limits, limits at infinity and infinite limits, and the discipline of "
             "falling back to one-sided limits when the two-sided one fails to exist.",
             [f"{N}-ch05-funktionsgrenzwerte"]),
            (f"{N}-ch05-stetigkeit", "Stetige Funktionen (§5.3)",
             "Continuity at a point and on a set, the epsilon-delta and sequence formulations, "
             "and the rules for sums, products, quotients and compositions. Proving continuity "
             "at exactly one point is a recurring exam shape.",
             [f"{N}-ch05-funktionsgrenzwerte"]),
            (f"{N}-ch05-zwischenwertsatz", "Zwischenwertsatz, Umkehrfunktion und Extrempunkte (§5.4)",
             "The intermediate value theorem with its hypotheses stated exactly, the existence "
             "and continuity of inverse functions on intervals, and extreme points. WV1.4 asks "
             "for the statement first and the application second, in that order.",
             [f"{N}-ch05-stetigkeit"]),
            (f"{N}-ch05-kompakte-intervalle",
             "Besonderheiten stetiger Funktionen auf abgeschlossenen, beschränkten Intervallen (§5.5)",
             "Boundedness, attained maximum and minimum, and uniform continuity on a compact "
             "interval. Short in the script and heavily used afterwards — several external "
             "Klausur tasks are this theorem in disguise.",
             [f"{N}-ch05-zwischenwertsatz"]),
            (f"{N}-ch05-exponentialfunktion", "Exponentialfunktion und Logarithmen (§5.6)",
             "The exponential series, the functional equation, the logarithm as its inverse and "
             "the general power. Kept computational: the laws must be usable, the construction "
             "need not be reproduced.", [f"{N}-ch05-stetigkeit"]),
            (f"{N}-ch05-gleichmaessige-konvergenz",
             "Gleichmäßige Konvergenz von Funktionenfolgen (§5.7)",
             "Pointwise versus uniform convergence of a sequence of functions, and what uniform "
             "convergence preserves that pointwise does not. Two script pages and no HU sheet, "
             "which is exactly why it is easy to arrive at the exam never having practised it.",
             [f"{N}-ch05-funktionsgrenzwerte"]),
        ],
    },
    {
        "unit_id": "unit-m2-analysis-ch06",
        "order": 106,
        "title": "Analysis Kapitel 6 — Differentialrechnung II",
        "pages": (137, 190),
        "scope": (
            "Script Chapter 6 'Differentialrechnung II', printed pp. 137-190 (PDF pp. 147-200). "
            "The longest chapter, and the first with no current HU exercise sheet at all — the "
            "local HU set stops at §5.5, so every drill on this session is a substitute, "
            "recorded as such since the 2026-08-03 audit. §§6.2, 6.6 and 6.9 are Exkurse; §6.4 "
            "and §6.10 are Ausflüge."
        ),
        "summary": (
            "Chapter 6 builds the derivative from the function limit of Chapter 5 and then spends "
            "itself on one theorem — the mean value theorem — and its consequences: monotonicity, "
            "extrema, l'Hospital, and finally Taylor approximation with an error bound. The "
            "chapter is where the module stops being about existence and starts being about "
            "computation, and it is also where the practice evidence gets thinnest."
        ),
        "nodes": [
            (f"{N}-ch06-differenzierbarkeit", "Differenzierbarkeit und Ableitungen (§6.1)",
             "The derivative as a limit of difference quotients, differentiability implying "
             "continuity, and the calculation rules including chain rule and the derivative of an "
             "inverse function.", []),
            (f"{N}-ch06-mittelwertsatz", "Mittelwertsatz der Differentialrechnung (§6.3)",
             "Rolle's theorem and the mean value theorem, and the corollaries that do the actual "
             "work: zero derivative means constant, and the sign of the derivative controls "
             "monotonicity.", [f"{N}-ch06-differenzierbarkeit"]),
            (f"{N}-ch06-trigonometrie", "Ausflug – Sinus-, Kosinus- und Tangensfunktion (§6.4)",
             "The trigonometric functions and their derivatives. Ausflug depth in the script, but "
             "they appear as raw material in almost every external limit, derivative and integral "
             "task, so they are kept usable rather than skipped.",
             [f"{N}-ch06-differenzierbarkeit"]),
            (f"{N}-ch06-hospital", "Regel von l'Hospital (§6.5)",
             "L'Hospital's rule, its indeterminate forms, and the hypothesis check that has to "
             "precede every application. The commonest way to lose points here is applying it to "
             "a form that is not indeterminate.", [f"{N}-ch06-mittelwertsatz"]),
            (f"{N}-ch06-hoehere-ableitungen", "Höhere Ableitungen (§6.7)",
             "Higher derivatives, the C^k classes, and convexity — the vocabulary Taylor's "
             "theorem is stated in.", [f"{N}-ch06-mittelwertsatz"]),
            (f"{N}-ch06-taylor", "Taylorpolynome und Taylorreihen (§6.8)",
             "The Taylor polynomial, the Lagrange remainder and the error bound that makes the "
             "approximation usable. No HU sheet reaches this section, so the whole practice load "
             "is assembled from four named external sets.",
             [f"{N}-ch06-hoehere-ableitungen"]),
            (f"{N}-ch06-interpolation", "Ausflug – Einblick in die numerische Interpolation (§6.10)",
             "Polynomial interpolation and its error term, the chapter's second Informatik "
             "excursion. Ausflug depth — the idea and the error statement, not the algorithms.",
             [f"{N}-ch06-taylor"]),
        ],
    },
    {
        "unit_id": "unit-m2-analysis-ch07",
        "order": 107,
        "title": "Analysis Kapitel 7 — Integralrechnung",
        "pages": (191, 225),
        "scope": (
            "Script Chapter 7 'Integralrechnung', printed pp. 191-225 (PDF pp. 201-235). Like "
            "Chapter 6 it has no current HU sheet. §7.4 (numerische Integration) is an Exkurs. "
            "This is the chapter the external Klausur bank covers best — Regensburg asks the "
            "Hauptsatz and partielle Integration to be stated and proved, Paderborn and Ulm both "
            "set substitution/parts integrals — so the substitute practice here is stronger than "
            "for Chapter 6."
        ),
        "summary": (
            "Chapter 7 defines the Riemann integral through upper and lower sums, proves that "
            "continuous functions on a compact interval are integrable — which is Chapter 5's "
            "theorem doing its work — and then hands over the fundamental theorem, which turns "
            "integration into antidifferentiation. Substitution and integration by parts are the "
            "two techniques, and improper integrals are where convergence returns."
        ),
        "nodes": [
            (f"{N}-ch07-riemann-integral", "Das Riemann-Integral (§7.1)",
             "Partitions, upper and lower sums, the integrability criterion, and the classes of "
             "function it covers — continuous and monotone. The definition is asked for in "
             "words at least as often as it is computed.", []),
            (f"{N}-ch07-hauptsatz", "Hauptsatz und Integrationsregeln (§7.2)",
             "Both parts of the fundamental theorem, then substitution and integration by parts "
             "as its corollaries. Regensburg's Aufgabe 4 is exactly this: state the second "
             "Hauptsatz, state partielle Integration, then derive the second from the first.",
             [f"{N}-ch07-riemann-integral"]),
            (f"{N}-ch07-uneigentliche-integrale", "Uneigentliche Integrale (§7.3)",
             "Integrals over unbounded intervals and of unbounded integrands, defined as limits — "
             "so convergence criteria return in an integral costume.",
             [f"{N}-ch07-hauptsatz"]),
        ],
    },
]

# The existing unit is kept, not deleted: it holds the two things that are not
# a chapter — the method calibration that has to happen once before Chapter 1,
# and the Analysis-only retrieval and timed transfer that only makes sense once
# the chapters exist. Its three surviving stage ids keep their relative order,
# so the plan importer's ordering check sees an expansion, not a reshuffle.
TRANSFER_UNIT = {
    "unit_id": OLD_UNIT,
    "order": 108,
    "title": "Analysis — calibration, retrieval and timed transfer",
    "pages": None,
    "scope": (
        "The two Analysis sessions that are not a script chapter. Calibration owns the course "
        "contract (script pp. iv-vii), the exam boundary, and the cold diagnostic that decides "
        "which chapters need which support. Retrieval owns mixed Analysis-only practice, the HU "
        "WV set under exam conditions, the scope-filtered external Klausuren, and the "
        "theorem-condition ledger. Switching between Analysis and Statistics is rehearsed in "
        "unit-m2-combined-exam-rehearsal, not here. Chapter 8 and every Exkurs stay deferred."
    ),
    "summary": (
        "Everything in the chapter units is learning one chapter; this unit is the two jobs that "
        "cut across all of them. Calibration is run once, before Chapter 1, and answers what "
        "counts as in scope and at what depth. Retrieval is run repeatedly, after chapters are "
        "in place, and is the only session where whole papers are worked cold and timed."
    ),
    "nodes": [
        (f"{N}-calibrate", "Calibrate the script-led method and the exam boundary",
         "Read the course contract and fix the three depths it defines — Wiederholung required, "
         "Ausflug at overview depth, Exkurs out of scope — then run a cold diagnostic so the "
         "chapter sessions can be entered at the right level rather than uniformly from zero.",
         []),
        (f"{N}-anx", "Analysis-only retrieval and timed transfer",
         "Mixed retrieval across all seven chapters, the HU WV set at its stated 30-45 minutes "
         "per task, scope-filtered external Klausuren under exam conditions, and a "
         "theorem-condition ledger that records which hypotheses were dropped.",
         [f"{N}-calibrate"]),
        (f"{N}-exkurse", "Deferred – Chapter 8 and the non-exam Exkurse",
         "The explicit deferral ledger: script Chapter 8 in full, and every section labelled "
         "Exkurs. Held as a named boundary so a deferred topic is never re-discovered as a gap, "
         "and so the decision can be revisited if the lecturer changes scope.",
         [f"{N}-calibrate"]),
    ],
}

ALL_UNITS = CHAPTERS + [TRANSFER_UNIT]


# --------------------------------------------------------------------------
# The material menu, re-cut per chapter.
#
# SOURCES holds what is true of a source everywhere in this module (its format,
# how deep it goes, how it stands to exam scope, where its file lives). ROUTES
# holds what is true of it *for one chapter*: which nodes it reaches, at which
# page, and the angle that makes it worth opening for that chapter rather than
# another. Every locator below was read out of the PDF on 2026-08-29 — outlines
# and printed tables of contents — except where the entry says otherwise.
# --------------------------------------------------------------------------

SOURCES = {
    "source-analysis-skript": dict(fmt="course-material", depth="course-aligned",
                                   scope="current"),
    "source-analysis-skript-hu": dict(sid="source-analysis-skript", fmt="exercise",
                                      depth="practice", scope="current"),
    "source-analysis-skript-beweise": dict(sid="source-analysis-skript", fmt="course-material",
                                           depth="course-aligned", scope="current"),
    "source-fritzsche-trainingsbuch": dict(fmt="exercise", depth="practice",
                                           scope="complementary"),
    "source-forster-wessoly": dict(fmt="exercise", depth="practice", scope="complementary"),
    "source-deitmar-uebungsbuch": dict(fmt="exercise", depth="practice", scope="complementary"),
    "source-analysis-drill-blaetter-extern": dict(fmt="exercise", depth="practice",
                                                  scope="complementary"),
    "source-analysis-klausuren-extern": dict(fmt="exam", depth="practice",
                                             scope="complementary"),
    "source-analysis-klausuren-tum": dict(sid="source-analysis-klausuren-extern", fmt="book",
                                          depth="practice", scope="complementary"),
    "source-analysis-grundlagen-handouts": dict(fmt="documentation", depth="orientation",
                                                scope="complementary"),
    "source-ableitinger-musterloesungen": dict(fmt="solutions", depth="practice",
                                               scope="complementary"),
    "source-professor-leonard": dict(fmt="video", depth="intuition", scope="complementary"),
    "source-3b1b-essence-of-calculus": dict(fmt="video", depth="intuition",
                                            scope="complementary"),
    "source-strang-calculus": dict(fmt="book", depth="intuition", scope="complementary"),
    "source-mit-18100a": dict(fmt="course", depth="derivation", scope="optional"),
    "source-abbott-understanding-analysis": dict(fmt="book", depth="derivation",
                                                 scope="complementary"),
    "source-grieser-analysis1": dict(fmt="book", depth="derivation", scope="complementary"),
    "source-lebl-basic-analysis": dict(fmt="book", depth="derivation", scope="complementary"),
    # depth/scope for the five below stay `unassessed`/`unevaluated`: the 2026-08-22
    # fix deliberately separated locating a source (a fact an operator may record)
    # from judging it (a contextual evaluation that needs review — CLAUDE.md §4).
    # This pass sharpened their locators to chapter level and left the judgment open.
    "source-mfnf-analysis1": dict(fmt="book", depth="unassessed", scope="unevaluated"),
    "source-ross-elementary-analysis": dict(fmt="book", depth="unassessed", scope="unevaluated"),
    "source-labs-schreyer-mathe-informatiker": dict(fmt="book", depth="unassessed",
                                                    scope="unevaluated"),
    "source-thomas-calculus": dict(fmt="book", depth="unassessed", scope="unevaluated"),
    "source-stewart-calculus": dict(fmt="book", depth="unassessed", scope="unevaluated"),
    "source-velleman-how-to-prove-it": dict(fmt="book", depth="unassessed", scope="unevaluated"),
    "source-ohlbach-eisinger-beweise": dict(fmt="book", depth="unassessed", scope="unevaluated"),
}

VAULT = {
    "source-fritzsche-trainingsbuch": "material://source-fritzsche-trainingsbuch/fritzsche.pdf",
    "source-forster-wessoly": "material://source-forster-wessoly/forster-wessoly.pdf",
    "source-deitmar-uebungsbuch": "material://source-deitmar-uebungsbuch/deitmar.pdf",
    "source-ableitinger-musterloesungen":
        "material://source-ableitinger-musterloesungen/ableitinger.pdf",
    "source-abbott-understanding-analysis":
        "material://source-abbott-understanding-analysis/abbott.pdf",
    "source-grieser-analysis1": "material://source-grieser-analysis1/grieser.pdf",
    "source-lebl-basic-analysis": "material://source-lebl-basic-analysis/realanal.pdf",
    "source-mfnf-analysis1": "material://source-mfnf-analysis1/MfNF_Analysis-1.pdf",
    "source-ross-elementary-analysis":
        "material://source-ross-elementary-analysis/Ross_Elementary-Analysis_2ed.pdf",
    "source-labs-schreyer-mathe-informatiker":
        "material://source-labs-schreyer-mathe-informatiker/"
        "Labs-Schreyer_Mathematik-fuer-Informatiker.pdf",
    "source-thomas-calculus":
        "material://source-thomas-calculus/Thomas-Calculus_Early-Transcendentals.pdf",
    "source-stewart-calculus": "material://source-stewart-calculus/Stewart.pdf",
    "source-velleman-how-to-prove-it":
        "material://source-velleman-how-to-prove-it/Velleman_How-To-Prove-It.pdf",
    "source-ohlbach-eisinger-beweise":
        "material://source-ohlbach-eisinger-beweise/"
        "Ohlbach-Eisinger_Design-Patterns-fuer-mathematische-Beweise.pdf",
    "source-mit-18100a": "material://source-mit-18100a/mit18_100af20_lec_full2.pdf",
}

ROUTE_ROWS: list[dict] = []


def R(unit, key, title, covers, locator, angle, angle_detail, *, vault=None,
      fmt=None, depth=None, scope=None, rid=None):
    """One material option, for one chapter."""
    spec = SOURCES[key]
    sid = spec.get("sid", key)
    ROUTE_ROWS.append({
        "unit_id": unit,
        "source_id": sid,
        "route_key": key,
        "title": title,
        "covers": [f"{N}-{c}" for c in covers],
        "locator": locator,
        "angle": angle,
        "angle_detail": angle_detail,
        "format": fmt or spec["fmt"],
        "depth": depth or spec["depth"],
        "scope": scope or spec["scope"],
        "vault_path": vault if vault is not None else VAULT.get(sid),
        "id": rid,
    })


# ==========================================================================
# Kapitel 1 — Wiederholung: Grundlagen
# ==========================================================================
C1 = "unit-m2-analysis-ch01"
ALL1 = ["ch01-zahlenmengen", "ch01-induktion", "ch01-beziehungen"]

R(C1, "source-analysis-skript", "unser skript.pdf Kapitel 1 — the scope authority", ALL1,
  f"unser skript.pdf Kapitel 1, {sk(1)}–{sk(6)}; §1.1 Zahlenmengen {sk(2)}, "
  f"§1.2 Vollständige Induktion {sk(2)}, §1.3 Wichtige Beziehungen in der Analysis {sk(5)}",
  "The chapter that defines what 'assumed known' means for this exam, in this examiner's "
  "notation.",
  "Six printed pages, and the whole chapter carries the Wiederholung label — under the course "
  "contract (script p. vii) that means the lecture does not re-teach it and expects it to be "
  "usable. So this route is read differently from every other spine route in the module: not "
  "as instruction but as a checklist of what has to already work. Its practical value is the "
  "notation: §1.3's inequalities are cited by number throughout Chapters 3 to 7, and finding "
  "them here once is cheaper than reconstructing them mid-proof.",
  vault="material://source-analysis-skript/unser skript.pdf"),

R(C1, "source-analysis-skript-hu", "HU Serie 05, Aufgabe 5.1(c) — induction inside a recursion",
  ["ch01-induktion"],
  "ana_inf_serie05.pdf, Übungsaufgabe 5.1 'Rekursionen – am Beispiel der Türme von Hanoi', "
  "part (c): solve the recurrence, or guess the closed form and prove it by induction",
  "The only current HU task that examines induction, and it examines it as a tool rather than "
  "as a topic.",
  "This matters more than its size suggests. The sheet does not set an induction exercise; it "
  "sets a modelling problem and then allows induction as the way to finish it — which is how "
  "induction actually appears in this course and, on the evidence of the external papers, in "
  "the exam. Note the boundary: apart from this part-task there is no current HU practice for "
  "Chapter 1 at all, so everything else on this session is a substitute and is labelled as one.",
  vault="material://source-analysis-skript/ana_inf_serie05.pdf"),

R(C1, "source-fritzsche-trainingsbuch", "Fritzsche §§1.1-1.2 — Mengen von Zahlen, Induktion",
  ALL1,
  "fritzsche.pdf §1.1 Mengen von Zahlen p. 9, §1.2 Induktion p. 17; Lösungen in Kap. 5 Anhang "
  "from p. 253",
  "Explained German solutions at tutorial pace — the gentlest route on this session, and the "
  "one that shows the write-up, not just the answer.",
  "Fritzsche is a Trainingsbuch: each section opens with worked reasoning before the exercises, "
  "and the Anhang solutions are written out in full sentences rather than sketched. For a "
  "Wiederholung chapter that is the right shape — the risk here is not that induction is "
  "unknown but that the written argument is sloppy, and this is the source that models the "
  "written argument. §§1.5-1.6 (Vektoren, komplexe Zahlen, Polynome) go past the script and "
  "are left closed."),

R(C1, "source-forster-wessoly", "Forster/Wessoly §1 Vollständige Induktion", ["ch01-induktion"],
  "forster-wessoly.pdf Aufgaben §1 p. 11; Lösungen §1 p. 68",
  "Terse induction problems in Klausur vocabulary, with complete solutions ten pages of "
  "exercises later.",
  "Forster/Wessoly is the companion volume to the standard German Analysis 1 text, so its "
  "wording is the wording German exam setters grew up on. The solutions are correct and "
  "compressed — which is a feature once the technique is secure and a liability while it is "
  "not. Use it after Fritzsche on this node, not before."),

R(C1, "source-deitmar-uebungsbuch", "Deitmar Kap. 1 — Grundlagen", ALL1,
  "deitmar.pdf Kap. 1 Grundlagen p. 12 (§1.1 Aussagen, §1.2 Mengen, §1.3 Abbildungen, "
  "§1.4 Vollständige Induktion p. 15); Lösungen Kap. 21 p. 130",
  "A third solved bank, held in reserve for when Fritzsche and Forster are spent on this node.",
  "Deitmar's Übungsbuch covers far more than this module (Kap. 8-20 run to measure theory and "
  "complex analysis) and only Kap. 1-7 are in scope at all. Its value on Chapter 1 is volume "
  "of fresh problems with worked Lösungsvorschläge, at a difficulty between Fritzsche and "
  "Forster. Nothing here is a new explanation — reach for it when the technique needs more "
  "repetitions, not when it needs a different account."),

R(C1, "source-analysis-grundlagen-handouts",
  "Mengen und Abbildungen / Relationen handouts", ["ch01-zahlenmengen"],
  "Mengen-und-Abbildungen.pdf (22 pp), Relationen.pdf (9 pp) — targeted subsection only",
  "Prerequisite repair for the set and mapping vocabulary the script assumes from M1 and never "
  "restates.",
  "These are short orientation handouts, not a course. They exist on this session for one "
  "reason: the script's Bezeichnungen section lists the symbols without explaining them, and "
  "if image/preimage, injectivity or an equivalence relation is genuinely rusty, that shows up "
  "later as an inability to read a theorem statement rather than as a Chapter 1 problem. Open "
  "the subsection the diagnostic named and close the file again."),

R(C1, "source-analysis-klausuren-extern",
  "Solved German Klausur tasks on logic, sets and induction",
  ALL1,
  "Marburg_Analysis-I_3-Klausuren-mit-Loesungen.pdf: 1. Klausur A1 (set identities and "
  "inclusion-exclusion), A3 (induction sum formula), A4 (an inequality by completing a square); "
  "2. Klausur A1 (n! ≤ (n/2)^n with proof), A2 (a complex modulus set); Wiederholungsklausur A1 "
  "(binomial identity), A2 (a product-to-sum identity by induction). "
  "Darmstadt_Analysis-I_Probeklausur_mit-Loesungen.pdf: A1 Aussagenlogik, A5 rekursive Folgen "
  "und Induktion. Regensburg_...pdf: A1 (tautology, power set, an induction-like principle, "
  "transitivity) with its 'Häufige Fehler' commentary",
  "Real German exam wording for exactly this chapter, with solutions — and the only place the "
  "graders' commentary on how it is got wrong is written down.",
  "This is the substitute for the missing HU sheet, and it is a good one: Chapter 1 material is "
  "over-represented in the external bank because most Analysis 1 courses open there. Two "
  "cautions. First, spend these on diagnosed gaps rather than as a test — the unsolved papers "
  "held for timed work live on the transfer unit, and a solved paper read early cannot be "
  "un-read. Second, Marburg's Aufgabe 2 (ordered rings) and the complex-number tasks sit past "
  "this script's boundary; work the parts that match §§1.1-1.3 and leave the rest. The "
  "Regensburg 'Häufige Fehler' boxes are the single most useful thing in the folder for this "
  "chapter: they name the wrong moves rather than the right ones."),

R(C1, "source-analysis-klausuren-tum",
  "TUM Ferienkurs Analysis 1 — Kapitel 1 Grundlagen + Übungsaufgaben", ALL1,
  "TUM_Ferienkurs-Analysis-1_Skriptum.pdf: Kap. 1 Grundlagen PDF p. 5 (§1.1 Aussagenlogik, "
  "§1.2 Mengen und Quantoren, §1.4 Beweise PDF p. 9, §1.5 Funktionen und Abbildungen), "
  "Übungsaufgaben PDF p. 17; Anhang A 'Wichtige Hinweise zum Beweisen und Rechnen' PDF p. 82",
  "A compressed German revision script with its own exercise set — built for exactly this "
  "situation, revising a whole Analysis 1 quickly.",
  "This is a Ferienkurs Skriptum, not a Klausur, which is why it is separated from the exam "
  "papers: it is meant to be read and worked, not spent once. It compresses Analysis 1 into 88 "
  "pages, so it is the fastest complete second account available. Two caveats: it is written "
  "for physicists, so §1.6 (komplexe Zahlen) and §1.7 (Gruppen und Körper) reach past this "
  "script; and it carries QR codes to videos that were not checked. Anhang A is worth reading "
  "once regardless of chapter — it is a page on how to write the arguments this exam grades."),

R(C1, "source-velleman-how-to-prove-it",
  "Velleman — Mathematical Induction and the proof strategies behind it",
  ["ch01-induktion", "ch01-zahlenmengen"],
  "Velleman_How-To-Prove-It.pdf Ch 6 Mathematical Induction p. 335 (§6.1 Proof by Mathematical "
  "Induction, §6.2 More Examples p. 343, §6.3 Recursion p. 359, §6.4 Strong Induction p. 371); "
  "Ch 3 Proofs p. 118 for the strategies; Ch 1-2 logic and sets p. 21; solutions to selected "
  "exercises p. 483. Located by the 2026-08-03 coverage audit; no contextual evaluation "
  "registered, so its depth and scope are deliberately left unassessed (CLAUDE.md §4).",
  "The book that teaches induction as a proof strategy rather than a formula, including the "
  "strong-induction and recursion variants the Hanoi task needs.",
  "Routed here for the first time at chapter level: before this pass it carried "
  "`proof-presentation` and a bare page count. §6.3 Recursion is the direct match for HU Serie "
  "05.1, and §6.4 Strong Induction is what a recurrence with two previous terms actually "
  "requires — the script's §3.4 case. It is English, 569 pages, and structured as a course, so "
  "it is a reference to enter at a named section, never a book to read through. Nobody has "
  "assessed it against this exam, which is recorded rather than guessed."),

R(C1, "source-ohlbach-eisinger-beweise",
  "Ohlbach/Eisinger — Beweismuster und vollständige Induktion",
  ["ch01-induktion", "ch01-beziehungen"],
  "Ohlbach-Eisinger_Design-Patterns-fuer-mathematische-Beweise.pdf Kap. 4 Einfache Beweismuster "
  "p. 29 (Fallunterscheidung, Allbeweis, Implikationsbeweis, Existenzbeweis), Kap. 5 Komplexe "
  "Beweismuster p. 50 (Kontraposition, Äquivalenzbeweis, Widerspruchsbeweis, Widerlegung durch "
  "Gegenbeispiel), Kap. 6 Vollständige Induktion p. 71 (Grundmuster p. 73, starke Induktion "
  "p. 80, strukturelle Induktion p. 113). Located by the 2026-08-03 coverage audit; no "
  "contextual evaluation registered, so depth and scope stay unassessed (CLAUDE.md §4).",
  "The German catalogue of proof shapes, written for computer scientists — it names the pattern "
  "a task is asking for, which is the step that usually fails.",
  "Chapter-level routing is new here too. The book's premise is that proofs come in a small "
  "number of reusable patterns, and it gives each one a name, a skeleton and worked instances "
  "in German. That is directly useful for a paper like Regensburg's, whose Aufgabe 1 is four "
  "short 'is this true, justify in one to three sentences' items — every one of which is a "
  "pattern choice. Kap. 7-11 (transfinite ordinals) are outside anything this module needs."),

R(C1, "source-labs-schreyer-mathe-informatiker",
  "Labs/Schreyer — Logik, Beweismethoden, Mengen und Abbildungen", ALL1,
  "Labs-Schreyer_Mathematik-fuer-Informatiker.pdf Teil I Grundlagen p. 21: 'Logik und "
  "Beweismethoden' p. 25 (Beweis durch Widerspruch p. 29, Vollständige Induktion p. 30, "
  "Summen- und Produktzeichen p. 32), 'Mengen und Abbildungen' p. 39, 'Äquivalenzrelationen "
  "und Kongruenzen' p. 55. Located by the 2026-08-03 coverage audit; no contextual evaluation "
  "registered, so depth and scope stay unassessed (CLAUDE.md §4).",
  "A German mathematics-for-CS textbook whose Teil I is precisely the M1 prerequisite block "
  "this chapter assumes.",
  "Its 669 pages were previously the reason it was routed to 'AN.0 prerequisite gap' and "
  "nothing more. Opened at chapter level it turns out to be organised the way this script is: "
  "Teil I is the Grundlagen, Teil II is one-variable Analysis section by section. For Chapter 1 "
  "the relevant span is 30 pages, and it is in German with CS examples, which makes it a closer "
  "match to the lecture's own framing than the English references on this menu."),


# ==========================================================================
# Kapitel 2 — Die reellen Zahlen
# ==========================================================================
C2 = "unit-m2-analysis-ch02"
ALL2 = ["ch02-koerperaxiome", "ch02-anordnung", "ch02-intervalle-betrag",
        "ch02-supremum-infimum", "ch02-vollstaendigkeitsaxiom", "ch02-folgerungen",
        "ch02-potenzen-wurzeln", "ch02-maschinenzahlen"]
CORE2 = ["ch02-supremum-infimum", "ch02-vollstaendigkeitsaxiom", "ch02-folgerungen"]

R(C2, "source-analysis-skript", "unser skript.pdf Kapitel 2 — the scope authority", ALL2,
  f"unser skript.pdf Kapitel 2, {sk(7)}–{sk(40)}; §2.1 Körperaxiome (Wiederholung) {sk(8)}, "
  f"§2.2 Anordnung {sk(9)}, §2.3.1 Intervalle und Betrag {sk(13)}, §2.3.2 Supremum und Infimum "
  f"{sk(15)}, §2.3.3 Vollständigkeitsaxiom {sk(16)}, §2.3.4 Folgerungen {sk(18)}, §2.3.5 "
  f"Potenzen {sk(22)}, §2.3.6 Wurzeln {sk(23)}, §2.4 Ausflug – Maschinenzahlen {sk(26)}",
  "The chapter that installs the one axiom the rest of the script cannot do without, in the "
  "form this examiner states it.",
  "Read §2.3 as the chapter and the rest as its setting. Completeness is stated here in the "
  "supremum form, and every convergence theorem from Chapter 3 onward is either a direct "
  "consequence or reaches it through Bolzano-Weierstraß — so the exact statement, including "
  "which sets it applies to, is worth more than any amount of practice on §2.1. The §2.4 "
  "Ausflug on machine numbers is the chapter's Informatik payoff; the contract puts it at "
  "overview depth, and no other source on this menu covers it at all.",
  vault="material://source-analysis-skript/unser skript.pdf"),

R(C2, "source-analysis-skript-hu",
  "HU Serie 05, Hausaufgabe 5.4 — supremum, infimum, maximum, minimum with proof",
  ["ch02-supremum-infimum", "ch02-intervalle-betrag"],
  "ana_inf_serie05.pdf, Hausaufgabe 5.4 (HA, 10 Punkte): decide boundedness of "
  "B = {1/2^n + (-1)^m : n, m ∈ N_0} and determine sup, inf, max, min with proof. "
  "Related: Übungsaufgabe 7.1 (Heron) on ana_inf_serie07.pdf reaches §2.3.6.",
  "The only current HU task on this chapter, and it is graded — so it is the most reliable "
  "single signal of the expected depth.",
  "Read what the task actually asks: not 'compute the supremum' but 'determine it and prove "
  "your answer', with maximum and minimum asked separately so the sup-versus-max distinction "
  "has to be argued rather than assumed. Its own Tipp routes the solution through monotonicity "
  "and convergence of two auxiliary sequences — that is, it answers a Chapter 2 question with "
  "Chapter 3 machinery, which is exactly the dependency this session should leave in place. "
  "Beyond this one Hausaufgabe there is no current HU practice for Chapter 2; that gap has been "
  "open and unowned since the 2026-08-03 audit.",
  vault="material://source-analysis-skript/ana_inf_serie05.pdf"),

R(C2, "source-fritzsche-trainingsbuch", "Fritzsche §1.3 Vollständigkeit", CORE2 + ["ch02-anordnung"],
  "fritzsche.pdf §1.3 Vollständigkeit p. 25 (with §1.1 Mengen von Zahlen p. 9 for the order "
  "rules); Lösungen in Kap. 5 Anhang from p. 253",
  "Explained German solutions on suprema and completeness, at the pace that makes the "
  "definition's two halves visible.",
  "Fritzsche's treatment is unusual in spending its words on why an upper bound and a least "
  "upper bound are different objects, which is the distinction the HU Hausaufgabe is built on. "
  "The exercises come with fully written solutions in the Anhang, so this is the route that "
  "shows what a supremum proof looks like when it is written out rather than asserted."),

R(C2, "source-forster-wessoly",
  "Forster/Wessoly §§2, 3, 5, 6 — Körper, Anordnung, Vollständigkeit, Wurzeln", ALL2[:-1],
  "forster-wessoly.pdf Aufgaben §2 Die Körperaxiome p. 15, §3 Anordnungsaxiome p. 18, "
  "§5 Das Vollständigkeitsaxiom p. 23, §6 Wurzeln p. 24; Lösungen §2 p. 78, §3 p. 84, "
  "§5 p. 93, §6 p. 101",
  "Section-for-section the closest external match to §§2.1-2.3.6, with solutions, in the "
  "German the exam is written in.",
  "The alignment here is unusually tight: Forster's §2/§3/§5/§6 map onto the script's "
  "§2.1/§2.2/§2.3.3/§2.3.6 almost one to one, including the same ordering of ideas. That makes "
  "this the default drill for the chapter and the reason it is listed before the English texts. "
  "The solutions are terse — they show the argument, not the search for it — so pair a first "
  "attempt with Fritzsche's fuller write-up when one does not come out."),

R(C2, "source-deitmar-uebungsbuch", "Deitmar Kap. 2 — Die reellen Zahlen", ALL2[:-1],
  "deitmar.pdf Kap. 2 Die reellen Zahlen p. 19 (§2.1 Körper, §2.2 Anordnung p. 20, §2.3 "
  "Intervalle und beschränkte Mengen p. 21, §2.4 Dedekind-Vollständigkeit p. 22); "
  "Lösungen Kap. 22 p. 138",
  "Fresh problems on the same four subsections, in reserve once Forster is spent.",
  "One difference worth knowing before opening it: Deitmar states completeness in the "
  "Dedekind-cut form while the script uses the supremum form. The two are equivalent and the "
  "exercises are unaffected, but a definition read here and reproduced in the exam would be in "
  "the wrong vocabulary. Use it for problems, not for the statement."),

R(C2, "source-analysis-drill-blaetter-extern",
  "AS-Ana1 — Aufgabe über Supremum und Infimum, worked in full",
  ["ch02-supremum-infimum"],
  "AS-Ana1.pdf (53 pp): Aufgabe 1.8 'Supremum und Infimum' p. 9 with Lösung 2.8 p. 42; "
  "Aufgabe 1.7 'Abgeschlossenheit' p. 8 with Lösung 2.7 p. 37",
  "One supremum problem solved with every thought step shown, including the false starts — the "
  "opposite of a model solution.",
  "The author's stated intention is to write out what a person actually needs while solving, "
  "not the polished result: sketches, the reasoning that motivates each estimate, and enough "
  "detail to resume the proof once the idea lands. That makes it the right route when the HU "
  "Hausaufgabe 5.4 has been attempted and stalled — it is thirty pages of solution for ten "
  "problems, and Aufgabe 1.8 is the one that matches."),

R(C2, "source-analysis-drill-blaetter-extern",
  "Bestimmt_Scan.pdf — handwritten field and order axioms",
  ["ch02-koerperaxiome", "ch02-anordnung"],
  "Bestimmt_Scan.pdf (12 pp; scanned, weak text layer)",
  "Handwritten axiom manipulation of the kind §2.1 and §2.2 assume and never demonstrate.",
  "A short scanned set on deriving the order rules from the axioms. Its limitation is "
  "mechanical rather than mathematical: the text layer is weak, so it cannot be searched or "
  "excerpted, and it was flagged as such in the 2026-08-03 inventory. Worth a pass only if the "
  "axiom-level manipulation in §2.2 is genuinely unfamiliar; otherwise Forster §2/§3 does the "
  "same job with solutions you can search. The scan has no usable text layer: it cannot be "
  "searched or excerpted and has to be read as images."),

R(C2, "source-mfnf-analysis1", "Mathe für Nicht-Freaks — Supremum und Infimum", CORE2,
  "MfNF_Analysis-1.pdf: 'Einleitung – Was sind reelle Zahlen?' p. 20; 'Supremum und Infimum' "
  "p. 29 (Definition p. 30, uneigentliches Supremum p. 38, 'Supremum und Infimum bestimmen und "
  "beweisen' p. 41, Eigenschaften p. 48). Located by the 2026-08-03 coverage audit; no "
  "contextual evaluation registered, so depth and scope stay unassessed (CLAUDE.md §4).",
  "A German open text with a section devoted specifically to *determining and proving* a "
  "supremum, which is the exact verb the HU Hausaufgabe uses.",
  "This route is new at chapter level: the source previously carried only "
  "foundations/sequences/series and a bare page count. It is a Wikibook, so it is verbose and "
  "assumes nothing, and it splits every idea into its own titled section — which is why it can "
  "offer twelve pages on the single question of how you prove that a number is the supremum. "
  "It is not a substitute for the script's statement of completeness; it is the route for when "
  "the proof technique, not the definition, is what is missing."),

R(C2, "source-abbott-understanding-analysis", "Abbott Ch 1 — The Real Numbers", CORE2,
  "abbott.pdf §1.2 Some Preliminaries p. 18, §1.3 The Axiom of Completeness p. 27, "
  "§1.4 Consequences of Completeness p. 33 (§§1.5-1.6 cardinality and Cantor are past the "
  "script)",
  "The most readable argument in the collection for *why* completeness has to be an axiom at "
  "all, opened by the irrationality of √2.",
  "Abbott opens each chapter with a discussion section whose only job is to make the coming "
  "definition feel necessary, and Chapter 1's is the gap in Q that √2 falls through. If the "
  "completeness axiom reads as an arbitrary extra rule, this is the twenty pages that fix that, "
  "and it is English written for undergraduates rather than for specialists. It is more rigour "
  "than this exam asks for, so it is a reference to enter for one blocked idea, not a parallel "
  "text to read through."),

R(C2, "source-lebl-basic-analysis", "Lebl — Real Numbers", ALL2[:-1],
  "realanal.pdf 'Real Numbers' p. 23: Basic properties p. 23, The set of real numbers p. 29, "
  "Absolute value and bounded functions p. 36, Intervals and the size of R p. 41",
  "The free English text whose section order tracks the script most closely — the structural "
  "second reading.",
  "Lebl builds R in the same sequence the script does: ordered field, then bounded sets and "
  "suprema, then completeness, then absolute value and intervals. That makes it useful in a way "
  "Abbott is not — you can read a script section and its Lebl counterpart side by side and the "
  "arguments line up. Volume II (realanal2.pdf) is multivariable and out of scope entirely."),

R(C2, "source-grieser-analysis1", "Grieser Kap. 2 und Kap. 5 — reelle Zahlen und Vollständigkeit",
  ALL2[:-1],
  "grieser.pdf Kap. 2 'Reelle, rationale und ganze Zahlen' p. 20 (§2.1 Die reellen Zahlen p. 20, "
  "§2.3 vollständige Induktion p. 33, Übungen p. 40); Kap. 5 'Die Vollständigkeit der reellen "
  "Zahlen' p. 74 (§5.1 Das Supremumsaxiom p. 74, §5.2 Potenzen mit rationalen Exponenten p. 79, "
  "§5.3 Das Extremalprinzip p. 83, Übungen p. 87); Lösungen und Hinweise p. 329",
  "The German second voice: same rigour as the English texts, with motivation, and exercises "
  "that carry both hints and solutions.",
  "Grieser separates the number systems (Kap. 2) from completeness (Kap. 5) and puts "
  "combinatorics between them, so it is read by section rather than in order. Two things make "
  "it worth the detour on this chapter: §5.2 derives rational powers from the supremum axiom, "
  "which is the script's §2.3.5-2.3.6 done slowly; and the exercises come with Hinweise as well "
  "as Lösungen, so a stuck problem has an intermediate step between 'nothing' and 'the answer'."),

R(C2, "source-ross-elementary-analysis", "Ross §§3-4 — the set R and the completeness axiom",
  CORE2 + ["ch02-koerperaxiome", "ch02-anordnung"],
  "Ross_Elementary-Analysis_2ed.pdf §3 The Set R of Real Numbers p. 25, §4 The Completeness "
  "Axiom p. 32, §5 The Symbols +∞ and −∞ p. 40; Selected Hints and Answers p. 376. Located by "
  "the 2026-08-03 coverage audit; no contextual evaluation registered, so depth and scope stay "
  "unassessed (CLAUDE.md §4).",
  "Proof-oriented and unusually explicit about which axiom is being used in which step.",
  "Ross numbers his sections rather than chapters and keeps them short, which makes him easy to "
  "enter at a point. §4 is the completeness axiom with the Archimedean property drawn out as an "
  "immediate consequence — the script's §2.3.4. The book has been unassessed against this exam "
  "since it was located; the locator is a fact, the judgement about whether it earns time here "
  "is not, and is left open deliberately."),

R(C2, "source-mit-18100a", "MIT 18.100A — characterizing R and the Archimedean property", CORE2,
  "mit18_100af20_lec_full2.pdf: 'Cantor's Remarkable Theorem and the Rationals' Lack of the "
  "Least Upper Bound Property' p. 9, 'The Characterization of the Real Numbers' p. 13, "
  "'The Archimedian Property, Density of the Rationals, and Absolute Value' p. 16",
  "Full rigour for one blocked distinction — deliberately more than this exam needs.",
  "The rule attached to this source has not changed: it is opened for a single definition that "
  "refuses to make sense, never watched or read through. What is new is that the lecture titles "
  "are now named rather than referred to as 'lectures 7-9'. For Chapter 2 the useful pair is "
  "p. 9 (why Q fails the least-upper-bound property, which is the negative result the axiom "
  "answers) and p. 16 (Archimedean property and density, the script's §2.3.4)."),

R(C2, "source-labs-schreyer-mathe-informatiker", "Labs/Schreyer — Die reellen Zahlen",
  ALL2[:-1],
  "Labs-Schreyer_Mathematik-fuer-Informatiker.pdf Teil II 'Analysis in einer Veränderlichen' "
  "p. 75: 'Die reellen Zahlen' p. 79 (Die Körperaxiome p. 79, Ringe p. 81, Folgerungen aus den "
  "Körperaxiomen p. 81, Die Anordnungsaxiome p. 83, Irrationale Zahlen p. 85); "
  "'Das Vollständigkeitsaxiom' p. 95, 'Quadratwurzeln' p. 100, 'Zur Existenz der reellen "
  "Zahlen' p. 103. Located by the 2026-08-03 coverage audit; no contextual evaluation "
  "registered, so depth and scope stay unassessed (CLAUDE.md §4).",
  "German, written for computer scientists, and structured like the script — the closest match "
  "in framing to the lecture itself.",
  "The 2026-08-03 audit routed this source to 'AN.0 prerequisite gap' because 669 pages made it "
  "look too broad to use. Opened, its Teil II is a complete one-variable Analysis in the same "
  "order as the script, and the Chapter 2 material is a well-marked 25-page span. Note that it "
  "puts the completeness axiom inside its Konvergenz chapter rather than with the field axioms — "
  "a different arrangement from the script, and a reason to take problems from it rather than "
  "structure."),

R(C2, "source-analysis-klausuren-extern",
  "Solved German Klausur tasks on order, suprema and bounded sets",
  ["ch02-supremum-infimum", "ch02-anordnung", "ch02-koerperaxiome"],
  "Marburg_Analysis-I_3-Klausuren-mit-Loesungen.pdf: 1. Klausur A2 (make a ring totally ordered "
  "from a positivity set — the order axioms as axioms), A6 (for which n is a two-index set "
  "bounded, and what are its inf and sup); Regensburg_...pdf A2.1 (if every element of A is "
  "negative, must sup A be negative?) with its 'Häufige Fehler' note that this was widely got "
  "wrong",
  "Exam-shaped supremum questions with solutions, including one that is graded commentary on "
  "the standard mistake.",
  "Regensburg's A2.1 is worth more than its three points suggest: it is the sup-versus-max "
  "confusion set as a true/false with justification, and the printed 'Häufige Fehler' records "
  "that students asserted sup A = 0 for every A ⊂ R_<0. That is the same error the HU "
  "Hausaufgabe 5.4 is built to expose. Marburg's A6 is the closer match for a full written "
  "answer. Both are solved, so spend them on a diagnosed gap rather than as a test."),

R(C2, "source-analysis-klausuren-tum", "TUM Ferienkurs §1.3 — Supremum und Infimum",
  ["ch02-supremum-infimum", "ch02-vollstaendigkeitsaxiom"],
  "TUM_Ferienkurs-Analysis-1_Skriptum.pdf §1.3 Supremum und Infimum PDF p. 8; Kap. 1 "
  "Übungsaufgaben PDF p. 17",
  "The compressed statement plus a matching exercise set, when what is wanted is a fast second "
  "pass rather than a fuller explanation.",
  "Three pages against MfNF's twelve. This is the route for revision — after the definition is "
  "understood once, to check it is still there — rather than for first repair. Its exercises "
  "are grouped at the end of the chapter and carry no separate solutions section, which is the "
  "one thing it does worse than Forster or Fritzsche."),


# ==========================================================================
# Kapitel 3 — Folgen und Konvergenz
# ==========================================================================
C3 = "unit-m2-analysis-ch03"
ALL3 = ["ch03-folgen", "ch03-rekursionen", "ch03-konvergenzkriterien",
        "ch03-rechenregeln", "ch03-bestimmte-divergenz", "ch03-quadratwurzel"]
CORE3 = ["ch03-folgen", "ch03-konvergenzkriterien", "ch03-rechenregeln",
         "ch03-bestimmte-divergenz"]

R(C3, "source-analysis-skript", "unser skript.pdf Kapitel 3 — the scope authority", ALL3,
  f"unser skript.pdf Kapitel 3, {sk(41)}–{sk(79)}; §3.1 Folgen {sk(42)}, §3.2 Exkurs "
  f"Landau-Notation {sk(46)}, §3.3 Ausflug lineare Rekursionsgleichungen {sk(47)}, §3.4 Exkurs "
  f"{sk(52)}, §3.5 Konvergenzkriterien für Folgen {sk(55)}, §3.6 Rechnen mit konvergenten "
  f"Folgen {sk(61)}, §3.7 Bestimmt divergente Folgen {sk(69)}, §3.8 Ausflug Berechnung der "
  f"Quadratwurzel {sk(74)}",
  "The longest exam-bearing chapter in the script, and the one the four chapters after it are "
  "defined in terms of.",
  "Thirty-nine printed pages, of which §§3.5-3.7 carry the exam weight. The chapter's shape is "
  "worth noticing before working it: one definition (§3.5's epsilon-N), then a set of criteria "
  "whose whole purpose is to avoid using it, then an arithmetic (§3.6) that turns limits into "
  "computation. Choosing between the criteria is the graded skill. Two of the four "
  "Exkurs/Ausflug sections are examined anyway through the HU sheets — §3.3 by Serie 05.1 and "
  "§3.8 by Serie 07.1 — so 'Ausflug' here means shallower, not skipped.",
  vault="material://source-analysis-skript/unser skript.pdf"),

R(C3, "source-analysis-skript-hu",
  "HU Serien 05, 06, 07 and Hausaufgabe WV1.1 — the calibrated sequence practice",
  ALL3,
  "ana_inf_serie05.pdf: 5.1 Türme von Hanoi (recursion → §3.3), 5.2 limits from Definition 3.19 "
  "with the ε-N step shown, 5.3 HA (10 P) 1/n^k → 0 from the definition. "
  "ana_inf_serie06.pdf: 6.1 prove Satz 3.25(i) by choosing ε and n_0, 6.2 HA (15 P) the scalar "
  "rule plus √(n+1) − √n by rationalising, 6.3 Häufungspunkte (prove Lemma 3.35 and three "
  "consequences). ana_inf_serie07.pdf: 7.1 Heron (→ §3.8), 7.2 and 7.3 HA (20 P) further "
  "limits, 7.4 Rechenregeln. ana_inf_serieWV.pdf: Hausaufgabe WV1.1 (20 P), parts (a) "
  "Bolzano-Weierstraß, (b) Cauchy sequences converge, (c) three limits",
  "Three full sheets plus one exam-format Hausaufgabe, all in the script's own numbering — the "
  "densest current practice anywhere in the Analysis half.",
  "These sheets are the closest thing to seeing the exam. Notice what they keep asking for: not "
  "the value of a limit but the ε-N argument that establishes it, cited against the script's "
  "numbered definitions and theorems (Definition 3.19, Satz 3.25, Lemma 3.35). Two of the tasks "
  "are the *proofs* of limit laws rather than their application. WV1.1 is explicitly written as "
  "an exam-format question at 30-45 minutes; it belongs to the transfer unit as a timed sitting "
  "and is named here so this chapter's preparation knows what it is preparing for. Work all of "
  "these before opening any external bank: everything else on this menu is a different examiner "
  "asking differently.",
  vault="material://source-analysis-skript/ana_inf_serie05.pdf"),

R(C3, "source-analysis-skript-beweise",
  "kleine_beweise.pdf — the seven Chapter 3 proofs the tutors named",
  ["ch03-konvergenzkriterien", "ch03-rechenregeln", "ch03-bestimmte-divergenz"],
  "kleine_beweise.pdf, section 'Kapitel 3: Folgen und Konvergenz': Lemma 3.21 (uniqueness of "
  "the limit; convergent sequences are bounded), Satz 3.25(i)-(iii) (Grenzwertsätze), Satz 3.30 "
  "including (ii) (Monotonieprinzip), Satz 3.40 (Teilfolgenkriterium), Satz 3.42 (Cauchy "
  "sequences are bounded), Satz 3.43 (Cauchy-Kriterium), Satz 3.49 (limits with definitely "
  "divergent sequences)",
  "A named, bounded list of which Chapter 3 proofs are worth being able to reproduce — with the "
  "authors' own disclaimer that it is not exam intelligence.",
  "This is a two-page handout by student tutors for the SoSe 2025 exam preparation, and it "
  "states plainly that it has no known relation to the exam contents. Treated as what it is — "
  "an experienced reader's shortlist — it solves a real problem: the script says proofs need "
  "not be memorised, which leaves 'then which ones are worth understanding?' unanswered. Seven "
  "results for a thirty-nine-page chapter is a defensible answer. Use it to repair a failed "
  "application, and note that Serie 06.1 asks for one of these (Satz 3.25(i)) as an exercise, "
  "which is corroboration from the sheets themselves.",
  vault="material://source-analysis-skript/kleine_beweise.pdf"),

R(C3, "source-fritzsche-trainingsbuch", "Fritzsche §2.1 Konvergenz", CORE3,
  "fritzsche.pdf §2.1 Konvergenz p. 52; Lösungen in Kap. 5 Anhang from p. 253",
  "The whole convergence idea developed at tutorial pace, with solutions written as prose.",
  "Fritzsche puts sequences, series and function limits in one chapter (Der Grenzwertbegriff), "
  "which mirrors the script's own dependency chain and makes §2.1 read as the beginning of "
  "something rather than an isolated topic. On this chapter it is the first drill to open after "
  "the HU sheets: the explanations are fuller than Forster's and the solutions show the "
  "estimate being constructed, which is precisely the step an ε-N argument gets stuck on."),

R(C3, "source-forster-wessoly", "Forster/Wessoly §§4-6 — Folgen, Vollständigkeit, Wurzeln",
  CORE3 + ["ch03-quadratwurzel"],
  "forster-wessoly.pdf Aufgaben §4 Folgen, Grenzwerte p. 20, §5 Das Vollständigkeitsaxiom "
  "p. 23, §6 Wurzeln p. 24; Lösungen §4 p. 88, §5 p. 93, §6 p. 101",
  "Terse solved problems in the exact vocabulary German Analysis exams are written in.",
  "§4 is the main drill and §5 is where completeness gets used on sequences rather than sets, "
  "which is the join the script makes in §3.5. §6 (Wurzeln) is the natural partner to the "
  "script's §3.8 Heron Ausflug. The solutions assume you can supply the routine algebra; that "
  "is the right level once Fritzsche has been worked and the wrong one before."),

R(C3, "source-deitmar-uebungsbuch", "Deitmar §3.1 Konvergenz", CORE3,
  "deitmar.pdf §3.1 Konvergenz p. 24; Lösungen Kap. 23 p. 142",
  "The third solved bank — fresh problems once Fritzsche and Forster are spent on this node.",
  "Deitmar is deliberately last of the three German exercise books on this chapter, for a "
  "practical reason rather than a quality one: its Kap. 3 is short (six pages of problems) and "
  "its value is that it has not been seen yet. Reach for it when a technique needs more "
  "repetitions and the earlier two banks no longer supply unseen ones."),

R(C3, "source-analysis-drill-blaetter-extern",
  "Kippels 'Grenzwerte von Folgen' — fourteen exercises, each solved on its own page",
  ["ch03-konvergenzkriterien", "ch03-rechenregeln"],
  "Grenzwerte-von-Folgen.pdf (26 pp): Definition des Grenzwertes p. 4 with two worked examples, "
  "Grenzwertlehrsätze p. 8 with three, Übungsaufgaben p. 11-12 (Aufgaben 1-14), Lösungen "
  "p. 13-26, one per page",
  "Volume, at a deliberately gentle level, with a separate full solution for every single task.",
  "This is repetition material, not a new account: fourteen limits of the kind §3.6 is about, "
  "each with a complete worked solution on its own page so nothing is skipped. It is aimed "
  "below university level, which is exactly why it works when the algebra of limits is the "
  "problem rather than the concept. Use after the HU sheets, and stop as soon as the "
  "manipulation is automatic."),

R(C3, "source-analysis-drill-blaetter-extern",
  "auf-2-2 Folgen — monotone and bounded first, with solutions",
  ["ch03-konvergenzkriterien", "ch03-folgen"],
  "auf-2-2_Folgen_Loesungen.pdf (30 pp), Aufgabenkatalog Analysis SoSe 2019: opens on the "
  "monotone-convergence criterion (Aufgabe 1 'Monotone Zahlenfolgen I'), then existence before "
  "value (Aufgaben 4, 5), with Lösungen inline",
  "Organised around the one criterion the script leans on hardest — prove convergence first, "
  "compute the limit second.",
  "Its opening line is the pedagogical claim: the most important convergence criterion is that "
  "monotone bounded sequences converge, and sometimes you must establish convergence before you "
  "can compute anything. That is exactly the structure of the script's recursive-sequence "
  "material and of Marburg's recursion tasks. Thirty pages of German problems with inline "
  "solutions, at university level — the strongest of the seven loose drill sheets for this "
  "chapter."),

R(C3, "source-analysis-drill-blaetter-extern",
  "Loesungen4.pdf — choosing N explicitly for a given epsilon",
  ["ch03-konvergenzkriterien"],
  "Loesungen4.pdf (3 pp), Aufgabe 16: for a_n = (n(n+3) − 4)/(n² − 1), find N with |a_n − 1| < ε "
  "for ε = 1/10, ε = 1/100 and then arbitrary ε > 0, with the full estimate shown",
  "The ε-N definition worked with concrete numbers before the general case — the one move that "
  "makes the definition stop being abstract.",
  "Three pages, one task. It is on this menu because of its structure rather than its size: it "
  "asks for N at two specific tolerances first and only then for arbitrary ε, so the quantifier "
  "order becomes visible instead of memorised. HU Serie 05.2 and 05.3 ask for the general case "
  "directly; if that is where the block is, this is the intermediate step."),

R(C3, "source-analysis-drill-blaetter-extern",
  "AS-Ana1 — Konvergenz von Folgen and Häufungspunkte, worked with the thinking shown",
  ["ch03-konvergenzkriterien", "ch03-folgen"],
  "AS-Ana1.pdf (53 pp): Aufgabe 1.1 'Konvergenz von Folgen' p. 3 with Lösung 2.1 p. 11; "
  "Aufgabe 1.2 'Häufungspunkte' p. 3 with Lösung 2.2 p. 15",
  "Two problems, nine pages of solution — the accumulation-point one is the direct partner to "
  "HU Serie 06.3.",
  "Same author and same principle as the supremum entry on Chapter 2: the solution records the "
  "search, not the polished proof, including the pictures. Serie 06.3 asks four connected "
  "claims about accumulation points and is one of the harder current HU tasks; Aufgabe 1.2 here "
  "is the same material with every step written out."),

R(C3, "source-analysis-drill-blaetter-extern",
  "IngMath2 Kap. 10.1-10.5 — computational sequence technique at volume",
  CORE3,
  "IngMath2_Aufgaben.pdf (312 pp, Voß, TU Hamburg 1991): §10.1 Einführende Beispiele p. 2, "
  "§10.2 Konvergenz von Folgen p. 8, §10.3 Reelle Zahlenfolgen p. 16, §10.4 Cauchysches "
  "Konvergenzkriterium p. 35, §10.5 Folgen in Vektorräumen p. 44 (out of scope)",
  "Engineering-style drill: many exercises, all with solutions, aimed at fluency rather than "
  "at understanding.",
  "This file is the practice workhorse for Chapters 6 and 7, where nothing else covers the "
  "ground; on Chapter 3 it is optional volume. §10.4 is the one worth naming — a whole section "
  "of Cauchy-criterion exercises, which the German exercise books treat in a handful of "
  "problems. §10.5 (sequences in vector spaces) goes past the script and is left closed."),

R(C3, "source-analysis-drill-blaetter-extern",
  "Aufgabensammlung-M1 Aufgabe 1 — five sequences of different types in one task",
  ["ch03-konvergenzkriterien", "ch03-rechenregeln", "ch03-bestimmte-divergenz"],
  "Aufgabensammlung-M1_Loesung.pdf (7 pp), Aufgabe 1: decide convergence and find the limit for "
  "n^((−1)^n), the n-th root of 1 + 1/n, a sum, a product and cos(nπ)",
  "One mixed task where the work is choosing a different tool for each of five sequences — a "
  "method-choice drill rather than a technique drill.",
  "Small, and useful for a specific purpose: every other route on this node groups problems by "
  "the technique that solves them, which quietly removes the decision the exam actually tests. "
  "Here the five parts need five different arguments — unbounded divergence, sandwich, a closed "
  "sum, a telescoping product, and a two-accumulation-point argument — with no signposting. "
  "The solution names the sandwich lemma and Gauß's sum formula at the point it uses them."),

R(C3, "source-mfnf-analysis1",
  "Mathe für Nicht-Freaks — Folgen, Konvergenz, Häufungspunkte und Cauchy-Folgen",
  CORE3,
  "MfNF_Analysis-1.pdf: 'Folgen' p. 51 (Definition p. 52, explizite und rekursive "
  "Bildungsgesetze p. 57); 'Konvergenz und Divergenz' p. 65 (Definition Grenzwert p. 66, "
  "'Konvergenz und Divergenz beweisen' p. 76, Grenzwertsätze p. 94, Sandwichsatz p. 104, "
  "Monotoniekriterium p. 107, 'Konvergenzbeweise rekursiver Folgen' p. 109); 'Häufungspunkte "
  "und Cauchy-Folgen' p. 115 (Teilfolgen p. 116, Bolzano-Weierstraß p. 129, bestimmte Divergenz "
  "p. 134, Cauchy-Folgen p. 145). Located by the 2026-08-03 coverage audit; no contextual "
  "evaluation registered, so depth and scope stay unassessed (CLAUDE.md §4).",
  "A hundred German pages on this chapter alone, split into sections that are named after the "
  "*task* — 'prove convergence', 'prove convergence of a recursive sequence' — not the theory.",
  "The section titles are the reason this route is worth its length. Where the script has one "
  "§3.5, this has separate treatments of proving convergence, proving divergence, the sandwich "
  "argument, the monotone criterion and recursive sequences, each with worked examples. It is "
  "the most complete free German account available for the chapter with the heaviest HU load. "
  "It is also verbose and nobody has yet judged it against this exam — the locator is recorded, "
  "the evaluation is not."),

R(C3, "source-abbott-understanding-analysis", "Abbott Ch 2 — Sequences and Series", CORE3,
  "abbott.pdf §2.2 The Limit of a Sequence p. 54, §2.3 The Algebraic and Order Limit Theorems "
  "p. 61, §2.4 The Monotone Convergence Theorem p. 68, §2.5 Subsequences and Bolzano-Weierstrass "
  "p. 74, §2.6 The Cauchy Criterion p. 78 (§2.7 onward is series — Chapter 4's session)",
  "The clearest available answer to why the ε-N definition has the shape it does, rather than "
  "how to apply it.",
  "Abbott's §2.2 spends its pages on the logical structure of the definition — the order of the "
  "quantifiers, and why the game of 'given ε, produce N' is the right formalisation of "
  "approaching a value. That is the specific thing that makes the definition finally readable "
  "for most people, and no drill sheet supplies it. Rule from its record, unchanged: one book "
  "per stuck idea, not a parallel course."),

R(C3, "source-lebl-basic-analysis", "Lebl — Sequences and Series", CORE3,
  "realanal.pdf 'Sequences and Series' p. 51: Sequences and limits p. 51, Facts about limits "
  "of sequences p. 61, Limit superior, limit inferior, and Bolzano–Weierstrass p. 73, Cauchy "
  "sequences p. 84",
  "The structural twin of the script's §§3.5-3.7, in English, free, and with the same ordering.",
  "Where Abbott motivates, Lebl mirrors: the four sections listed here correspond almost "
  "exactly to the script's convergence criteria, limit arithmetic, subsequences and Cauchy "
  "material, in that order. That makes it the route for a second pass over the same argument "
  "rather than a different account of it — useful when a script proof is followable but not yet "
  "reconstructable."),

R(C3, "source-grieser-analysis1", "Grieser Kap. 7 — Konvergenz von Folgen", CORE3,
  "grieser.pdf Kap. 7 'Konvergenz von Folgen' p. 97: §7.2 Definition der Konvergenz p. 99, "
  "§7.3 Konvergenz, algebraische Operationen und Anordnung p. 103, §7.4 Der Grenzwert "
  "»unendlich« p. 106, §7.5 Beispiele und Strategien zur Grenzwertberechnung p. 110, "
  "§7.6 Konvergenz und Vollständigkeit p. 116, Übungen p. 124; Lösungen und Hinweise p. 329",
  "German rigour with a section explicitly devoted to *strategies* for computing limits, and "
  "exercises that carry hints before answers.",
  "§7.5 is the reason this route is here rather than any other German text: it is six pages of "
  "worked strategy — which manipulation to try, in what order — for exactly the limits §3.6 "
  "sets. §7.4 covers definite divergence, the script's §3.7, which several of the other "
  "references treat only in passing."),

R(C3, "source-ross-elementary-analysis", "Ross §§7-12 — sequences, in numbered short sections",
  CORE3,
  "Ross_Elementary-Analysis_2ed.pdf §7 Limits of Sequences p. 45, §8 A Discussion about Proofs "
  "p. 51, §9 Limit Theorems for Sequences p. 57, §10 Monotone Sequences and Cauchy Sequences "
  "p. 68, §11 Subsequences p. 78, §12 limsup's and liminf's p. 90; Selected Hints and Answers "
  "p. 376. Located by the 2026-08-03 coverage audit; no contextual evaluation registered, so "
  "depth and scope stay unassessed (CLAUDE.md §4).",
  "Short numbered sections, one idea each — and §8 is a discussion about how these proofs are "
  "written, placed deliberately between the definition and the theorems.",
  "The §8 placement is the distinctive thing: Ross interrupts the mathematics after the first "
  "ε-N definition to talk about proof writing, which is the same diagnosis the script's own "
  "'you need not reproduce proofs' contract makes from the other direction. Sections are three "
  "to twelve pages, so it is easy to enter at a point. Unassessed against this exam."),

R(C3, "source-labs-schreyer-mathe-informatiker",
  "Labs/Schreyer — Konvergenz, mit Landau-Notation und Quadratwurzeln am selben Ort",
  ALL3,
  "Labs-Schreyer_Mathematik-fuer-Informatiker.pdf 'Konvergenz' p. 89: Folgen p. 89, "
  "'Beispiele für Folgen in der Informatik' p. 94, 'Landau–Symbole (O– und o–Notation)' p. 94, "
  "'Aufwandsanalyse der Multiplikation' p. 95, Das Vollständigkeitsaxiom p. 95, Quadratwurzeln "
  "p. 100, Der Satz von Bolzano–Weierstrass p. 105. Located by the 2026-08-03 coverage audit; "
  "no contextual evaluation registered, so depth and scope stay unassessed (CLAUDE.md §4).",
  "The only source on this menu that puts sequences, Landau notation and square-root iteration "
  "in the same chapter — the same three things the script's Chapter 3 puts together.",
  "This is the discovery of the 2026-08-29 pass. The script's Chapter 3 is unusual in "
  "interleaving pure convergence with two Informatik excursions (§3.2 Landau-Notation, §3.8 "
  "Heron), and every English reference on this menu drops both. Labs/Schreyer keeps them: "
  "O-notation and a running-time analysis sit inside the Konvergenz chapter, and Quadratwurzeln "
  "follows the completeness axiom, which is the script's own §2.3.6 → §3.8 arc. For §3.2 in "
  "particular it is the only route here at all — and §3.2 is an Exkurs, so this is offered for "
  "the Algorithmen-2 overlap rather than for the exam."),

R(C3, "source-mit-18100a", "MIT 18.100A — convergence, the squeeze theorem, Bolzano-Weierstrass",
  ["ch03-konvergenzkriterien", "ch03-rechenregeln"],
  "mit18_100af20_lec_full2.pdf: 'Convergent Sequences of Real Numbers' p. 24, 'The Squeeze "
  "Theorem and Operations Involving Convergent Sequences' p. 27, 'Limsup, Liminf, and the "
  "Bolzano-Weierstrass Theorem' p. 31, 'The Completeness of the Real Numbers and Basic "
  "Properties of Infinite Series' p. 35",
  "Full rigour for one blocked definition — the permitted window for this chapter, named "
  "lecture by lecture.",
  "The record's rule stands: opened for a single definition that refuses to make sense, never "
  "read through. What changed on 2026-08-29 is that the lectures are named rather than "
  "numbered, so the right one can be found without paging. Note that p. 35 spans the Chapter "
  "3/Chapter 4 boundary — it derives the basic series facts from completeness, which is the "
  "join the script makes at the start of its Chapter 4."),

R(C3, "source-ableitinger-musterloesungen",
  "Ableitinger 6.2 und 6.3 — Musterlösungen für Konvergenz und Cauchyfolgen",
  ["ch03-konvergenzkriterien"],
  "ableitinger.pdf §6.2 Konvergenz von Folgen p. 61, §6.3 Cauchyfolgen p. 64; the compressed "
  "counterparts in §4.2 'Hinweise zum Verfassen komprimierter Musterlösungen' p. 38; "
  "Lösungsvorschläge to Kap. 6 in §11.2 p. 190",
  "Model solutions written to be studied as *writing*, with the solver's decision process "
  "annotated alongside the mathematics.",
  "Ableitinger is a didactics book, not an exercise book: Teil I sets out seven named "
  "sub-processes of solving a task (creating problem awareness, clarifying the options, "
  "getting a grip, checking fit, craft, tricks, structuring commentary) and Teil II shows "
  "worked Analysis solutions with those sub-processes marked. Before this pass it was routed "
  "only to the transfer unit with the locator 'One example matching the diagnosed error'. It is "
  "now routed per chapter, because §6.2 and §6.3 are Chapter 3's material specifically. Read a "
  "solution here after writing your own, to compare the presentation rather than the answer."),

R(C3, "source-analysis-klausuren-extern",
  "Solved German Klausur tasks on sequences, recursion and Cauchy",
  CORE3,
  "Marburg_Analysis-I_3-Klausuren-mit-Loesungen.pdf: 1. Klausur A7 (two quotient sequences with "
  "competing exponentials), A8 (a recursive sequence — show it converges, then find the limit); "
  "2. Klausur A3 (three limits incl. √(k²+3k) − k), A4 (recursive, with well-definedness asked "
  "first), A5 (show a given sequence is Cauchy by estimating a_{k+1} − a_k); "
  "Wiederholungsklausur A3, A4. Darmstadt_...pdf A2 (Grenzwerte konkreter Folgen), A5 (rekursive "
  "Folgen und Induktion). Regensburg_...pdf A2.2 (negate convergence correctly), A2.3 (does "
  "e^(1/n²) converge)",
  "German exam wording for the exact three shapes this chapter is examined in — compute, "
  "recursion, and negate the definition — all with solutions.",
  "The recursion tasks are the ones to notice. Marburg's A8 and 2. Klausur A4 both ask for "
  "well-definedness and boundedness before the limit, which is the same order the script's §3.5 "
  "monotone criterion imposes and the same order HU Serie 07.1 uses on Heron. Regensburg's "
  "A2.2 is a different and rarer test: it prints a wrong negation of convergence and asks "
  "whether it holds, with a printed note that saying 'the negation looks different' was not "
  "accepted. That is a quantifier-handling check no drill sheet on this menu supplies."),

R(C3, "source-analysis-klausuren-tum", "TUM Ferienkurs Kap. 2 Folgen + Übungsaufgaben", CORE3,
  "TUM_Ferienkurs-Analysis-1_Skriptum.pdf: Kap. 2 Folgen PDF p. 19 (§2.1 Konvergenz & "
  "Cauchy-Konvergenz, §2.2 Monotonie, Häufungspunkte und Rechenregeln PDF p. 21), "
  "Übungsaufgaben PDF p. 25; Anhang B 'Ausführliches Beispiel zu einem ε-Beweis' PDF p. 84",
  "The whole chapter in six pages plus exercises — and one fully worked ε-proof kept as a "
  "separate appendix.",
  "Anhang B is the reason to open this file for Chapter 3 even if the main text is too "
  "compressed to learn from: it is a single ε-argument written out at length, with the "
  "scratch-work that produces the choice of N shown before the clean version. That is the "
  "artifact this chapter's HU tasks keep asking to be produced, and it is the only worked "
  "example of it in the Klausur folder."),

R(C3, "source-professor-leonard", "Professor Leonard — Calculus 2, sequences",
  ["ch03-folgen", "ch03-konvergenzkriterien", "ch03-rechenregeln"],
  "Professor Leonard, Calculus 2: the sequences block (sequences, convergence, monotone and "
  "bounded). Topic-matched selection from the source record's own list; no local copy, so the "
  "selection is by topic rather than by timestamp.",
  "Slow blackboard teaching that does the computation in full where the script compresses it to "
  "a result. The angle is pace.",
  "Conditional, not scheduled: reach for it when a cold diagnostic shows a block on this "
  "chapter, take the one topic, and stop. The reason it earns a place at all is that the "
  "script's §3.6 states limit rules and applies them in one or two lines, while this works "
  "every intermediate step aloud — which is what an actual gap in the algebra needs. It is a "
  "US calculus course, so it never reaches the ε-N material the HU sheets grade; for that, the "
  "route is Abbott or MIT 18.100A, not this."),

R(C3, "source-thomas-calculus", "Thomas §10.1 Sequences", ["ch03-folgen", "ch03-rechenregeln"],
  "Thomas-Calculus_Early-Transcendentals.pdf §10.1 Sequences p. 586 (1205 pp). Located by the "
  "2026-08-03 coverage audit; no contextual evaluation registered, so depth and scope stay "
  "unassessed (CLAUDE.md §4).",
  "A large computational calculus text — reserve volume for routine limit calculations, with "
  "no ε-N content.",
  "Named at section level for the first time. Thomas treats sequences in one section as a "
  "prelude to series, at a computational level well below the script's; that makes it a "
  "fallback for calculation practice and useless for the proof half of the chapter. It "
  "overlaps almost entirely with Stewart §11.1 — there is no reason to open both."),

R(C3, "source-stewart-calculus", "Stewart §11.1 Sequences", ["ch03-folgen", "ch03-rechenregeln"],
  "Stewart.pdf §11.1 Sequences p. 726 (1404 pp). Located by the 2026-08-03 coverage audit; no "
  "contextual evaluation registered, so depth and scope stay unassessed (CLAUDE.md §4).",
  "The same computational level as Thomas, with more worked examples and a fuller exercise set.",
  "Kept on the menu as the alternative to Thomas rather than in addition to it: the two books "
  "cover this section identically. Pick one when routine calculation is what is missing, and "
  "neither when the missing thing is the definition."),


# ==========================================================================
# Kapitel 4 — Reihen
# ==========================================================================
C4 = "unit-m2-analysis-ch04"
ALL4 = ["ch04-reihen", "ch04-konvergenzkriterien", "ch04-absolute-konvergenz",
        "ch04-umordnungen"]
CORE4 = ["ch04-reihen", "ch04-konvergenzkriterien", "ch04-absolute-konvergenz"]

R(C4, "source-analysis-skript", "unser skript.pdf Kapitel 4 — the scope authority", ALL4,
  f"unser skript.pdf Kapitel 4, {sk(80)}–{sk(97)}; §4.1 Reihen {sk(80)}, §4.2 "
  f"Konvergenzkriterien für Reihen {sk(84)}, §4.3 Absolute Konvergenz {sk(88)}, §4.4 Ausflug "
  f"Umordnungen {sk(92)}, §4.5 Exkurs Produktreihen {sk(95)}",
  "The shortest exam-bearing chapter and the most procedural — eighteen pages that amount to a "
  "decision tree.",
  "Chapter 4 introduces no new notion of convergence: a series is the sequence of its partial "
  "sums, so everything from §3.5 still applies. What it adds is a set of criteria and, "
  "implicitly, the problem of choosing among them. Build the decision tree from §4.2 with the "
  "script's own theorem numbers on it — the hypotheses are what the exam checks, and §4.3's "
  "absolute-versus-conditional distinction is the hypothesis that §4.4's rearrangement result "
  "turns on. §4.5 is an Exkurs and out of scope.",
  vault="material://source-analysis-skript/unser skript.pdf"),

R(C4, "source-analysis-skript-hu",
  "HU Serie 08 (8.1-8.3) and Hausaufgabe WV1.3 — the calibrated series practice", CORE4,
  "Pd3szO-ana_inf_serie08.pdf (Serie 08 exists only under this download-mangled name): "
  "8.1 compute three series sums (geometric, alternating geometric, and 1/(4k²−1) by "
  "telescoping), 8.2 decide convergence for four series including a case split on x, "
  "8.3 HA (20 P) one sum plus three convergence decisions. ana_inf_serieWV.pdf: Hausaufgabe "
  "WV1.3 (20 P) — prove that Σ(−11)^n/3^(n²+1) converges four times over, by the ratio, root, "
  "comparison and Leibniz criteria in turn",
  "Current, graded, and WV1.3 is the clearest statement anywhere of what this chapter is "
  "actually testing.",
  "WV1.3 is the single most informative task in the Analysis half of the local HU set. It takes "
  "one series and demands it be settled with four different criteria — which only makes sense "
  "as a test of whether each criterion's hypotheses can be checked and stated, since the answer "
  "is never in doubt. Build the §4.2 decision tree against it. Serie 08.2(iv) is the other one "
  "to notice: it needs a case split on the parameter before any criterion applies, which is the "
  "step that gets skipped. 8.4 belongs to Chapter 5, not here.",
  vault="material://source-analysis-skript/Pd3szO-ana_inf_serie08.pdf"),

R(C4, "source-analysis-skript-beweise",
  "kleine_beweise.pdf — the two Chapter 4 proofs the tutors named",
  ["ch04-konvergenzkriterien"],
  "kleine_beweise.pdf, section 'Kapitel 4: Reihen': Satz 4.12 (Majorantenkriterium), "
  "Satz 4.15 (Wurzelkriterium)",
  "Two proofs for the whole chapter — the shortest per-chapter list in the handout, and worth "
  "reading as a statement about where the value is.",
  "The tutors picked comparison and root, and nothing else. That is consistent with how the "
  "criteria relate: comparison is the one the others are proved from, and the root criterion is "
  "the one whose proof is a direct comparison with a geometric series. Understanding those two "
  "arguments makes the rest of §4.2 a corollary rather than a list to memorise. Same "
  "disclaimer as always — the authors state the handout has no known relation to exam contents.",
  vault="material://source-analysis-skript/kleine_beweise.pdf"),

R(C4, "source-fritzsche-trainingsbuch", "Fritzsche §2.2 Unendliche Reihen", CORE4,
  "fritzsche.pdf §2.2 Unendliche Reihen p. 68; Lösungen in Kap. 5 Anhang from p. 253",
  "Series presented as the continuation of the sequence chapter it belongs to, with solutions "
  "written out as prose.",
  "Fritzsche keeps sequences (§2.1), series (§2.2) and function limits (§2.3) in one chapter "
  "called Der Grenzwertbegriff, which is the same dependency the script builds. On this chapter "
  "that framing pays: the partial-sum definition stops being a formality when the previous "
  "section is fresh. First drill after the HU sheets."),

R(C4, "source-forster-wessoly",
  "Forster/Wessoly §7 Konvergenzkriterien für Reihen und §8 Die Exponentialreihe", CORE4,
  "forster-wessoly.pdf Aufgaben §7 Konvergenzkriterien für Reihen p. 26, §8 Die Exponentialreihe "
  "p. 30; Lösungen §7 p. 106, §8 p. 114",
  "A whole section of criterion-selection problems in the German the exam is set in, with "
  "solutions.",
  "§7 is the closest external match to the script's §4.2 and the natural drill for the decision "
  "tree. §8 is included deliberately even though the exponential series belongs to the script's "
  "§5.6: it is the worked example that shows a series *defining* a function, which is the join "
  "Chapter 5 will need and which no other Chapter 4 route makes."),

R(C4, "source-deitmar-uebungsbuch", "Deitmar §3.2 Reihen", CORE4,
  "deitmar.pdf §3.2 Reihen p. 29; Lösungen Kap. 23 p. 142",
  "Fresh criterion problems in reserve, once Forster §7 is spent.",
  "Two pages of problems with worked Lösungsvorschläge. Its role on this chapter is unchanged "
  "from Chapter 3 — unseen repetitions rather than a different explanation — and its Kap. 7.2 "
  "(Potenzreihen) matches the script's §5.8 Exkurs and is therefore left closed."),

R(C4, "source-analysis-drill-blaetter-extern",
  "auf-2-3 Reihen — the Cauchy criterion for series, worked in German",
  CORE4,
  "auf-2-3_Reihen_Loesungen.pdf (20 pp), Aufgabenkatalog Analysis SoSe 2019: opens with "
  "Aufgabe 1 'Cauchy Konvergenzkriterium', with Lösungen inline",
  "The one drill that makes the sequence-to-series translation explicit instead of assuming it.",
  "Its first task is not a computation: it prints the Cauchy criterion for sequences and for "
  "series and asks for the relationship in words. That is exactly the step the script performs "
  "silently when it defines a series as its partial sums, and it is the step that, if left "
  "implicit, makes the whole chapter feel like a new set of rules. Aufgabe 1 asks for the "
  "sequence form and the series form side by side and for the connection in your own words. "
  "Twenty pages, university level, solutions inline."),

R(C4, "source-analysis-drill-blaetter-extern",
  "KIT-Blatt and Tutorium-Musterlösung — criterion practice with an exam-write-up note",
  ["ch04-konvergenzkriterien", "ch04-absolute-konvergenz"],
  "KIT_Blatt-Reihen.pdf (4 pp; 6. Übungsblatt, Aufgaben mit Lösungen — e.g. Aufgabe 26 on "
  "Σ(−1)^(k+1)·k/2^k); Tutorium-Musterloesung-Reihen.pdf (6 pp; the rules for combining series, "
  "the necessary null-sequence condition, the list of series 'die jeder kennen muss', and a "
  "'Hinweis für die Klausur' on what need not be written out)",
  "Short, dense criterion practice — and the Tutorium sheet is the only source here that says "
  "which steps a marker expects to *see*.",
  "The Tutorium sheet is worth its six pages for one paragraph: it states that the null-sequence "
  "condition need not be mentioned explicitly except for the Leibniz criterion, and that a "
  "non-null term is a trivial divergence argument that saves working through any criterion. "
  "That is presentation advice of the kind the script's contract does not give, and it converts "
  "directly into time in a three-hour paper. The KIT sheet is four pages of standard tasks with "
  "solutions."),

R(C4, "source-analysis-drill-blaetter-extern",
  "AS-Ana1 — geometrische Reihen, Teleskopreihen, Cauchy-Produkt, Koch'sche Schneeflocke",
  ALL4,
  "AS-Ana1.pdf (53 pp): Aufgabe 1.3 'Beispiele von geometrischen Reihen' p. 5 (Lösung p. 20), "
  "1.4 'Das Cauchy-Produkt von Reihen' p. 5 (Lösung p. 23 — matches the §4.5 Exkurs), "
  "1.6 'Teleskopreihen' p. 8 (Lösung p. 33), 1.9 'Die Koch'sche Schneeflocke' p. 10 "
  "(Lösung p. 45)",
  "The two series types that can actually be summed, worked at length — plus one geometric "
  "application that is a real object rather than an exercise.",
  "Geometric and telescoping are the only families the exam can ask for a *value* from, and HU "
  "Serie 08.1 asks for exactly those three. This is the route that works them slowly. The Koch "
  "snowflake task is the one place in the whole Analysis collection where a geometric series "
  "answers a question someone might actually ask. Aufgabe 1.4 covers the Cauchy product, which "
  "is the script's §4.5 Exkurs — worked here if the boundary is ever revisited, not needed for "
  "the exam."),

R(C4, "source-analysis-drill-blaetter-extern",
  "IngMath2 §10.6 Konvergenzkriterien für Reihen", CORE4,
  "IngMath2_Aufgaben.pdf §10.6 Konvergenzkriterien für Reihen p. 47-74 (27 pages of solved "
  "exercises)",
  "Twenty-seven pages of criterion drill with solutions — the largest single block of series "
  "practice available.",
  "Volume, when the decision tree is built and what remains is making the choice fast. "
  "Engineering-style and computational: it will not explain why a criterion works, and it does "
  "not need to by the time this route is the right one."),

R(C4, "source-mfnf-analysis1",
  "Mathe für Nicht-Freaks — Reihen und die Konvergenzkriterien, one section per criterion",
  ALL4,
  "MfNF_Analysis-1.pdf: 'Reihen' p. 153 (Begriff der Reihe p. 154, Rechenregeln p. 162, "
  "Teleskopsumme und Teleskopreihe p. 169, Geometrische Reihe p. 173, Harmonische Reihe p. 177, "
  "Absolute Konvergenz p. 179, Umordnungssatz p. 184); 'Kriterien für Konvergenz von Reihen' "
  "p. 189 (Trivialkriterium p. 190, Majoranten-/Minorantenkriterium p. 193, Wurzelkriterium "
  "p. 199, Quotientenkriterium p. 205, Leibniz-Kriterium p. 216, 'Anwendung der "
  "Konvergenzkriterien' p. 222). Located by the 2026-08-03 coverage audit; no contextual "
  "evaluation registered, so depth and scope stay unassessed (CLAUDE.md §4).",
  "Every criterion in the script's §4.2 gets its own titled section here, and the chapter ends "
  "with a section on choosing between them.",
  "The structure is the value: where the script gives §4.2 as one section, this gives six, and "
  "then adds 'Anwendung der Konvergenzkriterien' — the choosing step, written down as its own "
  "topic. That is the one thing WV1.3 is testing and the one thing most texts leave to "
  "osmosis. It also has separate sections for the harmonic and geometric series, which are the "
  "two comparison series everything else is measured against. German, free, verbose; no "
  "contextual evaluation registered yet."),

R(C4, "source-abbott-understanding-analysis",
  "Abbott §2.7 Properties of Infinite Series and the rearrangement discussion",
  ["ch04-absolute-konvergenz", "ch04-umordnungen", "ch04-konvergenzkriterien"],
  "abbott.pdf §2.1 Discussion: Rearrangements of Infinite Series p. 51, §2.7 Properties of "
  "Infinite Series p. 83, §2.8 Double Summations and Products of Infinite Series p. 91 "
  "(matches the §4.5 Exkurs)",
  "The book opens its whole sequences-and-series chapter on the rearrangement paradox, which "
  "makes the absolute-convergence hypothesis feel earned rather than technical.",
  "Abbott's §2.1 shows a conditionally convergent series being rearranged to a different sum "
  "before any theory is developed, and then spends the chapter earning the right to explain it. "
  "For the script's §4.3-§4.4 that is the ideal order — the script states absolute convergence "
  "as a definition and rearrangement as an Ausflug, which leaves the connection available but "
  "not felt. Four pages of reading for the discussion; the rest as needed."),

R(C4, "source-lebl-basic-analysis", "Lebl — Series and More on series", CORE4,
  "realanal.pdf Series p. 87, More on series p. 100 (inside 'Sequences and Series' p. 51)",
  "The structural twin again: criteria in the same order as §4.2, in English, free.",
  "Used the same way as on Chapter 3 — a second pass over the same argument rather than a "
  "different account. Its 'More on series' section carries absolute convergence and "
  "rearrangement, matching §4.3-§4.4."),

R(C4, "source-grieser-analysis1", "Grieser Kap. 8 — Reihen", CORE4 + ["ch04-umordnungen"],
  "grieser.pdf Kap. 8 'Reihen' p. 128: §8.1 Definition und Beispiele p. 128, §8.2 "
  "Konvergenzkriterien für Reihen p. 133, §8.3 Umordnung von Reihen p. 141, §8.4 Doppelreihen, "
  "Cauchy-Produkt p. 143, Übungen p. 146; Lösungen und Hinweise p. 329",
  "German, rigorous, with hints as well as solutions — and §8.3 covers the Ausflug that most "
  "references skip.",
  "Grieser's Kap. 8 maps onto the script's Chapter 4 section for section, including §8.3 for "
  "the §4.4 Umordnungen Ausflug and §8.4 for the §4.5 Produktreihen Exkurs. Since both of those "
  "are below exam priority, the practical value here is §8.2 plus exercises that come with an "
  "intermediate hint layer."),

R(C4, "source-ross-elementary-analysis", "Ross §14 Series and §15 Alternating Series", CORE4,
  "Ross_Elementary-Analysis_2ed.pdf §14 Series p. 107, §15 Alternating Series and Integral "
  "Tests p. 117; Selected Hints and Answers p. 376. Located by the 2026-08-03 coverage audit; "
  "no contextual evaluation registered, so depth and scope stay unassessed (CLAUDE.md §4).",
  "Two short numbered sections, entered directly, with the alternating case separated out.",
  "Ross's §15 pairs the Leibniz criterion with the integral test. The integral test is not in "
  "the script's §4.2 and is not examinable here — noted so it is recognised as extra rather "
  "than assumed missing from the script."),

R(C4, "source-mit-18100a",
  "MIT 18.100A — absolute convergence, comparison, and the ratio/root/alternating tests",
  CORE4,
  "mit18_100af20_lec_full2.pdf: 'The Completeness of the Real Numbers and Basic Properties of "
  "Infinite Series' p. 35, 'Absolute Convergence and the Comparison Test for Series' p. 39, "
  "'The Ratio, Root, and Alternating Series Tests' p. 43",
  "The criteria derived rather than listed, for the case where a hypothesis makes no sense.",
  "Three consecutive lectures covering exactly §§4.1-4.3. The distinctive thing is p. 35, which "
  "derives the basic series facts *from completeness* — making explicit the dependency the "
  "script carries implicitly from Chapter 2. Still one blocked idea at a time, not a course to "
  "follow."),

R(C4, "source-labs-schreyer-mathe-informatiker", "Labs/Schreyer — Reihen", CORE4 + ["ch04-umordnungen"],
  "Labs-Schreyer_Mathematik-fuer-Informatiker.pdf 'Reihen' p. 113: Definition und erste "
  "Eigenschaften p. 113, Konvergenzkriterien für Reihen p. 115, Umordnung von Reihen p. 120. "
  "Located by the 2026-08-03 coverage audit; no contextual evaluation registered, so depth and "
  "scope stay unassessed (CLAUDE.md §4).",
  "German, CS-framed, and short — the criteria in seven pages, in the same order as §4.2.",
  "The compact German alternative to MfNF's sixty pages on the same material. Use it when the "
  "criteria are known and what is wanted is the German statement to check a write-up against."),

R(C4, "source-ableitinger-musterloesungen",
  "Ableitinger §6.4 — Musterlösung für Konvergenz von Reihen",
  ["ch04-konvergenzkriterien"],
  "ableitinger.pdf §6.4 Konvergenz von Reihen p. 66; Lösungsvorschläge in §11.2 p. 190",
  "One series-convergence solution written with the solver's reasoning annotated beside the "
  "mathematics.",
  "Routed to this chapter for the first time. Read after WV1.3 has been attempted: WV1.3 asks "
  "for four write-ups of the same fact, which makes it the ideal place to compare your "
  "presentation against a model that explains its own choices."),

R(C4, "source-analysis-klausuren-extern",
  "Solved German Klausur tasks on series and convergence criteria", CORE4,
  "Marburg_Analysis-I_3-Klausuren-mit-Loesungen.pdf: 1. Klausur A11 (Σ n!/n^n by the ratio "
  "criterion), A12 (Σ√k·x^k — absolute convergence for |x|<1, divergence for |x|>1); "
  "2. Klausur A6 (disprove: Σa_l convergent and (b_l) bounded ⇒ Σa_l b_l convergent), A7, A8; "
  "Wiederholungsklausur A5, A6, A7. Darmstadt_...pdf A3 (decide convergence for each of "
  "several series). Regensburg_...pdf A2.4. Paderborn_...pdf A2(b) (for which x does "
  "Σ(n+1)x^n converge, and to what), A4(a) (absolutely convergent times bounded)",
  "Exam-shaped criterion selection with solutions — and two papers set the same trap about "
  "'absolutely convergent times bounded'.",
  "Marburg 2. Klausur A6 and Paderborn A4(a) are the same statement with one word changed: "
  "Paderborn's series is absolutely convergent and the claim is true; Marburg's is merely "
  "convergent and the claim is false, with (−1)^l/(l+1) against b_l = (−1)^l as the "
  "counterexample. Working the pair is the sharpest available drill on why §4.3 exists. "
  "Paderborn A2(b) additionally wants the *value*, which needs the derivative trick rather than "
  "a criterion."),

R(C4, "source-analysis-klausuren-tum", "TUM Ferienkurs Kap. 3 Reihen + Übungsaufgaben", CORE4,
  "TUM_Ferienkurs-Analysis-1_Skriptum.pdf: Kap. 3 Reihen PDF p. 26 (§3.1 Konvergenzkriterien "
  "für Reihen PDF p. 27, §3.2 Potenzreihen PDF p. 28 — matches the §5.8 Exkurs), "
  "Übungsaufgaben PDF p. 31",
  "The criteria compressed to two pages with a matching exercise set — a revision pass, not a "
  "first account.",
  "Fast and complete for what it covers. Its §3.2 on power series belongs to the script's §5.8 "
  "Exkurs and is out of scope here; the boundary is worth knowing before working the exercise "
  "set, which does not separate them."),

R(C4, "source-professor-leonard", "Professor Leonard — Calculus 2, series and convergence tests",
  CORE4,
  "Professor Leonard, Calculus 2: the series block (series, convergence tests, alternating "
  "series). Topic-matched selection from the source record's own list; no local copy, so the "
  "selection is by topic rather than by timestamp.",
  "Every criterion worked at blackboard pace with full arithmetic — the pace angle again, "
  "applied to the chapter with the most mechanical content.",
  "Conditional and capped, as always. This chapter is where the pace angle is most defensible: "
  "the criteria are mechanical, the failure is usually in executing the estimate, and a US "
  "calculus course covers the ratio, root, comparison and alternating tests at exactly the "
  "computational level the script assumes. It will not cover absolute-versus-conditional "
  "convergence at §4.3's depth."),

R(C4, "source-thomas-calculus", "Thomas §§10.2-10.6 — series and the convergence tests", CORE4,
  "Thomas-Calculus_Early-Transcendentals.pdf §10.2 Infinite Series p. 598, §10.3 The Integral "
  "Test p. 607, §10.4 Comparison Tests p. 614, §10.5 Absolute Convergence; The Ratio and Root "
  "Tests p. 618, §10.6 Alternating Series and Conditional Convergence p. 624. Located by the "
  "2026-08-03 coverage audit; no contextual evaluation registered, so depth and scope stay "
  "unassessed (CLAUDE.md §4).",
  "One section per test with large exercise sets — reserve computational volume.",
  "Named at section level for the first time. §10.3 (integral test) is not in the script's "
  "§4.2 and is not examinable; the other four sections map onto it directly. Overlaps almost "
  "completely with Stewart §§11.2-11.6, so open one book, not both."),

R(C4, "source-stewart-calculus", "Stewart §§11.2-11.7 — series, the tests, and a strategy section",
  CORE4,
  "Stewart.pdf §11.2 Series p. 739, §11.3 The Integral Test p. 751, §11.4 The Comparison Tests "
  "p. 759, §11.5 Alternating Series p. 764, §11.6 Absolute Convergence and the Ratio and Root "
  "Tests p. 769, §11.7 Strategy for Testing Series p. 776. Located by the 2026-08-03 coverage "
  "audit; no contextual evaluation registered, so depth and scope stay unassessed "
  "(CLAUDE.md §4).",
  "The same coverage as Thomas plus §11.7, which is a section on nothing but choosing the test.",
  "§11.7 is the reason to prefer Stewart over Thomas on this one chapter: a short section whose "
  "entire content is how to decide which test to reach for, which is what WV1.3 examines and "
  "what §4.2 leaves as an exercise for the reader. Everything else here is interchangeable with "
  "Thomas."),


# ==========================================================================
# Kapitel 5 — Differentialrechnung I
# ==========================================================================
C5 = "unit-m2-analysis-ch05"
ALL5 = ["ch05-funktionsgrenzwerte", "ch05-einseitige-grenzwerte", "ch05-stetigkeit",
        "ch05-zwischenwertsatz", "ch05-kompakte-intervalle", "ch05-exponentialfunktion",
        "ch05-gleichmaessige-konvergenz"]
CONT5 = ["ch05-funktionsgrenzwerte", "ch05-einseitige-grenzwerte", "ch05-stetigkeit",
         "ch05-zwischenwertsatz", "ch05-kompakte-intervalle"]

R(C5, "source-analysis-skript", "unser skript.pdf Kapitel 5 — the scope authority", ALL5,
  f"unser skript.pdf Kapitel 5, {sk(98)}–{sk(136)}; §5.1 Grenzwerte bei Funktionen {sk(98)}, "
  f"§5.2 Uneigentliche und einseitige Grenzwerte {sk(102)}, §5.3 Stetige Funktionen {sk(107)}, "
  f"§5.4 Zwischenwertsatz, Umkehrfunktion und Extrempunkte {sk(111)}, §5.5 Besonderheiten "
  f"stetiger Funktionen auf abgeschlossenen, beschränkten Intervallen {sk(121)}, §5.6 "
  f"Exponentialfunktion und Logarithmen {sk(122)}, §5.7 Gleichmäßige Konvergenz von "
  f"Funktionenfolgen {sk(129)}. §5.8 is an Exkurs and is not worked here.",
  "The chapter whose title says derivatives and whose content is continuity — and the last one "
  "with current HU exercises.",
  "Read §5.1 as the hinge of the whole script: it defines the limit of a function through "
  "sequences, which is why Chapter 3 had to come first and why a weak §3.5 shows up here. "
  "§§5.4-5.5 are the three theorems the external papers ask to be *stated* with complete "
  "hypotheses — intermediate value, attained extrema, continuous inverse — and stating them "
  "precisely is worth more marks than any calculation in the chapter. §5.7 is two pages with no "
  "HU sheet behind it, which makes it the easiest thing in the chapter to arrive at the exam "
  "never having practised.",
  vault="material://source-analysis-skript/unser skript.pdf"),

R(C5, "source-analysis-skript-hu",
  "HU Serie 08.4, Serie 09 and Hausaufgaben WV1.2 and WV1.4 — the last calibrated practice",
  CONT5,
  "Pd3szO-ana_inf_serie08.pdf: 8.4 Grenzwerte von Funktionen — compute the limits and prove one "
  "of them twice, once from Definition 5.5 and once from the Folgenkriterium Satz 5.6. "
  "ana_inf_serie09.pdf: 9.1 Stetigkeit, 9.2 Eigenschaften von Grenzwerten von Funktionen, "
  "9.3 HA (20 P) Grenzwerte von Funktionen und Stetigkeit. ana_inf_serieWV.pdf: WV1.2 (20 P), "
  "parts (a) define continuity at a point, (b) the function that is x on Q and −x "
  "elsewhere is continuous only at 0, (c) three limits built on it; WV1.4 (20 P), parts (a) "
  "state the Zwischenwertsatz with complete hypotheses, (b) a unique solution exists, "
  "(c)-(d) the bisection method and its iteration count",
  "The last current HU material in the script's order, and the two WV Hausaufgaben are the "
  "closest thing available to real exam questions on this chapter.",
  "Two things in these sheets are worth reading as instructions rather than tasks. Serie 8.4(a) "
  "asks for one limit proved *both* ways and names the script's Definition 5.5 and Satz 5.6 — "
  "so the sequence criterion is expected to be usable in both directions, not just recognised. "
  "WV1.4 asks for the theorem statement first and the application second, and says "
  "'achten Sie insbesondere auf die korrekte und vollständige Angabe der Voraussetzungen' — "
  "the hypotheses are separately graded. After Serie 09 and the WV set the local HU material "
  "stops; Chapters 6 and 7 have nothing, and that gap has been open since 2026-08-03.",
  vault="material://source-analysis-skript/ana_inf_serie09.pdf"),

R(C5, "source-analysis-skript-beweise",
  "kleine_beweise.pdf — the three Chapter 5 proofs the tutors named",
  ["ch05-funktionsgrenzwerte", "ch05-stetigkeit"],
  "kleine_beweise.pdf, section 'Kapitel 5: Differentialrechnung I': Lemma 5.3 (accumulation "
  "points of a set ⇔ existence of a convergent sequence), Satz 5.20(i) and (ii) written out "
  "explicitly via Satz 3.25 (Rechenregeln stetiger Funktionen), Satz 5.21 (continuity of a "
  "composition)",
  "Three proofs, and the middle one is chosen precisely because it shows Chapter 5 standing on "
  "Chapter 3.",
  "The instruction attached to Satz 5.20 in the handout is 'explizit mittels Satz 3.25 "
  "aufschreiben' — write it out using the limit laws for sequences. That is the dependency this "
  "whole chapter rests on, made into an exercise. Lemma 5.3 is the technical result that makes "
  "the sequence criterion for function limits work at all. Same tutor disclaimer as elsewhere: "
  "no known relation to exam contents.",
  vault="material://source-analysis-skript/kleine_beweise.pdf"),

R(C5, "source-fritzsche-trainingsbuch", "Fritzsche §2.3 Grenzwerte von Funktionen", CONT5,
  "fritzsche.pdf §2.3 Grenzwerte von Funktionen p. 77; Lösungen in Kap. 5 Anhang from p. 253",
  "Function limits presented as the third step of one continuous argument that began with "
  "sequences — the same move the script makes.",
  "By placing §2.3 immediately after series in the same chapter, Fritzsche makes the sequence "
  "criterion feel like a consequence rather than a new definition. Explained solutions in the "
  "Anhang. Its §2.5 'Flächen als Grenzwerte' previews integration and is Chapter 7's business, "
  "not this session's."),

R(C5, "source-forster-wessoly",
  "Forster/Wessoly §§10-12 und §21 — Stetigkeit, Logarithmus, gleichmäßige Konvergenz", ALL5,
  "forster-wessoly.pdf Aufgaben §10 Funktionen, Stetigkeit p. 33, §11 Sätze über stetige "
  "Funktionen p. 35, §12 Logarithmus und allgemeine Potenz p. 37, §21 Gleichmäßige Konvergenz "
  "von Funktionenfolgen p. 59; Lösungen §10 p. 124, §11 p. 127, §12 p. 132, §21 p. 192. "
  "§§13-14 (komplexe Exponentialfunktion, trigonometrische Funktionen) go past this chapter.",
  "The only German exercise book on this menu with a dedicated §21 on uniform convergence — the "
  "one section of Chapter 5 with no HU practice at all.",
  "§10 and §11 are the standard continuity drill and map onto §§5.3-5.5. §12 covers the "
  "logarithm and general power, matching §5.6. The one to notice is §21: the script's §5.7 is "
  "two pages, has no HU sheet, and is exactly the kind of section that gets read once and never "
  "practised — and Forster has a whole exercise section with solutions for it. That makes this "
  "the primary route for §5.7, not a reserve one."),

R(C5, "source-deitmar-uebungsbuch",
  "Deitmar Kap. 4 und §7.1 — Funktionen und Stetigkeit, gleichmäßige Konvergenz", ALL5,
  "deitmar.pdf Kap. 4 Funktionen und Stetigkeit p. 31 (§4.1 Stetige Funktionen p. 31, §4.2 "
  "Monotone Funktionen p. 34, §4.3 Die Exponentialfunktion p. 35, §4.4 Anwendungen p. 36); "
  "Lösungen Kap. 24 p. 150. §7.1 Gleichmäßige Konvergenz p. 46; Lösungen Kap. 27 p. 167. "
  "§4.5 (komplexe Zahlen) and §7.2-7.3 (Potenzreihen, Fourier) are outside this script.",
  "A second solved bank that also carries a §7.1 on uniform convergence — the second of only "
  "two on this menu.",
  "Deitmar's §4.2 on monotone functions is the direct partner to the script's §5.4 inverse "
  "function material, which most references treat only inside a continuity section. Together "
  "with Forster §21 it means §5.7 has two independent solved exercise sets, which is more than "
  "it looked like having before this pass."),

R(C5, "source-analysis-drill-blaetter-extern",
  "u10_Loesung.pdf — epsilon-delta continuity worked out in full",
  ["ch05-stetigkeit"],
  "u10_Loesung.pdf (4 pp, TU Darmstadt SoSe 2007, 10. Übungsblatt): Aufgabe G31 — prove the "
  "square-root function is continuous at p = 0 directly from the definition, with an "
  "'Informelle Vorüberlegung' section shown before the 'Formaler Beweis'",
  "One ε-δ continuity proof with the scratch-work printed above the clean proof — the exact "
  "shape HU Serie 09.1 asks for.",
  "Four pages, one idea, and the layout is the point: the informal estimate that finds δ = ε² "
  "is written out first, and only then the formal argument that presents it. Students who can "
  "follow an ε-δ proof but cannot produce one are usually missing that first half, and it is "
  "almost never printed. Use it immediately before attempting Serie 09.1 or WV1.2(b)."),

R(C5, "source-analysis-drill-blaetter-extern",
  "IngMath2 Kap. 11 und §12.3 — stetige Funktionen, Exponential und Logarithmus", ALL5,
  "IngMath2_Aufgaben.pdf: Kap. 11 Stetige Funktionen p. 75 (§11.1 Motivation und Definition "
  "p. 75, §11.2 Eigenschaften stetiger reeller Funktionen p. 85, §11.3 Gleichmäßige Stetigkeit "
  "p. 90, §11.4 Grenzwerte von Funktionen p. 92); §12.3 Exponentialfunktion, "
  "Logarithmusfunktion p. 118. §12.2 Potenzreihen matches the §5.8 Exkurs and is skipped.",
  "Solved computational drill on continuity and the elementary functions, at volume.",
  "§11.3 is worth naming separately: uniform *continuity* (as opposed to uniform convergence) "
  "belongs to the script's §5.5 and is the distinction most likely to be confused with §5.7. "
  "Having a section of exercises that isolates it is useful. Engineering-style throughout — "
  "fluency, not insight."),

R(C5, "source-analysis-drill-blaetter-extern",
  "AS-Ana1 — Exponentialfunktion und gleichmäßige Konvergenz, worked at length",
  ["ch05-exponentialfunktion", "ch05-gleichmaessige-konvergenz"],
  "AS-Ana1.pdf (53 pp): Aufgabe 1.5 'Die Exponentialfunktion' p. 6 with Lösung 2.5 p. 28; "
  "Aufgabe 1.10 'Funktionenfolgen und gleichmäßige Konvergenz' p. 11 with Lösung 2.10 p. 48",
  "The only worked, thought-process-level solution in the drill collection for §5.7.",
  "Aufgabe 1.10 matters out of proportion to its size. §5.7 has no HU sheet, two pages of "
  "script, and is a standing candidate for the thing that is recognised but not reproducible; "
  "this is a full worked treatment with the reasoning shown, from the same author whose "
  "supremum and accumulation-point solutions are on Chapters 2 and 3. Aufgabe 1.5 pairs with "
  "the script's §5.6 and with Forster §8's exponential series."),

R(C5, "source-mfnf-analysis1",
  "Mathe für Nicht-Freaks — Stetigkeit, one section per proof obligation", CONT5,
  "MfNF_Analysis-1.pdf 'Stetigkeit von Funktionen' p. 227: Folgenkriterium p. 228, "
  "Epsilon-Delta-Kriterium p. 232, Komposition stetiger Funktionen p. 240, 'Stetigkeit beweisen' "
  "p. 242, 'Unstetigkeit beweisen' p. 249, Zwischenwertsatz p. 257, Satz vom Minimum und Maximum "
  "p. 264, Gleichmäßige Stetigkeit p. 268. Located by the 2026-08-03 coverage audit; no "
  "contextual evaluation registered, so depth and scope stay unassessed (CLAUDE.md §4).",
  "Separate German sections for proving continuity and for proving *dis*continuity — and the "
  "second is what WV1.2 actually asks for.",
  "WV1.2(b) asks to show a function is continuous only at 0, which means one continuity proof "
  "and a discontinuity proof for every other point. Almost every text on this menu treats "
  "discontinuity as the negation of a definition and moves on; this one gives it seven pages of "
  "its own. Both criteria (sequence and ε-δ) also get separate sections, matching the script's "
  "§5.3 and Serie 8.4's demand for both. Unassessed against this exam."),

R(C5, "source-abbott-understanding-analysis",
  "Abbott Ch 4 — Functional Limits and Continuity, plus §6.2 uniform convergence", ALL5,
  "abbott.pdf §4.1 Discussion: Examples of Dirichlet and Thomae p. 122, §4.2 Functional Limits "
  "p. 126, §4.3 Continuous Functions p. 133, §4.4 Continuous Functions on Compact Sets p. 140, "
  "§4.5 The Intermediate Value Theorem p. 147, §4.6 Sets of Discontinuity p. 152; "
  "§6.2 Uniform Convergence of a Sequence of Functions p. 183",
  "Its chapter opens on the Dirichlet function — which is the function WV1.2 is built from.",
  "The alignment here is unusually direct. WV1.2 sets f(x) = x on Q and −x elsewhere, a "
  "Dirichlet-type construction, and asks where it is continuous; Abbott opens Chapter 4 with "
  "Dirichlet and Thomae for exactly the purpose of showing what continuity can and cannot look "
  "like. §4.4 (compact sets) and §4.5 (IVT) map onto §§5.4-5.5. §6.2 is the uniform-convergence "
  "route. One blocked idea at a time, as always."),

R(C5, "source-lebl-basic-analysis",
  "Lebl — Continuous Functions and Sequences of Functions", ALL5,
  "realanal.pdf 'Continuous Functions' p. 113: Limits of functions p. 113, Continuous functions "
  "p. 122, Extreme and intermediate value theorems p. 130, Uniform continuity p. 138, Limits at "
  "infinity p. 145, Monotone functions and continuity p. 149. 'Sequences of Functions' p. 227: "
  "Pointwise and uniform convergence p. 227, Interchange of limits p. 234",
  "Section for section the closest structural match to §§5.1-5.5 and §5.7 anywhere on this menu.",
  "Six subsections that correspond to the script's five, in the same order, plus a separate "
  "chapter for uniform convergence whose first section is precisely §5.7 and whose second names "
  "what uniform convergence is *for* — interchanging limits. That framing is missing from the "
  "script's two pages and is the thing that makes the distinction memorable."),

R(C5, "source-grieser-analysis1",
  "Grieser Kap. 10 und Kap. 11 — Exponentialfunktion und Stetigkeit", ALL5,
  "grieser.pdf Kap. 10 'Exponentialfunktion, Logarithmus und allgemeine Potenz' p. 164 "
  "(§10.1 Eigenschaften p. 165, §10.2 Logarithmus und allgemeine Potenz p. 167, Übungen p. 179); "
  "Kap. 11 'Stetigkeit' p. 181 (§11.1 Grenzwerte von Funktionen p. 181, §11.2 Definition und "
  "elementare Eigenschaften p. 188, §11.3 Die Hauptsätze über stetige Funktionen p. 197, "
  "§11.4 Gleichmäßige Stetigkeit p. 207, §11.5 Funktionenfolgen; gleichmäßige Konvergenz p. 210, "
  "Übungen p. 216); Lösungen und Hinweise p. 329",
  "German, and the only reference that gives the exponential function and continuity a chapter "
  "each — matching the script's §5.6 and §§5.1-5.5 split.",
  "§11.3 is literally titled 'Die Hauptsätze über stetige Funktionen', which is the script's "
  "§§5.4-5.5 material under one heading and the material the external papers ask to be stated. "
  "§11.5 covers §5.7. Exercises carry Hinweise before Lösungen, so a stuck problem has an "
  "intermediate step."),

R(C5, "source-ross-elementary-analysis",
  "Ross §§17-20 und §24 — continuity, uniform continuity, function limits", ALL5,
  "Ross_Elementary-Analysis_2ed.pdf §17 Continuous Functions p. 134, §18 Properties of "
  "Continuous Functions p. 144, §19 Uniform Continuity p. 150, §20 Limits of Functions p. 164; "
  "§24 Uniform Convergence p. 203, §25 More on Uniform Convergence p. 210. Located by the "
  "2026-08-03 coverage audit; no contextual evaluation registered, so depth and scope stay "
  "unassessed (CLAUDE.md §4).",
  "Continuity before limits — the reverse of the script's order, which is exactly why it is "
  "worth one look.",
  "Ross defines continuity first and function limits afterwards (§20), where the script does "
  "the opposite. Reading a section in the other order is a cheap test of whether the "
  "definitions are actually understood or merely sequenced. §19 isolates uniform continuity and "
  "§§24-25 cover uniform convergence, so both of Chapter 5's easily-confused 'uniform' notions "
  "have their own sections here. Unassessed against this exam."),

R(C5, "source-mit-18100a",
  "MIT 18.100A — function limits, the sequence criterion, min/max and IVT, uniform convergence",
  ALL5,
  "mit18_100af20_lec_full2.pdf: 'Limits of Functions' p. 47, 'Limits of Functions in Terms of "
  "Sequences and Continuity' p. 50, 'The Continuity of Sine and Cosine and the Many "
  "Discontinuities of Dirichlet's Function' p. 53, 'The Min/Max Theorem and Bolzano's "
  "Intermediate Value Theorem' p. 56, 'Uniform Continuity and the Definition of the Derivative' "
  "p. 59; 'Pointwise and Uniform Convergence of Sequences of Functions' p. 81, 'Uniform "
  "Convergence, the Weierstrass M-Test, and Interchanging Limits' p. 84",
  "The permitted window for this chapter, named lecture by lecture — including the two lectures "
  "that are the whole of §5.7.",
  "The p. 50 lecture is the sequence criterion for function limits, which is the script's Satz "
  "5.6 and the thing Serie 8.4 grades. The p. 53 lecture covers Dirichlet's function directly, "
  "which is WV1.2's construction. Note that this route now names the §5.7 lectures (pp. 81, 84) "
  "explicitly; the pre-2026-08-29 record said 'lectures 23-24' without saying what they were. "
  "Still one blocked idea at a time."),

R(C5, "source-labs-schreyer-mathe-informatiker",
  "Labs/Schreyer — Stetigkeit, spezielle Funktionen, Konvergenz von Funktionenfolgen", ALL5,
  "Labs-Schreyer_Mathematik-fuer-Informatiker.pdf 'Stetigkeit' p. 143 (Definition und "
  "Folgenkriterium p. 143, Der Zwischenwertsatz und Anwendungen p. 147); 'Spezielle Funktionen' "
  "p. 171 (Die Exponentialfunktion p. 171, Der Logarithmus p. 173, Trigonometrische Funktionen "
  "p. 175); 'Konvergenz von Funktionenfolgen' p. 217 (Gleichmäßige Konvergenz p. 217). Located "
  "by the 2026-08-03 coverage audit; no contextual evaluation registered, so depth and scope "
  "stay unassessed (CLAUDE.md §4).",
  "German and compact: continuity via the sequence criterion, then the IVT with applications, "
  "which is the script's own emphasis.",
  "'Der Zwischenwertsatz und Anwendungen' is the section title, and applications is what WV1.4 "
  "asks for — the bisection method is an IVT application. Its Spezielle Funktionen chapter "
  "collects exp, log and the trigonometric functions in one place, which serves §5.6 here and "
  "the §6.4 Ausflug on the next chapter."),

R(C5, "source-ableitinger-musterloesungen",
  "Ableitinger §§6.5-6.7, §6.10 und 7.1 — Musterlösungen für Stetigkeit und Funktionsgrenzwerte",
  ALL5,
  "ableitinger.pdf §6.5 Folgenstetigkeit p. 70, §6.6 Stetigkeit mit Epsilon und Delta p. 73, "
  "§6.7 Gleichmäßige Stetigkeit und Lipschitz-Stetigkeit p. 75, §6.10 Funktionenreihen p. 82, "
  "§7.1 Funktionengrenzwerte p. 85; the 'ausführliche Musterlösungen' for the same topics in "
  "§10.2 p. 170 and §12.2 p. 243 (Stetigkeit mit Epsilon und Delta, Zwischenwertsatz, "
  "Funktionsgrenzwerte ohne l'Hospital, Funktionenfolgen); Lösungsvorschläge §11.2 p. 190",
  "Five separate model solutions covering exactly this chapter's proof obligations, each "
  "annotated with the decisions behind it.",
  "This is the source that gained most from the 2026-08-29 pass. It was routed once, to the "
  "transfer unit, with the locator 'One example matching the diagnosed error'; opened, it has "
  "section-level model solutions for both continuity criteria, for uniform and Lipschitz "
  "continuity, and — in Teil III — full-length worked write-ups of the Zwischenwertsatz and of "
  "function limits computed without l'Hospital. Read these after writing your own version, as "
  "writing samples rather than as answers."),

R(C5, "source-analysis-klausuren-extern",
  "Solved German Klausur tasks on continuity, IVT and compactness", CONT5,
  "Regensburg_...pdf A3 (four quickfire questions on which sets can be the continuous image of "
  "[0,1] — IVT and compactness together, with 'Häufige Fehler' notes), A7 (no continuous "
  "f: [0,1] → R≥0 with f(0)=f(1)=0 takes every value exactly twice — Extremwertsatz plus IVT). "
  "Marburg_...pdf 2. Klausur A9 (for which a is a piecewise function continuous), A10 (exactly "
  "one solution of 1 − x² = exp(x−1) on [0,1]), A11 (a maximum exists on [0,∞)), A12 "
  "(injectivity, image, and continuity of the inverse); Wiederholungsklausur A9, A10, A12. "
  "Paderborn_...pdf A3(a) (show x ↦ e^x + x + 1 is bijective), A4(b) (is sin(1/(x−1)) extended "
  "by 0 continuous), A4(c) (a function sequence)",
  "The richest chapter in the external bank — and the tasks come in exactly the two shapes the "
  "HU WV set uses.",
  "Sort them into the two shapes before working any: 'is this piecewise function continuous, "
  "and for which parameter' (Marburg 2.A9, WK A9, Paderborn A4(b)) and 'show a solution exists "
  "and is unique' (Marburg 2.A10, WK A10, Paderborn A3(a)) — the second being WV1.4's shape "
  "exactly, IVT for existence plus monotonicity for uniqueness. Regensburg A3 and A7 are a "
  "third, rarer shape: reasoning about what continuity forbids. All solved, so spend them on "
  "diagnosed gaps; the unsolved papers stay on the transfer unit."),

R(C5, "source-analysis-klausuren-tum",
  "TUM Ferienkurs Kap. 4 Stetigkeit und Kap. 7 Funktionenfolgen", ALL5,
  "TUM_Ferienkurs-Analysis-1_Skriptum.pdf: Kap. 4 Stetigkeit PDF p. 33 (§4.1 Stetigkeit von "
  "Funktionen, §4.2 Funktionsgrenzwerte PDF p. 36), Übungsaufgaben PDF p. 38; Kap. 7 "
  "Funktionenfolgen PDF p. 62, Übungsaufgaben PDF p. 65",
  "A five-page compressed version of the chapter plus a separate short chapter and exercise set "
  "for §5.7.",
  "Its Kap. 7 is the third exercise set available for uniform convergence, after Forster §21 "
  "and Deitmar §7.1 — for a two-page script section with no HU sheet, that is now adequate "
  "cover rather than a hole. Revision pace, not first exposure."),

R(C5, "source-professor-leonard", "Professor Leonard — Calculus 1, limits and continuity",
  ["ch05-funktionsgrenzwerte", "ch05-einseitige-grenzwerte", "ch05-stetigkeit"],
  "Professor Leonard, Calculus 1: the limits and continuity block. Topic-matched selection from "
  "the source record's own list; no local copy, so the selection is by topic rather than by "
  "timestamp.",
  "Blackboard pace on the computational half of the chapter — one-sided limits and the "
  "indeterminate forms, worked in full.",
  "Conditional on a diagnosed block, one topic at a time. It is a good fit for §5.2 "
  "specifically, where the work is case analysis and algebra rather than proof. It does not "
  "reach the sequence criterion, the compactness theorems or uniform convergence at the "
  "script's depth — for those the routes are Abbott, Lebl or MIT 18.100A."),

R(C5, "source-3b1b-essence-of-calculus", "3Blue1Brown — the limits episode",
  ["ch05-funktionsgrenzwerte", "ch05-einseitige-grenzwerte"],
  "Essence of Calculus: the limits episode (which also introduces l'Hôpital). Topic-matched "
  "selection from the source record's own list; no local copy, so the selection is by topic "
  "rather than by timestamp.",
  "A short visual preview for when the *picture* of a limit is missing, not the technique.",
  "Ten to fifteen minutes, watched once, before rather than instead of the script. It shows the "
  "ε-δ picture geometrically, which is the one thing a written definition cannot do. It is not "
  "a source of rigour and should never be the thing an exam answer is reconstructed from. The "
  "l'Hôpital half of the same episode belongs to Chapter 6."),

R(C5, "source-strang-calculus", "Strang Ch 2.6-2.7 and Ch 6 — limits, continuity, exp and log",
  ["ch05-funktionsgrenzwerte", "ch05-stetigkeit", "ch05-exponentialfunktion"],
  "mitres_18_001_f17_ch02.pdf §2.6 Limits p. 123, §2.7 Continuous Functions p. 131; "
  "mitres_18_001_f17_ch06.pdf Exponentials and Logarithms (§6.2 The Exponential e^x p. 292, "
  "§6.4 Logarithms p. 310); matching guide_ch02.pdf and guide_ch06.pdf are secondary",
  "Applied-first intuition: Strang reaches limits only after using them, which is the opposite "
  "of the script's order and occasionally the more memorable one.",
  "Strang puts limits in §2.6 — after two chapters of derivatives — precisely because he thinks "
  "the definition is easier once you have needed it. That makes this a reserve route rather "
  "than a parallel text, useful when the formal definition has been read several times without "
  "landing. Chapter 6 is the applied account of exp and log for §5.6."),

R(C5, "source-thomas-calculus", "Thomas Ch 2 and §7.1 — limits, continuity, log as an integral",
  CONT5 + ["ch05-exponentialfunktion"],
  "Thomas-Calculus_Early-Transcendentals.pdf §2.2 Limit of a Function and Limit Laws p. 80, "
  "§2.3 The Precise Definition of a Limit p. 91, §2.4 One-Sided Limits p. 100, §2.5 Continuity "
  "p. 107, §2.6 Limits Involving Infinity p. 118; §7.1 The Logarithm Defined as an Integral "
  "p. 434. Located by the 2026-08-03 coverage audit; no contextual evaluation registered, so "
  "depth and scope stay unassessed (CLAUDE.md §4).",
  "Reserve computational volume, with §2.3 the one section that does attempt the precise "
  "definition.",
  "§§2.4 and 2.6 are the closest external match to the script's §5.2, which is otherwise thinly "
  "covered — one-sided limits and limits involving infinity each get a full section with a "
  "large exercise set. §2.3 is the ε-δ definition at calculus-course depth: worth knowing it is "
  "there, not a substitute for Abbott or the script."),

R(C5, "source-stewart-calculus", "Stewart Ch 2 and §1.5 — limits, continuity, inverse functions",
  CONT5 + ["ch05-exponentialfunktion"],
  "Stewart.pdf §2.2 The Limit of a Function p. 115, §2.3 Calculating Limits Using the Limit Laws "
  "p. 127, §2.4 The Precise Definition of a Limit p. 136, §2.5 Continuity p. 146, §2.6 Limits at "
  "Infinity p. 158; §1.5 Inverse Functions and Logarithms p. 87. Located by the 2026-08-03 "
  "coverage audit; no contextual evaluation registered, so depth and scope stay unassessed "
  "(CLAUDE.md §4).",
  "The Thomas alternative — same coverage, more worked examples; open one, not both.",
  "Interchangeable with Thomas for this chapter. §1.5 covers inverse functions and logarithms "
  "together, which is a slightly better fit for the script's §5.4 inverse-function material "
  "than Thomas's arrangement."),


# ==========================================================================
# Kapitel 6 — Differentialrechnung II
# ==========================================================================
C6 = "unit-m2-analysis-ch06"
ALL6 = ["ch06-differenzierbarkeit", "ch06-mittelwertsatz", "ch06-trigonometrie",
        "ch06-hospital", "ch06-hoehere-ableitungen", "ch06-taylor", "ch06-interpolation"]
CORE6 = ["ch06-differenzierbarkeit", "ch06-mittelwertsatz", "ch06-hospital",
         "ch06-hoehere-ableitungen"]

R(C6, "source-analysis-skript", "unser skript.pdf Kapitel 6 — the scope authority", ALL6,
  f"unser skript.pdf Kapitel 6, {sk(137)}–{sk(190)}; §6.1 Differenzierbarkeit und Ableitungen "
  f"{sk(137)}, §6.3 Mittelwertsatz {sk(145)}, §6.4 Ausflug Sinus, Kosinus, Tangens {sk(148)}, "
  f"§6.5 Regel von l'Hospital {sk(151)}, §6.7 Höhere Ableitungen {sk(165)}, §6.8 Taylorpolynome "
  f"und Taylorreihen {sk(168)}, §6.10 Ausflug numerische Interpolation {sk(174)}. §§6.2, 6.6 "
  f"and 6.9 are Exkurse and are not worked here.",
  "The longest chapter in the script, and the first with no current HU exercise sheet behind it "
  "at all.",
  "Two things govern this session. First, the chapter is really one theorem and its "
  "consequences: §6.3's mean value theorem is what makes the derivative say anything about the "
  "function, and monotonicity, extrema, l'Hospital and Taylor all descend from it. Second, the "
  "practice situation changes here: the local HU set stops at §5.5, so every drill on this menu "
  "is a substitute chosen by topic rather than calibrated to this examiner. That has been an "
  "open, unowned gap since the 2026-08-03 audit, and it is the reason this session leans harder "
  "on IngMath2 and the German exercise books than any earlier one.",
  vault="material://source-analysis-skript/unser skript.pdf"),

R(C6, "source-analysis-skript-beweise",
  "kleine_beweise.pdf — the six Chapter 6 proofs the tutors named", CORE6,
  "kleine_beweise.pdf, section 'Kapitel 6: Differentialrechnung II': Lemma 6.3 (differentiable "
  "⇒ continuous), Satz 6.4 (Rechenregeln der Differenziation), Lemma 6.11 (f'(x₀) = 0 is "
  "necessary for an extremum), Korollar 6.13 written out explicitly via 6.12 (Satz von Rolle), "
  "Korollar 6.14 (zero derivative ⇒ constant), Satz 6.15 (monotonicity and the first derivative)",
  "The longest per-chapter list in the handout — six results, and together they are the chain "
  "from the definition to the monotonicity test.",
  "Read the six in order and they are one argument: differentiability gives continuity, the "
  "rules let you compute, a vanishing derivative is necessary at an extremum, Rolle follows, "
  "the mean value theorem follows from Rolle, and monotonicity follows from that. That is the "
  "chapter. Since no HU sheet reaches Chapter 6, this handout is the closest thing to a "
  "statement of expected depth for it — with the authors' standing disclaimer that it has no "
  "known relation to exam contents.",
  vault="material://source-analysis-skript/kleine_beweise.pdf"),

R(C6, "source-fritzsche-trainingsbuch",
  "Fritzsche §3.1, §3.2 und §4.2 — Differenzierbarkeit, Mittelwertsatz, Taylorentwicklung",
  ALL6,
  "fritzsche.pdf §3.1 Differenzierbare Funktionen p. 116, §3.2 Der Mittelwertsatz p. 126, "
  "§4.2 Die Taylorentwicklung p. 200; Lösungen in Kap. 5 Anhang from p. 253. §§3.5-3.6 "
  "(Bogenlänge, Differentialgleichungen) are outside this script.",
  "Explained German solutions covering both halves of the chapter, including a dedicated "
  "Taylor section — one of only four Taylor sources in the whole collection.",
  "Fritzsche splits the chapter across two of its own chapters: Der Calculus for §§6.1-6.7 and "
  "Vertauschung von Grenzprozessen for Taylor. §4.2 is the one to note — the script's §6.8 has "
  "no HU sheet, and this is the gentlest of the four available substitutes, with solutions "
  "written as prose. Work §3.1 and §3.2 first; they are the chapter's spine."),

R(C6, "source-forster-wessoly",
  "Forster/Wessoly §15, §16 und §22 — Differentiation, Extrema, Taylor-Reihen", ALL6,
  "forster-wessoly.pdf Aufgaben §15 Differentiation p. 43, §16 Lokale Extrema. Mittelwertsatz. "
  "Konvexität p. 45, §22 Taylor-Reihen p. 61; Lösungen §15 p. 150, §16 p. 156, §22 p. 195. "
  "§17 (numerische Lösung von Gleichungen) parallels the §6.6 Exkurs and is skipped.",
  "Section-matched German drill for the whole chapter, with §22 supplying Taylor problems and "
  "solutions.",
  "§16's title is the script's §§6.3-6.7 in one line — local extrema, mean value theorem, "
  "convexity — which makes it the single most efficient drill section for the chapter. §22 was "
  "added to the routing in the 2026-08-22 fix and is confirmed here: Taylor-Reihen with "
  "Aufgaben on p. 61 and Lösungen on p. 195. Terse solutions, so pair with Fritzsche when an "
  "argument does not come out."),

R(C6, "source-deitmar-uebungsbuch", "Deitmar Kap. 5 — Differentialrechnung", CORE6,
  "deitmar.pdf §5.1 Differenzierbarkeit p. 38, §5.2 Lokale Extrema, Mittelwertsatz p. 39, "
  "§5.3 Die Regeln von de l'Hospital p. 42; Lösungen Kap. 25 p. 158",
  "A third solved bank with a section devoted to l'Hospital specifically.",
  "Its §5.3 is the only place in the three German exercise books where l'Hospital gets its own "
  "problem section rather than appearing inside a limits set — useful because the script gives "
  "it its own §6.5 and because the hypothesis check is the part that gets skipped. Deitmar has "
  "no Taylor section in scope (its Kap. 9.4 is the multivariable Taylor formula), so Taylor "
  "practice has to come from elsewhere."),

R(C6, "source-analysis-drill-blaetter-extern",
  "IngMath2 Kap. 13 und Kap. 14 — the chapter's practice workhorse", ALL6,
  "IngMath2_Aufgaben.pdf: Kap. 13 Differenzierbare reelle Funktionen p. 127 (§13.1 Motivation "
  "und Definition p. 127, §13.2 Rechenregeln p. 132); Kap. 14 Anwendungen der "
  "Differentialrechnung p. 140 (§14.1 Mittelwertsätze p. 140, §14.2 Regeln von de l'Hospital "
  "p. 150, §14.3 Der Satz von Taylor p. 158, §14.4 Kurvendiskussion p. 180, §14.5 Noch einmal "
  "Polynominterpolation p. 190). Kap. 15 (numerische Lösung von Gleichungen) parallels the §6.6 "
  "Exkurs and is skipped.",
  "The only source in the local collection that covers every section of this chapter with "
  "solved exercises — including twenty-two pages on Taylor alone.",
  "This file carries the Chapter 6 practice load by itself, and §14.3 is why: twenty-two pages "
  "of Taylor problems with solutions, where no HU sheet exists and the German exercise books "
  "offer a section each. §14.5 matches the script's §6.10 Ausflug on interpolation — the only "
  "external drill for it anywhere. The style is engineering-computational: it will build "
  "fluency and will not explain why the remainder term has the form it does. Sections are "
  "numbered by the printed chapter numbering shown above, which starts at 10 rather than 1."),

R(C6, "source-mfnf-analysis1", "Mathe für Nicht-Freaks — Ableitung, one section per rule",
  CORE6,
  "MfNF_Analysis-1.pdf 'Ableitung' p. 273: Ableitung p. 274, Ableitungsregeln p. 292, Ableitung "
  "der Umkehrfunktion p. 294, Beispiele p. 300, Ableitung höherer Ordnung p. 302, Satz von "
  "Rolle p. 304, Mittelwertsatz p. 309, Konstanzkriterium p. 315, Monotoniekriterium p. 318, "
  "Ableitung und lokale Extrema p. 320. Located by the 2026-08-03 coverage audit; no contextual "
  "evaluation registered, so depth and scope stay unassessed (CLAUDE.md §4).",
  "The whole Rolle → mean value theorem → constancy → monotonicity → extrema chain, one German "
  "section per link — which is the same chain the tutors' proof list picks out.",
  "Compare the section list here with the kleine_beweise Chapter 6 entries and they are the "
  "same six results in the same order. That correspondence makes this the natural place to "
  "repair any single link: each has its own worked section rather than a paragraph inside a "
  "longer theorem. It has no Taylor section, so §6.8 must come from elsewhere. Unassessed "
  "against this exam."),

R(C6, "source-abbott-understanding-analysis", "Abbott Ch 5 and §6.6 — The Derivative, Taylor Series",
  CORE6 + ["ch06-taylor"],
  "abbott.pdf §5.2 Derivatives and the Intermediate Value Property p. 159, §5.3 The Mean Value "
  "Theorems p. 166, §5.4 A Continuous Nowhere-Differentiable Function p. 173; §6.6 Taylor Series "
  "p. 207",
  "Its chapter opens by asking whether derivatives must be continuous — a question that makes "
  "the mean value theorem's role visible.",
  "Abbott's §5.1 discussion ('Are Derivatives Continuous?') sets up why the derivative is a "
  "more delicate object than the difference quotient suggests, and §5.3 then treats the mean "
  "value theorems as the answer. That is the framing the script's §6.3 states without "
  "motivating. §6.6 is a rigorous Taylor treatment — more than this exam needs, but it is one "
  "of the four Taylor routes available and the only one that proves the remainder estimate "
  "carefully."),

R(C6, "source-lebl-basic-analysis", "Lebl — The Derivative, with Taylor's theorem in place",
  ALL6,
  "realanal.pdf 'The Derivative' p. 155: The derivative p. 155, Mean value theorem p. 162, "
  "Taylor's theorem p. 171, Inverse function theorem p. 176",
  "Four sections that are the script's §§6.1, 6.3, 6.8 and the derivative half of §5.4 — the "
  "tightest structural match available for this chapter.",
  "Lebl puts Taylor's theorem inside the derivative chapter rather than with series, which is "
  "exactly the script's arrangement and unusual among the English references. That makes it the "
  "best route for reading §6.8 as a consequence of the mean value theorem rather than as a "
  "series topic. Free, English, and structured for a second pass over an argument already "
  "read once."),

R(C6, "source-grieser-analysis1", "Grieser Kap. 12 — Differentialrechnung mit Taylorapproximation",
  ALL6,
  "grieser.pdf Kap. 12 'Differentialrechnung' p. 219: §12.1 Definition und Bedeutung der "
  "Ableitung p. 219, §12.2 Berechnung der Ableitung p. 226, §12.3 Ableitung und "
  "Funktionseigenschaften p. 236, §12.4 Ableitung und Grenzwertberechnung p. 242, §12.5 Zweite "
  "Ableitung und Konvexität p. 245, §12.6 Taylorapproximation und Taylorreihen p. 248, Übungen "
  "p. 259; Lösungen und Hinweise p. 329. Kap. 14 Die trigonometrischen Funktionen p. 278 covers "
  "the §6.4 Ausflug.",
  "One German chapter covering all seven in-scope sections, including Taylor, with hints and "
  "solutions on the exercises.",
  "The section titles say what each part is *for*: §12.3 is the derivative used to read off "
  "function properties (the script's §§6.3 and 6.7), §12.4 is the derivative used to compute "
  "limits (l'Hospital, §6.5). For a chapter with no HU sheet, a German text that is organised "
  "by purpose and carries graded hints is a strong substitute. Kap. 14 supplies the §6.4 "
  "Ausflug material separately."),

R(C6, "source-ross-elementary-analysis",
  "Ross §§28-31 — the derivative, mean value theorem, l'Hospital, Taylor", ALL6,
  "Ross_Elementary-Analysis_2ed.pdf §28 Basic Properties of the Derivative p. 232, §29 The Mean "
  "Value Theorem p. 241, §30 L'Hospital's Rule p. 250, §31 Taylor's Theorem p. 258; Selected "
  "Hints and Answers p. 376. Located by the 2026-08-03 coverage audit; no contextual evaluation "
  "registered, so depth and scope stay unassessed (CLAUDE.md §4).",
  "Four short numbered sections that match §§6.1, 6.3, 6.5 and 6.8 one to one.",
  "Ross gives l'Hospital and Taylor a section each rather than folding them into a longer "
  "chapter, which makes both easy to enter directly — and both are sections of the script that "
  "have no calibrated practice. Unassessed against this exam; the locator is a fact, the "
  "judgement is not."),

R(C6, "source-mit-18100a",
  "MIT 18.100A — differentiation rules, Rolle, the mean value theorem, Taylor",
  CORE6 + ["ch06-taylor"],
  "mit18_100af20_lec_full2.pdf: 'Differentiation Rules, Rolle's Theorem, and the Mean Value "
  "Theorem' p. 65, 'Taylor's Theorem and the Definition of Riemann Sums' p. 69",
  "Two lectures covering the chapter's spine and its endpoint, for one blocked idea.",
  "The p. 69 lecture is the boundary between this chapter and the next: Taylor's theorem and "
  "then the definition of Riemann sums, which is exactly how the script moves from §6.8 to "
  "§7.1. Reading it once makes that transition deliberate rather than incidental. Rule "
  "unchanged: one definition at a time, not a course."),

R(C6, "source-labs-schreyer-mathe-informatiker",
  "Labs/Schreyer — Differentiation, Mittelwertsatz, L'Hospital, Taylorpolynom", ALL6,
  "Labs-Schreyer_Mathematik-fuer-Informatiker.pdf 'Differentiation' p. 153 (Differenzierbarkeit "
  "p. 153, Rechenregeln p. 155); 'Mittelwertsatz und lokale Extrema' p. 161 (Die erste Ableitung "
  "p. 161, Höhere Ableitungen p. 164, Das Newtonverfahren p. 166); 'Asymptotisches Verhalten und "
  "Regel von L'Hospital' p. 181; 'Taylorpolynom und Taylorreihe' p. 209. Located by the "
  "2026-08-03 coverage audit; no contextual evaluation registered, so depth and scope stay "
  "unassessed (CLAUDE.md §4).",
  "German, CS-framed, and it gives Taylor its own chapter — one of the four Taylor routes, and "
  "the only German textbook one.",
  "The chapter divisions match the script closely: differentiation, then mean value theorem with "
  "higher derivatives, then l'Hospital, then Taylor. Its Newtonverfahren section corresponds to "
  "the script's §6.6 Exkurs and can be skipped. For a chapter this thinly practised, a German "
  "account at the right level is worth more than another English reference."),

R(C6, "source-ableitinger-musterloesungen",
  "Ableitinger §6.8 und §6.9 — Musterlösungen für Differenzierbarkeit und Taylorpolynom",
  ["ch06-differenzierbarkeit", "ch06-taylor"],
  "ableitinger.pdf §6.8 Differenzierbarkeit p. 77, §6.9 Taylorpolynom p. 80; "
  "Lösungsvorschläge §11.2 p. 190",
  "A model Taylor-polynomial solution with the solver's decisions annotated — the only worked "
  "*presentation* of a Taylor task in the collection.",
  "Newly routed at chapter level. §6.9 matters because §6.8 of the script has no HU sheet and "
  "no HU marking scheme, which leaves the question of how much working to show completely open. "
  "This is the one source that answers it by showing a full write-up and explaining why each "
  "step is there."),

R(C6, "source-analysis-klausuren-extern",
  "Solved German Klausur tasks on derivatives, extrema and the mean value theorem",
  CORE6 + ["ch06-trigonometrie"],
  "Regensburg_...pdf A5 (define sin and cos, prove sin is differentiable with sin' = cos), "
  "A6 (show f ∈ C¹ and compute the derivative; then whether an antiderivative with two given "
  "values exists — a mean value theorem argument). Paderborn_...pdf A3(b) (derivative of an "
  "inverse function at a point), A5 (local extrema of e^x/x^e, then decide whether e^π or π^e "
  "is larger). Marburg_...pdf 2. Klausur A11 (a maximum exists), Wiederholungsklausur A11. "
  "⚠ No paper in this bank contains a Taylor task.",
  "Real exam wording for the derivative half of the chapter — and a documented absence for the "
  "Taylor half.",
  "The absence is the important part and is recorded rather than left to be discovered: four "
  "solved German papers, three unsolved ones and the MIT set, and not one Taylor question among "
  "them. Chapter 6's Taylor practice must therefore be assembled from Fritzsche §4.2, Forster "
  "§22, IngMath2 §14.3 and the TUM Übungsaufgaben, and that assembly is a deliberate "
  "construction rather than a found exam set. Paderborn A5(b) is the most interesting solved "
  "task here: comparing e^π with π^e is a monotonicity argument disguised as arithmetic."),

R(C6, "source-analysis-klausuren-tum",
  "TUM Ferienkurs Kap. 5 Differenzierbarkeit — Satz von Taylor with exercises", ALL6,
  "TUM_Ferienkurs-Analysis-1_Skriptum.pdf: Kap. 5 Differenzierbarkeit PDF p. 39 (§5.1 "
  "Definition, Grundbegriffe und Rechenregeln, §5.2 Stammfunktionen PDF p. 42, §5.3 Anwendungen "
  "der Differentialrechnung PDF p. 43, with the Satz von Taylor at PDF pp. 47-48), "
  "Übungsaufgaben PDF p. 49",
  "One of only four sources with Taylor exercises, and the only one that is a revision script "
  "rather than a textbook.",
  "This is why the TUM file was separated from the Klausur papers in the 2026-08-22 fix: it is "
  "not a past paper to be spent once but a revision script with its own exercise sets, and its "
  "Taylor pages plus the exercise set at PDF p. 49 are a scarce resource for §6.8. Its §5.2 on "
  "Stammfunktionen arrives before the integral, which is the reverse of the script's order — "
  "read it with Chapter 7 rather than here."),

R(C6, "source-professor-leonard",
  "Professor Leonard — Calculus 1 derivative and Mittelwertsatz, Calculus 2 Taylor",
  ALL6,
  "Professor Leonard, Calculus 1: the derivative, the Mittelwertsatz, l'Hospital. Calculus 2: "
  "Taylor and power series. Topic-matched selection from the source record's own list; no local "
  "copy, so the selection is by topic rather than by timestamp.",
  "The chapter where a US calculus course covers the most of what is actually examined — at "
  "blackboard pace, with every step of the computation shown.",
  "Chapter 6 is the best fit for this source in the whole module: derivative rules, the mean "
  "value theorem, l'Hospital and Taylor polynomials are standard calculus-course content, "
  "taught computationally, which is the level §§6.1-6.8 mostly ask for. Still conditional on a "
  "diagnosed block and still one topic at a time — the pace angle is a repair tool, not a "
  "syllabus."),

R(C6, "source-3b1b-essence-of-calculus",
  "3Blue1Brown — the derivative, chain rule and Taylor series episodes", ALL6,
  "Essence of Calculus: the derivative and chain-rule episodes; the l'Hôpital half of the limits "
  "episode; the Taylor series episode. Topic-matched selection from the source record's own "
  "list; no local copy, so the selection is by topic rather than by timestamp.",
  "The Taylor episode in particular gives the picture — successive derivatives matching at a "
  "point — that the formula alone does not.",
  "Short, watched once, before the script rather than instead of it. The Taylor episode is the "
  "one worth the time on this chapter: §6.8 introduces the polynomial and the remainder as "
  "formulas, and the visual account of why matching derivatives at a point produces a good "
  "local approximation is the missing motivation. No rigour, and nothing here should be "
  "reconstructed into an exam answer."),

R(C6, "source-strang-calculus",
  "Strang Ch 2-4 and §10.4 — derivatives, the MVT with l'Hôpital, the Taylor series", ALL6,
  "mitres_18_001_f17_ch02.pdf Derivatives (§2.1 The Derivative of a Function p. 87, §2.5 The "
  "Product and Quotient and Power Rules p. 116); mitres_18_001_f17_ch03.pdf Applications of the "
  "Derivative (§3.2 Maximum and Minimum Problems p. 143, §3.8 The Mean Value Theorem and "
  "l'Hôpital's Rule p. 197); mitres_18_001_f17_ch04.pdf Derivatives by the Chain Rule "
  "(§4.3 Inverse Functions and Their Derivatives p. 216); mitres_18_001_f17_ch10.pdf "
  "§10.4 The Taylor Series for e^x, sin x, and cos x p. 452; matching guide_chNN.pdf are "
  "secondary",
  "Applied-first intuition, with §3.8 putting the mean value theorem and l'Hôpital in the same "
  "section — as consequence and application.",
  "Strang's arrangement makes an argument the script leaves implicit: l'Hôpital is a corollary "
  "of the mean value theorem, and putting them in one section says so. §10.4 develops the "
  "Taylor series for the three functions it is usually wanted for. Reserve intuition, chosen "
  "per diagnosed block."),

R(C6, "source-thomas-calculus",
  "Thomas Ch 3, §§4.1-4.5 and §§10.8-10.10 — derivatives, applications, Taylor", ALL6,
  "Thomas-Calculus_Early-Transcendentals.pdf §3.2 The Derivative as a Function p. 142, §3.3 "
  "Differentiation Rules p. 150, §3.6 The Chain Rule p. 177, §3.8 Derivatives of Inverse "
  "Functions and Logarithms p. 191; §4.1 Extreme Values of Functions p. 237, §4.2 The Mean Value "
  "Theorem p. 245, §4.3 Monotonic Functions and the First Derivative Test p. 253, §4.4 Concavity "
  "and Curve Sketching p. 258, §4.5 Indeterminate Forms and L'Hôpital's Rule p. 269; §10.8 "
  "Taylor and Maclaurin Series p. 640, §10.9 Convergence of Taylor Series p. 645, §10.10 The "
  "Binomial Series and Applications of Taylor Series p. 652. Located by the 2026-08-03 coverage "
  "audit; no contextual evaluation registered, so depth and scope stay unassessed "
  "(CLAUDE.md §4).",
  "Reserve computational volume with the largest exercise sets on this menu, section-matched to "
  "the whole chapter.",
  "Named at section level for the first time — the pre-2026-08-29 record carried only a file "
  "path and 1205 pages. For a chapter with no HU practice, having a large exercise bank indexed "
  "to each script section is worth more than it would be elsewhere. §4.4 (curve sketching) "
  "corresponds to IngMath2's §14.4 Kurvendiskussion; neither is a script section, and both are "
  "the standard application of §6.7. Overlaps with Stewart — open one."),

R(C6, "source-stewart-calculus",
  "Stewart Ch 3, §§4.1-4.4 and §§11.10-11.11 — derivatives, applications, Taylor", ALL6,
  "Stewart.pdf §3.1-§3.6 Differentiation Rules p. 204-250 (chain rule §3.4 p. 229, logarithmic "
  "§3.6 p. 250); §4.1 Maximum and Minimum Values p. 308, §4.2 The Mean Value Theorem p. 319, "
  "§4.3 How Derivatives Affect the Shape of a Graph p. 325, §4.4 Indeterminate Forms and "
  "L'Hospital's Rule p. 336; §11.10 Taylor and Maclaurin Series p. 791, §11.11 Applications of "
  "Taylor Polynomials p. 806. Located by the 2026-08-03 coverage audit; no contextual "
  "evaluation registered, so depth and scope stay unassessed (CLAUDE.md §4).",
  "The Thomas alternative, with §11.11 devoted to using Taylor polynomials with an error bound.",
  "§11.11 is the reason to prefer Stewart here: it is a section about applying Taylor "
  "polynomials *with the remainder estimate*, which is the part of §6.8 that turns the "
  "polynomial into something usable and the part most likely to be skipped. Otherwise "
  "interchangeable with Thomas."),


# ==========================================================================
# Kapitel 7 — Integralrechnung
# ==========================================================================
C7 = "unit-m2-analysis-ch07"
ALL7 = ["ch07-riemann-integral", "ch07-hauptsatz", "ch07-uneigentliche-integrale"]

R(C7, "source-analysis-skript", "unser skript.pdf Kapitel 7 — the scope authority", ALL7,
  f"unser skript.pdf Kapitel 7, {sk(191)}–{sk(225)}; §7.1 Das Riemann-Integral {sk(192)}, "
  f"§7.2 Hauptsatz und Integrationsregeln {sk(203)}, §7.3 Uneigentliche Integrale {sk(212)}. "
  f"§7.4 is an Exkurs and is not worked here.",
  "The chapter that cashes in Chapter 5 — continuity on a compact interval is what makes the "
  "integral exist — and then hands over the fundamental theorem.",
  "Three sections and a clear division of labour: §7.1 is the definition and the integrability "
  "criterion, and it is asked for in words at least as often as it is computed; §7.2 is the "
  "fundamental theorem with substitution and integration by parts as its corollaries, and is "
  "where the marks are; §7.3 turns integrals back into limits and so re-uses Chapter 4's "
  "convergence thinking. Like Chapter 6 there is no HU sheet — but unlike Chapter 6, the "
  "external Klausur bank covers this ground well, so the substitutes here are stronger.",
  vault="material://source-analysis-skript/unser skript.pdf"),

R(C7, "source-analysis-skript-beweise",
  "kleine_beweise.pdf — the two Chapter 7 proofs the tutors named",
  ["ch07-hauptsatz"],
  "kleine_beweise.pdf, section 'Kapitel 7: Integralrechnung': Satz 7.20 (Partielle Integration), "
  "Satz 7.24 (Mittelwertsatz der Integralrechnung)",
  "Two proofs, and the first is the one Regensburg's Aufgabe 4 asks to be produced from the "
  "fundamental theorem.",
  "The correspondence is worth acting on. The tutors name partielle Integration as a proof worth "
  "knowing; Regensburg's Aufgabe 4 asks precisely for the second Hauptsatz, then the statement "
  "of partielle Integration, then its proof from the Hauptsatz. That is two independent sources "
  "pointing at the same short argument, in a chapter with no HU practice. The tutor disclaimer "
  "stands.",
  vault="material://source-analysis-skript/kleine_beweise.pdf"),

R(C7, "source-fritzsche-trainingsbuch",
  "Fritzsche §3.3, §3.4 und §4.4 — Stammfunktionen, Integrationsmethoden, uneigentliche Integrale",
  ALL7,
  "fritzsche.pdf §3.3 Stammfunktionen und Integrale p. 148, §3.4 Integrationsmethoden p. 159, "
  "§4.4 Uneigentliche Integrale p. 225; Lösungen in Kap. 5 Anhang from p. 253. §2.5 'Flächen als "
  "Grenzwerte' p. 105 is the gentle preview of §7.1.",
  "All three script sections covered, with explained solutions — and §2.5 approaches the "
  "integral as a limit of areas before any formalism.",
  "§2.5 is the entry point worth knowing about: it develops area as a limit inside the "
  "chapter on limits, which is where the Riemann sum idea actually comes from and which the "
  "script's §7.1 presents already formalised. §3.4 is the technique drill — substitution and "
  "parts — and §4.4 is one of the few dedicated improper-integral exercise sections available."),

R(C7, "source-forster-wessoly",
  "Forster/Wessoly §§18-20 — Riemannsches Integral, Integration und Differentiation, "
  "uneigentliche Integrale", ALL7,
  "forster-wessoly.pdf Aufgaben §18 Das Riemannsche Integral p. 49, §19 Integration und "
  "Differentiation p. 51, §20 Uneigentliche Integrale. Die Gamma-Funktion p. 57; Lösungen §18 "
  "p. 174, §19 p. 177, §20 p. 186",
  "Three German exercise sections that map onto the script's three, one to one, with solutions.",
  "The mapping is exact: §18 ↔ §7.1, §19 ↔ §7.2, §20 ↔ §7.3. For a chapter with no HU sheet "
  "that alignment makes this the default drill. The Gamma function part of §20 goes past the "
  "script and can be left; the improper-integral problems before it are in scope."),

R(C7, "source-deitmar-uebungsbuch", "Deitmar Kap. 6 — Integralrechnung", ALL7,
  "deitmar.pdf §6.1 Hauptsatz der Differential- und Integralrechnung p. 43, §6.2 Uneigentliche "
  "Integrale p. 44; Lösungen Kap. 26 p. 162",
  "Short and precisely targeted: one section on the fundamental theorem, one on improper "
  "integrals.",
  "Two pages of problems, which is small — but they are on exactly the two sections that carry "
  "the marks, with worked Lösungsvorschläge. Reserve volume once Forster §§18-20 is spent."),

R(C7, "source-analysis-drill-blaetter-extern",
  "IngMath2 Kap. 16-18 — the integral, the techniques, and improper integrals at volume", ALL7,
  "IngMath2_Aufgaben.pdf: Kap. 16 Das bestimmte Riemannsche Integral p. 219 (§16.1 Definition "
  "p. 219, §16.2 Integrierbarkeitskriterien p. 221, §16.3 Klassen integrierbarer Funktionen "
  "p. 225, §16.4 Rechenregeln p. 227); Kap. 17 Das unbestimmte Integral p. 234 (§17.1 "
  "Fundamentalsatz p. 234, §17.2 Partielle Integration p. 238, §17.3 Substitutionsregel p. 245, "
  "§17.4 Partialbruchzerlegung p. 246); Kap. 18 Uneigentliche Integrale p. 252 (§18.1 "
  "unbeschränkte Intervalle p. 252, §18.2 unbeschränkte Integranden p. 265). Kap. 19-20 "
  "(numerische Integration, Anwendungen) parallel the §7.4 Exkurs and are skipped.",
  "Thirty-five pages of solved integration technique, split exactly the way the script splits "
  "the chapter — including both kinds of improper integral separately.",
  "Together with Chapter 6 this file is the substitute for the missing HU sheets, and here it "
  "is at its strongest: §17.2 and §17.3 are dedicated sections for parts and substitution, "
  "which are the two techniques §7.2 introduces, and §§18.1-18.2 separate the unbounded-interval "
  "and unbounded-integrand cases that the script's §7.3 treats together. §17.4 "
  "(Partialbruchzerlegung) is not a script section but is standard preparation for the "
  "integrals the external papers set."),

R(C7, "source-analysis-drill-blaetter-extern",
  "Aufgabensammlung-M1 Aufgabe 13 — the integration item in the mixed bank",
  ["ch07-hauptsatz"],
  "Aufgabensammlung-M1_Loesung.pdf (7 pp), Aufgabe 13",
  "One integration task sitting inside a mixed set — a small check that the technique survives "
  "when it is not signposted.",
  "Small by design. Its value is not the problem but the context: every other integration route "
  "on this menu is a section of integration problems, which removes the recognition step. This "
  "one is item thirteen in a bank whose other items are sequences and series, so the "
  "technique has to be recognised before it can be applied."),

R(C7, "source-mfnf-analysis1",
  "Mathe für Nicht-Freaks — Integrale, from the definition to the two techniques", ALL7,
  "MfNF_Analysis-1.pdf 'Integrale' p. 329: Das Integral p. 330, Riemannintegral p. 332, "
  "Eigenschaften des Riemannintegrals p. 347, Mittelwertsatz für Integrale p. 348, Hauptsatz "
  "der Differential- und Integralrechnung p. 355, Substitutionsregel p. 363, Partielle "
  "Integration p. 366. Located by the 2026-08-03 coverage audit; no contextual evaluation "
  "registered, so depth and scope stay unassessed (CLAUDE.md §4).",
  "German, section by section, and it includes the Mittelwertsatz für Integrale — one of the "
  "two proofs the tutors named for this chapter.",
  "The section list is close to the script's own order, and the presence of a dedicated "
  "Mittelwertsatz-für-Integrale section matters because that is kleine_beweise's Satz 7.24 and "
  "is otherwise easy to lose between §7.1 and §7.2. It stops before improper integrals, so §7.3 "
  "needs another route. Unassessed against this exam."),

R(C7, "source-abbott-understanding-analysis", "Abbott Ch 7 — The Riemann Integral", ALL7,
  "abbott.pdf §7.1 Discussion: How Should Integration be Defined? p. 224, §7.2 The Definition of "
  "the Riemann Integral p. 227, §7.3 Integrating Functions with Discontinuities p. 233, §7.4 "
  "Properties of the Integral p. 237, §7.5 The Fundamental Theorem of Calculus p. 243",
  "Opens by asking what an integral should be before defining one — which is what makes upper "
  "and lower sums look inevitable rather than arbitrary.",
  "The script's §7.1 introduces partitions and upper/lower sums as machinery. Abbott's §7.1 "
  "discussion asks first what properties an integral ought to have, so the machinery arrives as "
  "an answer. §7.3 (functions with discontinuities) is the sharpest available treatment of which "
  "functions are integrable, which is the script's integrability criterion. One blocked idea at "
  "a time."),

R(C7, "source-lebl-basic-analysis", "Lebl — The Riemann Integral, including improper integrals",
  ALL7,
  "realanal.pdf 'The Riemann Integral' p. 181: The Riemann integral p. 181, Properties of the "
  "integral p. 191, Fundamental theorem of calculus p. 200, The logarithm and the exponential "
  "p. 207, Improper integrals p. 214",
  "The closest structural twin again — and one of the few references with a dedicated improper "
  "integrals section.",
  "Five subsections against the script's three, in the same order, plus improper integrals "
  "treated properly rather than as an appendix. Its logarithm-and-exponential section defines "
  "them via the integral, which is a different construction from the script's §5.6 series "
  "definition — interesting, but not the one to reproduce in the exam."),

R(C7, "source-grieser-analysis1", "Grieser Kap. 15 — Integration", ALL7,
  "grieser.pdf Kap. 15 'Integration' p. 291: §15.1 Das Integral für Treppenfunktionen p. 292, "
  "§15.2 Das Integral für Regelfunktionen p. 295, §15.3 Der Hauptsatz p. 302, §15.4 Berechnung "
  "von Integralen: Partielle Integration, Substitution und Potenzreihen p. 308, §15.5 "
  "Uneigentliche Integrale p. 318, Übungen p. 326; Lösungen und Hinweise p. 329",
  "German, complete for the chapter, with hints before solutions — but note it builds the "
  "integral for Regelfunktionen, not the Riemann integral.",
  "The construction difference is worth knowing before opening it: Grieser goes via step "
  "functions and regulated functions, where the script uses Riemann upper and lower sums. The "
  "theorems and the techniques are the same and §§15.3-15.5 are directly usable; §§15.1-15.2 "
  "are a different route to the same place and should not be reproduced as if they were the "
  "script's definition."),

R(C7, "source-ross-elementary-analysis",
  "Ross §§32-34 and §36 — the Riemann integral, its properties, the fundamental theorem", ALL7,
  "Ross_Elementary-Analysis_2ed.pdf §32 The Riemann Integral p. 278, §33 Properties of the "
  "Riemann Integral p. 289, §34 Fundamental Theorem of Calculus p. 300, §36 Improper Integrals "
  "p. 340 (§35 Riemann-Stieltjes is past this script); Selected Hints and Answers p. 376. "
  "Located by the 2026-08-03 coverage audit; no contextual evaluation registered, so depth and "
  "scope stay unassessed (CLAUDE.md §4).",
  "Short numbered sections matching §§7.1-7.3, entered directly.",
  "§35 (Riemann-Stieltjes) sits between §34 and §36 and is out of scope — worth naming so it is "
  "skipped deliberately rather than worked by accident when paging from the fundamental theorem "
  "to improper integrals. Unassessed against this exam."),

R(C7, "source-mit-18100a",
  "MIT 18.100A — the Riemann integral of a continuous function, and the FTC with its corollaries",
  ALL7,
  "mit18_100af20_lec_full2.pdf: 'Taylor's Theorem and the Definition of Riemann Sums' p. 69, "
  "'The Riemann Integral of a Continuous Function' p. 72, 'The Fundamental Theorem of Calculus, "
  "Integration by Parts, and Change of Variable Formula' p. 76",
  "Three lectures, and the last one derives parts and substitution from the fundamental theorem "
  "— which is Regensburg's Aufgabe 4.",
  "The p. 76 lecture is the one to know about: it treats integration by parts and the change of "
  "variable formula as consequences of the fundamental theorem rather than as separate "
  "techniques, which is both the script's §7.2 arrangement and the exact argument the "
  "Regensburg paper asks to be reproduced. One blocked idea at a time, as always."),

R(C7, "source-labs-schreyer-mathe-informatiker",
  "Labs/Schreyer — Integration und uneigentliche Integrale", ALL7,
  "Labs-Schreyer_Mathematik-fuer-Informatiker.pdf 'Integration' p. 189 ((Riemann-)"
  "Integrierbarkeit p. 190, Stammfunktionen p. 196, Elementare Funktionen p. 201); "
  "'Uneigentliche Integrale' p. 205. Located by the 2026-08-03 coverage audit; no contextual "
  "evaluation registered, so depth and scope stay unassessed (CLAUDE.md §4).",
  "German, Riemann-based like the script, with improper integrals as their own chapter.",
  "Unlike Grieser it builds the Riemann integral directly, so its definition matches the "
  "script's and can be used to check a written statement. Short — about twenty pages for the "
  "whole chapter — which makes it a second reading rather than a first one."),

R(C7, "source-ableitinger-musterloesungen",
  "Ableitinger §7.2 und §7.3 — Musterlösungen für Integrationsmethoden und uneigentliche "
  "Integrale", ["ch07-hauptsatz", "ch07-uneigentliche-integrale"],
  "ableitinger.pdf §7.2 Integrationsmethoden p. 90, §7.3 Uneigentliche Integrale p. 93; "
  "Lösungsvorschläge §11.3 p. 202",
  "Model solutions for the two techniques and for improper integrals, with the choice of method "
  "explained rather than assumed.",
  "These sit in the book's 'Analysis 2' part, which is a labelling difference rather than a "
  "scope one: integration methods and improper integrals are the script's §§7.2-7.3. The value "
  "is the same as elsewhere in this source — how the solution is written and why each step was "
  "chosen, read after your own attempt."),

R(C7, "source-analysis-klausuren-extern",
  "Solved German Klausur tasks on the fundamental theorem and integration technique", ALL7,
  "Regensburg_...pdf A4 (state the second Hauptsatz, state partielle Integration, then prove "
  "partielle Integration from the Hauptsatz — 3+3+4 points), A5.3 (show x ↦ sin x·cos x is "
  "Riemann-integrable on [0,1] and compute the integral), A6.2 (does an antiderivative with two "
  "prescribed values exist). Paderborn_...pdf A6 (∫₀¹ arcsin t dt — substitution followed by "
  "integration by parts, 10 points)",
  "The best-covered chapter in the external bank, and Regensburg A4 is the closest thing "
  "available to a marking scheme for §7.2.",
  "Regensburg A4 is worth working carefully even though it is solved: it separates 'state the "
  "theorem' from 'prove the corollary' and prices them (3 + 3 + 4), which is direct evidence "
  "that stating a theorem with its hypotheses is independently graded — the same signal HU's "
  "WV1.4 gives for the Zwischenwertsatz. Paderborn A6 is the standard two-technique integral. "
  "Both solved, so spend them on diagnosed gaps; Ulm's task 8 (two antiderivatives) is on the "
  "unsolved list and stays with the transfer unit."),

R(C7, "source-analysis-klausuren-tum",
  "TUM Ferienkurs Kap. 6 Riemann-Integral + Übungsaufgaben", ALL7,
  "TUM_Ferienkurs-Analysis-1_Skriptum.pdf: Kap. 6 Riemann-Integral PDF p. 51 (§6.1 Definition "
  "und Grundbegriffe, §6.2 Integrationstechniken PDF p. 54, §6.3 Uneigentliche Integrale PDF "
  "p. 56), Übungsaufgaben PDF p. 59",
  "The chapter compressed to eight pages with its own exercise set — a revision pass for a "
  "chapter with no HU sheet.",
  "Its three sections match the script's three exactly, and the exercise set at PDF p. 59 is "
  "one of the few German problem sets for this chapter that is not inside a textbook. Revision "
  "pace: it will confirm what is there, not build it."),

R(C7, "source-professor-leonard",
  "Professor Leonard — Calculus 1 definite integral and FTC, Calculus 2 techniques and improper "
  "integrals", ALL7,
  "Professor Leonard, Calculus 1: the definite integral and the fundamental theorem. Calculus 2: "
  "integration techniques, improper integrals. Topic-matched selection from the source record's "
  "own list; no local copy, so the selection is by topic rather than by timestamp.",
  "Blackboard pace on substitution and parts, where the failure is almost always execution "
  "rather than understanding.",
  "Conditional on a diagnosed block, one topic at a time. Integration technique is the part of "
  "the module where watching someone work through the algebra is genuinely the efficient "
  "repair, because the errors are arithmetic and bookkeeping. It will not cover the "
  "integrability criterion of §7.1 at the script's depth."),

R(C7, "source-3b1b-essence-of-calculus",
  "3Blue1Brown — integration and the fundamental theorem", ALL7,
  "Essence of Calculus: the integration and fundamental-theorem episode (and the following one "
  "on areas). Topic-matched selection from the source record's own list; no local copy, so the "
  "selection is by topic rather than by timestamp.",
  "The visual argument for why differentiation and integration are inverse — the claim §7.2 "
  "states and does not motivate.",
  "Fifteen minutes, watched once, before the script. The fundamental theorem is the single "
  "most surprising statement in the module and the one most often held as a rule rather than "
  "understood; this is the cheapest available fix for that. No rigour, and not a source to "
  "reconstruct an answer from."),

R(C7, "source-strang-calculus", "Strang Ch 5 and Ch 7 — Integrals and Techniques of Integration",
  ALL7,
  "mitres_18_001_f17_ch05.pdf Integrals (§5.1 The Idea of the Integral p. 229, §5.3 Summation "
  "versus Integration p. 240, §5.5 The Definite Integral p. 254, §5.7 The Fundamental Theorem "
  "and Its Applications p. 267); mitres_18_001_f17_ch07.pdf Techniques of Integration (§7.1 "
  "Integration by Parts p. 342, §7.5 Improper Integrals p. 367); matching guide_ch05.pdf and "
  "guide_ch07.pdf are secondary",
  "The two chapters the 2026-08-03 audit marked `selected` out of the whole Strang bundle — "
  "applied-first intuition for the chapter where it works best.",
  "Only chapters 5, 7 and 10 of Strang were selected; the rest of the bundle is reserve or "
  "multivariable and out of scope. §5.3 'Summation versus Integration' is the section worth the "
  "detour: it sets the Riemann sum against the finite sum explicitly, which is what makes §7.1's "
  "partitions read as an approximation being refined rather than as notation."),

R(C7, "source-thomas-calculus", "Thomas Ch 5, §§8.1-8.2, §8.5 and §8.8 — integrals and techniques",
  ALL7,
  "Thomas-Calculus_Early-Transcendentals.pdf §5.2 Sigma Notation and Limits of Finite Sums "
  "p. 323, §5.3 The Definite Integral p. 330, §5.4 The Fundamental Theorem of Calculus p. 342, "
  "§5.5 Indefinite Integrals and the Substitution Method p. 353; §8.1 Using Basic Integration "
  "Formulas p. 470, §8.2 Integration by Parts p. 475, §8.5 Integration of Rational Functions by "
  "Partial Fractions p. 494, §8.8 Improper Integrals p. 518. Located by the 2026-08-03 coverage "
  "audit; no contextual evaluation registered, so depth and scope stay unassessed "
  "(CLAUDE.md §4).",
  "Reserve computational volume with a large exercise set for every technique in §7.2 and for "
  "§7.3.",
  "Named at section level for the first time. §8.8 is a full section of improper integrals with "
  "convergence tests, which is more practice on §7.3 than any German source here offers. "
  "Overlaps with Stewart §§7.1-7.8 — open one, not both."),

R(C7, "source-stewart-calculus", "Stewart Ch 5, §7.1, §7.4 and §7.8 — integrals and techniques",
  ALL7,
  "Stewart.pdf §5.2 The Definite Integral p. 410, §5.3 The Fundamental Theorem of Calculus "
  "p. 424, §5.5 The Substitution Rule p. 444; §7.1 Integration by Parts p. 504, §7.4 Integration "
  "of Rational Functions by Partial Fractions p. 525, §7.5 Strategy for Integration p. 535, "
  "§7.8 Improper Integrals p. 559. Located by the 2026-08-03 coverage audit; no contextual "
  "evaluation registered, so depth and scope stay unassessed (CLAUDE.md §4).",
  "The Thomas alternative, and §7.5 is a section on nothing but choosing the technique.",
  "§7.5 'Strategy for Integration' is the counterpart to §11.7 for series: a short section whose "
  "content is the decision, which is the step that a section-organised exercise book removes. "
  "For an exam where the integral arrives without a label, that is the practice worth having."),


# ==========================================================================
# The transfer unit — calibration, retrieval, and the deferral ledger
# ==========================================================================
CX = OLD_UNIT

R(CX, "source-analysis-skript",
  "unser skript.pdf — the course contract and the chapter map",
  ["calibrate", "anx", "exkurse"],
  "unser skript.pdf: Vorwort and the three-label contract pp. iv-vii (Wiederholung required, "
  "Ausflug at overview depth, Exkurs not exam-relevant, proofs need not be reproduced); "
  "Inhaltsverzeichnis pp. ii-iii; Bezeichnungen p. viii; Kapitel 8 Exkurse "
  f"{sk(226)} onward",
  "The document that decides what counts as in scope, at what depth, and therefore what every "
  "other route on every other session is for.",
  "Read pp. iv-vii once, deliberately, before Chapter 1. Three claims there govern the whole "
  "plan: Wiederholung sections are assumed known and are not re-taught; Ausflug sections should "
  "be understood and applied but are not an exam focus; Exkurs sections are explicitly not "
  "exam-relevant. And the sentence that shapes everything else — 'Die Beweise müssen Sie nicht "
  "können' — with the positive form beside it: definitions, results and their application in "
  "concrete problems are what the exam asks for. Every 'reference-only' label in this module "
  "traces back to that page.",
  vault="material://source-analysis-skript/unser skript.pdf"),

R(CX, "source-analysis-skript-hu",
  "HU Aufgaben zur Wiederholung und Vertiefung — the exam-format set, held for timed sittings",
  ["anx"],
  "ana_inf_serieWV.pdf: WV1.1 Folgen, WV1.2 Stetigkeit, WV1.3 Konvergenzkriterien, WV1.4 "
  "Bisektionsverfahren — 20 points each, and the sheet's own instruction: these cover Kapitel 1 "
  "to 5 (up to §5.5), 'die so auch in einer Klausur enthalten sein könnten', to be attempted "
  "first under exam conditions at about 30-45 minutes per task",
  "The only current HU material that states its own exam conditions — the closest available "
  "simulation of the Analysis half of the paper.",
  "This is the set to protect. It is named on the Chapter 3, 4 and 5 sessions so those sessions "
  "know what they are preparing for, but it is worked here, cold and timed, not there. Its own "
  "framing is unusually explicit: exam-format questions, 30-45 minutes each, covering Chapters "
  "1 to 5 only. That coverage boundary is also the honest limit of this rehearsal — there is no "
  "HU-format material for Chapters 6 and 7 at all, so a full Analysis mock has to be assembled "
  "from external papers and labelled as an assembly.",
  vault="material://source-analysis-skript/ana_inf_serieWV.pdf"),

R(CX, "source-analysis-skript-beweise",
  "kleine_beweise.pdf — the whole list, and its disclaimer", ["calibrate", "anx"],
  "kleine_beweise.pdf (2 pp, SoSe 2025 Tutorium zur Prüfungsvorbereitung, Hannah Shorten and "
  "Noah-Joël Seegert): twenty results across Kapitel 3 to 7, with the printed caveat that the "
  "list was compiled by student assistants and 'steht in keinem uns bekannten Zusammenhang mit "
  "den Inhalten der Klausur'",
  "One page that answers the question the course contract leaves open — if proofs need not be "
  "reproduced, which ones are still worth understanding.",
  "Read once at calibration to see the shape of the answer: twenty results for a 225-page "
  "script, concentrated in Chapters 3 and 6. Then use it per chapter, where it is routed "
  "individually, to repair a failed application. The disclaimer is real and is why this is a "
  "calibration input rather than an authority — it is an experienced reader's shortlist, not "
  "exam intelligence, and the plan treats it as the former.",
  vault="material://source-analysis-skript/kleine_beweise.pdf"),

R(CX, "source-analysis-klausuren-extern",
  "Unsolved German papers, held for timed sittings", ["anx"],
  "Ulm_Analysis-fuer-Informatiker_Klausur-SS10_nur-Aufgaben.pdf (2 pp, 120 min, 100 points, "
  "8 tasks — tasks 2, 3, 4, 5, 6 and 8 are in scope; task 7 is multivariable and task 1 is "
  "partly number-system material); Leipzig_Analysis-fuer-Informatiker_Probeklausur.pdf (2 pp, "
  "4 tasks: Mengen/Abbildungen/Induktion/reelle Zahlen, Folgen, Reihen, Stetigkeit — the "
  "closest single paper to Chapters 1-5)",
  "The only Analysis papers in the collection that have not been read with their solutions — "
  "they can be spent exactly once each, under exam conditions.",
  "Their value is entirely in being unseen, which is why they are routed here and to no chapter "
  "session: a paper opened during Chapter 3 revision is no longer a mock. Ulm is the better "
  "full rehearsal — 120 minutes, 100 points, and six of its eight tasks map onto script "
  "Chapters 3 to 7 including two antiderivatives and an existence argument by IVT. Leipzig is "
  "the better coverage check for the first half. Note both are 'für Informatiker' papers, which "
  "is the same audience as this module.",
  vault=None),

R(CX, "source-analysis-klausuren-extern",
  "Stuttgart Probeklausur 1 — solved; only Aufgabe 3 is in scope", ["anx"],
  "'Aufgabe 3 ist gut.pdf' (3 pp, Universität Stuttgart, 'Lösungen zur Probeklausur 1'): "
  "Aufgabe 1 Äquivalenzrelationen, Aufgabe 2 komplexe Zahlen (out of scope), Aufgabe 3 parts "
  "(a) define a Cauchy sequence, (b) negate the definition, (c) two limit computations",
  "One good task on Cauchy sequences and the negation of a definition — already solved, so it "
  "cannot serve as a timed mock.",
  "⚠ Correction, 2026-08-29: the pre-existing route listed this file among the *unsolved* "
  "papers held for timed sittings. It is not unsolved — the file is titled 'Lösungen zur "
  "Probeklausur 1' and every task is worked. That matters for how the file is used, not for "
  "whether it is useful. As a solved "
  "task it belongs with the diagnosed-gap material rather than with Ulm and Leipzig; the "
  "negation half of Aufgabe 3 is the same skill Regensburg's A2.2 tests and is worth working "
  "for that reason. Aufgabe 2 is complex numbers and outside this script.",
  vault=None),

R(CX, "source-analysis-klausuren-extern",
  "MIT 18.100C exam set — English, proof-heavy, a different syllabus", ["anx"],
  "MIT18100C_Final.pdf (7 pp) with MIT18100C_Final-Solutions.pdf (6 pp), MIT18100C_Midterm2.pdf "
  "(5 pp), MIT18100C_Practice-Final.pdf (2 pp), MIT18100C_Practice-Midterm1.pdf (3 pp), "
  "MIT18100C_Practice-Midterm2.pdf (2 pp)",
  "A different course's exam culture: everything is a proof, and the language is English. Use "
  "for proof stamina, never as a scope signal.",
  "Kept at the bottom of the retrieval menu deliberately. 18.100C is a real-analysis course "
  "with a metric-space and topology component this script does not have, so its questions "
  "routinely fall outside scope, and its style — prove everything — contradicts this script's "
  "explicit contract that proofs need not be reproduced. The one thing it is good for is "
  "practising sustained written argument when that is the diagnosed weakness. It is not "
  "evidence about what the M2 Klausur will ask.",
  vault=None),

R(CX, "source-ableitinger-musterloesungen",
  "Ableitinger Teil I and Teil III — the method behind a written solution",
  ["calibrate", "anx"],
  "ableitinger.pdf Teil I: Kap. 3 'Teilprozesse beim Aufgabenlösen' p. 22 (P Problembewusstsein, "
  "K Klärung der Handlungsoptionen, Z Zugriff herstellen, A Anpassen/Prüfen der Passung, "
  "H Handwerk, T Tricks, B begleitende Kommentare) and §3.8 'Die Teilprozesse in einer "
  "vollständigen Musterlösung' p. 30; Teil II §4.2 'Hinweise zum Verfassen komprimierter "
  "Musterlösungen' p. 38; Teil III Kap. 10 'Verfassen ausführlicher Musterlösungen' p. 165 with "
  "the full write-ups in Kap. 12 p. 232",
  "The one source here that treats writing a solution as a skill with named parts, rather than "
  "as what happens after you know the answer.",
  "Read Teil I once at calibration. Its claim is that solving a task decomposes into seven "
  "sub-processes and that most teaching only ever shows the last one, which is why a student "
  "who follows every step of a model solution still cannot produce one. That is a precise "
  "description of the failure this plan's per-chapter Musterlösungen routes are meant to "
  "prevent, and §4.2 on writing *compressed* solutions is directly relevant to a three-hour "
  "paper. The per-chapter sections (§§6.1-6.10, §§7.1-7.3) are routed on the chapters "
  "themselves."),

R(CX, "source-analysis-grundlagen-handouts",
  "Maths220 — Proofs in Calculus", ["calibrate", "anx"],
  "Maths220_Proofs-in-Calculus.pdf (17 pp)",
  "Seventeen pages on how a limit or convergence proof is actually written — the shape, not the "
  "content.",
  "Short enough to read at calibration and specific enough to be worth it: it is about the "
  "written form of the arguments this module keeps asking for, which is the gap between "
  "understanding a proof and producing one under time. Routed here rather than to a chapter "
  "because it is about the form of every chapter's arguments at once."),

R(CX, "source-velleman-how-to-prove-it",
  "Velleman — proof strategies and the summary of techniques", ["calibrate"],
  "Velleman_How-To-Prove-It.pdf Ch 3 Proofs p. 118 (§3.1 Proof Strategies p. 118); 'Summary of "
  "Proof Techniques' p. 555. Located by the 2026-08-03 coverage audit; no contextual evaluation "
  "registered, so depth and scope stay unassessed (CLAUDE.md §4).",
  "A two-page summary of proof techniques at the back, which is the part worth having at "
  "calibration; the rest is a course.",
  "Routed lightly here on purpose. The induction chapters are on the Chapter 1 session where "
  "they belong; what belongs at calibration is p. 555, a single table of which technique the "
  "shape of a statement calls for. Reading the book is not part of this plan."),

R(CX, "source-ohlbach-eisinger-beweise",
  "Ohlbach/Eisinger — the catalogue of proof patterns", ["calibrate"],
  "Ohlbach-Eisinger_Design-Patterns-fuer-mathematische-Beweise.pdf Kap. 4 Einfache Beweismuster "
  "p. 29, Kap. 5 Komplexe Beweismuster p. 50. Located by the 2026-08-03 coverage audit; no "
  "contextual evaluation registered, so depth and scope stay unassessed (CLAUDE.md §4).",
  "The German naming of the patterns — useful once at calibration so a task's shape can be "
  "recognised rather than rediscovered.",
  "Same light touch as Velleman: two chapters skimmed once, not a book to work. Its value at "
  "calibration is vocabulary — Kontraposition, Widerspruchsbeweis, Widerlegung durch "
  "Gegenbeispiel — because a task that says 'beweisen oder widerlegen Sie' is asking for a "
  "named pattern and the naming makes the choice faster."),

R(CX, "source-analysis-skript",
  "The deferral ledger — Kapitel 8 and every Exkurs, named once and left", ["exkurse"],
  "unser skript.pdf Kapitel 8 Exkurse " + sk(226) + " to the end; and the Exkurs sections in "
  "Chapters 3-7: §3.2 Landau-Notation " + sk(46) + ", §3.4 Lösung homogener "
  "Rekursionsgleichungen " + sk(52) + ", §4.5 Produktreihen " + sk(95) + ", §5.8 Potenzreihen "
  + sk(130) + ", §6.2 Ableitung von Potenzreihen " + sk(144) + ", §6.6 Numerisches Lösen von "
  "Gleichungen " + sk(153) + ", §6.9 Potenzreihen und Taylorentwicklungen " + sk(173) + ", "
  "§7.4 Numerische Integration " + sk(215),
  "One list of everything the course contract puts outside the exam, so a deferred section is "
  "never re-discovered as a gap.",
  "Handled lightly and deliberately: the script states that Exkurse are not exam-relevant, so "
  "none of these sections gets a session, a stage or a material menu, and none of the chapter "
  "sessions spends time on them. They are written down once, here, for two reasons only — so "
  "that meeting a power-series or Newton-method task in an external bank is recognised as "
  "out-of-scope rather than as a hole, and so that the decision is reversible in one place if "
  "the lecturer ever says otherwise. One of them has value elsewhere: §3.2's Landau notation is "
  "the same O-notation Algorithmen 2 uses, and Labs/Schreyer p. 94 covers it if it is ever "
  "wanted for that reason rather than this one.",
  vault="material://source-analysis-skript/unser skript.pdf"),


# --------------------------------------------------------------------------
# Node → concept edges for the new Analysis nodes.
#
# The assembler refuses a stage with no concept coverage, and its automatic
# matcher only fires on registered names that appear in a node title. These are
# the curated edges, written where they can be argued with. They are applied to
# the assembler's own table during generation, and the same block has to be
# added to `tools/assemble_lecture_study_maps.py` when the plan is applied —
# not before, because that file's `curation_problems()` check refuses entries
# naming nodes that are not live yet.
# --------------------------------------------------------------------------

NEW_NODE_CONCEPTS = {
    f"{N}-ch01-zahlenmengen": ("concept-real-numbers",),
    f"{N}-ch01-induktion": ("concept-proof-technique",),
    f"{N}-ch01-beziehungen": ("concept-proof-technique", "concept-real-numbers"),
    f"{N}-ch02-koerperaxiome": ("concept-real-numbers",),
    f"{N}-ch02-anordnung": ("concept-real-numbers",),
    f"{N}-ch02-intervalle-betrag": ("concept-real-numbers",),
    f"{N}-ch02-supremum-infimum": ("concept-real-numbers",),
    f"{N}-ch02-vollstaendigkeitsaxiom": ("concept-real-numbers",),
    f"{N}-ch02-folgerungen": ("concept-real-numbers",),
    f"{N}-ch02-potenzen-wurzeln": ("concept-real-numbers",),
    f"{N}-ch02-maschinenzahlen": ("concept-real-numbers",),
    f"{N}-ch03-folgen": ("concept-sequences-convergence",),
    f"{N}-ch03-rekursionen": ("concept-sequences-convergence", "concept-proof-technique"),
    f"{N}-ch03-konvergenzkriterien": ("concept-sequences-convergence",),
    f"{N}-ch03-rechenregeln": ("concept-sequences-convergence",),
    f"{N}-ch03-bestimmte-divergenz": ("concept-sequences-convergence",),
    f"{N}-ch03-quadratwurzel": ("concept-sequences-convergence", "concept-real-numbers"),
    f"{N}-ch04-reihen": ("concept-series",),
    f"{N}-ch04-konvergenzkriterien": ("concept-series",),
    f"{N}-ch04-absolute-konvergenz": ("concept-series",),
    f"{N}-ch04-umordnungen": ("concept-series",),
    f"{N}-ch05-funktionsgrenzwerte": ("concept-limits-continuity",),
    f"{N}-ch05-einseitige-grenzwerte": ("concept-limits-continuity",),
    f"{N}-ch05-stetigkeit": ("concept-limits-continuity",),
    f"{N}-ch05-zwischenwertsatz": ("concept-limits-continuity",),
    f"{N}-ch05-kompakte-intervalle": ("concept-limits-continuity",),
    f"{N}-ch05-exponentialfunktion": ("concept-limits-continuity", "concept-series"),
    f"{N}-ch05-gleichmaessige-konvergenz": ("concept-uniform-convergence",),
    f"{N}-ch06-differenzierbarkeit": ("concept-differentiation",),
    f"{N}-ch06-mittelwertsatz": ("concept-differentiation",),
    f"{N}-ch06-trigonometrie": ("concept-differentiation",),
    f"{N}-ch06-hospital": ("concept-differentiation",),
    f"{N}-ch06-hoehere-ableitungen": ("concept-differentiation",),
    f"{N}-ch06-taylor": ("concept-taylor-series",),
    f"{N}-ch06-interpolation": ("concept-taylor-series",),
    f"{N}-ch07-riemann-integral": ("concept-riemann-integral",),
    f"{N}-ch07-hauptsatz": ("concept-riemann-integral",),
    f"{N}-ch07-uneigentliche-integrale": ("concept-riemann-integral",),
    f"{N}-calibrate": ("concept-proof-technique",),
    f"{N}-anx": ("concept-proof-technique",),
    # The deferral ledger is tagged only with the one concept it genuinely
    # names and nothing else teaches here — Landau notation. A concept tag is
    # read as coverage, so a wider tag on a deferred-topic stage would suppress
    # material that has not in fact been seen.
    f"{N}-exkurse": ("concept-asymptotic-analysis",),
}


# --------------------------------------------------------------------------
# Assembly
# --------------------------------------------------------------------------

def route_id(row: dict, seen: set) -> str:
    if row.get("id"):
        return row["id"]
    unit_tail = row["unit_id"].removeprefix("unit-m2-analysis-")
    src_tail = row["route_key"].removeprefix("source-").replace("-", "")[:24]
    base = f"route-an-{unit_tail}-{src_tail}".lower()
    base = "".join(ch if ch.isalnum() or ch == "-" else "-" for ch in base)
    candidate, n = base, 1
    while candidate in seen:
        n += 1
        candidate = f"{base}-{n}"
    seen.add(candidate)
    return candidate


def unit_record(spec: dict) -> dict:
    nodes = []
    for node_id, title, summary, builds_on in spec["nodes"]:
        node = {"id": node_id, "title": title, "summary": summary}
        if builds_on:
            node["builds_on"] = list(builds_on)
        nodes.append(node)
    pages = spec.get("pages")
    if pages:
        locator = (f"unser skript.pdf Kapitel {spec['unit_id'][-2:].lstrip('0')}, "
                   f"printed pp. {pages[0]}-{pages[1]} "
                   f"(PDF pp. {pages[0] + PDF_OFFSET}-{pages[1] + PDF_OFFSET}); "
                   f"Stand 04.02.2025")
    else:
        locator = ("unser skript.pdf course contract pp. iv-vii and Inhaltsverzeichnis "
                   "pp. ii-iii; Stand 04.02.2025")
    return {
        "id": spec["unit_id"],
        "type": "unit",
        "module_id": MODULE_ID,
        "component_id": COMPONENT_ID,
        "kind": "exam-block" if spec["unit_id"] == OLD_UNIT else "topic",
        "title": spec["title"],
        "order": spec["order"],
        "scope": spec["scope"],
        "status": "ready",
        "knowledge_map": {"summary": spec["summary"], "nodes": nodes},
        "scope_sources": [{
            "source_id": "source-analysis-skript",
            "authority": "brief",
            "locator": locator,
        }],
        "source_selections": [],
        "artifacts": {},
        "workspace_ids": [WORKSPACE_ID],
        "current_study_map": f"study-map-{spec['unit_id'].removeprefix('unit-')}",
    }


def patched_source_map(repo) -> dict:
    """Replace every Analysis unit route with the re-cut per-chapter routes."""
    current = copy.deepcopy(repo.module_source_maps[MODULE_ID])
    by_source: dict[str, list[dict]] = {}
    seen_ids: set[str] = set()
    for row in ROUTE_ROWS:
        route = {
            "id": route_id(row, seen_ids),
            "unit_id": row["unit_id"],
            "title": row["title"],
            "format": row["format"],
            "angle": row["angle"],
            "angle_detail": row["angle_detail"],
            "covers": row["covers"],
            "depth": row["depth"],
            "scope": row["scope"],
            "locator": row["locator"],
        }
        if row.get("vault_path"):
            route["vault_path"] = row["vault_path"]
        by_source.setdefault(row["source_id"], []).append(route)

    known = {entry["source_id"] for entry in current.get("sources", [])}
    missing = sorted(set(by_source) - known)
    if missing:
        raise SystemExit(f"source map lacks entries for: {missing}")

    for entry in current.get("sources", []):
        kept = [r for r in (entry.get("unit_routes") or [])
                if (r if isinstance(r, str) else r.get("unit_id")) != OLD_UNIT]
        entry["unit_routes"] = kept + by_source.get(entry["source_id"], [])
        if not entry["unit_routes"]:
            entry.pop("unit_routes")
    return current


def assemble(units: list[dict], source_map: dict, phrases: dict) -> dict[str, dict]:
    maps: dict[str, dict] = {}
    problems: list[str] = []
    for unit in units:
        routes = [r for entry in source_map.get("sources", [])
                  for r in (entry.get("unit_routes") or [])
                  if isinstance(r, dict) and r.get("unit_id") == unit["id"]]
        # The assembler reads the material URI under the name `material_uri`;
        # the canonical source-map field is `vault_path`. Translate for the call.
        for r in routes:
            if r.get("vault_path"):
                r = r
        routes = [dict(r, material_uri=r["vault_path"]) if r.get("vault_path") else dict(r)
                  for r in routes]
        if not routes:
            problems.append(f"{unit['id']}: no material routes reach it")
            continue
        record = build(unit, MODULE_ID, routes, phrases, True)
        problems.extend(assembly_problems(unit, routes, record))
        try:
            require_current_template(record, "curriculum")
            validate_contract(REPO, "study-map.schema.json", record,
                              label=f"assembled study map for {unit['id']}")
        except Exception as exc:  # noqa: BLE001 - reported, not swallowed
            problems.append(f"{unit['id']}: {exc}")
            continue
        maps[unit["id"]] = record
    if problems:
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        raise SystemExit("assembly preflight failed; nothing was written")
    return maps


def plan_package(units: list[dict], source_map: dict, maps: dict[str, dict],
                 repo) -> dict:
    order = list(repo.modules[MODULE_ID].get("unit_order", []) or [])
    insert_at = order.index(OLD_UNIT)
    new_order = order[:insert_at] + CHAPTER_UNITS + order[insert_at:]
    workspace = repo.workspaces.get(WORKSPACE_ID)
    ws_sources = sorted({row["source_id"] for row in ROUTE_ROWS} |
                        set(workspace.meta.get("sources", []) or []) if workspace
                        else {row["source_id"] for row in ROUTE_ROWS})
    return {
        "module_id": MODULE_ID,
        "plan_contract": {
            "version": 2,
            "plan_template_version": 1,
            "coverage_audit": (
                f"work/active/{WORKSPACE_ID}/outputs/"
                f"Analysis-chapter-coverage-audit-{DATE}.md"
            ),
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
        "module_patch": {"unit_order": new_order},
        "source_patches": [],
        "source_map": source_map,
        "units": [{"unit": u, "study_map": maps[u["id"]]} for u in units],
        "workspace_updates": [{"id": WORKSPACE_ID, "sources": ws_sources}],
    }


def md_escape(value: str) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


CHAPTER_TITLES = {spec["unit_id"]: spec["title"] for spec in ALL_UNITS}


def overview_markdown(maps: dict[str, dict]) -> str:
    out = [f"# Analysis — chapter-per-session plan, overview ({DATE})", "",
           "One session per chapter of `unser skript.pdf`, one stage per script section, and "
           "for each stage every material that reaches it with the angle it contributes.",
           "",
           "Generated by `build_analysis_chapter_plan_2026_08_29.py`. This file is a review "
           "artifact: the canonical records are written only through the Gateway.", ""]
    for spec in ALL_UNITS:
        uid = spec["unit_id"]
        record = maps[uid]
        out.append(f"## {spec['title']}")
        out.append("")
        out.append(f"`{uid}` · {len(record['stages'])} stages · "
                   f"{sum(len(s['resources']) for s in record['stages'])} material rows")
        out.append("")
        out.append(f"> {spec['scope']}")
        out.append("")
        for stage in record["stages"]:
            out.append(f"### {stage['number']}. {stage['title']}")
            out.append("")
            out.append(stage["objective"])
            out.append("")
            out.append("| Use | Material | Angle | Locator | Triage |")
            out.append("|---|---|---|---|---|")
            for res in stage["resources"]:
                out.append("| {} | {} | {} | {} | {} |".format(
                    md_escape(res.get("kind", "")),
                    md_escape(res.get("label", "")),
                    md_escape(res.get("angle", "")),
                    md_escape(res.get("locator", "")),
                    md_escape(res.get("scope_triage", "")),
                ))
            out.append("")
    return "\n".join(out) + "\n"


LOCAL_INVENTORY = [
    # (locator, pages, what it is, disposition, routed to)
    ("material://source-analysis-skript/unser skript.pdf", 258,
     "Hella Rabus, M2.1 Analysis script, Stand 04.02.2025; Kapitel 1-8 plus Einführung",
     "selected", "every chapter unit + the transfer unit"),
    ("material://source-analysis-skript/ana_inf_serie05.pdf", 2,
     "HU Serie 05 — Vollständigkeit, Rekursionen, Folgen und Grenzwerte (5.1-5.4)",
     "selected", "ch01 (5.1c), ch02 (5.4), ch03"),
    ("material://source-analysis-skript/ana_inf_serie06.pdf", 1,
     "HU Serie 06 — Folgen, Konvergenz, Häufungspunkte (6.1-6.3)", "selected", "ch03"),
    ("material://source-analysis-skript/ana_inf_serie07.pdf", 2,
     "HU Serie 07 — Folgen, Konvergenz, Heron (7.1-7.4)", "selected", "ch03"),
    ("material://source-analysis-skript/Pd3szO-ana_inf_serie08.pdf", 2,
     "HU Serie 08 — Reihen und Grenzwerte (8.1-8.4); the file exists only under this "
     "download-mangled name", "selected", "ch04 (8.1-8.3), ch05 (8.4)"),
    ("material://source-analysis-skript/ana_inf_serie09.pdf", 2,
     "HU Serie 09 — Grenzwerte von Funktionen, Stetigkeit (9.1-9.3)", "selected", "ch05"),
    ("material://source-analysis-skript/ana_inf_serieWV.pdf", 2,
     "HU Wiederholung und Vertiefung — WV1.1-WV1.4, exam format, 30-45 min each, Kapitel 1-5 "
     "up to §5.5", "selected", "transfer unit (timed); named on ch03/ch04/ch05"),
    ("material://source-analysis-skript/kleine_beweise.pdf", 2,
     "SoSe 2025 tutor handout listing twenty 'kleine Beweise' grouped by script chapter 3-7, "
     "with an explicit no-known-relation-to-the-exam disclaimer",
     "selected", "ch03, ch04, ch05, ch06, ch07, transfer unit"),
    ("material://source-analysis-skript/rabus-skript_kapitel-2_stand-2024-10.pdf", 49,
     "Earlier partial build of the same script (Stand 11.10.2024), different pagination",
     "superseded", "none — the current script defines scope"),
    ("material://source-fritzsche-trainingsbuch/fritzsche.pdf", 342,
     "Trainingsbuch zur Analysis 1; Kap. 1-4 with all solutions in the Kap. 5 Anhang from p. 253",
     "selected", "ch01, ch02, ch03, ch04, ch05, ch06, ch07"),
    ("material://source-forster-wessoly/forster-wessoly.pdf", 206,
     "Übungsbuch zur Analysis 1; Aufgaben §§1-23 pp. 11-63, Lösungen §§1-23 pp. 68-199",
     "selected", "ch01, ch02, ch03, ch04, ch05, ch06, ch07"),
    ("material://source-deitmar-uebungsbuch/deitmar.pdf", 257,
     "Übungsbuch zur Analysis; Kap. 1-7 in scope, Lösungen in Kap. 21-27; Kap. 8-20 are past "
     "this module", "selected", "ch01, ch02, ch03, ch04, ch05, ch06, ch07"),
    ("material://source-analysis-drill-blaetter-extern/AS-Ana1.pdf", 53,
     "Aufgabensammlung zur Analysis 1 — ten problems, each with a long solution that shows the "
     "search rather than the polished proof", "selected", "ch02, ch03, ch04, ch05"),
    ("material://source-analysis-drill-blaetter-extern/Grenzwerte-von-Folgen.pdf", 26,
     "Kippels, Grenzwerte von Folgen — 14 exercises, one solution per page", "selected", "ch03"),
    ("material://source-analysis-drill-blaetter-extern/auf-2-2_Folgen_Loesungen.pdf", 30,
     "Aufgabenkatalog Analysis SoSe 2019, Folgen und Grenzwerte, solutions inline",
     "selected", "ch03"),
    ("material://source-analysis-drill-blaetter-extern/auf-2-3_Reihen_Loesungen.pdf", 20,
     "Aufgabenkatalog Analysis SoSe 2019, Reihen, solutions inline; opens on the Cauchy "
     "criterion for series", "selected", "ch04"),
    ("material://source-analysis-drill-blaetter-extern/KIT_Blatt-Reihen.pdf", 4,
     "KIT 6. Übungsblatt, Reihen, Aufgaben mit Lösungen", "selected", "ch04"),
    ("material://source-analysis-drill-blaetter-extern/Tutorium-Musterloesung-Reihen.pdf", 6,
     "Tutorium Musterlösung Reihen; includes a 'Hinweis für die Klausur' on which steps need "
     "not be written out", "selected", "ch04"),
    ("material://source-analysis-drill-blaetter-extern/Loesungen4.pdf", 3,
     "4. Übungsblatt, Aufgabe 16 — choose N explicitly for ε = 1/10, 1/100 and general ε",
     "selected", "ch03"),
    ("material://source-analysis-drill-blaetter-extern/u10_Loesung.pdf", 4,
     "TU Darmstadt 10. Übungsblatt SoSe 2007 — ε-δ continuity of √x at 0, informal "
     "Vorüberlegung printed before the formal proof", "selected", "ch05"),
    ("material://source-analysis-drill-blaetter-extern/IngMath2_Aufgaben.pdf", 312,
     "Voß, Aufgaben und Lösungen zu Mathematik für Ingenieurwissenschaften II (1991); printed "
     "chapters 10-21, of which 10-14 and 16-18 are in scope", "selected",
     "ch03, ch04, ch05, ch06, ch07"),
    ("material://source-analysis-drill-blaetter-extern/Aufgabensammlung-M1_Loesung.pdf", 7,
     "Mixed solved bank; Aufgabe 1 is five sequences of different types, Aufgabe 13 the "
     "integration item", "selected", "ch03, ch07"),
    ("material://source-analysis-drill-blaetter-extern/Bestimmt_Scan.pdf", 12,
     "Handwritten field and order axioms; scanned, weak text layer, not searchable",
     "selected", "ch02"),
    ("material://source-analysis-klausuren-extern/Marburg_Analysis-I_3-Klausuren-mit-Loesungen.pdf",
     35, "Three full Analysis I papers with solutions (Marburg WS 2001/02), 12 tasks each",
     "selected", "ch01, ch02, ch03, ch04, ch05, ch06"),
    ("material://source-analysis-klausuren-extern/"
     "Regensburg_Analysis-I_Klausur-mit-Loesungen-und-Haeufige-Fehler.pdf", 14,
     "Regensburg 2011, 7 tasks, 72 points, 120 min, with printed 'Häufige Fehler' commentary",
     "selected", "ch01, ch02, ch03, ch05, ch06, ch07"),
    ("material://source-analysis-klausuren-extern/"
     "Paderborn_Analysis-1_Klausur-2023_Loesungsvorschlag.pdf", 9,
     "Paderborn SoSe 2023, 6 tasks, 70 points, 120 min, Lösungsvorschlag; A1 is complex "
     "numbers and out of scope", "selected", "ch03, ch04, ch05, ch06, ch07"),
    ("material://source-analysis-klausuren-extern/"
     "Darmstadt_Analysis-I_Probeklausur_mit-Loesungen.pdf", 7,
     "Darmstadt Probeklausur with solutions; A4 is metric spaces and out of scope",
     "selected", "ch01, ch03, ch04"),
    ("material://source-analysis-klausuren-extern/"
     "Ulm_Analysis-fuer-Informatiker_Klausur-SS10_nur-Aufgaben.pdf", 2,
     "Ulm 2009, 8 tasks, 100 points, 120 min, tasks only; task 7 is multivariable",
     "selected — held unseen", "transfer unit only"),
    ("material://source-analysis-klausuren-extern/"
     "Leipzig_Analysis-fuer-Informatiker_Probeklausur.pdf", 2,
     "Leipzig Probeklausur, 4 tasks covering Mengen/Induktion/reelle Zahlen, Folgen, Reihen, "
     "Stetigkeit; tasks only", "selected — held unseen", "transfer unit only"),
    ("material://source-analysis-klausuren-extern/Aufgabe 3 ist gut.pdf", 3,
     "Universität Stuttgart, 'Lösungen zur Probeklausur 1' — SOLVED, not unsolved as the "
     "pre-2026-08-29 route recorded; A1 Äquivalenzrelationen, A2 komplexe Zahlen "
     "(out of scope), A3 Cauchy-Folgen und Negation", "selected — corrected", "transfer unit"),
    ("material://source-analysis-klausuren-extern/TUM_Ferienkurs-Analysis-1_Skriptum.pdf", 88,
     "TUM Ferienkurs Analysis 1 revision script with Übungsaufgaben per chapter; Kap. 1-7 in "
     "scope, Kap. 8-9 (Fourier, DGL) out; Anhang A p. 82 on writing proofs, Anhang B p. 84 a "
     "worked ε-proof", "selected", "ch01, ch02, ch03, ch04, ch05, ch06, ch07"),
    ("material://source-analysis-klausuren-extern/MIT18100C_Final.pdf", 7,
     "MIT 18.100C final; the set also holds MIT18100C_Final-Solutions.pdf (6 pp), "
     "MIT18100C_Midterm2.pdf (5 pp), MIT18100C_Practice-Final.pdf (2 pp), "
     "MIT18100C_Practice-Midterm1.pdf (3 pp), MIT18100C_Practice-Midterm2.pdf (2 pp). English, "
     "proof-heavy, includes metric-space material this script does not have",
     "selected — low priority", "transfer unit only"),
    ("material://source-analysis-grundlagen-handouts/Mengen-und-Abbildungen.pdf", 22,
     "Set and mapping prerequisite handout", "selected", "ch01"),
    ("material://source-analysis-grundlagen-handouts/Relationen.pdf", 9,
     "Relations prerequisite handout", "selected", "ch01"),
    ("material://source-analysis-grundlagen-handouts/Maths220_Proofs-in-Calculus.pdf", 17,
     "How a limit or convergence proof is written", "selected", "transfer unit (calibrate, anx)"),
    ("material://source-ableitinger-musterloesungen/ableitinger.pdf", 282,
     "Musterlösungen with the solving process named and annotated; §§6.1-6.10 are Analysis 1 "
     "topics, §§7.1-7.3 cover function limits and integration methods",
     "selected", "ch03, ch04, ch05, ch06, ch07, transfer unit"),
    ("material://source-abbott-understanding-analysis/abbott.pdf", 320,
     "Understanding Analysis; each chapter opens with a motivating discussion",
     "reference-only", "ch02, ch03, ch04, ch05, ch06, ch07"),
    ("material://source-lebl-basic-analysis/realanal.pdf", 312,
     "Basic Analysis I, one-variable; section order closest to the script",
     "reference-only", "ch02, ch03, ch04, ch05, ch06, ch07"),
    ("material://source-lebl-basic-analysis/realanal2.pdf", 217,
     "Basic Analysis II, multivariable", "off-scope", "none"),
    ("material://source-grieser-analysis1/grieser.pdf", 353,
     "Analysis I (German), exercises carry Hinweise and Lösungen from p. 329",
     "reference-only", "ch02, ch03, ch04, ch05, ch06, ch07"),
    ("material://source-mfnf-analysis1/MfNF_Analysis-1.pdf", 383,
     "Mathe für Nicht-Freaks, Analysis 1 (German, open); one titled section per proof "
     "obligation", "reference-only — depth/scope unassessed", "ch02, ch03, ch04, ch05, ch06, ch07"),
    ("material://source-ross-elementary-analysis/Ross_Elementary-Analysis_2ed.pdf", 416,
     "Elementary Analysis, short numbered sections; §35 Riemann-Stieltjes is out of scope",
     "reference-only — depth/scope unassessed", "ch02, ch03, ch04, ch05, ch06, ch07"),
    ("material://source-labs-schreyer-mathe-informatiker/"
     "Labs-Schreyer_Mathematik-fuer-Informatiker.pdf", 669,
     "Mathematik für Informatiker; Teil I is the M1 prerequisite block, Teil II a complete "
     "one-variable Analysis in the script's order",
     "reference-only — depth/scope unassessed", "ch01, ch02, ch03, ch04, ch05, ch06, ch07"),
    ("material://source-mit-18100a/mit18_100af20_lec_full2.pdf", 92,
     "MIT 18.100A complete lecture notes, 25 titled lectures",
     "selected — one blocked idea at a time", "ch02, ch03, ch04, ch05, ch06, ch07"),
    ("material://source-thomas-calculus/Thomas-Calculus_Early-Transcendentals.pdf", 1205,
     "Large computational calculus text",
     "reference-only — depth/scope unassessed", "ch03, ch04, ch05, ch06, ch07"),
    ("material://source-stewart-calculus/Stewart.pdf", 1404,
     "Large computational calculus text; §7.5 and §11.7 are strategy sections",
     "reference-only — depth/scope unassessed", "ch03, ch04, ch05, ch06, ch07"),
    ("material://source-strang-calculus/static_resources/mitres_18_001_f17_ch05.pdf", 56,
     "Strang Calculus, Integrals — the chapter PDFs ch00-ch16 are individually inventoried in "
     "the 2026-08-03 audit; only ch05, ch07 and ch10 are marked selected, ch02-ch04 and ch06 "
     "are reserve intuition, ch08-ch16 are multivariable and off-scope",
     "selected / reserve / off-scope", "ch05, ch06, ch07"),
    ("material://source-velleman-how-to-prove-it/Velleman_How-To-Prove-It.pdf", 569,
     "How To Prove It; Ch 6 induction and recursion, Summary of Proof Techniques p. 555",
     "reference-only — depth/scope unassessed", "ch01, transfer unit (calibrate)"),
    ("material://source-ohlbach-eisinger-beweise/"
     "Ohlbach-Eisinger_Design-Patterns-fuer-mathematische-Beweise.pdf", 183,
     "German catalogue of proof patterns; Teil II (transfinite ordinals) is out of scope",
     "reference-only — depth/scope unassessed", "ch01, transfer unit (calibrate)"),
    ("material://source-rudin-principles/Rudin_Principles-of-Mathematical-Analysis_3ed.pdf", 351,
     "Principles of Mathematical Analysis; proof-dense, weak text layer",
     "deferred — post-exam", "none"),
]

LINKED_INVENTORY = [
    ("source-professor-leonard", "Professor Leonard — Calculus 1 and Calculus 2 (video)",
     "No local copy. Selected by topic from the list already recorded on the source; the "
     "per-chapter split below re-partitions that list and adds no new claim about the videos.",
     "ch03, ch04, ch05, ch06, ch07"),
    ("source-3b1b-essence-of-calculus", "3Blue1Brown — Essence of Calculus (video)",
     "No local copy. Same treatment: the episodes named were already on the source record; "
     "this pass assigns each to the chapter it serves.", "ch05, ch06, ch07"),
    ("HU Moodle course", "Current lecture decks, recordings, and any Chapter 6-7 exercise sheets",
     "Private and inaccessible; unresolved since 2026-08-03 with no owner and no date. This is "
     "the single gap that, if closed, would retire most of the substitute practice on ch06 and "
     "ch07.", "unresolved"),
]


def audit_markdown(maps: dict[str, dict]) -> str:
    out = [f"# Analysis chapter-plan coverage audit — {DATE}", "",
           f"Plan package: `work/active/{WORKSPACE_ID}/outputs/Analysis-chapter-plan-{DATE}.yaml`",
           "",
           "Scope authority: `material://source-analysis-skript/unser skript.pdf` "
           "(Stand 04.02.2025), chosen by the learner. Its own course contract binds: "
           "Wiederholung is required, Ausflug is exam-light application context, Exkurs is not "
           "exam-relevant, and definitions, results and application take priority over proof "
           "reproduction.", "",
           "What this pass changed: the Analysis half moves from one unit with eleven "
           "hand-written stages to one unit per script chapter with one stage per script "
           "section, and every material route is re-cut per chapter with an `angle` and an "
           "`angle_detail`. Section titles and page numbers come from the script's own "
           "Inhaltsverzeichnis (PDF pp. 2-3); every other locator was read out of the source "
           "PDF on 2026-08-29 via its outline or its printed table of contents.", "",
           "Exkurs sections carry no stage and no material menu: the script states they are not "
           "exam-relevant, so they are recorded once in the transfer unit's deferral ledger and "
           "handled lightly (learner instruction, 2026-08-29). Ausflug sections keep a stage, "
           "because the contract puts them in scope at overview depth and two of them "
           "(§3.3, §3.8) are examined by current HU sheets.", "",
           "## Local material inventory", "",
           "Every PDF below was opened on 2026-08-29 — outline extraction, printed table of "
           "contents, or page text — and its section structure recorded before it was routed. "
           "No routing decision was taken from a filename or a page count.", "",
           "| Locator | Pages | What it actually contains | Disposition | Routed to |",
           "|---|---|---|---|---|"]
    for locator, pages, contents, disposition, routed in LOCAL_INVENTORY:
        pg = str(pages) if pages else "n/a"
        out.append(f"| `{md_escape(locator)}` | {pg} | {md_escape(contents)} | "
                   f"{md_escape(disposition)} | {md_escape(routed)} |")
    out += ["", "## Linked and unresolved material", "",
            "| Source | What it is | Evidence and limits | Routed to |", "|---|---|---|---|"]
    for sid, what, evidence, routed in LINKED_INVENTORY:
        out.append(f"| `{md_escape(sid)}` | {md_escape(what)} | {md_escape(evidence)} | "
                   f"{md_escape(routed)} |")
    out += ["", "## Current and prior scope reconciliation", "",
            "| Current asset | Alternate | Relation | Decision |", "|---|---|---|---|",
            "| `unser skript.pdf` (04.02.2025, 258 pp) | "
            "`rabus-skript_kapitel-2_stand-2024-10.pdf` (49 pp) | Earlier partial build, "
            "different pagination | Current script defines scope; the older file is routed "
            "nowhere |",
            "| HU Serien 05-09 + WV (WiSe 2024/25) | external drill and exam banks | HU sheets "
            "match the script's numbering and this examiner's wording | HU first on every "
            "chapter it reaches; external material is a substitute and is labelled as one |",
            "| Split Strang chapter PDFs | `mitres_18_001_f17_full_book.pdf` | Same content, "
            "different packaging | Chapter PDFs routed; the full book is a duplicate |",
            "| `'Aufgabe 3 ist gut.pdf'` recorded as unsolved | the file itself | The file is "
            "titled 'Lösungen zur Probeklausur 1' and every task is worked | **Corrected "
            "2026-08-29**: it is a solved paper, moved out of the unseen-papers set |",
            "| `kleine_beweise.pdf` routed only to calibrate/AN.X | the file itself | It is "
            "organised by script chapter, 3 through 7 | **Corrected 2026-08-29**: now routed "
            "to each of those chapter units as well |",
            "",
            "## Explicit exclusions and unresolved gaps", "",
            "| Item | Disposition | Evidence | Revisit condition |", "|---|---|---|---|",
            "| Every `Exkurs` section and Kapitel 8 | deferred, handled lightly | script "
            "p. vii states Exkurse are not exam-relevant; learner instruction 2026-08-29 | if "
            "the lecturer changes scope |",
            "| Proof reproduction as a default track | off-scope | script p. vi: 'Die Beweise "
            "müssen Sie nicht können' | repair only when a failed application exposes a gap |",
            "| Current HU exercise sheets for Kapitel 6 and 7 | **unresolved** | the local HU "
            "set stops at §5.5 | replace the substitutes if Moodle supplies matching sheets |",
            "| An HU-format full Analysis mock | **unresolved** | the WV set covers Kapitel 1-5 "
            "only | add when Moodle or the Fachschaft supplies one |",
            "| Current lecture decks or recordings | **unresolved** | none exist in the local "
            "Analysis root; the script says it does not exactly reproduce lecture scope | "
            "reconcile if decks become available |",
            "| Rudin; Lebl II; Strang ch08-ch16; Deitmar Kap. 8-20; Ross §35; Grieser Kap. 6, "
            "13, 14 | deferred / off-scope | opened contents exceed the one-variable script | "
            "post-exam |",
            "| Depth and scope for MfNF, Ross, Labs/Schreyer, Thomas, Stewart, Velleman, "
            "Ohlbach | left `unassessed` / `unevaluated` | locators were sharpened to chapter "
            "level; a contextual evaluation is a judgment that needs review (CLAUDE.md §4) | "
            "repay on first use (WORKFLOWS §6a) |",
            "",
            "## Unit and stage coverage matrix", "",
            "| Unit | Script sections | Stages | Material rows | Current HU practice |",
            "|---|---|---|---|---|"]
    hu = {
        "unit-m2-analysis-ch01": "Serie 05.1(c) only",
        "unit-m2-analysis-ch02": "Serie 05.4 only",
        "unit-m2-analysis-ch03": "Serien 05, 06, 07 + WV1.1",
        "unit-m2-analysis-ch04": "Serie 08.1-8.3 + WV1.3",
        "unit-m2-analysis-ch05": "Serie 08.4, Serie 09 + WV1.2, WV1.4",
        "unit-m2-analysis-ch06": "**none — substitutes only**",
        "unit-m2-analysis-ch07": "**none — substitutes only**",
        OLD_UNIT: "WV set, timed",
    }
    for spec in ALL_UNITS:
        uid = spec["unit_id"]
        record = maps[uid]
        pages = spec.get("pages")
        span = (f"printed pp. {pages[0]}-{pages[1]}" if pages
                else "course contract pp. iv-vii; deferral ledger")
        out.append(f"| `{uid}` | {span} | {len(record['stages'])} | "
                   f"{sum(len(s['resources']) for s in record['stages'])} | {hu[uid]} |")
    out += ["", "## Completeness", "",
            "- [x] Every PDF under the declared local Analysis roots has an inventory row.",
            "- [x] Every source routed to an Analysis unit was opened on 2026-08-29 and its "
            "section structure recorded before routing.",
            "- [x] Current and prior scope reconciled; two pre-existing records corrected.",
            "- [x] Duplicates and version relations recorded.",
            "- [x] Exclusions and unresolved gaps recorded, including the two chapters with no "
            "current HU practice.",
            "- [x] Every knowledge node carries at least one material route "
            "(enforced by the assembler's own preflight).", "",
            "No claim of mastery or readiness is made anywhere in this document.", ""]
    return "\n".join(out) + "\n"


def main() -> int:
    import assemble_lecture_study_maps as asm
    asm.NODE_CONCEPTS.update(NEW_NODE_CONCEPTS)

    repo = load_repo(REPO)
    manifest = _manifest(REPO)
    phrases = concept_phrases(manifest["records"])

    units = [unit_record(spec) for spec in ALL_UNITS]
    source_map = patched_source_map(repo)
    maps = assemble(units, source_map, phrases)

    MAP_DIR.mkdir(parents=True, exist_ok=True)
    for uid, record in maps.items():
        (MAP_DIR / f"{uid}.study-map.yaml").write_text(dump_yaml(record), encoding="utf-8")

    AUDIT_PATH.write_text(audit_markdown(maps), encoding="utf-8")
    OVERVIEW_PATH.write_text(overview_markdown(maps), encoding="utf-8")

    package = plan_package(units, source_map, maps, repo)
    PLAN_PATH.write_text(dump_yaml(package), encoding="utf-8")

    total_rows = sum(len(s["resources"]) for m in maps.values() for s in m["stages"])
    total_stages = sum(len(m["stages"]) for m in maps.values())
    print(f"{len(units)} units, {total_stages} stages, {len(ROUTE_ROWS)} routes, "
          f"{total_rows} resource rows")
    print(f"plan  -> {PLAN_PATH.relative_to(REPO)}")
    print(f"maps  -> {MAP_DIR.relative_to(REPO)}")
    print(f"audit -> {AUDIT_PATH.relative_to(REPO)}")
    print(f"read  -> {OVERVIEW_PATH.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
