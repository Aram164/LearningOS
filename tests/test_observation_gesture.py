"""Finding 0: asymmetric admission for learner evidence.

Aram recording his own results is the one write where the author is the
ground truth: append-only ledger, tested --supersedes correction path, one
JSONL line of blast radius. `los observe` therefore takes the snapshot and
revision guard under the operator lock instead of requiring the caller to
supply and hash them. Agent writes — including canonical semantics — keep
the full envelope ceremony, and the gesture kind stays admitted only for
the closed user-originated allowlist: anything else claiming it is the
untrusted producer claiming to be the trusted one.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
import yaml
from gateway_helpers import run_v2_capability
from repo_builders import _add_material_overview, add_curriculum, run_los, write_yaml

from learning_os.commands.capability import GESTURE_ALLOWLIST
from learning_os.contracts.gateway import intent_sha256
from learning_os.fingerprint import canonical_fingerprint
from learning_os.transactions import artifact_revision

MAP = "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
REQUIREMENT = "req-demo-l01-demo"

TARGET = {
    "concept": "concept-expected-value",
    "capability": {"kind": "explain", "operands": ["expectation"]},
    "conditions": ["unfamiliar-example"],
    "evidence_spec": ["explain-reason"],
}


@pytest.fixture()
def observe_repo(mini_repo: Path) -> Path:
    """Synthetic repo with one requirement Aram can record evidence against."""
    add_curriculum(mini_repo)
    _add_material_overview(mini_repo)
    data = yaml.safe_load((mini_repo / MAP).read_text(encoding="utf-8"))
    stage = data["stages"][0]
    stage["concepts"] = ["concept-expected-value"]
    stage["runtime_target"] = copy.deepcopy(TARGET)
    write_yaml(mini_repo / MAP, data)
    return mini_repo


def _gesture_envelope(root: Path, capability: str, payload: dict, key: str) -> dict:
    envelope = {
        "schema_version": 2,
        "request_id": f"request-{key}",
        "idempotency_key": key,
        "capability": capability,
        "channel": "operator",
        "expected_snapshot": f"sha256:{canonical_fingerprint(root)}",
        "expected_revisions": {},
        "approval": {"kind": "direct-user-gesture",
                     "subject_sha256": "sha256:" + "0" * 64},
        "payload": payload,
    }
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    return envelope


def test_observe_records_evidence_without_envelope(observe_repo: Path):
    proc = run_los(observe_repo, "observe", REQUIREMENT,
                   "--activity", "exercise", "--result", "partial",
                   "--condition", "unfamiliar-example",
                   "--note", "3/5, missed the asymptotic case")
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)
    assert result["ok"] is True
    assert result["workspace_id"] == "workspace-demo"
    assert result["observation_id"].startswith("observation-")
    ledger = observe_repo / "work/active/workspace-demo/observations.jsonl"
    rows = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()
            if line.strip()]
    assert len(rows) == 1
    row = rows[0]
    assert row["id"] == result["observation_id"]
    assert row["requirement"] == REQUIREMENT
    assert row["result"] == "partial"
    assert row["context"] == "3/5, missed the asymptotic case"
    assert row["requirement_sha256"].startswith("sha256:")
    receipt = yaml.safe_load(
        (observe_repo / result["receipt_path"]).read_text(encoding="utf-8"))
    assert receipt["schema_version"] == 2
    assert receipt["request"]["approval"]["kind"] == "direct-user-gesture"
    assert receipt["capability"] == "learner.observation.append"


def test_observe_correction_path_uses_supersedes(observe_repo: Path):
    first = run_los(observe_repo, "observe", REQUIREMENT,
                    "--activity", "exercise", "--result", "incorrect")
    assert first.returncode == 0, first.stderr
    first_id = json.loads(first.stdout)["observation_id"]
    second = run_los(observe_repo, "observe", REQUIREMENT,
                     "--activity", "exercise", "--result", "partial",
                     "--supersedes", first_id)
    assert second.returncode == 0, second.stderr
    ledger = observe_repo / "work/active/workspace-demo/observations.jsonl"
    rows = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()
            if line.strip()]
    assert [row.get("supersedes") for row in rows] == [None, first_id]


def test_observe_refuses_unknown_requirement(observe_repo: Path):
    proc = run_los(observe_repo, "observe", "req-no-such-stage",
                   "--activity", "exercise", "--result", "partial")
    assert proc.returncode == 2
    assert "unknown requirement" in proc.stderr


def test_observe_refuses_ambiguous_workspace(observe_repo: Path):
    second = observe_repo / "work/active/workspace-demo2"
    second.mkdir(parents=True)
    text = (observe_repo / "work/active/workspace-demo/CONTEXT.md").read_text(encoding="utf-8")
    (second / "CONTEXT.md").write_text(
        text.replace("workspace-demo", "workspace-demo2").replace(
            "Demo workspace", "Second demo workspace"),
        encoding="utf-8")
    proc = run_los(observe_repo, "observe", REQUIREMENT,
                   "--activity", "exercise", "--result", "partial")
    assert proc.returncode == 2
    assert "pass --workspace to choose one" in proc.stderr
    explicit = run_los(observe_repo, "observe", REQUIREMENT,
                       "--workspace", "workspace-demo",
                       "--activity", "exercise", "--result", "partial")
    assert explicit.returncode == 0, explicit.stderr


def test_allowlisted_gesture_envelope_keeps_the_full_ceremony(
    observe_repo: Path,
):
    """A remote gesture envelope for the allowlisted capability still
    asserts its snapshot and intent exactly like any other envelope — the
    cheap path requires the local terminal (`los observe`), never a claim
    over the wire."""
    envelope = _gesture_envelope(
        observe_repo, "learner.observation.append",
        {"workspace": "workspace-demo", "requirement": REQUIREMENT,
         "activity": "exercise", "result": "partial"},
        "gesture-allowlisted-001")
    envelope["expected_revisions"] = {
        "workspace-demo": artifact_revision(observe_repo, "workspace-demo")}
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    proc = run_v2_capability(observe_repo, envelope)
    assert proc.returncode == 0, proc.stdout
    response = json.loads(proc.stdout)
    assert response["ok"] is True
    assert response["result"]["artifact_revisions"] == {"workspace-demo": 1}


def test_canonical_semantics_can_never_take_the_gesture_path(observe_repo: Path):
    envelope = _gesture_envelope(
        observe_repo, "concept.relations.change", {"op": "add"}, "gesture-canonical-001")
    proc = run_v2_capability(observe_repo, envelope)
    assert proc.returncode == 2
    response = json.loads(proc.stdout)
    assert response["ok"] is False
    assert response["error"]["code"] == "UNCONFIRMED"


def test_allowlist_matches_the_capability_contract(repo_root: Path):
    contract = yaml.safe_load(
        (repo_root / "system/contracts/capabilities.yaml").read_text(encoding="utf-8"))
    admitted = {name for name, row in contract["commands"].items()
                if row.get("admission") == "direct-user-gesture"}
    assert admitted == set(GESTURE_ALLOWLIST) == {
        "learner.observation.append", "capture.create", "garden.seed.create"}


def test_observation_append_still_requires_the_gateway(observe_repo: Path):
    proc = run_los(observe_repo, "observation-append",
                   "--workspace", "workspace-demo", "--requirement", REQUIREMENT,
                   "--activity", "exercise", "--result", "partial")
    assert proc.returncode == 2
    assert "GatewayEnvelopeV2" in proc.stderr
