#!/usr/bin/env python3
"""Assemble one study map per lecture unit from records that already exist.

Nothing here is invented. Every unit already carries an authored knowledge map
(what the lecture covers, node by node, with dependencies) and every material
route in the module source map already declares the nodes it `covers`, the
angle it takes, its depth and its scope status. A lecture study map is the
ordered join of those two: one stage per knowledge node, carrying every route
that reaches it.

Two authoring rules come from the learner's standing instruction of 2026-08-22,
recorded in `AML-plan-fix-2026-08-22.md`:

  * "give each stage the set of all possible materials and the angle they
    highlight" — so a stage takes every route covering its node, not a chosen
    few; and
  * "do not plan time per stage" — so `estimate_minutes` is never written. A
    constant estimate is worse than an absent field, because it looks like
    information.

Usage:
    python tools/assemble_lecture_study_maps.py --out DIR [--unit UNIT_ID ...]
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import yaml

from learning_os.contracts import (
    ContractValidationError,
    PlanTemplateError,
    require_current_template,
    validate_contract,
)
from learning_os.genout import build_backlinks, build_manifest
from learning_os.loader import load_repo

REPO = Path(__file__).resolve().parents[1]

# Route `format` says what the material is; `depth` says what it is for. Kind is
# the learner-facing verb, so depth wins when the two disagree: an
# advanced-reference book chapter is something you consult, not something you
# read through.
_KIND_BY_FORMAT = {
    "video": "watch",
    "exercise": "practise",
    "course-material": "read",
    "course": "read",
    "book": "read",
    "paper": "read",
    "documentation": "reference",
}


def _kind(route: dict) -> str:
    if route.get("depth") == "advanced-reference":
        return "reference"
    return _KIND_BY_FORMAT.get(str(route.get("format") or ""), "read")


def _triage(route: dict) -> str:
    """Scope status decides how hard a route is claimed, never its format.

    `current` is the taught deck for this lecture and is the scope authority
    (SOP Gate 2). Everything else supports it, and prior-year material is only
    ever practice or reference — the SOP forbids treating it as scope evidence.
    """
    scope = str(route.get("scope") or "")
    depth = str(route.get("depth") or "")
    if scope == "current":
        return "required-now"
    if depth == "advanced-reference":
        return "reference-only"
    if scope in {"superseded", "out-of-scope"}:
        return "reference-only"
    if scope == "prior-year":
        return "helpful-now" if depth == "practice" else "reference-only"
    return "helpful-now"


def _stage_id(node_id: str) -> str:
    return "stage-" + re.sub(r"^knowledge-", "", str(node_id))


def _order_nodes(nodes: list[dict]) -> list[dict]:
    """Authored order, adjusted only so a node never precedes what it builds on.

    A stable topological pass rather than a sort: the deck's own sequence is the
    lecture's argument, and the dependency edges only ever move a node later.
    """
    remaining = list(nodes)
    placed: list[dict] = []
    seen: set[str] = set()
    while remaining:
        progressed = False
        for node in list(remaining):
            deps = {d for d in (node.get("builds_on") or [])
                    if any(other["id"] == d for other in nodes)}
            if deps <= seen:
                placed.append(node)
                seen.add(node["id"])
                remaining.remove(node)
                progressed = True
        if not progressed:
            # A dependency cycle is authored data, not something to resolve
            # silently: keep the remaining nodes in their authored order and
            # let the reader see the original sequence.
            placed.extend(remaining)
            break
    return placed


def concept_phrases(records: list[dict]) -> dict[str, list[str]]:
    """Every registered name a concept goes by: its id, its title, its aliases.

    Matching on the id slug alone finds almost nothing — `concept-probability`
    is written "probability axioms" in the deck, and that string lives in the
    concept's aliases, not its id.
    """
    phrases: dict[str, list[str]] = {}
    for row in records:
        cid = str(row.get("id") or "")
        if not cid.startswith("concept-") or row.get("deprecated"):
            continue
        names = [cid.removeprefix("concept-").replace("-", " "),
                 str(row.get("title") or "")]
        names += [str(alias) for alias in (row.get("aliases") or [])]
        phrases[cid] = sorted({
            _norm(name) for name in names if len(name.strip()) >= 8
        })
    return {cid: names for cid, names in phrases.items() if names}


def _norm(text: str) -> str:
    """Apostrophes vary between the decks and the concept register — "Bayes'
    theorem" against "Bayes theorem" — and never carry meaning here."""
    return re.sub(r"['’]", "", str(text).strip().lower())


