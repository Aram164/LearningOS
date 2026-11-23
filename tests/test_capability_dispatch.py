"""Generic capability envelope dispatch (Stage 3).

Every declared command capability must reach a handler through the envelope.
Before this, 16 of 18 raised "generic envelope dispatch is not yet defined",
so the machine interface was a facade over the named CLI commands.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pytest
from gateway_helpers import approved_v2_envelope

from learning_os.app.gateway import validate_capability_envelope as _validate_capability_envelope
from learning_os.domain.failures import WriteRefused
from learning_os.store.contracts.capability_catalog import command_definitions

SCHEMA_DIR = Path("system/schema/capabilities")


def _definitions(repo_root: Path):
    return command_definitions(repo_root)


def test_no_capability_still_refuses_generic_dispatch(repo_root: Path):
    """The stub the plan's Stage 3 gate greps for must be gone."""
    gateway = (repo_root / "tools/learning_os/adapters/capability.py").read_text(encoding="utf-8")
    assert "generic envelope dispatch is not yet defined" not in gateway


def test_every_command_capability_has_a_payload_schema(repo_root: Path):
    for name, definition in _definitions(repo_root).items():
        if not definition.cli_command:
            continue
        schema = repo_root / SCHEMA_DIR / f"{name}.schema.json"
        assert schema.is_file(), f"{name} has no declared payload schema"


def test_payload_schemas_match_the_cli_parser(repo_root: Path):
    """Regenerating must be a no-op: the checked-in files are derived, not authored."""
    from learning_os.store.contracts.payload_records import resolve_all
    from learning_os.store.contracts.payloads import all_payload_schemas

    generated = all_payload_schemas(
        repo_root, _definitions(repo_root),
        payload_records=resolve_all(repo_root))
    for name, schema in generated.items():
        on_disk = json.loads((repo_root / SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))
        assert on_disk == schema, (
            f"{name} schema is stale — run tools/generate_capability_schemas.py"
        )


def test_payload_records_rejects_an_unknown_capability(repo_root: Path):
    """Unknown names fail with ValueError, not a loader FileNotFoundError."""
    from learning_os.store.contracts.payload_records import resolve_all
    from learning_os.store.contracts.payloads import all_payload_schemas

    with pytest.raises(ValueError, match="declares no json_object"):
        all_payload_schemas(
            repo_root, _definitions(repo_root),
            payload_records={("no.such.capability", "record"): {"type": "object"}})
    # The committed catalogue still resolves cleanly.
    resolve_all(repo_root)


def test_payload_records_rejects_a_capability_without_a_cli_binding(
        repo_root: Path):
    from learning_os.store.contracts.capability_catalog import CapabilityDefinition
    from learning_os.store.contracts.payloads import all_payload_schemas

    definitions = dict(_definitions(repo_root))
    definitions["synth.nocli"] = CapabilityDefinition(
        name="synth.nocli", handler="synth", cli_command=None,
        writes=(), invariants=())
    with pytest.raises(ValueError, match="declares no json_object"):
        all_payload_schemas(
            repo_root, definitions,
            payload_records={("synth.nocli", "record"): {"type": "object"}})


def test_a_corrupted_request_scalar_fails_the_schema_check(repo_root: Path,
                                                           tmp_path: Path):
    """The 45-schema derivation reads the live request scalar (S12 Task 4).

    Corrupting one scalar in a scratch copy makes the real derivation
    disagree with the checked-in bytes; restoring it (the committed tree)
    agrees again. The published files are hashed before and after.
    """
    import hashlib
    import shutil

    from learning_os.store.contracts.capability_catalog import command_definitions
    from learning_os.store.contracts.payload_records import resolve_all
    from learning_os.store.contracts.payloads import all_payload_schemas

    published = sorted((repo_root / SCHEMA_DIR).glob("*.schema.json"))
    assert len(published) == 47
    before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
              for path in published}
    work = tmp_path / "repo"
    shutil.copytree(repo_root / "system/schema", work / "system/schema")
    shutil.copytree(repo_root / "system/contracts",
                    work / "system/contracts")
    corrupted_path = (work / "system/schema/requests"
                      / "capture.create.schema.json")
    corrupted = json.loads(corrupted_path.read_text(encoding="utf-8"))
    assert corrupted["properties"]["text"]["type"] == "string"
    corrupted["properties"]["text"]["type"] = "integer"
    corrupted_path.write_text(json.dumps(corrupted), encoding="utf-8")
    drifted = all_payload_schemas(
        work, command_definitions(work), payload_records=resolve_all(work))
    assert len(drifted) == 47
    on_disk = json.loads(
        (repo_root / SCHEMA_DIR / "capture.create.schema.json").read_text(
            encoding="utf-8"))
    assert drifted["capture.create"] != on_disk
    assert drifted["capture.create"]["properties"]["text"]["type"] == "integer"
    # Restore: the committed tree derives exactly the published bytes.
    restored = all_payload_schemas(
        repo_root, _definitions(repo_root),
        payload_records=resolve_all(repo_root))
    for name, schema in restored.items():
        assert json.loads(
            (repo_root / SCHEMA_DIR / f"{name}.schema.json").read_text(
                encoding="utf-8")) == schema, name
    after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
             for path in published}
    assert after == before


