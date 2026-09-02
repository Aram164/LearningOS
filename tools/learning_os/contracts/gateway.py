"""GatewayEnvelopeV2 intent hashing and request-local transaction context."""

from __future__ import annotations

import contextlib
import contextvars
import hashlib
import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path

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
    # The approved projection identity. Real GatewayEnvelopeV2 requests always
    # provide it; ``None`` remains available for focused service tests and
    # historical callers that construct the context directly.
    expected_snapshot: str | None = None


_CURRENT_REQUEST: contextvars.ContextVar[GatewayRequestContext | None] = (
    contextvars.ContextVar("learningos_gateway_request", default=None)
)
_VERIFIED_SNAPSHOT: contextvars.ContextVar[tuple[str, str] | None] = (
    contextvars.ContextVar("learningos_verified_gateway_snapshot", default=None)
)


def current_gateway_request() -> GatewayRequestContext | None:
    return _CURRENT_REQUEST.get()


def gateway_snapshot_is_verified(root: Path, snapshot: str) -> bool:
    """Whether ``snapshot`` was observed while the gateway holds ``root``'s lock."""
    return _VERIFIED_SNAPSHOT.get() == (str(root.resolve()), snapshot)


@contextlib.contextmanager
def verified_gateway_snapshot(root: Path, snapshot: str) -> Iterator[None]:
    """Mark one locked V2 dispatch as already compared with canonical state."""
    token = _VERIFIED_SNAPSHOT.set((str(root.resolve()), snapshot))
    try:
        yield
    finally:
        _VERIFIED_SNAPSHOT.reset(token)


@contextlib.contextmanager
def gateway_request_context(context: GatewayRequestContext) -> Iterator[None]:
    token = _CURRENT_REQUEST.set(context)
    try:
        yield
    finally:
        _CURRENT_REQUEST.reset(token)
