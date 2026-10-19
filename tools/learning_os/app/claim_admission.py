"""Shared claim admission and explicit, digest-only planned lineage effects."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import NamedTuple

from learning_os.derive.material_synthesis import publication_lineage_record, synthesis_destination
from learning_os.derive.semantics.claim_audits import AuditError, memberships
from learning_os.derive.semantics.claim_status import observe_claims, read_audits
from learning_os.derive.semantics.lineage import (
    NODE_CONTENT_PREFIX,
    ROUTE_CONTENT_PREFIX,
    LineageError,
    dump_ledger,
    emit_route_covers,
    load_ledger,
    node_content_digest,
    route_content_digest,
    to_dict,
    withdraw,
)
from learning_os.domain.failures import TransactionFailure
from learning_os.domain.plan_import import (
    knowledge_node_rows,
)
from learning_os.domain.route_identity import route_with_identity
from learning_os.domain.snapshot import Repo
from learning_os.domain.verbatim import Quote, QuoteError, quote_from_mapping
from learning_os.store.codec import dump_yaml
from learning_os.store.contracts.gateway import current_gateway_request
from learning_os.store.loading.yamlio import LoaderError, load_yaml
from learning_os.store.materials.anchors import (
    AnchorError,
    AnchorProof,
    AnchorReader,
    RouteMaterial,
)
from learning_os.store.materials.resolution import stable_checksum
from learning_os.store.revisions import load_revisions

LINEAGE_ARTIFACT = "file:operations/transactions/lineage.yaml"
IDENTITY_FIELDS = ("locator", "vault_path", "url")
EVIDENCE_KINDS = ("route-locator", "manifest", "repo-file", "external", "quote")


@dataclass(frozen=True)
class AdmittedEvidence:
    trails: tuple[str, ...]
    source_hashes: tuple[tuple[str, str], ...]
    reads: tuple[tuple[str, int], ...]
    anchors: tuple[AnchorProof, ...] = ()
    classification: str = "remote-unanchored"
    quotes: tuple[Quote, ...] = ()


def lineage_artifacts(owners: Iterable[str], will_write: bool = True) -> list[str]:
    """Logical owners retain their meaning; whole-ledger replacements share one guard."""
    return sorted(set(owners) | ({LINEAGE_ARTIFACT} if will_write else set()))


def anchor_report(evidence: Mapping[str, AdmittedEvidence]) -> list[dict[str, object]]:
    """Ephemeral review excerpts never enter a rendered lineage record."""
    return [{"claim_id": cid, "classification": row.classification,
             "quotes": [{"ref": quote.ref, "text": quote.text, "page": quote.page,
                         "page_end": quote.page_end, "window": quote.window, "node": quote.node,
                         "matched": True} for quote in row.quotes],
             "bindings": [{"material": proof.material_uri, "manifest": proof.manifest_path,
                           "sha256": proof.material_sha256, "place": proof.place,
                           "language": proof.language} for proof in row.anchors]}
            for cid, row in sorted(evidence.items())]


class ClaimAdmission(NamedTuple):
    problems: list[str]
    changed: dict[str, list[str]]
    evidence: dict[str, AdmittedEvidence]
    live_routes: dict[str, dict[str, object]]


def read_material_manifest(root: Path) -> dict[str, object]:
    path = root / "records/materials-manifest.yaml"
    if not path.exists() and not path.is_symlink():
        return {}
    try:
        raw: object = load_yaml(path, root)
    except (OSError, LoaderError) as exc:
        raise LineageError(f"cannot read materials manifest: {exc}") from exc
    rows: object = raw.get("files") if isinstance(raw, dict) else None
    if not isinstance(rows, dict):
        raise LineageError("materials manifest needs a files mapping")
    return {str(key): value for key, value in rows.items()}


def _routes(source_map: object) -> dict[str, dict[str, object]]:
    return {key: row for key, (_, row) in _owned(source_map).items()}


def _owned(source_map: object) -> dict[str, tuple[str, dict[str, object]]]:
    if not isinstance(source_map, dict):
        return {}
    result: dict[str, tuple[str, dict[str, object]]] = {}
    sources: object = source_map.get("sources")
    for source in sources if isinstance(sources, list) else ():
        if not isinstance(source, dict):
            continue
        sid = str(source.get("source_id") or "")
        rows: object = source.get("unit_routes")
        for row in rows if isinstance(rows, list) else ():
            if isinstance(row, dict):
                # Legacy rich routes have the same public identity on reads
                # and on the edit that first persists it.
                identified = route_with_identity(str(source_map.get("module_id") or ""), sid, row)
                result[str(identified["id"])] = (sid, {str(k): v for k, v in identified.items()})
    return result


def _covers(row: Mapping[str, object]) -> list[str]:
    value = row.get("covers")
    return [str(node) for node in value] if isinstance(value, list) else []


def _material(rid: str, owned: tuple[str, Mapping[str, object]]) -> RouteMaterial:
    source, row = owned
    return RouteMaterial(rid, source, str(row.get("locator") or ""),
                         str(row.get("vault_path") or ""), str(row.get("url") or ""))


def admit_evidence(root: Path, reader: AnchorReader, claim_id: str, route: RouteMaterial,
                   previous: RouteMaterial | None, items: Sequence[Mapping[str, object]],
                   reads: Mapping[str, object], current_revisions: Mapping[str, int],
                   *, positive: bool) -> AdmittedEvidence:
    """The same evidence rule applies to material edits and stale re-judgments."""
    trails: list[str] = []
    hashes: dict[str, str] = {}
    if positive:
        source: object = reader.repo.sources.get(route.source_id)
        hashes["source-material:" + route.source_id] = stable_checksum({
            "material": source.get("material") if isinstance(source, dict) else None})
    proofs: list[AnchorProof] = []
    quotes: list[Quote] = []
    declared_reads: dict[str, int] = {}
    material = reader.materials(route, previous)
    if positive and material.kind == "offline":
        raise AnchorError("local material is offline; a local claim cannot use existence-only evidence")
    for item in items:
        kind, ref = item.get("kind"), item.get("ref")
        if kind not in EVIDENCE_KINDS:
            raise AnchorError(f"{claim_id} cites unknown evidence kind {kind!r}")
        if not isinstance(ref, str) or not ref.strip():
            raise AnchorError(f"{claim_id} evidence needs a non-empty ref")
        note = item.get("note")
        trail = f"{kind}:{ref}"
        if kind == "quote":
            quote = quote_from_mapping(item)
            proof = reader.verify_quote(route, quote, previous)
            quotes.append(quote)
            proofs.append(proof)
            trail = proof.trail
            entry = reader.manifest[proof.manifest_path]
            digest: object = entry.get("sha256") if isinstance(entry, dict) else None
            if not isinstance(digest, str):
                raise AnchorError("verified material has no manifest digest")
            hashes["manifest:" + proof.manifest_path] = digest
        elif kind == "route-locator":
            if ref not in route.locator:
                raise AnchorError(f"{claim_id} cites route-locator text absent from the recorded locator")
        elif kind == "manifest":
            entry = reader.manifest.get(ref)
            digest = entry.get("sha256") if isinstance(entry, dict) else None
            if not isinstance(digest, str) or not digest.strip():
                raise AnchorError(f"{claim_id} cites unregistered manifest path {ref!r} or one with no digest")
            hashes["manifest:" + ref] = digest
        elif kind == "repo-file":
            try:
                candidate = (root / ref).resolve()
                candidate.relative_to(root.resolve())
                content = candidate.read_bytes()
            except (OSError, ValueError) as exc:
                raise AnchorError(f"{claim_id} cites unreadable repo file {ref!r}") from exc
            hashes["file:" + ref] = "sha256:" + hashlib.sha256(content).hexdigest()
        elif kind == "external":
            if not ref.startswith(("http://", "https://")):
                raise AnchorError(f"{claim_id} external evidence must be an http(s) URL")
            if not isinstance(note, str) or not note.strip():
                raise AnchorError(f"{claim_id} external evidence needs its verification trail in note")
        if isinstance(note, str) and note.strip():
            trail += " -- trail: " + note.strip()
        trails.append(trail)
    if positive and material.kind in {"local", "local-unresolved"} and not proofs:
        # A manifest fallback proves an unsupported format or an explicitly
        # cited PDF page without text. Parser and extraction errors refuse.
        for item in items:
            if item.get("kind") != "manifest":
                continue
            ref, note, page = item.get("ref"), item.get("note"), item.get("page")
            if isinstance(ref, str) and isinstance(note, str):
                if page is not None and type(page) is not int:
                    raise AnchorError("unreadable PDF fallback page must be a positive integer")
                proofs.append(reader.verify_unreadable(route, ref, note, page, previous))
        if not proofs:
            raise AnchorError("local claim requires a verified quote, or an explicit unreadable-material fallback")
    for artifact, revision in sorted(reads.items()):
        if not isinstance(revision, (str, int)):
            raise AnchorError(f"{claim_id} declares malformed revision for {artifact!r}")
        try:
            value = int(revision)
        except ValueError as exc:
            raise AnchorError(f"{claim_id} declares malformed revision for {artifact!r}") from exc
        if artifact not in current_revisions:
            raise AnchorError(f"{claim_id} reads unknown artifact {artifact!r}")
        if current_revisions[artifact] != value:
            raise AnchorError(f"{claim_id} reads stale revision of {artifact!r}: package saw {value}, current is {current_revisions[artifact]}")
        declared_reads[artifact] = value
    reader.assert_unchanged()
    return AdmittedEvidence(tuple(trails), tuple(sorted(hashes.items())),
                            tuple(sorted(declared_reads.items())), tuple(proofs),
                            "anchored" if any(p.quote_sha256 for p in proofs)
                            else "manifest-bound" if proofs else "remote-unanchored", tuple(quotes))


def prepare_claim_admission(root: Path, repo: Repo, module_id: str,
                            package: Mapping[str, object], *, unit_scope: str | None = None) -> ClaimAdmission:
    live_map = repo.module_source_maps.get(module_id) or {}
    proposed_map = package.get("source_map") if package.get("source_map") is not None else live_map
    live, proposed = _routes(live_map), _routes(proposed_map)
    live_owned, owned = _owned(live_map), _owned(proposed_map)
    sources = dict(repo.sources)
    material_changes: set[str] = set()
    patches = package.get("source_patches") or []
    if not isinstance(patches, list):
        return ClaimAdmission(["source_patches must be a list"], {}, {}, live)
    for patch in patches:
        sid = patch.get("id") if isinstance(patch, dict) else None
        if not isinstance(sid, str) or sid not in sources or not isinstance(patch, dict):
            return ClaimAdmission(["source patch targets an unknown source"], {}, {}, live)
        before_source = sources[sid]
        sources[sid] = {**before_source, **patch}
        if before_source.get("material") != sources[sid].get("material"):
            material_changes.add(sid)
    proposed_repo = replace(repo, sources=sources)
    changed: dict[str, list[str]] = {}
    if package.get("source_map") is not None:
        for rid, row in sorted(proposed.items()):
            before = live.get(rid)
            identity_changed = before is not None and (
                any(before.get(field) != row.get(field) for field in IDENTITY_FIELDS)
                or live_owned[rid][0] != owned[rid][0])
            if (before is None and _covers(row)) or (before is not None and (
                    sorted(_covers(before)) != sorted(_covers(row)) or (identity_changed and _covers(row)))):
                changed[rid] = _covers(row)
        for rid in sorted(set(live) - set(proposed)):
            if _covers(live[rid]):
                changed[rid] = []
    for rid, (sid, row) in owned.items():
        if sid in material_changes and _covers(row):
            changed[rid] = _covers(row)
    problems: list[str] = []
    raw = package.get("claim_evidence", [])
    if raw is None:
        raw = []
    if not isinstance(raw, list):
        return ClaimAdmission(["claim_evidence must be a list of per-claim evidence maps"], {}, {}, live)
    supplied: dict[str, tuple[list[Mapping[str, object]], dict[str, object]]] = {}
    for index, entry in enumerate(raw):
        label = f"claim_evidence[{index}]"
        if not isinstance(entry, dict):
            problems.append(f"{label} must be a mapping")
            continue
        claim_id, items, reads = entry.get("claim_id"), entry.get("evidence"), entry.get("reads", {})
        if reads is None:
            reads = {}
        if not isinstance(claim_id, str) or not claim_id.strip():
            problems.append(f"{label} needs a non-empty claim_id")
        elif claim_id in supplied:
            problems.append(f"{label} repeats claim {claim_id!r}")
        elif not isinstance(items, list) or not items or any(not isinstance(item, dict) for item in items):
            problems.append(f"{label} needs a non-empty evidence list of mappings")
        elif not isinstance(reads, dict):
            problems.append(f"{label} reads must be a mapping")
        else:
            supplied[claim_id] = ([dict(item) for item in items], {str(key): value for key, value in reads.items()})
    try:
        records = load_ledger(root)
        manifest = read_material_manifest(root)
        revisions = load_revisions(root)
        statuses = observe_claims(root, repo=repo, records=records,
                                  route_ids=[key.removeprefix("covers:") for key in supplied])
    except (ValueError, TransactionFailure) as exc:
        return ClaimAdmission([str(exc)], {}, {}, live)
    audit_defects: frozenset[tuple[str, str]] | None = None
    for claim_id in supplied:
        rid = claim_id.removeprefix("covers:")
        claim_row = proposed.get(rid) or live.get(rid)
        if unit_scope is not None and claim_row is not None and claim_row.get("unit_id") != unit_scope:
            problems.append(f"claim evidence {claim_id!r} is outside unit scope {unit_scope}")
            continue
        if claim_id.startswith("covers:") and rid in changed:
            continue
        prior = records.get(claim_id)
        eligible = False
        if claim_id.startswith("covers:") and claim_row is not None and prior is not None:
            if prior.status in {"stale", "contested"}:
                eligible = True
            elif prior.status == "supported":
                status = statuses.get(claim_id)
                if status is not None and status.status == "stale":
                    eligible = True
                elif status is not None:
                    if audit_defects is None:
                        try:
                            _, audit_defects = memberships(read_audits(root))
                        except AuditError as exc:
                            problems.append(str(exc))
                            continue
                    eligible = (claim_id, status.basis) in audit_defects
        if eligible and claim_row is not None:
            changed[rid] = _covers(claim_row)
        else:
            problems.append(f"claim evidence names {claim_id!r}, which this package does not change and is not stale or disputed; lineage is prospective only, never backfill")
    for rid in sorted(changed):
        if "covers:" + rid not in supplied:
            problems.append(f"route {rid} changes covers or material identity without claim evidence; Phase B requires admitted evidence for covers:{rid}")
    if problems:
        return ClaimAdmission(problems, {}, {}, live)
    reader = AnchorReader(proposed_repo, manifest, previous_repo=repo)
    admitted: dict[str, AdmittedEvidence] = {}
    for claim_id, (items, reads) in sorted(supplied.items()):
        rid = claim_id[7:]
        route = _material(rid, owned.get(rid) or live_owned[rid])
        previous = _material(rid, live_owned[rid]) if rid in live_owned else None
        try:
            admitted[claim_id] = admit_evidence(root, reader, claim_id, route, previous,
                                               items, reads, revisions, positive=bool(changed[rid]))
        except (AnchorError, QuoteError) as exc:
            problems.append(f"{claim_id}: {exc}")
    return ClaimAdmission(problems, changed if not problems else {}, admitted if not problems else {}, live)


def render_claim_lineage(root: Path, repo: Repo, module_id: str, package: Mapping[str, object],
                         changed: Mapping[str, Sequence[str]], evidence_by_claim: Mapping[str, AdmittedEvidence],
                         live_routes: Mapping[str, Mapping[str, object]],
                         incremented_artifacts: Iterable[str] | None = None,
                         synthesis_entries: Sequence[tuple[str, Mapping[str, object]]] = ()) -> str:
    request = current_gateway_request()
    if request is None:
        raise LineageError("prospective lineage needs gateway admission context")
    revisions = load_revisions(root)
    records = dict(load_ledger(root))
    owned = _owned(package.get("source_map"))
    live_owned = _owned(repo.module_source_maps.get(module_id) or {})
    nodes: dict[str, Mapping[str, object]] = {}
    for unit in repo.units.values():
        nodes.update(knowledge_node_rows(unit.data))
    incremented = {module_id}
    units = package.get("units")
    for entry in units if isinstance(units, list) else ():
        data: object = entry.get("unit") if isinstance(entry, dict) else None
        if isinstance(data, dict):
            nodes.update(knowledge_node_rows(data))
            uid = data.get("id")
            if isinstance(uid, str) and data.get("module_id") == module_id:
                incremented.add(uid)
    if incremented_artifacts is not None:
        incremented = set(incremented_artifacts)
    for rid, covers in sorted(changed.items()):
        claim_id = "covers:" + rid
        evidence = evidence_by_claim[claim_id]
        hashes = dict(evidence.source_hashes)
        owner = owned.get(rid) or live_owned.get(rid)
        if owner is not None:
            source, row = owner
            hashes[ROUTE_CONTENT_PREFIX + rid] = route_content_digest(module_id=module_id, source_id=source, route=row)
        for nid in covers:
            if nid in nodes:
                hashes[NODE_CONTENT_PREFIX + nid] = node_content_digest(nodes[nid])
        read_revisions = {artifact: revisions.get(artifact, 0) + 1 if artifact in incremented else revision
                          for artifact, revision in evidence.reads}
        prior = records.get(claim_id)
        records[claim_id] = emit_route_covers(
            route_id=rid, covers=covers, read_revisions=read_revisions,
            judged_by=f"{request.channel}/{request.approval_kind}",
            admitted_by={"request_id": request.request_id, "idempotency_key": request.idempotency_key},
            evidence=evidence.trails, source_hashes=hashes,
            supersedes=to_dict(prior) if prior is not None else None)
    if package.get("source_map") is not None:
        for rid in sorted(set(live_routes) - set(owned)):
            if "covers:" + rid in records:
                for lineage in withdraw(list(records.values()), "covers:" + rid):
                    records[lineage.claim_id] = lineage
    for unit_id, dossier in synthesis_entries:
        content = dump_yaml(dict(dossier))
        path = synthesis_destination(root, unit_id)
        if path.is_file() and path.read_bytes() == content.encode("utf-8"):
            continue
        cid = f"dossier:{dossier['id']}"
        records[cid] = publication_lineage_record(root, unit_id, dict(dossier), content, request,
                                                  prior=records.get(cid))
    return dump_ledger(records)