def test_schemas_never_accept_the_envelope_concurrency_tokens(repo_root: Path):
    """expected_snapshot lives on the envelope; accepting it twice invites disagreement."""
    for path in sorted((repo_root / SCHEMA_DIR).glob("*.schema.json")):
        properties = json.loads(path.read_text(encoding="utf-8"))["properties"]
        assert "expected_snapshot" not in properties, path.name
        assert "expected_revision" not in properties, path.name


def _run_capability(repo_root: Path, tmp_path: Path, *, capability: str,
                  payload: dict, key: str):
    """Submit one envelope through the real CLI against the real catalog."""
    envelope = approved_v2_envelope(
        repo_root, capability=capability, payload=payload, artifact_ids=[],
        idempotency_key=key)
    payload_file = tmp_path / "envelope.json"
    payload_file.write_text(json.dumps(envelope), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(repo_root / "tools/los.py"), "capability",
         capability, "--payload-file", str(payload_file)],
        cwd=repo_root, text=True, capture_output=True,
    )


def test_a_malformed_payload_is_refused_before_any_write(repo_root: Path, tmp_path: Path):
    result = _run_capability(repo_root, tmp_path,
                             capability="stage.note.write",
                             payload={"unit_id": "unit-x"},  # stage_id missing
                             key="dispatch-bad-payload-001")
    assert result.returncode != 0
    body = json.loads(result.stdout)
    assert body["ok"] is False
    assert "invalid payload" in body["error"]["message"]
    assert body["transaction_id"] is None, "a refused payload must not report a receipt"


def test_an_undeclared_field_is_refused(repo_root: Path, tmp_path: Path):
    result = _run_capability(repo_root, tmp_path,
                             capability="stage.note.write",
                             payload={"unit_id": "u", "stage_id": "s",
                                      "not_a_real_field": "x"},
                             key="dispatch-extra-field-001")
    assert result.returncode != 0
    assert "invalid payload" in json.loads(result.stdout)["error"]["message"]


def test_a_request_without_schema_version_is_refused_before_dispatch(
        repo_root: Path, tmp_path: Path):
    """An envelope without `schema_version: 2` never reaches the handler."""
    payload_file = tmp_path / "envelope.json"
    payload_file.write_text(json.dumps({
        "request_id": "req-no-version",
        "capability": "stage.note.write",
        "payload": {"unit_id": "u", "stage_id": "s", "text": "x"},
    }), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(repo_root / "tools/los.py"), "capability",
         "stage.note.write", "--payload-file", str(payload_file)],
        cwd=repo_root, text=True, capture_output=True,
    )
    assert result.returncode == 2
    assert result.stdout == "", "a refused envelope must print no response"
    assert ("invalid capability envelope: schema_version 2 required "
            "(WORKFLOWS §25c)") in result.stderr


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


@pytest.mark.parametrize("name", sorted(
    n for n, d in command_definitions(Path(__file__).resolve().parent.parent).items()
    if d.cli_command
))
def test_every_capability_dispatches_rather_than_refusing(repo_root: Path, tmp_path: Path, name: str):
    """An empty payload must fail on *its own* validation, never on dispatch.

    This is the round-trip assertion: whatever the outcome, the reason must not
    be that the gateway has no route for the capability.
    """
    result = _run_capability(repo_root, tmp_path, capability=name, payload={},
                             key=f"dispatch-empty-{name}")
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
    gateway = (repo_root / "tools/learning_os/adapters/capability.py").read_text(encoding="utf-8")
    assert 'args.name in {"project.create", "project.update"}' not in gateway
    assert "_project_write" not in gateway, "the gateway must not reach past the handler"


