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


def test_health_report_validates_once_when_stored_is_current(mini_repo, monkeypatch):
    """#92: one schema pass when stored bytes equal a fresh build."""
    from learning_os.contracts import manifest_contract
    from learning_os.genout import generate_all
    from learning_os.genout.outputs import write_outputs
    from learning_os.loader import load_repo

    repo = load_repo(mini_repo)
    write_outputs(repo, generate_all(repo))

    calls: list[str] = []
    original = manifest_contract.check

    def counting(manifest, root):
        calls.append("check")
        return original(manifest, root)

    monkeypatch.setattr(manifest_contract, "check", counting)
    monkeypatch.setattr(health, "check_manifest_contract", counting)

    report = health.build_health_report(mini_repo)
    assert len(calls) == 1
    proj = next(c for c in report["checks"] if c["id"] == "projection-state")
    assert proj["status"] == "ok"
    contract = next(c for c in report["checks"] if c["id"] == "manifest-contract")
    assert contract["status"] == "ok"


def test_health_report_still_validates_stale_and_corrupt(mini_repo, monkeypatch):
    """#92: differing stored bytes still get their own schema pass."""
    from learning_os.contracts import manifest_contract
    from learning_os.genout import generate_all
    from learning_os.genout.outputs import write_outputs
    from learning_os.loader import load_repo

    repo = load_repo(mini_repo)
    write_outputs(repo, generate_all(repo))
    manifest_path = mini_repo / "generated" / "manifest.json"

    calls: list[str] = []
    original = manifest_contract.check

    def counting(manifest, root):
        calls.append("check")
        return original(manifest, root)

    monkeypatch.setattr(manifest_contract, "check", counting)
    monkeypatch.setattr(health, "check_manifest_contract", counting)

    altered = json.loads(manifest_path.read_text(encoding="utf-8"))
    for rec in altered.get("records", []):
        if "title" in rec:
            rec["title"] = "Stale title for counting"
            break
    manifest_path.write_text(json.dumps(altered), encoding="utf-8")
    calls.clear()
    stale = health.build_health_report(mini_repo)
    assert len(calls) == 2
    proj = next(c for c in stale["checks"] if c["id"] == "projection-state")
    assert proj["status"] == "warning"

    manifest_path.write_text(json.dumps({"_generated": {}}), encoding="utf-8")
    calls.clear()
    corrupt = health.build_health_report(mini_repo)
    assert len(calls) == 2
    proj2 = next(c for c in corrupt["checks"] if c["id"] == "projection-state")
    assert proj2["status"] == "error"


def _plugin_pair(tmp_path, *, installed_main: str = "bundle-v2",
                 installed_info: dict | None = None):
    """A fake UI checkout beside a fake vault, sharing one parent."""
    ui = tmp_path / "obsidian-ui"
    built = ui / "plugin"
    built.mkdir(parents=True)
    (ui / "plugin-assets.json").write_text(json.dumps({
        "schema_version": 1,
        "type": "learningos-ui-plugin-assets",
        "shipped": ["main.js", "styles.css", "manifest.json", "build-info.json"],
        "vault_owned": ["data.json"],
    }), encoding="utf-8")
    (built / "main.js").write_text("bundle-v2", encoding="utf-8")
    (built / "styles.css").write_text("css", encoding="utf-8")
    (built / "manifest.json").write_text("{}", encoding="utf-8")
    (built / "build-info.json").write_text(json.dumps({
        "source_fingerprint": "fp-new", "source_revision": "rev-new",
    }), encoding="utf-8")
    vault = tmp_path / "repository"
    installed = vault / ".obsidian" / "plugins" / "learningos-ui"
    installed.mkdir(parents=True)
    (installed / "main.js").write_text(installed_main, encoding="utf-8")
    (installed / "styles.css").write_text("css", encoding="utf-8")
    (installed / "manifest.json").write_text("{}", encoding="utf-8")
    (installed / "build-info.json").write_text(json.dumps(
        installed_info if installed_info is not None else {
            "source_fingerprint": "fp-old", "source_revision": "rev-old",
        }), encoding="utf-8")
    return vault, ui, installed


def test_plugin_check_flags_a_stale_installed_build(tmp_path):
    """#110: a vault running an older bundle is a warning naming reinstall."""
    vault, ui, _installed = _plugin_pair(tmp_path, installed_main="bundle-v1")
    row = health._ui_plugin_check(vault, ui_root=ui)
    assert row["id"] == "ui-plugin-current"
    assert row["status"] == "warning"
    assert "DIFFERENT BUILD" in row["summary"]
    assert "reinstall the plugin" in row["summary"]
    assert "install.py" in row["remedy"]
    assert [entry["name"] for entry in row["details"]["differing"]] == [
        "main.js", "build-info.json"]
    assert row["details"]["built"]["source_fingerprint"] == "fp-new"
    assert row["details"]["installed_build"]["source_fingerprint"] == "fp-old"


def test_plugin_check_is_ok_when_the_vault_runs_this_build(tmp_path):
    vault, ui, _installed = _plugin_pair(
        tmp_path,
        installed_info={"source_fingerprint": "fp-new", "source_revision": "rev-new"})
    row = health._ui_plugin_check(vault, ui_root=ui)
    assert row["status"] == "ok"
    assert "4 shipped files match" in row["summary"]


def test_plugin_check_is_unknown_without_an_install_or_a_checkout(tmp_path):
    """Core alone is not stale: missing metadata answers unknown, never warning."""
    vault, ui, _installed = _plugin_pair(tmp_path)
    missing_install = tmp_path / "empty-vault"
    missing_install.mkdir()
    row = health._ui_plugin_check(missing_install, ui_root=ui)
    assert row["status"] == "unknown"
    assert "No plugin is installed" in row["summary"]

    row = health._ui_plugin_check(vault, ui_root=tmp_path / "no-such-ui")
    assert row["status"] == "unknown"
    assert "unavailable" in row["summary"]


def test_health_report_carries_the_plugin_check(mini_repo):
    """The full report always carries `ui-plugin-current` (unknown here)."""
    report = health.build_health_report(mini_repo)
    row = next(c for c in report["checks"] if c["id"] == "ui-plugin-current")
    assert row["status"] == "unknown"

