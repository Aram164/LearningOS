"""Public V2 error codes and refusal reasons, spelled once (SPEC §8.2).

``PUBLIC_CODES`` is the ``capability-envelope.schema.json`` resultV2 error
code enum, in that order; ``tools/generate_capability_schemas.py --check``
fails if the two drift. Every other spelling lives behind these constants
(A14): import the name, never the literal.
"""

from __future__ import annotations

INVALID_REQUEST = "INVALID_REQUEST"
UNKNOWN_CAPABILITY = "UNKNOWN_CAPABILITY"
STALE_SNAPSHOT = "STALE_SNAPSHOT"
REVISION_CONFLICT = "REVISION_CONFLICT"
OUT_OF_SCOPE = "OUT_OF_SCOPE"
VALIDATION_FAILED = "VALIDATION_FAILED"
AMBIGUOUS_MIGRATION = "AMBIGUOUS_MIGRATION"
PROJECTION_FAILED = "PROJECTION_FAILED"
IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
UNCONFIRMED = "UNCONFIRMED"
INTERNAL_FAILURE = "INTERNAL_FAILURE"

PUBLIC_CODES: tuple[str, ...] = (
    INVALID_REQUEST,
    UNKNOWN_CAPABILITY,
    STALE_SNAPSHOT,
    REVISION_CONFLICT,
    OUT_OF_SCOPE,
    VALIDATION_FAILED,
    AMBIGUOUS_MIGRATION,
    PROJECTION_FAILED,
    IDEMPOTENCY_CONFLICT,
    UNCONFIRMED,
    INTERNAL_FAILURE,
)

REASONS: tuple[str, ...] = (
    "NOT_FOUND",
    "MALFORMED_ID",
    # LearningOS #12: the projection snapshot conflict names changed
    # canonical inputs; see outcomes.projection_failure_details.
    "CANONICAL_INPUTS_CHANGED",
)
