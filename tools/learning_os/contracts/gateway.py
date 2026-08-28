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
