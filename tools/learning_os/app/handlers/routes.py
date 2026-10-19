"""Material route patches and module material compaction."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from dataclasses import replace

import yaml

from learning_os.app._plan_gate import compose_plan_gate_errors as _compose_plan_gate_errors
from learning_os.app._plan_gate import (
    module_plan_validation_errors as _module_plan_validation_errors,
)
from learning_os.app._plan_gate import plan_apply_gate as _plan_apply_gate
from learning_os.app._plan_gate import real_perimeter_errors as _real_perimeter_errors
from learning_os.app.claim_admission import (
    anchor_report,
    lineage_artifacts,
    prepare_claim_admission,
    render_claim_lineage,
)
from learning_os.app.context import OpContext
from learning_os.app.encoders import dumps_compact
from learning_os.app.handlers._shared import guard_rows as _guard_rows
from learning_os.app.handlers._shared import map_for_unit as _map_for_unit
from learning_os.app.proposal import ResponsePayload, Result, TransactionProposal
from learning_os.app.registry import register
from learning_os.derive.semantics.claim_status import claim_impacts, observe_claims
from learning_os.derive.semantics.lineage import LEDGER_RELATIVE
from learning_os.domain.failures import NotFound, ValidationFailed, WriteRefused
from learning_os.domain.material_refs import (
    MATERIAL_FIELDS,
    PATCH_FIELDS,
    MaterialReferenceError,
    compact_map,
    expand_map,
    matching_routes,
    persist_route_ids,
    unit_routes,
)
from learning_os.domain.suggest import with_suggestions
from learning_os.store.codec import dump_yaml as _dump_yaml
from learning_os.store.contracts.gateway import current_gateway_request
from learning_os.store.transactions import parse_expected_revisions
from learning_os.store.warning_baseline import signatures_from_issues


def _apply_hint(args, capability, snapshot_id, revisions):
    """Ready-to-submit apply values for a successful --check.

    Direct CLI application is disabled, so the hint echoes everything the
    GatewayEnvelopeV2 needs except the per-request fields (request_id,
    idempotency_key, channel, approval): capability, exact payload,
    expected snapshot, and expected revisions. Output layer only —
    validation, guards, and receipts are unchanged.
    """
    if capability != "route.patch":
        return None
    payload = {"unit_id": args.unit_id, "route_id": args.route_id, "changes": args.changes}
    if getattr(args, "claim_evidence", None) is not None:
        payload["claim_evidence"] = args.claim_evidence
    return {
        "apply_via": "GatewayEnvelopeV2",
        "capability": capability,
        "payload": payload,
        "expected_snapshot": snapshot_id,
        "expected_revisions": dict(revisions),
        "apply_how": ("direct CLI application is disabled; submit a "
                      "GatewayEnvelopeV2 with this capability, payload, "
                      "expected_snapshot and expected_revisions"),
    }


def _changed_write(writes, path, data):
    content = _dump_yaml(data)
    # Callers compare record values first; this second check also avoids a
    # write intent when the exact serialized bytes are already current.
    if path.read_bytes() != content.encode("utf-8"):
        writes[path] = content


def _require_unit(repo, unit_id):
    """The raising twin of ``commands.material._unit`` for route.patch (SPEC R3).

    Identical messages: ``not_found("unit", …)`` is the original's
    ``with_suggestions(f"unit not found: …")``; the lookup refusal is now
    the typed ``NotFound``. The original stays for its other callers.
    """
    unit = repo.units.get(unit_id)
    if unit is None:
        raise NotFound("unit", unit_id, repo.units,
                       site="route.patch.unknown-unit")
    if unit.module_id not in repo.module_source_maps:
        raise WriteRefused(f"unit {unit_id} has no module source map")
    return unit


def _require_route(routes, route_id):
    """The raising twin of the legacy route lookup for route.patch (SPEC (bf) G2).

    Zero matches raise the typed ``NotFound`` with the byte-identical
    legacy complaint; several matches keep the plain ``WriteRefused``.
    """
    matches = [r for r in routes if r["id"] == route_id]
    if len(matches) == 1:
        return matches[0]
    ids = [row["id"] for row in routes]
    complaint = with_suggestions(
        f"route {route_id} is missing or ambiguous in this unit",
        route_id, ids)
    if not matches:
        raise NotFound("route", route_id, ids, message=complaint,
                       site="route.patch.unknown-route")
    raise WriteRefused(complaint)


def route_patch_plan(repo, unit_id, route_id, changes):
    if not isinstance(changes, dict) or not changes or any(
        k not in PATCH_FIELDS or not isinstance(v, str) or not v.strip() or len(v) > 16000
        for k, v in changes.items()
    ):
        raise WriteRefused("changes must contain nonempty text for declared material fields only")
    unit = _require_unit(repo, unit_id)
    module_id = unit.module_id
    source_map = repo.module_source_maps[module_id]
    routes = unit_routes(source_map, module_id, unit_id)
    old = _require_route(routes, route_id)
    changes = {k: v for k, v in changes.items() if k not in old or old[k] != v}
    if not changes:
        return {}, set(), {"unit_id": unit_id, "route_id": route_id, "changes": {}}
    updated = persist_route_ids(source_map, module_id, {route_id})
    found = []
    for entry in updated["sources"]:
        for row in entry.get("unit_routes", []) or []:
            if isinstance(row, dict) and row.get("id") == route_id:
                found.append(row)
    if len(found) != 1:
        raise WriteRefused(f"route {route_id} is ambiguous in its module")
    found[0].update(changes)
    writes = {}
    _changed_write(writes, repo.module_source_map_origins[module_id], updated)
    artifacts = {module_id, unit_id}
    unit_data = copy.deepcopy(unit.data)
    for selection in unit_data.get("source_selections", []) or []:
        if not isinstance(selection, dict):
            continue
        same = selection.get("route_id") == route_id if selection.get("route_id") else (
            selection.get("source_id") == old["source_id"] and selection.get("locator") == old.get("locator")
        )
        if same and "locator" in changes:
            # A legacy selection must identify exactly one route, not just a
            # file reused for several pedagogical routes.
            if not selection.get("route_id") and len([r for r in routes if
                r.get("source_id") == selection.get("source_id") and r.get("locator") == selection.get("locator")
            ]) != 1:
                raise WriteRefused("legacy source selection is ambiguous; link its exact route first")
            selection["locator"] = changes["locator"]
    if unit_data != unit.data:
        _changed_write(writes, unit.path, unit_data)
    sm = _map_for_unit(repo, unit_id)
    if sm:
        raw = copy.deepcopy(sm.authored_data or sm.data)
        for stage, effective in zip(raw["stages"], sm.data["stages"], strict=True):
            for resource, expanded in zip(stage.get("resources", []), effective.get("resources", []), strict=True):
                if not isinstance(resource, dict):
                    continue
                ref = resource.get("material_ref")
                matches = matching_routes(expanded, routes)
                linked = ref is not None and ref["route_id"] == route_id
                if not linked and not (len(matches) == 1 and matches[0]["id"] == route_id):
                    continue
                if ref is not None:
                    # Once sharing is explicit, all remaining local values are
                    # deliberate overrides, even if they equal today's owner.
                    continue
                for field, owner in MATERIAL_FIELDS.items():
                    # Explicit stage overrides survive. Only identical legacy
                    # mirrors are synchronized; inherited fields expand later.
                    if owner in changes and field in resource and resource[field] == old.get(owner):
                        resource[field] = changes[owner]
        if raw != (sm.authored_data or sm.data):
            _changed_write(writes, sm.path, raw)
        # A map's effective material changes even when only its owner is written.
        if expand_map(raw, updated, module_id, unit_id) != sm.data:
            artifacts.add(sm.id)
    return writes, artifacts, {"unit_id": unit_id, "route_id": route_id,
                               "changes": {k: {"before": old.get(k), "after": v} for k, v in changes.items()}}


def compaction_plan(repo, module_id):
    """The module compaction planner, moved for its conversion (SPEC §12 R4).

    Moved verbatim from ``commands.material`` except the module miss, which
    is a canonical-kind lookup (R6): the typed ``NotFound`` carries the
    byte-identical legacy complaint.
    """
    if module_id not in repo.module_source_maps:
        raise NotFound("module", module_id, repo.module_source_maps,
                       message=f"module source map not found: {module_id}",
                       site="module.materials.compact.unknown-module")
    source_map = repo.module_source_maps[module_id]
    writes, artifacts, used = {}, set(), set()
    saved = 0
    for sm in sorted(repo.study_maps.values(), key=lambda row: row.id):
        if sm.module_id != module_id:
            continue
        raw = sm.authored_data or sm.data
        compact, refs = compact_map(raw, source_map, module_id, sm.unit_id)
        if compact == raw:
            continue
        if expand_map(compact, source_map, module_id, sm.unit_id) != sm.data:
            raise WriteRefused(f"compaction changed {sm.id}")
        _changed_write(writes, sm.path, compact)
        used.update(refs)
        artifacts.update((module_id, sm.unit_id, sm.id))
        saved += len(sm.path.read_bytes()) - len(writes.get(sm.path, "").encode())
    pinned = persist_route_ids(source_map, module_id, used)
    if pinned != source_map:
        _changed_write(writes, repo.module_source_map_origins[module_id], pinned)
    return writes, artifacts, {"module_id": module_id, "map_bytes_saved": saved,
                               "referenced_routes": len(used)}


def _check_gate(root, writes):
    """The plan preflight as a check ``validate_extra`` (SPEC (bd) item 3).

    Returns exactly what ``_module_plan_validation_errors(root, writes)``
    returned: the real-tree perimeter layer plus the staged run's content
    errors and warning delta, from ``check_proposal``'s one validation, and
    nothing when there are no writes (the preflight did not run then).
    """
    def validate_extra(staged_repo, staged_issues):
        if not writes:
            return []
        signatures, content_errors = signatures_from_issues(staged_issues)
        return _compose_plan_gate_errors(
            root,
            perimeter_errors=_real_perimeter_errors(root),
            synthesis_errors=[],
            ack_errors=[],
            content_errors=content_errors,
            signatures=signatures)

    return validate_extra


def _render_plan_check(record: dict, payload: dict) -> dict:
    """Today's ``--check`` output from the check record (SPEC §12 R4, (bd)).

    Refuses with the preflight's exact text when the record failed, else
    returns the ``_print_stable`` stamping of the check result with its
    ``next`` hint, on the record's snapshot.
    """
    if not record["ok"]:
        raise ValidationFailed(
            "canonical validation failed: "
            + "; ".join(map(str, record["errors"][:8])))
    result = payload["result"]
    snapshot = record["expected_snapshot"]
    check_result = {
        **result, "ok": True, "check": True, "canonical_files_written": 0,
    }
    hint = _apply_hint(argparse.Namespace(**payload["apply_args"]),
                       payload["capability"], snapshot,
                       result["expected_revisions"])
    if hint is not None:
        check_result["next"] = hint
    return {"schema_version": 1, "snapshot_id": snapshot, **check_result}


def _execute_material_plan(ctx: OpContext, req: dict, capability: str,
                           planner) -> Result:
    """``commands.material._execute`` as one R4 flow (SPEC §12 R4).

    Check mode returns the proposal for the pipeline's check; a direct-CLI
    apply keeps the shadow refusal; the commit's gate list raises from
    ``after_commit``; a refused commit prints the result JSON on stdout,
    as ``_execute`` did (SPEC (bd)).
    """
    root = ctx.root
    ctx.require_snapshot(req.get("expected_snapshot"))
    repo = ctx.repo()
    if repo.parse_failures:
        raise WriteRefused("material operation refuses unreadable canonical records")
    try:
        writes, artifacts, detail = planner(repo)
    except MaterialReferenceError as exc:
        raise WriteRefused(str(exc)) from exc
    checking = req.get("check") is True
    lineage_will_change = False
    if capability == "route.patch":
        unit = repo.units[req["unit_id"]]
        source_map_path = repo.module_source_map_origins[unit.module_id]
        proposed = (yaml.safe_load(writes[source_map_path]) if source_map_path in writes
                    else repo.module_source_maps[unit.module_id])
        supplied = req.get("claim_evidence")
        if supplied is not None and (not isinstance(supplied, dict)
                                    or supplied.get("claim_id") != "covers:" + req["route_id"]):
            raise WriteRefused("claim_evidence must name exactly this route's covers claim",
                               site="route.patch.lineage-preflight-failed", exit_code=1)
        package = {"source_map": proposed, "claim_evidence": [supplied] if supplied is not None else []}
        admission = prepare_claim_admission(root, repo, unit.module_id, package, unit_scope=unit.id)
        if admission.problems:
            raise WriteRefused("route patch lineage preflight failed; no canonical files were written",
                               site="route.patch.lineage-preflight-failed", exit_code=1,
                               extra_stderr=tuple("- " + problem for problem in admission.problems))
        lineage_will_change = bool(admission.changed)
        artifacts = set(lineage_artifacts(artifacts, lineage_will_change))
        detail["claim_anchors"] = anchor_report(admission.evidence)
        try:
            before = observe_claims(root, repo=repo, route_ids=[req["route_id"]])
        except ValueError as exc:
            raise WriteRefused(f"cannot read claim impact: {exc}") from exc
        after = {cid: replace(row, status="stale") if writes and row.status == "supported" else row
                 for cid, row in before.items()}
        detail["claims"] = claim_impacts(before, after, ["covers:" + rid for rid in admission.changed])

        if lineage_will_change and not checking and current_gateway_request() is not None:
            writes[root / LEDGER_RELATIVE] = render_claim_lineage(
                root, repo, unit.module_id, package, admission.changed,
                admission.evidence, admission.live_routes, incremented_artifacts=artifacts)
    rows = {p.relative_to(root).as_posix(): hashlib.sha256(v.encode()).hexdigest()
            for p, v in sorted(writes.items()) if p != root / LEDGER_RELATIVE}
    affected = sorted(set(rows) | ({LEDGER_RELATIVE} if lineage_will_change else set()))
    plan_hash = "sha256:" + hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
    result = {"schema_version": 1, **detail, "plan_sha256": plan_hash,
              "affected_files": affected, "artifact_ids": sorted(artifacts),
              "expected_revisions": _guard_rows(root, artifacts)}
    if req.get("plan_sha256") not in (None, plan_hash):
        raise WriteRefused("compaction plan changed; review the current plan")
    if not checking and capability == "module.materials.compact" and req.get("plan_sha256") is None:
        raise WriteRefused("compaction requires the reviewed plan SHA-256")
    if ctx.gateway is None and not req.get("check"):
        # Only a direct CLI apply — which the commit refuses as
        # envelope-less — keeps the shadow refusal text it always had.
        errors = _module_plan_validation_errors(root, writes) if writes else []
        if errors:
            raise ValidationFailed("canonical validation failed: " + "; ".join(map(str, errors[:8])))
    if checking:
        return Result(
            {"result": result, "capability": capability,
             "apply_args": {key: req.get(key)
                            for key in ("unit_id", "route_id", "changes", "claim_evidence")}},
            proposal=TransactionProposal(
                capability=capability,
                writes=writes,
                artifact_ids=sorted(artifacts),
                validate_extra=_check_gate(root, writes),
            ),

        )
    if not writes:
        raise WriteRefused("no material changes to apply",
                           site=f"{ctx.operation}.no-changes")
    validate_extra, gate_errors = _plan_apply_gate(root)
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(str(exc)) from exc

    refusal = (gate_errors, ValidationFailed("canonical validation failed"))

    def finish(confirmation):
        return {**result, "ok": True, **confirmation}

    def refused_stdout(errors):
        return dumps_compact({**result, "ok": False,
                            **({"errors": list(map(str, errors))} if errors else {})})

    return Result(
        ResponsePayload(result, finish({}), confirmation='merge'),
        proposal=TransactionProposal(refusal=refusal,
            capability=capability,
            writes=writes,
            artifact_ids=sorted(artifacts),
            expected_revisions=expected_revisions or {},
            validate_extra=validate_extra,
        ),




    )


@register("route.patch", kind="command", render_check=_render_plan_check)
def route_patch(ctx: OpContext, req: dict) -> Result:
    """Patch one material route's declared fields, with its map mirrors."""
    return _execute_material_plan(ctx, req, "route.patch", lambda repo: route_patch_plan(
        repo, req["unit_id"], req["route_id"], req["changes"],
    ))


@register("module.materials.compact", kind="command",
          render_check=_render_plan_check)
def module_materials_compact(ctx: OpContext, req: dict) -> Result:
    """Share repeated stage material fields losslessly across one module's maps."""
    return _execute_material_plan(
        ctx, req, "module.materials.compact",
        lambda repo: compaction_plan(repo, req["module_id"]))
