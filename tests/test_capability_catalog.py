from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from learning_os.contracts.capability_catalog import (
    CapabilityCatalogError,
    command_definitions,
    domain_capability_definitions,
    query_definitions,
)


def test_every_public_command_is_bound_to_its_declared_cli_handler(repo_root: Path):
    import los
    from learning_os.contracts.payloads import subparsers

    parsers = subparsers(los.build_parser())
    definitions = command_definitions(repo_root)
    assert definitions, "the producer catalogue must declare public commands"
    assert len({definition.cli_command for definition in definitions.values()}) == len(definitions)
    for definition in definitions.values():
        parser = parsers.get(definition.cli_command or "")
        assert parser is not None, f"{definition.name} has no executable CLI route"
        handler = parser.get_default("func")
        assert handler is not None
        assert handler.__name__ == f"cmd_{definition.handler}"


def test_job_query_declares_its_producer_owned_schema(repo_root: Path):
    definition = query_definitions(repo_root)["job.dashboard"]
    assert definition.result == "job-dashboard-v2"
    assert definition.schema == "system/schema/job-dashboard.schema.json"
    assert (repo_root / definition.schema).is_file()


def test_ai_action_domain_capabilities_are_loaded_by_the_validated_catalogue(repo_root: Path):
    definitions = domain_capability_definitions(repo_root)
    assert definitions["garden.add-transcription"].writes == (
        "knowledge/garden/transcriptions/",
    )
    assert definitions["garden.update"].allowed_fields == ("title", "state")


def test_a_versioned_query_cannot_skip_its_schema(mini_repo: Path):
    import yaml

    path = mini_repo / "system/contracts/capabilities.yaml"
    catalogue = yaml.safe_load(path.read_text(encoding="utf-8"))
    catalogue["queries"]["job.dashboard"].pop("schema")
    path.write_text(yaml.safe_dump(catalogue, sort_keys=False), encoding="utf-8")
    with pytest.raises(CapabilityCatalogError, match="no producer-owned schema"):
        query_definitions(mini_repo)


def test_a_domain_capability_cannot_skip_its_write_scope(mini_repo: Path):
    import yaml

    path = mini_repo / "system/contracts/capabilities.yaml"
    catalogue = yaml.safe_load(path.read_text(encoding="utf-8"))
    catalogue["domain_capabilities"]["garden.update"]["writes"] = []
    path.write_text(yaml.safe_dump(catalogue, sort_keys=False), encoding="utf-8")
    with pytest.raises(CapabilityCatalogError, match="writes must not be empty"):
        domain_capability_definitions(mini_repo)


def test_unknown_generic_capability_fails_before_payload_read(repo_root: Path):
    result = subprocess.run(
        [sys.executable, str(repo_root / "tools/los.py"), "capability", "unknown.write", "--payload-file", "/does/not/exist"],
        cwd=repo_root, text=True, capture_output=True,
    )
    assert result.returncode == 2
    assert "unknown or non-public capability" in result.stderr
    assert "no such file" not in result.stderr


def _project(project_id: str) -> dict:
    return {
        "schema_version": 1, "id": project_id, "type": "project", "revision": 0,
        "title": project_id.replace("-", " ").title(), "project_type": "other",
        "status": "planned", "root_uri": "github://Aram164/LearningOS",
        "objective": "Exercise the declared project capability.", "milestone_ids": [],
        "linked_module_ids": [], "unit_ids": [], "workspace_ids": [],
        "thematic_group_ids": [],
        "boundaries": {"confidentiality": "private", "external_code_access": "none"},
        "structure": {"kind": "none", "nodes": []}, "files": [], "decisions": [],
    }


def test_project_capability_envelope_round_trips(mini_repo: Path, repo_root: Path, tmp_path: Path):
    envelope = {
        "request_id": "request-project-create",
        "capability": "project.create",
        "payload": {"project": _project("project-envelope-demo")},
        "expected_revisions": {"project-envelope-demo": 0},
    }
    request = tmp_path / "request.json"
    request.write_text(json.dumps(envelope), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(repo_root / "tools/los.py"), "--root", str(mini_repo),
         "capability", "project.create", "--payload-file", str(request)],
        cwd=repo_root, text=True, capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    response = json.loads(result.stdout)
    assert response["request_id"] == envelope["request_id"]
    assert response["capability"] == "project.create"
    assert response["ok"] is True
    assert response["transaction_id"]
    assert response["receipt_path"].startswith("operations/transactions/")
    assert (mini_repo / "projects/registry/project-envelope-demo.yaml").is_file()
