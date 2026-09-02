#!/usr/bin/env python3
"""Close the remaining M2 exact-locator debt through a governed plan package.

The edits below are keyed by stable route id.  Paginated local or official
PDFs use viewer-page numbers (cover = page 1).  Web courses and videos name an
exact published item.  The Swanson route is removed because the opened book is
about probabilistic logic and does not support the route's measurable-function
claim; inventing a better-looking locator would preserve a false judgment.
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
    _manifest,
    assembly_problems,
    build,
    concept_phrases,
)
from learning_os.contracts import require_current_template, validate_contract  # noqa: E402
from learning_os.loader import load_repo  # noqa: E402


MODULE_ID = "module-hu-m2-statistik-analysis"
WORKSPACE_ID = "workspace-m2-exam-prep"
DATE = "2026-09-01"
PLAN_PATH = OUT / f"M2-exact-locator-plan-{DATE}.yaml"
AUDIT_PATH = OUT / f"M2-exact-locator-coverage-audit-{DATE}.md"
MAP_DIR = OUT / f"M2-exact-locator-maps-{DATE}"


EDITS: dict[str, dict[str, str]] = {
    # Professor Leonard: exact public episode identities replace topic hunting.
    "route-an-ch03-professorleonard": {
        "locator": "Calculus 2 Lecture 9.1: 'Convergence and Divergence of Sequences'",
    },
    "route-an-ch04-professorleonard": {
        "locator": (
            "Calculus 2 Lecture 9.3: 'Using the Integral Test for "
            "Convergence/Divergence of Series, P-Series'"
        ),
    },
    "route-an-ch05-professorleonard": {
        "locator": "Calculus 1 Lecture 1.1: 'An Introduction to Limits'",
    },
    "route-an-ch06-professorleonard": {
        "locator": (
            "Calculus 1 Lecture 2.1: 'An Introduction to the Derivative'; "
            "Calculus 2 Lecture 10.10: 'Taylor and Maclaurin Series'"
        ),
    },
    "route-an-ch07-professorleonard": {
        "locator": (
            "Calculus 1 Lecture 4.5: 'The Fundamental Theorem of Calculus'; "
            "Calculus 2 Lecture 7.1: 'Integration By Parts'"
        ),
    },
    # 3Blue1Brown's titles are the episode addresses; there are no pages.
    "route-an-ch05-3b1bessenceofcalculus": {
        "locator": (
            "Chapter 7, Essence of calculus: 'Limits, L'Hôpital's rule, and "
            "epsilon delta definitions'"
        ),
    },
    "route-an-ch06-3b1bessenceofcalculus": {
        "locator": (
            "Chapter 2 'The paradox of the derivative'; Chapter 4 'Chain rule "
            "and product rule'; Chapter 7 'Limits, L'Hôpital's rule, and "
            "epsilon delta definitions'; Chapter 11 'Taylor series'"
        ),
    },
    "route-an-ch07-3b1bessenceofcalculus": {
        "locator": (
            "Chapter 8, Essence of calculus: 'Integration and the fundamental "
            "theorem of calculus'"
        ),
    },
    # Grinstead & Snell official PDF; viewer page = printed page + 8.
    "route-fe8b4fbc40e7e85daf8ef25b": {
        "locator": (
            "Official PDF, Ch 4 'Conditional Probability', §§4.1-4.3, PDF "
            "pp. 141-190"
        ),
    },
    "route-fa2f72cfc8de281124afb34d": {
        "locator": (
            "Official PDF, Ch 3 'Combinatorics', §§3.1-3.3, PDF pp. 83-140"
        ),
    },
    "route-30bde2200182449152e8a76a": {
        "locator": (
            "Official PDF, Ch 6 'Expected Value and Variance', §§6.1-6.3, "
            "PDF pp. 233-292"
        ),
    },
    "route-58f13d47b87582e36563f616": {
        "locator": (
            "Official PDF, Ch 5 'Distributions and Densities', §§5.1-5.2, "
            "PDF pp. 191-232"
        ),
    },
    "route-c58e4eb43dc4c166ca3c4822": {
        "locator": (
            "Official PDF, Ch 8 'Law of Large Numbers', PDF pp. 313-332, and "
            "Ch 9 'Central Limit Theorem', PDF pp. 333-372"
        ),
    },
    # The current Jurafsky release moved Naive Bayes from Ch 4 to Appendix B.
    "route-878acd203c5603b70539868d": {
        "title": "Jurafsky & Martin Appendix B — naive Bayes classification",
        "format": "website",
        "locator": (
            "August 19, 2026 release, Appendix B 'Naive Bayes "
            "Classification': classifier, training, and worked-example sections"
        ),
    },
    "route-c6ef21e8e56052473f0d7cef": {
        "title": "Jurafsky & Martin Appendix B — smoothing and evaluation",
        "format": "website",
        "locator": (
            "August 19, 2026 release, Appendix B 'Naive Bayes "
            "Classification': add-one smoothing, text event model, and "
            "evaluation sections"
        ),
    },
    # These publishers expose chapter HTML, so a website title is the truthful
    # address.  Keeping `book` would falsely promise edition-stable PDF pages.
    "route-bbf99a1908887e14e567f182": {
        "format": "website",
        "locator": (
            "Neural Networks and Deep Learning, Ch 1 'Using neural nets to "
            "recognize handwritten digits' and Ch 2 'How the backpropagation "
            "algorithm works'"
        ),
    },
    "route-04c9e37880237050c4ac3b25": {
        "format": "website",
        "locator": (
            "Neural Networks and Deep Learning, Ch 4 'A visual proof that "
            "neural nets can compute any function'"
        ),
    },
    "route-b252f1f176fedf4bbd32e974": {
        "format": "website",
        "locator": (
            "Dive into Deep Learning, 'Multilayer Perceptrons', "
            "'Implementation of Multilayer Perceptrons', and 'Forward "
            "Propagation, Backward Propagation, and Computational Graphs'"
        ),
    },
    "route-652350e4a873de885cb7f5bd": {
        "format": "website",
        "locator": (
            "Understanding Deep Learning, Ch 3 'Shallow Neural Networks' and "
            "Ch 4 'Deep Neural Networks', including the linked chapter notebooks"
        ),
    },
    "route-24a20095c2e04038e9907ea0": {
        "format": "website",
        "locator": (
            "Deep Learning online book, Ch 6 'Deep Feedforward Networks': "
            "§6.1 XOR, §6.2 gradient-based learning, §6.3 hidden units, and "
            "§6.5 back-propagation"
        ),
    },
    # Public courses and exercise banks: exact artifact, item, and page where
    # the artifact is paginated.
    "route-3857218e50e782951579fa76": {
        "locator": (
            "Spring 2026 Midterm Solutions, Question 1(ii)-(v), PDF pp. 3-4"
        ),
    },
    "route-cd624eec2c74722433fa56ea": {
        "locator": (
            "Fall 2024 Final Solutions, decision-tree and random-forest "
            "problem, PDF p. 9"
        ),
    },
    "route-c4a8afb529925b777fde9628": {
        "locator": (
            "MIT 6.041SC Unit IV, Lecture 19 'Weak Law of Large Numbers', "
            "Lecture 20 'Central Limit Theorem', and recitation 'Using the "
            "Central Limit Theorem'"
        ),
    },
    "route-9a418de23be3ffd147750581": {
        "locator": (
            "CS229 Problem Set #2, Problem 2 'Spam classification', especially "
            "part 2(b) multinomial Naive Bayes with Laplace smoothing; "
            "official ps2-sol.pdf"
        ),
    },
    "route-63f597ce7e7321c8ee2355d3": {
        "locator": (
            "MIT 6.036 Fall 2020 OCW, Unit 2 'Nearest Neighbors' and its "
            "exercises; Notes Ch 14 'Non-parametric methods'"
        ),
    },
    "route-f9b2e466618b722b3b41db6a": {
        "locator": (
            "MIT 6.036 Fall 2020 OCW, Unit 7 'Neural Networks' and Unit 8 "
            "'Backpropagation', with their exercises"
        ),
    },
    "route-b2cb82ed2840a70e81bfbaa5": {
        "locator": (
            "Machine Learning Specialization, Course 1 'Supervised Machine "
            "Learning: Regression and Classification', Week 1 'Linear "
            "regression model' and Week 2 'Multiple linear regression', "
            "'Feature scaling', and 'Choosing the learning rate'"
        ),
    },
    "route-024e86952ae27f3fe2fd451d": {
        "locator": (
            "Z Statistics 'Descriptive Statistics': 'The Mean', 'The Median', "
            "'The Mode', 'Range and IQR (Interquartile Range)', and 'Variance "
            "and Standard deviation'"
        ),
    },
    "route-5c3e138d6b1230dcb502e951": {
        "locator": "zedstatistics video 'What are confidence intervals? Actually.'",
    },
    "route-9bba0280753490bc6058ad4e": {
        "locator": "zedstatistics video 'Hypothesis testing (ALL YOU NEED TO KNOW!)'",
    },
    "route-9e8924fd776e576177b5fbd1": {
        "locator": (
            "Official Bishop PDF, Ch 8 'Graphical Models', PDF pp. 379-438: "
            "§8.1 'Bayesian Networks' p. 380, §8.2 'Conditional Independence' "
            "p. 392, and §8.2.2 'D-separation' p. 398"
        ),
    },
    "route-ad19f7b757106baf204564cc": {
        "locator": (
            "ISLP community solution notebooks: Ch 2 Exercise 1 "
            "'statistical learning and bias-variance' and Ch 5 Exercise 3 "
            "'k-fold cross-validation' in the botlnec, a-martyn, and "
            "applied-on-ISLP repositories"
        ),
    },
    "route-1e172cc16490b20444290684": {
        "locator": (
            "MIT 18.05 Spring 2022 'Final Exam' "
            "(mit18_05_s22_exam_final.pdf) and 'Final Exam Solutions' "
            "(mit18_05_s22_exam_final_sol.pdf)"
        ),
    },
    "route-de38ce9e78f4dd052d5013b4": {
        "locator": (
            "Stat 110 Lectures 4-5: 'independence, conditional probability, "
            "Bayes' rule, and conditional independence'; Strategic Practice 2 "
            "with solutions"
        ),
    },
    "route-0f4dd7d42e4f26f7e9730a91": {
        "locator": "Spring 2022 playlist, Lecture 11 'Decision Trees' and Lecture 12 'Boosting'",
    },
    "route-c0b5823ea68abe2175956a82": {
        "locator": (
            "Spring 2022 playlist, Lecture 5 'Gaussian Discriminant Analysis "
            "and Naive Bayes'"
        ),
    },
    "route-808f7b40861516f88124d45b": {
        "locator": "Spring 2022 playlist, Lecture 8 'Neural Networks I'",
    },
    "route-8fec57420f21e471d11c0a87": {
        "locator": (
            "MIT6_034F10_quiz3_2010.pdf, Fall 2010 Quiz 3, Problem 1 Part B "
            "'ID Trees', PDF pp. 4-5"
        ),
    },
    "route-eee4f9463982afe90b504b65": {
        "locator": (
            "MIT6_034F10_quiz3_2010.pdf, Fall 2010 Quiz 3, Problem 1 Part A "
            "'Nearest Neighbors', PDF pp. 2-3"
        ),
    },
    "route-7e22f14226c54dedd0fe872b": {
        "locator": (
            "MIT6_034F10_quiz3_2010.pdf, Fall 2010 Quiz 3, Problem 2 Parts A-C "
            "'Neural Networks'"
        ),
    },
    "route-0591d0ea916475d5ea97b91d": {
        "locator": (
            "MIT6_034F10_quiz3_2010.pdf, Fall 2010 Quiz 3, Problem 1 Parts A-B "
            "and Problem 2 Parts A-C, with the corresponding official solution"
        ),
    },
}


REMOVE_ROUTE_IDS = {"route-f80f5a51cfd87b7a1d954a88"}


def patched_source_map(repo) -> tuple[dict, set[str], list[str]]:
    source_map = copy.deepcopy(repo.module_source_maps[MODULE_ID])
    unseen_edits = set(EDITS)
    unseen_removals = set(REMOVE_ROUTE_IDS)
    touched_units: set[str] = set()
    removed_sources: list[str] = []

    kept_sources = []
    for source in source_map.get("sources", []):
        sid = source.get("source_id")
        original_routes = list(source.get("unit_routes") or [])
        kept_routes = []
        for route in original_routes:
            if not isinstance(route, dict):
                kept_routes.append(route)
                continue
            route_id = route.get("id")
            if route_id in REMOVE_ROUTE_IDS:
                unseen_removals.discard(route_id)
                touched_units.add(route["unit_id"])
                continue
            if route_id in EDITS:
                unseen_edits.discard(route_id)
                touched_units.add(route["unit_id"])
                route.update(EDITS[route_id])
            kept_routes.append(route)
        source["unit_routes"] = kept_routes
        if kept_routes or not original_routes:
            kept_sources.append(source)
        else:
            removed_sources.append(str(sid))
    source_map["sources"] = kept_sources

    if unseen_edits or unseen_removals:
        raise SystemExit(
            f"unknown route ids: edits={sorted(unseen_edits)}, "
            f"removals={sorted(unseen_removals)}"
        )
    return source_map, touched_units, removed_sources


def derived_stage_ids(unit: dict) -> list[str]:
    return [
        "stage-" + node["id"].removeprefix("knowledge-")
        for node in (unit.get("knowledge_map") or {}).get("nodes", [])
    ]


def assemble(units: dict[str, dict], source_map: dict, phrases: dict) -> dict[str, dict]:
    maps: dict[str, dict] = {}
    problems: list[str] = []
    for uid, unit in units.items():
        routes = [
            dict(route, material_uri=route["vault_path"])
            if route.get("vault_path") else dict(route)
            for source in source_map.get("sources", [])
            for route in (source.get("unit_routes") or [])
            if isinstance(route, dict) and route.get("unit_id") == uid
        ]
        if not routes:
            problems.append(f"{uid}: no material routes reach it")
            continue
        record = build(unit, MODULE_ID, routes, phrases, True)
        problems.extend(assembly_problems(unit, routes, record))
        try:
            require_current_template(record, "curriculum")
            validate_contract(
                REPO,
                "study-map.schema.json",
                record,
                label=f"assembled study map for {uid}",
            )
        except Exception as exc:  # noqa: BLE001
            problems.append(f"{uid}: {exc}")
            continue
        maps[uid] = record
    if problems:
        raise SystemExit("assembly preflight failed:\n- " + "\n- ".join(problems))
    return maps


AUDIT = """# M2 exact-locator closure audit — 2026-09-01

