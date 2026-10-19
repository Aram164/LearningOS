"""Plan-area handlers (PLAN D4): material plans, revisions, and reads."""

from __future__ import annotations

import contextlib
import copy
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

import yaml

from learning_os.app._plan_gate import coverage_audit_problems as _coverage_audit_problems
from learning_os.app._plan_gate import enumerate_inventory_roots as _enumerate_inventory_roots
from learning_os.app._plan_gate import inventory_row_problems as _inventory_row_problems
from learning_os.app._plan_gate import (
    master_promotion_check_result as _master_promotion_check_result,
)
from learning_os.app._plan_gate import master_promotion_preflight as _master_promotion_preflight
from learning_os.app._plan_gate import module_plan_check_report as _module_plan_check_report
from learning_os.app._plan_gate import (
    module_plan_contract_problems as _module_plan_contract_problems,
)
from learning_os.app._plan_gate import (
    module_plan_validation_errors as _module_plan_validation_errors,
)
from learning_os.app._plan_gate import plan_apply_gate as _plan_apply_gate
from learning_os.app.admin.masters_planning import prepare_master_promotion
from learning_os.app.check import staged_shadow as _staged_shadow
from learning_os.app.claim_admission import anchor_report, lineage_artifacts
from learning_os.app.claim_admission import prepare_claim_admission as _phaseB_validate
from learning_os.app.claim_admission import render_claim_lineage as _phaseB_ledger_text
from learning_os.app.context import OpContext
from learning_os.app.gateway import prepare_review_envelope
from learning_os.app.gateway import read_content_bound_file as _read_content_bound_file
from learning_os.app.handlers._shared import apply_reviewed_envelope
from learning_os.app.proposal import ResponsePayload, Result, TransactionProposal
from learning_os.app.registry import register
from learning_os.derive.masters_catalog import MastersPlanningError
from learning_os.derive.material_synthesis import (
    MaterialSynthesisError,
    current_unit_material_basis,
    synthesis_destination,
)
from learning_os.derive.semantics.lineage import (
    LEDGER_RELATIVE,
    LineageError,
)
from learning_os.domain.failures import NotFound, RevisionConflict, WriteRefused
from learning_os.domain.plan_import import ack_shape_problems as _ack_shape_problems
from learning_os.domain.plan_import import apply_unit_route_changes as _apply_unit_route_changes
from learning_os.domain.plan_import import (
    assemble_compact_module_revision as _assemble_compact_module_revision,
)
from learning_os.domain.plan_import import inventory_block as _inventory_block
from learning_os.domain.plan_import import inventory_view as _inventory_view
from learning_os.domain.plan_import import minimal_artifact_ids as _minimal_artifact_ids
from learning_os.domain.plan_import import (
    module_plan_ordering_problems as _module_plan_ordering_problems,
)
from learning_os.domain.plan_import import (
    module_plan_routing_problems as _module_plan_routing_problems,
)
from learning_os.domain.plan_import import synthesis_entries as _synthesis_entries
from learning_os.domain.render import replace_h2_section as _replace_h2_section
from learning_os.domain.suggest import not_found
from learning_os.store.codec import dump_study_map as _dump_study_map
from learning_os.store.codec import dump_yaml as _dump_yaml
from learning_os.store.codec import render_frontmatter as _render_frontmatter
from learning_os.store.contracts import current_template_problems
from learning_os.store.contracts.gateway import current_gateway_request
from learning_os.store.revisions import load_revisions
from learning_os.store.transactions import parse_expected_revisions

# -------------------- module.plan.import / unit.plan.revise (PLAN 4.1,
# Task 82). Pure construction lives in learning_os/domain/plan_import.py;
# these helpers (repository reads, gateway context, report presentation)
# moved verbatim from commands/module.py; the handlers convert the three
# entries by SPEC 12 (R1 promotion/compact branches, R4 shared tail).


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