# Curated node → concept edges, 2026-08-22.
#
# The automatic matcher is deliberately conservative and reached 85 of 182
# stages; the rest name their concept in words the register spells differently
# ("1-NN and k-NN prediction" against `concept-k-nearest-neighbors`) or teach
# something the register had never been asked to name. Nineteen concepts were
# registered to close the second case. This table is the judgement, written
# down where it can be argued with rather than buried in a regex.
#
# Merged with, not instead of, the automatic match: an entry here adds edges,
# and a later deck revision that renames a node loses its curation loudly
# rather than silently keeping a stale one.
NODE_CONCEPTS: dict[str, tuple[str, ...]] = {
    # ---- AML: foundations
    "knowledge-aml-l01-history": (
        "concept-perceptron", "concept-xor-problem", "concept-backpropagation",
        "concept-convolutional-networks", "concept-recurrent-networks",
        "concept-transformer"),
    "knowledge-aml-l01-formulation": ("concept-supervised-learning",),
    "knowledge-aml-l01-data": ("concept-embedding", "concept-linear-algebra"),
    "knowledge-aml-l01-prerequisites": ("concept-linear-algebra", "concept-python"),
    "knowledge-aml-l02-representation": (
        "concept-embedding", "concept-k-nearest-neighbors"),
    "knowledge-aml-l02-algorithm": ("concept-k-nearest-neighbors",),
    "knowledge-aml-l02-distance": (
        "concept-k-nearest-neighbors", "concept-distance-metrics",
        "concept-feature-scaling"),
    "knowledge-aml-l03-problem": ("concept-linear-regression",),
    "knowledge-aml-l03-loss": ("concept-mean-squared-error",),
    "knowledge-aml-l03-solution": (
        "concept-normal-equation", "concept-linear-regression"),
    "knowledge-aml-l03-linear-algebra": ("concept-linear-algebra",),
    "knowledge-aml-l03-vectorization": (
        "concept-linear-algebra", "concept-linear-regression"),
    # ---- AML: optimization and classifiers
    "knowledge-aml-l06-gradient": ("concept-gradient-descent", "concept-convexity"),
    "knowledge-aml-l06-stochastic": ("concept-gradient-descent",),
    "knowledge-aml-l06-newton": ("concept-newton-method", "concept-gradient-descent"),
    "knowledge-aml-l07-linear-geometry": ("concept-decision-boundary",),
    "knowledge-aml-l07-xor": ("concept-xor-problem", "concept-perceptron"),
    "knowledge-aml-l07-rbf": (
        "concept-kernel-trick", "concept-bias-variance-tradeoff"),
    # ---- AML: networks
    "knowledge-aml-l08-xor-stacking": (
        "concept-xor-problem", "concept-neural-network"),
    "knowledge-aml-l08-forward": ("concept-neural-network", "concept-linear-algebra"),
    "knowledge-aml-l08-activations": (
        "concept-activation-function", "concept-neural-network", "concept-sigmoid"),
    "knowledge-aml-l08-output": (
        "concept-softmax", "concept-sigmoid", "concept-cross-entropy"),
    "knowledge-aml-l09-graph": ("concept-backpropagation", "concept-chain-rule"),
    "knowledge-aml-l09-gradient-health": (
        "concept-vanishing-gradients", "concept-backpropagation"),
    "knowledge-aml-l10-motivation": ("concept-convolutional-networks",),
    "knowledge-aml-l10-shapes": ("concept-convolutional-networks",),
    "knowledge-aml-l10-pooling": ("concept-convolutional-networks",),
    "knowledge-aml-l10-network": ("concept-convolutional-networks",),
    "knowledge-aml-l10-architectures": (
        "concept-convolutional-networks", "concept-residual-connection"),
    "knowledge-aml-l11-tokenization": ("concept-tokenization",),
    "knowledge-aml-l11-embeddings": (
        "concept-embedding", "concept-contextual-embedding"),
    "knowledge-aml-l11-position": (
        "concept-positional-encoding", "concept-attention"),
    "knowledge-aml-l11-training": (
        "concept-language-modelling", "concept-cross-entropy", "concept-softmax"),
    # ---- SaD: descriptive statistics
    "knowledge-sad-l01-data-questions": ("concept-descriptive-statistics",),
    "knowledge-sad-l01-location": ("concept-descriptive-statistics",),
    "knowledge-sad-l01-distributions": ("concept-descriptive-statistics",),
    "knowledge-sad-l01-sampling-context": (
        "concept-sampling-bias", "concept-descriptive-statistics"),
    "knowledge-sad-l02-vocabulary": ("concept-descriptive-statistics",),
    "knowledge-sad-l02-scales": ("concept-descriptive-statistics",),
    "knowledge-sad-l02-frequencies": ("concept-descriptive-statistics",),
    "knowledge-sad-l02-location": ("concept-descriptive-statistics",),
    "knowledge-sad-l02-simpson": ("concept-simpsons-paradox",),
    "knowledge-sad-l02-sampling": ("concept-sampling-bias",),
    "knowledge-sad-l03-paired-data": ("concept-correlation",),
    "knowledge-sad-l03-scaling-weights": (
        "concept-linear-regression", "concept-feature-scaling"),
    # ---- SaD: probability
    "knowledge-sad-l04-events": ("concept-probability",),
    "knowledge-sad-l04-bayes": (
        "concept-bayes-theorem", "concept-conditional-probability"),
    "knowledge-sad-l04-independence": (
        "concept-conditional-independence", "concept-probability"),
    "knowledge-sad-l05-permutations": ("concept-combinatorics",),
    "knowledge-sad-l05-variations": ("concept-combinatorics",),
    "knowledge-sad-l05-combinations": ("concept-combinatorics",),
    "knowledge-sad-l05-repetition": ("concept-combinatorics",),
    "knowledge-sad-l05-identities": ("concept-combinatorics",),
    "knowledge-sad-l06-distribution-functions": ("concept-random-variable",),
    "knowledge-sad-l06-transformations": ("concept-random-variable",),
    "knowledge-sad-l06-sample-mean": (
        "concept-expected-value", "concept-variance", "concept-random-variable"),
    "knowledge-sad-l06-concentration": ("concept-law-of-large-numbers",),
    "knowledge-sad-l07-model-selection": ("concept-discrete-distributions",),
    "knowledge-sad-l07-hypergeometric": ("concept-discrete-distributions",),
    "knowledge-sad-l07-geometric": ("concept-discrete-distributions",),
    "knowledge-sad-l07-poisson": ("concept-discrete-distributions",),
    "knowledge-sad-l07-relationships": (
        "concept-discrete-distributions", "concept-expected-value",
        "concept-variance"),
    "knowledge-sad-l08-normal": ("concept-normal-distribution",),
    "knowledge-sad-l08-transform-sum": (
        "concept-normal-distribution", "concept-variance"),
    "knowledge-sad-l08-approximation": (
        "concept-normal-distribution", "concept-central-limit-theorem"),
    # ---- SaD: inference
    "knowledge-sad-l09-estimator": ("concept-statistical-estimation",),
    "knowledge-sad-l09-z-interval": ("concept-statistical-estimation",),
    "knowledge-sad-l09-t-interval": ("concept-statistical-estimation",),
    "knowledge-sad-l09-data-bias": (
        "concept-sampling-bias", "concept-statistical-estimation"),
    "knowledge-sad-l10-test-model": ("concept-hypothesis-testing",),
    "knowledge-sad-l10-tails-pvalue": ("concept-hypothesis-testing",),
    "knowledge-sad-l10-errors-power": ("concept-hypothesis-testing",),
    "knowledge-sad-l10-z-t": (
        "concept-hypothesis-testing", "concept-normal-distribution"),
    "knowledge-sad-l10-chi-square": (
        "concept-chi-square-test", "concept-hypothesis-testing"),
    "knowledge-sad-l10-nonparametric": (
        "concept-nonparametric-tests", "concept-hypothesis-testing"),
    "knowledge-sad-l10-multiple": (
        "concept-multiple-testing", "concept-hypothesis-testing"),
    # ---- SaD: machine learning
    "knowledge-sad-l11-tasks": ("concept-supervised-learning",),
    "knowledge-sad-l11-representation": ("concept-supervised-learning",),
    "knowledge-sad-l11-objectives": (
        "concept-supervised-learning", "concept-regularization"),
    "knowledge-sad-l11-evaluation": ("concept-classification-metrics",),
    "knowledge-sad-l12-pruning": ("concept-decision-trees",),
    "knowledge-sad-l12-stacking": ("concept-ensemble-methods",),
    "knowledge-sad-l13-aggregation": ("concept-k-nearest-neighbors",),
    "knowledge-sad-l13-metrics": ("concept-distance-metrics",),
    "knowledge-sad-l13-special-measures": ("concept-distance-metrics",),
    "knowledge-sad-l13-exact-indexing": (
        "concept-similarity-search", "concept-k-nearest-neighbors"),
    "knowledge-sad-l14-numeric": (
        "concept-naive-bayes", "concept-gaussian-naive-bayes"),
    "knowledge-sad-l14-bayes-net": ("concept-bayesian-network",),
    "knowledge-sad-l14-markov": (
        "concept-conditional-independence", "concept-bayesian-network"),
    "knowledge-sad-l15-activation": (
        "concept-activation-function", "concept-xor-problem",
        "concept-neural-network"),
    "knowledge-sad-l15-output": ("concept-softmax", "concept-neural-network"),
    "knowledge-sad-l15-forward": (
        "concept-neural-network", "concept-linear-algebra"),
    "knowledge-sad-l15-universality": ("concept-universal-approximation",),
    # ---- SaD: clustering
    "knowledge-sad-clustering-unsupervised": (
        "concept-clustering", "concept-supervised-learning"),
    "knowledge-sad-clustering-kmeans": ("concept-k-means", "concept-clustering"),
    "knowledge-sad-clustering-initialization": (
        "concept-k-means", "concept-clustering"),
    "knowledge-sad-clustering-evaluation": (
        "concept-clustering", "concept-distance-metrics"),
    # Its title names the three families rather than a registered concept, so
    # the automatic matcher finds nothing on it.
    "knowledge-sad-clustering-families": ("concept-clustering",),
    # ---- M2 Analysis: one unit per script chapter (2026-08-29)
    #
    # The automatic matcher fires on registered concept names appearing in a
    # node title. These titles are the script's own German section headings
    # ("Konvergenzkriterien für Folgen", "Das Riemann-Integral"), which the
    # register spells differently, so the edges are curated here instead.
    "knowledge-m2-analysis-ch01-zahlenmengen": ("concept-real-numbers",),
    "knowledge-m2-analysis-ch01-induktion": ("concept-proof-technique",),
    "knowledge-m2-analysis-ch01-beziehungen": (
        "concept-proof-technique", "concept-real-numbers"),
    "knowledge-m2-analysis-ch02-koerperaxiome": ("concept-real-numbers",),
    "knowledge-m2-analysis-ch02-anordnung": ("concept-real-numbers",),
    "knowledge-m2-analysis-ch02-intervalle-betrag": ("concept-real-numbers",),
    "knowledge-m2-analysis-ch02-supremum-infimum": ("concept-real-numbers",),
    "knowledge-m2-analysis-ch02-vollstaendigkeitsaxiom": ("concept-real-numbers",),
    "knowledge-m2-analysis-ch02-folgerungen": ("concept-real-numbers",),
    "knowledge-m2-analysis-ch02-potenzen-wurzeln": ("concept-real-numbers",),
    "knowledge-m2-analysis-ch02-maschinenzahlen": ("concept-real-numbers",),
    "knowledge-m2-analysis-ch03-folgen": ("concept-sequences-convergence",),
    "knowledge-m2-analysis-ch03-rekursionen": (
        "concept-sequences-convergence", "concept-proof-technique"),
    "knowledge-m2-analysis-ch03-konvergenzkriterien": ("concept-sequences-convergence",),
    "knowledge-m2-analysis-ch03-rechenregeln": ("concept-sequences-convergence",),
    "knowledge-m2-analysis-ch03-bestimmte-divergenz": ("concept-sequences-convergence",),
    "knowledge-m2-analysis-ch03-quadratwurzel": (
        "concept-sequences-convergence", "concept-real-numbers"),
    "knowledge-m2-analysis-ch04-reihen": ("concept-series",),
    "knowledge-m2-analysis-ch04-konvergenzkriterien": ("concept-series",),
    "knowledge-m2-analysis-ch04-absolute-konvergenz": ("concept-series",),
    "knowledge-m2-analysis-ch04-umordnungen": ("concept-series",),
    "knowledge-m2-analysis-ch05-funktionsgrenzwerte": ("concept-limits-continuity",),
    "knowledge-m2-analysis-ch05-einseitige-grenzwerte": ("concept-limits-continuity",),
    "knowledge-m2-analysis-ch05-stetigkeit": ("concept-limits-continuity",),
    "knowledge-m2-analysis-ch05-zwischenwertsatz": ("concept-limits-continuity",),
    "knowledge-m2-analysis-ch05-kompakte-intervalle": ("concept-limits-continuity",),
    "knowledge-m2-analysis-ch05-exponentialfunktion": (
        "concept-limits-continuity", "concept-series"),
    "knowledge-m2-analysis-ch05-gleichmaessige-konvergenz": ("concept-uniform-convergence",),
    "knowledge-m2-analysis-ch06-differenzierbarkeit": ("concept-differentiation",),
    "knowledge-m2-analysis-ch06-mittelwertsatz": ("concept-differentiation",),
    "knowledge-m2-analysis-ch06-trigonometrie": ("concept-differentiation",),
    "knowledge-m2-analysis-ch06-hospital": ("concept-differentiation",),
    "knowledge-m2-analysis-ch06-hoehere-ableitungen": ("concept-differentiation",),
    "knowledge-m2-analysis-ch06-taylor": ("concept-taylor-series",),
    "knowledge-m2-analysis-ch06-interpolation": ("concept-taylor-series",),
    "knowledge-m2-analysis-ch07-riemann-integral": ("concept-riemann-integral",),
    "knowledge-m2-analysis-ch07-hauptsatz": ("concept-riemann-integral",),
    "knowledge-m2-analysis-ch07-uneigentliche-integrale": ("concept-riemann-integral",),
    "knowledge-m2-analysis-calibrate": ("concept-proof-technique",),
    "knowledge-m2-analysis-anx": ("concept-proof-technique",),
    "knowledge-m2-analysis-exkurse": ("concept-asymptotic-analysis",),
}


