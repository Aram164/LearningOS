from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

from learning_os.contracts.capability_catalog import command_definitions


GATEWAY = "tools/learning_os/commands/capability.py"


def _handler_mapping(repo_root: Path) -> dict[str, str]:
    """Read the gateway's handler table without importing the CLI.

    Parsed rather than imported so the assertion stays a statement about the
    declared catalogue, not about whatever a live import happens to produce.
    """
    tree = ast.parse((repo_root / GATEWAY).read_text(encoding="utf-8"))
    fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_capability_handlers")
    returned = next(node.value for node in ast.walk(fn) if isinstance(node, ast.Return))
    return ast.literal_eval(returned)


def test_public_capability_catalog_matches_gateway_handlers(repo_root: Path):
    declared = {name: row.handler for name, row in command_definitions(repo_root).items()}
    assert declared == _handler_mapping(repo_root)


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
