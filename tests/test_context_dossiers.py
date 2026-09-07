"""Context dossiers: same inputs hit the cache, one move invalidates,
poison is refused, and canonical inputs are never written.

The plan's Phase 5 validation in executable form: cache-hit on unchanged
inputs, single-dependency invalidation on a route change, no canonical
mutation — plus the poisoning refusal the risks section demands.
"""

from __future__ import annotations

import json

import pytest

from learning_os.semantics import (
    DossierError,
    build_dossier,
    cache_path,
    compute_hashes,
    is_fresh,
    load_dossier,
    store_dossier,
)

VERSIONS = {"semantic-contract": "2", "operator-contract": "operator-v1"}

MENU = {"routes": ["route-a", "route-b"]}
NODES = {"nodes": ["knowledge-a"]}
ROUTES = [
    {"id": "route-a", "locator": "ch 1"},
    {"id": "route-b", "locator": "ch 2"},
]


def _dossier(**overrides):
    inputs = {
        "unit_id": "unit-aml-l01",
        "knowledge_map": NODES,
        "source_map": MENU,
        "routes": ROUTES,
        "evidence": ["material://demo/deck.pdf"],
        "contract_versions": VERSIONS,
    }
    inputs.update(overrides)
    return build_dossier(**inputs)


def test_same_inputs_build_the_same_key():
    first, second = _dossier(), _dossier()
    assert first == second
    assert first.key.startswith("context://unit-aml-l01/semantic-dossier@")
    assert len(first.key.rsplit("@", 1)[1]) == 16
    assert {name for name, _ in first.hashes} == {
        "knowledge-map", "source-map", "routes", "evidence",
        "semantic-contract", "operator-contract",
    }


def test_a_cache_hit_returns_the_identical_dossier(tmp_path):
    dossier = _dossier()
    path = store_dossier(tmp_path, dossier)
    assert path.parent == tmp_path / "generated" / "dossiers"
    assert load_dossier(path) == dossier


def test_one_route_change_invalidates_exactly_its_hash():
    before = _dossier()
    moved = [dict(ROUTES[0], locator="ch 9"), ROUTES[1]]
    after = _dossier(routes=moved)
    assert after.key != before.key
    changed = {
        name for name, digest in after.hashes
        if dict(before.hashes)[name] != digest
    }
    assert changed == {"routes"}
    assert is_fresh(before, dict(before.hashes)) is True
    assert is_fresh(before, dict(after.hashes)) is False


def test_a_meaning_change_invalidates_like_a_content_change():
    before = _dossier()
    after = _dossier(contract_versions={
        **VERSIONS, "semantic-contract": "3"})
    assert after.key != before.key
    assert is_fresh(before, dict(after.hashes)) is False


def test_poisoned_cache_files_are_refused_not_served(tmp_path):
    path = store_dossier(tmp_path, _dossier())
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["content"]["routes"][0]["locator"] = "ch 9"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(DossierError, match="poison"):
        load_dossier(path)


def test_garbage_cache_files_are_refused(tmp_path):
    path = tmp_path / "x.json"
    path.write_text("not json", encoding="utf-8")
    with pytest.raises(DossierError):
        load_dossier(path)
    path.write_text(json.dumps({"key": "k"}), encoding="utf-8")
    with pytest.raises(DossierError):
        load_dossier(path)


def test_building_and_storing_touch_no_canonical_inputs(tmp_path):
    """A sentinel canonical file survives build plus store byte-identical."""
    canonical = tmp_path / "curriculum" / "unit.yaml"
    canonical.parent.mkdir(parents=True)
    canonical.write_bytes(b"id: unit-x\n")
    before = canonical.read_bytes()
    dossier = build_dossier(
        unit_id="unit-x",
        knowledge_map={"nodes": []},
        source_map={"routes": []},
        routes=[],
        evidence=[],
        contract_versions=VERSIONS,
    )
    store_dossier(tmp_path, dossier)
    assert canonical.read_bytes() == before
    assert list((tmp_path / "generated" / "dossiers").iterdir()) != []


def test_malformed_inputs_refuse():
    with pytest.raises(DossierError):
        build_dossier(
            unit_id=" ", knowledge_map={}, source_map={}, routes=[],
            contract_versions=VERSIONS)
    with pytest.raises(DossierError):
        build_dossier(
            unit_id="u", knowledge_map={}, source_map={}, routes="nope",
            contract_versions=VERSIONS)
    with pytest.raises(DossierError):
        build_dossier(
            unit_id="u", knowledge_map={}, source_map={}, routes=[],
            contract_versions={"semantic-contract": "2"})
    with pytest.raises(DossierError):
        compute_hashes(
            knowledge_map={}, source_map={}, routes=[], evidence=[],
            contract_versions={})


def test_cache_filenames_carry_the_digest_not_just_the_unit(tmp_path):
    first = store_dossier(tmp_path, _dossier())
    second = store_dossier(tmp_path, _dossier(
        routes=[dict(ROUTES[0], locator="ch 9"), ROUTES[1]]))
    assert first.name != second.name
    assert first.name.startswith("unit-aml-l01-")
    assert cache_path(tmp_path, load_dossier(first)) == first
