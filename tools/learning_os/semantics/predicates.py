"""Phase-0 semantic predicates: pure derived judgments over existing records.

The Intelligence Plane's semantic layer is interpretation, not stored truth.
Every predicate here is a pure function over already-loaded records or
projection rows. Predicates never write canonical data, never touch
``generated/``, and never call gateway capabilities. The producer
(``genout.projection``) keeps answering these derivations per row; this module
owns their *meaning* so agents read one declared layer instead of re-deriving
it from scattered YAML and rules.

Phase 0 carries exactly one predicate (``NeedsStudyMap``, the derivation the
producer already answers as ``needs_study_map``) to prove the evaluator
pattern. Phase 1 grows the registry toward ~25 predicates; any addition needs
a Verified Operator Question or a goal-detector motivating it.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

#: Version of the predicate contract. Bumped when a predicate's inputs, truth
#: table, or registry membership changes. Lineage sidecars (Phase 2) cite this
#: so "what goes stale if the contract changes" stays answerable.
CONTRACT_VERSION = 1

#: A module whose units are still being studied. A dropped or archived module
#: keeps its records as history and is never asked for new plans.
STUDIED_MODULE_STATUSES = frozenset({"active", "enrolled"})

#: A unit that is finished, paused/inactive, or explicitly set aside is not
#: owed a plan either. `ready-to-shelve` is operationally inactive: asking it
#: to acquire a new study map while it is leaving active study would reverse
#: the user's lifecycle decision.
UNIT_STATUSES_WITHOUT_OBLIGATION = frozenset({
    "complete", "archived", "paused", "ready-to-shelve",
})


def needs_study_map(
    *,
    unit_status: str | None,
    module_status: str | None,
    has_study_map: bool,
) -> bool:
    """Whether a unit still owes an ordered study map (OPERATOR.md rule 6).

    Derived, not declared. An authored label is a claim someone has to remember
    to set; one derivation ends the disagreement between counts, badges, and
    the Review queue. Authoritative inputs: the unit's `status`, its module's
    `status`, and whether a study map already covers the unit.
    """
    if has_study_map:
        return False
    if module_status not in STUDIED_MODULE_STATUSES:
        return False
    return unit_status not in UNIT_STATUSES_WITHOUT_OBLIGATION


@dataclass(frozen=True)
class Predicate:
    """One named semantic judgment plus the metadata a consumer needs."""

    name: str
    version: int
    function: Callable[..., bool]
    authoritative_inputs: tuple[str, ...]
    description: str


PREDICATES: Mapping[str, Predicate] = {
    "NeedsStudyMap": Predicate(
        name="NeedsStudyMap",
        version=CONTRACT_VERSION,
        function=needs_study_map,
        authoritative_inputs=("unit_status", "module_status", "has_study_map"),
        description=(
            "OPERATOR.md rule 6: every unit of an active or enrolled module "
            "owes a study map unless complete, archived, paused, or leaving "
            "active study."
        ),
    ),
}


def evaluate(name: str, **inputs: object) -> bool:
    """Evaluate one registered predicate by name. Unknown names fail closed."""
    try:
        predicate = PREDICATES[name]
    except KeyError:
        raise KeyError(f"unknown semantic predicate: {name!r}") from None
    return bool(predicate.function(**inputs))
