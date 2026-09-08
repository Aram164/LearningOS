"""Phase-6 proof-carrying change: every mutation arrives with its proof.

An envelope states claims, not verdicts about those claims: intent,
scope, the reads it depended on, the claim ids it relies on, bare
evidence references, the writes it wants (capability plus target), the
snapshot it read, the postconditions it promises, and the validation it
will run. Admission is deterministic and runs before any gateway apply,
against a trusted context the agent never touches: session
authorization, the capability contract, the live lineage ledger,
harness-resolved evidence, current revisions, and the current snapshot.
Evidence must resolve, reads must be fresh, the snapshot must match,
every claim must read supported in the live ledger, every write must sit
inside an Aram-approved scope grounded in the capability contract, and
every postcondition must be well-formed. Anything else returns conflict,
replan, or deny — never an overwrite. The gateway still applies; the
envelope is preflight, not an alternative path, and the snapshot guard
stays the final word.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from ..contracts.write_scopes import WriteScopeError, scope_matches
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
    """One promised check, evaluated after the gateway applies.

    ``selector`` names the post-apply observation the harness must
    supply (e.g. ``validation`` for the validator summary) — predicate
    inputs are derived from the live world, never fixed at envelope
    time. A check that promises about state the harness never observed
    is not a check.
    """

    predicate: str
    selector: str
    op: str
    value: object = None


@dataclass(frozen=True)
class ChangeEnvelope:
    """The preflight envelope around one governed mutation.

    Claims only: no approval, no lineage verdicts, no digests. Anything
    the agent asserts about authorization, lineage, or evidence is
    structurally unstatable here — admission reads those from context.
    """

    intent: str
    scope: tuple[str, ...]
    read_contract_version: int
    read_revisions: tuple[tuple[str, int], ...]
    claims: tuple[str, ...]
    evidence: tuple[str, ...]
    writes: tuple[WriteOp, ...]
    expected_snapshot: str
    postconditions: tuple[Postcondition, ...]
    validation_plan: tuple[str, ...]


@dataclass(frozen=True)
class AdmissionDecision:
    """Admit, or the reasoned refusal. Never an overwrite."""

    verdict: str
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class TrustedContext:
    """What admission trusts: everything the agent never touches.

    The harness builds this from the live session (who approved, which
    capabilities), the capability contract (each capability's granted
    write scopes), the live lineage ledger (claim statuses), resolved
    evidence digests, and the current revisions, contract version, and
    snapshot. Tuples throughout, like the envelope.
    """

    approved_by: str
    approved_capabilities: tuple[str, ...]
    capability_scopes: tuple[tuple[str, tuple[str, ...]], ...]
    claim_statuses: tuple[tuple[str, str], ...]
    evidence_digests: tuple[tuple[str, str | None], ...]
    current_contract_version: int
    current_revisions: tuple[tuple[str, int], ...]
    current_snapshot: str


def _refuse(verdict: str, *reasons: str) -> AdmissionDecision:
    assert verdict in VERDICTS, verdict
    return AdmissionDecision(verdict=verdict, reasons=tuple(reasons))


def build_envelope(
    *,
    intent: str,
    scope: Sequence[str],
    read_revisions: Mapping[str, int],
    claims: Sequence[str],
    evidence: Sequence[str],
    writes: Sequence[Mapping[str, object]],
    expected_snapshot: str,
    postconditions: Sequence[Mapping[str, object]],
    validation_plan: Sequence[str],
    read_contract_version: int = CONTRACT_VERSION,
) -> ChangeEnvelope:
    """Assemble an envelope. Malformed envelopes refuse at construction.

    Evidence travels as bare references — locators the harness resolves,
    never digests the agent asserts.
    """
    if not isinstance(intent, str) or not intent.strip():
        raise ChangeError("a change needs a stated intent")
    if isinstance(scope, str) or not isinstance(scope, Sequence) or not scope:
        raise ChangeError("a change needs a non-empty scope")
    if isinstance(evidence, str) or not isinstance(evidence, Sequence):
        raise ChangeError("change evidence comes as a list of locators")
    try:
        revisions = tuple(sorted(
            (str(key), int(value)) for key, value in read_revisions.items()))
        claim_ids = tuple(str(claim) for claim in claims)
        trails = tuple(sorted(str(locator) for locator in evidence))
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
                selector=str(check["selector"]),
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
    if any(not check.selector.strip() for check in checks):
        raise ChangeError("a postcondition names the observation it reads")
    if not isinstance(expected_snapshot, str) or not expected_snapshot:
        raise ChangeError("a change names the snapshot it read")
    return ChangeEnvelope(
        intent=intent,
        scope=tuple(str(area) for area in scope),
        read_contract_version=read_contract_version,
        read_revisions=revisions,
        claims=claim_ids,
        evidence=trails,
        writes=ops,
        expected_snapshot=expected_snapshot,
        postconditions=checks,
        validation_plan=plan,
    )


def build_trusted_context(
    *,
    approved_by: str,
    approved_capabilities: Sequence[str],
    capability_scopes: Mapping[str, Sequence[str]],
    claim_statuses: Mapping[str, str],
    evidence_digests: Mapping[str, str | None],
    current_contract_version: int,
    current_revisions: Mapping[str, int],
    current_snapshot: str,
) -> TrustedContext:
    """Assemble the trusted context. The harness builds this, never the
    agent: malformed context refuses at construction, like envelopes."""
    if not isinstance(approved_by, str) or not approved_by:
        raise ChangeError("trusted context names who approved")
    if not isinstance(current_snapshot, str) or not current_snapshot:
        raise ChangeError("trusted context names the current snapshot")
    if isinstance(current_contract_version, bool) \
            or not isinstance(current_contract_version, int):
        raise ChangeError("trusted context versions the contract it read")
    try:
        capabilities = tuple(str(name) for name in approved_capabilities)
        scopes = tuple(sorted(
            (str(capability), tuple(str(pattern) for pattern in patterns))
            for capability, patterns in capability_scopes.items()))
        statuses = tuple(sorted(
            (str(key), str(value)) for key, value in claim_statuses.items()))
        digests = tuple(sorted(
            (str(locator), (None if digest is None else str(digest)))
            for locator, digest in evidence_digests.items()))
        revisions = tuple(sorted(
            (str(key), int(value)) for key, value in current_revisions.items()))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ChangeError(f"malformed trusted context: {exc}") from exc
    return TrustedContext(
        approved_by=approved_by,
        approved_capabilities=capabilities,
        capability_scopes=scopes,
        claim_statuses=statuses,
        evidence_digests=digests,
        current_contract_version=current_contract_version,
        current_revisions=revisions,
        current_snapshot=current_snapshot,
    )


def _scope_covered(scope: str, granted: Sequence[str]) -> bool:
    """Whether a declared write scope stays inside the granted contract.

    Verbatim contract patterns always hold. A concrete path holds when it
    matches a granted pattern. Anything else — a wider glob the contract
    never granted — fails closed: declare narrower concrete scopes.
    """
    if scope in granted:
        return True
    if "*" in scope:
        return False
    try:
        return any(scope_matches(scope, pattern) for pattern in granted)
    except WriteScopeError:
        return False


def admit(
    envelope: ChangeEnvelope,
    context: TrustedContext,
) -> AdmissionDecision:
    """Run the deterministic admission check against trusted context.

    Order is fixed: authority, scope grounding, freshness, evidence,
    lineage, shape — the first failure wins, because a forbidden change
    needs no freshness verdict and a stale one needs no scope debate.
    Every verdict field comes from the context, never the envelope: the
    agent can assert anything in its proposal and it changes nothing.
    A malformed context is a harness bug and raises, never admits.
    """
    try:
        approved_capabilities = tuple(context.approved_capabilities)
        granted_scopes = {
            str(capability): tuple(patterns)
            for capability, patterns in context.capability_scopes
        }
        ledger_statuses = dict(context.claim_statuses)
        resolved = dict(context.evidence_digests)
        current_revisions = dict(context.current_revisions)
    except (TypeError, ValueError, AttributeError) as exc:
        raise ChangeError(f"malformed trusted context: {exc}") from exc
    if context.approved_by != APPROVER:
        return _refuse(
            "deny",
            f"Change scope needs {APPROVER}'s explicit approval; "
            f"context carries {context.approved_by!r}.",
        )
    for op in envelope.writes:
        if op.capability not in approved_capabilities:
            return _refuse(
                "deny",
                f"One approval, one scope: {op.capability!r} is outside "
                "the approved capabilities.",
            )
        granted = granted_scopes.get(op.capability, ())
        for scope in op.scopes:
            if not _scope_covered(scope, granted):
                return _refuse(
                    "deny",
                    f"{op.capability!r} claims scope {scope!r} outside "
                    "its capability contract: narrow the declared scopes.",
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
        current_contract_version=context.current_contract_version,
        read_revisions=dict(envelope.read_revisions),
        current_revisions=current_revisions,
    ):
        return _refuse(
            "conflict",
            "Read set is stale: reload the world and replan, never overwrite.",
        )
    if not snapshot_fresh(
        expected_snapshot=envelope.expected_snapshot,
        current_snapshot=context.current_snapshot,
    ):
        return _refuse(
            "conflict",
            "Snapshot mismatch: another write landed first; reload, never "
            "overwrite.",
        )
    for locator in envelope.evidence:
        if resolved.get(locator) is None:
            return _refuse(
                "replan",
                f"Evidence {locator!r} does not resolve: a claim without "
                "resolvable evidence is not a claim to apply.",
            )
    for claim_id in envelope.claims:
        if ledger_statuses.get(claim_id) != "supported":
            return _refuse(
                "conflict",
                f"Claim {claim_id!r} reads no supported lineage in the "
                "live ledger: re-judge it first.",
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
    live: Mapping[str, Mapping[str, object]],
) -> tuple[PostconditionResult, ...]:
    """Evaluate every postcondition against the post-apply world.

    The harness calls this after the gateway applies, with observations
    keyed by selector — validator summaries, re-read route pairs, and
    whatever else a postcondition promised about. Predicate inputs come
    from those live observations, never from the envelope: a promised
    ``RepoClean`` passes only when the actual repository validates
    clean. A promised observation the harness never made raises
    ChangeError: that is a harness bug, not a passing check. Unknown
    predicates raise KeyError: admission refuses malformed envelopes
    first, so anything reaching here malformed is a harness bug, not a
    judgment call.
    """
    results = []
    for check in envelope.postconditions:
        try:
            observed = dict(live[check.selector])
        except (KeyError, TypeError) as exc:
            raise ChangeError(
                f"postcondition on {check.predicate!r} names unobserved "
                f"{check.selector!r}: read the post-apply world first",
            ) from exc
        verdict = evaluate(check.predicate, **observed)
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
