"""`module.status` answers two questions; the projection answers them separately.

The schema lets a module be `planned, enrolled, active, paused, awaiting-grade,
completed, dropped, archived`. Five of those are administrative — what the
university thinks — and two are operational — whether Aram is working on it.
The axes are independent: Algo 2 is administratively enrolled and operationally
dropped, PPDS is submitted with a grade pending and operationally finished.

A consumer reading one field for both questions has to guess, and Home guessed:
it treated everything except `complete`/`archived` as current work, so dropped
and finished modules appeared under "Continue elsewhere". These tests pin the
derivation so the interface never has to interpret again (engineering audit
2026-08-08, finding 4).
"""

from __future__ import annotations

import json

from learning_os.genout import generate_all
from learning_os.genout.projection import module_lifecycle
from learning_os.loader import load_repo


def _academic(status: str) -> dict:
    return {"id": "module-x", "kind": "academic", "status": status}


def test_enrolled_with_paused_units_is_not_actionable():
    """Algo 2 exactly: enrolled on paper, nothing to do in practice."""
    result = module_lifecycle(_academic("enrolled"), ["paused"])
    assert result["administrative_status"] == "enrolled"
    assert result["operational_state"] == "paused"
    assert result["is_actionable"] is False


def test_enrolled_with_ready_units_is_actionable():
    result = module_lifecycle(_academic("enrolled"), ["ready", "paused"])
    assert result["operational_state"] == "active"
    assert result["is_actionable"] is True


def test_operational_state_is_read_from_the_units_not_the_module():
    """A module cannot be active while every unit under it is paused."""
    assert module_lifecycle(_academic("active"), ["paused"])["operational_state"] == "paused"


def test_an_explicit_module_pause_overrides_live_units():
    assert module_lifecycle(_academic("paused"), ["ready"])["is_actionable"] is False


def test_awaiting_grade_is_never_actionable():
    """PPDS: submitted, grade pending — nothing is expected of you."""
    result = module_lifecycle(_academic("awaiting-grade"), ["ready"])
    assert result["administrative_status"] == "awaiting-grade"
    assert result["is_actionable"] is False


def test_settled_administrative_states_are_never_actionable():
    for status in ("completed", "dropped", "archived"):
        assert module_lifecycle(_academic(status), ["ready"])["is_actionable"] is False


def test_a_module_with_no_units_has_nothing_to_continue():
    result = module_lifecycle(_academic("enrolled"), [])
    assert result["operational_state"] == "none"
    assert result["is_actionable"] is False


def test_all_units_complete_reads_as_complete_not_paused():
    result = module_lifecycle(_academic("enrolled"), ["complete", "complete"])
    assert result["operational_state"] == "complete"
    assert result["is_actionable"] is False


def test_unstarted_work_is_still_work():
    for status in ("needs-map", "not-started", "ready", "active"):
        assert module_lifecycle(_academic("enrolled"), [status])["operational_state"] == "active"


def test_a_skill_module_has_no_registrar():
    """Only academic modules have an administrative state to report."""
    result = module_lifecycle({"id": "module-skill", "kind": "skill", "status": "active"},
                               ["ready"])
    assert result["administrative_status"] is None
    assert result["is_actionable"] is True


def test_the_projection_carries_all_three_fields(mini_repo):
    manifest = json.loads(generate_all(load_repo(mini_repo), "T1")["manifest.json"])
    for module in manifest["modules"]:
        assert set(module) >= {"administrative_status", "operational_state", "is_actionable"}
        assert isinstance(module["is_actionable"], bool)


def test_the_raw_authored_status_is_still_published(mini_repo):
    """Deriving must not remove the field anything else may legitimately read."""
    manifest = json.loads(generate_all(load_repo(mini_repo), "T1")["manifest.json"])
    assert all("status" in module for module in manifest["modules"])