This is the closeout to `M2-route-rigor-coverage-audit-2026-08-29.md`.
It changes only the M2 source map, locator drift guards, and assembler-owned
study-map projections. No unit, knowledge node, or reviewed order changes.

## Local and temporary paginated verification

| Source | Evidence opened | Canonical locator convention |
|---|---|---|
| Grinstead & Snell | Official Dartmouth PDF; outline and five heading checks | PDF viewer pages: Ch 3 pp. 83-140, Ch 4 pp. 141-190, Ch 5 pp. 191-232, Ch 6 pp. 233-292, Ch 8 pp. 313-332, Ch 9 pp. 333-372 |
| Bishop PRML | Official Microsoft Research PDF; embedded outline | Ch 8 pp. 379-438; §8.1 p. 380, §8.2 p. 392, §8.2.2 p. 398 |

The PDFs above were temporary verification inputs. They were not added to the
material registry or treated as locally owned source bytes.

## Linked source identities

Every other repaired route now names a quoted episode, lecture, problem,
release appendix, notebook exercise, exam file, or exam page. The identities
were checked against the publisher, course, channel, or official course-resource
page on 2026-09-01. Web-published books (Nielsen, D2L, Prince, Goodfellow, and
the current Jurafsky appendix) are typed `website`; the old `book` type falsely
promised edition-stable PDF pagination.