def _replace_registry_list_record(content: str, record_id: str, record: dict) -> str:
    """Render one record in a top-level YAML list without reformatting siblings."""
    lines = content.splitlines(keepends=True)
    id_line = next((i for i, line in enumerate(lines)
                    if re.match(rf"^[ ]*(?:- )?id: {re.escape(record_id)}[ ]*$",
                                line.rstrip("\r\n"))), None)
    if id_line is None:
        raise ValueError(f"registry record not found in source text: {record_id}")
    id_indent = len(lines[id_line]) - len(lines[id_line].lstrip(" "))
    if lines[id_line].lstrip(" ").startswith("- id:"):
        start = id_line
        item_indent = " " * id_indent
    else:
        item_indent = " " * max(0, id_indent - 2)
        start = next((i for i in range(id_line, -1, -1)
                      if lines[i].startswith(item_indent + "- ")), None)
        if start is None:
            raise ValueError(f"registry list item not found for: {record_id}")
    end = next((i for i in range(start + 1, len(lines))
                if lines[i].startswith(item_indent + "- ")), len(lines))
    rendered = _dump_yaml(record).rstrip().splitlines()
    replacement = item_indent + "- " + rendered[0] + "\n"
    replacement += "\n".join(item_indent + "  " + line if line else ""
                              for line in rendered[1:])
    replacement += "\n\n"
    return "".join(lines[:start]) + replacement + "".join(lines[end:]).lstrip("\n")


def _plan_refuse(ctx, message, slug, *, exit_code=2, extra=(), cls=WriteRefused):
    extra = tuple(extra)
    gateway = f"los: {message}" + "".join(f"\n{line}" for line in extra)
    raise cls(
        message,
        site=f"{ctx.operation}.{slug}",
        extra_stderr=extra,
        gateway_message=gateway,
        exit_code=exit_code,
    )


def _master_promotion_import(ctx: OpContext, req: dict) -> Result:
    root = ctx.root
    value = req.get("promotion")
    if not isinstance(value, dict) or value.get("canonical_module_id") != req.get("module_id"):
        _plan_refuse(
            ctx,
            "promotion must be an inline object whose canonical_module_id "
            "matches the requested module",
            "promotion-mismatch",
        )
    if not req.get("check"):
        request = current_gateway_request()
        if request is None or request.capability != "module.plan.import":
            _plan_refuse(
                ctx,
                "live Master Planning promotion requires an approved "
                "GatewayEnvelopeV2; run --check directly for a no-write dry run",
                "promotion-needs-gateway",
            )
        if not req.get("approve"):
            _plan_refuse(
                ctx, "Master Planning promotion requires exact gateway approval",
                "promotion-needs-approval",
            )
        if not req.get("expected_snapshot"):
            _plan_refuse(
                ctx, "Master Planning promotion requires expected_snapshot",
                "promotion-needs-snapshot",
            )
    try:
        plan = prepare_master_promotion(root, value)
    except MastersPlanningError as exc:
        _plan_refuse(ctx, f"Master Planning promotion refused: {exc}",
                     "promotion-refused")
    supplied_hash = req.get("package_sha256")
    if supplied_hash is not None and supplied_hash != plan.package_sha256:
        detail = json.dumps(
            {"expected": plan.package_sha256, "supplied": supplied_hash},
            ensure_ascii=False)
        _plan_refuse(
            ctx,
            "promotion package hash does not match the exact checked content",
            "promotion-hash-mismatch",
            exit_code=3,
            extra=(detail,),
            cls=RevisionConflict,
        )
    if not req.get("check") and supplied_hash is None:
        _plan_refuse(
            ctx,
            "live promotion requires the exact package_sha256 returned by --check",
            "promotion-needs-hash",
        )
    problems = _master_promotion_preflight(
        root,
        req["module_id"],
        plan,
        value["module_plan"],
        skip_validation=not req.get("check")
        and current_gateway_request() is not None,
    )
    if problems:
        _plan_refuse(
            ctx,
            "Master Planning promotion preflight failed; no canonical "
            "files were written",
            "promotion-preflight-failed",
            exit_code=1,
            extra=tuple(f"- {problem}" for problem in problems[:12]),
        )
    if req.get("check"):
        return Result(
            _master_promotion_check_result(root, req["module_id"], plan),

        )
    ctx.require_snapshot(req.get("expected_snapshot"))
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc),
            site=f"{ctx.operation}.bad-expected-revision",
            prefixed=True,
            exit_code=2,
        ) from exc
    if expected_revisions != plan.expected_revisions:
        detail = json.dumps(
            {"expected": plan.expected_revisions,
             "supplied": expected_revisions},
            ensure_ascii=False)
        _plan_refuse(
            ctx,
            "promotion expected revisions must match the complete checked "
            "bundle; reload and run --check again",
            "promotion-revisions-mismatch",
            exit_code=3,
            extra=(detail,),
            cls=RevisionConflict,
        )
    validate_extra, gate_errors = _plan_apply_gate(root)

    refusal = (gate_errors, WriteRefused('Master Planning promotion preflight failed; no canonical files were written',
        site=f"{ctx.operation}.promotion-preflight-failed", prefixed=True, exit_code=1))

    def finish_promotion(confirmation):
        return {
            "ok": True,
            "mode": "apply",
            "module_id": req["module_id"],
            "candidate_module_id": plan.provenance["candidate_module_id"],
            "promotion_id": plan.provenance["id"],
            "package_sha256": plan.package_sha256,
            "files_written": len(plan.writes),
            **confirmation,
        }

    def refused_promotion(errors):
        return ["los: Master Planning promotion failed", *errors[:12]]

    return Result(
        ResponsePayload({"ok": True}, finish_promotion({}), confirmation='merge'),
        proposal=TransactionProposal(refusal=refusal,
            capability="module.plan.import",
            writes=plan.writes,
            artifact_ids=plan.artifact_ids,
            expected_revisions=expected_revisions,
            validate_extra=validate_extra,
        ),




    )


