"""Pure, frozen claim/basis audit authorization and result validation."""

from __future__ import annotations

import hashlib
import json
import random
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

SAMPLE_SIZE = 30
ALGORITHM = "python-mt19937-shuffle-v1"
_HEX = re.compile(r"[0-9a-f]{64}")


class AuditError(ValueError):
    """An audit cannot prove its frozen population, draw or result."""


@dataclass(frozen=True, order=True)
class ClaimBasis:
    claim_id: str
    basis: str

    def payload(self) -> dict[str, str]:
        return {"claim_id": self.claim_id, "basis": self.basis}


def _pairs(value: object, label: str) -> tuple[ClaimBasis, ...]:
    if not isinstance(value, list):
        raise AuditError(f"audit {label} must be a list of claim/basis pairs")
    rows: list[ClaimBasis] = []
    for item in value:
        if not isinstance(item, dict) or set(item) != {"claim_id", "basis"}:
            raise AuditError(f"audit {label} contains a malformed claim/basis pair")
        cid, basis = item["claim_id"], item["basis"]
        if not isinstance(cid, str) or not cid.startswith("covers:") or not cid[7:] or any(c.isspace() for c in cid):
            raise AuditError(f"audit {label} needs exact covers claim ids")
        if not isinstance(basis, str) or _HEX.fullmatch(basis) is None:
            raise AuditError(f"audit {label} needs full basis digests")
        rows.append(ClaimBasis(cid, basis))
    if len(set(rows)) != len(rows) or len({p.claim_id for p in rows}) != len(rows):
        raise AuditError(f"audit {label} repeats a claim")
    return tuple(rows)


def pool_digest(pool: Sequence[ClaimBasis]) -> str:
    canonical = [pair.payload() for pair in sorted(pool)]
    return hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def audit_id(pool: Sequence[ClaimBasis]) -> str:
    return "claims-audit:" + pool_digest(pool)


def sample_pool(pool: Sequence[ClaimBasis], seed: str) -> tuple[ClaimBasis, ...]:
    if _HEX.fullmatch(seed) is None:
        raise AuditError("audit seed must contain 256 bits as 64 lowercase hex digits")
    if len(pool) < SAMPLE_SIZE:
        raise AuditError(f"audit pool needs at least {SAMPLE_SIZE} claims")
    rows = sorted(pool)
    random.Random(int(seed, 16)).shuffle(rows)
    return tuple(rows[:SAMPLE_SIZE])


@dataclass(frozen=True)
class AuditAuthorization:
    pool: tuple[ClaimBasis, ...]
    seed: str
    sample: tuple[ClaimBasis, ...]

    @property
    def goal_id(self) -> str:
        return audit_id(self.pool)

    def payload(self) -> dict[str, object]:
        return {"pool": [pair.payload() for pair in self.pool], "pool_sha256": pool_digest(self.pool),
                "seed": self.seed, "algorithm": ALGORITHM,
                "sample": [pair.payload() for pair in self.sample]}


def authorization_from_mapping(value: object) -> AuditAuthorization:
    if not isinstance(value, dict) or set(value) != {"pool", "pool_sha256", "seed", "algorithm", "sample"}:
        raise AuditError("audit authorization needs exactly pool, pool_sha256, seed, algorithm and sample")
    pool, sample = _pairs(value["pool"], "pool"), _pairs(value["sample"], "sample")
    seed = value["seed"]
    if tuple(sorted(pool)) != pool or value["pool_sha256"] != pool_digest(pool):
        raise AuditError("audit pool is not canonical or its full digest differs")
    if value["algorithm"] != ALGORITHM or not isinstance(seed, str):
        raise AuditError("audit sampling algorithm or seed is unsupported")
    if sample != sample_pool(pool, seed):
        raise AuditError("audit sample does not reproduce its frozen pool and seed")
    return AuditAuthorization(pool, seed, sample)


@dataclass(frozen=True)
class AuditResult:
    sample: tuple[ClaimBasis, ...]
    defects: tuple[ClaimBasis, ...]
    reviewer: str
    report_path: str
    report_sha256: str

    def payload(self) -> dict[str, object]:
        return {"sample": [pair.payload() for pair in self.sample],
                "defects": [pair.payload() for pair in self.defects],
                "reviewer": self.reviewer, "report_path": self.report_path,
                "report_sha256": self.report_sha256}


