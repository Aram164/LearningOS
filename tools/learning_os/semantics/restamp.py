"""Mechanical eligibility for the governed lineage re-stamp (#94).

A route-covers claim judged under the old read shape pins its module
revision plus every co-imported unit. The re-stamp may narrow those
reads to the per-route shape — the route row plus each covered node, by
content digest — only while the judged rows are byte-identical to live.
This module recomputes, read-only, which supported claims satisfy that:

* the claim's latest judgment commit (the newest commit touching the
  ledger where its judged basis changed; status-only moves do not count);
* the route row and covered-node rows at that commit, hashed with the
  same helpers new judgments use, compared against live;
* the judging receipt's recorded after-hashes, which must equal the
  judgment-commit blobs — otherwise the judged bytes were never
  committed and the window between judgment and commit needs
  attribution;
* stored evidence, re-resolved against live bytes with the scan's own
  resolver.

A bundled window whose rewriters are all ``route.patch`` is attributed
row by row: a patch provably edits exactly one route row
(``route_patch_plan`` updates the single matched row and never touches
``knowledge_map``), and its receipt scopes it to one unit. A claim whose
own row a bundled patch touched needs re-judgment; a claim no bundled
patch could have touched recovers. Anything else bundled — notably a
``module.plan.import`` — leaves the judged bytes unrecoverable and the
claim needs review. Row attribution inside one unit follows the reviewed
request-slug rule below, and fails closed to needs-review whenever the
slug does not name exactly one route.

Verdicts reuse the eligibility report's buckets: ``eligible``,
``needs-rejudgment``, ``needs-review``.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import yaml

from .. import githistory
from ..loader import load_repo
from .lineage import (
    LEDGER_RELATIVE,
    NODE_CONTENT_PREFIX,
    ROUTE_CONTENT_PREFIX,
    LineageError,
    load_ledger,
    node_content_digest,
    parse_covers_statement,
    route_content_digest,
)
from .predicates import CONTRACT_VERSION
from .scan import (
    _live_claim_digests,
    _scan_manifest_files,
    live_evidence_digest,
)

#: Verdicts, in report order.
ELIGIBLE = "eligible"
NEEDS_REJUDGMENT = "needs-rejudgment"
NEEDS_REVIEW = "needs-review"


def claims_list_sha256(claim_ids) -> str:
    """Bind a reviewed claim list to its exact bytes.

    The canonical form is the sorted ids, one per line, with a trailing
    newline — the reviewer hashes the reviewed file directly, and the
    apply path recomputes this over the payload ids. Duplicates refuse:
    the binding is over the exact list, not a set.
    """
    ids = list(claim_ids)
    if any(not isinstance(cid, str) or not cid for cid in ids):
        raise LineageError("a claim list names non-empty claim ids")
    if len(set(ids)) != len(ids):
        raise LineageError("a claim list names each claim once")
    body = "".join(cid + "\n" for cid in sorted(ids))
    return "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest()


def _git_show_bytes(root: Path, commit: str, rel: str) -> bytes | None:
    """One blob at one commit, or None when it is absent there."""
    try:
        proc = subprocess.run(
            ["git", "show", f"{commit}:{rel}"],
            cwd=str(root), capture_output=True, timeout=120,
            env={"PATH": "/usr/bin:/bin:/usr/local/bin",
                 "GIT_OPTIONAL_LOCKS": "0"},
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise githistory.GitHistoryError(
            f"git show {commit}:{rel} failed: {exc}") from exc
    if proc.returncode != 0:
        return None
    return proc.stdout


def _git_lines(root: Path, *args: str) -> list[str]:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(root), capture_output=True, timeout=120,
            env={"PATH": "/usr/bin:/bin:/usr/local/bin",
                 "GIT_OPTIONAL_LOCKS": "0"},
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise githistory.GitHistoryError(
            f"git {' '.join(args)} failed: {exc}") from exc
    if proc.returncode != 0:
        detail = proc.stderr.decode("utf-8", "replace").strip()
        raise githistory.GitHistoryError(
            f"git {' '.join(args)} failed (exit {proc.returncode}): {detail}")
    return proc.stdout.decode("utf-8").splitlines()


def _judgment_commits(root: Path, supported: set[str]) -> dict[str, str]:
    """The latest judgment commit per claim, over ledger history.

    The judged basis is the statement, revisions, source hashes,
    evidence, judge and admission: the newest commit where any of those
    changed. Status-only changes do not move it.
    """
    commits = _git_lines(
        root, "log", "--format=%H", "--reverse", "--", LEDGER_RELATIVE)
    basis_at: dict[str, tuple[str, str]] = {}
    for commit in commits:
        raw = _git_show_bytes(root, commit, LEDGER_RELATIVE)
        if raw is None:
            continue
        try:
            data = yaml.safe_load(raw.decode("utf-8")) or {}
        except (UnicodeDecodeError, yaml.YAMLError):
            continue
        records = data.get("records") or {}
        for cid in sorted(supported):
            rec = records.get(cid)
            if not isinstance(rec, dict):
                continue
            derived = rec.get("derived_from") or {}
            basis = json.dumps({
                "statement": rec.get("statement"),
                "derived_from": {
                    "contract_version": derived.get("contract_version"),
                    "revisions": derived.get("revisions"),
                    "source_hashes": derived.get("source_hashes"),
                    "evidence": derived.get("evidence"),
                },
                "judged_by": rec.get("judged_by"),
                "admitted_by": rec.get("admitted_by"),
            }, sort_keys=True, default=str)
            if basis_at.get(cid, (None, None))[1] != basis:
                basis_at[cid] = (commit, basis)
    return {cid: commit for cid, (commit, _basis) in basis_at.items()}


def _load_receipts(root: Path) -> tuple[list[dict], dict[tuple, dict]]:
    receipts = []
    for path in sorted((root / "operations" / "transactions").glob("transaction-*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            continue
        if isinstance(data, dict) and data.get("id"):
            receipts.append(data)
    by_request = {}
    for receipt in receipts:
        req = receipt.get("request") or {}
        by_request[(req.get("request_id"),
                    req.get("idempotency_key"))] = receipt
    return receipts, by_request


def _routes_in_text(text: str) -> dict[str, tuple[str, dict]]:
    """route id -> (source_id, row) for one source-map document."""
    found: dict[str, tuple[str, dict]] = {}
    try:
        smap = yaml.safe_load(text) or {}
    except yaml.YAMLError:
        return found
    if not isinstance(smap, dict):
        return found
    for src in smap.get("sources") or []:
        if not isinstance(src, dict):
            continue
        sid = str(src.get("source_id") or "")
        for row in src.get("unit_routes") or []:
            if isinstance(row, dict) and row.get("id"):
                found[str(row["id"])] = (sid, row)
    return found


def _nodes_in_text(text: str) -> dict[str, dict]:
    """node id -> row for one unit document."""
    found: dict[str, dict] = {}
    try:
        unit = yaml.safe_load(text) or {}
    except yaml.YAMLError:
        return found
    if not isinstance(unit, dict):
        return found
    knowledge = unit.get("knowledge_map") or {}
    if not isinstance(knowledge, dict):
        return found
    for row in knowledge.get("nodes") or []:
        if isinstance(row, dict) and str(row.get("id") or "").strip():
            found[str(row["id"])] = row
    return found


def _patch_units(receipt: dict) -> set[str]:
    """The unit artifacts one receipt bumped (module excluded)."""
    artifacts = receipt.get("artifact_revisions") or {}
    if not isinstance(artifacts, dict):
        return set()
    return {str(key) for key in artifacts if str(key).startswith("unit-")}


def _attribute_bundled_patch(*, request_id, units: set[str],
                             routes_by_unit: dict[str, list[str]]) -> str | None:
    """The one route a bundled patch named, or None when it names none.

    The reviewed rule for the 2026-09-12 bundled window: a ``route.patch``
    request slug ends in ``<unit-hint>-<route-hint>``
    (``request-kleine-beweise-20260912-ch03-dierks``), and the patch
    touched the unique route of its bumped unit containing the route
    hint. Every condition fails closed — a slug of another shape, a unit
    hint outside the bumped unit, a trailing counter instead of a name,
    or anything but exactly one matching route attributes nothing, and
    the claim keeps needs-review.
    """
    if not isinstance(request_id, str) or len(units) != 1:
        return None
    segments = request_id.split("-")
    if len(segments) < 2:
        return None
    unit_hint, route_hint = segments[-2].casefold(), segments[-1].casefold()
    if not unit_hint or not route_hint:
        return None
    if route_hint.isdigit():
        # A trailing counter (op-20260909-harv-l08-001) names no route.
        return None
    (unit_id,) = sorted(units)
    if unit_hint not in unit_id.casefold():
        return None
    matches = [rid for rid in routes_by_unit.get(unit_id, [])
               if route_hint in rid.casefold()]
    if len(matches) != 1:
        return None
    return matches[0]


def analyze(root: Path | str) -> dict:
    """Mechanical eligibility for every supported route-covers claim.

    Read-only. Returns ``{"claims": {id: row}, "already_stamped": [...],
    "totals": {...}}``; each row carries its verdict, reasons, basis,
    judgment commit, module, route, nodes, bundled rewriters, and — for
    stampable claims — the narrowed reads to stamp. Deterministic.
    """
    root = Path(root)
    records = load_ledger(root)
    supported = {
        cid: rec for cid, rec in records.items()
        if rec.claim_kind == "route-covers" and rec.status == "supported"
    }
    already_stamped = sorted(
        cid for cid, rec in supported.items()
        if any(key.startswith(ROUTE_CONTENT_PREFIX)
               or key.startswith(NODE_CONTENT_PREFIX)
               for key in dict(rec.derived_from.source_hashes)))
    todo = {cid: rec for cid, rec in supported.items()
            if cid not in already_stamped}

    repo = load_repo(root)
    live_routes: dict[str, tuple[str, str, dict]] = {}
    for module_id, smap in (repo.module_source_maps or {}).items():
        if not isinstance(smap, dict):
            continue
        for src in smap.get("sources") or []:
            if not isinstance(src, dict):
                continue
            sid = str(src.get("source_id") or "")
            for row in src.get("unit_routes") or []:
                if isinstance(row, dict) and row.get("id"):
                    live_routes[str(row["id"])] = (str(module_id), sid, row)
    live_nodes: dict[str, dict] = {}
    live_node_unit_file: dict[str, str] = {}
    for unit in (repo.units or {}).values():
        data = getattr(unit, "data", None)
        knowledge = data.get("knowledge_map") if isinstance(data, dict) else None
        nodes = knowledge.get("nodes") if isinstance(knowledge, dict) else None
        if not isinstance(nodes, list):
            continue
        try:
            rel = Path(unit.path).relative_to(root).as_posix()
        except (TypeError, ValueError):
            rel = None
        for row in nodes:
            if isinstance(row, dict) and str(row.get("id") or "").strip():
                live_nodes[str(row["id"])] = row
                if rel:
                    live_node_unit_file[str(row["id"])] = rel
    claim_routes, claim_nodes = _live_claim_digests(repo)
    manifest_files = _scan_manifest_files(root)

    commits = _judgment_commits(root, set(todo))
    receipts, by_request = _load_receipts(root)
    receipts_by_id = {r["id"]: r for r in receipts}
    blob_cache: dict[tuple[str, str], str | None] = {}

    def cached_blob(commit, rel):
        key = (commit, rel)
        if key not in blob_cache:
            raw = _git_show_bytes(root, commit, rel)
            try:
                blob_cache[key] = raw.decode("utf-8") if raw is not None else None
            except UnicodeDecodeError:
                blob_cache[key] = None
        return blob_cache[key]

    def unit_files_at(commit, module_id):
        out = _git_lines(
            root, "ls-tree", "-r", "--name-only", commit,
            f"curriculum/modules/{module_id}/units/")
        return [line for line in out if line.endswith("/unit.yaml")]

    rows = {}
    for cid in sorted(todo):
        rec = todo[cid]
        rows[cid] = _analyze_claim(
            root, rec, commits.get(cid), live_routes, live_nodes,
            live_node_unit_file, claim_routes, claim_nodes,
            manifest_files, repo, receipts, receipts_by_id,
            by_request, cached_blob, unit_files_at)
    totals = {ELIGIBLE: 0, NEEDS_REJUDGMENT: 0, NEEDS_REVIEW: 0}
    for row in rows.values():
        totals[row["verdict"]] += 1
    return {"claims": rows, "already_stamped": already_stamped,
            "totals": totals}


def _analyze_claim(root, rec, commit, live_routes, live_nodes,
                   live_node_unit_file, claim_routes, claim_nodes,
                   manifest_files, repo, receipts, receipts_by_id,
                   by_request, cached_blob, unit_files_at) -> dict:
    cid = rec.claim_id
    row: dict = {"claim_id": cid, "verdict": NEEDS_REVIEW, "reasons": [],
                 "basis": "unknown", "judgment_commit": commit or "",
                 "module_id": "", "route_id": "", "nodes": [],
                 "new_reads": None, "stampable": None,
                 "bundled_rewriters": []}
    try:
        route_id, nodes = parse_covers_statement(cid, rec.statement)
    except LineageError:
        row["reasons"] = ["unparsable-statement"]
        return row
    row["route_id"] = route_id
    row["nodes"] = list(nodes)
    modules = [a for a in dict(rec.derived_from.revisions) if a.startswith("module-")]
    if len(modules) != 1:
        row["reasons"] = ["analysis-gap"]
        return row
    module_id = modules[0]
    row["module_id"] = module_id
    if rec.derived_from.contract_version != CONTRACT_VERSION:
        row["reasons"] = ["contract-version"]
        row["verdict"] = NEEDS_REJUDGMENT
        return row
    if commit is None:
        row["reasons"] = ["analysis-gap"]
        return row

    smap_rel = f"curriculum/modules/{module_id}/source-map.yaml"
    smap_text = cached_blob(commit, smap_rel)
    judged_routes = _routes_in_text(smap_text) if smap_text is not None else {}
    judged_nodes: dict[str, dict] = {}
    for rel in unit_files_at(commit, module_id):
        text = cached_blob(commit, rel)
        if text is not None:
            judged_nodes.update(_nodes_in_text(text))

    reasons: list[str] = []
    live_key = ROUTE_CONTENT_PREFIX + route_id
    if route_id not in judged_routes:
        reasons.append("route-absent-at-judgment")
    elif route_id not in live_routes:
        reasons.append("route-deleted")
    elif claim_routes.get(live_key) is None:
        # The scan drops ids it cannot own uniquely; a stamp the scan
        # cannot resolve would not stick, so ambiguity refuses.
        reasons.append("route-unresolvable")
    else:
        sid, judged_row = judged_routes[route_id]
        try:
            judged_digest = route_content_digest(
                module_id=module_id, source_id=sid, route=judged_row)
        except LineageError:
            judged_digest = None
        if judged_digest != claim_routes[live_key]:
            reasons.append("route-changed")
        row["_live_route_digest"] = claim_routes[live_key]
        row["_live_route_key"] = live_key
    for node in nodes:
        node_key = NODE_CONTENT_PREFIX + node
        if node not in judged_nodes:
            reasons.append(f"node-absent-at-judgment:{node}")
        elif node not in live_nodes:
            reasons.append(f"node-deleted:{node}")
        elif claim_nodes.get(node_key) is None:
            reasons.append(f"node-unresolvable:{node}")
        elif node_content_digest(judged_nodes[node]) != claim_nodes[node_key]:
            reasons.append(f"node-changed:{node}")
        else:
            row.setdefault("_live_node_digests", {})[node] = claim_nodes[node_key]

    key = (rec.admitted_by.request_id, rec.admitted_by.idempotency_key)
    receipt = by_request.get(key)
    if receipt is None:
        row["basis"] = "receipt-unmatched"
    else:
        recorded = {w.get("path"): w.get("sha256_after")
                    for w in receipt.get("writes") or []
                    if isinstance(w, dict)}
        check_paths = [smap_rel] + [
            live_node_unit_file[n] for n in nodes if n in live_node_unit_file]
        compared = matched = 0
        for rel in dict.fromkeys(check_paths):
            raw = _git_show_bytes(root, commit, rel)
            want = recorded.get(rel)
            if raw is None or want is None:
                continue
            compared += 1
            if hashlib.sha256(raw).hexdigest() == want:
                matched += 1
        if compared == 0:
            row["basis"] = "receipt-unmatched-files"
        elif matched == compared:
            row["basis"] = "exact"
        else:
            row["basis"] = "approximate-bundled"

    evidence_bad = []
    stored_hashes = dict(rec.derived_from.source_hashes)
    for ekey in sorted(stored_hashes):
        live = live_evidence_digest(
            root, ekey, manifest_files, repo=repo,
            route_digests=claim_routes, node_digests=claim_nodes)
        if live != stored_hashes[ekey]:
            evidence_bad.append(ekey)
    if evidence_bad:
        reasons.append("evidence-unverifiable:" + ",".join(evidence_bad))

    row["reasons"] = reasons
    if row["basis"] in ("exact",):
        if not reasons:
            row["verdict"] = ELIGIBLE
            row["stampable"] = "exact"
            row["new_reads"] = _new_reads(row, nodes)
        elif all(r.startswith("evidence-unverifiable")
                 or r == "route-unresolvable"
                 or r.startswith("node-unresolvable:") for r in reasons):
            row["verdict"] = NEEDS_REVIEW
        else:
            row["verdict"] = NEEDS_REJUDGMENT
        row.pop("_live_route_digest", None)
        row.pop("_live_route_key", None)
        row.pop("_live_node_digests", None)
        return row
    if row["basis"] in ("receipt-unmatched", "receipt-unmatched-files"):
        row["verdict"] = NEEDS_REVIEW
        row.pop("_live_route_digest", None)
        row.pop("_live_route_key", None)
        row.pop("_live_node_digests", None)
        return row
    # Approximate: the judged bytes were never committed. Attribute the
    # bundled window before believing any comparison against it.
    _attribute_bundled_window(
        root, row, rec, receipt, receipts, receipts_by_id, commit,
        smap_rel, nodes, live_node_unit_file, judged_routes,
        cached_blob)
    row.pop("_live_route_digest", None)
    row.pop("_live_route_key", None)
    row.pop("_live_node_digests", None)
    return row


def _new_reads(row: dict, nodes) -> dict:
    reads = {row["_live_route_key"]: row["_live_route_digest"]}
    for node in nodes:
        reads[NODE_CONTENT_PREFIX + node] = row["_live_node_digests"][node]
    return reads


def _attribute_bundled_window(root, row, rec, receipt, receipts,
                              receipts_by_id, commit, smap_rel, nodes,
                              live_node_unit_file, judged_routes,
                              cached_blob) -> None:
    """Verdict for a claim whose judged bytes were never committed."""
    reasons = list(row["reasons"])
    if any(r.startswith("evidence-unverifiable") for r in reasons):
        row["verdict"] = NEEDS_REVIEW
        return
    judging_id = receipt["id"] if receipt is not None else None
    watched = {smap_rel} | {
        live_node_unit_file[n] for n in nodes if n in live_node_unit_file}
    bundled = []
    for candidate in receipts:
        if judging_id is not None and candidate["id"] <= judging_id:
            continue
        touched = {w.get("path") for w in candidate.get("writes") or []
                   if isinstance(w, dict)}
        if not (touched & watched):
            continue
        name = f"operations/transactions/{candidate['id']}.yaml"
        if _git_show_bytes(root, commit, name) is None:
            continue
        bundled.append(candidate)
    bundled.sort(key=lambda r: r["id"])
    row["bundled_rewriters"] = [
        {"receipt": r["id"], "capability": r.get("capability"),
         "request_id": (r.get("request") or {}).get("request_id"),
         "units": sorted(_patch_units(r))}
        for r in bundled
    ]
    if not bundled:
        row["verdict"] = NEEDS_REVIEW
        row["reasons"] = reasons + ["bundled-unexplained"]
        return
    if any(r.get("capability") != "route.patch" for r in bundled):
        row["verdict"] = NEEDS_REVIEW
        row["reasons"] = reasons + ["import-bundled-intermediate"]
        return
    # Every bundled rewrite is a single-row patch that never touches
    # knowledge nodes: judged nodes equal commit nodes, so the node
    # comparison stands, and each patch is attributed to its row.
    node_reasons = [r for r in reasons if r.startswith("node-")]
    if any(r.startswith("node-changed:") or r.startswith("node-deleted:")
           or r.startswith("node-absent-at-judgment:") for r in node_reasons):
        row["verdict"] = NEEDS_REJUDGMENT
        return
    if any(r.startswith("node-unresolvable:") for r in node_reasons):
        row["verdict"] = NEEDS_REVIEW
        return
    routes_by_unit: dict[str, list[str]] = {}
    for rid, (_sid, judged_row) in judged_routes.items():
        unit = judged_row.get("unit_id") if isinstance(judged_row, dict) else None
        if isinstance(unit, str) and unit:
            routes_by_unit.setdefault(unit, []).append(rid)
    claim_unit = None
    for unit, rids in routes_by_unit.items():
        if row["route_id"] in rids:
            claim_unit = unit
    ambiguous = False
    for patch in bundled:
        units = _patch_units(patch)
        if not units or (claim_unit is not None and claim_unit not in units):
            if not units:
                ambiguous = True
            continue
        if claim_unit is None:
            ambiguous = True
            continue
        attributed = _attribute_bundled_patch(
            request_id=(patch.get("request") or {}).get("request_id"),
            units=units, routes_by_unit=routes_by_unit)
        if attributed is None:
            ambiguous = True
        elif attributed == row["route_id"]:
            row["verdict"] = NEEDS_REJUDGMENT
            row["reasons"] = reasons + [
                f"attributed-route-patch:{patch['id']}"]
            return
    if ambiguous:
        row["verdict"] = NEEDS_REVIEW
        row["reasons"] = reasons + ["bundled-window-ambiguous"]
        return
    # No bundled patch could have touched this row: judged bytes equal the
    # commit bytes, so the commit comparison decides.
    if any(r == "route-changed" or r == "route-deleted"
           or r == "route-absent-at-judgment" for r in reasons):
        row["verdict"] = NEEDS_REJUDGMENT
        return
    if "route-unresolvable" in reasons:
        row["verdict"] = NEEDS_REVIEW
        return
    row["verdict"] = ELIGIBLE
    row["stampable"] = "recovered-exact"
    row["basis"] = "recovered-exact"
    row["new_reads"] = _new_reads(row, row["nodes"])