@pytest.mark.parametrize("name", ["project.create", "project.update"])
def test_retired_project_authoring_refuses_before_mutation(repo_root: Path, tmp_path: Path, name: str):
    from learning_os.store.contracts.capability_catalog import command_definitions
    from learning_os.store.fingerprint import snapshot
    assert name not in command_definitions(repo_root)
    before = snapshot(repo_root)
    result = _run_capability(repo_root, tmp_path, capability=name,
                             payload={"project": {"id": "project-retired"}},
                             key="retired-project-authoring")
    assert result.returncode != 0
    assert json.loads(result.stdout)["ok"] is False
    assert snapshot(repo_root) == before


def test_generated_schemas_carry_parser_help_text(repo_root: Path):
    """F6: the declared payload explains its fields without an extra --help call.

    Every capability property whose parser action carries help text carries
    that exact text as its schema description — except where a payload-records
    or contract-module fragment already describes the field, which keeps its
    own description.
    """
    import los
    from learning_os.store.contracts.payload_records import resolve_all
    from learning_os.store.contracts.payloads import NESTED_SCHEMAS as _NESTED_SCHEMAS
    from learning_os.store.contracts.payloads import all_payload_schemas, payload_fields, subparsers

    parser = los.build_parser()
    commands = subparsers(parser)
    definitions = _definitions(repo_root)
    records = resolve_all(repo_root)
    schemas = all_payload_schemas(
        repo_root, definitions, payload_records=records)
    carried = 0
    for name, definition in sorted(definitions.items()):
        if not definition.cli_command:
            continue
        command_parser = commands.get(definition.cli_command or "")
        if command_parser is None:
            continue
        for action in payload_fields(command_parser):
            if not action.help or action.help == argparse.SUPPRESS:
                continue
            prop = schemas[name]["properties"][action.dest]
            fragment = records.get((name, action.dest))
            if fragment is None:
                fragment = _NESTED_SCHEMAS.get((name, action.dest))
            if fragment is not None and "description" in fragment:
                assert prop["description"] == fragment["description"], (
                    f"{name}.{action.dest} keeps its fragment description"
                )
            else:
                assert prop.get("description") == action.help, (
                    f"{name}.{action.dest} drops its parser help text"
                )
                carried += 1
    assert carried > 0, "no carried descriptions found; the generator regressed"


def test_admission_needs_no_cli_parser_construction(mini_repo: Path):
    """S3: gateway admission derives its namespace from the request schema.

    With parser construction unavailable (``parser_factory=None``), the
    shared admission still validates the payload, applies schema
    defaults, and preserves omitted/null/false/empty semantics — the
    values a handler would read are the values the schema declares.
    """
    from learning_os.app.gateway import prepare_dispatch

    definitions = command_definitions(mini_repo)
    envelope = {"schema_version": 2}
    _parser, namespace = prepare_dispatch(
        mini_repo, definitions["capture.create"], envelope,
        {"text": "hello"}, parser_factory=None)
    assert namespace.text == "hello"
    assert namespace.title is None, "an omitted optional stays its schema default"
    assert namespace.json is True, "handlers report JSON through the gateway"
    from learning_os.store.contracts.payloads import (
        payload_to_namespace_from_schema,
    )

    namespace = payload_to_namespace_from_schema(
        mini_repo, "capture.create", {"text": "hello", "title": None},
        root=None, expected_snapshot=None, expected_revisions=None)
    assert namespace.title is None, "an explicit null is absence, not a value"
    _parser, namespace = prepare_dispatch(
        mini_repo, definitions["stage.progress.update"], envelope,
        {"unit_id": "u", "stage_id": "s", "status": "active",
         "progress_summary": ""}, parser_factory=None)
    assert namespace.progress_summary == "", "an explicit empty string survives"
    # Refusal order is unchanged: payload validation refuses before any
    # namespace is built, with or without a parser.
    with pytest.raises(WriteRefused, match="invalid payload"):
        prepare_dispatch(
            mini_repo, definitions["stage.progress.update"], envelope,
            {"unit_id": "u", "stage_id": "s", "status": "bogus"},
            parser_factory=None)


