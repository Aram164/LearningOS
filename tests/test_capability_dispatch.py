"""Generic capability envelope dispatch (Stage 3).

Every declared command capability must reach a handler through the envelope.
Before this, 16 of 18 raised "generic envelope dispatch is not yet defined",
so the machine interface was a facade over the named CLI commands.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from learning_os.contracts.capability_catalog import command_definitions
from learning_os.commands.capability import _dispatch, _validate_capability_envelope
from learning_os.commands.support import WriteRefused

SCHEMA_DIR = Path("system/schema/capabilities")


def _definitions(repo_root: Path):
    return command_definitions(repo_root)


def test_no_capability_still_refuses_generic_dispatch(repo_root: Path):
    """The stub the plan's Stage 3 gate greps for must be gone."""
    gateway = (repo_root / "tools/learning_os/commands/capability.py").read_text(encoding="utf-8")
    assert "generic envelope dispatch is not yet defined" not in gateway


def test_every_command_capability_has_a_payload_schema(repo_root: Path):
    for name, definition in _definitions(repo_root).items():
        if not definition.cli_command:
            continue
        schema = repo_root / SCHEMA_DIR / f"{name}.schema.json"
        assert schema.is_file(), f"{name} has no declared payload schema"


def test_payload_schemas_match_the_cli_parser(repo_root: Path):
    """Regenerating must be a no-op: the checked-in files are derived, not authored."""
    import los
    from learning_os.contracts.payloads import all_payload_schemas

    generated = all_payload_schemas(los.build_parser(), _definitions(repo_root))
    for name, schema in generated.items():
        on_disk = json.loads((repo_root / SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))
        assert on_disk == schema, (
            f"{name} schema is stale — run tools/generate_capability_schemas.py"
        )


def test_schemas_never_accept_the_envelope_concurrency_tokens(repo_root: Path):
    """expected_snapshot lives on the envelope; accepting it twice invites disagreement."""
    for path in sorted((repo_root / SCHEMA_DIR).glob("*.schema.json")):
        properties = json.loads(path.read_text(encoding="utf-8"))["properties"]
        assert "expected_snapshot" not in properties, path.name
        assert "expected_revision" not in properties, path.name


def _run_capability(repo_root: Path, tmp_path: Path, envelope: dict):
    payload_file = tmp_path / "envelope.json"
    payload_file.write_text(json.dumps(envelope), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(repo_root / "tools/los.py"), "capability",
         envelope["capability"], "--payload-file", str(payload_file)],
        cwd=repo_root, text=True, capture_output=True,
    )


def test_a_malformed_payload_is_refused_before_any_write(repo_root: Path, tmp_path: Path):
    result = _run_capability(repo_root, tmp_path, {
        "request_id": "req-bad-payload",
        "capability": "stage.note.write",
        "payload": {"unit_id": "unit-x"},          # stage_id missing
    })
    assert result.returncode != 0
    body = json.loads(result.stdout)
    assert body["ok"] is False
    assert "invalid payload" in body["error"]
    assert body["transaction_id"] is None, "a refused payload must not report a receipt"


def test_an_undeclared_field_is_refused(repo_root: Path, tmp_path: Path):
    result = _run_capability(repo_root, tmp_path, {
        "request_id": "req-extra-field",
        "capability": "stage.note.write",
        "payload": {"unit_id": "u", "stage_id": "s", "not_a_real_field": "x"},
    })
    assert result.returncode != 0
    assert "invalid payload" in json.loads(result.stdout)["error"]


def test_a_result_envelope_cannot_be_dispatched_as_a_request(repo_root: Path):
    with pytest.raises(WriteRefused, match="invalid capability envelope"):
        _validate_capability_envelope(repo_root, {
            "request_id": "req-result-as-request",
            "capability": "capture.create",
            "ok": True,
            "transaction_id": None,
            "receipt_path": None,
            "result": {},
            "error": None,
        }, kind="request")


