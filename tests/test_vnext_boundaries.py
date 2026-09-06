"""Synthetic-only tests for the vNext comparison and planning boundaries."""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from test_curriculum_v2 import add_curriculum, write_yaml

from learning_os.ai_actions import AIActionService
from learning_os.backup_manifest import (
    BackupManifestError,
    build_backup_manifest,
    verify_backup_manifest,
    verify_restored_system,
)
from learning_os.contracts.gateway import intent_sha256
from learning_os.fingerprint import canonical_fingerprint
from learning_os.legacy_archive import LegacyArchiveError, inspect_legacy_archive
from learning_os.masters_planning import (
    MastersPlanningError,
    candidate_set_checksum,
    masters_planning_dashboard,
    validate_candidate_comparison,
    validate_master_catalog,
)
from learning_os.material_synthesis import (
    current_unit_material_basis,
    material_synthesis_freshness,
    validate_unit_material_synthesis,
)
from learning_os.transactions import artifact_revision


def _add_routed_unit(root: Path) -> None:
    add_curriculum(root)
    unit_path = root / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    unit = yaml.safe_load(unit_path.read_text(encoding="utf-8"))
    unit["knowledge_map"] = {
        "summary": "Expected value connects outcomes to probability weights.",
        "nodes": [
            {"id": "knowledge-demo-outcomes", "title": "Outcomes",
             "summary": "A variable maps outcomes to values."},
            {"id": "knowledge-demo-expectation", "title": "Expectation",
             "summary": "Expectation is a probability-weighted average.",
             "builds_on": ["knowledge-demo-outcomes"]},
        ],
    }
    write_yaml(unit_path, unit)

    source_map_path = root / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(source_map_path.read_text(encoding="utf-8"))
    source_map["sources"][0]["unit_routes"] = [{
        "id": "route-demo-l01-book",
        "unit_id": "unit-demo-l01",
        "title": "Demo Book — expectation",
        "format": "book",
        "angle": "Derives the weighted sum with one discrete example.",
        "covers": ["knowledge-demo-outcomes", "knowledge-demo-expectation"],
        "depth": "derivation",
        "scope": "current",
        "locator": "lecture-01.pdf",
    }]
    write_yaml(source_map_path, source_map)

    registry_path = root / "sources/sources.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["sources"][0]["material"] = "material://source-demo-book/book.pdf"
    write_yaml(registry_path, registry)
    material = root.parent / "materials/source-demo-book/lecture-01.pdf"
    material.parent.mkdir(parents=True, exist_ok=True)
    material.write_bytes(b"synthetic expected-value lecture")


def _synthesis(root: Path) -> dict:
    basis = current_unit_material_basis(root, "unit-demo-l01")
    checksum = basis["material_checksums"]["route-demo-l01-book"]
    return {
        "schema_version": 1,
        "id": "material-synthesis-demo-l01",
        "type": "unit-material-synthesis",
        "unit_id": "unit-demo-l01",
        "status": "approved",
        "basis": {
            **basis,
            "ai_provenance": {
                "request_id": "ai-request-demo",
                "delivery_id": "ai-delivery-demo",
                "provider": "manual-bundle",
            },
        },
        "route_assessments": [{
            "route_id": "route-demo-l01-book",
            "source_id": "source-demo-book",
            "locator": "lecture-01.pdf",
            "review_status": "deep-reviewed",
            "concept_ids": ["concept-expected-value"],
            "contribution": "A direct derivation of the weighted sum.",
            "assumptions": "Finite discrete outcomes are assumed.",
            "notation": "Uses uppercase X and lowercase outcome values.",
            "exercise_value": "Includes a small worked calculation.",
            "best_for": "Checking the lecture's core derivation.",
            "limitations": "Does not cover continuous variables.",
            "evidence": [{"locator": "lecture-01.pdf p.1", "checksum": checksum}],
        }],
        "comparisons": [],
        "concept_groups": [
            {
                "concept_id": "concept-variance",
                "local_node_ids": ["knowledge-demo-outcomes"],
                "related_unit_ids": [],
                "bridge_note_ids": [],
                "narrative": "Outcome values are the inputs to later dispersion measures.",
            },
            {
                "concept_id": "concept-expected-value",
                "local_node_ids": ["knowledge-demo-expectation"],
                "related_unit_ids": ["unit-demo-l01"],
                "bridge_note_ids": ["note-demo"],
                "narrative": "The local derivation is the canonical expectation concept.",
            },
        ],
    }


def test_material_synthesis_covers_routes_and_derives_staleness(mini_repo):
    _add_routed_unit(mini_repo)
    value = _synthesis(mini_repo)
    assert validate_unit_material_synthesis(mini_repo, "unit-demo-l01", value) == value
    assert material_synthesis_freshness(mini_repo, "unit-demo-l01", value) == {
        "status": "current", "reasons": [],
    }

    source_map = mini_repo / "curriculum/modules/module-demo/source-map.yaml"
    changed = yaml.safe_load(source_map.read_text(encoding="utf-8"))
    changed["sources"][0]["unit_routes"][0]["angle"] = "A changed route judgment."
    write_yaml(source_map, changed)
    freshness = material_synthesis_freshness(mini_repo, "unit-demo-l01", value)
    assert freshness["status"] == "stale"
    assert "route_set_checksum" in freshness["reasons"]


def test_material_synthesis_hashes_every_file_in_a_multi_file_route(mini_repo):
    _add_routed_unit(mini_repo)
    source_map_path = mini_repo / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(source_map_path.read_text(encoding="utf-8"))
    source_map["sources"][0]["unit_routes"][0]["locator"] = (
        "lecture-01.pdf, reviewed section; lecture-02.pdf"
    )
    write_yaml(source_map_path, source_map)
    second = mini_repo.parent / "materials/source-demo-book/lecture-02.pdf"
    second.write_bytes(b"synthetic worked exercises")

    before = current_unit_material_basis(mini_repo, "unit-demo-l01")
    before_checksum = before["material_checksums"]["route-demo-l01-book"]
    second.write_bytes(b"synthetic worked exercises changed")
    after = current_unit_material_basis(mini_repo, "unit-demo-l01")

    assert after["material_checksums"]["route-demo-l01-book"] != before_checksum


def test_material_synthesis_schema_forbids_scores_and_shallow_deep_claims(mini_repo):
    _add_routed_unit(mini_repo)
    value = _synthesis(mini_repo)
    value["score"] = 9
    with pytest.raises(ValueError, match="properties.*unexpected"):
        validate_unit_material_synthesis(mini_repo, "unit-demo-l01", value)

    value = _synthesis(mini_repo)
    assessment = value["route_assessments"][0]
    assessment["review_status"] = "screened"
    assessment["reason"] = "Only metadata was screened."
    with pytest.raises(ValueError, match="not be valid"):
        validate_unit_material_synthesis(mini_repo, "unit-demo-l01", value)

    value = _synthesis(mini_repo)
    value["route_assessments"][0]["evidence"][0]["checksum"] = (
        "sha256:" + "0" * 64
    )
    with pytest.raises(ValueError, match="evidence checksum"):
        validate_unit_material_synthesis(mini_repo, "unit-demo-l01", value)