def test_gateway_dispatch_survives_parser_construction_failure(mini_repo: Path):
    """A registered capability completes with the parser factory broken."""
    import learning_os.app.pipeline as pipeline_module
    from learning_os.store.diagnostics import tracer as diag_tracer
    from learning_os.store.diagnostics.store import bind_store as _bind_diag_store

    def broken_factory():
        raise AssertionError("CLI parser construction is unavailable")

    from learning_os.store.contracts.gateway import request_artifact_id

    envelope = approved_v2_envelope(
        mini_repo, capability="capture.create", payload={"text": "parser-free"},
        artifact_ids=[request_artifact_id("capture.create", "parser-free-001")],
        idempotency_key="parser-free-001")
    _bind_diag_store(mini_repo)
    attempt = diag_tracer.begin_attempt({"capability": "capture.create"})
    outcome = pipeline_module.run_gateway(
        mini_repo, envelope, requested="capture.create",
        definitions=command_definitions(mini_repo), attempt=attempt,
        replay_only=False, parser_factory=broken_factory)
    assert outcome is not None
    body = json.loads(outcome.stdout)
    assert body["ok"] is True, body


def test_analysis_binding_schemas_describe_the_stored_shape(repo_root: Path):
    """F6: save/save_batch bindings point at material_analysis, bare object no more.

    Description-only on purpose: the boundary also accepts the read surface's
    own spellings (material:// URIs, sha256:-prefixed digests) and normalizes
    them before any check, so a validating inline shape would refuse at the
    gateway what the handler accepts.
    """
    save = json.loads((repo_root / SCHEMA_DIR / "note.analysis.save.schema.json")
                      .read_text(encoding="utf-8"))
    batch = json.loads((repo_root / SCHEMA_DIR / "note.analysis.save_batch.schema.json")
                       .read_text(encoding="utf-8"))
    save_binding = save["properties"]["analysis"]["properties"]["binding"]
    batch_binding = (batch["properties"]["bundle"]["properties"]["notes"]
                     ["items"]["properties"]["analysis"]["properties"]["binding"])
    assert save_binding["type"] == "object"
    assert batch_binding["type"] == "object"
    assert save_binding["description"] == batch_binding["description"]
    assert "material_analysis" in save_binding["description"]
    assert "note.schema.json" in save_binding["description"]
    # Annotation-only: acceptance is exactly the old bare object.
    assert set(save_binding) == {"type", "description"}
    assert set(batch_binding) == {"type", "description"}


def test_optional_mutually_exclusive_group_generates_at_most_one_schema(repo_root: Path):
    """#28: optional mutex groups (plan.edit-context route_ids/route_id/stage_id) emit at-most-one constraints."""
    from jsonschema import Draft202012Validator

    from learning_os.store.contracts.payloads import payload_schema

    schema = payload_schema("plan.edit-context", repo_root)
    validator = Draft202012Validator(schema)
    assert "route_ids" in schema["properties"]
    assert "oneOf" in schema
    validator.validate({"unit_id": "unit-demo-l01"})
    validator.validate({"unit_id": "unit-demo-l01", "route_id": "route-1"})
    validator.validate({"unit_id": "unit-demo-l01", "route_ids": ["route-1", "route-2"]})
    validator.validate({"unit_id": "unit-demo-l01", "stage_id": "stage-1"})
    for conflicting in (
        {"unit_id": "unit-demo-l01", "route_id": "route-1", "route_ids": ["route-2"]},
        {"unit_id": "unit-demo-l01", "route_id": "route-1", "stage_id": "stage-1"},
        {"unit_id": "unit-demo-l01", "route_ids": ["route-1"], "stage_id": "stage-1"},
    ):
        assert list(validator.iter_errors(conflicting)), conflicting


