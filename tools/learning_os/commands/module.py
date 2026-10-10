"""Academic modules and the module plan import, including its contract and routing checks."""

from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

import yaml

from learning_os.contracts import PLAN_TEMPLATE_VERSION, current_template_problems
from learning_os.contracts.gateway import current_gateway_request
from learning_os.domain.codes import REVISION_CONFLICT
from learning_os.domain.failures import WriteRefused
from learning_os.domain.suggest import not_found
from learning_os.fingerprint import canonical_fingerprint
from learning_os.loader import load_repo
from learning_os.masters_planning import (
    MasterPromotionPlan,
    MastersPlanningError,
    prepare_master_promotion,
)
from learning_os.material_analysis import observe_local_material
from learning_os.material_refs import MaterialReferenceError, expand_map
from learning_os.material_synthesis import (
    MaterialSynthesisError,
    publication_lineage_record,
    synthesis_destination,
    validate_unit_material_synthesis,
)
from learning_os.materials_resolution import sha256_file
from learning_os.ops._legacy_plumbing import (
    _dump_study_map,
    _dump_yaml,
    _fresh_manifest,
    _operator_lock,
    _read_content_bound_file,
    _record_gateway_refusal,
    _take_gateway_refusal,
)
from learning_os.ops._plan_gate import (
    _evidential_diff,
    _module_plan_validation_errors,
    _plan_apply_gate,
    _route_changed_units,
    _semantic_ack_problems,
    _unit_route_rows,
    _unit_semantic_diff,
)
from learning_os.ops.check import _staged_shadow
from learning_os.render import replace_h2_section as _replace_h2_section
from learning_os.revisions import load_revisions
from learning_os.semantics.lineage import (
    LEDGER_RELATIVE,
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

from .support import (
    _expected_ok,
    _expected_revisions_from_args,
    _print_rows,
    _render_frontmatter,
    _replace_registry_list_record,
    _root,
    _write_transaction,
)

_PLAN_COMPLETENESS_CHECKS = (
    "local_inventory_complete",
    "linked_inventory_complete",
    "materials_opened_and_content_checked",
    "current_and_prior_scope_reconciled",
    "duplicates_and_numbering_checked",
    "exclusions_and_unresolved_gaps_recorded",
)


def cmd_module_list(args) -> int:
    manifest = _fresh_manifest(_root(args))
    rows = manifest.get("modules", [])
    if args.program_id:
        rows = [row for row in rows if row.get("area_id") == args.program_id]
    if args.status:
        rows = [row for row in rows if row.get("status") == args.status]
    return _print_rows(rows)


_LINEAGE_EVIDENCE_KINDS = ("route-locator", "manifest", "repo-file", "external")


def _materials_files(root: Path) -> dict:
    try:
        raw = yaml.safe_load(
            (root / "records" / "materials-manifest.yaml").read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    files = raw.get("files") if isinstance(raw, dict) else None
    return files if isinstance(files, dict) else {}


def _source_map_routes(source_map) -> dict:
    routes = {}
    if not isinstance(source_map, dict):
        return routes
    for source in source_map.get("sources", []) or []:
        if not isinstance(source, dict):
            continue
        for route in source.get("unit_routes") or []:
            if isinstance(route, dict) and route.get("id"):
                routes[str(route["id"])] = route
    return routes


def _source_map_routes_with_source(source_map) -> dict:
    """Route id to (owning source id, row), for content-digest reads."""
    routes = {}
    if not isinstance(source_map, dict):
        return routes
    for source in source_map.get("sources", []) or []:
        if not isinstance(source, dict):
            continue
        source_id = str(source.get("source_id") or "")
        for route in source.get("unit_routes") or []:
            if isinstance(route, dict) and route.get("id"):
                routes[str(route["id"])] = (source_id, route)
    return routes


def _knowledge_node_rows(unit_data) -> dict:
    """Knowledge node id to row for one unit mapping, or {} when absent."""
    if not isinstance(unit_data, dict):
        return {}
    knowledge = unit_data.get("knowledge_map")
    nodes = knowledge.get("nodes") if isinstance(knowledge, dict) else None
    if not isinstance(nodes, list):
        return {}
    rows = {}
    for node in nodes:
        if isinstance(node, dict) and str(node.get("id") or "").strip():
            rows[str(node["id"])] = node
    return rows


def _phaseB_validate(root: Path, repo, module_id: str, package: dict):
    problems = []
    live_map = (repo.module_source_maps or {}).get(module_id) or {}
    live_routes = _source_map_routes(live_map)
    package_map = package.get("source_map")
    package_routes = _source_map_routes(package_map) if package_map is not None else {}
    changed = {}
    if package_map is not None:
        for rid, route in sorted(package_routes.items()):
            old = live_routes.get(rid)
            new_covers = [str(node) for node in (route.get("covers") or [])]
            if old is None:
                if new_covers:
                    changed[rid] = new_covers
            elif sorted(str(node) for node in (old.get("covers") or [])) != sorted(new_covers):
                changed[rid] = new_covers
        # Deleting the route deletes its covers claim too. Include removals
        # even when there is no added/edited route to trigger ledger handling.
        for rid in sorted(set(live_routes) - set(package_routes)):
            if live_routes[rid].get("covers"):
                changed[rid] = []
    raw_evidence = package.get("claim_evidence", [])
    if raw_evidence is None:
        raw_evidence = []
    if not isinstance(raw_evidence, list):
        return (["claim_evidence must be a list of per-claim evidence maps"], {}, {}, live_routes)
    evidence_by_claim = {}
    for index, entry in enumerate(raw_evidence):
        label = f"claim_evidence[{index}]"
        if not isinstance(entry, dict):
            problems.append(f"{label} must be a mapping")
            continue
        claim_id = entry.get("claim_id")
        if not isinstance(claim_id, str) or not claim_id.strip():
            problems.append(f"{label} needs a non-empty claim_id")
            continue
        if claim_id in evidence_by_claim:
            problems.append(f"{label} repeats claim {claim_id!r}")
            continue
        items = entry.get("evidence")
        if not isinstance(items, list) or not items:
            problems.append(f"{label} needs a non-empty evidence list")
            continue
        reads = entry.get("reads", {})
        if reads is None:
            reads = {}
        if not isinstance(reads, dict):
            problems.append(f"{label} reads must be a mapping")
            continue
        evidence_by_claim[claim_id] = {"evidence": items, "reads": reads}
    for rid in sorted(changed):
        claim_id = "covers:" + rid
        if claim_id not in evidence_by_claim:
            problems.append(
                f"route {rid} changes covers without claim evidence; Phase B "
                f"requires admitted evidence for {claim_id}")
    for claim_id in sorted(evidence_by_claim):
        if not claim_id.startswith("covers:") or claim_id[7:] not in changed:
            problems.append(
                f"claim evidence names {claim_id!r}, which this package does not "
                "change; lineage is prospective only, never backfill")
    if problems:
        return (problems, {}, {}, live_routes)
    try:
        current_revisions = load_revisions(root)
    except (OSError, ValueError) as exc:
        return ([f"cannot read revision ledger: {exc}"], {}, {}, live_routes)
    manifest_files = _materials_files(root)
    for claim_id in sorted(evidence_by_claim):
        rid = claim_id[7:]
        route = package_routes.get(rid, live_routes.get(rid)) or {}
        locator = str(route.get("locator") or "")
        for item in evidence_by_claim[claim_id]["evidence"]:
            problems.extend(_phaseB_check_item(claim_id, item, locator, manifest_files, root))
        for artifact, revision in sorted(evidence_by_claim[claim_id]["reads"].items()):
            try:
                declared = int(revision)
            except (TypeError, ValueError):
                problems.append(f"{claim_id} declares malformed revision for {artifact!r}")
                continue
            if artifact not in current_revisions:
                problems.append(f"{claim_id} reads unknown artifact {artifact!r}")
            elif current_revisions[artifact] != declared:
                problems.append(
                    f"{claim_id} reads stale revision of {artifact!r}: package saw "
                    f"{declared}, current is {current_revisions[artifact]}")
    if problems:
        return (problems, {}, {}, live_routes)
    return ([], changed, evidence_by_claim, live_routes)


def _phaseB_check_item(claim_id, item, locator, manifest_files, root):
    if not isinstance(item, dict):
        return [f"{claim_id} evidence entries must be mappings"]
    kind = item.get("kind")
    ref = item.get("ref")
    if kind not in _LINEAGE_EVIDENCE_KINDS:
        return [f"{claim_id} cites unknown evidence kind {kind!r}"]
    if not isinstance(ref, str) or not ref.strip():
        return [f"{claim_id} evidence needs a non-empty ref"]
    if kind == "route-locator":
        if ref not in locator:
            return [f"{claim_id} cites route-locator text absent from the recorded locator"]
    elif kind == "manifest":
        if ref not in manifest_files:
            return [f"{claim_id} cites unregistered manifest path {ref!r}"]
        entry = manifest_files[ref]
        digest = entry.get("sha256") if isinstance(entry, dict) else None
        if not isinstance(digest, str) or not digest.strip():
            return [f"{claim_id} cites manifest path {ref!r} with no digest"]
    elif kind == "repo-file":
        try:
            candidate = (root / ref).resolve()
            inside = candidate == root.resolve() or root.resolve() in candidate.parents
        except (OSError, ValueError):
            inside = False
        if not inside or not candidate.is_file():
            return [f"{claim_id} cites unreadable repo file {ref!r}"]
    elif kind == "external":
        if not ref.startswith(("http://", "https://")):
            return [f"{claim_id} external evidence must be an http(s) URL"]
        if not isinstance(item.get("note"), str) or not str(item.get("note")).strip():
            return [f"{claim_id} external evidence needs its verification trail in note"]
    return []


def _phaseB_ledger_text(root, repo, module_id, package, changed, evidence_by_claim, live_routes,
                       incremented_artifacts=None, synthesis_entries=()):
    request = current_gateway_request()
    if request is None:
        raise LineageError("prospective lineage needs gateway admission context")
    judged_by = f"{request.channel}/{request.approval_kind}"
    admitted = {"request_id": request.request_id, "idempotency_key": request.idempotency_key}
    try:
        current_revisions = load_revisions(root)
    except (OSError, ValueError) as exc:
        raise LineageError(f"cannot read revision ledger: {exc}") from exc
    manifest_files = _materials_files(root)
    records = dict(load_ledger(root))
    package_routes = _source_map_routes(package.get("source_map"))
    # Post-apply route rows with ownership: the package row when this import
    # carries the route, else the live row (a deletion still emits before
    # its withdrawal below). Package unit rows likewise override live rows,
    # so covered-node digests describe post-apply validity.
    live_map = (getattr(repo, "module_source_maps", {}) or {}).get(module_id) or {}
    package_owned = _source_map_routes_with_source(package.get("source_map"))
    live_owned = _source_map_routes_with_source(live_map)
    post_apply_nodes: dict = {}
    for unit in (getattr(repo, "units", {}) or {}).values():
        post_apply_nodes.update(_knowledge_node_rows(getattr(unit, "data", None)))
    # Post-apply stamping: the gateway increments exactly module_id and the
    # units supplied in the package (see cmd_module_plan_import artifact_ids).
    # Declared reads store post-apply validity for those artifacts so the new
    # claim is supported immediately after its own commit. Nothing else is
    # stamped: each covers claim reads its own route row plus its covered
    # nodes (content digests below), never the module revision and never
    # co-imported units or learner state.
    package_unit_ids = set()
    for entry in package.get("units", []) or []:
        unit_data = entry.get("unit") if isinstance(entry, dict) else None
        uid = unit_data.get("id") if isinstance(unit_data, dict) else None
        if isinstance(uid, str) and uid \
                and unit_data.get("module_id") == module_id:
            package_unit_ids.add(uid)
        if isinstance(unit_data, dict):
            post_apply_nodes.update(_knowledge_node_rows(unit_data))
    incremented = ({module_id} | package_unit_ids) if incremented_artifacts is None \
        else set(incremented_artifacts)
    for rid in sorted(changed):
        claim_id = "covers:" + rid
        trails = []
        digests = {}
        for item in evidence_by_claim[claim_id]["evidence"]:
            ref = str(item["ref"])
            trail = "{}:{}".format(item["kind"], ref)
            note = item.get("note")
            if isinstance(note, str) and note.strip():
                trail += f" -- trail: {note.strip()}"
            trails.append(trail)
            if item["kind"] == "manifest":
                entry = manifest_files.get(ref)
                digest = str(entry.get("sha256") or "") \
                    if isinstance(entry, dict) else ""
                if not digest:
                    raise LineageError(
                        f"{claim_id} cites manifest path {ref!r} with no digest")
                digests["manifest:" + ref] = digest
            elif item["kind"] == "repo-file":
                try:
                    candidate = (root / ref).resolve()
                    inside = candidate == root.resolve() \
                        or root.resolve() in candidate.parents
                except (OSError, ValueError):
                    inside = False
                    candidate = None
                if not inside or candidate is None or not candidate.is_file():
                    raise LineageError(
                        f"{claim_id} cites unreadable repo file {ref!r}")
                try:
                    content = candidate.read_bytes()
                except OSError as exc:
                    raise LineageError(
                        f"{claim_id} cites unreadable repo file {ref!r}: "
                        f"{exc}") from exc
                digests["file:" + ref] = "sha256:" + hashlib.sha256(
                    content).hexdigest()
        try:
            declared = {
                str(artifact): int(revision)
                for artifact, revision
                in dict(evidence_by_claim[claim_id].get("reads") or {}).items()
            }
        except (TypeError, ValueError) as exc:
            raise LineageError(
                f"{claim_id} declares malformed revision: {exc}") from exc
        # Declared reads were validated fresh against pre-commit state;
        # store post-apply validity for incremented artifacts so the new
        # claim is supported immediately after its own commit.
        read_revisions = {}
        for artifact, revision in declared.items():
            if artifact in incremented:
                read_revisions[artifact] = current_revisions.get(artifact, 0) + 1
            else:
                read_revisions[artifact] = revision
        # The judgment's own reads: this route's row plus the nodes it
        # covers. A covered node without a post-apply row earns no key —
        # canonical validation owns covers resolvability, and the ledger
        # never invents a digest for a row that is not there.
        owned = package_owned.get(rid) or live_owned.get(rid)
        if owned is not None:
            source_id, route_row = owned
            digests[ROUTE_CONTENT_PREFIX + rid] = route_content_digest(
                module_id=module_id, source_id=source_id, route=route_row)
        for node_id in changed[rid]:
            node_row = post_apply_nodes.get(str(node_id))
            if node_row is not None:
                digests[NODE_CONTENT_PREFIX + str(node_id)] = node_content_digest(
                    node_row)
        prior = records.get(claim_id)
        records[claim_id] = emit_route_covers(
            route_id=rid,
            covers=changed[rid],
            read_revisions=read_revisions,
            judged_by=judged_by,
            admitted_by=admitted,
            evidence=trails,
            supersedes=to_dict(prior) if prior is not None else None,
            source_hashes=digests,
        )
    live_ids = set(live_routes)
    package_ids = set(package_routes)
    for rid in sorted(live_ids - package_ids):
        claim_id = "covers:" + rid
        if claim_id in records:
            for lineage in withdraw(list(records.values()), claim_id):
                records[lineage.claim_id] = lineage
    for unit_id, dossier in synthesis_entries:
        content = _dump_yaml(dossier)
        destination = synthesis_destination(root, unit_id)
        if destination.is_file() and destination.read_bytes() == content.encode("utf-8"):
            continue
        claim_id = f"dossier:{dossier['id']}"
        records[claim_id] = publication_lineage_record(
            root, unit_id, dossier, content, request, prior=records.get(claim_id))
    return dump_ledger(records)


def _coverage_audit_problems(root: Path, contract: dict) -> list[str]:
    """The audit-evidence rules shared by the module (v2) and unit (v1) contracts."""
    problems: list[str] = []
    if contract.get("plan_template_version") != PLAN_TEMPLATE_VERSION:
        problems.append(
            f"plan_contract.plan_template_version must be {PLAN_TEMPLATE_VERSION}"
        )
    audit_ref = contract.get("coverage_audit")
    if not isinstance(audit_ref, str) or not audit_ref.strip():
        problems.append("plan_contract.coverage_audit must name the completed audit")
    else:
        audit = (root / audit_ref).resolve()
        try:
            audit_relative = audit.relative_to(root.resolve())
        except ValueError:
            problems.append("plan_contract.coverage_audit must stay inside the repository")
        else:
            if audit_relative.parts[:2] != ("work", "active"):
                problems.append(
                    "plan_contract.coverage_audit must stay under snapshot-bound work/active/"
                )
            elif not audit.is_file():
                problems.append(f"coverage audit does not exist: {audit_ref}")
            else:
                audit_text = audit.read_text(encoding="utf-8")
                for marker in ("## Local", "## Linked", "## Completeness"):
                    if marker not in audit_text:
                        problems.append(
                            f"coverage audit lacks required section marker: {marker}"
                        )
    checks = contract.get("checks")
    if not isinstance(checks, dict):
        problems.append("plan_contract.checks must be a mapping")
    else:
        for key in _PLAN_COMPLETENESS_CHECKS:
            if checks.get(key) is not True:
                problems.append(f"plan_contract.checks.{key} must be true")
    if isinstance(audit_ref, str) and audit_ref.strip():
        problems.extend(_structured_inventory_problems(root, audit_ref))
    return problems


#: Fenced YAML block inside the coverage audit carrying machine-checkable
#: disposition rows. Additive: an audit without the block keeps the legacy
#: marker + boolean path, so old packages stay readable during rollout.
_INVENTORY_FENCE = "```inventory-v1"
_INVENTORY_ROW_DISPOSITIONS = ("routed", "linked", "out-of-scope", "duplicate")


def _inventory_block(audit_text: str) -> tuple[dict | None, list[str]]:
    """Parse the structured inventory block, or (None, []) when absent."""
    opens = [i for i in range(len(audit_text))
             if audit_text.startswith(_INVENTORY_FENCE, i)]
    if not opens:
        return None, []
    if len(opens) > 1:
        return None, ["coverage audit carries more than one inventory-v1 block"]
    start = opens[0] + len(_INVENTORY_FENCE)
    close = audit_text.find("```", start)
    if close < 0:
        return None, ["coverage audit inventory-v1 block is never closed"]
    try:
        block = yaml.safe_load(audit_text[start:close])
    except yaml.YAMLError as exc:
        return None, [f"coverage audit inventory-v1 block is not YAML: {exc}"]
    if not isinstance(block, dict):
        return None, ["coverage audit inventory-v1 block must be a mapping"]
    return block, []


def _enumerate_inventory_roots(materials: Path, roots: list) -> tuple[dict[str, str], list[str]]:
    """Live file set under explicitly scoped material roots: relpath -> sha256.

    Only the declared roots are walked; dotfiles and symlinks are skipped.
    A root that is not an observable directory fails the preflight instead
    of silently narrowing the scope the audit claims to cover.
    """
    observed: dict[str, str] = {}
    problems: list[str] = []
    try:
        boundary = materials.resolve()
    except OSError as exc:
        return {}, [f"material inventory cannot resolve the materials tree: {exc}"]
    cache: dict[Path, str] = {}
    for entry in roots:
        if not isinstance(entry, str) or not entry.strip():
            problems.append("material inventory roots must be nonempty strings")
            continue
        try:
            target = (materials / entry).resolve()
            target.relative_to(boundary)
        except (OSError, ValueError):
            problems.append(f"material inventory root escapes the materials tree: {entry}")
            continue
        if not target.is_dir():
            problems.append(f"material inventory root is not observable: {entry}")
            continue
        for path in sorted(target.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            if any(part.startswith(".") for part in path.relative_to(target).parts):
                continue
            rel = path.relative_to(boundary).as_posix()
            try:
                observed[rel] = sha256_file(path, cache).removeprefix("sha256:")
            except OSError:
                problems.append(f"material inventory cannot read observed file: {rel}")
    return observed, problems


def _inventory_row_problems(block: dict, observed: dict[str, str],
                            materials: Path) -> list[str]:
    """Row shape, scope, digest, and duplicate-bytes rules for one inventory."""
    problems: list[str] = []
    rows = block.get("rows")
    if not isinstance(rows, list):
        return ["coverage audit inventory-v1 block needs a rows list"]
    roots = [r for r in (block.get("roots") or []) if isinstance(r, str)]
    seen: dict[str, dict] = {}
    local_rows: dict[str, dict] = {}
    for index, row in enumerate(rows):
        label = f"inventory row {index}"
        if not isinstance(row, dict):
            problems.append(f"{label} must be a mapping")
            continue
        kind = row.get("kind", "local")
        if kind not in ("local", "linked"):
            problems.append(f"{label} kind must be local or linked")
            continue
        disposition = row.get("disposition")
        if disposition not in _INVENTORY_ROW_DISPOSITIONS:
            problems.append(
                f"{label} disposition must be one of "
                f"{', '.join(_INVENTORY_ROW_DISPOSITIONS)}")
            continue
        if kind == "linked":
            for field in ("path", "sha256", "duplicate_of"):
                if row.get(field) is not None:
                    problems.append(
                        f"{label} is linked: {field} would impersonate observed bytes")
            if disposition not in ("linked", "out-of-scope"):
                problems.append(f"{label} is linked but disposed as {disposition}")
            if not isinstance(row.get("reference"), str) or not row["reference"].strip():
                problems.append(f"{label} is linked but names no reference")
            continue
        if disposition == "linked":
            problems.append(f"{label} observes local bytes but is disposed as linked")
            continue
        path = row.get("path")
        observation = observe_local_material(materials, path, "")
        if observation["status"] == "outside-boundary":
            problems.append(f"{label} path escapes the materials tree: {path}")
            continue
        if not any(path == root or path.startswith(root.rstrip("/") + "/")
                   for root in roots):
            problems.append(f"{label} path is outside the declared roots: {path}")
            continue
        if path in seen:
            problems.append(f"inventory row repeats path: {path}")
            continue
        seen[path] = row
        local_rows[path] = row
        recorded = row.get("sha256")
        if not isinstance(recorded, str) or len(recorded) != 64:
            problems.append(f"{label} needs the observed 64-hex sha256 for {path}")
            continue
        live = observed.get(path)
        if live is None:
            problems.append(f"inventory row names an unobserved file: {path}")
        elif live.lower() != recorded.lower():
            problems.append(f"inventory digest differs from observed bytes: {path}")
    for rel in sorted(observed):
        if rel not in seen:
            problems.append(f"material inventory lacks a row for observed file: {rel}")
    by_digest: dict[str, list[str]] = {}
    for path, row in local_rows.items():
        recorded = row.get("sha256")
        if isinstance(recorded, str) and len(recorded) == 64:
            by_digest.setdefault(recorded.lower(), []).append(path)
    for _digest, paths in sorted(by_digest.items()):
        if len(paths) < 2:
            continue
        canonical = [p for p in paths
                     if local_rows[p].get("disposition") != "duplicate"]
        if len(canonical) != 1:
            problems.append(
                "duplicate bytes need exactly one canonical row and "
                f"duplicate dispositions: {', '.join(sorted(paths))}")
            continue
        for path in sorted(paths):
            row = local_rows[path]
            if row.get("disposition") != "duplicate":
                continue
            target = row.get("duplicate_of")
            if target not in paths:
                problems.append(
                    f"inventory row {path} duplicate_of must name a row "
                    f"with equal bytes: {target}")
    return problems


def _structured_inventory_problems(root: Path, audit_ref: str) -> list[str]:
    """Reconcile the audit's structured inventory against observed bytes.

    Returns [] for a legacy audit without an inventory-v1 block. A present
    block must enumerate exactly the observed local set: missing rows,
    unobserved rows, digest drift, and undeclared duplicate bytes all fail.
    """
    audit = (root / audit_ref).resolve()
    try:
        audit.relative_to(root.resolve())
    except ValueError:
        return []
    if not audit.is_file():
        return []
    block, problems = _inventory_block(audit.read_text(encoding="utf-8"))
    if problems or block is None:
        return problems
    roots = block.get("roots")
    if not isinstance(roots, list) or not roots:
        return ["coverage audit inventory-v1 block needs a nonempty roots list"]
    materials = root.parent / "materials"
    observed, problems = _enumerate_inventory_roots(materials, roots)
    if problems:
        return problems
    return _inventory_row_problems(block, observed, materials)


def _inventory_view(block: dict) -> dict:
    """The human audit view, generated from the structured rows."""
    local, linked = [], []
    for row in block.get("rows") or []:
        if not isinstance(row, dict):
            continue
        if row.get("kind", "local") == "linked":
            linked.append({"reference": row.get("reference"),
                           "disposition": row.get("disposition"),
                           "observed": row.get("observed")})
        else:
            digest = row.get("sha256") or ""
            local.append({"path": row.get("path"),
                          "disposition": row.get("disposition"),
                          "sha256": digest[:12]})
    local.sort(key=lambda row: str(row.get("path")))
    linked.sort(key=lambda row: str(row.get("reference")))
    return {"local": local, "linked": linked}


def _observed_material_binding(root: Path, contract: dict) -> tuple[dict | None, list[str]]:
    """Bind the observed material set to the preflight report.

    Returns (None, []) for a legacy audit without an inventory-v1 block.
    Otherwise the fragment carries the observed-set digest the reviewed
    apply re-verifies, plus the generated human view of the rows.
    """
    audit_ref = contract.get("coverage_audit")
    if not isinstance(audit_ref, str) or not audit_ref.strip():
        return None, []
    audit = (root / audit_ref).resolve()
    try:
        audit.relative_to(root.resolve())
    except ValueError:
        return None, []
    if not audit.is_file():
        return None, []
    block, problems = _inventory_block(audit.read_text(encoding="utf-8"))
    if problems or block is None:
        return None, problems
    roots = block.get("roots")
    if not isinstance(roots, list) or not roots:
        return None, ["coverage audit inventory-v1 block needs a nonempty roots list"]
    materials = root.parent / "materials"
    observed, problems = _enumerate_inventory_roots(materials, roots)
    if problems:
        return None, problems
    problems = _inventory_row_problems(block, observed, materials)
    if problems:
        return None, problems
    digest = hashlib.sha256(json.dumps(
        {"roots": sorted(str(r) for r in roots),
         "files": {path: observed[path] for path in sorted(observed)}},
        ensure_ascii=False, sort_keys=True,
        separators=(",", ":")).encode("utf-8")).hexdigest()
    return ({"observed_material": {
                "sha256": f"sha256:{digest}",
                "roots": sorted(str(r) for r in roots),
                "local_files": len(observed),
                "rows": len(block.get("rows") or []),
             },
             "inventory_view": _inventory_view(block)}, [])


def _verify_observed_material(root: Path, contract: dict,
                              review_report: str | None) -> str | None:
    """Refuse a reviewed apply whose material moved since --check, else None.

    Legacy reports without an observed-material binding skip this check;
    old packages stay applicable. A present binding is recomputed live and
    must match exactly, or the operator re-runs --check on current bytes.
    """
    if not review_report:
        return None
    try:
        with open(review_report, encoding="utf-8") as handle:
            report = json.load(handle)
    except (OSError, ValueError):
        return None
    binding = report.get("observed_material") if isinstance(report, dict) else None
    if not isinstance(binding, dict) or not binding.get("sha256"):
        return None
    fragment, problems = _observed_material_binding(root, contract)
    if problems or fragment is None:
        detail = f": {problems[0]}" if problems else ""
        return ("material inventory changed since --check; re-run --check, "
                f"review the new report, then apply that report{detail}")
    if fragment["observed_material"]["sha256"] != binding["sha256"]:
        return ("relevant material changed since --check; re-run --check, "
                "review the new report, then apply that report")
    return None


def _ack_shape_problems(acknowledgments) -> list[str]:
    problems: list[str] = []
    if acknowledgments is None:
        return problems
    if not isinstance(acknowledgments, list):
        return ["acknowledgments must be a list"]
    for index, ack in enumerate(acknowledgments):
        where = f"acknowledgments[{index}]"
        if not isinstance(ack, dict):
            problems.append(f"{where} must be a mapping")
            continue
        for key in ("kind", "target", "reason"):
            if not isinstance(ack.get(key), str) or not ack.get(key).strip():
                problems.append(f"{where}.{key} must be a nonempty string")
    return problems


def _module_plan_contract_problems(root: Path, package: dict) -> list[str]:
    """Verify the human review evidence required before a plan is executable."""
    problems: list[str] = []
    contract = package.get("plan_contract")
    if not isinstance(contract, dict) or contract.get("version") != 2:
        return ["plan_contract.version must be 2 (see system/PLAN-CREATION-SOP.md)"]
    problems.extend(_coverage_audit_problems(root, contract))
    problems.extend(_ack_shape_problems(package.get("acknowledgments", [])))
    intentional_reorders = contract.get("intentional_reorders", [])
    if not isinstance(intentional_reorders, list):
        problems.append("plan_contract.intentional_reorders must be a list")
    else:
        seen: set[tuple[str, str]] = set()
        for index, declaration in enumerate(intentional_reorders):
            if not isinstance(declaration, dict):
                problems.append(
                    f"plan_contract.intentional_reorders[{index}] must be a mapping"
                )
                continue
            target = declaration.get("target")
            record_id = declaration.get("id")
            reason = declaration.get("reason")
            if target not in {"module-unit-order", "study-map-stage-order"}:
                problems.append(
                    f"plan_contract.intentional_reorders[{index}].target must be "
                    "module-unit-order or study-map-stage-order"
                )
            if not isinstance(record_id, str) or not record_id.strip():
                problems.append(
                    f"plan_contract.intentional_reorders[{index}].id must name the reordered record"
                )
            if not isinstance(reason, str) or not reason.strip():
                problems.append(
                    f"plan_contract.intentional_reorders[{index}].reason must explain the pedagogical change"
                )
            key = (str(target), str(record_id))
            if key in seen:
                problems.append(
                    f"plan_contract.intentional_reorders repeats {key[0]} for {key[1]}"
                )
            seen.add(key)
    for unit_index, entry in enumerate(package.get("units", []) or []):
        if not isinstance(entry, dict) or entry.get("study_map") is None:
            continue
        for problem in current_template_problems(entry.get("study_map"), "curriculum"):
            problems.append(f"units[{unit_index}].study_map: {problem}")
    _, synthesis_problems = _synthesis_entries(
        package.get("module_id", ""), package)
    problems.extend(synthesis_problems)
    return problems


def _relative_order_changed(before: list[str], after: list[str]) -> bool:
    """Return whether records present in both sequences changed relative order.

    Adding a new unit or stage is not a reorder. Moving existing records around
    the insertion is. That distinction lets plan expansion stay convenient
    while making accidental reshuffles fail closed.
    """
    shared = set(before) & set(after)
    return (
        [record_id for record_id in before if record_id in shared]
        != [record_id for record_id in after if record_id in shared]
    )


def _declared_reorders(package: dict) -> set[tuple[str, str]]:
    contract = package.get("plan_contract") or {}
    declarations = contract.get("intentional_reorders", []) or []
    return {
        (str(row.get("target")), str(row.get("id")))
        for row in declarations
        if isinstance(row, dict)
    }


def _module_plan_ordering_problems(repo, module_id: str, package: dict) -> list[str]:
    """Reject silent reordering while allowing explicit reviewed changes."""
    declared = _declared_reorders(package)
    actual_changes: set[tuple[str, str]] = set()
    problems: list[str] = []

    module_patch = package.get("module_patch", {}) or {}
    proposed_units = module_patch.get("unit_order")
    if isinstance(proposed_units, list):
        before_units = list(repo.modules[module_id].get("unit_order", []) or [])
        after_units = [str(record_id) for record_id in proposed_units]
        key = ("module-unit-order", module_id)
        if _relative_order_changed(before_units, after_units):
            actual_changes.add(key)
            if key not in declared:
                problems.append(
                    f"{module_id} reorders existing units; preserve their relative order or "
                    "declare an intentional module-unit-order change with a reason"
                )

    for entry in package.get("units", []) or []:
        if not isinstance(entry, dict) or not isinstance(entry.get("unit"), dict):
            continue
        uid = entry["unit"].get("id")
        proposed_map = entry.get("study_map")
        if not isinstance(uid, str) or not isinstance(proposed_map, dict):
            continue
        current_unit = repo.units.get(uid)
        current_id = (
            current_unit.data.get("current_study_map")
            if current_unit is not None
            else None
        )
        current_map = repo.study_maps.get(current_id) if current_id else None
        if current_map is None:
            continue
        before_stages = [
            str(stage.get("id"))
            for stage in current_map.data.get("stages", []) or []
            if isinstance(stage, dict) and stage.get("id")
        ]
        after_stages = [
            str(stage.get("id"))
            for stage in proposed_map.get("stages", []) or []
            if isinstance(stage, dict) and stage.get("id")
        ]
        key = ("study-map-stage-order", str(current_map.id))
        if _relative_order_changed(before_stages, after_stages):
            actual_changes.add(key)
            if key not in declared:
                problems.append(
                    f"{current_map.id} reorders existing stages; plan expansion must preserve "
                    "their relative order unless an intentional study-map-stage-order change "
                    "is declared with a reason"
                )

    for target, record_id in sorted(declared - actual_changes):
        problems.append(
            f"intentional reorder declared for {target} {record_id}, but the package does not "
            "reorder existing records"
        )
    return problems


def _unit_source_refs(unit_data: dict, map_data: dict | None) -> set[str]:
    refs: set[str] = set()
    for field in ("scope_sources", "source_selections"):
        for entry in unit_data.get(field, []) or []:
            sid = entry.get("source_id") if isinstance(entry, dict) else None
            if isinstance(sid, str):
                refs.add(sid)
    if isinstance(map_data, dict):
        for stage in map_data.get("stages", []) or []:
            if not isinstance(stage, dict):
                continue
            for field in ("resources", "source_feedback"):
                for entry in stage.get(field, []) or []:
                    sid = entry.get("source_id") if isinstance(entry, dict) else None
                    if isinstance(sid, str):
                        refs.add(sid)
    return refs


def _route_unit_id(route) -> str | None:
    if isinstance(route, str):
        return route
    if isinstance(route, dict) and isinstance(route.get("unit_id"), str):
        return route["unit_id"]
    return None


def _module_plan_routing_problems(repo, module_id: str, package: dict) -> list[str]:
    """Catch source omissions that ordinary referential validation cannot see."""
    source_map = package.get("source_map")
    if source_map is None:
        source_map = repo.module_source_maps.get(module_id, {})
    routes: dict[str, set[str]] = {}
    source_entries = source_map.get("sources", []) if isinstance(source_map, dict) else []
    for entry in source_entries or []:
        if not isinstance(entry, dict) or not isinstance(entry.get("source_id"), str):
            continue
        routed_units = {
            uid for route in (entry.get("unit_routes", []) or [])
            if (uid := _route_unit_id(route))
        }
        routes.setdefault(entry["source_id"], set()).update(routed_units)

    units: dict[str, tuple[dict, dict | None]] = {}
    for uid, unit in repo.units.items():
        if unit.module_id != module_id:
            continue
        study_map = repo.study_maps.get(unit.data.get("current_study_map"))
        units[uid] = (unit.data, study_map.data if study_map else None)
    for entry in package.get("units", []) or []:
        if not isinstance(entry, dict) or not isinstance(entry.get("unit"), dict):
            continue
        uid = entry["unit"].get("id")
        if isinstance(uid, str):
            units[uid] = (entry["unit"], entry.get("study_map"))

    problems: list[str] = []
    for uid, (unit_data, map_data) in sorted(units.items()):
        if isinstance(map_data, dict):
            try:
                map_data = expand_map(map_data, source_map, module_id, uid)
            except MaterialReferenceError as exc:
                problems.append(f"{uid}: {exc}")
                continue
        for sid in sorted(_unit_source_refs(unit_data, map_data)):
            if sid not in routes:
                problems.append(f"{uid} uses {sid}, but the module source map omits it")
            elif uid not in routes[sid]:
                problems.append(f"{uid} uses {sid}, but its source-map unit_routes omit the unit")
    for update in package.get("workspace_updates", []) or []:
        if not isinstance(update, dict):
            continue
        workspace = repo.workspaces.get(update.get("id"))
        if workspace is None or set(workspace.meta.get("module_ids", []) or []) != {module_id}:
            continue
        for sid in update.get("sources", []) or []:
            if sid not in routes:
                problems.append(
                    f"workspace {update.get('id')} lists {sid}, but the module source map omits it"
                )
    return problems


def _synthesis_entries(module_id: str, package: dict) -> tuple[list[tuple[str, dict]], list[str]]:
    """Split the optional atomic synthesis replacements from the package.

    Returns ``([(unit_id, dossier)], [problems])``. Shape problems are
    contract failures; an empty list with no problems means the package
    carries no replacements.
    """
    raw = package.get("material_syntheses", [])
    if raw is None:
        return [], []
    if not isinstance(raw, list):
        return [], ["material_syntheses must be a list"]
    entries: list[tuple[str, dict]] = []
    problems: list[str] = []
    seen: set[str] = set()
    for index, row in enumerate(raw):
        where = f"material_syntheses[{index}]"
        if not isinstance(row, dict):
            problems.append(f"{where} must be a mapping")
            continue
        unit_id = row.get("unit_id")
        dossier = row.get("dossier")
        if not isinstance(unit_id, str) or not unit_id.strip():
            problems.append(f"{where}.unit_id must name a unit")
            continue
        if unit_id in seen:
            problems.append(f"{where} repeats unit {unit_id}")
            continue
        seen.add(unit_id)
        if not isinstance(dossier, dict):
            problems.append(f"{where}.dossier must be a mapping")
            continue
        if dossier.get("unit_id", unit_id) != unit_id:
            problems.append(f"{where}.dossier.unit_id does not match {unit_id}")
            continue
        entries.append((unit_id, dossier))
    return entries, problems


_LEARNER_RESOURCE_FIELDS = ("independent_evidence",)


def _module_plan_check_report(root: Path, module_id: str, package: dict,
                              writes: dict[Path, str],
                              entries: list[tuple[str, dict]],
                              package_sha: str,
                              seen_units: set[str]) -> dict:
    """The review artifact for a plan preflight: stable schema, no writes.

    Counts, diffs, freshness and learner-state preservation for exactly the
    touched units, computed from the live repository and one staged shadow.
    """
    from learning_os.material_synthesis import validate_unit_material_synthesis as _validate_dossier

    live_repo = load_repo(root)
    live_map = (live_repo.module_source_maps or {}).get(module_id) or {}
    acknowledgments = package.get("acknowledgments", []) or []
    supplied = {unit_id for unit_id, _ in entries}
    with _staged_shadow(root, writes) as shadow:
        staged_repo = load_repo(shadow)
        staged_map = (staged_repo.module_source_maps or {}).get(module_id) or {}

        def rows(source_map):
            out: dict[str, dict] = {}
            for source in source_map.get("sources", []) or []:
                if not isinstance(source, dict):
                    continue
                for route in source.get("unit_routes", []) or []:
                    if isinstance(route, dict) and route.get("id"):
                        out.setdefault(str(route["id"]), route)
            return out

        live_rows, staged_rows = rows(live_map), rows(staged_map)
        units: dict[str, dict] = {}
        for uid in sorted(seen_units):
            live_study = next((sm.data for sm in live_repo.study_maps.values()
                               if sm.unit_id == uid), None)
            staged_study = next((sm.data for sm in staged_repo.study_maps.values()
                                 if sm.unit_id == uid), None)
            units[uid] = _unit_semantic_diff(live_map, staged_map, live_study, staged_study, uid)
        synthesis: dict[str, dict] = {}
        for uid in sorted(seen_units):
            try:
                destination = synthesis_destination(root, uid)
            except MaterialSynthesisError:
                continue
            exists = destination.exists()
            before: dict = {"present": exists, "fresh": False, "detail": None}
            if exists:
                try:
                    current = yaml.safe_load(destination.read_text(encoding="utf-8"))
                    validate_unit_material_synthesis(root, uid, current)
                    before["fresh"] = True
                except (MaterialSynthesisError, OSError, ValueError) as exc:
                    before["detail"] = str(exc)
            after: dict = {"replaced": uid in supplied, "fresh": False, "detail": None}
            if uid in supplied:
                dossier = dict(next(d for u, d in entries if u == uid))
                try:
                    _validate_dossier(shadow, uid, dossier, repo=staged_repo)
                    after["fresh"] = True
                except MaterialSynthesisError as exc:
                    after["detail"] = str(exc)
            elif exists and not before["fresh"]:
                after["detail"] = "live dossier already stale"
            elif exists:
                rows_live = _unit_route_rows(live_map, uid)
                rows_staged = _unit_route_rows(staged_map, uid)
                a, r, c = _evidential_diff(rows_live, rows_staged)
                if not (a or r or c):
                    after["fresh"] = True
                else:
                    after["detail"] = f"routes change without replacement: added={a} removed={r} changed={c}"
            synthesis[uid] = {"before": before, "after": after}
        ack_problems = _semantic_ack_problems(
            module_id, live_repo, staged_repo,
            sorted(set(seen_units)
                   | _route_changed_units(live_repo, staged_repo, module_id)),
            acknowledgments if isinstance(acknowledgments, list) else [])
    affected = sorted(str(p.resolve().relative_to(root.resolve())) for p in writes)
    changing: list[str] = []
    for path in writes:
        try:
            if (not path.exists()
                    or path.read_bytes() != writes[path].encode("utf-8")):
                changing.append(str(path.resolve().relative_to(root.resolve())))
        except OSError:
            changing.append(str(path.resolve().relative_to(root.resolve())))
    artifact_ids = [module_id, *sorted(seen_units),
                    *[d.get("id") for _, d in entries
                      if isinstance(d.get("id"), str)]]
    changing_writes = {}
    for path in writes:
        try:
            rel = str(path.resolve().relative_to(root.resolve()))
        except ValueError:
            continue
        if rel in changing:
            changing_writes[path] = writes[path]
    commit_artifact_ids = _minimal_artifact_ids(root, module_id, changing_writes, entries)
    revisions = load_revisions(root)
    live_sources = live_map.get("sources", []) or []
    staged_sources = staged_map.get("sources", []) or []
    return {
        "ok": True,
        "mode": "check",
        "module_id": module_id,
        "package_sha256": package_sha,
        "expected_snapshot": f"sha256:{canonical_fingerprint(root)}",
        "expected_revisions": {aid: revisions.get(aid, 0) for aid in artifact_ids},
        "artifact_ids": artifact_ids,
        "affected_files": affected,
        "byte_changing_files": sorted(changing),
        "route_counts": {"before": len(live_rows), "after": len(staged_rows)},
        "source_records": {"before": len(live_sources), "after": len(staged_sources)},
        "units": units,
        "routes_added": sorted(set(staged_rows) - set(live_rows)),
        "routes_removed": sorted(set(live_rows) - set(staged_rows)),
        "routes_updated": sorted(rid for rid in set(live_rows) & set(staged_rows)
                                 if live_rows[rid] != staged_rows[rid]),
        "synthesis": synthesis,
        "semantic_ack_required": ack_problems,
        "commit_artifact_ids": commit_artifact_ids,
        "canonical_files_written": 0,
    }


def _master_promotion_preflight(
    root: Path,
    module_id: str,
    plan: MasterPromotionPlan,
    package: dict,
    *,
    skip_validation: bool = False,
) -> list[str]:
    problems = _module_plan_contract_problems(root, package)
    if problems:
        return [f"contract: {problem}" for problem in problems]
    repo = load_repo(root)
    problems = _module_plan_routing_problems(repo, module_id, package)
    if problems:
        return [f"routing: {problem}" for problem in problems]
    if skip_validation:
        # A gateway apply enforces the validation layer inside its
        # transaction instead; the package layers above still refuse here.
        return []
    try:
        errors = _module_plan_validation_errors(root, plan.writes)
    except ValueError as exc:
        return [str(exc)]
    return [str(issue) for issue in errors]


def _master_promotion_check_result(
    root: Path,
    module_id: str,
    plan: MasterPromotionPlan,
) -> dict:
    return {
        "ok": True,
        "mode": "check",
        "module_id": module_id,
        "candidate_module_id": plan.provenance["candidate_module_id"],
        "promotion_id": plan.provenance["id"],
        "package_sha256": plan.package_sha256,
        "expected_snapshot": f"sha256:{canonical_fingerprint(root)}",
        "expected_revisions": dict(plan.expected_revisions),
        "artifact_ids": list(plan.artifact_ids),
        "affected_files": list(plan.affected_paths),
        "provenance": plan.provenance,
        "diff": plan.diff,
        "canonical_files_written": 0,
    }


def _cmd_master_promotion_import(args) -> int:
    root = _root(args)
    value = args.promotion
    if not isinstance(value, dict) or value.get("canonical_module_id") != args.module_id:
        print(
            "los: promotion must be an inline object whose canonical_module_id "
            "matches the requested module",
            file=sys.stderr,
        )
        return 2
    if not args.check:
        request = current_gateway_request()
        if request is None or request.capability != "module.plan.import":
            print(
                "los: live Master Planning promotion requires an approved "
                "GatewayEnvelopeV2; run --check directly for a no-write dry run",
                file=sys.stderr,
            )
            return 2
        if not getattr(args, "approve", False):
            print("los: Master Planning promotion requires exact gateway approval",
                  file=sys.stderr)
            return 2
        if not args.expected_snapshot:
            print("los: Master Planning promotion requires expected_snapshot",
                  file=sys.stderr)
            return 2

    with _operator_lock(root):
        try:
            plan = prepare_master_promotion(root, value)
        except MastersPlanningError as exc:
            print(f"los: Master Planning promotion refused: {exc}", file=sys.stderr)
            return 2
        supplied_hash = getattr(args, "package_sha256", None)
        if supplied_hash is not None and supplied_hash != plan.package_sha256:
            print(
                "los: promotion package hash does not match the exact checked content",
                file=sys.stderr,
            )
            print(json.dumps({
                "expected": plan.package_sha256,
                "supplied": supplied_hash,
            }, ensure_ascii=False), file=sys.stderr)
            _record_gateway_refusal(REVISION_CONFLICT, True)
            return 3
        if not args.check and supplied_hash is None:
            print(
                "los: live promotion requires the exact package_sha256 returned by --check",
                file=sys.stderr,
            )
            return 2

        problems = _master_promotion_preflight(
            root,
            args.module_id,
            plan,
            value["module_plan"],
            skip_validation=not args.check
            and current_gateway_request() is not None,
        )
        if problems:
            print(
                "los: Master Planning promotion preflight failed; no canonical "
                "files were written",
                file=sys.stderr,
            )
            for problem in problems[:12]:
                print(f"- {problem}", file=sys.stderr)
            return 1
        if args.check:
            print(json.dumps(
                _master_promotion_check_result(root, args.module_id, plan),
                indent=2,
                ensure_ascii=False,
            ))
            return 0

        if not _expected_ok(root, args.expected_snapshot):
            return 3
        try:
            expected_revisions = _expected_revisions_from_args(args)
        except WriteRefused as exc:
            print(f"los: {exc}", file=sys.stderr)
            return 2
        if expected_revisions != plan.expected_revisions:
            print(
                "los: promotion expected revisions must match the complete checked "
                "bundle; reload and run --check again",
                file=sys.stderr,
            )
            print(json.dumps({
                "expected": plan.expected_revisions,
                "supplied": expected_revisions,
            }, ensure_ascii=False), file=sys.stderr)
            _record_gateway_refusal(REVISION_CONFLICT, True)
            return 3
        validate_extra, gate_errors = _plan_apply_gate(root)
        code, errors, confirmation = _write_transaction(
            root,
            plan.writes,
            capability="module.plan.import",
            expected_revisions=expected_revisions,
            artifact_ids=plan.artifact_ids,
            validate_extra=validate_extra,
        )
        if gate_errors:
            # The in-transaction gate refused with the preflight's exact
            # list: report it with the preflight's exact text and exit,
            # dropping the transaction's recorded code, which the
            # preflight path never carried.
            _take_gateway_refusal()
            print(
                "los: Master Planning promotion preflight failed; no canonical "
                "files were written",
                file=sys.stderr,
            )
            for problem in gate_errors[:12]:
                print(f"- {problem}", file=sys.stderr)
            return 1
        if code:
            print("los: Master Planning promotion failed", file=sys.stderr)
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code
        result = {
            "ok": True,
            "mode": "apply",
            "module_id": args.module_id,
            "candidate_module_id": plan.provenance["candidate_module_id"],
            "promotion_id": plan.provenance["id"],
            "package_sha256": plan.package_sha256,
            "files_written": len(plan.writes),
            **confirmation,
        }
    print(json.dumps(result, ensure_ascii=False))
    return 0


_COMPACT_STAGE_FIELDS = frozenset({
    "title", "objective", "done_when", "exam_critical", "concepts",
    "scope_triage", "resources", "runtime_target", "runtime_review",
})

# Mirrors module-source-map.schema.json's role enum; the assembler refuses an
# unknown role with the join named instead of failing the staged schema check.
_SOURCE_MAP_ROLES = frozenset({
    "course-material", "spine", "first-exposure", "intuition", "derivation",
    "implementation", "practice", "exam-preparation", "optional-depth",
    "reference", "candidate",
})
_COMPACT_JOIN_FIELDS = frozenset({"source_id", "role", "why", "priority", "when"})


def _assemble_compact_module_revision(repo, module_id: str,
                                      revision: dict) -> tuple[dict | None, list[str]]:
    """Expand reviewed unit deltas against one live snapshot for the existing import gate."""
    problems: list[str] = []
    allowed = {"module_id", "plan_contract", "unit_revisions", "source_joins",
               "claim_evidence", "acknowledgments"}
    if set(revision) - allowed:
        problems.append(f"compact module revision has unknown fields: {sorted(set(revision) - allowed)}")
    if module_id not in repo.modules:
        problems.append(not_found("module", module_id, repo.modules))
    revisions = revision.get("unit_revisions")
    if not isinstance(revisions, list) or not revisions:
        problems.append("unit_revisions must be a non-empty list")
        return None, problems
    if problems:
        return None, problems
    source_map = copy.deepcopy(repo.module_source_maps.get(module_id) or {})
    joins = revision.get("source_joins")
    if joins is None:
        joins = []
    if not isinstance(joins, list):
        return None, ["source_joins must be a list"]
    joined_ids = {entry.get("source_id") for entry in source_map.get("sources", [])
                  if isinstance(entry, dict)}
    seen_joins: set[str] = set()
    for position, join in enumerate(joins):
        where = f"source_joins[{position}]"
        if not isinstance(join, dict):
            problems.append(f"{where} must be a mapping")
            continue
        unknown = set(join) - _COMPACT_JOIN_FIELDS
        if unknown:
            problems.append(f"{where} has unknown fields: {sorted(unknown)}")
            continue
        sid = join.get("source_id")
        if not isinstance(sid, str) or not sid:
            problems.append(f"{where} needs a source_id")
            continue
        if sid not in repo.sources:
            problems.append(f"{where} joins a source that is not registered: {sid}")
            continue
        if sid in joined_ids:
            problems.append(f"{where} joins a source already joined to {module_id}: {sid}")
            continue
        if sid in seen_joins:
            problems.append(f"{where} joins the same source twice: {sid}")
            continue
        role = join.get("role")
        if role not in _SOURCE_MAP_ROLES:
            problems.append(f"{where} role {role!r} is not a source-map role")
            continue
        why = join.get("why")
        if not isinstance(why, str) or not why.strip():
            problems.append(f"{where} needs a non-empty 'why'")
            continue
        priority = join.get("priority")
        if not isinstance(priority, int) or isinstance(priority, bool) or priority < 0:
            problems.append(f"{where} 'priority' must be an integer >= 0")
            continue
        when = join.get("when")
        if when is not None and not isinstance(when, str):
            problems.append(f"{where} 'when' must be a string")
            continue
        seen_joins.add(sid)
        entry: dict = {"source_id": sid, "role": role, "why": why,
                       "priority": priority, "unit_routes": []}
        if when is not None:
            entry["when"] = when
        source_map.setdefault("sources", []).append(entry)
    if problems:
        return None, problems
    entries: list[dict] = []
    syntheses: list[dict] = []
    seen_units: set[str] = set()
    for index, item in enumerate(revisions):
        where = f"unit_revisions[{index}]"
        if not isinstance(item, dict):
            problems.append(f"{where} must be a mapping")
            continue
        unknown = set(item) - {"unit_id", "route_changes", "stage_patches",
                               "material_synthesis"}
        if unknown:
            problems.append(f"{where} has unknown fields: {sorted(unknown)}")
        uid = item.get("unit_id")
        if not isinstance(uid, str) or uid in seen_units:
            problems.append(f"{where} needs a distinct unit_id")
            continue
        seen_units.add(uid)
        unit = repo.units.get(uid)
        if unit is None or unit.module_id != module_id:
            problems.append(f"{where} targets a unit outside {module_id}: {uid}")
            continue
        changes = item.get("route_changes", {})
        if not isinstance(changes, dict) or set(changes) - {"add", "update", "remove"}:
            problems.append(f"{where}.route_changes allows only add, update, remove")
            continue
        for kind in ("add", "update", "remove"):
            if not isinstance(changes.get(kind, []), list):
                problems.append(f"{where}.route_changes.{kind} must be a list")
        if problems:
            continue
        source_map, _, route_problems = _apply_unit_route_changes(
            source_map, module_id, uid, changes)
        problems.extend(f"{where}: {problem}" for problem in route_problems)
        patches = item.get("stage_patches", [])
        if not isinstance(patches, list):
            problems.append(f"{where}.stage_patches must be a list")
            continue
        current_id = unit.data.get("current_study_map")
        current_map = repo.study_maps.get(current_id) if current_id else None
        if patches and current_map is None:
            problems.append(f"{where} has no current study map to patch")
            continue
        base_data = None
        if patches and current_map is not None:
            # An append patch carries authored placements forward, so the whole
            # map starts from the authored form; legacy patches keep the
            # expanded base they were reviewed against.
            if any(isinstance(patch, dict) and "resources_append" in patch
                   for patch in patches):
                base_data = current_map.authored_data or current_map.data
            else:
                base_data = current_map.data
        study_map = copy.deepcopy(base_data) if base_data is not None else None
        stages = {stage.get("id"): stage for stage in study_map.get("stages", [])
                  if isinstance(stage, dict)} if study_map else {}
        existing_ids = {row.get("id") for stage in stages.values()
                        for row in (stage.get("resources") or [])
                        if isinstance(row, dict)}
        existing_ids = {rid for rid in existing_ids if isinstance(rid, str)}
        seen_stages: set[str] = set()
        for stage_index, patch in enumerate(patches):
            stage_where = f"{where}.stage_patches[{stage_index}]"
            if not isinstance(patch, dict) or "stage_id" not in patch \
                    or set(patch) - {"stage_id", "fields", "resources_append"}:
                problems.append(f"{stage_where} needs stage_id plus fields and/or resources_append")
                continue
            sid = patch["stage_id"]
            fields = patch.get("fields")
            append = patch.get("resources_append")
            if fields is None and append is None:
                problems.append(f"{stage_where} changes nothing; give fields and/or resources_append")
                continue
            if not isinstance(sid, str) or sid in seen_stages or sid not in stages:
                problems.append(f"{stage_where} names a missing or repeated stage: {sid}")
                continue
            seen_stages.add(sid)
            if fields is not None:
                if not isinstance(fields, dict) or not fields or set(fields) - _COMPACT_STAGE_FIELDS:
                    problems.append(f"{stage_where}.fields must be non-empty and limited to "
                                    f"{sorted(_COMPACT_STAGE_FIELDS)}")
                    continue
                if append is not None and "resources" in fields:
                    problems.append(f"{stage_where} cannot combine resources_append with fields.resources")
                    continue
            if append is not None:
                if not isinstance(append, list) or not append \
                        or any(not isinstance(row, dict) for row in append):
                    problems.append(f"{stage_where}.resources_append must be a non-empty list of resource objects")
                    continue
                new_ids = [row.get("id") for row in append]
                if any(not isinstance(rid, str) or not rid for rid in new_ids):
                    problems.append(f"{stage_where}.resources_append needs a fresh resource id on every row")
                    continue
                if len(set(new_ids)) != len(new_ids):
                    problems.append(f"{stage_where}.resources_append repeats a resource id")
                    continue
                collisions = [rid for rid in new_ids if rid in existing_ids]
                if collisions:
                    problems.append(f"{stage_where}.resources_append reuses an existing resource id: {collisions[0]}")
                    continue
            if fields is not None:
                stages[sid].update(copy.deepcopy(fields))
            if append is not None:
                stages[sid].setdefault("resources", []).extend(copy.deepcopy(append))
                existing_ids.update(row["id"] for row in append)
        dossier = item.get("material_synthesis")
        if dossier is not None:
            if not isinstance(dossier, dict) or dossier.get("unit_id", uid) != uid:
                problems.append(f"{where}.material_synthesis must belong to {uid}")
            else:
                syntheses.append({"unit_id": uid, "dossier": copy.deepcopy(dossier)})
        if not any(changes.get(kind) for kind in ("add", "update", "remove")) \
                and not patches and dossier is None:
            problems.append(f"{where} changes nothing")
        entries.append({"unit": copy.deepcopy(unit.data), "study_map": study_map})
    if problems:
        return None, problems
    package = {
        "module_id": module_id,
        "plan_contract": copy.deepcopy(revision.get("plan_contract")),
        "module_patch": {}, "source_patches": [], "source_map": source_map,
        "units": entries, "material_syntheses": syntheses,
        "claim_evidence": copy.deepcopy(revision.get("claim_evidence", [])),
        "acknowledgments": copy.deepcopy(revision.get("acknowledgments", [])),
        "workspace_updates": [],
    }
    return package, []


def _cmd_compact_module_plan_import(args, root: Path, source: Path,
                                    revision_bytes: bytes, revision: dict) -> int:
    """Use the same reviewed module.import transaction for a smaller input."""
    apply_sha = getattr(args, "apply_reviewed_sha256", None)
    if apply_sha:
        if args.check:
            print("los: --check and --apply-reviewed-sha256 are mutually exclusive",
                  file=sys.stderr)
            return 2
        from learning_os.commands.capability import reviewed_envelope_apply
        stale_material = _verify_observed_material(
            root, revision.get("plan_contract") or {},
            getattr(args, "review_report", None))
        if stale_material:
            print(f"los: {stale_material}", file=sys.stderr)
            return 2
        return reviewed_envelope_apply(
            root=root, capability_name="module.plan.import",
            payload={"module_id": args.module_id, "file": str(source),
                     "file_sha256": apply_sha},
            reviewed_content=revision_bytes, reviewed_sha256=apply_sha,
            review_report=getattr(args, "review_report", None),
            parser_factory=getattr(args, "_parser_factory", None))
    with _operator_lock(root):
        repo = load_repo(root)
        package, problems = _assemble_compact_module_revision(repo, args.module_id, revision)
        if problems:
            print("los: compact module revision failed; no canonical files were written",
                  file=sys.stderr)
            for problem in problems:
                print(f"- {problem}", file=sys.stderr)
            return 2
        assembled = _dump_yaml(package).encode("utf-8")
        fd, tmp_name = tempfile.mkstemp(prefix="learningos-module-revise-", suffix=".yaml")
        os.close(fd)
        tmp_path = Path(tmp_name)
        try:
            tmp_path.write_bytes(assembled)
            reviewed_sha = f"sha256:{hashlib.sha256(revision_bytes).hexdigest()}"
            inner = argparse.Namespace(
                root=getattr(args, "root", None), module_id=args.module_id,
                file=str(tmp_path),
                file_sha256=f"sha256:{hashlib.sha256(assembled).hexdigest()}",
                promotion=None, check=args.check,
                staged_basis=getattr(args, "staged_basis", None),
                expected_snapshot=args.expected_snapshot,
                expected_revision=list(getattr(args, "expected_revision", []) or []),
                _parser_factory=getattr(args, "_parser_factory", None),
                _minimal_writes=True,
                _review_input=(reviewed_sha,
                               {"module_id": args.module_id, "file": str(source),
                                "file_sha256": reviewed_sha}),
            )
            return cmd_module_plan_import(inner)
        finally:
            with contextlib.suppress(OSError):
                tmp_path.unlink()


def cmd_module_plan_import(args) -> int:
    """Apply one reviewable, module-scoped curriculum plan as a transaction.

    This gateway exists for the structural part of WORKFLOWS §23: a lecture
    batch may add units, their current study maps, module source routing, and
    explicit workspace joins together. It never deletes units or creates
    durable notes, and every stage remains bounded to the requested module.
    """
    if getattr(args, "staged_basis", None) and not args.check:
        print("los: --staged-basis requires --check", file=sys.stderr)
        return 2
    if getattr(args, "promotion", None) is not None:
        return _cmd_master_promotion_import(args)

    root = _root(args)
    try:
        _source, package_bytes = _read_content_bound_file(
            args.file,
            getattr(args, "file_sha256", None),
            label="module plan file",
        )
    except WriteRefused as exc:
        print(f"los: {exc}", file=sys.stderr)
        return 2
    try:
        package = yaml.safe_load(package_bytes.decode("utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        print(f"los: invalid module-plan YAML: {exc}", file=sys.stderr)
        return 2
    if not isinstance(package, dict) or package.get("module_id") != args.module_id:
        print("los: module plan must be a mapping with the requested module_id",
              file=sys.stderr)
        return 2
    if "unit_revisions" in package:
        return _cmd_compact_module_plan_import(args, root, _source,
                                               package_bytes, package)
    contract_problems = _module_plan_contract_problems(root, package)
    if contract_problems:
        print("los: module plan contract failed; no canonical files were written",
              file=sys.stderr)
        for problem in contract_problems:
            print(f"- {problem}", file=sys.stderr)
        return 2
    package_sha = f"sha256:{hashlib.sha256(package_bytes).hexdigest()}"
    synthesis_entries, _ = _synthesis_entries(args.module_id, package)
    acknowledgments = package.get("acknowledgments", []) or []
    if not isinstance(acknowledgments, list):
        acknowledgments = []
    apply_sha = getattr(args, "apply_reviewed_sha256", None)
    if apply_sha and args.check:
        print("los: --check and --apply-reviewed-sha256 are mutually exclusive",
              file=sys.stderr)
        return 2
    if apply_sha:
        from learning_os.commands.capability import reviewed_envelope_apply

        if not getattr(args, "file", None):
            print("los: --apply-reviewed-sha256 applies a --file plan package",
                  file=sys.stderr)
            return 2
        stale_material = _verify_observed_material(
            root, package.get("plan_contract") or {},
            getattr(args, "review_report", None))
        if stale_material:
            print(f"los: {stale_material}", file=sys.stderr)
            return 2
        return reviewed_envelope_apply(
            root=root,
            capability_name="module.plan.import",
            payload={"module_id": args.module_id, "file": str(_source),
                     "file_sha256": apply_sha},
            reviewed_content=package_bytes,
            reviewed_sha256=apply_sha,
            review_report=getattr(args, "review_report", None),
            parser_factory=getattr(args, "_parser_factory", None),
        )
    if not args.check and not args.expected_snapshot \
            and not getattr(args, "apply_reviewed_sha256", None):
        print("los: module plan import requires --expected-snapshot; run --check first, "
              "then copy snapshot.snapshot_id from bootstrap", file=sys.stderr)
        return 2

    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        repo = load_repo(root)
        module = repo.modules.get(args.module_id)
        if module is None:
            print(f"los: {not_found('module', args.module_id, repo.modules)}",
                  file=sys.stderr)
            return 2
        module_path = repo.module_origins[args.module_id]
        writes: dict[Path, str] = {}

        module_patch = package.get("module_patch", {}) or {}
        if not isinstance(module_patch, dict) or module_patch.get("id", args.module_id) != args.module_id:
            print("los: module_patch must stay inside the requested module", file=sys.stderr)
            return 2
        module_data = copy.deepcopy(module)
        module_data.update(module_patch)
        module_data["id"] = args.module_id
        writes[module_path] = _dump_yaml(module_data)

        source_map = package.get("source_map")
        if source_map is not None:
            if not isinstance(source_map, dict) or source_map.get("module_id") != args.module_id:
                print("los: source_map must belong to the requested module", file=sys.stderr)
                return 2
            target = repo.module_source_map_origins.get(
                args.module_id, module_path.parent / "source-map.yaml")
            writes[target] = _dump_yaml(source_map)

        source_patches = package.get("source_patches", []) or []
        if not isinstance(source_patches, list):
            print("los: source_patches must be a list", file=sys.stderr)
            return 2
        registry_texts: dict[Path, str] = {}
        patched_source_ids: set[str] = set()
        for patch in source_patches:
            sid = patch.get("id") if isinstance(patch, dict) else None
            if not sid or sid not in repo.sources or sid in patched_source_ids:
                print(f"los: source patch targets an unknown source: {sid}", file=sys.stderr)
                return 2
            patched_source_ids.add(sid)
            origin = repo.source_origins[sid]
            record = copy.deepcopy(repo.sources[sid])
            record.update(copy.deepcopy(patch))
            content = registry_texts.get(origin, origin.read_text(encoding="utf-8"))
            try:
                registry_texts[origin] = _replace_registry_list_record(content, sid, record)
            except ValueError as exc:
                print(f"los: {exc}", file=sys.stderr)
                return 2
        writes.update(registry_texts)

        units = package.get("units", []) or []
        if not isinstance(units, list):
            print("los: units must be a list", file=sys.stderr)
            return 2
        seen_units: set[str] = set()
        for entry in units:
            unit_data = entry.get("unit") if isinstance(entry, dict) else None
            map_data = entry.get("study_map") if isinstance(entry, dict) else None
            uid = unit_data.get("id") if isinstance(unit_data, dict) else None
            if not uid or uid in seen_units or unit_data.get("module_id") != args.module_id:
                print(f"los: invalid or duplicate module unit: {uid}", file=sys.stderr)
                return 2
            seen_units.add(uid)
            unit_dir = module_path.parent / "units" / uid
            writes[unit_dir / "unit.yaml"] = _dump_yaml(unit_data)
            if map_data is None:
                continue
            if not isinstance(map_data, dict) or map_data.get("unit_id") != uid:
                print(f"los: study map must belong to {uid}", file=sys.stderr)
                return 2
            existing_map = next((sm for sm in repo.study_maps.values() if sm.unit_id == uid), None)
            writes[unit_dir / "study-map.yaml"] = (
                _dump_study_map(existing_map, map_data) if existing_map else _dump_yaml(map_data)
            )
            prefix = f"curriculum/modules/{args.module_id}/units/{uid}/stages/"
            for stage in map_data.get("stages", []) or []:
                note_ref = stage.get("working_note") if isinstance(stage, dict) else None
                if not isinstance(note_ref, str) or not note_ref.startswith(prefix) \
                        or not note_ref.endswith("/notes.md"):
                    print(f"los: stage note escapes module/unit scope: {note_ref}", file=sys.stderr)
                    return 2
                note = root / note_ref
                if not note.exists():
                    writes[note] = ""

        synthesis_ids: list[str] = []
        for unit_id, dossier in synthesis_entries:
            unit = repo.units.get(unit_id)
            if unit is None or unit.module_id != args.module_id:
                print(f"los: synthesis replacement targets an unknown unit: {unit_id}",
                      file=sys.stderr)
                return 2
            try:
                destination = synthesis_destination(root, unit_id)
            except MaterialSynthesisError as exc:
                print(f"los: {exc}", file=sys.stderr)
                return 2
            writes[destination] = _dump_yaml(dossier)
            if isinstance(dossier.get("id"), str):
                synthesis_ids.append(dossier["id"])

        workspace_updates = package.get("workspace_updates", []) or []
        if not isinstance(workspace_updates, list):
            print("los: workspace_updates must be a list", file=sys.stderr)
            return 2
        for update in workspace_updates:
            wid = update.get("id") if isinstance(update, dict) else None
            workspace = repo.workspaces.get(wid)
            if workspace is None or workspace.archived or args.module_id not in workspace.meta.get("module_ids", []):
                print(f"los: workspace update is not joined to {args.module_id}: {wid}", file=sys.stderr)
                return 2
            meta = copy.deepcopy(workspace.meta)
            for key in ("sources", "unit_ids"):
                if key in update:
                    meta[key] = copy.deepcopy(update[key])
            body = workspace.body
            try:
                for heading, content in (update.get("sections", {}) or {}).items():
                    body = _replace_h2_section(body, str(heading), str(content))
            except ValueError as exc:
                print(f"los: {exc}", file=sys.stderr)
                return 2
            writes[workspace.path] = _render_frontmatter(meta, body)

        ordering_problems = _module_plan_ordering_problems(
            repo, args.module_id, package
        )
        if ordering_problems:
            print("los: module plan ordering preflight failed; no canonical files were written",
                  file=sys.stderr)
            for problem in ordering_problems:
                print(f"- {problem}", file=sys.stderr)
            return 1

        routing_problems = _module_plan_routing_problems(repo, args.module_id, package)
        if routing_problems:
            print("los: module plan routing preflight failed; no canonical files were written",
                  file=sys.stderr)
            for problem in routing_problems:
                print(f"- {problem}", file=sys.stderr)
            return 1
        lineage_problems, changed_claims, claim_evidence, live_routes = _phaseB_validate(
            root, repo, args.module_id, package)
        if lineage_problems:
            print("los: module plan lineage preflight failed; no canonical files were written",
                  file=sys.stderr)
            for problem in lineage_problems:
                print(f"- {problem}", file=sys.stderr)
            return 1
        if not args.check and (changed_claims or synthesis_entries):
            try:
                writes[root / LEDGER_RELATIVE] = _phaseB_ledger_text(
                    root, repo, args.module_id, package,
                    changed_claims, claim_evidence, live_routes,
                    synthesis_entries=synthesis_entries,
                    incremented_artifacts=_minimal_artifact_ids(
                        root, args.module_id, _drop_unchanged_writes(writes), synthesis_entries)
                    if getattr(args, "_minimal_writes", False) else None)
            except LineageError as exc:
                print("los: module plan lineage admission failed; no canonical files were written",
                      file=sys.stderr)
                print(f"- {exc}", file=sys.stderr)
                return 2
        if getattr(args, "_minimal_writes", False):
            writes = _drop_unchanged_writes(writes)
            if not writes and not args.check:
                print("los: revision changes no canonical bytes; nothing to apply",
                      file=sys.stderr)
                return 2
        basis_unit = getattr(args, "staged_basis", None)
        if basis_unit:
            if basis_unit not in seen_units:
                print(f"los: staged basis unit is not in this package: {basis_unit}",
                      file=sys.stderr)
                return 2
            from learning_os.material_synthesis import current_unit_material_basis

            try:
                with _staged_shadow(root, writes) as shadow:
                    basis = current_unit_material_basis(shadow, basis_unit)
            except (MaterialSynthesisError, OSError, ValueError) as exc:
                print(f"los: staged basis unavailable: {exc}", file=sys.stderr)
                return 2
            print(json.dumps({
                "unit_id": basis_unit,
                "basis": basis,
                "package_sha256": package_sha,
                "validated": False,
            }, indent=2, ensure_ascii=False, sort_keys=True))
            return 0
        # --check validates the shadow because nothing is written and it is
        # the only validation. A gateway apply instead enforces the same gate
        # inside its transaction (one full validation, on the staged state,
        # still refusing before anything commits); only a direct CLI apply —
        # which the transaction below refuses as envelope-less — keeps the
        # shadow refusal text it always had.
        if args.check or current_gateway_request() is None:
            try:
                errors = _module_plan_validation_errors(
                    root, writes,
                    module_id=args.module_id,
                    syntheses=synthesis_entries,
                    touched_units=sorted(seen_units),
                    acknowledgments=acknowledgments,
                )
            except ValueError as exc:
                print(f"los: {exc}", file=sys.stderr)
                return 2
            if errors:
                print("los: module plan validation preflight failed; no canonical files were written",
                      file=sys.stderr)
                for issue in errors[:12]:
                    print(issue, file=sys.stderr)
                return 1
        if args.check:
            result = _module_plan_check_report(
                root, args.module_id, package, writes,
                synthesis_entries, package_sha, seen_units)
            result["units_checked"] = sorted(seen_units)
            result["files_checked"] = len(writes)
            from learning_os.ops._legacy_plumbing import prepare_review_envelope

            capability = getattr(args, "_capability_override", None) or "module.plan.import"
            review_input = getattr(args, "_review_input", None)
            reviewed_sha = review_input[0] if review_input else package_sha
            payload = review_input[1] if review_input else {
                "module_id": args.module_id, "file": str(_source), "file_sha256": package_sha}
            owners = result["commit_artifact_ids"] if getattr(args, "_minimal_writes", False) \
                else [args.module_id, *sorted(seen_units), *synthesis_ids]
            result["expected_revisions"] = {aid: load_revisions(root).get(aid, 0) for aid in owners}
            result["commit_artifact_ids"] = owners
            result["reviewed_file_sha256"] = reviewed_sha
            result["assembled_package_sha256"] = package_sha
            result["capability"] = capability
            result["changes"] = "present" if writes else "none"
            result["expected_write_paths"] = sorted({
                str(p.relative_to(root)) for p in writes
            } | ({LEDGER_RELATIVE} if changed_claims or synthesis_entries else set()))
            result["expected_write_sha256"] = {
                str(p.relative_to(root)): hashlib.sha256(content.encode("utf-8")).hexdigest()
                for p, content in writes.items()}
            result["gateway_envelope"] = prepare_review_envelope(
                capability, payload, result["expected_snapshot"], result["expected_revisions"])
            fragment, inventory_problems = _observed_material_binding(
                root, package.get("plan_contract") or {})
            if inventory_problems:
                print("los: module plan inventory preflight failed; "
                      "no canonical files were written", file=sys.stderr)
                for problem in inventory_problems:
                    print(f"- {problem}", file=sys.stderr)
                return 1
            if fragment is not None:
                result.update(fragment)
            report_out = getattr(args, "report_out", None)
            if report_out:
                compact, failure = _save_check_report_and_compact(
                    root, result, report_out,
                    draft=getattr(args, "_report_out_draft", None))
                if failure is not None:
                    code, message = failure
                    print(f"los: {message}; no canonical files were written",
                          file=sys.stderr)
                    return code
                result = compact
        else:
            if getattr(args, "_minimal_writes", False):
                artifact_ids = _minimal_artifact_ids(
                    root, args.module_id, writes, synthesis_entries)
            else:
                artifact_ids = [args.module_id, *sorted(seen_units), *synthesis_ids]
            validate_extra, gate_errors = _plan_apply_gate(
                root, live_repo=repo, module_id=args.module_id,
                syntheses=synthesis_entries,
                touched_units=sorted(seen_units),
                acknowledgments=acknowledgments)
            code, errors, confirmation = _write_transaction(
                root, writes,
                capability=getattr(args, "_capability_override", None)
                or "module.plan.import",
                expected_revisions=_expected_revisions_from_args(args),
                artifact_ids=artifact_ids,
                validate_extra=validate_extra,
            )
            if gate_errors:
                # The in-transaction gate refused with the preflight's exact
                # list: report it with the preflight's exact text and exit,
                # dropping the transaction's recorded code, which the
                # preflight path never carried.
                _take_gateway_refusal()
                print("los: module plan validation preflight failed; no canonical files were written",
                      file=sys.stderr)
                for issue in gate_errors[:12]:
                    print(issue, file=sys.stderr)
                return 1
            if code:
                print("los: module plan import failed", file=sys.stderr)
                for issue in errors[:12]:
                    print(issue, file=sys.stderr)
                return code
            result = {"ok": True, "mode": "apply", "module_id": args.module_id,
                      "units_written": sorted(seen_units), "files_written": len(writes),
                      **confirmation}
    print(json.dumps(result, ensure_ascii=False))
    return 0


def _drop_unchanged_writes(writes: dict[Path, str]) -> dict[Path, str]:
    """Keep only writes that change bytes: new files or different content."""
    kept: dict[Path, str] = {}
    for path, content in writes.items():
        try:
            if path.is_file() and path.read_bytes() == content.encode("utf-8"):
                continue
        except OSError:
            pass
        kept[path] = content
    return kept


def _minimal_artifact_ids(root: Path, module_id: str, writes: dict[Path, str],
                          entries: list[tuple[str, dict]]) -> list[str]:
    """Semantic owners for exactly the files a unit revision changes."""
    ids: list[str] = []
    dossier_by_unit = {unit_id: dossier for unit_id, dossier in entries}
    for path in writes:
        try:
            rel = path.resolve().relative_to(root.resolve())
        except ValueError:
            continue
        parts = rel.parts
        if len(parts) >= 4 and parts[0] == "curriculum" and parts[1] == "modules" \
                and parts[3] == "source-map.yaml":
            if module_id not in ids:
                ids.append(module_id)
        elif "units" in parts:
            uid = parts[parts.index("units") + 1]
            if rel.name == "material-synthesis.yaml":
                dossier = dossier_by_unit.get(uid, {})
                did = dossier.get("id") if isinstance(dossier, dict) else None
                if isinstance(did, str) and did not in ids:
                    ids.append(did)
            elif uid not in ids:
                ids.append(uid)
    return ids


#: Route fields a unit revision may change in place. Identity and ownership
#: (`id`, `unit_id`, and the parent `source_id`) move only through a
#: remove-plus-add pair, so a silent cross-unit move is never an "update".
UNIT_ROUTE_UPDATE_FIELDS = frozenset({
    "title", "format", "angle", "angle_detail", "covers", "depth", "scope",
    "locator", "url", "vault_path", "exposes_solutions_for", "requires_assets",
})


def _unit_revision_contract_problems(root: Path, unit_id: str, revision: dict) -> list[str]:
    """The compact v1 contract: same audit evidence, lecture-scoped shape."""
    problems: list[str] = []
    if not isinstance(revision, dict):
        return ["unit revision must be a mapping"]
    unknown = set(revision) - {"unit_id", "plan_contract", "route_changes", "study_map",
                               "material_synthesis", "claim_evidence", "acknowledgments"}
    if unknown:
        problems.append(f"unknown revision fields: {sorted(unknown)}")
    if revision.get("unit_id", unit_id) != unit_id:
        problems.append("revision unit_id does not match the requested unit")
    contract = revision.get("plan_contract")
    if not isinstance(contract, dict) or contract.get("version") != 1:
        problems.append("plan_contract.version must be 1 (see system/PLAN-CREATION-SOP.md)")
    else:
        problems.extend(_coverage_audit_problems(root, contract))
    changes = revision.get("route_changes", {})
    if changes is None:
        changes = {}
    if not isinstance(changes, dict):
        problems.append("route_changes must be a mapping")
    else:
        if set(changes) - {"add", "update", "remove"}:
            problems.append("route_changes allows only add, update, remove")
        for key in ("add", "update", "remove"):
            items = changes.get(key, [])
            if items is None:
                continue
            if not isinstance(items, list):
                problems.append(f"route_changes.{key} must be a list")
    study_map = revision.get("study_map")
    if study_map is not None:
        if not isinstance(study_map, dict) or study_map.get("unit_id", unit_id) != unit_id:
            problems.append("study_map must belong to the requested unit")
        else:
            for problem in current_template_problems(study_map, "curriculum"):
                problems.append(f"study_map: {problem}")
    dossier = revision.get("material_synthesis")
    if dossier is not None and not isinstance(dossier, dict):
        problems.append("material_synthesis must be a mapping")
    elif isinstance(dossier, dict) and dossier.get("unit_id", unit_id) != unit_id:
        problems.append("material_synthesis.unit_id does not match the requested unit")
    claim_evidence = revision.get("claim_evidence", [])
    if claim_evidence is None:
        pass
    elif not isinstance(claim_evidence, list) or any(
            not isinstance(row, dict) for row in claim_evidence):
        problems.append("claim_evidence must be a list of mappings")
    problems.extend(_ack_shape_problems(revision.get("acknowledgments", [])))
    return problems


def _apply_unit_route_changes(source_map: dict, module_id: str, unit_id: str,
                              changes: dict) -> tuple[dict, dict, list[str]]:
    """Apply add/update/remove ops to one unit's routes, fail closed.

    Returns ``(new_source_map, summary, problems)``. Unrelated routes are
    carried forward untouched internally; the caller never copies them.
    """
    problems: list[str] = []
    new_map = copy.deepcopy(source_map)
    sources = new_map.get("sources", []) or []
    by_id: dict[str, tuple[dict, dict]] = {}
    for source in sources:
        if not isinstance(source, dict):
            continue
        for route in source.get("unit_routes", []) or []:
            if isinstance(route, dict) and route.get("id"):
                by_id.setdefault(str(route["id"]), (source, route))

    def unit_of(route) -> str | None:
        return route.get("unit_id") if isinstance(route, dict) else None

    summary: dict[str, list[str]] = {"added": [], "updated": [], "removed": []}
    operated: set[str] = set()
    for kind in ("add", "update", "remove"):
        for row in changes.get(kind, []) or []:
            if not isinstance(row, dict):
                continue
            allowed = {"source_id", "route"} if kind == "add" else \
                {"route_id", "fields"} if kind == "update" else {"route_id", "reason"}
            if set(row) - allowed:
                problems.append(f"route_changes.{kind} has unknown fields "
                                f"{sorted(set(row) - allowed)}; expected {sorted(allowed)}")
            route = row.get("route") if kind == "add" else row
            rid = route.get("id" if kind == "add" else "route_id") if isinstance(route, dict) else None
            if isinstance(rid, str):
                if rid in operated:
                    problems.append(f"ambiguous repeated route operation: {rid}")
                operated.add(rid)
    if problems:
        return new_map, summary, problems
    for row in (changes.get("add", []) or []):
        if not isinstance(row, dict):
            problems.append("route_changes.add entries must be mappings")
            continue
        source_id = row.get("source_id")
        route = row.get("route")
        if not isinstance(source_id, str) or not isinstance(route, dict):
            problems.append("route_changes.add needs {source_id, route}")
            continue
        rid = route.get("id")
        if not isinstance(rid, str) or not rid.strip():
            problems.append("route_changes.add route needs a stable id")
            continue
        if rid in by_id:
            problems.append(f"route_changes.add duplicates existing route: {rid}")
            continue
        if route.get("unit_id") != unit_id:
            problems.append(f"route_changes.add {rid} must belong to {unit_id}")
            continue
        missing = [k for k in ("title", "format", "angle", "covers", "depth", "scope")
                   if k not in route]
        if missing:
            problems.append(f"route_changes.add {rid} lacks rich route fields: {missing}")
            continue
        targets = [s for s in sources
                   if isinstance(s, dict) and s.get("source_id") == source_id]
        if not targets:
            problems.append(f"route_changes.add {rid} names an unknown source: {source_id}")
            continue
        stored = {k: v for k, v in route.items() if k != "source_id"}
        targets[0].setdefault("unit_routes", []).append(stored)
        by_id[rid] = (targets[0], stored)
        summary["added"].append(rid)
    for row in (changes.get("update", []) or []):
        if not isinstance(row, dict):
            problems.append("route_changes.update entries must be mappings")
            continue
        rid = row.get("route_id")
        fields = row.get("fields", {})
        if not isinstance(rid, str) or not isinstance(fields, dict):
            problems.append("route_changes.update needs {route_id, fields}")
            continue
        found = by_id.get(rid)
        if found is None:
            problems.append(f"route_changes.update names a missing route: {rid}")
            continue
        _, route = found
        if unit_of(route) != unit_id:
            problems.append(f"route_changes.update {rid} belongs to another unit")
            continue
        unknown = sorted(set(fields) - UNIT_ROUTE_UPDATE_FIELDS)
        if unknown:
            problems.append(
                f"route_changes.update {rid} touches identity/ownership fields: {unknown}")
            continue
        if not fields:
            problems.append(f"route_changes.update {rid} changes nothing")
            continue
        route.update(copy.deepcopy(fields))
        summary["updated"].append(rid)
    for row in (changes.get("remove", []) or []):
        if not isinstance(row, dict):
            problems.append("route_changes.remove entries must be mappings")
            continue
        rid = row.get("route_id")
        reason = row.get("reason")
        if not isinstance(rid, str):
            problems.append("route_changes.remove needs a route_id")
            continue
        if not isinstance(reason, str) or not reason.strip():
            problems.append(f"route_changes.remove {rid} needs a disposition reason")
            continue
        found = by_id.get(rid)
        if found is None:
            problems.append(f"route_changes.remove names a missing route: {rid}")
            continue
        source, route = found
        if unit_of(route) != unit_id:
            problems.append(f"route_changes.remove {rid} belongs to another unit")
            continue
        source["unit_routes"].remove(route)
        del by_id[rid]
        summary["removed"].append(rid)
    for key in summary:
        summary[key] = sorted(summary[key])
    return new_map, summary, problems


def _report_out_target(target_text: str) -> Path:
    """Resolve a --report-out target against the filesystem, not the repo."""
    return Path(target_text).expanduser().resolve()


def _report_out_target_problem(root: Path, target_text: str, *, draft: str | None) -> str | None:
    """Refuse a --report-out target that would endanger the review.

    The saved report must land outside the repository (writing under the
    guarded roots would move the snapshot it attests), must never replace
    the reviewed draft, and must never overwrite an existing saved report.
    Returns an error message, or None when the target is acceptable.
    """
    root_resolved = root.resolve()
    try:
        target = _report_out_target(target_text)
    except OSError as exc:
        return f"cannot resolve --report-out target: {exc}"
    if target == root_resolved or root_resolved in target.parents:
        return f"--report-out target must be outside the repository: {target_text}"
    if draft:
        try:
            if target == Path(draft).expanduser().resolve():
                return f"--report-out target must not replace the reviewed draft: {target_text}"
        except OSError:
            pass
    parent = target.parent
    if not parent.is_dir():
        return f"--report-out directory does not exist: {parent}"
    if target.exists() or target.is_symlink():
        return f"--report-out target already exists; refusing to overwrite: {target_text}"
    return None


def _save_check_report_and_compact(
    root: Path, result: dict, target_text: str, *, draft: str | None,
) -> tuple[dict | None, tuple[int, str] | None]:
    """Save one complete check report, return its compact stdout shape.

    The saved bytes are exactly what a bare --check would print, so the
    complete report stays the object of review, apply, receipt verification
    and recovery. The compact response carries every review field except
    the sealed gateway_envelope, plus the saved report's path and digest.
    No second envelope is ever prepared. Returns (compact, None) on
    success, or (None, (exit_code, message)) on failure.
    """
    problem = _report_out_target_problem(root, target_text, draft=draft)
    if problem is not None:
        return None, (2, problem)
    target = _report_out_target(target_text)
    payload = (json.dumps(result, ensure_ascii=False) + "\n").encode("utf-8")
    try:
        fd, tmp_name = tempfile.mkstemp(prefix=".check-report-", suffix=".tmp",
                                        dir=str(target.parent))
    except OSError as exc:
        return None, (1, f"could not save --report-out report: {exc}")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
        try:
            os.link(tmp_name, target)
        except FileExistsError:
            return None, (2, f"--report-out target already exists; refusing to overwrite: {target_text}")
        except OSError as exc:
            return None, (1, f"could not save --report-out report: {exc}")
    except OSError as exc:
        return None, (1, f"could not save --report-out report: {exc}")
    finally:
        with contextlib.suppress(OSError):
            Path(tmp_name).unlink()
    digest = "sha256:" + hashlib.sha256(payload).hexdigest()
    compact = {key: value for key, value in result.items() if key != "gateway_envelope"}
    compact["saved_report"] = {
        "path": str(target),
        "sha256": digest,
        "bytes": len(payload),
    }
    return compact, None


def cmd_unit_plan_revise(args) -> int:
    # Assembly, preflight and the report must observe one locked snapshot.
    with _operator_lock(_root(args)):
        return _unit_plan_revise_locked(args)


def _unit_plan_revise_locked(args) -> int:
    """Revise one existing lecture: compact patch in, one governed transaction out.

    The compact revision names only what changes — route ops, the reviewed
    final study map, and an optional replacement dossier. Unrelated source-map
    routes are carried forward internally, and the assembled full package runs
    the same validation, receipt and rollback path as `module.plan.import`,
    with artifact IDs for exactly the semantic owners the revision touches.
    """
    root = _root(args)
    revision = getattr(args, "record", None)
    if revision is None:
        if not getattr(args, "file", None):
            print("los: unit-plan-revise needs --file or --record",
                  file=sys.stderr)
            return 2
        try:
            _source, revision_bytes = _read_content_bound_file(
                args.file, getattr(args, "file_sha256", None),
                label="unit revision file",
            )
        except WriteRefused as exc:
            print(f"los: {exc}", file=sys.stderr)
            return 2
        try:
            revision = yaml.safe_load(revision_bytes.decode("utf-8"))
        except (UnicodeDecodeError, yaml.YAMLError) as exc:
            print(f"los: invalid unit-revision YAML: {exc}", file=sys.stderr)
            return 2
    contract_problems = _unit_revision_contract_problems(root, args.unit_id, revision)
    if contract_problems:
        print("los: unit revision contract failed; no canonical files were written",
              file=sys.stderr)
        for problem in contract_problems:
            print(f"- {problem}", file=sys.stderr)
        return 2
    report_out = getattr(args, "report_out", None)
    if report_out:
        if getattr(args, "apply_reviewed_sha256", None):
            print("los: --report-out is only for --check; it cannot be combined with reviewed apply",
                  file=sys.stderr)
            return 2
        if getattr(args, "staged_basis", None):
            print("los: --report-out is only for ordinary final --check; it cannot be combined with --staged-basis",
                  file=sys.stderr)
            return 2
        if not args.check:
            print("los: --report-out needs --check; run the ordinary final preflight first",
                  file=sys.stderr)
            return 2
        target_problem = _report_out_target_problem(
            root, report_out, draft=getattr(args, "file", None))
        if target_problem:
            print(f"los: {target_problem}", file=sys.stderr)
            return 2
    _apply_flag = getattr(args, "apply_reviewed_sha256", None)
    if _apply_flag:
        if args.check or getattr(args, "record", None) is not None:
            print("los: reviewed apply needs --file and cannot use --check or --record", file=sys.stderr)
            return 2
        from learning_os.commands.capability import reviewed_envelope_apply

        stale_material = _verify_observed_material(
            root, revision.get("plan_contract") or {},
            getattr(args, "review_report", None))
        if stale_material:
            print(f"los: {stale_material}", file=sys.stderr)
            return 2
        return reviewed_envelope_apply(
            root=root, capability_name="unit.plan.revise",
            payload={"unit_id": args.unit_id, "record": revision},
            reviewed_content=revision_bytes, reviewed_sha256=_apply_flag,
            review_report=getattr(args, "review_report", None),
            parser_factory=getattr(args, "_parser_factory", None))
    if not args.check and not args.expected_snapshot and not _apply_flag:
        print("los: unit plan revise requires --expected-snapshot; run --check first, "
              "then copy the expected_snapshot from the check report", file=sys.stderr)
        return 2
    repo = load_repo(root)
    unit = repo.units.get(args.unit_id)
    if unit is None:
        print(f"los: {not_found('unit', args.unit_id, repo.units)}",
              file=sys.stderr)
        return 2
    module_id = unit.module_id
    live_map = copy.deepcopy(repo.module_source_maps.get(module_id) or {})
    changes = revision.get("route_changes", {}) or {}
    new_map, _route_summary, route_problems = _apply_unit_route_changes(
        live_map, module_id, args.unit_id, changes)
    if route_problems:
        print("los: unit revision route changes failed; no canonical files were written",
              file=sys.stderr)
        for problem in route_problems:
            print(f"- {problem}", file=sys.stderr)
        return 2
    contract = revision["plan_contract"]
    unit_data = copy.deepcopy(unit.data)
    map_data = copy.deepcopy(revision.get("study_map"))
    dossier = copy.deepcopy(revision.get("material_synthesis"))
    package = {
        "module_id": module_id,
        "plan_contract": {
            "version": 2,
            "plan_template_version": contract.get("plan_template_version"),
            "coverage_audit": contract.get("coverage_audit"),
            "checks": copy.deepcopy(contract.get("checks")),
            "intentional_reorders": [],
        },
        "module_patch": {},
        "source_map": new_map,
        "units": [{"unit": unit_data, "study_map": map_data}],
        "claim_evidence": copy.deepcopy(revision.get("claim_evidence", []) or []),
        "acknowledgments": copy.deepcopy(revision.get("acknowledgments", []) or []),
    }
    if isinstance(dossier, dict):
        package["material_syntheses"] = [
            {"unit_id": args.unit_id, "dossier": dossier}]
    package_bytes = _dump_yaml(package).encode("utf-8")

    def _run(check: bool, expected_snapshot):
        fd, tmp_name = tempfile.mkstemp(prefix="learningos-unit-revise-", suffix=".yaml")
        os.close(fd)
        tmp_path = Path(tmp_name)
        try:
            tmp_path.write_bytes(package_bytes)
            inner = argparse.Namespace(
                root=getattr(args, "root", None),
                module_id=module_id,
                file=str(tmp_path),
                file_sha256=f"sha256:{hashlib.sha256(package_bytes).hexdigest()}",
                promotion=None,
                check=check,
                staged_basis=getattr(args, "staged_basis", None),
                expected_snapshot=expected_snapshot,
                expected_revision=list(getattr(args, "expected_revision", []) or []),
                _parser_factory=getattr(args, "_parser_factory", None),
                _capability_override="unit.plan.revise",
                _minimal_writes=True,
                report_out=getattr(args, "report_out", None),
                _report_out_draft=(str(args.file) if getattr(args, "file", None) else None),
                _review_input=(
                    "sha256:" + hashlib.sha256(revision_bytes).hexdigest()
                    if getattr(args, "record", None) is None else None,
                    {"unit_id": args.unit_id, "record": revision}),
            )
            return cmd_module_plan_import(inner)
        finally:
            with contextlib.suppress(OSError):
                tmp_path.unlink()

    return _run(bool(args.check), args.expected_snapshot)
