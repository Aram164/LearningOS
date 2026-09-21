"""Academic modules and the module plan import, including its contract and routing checks."""

from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

import yaml

from learning_os.contracts import PLAN_TEMPLATE_VERSION, current_template_problems
from learning_os.contracts.gateway import current_gateway_request
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
    synthesis_destination,
    validate_unit_material_synthesis,
)
from learning_os.materials_resolution import evidential_route_projection, sha256_file
from learning_os.render import replace_h2_section as _replace_h2_section
from learning_os.revisions import load_revisions
from learning_os.rules import validate
from learning_os.semantics.lineage import (
    LEDGER_RELATIVE,
    LineageError,
    dump_ledger,
    emit_route_covers,
    load_ledger,
    to_dict,
    withdraw,
)
from learning_os.warning_baseline import delta, load_baseline, signatures_from_issues

from .support import (
    WriteRefused,
    _atomic_text,
    _dump_study_map,
    _dump_yaml,
    _expected_ok,
    _expected_revisions_from_args,
    _fresh_manifest,
    _operator_lock,
    _print_rows,
    _read_content_bound_file,
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
                       incremented_artifacts=None):
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
    touched_units = set()
    for rid in sorted(changed):
        unit_id = str((package_routes.get(rid) or live_routes.get(rid) or {}).get("unit_id") or "")
        if unit_id:
            touched_units.add(unit_id)
    # Post-apply stamping: the gateway increments exactly module_id and the
    # units supplied in the package (see cmd_module_plan_import artifact_ids).
    # Stamping pre-commit values leaves every new claim immediately stale
    # after its own commit. Touched units absent from the package are not
    # incremented, so they stay at current.
    package_unit_ids = set()
    for entry in package.get("units", []) or []:
        unit_data = entry.get("unit") if isinstance(entry, dict) else None
        uid = unit_data.get("id") if isinstance(unit_data, dict) else None
        if isinstance(uid, str) and uid \
                and unit_data.get("module_id") == module_id:
            package_unit_ids.add(uid)
    incremented = ({module_id} | package_unit_ids) if incremented_artifacts is None \
        else set(incremented_artifacts)

    def _post_apply(artifact: str) -> int:
        base = current_revisions.get(artifact, 0)
        return base + 1 if artifact in incremented else base

    stamped = {module_id: _post_apply(module_id)}
    for unit_id in sorted(touched_units):
        if unit_id not in stamped:
            stamped[unit_id] = _post_apply(unit_id)
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
        read_revisions = dict(stamped)
        for artifact, revision in declared.items():
            # Declared reads were validated fresh against pre-commit state;
            # store post-apply validity for incremented artifacts so the new
            # claim is supported immediately after its own commit.
            if artifact in incremented:
                read_revisions[artifact] = current_revisions.get(artifact, 0) + 1
            else:
                read_revisions[artifact] = revision
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


def _unit_route_rows(source_map: dict, unit_id: str) -> dict[str, dict]:
    """This unit's routes from a module source-map document, keyed by route ID."""
    rows: dict[str, dict] = {}
    for source in source_map.get("sources", []) or []:
        if not isinstance(source, dict):
            continue
        source_id = source.get("source_id")
        for route in source.get("unit_routes", []) or []:
            if not isinstance(route, dict) or route.get("unit_id") != unit_id:
                continue
            rid = route.get("id")
            if isinstance(rid, str) and rid not in rows:
                row = dict(route)
                row["source_id"] = source_id
                rows[rid] = row
    return rows