def test_pairwise_synthesis_requires_two_deep_reviewed_sources(mini_repo):
    _add_routed_unit(mini_repo)
    source_map_path = mini_repo / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(source_map_path.read_text(encoding="utf-8"))
    source_map["sources"][0]["unit_routes"].append({
        "id": "route-demo-l01-screened",
        "unit_id": "unit-demo-l01",
        "title": "Screened alternate",
        "format": "book",
        "angle": "A catalogued alternate that was not opened.",
        "covers": ["knowledge-demo-expectation"],
        "depth": "unassessed",
        "scope": "optional",
        "locator": "lecture-02.pdf",
    })
    write_yaml(source_map_path, source_map)
    value = _synthesis(mini_repo)
    screened_checksum = value["basis"]["material_checksums"][
        "route-demo-l01-screened"
    ]
    first_checksum = value["basis"]["material_checksums"]["route-demo-l01-book"]
    value["route_assessments"].append({
        "route_id": "route-demo-l01-screened",
        "source_id": "source-demo-book",
        "locator": "lecture-02.pdf",
        "review_status": "screened",
        "concept_ids": ["concept-expected-value"],
        "reason": "Only the canonical route metadata was screened.",
    })
    value["comparisons"] = [{
        "left_route_id": "route-demo-l01-book",
        "right_route_id": "route-demo-l01-screened",
        "relation": "overlaps",
        "narrative": "A detailed comparison would overclaim the screened source.",
        "concept_ids": ["concept-expected-value"],
        "evidence": {
            "left": [{"locator": "lecture-01.pdf p.1", "checksum": first_checksum}],
            "right": [{"locator": "lecture-02.pdf", "checksum": screened_checksum}],
        },
    }]

    with pytest.raises(ValueError, match="two deep-reviewed"):
        validate_unit_material_synthesis(mini_repo, "unit-demo-l01", value)


def test_unit_compare_materials_prepares_bounded_local_request(mini_repo):
    _add_routed_unit(mini_repo)
    request = AIActionService(mini_repo).prepare(
        action_id="unit.compare-materials",
        target_kind="unit",
        target_id="unit-demo-l01",
        provider="manual-bundle",
        request_id="ai-request-unit-demo",
    )
    assert request["target"] == {"kind": "unit", "id": "unit-demo-l01"}
    assert request["allowed_capabilities"] == ["unit.material-synthesis.publish"]
    bundle = mini_repo / "operations/ai-actions/requests/ai-request-unit-demo"
    context = (bundle / "context.md").read_text(encoding="utf-8")
    assert "route-demo-l01-book" in context
    assert "repository.read-external" not in context
    assert not any(path.suffix == ".pdf" for path in bundle.rglob("*"))


def _import_unit_synthesis_delivery(root: Path, tmp_path: Path):
    app = AIActionService(root)
    request = app.prepare(
        action_id="unit.compare-materials",
        target_kind="unit",
        target_id="unit-demo-l01",
        provider="manual-bundle",
        request_id="ai-request-demo",
    )
    source = tmp_path / "approved-unit-delivery"
    (source / "artifacts").mkdir(parents=True)
    synthesis = _synthesis(root)
    write_yaml(source / "artifacts/material-synthesis.yaml", synthesis)
    write_yaml(source / "delivery.yaml", {
        "schema_version": 1,
        "id": "ai-delivery-demo",
        "type": "ai-action-delivery",
        "request_id": request["id"],
        "action_id": "unit.compare-materials",
        "status": "ready",
        "producer": {"provider": "manual", "adapter": "manual-bundle"},
        "approval": {
            "user_approved": True,
            "approved_at": "2026-08-25T12:00:00+00:00",
        },
        "operations": [{
            "capability": "unit.material-synthesis.publish",
            "target_id": "unit-demo-l01",
            "artifact_ref": "artifacts/material-synthesis.yaml",
        }],
        "preconditions": request["preconditions"],
    })
    delivery = app.import_delivery(source)
    return app, delivery


def _delivery_apply_envelope(root: Path, app: AIActionService, delivery_id: str,
                             *, key: str = "apply-unit-demo-001") -> dict:
    delivery, directory = app.repository.get_delivery(delivery_id)
    artifact_hashes = {
        str(operation["artifact_ref"]): (
            "sha256:" + hashlib.sha256(
                (directory / str(operation["artifact_ref"])).read_bytes()
            ).hexdigest()
        )
        for operation in delivery["operations"]
        if operation.get("artifact_ref")
    }
    envelope = {
        "schema_version": 2,
        "request_id": "request-apply-unit-demo-001",
        "idempotency_key": key,
        "capability": "ai-action.delivery.apply",
        "channel": "operator",
        "expected_snapshot": f"sha256:{canonical_fingerprint(root)}",
        "expected_revisions": {
            artifact_id: artifact_revision(root, artifact_id)
            for artifact_id in ("unit-demo-l01", "material-synthesis-demo-l01")
        },
        "approval": {
            "kind": "approved-delivery",
            "subject_sha256": "sha256:" + "0" * 64,
        },
        "payload": {
            "delivery_id": delivery_id,
            "delivery_sha256": "sha256:" + hashlib.sha256(
                (directory / "delivery.yaml").read_bytes()
            ).hexdigest(),
            "artifact_sha256": artifact_hashes,
        },
    }
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    return envelope


def _run_delivery_apply(repo_root: Path, root: Path, request_file: Path,
                        envelope: dict):
    request_file.write_text(json.dumps(envelope), encoding="utf-8")
    return subprocess.run(
        [
            sys.executable,
            str(repo_root / "tools/los.py"),
            "--root", str(root),
            "capability", "ai-action.delivery.apply",
            "--payload-file", str(request_file),
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )


def test_unit_delivery_apply_is_content_bound_receipt_v2_and_replay_safe(
    mini_repo, repo_root, tmp_path,
):
    _add_routed_unit(mini_repo)
    app, delivery = _import_unit_synthesis_delivery(mini_repo, tmp_path)
    envelope = _delivery_apply_envelope(mini_repo, app, delivery["id"])

    first = _run_delivery_apply(
        repo_root, mini_repo, tmp_path / "apply-first.json", envelope,
    )
    assert first.returncode == 0, first.stderr or first.stdout
    response = json.loads(first.stdout)
    assert response["ok"] is True
    assert response["transaction_id"]
    receipt = yaml.safe_load((mini_repo / response["receipt_path"]).read_text())
    assert receipt["schema_version"] == 2
    assert receipt["capability"] == "ai-action.delivery.apply"
    assert receipt["request"]["approval"]["kind"] == "approved-delivery"
    assert receipt["request"]["intent_sha256"] == intent_sha256(envelope)
    assert receipt["expected_revisions"] == envelope["expected_revisions"]
    assert receipt["metadata"]["approved_delivery"] == {
        "delivery_sha256": envelope["payload"]["delivery_sha256"],
        "artifact_sha256": envelope["payload"]["artifact_sha256"],
    }
    assert receipt["authority"]["grants"] == [
        {
            "capability": "ai-action.delivery.apply",
            "declared_writes": ["operations/ai-actions/requests/**"],
        },
        {
            "capability": "unit.material-synthesis.publish",
            "declared_writes": [
                "curriculum/modules/**/units/**/material-synthesis.yaml"
            ],
        },
    ]
    destination = (
        mini_repo
        / "curriculum/modules/module-demo/units/unit-demo-l01/material-synthesis.yaml"
    )
    before = destination.read_bytes()
    receipts_before = sorted(
        (mini_repo / "operations/transactions").glob("transaction-*.yaml")
    )

    replay = _run_delivery_apply(
        repo_root, mini_repo, tmp_path / "apply-replay.json", envelope,
    )
    assert replay.returncode == 0, replay.stderr or replay.stdout
    replayed = json.loads(replay.stdout)
    assert replayed["replayed"] is True
    assert replayed["transaction_id"] == response["transaction_id"]
    assert destination.read_bytes() == before
    assert sorted((mini_repo / "operations/transactions").glob("transaction-*.yaml")) \
        == receipts_before

    changed_intent = json.loads(json.dumps(envelope))
    changed_intent["payload"]["delivery_sha256"] = "sha256:" + "f" * 64
    changed_intent["approval"]["subject_sha256"] = intent_sha256(changed_intent)
    conflict = _run_delivery_apply(
        repo_root, mini_repo, tmp_path / "apply-key-conflict.json", changed_intent,
    )
    assert conflict.returncode == 2
    assert json.loads(conflict.stdout)["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    assert destination.read_bytes() == before
    assert sorted((mini_repo / "operations/transactions").glob("transaction-*.yaml")) \
        == receipts_before


def test_unit_delivery_apply_refuses_artifact_changed_after_approval_atomically(
    mini_repo, repo_root, tmp_path,
):
    _add_routed_unit(mini_repo)
    app, delivery = _import_unit_synthesis_delivery(mini_repo, tmp_path)
    envelope = _delivery_apply_envelope(mini_repo, app, delivery["id"])
    _loaded, directory = app.repository.get_delivery(delivery["id"])
    artifact = directory / "artifacts/material-synthesis.yaml"
    artifact.write_text(artifact.read_text(encoding="utf-8") + "# changed\n",
                        encoding="utf-8")

    refused = _run_delivery_apply(
        repo_root, mini_repo, tmp_path / "apply-tampered.json", envelope,
    )
    assert refused.returncode == 2
    response = json.loads(refused.stdout)
    assert response["error"]["code"] == "UNCONFIRMED"
    assert not (
        mini_repo
        / "curriculum/modules/module-demo/units/unit-demo-l01/material-synthesis.yaml"
    ).exists()
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))


