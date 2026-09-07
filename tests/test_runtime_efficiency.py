"""Optimizations must preserve parsing, publication, and transaction guards."""

from __future__ import annotations

import importlib.util
from copy import deepcopy

import pytest
import yaml

from learning_os.genout.outputs import write_outputs
from learning_os.loader import load_repo
from learning_os.loading import yamlio
from learning_os.transactions import TransactionConflict, TransactionService


@pytest.fixture(params=["installed", "python-fallback"])
def safe_loader(request, monkeypatch):
    if request.param == "installed":
        return yamlio.UniqueKeySafeLoader
    # Exercise the actual fallback selection in isolation; do not change the
    # loader used by the rest of the suite.
    monkeypatch.delattr(yaml, "CSafeLoader", raising=False)
    spec = importlib.util.spec_from_file_location(
        "learning_os.loading._fallback_yamlio", yamlio.__file__,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert issubclass(module.UniqueKeySafeLoader, yaml.SafeLoader)
    return module.UniqueKeySafeLoader


@pytest.mark.parametrize("text", [
    "nested: {id: first, id: second}",
    "id: first\nid: second\n",
    "? [unhashable, key]\n: value\n",
    "value: !!python/object/apply:os.system ['false']",
    "value: [unfinished",
])
def test_safe_loader_refuses_ambiguous_or_unsafe_yaml(safe_loader, text):
    with pytest.raises(yaml.YAMLError):
        yaml.load(text, Loader=safe_loader)


def test_safe_loader_preserves_merges_scalars_and_unicode(safe_loader):
    text = (
        "defaults: &defaults {title: Grüß dich, active: true}\n"
        "record:\n  <<: *defaults\n  title: Überprüfung\n"
        "  reviewed: 2026-09-07\n  quoted: '2026-09-07'\n"
        "  values: [null, 0, 1.25, yes, 'yes']\n"
        "  body: |\n    First line\n    Second line\n"
    )
    assert yaml.load(text, Loader=safe_loader) == yaml.safe_load(text)


def test_unchanged_outputs_keep_identity_and_repair_only_changed_bytes(mini_repo, monkeypatch):
    import learning_os.genout.outputs as publisher

    repo = load_repo(mini_repo)
    outputs = {"manifest.json": "{}\n", "concept-index.md": "GENERATED\n"}
    write_outputs(repo, outputs)
    gen = mini_repo / "generated"
    manifest = gen / "manifest.json"
    original = manifest.stat()
    replaced = []
    replace = publisher.os.replace

    def tracked_replace(source, target):
        replaced.append(target.name)
        replace(source, target)

    monkeypatch.setattr(publisher.os, "replace", tracked_replace)
    write_outputs(repo, outputs)
    assert replaced == []
    assert (manifest.stat().st_ino, manifest.stat().st_mtime_ns) == (
        original.st_ino, original.st_mtime_ns,
    )
    # Text-mode reads would mistakenly regard CRLF corruption as identical.
    (gen / "concept-index.md").write_bytes(b"GENERATED\r\n")
    (gen / "stale.md").write_text("stale")
    write_outputs(repo, outputs)
    assert replaced == ["concept-index.md"]
    assert not (gen / "stale.md").exists()
    assert (gen / "concept-index.md").read_bytes() == b"GENERATED\n"
    replaced.clear()
    write_outputs(repo, {"manifest.json": "{\"new\": true}\n", "concept-index.md": "new\n"})
    assert replaced == ["concept-index.md", "manifest.json"]


def test_identical_canonical_write_preserves_inode_but_checks_revisions(tmp_path):
    target = tmp_path / "projects/registry/project-demo.yaml"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"unchanged\n")
    before = target.stat()
    service = TransactionService(tmp_path)
    validated = []
    result = service.commit(
        capability="project.update", writes={target: b"unchanged\n"},
        artifact_ids=["project-demo"], expected_revisions={"project-demo": 0},
        validate_state=lambda: validated.append(True) or [],
    )
    assert validated == [True]
    assert (target.stat().st_ino, target.stat().st_mtime_ns) == (
        before.st_ino, before.st_mtime_ns,
    )
    assert result.receipt_path.is_file()
    assert result.revisions == {"project-demo": 1}
    with pytest.raises(TransactionConflict):
        service.commit(
            capability="project.update", writes={target: b"unchanged\n"},
            artifact_ids=["project-demo"], expected_revisions={"project-demo": 0},
        )


def test_routes_resolve_once_per_build_and_refresh_material_existence(mini_repo, monkeypatch):
    from test_manifest_v7_routes import _rich_fixture

    from learning_os.genout.manifest import build_manifest
    from learning_os.genout.projection import records_curriculum

    route_id, route = _rich_fixture(mini_repo)
    repo = load_repo(mini_repo)
    study_map = next(iter(repo.study_maps.values()))
    study_map.data["stages"][0]["resources"] = [{
        "kind": "read", "label": route["title"],
        "source_id": "source-demo-book",
        "locator": "lecture-01.pdf — the current derivation",
        "scope_triage": "required-now",
    }]
    target = repo.materials_root / "source-demo-book/lecture-01.pdf"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("synthetic lecture\n")
    original = deepcopy(repo.module_source_maps)
    resolve = records_curriculum._project_material_resource
    resolved = []

    def tracked_resolve(repo, resource):
        resolved.append(resource["id"])
        return resolve(repo, resource)

    monkeypatch.setattr(records_curriculum, "_project_material_resource", tracked_resolve)
    for exists in (True, False):
        if not exists:
            target.unlink()
        resolved.clear()
        manifest = build_manifest(repo, "T1")
        assert resolved == [route_id]
        projected_route = manifest["module_source_maps"][0]["sources"][0]["unit_routes"][0]
        resource = manifest["study_maps"][0]["stages"][0]["resources"][0]
        assert projected_route["material_uri"] == "material://source-demo-book/lecture-01.pdf"
        assert projected_route["material_exists"] is exists
        if exists:
            assert resource["material_uri"] == projected_route["material_uri"]
            assert resource["material_exists"] is True
        else:
            # A vanished route must no longer provide an openable fallback.
            assert resource.get("material_exists") is not True
            assert "route_id" not in resource
        assert repo.module_source_maps == original
