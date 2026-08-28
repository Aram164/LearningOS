"""The published manifest shape is a versioned interface the producer owns.

Core publishes one manifest that every interface reads. Before 2026-08-08 only
the *consumer* declared which version it expected (the Obsidian UI's
``contracts/manifest-v2.lock.json``), so Core could reshape the projection, pass
its own CI, and push — and the incompatibility surfaced in the other repository.
It did: Core began publishing a top-level ``topics`` collection (ADR-009) while
still announcing ``contract_version: 2``, and UI CI went red.

These tests are the gate that makes that impossible to repeat. They fail in
Core's own run, which is the only place the mistake is still cheap.
"""

from __future__ import annotations

import hashlib
import json

import pytest
import yaml

from learning_os.contracts.manifest_contract import (
    ManifestContractError,
    bump,
    check,
    contract_path,
    declared_version,
    enforce,
    shape_of,
)
from learning_os.genout import generate_all
from learning_os.genout.manifest import build_manifest
from learning_os.loader import load_repo


def _manifest(root, enforce_contract: bool = True) -> dict:
    return build_manifest(load_repo(root), "T1", enforce_contract=enforce_contract)


def test_built_manifest_matches_the_declared_contract(mini_repo):
    ok, message = check(_manifest(mini_repo), mini_repo)
    assert ok, message


def test_generated_manifest_announces_the_declared_version(mini_repo):
    manifest = json.loads(generate_all(load_repo(mini_repo), "T1")["manifest.json"])
    assert manifest["_generated"]["contract_version"] == declared_version(mini_repo)


def test_topics_is_part_of_the_contract(mini_repo):
    """ADR-009's collection is published *and* declared — the v3 bump itself."""
    contract = yaml.safe_load(contract_path(mini_repo).read_text(encoding="utf-8"))
    assert "topics" in contract["top_level_keys"]
    assert "topics" in _manifest(mini_repo)


def test_adding_a_top_level_key_without_bumping_fails(mini_repo):
    """The exact 2026-08-08 defect, reproduced: new key, unchanged version."""
    manifest = _manifest(mini_repo)
    manifest["experimental_widgets"] = []
    ok, message = check(manifest, mini_repo)
    assert not ok
    assert "experimental_widgets" in message
    assert "manifest_contract.py --bump" in message


def test_removing_a_published_key_fails(mini_repo):
    manifest = _manifest(mini_repo)
    del manifest["topics"]
    ok, message = check(manifest, mini_repo)
    assert not ok
    assert "topics" in message


def test_new_index_table_fails(mini_repo):
    """Indexes are interface too — a consumer enumerates them exactly."""
    manifest = _manifest(mini_repo)
    manifest["indexes"]["unit_to_workspaces"] = {}
    ok, message = check(manifest, mini_repo)
    assert not ok
    assert "index_keys" in message


def test_announced_version_must_match_declared_version(mini_repo):
    manifest = _manifest(mini_repo)
    manifest["_generated"]["contract_version"] = 99
    ok, message = check(manifest, mini_repo)
    assert not ok
    assert "declares" in message


def test_schema_path_must_stay_inside_the_repository(mini_repo):
    """A contract cannot redirect producer validation to arbitrary bytes."""
    manifest = _manifest(mini_repo)
    contract = yaml.safe_load(contract_path(mini_repo).read_text(encoding="utf-8"))
    contract["schema_path"] = "../manifest-v8.schema.json"
    contract_path(mini_repo).write_text(
        yaml.safe_dump(contract, sort_keys=False), encoding="utf-8")

    ok, message = check(manifest, mini_repo)

    assert not ok
    assert "schema_path must be repository-relative" in message


def test_v8_schema_rejects_an_edge_without_evidence(mini_repo):
    manifest = _manifest(mini_repo)
    manifest["module_concept_edges"] = [{
        "module_id": "module-demo",
        "concept_id": "concept-expected-value",
        "evidence": [],
    }]

    ok, message = check(manifest, mini_repo)

    assert not ok
    assert "module_concept_edges" in message
    assert "non-empty" in message


