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

LEDGER_SCHEMA_VERSION = 1
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
class ClaimLineage:
    """Why one derived claim is believed, and whether it still is."""

    claim_id: str
    claim_kind: str
    statement: str
    derived_from: DerivedFrom
    judged_by: str
    status: str = "supported"
    reviewed_by: str = ""
    contested_by: str = ""
    contest_reason: str = ""


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
) -> ClaimLineage:
    """Judge a claim now: record what was read, by whom, as supported."""
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
        status="supported",
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
    return ClaimLineage(
        claim_id=lineage.claim_id,
        claim_kind=lineage.claim_kind,
        statement=lineage.statement,
        derived_from=lineage.derived_from,
        judged_by=lineage.judged_by,
        status=status,
        reviewed_by=lineage.reviewed_by,
        contested_by=lineage.contested_by,
        contest_reason=lineage.contest_reason,
    )


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
    return ClaimLineage(
        claim_id=lineage.claim_id,
        claim_kind=lineage.claim_kind,
        statement=lineage.statement,
        derived_from=lineage.derived_from,
        judged_by=lineage.judged_by,
        status="contested",
        reviewed_by=lineage.reviewed_by,
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
    return ClaimLineage(
        claim_id=lineage.claim_id,
        claim_kind=lineage.claim_kind,
        statement=lineage.statement,
        derived_from=lineage.derived_from,
        judged_by=lineage.judged_by,
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
    evidence: Sequence[str] = (),
    assumes: Sequence[str] = (),
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
        judged_by=judged_by,
        evidence=evidence,
        assumes=assumes,
    )


def emit_scope_authority(
    *,
    fact_kind: str,
    owner: str,
    read_revisions: Mapping[str, int],
    judged_by: str,
    evidence: Sequence[str] = (),
    assumes: Sequence[str] = (),
) -> ClaimLineage:
    """Lineage for a scope-authority judgment: who owns this fact."""
    return record_claim(
        claim_id=f"scope:{fact_kind}:{owner}",
        claim_kind="scope-authority",
        statement=f"{fact_kind} is owned by {owner}",
        revisions=read_revisions,
        judged_by=judged_by,
        evidence=evidence,
        assumes=assumes,
    )


def emit_dossier_freshness(
    *,
    dossier_key: str,
    hashes: Mapping[str, str],
    judged_by: str,
    assumes: Sequence[str] = (),
) -> ClaimLineage:
    """Lineage for a dossier-freshness judgment: fresh at these hashes."""
    return record_claim(
        claim_id=f"dossier:{dossier_key}",
        claim_kind="dossier-freshness",
        statement=f"{dossier_key} is fresh",
        source_hashes=hashes,
        judged_by=judged_by,
        assumes=assumes,
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
        "reviewed_by": lineage.reviewed_by,
        "status": lineage.status,
    }
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
            status=str(record.get("status") or "supported"),
            reviewed_by=str(record.get("reviewed_by") or ""),
            contested_by=str(contest.get("by") or ""),
            contest_reason=str(contest.get("reason") or ""),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise LineageError(f"malformed lineage record: {exc}") from exc


def _schema(root: Path) -> dict:
    path = root / SCHEMA_RELATIVE
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LineageError(f"cannot read {SCHEMA_RELATIVE}: {exc}") from exc


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