def test_unit_delivery_apply_requires_exact_subject_and_cannot_run_directly(
    mini_repo, repo_root, tmp_path,
):
    _add_routed_unit(mini_repo)
    app, delivery = _import_unit_synthesis_delivery(mini_repo, tmp_path)
    envelope = _delivery_apply_envelope(mini_repo, app, delivery["id"])
    approved_payload = dict(envelope["payload"])
    envelope["payload"]["delivery_sha256"] = "sha256:" + "f" * 64

    unbound = _run_delivery_apply(
        repo_root, mini_repo, tmp_path / "apply-unbound.json", envelope,
    )
    assert unbound.returncode == 2
    assert json.loads(unbound.stdout)["error"]["code"] == "UNCONFIRMED"

    direct = subprocess.run(
        [
            sys.executable,
            str(repo_root / "tools/los.py"),
            "--root", str(mini_repo),
            "ai-action-apply-delivery", delivery["id"],
            "--delivery-sha256", approved_payload["delivery_sha256"],
            "--artifact-sha256", json.dumps(approved_payload["artifact_sha256"]),
            "--expected-snapshot", envelope["expected_snapshot"],
            *[
                token
                for artifact_id, revision in envelope["expected_revisions"].items()
                for token in ("--expected-revision", f"{artifact_id}={revision}")
            ],
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )
    assert direct.returncode == 2
    assert "must use GatewayEnvelopeV2" in direct.stderr
    assert not (
        mini_repo
        / "curriculum/modules/module-demo/units/unit-demo-l01/material-synthesis.yaml"
    ).exists()


def test_unit_delivery_apply_returns_typed_revision_conflict_without_partial_write(
    mini_repo, repo_root, tmp_path,
):
    _add_routed_unit(mini_repo)
    app, delivery = _import_unit_synthesis_delivery(mini_repo, tmp_path)
    envelope = _delivery_apply_envelope(mini_repo, app, delivery["id"])

    missing = json.loads(json.dumps(envelope))
    del missing["expected_revisions"]["material-synthesis-demo-l01"]
    missing["approval"]["subject_sha256"] = intent_sha256(missing)
    incomplete = _run_delivery_apply(
        repo_root, mini_repo, tmp_path / "apply-incomplete-revisions.json", missing,
    )
    assert incomplete.returncode == 2
    assert json.loads(incomplete.stdout)["error"]["code"] == "INVALID_REQUEST"

    envelope["expected_revisions"]["material-synthesis-demo-l01"] = 7
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)

    refused = _run_delivery_apply(
        repo_root, mini_repo, tmp_path / "apply-conflict.json", envelope,
    )
    assert refused.returncode == 3
    response = json.loads(refused.stdout)
    assert response["error"]["code"] == "REVISION_CONFLICT"
    assert not (
        mini_repo
        / "curriculum/modules/module-demo/units/unit-demo-l01/material-synthesis.yaml"
    ).exists()
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))


def test_legacy_inspector_never_discovers_sealed_entries(mini_repo, tmp_path, monkeypatch):
    archive = tmp_path / "legacy-safe-fixture"
    safe = archive / "safe/note.md"
    sealed = archive / "sealed/private.md"
    safe.parent.mkdir(parents=True)
    sealed.parent.mkdir(parents=True)
    safe.write_text("preserved", encoding="utf-8")
    sealed.write_text("MUST-NOT-BE-READ", encoding="utf-8")
    target = mini_repo / "archive/safe-note.md"
    target.write_text("preserved", encoding="utf-8")

    original_read_bytes = Path.read_bytes
    original_scandir = os.scandir

    def guarded_read_bytes(path):
        assert path.resolve() != sealed.resolve(), "sealed Legacy content was opened"
        return original_read_bytes(path)

    def guarded_scandir(path):
        candidate = Path(path).resolve()
        assert candidate != archive.resolve(), "Legacy root was enumerated"
        return original_scandir(path)

    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)
    monkeypatch.setattr(os, "scandir", guarded_scandir)
    lock = inspect_legacy_archive(mini_repo, archive, {
        "schema_version": 1,
        "type": "legacy-archive-allowlist",
        "safe_entries": [{
            "relative_path": "safe/note.md",
            "category": "academic-note",
            "disposition": "byte-preserved",
            "canonical_targets": ["archive/safe-note.md"],
        }],
        "excluded_count": 1,
    })
    assert lock["verification"]["status"] == "verified"
    assert lock["excluded"] == {"count": 1, "status": "sealed-not-inspected"}
    assert "private.md" not in json.dumps(lock)


def test_legacy_inspector_refuses_intermediate_symlink_indirection(mini_repo, tmp_path):
    archive = tmp_path / "legacy-symlink-fixture"
    actual = archive / "actual"
    actual.mkdir(parents=True)
    (actual / "note.md").write_text("sealed-by-indirection", encoding="utf-8")
    (archive / "safe").symlink_to(actual, target_is_directory=True)

    with pytest.raises(LegacyArchiveError, match="traverses a symlink"):
        inspect_legacy_archive(mini_repo, archive, {
            "schema_version": 1,
            "type": "legacy-archive-allowlist",
            "safe_entries": [{
                "relative_path": "safe/note.md",
                "category": "academic-note",
                "disposition": "historical-only",
                "canonical_targets": [],
            }],
            "excluded_count": 0,
        })


def _catalog() -> dict:
    return {
        "schema_version": 1,
        "id": "master-planning-catalog",
        "type": "master-planning-catalog",
        "revision": 0,
        "updated_at": "2026-08-25T12:00:00+00:00",
        "candidate_modules": [{
            "id": "candidate-module-demo",
            "title": "Prospective Demo Module",
            "planning_state": "shortlist",
            "privacy_class": "academic-only",
            "provenance": ["reviewed academic-only derivative"],
            "fact_state": {"status": "unverified", "as_of": None, "evidence": []},
            "source_ids": ["candidate-source-demo"],
            "unresolved_references": [],
        }],
        "candidate_sources": [{
            "id": "candidate-source-demo",
            "title": "Prospective Demo Source",
            "planning_state": "shortlist",
            "privacy_class": "academic-only",
            "provenance": ["reviewed academic-only derivative"],
            "fact_state": {"status": "unverified", "as_of": None, "evidence": []},
        }],
        "comparison_ids": ["candidate-comparison-demo"],
    }


