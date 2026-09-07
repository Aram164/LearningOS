"""The derived semantic layer (Intelligence Plane, Phase 0).

Phase 1 grows this package toward ~25 predicates plus lineage, goal
detection, task IR, dossier, and proof-carrying-change services. Each of
those arrives as its own module with its own tests; nothing here may become
a canonical writer — see `system/SEMANTIC-CONTRACT.md`.
"""

from __future__ import annotations

from .lineage import (
    ClaimLineage,
    DerivedFrom,
    LineageError,
    contest,
    dump_ledger,
    emit_dossier_freshness,
    emit_route_covers,
    emit_scope_authority,
    endorse,
    impacted,
    load_ledger,
    record_claim,
    refresh,
)
from .policy import POLICY_RULES, PolicyDecision, query
from .predicates import (
    CONTRACT_VERSION,
    PREDICATES,
    Predicate,
    evaluate,
    needs_study_map,
)

__all__ = [
    "CONTRACT_VERSION",
    "POLICY_RULES",
    "PREDICATES",
    "ClaimLineage",
    "DerivedFrom",
    "LineageError",
    "PolicyDecision",
    "Predicate",
    "contest",
    "dump_ledger",
    "emit_dossier_freshness",
    "emit_route_covers",
    "emit_scope_authority",
    "endorse",
    "evaluate",
    "impacted",
    "load_ledger",
    "needs_study_map",
    "query",
    "record_claim",
    "refresh",
]
