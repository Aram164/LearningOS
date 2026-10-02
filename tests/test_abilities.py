"""Stage-independent ability evidence and reviewed cross-course transfer."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC
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


def _grow_registry(root: Path, count: int) -> list[str]:
    """Append reviewed abilities so the horizon must page; returns their ids."""
    path = root / "knowledge/abilities.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    template = next(row for row in data["abilities"]
                    if row["id"] == "ability-sad-ols")
    ids = []
    for number in range(count):
        aid = f"ability-zz-extra-{number:02d}"
        data["abilities"].append({**template, "id": aid,
                                  "title": f"Extra ability {number}",
                                  "preparation_routes": []})
        ids.append(aid)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return ids


def _distant_bridge(root: Path) -> None:
    """One reviewed bridge from page one to an ability only page two lists."""
    path = root / "knowledge/abilities.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    template = data["bridges"][0]
    data["bridges"].append({**template, "from": "ability-aml-ols",
                            "to": "ability-zz-extra-57"})
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def test_horizon_pages_enumerate_every_ability_once(ability_root: Path):
    import shlex

    _grow_registry(ability_root, 58)
    first = run_los(ability_root, "ability-context", "--limit", "50")
    assert first.returncode == 0, first.stderr
    page = json.loads(first.stdout)
    assert page["total"] == 61 and page["returned"] == 50
    assert page["offset"] == 0
    assert page["next_offset"] == 50 and page["has_more"] is True
    assert page["truncated"] is True
    assert page["expand"] == "ability-context ABILITY_ID"
    follow = run_los(ability_root, *shlex.split(page["expansions"]["next"]))
    assert follow.returncode == 0, follow.stderr
    tail = json.loads(follow.stdout)
    assert tail["offset"] == 50 and tail["returned"] == 11
    assert tail["total"] == 61
    assert tail["next_offset"] is None and tail["has_more"] is False
    assert tail["expansions"]["next"] is None
    ids = ([row["id"] for row in page["abilities"]]
           + [row["id"] for row in tail["abilities"]])
    assert len(set(ids)) == 61
    # One global rank, not per-page ranks: every fixture ability is
    # uncertain, so the horizon order is the stable id order.
    assert ids == sorted(ids)
    assert "ability-zz-extra-57" in {row["id"] for row in tail["abilities"]}


def test_horizon_first_page_keeps_legacy_shape(ability_root: Path):
    brief = ability_context(load_repo(ability_root))
    assert brief["total"] == 3 and brief["returned"] == 3
    assert brief["offset"] == 0 and brief["next_offset"] is None
    assert brief["has_more"] is False and brief["truncated"] is False
    assert brief["expand"] == "ability-context ABILITY_ID"
    assert {(row["from"], row["to"]) for row in brief["bridges"]} == {
        ("ability-sad-ols", "ability-aml-ols"),
        ("ability-aml-ols", "ability-aml-extension")}
    for row in brief["abilities"]:
        assert row["off_page_bridge_count"] == 0
        assert row["off_page_candidate_count"] == 0
    cli = json.loads(run_los(ability_root, "ability-context").stdout)
    assert cli["contract"] == "ability-context-v1"
    assert cli["expansions"] == {"next": None}


def test_horizon_edges_stay_page_local_with_off_page_pointers(ability_root: Path):
    _grow_registry(ability_root, 58)
    _distant_bridge(ability_root)
    first = run_los(ability_root, "ability-context", "--limit", "50")
    assert first.returncode == 0, first.stderr
    page = json.loads(first.stdout)
    assert {(row["from"], row["to"]) for row in page["bridges"]} == {
        ("ability-sad-ols", "ability-aml-ols"),
        ("ability-aml-ols", "ability-aml-extension")}
    listed = {row["id"] for row in page["abilities"]}
    assert "ability-zz-extra-57" not in listed
    by_id = {row["id"]: row for row in page["abilities"]}
    assert by_id["ability-aml-ols"]["off_page_bridge_count"] == 1
    assert by_id["ability-sad-ols"]["off_page_bridge_count"] == 0
    assert all(row["off_page_candidate_count"] == 0
               for row in page["abilities"])
    second = run_los(ability_root, "ability-context", "--limit", "50",
                     "--offset", "50",
                     "--expected-snapshot", page["snapshot_id"])
    assert second.returncode == 0, second.stderr
    tail = json.loads(second.stdout)
    assert tail["bridges"] == []
    tail_by_id = {row["id"]: row for row in tail["abilities"]}
    assert tail_by_id["ability-zz-extra-57"]["off_page_bridge_count"] == 1
    assert tail_by_id["ability-zz-extra-47"]["off_page_bridge_count"] == 0


def test_horizon_rejects_bad_windows(ability_root: Path):
    bad = (("ability-context", "--offset", "-1"),
           ("ability-context", "--limit", "0"),
           ("ability-context", "--limit", "51"),
           ("ability-context", "ability-sad-ols", "--offset", "1"),
           ("ability-context", "--offset", "1"))
    for args in bad:
        result = run_los(ability_root, *args)
        assert result.returncode != 0, args
        assert not result.stdout, args


def test_horizon_refuses_a_stale_snapshot(ability_root: Path):
    first = json.loads(run_los(ability_root, "ability-context",
                               "--limit", "1").stdout)
    note = next(iter(load_repo(ability_root).notes.values()))
    note.path.write_text(note.path.read_text(encoding="utf-8")
                         + "\nA changed explanation.\n", encoding="utf-8")
    stale = run_los(ability_root, "ability-context", "--limit", "1",
                    "--offset", "1",
                    "--expected-snapshot", first["snapshot_id"])
    assert stale.returncode == 3, stale.stderr
    assert not stale.stdout


def test_horizon_empty_page_past_total(ability_root: Path):
    first = json.loads(run_los(ability_root, "ability-context",
                               "--limit", "1").stdout)
    far = run_los(ability_root, "ability-context", "--limit", "1",
                  "--offset", "3",
                  "--expected-snapshot", first["snapshot_id"])
    assert far.returncode == 0, far.stderr
    page = json.loads(far.stdout)
    assert page["abilities"] == [] and page["total"] == 3
    assert page["returned"] == 0 and page["offset"] == 3
    assert page["next_offset"] is None and page["has_more"] is False
    assert page["truncated"] is True
    assert page["bridges"] == []
    assert page["expansions"] == {"next": None}


def _history(root: Path, aid: str, count: int, *, start: int = 0):
    """Append valid confirmed attempts with increasing ISO timestamps."""
    from datetime import datetime, timedelta

    repo = load_repo(root)
    base = datetime(2026, 9, 23, 10, 0, tzinfo=UTC)
    for offset in range(count):
        number = start + offset
        stamp = (base + timedelta(minutes=number)).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        _append(root, _work(repo, aid, number, timestamp=stamp))


def _stage_encounter(root: Path, aid: str):
    from repo_builders import add_curriculum, write_yaml

    add_curriculum(root)
    map_path = (root / "curriculum/modules/module-demo/units/unit-demo-l01"
                "/study-map.yaml")
    study_map = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    study_map["stages"][0]["ability_ids"] = [aid]
    write_yaml(map_path, study_map)


def test_focused_brief_summarizes_state_without_history(ability_root: Path):
    import shlex

    _history(ability_root, "ability-sad-ols", 30)
    proc = run_los(ability_root, "ability-context", "ability-sad-ols",
                   "--brief")
    assert proc.returncode == 0, proc.stderr
    brief = json.loads(proc.stdout)
    full = json.loads(run_los(ability_root, "ability-context",
                              "ability-sad-ols").stdout)
    assert brief["brief"] is True and "brief" not in full
    assert brief["ability"]["state"] == full["ability"]["state"] == "supported"
    assert brief["ability"]["reasons"] == full["ability"]["reasons"]
    assert brief["ability"]["transfer"] == full["ability"]["transfer"]
    assert (brief["ability"]["preparation_routes"]
            == full["ability"]["preparation_routes"])
    assert "evidence" not in brief["ability"]
    assert brief["ability_sha256"] == ability_fingerprint(
        load_repo(ability_root).abilities["ability-sad-ols"])
    summary = brief["evidence_summary"]
    assert (summary["total"], summary["active"], summary["comparable"],
            summary["valid"]) == (30, 30, 30, 30)
    assert summary["superseded"] == 0
    assert summary["corrections"] == [] and summary["corrections_total"] == 0
    assert [pointer["role"] for pointer in summary["state_basis"]] == [
        "latest-comparable"]
    assert summary["state_basis"][0]["id"] == "ability-observation-29"
    assert "I derived this from the stated problem." not in proc.stdout
    assert len(full["ability"]["evidence"]) == 30
    evidence = run_los(ability_root, *shlex.split(brief["expand"]["evidence"]))
    assert evidence.returncode == 0, evidence.stderr
    assert json.loads(evidence.stdout)["total"] == 30


def test_focused_brief_stays_bounded_as_history_grows(ability_root: Path):
    _history(ability_root, "ability-sad-ols", 5)
    small = run_los(ability_root, "ability-context", "ability-sad-ols",
                    "--brief")
    assert small.returncode == 0, small.stderr
    _history(ability_root, "ability-sad-ols", 25, start=5)
    big = run_los(ability_root, "ability-context", "ability-sad-ols",
                  "--brief")
    assert big.returncode == 0, big.stderr
    assert json.loads(big.stdout)["evidence_summary"]["total"] == 30
    assert len(big.stdout) - len(small.stdout) < 500


def test_section_evidence_pages_the_complete_ledger_once(ability_root: Path):
    import shlex

    _history(ability_root, "ability-sad-ols", 30)
    seen = []
    offset, snapshot = 0, None
    first_next = None
    while True:
        args = ["ability-context", "ability-sad-ols", "--section", "evidence",
                "--limit", "10", "--offset", str(offset)]
        if snapshot is not None:
            args += ["--expected-snapshot", snapshot]
        proc = run_los(ability_root, *args)
        assert proc.returncode == 0, proc.stderr
        page = json.loads(proc.stdout)
        assert page["section"] == "evidence"
        assert page["focus"] == "ability-sad-ols"
        assert page["total"] == 30
        if first_next is None:
            first_next = page["expansions"]["next"]
        seen.extend(page["observations"])
        if page["next_offset"] is None:
            assert page["has_more"] is False
            assert page["expansions"] == {"next": None}
            break
        offset, snapshot = page["next_offset"], page["snapshot_id"]
    assert [row["id"] for row in seen] == [
        f"ability-observation-{number}" for number in range(30)]
    assert all(row["claim"] and row["origin"]["path"] for row in seen)
    follow = run_los(ability_root, *shlex.split(first_next))
    assert follow.returncode == 0, follow.stderr
    assert [row["id"] for row in
            json.loads(follow.stdout)["observations"]] == [
        f"ability-observation-{number}" for number in range(10, 20)]


def test_brief_conflicts_and_corrections_match_the_full_read(ability_root: Path):
    repo = load_repo(ability_root)
    _append(ability_root, _work(repo, "ability-sad-ols", 1))
    _append(ability_root, _work(repo, "ability-sad-ols", 2,
                                result="incorrect", assistance="hint"))
    conflicted = json.loads(run_los(ability_root, "ability-context",
                                    "ability-sad-ols", "--brief").stdout)
    full = json.loads(run_los(ability_root, "ability-context",
                              "ability-sad-ols").stdout)
    assert conflicted["ability"]["state"] == "uncertain"
    assert conflicted["ability"]["state"] == full["ability"]["state"]
    assert conflicted["ability"]["reasons"] == ["conflicting later work"]
    assert conflicted["ability"]["reasons"] == full["ability"]["reasons"]
    assert [(pointer["role"], pointer["id"])
            for pointer in conflicted["evidence_summary"]["state_basis"]] == [
        ("latest-comparable", "ability-observation-1"),
        ("later-conflict", "ability-observation-2")]
    _append(ability_root, _work(repo, "ability-sad-ols", 3,
                                supersedes="ability-observation-2"))
    healed = json.loads(run_los(ability_root, "ability-context",
                                "ability-sad-ols", "--brief").stdout)
    full_healed = json.loads(run_los(ability_root, "ability-context",
                                     "ability-sad-ols").stdout)
    assert healed["ability"]["state"] == "supported"
    assert healed["ability"]["state"] == full_healed["ability"]["state"]
    assert healed["ability"]["reasons"] == full_healed["ability"]["reasons"]
    summary = healed["evidence_summary"]
    assert (summary["total"], summary["active"],
            summary["superseded"]) == (3, 2, 1)
    assert summary["corrections"] == [{
        "id": "ability-observation-3", "supersedes": "ability-observation-2",
        "origin": {"path": "work/active/workspace-demo/ability-observations.jsonl",
                   "line": 3, "workspace_id": "workspace-demo"}}]
    section = json.loads(run_los(
        ability_root, "ability-context", "ability-sad-ols", "--section",
        "evidence", "--limit", "50").stdout)
    assert section["total"] == 3
    assert len(section["observations"]) == 3


def test_brief_encounters_summarize_materials_with_expansions(ability_root: Path):
    import shlex

    _history(ability_root, "ability-sad-ols", 2)
    _stage_encounter(ability_root, "ability-sad-ols")
    brief = json.loads(run_los(ability_root, "ability-context",
                               "ability-sad-ols", "--brief").stdout)
    full = json.loads(run_los(ability_root, "ability-context",
                              "ability-sad-ols").stdout)
    assert brief["encounters_total"] == 1
    assert brief["encounters_truncated"] is False
    summary = brief["encounters"][0]
    assert summary["stage_id"] == "stage-demo"
    assert summary["unit_id"] == "unit-demo-l01"
    assert summary["materials_total"] == 3
    assert (summary["materials_exact"] + summary["materials_unmapped"]) == 3
    assert "materials" not in summary and "objective" not in summary
    assert summary["expand"] == (
        "plan-edit-context unit-demo-l01 --stage-id stage-demo "
        f"--expected-snapshot {brief['snapshot_id']}")
    assert len(full["encounters"][0]["materials"]) == 3
    expand = run_los(ability_root, *shlex.split(summary["expand"]))
    assert expand.returncode == 0, expand.stderr


def test_brief_and_full_agree_across_state_transitions(ability_root: Path):
    def _pair():
        brief = json.loads(run_los(ability_root, "ability-context",
                                   "ability-sad-ols", "--brief").stdout)
        full = json.loads(run_los(ability_root, "ability-context",
                                  "ability-sad-ols").stdout)
        return brief["ability"], full["ability"]

    repo = load_repo(ability_root)
    _append(ability_root, _work(repo, "ability-sad-ols", 1, assistance="hint"))
    brief, full = _pair()
    assert brief["state"] == full["state"] == "uncertain"
    assert brief["reasons"] == full["reasons"]
    path = ability_root / "knowledge/abilities.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["abilities"][0]["evidence_spec"] = ["a newly reviewed derivation"]
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    brief, full = _pair()
    assert brief["state"] == full["state"] == "uncertain"
    assert brief["reasons"] == full["reasons"]
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["abilities"][0]["lifecycle"] = "retired"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    brief, full = _pair()
    assert brief["state"] == full["state"] == "unmapped"
    assert brief["lifecycle"] == full["lifecycle"] == "retired"
    assert brief["reasons"] == full["reasons"]


def test_brief_and_section_refuse_invalid_combinations(ability_root: Path):
    bad = (("ability-context", "--brief"),
           ("ability-context", "--section", "evidence"),
           ("ability-context", "ability-sad-ols", "--brief",
            "--section", "evidence"),
           ("ability-context", "ability-sad-ols", "--brief", "--limit", "5"),
           ("ability-context", "ability-sad-ols", "--brief", "--offset", "1"),
           ("ability-context", "ability-sad-ols", "--section", "evidence",
            "--offset", "1"),
           ("ability-context", "ability-sad-ols", "--section", "evidence",
            "--limit", "0"),
           ("ability-context", "ability-sad-ols", "--section", "evidence",
            "--limit", "51"),
           ("ability-context", "ability-sad-ols", "--section", "history"))
    for args in bad:
        result = run_los(ability_root, *args)
        assert result.returncode != 0, args
        assert not result.stdout, args


def test_section_evidence_refuses_a_stale_snapshot(ability_root: Path):
    _history(ability_root, "ability-sad-ols", 2)
    first = json.loads(run_los(ability_root, "ability-context",
                               "ability-sad-ols", "--section", "evidence",
                               "--limit", "1").stdout)
    note = next(iter(load_repo(ability_root).notes.values()))
    note.path.write_text(note.path.read_text(encoding="utf-8")
                         + "\nA changed explanation.\n", encoding="utf-8")
    stale = run_los(ability_root, "ability-context", "ability-sad-ols",
                    "--section", "evidence", "--limit", "1",
                    "--offset", "1",
                    "--expected-snapshot", first["snapshot_id"])
    assert stale.returncode == 3, stale.stderr
    assert not stale.stdout


def _chain_history(root: Path, aid: str, count: int, *, start: int = 0):
    """Each correct observation supersedes the preceding one."""
    from datetime import datetime, timedelta

    repo = load_repo(root)
    base = datetime(2026, 9, 23, 10, 0, tzinfo=UTC)
    for offset in range(count):
        number = start + offset
        stamp = (base + timedelta(minutes=number)).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        row = _work(repo, aid, number, timestamp=stamp)
        if number:
            row["supersedes"] = f"ability-observation-{number - 1}"
        _append(root, row)


def _conflict_history(root: Path, aid: str, count: int, *, start: int = 0):
    """One independent correct observation, then assisted incorrect ones."""
    from datetime import datetime, timedelta

    repo = load_repo(root)
    base = datetime(2026, 9, 23, 10, 0, tzinfo=UTC)
    for offset in range(count):
        number = start + offset
        stamp = (base + timedelta(minutes=number)).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        if number == 0:
            _append(root, _work(repo, aid, number, timestamp=stamp))
        else:
            _append(root, _work(repo, aid, number, timestamp=stamp,
                                result="incorrect", assistance="hint"))


def test_brief_correction_chain_stays_bounded(ability_root: Path):
    _chain_history(ability_root, "ability-sad-ols", 5)
    small = run_los(ability_root, "ability-context", "ability-sad-ols",
                    "--brief")
    assert small.returncode == 0, small.stderr
    _chain_history(ability_root, "ability-sad-ols", 195, start=5)
    mid = run_los(ability_root, "ability-context", "ability-sad-ols",
                  "--brief")
    assert mid.returncode == 0, mid.stderr
    _chain_history(ability_root, "ability-sad-ols", 800, start=200)
    big = run_los(ability_root, "ability-context", "ability-sad-ols",
                  "--brief")
    assert big.returncode == 0, big.stderr
    brief = json.loads(big.stdout)
    summary = brief["evidence_summary"]
    assert summary["total"] == 1000
    assert summary["corrections_total"] == 999
    assert summary["corrections_returned"] == 20
    assert summary["corrections_truncated"] is True
    assert [row["id"] for row in summary["corrections"]] == [
        f"ability-observation-{number}" for number in range(1, 21)]
    assert summary["corrections"][0]["supersedes"] == "ability-observation-0"
    full = json.loads(run_los(ability_root, "ability-context",
                              "ability-sad-ols").stdout)
    assert brief["ability"]["state"] == full["ability"]["state"] == "supported"
    assert brief["ability"]["reasons"] == full["ability"]["reasons"]
    assert (brief["ability"]["preparation_routes"]
            == full["ability"]["preparation_routes"])
    assert len(big.stdout) - len(mid.stdout) < 500
    assert len(big.stdout) < 12000
    section = json.loads(run_los(
        ability_root, "ability-context", "ability-sad-ols", "--section",
        "evidence", "--limit", "50").stdout)
    assert section["total"] == 1000
    assert [row["id"] for row in section["observations"]] == [
        f"ability-observation-{number}" for number in range(50)]


def test_brief_later_conflicts_stays_bounded(ability_root: Path):
    _conflict_history(ability_root, "ability-sad-ols", 5)
    small = run_los(ability_root, "ability-context", "ability-sad-ols",
                    "--brief")
    assert small.returncode == 0, small.stderr
    _conflict_history(ability_root, "ability-sad-ols", 195, start=5)
    mid = run_los(ability_root, "ability-context", "ability-sad-ols",
                  "--brief")
    assert mid.returncode == 0, mid.stderr
    _conflict_history(ability_root, "ability-sad-ols", 800, start=200)
    big = run_los(ability_root, "ability-context", "ability-sad-ols",
                  "--brief")
    assert big.returncode == 0, big.stderr
    brief = json.loads(big.stdout)
    summary = brief["evidence_summary"]
    assert summary["total"] == 1000
    assert summary["later_conflicts_total"] == 999
    assert summary["later_conflicts_returned"] == 20
    assert summary["later_conflicts_truncated"] is True
    assert [pointer["role"] for pointer in summary["state_basis"]] == (
        ["latest-comparable"] + ["later-conflict"] * 20)
    assert summary["state_basis"][0]["id"] == "ability-observation-0"
    assert summary["state_basis"][1]["id"] == "ability-observation-1"
    full = json.loads(run_los(ability_root, "ability-context",
                              "ability-sad-ols").stdout)
    assert brief["ability"]["state"] == full["ability"]["state"] == "uncertain"
    assert brief["ability"]["reasons"] == ["conflicting later work"]
    assert brief["ability"]["reasons"] == full["ability"]["reasons"]
    assert len(big.stdout) - len(mid.stdout) < 500
    assert len(big.stdout) < 12000