def result_from_mapping(value: object, authorization: AuditAuthorization) -> AuditResult:
    if not isinstance(value, dict) or set(value) != {"sample", "defects", "reviewer", "report_path", "report_sha256"}:
        raise AuditError("audit result needs exactly sample, defects, reviewer, report_path and report_sha256")
    sample, defects = _pairs(value["sample"], "sample"), _pairs(value["defects"], "defects")
    if sample != authorization.sample or not set(defects).issubset(sample):
        raise AuditError("audit result changes the authorized sample or names an unsampled defect")
    reviewer, path, digest = value["reviewer"], value["report_path"], value["report_sha256"]
    if not isinstance(reviewer, str) or not reviewer.strip() or not isinstance(path, str) or not path.strip():
        raise AuditError("audit result needs its actual reviewer and report path")
    if not isinstance(digest, str) or _HEX.fullmatch(digest.removeprefix("sha256:")) is None:
        raise AuditError("audit result needs a full report digest")
    return AuditResult(sample, defects, reviewer, path, digest)


@dataclass(frozen=True)
class AuditRecord:
    authorization: AuditAuthorization
    result: AuditResult | None = None
    authorization_reviewed_sha256: str = ""
    result_reviewed_sha256: str = ""
    authorization_intent_sha256: str = ""
    result_intent_sha256: str = ""

    def payload(self) -> dict[str, object]:
        out: dict[str, object] = {"authorization": self.authorization.payload()}
        if self.result is not None:
            out["result"] = self.result.payload()
        if self.authorization_reviewed_sha256:
            out["authorization_reviewed_sha256"] = self.authorization_reviewed_sha256
        if self.result_reviewed_sha256:
            out["result_reviewed_sha256"] = self.result_reviewed_sha256
        if self.authorization_intent_sha256:
            out["authorization_intent_sha256"] = self.authorization_intent_sha256
        if self.result_intent_sha256:
            out["result_intent_sha256"] = self.result_intent_sha256
        return out


def audit_records(value: object) -> dict[str, AuditRecord]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise AuditError("goal ledger audits must be a mapping")
    records: dict[str, AuditRecord] = {}
    for goal_id, raw in value.items():
        if not isinstance(goal_id, str) or not isinstance(raw, dict) or not set(raw).issubset({
                "authorization", "result", "authorization_reviewed_sha256", "result_reviewed_sha256",
                "authorization_intent_sha256", "result_intent_sha256"}):
            raise AuditError("goal ledger contains a malformed audit")
        authorization = authorization_from_mapping(raw.get("authorization"))
        if goal_id != authorization.goal_id:
            raise AuditError("audit id does not bind its full pool")
        result = result_from_mapping(raw["result"], authorization) if "result" in raw else None
        proofs = []
        for key in ("authorization_reviewed_sha256", "result_reviewed_sha256",
                    "authorization_intent_sha256", "result_intent_sha256"):
            proof = raw.get(key, "")
            if not isinstance(proof, str) or (proof and re.fullmatch(r"sha256:[0-9a-f]{64}", proof) is None):
                raise AuditError("audit replay proof must be a full reviewed digest")
            proofs.append(proof)
        if bool(proofs[0]) != bool(proofs[2]) or bool(proofs[1]) != bool(proofs[3]):
            raise AuditError("audit replay evidence needs both its reviewed hash and exact intent")
        if result is None and (proofs[1] or proofs[3]):
            raise AuditError("audit result replay evidence has no immutable result")
        records[goal_id] = AuditRecord(authorization, result, *proofs)
    return records


def audits_from_ledger(value: object) -> dict[str, AuditRecord]:
    """Validate only the audit evidence boundary in an observed ledger."""
    if not isinstance(value, dict) or not isinstance(value.get("decisions"), dict):
        raise AuditError("cannot read preserved audit state: goal ledger needs a decisions mapping")
    return audit_records(value.get("audits"))


def memberships(records: Mapping[str, AuditRecord]) -> tuple[frozenset[tuple[str, str]], frozenset[tuple[str, str]]]:
    certified: set[tuple[str, str]] = set()
    defective: set[tuple[str, str]] = set()
    for record in records.values():
        if record.result is not None:
            if not record.result.defects:
                certified.update((p.claim_id, p.basis) for p in record.authorization.pool)
            else:
                defective.update((p.claim_id, p.basis) for p in record.result.defects)
    return frozenset(certified), frozenset(defective)


class AuditCandidate(Protocol):
    @property
    def claim_id(self) -> str: ...
    @property
    def basis(self) -> str: ...
    @property
    def status(self) -> str: ...
    @property
    def audit(self) -> str: ...


def eligible_pool(claims: Iterable[AuditCandidate]) -> tuple[ClaimBasis, ...]:
    return tuple(sorted(ClaimBasis(row.claim_id, row.basis) for row in claims
                        if row.claim_id.startswith("covers:") and row.status == "supported"
                        and row.audit != "audited"))
