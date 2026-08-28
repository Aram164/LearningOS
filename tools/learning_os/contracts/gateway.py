"""GatewayEnvelopeV2 intent hashing and request-local transaction context."""

from __future__ import annotations

import contextlib
import contextvars
import hashlib
import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass

GATEWAY_SCHEMA_VERSION = 2
GATEWAY_CHANNELS = frozenset({"ui", "codex", "operator", "system-task"})
APPROVAL_KINDS = frozenset({
    "direct-user-gesture",
    "approved-delivery",
    "operator-approval",
})

# Capabilities whose write target is named by the handler, not by the caller.
# A caller cannot guard `capture:work/inbox/20260829-…md` because the filename
# does not exist until the handler picks it, so these two guard the *request*
# instead. Both sides have to derive the identical string: Core when it opens
# the transaction, and every interface when it builds the envelope. The literal
# lived in three places and drifted; this mapping is now the only one.
REQUEST_SCOPED_ARTIFACT_PREFIXES: Mapping[str, str] = {
    "capture.create": "capture-request",
    "garden.seed.create": "garden-request",
}


def is_request_scoped_capability(capability: str) -> bool:
    """True when the capability guards its request rather than a named file."""
    return str(capability) in REQUEST_SCOPED_ARTIFACT_PREFIXES


def request_artifact_id(capability: str, idempotency_key: str) -> str:
    """Return the one request-scoped artifact id for a dynamically-named write."""
    try:
        prefix = REQUEST_SCOPED_ARTIFACT_PREFIXES[str(capability)]
    except KeyError as exc:
        raise ValueError(
            f"{capability} does not use request-scoped artifacts"
        ) from exc
    key = str(idempotency_key).strip()
    if not key:
        raise ValueError(
            f"{capability} requires a non-empty idempotency key to guard its request"
        )
    return f"{prefix}:{key}"


def intent_subject(envelope: Mapping) -> dict:
    """Return the exact approval subject; request identities are not intent."""
    return {
        "schema_version": envelope.get("schema_version"),
        "capability": envelope.get("capability"),
        "channel": envelope.get("channel"),
        "expected_snapshot": envelope.get("expected_snapshot"),
        "expected_revisions": envelope.get("expected_revisions"),
        "payload": envelope.get("payload"),
    }


def intent_sha256(envelope: Mapping) -> str:
    encoded = json.dumps(
        intent_subject(envelope),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class GatewayRequestContext:
    request_id: str
    idempotency_key: str
    capability: str
    channel: str
    intent_sha256: str
    approval_kind: str
    approval_subject_sha256: str


_CURRENT_REQUEST: contextvars.ContextVar[GatewayRequestContext | None] = (
    contextvars.ContextVar("learningos_gateway_request", default=None)
)


def current_gateway_request() -> GatewayRequestContext | None:
    return _CURRENT_REQUEST.get()


@contextlib.contextmanager
def gateway_request_context(context: GatewayRequestContext) -> Iterator[None]:
    token = _CURRENT_REQUEST.set(context)
    try:
        yield
    finally:
        _CURRENT_REQUEST.reset(token)