def _evidential_diff(live_rows: dict[str, dict],
                     staged_rows: dict[str, dict]) -> tuple[list[str], list[str], list[str]]:
    """(added, removed, evidentially-changed) route IDs between two route sets.

    Angle, title, depth and other exempt prose never appears here: those edits
    intentionally keep a dossier fresh. Anything in the evidential projection
    — identity, locator, material binding, coverage, scope — does.
    """
    added = sorted(set(staged_rows) - set(live_rows))
    removed = sorted(set(live_rows) - set(staged_rows))
    changed: list[str] = []
    for rid in sorted(set(live_rows) & set(staged_rows)):
        try:
            before = evidential_route_projection(live_rows[rid])
        except ValueError:
            before = {k: v for k, v in live_rows[rid].items() if k != "angle"
                      if k != "angle_detail"}
        try:
            after = evidential_route_projection(staged_rows[rid])
        except ValueError:
            after = {k: v for k, v in staged_rows[rid].items() if k != "angle"
                     if k != "angle_detail"}
        if before != after:
            changed.append(rid)
    return added, removed, changed


def _staged_synthesis_errors(root: Path, module_id: str, live_repo,
                             shadow: Path, shadow_repo,
                             entries: list[tuple[str, dict]]) -> list[str]:
    """Validate replacements against staged state and demand missing ones.

    Every replacement dossier is validated against the shadow post-change
    repository — never the live tree — so the new source map, study maps and
    dossier commit or roll back together. Units with an existing dossier whose
    routes change evidentially without a replacement get one actionable
    diagnostic instead of a stale commit.
    """
    errors: list[str] = []
    supplied = {unit_id for unit_id, _ in entries}
    live_map = (live_repo.module_source_maps or {}).get(module_id) or {}
    staged_map = (shadow_repo.module_source_maps or {}).get(module_id) or {}
    for unit_id, dossier in entries:
        unit = live_repo.units.get(unit_id)
        if unit is None or unit.module_id != module_id:
            errors.append(f"material_syntheses: unknown unit for {module_id}: {unit_id}")
            continue
        try:
            expected = synthesis_destination(live_repo.root, unit_id)
        except MaterialSynthesisError as exc:
            errors.append(f"material_syntheses {unit_id}: {exc}")
            continue
        try:
            rel = expected.resolve().relative_to(live_repo.root.resolve())
        except ValueError:
            errors.append(f"material_syntheses {unit_id}: destination escapes repository")
            continue
        if (shadow / rel).suffix != ".yaml":
            errors.append(f"material_syntheses {unit_id}: destination is not a YAML record")
        try:
            validate_unit_material_synthesis(shadow, unit_id, dossier, repo=shadow_repo)
        except MaterialSynthesisError as exc:
            errors.append(f"material_syntheses {unit_id}: replacement dossier invalid: {exc}")
    for unit_id, unit in sorted(live_repo.units.items()):
        if unit.module_id != module_id:
            continue
        try:
            destination = synthesis_destination(live_repo.root, unit_id)
        except MaterialSynthesisError:
            continue
        if not destination.exists():
            continue
        if unit_id in supplied:
            continue
        live_rows = _unit_route_rows(live_map, unit_id)
        staged_rows = _unit_route_rows(staged_map, unit_id)
        added, removed, changed = _evidential_diff(live_rows, staged_rows)
        if not (added or removed or changed):
            continue
        preservable = sorted(set(live_rows) & set(staged_rows) - set(changed))
        needs_review = sorted(set(added) | set(changed))
        errors.append(
            f"material_syntheses: {unit_id} routes change evidentially "
            f"(added={added}, removed={removed}, changed={changed}) but no "
            f"replacement dossier was supplied; assessments reusable unchanged={preservable}, "
            f"requiring fresh review={needs_review}"
        )
    return errors


#: Stage/resource fields that record learner state rather than plan content.
#: A revision that touches them must say so explicitly; silence corrupts
#: progress, notes, attachments, feedback and review attestations.
_LEARNER_STAGE_FIELDS = ("status", "working_note", "attachments",
                         "source_feedback", "runtime_review", "completed")
_LEARNER_RESOURCE_FIELDS = ("independent_evidence",)


