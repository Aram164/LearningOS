"""Finish AML route rationale and the remaining exact-locator repairs.

The short ``angle`` on every route is already the reviewed, route-specific
claim.  This phase expands that claim against the nearest overlapping route in
the same unit, rather than copying a generic hover paragraph.  The resulting
detail always records four independently reviewable facts: the contribution,
the expected depth, the discriminator, and the boundary relative to the
current HU deck.
"""

from __future__ import annotations

import builder


REBUILD_UNITS = set(builder.UNIT_ORDER)


LOCATOR_EDITS = {
    "route-da3215e650cc6b3007807144": {
        "locator": (
            "Official PDF, Ch 9 'Linear Regression', PDF pp. 295-305: "
            "§9.1 'Problem Formulation' p. 297 and §9.2.1 "
            "'Maximum Likelihood Estimation' pp. 298-305"
        ),
    },
    "route-5a74fc054147728a14f2d60a": {
        "locator": (
            "Official PDF, Ch 9 'Linear Regression': §9.2.2 "
            "'Maximum A Posteriori Estimation' PDF pp. 306-308 and §9.4 "
            "'Maximum Likelihood as Orthogonal Projection' PDF pp. 319-320"
        ),
    },
    "route-6a75b1b8d8b317dabe077fb2": {
        "locator": (
            "Official PDF, Ch 7 'Continuous Optimization': §7.1 "
            "'Optimization Using Gradient Descent' PDF pp. 233-238 and §7.3 "
            "'Convex Optimization' PDF pp. 242-251"
        ),
    },
    "route-cb9b43283aec0fabd1a672fe": {
        "locator": (
            "Official PDF, §5.6 'Backpropagation and Automatic "
            "Differentiation', PDF pp. 165-169"
        ),
    },
    # The title is exact; the old suffix "feature/model-selection chapters"
    # was an instruction to hunt inside the video rather than an address.
    "route-78c80f90e01473339746d6f0": {
        "locator": (
            "Spring 2022 playlist, Lecture 10 "
            "'Bias/Variance, Regularization, and Model Selection'"
        ),
    },
    "route-69c5b6e2f97ec6539c186fca": {
        "locator": (
            "MIT6_034F10_quiz3_2010.pdf, Fall 2010 Quiz 3, "
            "Problem 2, Parts B-C"
        ),
    },
    # These are routed to the publishers' chapter HTML, not to paginated local
    # editions.  Keeping them as ``book`` falsely promised a PDF page address.
    "route-6c95659e3d8d3bd3757200b8": {"format": "website"},
    "route-718c7af06b865756c1ac24cc": {"format": "website"},
    "route-71e1e305a548c2b59df832e5": {"format": "website"},
    "route-9bcc9d3896b681bb196226d4": {"format": "website"},
    "route-f78d93013bf6dc20254072a3": {"format": "website"},
    "route-339aea2b5f4d02caaeba8f88": {"format": "website"},
    "route-be930494e036304299d22b23": {"format": "website"},
    "route-b21ef88cc62edb59bcde2559": {"format": "website"},
    "route-897cd2cf70b2c4e0a6a33bfa": {"format": "website"},
}


DEPTH_EXPECTATION = {
    "orientation": (
        "It assumes no derivation beyond the current unit's vocabulary and is "
        "for framing the problem before calculation."
    ),
    "intuition": (
        "It assumes the unit vocabulary but not a completed proof and is meant "
        "to make the mechanism explainable before formal derivation."
    ),
    "course-aligned": (
        "It assumes the prerequisites declared by the unit and stays at the "
        "notation and derivation depth used by the HU course."
    ),
    "derivation": (
        "It assumes comfort with the unit's notation and asks the reader to "
        "follow or reproduce the mathematical steps, not merely recognize them."
    ),
    "practice": (
        "It assumes the relevant rule or algorithm has already been introduced "
        "and is for an attempted solution, trace, or calculation with feedback."
    ),
    "implementation": (
        "It assumes the mathematical object is already understood and shifts "
        "attention to executable behavior, shapes, APIs, or numerical checks."
    ),
    "advanced-reference": (
        "It assumes the lecture treatment is already secure and deliberately "
        "goes beyond exam-first depth for a precise reference or second derivation."
    ),
}


COURSE_BOUNDARY = {
    "current": (
        "This is current course evidence and may calibrate examined notation, "
        "but the route's stated locator—not the rest of the source—defines its scope."
    ),
    "prior-year": (
        "This is prior-year evidence: use it only for a second explanation, and "
        "let the current deck win wherever examples, notation, or scope differ."
    ),
    "prerequisite": (
        "This repairs a prerequisite only; it must not expand the current AML "
        "deck or become a parallel unit of study."
    ),
    "complementary": (
        "It complements the current deck but cannot override the deck's notation, "
        "topic boundary, or examination emphasis."
    ),
    "optional": (
        "It is optional depth: open it for the named gap, then return to the "
        "current deck rather than importing the source's wider syllabus."
    ),
}


def _one_line(value: str) -> str:
    return " ".join(str(value).split()).strip()


def _nearest_neighbor(route: dict, routes: list[dict]) -> dict:
    covers = set(route.get("covers") or [])

    def score(candidate: dict) -> tuple[int, int, int]:
        other = set(candidate.get("covers") or [])
        return (
            len(covers & other),
            int(candidate.get("scope") == "current"),
            -len(other - covers),
        )

    candidates = [candidate for candidate in routes if candidate["id"] != route["id"]]
    if not candidates:
        raise RuntimeError(f"route {route['id']} has no unit neighbor")
    return max(candidates, key=score)


def _detail(route: dict, neighbor: dict) -> str:
    contribution = _one_line(route["angle"])
    neighbor_contribution = _one_line(neighbor["angle"])
    depth = DEPTH_EXPECTATION[route["depth"]]
    boundary = COURSE_BOUNDARY[route["scope"]]
    return (
        f"Contribution: {contribution} "
        f"Depth and prerequisites: {depth} "
        f"Discriminator: choose '{_one_line(route['title'])}' over "
        f"'{_one_line(neighbor['title'])}' when you need this contribution; "
        f"the neighboring route instead contributes: {neighbor_contribution} "
        f"Course boundary: {boundary}"
    )


_map = builder.load_map()
_routes_by_unit: dict[str, list[dict]] = {}
for _source in _map["sources"]:
    for _route in _source.get("unit_routes") or []:
        _routes_by_unit.setdefault(_route["unit_id"], []).append(_route)

EDITS = {route_id: dict(patch) for route_id, patch in LOCATOR_EDITS.items()}
for _unit_id, _routes in _routes_by_unit.items():
    for _route in _routes:
        if _route.get("angle_detail"):
            continue
        _generated = _detail(_route, _nearest_neighbor(_route, _routes))
        EDITS.setdefault(_route["id"], {})["angle_detail"] = _generated

_details = [patch["angle_detail"] for patch in EDITS.values() if "angle_detail" in patch]
if len(_details) != 218:
    raise RuntimeError(f"P4 expected 218 missing details, found {len(_details)}")
if len(_details) != len(set(_details)):
    raise RuntimeError("P4 produced duplicate route details")
for _value in _details:
    for _label in ("Contribution:", "Depth and prerequisites:", "Discriminator:", "Course boundary:"):
        if _label not in _value:
            raise RuntimeError(f"P4 detail lacks {_label}")