def test_v8_schema_rejects_an_undeclared_edge_field(mini_repo):
    manifest = _manifest(mini_repo)
    manifest["module_concept_edges"] = [{
        "module_id": "module-demo",
        "concept_id": "concept-expected-value",
        "evidence": [{
            "kind": "stage-concept",
            "unit_id": "unit-demo-probability",
            "study_map_id": "study-map-demo-probability",
            "stage_id": "stage-demo-start",
        }],
        "confidence": 1,
    }]

    ok, message = check(manifest, mini_repo)

    assert not ok
    assert "module_concept_edges" in message
    assert "confidence" in message


def test_retired_key_cannot_return(mini_repo):
    """`exam_spine` was a second shape for `academic_deadlines` (ADR-006)."""
    manifest = _manifest(mini_repo)
    manifest["exam_spine"] = []
    ok, message = check(manifest, mini_repo)
    assert not ok
    assert "exam_spine" in message


def test_build_manifest_refuses_to_publish_a_drifted_shape(mini_repo):
    """Enforcement is in the builder, so every path that publishes is covered."""
    contract = yaml.safe_load(contract_path(mini_repo).read_text(encoding="utf-8"))
    contract["top_level_keys"] = [k for k in contract["top_level_keys"] if k != "topics"]
    contract_path(mini_repo).write_text(yaml.safe_dump(contract), encoding="utf-8")
    with pytest.raises(ManifestContractError) as excinfo:
        _manifest(mini_repo)
    assert "topics" in str(excinfo.value)


def test_bump_escape_hatch_lets_the_shape_be_inspected(mini_repo):
    """`--bump` must be able to build the very shape enforcement would reject."""
    contract = yaml.safe_load(contract_path(mini_repo).read_text(encoding="utf-8"))
    contract["top_level_keys"] = [k for k in contract["top_level_keys"] if k != "topics"]
    contract_path(mini_repo).write_text(yaml.safe_dump(contract), encoding="utf-8")
    shape = shape_of(_manifest(mini_repo, enforce_contract=False))
    assert "topics" in shape["top_level_keys"]


def test_bump_selects_and_hashes_the_new_versions_schema(mini_repo):
    """Regression: a bump must never retain the previous schema pointer."""
    path = contract_path(mini_repo)
    contract = yaml.safe_load(path.read_text(encoding="utf-8"))
    v7_schema = mini_repo / "system/contracts/manifest-v7.schema.json"
    contract.update({
        "contract_version": 7,
        "schema_path": "system/contracts/manifest-v7.schema.json",
        "schema_sha256": f"sha256:{hashlib.sha256(v7_schema.read_bytes()).hexdigest()}",
    })
    path.write_text(yaml.safe_dump(contract, sort_keys=False), encoding="utf-8")
    manifest = _manifest(mini_repo, enforce_contract=False)

    updated = bump(manifest, mini_repo, "test v8 bump")
    v8_schema = mini_repo / "system/contracts/manifest-v8.schema.json"

    assert updated["contract_version"] == 8
    assert updated["schema_path"] == "system/contracts/manifest-v8.schema.json"
    assert updated["schema_sha256"] == (
        f"sha256:{hashlib.sha256(v8_schema.read_bytes()).hexdigest()}"
    )


def test_bump_refuses_to_activate_a_version_without_its_schema(mini_repo):
    manifest = _manifest(mini_repo, enforce_contract=False)

    with pytest.raises(ManifestContractError) as excinfo:
        bump(manifest, mini_repo, "missing v9 schema")

    assert "manifest-v9.schema.json does not exist" in str(excinfo.value)


def test_missing_contract_is_a_clear_failure_not_a_silent_pass(mini_repo):
    contract_path(mini_repo).unlink()
    with pytest.raises(ManifestContractError) as excinfo:
        enforce({}, mini_repo)
    assert "no declared version" in str(excinfo.value)
