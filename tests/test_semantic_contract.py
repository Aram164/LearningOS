"""The semantic contract holds for its first predicate (Phase 0 spike).

`NeedsStudyMap` is the derivation the producer already answers per unit row
as `needs_study_map`. These pin the evaluator's truth table, the registry
shape Phase 1 will grow, and the fact that the producer's wrapper and the
evaluator cannot disagree — so the spike proves the pattern rather than
adding a second opinion.
"""

from __future__ import annotations

import pytest

from learning_os.genout.projection.records_curriculum import _needs_study_map
from learning_os.semantics import (
    CONTRACT_VERSION,
    PREDICATES,
    evaluate,
    needs_study_map,
)


def test_the_contract_version_is_pinned():
    """Lineage (Phase 2) cites this; a bump must be a deliberate diff."""
    assert CONTRACT_VERSION == 1


def test_the_registry_names_the_spike_predicate():
    predicate = PREDICATES["NeedsStudyMap"]
    assert predicate.version == CONTRACT_VERSION
    assert predicate.authoritative_inputs == (
        "unit_status", "module_status", "has_study_map",
    )
    assert predicate.description


def test_unknown_predicates_fail_closed():
    with pytest.raises(KeyError):
        evaluate("DoesNotExist", unit_status="active")


@pytest.mark.parametrize(
    ("unit_status", "module_status", "has_map", "owed", "why"),
    [
        ("not-started", "enrolled", False, True,
         "an enrolled lecture with no map owes one"),
        ("active", "active", False, True, "so does an active one"),
        ("not-started", "enrolled", True, False,
         "a map discharges the obligation"),
        ("complete", "enrolled", False, False, "a finished unit owes nothing"),
        ("archived", "enrolled", False, False, "nor one set aside"),
        ("paused", "enrolled", False, False, "a paused unit is inactive"),
        ("ready-to-shelve", "active", False, False,
         "a unit leaving active study owes no new map"),
        ("not-started", "dropped", False, False,
         "a dropped module is history"),
        ("not-started", "archived", False, False, "nor is an archived one"),
        ("needs-map", "dropped", False, False,
         "an old label cannot oblige an inactive module"),
        ("not-started", None, False, False,
         "an unresolvable module accuses nobody"),
        (None, "enrolled", False, True,
         "a missing unit status still owes when the module is studied"),
    ],
)
def test_the_evaluator_answers_the_obligation(
    unit_status, module_status, has_map, owed, why,
):
    assert evaluate(
        "NeedsStudyMap",
        unit_status=unit_status,
        module_status=module_status,
        has_study_map=has_map,
    ) is owed, why


def test_the_producer_and_the_evaluator_cannot_disagree():
    """Sweep the input space: the wrapper must equal the predicate everywhere."""
    unit_statuses = [
        "not-started", "active", "complete", "archived", "paused",
        "ready-to-shelve", "needs-map", None,
    ]
    module_statuses = [
        "active", "enrolled", "dropped", "archived", "paused", None,
    ]
    for unit_status in unit_statuses:
        for module_status in module_statuses:
            for has_map in (False, True):
                assert _needs_study_map(
                    {"status": unit_status}, module_status, has_map,
                ) is needs_study_map(
                    unit_status=unit_status,
                    module_status=module_status,
                    has_study_map=has_map,
                )
