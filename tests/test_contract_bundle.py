"""Prototype contract bundler: closure, digest, and registry parity.

Exercises the checked-in v11 schemas (``full_repo``): the bundler must resolve
exactly the verified 9-document closure, digest canonical content (never mere
serialization), and admit exactly the identities the live Core validator
admits through ``schema_registry()``.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from learning_os.contracts.bundle import (
    BundleError,
    build_bundle,
    build_identity_index,
    build_meta,
    digest_of,
    resolve_closure,
)
from learning_os.contracts.json_schema import schema_registry

pytestmark = pytest.mark.full_repo

V11_REL = "system/contracts/manifest-v11.schema.json"
SCHEMA_DIR_REL = "system/schema"

# Verified 2026-09-20: the 7 documents the v11 root references directly, plus
# learning-plan (reached by declared $id .../learning-plan-v1) and
# material-comparison-defs (reached from unit-material-synthesis). Neither
# depth-2 document references anything further out.
EXPECTED_V11_RESOURCES = sorted([
    "learning-path.schema.json",
    "learning-plan.schema.json",
    "material-comparison-defs.schema.json",
    "module.schema.json",
    "note.schema.json",
    "project.schema.json",
    "study-map.schema.json",
    "unit-material-synthesis.schema.json",
    "unit.schema.json",
])


def _copy_tree_with_indent(src: Path, dst: Path, indent: int | None) -> None:
    """Copy ``*.schema.json`` re-serialized, so bytes differ but values match."""

    dst.mkdir(parents=True, exist_ok=True)
    for candidate in sorted(src.glob("*.schema.json")):
        value = json.loads(candidate.read_text(encoding="utf-8"))
        dst.joinpath(candidate.name).write_text(
            json.dumps(value, indent=indent, ensure_ascii=False), encoding="utf-8")


def _mutate_first_description(schema_dir: Path) -> Path:
    """Deterministically change one JSON value in a copied resource."""

    target = schema_dir / "module.schema.json"
    schema = json.loads(target.read_text(encoding="utf-8"))
    stack = [schema]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "description" and isinstance(value, str):
                    node[key] = value + " [prototype sensitivity probe]"
                    target.write_text(json.dumps(schema, indent=2), encoding="utf-8")
                    return target
                stack.append(value)
        elif isinstance(node, list):
            stack.extend(node)
    raise AssertionError("module.schema.json copy carries no description to mutate")


def test_build_is_deterministic(repo_root: Path, tmp_path: Path) -> None:
    first = build_bundle(repo_root / V11_REL, repo_root / SCHEMA_DIR_REL)
    out_a = tmp_path / "a"
    out_b = tmp_path / "b"
    out_a.mkdir()
    out_b.mkdir()
    out_a.joinpath("bundle.json").write_bytes(first)
    out_b.joinpath("bundle.json").write_bytes(
        build_bundle(repo_root / V11_REL, repo_root / SCHEMA_DIR_REL))
    assert out_a.joinpath("bundle.json").read_bytes() == out_b.joinpath("bundle.json").read_bytes()


def test_inventory_is_exactly_the_verified_nine(repo_root: Path) -> None:
    closure = resolve_closure(repo_root / V11_REL, repo_root / SCHEMA_DIR_REL)
    assert [resource["path"] for resource in closure["resources"]] == EXPECTED_V11_RESOURCES


def test_bundle_envelope_carries_generated_warning(repo_root: Path) -> None:
    envelope = json.loads(build_bundle(repo_root / V11_REL, repo_root / SCHEMA_DIR_REL))
    assert envelope["_generated"].startswith("GENERATED file")


def test_serialization_does_not_change_digest(repo_root: Path, tmp_path: Path) -> None:
    schema_copy = tmp_path / "schema"
    _copy_tree_with_indent(repo_root / SCHEMA_DIR_REL, schema_copy, indent=2)
    root_copy = tmp_path / "manifest-v11.schema.json"
    root_value = json.loads((repo_root / V11_REL).read_text(encoding="utf-8"))
    root_copy.write_text(json.dumps(root_value, indent=4), encoding="utf-8")
    assert root_copy.read_bytes() != (repo_root / V11_REL).read_bytes()
    assert digest_of(build_bundle(root_copy, schema_copy)) == digest_of(
        build_bundle(repo_root / V11_REL, repo_root / SCHEMA_DIR_REL))


def test_json_value_change_changes_digest(repo_root: Path, tmp_path: Path) -> None:
    schema_copy = tmp_path / "schema"
    shutil.copytree(repo_root / SCHEMA_DIR_REL, schema_copy)
    before = digest_of(build_bundle(repo_root / V11_REL, repo_root / SCHEMA_DIR_REL))
    mutated = _mutate_first_description(schema_copy)
    assert mutated.is_file()
    after = digest_of(build_bundle(repo_root / V11_REL, schema_copy))
    assert after != before


def test_missing_alias_fails_closed_naming_the_uri(repo_root: Path, tmp_path: Path) -> None:
    schema_copy = tmp_path / "schema"
    shutil.copytree(repo_root / SCHEMA_DIR_REL, schema_copy)
    target = schema_copy / "learning-plan.schema.json"
    schema = json.loads(target.read_text(encoding="utf-8"))
    del schema["$id"]
    target.write_text(json.dumps(schema), encoding="utf-8")
    with pytest.raises(BundleError, match="learning-plan-v1"):
        resolve_closure(repo_root / V11_REL, schema_copy)


def test_registry_parity(repo_root: Path) -> None:
    """The bundler admits exactly the identities the live validator admits."""

    schema_dir = repo_root / SCHEMA_DIR_REL
    index = build_identity_index(schema_dir)
    expected: dict[str, Path] = {}
    for candidate in sorted(schema_dir.glob("*.schema.json")):
        schema = json.loads(candidate.read_text(encoding="utf-8"))
        schema_id = schema.get("$id")
        if isinstance(schema_id, str) and schema_id:
            expected[schema_id] = candidate
        expected[f"https://learningos.local/schema/{candidate.name}"] = candidate
    assert index == expected

    registry = schema_registry(schema_dir)
    for uri, path in sorted(index.items()):
        retrieved = registry.get_or_retrieve(uri)
        assert retrieved.value.contents == json.loads(path.read_text(encoding="utf-8"))

    learnt = registry.get_or_retrieve("https://learningos.local/schema/learning-plan-v1")
    assert learnt.value.contents.get("$id") == "https://learningos.local/schema/learning-plan-v1"


def test_build_meta_carries_contract_keys_and_closure() -> None:
    meta = build_meta(
        contract={"contract_version": 11, "schema_sha256": "sha256:root",
                  "top_level_keys": ["a"], "generated_keys": ["b"],
                  "index_keys": [], "forbidden_top_level_keys": ["c"]},
        schema_label="system/contracts/manifest-v11.schema.json",
        closure_digest="sha256:closure",
        resources=[{"path": "x.schema.json", "declared_id": None,
                    "aliases": ["https://learningos.local/schema/x.schema.json"],
                    "schema": {"type": "object"}}],
    )
    assert meta["contract_version"] == 11
    assert meta["_generated"].startswith("GENERATED file")
    assert meta["closure_sha256"] == "sha256:closure"
    assert meta["contract_keys"]["top_level_keys"] == ["a"]
    assert meta["contract_keys"]["forbidden_top_level_keys"] == ["c"]
    assert meta["resources"][0]["sha256"].startswith("sha256:")
    assert meta["generator"]["name"] == "learningos-contract-bundle"


def test_root_hash_is_blind_to_resource_change(repo_root: Path, tmp_path: Path) -> None:
    """The current identity cannot see what the closure digest must catch."""

    root_path = repo_root / V11_REL
    root_hash_before = f"sha256:{hashlib.sha256(root_path.read_bytes()).hexdigest()}"
    schema_copy = tmp_path / "schema"
    shutil.copytree(repo_root / SCHEMA_DIR_REL, schema_copy)
    _mutate_first_description(schema_copy)
    assert f"sha256:{hashlib.sha256(root_path.read_bytes()).hexdigest()}" == root_hash_before
    assert digest_of(build_bundle(repo_root / V11_REL, schema_copy)) != digest_of(
        build_bundle(repo_root / V11_REL, repo_root / SCHEMA_DIR_REL))
