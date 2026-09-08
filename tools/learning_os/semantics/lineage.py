"""Phase-2 semantic lineage: why a derived claim is believed.

A predicate answers; lineage remembers the answer's basis. Every high-value
derived claim carries what it read (artifact revisions, source hashes,
evidence locators), the contract version it was judged under, who judged
and who reviewed it, and a status that moves supported → stale →
supported as the world changes underneath it.

Storage is a receipt-adjacent sidecar, never a canonical edit and never a
projection: ``operations/transactions/lineage.yaml`` follows the
``revisions.yaml`` precedent (one ledger file, schema-validated on load).
A generated projection would evaporate on rebuild; the point of lineage is
surviving one. Backfill is lazy — records are created when a claim is
judged, never bulk-migrated — and only three high-value claim families
earn records (route covers edges, scope-authority judgments, dossier
freshness). Staleness itself delegates to the ``ClaimStale`` predicate, so
there is exactly one definition of stale in the system.

Retraction (Phase 10) layers assumption tracking on top: each record
names the other derived claims it assumed. Invalidating a claim
withdraws everything that assumed it, recursively, in the sidecar only —
canonical data is never touched and nothing re-derives itself.
``retraction_impact`` answers the blast radius before ``withdraw``
applies it. Tracking is forward-only: records judged before this layer
carry no assumptions and cascade only to themselves.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from .predicates import CONTRACT_VERSION, claim_stale

#: The receipt-adjacent sidecar. Canonical records never carry lineage;
#: the manifest never projects it.
LEDGER_RELATIVE = "operations/transactions/lineage.yaml"
SCHEMA_RELATIVE = "system/contracts/semantic-lineage-ledger.schema.json"

LEDGER_SCHEMA_VERSION = 2
LEDGER_TYPE = "semantic-lineage-ledger"

#: The only claim families that earn lineage. Everything else is either
#: cheap to recompute or not believed in the first place.
CLAIM_KINDS = ("route-covers", "scope-authority", "dossier-freshness")

#: Lineage statuses. ``contested`` needs a reviewer, not a recompute;
#: ``withdrawn`` needs a fresh judgment, never a recompute.
STATUSES = ("supported", "stale", "contested", "withdrawn")


class LineageError(ValueError):
    """A lineage record or ledger cannot be read as written."""


@dataclass(frozen=True)
class DerivedFrom:
    """Everything a claim's verdict depended on."""

    contract_version: int
    revisions: tuple[tuple[str, int], ...] = ()
    source_hashes: tuple[tuple[str, str], ...] = ()
    evidence: tuple[str, ...] = ()
    assumes: tuple[str, ...] = ()


@dataclass(frozen=True)
class AdmittedBy:
    """Which admitted gesture this record rides on.

    Both halves are known before apply and stable across idempotent
    replay, unlike the time-based transaction id the service mints
    inside the commit — so the binding survives a replayed apply while
    the receipt still ties it to the concrete transaction.
    """

    request_id: str
    idempotency_key: str


@dataclass(frozen=True)
class ClaimLineage:
    """Why one derived claim is believed, and whether it still is."""

    claim_id: str
    claim_kind: str
    statement: str
    derived_from: DerivedFrom
    judged_by: str
    admitted_by: AdmittedBy
    status: str = "supported"
    reviewed_by: str = ""
    contested_by: str = ""
    contest_reason: str = ""
    supersedes: Mapping[str, object] | None = None


def _reads(lineage: ClaimLineage) -> dict[str, int]:
    return dict(lineage.derived_from.revisions)


def _hashes(lineage: ClaimLineage) -> dict[str, str]:
    return dict(lineage.derived_from.source_hashes)


def _fresh(
    lineage: ClaimLineage,
    current_contract_version: int,
    current_revisions: Mapping[str, int],
    current_source_hashes: Mapping[str, str],
) -> bool:
    """True while every read still matches. Total: malformed maps are stale."""
    if claim_stale(
        read_contract_version=lineage.derived_from.contract_version,
        current_contract_version=current_contract_version,
        read_revisions=_reads(lineage),
        current_revisions=current_revisions,
    ):
        return False
    if not isinstance(current_source_hashes, Mapping):
        return False
    current = current_source_hashes
    try:
        return all(
            key in current and current[key] == digest
            for key, digest in _hashes(lineage).items()
        )
    except TypeError:
        return False


