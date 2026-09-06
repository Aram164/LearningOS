"""Focused recovery-objective diagnostics for LearningOS vNext."""

from __future__ import annotations

import datetime as dt
import json
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



def test_projection_check_requires_matching_payload(mini_repo):
    from learning_os.genout import generate_all
    from learning_os.loader import load_repo
    repo = load_repo(mini_repo)
    from learning_os.genout.outputs import write_outputs
    outputs = generate_all(repo)
    write_outputs(repo, outputs)

    manifest_path = mini_repo / "generated" / "manifest.json"
    original = json.loads(manifest_path.read_text(encoding="utf-8"))

    report = health.build_health_report(mini_repo)
    proj_check = next(c for c in report["checks"] if c["id"] == "projection-state")
    assert proj_check["status"] == "ok"

    altered = json.loads(manifest_path.read_text(encoding="utf-8"))
    for rec in altered.get("records", []):
        if "title" in rec:
            rec["title"] = "Invented title never authored"
            break
    manifest_path.write_text(json.dumps(altered), encoding="utf-8")

    report2 = health.build_health_report(mini_repo)
    proj_check2 = next(c for c in report2["checks"] if c["id"] == "projection-state")
    assert proj_check2["status"] == "warning"
    # The report has to name the section that is wrong. "something differs" is
    # the same non-answer as "ok" — neither tells the operator what to distrust.
    mismatches = proj_check2["details"]["mismatches"]
    assert "records" in mismatches, mismatches
    assert mismatches["records"]["first_difference_at"] == 0
    # …without quoting the manifest itself into a health report.
    assert "Invented title never authored" not in json.dumps(mismatches)

    header_only = {"_generated": original["_generated"]}
    manifest_path.write_text(json.dumps(header_only), encoding="utf-8")

    report3 = health.build_health_report(mini_repo)
    proj_check3 = next(c for c in report3["checks"] if c["id"] == "projection-state")
    assert proj_check3["status"] == "error"
    assert "contract validation" in proj_check3["summary"].lower()