def _match_key(resource: dict) -> tuple:
    if isinstance(resource.get("route_id"), str):
        return ("route", resource["route_id"])
    if isinstance(resource.get("source_id"), str):
        return ("source", resource.get("source_id"), resource.get("locator"))
    return ("label", resource.get("label"))


def _stage_by_id(map_data: dict | None) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for stage in (map_data or {}).get("stages", []) or []:
        if isinstance(stage, dict) and isinstance(stage.get("id"), str):
            out.setdefault(stage["id"], stage)
    return out


def _unit_semantic_diff(live_map: dict, staged_map: dict,
                        live_study: dict | None, staged_study: dict | None) -> dict:
    """Reviewable diff for one unit: routes, placements, triage, learner state."""
    unit_id = (staged_study or {}).get("unit_id") or (live_study or {}).get("unit_id") or ""
    live_rows = _unit_route_rows(live_map, unit_id)
    staged_rows = _unit_route_rows(staged_map, unit_id)
    added = sorted(set(staged_rows) - set(live_rows))
    removed = sorted(set(live_rows) - set(staged_rows))
    updated = sorted(rid for rid in set(live_rows) & set(staged_rows)
                     if live_rows[rid] != staged_rows[rid])
    _, _, evidential_changed = _evidential_diff(live_rows, staged_rows)
    demoted = sorted(rid for rid in set(live_rows)
                     if live_rows[rid].get("scope") in {"current", "prerequisite"}
                     and (rid in removed or staged_rows.get(rid, {}).get("scope")
                          not in {"current", "prerequisite"}))
    live_placements = [r for s in _stage_by_id(live_study).values()
                       for r in (s.get("resources", []) or []) if isinstance(r, dict)]
    staged_placements = [r for s in _stage_by_id(staged_study).values()
                         for r in (s.get("resources", []) or []) if isinstance(r, dict)]

    def triage(rows):
        counts: dict[str, int] = {}
        for row in rows:
            counts[row.get("scope_triage", "untriaged")] = \
                counts.get(row.get("scope_triage", "untriaged"), 0) + 1
        return counts

    # A route can appear in several stages. Never collapse those placements:
    # one reference-only placement must not hide another required placement.
    promoted_advanced = sorted(
        rid for rid, row in staged_rows.items()
        if row.get("depth") == "advanced-reference"
        and any(_match_key(p) in {("route", rid),
                                 ("source", row.get("source_id"), row.get("locator"))}
                and p.get("scope_triage") in {"required-now", "helpful-now"}
                for p in staged_placements)
        and (live_rows.get(rid, {}).get("depth") != "advanced-reference"
             or not any(_match_key(p) in {("route", rid),
                                         ("source", row.get("source_id"), row.get("locator"))}
                        and p.get("scope_triage") in {"required-now", "helpful-now"}
                        for p in live_placements)))
    placed_keys = {_match_key(r) for r in staged_placements}
    unplaced = sorted(
        rid for rid, row in staged_rows.items()
        if ("route", rid) not in placed_keys
        and ("source", row.get("source_id"), row.get("locator")) not in placed_keys)
    live_nodes = {n for r in live_rows.values() for n in (r.get("covers", []) or [])}
    staged_nodes = {n for r in staged_rows.values() for n in (r.get("covers", []) or [])}
    uncovered_nodes = sorted(live_nodes - staged_nodes)
    escalated = sorted(
        rid for rid in set(live_rows) & set(staged_rows)
        if live_rows[rid].get("scope") in {"out-of-scope", "prior-year", "optional", "complementary"}
        and staged_rows[rid].get("scope") in {"current", "prerequisite"})
    exact_to_unresolved = sorted(
        rid for rid in set(live_rows) & set(staged_rows)
        if (live_rows[rid].get("locator") or "").strip()
        and not (staged_rows[rid].get("locator") or "").strip())
    live_stages = _stage_by_id(live_study)
    staged_stages = _stage_by_id(staged_study)
    learner_changes: dict[str, list[str]] = {}
    learner_preserved: dict[str, list[str]] = {}
    for sid, old in live_stages.items():
        stage = staged_stages.get(sid, {})
        changed = [f for f in _LEARNER_STAGE_FIELDS if stage.get(f) != old.get(f)]
        kept = [f for f in _LEARNER_STAGE_FIELDS if f not in changed]
        if changed:
            learner_changes[sid] = changed
        if kept:
            learner_preserved[sid] = kept
    resource_learner_changes: list[str] = []
    destructive: list[str] = []
    for sid, old_stage in live_stages.items():
        stage = staged_stages.get(sid)
        if stage is None:
            destructive.append(f"stage {sid} removed (working note and learner state must remain reachable)")
        else:
            for field in ("attachments", "source_feedback"):
                if any(item not in (stage.get(field) or [])
                       for item in old_stage.get(field, []) or []):
                    destructive.append(f"{sid}.{field} loses recorded evidence")
            for field in ("completed", "working_note"):
                if old_stage.get(field) and stage.get(field) != old_stage[field]:
                    destructive.append(f"{sid}.{field} changes recorded evidence")
            if old_stage.get("status") not in {None, "pending"} \
                    and stage.get("status") != old_stage.get("status"):
                destructive.append(f"{sid}.status changes recorded progress")
        remaining = list((stage or {}).get("resources", []) or [])
        for old in old_stage.get("resources", []) or []:
            if not isinstance(old, dict) or not old.get("independent_evidence"):
                continue
            # Preserve each evidence-bearing placement, including duplicates.
            match = next((i for i, r in enumerate(remaining)
                          if isinstance(r, dict) and _match_key(r) == _match_key(old)
                          and r.get("independent_evidence") == old["independent_evidence"]), None)
            if match is None:
                resource_learner_changes.append(f"{sid}:{_match_key(old)}:independent_evidence")
                destructive.append(f"{sid}:{_match_key(old)} loses independent evidence")
            else:
                remaining.pop(match)
    map_state_changes = [f for f in ("status", "current_stage", "detours", "shelving")
                         if live_study and staged_study
                         and live_study.get(f) != staged_study.get(f)]
    for field in ("detours", "shelving"):
        if live_study and live_study.get(field) and field in map_state_changes:
            destructive.append(f"study-map.{field} changes recorded learner state")
    return {
        "unit_id": unit_id,
        "routes_before": len(live_rows),
        "routes_after": len(staged_rows),
        "added": added,
        "updated": updated,
        "removed": removed,
        "evidential_changed": evidential_changed,
        "demoted_current_or_prerequisite": demoted,
        "promoted_advanced_reference": promoted_advanced,
        "scope_escalations": escalated,
        "exact_to_unresolved": exact_to_unresolved,
        "uncovered_knowledge_nodes": uncovered_nodes,
        "placements_before": len(live_placements),
        "placements_after": len(staged_placements),
        "triage_before": triage(live_placements),
        "triage_after": triage(staged_placements),
        "unplaced_routes": unplaced,
        "learner_state_changes": learner_changes,
        "learner_state_preserved": learner_preserved,
        "resource_learner_changes": sorted(resource_learner_changes),
        "map_state_changes": map_state_changes,
        "destructive_learner_changes": destructive,
    }


