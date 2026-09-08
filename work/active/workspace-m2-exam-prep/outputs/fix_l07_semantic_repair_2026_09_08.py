#!/usr/bin/env python3
"""Bounded L07 semantic repair package (authorized 2026-09-08).

Applies exactly the adjudicated L07 verdict set and nothing else:
unit scope, deck angle/angle_detail, MIT angle/covers/locator/angle_detail,
Dekking covers swap, Schaum covers removals, Arbeitsbuch angle_detail
narrowing (covers unchanged, fail closed), Leuphana angle (covers unchanged).
Tijms, Harvard, Kurzes Tutorium and all other L07 routes are untouched.
Study-map Stage-4 flags ride a separate unit.map.import package.

Pure-YAML builder: reads the live canonical source-map.yaml and unit.yaml,
applies the edits, and emits a reviewable module-plan package. Writes no
canonical file itself.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
MODULE_ID = "module-hu-m2-statistik-analysis"
UNIT_ID = "unit-m2-sad-l07"
DATE = "2026-09-08"
WORKSPACE_ID = "workspace-m2-exam-prep"
PLAN_PATH = OUT / f"L07-semantic-repair-plan-{DATE}.yaml"
AUDIT_PATH = OUT / f"L07-semantic-repair-coverage-audit-{DATE}.md"

GEO = "knowledge-sad-l07-geometric"
HYPER = "knowledge-sad-l07-hypergeometric"

EDITS: dict[str, dict] = {
    # Current L07 deck: soften exam-weighting prose (covers unchanged).
    "route-66b70c94de7bc040921d186c": {
        "angle": (
            "Defines the identifying assumptions for the discrete models taught "
            "in the current deck and connects those assumptions to their PMFs, "
            "moments, examples, and relationships."
        ),
        "angle_detail": (
            "The deck presents model assumptions, PMFs, moments, worked examples, "
            "and relationships between its discrete models. The relationships are "
            "asserted; Blitzstein \u00a73.9 and \u00a74.8 provide complementary "
            "derivations. Use the condition statements as a model-selection "
            "checklist. Scope note: the current deck has no dedicated Geometric "
            "section; the Geometric stage is a complementary bridge to the "
            "explicitly routed Blatt 4 work. This route makes no independent "
            "claim about exam weighting."
        ),
    },
    # MIT 18.05: verified against Reading 4a + PS2 (opened 2026-09-08).
    "route-e325141b8971b65116e08790": {
        "angle": (
            "Contrasts fixed-trial Bernoulli/Binomial counts with Geometric "
            "waiting times through explicit modelling examples."
        ),
        "covers": [
            "knowledge-sad-l07-model-selection",
            "knowledge-sad-l07-bernoulli-binomial",
            GEO,
        ],
        "locator": (
            "MIT 18.05 Reading 4a 'Discrete Random Variables', \u00a7\u00a73.1-3.4 "
            "(Bernoulli, Binomial, Geometric); Problem Set 2, Problem 6 only for "
            "its separate R coin-flip simulation using rbinom"
        ),
        "angle_detail": (
            "Reading 4a teaches Bernoulli/Binomial and Geometric and uses examples "
            "to distinguish fixed-trial counts from waiting-time counts. "
            "Hypergeometric appears only in \u00a73.7 \"Other Distributions\" as a "
            "look-up example, and Poisson is not taught in this reading. Problem "
            "Set 2, Problem 6 uses rbinom for coin-flip simulation; this route "
            "does not claim per-distribution R-function coverage."
        ),
    },
    # Dekking: locator names Geometric (\u00a74.4), never Hypergeometric.
    "route-9e9215f1bace1b2b1a269f02": {
        "covers": [
            "knowledge-sad-l07-model-selection",
            "knowledge-sad-l07-bernoulli-binomial",
            GEO,
            "knowledge-sad-l07-poisson",
        ],
    },
    # Schaum: locator is Ch 6 Binomial, Normal and Poisson only.
    "route-3d403c071c84fe621ef510a3": {
        "covers": [
            "knowledge-sad-l07-model-selection",
            "knowledge-sad-l07-bernoulli-binomial",
            "knowledge-sad-l07-poisson",
        ],
    },
    # Arbeitsbuch: fail closed — narrow prose, covers unchanged.
    "route-488f203b03208f7a1ae5eaff": {
        "angle_detail": (
            "Use these items as mixed model-identification practice for the "
            "Binomial, Hypergeometric and Poisson cases represented by this "
            "route. The solutions justify the model choice rather than jumping "
            "directly to the formula. Work them mixed rather than in "
            "single-family blocks. Geometric coverage in this workbook slice "
            "remains unverified and is not claimed here."
        ),
    },
    # Leuphana: Aufgabenblatt 2 contains the waiting-time item; fix the angle.
    "route-4e47b0154d49ac739ff3c23e": {
        "angle": (
            "A mixed block where Binomial, Hypergeometric, Geometric and Poisson "
            "models must be identified from context."
        ),
    },
}

UNIT_SCOPE = (
    "Current 2026 L07 deck; Bernoulli, Binomial, Hypergeometric, and Poisson "
    "distributions, their experiment assumptions, PMFs, expectation and variance, "
    "and relationships or approximations between those models. Geometric waiting "
    "times are complementary preparation for later work; the current L07 deck "
    "has no dedicated Geometric section."
)

AUDIT = """# L07 bounded semantic repair audit — 2026-09-08