def _concepts(node: dict, phrases: dict[str, list[str]]) -> list[str]:
    """Tag on the node's title, or on a multi-word name in its summary.

    Conservative on purpose, and asymmetric on purpose. A wrong concept tag is
    worse than a missing one: concept coverage is how the system decides what it
    does not need to teach again, so a false positive silently suppresses
    material the learner has not actually seen. A title says what the node *is*,
    so any registered name there is trustworthy. A summary often *mentions* a
    concept it does not teach — L01's history node names backpropagation as a
    landmark — so a single word there is refused and only a multi-word name,
    which is far harder to hit incidentally, is accepted.
    """
    title = _norm(node.get("title", ""))
    summary = _norm(node.get("summary", ""))
    hits = list(NODE_CONCEPTS.get(str(node.get("id") or ""), ()))
    for cid, names in phrases.items():
        for name in names:
            pattern = rf"\b{re.escape(name)}\b"
            if re.search(pattern, title) or (
                " " in name and re.search(pattern, summary)
            ):
                hits.append(cid)
                break
    return sorted(set(hits))


def _done_when(node: dict, routes: list[dict]) -> list[str]:
    """One retrieval criterion and, where the menu allows it, one application.

    The retrieval criterion carries the node's authored summary verbatim, so it
    is specific to this node rather than a template sentence repeated across
    the module. The application criterion is written only when a practice route
    actually reaches the node, and it names that material — a proof criterion
    that names nothing is the boilerplate this system already has too much of.
    """
    summary = str(node.get("summary") or "").strip()
    criteria = [f"Reproduce without notes: {summary}"]
    practice = [r for r in routes if _kind(r) == "practise"]
    if practice:
        named = practice[0].get("title") or "the practice material on this stage"
        more = f", then the remaining {len(practice) - 1}" if len(practice) > 1 else ""
        criteria.append(
            f"Work {named}{more}, and record every miss with the step it failed at."
        )
    return criteria


