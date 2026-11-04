"""Focused recovery-objective diagnostics for LearningOS vNext."""

from __future__ import annotations

import datetime as dt
import json
import shutil
from types import SimpleNamespace

import pytest

from learning_os.derive import health


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
    from learning_os.derive.projection import generate_all
    from learning_os.store.loader import load_repo
    repo = load_repo(mini_repo)
    from learning_os.derive.projection.outputs import write_outputs
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
    from learning_os.derive.projection import generate_all
    from learning_os.derive.projection.outputs import write_outputs
    from learning_os.store.contracts import manifest_contract
    from learning_os.store.loader import load_repo

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
    from learning_os.derive.projection import generate_all
    from learning_os.derive.projection.outputs import write_outputs
    from learning_os.store.contracts import manifest_contract
    from learning_os.store.loader import load_repo

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


def test_plugin_check_flags_disk_build_disagreement(tmp_path):
    """A disk difference requires source review, not a claim about executing code."""
    vault, ui, _installed = _plugin_pair(tmp_path, installed_main="bundle-v1")
    row = health._ui_plugin_check(vault, ui_root=ui)
    assert row["id"] == "ui-plugin-current"
    assert row["status"] == "warning"
    assert "differ from the comparison build" in row["summary"]
    assert "--ui-root" in row["remedy"]
    assert row["details"]["runtime_identity"] == "not-observed"
    assert row["details"]["comparison_ui_root"] == str(ui)
    assert row["details"]["comparison_source"] == "explicit-ui-root"
    assert [entry["name"] for entry in row["details"]["differing"]] == [
        "main.js", "build-info.json"]
    assert row["details"]["built"]["source_fingerprint"] == "fp-new"
    assert row["details"]["installed_build"]["source_fingerprint"] == "fp-old"


def test_plugin_check_is_ok_when_installed_files_match_this_build(tmp_path):
    vault, ui, _installed = _plugin_pair(
        tmp_path,
        installed_info={"source_fingerprint": "fp-new", "source_revision": "rev-new"})
    row = health._ui_plugin_check(vault, ui_root=ui)
    assert row["status"] == "ok"
    assert "4 shipped files match" in row["summary"]


def test_plugin_check_identifies_default_and_explicit_sources_without_trusting_metadata(tmp_path):
    vault, older_ui, installed = _plugin_pair(
        tmp_path,
        installed_info={"source_fingerprint": "fp-new", "source_revision": "rev-new"})
    selected_ui = tmp_path / "other-source"
    shutil.copytree(older_ui, selected_ui)
    (older_ui / "plugin" / "main.js").write_text("older-source")

    default = health._ui_plugin_check(vault)
    assert default["status"] == "warning"
    assert default["details"]["comparison_ui_root"] == str(older_ui)
    assert default["details"]["comparison_source"] == "default-sibling"
    assert default["details"]["runtime_identity"] == "not-observed"

    selected = health._ui_plugin_check(vault, ui_root=selected_ui)
    assert selected["status"] == "ok"
    assert selected["details"]["comparison_ui_root"] == str(selected_ui)
    assert selected["details"]["comparison_source"] == "explicit-ui-root"

    # Even matching claimed build metadata cannot conceal a changed asset.
    (installed / "main.js").write_text("changed-after-install")
    tampered = health._ui_plugin_check(vault, ui_root=selected_ui)
    assert tampered["status"] == "warning"
    assert [row["name"] for row in tampered["details"]["differing"]] == ["main.js"]