def record_claim(
    *,
    claim_id: str,
    claim_kind: str,
    statement: str,
    contract_version: int = CONTRACT_VERSION,
    revisions: Mapping[str, int] | None = None,
    source_hashes: Mapping[str, str] | None = None,
    evidence: Sequence[str] = (),
    assumes: Sequence[str] = (),
    judged_by: str,
    admitted_by: Mapping[str, str],
    supersedes: Mapping[str, object] | None = None,
) -> ClaimLineage:
    """Judge a claim now: record what was read, by whom, as supported.

    Prospective records always name their admission — an unbound record
    cannot enter the ledger through a gateway, so construction refuses
    one. Repairs pass the prior record as ``supersedes``; the old state
    rides along instead of being erased.
    """
    if not isinstance(claim_id, str) or not claim_id.strip():
        raise LineageError("a lineage record needs a non-empty claim id")
    if claim_kind not in CLAIM_KINDS:
        raise LineageError(
            f"claim kind {claim_kind!r} earns no lineage; "
            f"high-value kinds are {', '.join(CLAIM_KINDS)}"
        )
    if not isinstance(statement, str) or not statement.strip():
        raise LineageError("a lineage record needs the claim in words")
    if not isinstance(judged_by, str) or not judged_by.strip():
        raise LineageError("a lineage record needs its judge")
    try:
        admission = AdmittedBy(
            request_id=str(admitted_by["request_id"]),
            idempotency_key=str(admitted_by["idempotency_key"]),
        )
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise LineageError(
            f"a lineage record needs its admission (request_id + "
            f"idempotency_key): {exc}"
        ) from exc
    if not admission.request_id.strip() or not admission.idempotency_key.strip():
        raise LineageError("a lineage record needs a non-empty admission")
    prior: Mapping[str, object] | None = None
    if supersedes is not None:
        if not isinstance(supersedes, Mapping):
            raise LineageError("supersedes must be the prior record mapping")
        for key in ("claim_id", "claim_kind", "statement"):
            if not isinstance(supersedes.get(key), str) or not str(supersedes[key]).strip():
                raise LineageError(
                    f"supersedes names no prior {key} for {claim_id!r}")
        prior = dict(supersedes)
    try:
        revision_pairs = tuple(
            sorted((str(key), int(value)) for key, value in (revisions or {}).items())
        )
        hash_pairs = tuple(
            sorted((str(key), str(value)) for key, value in (source_hashes or {}).items())
        )
        trails = tuple(str(locator) for locator in evidence)
    except (TypeError, ValueError) as exc:
        raise LineageError(f"malformed reads for {claim_id!r}: {exc}") from exc
    if isinstance(assumes, str) or not isinstance(assumes, Sequence):
        raise LineageError(f"malformed assumptions for {claim_id!r}")
    dependencies = tuple(str(claim) for claim in assumes)
    if any(not dep.strip() for dep in dependencies):
        raise LineageError(f"assumptions name claims for {claim_id!r}")
    if claim_id in dependencies:
        raise LineageError(f"a claim cannot assume itself: {claim_id!r}")
    return ClaimLineage(
        claim_id=claim_id,
        claim_kind=claim_kind,
        statement=statement,
        derived_from=DerivedFrom(
            contract_version=contract_version,
            revisions=revision_pairs,
            source_hashes=hash_pairs,
            evidence=trails,
            assumes=dependencies,
        ),
        judged_by=judged_by,
        admitted_by=admission,
        status="supported",
        supersedes=prior,
    )


def supersede(
    prior: ClaimLineage,
    *,
    statement: str,
    revisions: Mapping[str, int] | None = None,
    source_hashes: Mapping[str, str] | None = None,
    evidence: Sequence[str] = (),
    assumes: Sequence[str] = (),
    judged_by: str,
    admitted_by: Mapping[str, str],
) -> ClaimLineage:
    """Repair a claim without destroying why the old state existed.

    The fresh judgment carries the prior record as ``supersedes``; the
    prior fields are preserved, not withdrawn — withdrawal stays for
    genuine invalidation with its assumption cascade.
    """
    return record_claim(
        claim_id=prior.claim_id,
        claim_kind=prior.claim_kind,
        statement=statement,
        revisions=revisions,
        source_hashes=source_hashes,
        evidence=evidence,
        assumes=assumes,
        judged_by=judged_by,
        admitted_by=admitted_by,
        supersedes=to_dict(prior),
    )