def _resource(route: dict) -> dict:
    row: dict = {"kind": _kind(route), "label": str(route.get("title") or "").strip()}
    # The route id is the stage's only stable pointer back to the material it
    # came from. Without it a stage resource is matched downstream by source id
    # plus title, which fails closed on any ambiguity — so a stage displays a
    # required lecture with no way to open it even though the route resolves a
    # real file (2026-09-05 audit, F01). Titles are prose and may be edited;
    # the id survives that.
    route_id = str(route.get("id") or "").strip()
    if route_id.startswith("route-"):
        row["route_id"] = route_id
    if route.get("source_id"):
        row["source_id"] = route["source_id"]
    # The angle is why this material is on this stage rather than another. It
    # is the one field a menu without it becomes a list of names — so it is
    # carried as a field. Until 2026-08-23 it was concatenated onto `locator`
    # after an em dash, which meant nothing downstream could render it, sort by
    # it, or check that it was present: the 30% of rows missing one had to be
    # counted by string-searching for " — " (CRITIQUE-POINTS §1).
    locator = str(route.get("locator") or "").strip()
    if locator:
        row["locator"] = locator
    angle = str(route.get("angle") or "").strip()
    if angle:
        row["angle"] = angle
    angle_detail = str(route.get("angle_detail") or "").strip()
    if angle_detail:
        row["angle_detail"] = angle_detail
    if route.get("material_uri"):
        row["vault_path"] = route["material_uri"]
    # A web route's only openable target is its URL; dropping it here is how a
    # required web material reached a stage with no Open action at all.
    url = str(route.get("url") or "").strip()
    if url:
        row["url"] = url
    row["scope_triage"] = _triage(route)
    return row


