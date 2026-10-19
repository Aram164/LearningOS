"""Stage and learning-path state machines as pure domain rules (H8, P6-06).

Dicts in, dicts out: the handlers refuse invalid actions first, so these
tests only exercise valid actions against a counting fake clock.
"""

from __future__ import annotations

import datetime as dt

from learning_os.domain.curriculum.stages import (
    apply_path_action,
    apply_stage_action,
    progress_entry,
)

FIXED = dt.date(2026, 10, 1)


class FakeClock:
    """A ``today`` callable that counts its own reads."""

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> dt.date:
        self.calls += 1
        return FIXED


def _stage(stage_id: str, status: str, **extra) -> dict:
    return {"id": stage_id, "status": status, **extra}


def _map(*stages: dict) -> tuple[dict, dict]:
    data = {"stages": list(stages), "status": "pending"}
    unit_data: dict = {"status": "pending"}
    return data, unit_data


def test_activate_resets_other_active_and_paused_stages():
    first = _stage("s1", "active")
    second = _stage("s2", "paused")
    target = _stage("s3", "pending", completed="2026-01-01")
    data, unit_data = _map(first, second, target)
    clock = FakeClock()

    apply_stage_action(data, unit_data, target, "active", clock)

    assert first["status"] == "pending"
    assert second["status"] == "pending"
    assert target["status"] == "active"
    assert "completed" not in target
    assert data["current_stage"] == "s3"
    assert data["status"] == "active"
    assert unit_data["status"] == "active"
    assert clock.calls == 0


def test_revisit_behaves_like_active():
    other = _stage("s1", "paused")
    target = _stage("s2", "complete", completed="2026-01-01")
    data, unit_data = _map(other, target)
    clock = FakeClock()

    apply_stage_action(data, unit_data, target, "revisit", clock)

    assert other["status"] == "pending"
    assert target["status"] == "active"
    assert "completed" not in target
    assert data["current_stage"] == "s2"
    assert data["status"] == "active"
    assert unit_data["status"] == "active"
    assert clock.calls == 0


def test_pause_pauses_stage_map_and_unit():
    target = _stage("s1", "active")
    data, unit_data = _map(target, _stage("s2", "pending"))
    clock = FakeClock()

    apply_stage_action(data, unit_data, target, "paused", clock)

    assert target["status"] == "paused"
    assert data["current_stage"] == "s1"
    assert data["status"] == "paused"
    assert unit_data["status"] == "paused"
    assert clock.calls == 0


def test_complete_stamps_and_activates_next_pending():
    target = _stage("s1", "active")
    following = _stage("s2", "pending")
    data, unit_data = _map(target, following)
    clock = FakeClock()

    apply_stage_action(data, unit_data, target, "complete", clock)

    assert target["status"] == "complete"
    assert target["completed"] == "2026-10-01"
    assert clock.calls == 1
    assert following["status"] == "active"
    assert data["current_stage"] == "s2"
    assert data["status"] == "active"
    assert unit_data["status"] == "active"


def test_complete_on_last_stage_shelves_map_and_unit():
    target = _stage("s1", "active")
    data, unit_data = _map(_stage("s0", "complete"), target)
    clock = FakeClock()

    apply_stage_action(data, unit_data, target, "complete", clock)

    assert target["status"] == "complete"
    assert target["completed"] == "2026-10-01"
    assert clock.calls == 1
    assert data["status"] == "ready-to-shelve"
    assert data["shelving"]["state"] == "draft"
    assert unit_data["status"] == "ready-to-shelve"


def test_skipped_advances_without_stamping_or_clock():
    target = _stage("s1", "active")
    following = _stage("s2", "pending")
    data, unit_data = _map(target, following)
    clock = FakeClock()

    apply_stage_action(data, unit_data, target, "skipped", clock)

    assert target["status"] == "skipped"
    assert "completed" not in target
    assert clock.calls == 0
    assert following["status"] == "active"
    assert data["current_stage"] == "s2"
    assert data["status"] == "active"
    assert unit_data["status"] == "active"


def test_path_active_resets_only_active_stages():
    active = _stage("p1", "active")
    paused = _stage("p2", "paused")
    target = _stage("p3", "pending", completed="2026-01-01")
    data = {"stages": [active, paused, target], "status": "pending"}
    clock = FakeClock()

    apply_path_action(data, target, "active", clock)

    assert active["status"] == "pending"
    assert paused["status"] == "paused"
    assert target["status"] == "active"
    assert "completed" not in target
    assert data["current_stage"] == "p3"
    assert data["status"] == "active"
    assert clock.calls == 0


def test_path_complete_advances_to_next_pending():
    target = _stage("p1", "active")
    following = _stage("p2", "pending")
    data = {"stages": [target, following], "status": "active"}
    clock = FakeClock()

    apply_path_action(data, target, "complete", clock)

    assert target["status"] == "complete"
    assert target["completed"] == "2026-10-01"
    assert clock.calls == 1
    assert following["status"] == "active"
    assert data["current_stage"] == "p2"
    assert data["status"] == "active"


def test_path_complete_on_last_stage_shelves():
    target = _stage("p1", "active")
    data = {"stages": [target], "status": "active"}
    clock = FakeClock()

    apply_path_action(data, target, "complete", clock)

    assert target["status"] == "complete"
    assert target["completed"] == "2026-10-01"
    assert clock.calls == 1
    assert data["status"] == "ready-to-shelve"
    assert data["shelving"]["state"] == "draft"


def test_path_skipped_advances_without_clock():
    target = _stage("p1", "active")
    following = _stage("p2", "pending")
    data = {"stages": [target, following], "status": "active"}
    clock = FakeClock()

    apply_path_action(data, target, "skipped", clock)

    assert target["status"] == "skipped"
    assert "completed" not in target
    assert clock.calls == 0
    assert following["status"] == "active"
    assert data["current_stage"] == "p2"
    assert data["status"] == "active"


def test_progress_entry_strips_and_includes_next_when_given():
    clock = FakeClock()

    entry = progress_entry("  did the reading  ", "  write notes  ", clock)

    assert entry == {
        "updated": "2026-10-01",
        "summary": "did the reading",
        "next": "write notes",
    }
    assert clock.calls == 1


def test_progress_entry_omits_next_when_not_given():
    clock = FakeClock()

    entry = progress_entry("  did the reading  ", None, clock)

    assert entry == {"updated": "2026-10-01", "summary": "did the reading"}
    assert "next" not in entry
    assert clock.calls == 1