def refresh(
    lineage: ClaimLineage,
    current_contract_version: int,
    current_revisions: Mapping[str, int],
    current_source_hashes: Mapping[str, str] | None = None,
) -> ClaimLineage:
    """Re-examine a claim against the current world.

    A contested claim stays contested — disagreement needs a reviewer, not
    a recompute. A withdrawn claim stays withdrawn — invalidation is a
    judgment, and only a fresh judgment lifts it. Otherwise the status
    follows the reads: supported while everything matches, stale the
    moment anything moved.
    """
    if lineage.status in ("contested", "withdrawn"):
        return lineage
    fresh = _fresh(
        lineage, current_contract_version,
        current_revisions, current_source_hashes or {},
    )
    status = "supported" if fresh else "stale"
    return replace(lineage, status=status)


def contest(
    lineage: ClaimLineage, *, contested_by: str, reason: str,
) -> ClaimLineage:
    """Mark disagreement: a reviewer disputes the verdict itself."""
    if lineage.status == "withdrawn":
        raise LineageError("a withdrawn claim needs re-judgment, not contest")
    if not isinstance(contested_by, str) or not contested_by.strip():
        raise LineageError("a contest needs its reviewer")
    if not isinstance(reason, str) or not reason.strip():
        raise LineageError("a contest needs its reason")
    return replace(
        lineage,
        status="contested",
        contested_by=contested_by,
        contest_reason=reason,
    )


def endorse(lineage: ClaimLineage, *, reviewer: str) -> ClaimLineage:
    """A reviewer re-examines and stands behind the claim: supported."""
    if lineage.status == "withdrawn":
        raise LineageError(
            "a withdrawn claim needs re-judgment, not endorsement")
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise LineageError("an endorsement needs its reviewer")
    return replace(
        lineage,
        status="supported",
        reviewed_by=reviewer,
        contested_by="",
        contest_reason="",
    )


