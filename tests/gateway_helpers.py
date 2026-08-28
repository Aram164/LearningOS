"""Small GatewayEnvelopeV2 driver shared by canonical-write tests."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from learning_os.contracts.capability_catalog import command_definitions
from learning_os.contracts.gateway import intent_sha256
from learning_os.contracts.payloads import payload_fields, subparsers
from learning_os.fingerprint import canonical_fingerprint
from learning_os.transactions import artifact_revision

LOS = Path(__file__).resolve().parent.parent / "tools" / "los.py"


def file_sha256(path: Path) -> str:
    """Return the content token required by V2 path-backed payload fields."""
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def request_artifact_id(capability: str, idempotency_key: str) -> str:
    prefixes = {
        "capture.create": "capture-request",
        "garden.seed.create": "garden-request",
    }
    try:
        prefix = prefixes[capability]
    except KeyError as exc:
        raise ValueError(f"{capability} does not use request-scoped artifacts") from exc
    return f"{prefix}:{idempotency_key}"


def approved_v2_envelope(
    root: Path,
    *,
    capability: str,
    payload: dict,
    artifact_ids: list[str] | tuple[str, ...],
    idempotency_key: str,
    expected_snapshot: str | None = None,
) -> dict:
    envelope = {
        "schema_version": 2,
        "request_id": f"request-{idempotency_key}",
        "idempotency_key": idempotency_key,
        "capability": capability,
        "channel": "operator",
        "expected_snapshot": (
            expected_snapshot
            if expected_snapshot is not None
            else f"sha256:{canonical_fingerprint(root)}"
        ),
        "expected_revisions": {
            artifact_id: artifact_revision(root, artifact_id)
            for artifact_id in artifact_ids
        },
        "approval": {
            "kind": "operator-approval",
            "subject_sha256": "sha256:" + "0" * 64,
        },
        "payload": payload,
    }
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    return envelope


def run_v2_capability(root: Path, envelope: dict):
    return subprocess.run(
        [
            sys.executable,
            str(LOS),
            "--root",
            str(root),
            "capability",
            envelope["capability"],
            "--payload-file",
            "-",
        ],
        input=json.dumps(envelope),
        capture_output=True,
        text=True,
        timeout=120,
    )


def approved_v2_call(
    root: Path,
    *,
    capability: str,
    payload: dict,
    artifact_ids: list[str] | tuple[str, ...],
    idempotency_key: str,
    expected_snapshot: str | None = None,
):
    return run_v2_capability(
        root,
        approved_v2_envelope(
            root,
            capability=capability,
            payload=payload,
            artifact_ids=artifact_ids,
            idempotency_key=idempotency_key,
            expected_snapshot=expected_snapshot,
        ),
    )


def approved_v2_cli(
    root: Path,
    *cli_args: str,
    artifact_ids: list[str] | tuple[str, ...],
    idempotency_key: str,
    expected_snapshot: str | None = None,
):
    """Exercise one normal CLI-shaped gesture through its declared V2 gateway.

    Tests keep their readable command-line examples while the production rule
    remains absolute: the handler is reached only after a content-bound V2
    envelope.  Approval flags and concurrency flags are envelope authority and
    therefore never duplicated in the payload.
    """
    import los

    if not cli_args:
        raise ValueError("a CLI command is required")
    command = cli_args[0]
    parser = los.build_parser()
    commands = subparsers(parser)
    command_parser = commands.get(command)
    if command_parser is None:
        raise ValueError(f"unknown CLI command: {command}")
    parsed = parser.parse_args(["--root", str(root), *cli_args])
    payload: dict = {}
    for action in payload_fields(command_parser):
        if action.dest == "approve":
            continue
        value = getattr(parsed, action.dest)
        if action.option_strings and value == action.default:
            continue
        payload[action.dest] = value

    matches = [
        definition.name
        for definition in command_definitions(root).values()
        if definition.cli_command == command
    ]
    if len(matches) != 1:
        raise ValueError(
            f"CLI command {command!r} resolves {len(matches)} public capabilities"
        )
    return approved_v2_call(
        root,
        capability=matches[0],
        payload=payload,
        artifact_ids=artifact_ids,
        idempotency_key=idempotency_key,
        expected_snapshot=expected_snapshot,
    )