def test_masters_dashboard_is_explicit_sanitized_and_complete(mini_repo):
    catalog = validate_master_catalog(mini_repo, _catalog())
    destination = mini_repo / "curriculum/quarantine/masters-planning/catalog.yaml"
    write_yaml(destination, catalog)
    comparison = {
        "schema_version": 1,
        "id": "candidate-comparison-demo",
        "type": "candidate-source-comparison",
        "candidate_module_id": "candidate-module-demo",
        "status": "approved",
        "basis": {
            "catalog_revision": 0,
            "candidate_set_checksum": candidate_set_checksum(
                catalog, "candidate-module-demo"
            ),
            "policy": "tiered-v1",
            "request_id": "request-demo",
            "delivery_id": "delivery-demo",
        },
        "source_assessments": [{
            "candidate_source_id": "candidate-source-demo",
            "role": "selected",
            "review_status": "deep-reviewed",
            "concept_ids": [],
            "contribution": "A bounded synthetic comparison source.",
            "assumptions": "The reviewed academic-only derivative is current.",
            "notation": "No special notation is used.",
            "exercise_value": "Contains one representative exercise.",
            "best_for": "Checking the prospective module's source fit.",
            "limitations": "No official adoption decision is inferred.",
            "evidence": [{
                "locator": "sanitized catalog entry",
                "checksum": candidate_set_checksum(
                    catalog, "candidate-module-demo"
                ),
            }],
        }],
        "comparisons": [],
    }
    validate_candidate_comparison(mini_repo, comparison, catalog=catalog)
    write_yaml(
        mini_repo / "curriculum/quarantine/masters-planning/comparisons/candidate-comparison-demo.yaml",
        comparison,
    )

    with pytest.raises(MastersPlanningError, match="explicit access gesture"):
        masters_planning_dashboard(mini_repo, confirmed=False)
    dashboard = masters_planning_dashboard(mini_repo, confirmed=True)
    assert dashboard["banner"] == "Prospective—not current LearningOS"
    assert dashboard["catalog"]["candidate_modules"][0]["id"] == "candidate-module-demo"
    assert all(value is False for value in dashboard["isolation"].values())

    shallow = json.loads(json.dumps(comparison))
    shallow["source_assessments"][0] = {
        "candidate_source_id": "candidate-source-demo",
        "role": "selected",
        "review_status": "screened",
        "concept_ids": [],
        "reason": "Only the source menu was screened.",
    }
    with pytest.raises(MastersPlanningError, match="must be deep-reviewed"):
        validate_candidate_comparison(mini_repo, shallow, catalog=catalog)

    stale_set = json.loads(json.dumps(comparison))
    stale_set["basis"]["candidate_set_checksum"] = "sha256:" + "0" * 64
    with pytest.raises(MastersPlanningError, match="candidate set changed"):
        validate_candidate_comparison(mini_repo, stale_set, catalog=catalog)

    unsafe = _catalog()
    unsafe["candidate_modules"][0]["credential"] = "forbidden"
    with pytest.raises(MastersPlanningError, match="forbidden field"):
        validate_master_catalog(mini_repo, unsafe)


def test_masters_dashboard_refuses_intermediate_symlink_to_sealed_input(
    mini_repo,
    tmp_path,
):
    sealed = tmp_path / "sealed-master-input"
    sealed.mkdir()
    write_yaml(sealed / "catalog.yaml", _catalog())
    boundary = mini_repo / "curriculum/quarantine"
    boundary.mkdir(parents=True, exist_ok=True)
    (boundary / "masters-planning").symlink_to(sealed, target_is_directory=True)

    with pytest.raises(MastersPlanningError, match="symlink"):
        masters_planning_dashboard(mini_repo, confirmed=True)


def test_prospective_pairwise_comparison_requires_deep_evidence(mini_repo):
    catalog = _catalog()
    catalog["candidate_modules"][0]["source_ids"].append(
        "candidate-source-screened"
    )
    catalog["candidate_sources"].append({
        "id": "candidate-source-screened",
        "title": "Screened comparison source",
        "planning_state": "shortlist",
        "privacy_class": "academic-only",
        "provenance": ["reviewed academic-only derivative"],
        "fact_state": {"status": "unverified", "as_of": None, "evidence": []},
    })
    catalog = validate_master_catalog(mini_repo, catalog)
    checksum = candidate_set_checksum(catalog, "candidate-module-demo")
    deep = {
        "candidate_source_id": "candidate-source-demo",
        "role": "selected",
        "review_status": "deep-reviewed",
        "concept_ids": ["concept-expected-value"],
        "contribution": "A bounded synthetic comparison source.",
        "assumptions": "The academic-only derivative is current.",
        "notation": "Uses E[X].",
        "exercise_value": "Contains one representative exercise.",
        "best_for": "Checking source fit.",
        "limitations": "No adoption decision is inferred.",
        "evidence": [{"locator": "academic derivative p.1", "checksum": checksum}],
    }
    comparison = {
        "schema_version": 1,
        "id": "candidate-comparison-demo",
        "type": "candidate-source-comparison",
        "candidate_module_id": "candidate-module-demo",
        "status": "approved",
        "basis": {
            "catalog_revision": 0,
            "candidate_set_checksum": checksum,
            "policy": "tiered-v1",
            "request_id": "request-demo",
            "delivery_id": "delivery-demo",
        },
        "source_assessments": [deep, {
            "candidate_source_id": "candidate-source-screened",
            "role": "comparison",
            "review_status": "screened",
            "concept_ids": ["concept-expected-value"],
            "reason": "Only the sanitized source menu was screened.",
        }],
        "comparisons": [{
            "left_candidate_source_id": "candidate-source-demo",
            "right_candidate_source_id": "candidate-source-screened",
            "relation": "overlaps",
            "narrative": "This conclusion would overclaim a screened source.",
            "concept_ids": ["concept-expected-value"],
            "evidence": {
                "left": [{"locator": "academic derivative p.1", "checksum": checksum}],
                "right": [{"locator": "sanitized catalog", "checksum": checksum}],
            },
        }],
    }

    with pytest.raises(MastersPlanningError, match="two deep-reviewed"):
        validate_candidate_comparison(mini_repo, comparison, catalog=catalog)


