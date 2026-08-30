"""Exact-pair release receipt: generation and verification (Phase 9)."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

import pytest
import release_pair_receipt as rpr

WORKFLOW_ENV = {
    "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
}


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def _init_and_commit(repo: Path) -> str:
    _git(repo, "init", "-q")
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True, capture_output=True)
    _git(repo, "add", "-A")
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True,
                   capture_output=True, env={**os.environ, **WORKFLOW_ENV})
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, check=True,
                            capture_output=True, text=True)
    return result.stdout.strip()


def _sha256(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def _make_core(tmp_path: Path) -> Path:
    core = tmp_path / "core"
    contracts = core / "system" / "contracts"
    contracts.mkdir(parents=True)
    (contracts / "data-contract.yaml").write_text("contract_version: 14\n", encoding="utf-8")
    schema_dir = core / "system" / "schema"
    schema_dir.mkdir(parents=True)
    schema_file = schema_dir / "manifest.schema.json"
    schema_file.write_text("{}", encoding="utf-8")
    schema_sha = _sha256(schema_file.read_bytes())
    (contracts / "manifest-contract.yaml").write_text(
        "contract_version: 8\n"
        "schema_path: system/schema/manifest.schema.json\n"
        f"schema_sha256: '{schema_sha}'\n",
        encoding="utf-8",
    )
    return core


def _make_ui(tmp_path: Path, *, name: str = "ui") -> Path:
    ui = tmp_path / name
    plugin = ui / "plugin"
    plugin.mkdir(parents=True)
    (ui / ".gitignore").write_text("plugin/build-info.json\n", encoding="utf-8")
    (plugin / "main.js").write_bytes(b"'use strict';\nmodule.exports = {};\n")
    (plugin / "styles.css").write_bytes(b"body { color: black; }\n")
    (plugin / "manifest.json").write_text('{"version": "2.0.0"}', encoding="utf-8")
    return ui


def _write_build_info(ui: Path, *, ui_sha: str, core_sha: str, **overrides) -> None:
    bundle_sha256 = _sha256((ui / "plugin" / "main.js").read_bytes())
    stylesheet_sha256 = _sha256((ui / "plugin" / "styles.css").read_bytes())
    info = {
        "source_revision": ui_sha,
        "core_revision": core_sha,
        "source_dirty": False,
        "core_dirty": False,
        "manifest_contract_version": 8,
        "source_fingerprint": "sha256:" + "a" * 64,
        "bundle_sha256": bundle_sha256,
        "stylesheet_sha256": stylesheet_sha256,
    }
    info.update(overrides)
    (ui / "plugin" / "build-info.json").write_text(json.dumps(info), encoding="utf-8")


@pytest.fixture()
def clean_pair(tmp_path: Path) -> dict:
    core = _make_core(tmp_path)
    core_sha = _init_and_commit(core)
    ui = _make_ui(tmp_path)
    ui_sha = _init_and_commit(ui)
    _write_build_info(ui, ui_sha=ui_sha, core_sha=core_sha)
    return {"core": core, "ui": ui, "core_sha": core_sha, "ui_sha": ui_sha}


def _generate(pair: dict, **overrides) -> dict:
    kwargs = {
        "core_root": pair["core"], "ui_root": pair["ui"],
        "core_sha": pair["core_sha"], "ui_sha": pair["ui_sha"],
        "workflow_run_id": "123", "workflow_run_attempt": "1",
    }
    kwargs.update(overrides)
    return rpr.generate(**kwargs)


# ---- generation --------------------------------------------------------

def test_a_valid_exact_pair_generates_a_schema_valid_receipt(clean_pair):
    receipt = _generate(clean_pair)
    rpr.validate_receipt(receipt)
    assert receipt["core_sha"] == clean_pair["core_sha"]
    assert receipt["ui_sha"] == clean_pair["ui_sha"]
    assert receipt["data_contract_version"] == 14
    assert receipt["manifest_contract_version"] == 8
    assert set(receipt["shipped_asset_sha256"]) == set(rpr.SHIPPED_ASSETS)
    for name in rpr.SHIPPED_ASSETS:
        assert receipt["shipped_asset_sha256"][name] == _sha256(
            (clean_pair["ui"] / "plugin" / name).read_bytes()
        )
    assert receipt["system_check_passed"] is True
    assert receipt["stress_scope"] == "not-run-materials-unprovisioned"


def test_malformed_sha_is_refused(clean_pair):
    with pytest.raises(rpr.ReleasePairReceiptError, match="40-character"):
        _generate(clean_pair, core_sha="not-a-sha")


def test_wrong_core_sha_is_refused(clean_pair):
    fake = "0" * 40
    with pytest.raises(rpr.ReleasePairReceiptError, match="does not equal the requested SHA"):
        _generate(clean_pair, core_sha=fake)


def test_wrong_ui_sha_is_refused(clean_pair):
    fake = "1" * 40
    with pytest.raises(rpr.ReleasePairReceiptError, match="does not equal the requested SHA"):
        _generate(clean_pair, ui_sha=fake)


def test_dirty_core_worktree_is_refused(clean_pair):
    (clean_pair["core"] / "system" / "contracts" / "data-contract.yaml").write_text(
        "contract_version: 15\n", encoding="utf-8")
    with pytest.raises(rpr.ReleasePairReceiptError, match="dirty"):
        _generate(clean_pair)


def test_dirty_ui_worktree_is_refused(clean_pair):
    (clean_pair["ui"] / "plugin" / "manifest.json").write_text('{"version": "9.9.9"}', encoding="utf-8")
    with pytest.raises(rpr.ReleasePairReceiptError, match="dirty"):
        _generate(clean_pair)


def test_unknown_git_state_is_refused(clean_pair, monkeypatch):
    def fail(*_args, **_kwargs):
        raise FileNotFoundError("git not found")
    monkeypatch.setattr(rpr.subprocess, "run", fail)
    with pytest.raises(rpr.ReleasePairReceiptError, match="cannot run"):
        _generate(clean_pair)


def test_build_info_dirty_flag_is_refused(clean_pair):
    _write_build_info(clean_pair["ui"], ui_sha=clean_pair["ui_sha"],
                      core_sha=clean_pair["core_sha"], source_dirty=True)
    with pytest.raises(rpr.ReleasePairReceiptError, match="source_dirty"):
        _generate(clean_pair)


def test_build_info_contract_version_mismatch_is_refused(clean_pair):
    _write_build_info(
        clean_pair["ui"], ui_sha=clean_pair["ui_sha"],
        core_sha=clean_pair["core_sha"], manifest_contract_version=9,
    )
    with pytest.raises(rpr.ReleasePairReceiptError, match="manifest_contract_version"):
        _generate(clean_pair)


# ---- verification --------------------------------------------------------

def _artifact_dir(clean_pair: dict, receipt: dict, tmp_path: Path) -> Path:
    artifact = tmp_path / "artifact"
    plugin = artifact / "plugin"
    plugin.mkdir(parents=True)
    for name in rpr.SHIPPED_ASSETS:
        (plugin / name).write_bytes((clean_pair["ui"] / "plugin" / name).read_bytes())
    return artifact


def test_a_valid_artifact_verifies(clean_pair, tmp_path):
    receipt = _generate(clean_pair)
    artifact = _artifact_dir(clean_pair, receipt, tmp_path)
    rpr.verify(receipt, artifact)  # must not raise


def test_wrong_schema_version_is_refused(clean_pair, tmp_path):
    receipt = _generate(clean_pair)
    artifact = _artifact_dir(clean_pair, receipt, tmp_path)
    receipt["schema_version"] = 2
    with pytest.raises(rpr.ReleasePairReceiptError, match="schema validation"):
        rpr.verify(receipt, artifact)


@pytest.mark.parametrize("name", rpr.SHIPPED_ASSETS)
def test_every_shipped_asset_hash_mismatch_is_refused(clean_pair, tmp_path, name):
    receipt = _generate(clean_pair)
    artifact = _artifact_dir(clean_pair, receipt, tmp_path)
    target = artifact / "plugin" / name
    target.write_bytes(target.read_bytes() + b"\ntampered\n")
    with pytest.raises(rpr.ReleasePairReceiptError, match=rf"{re.escape(name)} sha256"):
        rpr.verify(receipt, artifact)


def test_runtime_source_fingerprint_mismatch_is_refused(clean_pair, tmp_path):
    receipt = _generate(clean_pair)
    artifact = _artifact_dir(clean_pair, receipt, tmp_path)
    receipt["runtime_source_fingerprint"] = "sha256:" + "e" * 64
    with pytest.raises(rpr.ReleasePairReceiptError, match="source_fingerprint"):
        rpr.verify(receipt, artifact)


@pytest.mark.parametrize("mutation", ["missing", "surplus"])
def test_shipped_asset_hash_map_is_closed(clean_pair, tmp_path, mutation):
    receipt = _generate(clean_pair)
    artifact = _artifact_dir(clean_pair, receipt, tmp_path)
    if mutation == "missing":
        receipt["shipped_asset_sha256"].pop("manifest.json")
    else:
        receipt["shipped_asset_sha256"]["extra.js"] = "sha256:" + "f" * 64
    with pytest.raises(rpr.ReleasePairReceiptError, match="schema validation"):
        rpr.verify(receipt, artifact)


def test_missing_asset_is_refused(clean_pair, tmp_path):
    receipt = _generate(clean_pair)
    artifact = _artifact_dir(clean_pair, receipt, tmp_path)
    (artifact / "plugin" / "manifest.json").unlink()
    with pytest.raises(rpr.ReleasePairReceiptError, match="missing shipped file"):
        rpr.verify(receipt, artifact)


def test_surplus_asset_is_refused(clean_pair, tmp_path):
    receipt = _generate(clean_pair)
    artifact = _artifact_dir(clean_pair, receipt, tmp_path)
    (artifact / "plugin" / "extra.txt").write_text("unexpected", encoding="utf-8")
    with pytest.raises(rpr.ReleasePairReceiptError, match="undeclared file"):
        rpr.verify(receipt, artifact)


def test_verify_rejects_a_receipt_whose_build_info_sha_disagrees(clean_pair, tmp_path):
    receipt = _generate(clean_pair)
    artifact = _artifact_dir(clean_pair, receipt, tmp_path)
    tampered_info = json.loads((artifact / "plugin" / "build-info.json").read_text(encoding="utf-8"))
    tampered_info["core_revision"] = "9" * 40
    build_info_path = artifact / "plugin" / "build-info.json"
    build_info_path.write_text(json.dumps(tampered_info), encoding="utf-8")
    receipt["shipped_asset_sha256"]["build-info.json"] = _sha256(
        build_info_path.read_bytes()
    )
    with pytest.raises(rpr.ReleasePairReceiptError, match="core_revision"):
        rpr.verify(receipt, artifact)


def test_verify_cross_checks_build_info_contract_version(clean_pair, tmp_path):
    receipt = _generate(clean_pair)
    artifact = _artifact_dir(clean_pair, receipt, tmp_path)
    build_info_path = artifact / "plugin" / "build-info.json"
    tampered_info = json.loads(build_info_path.read_text(encoding="utf-8"))
    tampered_info["manifest_contract_version"] = 9
    build_info_path.write_text(json.dumps(tampered_info), encoding="utf-8")
    receipt["shipped_asset_sha256"]["build-info.json"] = _sha256(
        build_info_path.read_bytes()
    )
    with pytest.raises(rpr.ReleasePairReceiptError, match="manifest_contract_version"):
        rpr.verify(receipt, artifact)


# ---- workflow-policy: release-pair.yml -------------------------------------

def test_release_pair_workflow_checks_out_both_repositories_at_exact_shas():
    text = (rpr.ROOT / ".github" / "workflows" / "release-pair.yml").read_text(encoding="utf-8")
    assert "core_sha" in text and "ui_sha" in text
    assert "ref: ${{ steps.inputs.outputs.core_sha }}" in text
    assert "ref: ${{ steps.inputs.outputs.ui_sha }}" in text


def test_release_pair_workflow_runs_system_check():
    text = (rpr.ROOT / ".github" / "workflows" / "release-pair.yml").read_text(encoding="utf-8")
    assert "make system-check" in text
    assert "make -C repository system-check" in text or "working-directory: repository" in text
