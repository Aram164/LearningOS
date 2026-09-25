"""Stage-independent ability evidence and reviewed cross-course transfer."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml
from gateway_helpers import approved_v2_call
from repo_builders import run_los

from learning_os.abilities import (
    ability_context,
    ability_fingerprint,
    bridge_source_freshness,
    read_ability_observations,
    validate_ability_registry,
)
from learning_os.learning_runtime import RuntimeInputError
from learning_os.loader import load_repo


@pytest.fixture
def ability_root(mini_repo: Path) -> Path:
    conditions = ["one predictor with nonzero variance", "intercept included"]
    source = "knowledge/notes/mathematics/note-demo.md"
    source_sha256 = "sha256:" + hashlib.sha256((mini_repo / source).read_bytes()).hexdigest()
    ability = {
        "title": "Derive simple least squares", "claim": "Derive slope and intercept.",
        "conditions": conditions, "evidence_spec": ["correct derivation"],
        "concept_ids": ["concept-expected-value"], "module_ids": ["module-demo"],
        "review": {"state": "reviewed", "reviewed_by": "test reviewer",
                   "reviewed_on": "2026-09-23"},
    }
    data = {"abilities": [
        {**ability, "id": "ability-sad-ols", "preparation_routes": []},
        {**ability, "id": "ability-aml-ols", "preparation_routes": []},
        {**ability, "id": "ability-aml-extension",
         "preparation_routes": [{"all_of": ["ability-aml-ols"],
                                 "reason": "The simple derivation prepares the extension."}]},
    ], "bridges": [
        {"from": "ability-sad-ols", "to": "ability-aml-ols",
         "kind": "equivalence", "carries": "Same slope and intercept derivation.",
         "changes": "Notation changes.", "conditions": conditions,
         "source": source, "source_sha256": source_sha256,
         "review": {"state": "reviewed", "reviewed_by": "test reviewer",
                    "reviewed_on": "2026-09-23"}},
        {"from": "ability-aml-ols", "to": "ability-aml-extension",
         "kind": "extension", "carries": "Preparation only.",
         "changes": "Extension needs its own demonstration.", "conditions": conditions,
         "source": source, "source_sha256": source_sha256,
         "review": {"state": "reviewed", "reviewed_by": "test reviewer",
                    "reviewed_on": "2026-09-23"}},
    ]}
    (mini_repo / "knowledge/abilities.yaml").write_text(
        yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return mini_repo


def _work(repo, aid: str, number: int, **changes) -> dict:
    ability = repo.abilities[aid]
    return {
        "id": f"ability-observation-{number}", "ability_id": aid,
        "ability_sha256": ability_fingerprint(ability),
        "claim": "I derived this from the stated problem.",
        "work_ref": f"conversation://test/work-{number}",
        "confirmation_ref": f"conversation://test/confirmation-{number}",
        "activity": "worked derivation", "result": "correct",
        "timestamp": f"2026-09-23T10:{number:02d}:00Z",
        "conditions": ability["conditions"], "evidence_tags": ability["evidence_spec"],
        "assistance": "none",
        "confirmed_by": "learner", **changes,
    }


def _append(root: Path, row: dict) -> None:
    ledger = root / "work/active/workspace-demo/ability-observations.jsonl"
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")


def _state(root: Path, aid: str) -> dict:
    return ability_context(load_repo(root), focus=aid)["ability"]


def test_no_stage_completion_or_shared_tag_grants_ability(ability_root: Path):
    for aid in ("ability-sad-ols", "ability-aml-ols", "ability-aml-extension"):
        assert _state(ability_root, aid)["state"] == "uncertain"
    assert _state(ability_root, "ability-aml-ols")["evidence"] == []


def test_reviewed_equivalence_transfers_only_independent_current_work(ability_root: Path):
    repo = load_repo(ability_root)
    row = _work(repo, "ability-sad-ols", 1)
    _append(ability_root, {**row, "assistance": "hint"})
    assert _state(ability_root, "ability-sad-ols")["state"] == "uncertain"
    assert _state(ability_root, "ability-aml-ols")["state"] == "uncertain"
    _append(ability_root, _work(repo, "ability-sad-ols", 2))
    assert _state(ability_root, "ability-sad-ols")["state"] == "supported"
    target = _state(ability_root, "ability-aml-ols")
    assert target["state"] == "supported"
    assert target["transfer"][0]["from"] == "ability-sad-ols"
    extension = _state(ability_root, "ability-aml-extension")
    assert extension["state"] == "nearby"
    assert extension["preparation_routes"][0]["supported"] == ["ability-aml-ols"]


def test_correct_label_without_criteria_is_not_support(ability_root: Path):
    repo = load_repo(ability_root)
    _append(ability_root, _work(repo, "ability-sad-ols", 1, evidence_tags=[]))
    state = _state(ability_root, "ability-sad-ols")
    assert state["state"] == "uncertain"
    assert any("criterion" in reason for reason in state["reasons"])
    assert _state(ability_root, "ability-aml-ols")["state"] == "uncertain"


def test_changed_bridge_source_withholds_transfer(ability_root: Path):
    repo = load_repo(ability_root)
    _append(ability_root, _work(repo, "ability-sad-ols", 1))
    assert _state(ability_root, "ability-aml-ols")["state"] == "supported"
    note = ability_root / "knowledge/notes/mathematics/note-demo.md"
    note.write_text(note.read_text(encoding="utf-8") + "\nChanged source.\n",
                    encoding="utf-8")
    focus = ability_context(load_repo(ability_root), focus="ability-aml-ols")
    assert focus["ability"]["state"] == "uncertain"
    assert focus["bridges"][0]["source_freshness"]["status"] == "stale"


@pytest.mark.full_repo
def test_live_extension_bridge_uses_stable_reviewed_source(real_repo):
    bridge = next(row for row in real_repo.ability_bridges
                  if row["from"] == "ability-sad-backprop-local"
                  and row["to"] == "ability-aml-backprop-layerwise")
    assert bridge["source"] == "knowledge/notes/cross-domain/note-aml-sad-master-wiring.md"
    assert bridge_source_freshness(real_repo, bridge)["status"] == "current"


def test_later_conflict_correction_and_definition_change(ability_root: Path):
    repo = load_repo(ability_root)
    _append(ability_root, _work(repo, "ability-sad-ols", 1))
    _append(ability_root, _work(repo, "ability-sad-ols", 2,
                                result="incorrect", assistance="hint"))
    assert _state(ability_root, "ability-sad-ols")["state"] == "uncertain"
    assert _state(ability_root, "ability-aml-ols")["state"] == "uncertain"
    _append(ability_root, _work(repo, "ability-sad-ols", 3,
                                supersedes="ability-observation-2"))
    assert _state(ability_root, "ability-sad-ols")["state"] == "supported"
    assert len(_state(ability_root, "ability-sad-ols")["evidence"]) == 3
    path = ability_root / "knowledge/abilities.yaml"
    data = yaml.safe_load(path.read_text())
    data["abilities"][0]["evidence_spec"] = ["a newly reviewed derivation"]
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    assert _state(ability_root, "ability-sad-ols")["state"] == "uncertain"
    assert _state(ability_root, "ability-aml-ols")["state"] == "uncertain"


def test_presentation_edits_do_not_invalidate_work(ability_root: Path):
    repo = load_repo(ability_root)
    _append(ability_root, _work(repo, "ability-sad-ols", 1))
    path = ability_root / "knowledge/abilities.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["abilities"][0]["title"] = "Derive a simple least-squares fit"
    data["abilities"][0]["review"]["reviewed_on"] = "2026-09-24"
    data["abilities"][0]["preparation_routes"] = [{
        "all_of": ["ability-aml-extension"], "reason": "Additional practice route."}]
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    assert _state(ability_root, "ability-sad-ols")["state"] == "supported"


def test_retirement_preserves_history_and_unrelated_writes(ability_root: Path):
    repo = load_repo(ability_root)
    _append(ability_root, _work(repo, "ability-sad-ols", 1))
    registry = ability_root / "knowledge/abilities.yaml"
    data = yaml.safe_load(registry.read_text(encoding="utf-8"))
    data["abilities"][0]["lifecycle"] = "retired"
    registry.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    retired_repo = load_repo(ability_root)
    assert validate_ability_registry(retired_repo) == []
    retired = ability_context(retired_repo, focus="ability-sad-ols")["ability"]
    assert retired["state"] == "unmapped"
    assert retired["lifecycle"] == "retired"
    assert len(retired["evidence"]) == 1
    assert _state(ability_root, "ability-aml-ols")["state"] == "uncertain"
    independent = approved_v2_call(
        ability_root, capability="ability.candidate.append",
        payload={"from_ability": "ability-aml-ols", "to_ability": "ability-aml-extension",
                 "kind": "connection", "carries": "Independent connection",
                 "changes": "Needs review", "condition": [],
                 "source_ref": "conversation://test/independent"},
        artifact_ids=["ability-candidates"], idempotency_key="retired-independent")
    assert independent.returncode == 0, independent.stderr
    refused = approved_v2_call(
        ability_root, capability="ability.candidate.append",
        payload={"from_ability": "ability-sad-ols", "to_ability": "ability-aml-extension",
                 "kind": "connection", "carries": "Retired connection",
                 "changes": "Must not be added", "condition": [],
                 "source_ref": "conversation://test/retired"},
        artifact_ids=["ability-candidates"], idempotency_key="retired-refused")
    assert refused.returncode != 0
    assert "two active abilities" in refused.stdout


def test_unicode_line_separators_round_trip_in_both_ledgers(ability_root: Path):
    repo = load_repo(ability_root)
    observations = ability_root / "work/active/workspace-demo/ability-observations.jsonl"
    with observations.open("w", encoding="utf-8") as handle:
        for number, character in enumerate(("\u2028", "\u2029", "\u0085"), 1):
            row = _work(repo, "ability-sad-ols", number,
                        claim=f"First line{character}second line")
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    assert len(read_ability_observations(load_repo(ability_root))) == 3
    candidates = ability_root / "knowledge/ability-candidates.jsonl"
    with candidates.open("w", encoding="utf-8") as handle:
        for number, character in enumerate(("\u2028", "\u2029", "\u0085")):
            handle.write(json.dumps({
                "id": f"ability-candidate-{number:032x}", "from": "ability-sad-ols",
                "to": "ability-aml-extension", "kind": "connection",
                "carries": f"First line{character}second line", "changes": "Unknown",
                "conditions": [], "source_ref": "conversation://test/discovery",
                "created_at": "2026-09-23T10:00:00Z", "state": "candidate",
            }, ensure_ascii=False) + "\n")
    from learning_os.abilities import read_ability_candidates
    assert len(read_ability_candidates(load_repo(ability_root))) == 3


def test_candidate_bridge_and_incomplete_conditions_never_transfer(ability_root: Path):
    repo = load_repo(ability_root)
    _append(ability_root, _work(repo, "ability-sad-ols", 1))
    path = ability_root / "knowledge/abilities.yaml"
    data = yaml.safe_load(path.read_text())
    data["bridges"][0]["review"]["state"] = "candidate"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    assert _state(ability_root, "ability-aml-ols")["state"] == "uncertain"
    data["bridges"][0]["review"]["state"] = "reviewed"
    data["bridges"][0]["conditions"] = ["intercept included"]
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    assert any("equivalence omits" in item for item in validate_ability_registry(load_repo(ability_root)))
    assert _state(ability_root, "ability-aml-ols")["state"] == "uncertain"


def test_malformed_correction_fails_closed(ability_root: Path):
    repo = load_repo(ability_root)
    _append(ability_root, _work(repo, "ability-sad-ols", 1,
                                supersedes="ability-observation-nonexistent"))
    with pytest.raises(RuntimeInputError, match="invalid correction"):
        read_ability_observations(load_repo(ability_root))


def test_governed_append_requires_exact_claim_and_preserves_ledger(ability_root: Path):
    payload = {
        "workspace": "workspace-demo", "ability": "ability-sad-ols",
        "claim": "I derived slope and intercept for the stated one-predictor exercise.",
        "work_ref": "conversation://test/work-1",
        "confirmation_ref": "conversation://test/confirmation-1",
        "activity": "worked derivation", "result": "correct",
        "assistance": "none", "condition": ["one predictor with nonzero variance",
                                              "intercept included"],
        "evidence_tag": ["correct derivation"],
    }
    bare = run_los(ability_root, "ability-observation-append",
                   "--workspace", payload["workspace"], "--ability", payload["ability"],
                   "--claim", payload["claim"], "--work-ref", payload["work_ref"],
                   "--confirmation-ref", payload["confirmation_ref"],
                   "--activity", payload["activity"], "--result", payload["result"],
                   "--assistance", "none")
    assert bare.returncode == 2
    assert "GatewayEnvelopeV2" in bare.stderr
    written = approved_v2_call(ability_root,
                               capability="learner.ability-observation.append",
                               payload=payload, artifact_ids=["workspace-demo"],
                               idempotency_key="ability-test-1")
    assert written.returncode == 0, written.stderr
    rows = read_ability_observations(load_repo(ability_root))
    assert len(rows) == 1
    assert rows[0]["confirmation_ref"] == payload["confirmation_ref"]
    assert _state(ability_root, "ability-sad-ols")["state"] == "supported"


def test_tentative_conversation_connection_is_visible_without_credit(ability_root: Path):
    repo = load_repo(ability_root)
    _append(ability_root, _work(repo, "ability-sad-ols", 1))
    before = _state(ability_root, "ability-aml-extension")["state"]
    written = approved_v2_call(
        ability_root, capability="ability.candidate.append",
        payload={"from_ability": "ability-sad-ols", "to_ability": "ability-aml-extension",
                 "kind": "equivalence", "carries": "Possible transfer from a conversation.",
                 "changes": "Still needs review.",
                 "condition": ["one predictor with nonzero variance"],
                 "source_ref": "conversation://test/discovery-1"},
        artifact_ids=["ability-candidates"], idempotency_key="candidate-test-1")
    assert written.returncode == 0, written.stdout
    focus = ability_context(load_repo(ability_root), focus="ability-aml-extension")
    assert focus["ability"]["state"] == before == "nearby"
    assert focus["candidate_connections"][0]["state"] == "candidate"
    assert focus["candidate_connections"][0]["source_ref"] == "conversation://test/discovery-1"
    assert ability_context(load_repo(ability_root))["candidate_connection_count"] == 1


def test_horizon_carries_its_own_bridges_and_tentative_connections(ability_root: Path):
    """One brief read is enough to draw the map; paging never dangles an edge."""
    brief = ability_context(load_repo(ability_root))
    assert {(row["from"], row["to"]) for row in brief["bridges"]} == {
        ("ability-sad-ols", "ability-aml-ols"),
        ("ability-aml-ols", "ability-aml-extension")}
    assert all(row["source_freshness"]["status"] == "current" for row in brief["bridges"])
    assert brief["candidate_connections"] == []
    written = approved_v2_call(
        ability_root, capability="ability.candidate.append",
        payload={"from_ability": "ability-sad-ols", "to_ability": "ability-aml-extension",
                 "kind": "connection", "carries": "Noticed in the app.",
                 "changes": "Needs review before it carries anything.",
                 "condition": [], "source_ref": "conversation://learningos-app/test-1"},
        artifact_ids=["ability-candidates"], idempotency_key="candidate-horizon-1")
    assert written.returncode == 0, written.stdout
    brief = ability_context(load_repo(ability_root))
    assert [row["source_ref"] for row in brief["candidate_connections"]] == [
        "conversation://learningos-app/test-1"]
    # A page that omits one end keeps that edge out of the horizon.
    narrow = ability_context(load_repo(ability_root), limit=2)
    listed = {row["id"] for row in narrow["abilities"]}
    assert all(row["from"] in listed and row["to"] in listed for row in narrow["bridges"])
    assert all(row["from"] in listed and row["to"] in listed
               for row in narrow["candidate_connections"])
    assert narrow["candidate_connection_count"] == 1