def test_backup_manifest_is_allowlisted_and_verifies_new_roots(mini_repo, tmp_path):
    promotion = (
        mini_repo
        / "curriculum/quarantine/masters-planning/promotions/promotion-demo.yaml"
    )
    promotion.parent.mkdir(parents=True)
    promotion.write_text("schema_version: 1\nid: promotion-demo\n", encoding="utf-8")
    ui = tmp_path / "ui"
    (ui / "src").mkdir(parents=True)
    (ui / "src/app.ts").write_text("export {};", encoding="utf-8")
    (ui / "contracts").mkdir()
    contract = yaml.safe_load(
        (mini_repo / "system/contracts/manifest-contract.yaml").read_text(encoding="utf-8")
    )
    lock_name = f"manifest-v{contract['contract_version']}.lock.json"
    (ui / "contracts" / lock_name).write_text(json.dumps({
        "contract_version": contract["contract_version"],
        "schema_sha256": contract["schema_sha256"],
    }), encoding="utf-8")
    (ui / "plugin").mkdir()
    (ui / "plugin/main.js").write_text("void 0;\n", encoding="utf-8")
    (ui / "plugin/styles.css").write_text("/* restored */\n", encoding="utf-8")
    (ui / "plugin/manifest.json").write_text("{}\n", encoding="utf-8")
    (ui / "plugin/build-info.json").write_text("{}\n", encoding="utf-8")
    (ui / "plugin-assets.json").write_text(json.dumps({
        "schema_version": 1,
        "type": "learningos-ui-plugin-assets",
        "shipped": ["main.js", "styles.css", "manifest.json", "build-info.json"],
        "vault_owned": ["data.json"],
    }), encoding="utf-8")
    _installer_fixture(ui)
    (ui / "node_modules/pkg").mkdir(parents=True)
    (ui / "node_modules/pkg/private.js").write_text("ignored", encoding="utf-8")
    materials = mini_repo.parent / "materials"
    (materials / "source-demo").mkdir(parents=True)
    (materials / "source-demo/a.pdf").write_bytes(b"pdf")
    manifest = build_backup_manifest(mini_repo, ui_root=ui, materials_root=materials)
    rows = {(row["root"], row["path"]) for row in manifest["entries"]}
    assert (
        "core",
        "curriculum/quarantine/masters-planning/promotions/promotion-demo.yaml",
    ) in rows
    assert ("ui", "src/app.ts") in rows
    assert ("materials", "source-demo/a.pdf") in rows
    assert not any("node_modules" in path for _root, path in rows)

    restore = tmp_path / "restore"
    restored_core = restore / "core"
    restored_ui = restore / "ui"
    restored_materials = restore / "materials"
    
    roots_map = {
        "core": (mini_repo, restored_core),
        "ui": (ui, restored_ui),
        "materials": (materials, restored_materials)
    }
    for row in manifest["entries"]:
        src_root, dest_root = roots_map[row["root"]]
        src_file = src_root / row["path"]
        dest_file = dest_root / row["path"]
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dest_file)
    assert verify_backup_manifest(
        mini_repo, manifest,
        restored_core=restored_core,
        restored_ui=restored_ui,
        restored_materials=restored_materials,
    )["ok"]
    assured = verify_restored_system(
        mini_repo, manifest,
        restored_core=restored_core,
        restored_ui=restored_ui,
        restored_materials=restored_materials,
    )
    assert assured["ok"], assured
    assert assured["manual_ui_open_required"] is True
    with pytest.raises(BackupManifestError, match="new directories"):
        verify_restored_system(
            mini_repo, manifest,
            restored_core=mini_repo,
            restored_ui=restored_ui,
            restored_materials=restored_materials,
        )
    (restored_ui / "src/app.ts").write_text("changed", encoding="utf-8")
    result = verify_backup_manifest(
        mini_repo, manifest,
        restored_core=restored_core,
        restored_ui=restored_ui,
        restored_materials=restored_materials,
    )
    assert not result["ok"]
    assert any(row["issue"] == "checksum-mismatch" for row in result["issues"])


@contextlib.contextmanager
def _unreadable(directory: Path):
    """Deny enumeration of `directory`, restoring its mode even on failure.

    The denial is proven before the test leans on it: root can still read a
    mode-000 directory, and a test that silently stops testing anything is
    worse than one that says why it did not run.
    """
    original = directory.stat().st_mode
    os.chmod(directory, 0o000)
    try:
        try:
            with os.scandir(directory) as entries:
                next(entries, None)
        except PermissionError:
            pass
        else:
            pytest.skip("this user can still enumerate a mode-000 directory")
        yield
    finally:
        os.chmod(directory, original)


def _installer_fixture(ui: Path) -> None:
    """Synthetic external installer; delegation to the real one is tested separately."""
    (ui / "bases").mkdir()
    (ui / "bases/demo.base").write_text("views: []\n", encoding="utf-8")
    (ui / "install.py").write_text(
        "import argparse\n"
        "from pathlib import Path\n"
        "p = argparse.ArgumentParser()\n"
        "p.add_argument('--vault', required=True)\n"
        "p.add_argument('--dry-run', action='store_true', required=True)\n"
        "p.add_argument('--skip-tests', action='store_true', required=True)\n"
        "args = p.parse_args()\n"
        "assert Path(args.vault).is_dir()\n"
        "assert not list(Path(args.vault).iterdir())\n"
        "bases = Path(__file__).parent / 'bases'\n"
        "if not bases.is_dir(): raise SystemExit('bases is missing')\n"
        "if not list(bases.glob('*.base')): raise SystemExit('nothing matches bases/*.base')\n",
        encoding="utf-8",
    )


def _ui_fixture(ui: Path, core: Path) -> None:
    """A UI checkout shaped like the real one: a declaration, and what it names."""
    (ui / "plugin").mkdir(parents=True)
    (ui / "plugin/main.js").write_text("void 0;\n", encoding="utf-8")
    (ui / "plugin/styles.css").write_text("/* restored */\n", encoding="utf-8")
    (ui / "plugin/manifest.json").write_text("{}\n", encoding="utf-8")
    (ui / "plugin/build-info.json").write_text("{}\n", encoding="utf-8")
    (ui / "plugin-assets.json").write_text(json.dumps({
        "schema_version": 1,
        "type": "learningos-ui-plugin-assets",
        "shipped": ["main.js", "styles.css", "manifest.json", "build-info.json"],
        "vault_owned": ["data.json"],
    }), encoding="utf-8")
    _installer_fixture(ui)
    (ui / "contracts").mkdir()
    contract = yaml.safe_load(
        (core / "system/contracts/manifest-contract.yaml").read_text(encoding="utf-8")
    )
    lock_name = f"manifest-v{contract['contract_version']}.lock.json"
    (ui / "contracts" / lock_name).write_text(json.dumps({
        "contract_version": contract["contract_version"],
        "schema_sha256": contract["schema_sha256"],
    }), encoding="utf-8")


def _restore_from_inventory(manifest, roots_map) -> None:
    """Copy exactly what the inventory names — the way a real restore works."""
    for row in manifest["entries"]:
        src_root, dest_root = roots_map[row["root"]]
        dest = dest_root / row["path"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_root / row["path"], dest)


def _manifest_without(manifest, root: str, path: str):
    """The manifest an older contract would have produced: without `path`.

    Deleting the file from the restore instead would fail the checksum check,
    which short-circuits before the UI checks run — so it would prove nothing
    about them. An inventory that never named the file is the real defect.
    """
    rows = [
        row for row in manifest["entries"]
        if not (row["root"] == root and row["path"] == path)
    ]
    assert len(rows) < len(manifest["entries"]), f"{root}:{path} was not inventoried"
    trimmed = dict(manifest, entries=rows)
    trimmed["aggregate_sha256"] = "sha256:" + hashlib.sha256(
        json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        .encode("utf-8")
    ).hexdigest()
    return trimmed


def _assured_for(mini_repo, tmp_path, dropped: str | None):
    ui = tmp_path / "ui"
    _ui_fixture(ui, mini_repo)
    materials = tmp_path / "materials"
    materials.mkdir()
    manifest = build_backup_manifest(mini_repo, ui_root=ui, materials_root=materials)
    if dropped is not None:
        manifest = _manifest_without(manifest, "ui", dropped)
    restore = tmp_path / "restore"
    roots = {
        "core": (mini_repo, restore / "core"),
        "ui": (ui, restore / "ui"),
        "materials": (materials, restore / "materials"),
    }
    _restore_from_inventory(manifest, roots)
    return verify_restored_system(
        mini_repo, manifest,
        restored_core=restore / "core",
        restored_ui=restore / "ui",
        restored_materials=restore / "materials",
    )