def test_health_cli_uses_one_selected_source_for_plugin_and_contract_lock(mini_repo):
    from repo_builders import run_los

    vault, older_ui, _installed = _plugin_pair(
        mini_repo.parent,
        installed_info={"source_fingerprint": "fp-new", "source_revision": "rev-new"})
    assert vault == mini_repo
    selected_ui = mini_repo.parent / "selected-ui"
    shutil.copytree(older_ui, selected_ui)
    version = health.declared_version(mini_repo)
    for ui, digest in ((older_ui, "obsolete"),
                       (selected_ui, health.declared_schema_sha256(mini_repo))):
        (ui / "contracts").mkdir()
        (ui / "contracts" / f"manifest-v{version}.lock.json").write_text(json.dumps({
            "contract_version": version, "schema_sha256": digest,
        }))
    (older_ui / "plugin" / "main.js").write_text("older-source")

    default = health.build_health_report(mini_repo)
    default_checks = {row["id"]: row for row in default["checks"]}
    assert default_checks["ui-plugin-current"]["status"] == "warning"
    assert default_checks["schema-core-ui-lock"]["status"] == "error"

    process = run_los(mini_repo, "health-report", "--ui-root", str(selected_ui), "--json")
    assert process.returncode == 0, process.stderr
    checks = {row["id"]: row for row in json.loads(process.stdout)["checks"]}
    assert checks["ui-plugin-current"]["status"] == "ok"
    assert checks["ui-plugin-current"]["details"]["comparison_ui_root"] == str(selected_ui)
    assert checks["schema-core-ui-lock"]["status"] == "ok"


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
    assert row["details"]["comparison_ui_root"] == str(tmp_path / "no-such-ui")


def test_health_report_carries_the_plugin_check(mini_repo):
    """The full report always carries `ui-plugin-current` (unknown here)."""
    report = health.build_health_report(mini_repo)
    row = next(c for c in report["checks"] if c["id"] == "ui-plugin-current")
    assert row["status"] == "unknown"


@pytest.mark.parametrize("component", [".obsidian", "plugins", "learningos-ui"])
def test_plugin_check_refuses_symlinked_installed_path_components(tmp_path, component):
    vault, ui, installed = _plugin_pair(
        tmp_path, installed_info={"source_fingerprint": "fp-new", "source_revision": "rev-new"})
    target = next(path for path in [installed, installed.parent, installed.parent.parent]
                  if path.name == component)
    moved = tmp_path / "indirect-install"
    target.rename(moved)
    target.symlink_to(moved, target_is_directory=True)
    # Explicit installed_dir must be inspected as supplied, without resolving
    # away the symlink that the installer and install:status refuse.
    row = health._ui_plugin_check(vault, ui_root=ui, installed_dir=installed)
    assert row["status"] == "error"


@pytest.mark.parametrize("install_missing", [False, True])
def test_plugin_check_refuses_interrupted_install_even_when_bytes_match(tmp_path, install_missing):
    vault, ui, installed = _plugin_pair(
        tmp_path, installed_info={"source_fingerprint": "fp-new", "source_revision": "rev-new"})
    (installed.parent / ".learningos-ui-install-transaction.json").write_text("{}")
    if install_missing:
        installed.rename(tmp_path / "old-install")
    row = health._ui_plugin_check(vault, ui_root=ui)
    assert row["status"] == "error"
    assert "transaction" in row["summary"].lower()


def test_plugin_check_never_approves_an_undeclared_build_file(tmp_path):
    vault, ui, _installed = _plugin_pair(
        tmp_path, installed_info={"source_fingerprint": "fp-new", "source_revision": "rev-new"})
    (ui / "plugin" / "unshipped.js").write_text("not in the shipping manifest")
    row = health._ui_plugin_check(vault, ui_root=ui)
    assert row["status"] == "error"
    assert "unshipped.js" in row["summary"]


@pytest.mark.parametrize("change", [
    {"schema_version": 2}, {"schema_version": True}, {"type": "other"}, {"unknown": True},
    {"shipped": ["../outside"]}, {"shipped": ["main.js", "main.js"]},
    {"vault_owned": ["main.js"]}, {"vault_owned": [{"invalid": "entry"}]},
])
def test_plugin_check_rejects_malformed_shipping_manifest(tmp_path, change):
    vault, ui, _installed = _plugin_pair(tmp_path)
    manifest_path = ui / "plugin-assets.json"
    manifest = json.loads(manifest_path.read_text())
    manifest.update(change)
    manifest_path.write_text(json.dumps(manifest))
    row = health._ui_plugin_check(vault, ui_root=ui)
    assert row["status"] == "unknown"
    assert "unavailable" in row["summary"]


def test_plugin_check_empty_install_directory_is_unknown(tmp_path):
    vault, ui, installed = _plugin_pair(tmp_path)
    for entry in installed.iterdir():
        entry.unlink()
    row = health._ui_plugin_check(vault, ui_root=ui)
    assert row["status"] == "unknown"
    assert "No plugin is installed" in row["summary"]