def _execute_plan_import(ctx, req, *, module_id, source, package_bytes,
                         package, minimal_writes=False, review_input=None,
                         capability_override=None, report_out=None,
                         report_out_draft=None) -> Result:
    root = ctx.root
    package_sha = f"sha256:{hashlib.sha256(package_bytes).hexdigest()}"
    synthesis_entries, _ = _synthesis_entries(module_id, package)
    acknowledgments = package.get("acknowledgments", []) or []
    if not isinstance(acknowledgments, list):
        acknowledgments = []
    ctx.require_snapshot(req.get("expected_snapshot"))
    repo = ctx.repo()
    module = repo.modules.get(module_id)
    if module is None:
        message = not_found("module", module_id, repo.modules)
        raise NotFound(
            "module", module_id, repo.modules,
            message=message,
            site=f"{ctx.operation}.unknown-module",
            gateway_message=f"los: {message}",
            exit_code=2,
        )
    module_path = repo.module_origins[module_id]
    writes: dict[Path, str] = {}

    module_patch = package.get("module_patch", {}) or {}
    if not isinstance(module_patch, dict) or module_patch.get("id", module_id) != module_id:
        _plan_refuse(ctx, "module_patch must stay inside the requested module",
                     "module-patch-escape")
    module_data = copy.deepcopy(module)
    module_data.update(module_patch)
    module_data["id"] = module_id
    writes[module_path] = _dump_yaml(module_data)

    source_map = package.get("source_map")
    if source_map is not None:
        if not isinstance(source_map, dict) or source_map.get("module_id") != module_id:
            _plan_refuse(ctx, "source_map must belong to the requested module",
                         "source-map-foreign")
        target = repo.module_source_map_origins.get(
            module_id, module_path.parent / "source-map.yaml")
        writes[target] = _dump_yaml(source_map)

    source_patches = package.get("source_patches", []) or []
    if not isinstance(source_patches, list):
        _plan_refuse(ctx, "source_patches must be a list", "source-patches-nonlist")
    registry_texts: dict[Path, str] = {}
    patched_source_ids: set[str] = set()
    for patch in source_patches:
        sid = patch.get("id") if isinstance(patch, dict) else None
        if not sid or sid not in repo.sources or sid in patched_source_ids:
            _plan_refuse(ctx, f"source patch targets an unknown source: {sid}",
                         "source-patch-unknown")
        patched_source_ids.add(sid)
        origin = repo.source_origins[sid]
        record = copy.deepcopy(repo.sources[sid])
        record.update(copy.deepcopy(patch))
        content = registry_texts.get(origin, origin.read_text(encoding="utf-8"))
        try:
            registry_texts[origin] = _replace_registry_list_record(content, sid, record)
        except ValueError as exc:
            _plan_refuse(ctx, str(exc), "source-patch-splice")
    writes.update(registry_texts)

    units = package.get("units", []) or []
    if not isinstance(units, list):
        _plan_refuse(ctx, "units must be a list", "units-nonlist")
    seen_units: set[str] = set()
    for entry in units:
        unit_data = entry.get("unit") if isinstance(entry, dict) else None
        map_data = entry.get("study_map") if isinstance(entry, dict) else None
        uid = unit_data.get("id") if isinstance(unit_data, dict) else None
        if not uid or uid in seen_units or unit_data.get("module_id") != module_id:
            _plan_refuse(ctx, f"invalid or duplicate module unit: {uid}",
                         "unit-invalid")
        seen_units.add(uid)
        unit_dir = module_path.parent / "units" / uid
        writes[unit_dir / "unit.yaml"] = _dump_yaml(unit_data)
        if map_data is None:
            continue
        if not isinstance(map_data, dict) or map_data.get("unit_id") != uid:
            _plan_refuse(ctx, f"study map must belong to {uid}", "map-foreign-unit")
        existing_map = next((sm for sm in repo.study_maps.values() if sm.unit_id == uid), None)
        writes[unit_dir / "study-map.yaml"] = (
            _dump_study_map(existing_map, map_data) if existing_map else _dump_yaml(map_data)
        )
        prefix = f"curriculum/modules/{module_id}/units/{uid}/stages/"
        for stage in map_data.get("stages", []) or []:
            note_ref = stage.get("working_note") if isinstance(stage, dict) else None
            if not isinstance(note_ref, str) or not note_ref.startswith(prefix) \
                    or not note_ref.endswith("/notes.md"):
                _plan_refuse(ctx, f"stage note escapes module/unit scope: {note_ref}",
                             "stage-note-escape")
            note = root / note_ref
            if not note.exists():
                writes[note] = ""

    synthesis_ids: list[str] = []
    for unit_id, dossier in synthesis_entries:
        unit = repo.units.get(unit_id)
        if unit is None or unit.module_id != module_id:
            _plan_refuse(ctx, f"synthesis replacement targets an unknown unit: {unit_id}",
                         "synthesis-unknown-unit")
        try:
            destination = synthesis_destination(root, unit_id)
        except MaterialSynthesisError as exc:
            _plan_refuse(ctx, str(exc), "synthesis-destination")
        writes[destination] = _dump_yaml(dossier)
        if isinstance(dossier.get("id"), str):
            synthesis_ids.append(dossier["id"])

    workspace_updates = package.get("workspace_updates", []) or []
    if not isinstance(workspace_updates, list):
        _plan_refuse(ctx, "workspace_updates must be a list",
                     "workspace-updates-nonlist")
    for update in workspace_updates:
        wid = update.get("id") if isinstance(update, dict) else None
        workspace = repo.workspaces.get(wid)
        if workspace is None or workspace.archived or module_id not in workspace.meta.get("module_ids", []):
            _plan_refuse(ctx, f"workspace update is not joined to {module_id}: {wid}",
                         "workspace-not-joined")
        meta = copy.deepcopy(workspace.meta)
        for key in ("sources", "unit_ids"):
            if key in update:
                meta[key] = copy.deepcopy(update[key])
        body = workspace.body
        try:
            for heading, content in (update.get("sections", {}) or {}).items():
                body = _replace_h2_section(body, str(heading), str(content))
        except ValueError as exc:
            _plan_refuse(ctx, str(exc), "workspace-splice")
        writes[workspace.path] = _render_frontmatter(meta, body)

    ordering_problems = _module_plan_ordering_problems(repo, module_id, package)
    if ordering_problems:
        _plan_refuse(
            ctx,
            "module plan ordering preflight failed; no canonical files were written",
            "ordering-preflight-failed",
            exit_code=1,
            extra=tuple(f"- {problem}" for problem in ordering_problems),
        )
    routing_problems = _module_plan_routing_problems(repo, module_id, package)
    if routing_problems:
        _plan_refuse(
            ctx,
            "module plan routing preflight failed; no canonical files were written",
            "routing-preflight-failed",
            exit_code=1,
            extra=tuple(f"- {problem}" for problem in routing_problems),
        )
    lineage_problems, changed_claims, claim_evidence, live_routes = _phaseB_validate(
        root, repo, module_id, package,
        unit_scope=req.get("unit_id") if capability_override == "unit.plan.revise" else None)
    if lineage_problems:
        _plan_refuse(
            ctx,
            "module plan lineage preflight failed; no canonical files were written",
            "lineage-preflight-failed",
            exit_code=1,
            extra=tuple(f"- {problem}" for problem in lineage_problems),
        )
    lineage_will_change = bool(changed_claims) or any(
        synthesis_destination(root, uid) in _drop_unchanged_writes(writes)
        for uid, _ in synthesis_entries)
    if not req.get("check") and lineage_will_change:
        try:
            writes[root / LEDGER_RELATIVE] = _phaseB_ledger_text(
                root, repo, module_id, package,
                changed_claims, claim_evidence, live_routes,
                synthesis_entries=synthesis_entries,
                incremented_artifacts=_minimal_artifact_ids(
                    root, module_id, _drop_unchanged_writes(writes), synthesis_entries)
                if minimal_writes else None)
        except LineageError as exc:
            _plan_refuse(
                ctx,
                "module plan lineage admission failed; no canonical files were written",
                "lineage-admission-failed",
                extra=(f"- {exc}",),
            )
    if minimal_writes:
        writes = _drop_unchanged_writes(writes)
        if not writes and not req.get("check"):
            _plan_refuse(ctx, "revision changes no canonical bytes; nothing to apply",
                         "noop-revision")
    basis_unit = req.get("staged_basis")
    if basis_unit:
        if basis_unit not in seen_units:
            _plan_refuse(ctx, f"staged basis unit is not in this package: {basis_unit}",
                         "staged-outside-package")
        try:
            with _staged_shadow(root, writes) as shadow:
                basis = current_unit_material_basis(shadow, basis_unit)
        except (MaterialSynthesisError, OSError, ValueError) as exc:
            _plan_refuse(ctx, f"staged basis unavailable: {exc}",
                         "staged-unavailable")
        return Result(
            {"unit_id": basis_unit, "basis": basis,
             "package_sha256": package_sha, "validated": False},

        )
    if req.get("check") or current_gateway_request() is None:
        try:
            errors = _module_plan_validation_errors(
                root, writes,
                module_id=module_id,
                syntheses=synthesis_entries,
                touched_units=sorted(seen_units),
                acknowledgments=acknowledgments,
            )
        except ValueError as exc:
            _plan_refuse(ctx, str(exc), "validation-crash")
        if errors:
            _plan_refuse(
                ctx,
                "module plan validation preflight failed; no canonical files were written",
                "validation-preflight-failed",
                exit_code=1,
                extra=tuple(str(issue) for issue in errors[:12]),
            )
    if req.get("check"):
        result = _module_plan_check_report(
            root, module_id, package, writes,
            synthesis_entries, package_sha, seen_units)
        result["units_checked"] = sorted(seen_units)
        result["files_checked"] = len(writes) + int(lineage_will_change)
        capability = capability_override or "module.plan.import"
        reviewed_sha = review_input[0] if review_input else package_sha
        payload = review_input[1] if review_input else {
            "module_id": module_id, "file": str(source), "file_sha256": package_sha}
        owners = result["commit_artifact_ids"] if minimal_writes \
            else [module_id, *sorted(seen_units), *synthesis_ids]
        owners = lineage_artifacts(owners, lineage_will_change)
        result["expected_revisions"] = {aid: load_revisions(root).get(aid, 0) for aid in owners}
        result["commit_artifact_ids"] = owners
        result["reviewed_file_sha256"] = reviewed_sha
        result["assembled_package_sha256"] = package_sha
        result["capability"] = capability
        result["changes"] = "present" if writes or lineage_will_change else "none"
        result["expected_write_paths"] = sorted({
            str(p.relative_to(root)) for p in writes
        } | ({LEDGER_RELATIVE} if lineage_will_change else set()))
        result["claim_anchors"] = anchor_report(claim_evidence)
        result["expected_write_sha256"] = {
            str(p.relative_to(root)): hashlib.sha256(content.encode("utf-8")).hexdigest()
            for p, content in writes.items()}
        result["gateway_envelope"] = prepare_review_envelope(
            capability, payload, result["expected_snapshot"], result["expected_revisions"])
        fragment, inventory_problems = _observed_material_binding(
            root, package.get("plan_contract") or {})
        if inventory_problems:
            _plan_refuse(
                ctx,
                "module plan inventory preflight failed; "
                "no canonical files were written",
                "inventory-preflight-failed",
                exit_code=1,
                extra=tuple(f"- {problem}" for problem in inventory_problems),
            )
        if fragment is not None:
            result.update(fragment)
        effective_report_out = report_out if report_out is not None else req.get("report_out")
        if effective_report_out:
            compact, failure = _save_check_report_and_compact(
                root, result, effective_report_out,
                draft=report_out_draft)
            if failure is not None:
                code, message = failure
                _plan_refuse(
                    ctx, f"{message}; no canonical files were written",
                    "report-out-failed",
                    exit_code=code,
                )
            result = compact
        return Result(result)
    if minimal_writes:
        artifact_ids = _minimal_artifact_ids(
            root, module_id, writes, synthesis_entries)
    else:
        artifact_ids = [module_id, *sorted(seen_units), *synthesis_ids]
    artifact_ids = lineage_artifacts(artifact_ids, lineage_will_change)
    validate_extra, gate_errors = _plan_apply_gate(
        root, live_repo=repo, module_id=module_id,
        syntheses=synthesis_entries,
        touched_units=sorted(seen_units),
        acknowledgments=acknowledgments)
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc),
            site=f"{ctx.operation}.bad-expected-revision",
            prefixed=True,
            exit_code=2,
        ) from exc

    refusal = (gate_errors, WriteRefused('module plan validation preflight failed; no canonical files were written',
        site=f"{ctx.operation}.validation-preflight-failed", prefixed=True, exit_code=1))

    def finish_plan_import(confirmation):
        return {"ok": True, "mode": "apply", "module_id": module_id,
                "units_written": sorted(seen_units), "files_written": len(writes),
                **confirmation}

    def refused_plan_import(errors):
        return ["los: module plan import failed", *errors[:12]]

    return Result(
        ResponsePayload({"ok": True}, finish_plan_import({}), confirmation='merge'),
        proposal=TransactionProposal(refusal=refusal,
            capability=capability_override or "module.plan.import",
            writes=writes,
            artifact_ids=artifact_ids,
            expected_revisions=expected_revisions,
            validate_extra=validate_extra,
        ),




    )