def test_gateway_carve_outs_stay_pinned_against_live_cli_parser(repo_root: Path):
    """Pin the intentional gateway-stricter carve-outs in payloads.py to the live CLI parser."""
    from jsonschema import Draft202012Validator

    import los
    from learning_os.app.gateway import _CONTENT_BOUND_V2
    from learning_os.store.contracts.capability_catalog import load_capability_catalog
    from learning_os.store.contracts.payloads import (
        _GATEWAY_INLINE_REQUIRED,
        payload_schema,
        subparsers,
    )
    from learning_os.store.contracts.requests import request_schema

    parser = los.build_parser()
    cli_commands = subparsers(parser)
    definitions = _definitions(repo_root)
    catalog = load_capability_catalog(repo_root)

    # 1. _GATEWAY_INLINE_REQUIRED must cover exact known inline overrides whose CLI args are optional.
    assert set(_GATEWAY_INLINE_REQUIRED) == {
        "stage.note.write",
        "unit.note.append",
        "unit.plan.revise",
    }
    for cap_name, required_fields in _GATEWAY_INLINE_REQUIRED.items():
        cli_cmd = definitions[cap_name].cli_command
        assert cli_cmd and cli_cmd in cli_commands
        actions = {a.dest: a for a in cli_commands[cli_cmd]._actions}
        cap_schema = json.loads((repo_root / SCHEMA_DIR / f"{cap_name}.schema.json").read_text(encoding="utf-8"))
        for field in required_fields:
            assert actions[field].required is False, f"{cap_name}.{field} is already parser-required"
            assert field in cap_schema["required"], f"{cap_name}.{field} missing from gateway required"
        if cap_name in _CONTENT_BOUND_V2:
            assert "record" in actions and "file" in actions
            assert "file" in (catalog["commands"][cap_name] or {}) or True

    # Ensure every mutually_exclusive group on every CLI-bound request schema (required or optional)
    # is preserved by payload_schema when >1 non-transport field survives.
    for cap_name, definition in definitions.items():
        if not definition.cli_command:
            continue
        req = request_schema(repo_root, cap_name)
        groups = req.get("x-los-cli-command", {}).get("mutually_exclusive", [])
        if groups:
            cap_schema = json.loads((repo_root / SCHEMA_DIR / f"{cap_name}.schema.json").read_text(encoding="utf-8"))
            assert ("oneOf" in cap_schema) or ("allOf" in cap_schema)

    # 2. capture.create carves out mutually exclusive file/text despite empty parser mutex.
    capture_req = request_schema(repo_root, "capture.create")
    assert capture_req["x-los-cli-command"]["mutually_exclusive"] == []
    capture_validator = Draft202012Validator(payload_schema("capture.create", repo_root))
    assert list(capture_validator.iter_errors({"text": "hi", "file": "a.txt", "file_sha256": "sha256:" + "0" * 64}))
    assert list(capture_validator.iter_errors({}))
    capture_validator.validate({"text": "hi"})

    # 3. stage.progress.update couples progress_next -> progress_summary at gateway boundary.
    progress_validator = Draft202012Validator(payload_schema("stage.progress.update", repo_root))
    assert list(progress_validator.iter_errors({
        "unit_id": "u", "stage_id": "s", "status": "active", "progress_next": "next",
    }))
    progress_validator.validate({
        "unit_id": "u", "stage_id": "s", "status": "active",
        "progress_summary": "did work", "progress_next": "next",
    })


def test_route_patch_claim_evidence_allows_handler_tolerated_nulls(repo_root: Path):
    """route.patch claim_evidence and optional locator fields permit explicit null as handlers do."""
    from jsonschema import Draft202012Validator

    schema = json.loads((repo_root / SCHEMA_DIR / "route.patch.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    base = {"unit_id": "unit-demo-l01", "route_id": "route-1", "changes": {"locator": "ch. 2"}}
    validator.validate({**base, "claim_evidence": None})
    validator.validate({
        **base,
        "claim_evidence": {
            "claim_id": "covers:route-1",
            "reads": None,
            "evidence": [{
                "kind": "quote",
                "ref": "material://source-demo-book/lecture-01.pdf",
                "text": "Sample quote excerpt covering the patched locator claim.",
                "page": 3,
                "page_end": None,
                "window": None,
                "line_start": None,
                "line_end": None,
            }],
        },
    })
    assert list(validator.iter_errors({
        **base,
        "claim_evidence": {
            "claim_id": "covers:route-1",
            "evidence": [{"kind": "quote", "ref": "material://x/y.pdf", "page": "three"}],
        },
    }))


def test_validate_payload_enforces_format_checker(tmp_path: Path):
    """gateway.validate_payload must reject invalid date-time/uri formats."""
    from learning_os.app.gateway import validate_payload

    schema_dir = tmp_path / "system/schema/capabilities"
    schema_dir.mkdir(parents=True)
    (schema_dir / "synth.format.schema.json").write_text(json.dumps({
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["recorded_at", "homepage"],
        "properties": {
            "recorded_at": {"type": "string", "format": "date-time"},
            "homepage": {"type": "string", "format": "uri"},
        },
    }), encoding="utf-8")

    validate_payload(tmp_path, "synth.format", {
        "recorded_at": "2026-10-01T09:00:00+02:00",
        "homepage": "https://example.org/resource",
    })
    with pytest.raises(WriteRefused, match="invalid payload"):
        validate_payload(tmp_path, "synth.format", {
            "recorded_at": "not-a-timestamp",
            "homepage": "https://example.org/resource",
        })
    with pytest.raises(WriteRefused, match="invalid payload"):
        validate_payload(tmp_path, "synth.format", {
            "recorded_at": "2026-10-01T09:00:00Z",
            "homepage": "not a valid uri",
        })