def test_backup_manifest_refuses_an_unreadable_directory_inside_an_admitted_tree(
    mini_repo, tmp_path
):
    ui = tmp_path / "ui"
    _ui_fixture(ui, mini_repo)
    materials = mini_repo.parent / "materials"
    restricted = materials / "restricted"
    restricted.mkdir(parents=True)
    (restricted / "only-copy.pdf").write_bytes(b"pdf")

    def inventory():
        return {
            row["path"]
            for row in build_backup_manifest(
                mini_repo, ui_root=ui, materials_root=materials
            )["entries"]
            if row["root"] == "materials"
        }

    assert "restricted/only-copy.pdf" in inventory()

    # Every authority exists, so an "unavailable authority" refusal cannot stand
    # in for the traversal failure this is actually testing.
    with _unreadable(restricted):
        with pytest.raises(BackupManifestError, match="unreadable"):
            build_backup_manifest(mini_repo, ui_root=ui, materials_root=materials)

    assert "restricted/only-copy.pdf" in inventory()


def test_backup_manifest_refuses_an_unreadable_declared_file(mini_repo, tmp_path):
    contract_path = mini_repo / "system/contracts/backup-roots.yaml"
    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    contract["roots"]["core"]["files"].append("nested/declared.txt")
    contract_path.write_text(yaml.safe_dump(contract), encoding="utf-8")
    nested = mini_repo / "nested"
    nested.mkdir()
    (nested / "declared.txt").write_text("content", encoding="utf-8")

    ui = tmp_path / "ui"
    _ui_fixture(ui, mini_repo)
    materials = tmp_path / "materials"
    materials.mkdir()

    def inventory():
        return {
            row["path"]
            for row in build_backup_manifest(
                mini_repo, ui_root=ui, materials_root=materials
            )["entries"]
        }

    assert "nested/declared.txt" in inventory()

    # `nested` is named by no admitted tree, so this exercises the declared-file
    # path rather than the walk.
    with _unreadable(nested):
        with pytest.raises(BackupManifestError, match="unreadable"):
            build_backup_manifest(mini_repo, ui_root=ui, materials_root=materials)


def test_backup_manifest_ignores_an_unreadable_excluded_directory(mini_repo, tmp_path):
    ui = tmp_path / "ui"
    _ui_fixture(ui, mini_repo)
    # `materials` declares `.`, so an excluded directory here really is inside an
    # admitted tree — which is what makes this a guard rather than a formality.
    materials = mini_repo.parent / "materials"
    (materials / "keep").mkdir(parents=True)
    (materials / "keep/kept.pdf").write_bytes(b"pdf")
    ignored = materials / "node_modules"
    ignored.mkdir()
    (ignored / "private.js").write_text("ignored", encoding="utf-8")

    with _unreadable(ignored):
        manifest = build_backup_manifest(
            mini_repo, ui_root=ui, materials_root=materials
        )

    assert {
        row["path"] for row in manifest["entries"] if row["root"] == "materials"
    } == {"keep/kept.pdf"}


def test_verify_restored_system_detects_a_missing_asset_declaration(mini_repo, tmp_path):
    assured = _assured_for(mini_repo, tmp_path, "plugin-assets.json")
    assert not assured["ok"]
    # The restore is faithful to its inventory; the inventory is the thing that
    # was wrong. If checksums could fail here the assertion below would be free.
    checksums = next(c for c in assured["checks"] if c["id"] == "checksums")
    assert checksums["ok"], checksums
    declaration = next(c for c in assured["checks"] if c["id"] == "ui-asset-declaration")
    assert not declaration["ok"]
    assert "could not be read" in declaration["detail"]["error"]


def test_verify_restored_system_detects_a_missing_shipped_asset(mini_repo, tmp_path):
    assured = _assured_for(mini_repo, tmp_path, "plugin/styles.css")
    assert not assured["ok"]
    checksums = next(c for c in assured["checks"] if c["id"] == "checksums")
    assert checksums["ok"], checksums
    declaration = next(c for c in assured["checks"] if c["id"] == "ui-asset-declaration")
    assert not declaration["ok"]
    assert declaration["detail"]["missing"] == ["styles.css"]


def test_backup_manifest_refuses_an_asset_the_checkout_cannot_ship(mini_repo, tmp_path):
    ui = tmp_path / "ui"
    _ui_fixture(ui, mini_repo)
    (ui / "plugin/styles.css").unlink()
    materials = tmp_path / "materials"
    materials.mkdir()
    with pytest.raises(BackupManifestError, match="plugin/styles.css"):
        build_backup_manifest(mini_repo, ui_root=ui, materials_root=materials)


def test_backup_manifest_refuses_an_empty_asset_declaration(mini_repo, tmp_path):
    ui = tmp_path / "ui"
    _ui_fixture(ui, mini_repo)
    # An empty `shipped` list is the shape that reads as "nothing to check" and
    # certifies a restore holding no plugin at all.
    (ui / "plugin-assets.json").write_text(json.dumps({
        "schema_version": 1,
        "type": "learningos-ui-plugin-assets",
        "shipped": [],
        "vault_owned": ["data.json"],
    }), encoding="utf-8")
    materials = tmp_path / "materials"
    materials.mkdir()
    with pytest.raises(BackupManifestError, match="no shipped assets"):
        build_backup_manifest(mini_repo, ui_root=ui, materials_root=materials)


def test_backup_manifest_refuses_a_shipped_entry_that_escapes_the_plugin_directory(
    mini_repo, tmp_path
):
    ui = tmp_path / "ui"
    _ui_fixture(ui, mini_repo)
    (ui / "plugin-assets.json").write_text(json.dumps({
        "schema_version": 1,
        "type": "learningos-ui-plugin-assets",
        "shipped": ["main.js", "../../etc/passwd"],
        "vault_owned": ["data.json"],
    }), encoding="utf-8")
    materials = tmp_path / "materials"
    materials.mkdir()
    with pytest.raises(BackupManifestError, match="bare filename"):
        build_backup_manifest(mini_repo, ui_root=ui, materials_root=materials)


def test_backup_manifest_refuses_an_unreadable_parent_of_an_admitted_tree(mini_repo, tmp_path):
    ui = tmp_path / "ui"
    _ui_fixture(ui, mini_repo)
    materials = tmp_path / "materials"
    materials.mkdir()
    parent = mini_repo / "operations"
    tree = parent / "legacy"
    tree.mkdir(parents=True, exist_ok=True)
    (tree / "only-copy.txt").write_text("keep me", encoding="utf-8")
    before = build_backup_manifest(mini_repo, ui_root=ui, materials_root=materials)
    assert any(row["path"] == "operations/legacy/only-copy.txt" for row in before["entries"])
    # The authority is still readable. Denying the authority would test an
    # already-working guard instead of the admitted-tree inspection failure.
    with _unreadable(parent):
        with pytest.raises(BackupManifestError, match="unreadable"):
            build_backup_manifest(mini_repo, ui_root=ui, materials_root=materials)


@pytest.mark.parametrize("operation", ["lstat", "resolve"])
def test_backup_manifest_refuses_file_inspection_io_errors(mini_repo, tmp_path, monkeypatch, operation):
    import errno

    ui = tmp_path / "ui"
    _ui_fixture(ui, mini_repo)
    materials = tmp_path / "materials"
    materials.mkdir()
    only_copy = materials / "only-copy.pdf"
    only_copy.write_bytes(b"pdf")
    before = build_backup_manifest(mini_repo, ui_root=ui, materials_root=materials)
    assert any(row["root"] == "materials" and row["path"] == only_copy.name
               for row in before["entries"])
    original = getattr(Path, operation)

    def fail_inspection(path, *args, **kwargs):
        if path == only_copy:
            raise OSError(errno.EIO, "injected storage failure", str(path))
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, operation, fail_inspection)
    with pytest.raises(BackupManifestError, match="unreadable.*only-copy.pdf"):
        build_backup_manifest(mini_repo, ui_root=ui, materials_root=materials)


