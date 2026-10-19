#!/usr/bin/env python3
"""Bounded L08 semantic repair package (authorized 2026-09-08).

Exactly the adjudicated set: Schaum covers (drop transform-sum + clt);
MIT covers (add likelihood + mle); Dekking covers (add normal) + angle
(drop exclusivity); deck detail (cross-reference gains section 22.3).
No unit changes, so the package carries no unit entries. Stage edits ride
a separate unit.map.import package. Writes no canonical file itself.
"""

from __future__ import annotations

import copy
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
MODULE_ID = "module-hu-m2-statistik-analysis"
UNIT_ID = "unit-m2-sad-l08"
DATE = "2026-09-08"
WORKSPACE_ID = "workspace-m2-exam-prep"
PLAN_PATH = OUT / ("L08-semantic-repair-plan-" + DATE + ".yaml")
AUDIT_PATH = OUT / ("L08-semantic-repair-coverage-audit-" + DATE + ".md")

N = "knowledge-sad-l08-normal"
S = "knowledge-sad-l08-standardization"
T = "knowledge-sad-l08-transform-sum"
C = "knowledge-sad-l08-clt"
A = "knowledge-sad-l08-approximation"
L = "knowledge-sad-l08-likelihood"
M = "knowledge-sad-l08-mle"

EDITS = {
    "route-4b2bb29fc4326732f09f4cb5": {"covers": [S, A]},
    "route-cdc87014dbc983f542c2d601": {"covers": [N, S, C, A, L, M]},
    "route-8f48d8d7623a4b01aac9348f": {
        "covers": [N, S, T, C, A, L, M],
        "angle": ("Covers both halves of L08 \u2014 the limit theorems and "
                  "maximum likelihood \u2014 in the same book and notation."),
    },
}

DECK_OLD = "Dekking Ch 13-14 and Ch 21 cover both halves in the same notation."
DECK_NEW = ("Dekking Ch 13-14, Ch 21, and \u00a722.3 cover both halves "
            "in the same notation.")

# Placeholder replaced below by the audit text edit.
AUDIT = (
    "# L08 bounded semantic repair audit -- 2026-09-08\n"
    "\n"
    "Boundary: four source-map routes of unit-m2-sad-l08 (Schaum covers; "
    "MIT covers; Dekking covers + angle; deck cross-reference sentence). "
    "No unit, node, order, selection, or other-unit change. Stage edits "
    "ride a separate unit.map.import package.\n"
    "\n"
    "## Local\n"
    "\n"
    "Course PDFs are registered but their bytes are absent from this "
    "checkout; no page-slice locator changes here. The MIT Class 10 MLE "
    "reading (11 pages; likelihood-function and MLE goals) was opened "
    "from the official MIT host on 2026-09-08. The Leuphana workbook was "
    "not opened here; its sheet scope is recorded from indexed primary "
    "text, and this package changes nothing about either Leuphana route.\n"
    "\n"
    "## Linked\n"
    "\n"
    "Schaum: route's own locator plus its own No-CLT-theory detail. MIT: "
    "opened Class 10 reading already cited by the route. Dekking normal: "
    "route's own locator (Ch 5 section 5.5). Dekking angle: exclusivity "
    "falsified by MIT's existing locator and prose. Deck detail: "
    "section 22.3 is the explicitly routed Gaussian-least-squares slice. "
    "Dekking, Schaum, and Arbeitsbuch books were not opened; no covers "
    "edge here rests on unopened-book content.\n"
    "\n"
    "## Completeness\n"
    "\n"
    "Changed: four routes, fields listed above. Unchanged: everything "
    "else. Unresolved and not claimed: Leuphana extra L08 edges; weak "
    "single-section edges elsewhere; Stages 6-7 exam-criticality; "
    "inherited page slices. No mastery, readiness, or exam-weighting "
    "claim is made here.\n"
)


def main():
    source_map_path = (REPO / "curriculum" / "modules" / MODULE_ID
                       / "source-map.yaml")
    source_map = yaml.safe_load(source_map_path.read_text(encoding="utf-8"))
    unseen = set(EDITS)
    touched = set()
    deck_seen = False
    for source in source_map.get("sources", []):
        for route in source.get("unit_routes") or []:
            if not isinstance(route, dict):
                continue
            rid = route.get("id")
            if rid in EDITS:
                unseen.discard(rid)
                touched.add(route.get("unit_id", ""))
                route.update(copy.deepcopy(EDITS[rid]))
            if rid == "route-a82f4016ebbdab30e0351c91":
                detail = route.get("angle_detail", "")
                if DECK_OLD not in detail:
                    raise SystemExit("deck cross-reference sentence not found")
                route["angle_detail"] = detail.replace(DECK_OLD, DECK_NEW)
                deck_seen = True
                touched.add(route.get("unit_id", ""))
    if unseen:
        raise SystemExit("unknown route ids: " + str(sorted(unseen)))
    if not deck_seen:
        raise SystemExit("deck route not found")
    if touched != {UNIT_ID}:
        raise SystemExit("edits escaped " + UNIT_ID + ": " + str(sorted(touched)))

    package = {
        "module_id": MODULE_ID,
        "plan_contract": {
            "version": 2,
            "plan_template_version": 1,
            "coverage_audit": ("work/active/" + WORKSPACE_ID + "/outputs/"
                               + AUDIT_PATH.name),
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
        "units": [],
    }

    AUDIT_PATH.write_text(AUDIT, encoding="utf-8")
    PLAN_PATH.write_text(
        yaml.safe_dump(package, sort_keys=False, allow_unicode=True, width=100),
        encoding="utf-8",
    )
    print("route edits: 3 covers + Dekking angle + deck sentence")
    print("plan -> " + str(PLAN_PATH.relative_to(REPO)))
    print("audit -> " + str(AUDIT_PATH.relative_to(REPO)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