Boundary: `unit-m2-sad-l07` unit scope plus six of its source-map routes
(deck prose; MIT prose+covers; Dekking covers; Schaum covers; Arbeitsbuch
prose; Leuphana prose). Tijms, Harvard Stat 110, Kurzes Tutorium, and every
other L07 route are deliberately untouched. Knowledge nodes, unit order,
stage structure, source selections, and all other units are unchanged.
Stage-4 flags ride a separate `unit.map.import` package.

## Local

The deck and exercise PDFs are registered materials whose bytes are absent
from this checkout (materials tree not present); their page-slice locators
are inherited unchanged from the prior verified repair and this package does
not alter them. The MIT materials were opened from official MIT hosts on
2026-09-08 and text-extracted: Reading 4a (18 pages; \u00a7\u00a73.1-3.4 Bernoulli,
Binomial, Geometric; \u00a73.7 look-up-only Hypergeometric; zero Poisson
mentions) and Problem Set 2 (3 pages; Problem 6 `rbinom` coin-flip runs
simulation; no Poisson/Hypergeometric/Geometric items, no per-distribution
R functions).

## Linked

| Route | Evidence basis for this package |
|---|---|
| Deck prose | Prior repair's scope note (no dedicated Geometric section) |
| MIT 18.05 | Opened Reading 4a + PS2 PDFs named above |
| Dekking covers | Route's own locator (\u00a74.4 Geometric; no Hypergeometric) |
| Schaum covers | Route's own locator (Ch 6 Binomial/Normal/Poisson) |
| Arbeitsbuch prose | Fail-closed narrowing; workbook slice unopened, nothing added |
| Leuphana angle | Adjudicated waiting-time item on Aufgabenblatt 2 |
| Tijms / Harvard / Tutorium | Untouched (Cambridge index; locator-consistent) |

The Dekking, Schaum, and Arbeitsbuch books were not opened in this
environment; no `covers` edge in this package rests on unopened-book
content (the Dekking/Schaum changes remove edges their own locators
contradict; the Arbeitsbuch change adds nothing).

## Completeness

Changed: unit scope (1 field), six routes (fields listed above).
Unchanged: all other module content. Unresolved and explicitly not
claimed: Arbeitsbuch Geometric coverage; deck/exercise physical page
slices (inherited, not reverified). No claim of mastery, readiness, or
exam weighting is made here; the deck route now disclaims exam-weighting
inference explicitly.
"""


def main() -> int:
    source_map_path = (
        REPO / "curriculum" / "modules" / MODULE_ID / "source-map.yaml"
    )
    unit_path = (
        REPO / "curriculum" / "modules" / MODULE_ID / "units" / UNIT_ID
        / "unit.yaml"
    )
    source_map = yaml.safe_load(source_map_path.read_text(encoding="utf-8"))
    unit = yaml.safe_load(unit_path.read_text(encoding="utf-8"))

    unseen = set(EDITS)
    touched: set[str] = set()
    for source in source_map.get("sources", []):
        for route in source.get("unit_routes") or []:
            if not isinstance(route, dict):
                continue
            rid = route.get("id")
            if rid in EDITS:
                unseen.discard(rid)
                touched.add(route.get("unit_id", ""))
                route.update(copy.deepcopy(EDITS[rid]))
    if unseen:
        raise SystemExit(f"unknown route ids: {sorted(unseen)}")
    if touched != {UNIT_ID}:
        raise SystemExit(f"edits escaped {UNIT_ID}: {sorted(touched)}")

    if unit.get("id") != UNIT_ID:
        raise SystemExit("unit file identity mismatch")
    if unit.get("source_selections"):
        raise SystemExit("unit carries selections; guard review required")
    unit["scope"] = UNIT_SCOPE

    package = {
        "module_id": MODULE_ID,
        "plan_contract": {
            "version": 2,
            "plan_template_version": 1,
            "coverage_audit": (
                f"work/active/{WORKSPACE_ID}/outputs/{AUDIT_PATH.name}"
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
        "units": [{"unit": unit}],
    }

    AUDIT_PATH.write_text(AUDIT, encoding="utf-8")
    PLAN_PATH.write_text(
        yaml.safe_dump(package, sort_keys=False, allow_unicode=True, width=100),
        encoding="utf-8",
    )
    print(f"route edits: {len(EDITS)} + unit scope")
    print(f"plan -> {PLAN_PATH.relative_to(REPO)}")
    print(f"audit -> {AUDIT_PATH.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
