"""Phase-1.5 policy queries: governance rules as structured allow/deny answers.

Predicates (``predicates.py``) own individual judgments. This module owns the
*query* surface agents program against: one rule name in, one structured
decision out — a normalized verdict plus the reasons behind it, OPA-style.
A verdict without reasons is an oracle; a boolean without authority is
folklore. Every decision therefore carries both.

The layer adds no new judgment: each rule maps one predicate's native
verdict onto the shared vocabulary below and explains the mapping from the
caller's own inputs. Composition of rules into a change envelope belongs to
Phase 6 (proof-carrying change), which will cite these decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..contracts.write_scopes import WriteScopeError, scope_matches
from .predicates import (
    PREDICATES,
    allowed_mutation,
    canonical_write_path,
    critique_point_actionable,
    mastery_declared,
    note_change_needs_review,
    shelving_approval,
    workspace_may_coordinate,
)

#: Shared verdict vocabulary. ``defer`` is not ``deny``: a deferred critique
#: point may come back with authorization, while a denied mutation must not
#: be retried unchanged. ``needs-review`` routes to a human, never forward.
VERDICTS = ("allow", "deny", "defer", "needs-review")


@dataclass(frozen=True)
class PolicyDecision:
    """One answered governance question."""

    rule: str
    verdict: str
    reasons: tuple[str, ...] = field(default_factory=tuple)
    predicate: str = ""
    authority: str = ""


def _decision(rule: str, verdict: str, reasons: list[str]) -> PolicyDecision:
    assert verdict in VERDICTS, verdict
    predicate = POLICY_RULES[rule]["predicate"]
    return PolicyDecision(
        rule=rule,
        verdict=verdict,
        reasons=tuple(reason for reason in reasons if reason),
        predicate=predicate,
        authority=PREDICATES[predicate].authority,
    )


def _query_mutation_allowed(
    *, capability: str, target_path: str, scopes: tuple[str, ...],
) -> PolicyDecision:
    try:
        matched = [
            pattern for pattern in scopes
            if isinstance(pattern, str) and scope_matches(target_path, pattern)
        ]
    except WriteScopeError:
        matched = []
    if allowed_mutation(
        capability=capability, target_path=target_path, scopes=scopes,
    ):
        return _decision("mutation_allowed", "allow", [
            f"{capability} admits {target_path} via scope {matched[0]!r}."
            if matched else f"{capability} admits {target_path}.",
        ])
    return _decision("mutation_allowed", "deny", [
        f"{capability} admits none of its {len(scopes)} declared scope(s) "
        f"for {target_path}.",
        "Authority is the capability contract's writes entry; matching is "
        "exact segments, never prefixes.",
    ])


def _query_shelving_apply(
    *, applied_items: tuple[str, ...], approved_items: tuple[str, ...],
) -> PolicyDecision:
    if shelving_approval(
        applied_items=applied_items, approved_items=approved_items,
    ):
        return _decision("shelving_apply", "allow", [
            f"{len(applied_items)} applied item(s) are all explicitly approved.",
        ])
    unapproved = sorted(set(applied_items) - set(approved_items))
    reasons = ["Apply only explicitly selected proposal items."]
    if not applied_items:
        reasons.append("An empty apply carries nothing and is refused.")
    if unapproved:
        reasons.append(f"Unapproved items: {', '.join(unapproved)}.")
    return _decision("shelving_apply", "deny", reasons)


def _query_critique_action(
    *, status: str, authorized_in_session: bool,
) -> PolicyDecision:
    outcome = critique_point_actionable(
        status=status, authorized_in_session=authorized_in_session,
    )
    if outcome == "actionable":
        return _decision("critique_action", "allow", [
            "Aram authorized this point in this session.",
        ])
    if outcome == "deferred":
        return _decision("critique_action", "defer", [
            f"Point status is {status!r} without in-session authorization.",
            "An open point is deferred work, not denied work: come back "
            "with authorization. Appending evidence never needs it.",
        ])
    return _decision("critique_action", "deny", [
        f"Point status is {status!r}: closed points stay closed.",
    ])


def _query_mastery_check(*, statement_kind: str) -> PolicyDecision:
    if mastery_declared(statement_kind=statement_kind):
        return _decision("mastery_check", "deny", [
            f"{statement_kind!r} declares mastery: report evidence or its "
            "absence instead.",
        ])
    return _decision("mastery_check", "allow", [
        f"{statement_kind!r} describes work without claiming it.",
    ])


def _query_note_review(*, change_kind: str) -> PolicyDecision:
    if note_change_needs_review(change_kind=change_kind):
        return _decision("note_review", "needs-review", [
            f"{change_kind!r} changes meaning, identity, or provenance: "
            "a human reviews before it lands.",
        ])
    return _decision("note_review", "allow", [
        f"{change_kind!r} never requires review on its own.",
    ])


def _query_write_path(*, channel: str) -> PolicyDecision:
    if canonical_write_path(channel=channel):
        return _decision("write_path", "allow", [
            f"{channel} is a declared gateway.",
        ])
    return _decision("write_path", "deny", [
        f"{channel!r} is not a declared gateway: a hand edit is never a "
        "faster version of the path.",
    ])


def _query_workspace_scope(*, claim_kind: str) -> PolicyDecision:
    if workspace_may_coordinate(claim_kind=claim_kind):
        return _decision("workspace_scope", "allow", [
            f"{claim_kind} is an explicit coordination list.",
        ])
    return _decision("workspace_scope", "deny", [
        f"{claim_kind!r} belongs to the curriculum hierarchy, which "
        "workspaces never own.",
    ])


POLICY_RULES: dict[str, dict[str, object]] = {
    "mutation_allowed": {
        "predicate": "AllowedMutation",
        "query": _query_mutation_allowed,
        "description": "A capability may write only inside its declared scopes.",
    },
    "shelving_apply": {
        "predicate": "ShelvingApproval",
        "query": _query_shelving_apply,
        "description": "Shelving applies only explicitly selected items.",
    },
    "critique_action": {
        "predicate": "CritiquePointActionable",
        "query": _query_critique_action,
        "description": "Open points need in-session authorization; closed stay closed.",
    },
    "mastery_check": {
        "predicate": "MasteryDeclared",
        "query": _query_mastery_check,
        "description": "Mastery is never declared.",
    },
    "note_review": {
        "predicate": "NoteChangeNeedsReview",
        "query": _query_note_review,
        "description": "Meaning, identity, and provenance changes need review.",
    },
    "write_path": {
        "predicate": "CanonicalWritePath",
        "query": _query_write_path,
        "description": "Plans change only through declared gateways.",
    },
    "workspace_scope": {
        "predicate": "WorkspaceMayCoordinate",
        "query": _query_workspace_scope,
        "description": "Workspaces coordinate; they own no hierarchy.",
    },
}


def query(rule: str, **inputs: object) -> PolicyDecision:
    """Answer one governance rule with a verdict and its reasons.

    Unknown rules fail closed with KeyError, exactly like unknown
    predicates. Malformed inputs deny rather than raise: a query an agent
    cannot even form is not a query to trust.
    """
    try:
        entry = POLICY_RULES[rule]
    except KeyError:
        raise KeyError(f"unknown policy rule: {rule!r}") from None
    function = entry["query"]
    assert callable(function)
    try:
        return function(**inputs)
    except TypeError as exc:
        return PolicyDecision(
            rule=rule,
            verdict="deny",
            reasons=(f"Malformed inputs for {rule}: {exc}.",),
            predicate=str(entry["predicate"]),
            authority=PREDICATES[str(entry["predicate"])].authority,
        )
