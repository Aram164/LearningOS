from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from gateway_helpers import approved_v2_call, file_sha256

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


def test_every_v2_external_file_input_is_content_bound_or_inline_only(
    repo_root: Path,
):
    """A newly exposed file path cannot silently approve only its pathname."""
    import los
    from learning_os.commands.capability import _CONTENT_BOUND_V2, _FILE_INPUTS_V2
    from learning_os.contracts.payloads import payload_fields, subparsers

    external_fields = {"file", "items_file", "attachment"}
    parsers = subparsers(los.build_parser())
    for name, definition in command_definitions(repo_root).items():
        parser = parsers[definition.cli_command]
        fields = {action.dest for action in payload_fields(parser)}
        file_fields = fields & external_fields
        if not file_fields:
            assert name not in _FILE_INPUTS_V2
            continue
        if name in _CONTENT_BOUND_V2:
            assert name not in _FILE_INPUTS_V2
            continue

        bindings = {
            field: digest_field
            for field, digest_field, _repeated in _FILE_INPUTS_V2.get(name, ())
        }
        assert set(bindings) == file_fields, (
            f"{name} exposes external file inputs without a V2 byte binding"
        )
        schema = json.loads(
            (repo_root / "system/schema/capabilities" / f"{name}.schema.json")
            .read_text(encoding="utf-8")
        )
        dependencies = schema.get("dependentRequired", {})
        for field, digest_field in bindings.items():
            assert digest_field in fields
            assert dependencies[field] == [digest_field]
            assert dependencies[digest_field] == [field]


def test_every_path_backed_handler_consumes_the_bytes_its_hash_check_read(
    repo_root: Path,
):
    """Guard against regressing to hash(path), then reopen(path)."""
    import inspect

    import los
    from learning_os.commands import project as project_commands
    from learning_os.commands.capability import _FILE_INPUTS_V2
    from learning_os.contracts.payloads import subparsers

    parsers = subparsers(los.build_parser())
    definitions = command_definitions(repo_root)
    for name in _FILE_INPUTS_V2:
        handler = parsers[definitions[name].cli_command].get_default("func")
        source = inspect.getsource(handler)
        if name in {"project.create", "project.update"}:
            source += inspect.getsource(project_commands._project_record)
        assert (
            "_read_content_bound_file" in source
            or "_read_structured_file" in source
        ), f"{name} does not consume bytes through the single-read content guard"


def test_health_query_declares_its_producer_owned_schema(repo_root: Path):
    definition = query_definitions(repo_root)["health.report"]
    assert definition.result == "health-report-v1"
    assert definition.schema == "system/schema/health-report.schema.json"
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
    catalogue["queries"]["health.report"].pop("schema")
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


def test_declared_command_rejects_an_absolute_write_scope(mini_repo: Path):
    import yaml

    path = mini_repo / "system/contracts/capabilities.yaml"
    catalogue = yaml.safe_load(path.read_text(encoding="utf-8"))
    catalogue["commands"]["capture.create"]["writes"].append("/tmp/escape/**")
    path.write_text(yaml.safe_dump(catalogue, sort_keys=False), encoding="utf-8")
    with pytest.raises(CapabilityCatalogError, match="invalid write scope"):
        command_definitions(mini_repo)


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


def test_project_capability_envelope_round_trips(mini_repo: Path):
    result = approved_v2_call(
        mini_repo,
        capability="project.create",
        payload={"project": _project("project-envelope-demo")},
        artifact_ids=["project-envelope-demo"],
        idempotency_key="project-create-round-trip-001",
    )
    assert result.returncode == 0, result.stderr
    response = json.loads(result.stdout)
    assert response["schema_version"] == 2
    assert response["request_id"] == "request-project-create-round-trip-001"
    assert response["capability"] == "project.create"
    assert response["ok"] is True
    assert response["transaction_id"]
    assert response["receipt_path"].startswith("operations/transactions/")
    assert (mini_repo / "projects/registry/project-envelope-demo.yaml").is_file()


def test_project_file_capability_consumes_the_approved_bytes(
    mini_repo: Path, tmp_path: Path
):
    import yaml

    source = tmp_path / "project-file-demo.yaml"
    source.write_text(
        yaml.safe_dump(_project("project-file-demo"), sort_keys=False),
        encoding="utf-8",
    )
    result = approved_v2_call(
        mini_repo,
        capability="project.create",
        payload={"file": str(source), "file_sha256": file_sha256(source)},
        artifact_ids=["project-file-demo"],
        idempotency_key="project-file-create-001",
    )
    assert result.returncode == 0, result.stderr
    assert (mini_repo / "projects/registry/project-file-demo.yaml").is_file()
