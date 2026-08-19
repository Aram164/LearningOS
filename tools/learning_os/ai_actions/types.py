"""Typed records crossing the AI-action service boundary.

The exchange files remain ordinary YAML/JSON mappings.  These definitions make
their required shape visible to Python callers without introducing a runtime
model dependency or changing the wire contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, NotRequired, TypedDict


class ArtifactTarget(TypedDict):
    kind: str
    id: str


class ProviderSelection(TypedDict):
    preferred: str
    adapter: str


class OriginalArtifact(TypedDict):
    id: str
    canonical_path: str
    bundle_path: str
    checksum: str
    media_type: str


class RequestContext(TypedDict):
    artifact_ids: list[str]
    attachment_ids: list[str]
    originals: list[OriginalArtifact]


class RequestPreconditions(TypedDict):
    snapshot_id: str
    artifact_revisions: dict[str, int | str]


class ConfidentialityPolicy(TypedDict):
    classification: str
    job_derived: bool
    export_confirmed: bool
    employer_repository_access: bool


class AIActionRequest(TypedDict):
    schema_version: int
    id: str
    type: str
    action_id: str
    status: str
    target: ArtifactTarget
    provider: ProviderSelection
    context: RequestContext
    allowed_capabilities: list[str]
    forbidden_capabilities: list[str]
    preconditions: RequestPreconditions
    confidentiality: ConfidentialityPolicy
    created_at: str
    delivery_id: NotRequired[str]
    receipt_id: NotRequired[str]


class DeliveryRecord(TypedDict, total=False):
    """Validated provider delivery.

    Fields are optional at load time because validation must be able to explain
    malformed, untrusted bundles.  A delivery is returned publicly only after
    the service has checked the required fields and policy constraints.
    """

    schema_version: int
    id: str
    type: str
    request_id: str
    action_id: str
    producer: dict[str, Any]
    preconditions: RequestPreconditions
    approval: dict[str, Any]
    operations: list[dict[str, Any]]


class DeliveryValidationResult(TypedDict):
    ok: bool
    delivery_id: str
    request_id: str


class ApplyDeliveryResult(TypedDict, total=False):
    transaction_id: str
    receipt_path: str
    touched_paths: list[str]
    capability: str
    status: str
    artifact_revisions: dict[str, int]


class RequestStatus(TypedDict):
    id: str
    action_id: str
    target: ArtifactTarget
    provider: str
    status: str
    created_at: str
    delivery_id: str | None
    receipt_id: str | None
    bundle_path: str


class GardenTarget(TypedDict):
    id: str
    type: str
    title: str
    path: str
    state: str
    tags: list[str]
    revision: str
    job_derived: NotRequired[bool]


@dataclass(frozen=True)
class ValidatedDelivery:
    """Internal hand-off from validation to application."""

    delivery_id: str
    request_id: str
    request: AIActionRequest
    target: GardenTarget
