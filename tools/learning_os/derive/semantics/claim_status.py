"""Shared, bounded observations and claim-status interpretation.

Only the selected claims and their assumption closure resolve evidence. Stable
judgment identity excludes restamps; occurrence identity includes current drift.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from pathlib import Path

from learning_os.derive.semantics.claim_audits import (
    AuditError,
    AuditRecord,
    audits_from_ledger,
    memberships,
)
from learning_os.derive.semantics.lineage import (
    NODE_CONTENT_PREFIX,
    ROUTE_CONTENT_PREFIX,
    ClaimLineage,
    LineageError,
    effective_statuses,
    load_ledger,
    node_content_digest,
    route_content_digest,
)
from learning_os.derive.semantics.predicates import CONTRACT_VERSION
from learning_os.domain.failures import TransactionFailure
from learning_os.domain.route_identity import route_with_identity
from learning_os.domain.snapshot import Repo
from learning_os.store.layout import PathBoundaryError, resolve_symlinks_inside
from learning_os.store.loader import load_repo
from learning_os.store.loading.yamlio import LoaderError, load_yaml
from learning_os.store.materials.resolution import stable_checksum
from learning_os.store.revisions import load_revisions

REVISIONS_RELATIVE = "operations/transactions/revisions.yaml"


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":")).encode()).hexdigest()


def judgment_basis(row: ClaimLineage) -> str:
    """One judgment, unchanged by read-shape-only restamping or review."""
    return _digest({"statement": row.statement, "evidence": row.derived_from.evidence,
                    "judged_by": row.judged_by,
                    "admitted_by": {"request_id": row.admitted_by.request_id,
                                    "idempotency_key": row.admitted_by.idempotency_key}})


@dataclass(frozen=True)
class ClaimStatus:
    claim_id: str
    status: str
    basis: str = ""
    occurrence: str = ""
    causes: tuple[str, ...] = ()
    moved: tuple[str, ...] = ()
    unit_id: str = ""
    audit: str = "unaudited"

    @property
    def goal_id(self) -> str:
        detector = ("lineage-stale" if self.status == "stale" else
                    "claims-needing-review" if self.status == "contested" or self.audit == "defective" else "")
        return f"{detector}:{self.claim_id}@{self.occurrence}" if detector else ""

    def payload(self) -> dict[str, object]:
        command = f"unit-plan-revise {self.unit_id} --file REVISION.yaml --check" if self.unit_id else ""
        return {"status": self.status, "basis": self.basis, "causes": list(self.causes),
                "audit": self.audit, "goal_id": self.goal_id, "next": command if self.goal_id else "",
                "authorize": f"goal {self.goal_id} --authorize" if self.goal_id else ""}


def interpret_claims(records: Mapping[str, ClaimLineage], revisions: Mapping[str, int],
                     hashes: Mapping[str, str], *, units: Mapping[str, str] | None = None,
                     certified: frozenset[tuple[str, str]] = frozenset(),
                     defective: frozenset[tuple[str, str]] = frozenset()) -> dict[str, ClaimStatus]:
    """Pure status, cause and occurrence calculation, delegating truth to lineage."""
    effective = effective_statuses(records, CONTRACT_VERSION, revisions, hashes)
    facts: dict[str, dict[str, object]] = {}
    for cid, row in records.items():
        drift: dict[str, object] = {}
        for key, old in row.derived_from.revisions:
            if revisions.get(key) != old:
                drift[key] = {"was": old, "now": revisions.get(key)}
        for key, old_hash in row.derived_from.source_hashes:
            if hashes.get(key) != old_hash:
                drift[key] = {"was": old_hash, "now": hashes.get(key)}
        if row.derived_from.contract_version != CONTRACT_VERSION:
            drift["contract-version"] = {"was": row.derived_from.contract_version, "now": CONTRACT_VERSION}
        facts[cid] = drift

    def dependency_facts(cid: str) -> dict[str, object]:
        row = records[cid]
        return {"basis": judgment_basis(row), "status": effective[cid].status,
                "drift": facts[cid], "blocked": {
                    dep: dependency_facts(dep) for dep in effective[cid].blocked_by}}

    out: dict[str, ClaimStatus] = {}
    for cid, row in records.items():
        basis = judgment_basis(row)
        verdict = effective[cid]
        moved = tuple(sorted(set(facts[cid]) | set(verdict.blocked_by)))
        causes: set[str] = set()
        if verdict.status == "stale":
            for key in facts[cid]:
                causes.add("route-edited" if key.startswith(ROUTE_CONTENT_PREFIX) else
                           "node-changed" if key.startswith(NODE_CONTENT_PREFIX) else
                           "contract-version" if key == "contract-version" else "evidence-changed")
            if row.claim_kind == "route-covers" and not any(
                    key.startswith(ROUTE_CONTENT_PREFIX) for key, _ in row.derived_from.source_hashes):
                causes.add("coarse-pin")
            if verdict.blocked_by:
                causes.add("assumption-blocked")
        audit = "defective" if (cid, basis) in defective else "audited" if (cid, basis) in certified else "unaudited"
        occurrence = _digest(dependency_facts(cid)) if verdict.status == "stale" else basis
        out[cid] = ClaimStatus(cid, verdict.status, basis, occurrence, tuple(sorted(causes)),
                               moved, (units or {}).get(cid, ""), audit)
    return out


def read_optional_yaml(path: Path) -> object:
    """Read optional semantic evidence, leaving unreadable input unavailable."""
    try:
        return load_yaml(path, path.parent)
    except (OSError, UnicodeError, LoaderError):
        return None


def current_revisions(root: Path) -> dict[str, int]:
    try:
        return load_revisions(root)
    except TransactionFailure as exc:
        raise LineageError(str(exc)) from exc


def scan_manifest_files(root: Path) -> dict[str, object]:
    """Live materials-manifest files map, or {} when unreadable."""
    data = read_optional_yaml(root / "records" / "materials-manifest.yaml")
    files = data.get("files") if isinstance(data, dict) else None
    return {str(k): v for k, v in files.items()} if isinstance(files, dict) else {}


def live_claim_digests(repo: Repo, keys: set[str] | None = None) -> tuple[dict[str, str], dict[str, str]]:
    """Live route-row and knowledge-node digests, keyed by claim-read key.

    Mirrors the Phase B digest binding in ``commands.module``: one entry
    per stored route row and per knowledge node. An id claimed twice with
    different digests resolves to no digest — the scan never invents
    ownership, and the affected claims fail closed to stale.
    """
    routes: dict[str, str] = {}
    dropped_routes: set[str] = set()
    maps = getattr(repo, "module_source_maps", {}) or {}
    for module_id, smap in maps.items():
        if not isinstance(smap, dict):
            continue
        for src in smap.get("sources") or []:
            if not isinstance(src, dict):
                continue
            source_id = str(src.get("source_id") or "")
            for row in src.get("unit_routes") or []:
                if not isinstance(row, dict):
                    continue
                row = route_with_identity(str(module_id), source_id, row)
                key = ROUTE_CONTENT_PREFIX + str(row["id"])
                if (keys is not None and key not in keys) or key in dropped_routes:
                    continue
                digest = route_content_digest(
                    module_id=str(module_id), source_id=source_id, route=row)
                if key in routes and routes[key] != digest:
                    del routes[key]
                    dropped_routes.add(key)
                else:
                    routes[key] = digest
    nodes: dict[str, str] = {}
    dropped_nodes: set[str] = set()
    for unit in (getattr(repo, "units", {}) or {}).values():
        data = getattr(unit, "data", None)
        if not isinstance(data, dict):
            continue
        knowledge = data.get("knowledge_map")
        rows = knowledge.get("nodes") if isinstance(knowledge, dict) else None
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict) or not str(row.get("id") or "").strip():
                continue
            key = NODE_CONTENT_PREFIX + str(row["id"])
            if (keys is not None and key not in keys) or key in dropped_nodes:
                continue
            digest = node_content_digest(row)
            if key in nodes and nodes[key] != digest:
                del nodes[key]
                dropped_nodes.add(key)
            else:
                nodes[key] = digest
    return routes, nodes


def live_evidence_digest(root: Path, key: str, manifest_files: Mapping[str, object], *, repo: Repo | None = None,
                         route_digests: dict[str, str] | None = None,
                         node_digests: dict[str, str] | None = None) -> str | None:
    """Resolve one stored source-hash key against live bytes.

    Material-synthesis basis keys use the publisher's evidential fields and live
    local bytes, excluding prose and revision-only changes. Mirrors the Phase B
    digest binding in ``commands.module``: manifest keys
    read the registered checksum, file keys hash current bytes inside the
    repository, route-content and node-content keys hash the live route row
    and knowledge node the covers judgment read. Returns ``None`` when the
    dependency is missing, escapes, unreadable, or in an unknown namespace.
    Callers treat ``None`` as stale: an unsupported namespace has no
    trustworthy live value.
    """
    if key.startswith("source-material:"):
        repo = repo if repo is not None else load_repo(root)
        source: object = repo.sources.get(key.removeprefix("source-material:"))
        return stable_checksum({"material": source.get("material")}) if isinstance(source, dict) else None
    if key.startswith(ROUTE_CONTENT_PREFIX) or key.startswith(NODE_CONTENT_PREFIX):
        if route_digests is None or node_digests is None:
            try:
                repo = load_repo(root) if repo is None else repo
                live_routes, live_nodes = live_claim_digests(repo)
            except (OSError, ValueError):
                return None
            if route_digests is None:
                route_digests = live_routes
            if node_digests is None:
                node_digests = live_nodes
        if key.startswith(ROUTE_CONTENT_PREFIX):
            return route_digests.get(key)
        return node_digests.get(key)
    if key.startswith("material-synthesis-basis:"):
        from learning_os.derive.material_synthesis import (
            MaterialSynthesisError,
            current_unit_material_basis,
            material_basis_checksum,
            material_synthesis_freshness,
            synthesis_destination,
        )
        unit_id = key[len("material-synthesis-basis:"):]
        try:
            repo = load_repo(root) if repo is None else repo
            cache: dict[Path, str] = {}
            basis = current_unit_material_basis(root, unit_id, repo=repo, cache=cache)
            value = read_optional_yaml(synthesis_destination(root, unit_id))
            if not isinstance(value, dict) or material_synthesis_freshness(
                    root, unit_id, value, repo=repo, cache=cache)["status"] != "current":
                return None
            return material_basis_checksum(basis)
        except (MaterialSynthesisError, OSError, ValueError):
            return None
    if key.startswith("manifest:"):
        ref = key[len("manifest:"):]
        entry = manifest_files.get(ref)
        digest = entry.get("sha256") if isinstance(entry, dict) else None
        return digest if isinstance(digest, str) and digest.strip() else None
    if key.startswith("file:"):
        ref = key[len("file:"):]
        try:
            candidate = resolve_symlinks_inside(root, root / ref)
            return "sha256:" + hashlib.sha256(
                candidate.read_bytes()).hexdigest()
        except (OSError, PathBoundaryError):
            return None
    return None




def route_units(repo: Repo) -> dict[str, str]:
    owners: dict[str, str] = {}
    ambiguous: set[str] = set()
    for mid, source_map in repo.module_source_maps.items():
        for source in source_map.get("sources") or []:
            if not isinstance(source, dict):
                continue
            for row in source.get("unit_routes") or []:
                if not isinstance(row, dict):
                    continue
                route = route_with_identity(mid, str(source.get("source_id") or ""), row)
                rid, uid = str(route["id"]), str(route.get("unit_id") or "")
                if rid in ambiguous:
                    continue
                if rid in owners and owners[rid] != uid:
                    owners.pop(rid)
                    ambiguous.add(rid)
                else:
                    owners[rid] = uid
    return owners


def read_audits(root: Path) -> dict[str, AuditRecord]:
    path = root / "operations/goal-ledger.yaml"
    if not path.exists() and not path.is_symlink():
        return {}
    try:
        value: object = load_yaml(path, root)
    except (LoaderError, OSError, UnicodeError) as exc:
        raise AuditError(f"cannot read preserved audit state: {exc}") from exc
    return audits_from_ledger(value)


def observe_claims(root: Path, *, repo: Repo | None = None,
                   route_ids: Iterable[str] | None = None,
                   records: Mapping[str, ClaimLineage] | None = None,
                   audits: Mapping[str, AuditRecord] | None = None,
                   certified: frozenset[tuple[str, str]] = frozenset(),
                   defective: frozenset[tuple[str, str]] = frozenset()) -> dict[str, ClaimStatus]:
    repo = repo if repo is not None else load_repo(root)
    all_records = records if records is not None else load_ledger(root)
    # Evidence freshness has no dependency on optional audit storage.
    # Consumers that need audit authority supply their own validated observation.
    recorded_certified, recorded_defective = memberships(audits or {})
    certified = certified | recorded_certified
    defective = defective | recorded_defective
    selected = set(route_ids) if route_ids is not None else None
    wanted = {"covers:" + rid for rid in selected} if selected is not None else set(all_records)
    closure = set(wanted)
    pending = list(wanted)
    while pending:
        row = all_records.get(pending.pop())
        if row is not None:
            for dep in row.derived_from.assumes:
                if dep not in closure:
                    closure.add(dep)
                    pending.append(dep)
    subset = {cid: row for cid, row in all_records.items() if cid in closure}
    keys = {key for row in subset.values() for key, _ in row.derived_from.source_hashes}
    routes, nodes = live_claim_digests(repo, keys)
    manifest = scan_manifest_files(root) if any(key.startswith("manifest:") for key in keys) else {}
    live: dict[str, str] = {}
    for key in sorted(keys):
        value = live_evidence_digest(root, key, manifest, repo=repo,
                                     route_digests=routes, node_digests=nodes)
        if value is not None:
            live[key] = value
    owners = route_units(repo)
    result = interpret_claims(subset, current_revisions(root), live,
                              units={"covers:" + rid: uid for rid, uid in owners.items()},
                              certified=certified, defective=defective)
    if selected is None:
        wanted.update("covers:" + rid for rid in owners)
    selected_statuses = {cid: result.get(cid, ClaimStatus(cid, "unrecorded", unit_id=owners.get(cid.removeprefix("covers:"), "")))
                         for cid in sorted(wanted)}
    if audits is None:
        return {cid: replace(row, audit="unavailable") if row.audit == "unaudited" else row
                for cid, row in selected_statuses.items()}
    return selected_statuses


def observe_claims_with_audits(root: Path, *, repo: Repo | None = None,
                              route_ids: Iterable[str] | None = None) -> dict[str, ClaimStatus]:
    """Enrich ordinary reads when possible; unavailable audit data grants nothing."""
    try:
        audits = read_audits(root)
    except AuditError:
        audits = None
    return observe_claims(root, repo=repo, route_ids=route_ids, audits=audits)


def claims_summary(statuses: Mapping[str, ClaimStatus]) -> dict[str, object]:
    actionable = [{"claim_id": cid, **row.payload()} for cid, row in sorted(statuses.items()) if row.goal_id]
    return {"counts": dict(sorted(Counter(row.status for row in statuses.values()).items())),
            "audit_counts": dict(sorted(Counter(row.audit for row in statuses.values()).items())),
            "actionable_count": len(actionable), "actionable": actionable[:10]}


def claim_impacts(before: Mapping[str, ClaimStatus], after: Mapping[str, ClaimStatus],
                  rejudged: Iterable[str]) -> list[dict[str, object]]:
    admitted = set(rejudged)
    rows: list[dict[str, object]] = []
    for cid, prior in sorted(before.items()):
        current = after.get(cid)
        outcome = ("rejudged" if cid in admitted else "withdrawn" if current is None else
                   "will-be-stale" if current.status == "stale" else "unchanged")
        command = f"unit-plan-revise {prior.unit_id} --file REVISION.yaml --check" if prior.unit_id else ""
        rows.append({"claim_id": cid, "before": prior.status, "after": outcome,
                     "warning": f"{cid} remains stale; re-judge with {command}" if outcome == "will-be-stale" else "",
                     "next": command if outcome == "will-be-stale" else ""})
    return rows