@pytest.mark.parametrize("printed", ["plain success", "[]", ""])
def test_non_object_handler_output_is_a_hard_gateway_failure(
        mini_repo: Path, monkeypatch: pytest.MonkeyPatch, printed: str):
    import los

    def malformed_success(_args):
        if printed:
            print(printed)
        return 0

    monkeypatch.setattr(los, "cmd_capture", malformed_success)
    definition = command_definitions(mini_repo)["capture.create"]
    with pytest.raises(WriteRefused, match="reported success"):
        _dispatch(
            mini_repo,
            definition,
            {"request_id": "req-malformed-success", "capability": definition.name},
            {"text": "capture me"},
        )


@pytest.mark.parametrize("name", sorted(
    n for n, d in command_definitions(Path(__file__).resolve().parent.parent).items()
    if d.cli_command
))
def test_every_capability_dispatches_rather_than_refusing(repo_root: Path, tmp_path: Path, name: str):
    """An empty payload must fail on *its own* validation, never on dispatch.

    This is the round-trip assertion: whatever the outcome, the reason must not
    be that the gateway has no route for the capability.
    """
    result = _run_capability(repo_root, tmp_path, {
        "request_id": f"req-{name}", "capability": name, "payload": {},
    })
    combined = result.stdout + result.stderr
    assert "not yet defined" not in combined, f"{name} is still a facade"
    assert "declares no CLI command" not in combined, f"{name} has no route"
    assert "has no bound handler" not in combined, f"{name} has no handler"


# --------------------------------------------------------------------------
# The project capabilities had a gateway-only branch until 2026-08-08: it
# accepted `{"project": {...}}`, a shape no schema declared, and skipped
# `_validate_payload` to do so. An agent obeying the published contract was
# refused; an agent sending the undeclared shape was obeyed. These tests hold
# the boundary to the contract it publishes.
# --------------------------------------------------------------------------

def test_the_gateway_has_no_capability_special_cases(repo_root: Path):
    gateway = (repo_root / "tools/learning_os/commands/capability.py").read_text(encoding="utf-8")
    assert 'args.name in {"project.create", "project.update"}' not in gateway
    assert "_project_write" not in gateway, "the gateway must not reach past the handler"


@pytest.mark.parametrize("name", ["project.create", "project.update"])
def test_project_payload_shape_is_declared(repo_root: Path, name: str):
    """The inline object the gateway accepts is in the schema, not just the code."""
    schema = json.loads((repo_root / SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))
    assert schema["properties"]["project"] == {"type": "object"}
    assert schema["oneOf"] == [{"required": ["file"]}, {"required": ["project"]}], (
        "exactly one record source must be required, and the schema must say so"
    )


def test_project_create_without_a_record_source_is_refused(repo_root: Path, tmp_path: Path):
    result = _run_capability(repo_root, tmp_path, {
        "request_id": "req-project-no-source",
        "capability": "project.create",
        "payload": {},
    })
    assert result.returncode != 0
    assert "invalid payload" in json.loads(result.stdout)["error"]


def test_project_create_rejects_an_undeclared_field(repo_root: Path, tmp_path: Path):
    """The regression proper: payload validation must not be skipped here."""
    result = _run_capability(repo_root, tmp_path, {
        "request_id": "req-project-extra-field",
        "capability": "project.create",
        "payload": {"project": {"id": "project-x", "type": "project"},
                    "not_a_real_field": "x"},
    })
    assert result.returncode != 0
    assert "invalid payload" in json.loads(result.stdout)["error"]


def test_project_create_refuses_both_record_sources_at_once(repo_root: Path, tmp_path: Path):
    result = _run_capability(repo_root, tmp_path, {
        "request_id": "req-project-two-sources",
        "capability": "project.create",
        "payload": {"file": "somewhere.yaml", "project": {"id": "project-x", "type": "project"}},
    })
    assert result.returncode != 0
    assert "invalid payload" in json.loads(result.stdout)["error"]
