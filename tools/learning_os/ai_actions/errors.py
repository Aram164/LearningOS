"""Refusal types and the delivery size ceilings that bound an import."""

from __future__ import annotations


class AIActionError(Exception):
    """Base class for a refused AI-action operation."""


MAX_DELIVERY_ENTRIES = 512


MAX_DELIVERY_BYTES = 32 * 1024 * 1024


class ActionNotFoundError(AIActionError):
    pass


class ActionPolicyError(AIActionError):
    pass


class ConfidentialityError(AIActionError):
    pass


class DeliveryValidationError(AIActionError):
    pass


class StaleDeliveryError(AIActionError):
    pass


class TargetNotFoundError(AIActionError):
    pass