def _route_changed_units(live_repo, staged_repo, module_id: str) -> set[str]:
    """Units whose routes differ evidentially between two repository states."""
    live_map = (live_repo.module_source_maps or {}).get(module_id) or {}
    staged_map = (staged_repo.module_source_maps or {}).get(module_id) or {}
    unit_ids = {uid for uid, unit in live_repo.units.items()
                if unit.module_id == module_id}
    unit_ids.update(uid for uid, unit in staged_repo.units.items()
                    if unit.module_id == module_id)
    changed: set[str] = set()
    for uid in unit_ids:
        added, removed, evidential = _evidential_diff(
            _unit_route_rows(live_map, uid), _unit_route_rows(staged_map, uid))
        if added or removed or evidential:
            changed.add(uid)
    return changed


def _semantic_ack_problems(module_id: str, live_repo, staged_repo,
                            touched_units: list[str],
                            acknowledgments: list[dict]) -> list[str]:
    """Context-dependent changes that need an explicit documented acknowledgment.

    Hard invariants stay errors elsewhere; these are suspicious-but-legitimate
    shapes (a demotion, a promotion, a reorder of meaning) that review must
    name. Each needs ``acknowledgments[]`` ``{kind, target, reason}``.
    """
    live_map = (live_repo.module_source_maps or {}).get(module_id) or {}
    staged_map = (staged_repo.module_source_maps or {}).get(module_id) or {}
    acked = {(str(a.get("kind")), str(a.get("target")))
             for a in acknowledgments if isinstance(a, dict)}
    missing_reason = {(str(a.get("kind")), str(a.get("target")))
                      for a in acknowledgments
                      if isinstance(a, dict) and not str(a.get("reason", "")).strip()}
    problems: list[str] = []

    def needs(kind: str, target: str, why: str):
        if (kind, target) in acked:
            if (kind, target) in missing_reason:
                problems.append(
                    f"semantic review: acknowledgment {kind} {target} needs a reason")
            return
        problems.append(f"semantic review required ({kind} {target}): {why}; "
                        f"add acknowledgments[] {{kind: {kind}, target: {target}, reason}}")

    live_unit_of = {}
    staged_unit_of = {}
    for source in live_map.get("sources", []) or []:
        for route in source.get("unit_routes", []) or []:
            if isinstance(route, dict) and route.get("id"):
                live_unit_of.setdefault(str(route["id"]), route.get("unit_id"))
    for source in staged_map.get("sources", []) or []:
        for route in source.get("unit_routes", []) or []:
            if isinstance(route, dict) and route.get("id"):
                staged_unit_of.setdefault(str(route["id"]), route.get("unit_id"))
    for rid in sorted(set(live_unit_of) & set(staged_unit_of)):
        if live_unit_of[rid] != staged_unit_of[rid]:
            needs("cross-unit-move", rid,
                  f"route moves from {live_unit_of[rid]} to {staged_unit_of[rid]}")
    scope = set(touched_units) | _route_changed_units(live_repo, staged_repo, module_id)
    for unit_id in sorted(scope):
        live_study = next((sm.data for sm in live_repo.study_maps.values()
                           if sm.unit_id == unit_id), None)
        staged_study = next((sm.data for sm in staged_repo.study_maps.values()
                             if sm.unit_id == unit_id), None)
        diff = _unit_semantic_diff(live_map, staged_map, live_study, staged_study)
        problems.extend(f"learner-state preservation: {unit_id}: {p}"
                        for p in diff["destructive_learner_changes"])
        for rid in diff["demoted_current_or_prerequisite"]:
            needs("demotion", rid, f"{unit_id} demotes a current/prerequisite resource")
        for rid in diff["promoted_advanced_reference"]:
            needs("promotion", rid, f"{unit_id} places advanced-reference as required/helpful")
        for rid in diff["scope_escalations"]:
            needs("scope-escalation", rid, f"{unit_id} escalates peripheral scope to current")
        for rid in diff["exact_to_unresolved"]:
            needs("locator-regression", rid, f"{unit_id} replaces an exact locator with none")
        for node in diff["uncovered_knowledge_nodes"]:
            needs("coverage-loss", node, f"{unit_id} removes the last route covering this node")
        if diff["routes_after"] < diff["routes_before"]:
            needs("coverage-reduction", unit_id,
                  f"menu shrinks {diff['routes_before']} to {diff['routes_after']}")
        if diff["learner_state_changes"] or diff["resource_learner_changes"] \
                or diff["map_state_changes"]:
            needs("learner-state", unit_id, "learner-state fields change")
    return problems


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
            units[uid] = _unit_semantic_diff(live_map, staged_map, live_study, staged_study)
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


