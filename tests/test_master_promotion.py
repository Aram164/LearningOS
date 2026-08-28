"""Synthetic assurance for the one-bundle Future Master's promotion boundary."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from test_curriculum_v2 import add_curriculum, write_yaml

from learning_os.commands.module import cmd_module_plan_import
from learning_os.contracts.gateway import (
    GatewayRequestContext,
    gateway_request_context,
    intent_sha256,
)
from learning_os.fingerprint import canonical_fingerprint
from learning_os.genout import build_manifest
from learning_os.loader import load_repo
from learning_os.masters_planning import (
    MastersPlanningError,
    master_promotion_destination,
    prepare_master_promotion,
    promotion_package_sha256,
)
from learning_os.transactions import TransactionFailure

NOW = dt.datetime.now(dt.UTC).replace(hour=0, minute=0, second=0, microsecond=0)


def _fact_state(*, days_old: int = 0) -> dict:
    as_of = (NOW.date() - dt.timedelta(days=days_old)).isoformat()
    return {
        "status": "verified-current",
        "as_of": as_of,
        "evidence": ["reviewed official academic listing"],
    }


def _catalog() -> dict:
    return {
        "schema_version": 1,
        "id": "master-planning-catalog",
        "type": "master-planning-catalog",
        "revision": 0,
        "updated_at": NOW.isoformat(),
        "candidate_modules": [
            {
                "id": "candidate-module-future-demo",
                "title": "Future Demo Module",
                "planning_state": "selected",
                "privacy_class": "academic-only",
                "provenance": ["reviewed academic-only derivative"],
                "fact_state": _fact_state(),
                "source_ids": [
                    "candidate-source-adopted",
                    "candidate-source-unadopted",
                ],
                "unresolved_references": [],
            },
            {
                "id": "candidate-module-other",
                "title": "Other Future Module",
                "planning_state": "shortlist",
                "privacy_class": "academic-only",
                "provenance": ["separate reviewed derivative"],
                "fact_state": _fact_state(),
                "source_ids": ["candidate-source-other"],
                "unresolved_references": [],
            },
        ],
        "candidate_sources": [
            {
                "id": "candidate-source-adopted",
                "title": "Adopted existing source",
                "planning_state": "selected",
                "privacy_class": "academic-only",
                "provenance": ["reviewed academic-only derivative"],
                "fact_state": _fact_state(),
            },
            {
                "id": "candidate-source-unadopted",
                "title": "Unadopted source menu entry",
                "planning_state": "selected",
                "privacy_class": "academic-only",
                "provenance": ["reviewed academic-only derivative"],
                "fact_state": _fact_state(),
            },
            {
                "id": "candidate-source-other",
                "title": "Other module source",
                "planning_state": "shortlist",
                "privacy_class": "academic-only",
                "provenance": ["separate reviewed derivative"],
                "fact_state": _fact_state(),
            },
        ],
        "comparison_ids": ["candidate-comparison-preserved"],
    }


def _promotion_package(root: Path) -> dict:
    audit = root / "work/active/workspace-future-demo/outputs/future-demo-coverage.md"
    audit.parent.mkdir(parents=True, exist_ok=True)
    audit.write_text(
        "# Coverage\n\n## Local\n\nComplete.\n\n## Linked\n\nComplete.\n\n"
        "## Completeness\n\nReviewed.\n",
        encoding="utf-8",
    )
    return {
        "schema_version": 1,
        "id": "master-promotion-future-demo",
        "type": "master-planning-promotion",
        "recorded_at": NOW.isoformat(),
        "candidate_module_id": "candidate-module-future-demo",
        "canonical_module_id": "module-future-demo",
        "catalog_revision": 0,
        "verification": {
            "policy": "official-academic-30d-v1",
            "status": "verified-current",
            "as_of": NOW.date().isoformat(),
            "evidence": [{
                "authority": "official-academic",
                "url": "https://example.edu/official/module-future-demo",
                "claim": "The module and adopted source remain current.",
                "verified_on": NOW.date().isoformat(),
            }],
        },
        "adopted_sources": [{
            "candidate_source_id": "candidate-source-adopted",
            "canonical_source_id": "source-demo-book",
        }],
        "module_plan": {
            "module_id": "module-future-demo",
            "plan_contract": {
                "version": 2,
                "plan_template_version": 1,
                "coverage_audit": (
                    "work/active/workspace-future-demo/outputs/"
                    "future-demo-coverage.md"
                ),
                "checks": {
                    "local_inventory_complete": True,
                    "linked_inventory_complete": True,
                    "materials_opened_and_content_checked": True,
                    "current_and_prior_scope_reconciled": True,
                    "duplicates_and_numbering_checked": True,
                    "exclusions_and_unresolved_gaps_recorded": True,
                },
                "intentional_reorders": [],
            },
            "module_patch": {
                "id": "module-future-demo",
                "type": "module",
                "kind": "academic",
                "area_id": "program-bachelors",
                "institution": "Example University",
                "title": "Future Demo Module",
                "semester": "sose-2026",
                "status": "planned",
                "unit_order": ["unit-future-demo-l01"],
                "source_map": "source-map.yaml",
            },
            "source_map": {
                "type": "module-source-map",
                "module_id": "module-future-demo",
                "sources": [{
                    "source_id": "source-demo-book",
                    "role": "spine",
                    "why": "The explicitly adopted existing canonical source.",
                    "priority": 0,
                    "unit_routes": [{
                        "id": "route-future-demo-l01-book",
                        "unit_id": "unit-future-demo-l01",
                        "title": "Demo book — future topic",
                        "format": "book",
                        "angle": "Covers the bounded prospective topic.",
                        "angle_detail": "Uses the already canonical source without importing alternatives.",
                        "covers": ["knowledge-future-demo-topic"],
                        "depth": "course-aligned",
                        "scope": "current",
                        "locator": "Chapter 1, PDF pp. 1-20",
                    }],
                }],
            },
            "units": [{
                "unit": {
                    "id": "unit-future-demo-l01",
                    "type": "unit",
                    "module_id": "module-future-demo",
                    "kind": "lecture",
                    "title": "Future topic",
                    "order": 1,
                    "scope": "The verified academic-only module scope.",
                    "status": "needs-map",
                    "knowledge_map": {
                        "summary": "A bounded map for the future topic.",
                        "nodes": [{
                            "id": "knowledge-future-demo-topic",
                            "title": "Future topic",
                            "summary": "The canonicalized unit's core topic.",
                        }],
                    },
                    "scope_sources": [{
                        "source_id": "source-demo-book",
                        "authority": "reference",
                        "locator": "Chapter 1, PDF pp. 1-20",
                    }],
                    "source_selections": [],
                    "artifacts": {},
                    "workspace_ids": [],
                },
            }],
            "source_patches": [],
            "workspace_updates": [],
        },
    }


def _new_source_package(root: Path) -> dict:
    package = copy.deepcopy(_promotion_package(root))
    canonical_id = "source-future-official"
    package["adopted_sources"] = [{
        "candidate_source_id": "candidate-source-adopted",
        "canonical_source_id": canonical_id,
        "canonical_source": {
            "id": canonical_id,
            "title": "Official Future Demo Reader",
            "type": "book",
            "organization": "Example University",
            "year": NOW.year,
            "url": "https://example.edu/official/future-demo-reader",
        },
        "registry_target": "sources/registry/future-demo.yaml",
    }]
    source_row = package["module_plan"]["source_map"]["sources"][0]
    source_row["source_id"] = canonical_id
    source_row["why"] = "The explicitly adopted new official academic source."
    package["module_plan"]["units"][0]["unit"]["scope_sources"][0][
        "source_id"
    ] = canonical_id
    return package


def _setup(root: Path) -> tuple[dict, bytes]:
    add_curriculum(root)
    catalog = _catalog()
    write_yaml(
        root / "curriculum/quarantine/masters-planning/catalog.yaml",
        catalog,
    )
    comparison = (
        root / "curriculum/quarantine/masters-planning/comparisons/"
        "candidate-comparison-preserved.yaml"
    )
    comparison.parent.mkdir(parents=True, exist_ok=True)
    comparison_bytes = b"synthetic-approved-comparison\n"
    comparison.write_bytes(comparison_bytes)
    return _promotion_package(root), comparison_bytes


def _gateway_envelope(root: Path, package: dict, *, revisions: dict[str, int]) -> dict:
    envelope = {
        "schema_version": 2,
        "request_id": "request-master-promotion-future-demo",
        "idempotency_key": "master-promotion-future-demo-001",
        "capability": "module.plan.import",
        "channel": "codex",
        "expected_snapshot": f"sha256:{canonical_fingerprint(root)}",
        "expected_revisions": revisions,
        "approval": {
            "kind": "operator-approval",
            "subject_sha256": "sha256:" + "0" * 64,
        },
        "payload": {
            "module_id": "module-future-demo",
            "promotion": package,
            "package_sha256": promotion_package_sha256(package),
        },
    }
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    return envelope


def _run_gateway(repo_root: Path, root: Path, request: Path, envelope: dict):
    request.write_text(json.dumps(envelope), encoding="utf-8")
    return subprocess.run(
        [
            sys.executable,
            str(repo_root / "tools/los.py"),
            "--root",
            str(root),
            "capability",
            "module.plan.import",
            "--payload-file",
            str(request),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_prepare_promotes_only_selected_bundle_and_preserves_quarantine(mini_repo):
    package, comparison_bytes = _setup(mini_repo)
    plan = prepare_master_promotion(mini_repo, package, now=NOW)

    assert not any(path.exists() for path in plan.writes if "catalog.yaml" not in str(path))
    assert plan.provenance["source_mappings"][0]["candidate_source_id"] \
        == "candidate-source-adopted"
    assert plan.provenance["source_mappings"][0]["canonical_source_id"] \
        == "source-demo-book"
    assert plan.provenance["source_mappings"][0]["created"] is False
    assert plan.provenance["source_mappings"][0]["source_record_sha256"].startswith(
        "sha256:"
    )
    assert "candidate-source-unadopted" not in json.dumps(plan.provenance)
    updated_sources = {
        row["id"]: row for row in plan.updated_catalog["candidate_sources"]
    }
    assert updated_sources["candidate-source-adopted"]["planning_state"] == "promoted"
    assert updated_sources["candidate-source-adopted"]["canonical_source_id"] \
        == "source-demo-book"
    assert updated_sources["candidate-source-unadopted"]["planning_state"] == "selected"
    assert "canonical_source_id" not in updated_sources["candidate-source-unadopted"]
    assert plan.updated_catalog["candidate_modules"][1] == _catalog()["candidate_modules"][1]
    comparison = (
        mini_repo / "curriculum/quarantine/masters-planning/comparisons/"
        "candidate-comparison-preserved.yaml"
    )
    assert comparison.read_bytes() == comparison_bytes
    assert not (mini_repo / "curriculum/modules/module-future-demo").exists()


def test_prepare_creates_only_an_explicitly_adopted_new_canonical_source(mini_repo):
    _existing_package, _comparison = _setup(mini_repo)
    package = _new_source_package(mini_repo)
    plan = prepare_master_promotion(mini_repo, package, now=NOW)

    target = mini_repo / "sources/registry/future-demo.yaml"
    assert target in plan.writes
    registry = yaml.safe_load(plan.writes[target])
    assert [row["id"] for row in registry["sources"]] == [
        "source-future-official"
    ]
    assert "candidate-source-unadopted" not in plan.writes[target]
    assert plan.expected_revisions["source-future-official"] == 0
    mapping = plan.provenance["source_mappings"][0]
    assert mapping["created"] is True
    assert mapping["registry_target"] == "sources/registry/future-demo.yaml"
    assert mapping["source_record_sha256"].startswith("sha256:")
    assert not target.exists()


def test_promotion_refuses_stale_verification_and_unresolved_mapping(mini_repo):
    package, _comparison = _setup(mini_repo)
    package["verification"]["as_of"] = (NOW.date() - dt.timedelta(days=31)).isoformat()
    with pytest.raises(MastersPlanningError, match="is stale"):
        prepare_master_promotion(mini_repo, package, now=NOW)

    package, _comparison = _setup_fresh_again(mini_repo)
    package["adopted_sources"][0]["canonical_source_id"] = "source-missing"
    with pytest.raises(MastersPlanningError, match="unknown canonical source"):
        prepare_master_promotion(mini_repo, package, now=NOW)

    package, _comparison = _setup_fresh_again(mini_repo)
    package["score"] = 10
    with pytest.raises(MastersPlanningError, match="Additional properties"):
        prepare_master_promotion(mini_repo, package, now=NOW)


def _setup_fresh_again(root: Path) -> tuple[dict, bytes]:
    write_yaml(root / "curriculum/quarantine/masters-planning/catalog.yaml", _catalog())
    return _promotion_package(root), b"synthetic-approved-comparison\n"


def test_promotion_rejects_intermediate_symlink_into_quarantine(
    mini_repo, monkeypatch
):
    package, _comparison = _setup(mini_repo)
    sealed_directory = mini_repo / "curriculum/quarantine/masters-planning"
    sealed_audit = sealed_directory / "sealed-audit.md"
    sealed_audit.write_text(
        "## Local\n## Linked\n## Completeness\nMUST-NOT-BE-READ\n",
        encoding="utf-8",
    )
    alias = mini_repo / "operations/planning-alias"
    alias.parent.mkdir(parents=True, exist_ok=True)
    alias.symlink_to(sealed_directory, target_is_directory=True)
    package["module_plan"]["plan_contract"]["coverage_audit"] = (
        "operations/planning-alias/sealed-audit.md"
    )

    original_read_text = Path.read_text

    def guarded_read_text(path, *args, **kwargs):
        assert path.resolve() != sealed_audit.resolve(), "sealed audit was opened"
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded_read_text)
    with pytest.raises(MastersPlanningError, match="symlink component"):
        prepare_master_promotion(mini_repo, package, now=NOW)


def test_direct_live_promotion_refuses_but_check_emits_exact_no_write_plan(
    mini_repo, capsys
):
    package, comparison_bytes = _setup(mini_repo)
    package_hash = promotion_package_sha256(package)
    args = argparse.Namespace(
        root=str(mini_repo),
        module_id="module-future-demo",
        file=None,
        promotion=package,
        package_sha256=package_hash,
        approve=True,
        check=False,
        expected_snapshot=f"sha256:{canonical_fingerprint(mini_repo)}",
        expected_revision=[],
    )
    assert cmd_module_plan_import(args) == 2
    assert "GatewayEnvelopeV2" in capsys.readouterr().err
    assert not (mini_repo / "curriculum/modules/module-future-demo").exists()

    args.check = True
    args.package_sha256 = None
    assert cmd_module_plan_import(args) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["canonical_files_written"] == 0
    assert result["package_sha256"] == package_hash
    assert result["expected_revisions"]
    assert "curriculum/modules/module-future-demo/module.yaml" in result["affected_files"]
    assert "--- a/curriculum/quarantine/masters-planning/catalog.yaml" in result["diff"]
    assert result["provenance"]["preservation"]["originals_immutable"] is True
    assert not (mini_repo / "curriculum/modules/module-future-demo").exists()
    comparison = (
        mini_repo / "curriculum/quarantine/masters-planning/comparisons/"
        "candidate-comparison-preserved.yaml"
    )
    assert comparison.read_bytes() == comparison_bytes


def test_gateway_refuses_stale_revision_without_partial_promotion(
    mini_repo, repo_root, tmp_path
):
    package, comparison_bytes = _setup(mini_repo)
    plan = prepare_master_promotion(mini_repo, package, now=NOW)
    stale = dict(plan.expected_revisions)
    stale["candidate-module-future-demo"] = 1
    envelope = _gateway_envelope(mini_repo, package, revisions=stale)
    result = _run_gateway(repo_root, mini_repo, tmp_path / "stale.json", envelope)
    assert result.returncode == 3, result.stderr or result.stdout
    response = json.loads(result.stdout)
    assert response["error"]["code"] == "REVISION_CONFLICT"
    assert not (mini_repo / "curriculum/modules/module-future-demo").exists()
    assert not master_promotion_destination(mini_repo, package["id"]).exists()
    comparison = (
        mini_repo / "curriculum/quarantine/masters-planning/comparisons/"
        "candidate-comparison-preserved.yaml"
    )
    assert comparison.read_bytes() == comparison_bytes


def test_promotion_transaction_rolls_back_and_candidates_never_leak(
    mini_repo, monkeypatch, capsys
):
    _existing_package, comparison_bytes = _setup(mini_repo)
    package = _new_source_package(mini_repo)
    plan = prepare_master_promotion(mini_repo, package, now=NOW)
    before_catalog = (
        mini_repo / "curriculum/quarantine/masters-planning/catalog.yaml"
    ).read_bytes()
    before_manifest = json.dumps(build_manifest(load_repo(mini_repo), NOW.isoformat()))
    assert "candidate-module-" not in before_manifest
    assert "candidate-source-" not in before_manifest

    import learning_os.transactions as transactions

    original_write = transactions._atomic_write_bytes
    failure_path = master_promotion_destination(mini_repo, package["id"])

    def fail_provenance(path, content):
        if path == failure_path:
            raise TransactionFailure("injected promotion provenance failure")
        return original_write(path, content)

    monkeypatch.setattr(transactions, "_atomic_write_bytes", fail_provenance)
    intent = "sha256:" + "1" * 64
    context = GatewayRequestContext(
        request_id="request-master-promotion-rollback",
        idempotency_key="master-promotion-rollback-001",
        capability="module.plan.import",
        channel="codex",
        intent_sha256=intent,
        approval_kind="operator-approval",
        approval_subject_sha256=intent,
    )
    args = argparse.Namespace(
        root=str(mini_repo),
        module_id="module-future-demo",
        file=None,
        promotion=package,
        package_sha256=plan.package_sha256,
        approve=True,
        check=False,
        expected_snapshot=f"sha256:{canonical_fingerprint(mini_repo)}",
        expected_revision=[
            f"{artifact}={revision}"
            for artifact, revision in plan.expected_revisions.items()
        ],
    )
    with gateway_request_context(context):
        assert cmd_module_plan_import(args) == 2
    assert "injected promotion provenance failure" in capsys.readouterr().err
    rolled_back_module = mini_repo / "curriculum/modules/module-future-demo"
    assert not rolled_back_module.exists() or not any(
        path.is_file() or path.is_symlink() for path in rolled_back_module.rglob("*")
    )
    assert not (mini_repo / "sources/registry/future-demo.yaml").exists()
    assert not failure_path.exists()
    assert (
        mini_repo / "curriculum/quarantine/masters-planning/catalog.yaml"
    ).read_bytes() == before_catalog
    comparison = (
        mini_repo / "curriculum/quarantine/masters-planning/comparisons/"
        "candidate-comparison-preserved.yaml"
    )
    assert comparison.read_bytes() == comparison_bytes
    after_manifest = json.dumps(build_manifest(load_repo(mini_repo), NOW.isoformat()))
    assert "candidate-module-" not in after_manifest
    assert "candidate-source-" not in after_manifest


def test_gateway_promotes_one_bundle_and_manifest_contains_only_canonical_ids(
    mini_repo, repo_root, tmp_path
):
    _existing_package, comparison_bytes = _setup(mini_repo)
    package = _new_source_package(mini_repo)
    plan = prepare_master_promotion(mini_repo, package, now=NOW)
    envelope = _gateway_envelope(
        mini_repo,
        package,
        revisions=plan.expected_revisions,
    )
    applied = _run_gateway(repo_root, mini_repo, tmp_path / "promotion.json", envelope)
    assert applied.returncode == 0, applied.stderr or applied.stdout
    response = json.loads(applied.stdout)
    assert response["ok"] is True
    assert response["receipt_path"]

    promoted_catalog = yaml.safe_load((
        mini_repo / "curriculum/quarantine/masters-planning/catalog.yaml"
    ).read_text(encoding="utf-8"))
    modules = {row["id"]: row for row in promoted_catalog["candidate_modules"]}
    sources = {row["id"]: row for row in promoted_catalog["candidate_sources"]}
    assert modules["candidate-module-future-demo"]["planning_state"] == "promoted"
    assert modules["candidate-module-future-demo"]["promoted_module_id"] \
        == "module-future-demo"
    assert modules["candidate-module-other"]["planning_state"] == "shortlist"
    assert sources["candidate-source-adopted"]["canonical_source_id"] \
        == "source-future-official"
    assert sources["candidate-source-unadopted"]["planning_state"] == "selected"
    assert "canonical_source_id" not in sources["candidate-source-unadopted"]
    assert set(load_repo(mini_repo).sources) == {
        "source-demo-book",
        "source-future-official",
    }
    created_registry = yaml.safe_load((
        mini_repo / "sources/registry/future-demo.yaml"
    ).read_text(encoding="utf-8"))
    assert [row["id"] for row in created_registry["sources"]] == [
        "source-future-official"
    ]
    comparison = (
        mini_repo / "curriculum/quarantine/masters-planning/comparisons/"
        "candidate-comparison-preserved.yaml"
    )
    assert comparison.read_bytes() == comparison_bytes

    manifest = json.dumps(build_manifest(load_repo(mini_repo), NOW.isoformat()))
    assert "module-future-demo" in manifest
    assert "candidate-module-" not in manifest
    assert "candidate-source-" not in manifest