def test_backup_manifest_preserves_absence_and_symlink_exclusions(mini_repo, tmp_path):
    ui = tmp_path / "ui"
    _ui_fixture(ui, mini_repo)
    materials = tmp_path / "materials"
    materials.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "private.pdf").write_bytes(b"private")
    (materials / "linked-tree").symlink_to(outside, target_is_directory=True)
    (materials / "linked-file.pdf").symlink_to(outside / "private.pdf")
    # This explicitly declared tree has a genuinely absent parent.
    contract_path = mini_repo / "system/contracts/backup-roots.yaml"
    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    contract["roots"]["core"]["trees"].append("absent-parent/absent-tree")
    contract_path.write_text(yaml.safe_dump(contract), encoding="utf-8")
    manifest = build_backup_manifest(mini_repo, ui_root=ui, materials_root=materials)
    assert not any(row["root"] == "materials" for row in manifest["entries"])
    assert not any(row["path"].startswith("absent-parent/") for row in manifest["entries"])
    # Explicit declarations that traverse a symlink retain their refusal.
    contract["roots"]["materials"]["trees"].append("linked-tree")
    contract_path.write_text(yaml.safe_dump(contract), encoding="utf-8")
    with pytest.raises(BackupManifestError, match="traverses a symlink"):
        build_backup_manifest(mini_repo, ui_root=ui, materials_root=materials)


# Mirrors obsidian-ui/install.py: read_plugin_assets' exact MANIFEST_KEYS,
# _check_names' non-empty array/filename/uniqueness rules for BOTH lists,
# and read_plugin_assets' disjoint ownership rule. Keep this corpus aligned
# when those installer rules change; the Core gate uses synthetic fixtures.
@pytest.mark.parametrize("change,error", [
    ({"vault_owned": ["main.js"]}, "both shipped and vault-owned"),
    ({"vault_owned": None}, "vault_owned"),
    ({"vault_owned": "data.json"}, "vault_owned"),
    ({"vault_owned": []}, "vault_owned"),
    ({"vault_owned": [None]}, "vault_owned"),
    ({"vault_owned": [" "]}, "vault_owned"),
    ({"vault_owned": ["../data.json"]}, "bare filename"),
    ({"vault_owned": ["dir\\data.json"]}, "bare filename"),
    ({"vault_owned": ["."]}, "bare filename"),
    ({"vault_owned": [".."]}, "bare filename"),
    ({"vault_owned": ["data.json", "data.json"]}, "repeats"),
    ({"unexpected": []}, "exactly"),
])
def test_backup_manifest_matches_installer_asset_rules(mini_repo, tmp_path, change, error):
    ui = tmp_path / "ui"
    _ui_fixture(ui, mini_repo)
    declaration = ui / "plugin-assets.json"
    parsed = json.loads(declaration.read_text(encoding="utf-8"))
    parsed.update(change)
    declaration.write_text(json.dumps(parsed), encoding="utf-8")
    materials = tmp_path / "materials"
    materials.mkdir()
    with pytest.raises(BackupManifestError, match=error):
        build_backup_manifest(mini_repo, ui_root=ui, materials_root=materials)


def test_backup_manifest_requires_installer_vault_owned_key(mini_repo, tmp_path):
    ui = tmp_path / "ui"
    _ui_fixture(ui, mini_repo)
    declaration = ui / "plugin-assets.json"
    parsed = json.loads(declaration.read_text(encoding="utf-8"))
    del parsed["vault_owned"]  # install.py requires exactly MANIFEST_KEYS.
    declaration.write_text(json.dumps(parsed), encoding="utf-8")
    materials = tmp_path / "materials"
    materials.mkdir()
    with pytest.raises(BackupManifestError, match="exactly"):
        build_backup_manifest(mini_repo, ui_root=ui, materials_root=materials)


