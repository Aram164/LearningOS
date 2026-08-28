"""Focused recovery-objective diagnostics for LearningOS vNext."""

from __future__ import annotations

import datetime as dt
from types import SimpleNamespace

from learning_os import health


def _runner(*responses):
    queue = list(responses)

    def run(_command, **_kwargs):
        return queue.pop(0)

    return run


def _response(stdout: str, *, returncode: int = 0):
    return SimpleNamespace(stdout=stdout, stderr="", returncode=returncode)


def test_backup_health_proves_encryption_and_one_day_rpo(monkeypatch):
    monkeypatch.setattr(
        health.subprocess,
        "run",
        _runner(
            _response("Name : External\nEncryption : 1\n"),
            _response("/Volumes/Backup/2026-08-25-010000.backup\n"),
        ),
    )

    row = health._time_machine_check(
        now=dt.datetime(2026, 8, 25, 12, 0, tzinfo=dt.UTC),
        local_timezone=dt.UTC,
    )

    assert row["status"] == "ok"
    assert row["details"]["encryption_proven"] is True
    assert row["details"]["age_hours"] == 11.0
    assert row["details"]["recovery_point_objective_hours"] == 24


def test_backup_health_warns_when_latest_backup_exceeds_rpo(monkeypatch):
    monkeypatch.setattr(
        health.subprocess,
        "run",
        _runner(
            _response("Name : External\nEncrypted : yes\n"),
            _response("/Volumes/Backup/2026-08-23-100000.backup\n"),
        ),
    )

    row = health._time_machine_check(
        now=dt.datetime(2026, 8, 25, 12, 0, tzinfo=dt.UTC),
        local_timezone=dt.UTC,
    )

    assert row["status"] == "warning"
    assert "older than one day" in row["summary"]
    assert row["details"]["age_hours"] == 50.0


def test_backup_health_does_not_infer_encryption_from_a_field_name(monkeypatch):
    monkeypatch.setattr(
        health.subprocess,
        "run",
        _runner(
            _response("Name : External\nEncryption : 0\n"),
            _response("/Volumes/Backup/2026-08-25-110000.backup\n"),
        ),
    )

    row = health._time_machine_check(
        now=dt.datetime(2026, 8, 25, 12, 0, tzinfo=dt.UTC),
        local_timezone=dt.UTC,
    )

    assert row["status"] == "warning"
    assert row["details"]["encryption_proven"] is False