def _real_perimeter_errors(root: Path) -> list[str]:
    """Environment errors from the real wrapper tree, in live format.

    Content validation runs in a shadow copy of ``repository/`` alone, where
    the perimeter checker is silent by design (no wrapper anchors exist there).
    The live transaction then validates the real tree and refuses on
    ``PERIMETER-*`` errors — so a preflight that omits this layer passes while
    the application fails. Run this layer against the real root before both
    ``--check`` and live application; synthetic repositories without a
    declaration stay silent, exactly as in live validation.
    """
    from learning_os.contracts import perimeter as _perimeter

    out: list[str] = []
    for issue in _perimeter.check(root):
        if issue.severity != "E":
            continue
        loc = f" [{issue.path}]" if issue.path else ""
        out.append(f"E PERIMETER-{issue.code}: {issue.message}{loc}")
    return out


@contextlib.contextmanager
def _staged_shadow(root: Path, writes: dict[Path, str]):
    """A shadow copy of ``repository/`` carrying planned writes, no canonical I/O.

    Content validation runs here; the real-tree perimeter layer runs against
    ``root`` because the shadow has no wrapper by design.
    """
    ignored_at_root = {
        ".git", ".obsidian", ".pytest_cache", ".venv", "generated",
        "migration", "tests", "tools",
    }

    def ignore_names(directory, names):
        directory = Path(directory).resolve()
        ignored = {"__pycache__"}
        if directory == root.resolve():
            ignored.update(ignored_at_root)
        if directory == (root / "knowledge").resolve():
            ignored.add("attachments")
        if directory == (root / "curriculum").resolve():
            # Prospective planning is a deliberately opened quarantine. A
            # normal module-plan preflight must not copy or inspect it; a
            # promotion supplies only the exact sanitized catalog write it
            # wants the shadow repository to validate.
            ignored.add("quarantine")
        return [name for name in names if name in ignored]

    with tempfile.TemporaryDirectory(prefix="learningos-plan-check-") as tmp:
        shadow = Path(tmp) / "repository"
        shutil.copytree(root, shadow, symlinks=True, ignore=ignore_names)
        attachments = root / "knowledge" / "attachments"
        if attachments.exists():
            link = shadow / "knowledge" / "attachments"
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to(attachments, target_is_directory=True)
        for external_name in ("materials", "projects"):
            external = root.parent / external_name
            if external.exists():
                (shadow.parent / external_name).symlink_to(external, target_is_directory=True)
        for path, content in writes.items():
            try:
                rel = path.resolve().relative_to(root.resolve())
            except ValueError:
                raise ValueError(f"planned write escapes repository: {path}") from None
            _atomic_text(shadow / rel, content)
        yield shadow


