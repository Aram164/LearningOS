"""The derived semantic layer (Intelligence Plane, Phase 0).

Phase 1 grows this package toward ~25 predicates plus lineage, goal
detection, task IR, dossier, and proof-carrying-change services. Each of
those arrives as its own module with its own tests; nothing here may become
a canonical writer — see `system/SEMANTIC-CONTRACT.md`.
"""

from __future__ import annotations

from .goals import (
    AUTHORIZER,
    STATES,
    TERMINAL_STATES,
    TRANSITIONS,
    CandidateGoal,
    GoalError,
    detect_covering_routes_stale,
    detect_inspection_without_dossier,
    detect_repeated_question_gap,
    detect_reviewer_correction_pattern,
    detect_source_changed_under_claim,
    goal_from_dict,
    goal_to_dict,
    transition,
)
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
    "AUTHORIZER",
    "CONTRACT_VERSION",
    "POLICY_RULES",
    "PREDICATES",
    "STATES",
    "TERMINAL_STATES",
    "TRANSITIONS",
    "CandidateGoal",
    "ClaimLineage",
    "DerivedFrom",
    "GoalError",
    "LineageError",
    "PolicyDecision",
    "Predicate",
    "contest",
    "detect_covering_routes_stale",
    "detect_inspection_without_dossier",
    "detect_repeated_question_gap",
    "detect_reviewer_correction_pattern",
    "detect_source_changed_under_claim",
    "dump_ledger",
    "emit_dossier_freshness",
    "emit_route_covers",
    "emit_scope_authority",
    "endorse",
    "evaluate",
    "goal_from_dict",
    "goal_to_dict",
    "impacted",
    "load_ledger",
    "needs_study_map",
    "query",
    "record_claim",
    "refresh",
    "transition",
]