def _compact_plan_import(ctx, req, root, source, revision_bytes, revision) -> Result:
    apply_sha = req.get("apply_reviewed_sha256")
    if apply_sha:
        if req.get("check"):
            _plan_refuse(ctx, "--check and --apply-reviewed-sha256 are mutually exclusive",
                         "check-and-reviewed")
        stale_material = _verify_observed_material(
            root, revision.get("plan_contract") or {}, req.get("review_report"))
        if stale_material:
            _plan_refuse(ctx, stale_material, "stale-reviewed-apply")
        return Result(
            apply_reviewed_envelope(ctx, capability_name='module.plan.import', payload={'module_id': req['module_id'], 'file': str(source), 'file_sha256': apply_sha}, reviewed_content=revision_bytes, reviewed_sha256=apply_sha, review_report=req.get('review_report')),

        )
    repo = ctx.repo()
    package, problems = _assemble_compact_module_revision(
        repo, req["module_id"], revision)
    if problems:
        _plan_refuse(
            ctx,
            "compact module revision failed; no canonical files were written",
            "compact-assembly-failed",
            extra=tuple(f"- {problem}" for problem in problems),
        )
    assembled = _dump_yaml(package).encode("utf-8")
    reviewed_sha = f"sha256:{hashlib.sha256(revision_bytes).hexdigest()}"
    assembled_package = yaml.safe_load(assembled.decode("utf-8"))
    assembled_contract_problems = _module_plan_contract_problems(
        root, assembled_package)
    if assembled_contract_problems:
        _plan_refuse(
            ctx,
            "module plan contract failed; no canonical files were written",
            "assembled-contract-failed",
            extra=tuple(f"- {problem}" for problem in assembled_contract_problems),
        )
    return _execute_plan_import(
        ctx, req,
        module_id=req["module_id"],
        source=source,
        package_bytes=assembled,
        package=assembled_package,
        minimal_writes=True,
        review_input=(reviewed_sha,
                      {"module_id": req["module_id"], "file": str(source),
                       "file_sha256": reviewed_sha}),
    )