def build(unit: dict, module_id: str, routes_for_unit: list[dict],
          phrases: dict[str, list[str]], exam_bearing: bool) -> dict:
    unit_id = unit["id"]
    slug = unit_id.removeprefix("unit-")
    nodes = _order_nodes((unit.get("knowledge_map") or {}).get("nodes") or [])
    if not nodes:
        raise ValueError(f"{unit_id} has no knowledge map to order")

    stages = []
    for number, node in enumerate(nodes, start=1):
        covering = [r for r in routes_for_unit
                    if node["id"] in (r.get("covers") or [])]
        stage_id = _stage_id(node["id"])
        stages.append({
            "id": stage_id,
            "number": number,
            "title": str(node.get("title") or "").strip(),
            "status": "pending",
            "objective": str(node.get("summary") or "").strip(),
            "done_when": _done_when(node, covering),
            "exam_critical": exam_bearing,
            "concepts": _concepts(node, phrases),
            "scope_triage": "required-now",
            "resources": [_resource(r) for r in covering],
            "working_note": (
                f"curriculum/modules/{module_id}/units/{unit_id}"
                f"/stages/{stage_id}/notes.md"
            ),
            "attachments": [],
            "source_feedback": [],
        })

    return {
        "id": f"study-map-{slug}",
        "type": "study-map",
        "plan_template_version": 1,
        "unit_id": unit_id,
        "status": "not-started",
        "current_stage": stages[0]["id"],
        # The source map is the authority these stages were assembled from:
        # it owns the node routing, the angles, the depths and the scope
        # statuses. Naming it keeps the provenance checkable.
        "source_plan": {
            "path": f"curriculum/modules/{module_id}/source-map.yaml",
            "provenance": "operator",
        },
        "detours": [],
        "shelving": {"state": "none"},
        "stages": stages,
    }