## Removed mismatch

`route-f80f5a51cfd87b7a1d954a88` is removed from M2. The opened Swanson LNM 2384
is a monograph on inductive and probabilistic logic; its short measure-space
background does not teach the route's claimed definition of a random variable
as a measurable function. The source itself is not deleted from the global
catalogue. Only the unsupported M2 routing judgment is removed.

## Completeness and boundaries

- 41 previously vague M2 routes receive exact addresses.
- One unsupported route is removed.
- Selection locator guards move with the repaired routes.
- Assembler-owned study maps are rebuilt; independently authored exam maps keep
  their stage structure.
- Algo2, AML, material bytes, source registrations, learning progress, and
  unrelated workspaces are outside this package.

No claim of mastery, readiness, installation, or live UI state is made here.
"""


def main() -> int:
    repo = load_repo(REPO)
    source_map, touched_units, removed_sources = patched_source_map(repo)
    manifest = _manifest(REPO)
    phrases = concept_phrases(manifest["records"])

    routes_by_id = {
        route["id"]: route
        for source in source_map.get("sources", [])
        for route in (source.get("unit_routes") or [])
        if isinstance(route, dict) and route.get("id")
    }

    # Move locator drift guards in the same governed transaction.
    guard_units: dict[str, dict] = {}
    for uid in touched_units:
        unit = copy.deepcopy(repo.units[uid].data)
        moved = False
        for selection in unit.get("source_selections", []) or []:
            route_id = selection.get("route_id")
            if route_id in REMOVE_ROUTE_IDS:
                raise SystemExit(
                    f"removed route {route_id} is selected by {uid}; explicit replacement required"
                )
            route = routes_by_id.get(route_id)
            if route and selection.get("locator") != route.get("locator"):
                selection["locator"] = route["locator"]
                moved = True
        if moved:
            guard_units[uid] = unit

    assembler_units: dict[str, dict] = {}
    standalone_units: list[str] = []
    for uid in sorted(touched_units):
        unit = guard_units.get(uid, repo.units[uid].data)
        live_stage_ids = [
            str(stage.get("id"))
            for stage in repo.study_maps[unit["current_study_map"]].data.get("stages", [])
        ]
        if live_stage_ids == derived_stage_ids(unit):
            assembler_units[uid] = unit
        else:
            standalone_units.append(uid)

    maps = assemble(assembler_units, source_map, phrases)
    MAP_DIR.mkdir(parents=True, exist_ok=True)
    for uid, record in maps.items():
        (MAP_DIR / f"{uid}.study-map.yaml").write_text(
            yaml.safe_dump(record, sort_keys=False, allow_unicode=True, width=100),
            encoding="utf-8",
        )

    package = {
        "module_id": MODULE_ID,
        "plan_contract": {
            "version": 2,
            "plan_template_version": 1,
            "coverage_audit": (
                f"work/active/{WORKSPACE_ID}/outputs/"
                f"M2-exact-locator-coverage-audit-{DATE}.md"
            ),
            "intentional_reorders": [],
            "checks": {
                key: True
                for key in (
                    "local_inventory_complete",
                    "linked_inventory_complete",
                    "materials_opened_and_content_checked",
                    "current_and_prior_scope_reconciled",
                    "duplicates_and_numbering_checked",
                    "exclusions_and_unresolved_gaps_recorded",
                )
            },
        },
        "module_patch": {},
        "source_patches": [],
        "source_map": source_map,
        "units": (
            [
                {"unit": assembler_units[uid], "study_map": maps[uid]}
                for uid in sorted(assembler_units)
            ]
            + [
                {"unit": guard_units[uid]}
                for uid in sorted(guard_units)
                if uid not in assembler_units
            ]
        ),
    }

    AUDIT_PATH.write_text(AUDIT, encoding="utf-8")
    PLAN_PATH.write_text(
        yaml.safe_dump(package, sort_keys=False, allow_unicode=True, width=100),
        encoding="utf-8",
    )
    print(f"exact locator edits: {len(EDITS)}")
    print(f"removed routes: {sorted(REMOVE_ROUTE_IDS)}")
    print(f"empty source entries removed: {removed_sources}")
    print(f"study maps regenerated: {sorted(assembler_units)}")
    print(f"independently authored maps retained: {standalone_units}")
    print(f"selection guards moved: {sorted(guard_units)}")
    print(f"plan -> {PLAN_PATH.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