def _module_plan_validation_errors(
    root: Path,
    writes: dict[Path, str],
    *,
    module_id: str | None = None,
    syntheses: list[tuple[str, dict]] | None = None,
    touched_units: list[str] | None = None,
    acknowledgments: list[dict] | None = None,
) -> list[str]:
    """Validate planned files in a small shadow repository without canonical writes.

    The gate is the repository's one warning policy (CLAUDE.md hard rule 9,
    `learning_os.warning_baseline`): zero errors, and no warning signature that
    is new or grown relative to the recorded baseline. Until 2026-08-29 this
    function instead failed on every non-exempt warning anywhere in the shadow
    repository, which made it unsatisfiable — the baselined content debt of
    CRITIQUE-POINTS §1 lives in the source maps, so `module-plan-import` for one
    module failed on another module's deferred locators. A plan must still be
    refused when it *introduces* a warning; that is what the delta measures.

    The first layer is the real-tree perimeter: the shadow has no wrapper, so
    content validation there can never see an undeclared sibling. The live
    transaction refuses on it, so the preflight must too, with the identical
    string, before any canonical write begins.
    """
    perimeter_errors = _real_perimeter_errors(root)
    with _staged_shadow(root, writes) as shadow:
        signatures, errors = signatures_from_issues(
            validate(load_repo(shadow), online=False))
        synthesis_errors: list[str] = []
        ack_errors: list[str] = []
        if module_id is not None and syntheses is not None:
            live_repo = load_repo(root)
            staged_repo = load_repo(shadow)
            try:
                synthesis_errors = _staged_synthesis_errors(
                    root, module_id, live_repo, shadow, staged_repo, syntheses)
            except MaterialSynthesisError as exc:
                synthesis_errors = [f"material_syntheses: staged state unreadable: {exc}"]
            if touched_units is not None and acknowledgments is not None:
                ack_errors = _semantic_ack_problems(
                    module_id, live_repo, staged_repo,
                    touched_units, acknowledgments)
        errors = synthesis_errors + ack_errors + errors
    # The baseline is read from the real repository: the shadow is a copy of it
    # plus the planned writes, so the baseline describes exactly the "before".
    baseline, _ = load_baseline(root)
    regressions, _repairs = delta(baseline, signatures)
    return perimeter_errors + errors + [
        f"W NEW-OR-GROWN-WARNING: {line} (introduced by this plan; fix it, or "
        "adopt it deliberately with `python tools/warning_baseline.py --update`)"
        for line in regressions
    ]