@register("module.plan.import", kind="command")
def module_plan_import(ctx: OpContext, req: dict) -> Result:
    """Apply one reviewable, module-scoped curriculum plan as a transaction.

    This gateway exists for the structural part of WORKFLOWS §23: a lecture
    batch may add units, their current study maps, module source routing, and
    explicit workspace joins together. It never deletes units or creates
    durable notes, and every stage remains bounded to the requested module.
    """
    if req.get("staged_basis") and not req.get("check"):
        _plan_refuse(ctx, "--staged-basis requires --check", "staged-basis-needs-check")
    if req.get("promotion") is not None:
        return _master_promotion_import(ctx, req)
    root = ctx.root
    try:
        _source, package_bytes = _read_content_bound_file(
            req.get("file"),
            req.get("file_sha256"),
            label="module plan file",
        )
    except WriteRefused as exc:
        exc.site = f"{ctx.operation}.bad-file"
        exc.gateway_message = f"los: {exc}"
        exc.exit_code = 2
        raise
    try:
        package = yaml.safe_load(package_bytes.decode("utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        _plan_refuse(ctx, f"invalid module-plan YAML: {exc}", "bad-yaml")
    if not isinstance(package, dict) or package.get("module_id") != req.get("module_id"):
        _plan_refuse(
            ctx, "module plan must be a mapping with the requested module_id",
            "wrong-module",
        )
    if "unit_revisions" in package:
        return _compact_plan_import(ctx, req, root, _source, package_bytes, package)
    contract_problems = _module_plan_contract_problems(root, package)
    if contract_problems:
        _plan_refuse(
            ctx,
            "module plan contract failed; no canonical files were written",
            "contract-failed",
            extra=tuple(f"- {problem}" for problem in contract_problems),
        )
    apply_sha = req.get("apply_reviewed_sha256")
    if apply_sha and req.get("check"):
        _plan_refuse(ctx, "--check and --apply-reviewed-sha256 are mutually exclusive",
                     "check-and-reviewed")
    if apply_sha:
        if not req.get("file"):
            _plan_refuse(ctx, "--apply-reviewed-sha256 applies a --file plan package",
                         "reviewed-needs-file")
        stale_material = _verify_observed_material(
            root, package.get("plan_contract") or {}, req.get("review_report"))
        if stale_material:
            _plan_refuse(ctx, stale_material, "stale-reviewed-apply")
        return Result(
            apply_reviewed_envelope(ctx, capability_name='module.plan.import', payload={'module_id': req['module_id'], 'file': str(_source), 'file_sha256': apply_sha}, reviewed_content=package_bytes, reviewed_sha256=apply_sha, review_report=req.get('review_report')),

        )
    if not req.get("check") and not req.get("expected_snapshot") \
            and not req.get("apply_reviewed_sha256"):
        _plan_refuse(
            ctx,
            "module plan import requires --expected-snapshot; run --check first, "
            "then copy snapshot.snapshot_id from bootstrap",
            "needs-snapshot",
        )
    return _execute_plan_import(
        ctx, req,
        module_id=req["module_id"],
        source=_source,
        package_bytes=package_bytes,
        package=package,
    )


@register("unit.plan.revise", kind="command")
def unit_plan_revise(ctx: OpContext, req: dict) -> Result:
    """Revise one existing lecture: compact patch in, one governed transaction out.

    The compact revision names only what changes — route ops, the reviewed
    final study map, and an optional replacement dossier. Unrelated source-map
    routes are carried forward internally, and the assembled full package runs
    the same validation, receipt and rollback path as `module.plan.import`,
    with artifact IDs for exactly the semantic owners the revision touches.
    """
    root = ctx.root
    revision = req.get("record")
    revision_bytes = b""
    if revision is None:
        if not req.get("file"):
            _plan_refuse(ctx, "unit-plan-revise needs --file or --record",
                         "needs-file-or-record")
        try:
            _source, revision_bytes = _read_content_bound_file(
                req.get("file"),
                req.get("file_sha256"),
                label="unit revision file",
            )
        except WriteRefused as exc:
            exc.site = f"{ctx.operation}.bad-file"
            exc.gateway_message = f"los: {exc}"
            exc.exit_code = 2
            raise
        try:
            revision = yaml.safe_load(revision_bytes.decode("utf-8"))
        except (UnicodeDecodeError, yaml.YAMLError) as exc:
            _plan_refuse(ctx, f"invalid unit-revision YAML: {exc}", "bad-yaml")
    contract_problems = _unit_revision_contract_problems(
        root, req["unit_id"], revision)
    if contract_problems:
        _plan_refuse(
            ctx,
            "unit revision contract failed; no canonical files were written",
            "contract-failed",
            extra=tuple(f"- {problem}" for problem in contract_problems),
        )
    report_out = req.get("report_out")
    if report_out:
        if req.get("apply_reviewed_sha256"):
            _plan_refuse(
                ctx,
                "--report-out is only for --check; it cannot be combined with reviewed apply",
                "report-out-with-reviewed",
            )
        if req.get("staged_basis"):
            _plan_refuse(
                ctx,
                "--report-out is only for ordinary final --check; it cannot be combined with --staged-basis",
                "report-out-with-staged",
            )
        if not req.get("check"):
            _plan_refuse(
                ctx,
                "--report-out needs --check; run the ordinary final preflight first",
                "report-out-needs-check",
            )
        target_problem = _report_out_target_problem(
            root, report_out, draft=req.get("file"))
        if target_problem:
            _plan_refuse(ctx, target_problem, "report-out-target")
    apply_flag = req.get("apply_reviewed_sha256")
    if apply_flag:
        if req.get("check") or req.get("record") is not None:
            _plan_refuse(
                ctx,
                "reviewed apply needs --file and cannot use --check or --record",
                "reviewed-needs-file",
            )
        stale_material = _verify_observed_material(
            root, revision.get("plan_contract") or {}, req.get("review_report"))
        if stale_material:
            _plan_refuse(ctx, stale_material, "stale-reviewed-apply")
        return Result(
            apply_reviewed_envelope(ctx, capability_name='unit.plan.revise', payload={'unit_id': req['unit_id'], 'record': revision}, reviewed_content=revision_bytes, reviewed_sha256=apply_flag, review_report=req.get('review_report')),

        )
    if not req.get("check") and not req.get("expected_snapshot") and not apply_flag:
        _plan_refuse(
            ctx,
            "unit plan revise requires --expected-snapshot; run --check first, "
            "then copy the expected_snapshot from the check report",
            "needs-snapshot",
        )
    repo = ctx.repo()
    unit = repo.units.get(req["unit_id"])
    if unit is None:
        message = not_found("unit", req["unit_id"], repo.units)
        raise NotFound(
            "unit", req["unit_id"], repo.units,
            message=message,
            site=f"{ctx.operation}.unknown-unit",
            gateway_message=f"los: {message}",
            exit_code=2,
        )
    module_id = unit.module_id
    live_map = copy.deepcopy(repo.module_source_maps.get(module_id) or {})
    changes = revision.get("route_changes", {}) or {}
    new_map, _route_summary, route_problems = _apply_unit_route_changes(
        live_map, module_id, req["unit_id"], changes)
    if route_problems:
        _plan_refuse(
            ctx,
            "unit revision route changes failed; no canonical files were written",
            "route-changes-failed",
            extra=tuple(f"- {problem}" for problem in route_problems),
        )
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
            {"unit_id": req["unit_id"], "dossier": dossier}]
    package_bytes = _dump_yaml(package).encode("utf-8")
    assembled_package = yaml.safe_load(package_bytes.decode("utf-8"))
    assembled_contract_problems = _module_plan_contract_problems(
        root, assembled_package)
    if assembled_contract_problems:
        _plan_refuse(
            ctx,
            "module plan contract failed; no canonical files were written",
            "assembled-contract-failed",
            extra=tuple(f"- {problem}" for problem in assembled_contract_problems),
        )
    return _execute_plan_import(
        ctx, req,
        module_id=module_id,
        source=None,
        package_bytes=package_bytes,
        package=assembled_package,
        minimal_writes=True,
        review_input=(
            "sha256:" + hashlib.sha256(revision_bytes).hexdigest()
            if req.get("record") is None else None,
            {"unit_id": req["unit_id"], "record": revision}),
        capability_override="unit.plan.revise",
        report_out=report_out,
        report_out_draft=(str(req["file"]) if req.get("file") else None),
    )