def _manifest(root: Path) -> dict:
    """Build the projection in memory; generated files are never authoring input."""
    repo = load_repo(root)
    generated_at = "lecture-study-map-assembly"
    return build_manifest(repo, generated_at, build_backlinks(repo, generated_at))


def curation_problems(manifest: dict) -> list[str]:
    """Keep the curated semantic edges attached to live nodes and concepts.

    The original workbench script claimed a renamed node would lose its
    curation loudly, but nothing actually checked for stale table keys. This
    check turns that statement into an invariant before any draft is written.
    """
    live_nodes = {
        str(node.get("id"))
        for unit in manifest.get("units", []) or []
        for node in (unit.get("knowledge_map") or {}).get("nodes", []) or []
        if isinstance(node, dict) and node.get("id")
    }
    live_concepts = {
        str(record.get("id"))
        for record in manifest.get("records", []) or []
        if isinstance(record, dict)
        and str(record.get("id") or "").startswith("concept-")
        and not record.get("deprecated")
    }
    problems = [
        f"curated concept mapping names a missing knowledge node: {node_id}"
        for node_id in sorted(set(NODE_CONCEPTS) - live_nodes)
    ]
    referenced = {concept_id for values in NODE_CONCEPTS.values() for concept_id in values}
    problems.extend(
        f"curated concept mapping names a missing or deprecated concept: {concept_id}"
        for concept_id in sorted(referenced - live_concepts)
    )
    return problems


