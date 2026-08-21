"""Bounded AI actions.

The UI never sends an open-ended prompt: it asks the core to persist an exact
request bundle, and later applies only a delivery the core has validated
against the locked contract. This package boundary is the stable surface —
callers import from ``learning_os.ai_actions`` and stay unaware of which
module owns which step.

Split from a single 988-line module dominated by one 505-line service class.
"""

from __future__ import annotations

from .errors import (
    MAX_DELIVERY_BYTES,
    MAX_DELIVERY_ENTRIES,
    ActionNotFoundError,
    ActionPolicyError,
    AIActionError,
    ConfidentialityError,
    DeliveryValidationError,
    StaleDeliveryError,
    TargetNotFoundError,
)
from .projection import manifest_ai_projection
from .registry import ActionDefinition, ActionRegistry, AdapterDefinition, AdapterRegistry
from .service import AIActionService
from .storage import FilesystemAIActionRepository
from .support import parse_frontmatter_request_id
from .types import (
    AIActionRequest,
    ApplyDeliveryResult,
    DeliveryRecord,
    DeliveryValidationResult,
    RequestStatus,
)

__all__ = [
    "AIActionError", "AIActionService", "ActionDefinition", "ActionNotFoundError",
    "ActionPolicyError", "ActionRegistry", "AdapterDefinition", "AdapterRegistry",
    "ConfidentialityError", "DeliveryValidationError", "FilesystemAIActionRepository",
    "MAX_DELIVERY_BYTES", "MAX_DELIVERY_ENTRIES", "StaleDeliveryError",
    "TargetNotFoundError", "manifest_ai_projection", "parse_frontmatter_request_id",
    "AIActionRequest", "ApplyDeliveryResult", "DeliveryRecord",
    "DeliveryValidationResult", "RequestStatus",
]