@pytest.mark.parametrize("vault_owned", [["main.js"], "data.json"])
def test_restore_reports_installer_asset_contract_failure(mini_repo, tmp_path, vault_owned):
    ui = tmp_path / "ui"
    _ui_fixture(ui, mini_repo)
    materials = tmp_path / "materials"
    materials.mkdir()
    manifest = build_backup_manifest(mini_repo, ui_root=ui, materials_root=materials)
    # Model an older inventory which faithfully captured a bad declaration.
    # Rebind its bytes so checksum failure cannot hide the missing validation.
    declaration = ui / "plugin-assets.json"
    parsed = json.loads(declaration.read_text(encoding="utf-8"))
    parsed["vault_owned"] = vault_owned
    declaration.write_text(json.dumps(parsed), encoding="utf-8")
    data = declaration.read_bytes()
    for row in manifest["entries"]:
        if (row["root"], row["path"]) == ("ui", "plugin-assets.json"):
            row["size"] = len(data)
            row["sha256"] = "sha256:" + hashlib.sha256(data).hexdigest()
    manifest["aggregate_sha256"] = "sha256:" + hashlib.sha256(
        json.dumps(manifest["entries"], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        .encode("utf-8")
    ).hexdigest()
    restore = tmp_path / "restore"
    _restore_from_inventory(manifest, {
        "core": (mini_repo, restore / "core"),
        "ui": (ui, restore / "ui"),
        "materials": (materials, restore / "materials"),
    })
    assured = verify_restored_system(
        mini_repo, manifest, restored_core=restore / "core",
        restored_ui=restore / "ui", restored_materials=restore / "materials",
    )
    checks = {check["id"]: check for check in assured["checks"]}
    assert checks["checksums"]["ok"]
    assert not assured["ok"]
    assert not checks["ui-asset-declaration"]["ok"]
    assert checks["ui-asset-declaration"]["detail"]["error"]


@pytest.mark.parametrize("empty_directory", [False, True], ids=["missing-bases", "empty-bases"])
def test_restore_runs_installer_bases_preflight(mini_repo, tmp_path, empty_directory):
    ui = tmp_path / "ui"
    _ui_fixture(ui, mini_repo)
    materials = tmp_path / "materials"
    materials.mkdir()
    manifest = _manifest_without(
        build_backup_manifest(mini_repo, ui_root=ui, materials_root=materials),
        "ui", "bases/demo.base",
    )
    restore = tmp_path / "restore"
    _restore_from_inventory(manifest, {
        "core": (mini_repo, restore / "core"),
        "ui": (ui, restore / "ui"),
        "materials": (materials, restore / "materials"),
    })
    if empty_directory:
        (restore / "ui/bases").mkdir()
    assured = verify_restored_system(
        mini_repo, manifest, restored_core=restore / "core",
        restored_ui=restore / "ui", restored_materials=restore / "materials",
    )
    checks = {check["id"]: check for check in assured["checks"]}
    assert checks["checksums"]["ok"]
    assert not assured["ok"]
    assert not checks["ui-install-preflight"]["ok"]
    expected = "nothing matches" if empty_directory else "bases is missing"
    assert expected in checks["ui-install-preflight"]["detail"]["stderr"]
    for name in ("ui-asset-declaration", "ui-bundle-smoke", "ui-contract-lock"):
        assert checks[name]["ok"], checks[name]


def test_restore_refuses_an_uninventoried_installer(mini_repo, tmp_path):
    assured = _assured_for(mini_repo, tmp_path, "install.py")
    checks = {check["id"]: check for check in assured["checks"]}
    assert checks["checksums"]["ok"]
    assert not assured["ok"]
    assert not checks["ui-install-preflight"]["ok"]
    assert "install.py" in checks["ui-install-preflight"]["detail"]["error"]


def test_restore_uses_the_restored_installers_new_requirements(mini_repo, tmp_path):
    ui = tmp_path / "ui"
    _ui_fixture(ui, mini_repo)
    # An installer can introduce a requirement unknown to Core. Prove that its
    # refusal propagates without adding that prerequisite to a second list.
    with (ui / "install.py").open("a", encoding="utf-8") as stream:
        stream.write("raise SystemExit('new installer prerequisite is missing')\n")
    materials = tmp_path / "materials"
    materials.mkdir()
    manifest = build_backup_manifest(mini_repo, ui_root=ui, materials_root=materials)
    restore = tmp_path / "restore"
    _restore_from_inventory(manifest, {
        "core": (mini_repo, restore / "core"),
        "ui": (ui, restore / "ui"),
        "materials": (materials, restore / "materials"),
    })
    assured = verify_restored_system(
        mini_repo, manifest, restored_core=restore / "core",
        restored_ui=restore / "ui", restored_materials=restore / "materials",
    )
    checks = {check["id"]: check for check in assured["checks"]}
    assert checks["checksums"]["ok"]
    assert not assured["ok"]
    assert "new installer prerequisite" in checks["ui-install-preflight"]["detail"]["stderr"]
    assert not (restore / "core/.obsidian").exists()
    assert not (restore / "core/bases").exists()


@pytest.mark.full_repo
@pytest.mark.parametrize("case", ["valid", "missing-bases", "empty-bases", "indirect-base", "missing-config"])
def test_restore_preflight_with_current_paired_installer(mini_repo, tmp_path, repo_root, case):
    # This integration uses the actual paired install.py, not a copied set of
    # its rules. Core-only CI has no paired UI; the paired checkout runs it.
    installer = repo_root.parent / "obsidian-ui/install.py"
    if not installer.is_file():
        pytest.skip("paired UI installer is not available in this Core-only checkout")
    ui = tmp_path / "ui"
    _ui_fixture(ui, mini_repo)
    shutil.copy2(installer, ui / "install.py")
    (ui / "vault-config").mkdir()
    (ui / "vault-config/app.json").write_text('{"userIgnoreFilters": []}', encoding="utf-8")
    (ui / "vault-config/core-plugins.json").write_text('{}', encoding="utf-8")
    materials = tmp_path / "materials"
    materials.mkdir()
    manifest = build_backup_manifest(mini_repo, ui_root=ui, materials_root=materials)
    if case in {"missing-bases", "empty-bases"}:
        manifest = _manifest_without(manifest, "ui", "bases/demo.base")
    elif case == "missing-config":
        manifest = _manifest_without(manifest, "ui", "vault-config/app.json")
    restore = tmp_path / "restore"
    _restore_from_inventory(manifest, {
        "core": (mini_repo, restore / "core"),
        "ui": (ui, restore / "ui"),
        "materials": (materials, restore / "materials"),
    })
    if case == "empty-bases":
        (restore / "ui/bases").mkdir()
    elif case == "indirect-base":
        (restore / "ui/bases/indirect.base").symlink_to(restore / "ui/bases/demo.base")
    before_ui = {path.relative_to(restore / "ui"): path.read_bytes()
                 for path in (restore / "ui").rglob("*") if path.is_file()}
    assured = verify_restored_system(
        mini_repo, manifest, restored_core=restore / "core",
        restored_ui=restore / "ui", restored_materials=restore / "materials",
    )
    checks = {check["id"]: check for check in assured["checks"]}
    assert checks["checksums"]["ok"], checks
    assert checks["ui-install-preflight"]["ok"] == (case == "valid"), checks
    assert assured["ok"] == (case == "valid"), checks
    assert checks["ui-install-preflight"]["detail"]["vault_unchanged"]
    assert before_ui == {path.relative_to(restore / "ui"): path.read_bytes()
                         for path in (restore / "ui").rglob("*") if path.is_file()}
    assert not (restore / "core/.obsidian").exists()
    assert not (restore / "core/bases").exists()


@pytest.mark.parametrize("failure", ["timeout", "launch-error", "dry-run-wrote"])
def test_restore_preflight_fails_closed_on_execution_problems(mini_repo, tmp_path, monkeypatch, failure):
    original = subprocess.run

    def fail_installer(argv, *args, **kwargs):
        if "--dry-run" not in argv:
            return original(argv, *args, **kwargs)
        if failure == "timeout":
            raise subprocess.TimeoutExpired(argv, 30)
        if failure == "launch-error":
            raise OSError("installer process could not start")
        vault = Path(argv[argv.index("--vault") + 1])
        (vault / "unexpected.txt").write_text("not a dry run", encoding="utf-8")
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fail_installer)
    # Keep every required input intact: only the injected failure can reject it.
    assured = _assured_for(mini_repo, tmp_path, None)
    checks = {check["id"]: check for check in assured["checks"]}
    assert checks["checksums"]["ok"]
    assert not checks["ui-install-preflight"]["ok"]
    assert not assured["ok"]
    if failure == "dry-run-wrote":
        assert checks["ui-install-preflight"]["detail"]["vault_unchanged"] is False
    else:
        assert checks["ui-install-preflight"]["detail"]["error"]


def test_restore_does_not_run_installer_before_checksum_verification(mini_repo, tmp_path, monkeypatch):
    ui = tmp_path / "ui"
    _ui_fixture(ui, mini_repo)
    materials = tmp_path / "materials"
    materials.mkdir()
    manifest = build_backup_manifest(mini_repo, ui_root=ui, materials_root=materials)
    restore = tmp_path / "restore"
    _restore_from_inventory(manifest, {
        "core": (mini_repo, restore / "core"),
        "ui": (ui, restore / "ui"),
        "materials": (materials, restore / "materials"),
    })
    (restore / "ui/install.py").write_text("raise SystemExit('changed')", encoding="utf-8")

    def unexpected_execution(*args, **kwargs):
        pytest.fail("checksum mismatch must short-circuit every subprocess")

    monkeypatch.setattr(subprocess, "run", unexpected_execution)
    assured = verify_restored_system(
        mini_repo, manifest, restored_core=restore / "core",
        restored_ui=restore / "ui", restored_materials=restore / "materials",
    )
    assert not assured["ok"]
    assert [check["id"] for check in assured["checks"]] == ["checksums"]


@pytest.mark.full_repo
def test_core_asset_reader_stays_in_step_with_paired_installer(tmp_path, repo_root):
    import runpy

    from learning_os.backup_manifest import read_shipped_assets

    installer = repo_root.parent / "obsidian-ui/install.py"
    if not installer.is_file():
        pytest.skip("paired UI installer is not available in this Core-only checkout")
    namespace = runpy.run_path(str(installer))
    base = {"schema_version": 1, "type": "learningos-ui-plugin-assets",
            "shipped": ["main.js"], "vault_owned": ["data.json"]}
    cases = [base, {}, {**base, "extra": None}]
    cases.extend({key: value for key, value in base.items() if key != field} for field in base)
    for field in ("shipped", "vault_owned"):
        cases.extend({**base, field: value} for value in (
            None, {}, True, "data.json", [], [None], [""], [" "], ["."], [".."],
            ["../x"], ["dir/x"], ["dir\\x"], ["x", "x"], ["main.js"], ["data.json"],
        ))
    cases.extend({**base, "schema_version": version} for version in (True, False, 0, 2, "1", None))
    for payload in cases:
        (tmp_path / "plugin-assets.json").write_text(json.dumps(payload), encoding="utf-8")
        decisions = []
        for reader, error in ((read_shipped_assets, BackupManifestError),
                              (namespace["read_plugin_assets"], namespace["PluginAssetsError"])):
            try:
                reader(tmp_path)
            except error:
                decisions.append(False)
            else:
                decisions.append(True)
        assert decisions[0] == decisions[1], payload