def assembly_problems(unit: dict, routes: list[dict], record: dict) -> list[str]:
    """Refuse a draft that would hide material or become invisible to retrieval."""
    nodes = (unit.get("knowledge_map") or {}).get("nodes", []) or []
    uncovered = [
        str(node.get("id"))
        for node in nodes
        if isinstance(node, dict)
        and not any(node.get("id") in (route.get("covers") or []) for route in routes)
    ]
    untagged = [
        str(stage.get("id"))
        for stage in record.get("stages", []) or []
        if isinstance(stage, dict) and not (stage.get("concepts") or [])
    ]
    problems = [
        f"{unit.get('id')} knowledge node has no material route: {node_id}"
        for node_id in uncovered
    ]
    problems.extend(
        f"{unit.get('id')} stage has no concept coverage: {stage_id}"
        for stage_id in untagged
    )
    # Every row this assembler writes came from a route, so every row must
    # carry that route's id. A row that lost it can only be matched downstream
    # by source id plus title, and that match fails closed on any duplicate —
    # which is how required materials reached stages with no Open action.
    unbound = [
        f"{stage.get('id')}/{resource.get('label')}"
        for stage in record.get("stages", []) or []
        if isinstance(stage, dict)
        for resource in stage.get("resources", []) or []
        if isinstance(resource, dict)
        and not str(resource.get("route_id") or "").startswith("route-")
    ]
    problems.extend(
        f"{unit.get('id')} stage resource has no route identity: {row}"
        for row in unbound
    )
    return problems


def _atomic_draft(path: Path, content: str) -> None:
    tmp = path.with_name(f".{path.name}.tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(content, encoding="utf-8")
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=REPO)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--unit", action="append", default=[])
    args = parser.parse_args()

    root = args.root.expanduser().resolve()
    manifest = _manifest(root)
    units = {u["id"]: u for u in manifest["units"]}
    modules = {m["id"]: m for m in manifest["modules"]}
    source_maps = {s["id"]: s for s in manifest["module_source_maps"]}
    phrases = concept_phrases(manifest["records"])

    wanted = args.unit or [
        u["id"] for u in manifest["units"] if u.get("needs_study_map")
    ]
    problems = curation_problems(manifest)
    drafts: dict[Path, str] = {}
    for unit_id in sorted(wanted):
        unit = units.get(unit_id)
        if unit is None:
            problems.append(f"{unit_id}: not a projected unit")
            continue
        module_id = str(unit.get("module_id") or "")
        module = modules.get(module_id)
        source_map = source_maps.get(f"source-map-{module_id.removeprefix('module-')}")
        if module is None or source_map is None:
            problems.append(f"{unit_id}: no projected module or source map")
            continue
        routes = [route for entry in source_map.get("sources") or []
                  for route in (entry.get("unit_routes") or [])
                  if route.get("unit_id") == unit_id]
        if not routes:
            problems.append(f"{unit_id}: no material routes reach it")
            continue
        try:
            record = build(unit, module_id, routes, phrases,
                           bool(module.get("examination")))
        except ValueError as exc:
            problems.append(str(exc))
            continue
        problems.extend(assembly_problems(unit, routes, record))
        try:
            require_current_template(record, "curriculum")
            validate_contract(
                root,
                "study-map.schema.json",
                record,
                label=f"assembled study map for {unit_id}",
            )
        except (PlanTemplateError, ContractValidationError) as exc:
            problems.append(f"{unit_id}: {exc}")
            continue
        path = args.out.expanduser().resolve() / f"{unit_id}.study-map.yaml"
        drafts[path] = yaml.safe_dump(
            record, sort_keys=False, allow_unicode=True, width=100
        )
        print(f"{unit_id}: {len(record['stages'])} stages, "
              f"{sum(len(s['resources']) for s in record['stages'])} resource rows")

    if problems:
        print("assembly preflight failed; no draft files were written", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        return 2

    for path, content in drafts.items():
        _atomic_draft(path, content)
    print(f"\n{len(drafts)} study map(s) written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