def _master_promotion_preflight(
    root: Path,
    module_id: str,
    plan: MasterPromotionPlan,
    package: dict,
) -> list[str]:
    problems = _module_plan_contract_problems(root, package)
    if problems:
        return [f"contract: {problem}" for problem in problems]
    repo = load_repo(root)
    problems = _module_plan_routing_problems(repo, module_id, package)
    if problems:
        return [f"routing: {problem}" for problem in problems]
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
            return 3
        code, errors, confirmation = _write_transaction(
            root,
            plan.writes,
            capability="module.plan.import",
            expected_revisions=expected_revisions,
            artifact_ids=plan.artifact_ids,
        )
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


def cmd_module_plan_import(args) -> int:
    """Apply one reviewable, module-scoped curriculum plan as a transaction.

    This gateway exists for the structural part of WORKFLOWS §23: a lecture
    batch may add units, their current study maps, module source routing, and
    explicit workspace joins together. It never deletes units or creates
    durable notes, and every stage remains bounded to the requested module.
    """
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
            print(f"los: module not found: {args.module_id}", file=sys.stderr)
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
        if not args.check and changed_claims:
            try:
                writes[root / LEDGER_RELATIVE] = _phaseB_ledger_text(
                    root, repo, args.module_id, package,
                    changed_claims, claim_evidence, live_routes,
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
            from learning_os.commands.capability import prepare_review_envelope

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
            } | ({LEDGER_RELATIVE} if changed_claims else set()))
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
        else:
            if getattr(args, "_minimal_writes", False):
                artifact_ids = _minimal_artifact_ids(
                    root, args.module_id, writes, synthesis_entries)
            else:
                artifact_ids = [args.module_id, *sorted(seen_units), *synthesis_ids]
            code, errors, confirmation = _write_transaction(
                root, writes,
                capability=getattr(args, "_capability_override", None)
                or "module.plan.import",
                expected_revisions=_expected_revisions_from_args(args),
                artifact_ids=artifact_ids,
            )
            if code:  # Defensive: prevalidated transactions do not normally reach this branch.
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
                problems.append(f"route_changes.{kind} has unknown fields")
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
        print(f"los: unit not found: {args.unit_id}", file=sys.stderr)
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
                expected_snapshot=expected_snapshot,
                expected_revision=list(getattr(args, "expected_revision", []) or []),
                _parser_factory=getattr(args, "_parser_factory", None),
                _capability_override="unit.plan.revise",
                _minimal_writes=True,
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
