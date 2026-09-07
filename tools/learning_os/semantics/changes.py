"""Phase-6 proof-carrying change: every mutation arrives with its proof.

An envelope states intent, scope, the reads it depended on, the claims it
believes with their evidence, the writes it wants (capability plus target),
the snapshot it read, the postconditions it promises, and the validation
it will run. Admission is deterministic and runs before any gateway
apply: evidence must resolve, reads must be fresh, the snapshot must
match, every claim must carry supported lineage, every write must sit
inside an Aram-approved scope, and every postcondition must be
well-formed. Anything else returns conflict, replan, or deny — never an
overwrite. The gateway still applies; the envelope is preflight, not an
alternative path, and the snapshot guard stays the final word.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .predicates import (
    CONTRACT_VERSION,
    PREDICATES,
    allowed_mutation,
    claim_stale,
    evaluate,
    snapshot_fresh,
)


class ChangeError(ValueError):
    """A change envelope cannot be read as written."""


#: Admission verdicts. ``conflict`` means the world moved (reload and
#: replan); ``replan`` means the envelope itself is incomplete;
#: ``deny`` means forbidden no matter the timing.
VERDICTS = ("admit", "conflict", "replan", "deny")

#: Postcondition assertion operators, shared with the VOQ suite.
POSTCONDITION_OPS = ("equals", "is_true", "is_false", "contains")

#: Only Aram approves a change scope.
APPROVER = "Aram"


@dataclass(frozen=True)
class WriteOp:
    """One wanted write: which capability, where, under which scopes."""

    capability: str
    target_path: str
    summary: str
    scopes: tuple[str, ...] = ()


@dataclass(frozen=True)
class Postcondition:
    """One promised check, evaluated after the gateway applies."""

    predicate: str
    inputs: tuple[tuple[str, object], ...]
    op: str
    value: object = None


@dataclass(frozen=True)
class ChangeEnvelope:
    """The preflight envelope around one governed mutation."""

    intent: str
    scope: tuple[str, ...]
    read_contract_version: int
    read_revisions: tuple[tuple[str, int], ...]
    claims: tuple[str, ...]
    claim_statuses: tuple[tuple[str, str], ...]
    evidence: tuple[tuple[str, str | None], ...]
    writes: tuple[WriteOp, ...]
    expected_snapshot: str
    approved_by: str
    approved_capabilities: tuple[str, ...]
    postconditions: tuple[Postcondition, ...]
    validation_plan: tuple[str, ...]


@dataclass(frozen=True)
class AdmissionDecision:
    """Admit, or the reasoned refusal. Never an overwrite."""

    verdict: str
    reasons: tuple[str, ...] = ()


def _refuse(verdict: str, *reasons: str) -> AdmissionDecision:
    assert verdict in VERDICTS, verdict
    return AdmissionDecision(verdict=verdict, reasons=tuple(reasons))


def build_envelope(
    *,
    intent: str,
    scope: Sequence[str],
    read_revisions: Mapping[str, int],
    claims: Sequence[str],
    claim_statuses: Mapping[str, str],
    evidence: Mapping[str, str | None],
    writes: Sequence[Mapping[str, object]],
    expected_snapshot: str,
    approved_by: str,
    approved_capabilities: Sequence[str],
    postconditions: Sequence[Mapping[str, object]],
    validation_plan: Sequence[str],
    read_contract_version: int = CONTRACT_VERSION,
) -> ChangeEnvelope:
    """Assemble an envelope. Malformed envelopes refuse at construction."""
    if not isinstance(intent, str) or not intent.strip():
        raise ChangeError("a change needs a stated intent")
    if isinstance(scope, str) or not isinstance(scope, Sequence) or not scope:
        raise ChangeError("a change needs a non-empty scope")
    try:
        revisions = tuple(sorted(
            (str(key), int(value)) for key, value in read_revisions.items()))
        claim_ids = tuple(str(claim) for claim in claims)
        statuses = tuple(sorted(
            (str(key), str(value)) for key, value in claim_statuses.items()))
        trails = tuple(sorted(
            (str(locator), (None if digest is None else str(digest)))
            for locator, digest in evidence.items()))
        ops = tuple(
            WriteOp(
                capability=str(op["capability"]),
                target_path=str(op["target_path"]),
                summary=str(op.get("summary") or ""),
                scopes=tuple(str(scope) for scope in op.get("scopes", ())),
            )
            for op in writes
        )
        checks = tuple(
            Postcondition(
                predicate=str(check["predicate"]),
                inputs=tuple(sorted(
                    (str(key), value)
                    for key, value in dict(check["inputs"]).items())),
                op=str(check["op"]),
                value=check.get("value"),
            )
            for check in postconditions
        )
        plan = tuple(str(step) for step in validation_plan)
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise ChangeError(f"malformed change envelope: {exc}") from exc
    if not ops:
        raise ChangeError("a change with no writes changes nothing")
    if not plan:
        raise ChangeError("a change with no validation plan proves nothing")
    if not isinstance(expected_snapshot, str) or not expected_snapshot:
        raise ChangeError("a change names the snapshot it read")
    return ChangeEnvelope(
        intent=intent,
        scope=tuple(str(area) for area in scope),
        read_contract_version=read_contract_version,
        read_revisions=revisions,
        claims=claim_ids,
        claim_statuses=statuses,
        evidence=trails,
        writes=ops,
        expected_snapshot=expected_snapshot,
        approved_by=str(approved_by),
        approved_capabilities=tuple(
            str(name) for name in approved_capabilities),
        postconditions=checks,
        validation_plan=plan,
    )


def admit(
    envelope: ChangeEnvelope,
    current_contract_version: int,
    current_revisions: Mapping[str, int],
    current_snapshot: str,
) -> AdmissionDecision:
    """Run the deterministic admission check. Order is fixed: authority,
    freshness, evidence, lineage, scope, shape — the first failure wins,
    because a forbidden change needs no freshness verdict and a stale one
    needs no scope debate.
    """
    if envelope.approved_by != APPROVER:
        return _refuse(
            "deny",
            f"Change scope needs {APPROVER}'s explicit approval; "
            f"carries {envelope.approved_by!r}.",
        )
    for op in envelope.writes:
        if op.capability not in envelope.approved_capabilities:
            return _refuse(
                "deny",
                f"One approval, one scope: {op.capability!r} is outside "
                "the approved capabilities.",
            )
        if not allowed_mutation(
            capability=op.capability,
            target_path=op.target_path,
            scopes=op.scopes,
        ):
            return _refuse(
                "deny",
                f"{op.capability!r} may not write {op.target_path!r}: "
                "out of its declared scopes.",
            )
    if claim_stale(
        read_contract_version=envelope.read_contract_version,
        current_contract_version=current_contract_version,
        read_revisions=dict(envelope.read_revisions),
        current_revisions=current_revisions,
    ):
        return _refuse(
            "conflict",
            "Read set is stale: reload the world and replan, never overwrite.",
        )
    if not snapshot_fresh(
        expected_snapshot=envelope.expected_snapshot,
        current_snapshot=current_snapshot,
    ):
        return _refuse(
            "conflict",
            "Snapshot mismatch: another write landed first; reload, never "
            "overwrite.",
        )
    statuses = dict(envelope.claim_statuses)
    for locator, digest in envelope.evidence:
        if digest is None:
            return _refuse(
                "replan",
                f"Evidence {locator!r} does not resolve: a claim without "
                "resolvable evidence is not a claim to apply.",
            )
    for claim_id in envelope.claims:
        if statuses.get(claim_id) != "supported":
            return _refuse(
                "conflict",
                f"Claim {claim_id!r} carries no supported lineage: "
                "re-judge it first.",
            )
    for check in envelope.postconditions:
        if check.predicate not in PREDICATES:
            return _refuse(
                "replan",
                f"Postcondition names unknown predicate "
                f"{check.predicate!r}: prove the checkable first.",
            )
        if check.op not in POSTCONDITION_OPS:
            return _refuse(
                "replan",
                f"Postcondition on {check.predicate!r} uses unknown "
                f"operator {check.op!r}.",
            )
    return AdmissionDecision(verdict="admit", reasons=(
        f"Intent {envelope.intent!r}: {len(envelope.writes)} write(s) "
        "approved, fresh, evidenced, and checkable.",
    ))


@dataclass(frozen=True)
class PostconditionResult:
    """One post-apply check: what was promised, whether it holds."""

    predicate: str
    passed: bool


def verify_postconditions(
    envelope: ChangeEnvelope,
) -> tuple[PostconditionResult, ...]:
    """Evaluate every postcondition. The harness calls this after the
    gateway applies, with the world the envelope promised about.

    Predicate inputs are fixed at envelope time, so this replays exactly
    what admission checked for shape. Unknown predicates raise KeyError:
    admission refuses malformed envelopes first, so anything reaching here
    malformed is a harness bug, not a judgment call.
    """
    results = []
    for check in envelope.postconditions:
        verdict = evaluate(check.predicate, **dict(check.inputs))
        if check.op == "equals":
            passed = verdict == check.value
        elif check.op == "is_true":
            passed = verdict is True
        elif check.op == "is_false":
            passed = verdict is False
        else:
            passed = check.value in verdict
        results.append(PostconditionResult(
            predicate=check.predicate, passed=bool(passed)))
    return tuple(results)