def impacted(
    lineages: Sequence[ClaimLineage],
    current_contract_version: int,
    current_revisions: Mapping[str, int],
    current_source_hashes: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    """Which claims go stale under the current world: the impact query.

    Answers "what depends on node-rev X / source-hash Y" by re-examining
    every record: contested and withdrawn claims are reported as-is (they
    already need a human), everything else exactly when its reads moved.
    """
    hashes = current_source_hashes or {}
    return tuple(
        lineage.claim_id
        for lineage in lineages
        if lineage.status in ("contested", "withdrawn")
        or refresh(
            lineage, current_contract_version, current_revisions, hashes,
        ).status == "stale"
    )


def retraction_impact(
    lineages: Sequence[ClaimLineage],
    claim_id: str,
) -> tuple[str, ...]:
    """The full retraction cascade for invalidating one claim, root first.

    Breadth-first over assumption edges: the claim, its direct
    dependents, then theirs. Neighbors sort for determinism. Read-only:
    nothing is marked. Records judged before assumption tracking carry
    no assumptions and cascade only to themselves — the forward-only
    limit, stated plainly.
    """
    known = {lineage.claim_id for lineage in lineages}
    if claim_id not in known:
        raise LineageError(f"no lineage for claim {claim_id!r}")
    dependents: dict[str, list[str]] = {}
    for lineage in lineages:
        for assumption in lineage.derived_from.assumes:
            dependents.setdefault(assumption, []).append(lineage.claim_id)
    cascade = [claim_id]
    seen = {claim_id}
    queue = [claim_id]
    while queue:
        for dependent in sorted(set(dependents.get(queue.pop(0), ()))):
            if dependent not in seen:
                seen.add(dependent)
                cascade.append(dependent)
                queue.append(dependent)
    return tuple(cascade)


def withdraw(
    lineages: Sequence[ClaimLineage],
    claim_id: str,
) -> tuple[ClaimLineage, ...]:
    """Invalidate a claim and everything that assumed it, recursively.

    Marks the full ``retraction_impact`` cascade withdrawn, preserving
    every other field; input order holds. Idempotent: withdrawing twice
    changes nothing the second time, and withdrawing A then B equals
    withdrawing B then A. The sidecar only: canonical data is untouched,
    nothing re-derives, and a withdrawn claim returns only through a
    fresh judgment.
    """
    cascade = set(retraction_impact(lineages, claim_id))
    return tuple(
        replace(lineage, status="withdrawn")
        if lineage.claim_id in cascade
        else lineage
        for lineage in lineages
    )


# ---- emission: the three high-value claim families --------------------------


def emit_route_covers(
    *,
    route_id: str,
    covers: Sequence[str],
    read_revisions: Mapping[str, int],
    judged_by: str,
    admitted_by: Mapping[str, str],
    evidence: Sequence[str] = (),
    assumes: Sequence[str] = (),
    supersedes: Mapping[str, object] | None = None,
    source_hashes: Mapping[str, str] | None = None,
) -> ClaimLineage:
    """Lineage for a route `covers` edge: which nodes, read from what."""
    try:
        nodes = ", ".join(sorted(set(str(node) for node in covers)))
    except TypeError as exc:
        raise LineageError(f"malformed covers edge for {route_id!r}") from exc
    return record_claim(
        claim_id=f"covers:{route_id}",
        claim_kind="route-covers",
        statement=f"{route_id} covers {nodes}" if nodes else f"{route_id} covers nothing",
        revisions=read_revisions,
        source_hashes=source_hashes,
        judged_by=judged_by,
        admitted_by=admitted_by,
        evidence=evidence,
        assumes=assumes,
        supersedes=supersedes,
    )


def emit_scope_authority(
    *,
    fact_kind: str,
    owner: str,
    read_revisions: Mapping[str, int],
    judged_by: str,
    admitted_by: Mapping[str, str],
    evidence: Sequence[str] = (),
    assumes: Sequence[str] = (),
    supersedes: Mapping[str, object] | None = None,
) -> ClaimLineage:
    """Lineage for a scope-authority judgment: who owns this fact."""
    return record_claim(
        claim_id=f"scope:{fact_kind}:{owner}",
        claim_kind="scope-authority",
        statement=f"{fact_kind} is owned by {owner}",
        revisions=read_revisions,
        judged_by=judged_by,
        admitted_by=admitted_by,
        evidence=evidence,
        assumes=assumes,
        supersedes=supersedes,
    )


def emit_dossier_freshness(
    *,
    dossier_key: str,
    hashes: Mapping[str, str],
    judged_by: str,
    admitted_by: Mapping[str, str],
    assumes: Sequence[str] = (),
    supersedes: Mapping[str, object] | None = None,
) -> ClaimLineage:
    """Lineage for a dossier-freshness judgment: fresh at these hashes."""
    return record_claim(
        claim_id=f"dossier:{dossier_key}",
        claim_kind="dossier-freshness",
        statement=f"{dossier_key} is fresh",
        source_hashes=hashes,
        judged_by=judged_by,
        admitted_by=admitted_by,
        assumes=assumes,
        supersedes=supersedes,
    )


# ---- sidecar ledger ---------------------------------------------------------


def to_dict(lineage: ClaimLineage) -> dict:
    """The sidecar shape, validated by the ledger schema on load."""
    record: dict = {
        "claim_id": lineage.claim_id,
        "claim_kind": lineage.claim_kind,
        "statement": lineage.statement,
        "derived_from": {
            "contract_version": lineage.derived_from.contract_version,
            "revisions": dict(lineage.derived_from.revisions),
            "source_hashes": dict(lineage.derived_from.source_hashes),
            "evidence": list(lineage.derived_from.evidence),
            "assumes": list(lineage.derived_from.assumes),
        },
        "judged_by": lineage.judged_by,
        "admitted_by": {
            "request_id": lineage.admitted_by.request_id,
            "idempotency_key": lineage.admitted_by.idempotency_key,
        },
        "reviewed_by": lineage.reviewed_by,
        "status": lineage.status,
    }
    if lineage.supersedes is not None:
        record["supersedes"] = dict(lineage.supersedes)
    if lineage.status == "contested":
        record["contest"] = {
            "by": lineage.contested_by,
            "reason": lineage.contest_reason,
        }
    return record


def from_dict(record: dict) -> ClaimLineage:
    """Rebuild a record the sidecar shape guarantees. Raises LineageError."""
    try:
        derived = record["derived_from"]
        contest = record.get("contest") or {}
        admission = record["admitted_by"]
        prior = record.get("supersedes")
        if prior is not None:
            if not isinstance(prior, dict):
                raise LineageError("supersedes must be the prior record mapping")
            for key in ("claim_id", "claim_kind", "statement"):
                if not isinstance(prior.get(key), str) or not str(prior[key]).strip():
                    raise LineageError(f"supersedes names no prior {key}")
        return ClaimLineage(
            claim_id=str(record["claim_id"]),
            claim_kind=str(record["claim_kind"]),
            statement=str(record["statement"]),
            derived_from=DerivedFrom(
                contract_version=int(derived["contract_version"]),
                revisions=tuple(sorted(
                    (str(key), int(value))
                    for key, value in dict(derived["revisions"]).items()
                )),
                source_hashes=tuple(sorted(
                    (str(key), str(value))
                    for key, value in dict(derived["source_hashes"]).items()
                )),
                evidence=tuple(
                    str(locator) for locator in derived["evidence"]
                ),
                assumes=tuple(
                    str(claim) for claim in (derived.get("assumes") or ())
                ),
            ),
            judged_by=str(record["judged_by"]),
            admitted_by=AdmittedBy(
                request_id=str(admission["request_id"]),
                idempotency_key=str(admission["idempotency_key"]),
            ),
            status=str(record.get("status") or "supported"),
            reviewed_by=str(record.get("reviewed_by") or ""),
            contested_by=str(contest.get("by") or ""),
            contest_reason=str(contest.get("reason") or ""),
            supersedes=dict(prior) if prior is not None else None,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise LineageError(f"malformed lineage record: {exc}") from exc


def _schema(root: Path) -> dict:
    path = root / SCHEMA_RELATIVE
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LineageError(f"cannot read {SCHEMA_RELATIVE}: {exc}") from exc


def check_assumptions(records: Mapping[str, ClaimLineage]) -> None:
    """Validate cross-record assumption integrity. Raises LineageError.

    Every assumption must name a claim in the same ledger
    (LINEAGE-ASSUMPTION-MISSING), and the assumption graph must be
    acyclic (LINEAGE-ASSUMPTION-CYCLE) — a cycle would make every
    cascade infinite and every blast radius the whole ledger.
    Single-record construction cannot check this; the ledger load must.
    """
    for claim_id, lineage in records.items():
        for assumption in lineage.derived_from.assumes:
            if assumption not in records:
                raise LineageError(
                    f"LINEAGE-ASSUMPTION-MISSING: claim {claim_id!r} "
                    f"assumes unknown {assumption!r}")
    visiting: set[str] = set()
    settled: set[str] = set()

    def visit(node: str) -> bool:
        if node in settled:
            return False
        if node in visiting:
            return True
        visiting.add(node)
        if any(visit(dep) for dep in records[node].derived_from.assumes):
            return True
        visiting.discard(node)
        settled.add(node)
        return False

    for claim_id in records:
        if visit(claim_id):
            raise LineageError(
                "LINEAGE-ASSUMPTION-CYCLE: assumption edges cycle; "
                f"no order satisfies them (at {claim_id!r})")


def load_ledger(root: Path) -> dict[str, ClaimLineage]:
    """Read the sidecar. A missing ledger is an empty one — lazy backfill."""
    path = root / LEDGER_RELATIVE
    if not path.is_file():
        return {}
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise LineageError(f"cannot read {LEDGER_RELATIVE}: {exc}") from exc
    if not isinstance(raw, dict):
        raise LineageError(f"{LEDGER_RELATIVE} is not a mapping")
    errors = sorted(
        Draft202012Validator(_schema(root)).iter_errors(raw),
        key=lambda error: [str(part) for part in error.absolute_path],
    )
    if errors:
        first = errors[0]
        location = "/".join(str(part) for part in first.absolute_path)
        raise LineageError(
            f"{LEDGER_RELATIVE} violates its schema at {location or '<root>'}: "
            f"{first.message}"
        )
    records = {}
    for claim_id, record in raw["records"].items():
        lineage = from_dict(record)
        if lineage.claim_id != claim_id:
            raise LineageError(
                f"{LEDGER_RELATIVE} renames claim {claim_id!r} "
                f"to {lineage.claim_id!r}"
            )
        records[claim_id] = lineage
    check_assumptions(records)
    return records


def dump_ledger(records: Mapping[str, ClaimLineage]) -> str:
    """Render the sidecar. The caller writes; this module never touches disk."""
    return yaml.safe_dump(
        {
            "schema_version": LEDGER_SCHEMA_VERSION,
            "type": LEDGER_TYPE,
            "records": {
                claim_id: to_dict(records[claim_id])
                for claim_id in sorted(records)
            },
        },
        sort_keys=False,
        allow_unicode=True,
    )
