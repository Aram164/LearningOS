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

from learning_os.commands.capability import (
    GESTURE_ALLOWLIST,
    UI_REVIEWED_ALLOWLIST,
    gesture_allowed,
)
from learning_os.contracts.capability_catalog import (
    gesture_admitted_capabilities,
    ui_reviewed_capabilities,
)
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


def test_an_agent_origin_semantic_request_is_still_refused(observe_repo: Path):
    """The boundary the old "never" was reaching for, stated precisely.

    This asserted that canonical semantics could never take the gesture path
    at all, which made a *current, binding* architecture decision unbuildable:
    ADR-017 designed the Atlas for Aram to author connections by hand in the
    app, and a readable refusal is still a refusal (review
    `workbench/audits/repair-review-2026-09-13`, D1). What actually protects
    canonical state is the producer, not the capability — so the four reviewed
    UI workflows are admitted over the `ui` channel, and every other origin
    claiming a gesture for them still fails closed, as here.
    """
    for channel in ("operator", "codex", "system-task"):
        envelope = _gesture_envelope(
            observe_repo, "concept.relations.change", {"op": "add"},
            f"gesture-canonical-{channel}")
        envelope["channel"] = channel
        envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
        proc = run_v2_capability(observe_repo, envelope)
        assert proc.returncode == 2, channel
        response = json.loads(proc.stdout)
        assert response["ok"] is False
        assert response["error"]["code"] == "UNCONFIRMED"
        assert "reviewed action in the LearningOS app" in response["error"]["message"]


def test_a_write_with_no_admission_at_all_is_refused_from_every_channel(
        observe_repo: Path):
    for channel in ("ui", "operator", "codex"):
        envelope = _gesture_envelope(
            observe_repo, "note.revise", {"note_id": "note-demo"},
            f"gesture-unadmitted-{channel}")
        envelope["channel"] = channel
        envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
        proc = run_v2_capability(observe_repo, envelope)
        assert proc.returncode == 2, channel
        assert json.loads(proc.stdout)["error"]["code"] == "UNCONFIRMED"


def test_allowlist_matches_the_capability_contract(repo_root: Path):
    contract = yaml.safe_load(
        (repo_root / "system/contracts/capabilities.yaml").read_text(encoding="utf-8"))
    rows = contract["commands"]
    admitted = {name for name, row in rows.items()
                if row.get("admission") == "direct-user-gesture"
                and not row.get("admission_channels")}
    assert admitted == set(GESTURE_ALLOWLIST) == {
        # Aram's own evidence, and the two unrouted inbox/Garden writers.
        "learner.observation.append", "capture.create", "garden.seed.create",
        # His own study record for one stage or unit, his own experience of a
        # resource, his own question, his own selection among authored routes.
        # Added 2026-09-13 for the installed UI's actual write paths; the
        # audit's F01 was Core refusing exactly these in the learner's face.
        "stage.progress.update", "unit.note.append", "stage.attachment.add",
        "detour.create", "detour.resolve", "source.feedback.record",
        "atlas.question.save", "unit.source-selection.set"}
    reviewed = {name for name, row in rows.items()
                if row.get("admission_channels") == ["ui"]}
    assert reviewed == set(UI_REVIEWED_ALLOWLIST) == {
        "concept.relations.change", "review.prepare", "review.apply",
        "unit.map.import"}


def test_contract_admission_is_readable_through_the_catalogue(repo_root: Path):
    """The loader's view and the enforcing sets are the same sets."""
    assert gesture_admitted_capabilities(repo_root) == GESTURE_ALLOWLIST
    assert ui_reviewed_capabilities(repo_root) == UI_REVIEWED_ALLOWLIST
    assert not (GESTURE_ALLOWLIST & UI_REVIEWED_ALLOWLIST)


def test_plan_content_and_note_semantics_stay_off_every_gesture_path():
    """Widening four reviewed workflows widened nothing else (D1)."""
    for capability in (
        "module.plan.import", "route.patch", "note.revise", "note.evidence.add",
        "unit.material-synthesis.publish", "ai-action.delivery.apply",
        "route.identity.migrate", "module.materials.compact",
    ):
        assert capability not in GESTURE_ALLOWLIST
        assert capability not in UI_REVIEWED_ALLOWLIST
        assert not gesture_allowed(capability, "ui")


def test_a_reviewed_workflow_is_admitted_only_over_the_ui_channel():
    for capability in UI_REVIEWED_ALLOWLIST:
        assert gesture_allowed(capability, "ui")
        for channel in ("operator", "codex", "system-task", None):
            assert not gesture_allowed(capability, channel), (capability, channel)
    # The learner's own study record is not channel-bound: `los observe` runs
    # over "operator" from his terminal.
    for capability in GESTURE_ALLOWLIST:
        assert gesture_allowed(capability, "operator")
        assert gesture_allowed(capability, "ui")


def test_gesture_refusal_says_what_to_do_instead(observe_repo: Path):
    """A refusal a learner can act on, not the name of an approval kind."""
    envelope = _gesture_envelope(
        observe_repo, "module.plan.import", {"module_id": "module-demo"},
        "gesture-recovery-001")
    proc = run_v2_capability(observe_repo, envelope)
    assert proc.returncode == 2
    message = json.loads(proc.stdout)["error"]["message"]
    assert "preflight" in message and "operator request" in message
    assert "is not admitted for" not in message


def test_observation_append_still_requires_the_gateway(observe_repo: Path):
    proc = run_los(observe_repo, "observation-append",
                   "--workspace", "workspace-demo", "--requirement", REQUIREMENT,
                   "--activity", "exercise", "--result", "partial")
    assert proc.returncode == 2
    assert "GatewayEnvelopeV2" in proc.stderr


def test_a_condition_recorded_both_ways_is_refused_at_intake(observe_repo: Path):
    """`--condition X --condition-not-met X` is a contradiction, not an input."""
    proc = run_los(observe_repo, "observe", REQUIREMENT, "--activity", "exercise",
                   "--result", "partial", "--condition", "unfamiliar-example",
                   "--condition-not-met", "unfamiliar-example")
    assert proc.returncode == 2
    assert "both met and not met" in proc.stderr


def test_stating_a_condition_did_not_hold_is_recorded_and_explained(observe_repo: Path):
    proc = run_los(observe_repo, "observe", REQUIREMENT, "--activity", "exercise",
                   "--result", "partial",
                   "--condition-not-met", "unfamiliar-example",
                   "--note", "I had already worked this exact example")
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)
    assert result["refuted_conditions"] == ["unfamiliar-example"]
    assert "different situation" in result["interpretation_notice"]
    assert "resets nothing" in result["interpretation_notice"]
    ledger = (observe_repo / "work/active/workspace-demo/observations.jsonl")
    recorded = json.loads(ledger.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert recorded["conditions_not_met"] == ["unfamiliar-example"]
    assert recorded["conditions"] == []


def test_the_unqualified_notice_offers_both_ways_to_settle_it(observe_repo: Path):
    proc = run_los(observe_repo, "observe", REQUIREMENT, "--activity", "exercise",
                   "--result", "partial", "--note", "still get this wrong")
    assert proc.returncode == 0, proc.stderr
    notice = json.loads(proc.stdout)["interpretation_notice"]
    assert "--condition unfamiliar-example" in notice
    assert "--condition-not-met unfamiliar-example" in notice
    assert "Two distinct qualified activities recorded after this" in notice
    assert "stop counting toward a current conclusion" in notice
