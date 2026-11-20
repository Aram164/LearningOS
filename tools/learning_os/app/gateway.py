"""GatewayEnvelopeV2 admission: envelope and payload validation, and approval-bound file inputs."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from learning_os.domain.failures import WriteRefused
from learning_os.store import observations
from learning_os.store.contracts.gateway import (
    GatewayRequestContext,
    current_gateway_request,
    intent_sha256,
    review_record_sha256,
)
from learning_os.store.session_ledger import (
    DEFAULT_SESSION_CHANNEL,
    has_review_check,
    remember_review_check,
)
from learning_os.store.study_fence import (
    STUDY_FENCE_CORE_ENV,
    STUDY_FENCE_SCRATCH_ENV,
    read_study_or_staged_file,
)


def read_content_bound_file(
    path_value: str,
    expected_sha256: str | None = None,
    *,
    label: str = "file input",
) -> tuple[Path, bytes]:
    """Read an external file once and verify the bytes a V2 request approved.

    The returned bytes are the bytes the caller must parse or write. Hashing
    and then reopening the pathname would merely move the TOCTOU window.
    Direct human CLI preflights may omit the digest; an active V2 gateway
    context may not.
    """
    if path_value == "-" and current_gateway_request() is not None:
        raise WriteRefused(
            f"GatewayEnvelopeV2 {label} must be a real path with an approved SHA-256; "
            "unbound stdin is not allowed"
        )
    fence_core = os.environ.get(STUDY_FENCE_CORE_ENV)
    if fence_core:
        fence_scratch = os.environ.get(STUDY_FENCE_SCRATCH_ENV)
        source, content = read_study_or_staged_file(
            path_value,
            core_root=Path(fence_core),
            scratch_dir=Path(fence_scratch) if fence_scratch else None,
            label=label,
        )
    else:
        source = Path(path_value).expanduser().resolve()
        if not source.is_file():
            raise WriteRefused(f"no such {label}: {source}")
        try:
            content = source.read_bytes()
        except OSError as exc:
            raise WriteRefused(f"cannot read {label} {source}: {exc}") from exc
    if expected_sha256 is None:
        if current_gateway_request() is not None:
            raise WriteRefused(
                f"GatewayEnvelopeV2 {label} requires a SHA-256 bound to the exact bytes"
            )
        return source, content
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", expected_sha256):
        raise WriteRefused(
            f"{label} SHA-256 must use sha256:<64 lowercase hexadecimal digits>"
        )
    actual_sha256 = "sha256:" + hashlib.sha256(content).hexdigest()
    if actual_sha256 != expected_sha256:
        raise WriteRefused(
            f"approved {label} changed before use; expected {expected_sha256}, "
            f"found {actual_sha256}. Review the new bytes and create a new approval."
        )
    return source, content


def read_structured_file(
    path_value: str,
    *,
    expected_sha256: str | None = None,
    label: str = "structured input",
) -> dict:
    """Read a JSON/YAML object from a path, or from stdin when given ``-``.

    Stdin matters for callers that build an envelope in memory: writing it to
    a temp file first means a real file holding canonical intent has to be
    created, found, and cleaned up on every write path, including the ones
    that fail. ``-`` removes that lifecycle entirely.
    """
    if path_value == "-" and expected_sha256 is None \
            and current_gateway_request() is None:
        raw = sys.stdin.read()
        try:
            data = json.loads(raw)
        except ValueError as exc:
            raise WriteRefused(f"cannot parse structured input from stdin: {exc}") from exc
        if not isinstance(data, dict):
            raise WriteRefused("structured input must be an object")
        return data
    path, raw_bytes = read_content_bound_file(
        path_value,
        expected_sha256,
        label=label,
    )
    try:
        raw = raw_bytes.decode("utf-8")
        if path.suffix.lower() == ".json":
            data = json.loads(raw)
        else:
            data = yaml.safe_load(raw)
    except (UnicodeDecodeError, ValueError, yaml.YAMLError) as exc:
        raise WriteRefused(f"cannot parse {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise WriteRefused(f"structured input must be an object: {path}")
    return data


def prepare_review_envelope(capability_name: str, payload: dict,
                            snapshot: str, revisions: dict,
                            *, checked_root: Path | None = None,
                            observed_material: dict | None = None) -> dict:
    """Prepare a recoverable request during preflight, while its lock is held.

    The envelope names the channel whose session ledger the reviewed write
    joins: the active gateway request's channel, else the operator default
    a bare `session-end` resolves. A fixed agent channel split one
    operator's writes across two ledgers, so `session-end --commit-message`
    committed the shared ledgers without the receipt and note they name.

    For a capability that requires a review, the prepared envelope also
    carries that review's binding, computed here — at check time, from
    the exact guards the check produced — so the later apply presents
    the review it came from.
    """
    request = current_gateway_request()
    channel = request.channel if request is not None else DEFAULT_SESSION_CHANNEL
    envelope = {
        "schema_version": 2,
        "request_id": f"request-reviewed-{observations.new_hex()}",
        "idempotency_key": f"reviewed-{observations.new_hex()}",
        "capability": capability_name,
        "channel": channel,
        "expected_snapshot": snapshot,
        "expected_revisions": revisions,
        "payload": payload,
        "approval": {"kind": "operator-approval", "subject_sha256": ""},
    }
    if checked_root is not None:
        envelope["review"] = issue_review_evidence(
            checked_root, capability_name, payload, snapshot, revisions, observed_material)
    from learning_os.store.session_ledger import resolve_session_identity
    session_id, source = resolve_session_identity(channel=channel)
    if source != "channel":
        envelope["session_id"] = session_id
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    return envelope


_CONTENT_BOUND_V2 = frozenset({
    "legacy.archive.lock.publish",
    "masters-planning.catalog.update",
    "masters-planning.comparison.publish",
    "collection.entry.revise",
    "source.intake.record",
    "source.record.revise",
    "unit.material-synthesis.publish",
    "unit.plan.revise",
})


def _payload_schema_path(root: Path, name: str) -> Path:
    return root / "system" / "schema" / "capabilities" / f"{name}.schema.json"


def validate_payload(root: Path, name: str, payload: dict) -> None:
    """Refuse a payload the capability never declared.

    A missing schema is itself a refusal: an undeclared payload surface means
    the capability is not actually specified, and guessing would let the
    gateway accept fields no contract describes.
    """
    path = _payload_schema_path(root, name)
    if not path.is_file():
        raise WriteRefused(f"no declared payload schema for capability {name}")
    schema = json.loads(path.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(payload),
                    key=lambda error: list(error.path))
    if errors:
        detail = "; ".join(f"{'/'.join(str(p) for p in e.path) or '<payload>'}: {e.message}"
                           for e in errors[:4])
        raise WriteRefused(f"invalid payload for {name}: {detail}")


def prepare_dispatch(
    root: Path,
    definition,
    envelope: dict,
    payload: dict,
    *,
    parser_factory=None,
):
    """Shared gateway admission (SPEC 11.2 K1).

    Refuses misplaced approval and content-bound file payloads, validates
    the payload, and builds the schema-derived namespace with envelope guards.
    ``parser_factory`` is accepted for caller compatibility and unused.
    Returns ``(None, namespace)``.
    """
    from learning_os.store.contracts.payloads import payload_to_namespace_from_schema

    if envelope.get("schema_version") == 2 and "approve" in payload:
        raise WriteRefused(
            "GatewayEnvelopeV2 approval belongs only in the envelope, not its payload"
        )
    if envelope.get("schema_version") == 2 \
            and definition.name in _CONTENT_BOUND_V2 \
            and "file" in payload:
        raise WriteRefused(
            f"GatewayEnvelopeV2 {definition.name} requires an inline record so "
            "approval is bound to the exact content"
        )
    validate_payload(root, definition.name, payload)
    namespace = payload_to_namespace_from_schema(
        root, definition.name, payload,
        root=str(root),
        expected_snapshot=envelope.get("expected_snapshot"),
        expected_revisions=envelope.get("expected_revisions", {}),
    )
    # A validated V2 envelope binds an approved user gesture to the intent
    # hash; handlers check ``namespace.approve`` identically to CLI ``--approve``.
    if envelope.get("schema_version") == 2 and hasattr(namespace, "approve"):
        namespace.approve = True
    # Handlers that can report either prose or JSON must report JSON here.
    if hasattr(namespace, "json"):
        namespace.json = True
    return None, namespace


def validate_capability_envelope(root: Path, envelope: dict, *, kind: str) -> None:
    if kind == "request" and envelope.get("schema_version") != 2:
        # Before dispatch, and before the schema's oneOf can misread the
        # shape: an envelope without `schema_version: 2` used to travel all
        # the way to the handler, which answered with a circular pointer.
        # The general sealing recipe is WORKFLOWS §25c.
        raise WriteRefused(
            "invalid capability envelope: schema_version 2 required "
            "(WORKFLOWS §25c)"
        )
    schema = json.loads((root / "system/schema/capability-envelope.schema.json").read_text(encoding="utf-8"))
    try:
        schema["$defs"][kind]
    except KeyError as exc:  # pragma: no cover - a repository contract defect
        raise WriteRefused(f"capability envelope schema has no {kind} definition") from exc
    directional_schema = {
        "$schema": schema.get("$schema", "https://json-schema.org/draft/2020-12/schema"),
        "$defs": schema["$defs"],
        "$ref": f"#/$defs/{kind}",
    }
    errors = sorted(
        Draft202012Validator(directional_schema).iter_errors(envelope),
        key=lambda error: list(error.path),
    )
    if errors:
        raise WriteRefused("invalid capability envelope: " + "; ".join(error.message for error in errors[:4]))


#: Capabilities whose check record binds observed material identity.
_MATERIAL_BOUND_REVIEW = frozenset({"module.plan.import", "unit.plan.revise"})


def issue_review_evidence(root: Path, capability: str, payload: dict,
                          snapshot: str, revisions: dict,
                          observed_material: dict | None = None) -> dict:
    """Bind a passing preflight to the checkout that actually ran it."""
    digest = review_record_sha256(
        capability=capability, payload=payload,
        expected_snapshot=snapshot, expected_revisions=revisions,
        observed_material=observed_material)
    remember_review_check(root, snapshot, digest)
    return {"record_sha256": digest}


def review_evidence_error(root: Path, envelope: dict) -> str | None:
    """The refusal for a reviewed capability applying without its review.

    ``None`` when a prior Core preflight registered the digest, and it
    still binds the checked payload, snapshot, revisions and observed material.
    A direct user gesture admitted for the capability is its own
    authorization and needs no record.
    """
    from learning_os.app.admission import gesture_allowed, requires_reviewed_seal

    capability = envelope.get("capability")
    payload = envelope.get("payload") or {}
    if not requires_reviewed_seal(capability, payload):
        return None
    approval = envelope.get("approval") or {}
    if approval.get("kind") == "direct-user-gesture" \
            and gesture_allowed(capability, envelope.get("channel")):
        return None
    if payload.get("check") is True:
        return None  # a preflight commits nothing; it *is* the review step
    observed = None
    if capability in _MATERIAL_BOUND_REVIEW:
        from learning_os.app._plan_gate import observed_material_for_payload

        fragment, problems = observed_material_for_payload(
            root, capability, payload, read_content_bound_file)
        if problems:
            return (f"{capability} review evidence cannot be verified: "
                    "the material it binds no longer resolves; re-run "
                    "--check and review the fresh record")
        observed = fragment.get("observed_material") if fragment else None
    expected = review_record_sha256(
        capability=capability, payload=payload,
        expected_snapshot=envelope.get("expected_snapshot"),
        expected_revisions=envelope.get("expected_revisions"),
        observed_material=observed)
    review = envelope.get("review")
    if (not isinstance(review, dict) or review.get("record_sha256") != expected
            or not has_review_check(root, envelope["expected_snapshot"], expected)):
        return (f"{capability} requires a reviewed check record: apply with "
                "the checked payload, snapshot and revisions of that review "
                "(seal with --guards-from REC), not with freshly derived "
                "guards")
    return None


def context_from_v2(envelope: dict) -> GatewayRequestContext:
    subject_hash = intent_sha256(envelope)
    approval = envelope["approval"]
    if approval["subject_sha256"] != subject_hash:
        raise WriteRefused(
            "approval subject does not match the current capability intent"
        )
    raw_session = envelope.get("session_id")
    sealed_session = raw_session.strip() if isinstance(raw_session, str) else None
    return GatewayRequestContext(
        request_id=envelope["request_id"],
        idempotency_key=envelope["idempotency_key"],
        capability=envelope["capability"],
        channel=envelope["channel"],
        intent_sha256=subject_hash,
        approval_kind=approval["kind"],
        approval_subject_sha256=approval["subject_sha256"],
        expected_snapshot=envelope["expected_snapshot"],
        session_id=sealed_session or None,
    )
