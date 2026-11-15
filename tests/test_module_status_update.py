"""Tests for ``module.status.update`` gateway command (WORKFLOWS §19)."""

from __future__ import annotations

import copy
import json

import pytest
import yaml
from gateway_helpers import approved_v2_cli, approved_v2_envelope, run_v2_capability
from repo_builders import add_curriculum, run_los

from learning_os.derive.validation import validate
from learning_os.store.contracts.gateway import intent_sha256
from learning_os.store.loader import load_repo


def _module_path(repo_root):
    return repo_root / "curriculum/modules/module-demo/module.yaml"


def _gateway_result(proc) -> dict:
    return json.loads(proc.stdout)["result"]


def test_module_status_update_bare_cli_refuses(mini_repo):
    add_curriculum(mini_repo)
    before = _module_path(mini_repo).read_bytes()
    proc = run_los(mini_repo, "module-status-update", "module-demo", "--status", "completed")
    assert proc.returncode == 2
    assert "GatewayEnvelopeV2" in proc.stderr
    assert _module_path(mini_repo).read_bytes() == before


@pytest.mark.parametrize(
    ("argv", "match"),
    [
        (["module-ghost", "--status", "completed"], "module not found"),
        (["module-demo", "--status", "bogus"], "invalid choice"),
        (["module-demo", "--status", "completed", "--expected-revision", "bogus"], "invalid expected revision"),
    ],
)
def test_module_status_update_refuses_invalid_inputs(mini_repo, argv, match):
    add_curriculum(mini_repo)
    before = _module_path(mini_repo).read_bytes()
    proc = run_los(mini_repo, "module-status-update", *argv)
    assert proc.returncode == 2, proc.stderr
    assert match in proc.stderr
    assert _module_path(mini_repo).read_bytes() == before


def test_module_status_update_changes_only_status_and_records_receipt(mini_repo):
    add_curriculum(mini_repo)
    before = yaml.safe_load(_module_path(mini_repo).read_text(encoding="utf-8"))
    applied = approved_v2_cli(
        mini_repo,
        "module-status-update",
        "module-demo",
        "--status",
        "completed",
        artifact_ids=["module-demo"],
        idempotency_key="module-status-completed-001",
    )
    assert applied.returncode == 0, applied.stdout + applied.stderr
    result = _gateway_result(applied)
    assert result["module_id"] == "module-demo"
    assert result["status"] == "completed"
    assert result["path"] == "curriculum/modules/module-demo/module.yaml"
    assert result["receipt_path"]

    after = yaml.safe_load(_module_path(mini_repo).read_text(encoding="utf-8"))
    expected = copy.deepcopy(before)
    expected["status"] = "completed"
    assert after == expected

    receipt = yaml.safe_load((mini_repo / result["receipt_path"]).read_text(encoding="utf-8"))
    assert receipt["capability"] == "module.status.update"
    assert receipt["artifact_revisions"]["module-demo"] == {"before": 0, "after": 1}
    assert not [i for i in validate(load_repo(mini_repo)) if i.severity == "E"]


def test_module_status_update_stale_revision_refuses(mini_repo):
    add_curriculum(mini_repo)
    proc = approved_v2_cli(
        mini_repo,
        "module-status-update",
        "module-demo",
        "--status",
        "paused",
        artifact_ids=["module-demo"],
        idempotency_key="module-status-first",
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    envelope = approved_v2_envelope(
        mini_repo,
        capability="module.status.update",
        payload={"module_id": "module-demo", "status": "completed"},
        artifact_ids=["module-demo"],
        idempotency_key="module-status-stale",
    )
    envelope["expected_revisions"] = {"module-demo": 0}
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    stale = run_v2_capability(mini_repo, envelope)
    assert stale.returncode != 0
    assert yaml.safe_load(_module_path(mini_repo).read_text(encoding="utf-8"))["status"] == "paused"
