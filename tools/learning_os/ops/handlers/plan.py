"""Plan-area handlers (PLAN D4): material plans, revisions, and reads."""

from __future__ import annotations

import argparse
import contextlib
import copy
import datetime as _dt
import hashlib
import json
import os
import re
import tempfile
import unicodedata
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlsplit

import yaml

from learning_os import githistory, observations
from learning_os.contracts import (
    PLAN_TEMPLATE_VERSION,
    ContractValidationError,
    PlanTemplateError,
    build_plan_template,
    current_template_problems,
    require_current_template,
)
from learning_os.contracts.gateway import current_gateway_request
from learning_os.contracts.json_schema import validate_contract
from learning_os.domain.failures import (
    NotFound,
    RevisionConflict,
    StaleSnapshot,
    ValidationFailed,
    WriteRefused,
    unreadable_refusal,
)
from learning_os.domain.plan_import import (
    _ack_shape_problems,
    _apply_unit_route_changes,
    _assemble_compact_module_revision,
    _inventory_block,
    _inventory_view,
    _knowledge_node_rows,
    _minimal_artifact_ids,
    _module_plan_ordering_problems,
    _module_plan_routing_problems,
    _source_map_routes,
    _source_map_routes_with_source,
    _synthesis_entries,
)
from learning_os.domain.suggest import (
    MAX_SUGGESTIONS,
    expansion,
    not_found,
    suggest,
    with_suggestions,
)
from learning_os.learning_runtime import (
    RuntimeInputError,
    read_stage_results,
    stage_results_for,
)
from learning_os.loading import FRONTMATTER_RE
from learning_os.masters_planning import (
    MastersPlanningError,
    prepare_master_promotion,
)
from learning_os.material_refs import (
    MATERIAL_FIELDS,
    PATCH_FIELDS,
    MaterialReferenceError,
    compact_map,
    expand_map,
    matching_routes,
    persist_route_ids,
    unit_routes,
)
from learning_os.material_slices import SliceResolutionError, _read_part
from learning_os.material_synthesis import (
    _COMPARED_BASIS_FIELDS,
    MaterialSynthesisError,
    MaterialSynthesisUnitNotFound,
    current_unit_material_basis,
    material_synthesis_freshness,
    publication_lineage,
    publication_lineage_record,
    synthesis_destination,
    validate_unit_material_synthesis,
)
from learning_os.materials_resolution import (
    MATERIAL_SCHEME,
    canonical_material_uri,
    material_uri_authority,
    project_material_resource,
    resolve_route_material_files,
    sha256_file,
)
from learning_os.ops._legacy_plumbing import (
    MAX_STAGE_RESULTS,
    _analysis_notes,
    _apply_hint,
    _approved_assessments,
    _changed_write,
    _dump_study_map,
    _dump_yaml,
    _evidence_label,
    _freshness_label,
    _guard_rows,
    _map_for_unit,
    _note_bytes,
    _read_content_bound_file,
    _read_structured_file,
    _render_frontmatter,
    _route_material_files,
    _snapshot,
    _unit_note_scope,
    _use_evidence,
    _window_values,
    prepare_review_envelope,
)
from learning_os.ops._plan_gate import (
    _compose_plan_gate_errors,
    _coverage_audit_problems,
    _enumerate_inventory_roots,
    _inventory_row_problems,
    _master_promotion_check_result,
    _master_promotion_preflight,
    _module_plan_check_report,
    _module_plan_contract_problems,
    _module_plan_validation_errors,
    _plan_apply_gate,
    _real_perimeter_errors,
)
from learning_os.ops.check import _staged_shadow
from learning_os.ops.context import OpContext
from learning_os.ops.handlers._shared import apply_reviewed_envelope
from learning_os.ops.proposal import Result, TransactionProposal
from learning_os.ops.registry import register
from learning_os.pathing import PathBoundaryError, resolve_symlinks_inside
from learning_os.render import replace_h2_section as _replace_h2_section
from learning_os.revisions import artifact_revision, load_revisions
from learning_os.rules.common import CANONICAL_TREES
from learning_os.semantics.lineage import (
    LEDGER_RELATIVE,
    NODE_CONTENT_PREFIX,
    ROUTE_CONTENT_PREFIX,
    LineageError,
    dump_ledger,
    emit_route_covers,
    load_ledger,
    node_content_digest,
    restamp_claim,
    route_content_digest,
    to_dict,
    withdraw,
)
from learning_os.semantics.restamp import (
    ELIGIBLE,
    analyze,
    claims_list_sha256,
)
from learning_os.transactions import parse_expected_revisions, transaction_artifacts
from learning_os.warning_baseline import signatures_from_issues


def _dumps_plan(payload: dict) -> str:
    """The exact material-plan encoder: compact, unescaped."""
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


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
    rows = {p.relative_to(root).as_posix(): hashlib.sha256(v.encode()).hexdigest()
            for p, v in sorted(writes.items())}
    plan_hash = "sha256:" + hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
    result = {"schema_version": 1, **detail, "plan_sha256": plan_hash,
              "affected_files": list(rows), "artifact_ids": sorted(artifacts),
              "expected_revisions": _guard_rows(root, artifacts)}
    checking = req.get("check") is True
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
                            for key in ("unit_id", "route_id", "changes")}},
            proposal=TransactionProposal(
                capability=capability,
                writes=writes,
                artifact_ids=sorted(artifacts),
                validate_extra=_check_gate(root, writes),
            ),
            json_dumps=_dumps_plan,
        )
    if not writes:
        raise WriteRefused("no material changes to apply",
                           site=f"{ctx.operation}.no-changes")
    validate_extra, gate_errors = _plan_apply_gate(root)
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(str(exc)) from exc

    def after_commit(code, errors, confirmation):
        if gate_errors:
            raise ValidationFailed("canonical validation failed: " + "; ".join(map(str, gate_errors[:8])))

    def finish(confirmation):
        return {**result, "ok": True, **confirmation}

    def refused_stdout(errors):
        return _dumps_plan({**result, "ok": False,
                            **({"errors": list(map(str, errors))} if errors else {})})

    return Result(
        result,
        proposal=TransactionProposal(
            capability=capability,
            writes=writes,
            artifact_ids=sorted(artifacts),
            expected_revisions=expected_revisions or {},
            validate_extra=validate_extra,
        ),
        finish=finish,
        after_commit=after_commit,
        refused_stdout=refused_stdout,
        json_dumps=_dumps_plan,
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


def _dumps_indented(payload: dict) -> str:
    """The exact revision encoder: indented, unescaped."""
    return json.dumps(payload, indent=2, ensure_ascii=False)


def _input_record(req: dict, label: str) -> dict:
    """The inline record or structured file, from the request (SPEC §12).

    Moved from ``commands.collection_entry`` with ``args.<dest>`` retargeted
    to the request dict; the source and publish units share this copy.
    """
    value = req.get("record")
    if value is not None:
        if not isinstance(value, dict):
            raise WriteRefused(f"{label} must be an object")
        return value
    file_name = req.get("file")
    if not file_name:
        raise WriteRefused(f"{label} is required")
    return _read_structured_file(file_name)


def _require_gateway_v2() -> None:
    """Refuse a direct CLI apply of an approved write (SPEC §12).

    Moved verbatim from ``commands.collection_entry``; the source units
    share this copy, and ``commands.vnext`` keeps its own for platform.
    """
    from learning_os.contracts.gateway import current_gateway_request

    if current_gateway_request() is None:
        raise WriteRefused(
            "this approved write must use GatewayEnvelopeV2; direct CLI publication is disabled"
        )


SOURCE_ID = re.compile(r"^source-[a-z0-9]+(?:-[a-z0-9]+)*$")
COLLECTION_STEM = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
COLLECTION_REVISE_FIELDS = frozenset({"collection", "source", "why"})


def _splice_why(raw: str, stem: str, position: int, sid: str,
                old: str, why: str) -> str:
    """Replace only the targeted entry's `why` scalar in the original text.

    A full YAML round-trip rewrites layout everywhere (81 to 91 lines on the
    math bookshelf); the revision owns one scalar, so only its source span is
    replaced. Indentation, the `why:` key, quoting elsewhere, sibling entries,
    header comments and blank lines survive byte-identical. Anything the
    splice cannot prove safe — flow style, anchors, duplicate keys, a raw
    text that no longer carries the loaded line — is refused, never guessed.
    """
    try:
        root = yaml.compose(raw)
    except yaml.YAMLError as exc:
        raise WriteRefused(f"collection '{stem}' does not parse: {exc}") from exc
    if not isinstance(root, yaml.MappingNode):
        raise WriteRefused(f"collection '{stem}' is not a mapping")
    entries_node = None
    for key, value in root.value:
        if isinstance(key, yaml.ScalarNode) and key.value == "entries":
            entries_node = value
    if not isinstance(entries_node, yaml.SequenceNode):
        raise WriteRefused(f"collection '{stem}' has no entries list")
    if position >= len(entries_node.value):
        raise WriteRefused(
            f"collection '{stem}' changed under the revision — re-run --check")
    entry_node = entries_node.value[position]
    if not isinstance(entry_node, yaml.MappingNode):
        raise WriteRefused(
            f"collection '{stem}' entry {position} is not a mapping")
    fields = [(k.value, v) for k, v in entry_node.value
              if isinstance(k, yaml.ScalarNode)]
    if sum(1 for name, _ in fields if name == "why") != 1:
        raise WriteRefused(
            f"collection '{stem}' entry {position} has no single 'why' scalar")
    sources = [v.value for name, v in fields
               if name == "source" and isinstance(v, yaml.ScalarNode)]
    if sources != [sid]:
        raise WriteRefused(
            f"collection '{stem}' changed under the revision — re-run --check")
    value = next(v for name, v in fields if name == "why")
    if not isinstance(value, yaml.ScalarNode) or value.value != old:
        raise WriteRefused(
            f"collection '{stem}' no longer carries the checked line — "
            "re-run --check")
    lines = raw.splitlines(keepends=True)
    start, end = value.start_mark, value.end_mark
    span_start = start.line
    span_end = end.line if end.column > 0 else end.line - 1
    # The prefix (indent, dash, `why:` key, spacing) is preserved verbatim;
    # flow style cannot reach here with a clean suffix (a closing `}`/`]`
    # always trails the scalar) and is refused below.
    prefix = lines[span_start][:start.column]
    comment = ""
    if value.style in (">", "|"):
        rest = lines[span_start][start.column:]
        match = re.match(r"^[|>][+-]?[0-9]?[ \t]*(#[^\n]*)?\n?$", rest)
        if match is None:
            raise WriteRefused(
                f"collection '{stem}' entry {position} carries an exotic "
                "block header — refusing the splice")
        comment = match.group(1) or ""
    else:
        rest = lines[span_end][end.column:]
        match = re.match(r"^[ \t]*(#[^\n]*)?\n?$", rest)
        if match is None:
            raise WriteRefused(
                f"collection '{stem}' entry {position} carries trailing "
                "content after its 'why' — refusing the splice")
        comment = match.group(1) or ""
    dumped = yaml.safe_dump({"why": why}, width=4096, allow_unicode=True,
                            sort_keys=False)
    if not dumped.startswith("why: "):
        raise WriteRefused("could not serialize the replacement line")
    scalar_lines = dumped[len("why: "):].rstrip("\n").split("\n")
    replacement = [prefix + scalar_lines[0] + "\n"]
    replacement.extend(line + "\n" for line in scalar_lines[1:])
    if comment:
        replacement[-1] = replacement[-1][:-1] + "  " + comment + "\n"
    if span_end == len(lines) - 1 and not lines[span_end].endswith("\n"):
        replacement[-1] = replacement[-1][:-1]
    return "".join(lines[:span_start] + replacement + lines[span_end + 1:])


def _plan_collection_entry_revise(root: Path, repo, item: Any) -> dict:
    """Validate one collection-entry revision; return diff, writes, guards.

    Moved from ``commands.collection_entry._plan_revise`` for its
    conversion (SPEC §12): the repository now arrives as a parameter
    (``ctx.repo()`` at the call sites) instead of a fresh ``load_repo``.
    """
    if not isinstance(item, dict):
        raise WriteRefused("collection revise payload must be an object")
    for field in sorted(set(item) - COLLECTION_REVISE_FIELDS):
        raise WriteRefused(
            f"field '{field}' is outside the revise allowlist "
            "(only one entry's 'why' is revised here; source, group, order "
            "and every other entry are never written through revision)"
        )
    if "collection" not in item or "source" not in item or "why" not in item:
        raise WriteRefused("a revision needs 'collection', 'source' and 'why'")
    stem, sid, why = item.get("collection"), item.get("source"), item.get("why")
    if not isinstance(stem, str) or not COLLECTION_STEM.match(stem):
        raise WriteRefused("'collection' must be a kebab-case filename stem")
    if not isinstance(sid, str) or not SOURCE_ID.match(sid):
        raise WriteRefused("'source' must match source-<slug>")
    if not isinstance(why, str) or not why.strip() or "\n" in why or "\r" in why:
        raise WriteRefused("'why' must be a nonempty one-line string")
    doc = (repo.collections or {}).get(stem)
    if doc is None:
        raise WriteRefused(with_suggestions(
            f"unknown collection: {stem}", stem, repo.collections or {}))
    origin = (repo.collection_origins or {}).get(stem)
    if origin is None:
        raise WriteRefused(f"collection '{stem}' has no file origin")
    entries = doc.get("entries") or []
    hits = [position for position, entry in enumerate(entries)
            if isinstance(entry, dict) and entry.get("source") == sid]
    if not hits:
        known_sources = [str(entry.get("source")) for entry in entries
                         if isinstance(entry, dict) and entry.get("source")]
        raise WriteRefused(with_suggestions(
            f"collection '{stem}' has no entry for source {sid}",
            sid, known_sources))
    if len(hits) > 1:
        raise WriteRefused(
            f"collection '{stem}' matches {len(hits)} entries for {sid} — "
            "deduplicate the collection before revising one line"
        )
    (position,) = hits
    old = entries[position].get("why")
    if old == why:
        raise WriteRefused(
            f"collection '{stem}' entry for {sid} already carries that line: no change"
        )
    if not isinstance(old, str):
        raise WriteRefused(
            f"collection '{stem}' entry for {sid} carries a non-string 'why' — "
            "repair the collection before revising one line"
        )
    try:
        # Universal newlines: a CRLF shelf normalizes to LF here, like
        # every governed write in the system — content and layout survive,
        # endings follow the writer.
        raw = origin.read_text(encoding="utf-8")
    except OSError as exc:
        raise WriteRefused(f"cannot re-read {origin}: {exc}") from exc
    spliced = _splice_why(raw, stem, position, sid, old, why)
    try:
        before_text = yaml.safe_load(raw)
        parsed = yaml.safe_load(spliced)
    except yaml.YAMLError as exc:
        raise WriteRefused(f"collection '{stem}' splice failed to parse: {exc}") from exc
    # Differential proof, same parser both sides: the splice replaced exactly
    # the targeted scalar and nothing else. (Comparing against the loaded doc
    # instead would false-refuse on loader normalization such as dates.)
    expected = copy.deepcopy(before_text)
    expected["entries"][position]["why"] = why
    if parsed != expected:
        raise WriteRefused(
            f"collection '{stem}' splice verification failed — refusing the write")
    try:
        validate_contract(root, "collections.schema.json", parsed)
    except ValueError as exc:
        raise WriteRefused(f"{stem}: {exc}") from exc
    artifact = f"collection:{stem}"
    diff = [{"collection": stem, "source": sid,
             "group": entries[position].get("group"),
             "before": old, "after": why}]
    canonical = json.dumps(diff, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return {
        "diff": diff,
        "diff_sha256": "sha256:" + hashlib.sha256(canonical).hexdigest(),
        "writes": {origin: spliced},
        "artifact_ids": [artifact],
        "expected_revisions": {artifact: artifact_revision(root, artifact)},
    }


@register("collection.entry.revise", kind="command")
def collection_entry_revise(ctx: OpContext, req: dict) -> Result:
    """Revise one collection entry's `why`, atomically."""
    root = ctx.root
    repo = ctx.repo()
    try:
        data = _input_record(req, "collection revise record")
        plan = _plan_collection_entry_revise(root, repo, data)
    except WriteRefused as exc:
        message = str(exc)
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.bad-record",
            gateway_message=json.dumps({"ok": False, "error": message}),
            exit_code=2,
        ) from exc
    if req.get("check") is True:
        return Result(
            {
                "ok": True, "check": True, "records": len(plan["diff"]),
                "diff": plan["diff"], "diff_sha256": plan["diff_sha256"],
                "expected_revisions": plan["expected_revisions"],
                "artifact_ids": plan["artifact_ids"],
            },
            json_dumps=_dumps_indented,
        )
    if not req.get("approve"):
        message = "collection entry revision requires explicit approval"
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.needs-approval",
            gateway_message=json.dumps({"ok": False, "error": message}),
            exit_code=2,
        )
    _require_gateway_v2()
    try:
        plan = _plan_collection_entry_revise(root, repo, data)
    except WriteRefused as exc:
        message = str(exc)
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.bad-record",
            gateway_message=json.dumps({"ok": False, "error": message}),
            exit_code=2,
        ) from exc
    expected_diff = req.get("expected_diff_sha256")
    if not expected_diff:
        message = "apply needs --expected-diff-sha256 from a check run"
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.needs-expected-diff",
            gateway_message=json.dumps({"ok": False, "error": message}),
            exit_code=2,
        )
    if expected_diff != plan["diff_sha256"]:
        message = "revision diff changed since check; re-run --check"
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.diff-changed",
            gateway_message=json.dumps({"ok": False, "error": message}),
            exit_code=2,
        )
    ctx.require_snapshot(req.get("expected_snapshot"))
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site=f"{ctx.operation}.bad-expected-revision",
        ) from exc

    def finish_collection_entry_revise(confirmation):
        return {"ok": True, **confirmation}

    def refused_stdout_collection_entry_revise(errors):
        return _dumps_indented({
            "ok": False,
            **({"errors": [str(error) for error in errors]} if errors else {}),
        })

    return Result(
        {"ok": True},
        proposal=TransactionProposal(
            capability="collection.entry.revise",
            writes=plan["writes"],
            artifact_ids=tuple(plan["artifact_ids"]),
            expected_revisions=expected_revisions,
        ),
        finish=finish_collection_entry_revise,
        refused_stdout=refused_stdout_collection_entry_revise,
        json_dumps=_dumps_indented,
    )


def _dumps_compact(payload: dict) -> str:
    """The exact stable-read encoder: compact, unescaped."""
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


#: Batch reads serve at most this many routes: one snapshot, one load,
#: and a payload an operator can still review. Mirrors inspect's batch cap.
MAX_BATCH_ROUTES = 20

#: The span excerpt stays well under the old 8 KiB operator print.
MAX_EXCERPT = 6000


def _unit(ctx, repo, unit_id):
    """The unit, or an R6 refusal (SPEC (bi) item 7).

    Moved from ``commands.material`` for the plan reads (SPEC (bs)
    item 3): the miss is a ``NotFound`` with the byte-identical legacy
    complaint; the corrupt-catalogue guard stays a site-less plain
    refusal, exactly as it propagated.
    """
    unit = repo.units.get(unit_id)
    if unit is None:
        complaint = with_suggestions(
            f"unit not found: {unit_id}", unit_id, repo.units)
        raise NotFound("unit", unit_id, repo.units, message=complaint,
                       site=f"{ctx.operation}.unknown-unit")
    if unit.module_id not in repo.module_source_maps:
        raise WriteRefused(f"unit {unit_id} has no module source map")
    return unit


def _route(ctx, routes, route_id):
    """One exact route id, or an R6 refusal (SPEC (bi) item 7).

    Moved from ``commands.material`` for the plan reads (SPEC (bs)
    item 3): the miss is a ``NotFound`` with the byte-identical legacy
    complaint; the ambiguous match keeps the legacy plain refusal and
    its text, as ``_require_route`` does.
    """
    matches = [r for r in routes if r["id"] == route_id]
    if len(matches) != 1:
        complaint = with_suggestions(
            f"route {route_id} is missing or ambiguous in this unit",
            route_id, [row["id"] for row in routes])
        if not matches:
            raise NotFound("route", route_id,
                           [row["id"] for row in routes],
                           message=complaint,
                           site=f"{ctx.operation}.unknown-route")
        raise WriteRefused(complaint)
    return matches[0]


def _route_entry(ctx, routes, study_map, source_map, unit, route_id):
    """One exact route plus its stage uses: the scalar and batch shape.

    Both selectors build on this so their per-route fields cannot drift.
    Raises WriteRefused for a missing, cross-unit or ambiguous route id.

    Moved from ``commands.material`` for the plan reads (SPEC (bs)
    item 3); only the context threads through to the lookup.
    """
    route = _route(ctx, routes, route_id)
    uses = []
    if study_map:
        raw_stages = {s["id"]: s for s in (study_map.authored_data or study_map.data)["stages"]}
        for stage in study_map.data.get("stages", []):
            for i, resource in enumerate(stage.get("resources", [])):
                if not isinstance(resource, dict):
                    continue
                raw = raw_stages[stage["id"]]["resources"][i]
                ref = raw.get("material_ref", {}) if isinstance(raw, dict) else {}
                matches = matching_routes(resource, routes)
                if ref.get("route_id") == route["id"] or (
                    len(matches) == 1 and matches[0]["id"] == route["id"]
                ):
                    uses.append({"stage_id": stage["id"], "resource_index": i,
                                 "scope_triage": resource.get("scope_triage"),
                                 "overrides": {k: v for k, v in resource.items()
                                               if k in MATERIAL_FIELDS
                                               and (k in raw if ref else
                                                    v != route.get(MATERIAL_FIELDS[k]))}})
    return {"route": route, "uses": uses,
            "patch_fields": sorted(PATCH_FIELDS),
            "patch_capability": "route.patch"}


def _batch_entries(ctx, routes, study_map, source_map, unit, route_ids):
    """Ordered route entries for 1-20 distinct routes of one unit.

    Every id is resolved before any entry is built, so a missing,
    cross-unit, duplicate or out-of-bounds request refuses the whole
    batch — never a partial payload.

    Moved from ``commands.material`` for the plan reads (SPEC (bs)
    item 3); only the context threads through to the lookups.
    """
    ids = list(route_ids or [])
    if not ids:
        raise WriteRefused(
            "plan-edit-context batch needs at least one route id",
            site=f"{ctx.operation}.empty-batch")
    if len(ids) > MAX_BATCH_ROUTES:
        raise WriteRefused(
            f"plan-edit-context accepts at most {MAX_BATCH_ROUTES} routes per batch",
            site=f"{ctx.operation}.batch-too-many")
    if len(set(ids)) != len(ids):
        raise WriteRefused(
            "plan-edit-context batch route ids are distinct",
            site=f"{ctx.operation}.batch-duplicate")
    for route_id in ids:
        _route(ctx, routes, route_id)
    return [_route_entry(ctx, routes, study_map, source_map, unit, route_id)
            for route_id in ids]


def _stage_entry(ctx, study_map, stage_id):
    """One stage's own flags and placements, without the whole map.

    Returns the stage row as stored (effective, expanded): identity,
    status, triage and exam flags, objective, concepts, runtime target,
    and resource placements. Raises WriteRefused for a missing stage or
    a unit with no study map — never a partial payload.

    Moved from ``commands.material`` for the plan reads (SPEC (bs)
    item 3): the miss is an R6 ``NotFound`` with the byte-identical
    legacy complaint; the ambiguous match keeps the legacy plain
    refusal and its text.
    """
    if study_map is None:
        raise WriteRefused(
            "plan-edit-context --stage-id needs a unit with a study map",
            site=f"{ctx.operation}.stage-needs-map")
    stages = [s for s in study_map.data.get("stages", []) if isinstance(s, dict)]
    matches = [s for s in stages if s.get("id") == stage_id]
    if len(matches) != 1:
        complaint = f"stage {stage_id} is missing or ambiguous in this unit"
        if not matches:
            raise NotFound("stage", stage_id,
                           [s["id"] for s in stages if s.get("id")],
                           message=complaint,
                           site=f"{ctx.operation}.unknown-stage")
        raise WriteRefused(complaint)
    return dict(matches[0])


def _unit_audit(root, repo, unit) -> dict:
    """Deterministic planning audit for one unit: counts and lists, no judgments.

    Reports what the catalogue contains and where it stands — depth, scope,
    triage, placements, synthesis freshness — without deciding what is useful.
    The operator still reads the material; this only makes the shape visible
    before that reading starts.

    Moved verbatim from ``commands.material`` for the plan reads (SPEC
    (bs) item 3).
    """
    from learning_os.material_synthesis import (
        MaterialSynthesisError,
        synthesis_destination,
        validate_unit_material_synthesis,
    )
    from learning_os.ops._plan_gate import _match_key

    source_map = repo.module_source_maps[unit.module_id]
    routes = unit_routes(source_map, unit.module_id, unit.id)
    study_map = _map_for_unit(repo, unit.id)
    stages = study_map.data.get("stages", []) if study_map else []
    placements = [r for s in stages if isinstance(s, dict)
                  for r in (s.get("resources", []) or []) if isinstance(r, dict)]
    placed_keys = {_match_key(r) for r in placements}

    def placed(route):
        return (("route", route.get("id")) in placed_keys
                or ("source", route.get("source_id"), route.get("locator")) in placed_keys)

    by_depth: dict[str, int] = {}
    by_scope: dict[str, int] = {}
    for route in routes:
        by_depth[route.get("depth", "unstated")] = by_depth.get(route.get("depth", "unstated"), 0) + 1
        by_scope[route.get("scope", "unstated")] = by_scope.get(route.get("scope", "unstated"), 0) + 1
    triage_by_stage: dict[str, dict] = {}
    for stage in stages:
        if not isinstance(stage, dict):
            continue
        counts: dict[str, int] = {}
        for resource in stage.get("resources", []) or []:
            if not isinstance(resource, dict):
                continue
            key = resource.get("scope_triage", "untriaged")
            counts[key] = counts.get(key, 0) + 1
        triage_by_stage[stage.get("id", "?")] = counts
    advanced_required = sorted(
        route["id"] for route in routes
        if route.get("depth") == "advanced-reference"
        and any(r.get("scope_triage") in {"required-now", "helpful-now"}
                for r in placements
                if _match_key(r) in (("route", route.get("id")),
                                     ("source", route.get("source_id"),
                                      route.get("locator")))))
    current_unplaced = sorted(
        route["id"] for route in routes
        if route.get("scope") in {"current", "prerequisite"} and not placed(route))
    legacy: dict[str, list] = {}
    for source in source_map.get("sources", []) or []:
        if not isinstance(source, dict):
            continue
        strings = [r for r in source.get("unit_routes", []) or []
                   if isinstance(r, str)]
        if strings:
            legacy[str(source.get("source_id"))] = strings
    legacy_sources = set(legacy)
    exact_with_unresolved = sorted(
        route["id"] for route in routes
        if route.get("source_id") in legacy_sources)
    unplaced = sorted(route["id"] for route in routes if not placed(route))
    try:
        destination = synthesis_destination(root, unit.id)
    except MaterialSynthesisError:
        destination = None
    present = bool(destination and destination.is_file())
    synthesis: dict = {"present": present,
                       "replacement_required_if_evidential_routes_change": present,
                       "replacement_reason": (
                           "an existing dossier needs a staged replacement when evidential routes change"
                           if present else "no existing dossier requires replacement"),
                       "fresh": False, "detail": None,
                       "deep_reviewed": 0, "screened": 0,
                       "unevaluated": 0, "unavailable": 0}
    if synthesis["present"]:
        try:
            dossier = yaml.safe_load(destination.read_text(encoding="utf-8"))
            validate_unit_material_synthesis(root, unit.id, dossier)
            synthesis["fresh"] = True
        except Exception as exc:  # noqa: BLE001 - freshness is best-effort reporting
            synthesis["detail"] = str(exc)
        try:
            for row in (dossier.get("route_assessments", []) or []):
                status = row.get("review_status")
                if status == "deep-reviewed":
                    synthesis["deep_reviewed"] += 1
                elif status == "screened":
                    synthesis["screened"] += 1
                elif status == "unevaluated":
                    synthesis["unevaluated"] += 1
                elif status == "unavailable":
                    synthesis["unavailable"] += 1
        except Exception:  # noqa: BLE001 - counts stay zero on unreadable dossiers
            pass
    adjacent: dict[str, list] = {}
    unit_source_ids = {r.get("source_id") for r in routes}
    for other_id, other in sorted(repo.units.items()):
        if other_id == unit.id or other.module_id != unit.module_id:
            continue
        try:
            other_routes = unit_routes(
                repo.module_source_maps[other.module_id], other.module_id, other_id)
        except Exception:  # noqa: BLE001 - one unreadable neighbour skips, never blocks
            continue
        shared = sorted(unit_source_ids & {r.get("source_id") for r in other_routes})
        if shared:
            adjacent[other_id] = shared
    return {
        "unit_id": unit.id,
        "module_id": unit.module_id,
        "source_records": len(unit_source_ids),
        "routes": len(routes),
        "placements": len(placements),
        "routes_by_depth": by_depth,
        "routes_by_scope": by_scope,
        "triage_by_stage": triage_by_stage,
        "advanced_reference_placed_required_or_helpful": advanced_required,
        "current_or_prerequisite_unplaced": current_unplaced,
        "legacy_string_routes_by_source": legacy,
        "exact_routes_with_unresolved_siblings": exact_with_unresolved,
        "unplaced_routes": unplaced,
        "synthesis": synthesis,
        "adjacent_unit_source_reuse": adjacent,
        "scope_authority": unit.data.get("scope_sources", []),
        "prior_year_boundary": sorted(
            route["id"] for route in routes if route.get("scope") == "prior-year"),
        "out_of_scope_present": sorted(
            route["id"] for route in routes if route.get("scope") == "out-of-scope"),
    }


def _brief_analysis_refs(root, repo, unit, routes, snapshot, *, include_related=False) -> dict:
    """Reusable analysis references for one unit's routes: ids, never bodies.

    The same durable records material-context searches — analysis notes
    standing direct against this unit's routes plus approved unit
    assessments — as identifiers with freshness, review, and resolution
    labels. Same-source-only notes are counted with an expansion hint,
    listed only through --include-related. Follow-up reads fetch bodies
    through the expand commands, never from here.

    Moved verbatim from ``commands.material`` for the plan reads (SPEC
    (bs) item 3).
    """
    pairs = [(route.get("source_id"), route) for route in routes
             if route.get("source_id")]
    refs = []
    related = []
    for note in _analysis_notes(repo):
        binding = note.meta["material_analysis"]
        standing = _unit_note_scope(repo, binding, pairs)
        if standing is None:
            continue
        (refs if standing == "direct" else related).append({
            "note_id": note.id,
            "source_id": binding.get("source_id"),
            "scope": standing,
            "resolution": binding.get("resolution"),
            "review": note.meta.get("semantic_review"),
            "inspected_range": binding.get("inspected_range") or {},
            "freshness": _freshness_label(root, binding),
            "path": note.path.relative_to(root).as_posix(),
        })
    assessed: list[str] = []
    stale: list[str] = []
    freshness_by_synthesis: dict[str, dict] = {}
    for synthesis_id, row_unit, assessment in _approved_assessments(repo):
        if row_unit != unit.id:
            continue
        route_id = assessment.get("route_id")
        if not isinstance(route_id, str):
            continue
        fresh = freshness_by_synthesis.get(synthesis_id)
        if fresh is None:
            dossier = repo.unit_material_syntheses.get(synthesis_id)
            fresh = material_synthesis_freshness(
                root, unit.id, dossier if isinstance(dossier, dict) else {},
                repo=repo)
            freshness_by_synthesis[synthesis_id] = fresh
        (assessed if fresh["status"] == "current" else stale).append(route_id)
    by_resolution: dict = {}
    for ref in refs:
        by_resolution[ref["resolution"]] = by_resolution.get(ref["resolution"], 0) + 1
    out = {"analysis_notes": refs,
           "related_count": len(related),
           "related_expand": expansion(
               "plan-edit-context", unit.id, "--brief", "--include-related",
               "--expected-snapshot", snapshot),
           "approved_assessment_routes": sorted(assessed),
           "stale_assessment_routes": sorted(stale),
           "analysis_by_resolution": by_resolution}
    if include_related:
        out["related_notes"] = related
    return out


def _brief_payload(root, repo, unit, routes, study_map, artifacts, snapshot,
                   *, include_related=False, include_neighbors=False) -> dict:
    """The brief preparation form: what the next command needs, nothing else.

    Identities, guards, id inventories, the audit's missing-evidence lists,
    reusable analysis references, required follow-up inputs, applicable
    preflight checks, and explicit expandable commands. Full route bodies,
    the study map, and analysis prose stay behind the expand references.
    The neighboring-unit source-reuse map is discovery information, not
    coverage: the brief carries its count, and the complete map lists only
    through the explicit expansion.

    Moved verbatim from ``commands.material`` for the plan reads (SPEC
    (bs) item 3).
    """
    route_ids = sorted(r["id"] for r in routes if r.get("id"))
    stages = study_map.data.get("stages", []) if study_map else []
    stage_rows = [s for s in stages if isinstance(s, dict)]
    stage_ids = sorted(s["id"] for s in stage_rows if s.get("id"))
    batches = [
        expansion("plan-edit-context", unit.id, "--route-ids",
                  *route_ids[i:i + MAX_BATCH_ROUTES],
                  "--expected-snapshot", snapshot)
        for i in range(0, len(route_ids), MAX_BATCH_ROUTES)]
    audit = _unit_audit(root, repo, unit)
    neighbors = audit["adjacent_unit_source_reuse"]
    brief_audit = {key: value for key, value in audit.items()
                   if key != "adjacent_unit_source_reuse"}
    brief_audit["adjacent_unit_source_reuse_count"] = len(neighbors)
    if include_neighbors:
        brief_audit["adjacent_unit_source_reuse"] = neighbors
    return {
        "contract": "plan-edit-context-brief",
        "unit_id": unit.id,
        "module_id": unit.module_id,
        "artifact_revisions": _guard_rows(root, artifacts),
        "inventory": {
            "route_ids": route_ids,
            "stage_ids": stage_ids,
            "route_count": len(route_ids),
            "stage_count": len(stage_ids),
            "placement_count": sum(
                len(s.get("resources", []) or []) for s in stage_rows),
        },
        "unit_audit": brief_audit,
        "analysis_refs": _brief_analysis_refs(
            root, repo, unit, routes, snapshot,
            include_related=include_related),
        "required_inputs": {
            "route_patch": {
                "route_id": (f"one of the {len(route_ids)} inventoried route ids"),
                "changes": {
                    "fields": sorted(PATCH_FIELDS),
                    "rules": ("nonempty text per field, at most 16000 characters, "
                              "declared material fields only"),
                },
                "guards": ("artifact_revisions above; the gateway envelope "
                           "carries the snapshot"),
            },
            "plan_replace": {
                "file": ("reviewed package bytes for unit-plan-revise, "
                         "unit-map-import, or module-plan-import"),
                "round_trip": ("save the --check JSON, then apply with "
                               "--apply-reviewed-sha256 and --review-report"),
                "guards": ("artifact_revisions above; the saved report carries "
                           "the exact prepared envelope"),
            },
        },
        "preflight": [
            {"operation": "route-patch",
             "check": expansion(
                 "route-patch", unit.id, "ROUTE_ID",
                 "--changes", "JSON", "--check")},
            {"operation": "unit-plan-revise",
             "check": expansion(
                 "unit-plan-revise", unit.id, "--file", "REVISION.yaml",
                 "--check")},
            {"operation": "unit-map-import",
             "check": expansion(
                 "unit-map-import", unit.id, "--file", "MAP.yaml", "--check")},
            {"operation": "module-plan-import",
             "check": expansion(
                 "module-plan-import", unit.module_id, "--file", "PLAN.yaml",
                 "--check")},
            {"operation": "verify",
             "check": (".venv/bin/python tools/verify_plan_receipt.py "
                       f"--report REPORT.json --unit {unit.id}")},
        ],
        "expand": {
            "full": expansion(
                "plan-edit-context", unit.id, "--expected-snapshot", snapshot),
            "full_audit": expansion(
                "plan-edit-context", unit.id, "--audit",
                "--expected-snapshot", snapshot),
            "adjacent_unit_source_reuse": expansion(
                "plan-edit-context", unit.id, "--brief", "--include-neighbors",
                "--expected-snapshot", snapshot),
            "route_batches": batches,
            "stages": {sid: expansion(
                "plan-edit-context", unit.id, "--stage-id", sid,
                "--expected-snapshot", snapshot)
                       for sid in stage_ids},
            "analysis_search": expansion(
                "material-context", "QUERY", "--unit", unit.id,
                "--expected-snapshot", snapshot),
        },
    }


@register("cli.plan-edit-context", kind="query")
@register("plan.edit-context", kind="query")
def plan_edit_context(ctx: OpContext, req: dict) -> Result:
    """Assemble one unit's edit context: map, routes, selections, audit."""
    root = ctx.root
    snapshot = _snapshot(root, req.get("expected_snapshot"))
    repo = ctx.repo()
    if repo.parse_failures:
        raise WriteRefused(
            "material operation refuses unreadable canonical records")
    unit = _unit(ctx, repo, req["unit_id"])
    source_map = repo.module_source_maps[unit.module_id]
    routes = unit_routes(source_map, unit.module_id, unit.id)
    study_map = _map_for_unit(repo, unit.id)
    artifacts = {unit.module_id, unit.id}
    if study_map:
        artifacts.add(study_map.id)
    payload = {"contract": "plan-edit-context", "unit_id": unit.id,
               "module_id": unit.module_id,
               "artifact_revisions": _guard_rows(root, artifacts),
               "preflight": "route-patch UNIT_ID ROUTE_ID --changes JSON --check returns exact write guards"}
    selectors = [bool(req.get("route_id")),
                 req.get("route_ids") is not None,
                 bool(req.get("stage_id"))]
    if sum(selectors) > 1:
        raise WriteRefused(
            "plan-edit-context takes one of --route-id, --route-ids, --stage-id",
            site=f"{ctx.operation}.one-selector")
    if req.get("audit") and any(selectors):
        raise WriteRefused(
            "plan-edit-context --audit attaches to the full unit context, "
            "not to a route or stage selection",
            site=f"{ctx.operation}.audit-needs-full")
    if req.get("brief") and any(selectors):
        raise WriteRefused(
            "plan-edit-context --brief is the full-unit preparation form; "
            "expand one route or stage through its listed command instead",
            site=f"{ctx.operation}.brief-needs-full")
    if req.get("brief") and req.get("audit"):
        raise WriteRefused(
            "plan-edit-context --brief already carries the unit audit",
            site=f"{ctx.operation}.brief-has-audit")
    if req.get("include_related") and not req.get("brief"):
        raise WriteRefused(
            "plan-edit-context --include-related needs --brief",
            site=f"{ctx.operation}.related-needs-brief")
    if req.get("include_neighbors") and not req.get("brief"):
        raise WriteRefused(
            "plan-edit-context --include-neighbors needs --brief",
            site=f"{ctx.operation}.neighbors-needs-brief")
    if req.get("route_id"):
        payload.update(_route_entry(
            ctx, routes, study_map, source_map, unit, req["route_id"]))
    elif req.get("route_ids") is not None:
        entries = _batch_entries(
            ctx, routes, study_map, source_map, unit, req["route_ids"])
        payload.update({"contract": "plan-edit-context-batch",
                        "requested_route_ids": list(req["route_ids"]),
                        "routes": entries})
    elif req.get("stage_id"):
        try:
            untargeted = stage_results_for(
                read_stage_results(repo), unit.id, req["stage_id"])
        except RuntimeInputError as exc:
            raise WriteRefused(
                str(exc), site=f"{ctx.operation}.bad-stage-results",
            ) from exc
        payload.update({"contract": "plan-edit-context-stage",
                        "requested_stage_id": req["stage_id"],
                        "stage": _stage_entry(ctx, study_map, req["stage_id"]),
                        "stage_results": {
                            "results": [
                                {"id": row.get("id"),
                                 "activity": row.get("activity"),
                                 "result": row.get("result"),
                                 "timestamp": row.get("timestamp"),
                                 "conditions": row.get("conditions", []),
                                 "assistance": row.get("assistance", ""),
                                 "note": row.get("note", "")}
                                for row in untargeted[:MAX_STAGE_RESULTS]
                            ],
                            "total": len(untargeted),
                            "credit": "none",
                        },
                        "scope": "one stage only — universe questions "
                                 "(e.g. no source covers X) need the full unit context"})
    elif req.get("brief"):
        payload = _brief_payload(
            root, repo, unit, routes, study_map, artifacts, snapshot,
            include_related=bool(req.get("include_related")),
            include_neighbors=bool(req.get("include_neighbors")))
    else:
        # Present the compact form even before an existing map is migrated.
        # Expansion inputs are included once, never separately per stage.
        compact = None
        if study_map:
            compact, _ = compact_map(study_map.authored_data or study_map.data,
                                     source_map, unit.module_id, unit.id)
        payload.update({"study_map": compact, "routes": routes,
                        "source_selections": unit.data.get("source_selections", [])})
        if req.get("audit"):
            payload.update({"unit_audit": _unit_audit(root, repo, unit)})
    _snapshot(root, snapshot)
    return Result(
        {"schema_version": 1, "snapshot_id": snapshot, **payload},
        json_dumps=_dumps_compact,
    )


def _placement_route(ctx, repo, unit, source_map, routes, route, req):
    """Use only a snapshot-bound canonical placement, never caller-supplied paths.

    Moved from ``commands.material_span`` for the plan reads (SPEC
    (bs) item 3): only the context threads through to the lookup and
    the request replaces the namespace.
    """
    stage_id = req.get("stage_id")
    index = req.get("resource_index")
    if bool(stage_id) != (index is not None):
        raise WriteRefused(
            "--stage and --resource-index must be supplied together",
            site=f"{ctx.operation}.stage-needs-index")
    if not stage_id:
        return route, ""
    study_map = _map_for_unit(repo, unit.id)
    if study_map is None:
        raise WriteRefused("unit has no stage placement to inspect",
                           site=f"{ctx.operation}.placement-needs-map")
    stages = [row for row in study_map.data.get("stages", [])
              if isinstance(row, dict) and row.get("id") == stage_id]
    if not stages:
        raise NotFound("stage", stage_id,
                       [row["id"] for row in study_map.data.get("stages", [])
                        if isinstance(row, dict) and row.get("id")],
                       message="placement is missing or ambiguous in this unit",
                       site=f"{ctx.operation}.unknown-placement")
    if len(stages) != 1 or index < 0 or index >= len(stages[0].get("resources", [])):
        raise WriteRefused("placement is missing or ambiguous in this unit",
                           site=f"{ctx.operation}.unknown-placement")
    uses = _route_entry(
        ctx, routes, study_map, source_map, unit, route["id"])["uses"]
    if not any(use["stage_id"] == stage_id and use["resource_index"] == index
               for use in uses):
        raise WriteRefused(
            "placement is missing or does not belong to this route",
            site=f"{ctx.operation}.placement-foreign")
    resource = stages[0]["resources"][index]
    if resource.get("source_id") != route.get("source_id"):
        raise WriteRefused("placement source does not match its route",
                           site=f"{ctx.operation}.placement-source-mismatch")
    selected = {**route, **{key: resource[key] for key in ("locator", "vault_path", "url")
                           if key in resource}}
    return selected, f" --stage {stage_id} --resource-index {index}"


@register("material.span", kind="query")
def material_span(ctx: OpContext, req: dict) -> Result:
    """One common source-span description, with optional bounded local inspection."""
    root = ctx.root
    try:
        snapshot = _snapshot(root, req.get("expected_snapshot"))
        repo = ctx.repo()
        unit = repo.units.get(req["unit_id"])
        if unit is None:
            complaint = with_suggestions(
                f"unknown unit {req['unit_id']}",
                req["unit_id"], repo.units)
            raise NotFound("unit", req["unit_id"], repo.units,
                           message=complaint,
                           site=f"{ctx.operation}.unknown-unit")
        source_map = repo.module_source_maps.get(unit.module_id)
        if source_map is None:
            raise WriteRefused("unit has no module source map")
        routes = unit_routes(source_map, unit.module_id, unit.id)
        matches = [row for row in routes
                   if row["id"] == req["route_id"]]
        if len(matches) > 1:
            raise WriteRefused(
                f"route {req['route_id']} is ambiguous in {unit.id}: "
                f"{len(matches)} matches")
        if not matches:
            route_ids = sorted(row["id"] for row in routes if row.get("id"))
            base = f"route not found: {req['route_id']} in {unit.id}"
            if suggest(req["route_id"], route_ids):
                complaint = with_suggestions(
                    base, req["route_id"], route_ids)
            else:
                # No ranked near-miss: still name the unit's routes, bounded,
                # so the caller picks an existing one instead of guessing.
                listed = route_ids[:MAX_SUGGESTIONS]
                extra = len(route_ids) - len(listed)
                detail = ", ".join([*listed, f"+{extra} more"] if extra > 0
                                   else listed)
                complaint = f"{base} (routes: {detail})" if detail else base
            raise NotFound("route", req["route_id"], route_ids,
                           message=complaint,
                           site=f"{ctx.operation}.unknown-route")
        route, placement_flags = _placement_route(
            ctx, repo, unit, source_map, routes, matches[0], req)
        source = repo.sources.get(route.get("source_id"), {})
        projected = project_material_resource(repo, route)
        files = resolve_route_material_files(repo, route)
        status = ("local-observed" if files else
                  "local-unavailable" if projected.get("material_uri") else
                  "remote-unobserved" if route.get("url") or source.get("url") else
                  "unavailable")
        next_action = None
        if status == "remote-unobserved":
            next_action = (
                "Open the URL explicitly to read it. For local extraction, "
                "register an authorized local copy as material, run "
                "make inventory, then rerun material-span "
                f"{unit.id} {route['id']}{placement_flags} --extract. No remote bytes "
                "were observed here."
            )
        elif status == "local-unavailable":
            next_action = (
                "Restore the registered local file, run make inventory, "
                f"then rerun material-span {unit.id} {route['id']}{placement_flags} --extract."
            )
        analysis = _brief_analysis_refs(root, repo, unit, [route], snapshot)
        notes = analysis["analysis_notes"]
        analysis["analysis_notes_total"] = len(notes)
        analysis["analysis_notes_truncated"] = len(notes) > 20
        analysis["analysis_notes"] = notes[:20]
        analysis["expand"] = expansion(
            "plan-edit-context", unit.id, "--route-id", route["id"],
            "--expected-snapshot", snapshot)
        analysis["approved_assessment_routes"] = [
            item for item in analysis["approved_assessment_routes"] if item == route["id"]]
        analysis["stale_assessment_routes"] = [
            item for item in analysis["stale_assessment_routes"] if item == route["id"]]
        spans = []
        materials_real = (repo.learningos_root / "materials").resolve()
        for resolved in files:
            path = Path(resolved.path)
            entry = {"material_uri": resolved.material_uri,
                     "format": path.suffix.lower().lstrip(".") or "unknown",
                     "file_sha256": sha256_file(path),
                     "extraction": "not-requested"}
            # A ready analysis binding: exactly what the draft needs,
            # minus inspected_range, in the stored canonical form
            # (materials-relative path, bare hex). Additive only.
            bare_digest = entry["file_sha256"].removeprefix("sha256:")
            entry["binding"] = {
                "resolution": "resolved",
                "source_id": route.get("source_id"),
                "material": path.resolve().relative_to(
                    materials_real).as_posix(),
                "recorded_source_digest": bare_digest,
                "live_source_digest": bare_digest,
            }
            if req.get("extract"):
                try:
                    part = _read_part(route["id"], resolved, route.get("locator", ""))
                    if sha256_file(path) != entry["file_sha256"]:
                        raise SliceResolutionError(route["id"], "file changed during inspection")
                    excerpt = part.text[:MAX_EXCERPT]
                    entry.update({"extraction": part.status,
                                  "excerpt": excerpt,
                                  "excerpt_truncated": len(part.text) > MAX_EXCERPT,
                                  "pages": list(part.pages),
                                  "page_total": part.page_total})
                    if part.kind == "text" and excerpt:
                        # Text bindings cite physical, one-based file lines,
                        # including a partly displayed final line.
                        last_line = excerpt.count("\n") + (not excerpt.endswith("\n"))
                        entry["inspected_range_unit"] = "line"
                        entry["inspected_range"] = {"start": 1, "end": last_line}
                except (SliceResolutionError, OSError, UnicodeError) as exc:
                    entry.update({"extraction": "unreadable", "reason": str(exc)})
            spans.append(entry)
        payload = {
            "contract": "material-span-v1", "unit_id": unit.id,
            "module_id": unit.module_id, "route_id": route["id"],
            "source_id": route.get("source_id"),
            "locator": route.get("locator"),
            "url": route.get("url") or source.get("url"),
            "availability": status,
            "next_action": next_action,
            "analysis_refs": analysis,
            "spans": spans,
            "expansion": None if req.get("extract") else expansion(
                "material-span", unit.id, route["id"],
                *([ "--stage", req["stage_id"], "--resource-index",
                    str(req["resource_index"])]
                  if req.get("stage_id") is not None else []),
                "--extract", "--expected-snapshot", snapshot),
        }
        _snapshot(root, snapshot)
        return Result(
            {"schema_version": 1, "snapshot_id": snapshot, **payload},
            json_dumps=_dumps_compact,
        )
    except StaleSnapshot as exc:
        raise StaleSnapshot(
            str(exc), site=f"{ctx.operation}.stale-snapshot",
            gateway_message=f"los: {exc}", exit_code=3,
        ) from exc
    except WriteRefused as exc:
        if exc.gateway_message is None:
            exc.gateway_message = f"los: {exc}"
        if exc.exit_code is None:
            exc.exit_code = 2
        raise
    except (OSError, ValueError) as exc:
        raise WriteRefused(
            str(exc), site=f"{ctx.operation}.read-failed",
            gateway_message=f"los: {exc}", exit_code=2,
        ) from exc


def _dumps_default(payload: dict) -> str:
    """The exact response encoder: default separators, unescaped."""
    return json.dumps(payload, ensure_ascii=False)


PLAN_TEMPLATE_CONTRACT = "plan-template-v1"

_PROFILE_SCHEMAS = {
    "curriculum": "study-map.schema.json",
}


def _human_plan_template(payload: dict) -> str:
    """The paste-ready YAML the operator reads (SPEC §12)."""
    return yaml.safe_dump(
        payload["plan"], sort_keys=False, allow_unicode=True, width=100
    ).removesuffix("\n")


@register("cli.plan-template", kind="query", human=_human_plan_template)
@register("plan.template", kind="query", human=_human_plan_template)
def plan_template(ctx: OpContext, req: dict) -> Result:
    """Read-only access to the single versioned study-map creation template."""
    root = ctx.root
    schema = _PROFILE_SCHEMAS[req["profile"]]
    try:
        plan = build_plan_template(
            req["profile"],
            title=req.get("title"),
            unit_id=req.get("unit_id"),
            module_id=req.get("module_id"),
        )
        validate_contract(root, schema, plan, label=f"{req['profile']} plan template v1")
    except (PlanTemplateError, ContractValidationError) as exc:
        message = f"cannot build plan template: {exc}"
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.bad-template",
            gateway_message=json.dumps({"ok": False, "error": message}),
            exit_code=2,
        ) from exc
    response = {
        "ok": True,
        "contract": PLAN_TEMPLATE_CONTRACT,
        "profile": req["profile"],
        "plan_template_version": PLAN_TEMPLATE_VERSION,
        "schema": schema,
        "plan": plan,
    }
    try:
        validate_contract(
            root, "plan-template.schema.json", response, label=PLAN_TEMPLATE_CONTRACT
        )
    except ContractValidationError as exc:
        message = f"plan template response invalid: {exc}"
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.bad-response",
            gateway_message=json.dumps({"ok": False, "error": message}),
            exit_code=2,
        ) from exc
    return Result(response, json_dumps=_dumps_default)


# ---------------------------------------------------------------------------
# Material-context helpers, moved verbatim from commands.reads with
# their last legacy caller (SPEC (bo) item 2).


ASSESSMENT_TEXT_FIELDS = ("contribution", "assumptions", "notation",
                          "exercise_value", "best_for", "limitations",
                          "locator")

_CONCEPT_VIA_LIMIT = 20

_ANCHOR_PREVIEW_LIMIT = 8

_ANCHOR_TEXT_LIMIT = 200


def _unit_route_pairs(repo, unit_id) -> list:
    """(source_id, route-dict) pairs routed to one unit.

    The same membership the scope check always used — a bare unit id or
    an expanded route carrying it — with string routes arriving as empty
    dicts so the shared rule, not the caller, decides what they prove.
    """
    unit = repo.units[unit_id]
    source_map = repo.module_source_maps.get(unit.module_id) or {}
    pairs = []
    for source in source_map.get("sources", []) or []:
        if not isinstance(source, dict) or not source.get("source_id"):
            continue
        for route in source.get("unit_routes", []) or []:
            if route == unit.id:
                pairs.append((source["source_id"], {}))
            elif isinstance(route, dict) and route.get("unit_id") == unit.id:
                pairs.append((source["source_id"], route))
    return pairs

def _route_material_index(repo, unit_id=None) -> dict:
    """route_id -> (source_id, route-dict), for one unit or every module."""
    if unit_id is not None:
        return {route.get("id"): pair for pair in _unit_route_pairs(repo, unit_id)
                for route in [pair[1]] if route.get("id")}
    index = {}
    for source_map in (repo.module_source_maps or {}).values():
        if not isinstance(source_map, dict):
            continue
        for source in source_map.get("sources", []) or []:
            if not isinstance(source, dict) or not source.get("source_id"):
                continue
            for route in source.get("unit_routes", []) or []:
                if isinstance(route, dict) and route.get("id"):
                    index.setdefault(route["id"], (source["source_id"], route))
    return index

def _concept_stage_routes(repo) -> dict[str, dict[str, list[tuple[str, dict]]]]:
    """concept id -> stage id -> the (source_id, route) pairs that stage places (F12).

    A stage joins a concept to a route when it tags the concept AND places
    the route — two declared edges, read-side only. Nothing is inferred and
    nothing is recorded: analysis notes carry no concept tags by
    construction, so without this join the concept filter's note branch
    could never match them. A note then joins only through the shared
    note-to-route rule (`_unit_note_scope`), never through a shared source
    id alone: one source (a lecture deck, a textbook) serves many concepts,
    and an analysis of its other pages is not evidence for this one.
    """
    routes = _route_material_index(repo, None)
    joined: dict[str, dict[str, list[tuple[str, dict]]]] = {}
    for map_id in sorted(repo.study_maps):
        stages = repo.study_maps[map_id].data.get("stages", []) or []
        for stage in stages:
            if not isinstance(stage, dict):
                continue
            stage_id = stage.get("id")
            if not isinstance(stage_id, str) or not stage_id:
                continue
            concepts = stage.get("concepts") or []
            if not concepts:
                continue
            placed: list[tuple[str, dict]] = []
            for resource in stage.get("resources", []) or []:
                if not isinstance(resource, dict):
                    continue
                route_id = resource.get("route_id")
                if not route_id and isinstance(
                        resource.get("material_ref"), dict):
                    route_id = resource["material_ref"].get("route_id")
                hit = routes.get(route_id)
                if hit is not None and isinstance(hit[0], str) and hit[0]:
                    placed.append(hit)
            if not placed:
                continue
            for concept_id in concepts:
                if not isinstance(concept_id, str) or not concept_id:
                    continue
                joined.setdefault(concept_id, {}).setdefault(
                    stage_id, []).extend(placed)
    return joined

def _explanation_snippets(title, text, body_offset, terms) -> list:
    """Title label plus true-file-line body windows for matched terms.

    A title hit yields one title snippet; body hits reuse the content
    search's windowing over the full text, so the reported lines are true
    file lines even though matching never sees the frontmatter. At most
    eight snippets either way, the title counting as one.
    """
    snippets = []
    if any(regex.search(title) for regex in terms):
        snippets.append({"label": "title", "text": title})
    body = text[body_offset:]
    positions = sorted({match.start() for regex in terms
                        if (match := regex.search(body)) is not None})
    for position in positions[:8 - len(snippets)]:
        absolute = body_offset + position
        start = max(text.rfind("\n", 0, absolute) + 1, absolute - 100)
        end = text.find("\n", absolute)
        end = min(end if end >= 0 else len(text), absolute + 180)
        snippets.append({"line": text.count("\n", 0, absolute) + 1,
                         "text": text[start:end]})
    return snippets

def _observations_digest(observations: dict) -> str:
    encoded = json.dumps(
        {key: observations[key] for key in sorted(observations)},
        ensure_ascii=False, sort_keys=True,
        separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"

def _note_purpose_hit(binding, purpose):
    if purpose is None:
        return True
    wanted = purpose.casefold()
    anchors = binding.get("anchors")
    if not isinstance(anchors, list):
        return False
    return any(wanted in str(anchor.get("purpose", "")).casefold()
               for anchor in anchors if isinstance(anchor, dict))

def _assessment_purpose_hit(assessment, purpose):
    if purpose is None:
        return True
    wanted = purpose.casefold()
    return any(wanted in str(assessment.get(field) or "").casefold()
               for field in ("best_for", "exercise_value"))

def _anchor_purpose_hit(anchor, wanted) -> bool:
    return (isinstance(anchor, dict)
            and wanted in str(anchor.get("purpose", "")).casefold())

def _anchor_selection(anchors, purpose):
    """Original-order anchors with literal purpose matches first, deduplicated.

    Returns (ordered, match_count): match_count is None without a purpose
    filter. Both groups keep file order; no anchor appears twice.
    """
    if not purpose:
        return list(anchors), None
    wanted = purpose.casefold()
    matches = [anchor for anchor in anchors
               if _anchor_purpose_hit(anchor, wanted)]
    seen = {id(anchor) for anchor in matches}
    return (matches + [anchor for anchor in anchors
                       if id(anchor) not in seen], len(matches))

def _clip_anchor_text(anchor):
    """The anchor with every long text field bounded, naming what clipped."""
    if not isinstance(anchor, dict):
        return anchor
    clipped = []
    shaped = {}
    for key, value in anchor.items():
        if isinstance(value, str) and len(value) > _ANCHOR_TEXT_LIMIT:
            shaped[key] = value[:_ANCHOR_TEXT_LIMIT]
            clipped.append(key)
        else:
            shaped[key] = value
    shaped["clipped_fields"] = clipped
    return shaped

def _analysis_note_item(root, note, *, raw_terms, terms, concept_id, purpose,
                        unit, material_ref, scope, evidence, observations,
                        include_anchors=False, concept_via=None):
    """One matched analysis note, or None when the terms miss.

    Terms match the explanation text — title plus body — with lexical AND;
    frontmatter (provenance paths, digests, ids) never matches. Title hits
    yield a title snippet; body hits yield true file line numbers. The
    scope label exists only under --unit, where direct and related mean
    something. Anchors preview bounded (purpose matches first) with exact
    totals; the complete index needs the explicit expansion.
    """
    raw = _note_bytes(root, note)
    text = raw.decode("utf-8")
    title = note.meta.get("title", note.id)
    front = FRONTMATTER_RE.match(text)
    body_offset = front.end() if front else 0
    body = text[body_offset:]
    matched = [raw_term for raw_term, regex in zip(raw_terms, terms, strict=True)
               if regex.search(title) or regex.search(body)]
    if len(matched) != len(raw_terms):
        return None
    binding = note.meta["material_analysis"]
    inspected = binding.get("inspected_range") or {}
    reasons = {"terms": matched}
    if concept_id is not None:
        reasons["concept"] = concept_id
    if concept_via:
        reasons["concept_via"] = [f"stage:{stage_id}" for stage_id in concept_via]
    if purpose:
        reasons["purpose"] = purpose
    if unit:
        reasons["unit"] = unit
    if material_ref is not None:
        reasons["material"] = material_ref
    item = {
        "origin": "analysis-note",
        "id": note.id, "title": title,
        "path": note.path.relative_to(root).as_posix(),
        "use_evidence": _evidence_label(
            evidence.get(binding.get("source_id")) or {}),
        "match": {**reasons, "snippets": _explanation_snippets(
            title, text, body_offset, terms)},
        "source": {
            "ref": binding.get("material"),
            "pages": [inspected.get("start"), inspected.get("end")],
            "freshness": _freshness_label(root, binding, observations),
        },
        "review": {
            "semantic_review": note.meta.get("semantic_review"),
            "resolution": binding.get("resolution"),
        },
    }
    anchors = binding.get("anchors") or []
    ordered, match_count = _anchor_selection(anchors, purpose)
    if include_anchors:
        item["anchors"] = list(anchors)
        item["anchor_returned"] = len(anchors)
        item["anchors_truncated"] = False
    else:
        item["anchors"] = [_clip_anchor_text(anchor)
                           for anchor in ordered[:_ANCHOR_PREVIEW_LIMIT]]
        item["anchor_returned"] = len(item["anchors"])
        item["anchors_truncated"] = len(anchors) > _ANCHOR_PREVIEW_LIMIT
    item["anchor_total"] = len(anchors)
    if purpose:
        item["purpose_match_count"] = match_count
        item["purpose_other_count"] = len(anchors) - match_count
    if scope is not None:
        item["scope"] = scope
    return item


def _resolve_concept(ctx, repo, raw):
    """A concept id or declared alias, matched case-insensitively.

    Moved from ``commands.reads`` with its last legacy caller (SPEC
    (bo) item 2); only the miss carries the caller's site, the
    ambiguous match keeps the legacy plain refusal and its text.
    """
    if raw in repo.concepts:
        return raw
    lowered = raw.casefold()
    hits = [cid for cid, concept in repo.concepts.items()
            if isinstance(concept, dict)
            and any(str(alias).casefold() == lowered
                    for alias in (concept.get("aliases") or []))]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        raise WriteRefused(
            f"unknown concept: {raw!r} matches no id or declared alias",
            site=f"{ctx.operation}.unknown-concept")
    raise WriteRefused(f"concept {raw!r} is ambiguous across {len(hits)} concepts; use an id")


def _check_material_ref(ctx, root, ref) -> str:
    """The exact materials-tree path a --material filter names, else refused.

    Exact: no canonicalization, so a near-miss matches nothing rather than
    something nearby. The boundary is still enforced — an escape refuses
    instead of reading outside the tree.

    Moved from ``commands.reads`` with its last legacy caller (SPEC
    (bo) item 2); only the caller's site is added.
    """
    materials = root.parent / "materials"
    pure = PurePosixPath(ref) if isinstance(ref, str) else None
    if (pure is None or not ref or pure.is_absolute()
            or "\\" in ref
            or any(part in {".", ".."} for part in pure.parts)):
        raise WriteRefused(
            f"--material must be a materials-tree-relative path: {ref!r}",
            site=f"{ctx.operation}.bad-material")
    try:
        (materials / ref).resolve(strict=False).relative_to(materials.resolve())
    except (OSError, ValueError) as exc:
        raise WriteRefused(
            f"--material must be a materials-tree-relative path: {ref!r}",
            site=f"{ctx.operation}.bad-material") from exc
    return ref


def _anchor_expansion_command(req, limit, snapshot, observed) -> str:
    """Re-run this read's selected page with complete anchor indexes.

    Moved from ``commands.reads`` with its last legacy caller (SPEC
    (bo) item 2); the request replaces the namespace.
    """
    parts = ["material-context", req.get("query") or ""]
    if req.get("concept"):
        parts += ["--concept", req["concept"]]
    if req.get("purpose"):
        parts += ["--purpose", req["purpose"]]
    if req.get("unit"):
        parts += ["--unit", req["unit"]]
    if req.get("material"):
        parts += ["--material", req["material"]]
    if req.get("include_related", False):
        parts += ["--include-related"]
    parts += ["--include-anchors", "--limit", str(limit),
              "--offset", str(req.get("offset")),
              "--expected-snapshot", snapshot,
              "--expected-observations", observed]
    return expansion(*parts)


@register("material.context", kind="query")
def material_context(ctx: OpContext, req: dict) -> Result:
    """Find saved explanations from an explanation need."""
    root = ctx.root
    try:
        try:
            offset, limit = _window_values(
                req.get("offset") or 0, req.get("limit") or 20,
                req.get("expected_snapshot"), 20)
        except WriteRefused as exc:
            exc.site = f"{ctx.operation}.bad-window"
            raise
        if offset and not req.get("expected_observations"):
            raise WriteRefused(
                "continuation requires --expected-observations from the "
                "previous response",
                site=f"{ctx.operation}.offset-needs-observations")
        raw_terms = (req.get("query") or "").split()
        terms = [re.compile(re.escape(term), re.IGNORECASE) for term in raw_terms]
        material_ref = req.get("material")
        if not terms and material_ref is None and not req.get("concept"):
            raise WriteRefused(
                "material context requires a nonempty query, --concept, "
                "or --material",
                site=f"{ctx.operation}.empty-need")
        if req.get("include_related") and not req.get("unit"):
            raise WriteRefused("--include-related needs --unit",
                               site=f"{ctx.operation}.related-needs-unit")
        if material_ref is not None:
            _check_material_ref(ctx, root, material_ref)
        snapshot = _snapshot(root, req.get("expected_snapshot"))
        repo = ctx.repo()
        note_dir = root / "knowledge" / "notes"
        note_failures = [
            (path, message) for path, message in repo.parse_failures
            if path.is_relative_to(note_dir)
        ]
        if note_failures:
            raise WriteRefused(unreadable_refusal(root, note_failures, "context"))
        synthesis_failures = [
            (path, message) for path, message in repo.parse_failures
            if path.name == "material-synthesis.yaml"
        ]
        if synthesis_failures:
            raise WriteRefused(unreadable_refusal(root, synthesis_failures, "context"))
        concept_id = _resolve_concept(ctx, repo, req["concept"]) \
            if req.get("concept") else None
        if req.get("unit") and req["unit"] not in repo.units:
            complaint = with_suggestions(
                f"unknown unit: {req['unit']!r}", req["unit"], repo.units)
            raise NotFound("unit", req["unit"], repo.units,
                           message=complaint,
                           site=f"{ctx.operation}.unknown-unit")
        assessments = _approved_assessments(repo)
        related_count = 0
        searched_related: list = []
        if req.get("unit"):
            assessments = [row for row in assessments if row[1] == req["unit"]]
            pairs = _unit_route_pairs(repo, req["unit"])
            direct_pool = []
            related_pool = []
            for note in _analysis_notes(repo):
                standing = _unit_note_scope(
                    repo, note.meta.get("material_analysis") or {}, pairs)
                if standing == "direct":
                    direct_pool.append(note)
                elif standing == "related":
                    related_pool.append(note)
            notes = direct_pool
            related_count = len(related_pool)
            if req.get("include_related"):
                searched_related = related_pool
        else:
            notes = _analysis_notes(repo)
        if concept_id is not None:
            concept_join = _concept_stage_routes(repo).get(concept_id, {})

            def _note_concept_via(note) -> list[str]:
                binding = note.meta.get("material_analysis") or {}
                if not isinstance(binding, dict):
                    return []
                via = [stage_id
                       for stage_id, placed in sorted(concept_join.items())
                       if _unit_note_scope(repo, binding, placed) == "direct"]
                return via[:_CONCEPT_VIA_LIMIT]

            def _note_matches_concept(note) -> bool:
                return (concept_id in (note.meta.get("concepts") or [])
                        or bool(_note_concept_via(note)))

            notes = [note for note in notes
                     if _note_matches_concept(note)]
            searched_related = [
                note for note in searched_related
                if _note_matches_concept(note)]
            assessments = [row for row in assessments
                           if concept_id in (row[2].get("concept_ids") or [])]
            via_by_note = {note.id: _note_concept_via(note)
                           for note in (*notes, *searched_related)}
        else:
            via_by_note = {}
        notes = [note for note in notes
                 if _note_purpose_hit(note.meta["material_analysis"], req.get("purpose"))]
        searched_related = [
            note for note in searched_related
            if _note_purpose_hit(note.meta["material_analysis"], req.get("purpose"))]
        assessments = [row for row in assessments
                       if _assessment_purpose_hit(row[2], req.get("purpose"))]
        if material_ref is not None:
            notes = [note for note in notes
                     if (note.meta.get("material_analysis") or {}).get("material")
                     == material_ref]
            searched_related = [
                note for note in searched_related
                if (note.meta.get("material_analysis") or {}).get("material")
                == material_ref]
            route_index = _route_material_index(repo, req.get("unit"))
            assessments = [
                row for row in assessments
                if material_ref in _route_material_files(
                    repo, *route_index.get(row[2].get("route_id"), (None, {})))]
        # Use evidence is deliberately global: feedback says a source
        # served in some stage, which bears on every result bound to
        # that source, however the query scoped the pool.
        evidence = _use_evidence(repo)
        pool = {
            "analysis_notes": len(notes),
            "assessments": len(assessments),
            # Related notes are counted, never pooled: the resolution
            # tallies below describe the default-visible direct set.
            "related_analysis_notes": related_count,
            "analysis_by_resolution": {},
            "analysis_unreviewed": 0,
        }
        for note in notes:
            binding = note.meta["material_analysis"]
            resolution = binding.get("resolution")
            pool["analysis_by_resolution"][resolution] = \
                pool["analysis_by_resolution"].get(resolution, 0) + 1
            if note.meta.get("semantic_review") == "unreviewed":
                pool["analysis_unreviewed"] += 1
        items = []
        observations: dict[str, str] = {}
        dossier_freshness: dict[str, dict] = {}
        include_anchors = bool(req.get("include_anchors", False))
        for note in notes:
            item = _analysis_note_item(
                root, note, raw_terms=raw_terms, terms=terms,
                concept_id=concept_id, purpose=req.get("purpose"),
                unit=req.get("unit"), material_ref=material_ref,
                scope="direct" if req.get("unit") else None,
                evidence=evidence, observations=observations,
                include_anchors=include_anchors,
                concept_via=via_by_note.get(note.id))
            if item is not None:
                items.append(item)
        for synthesis_id, unit_id, assessment in assessments:
            joined = "\n".join(str(assessment.get(field) or "")
                               for field in ASSESSMENT_TEXT_FIELDS)
            matched = [raw_term for raw_term, regex in zip(raw_terms, terms, strict=True)
                       if regex.search(joined)]
            if len(matched) != len(raw_terms):
                continue
            excerpts = []
            for field in ASSESSMENT_TEXT_FIELDS:
                if len(excerpts) >= 3:
                    break
                value = str(assessment.get(field) or "")
                if value and any(regex.search(value) for regex in terms):
                    excerpts.append({"field": field, "text": value[:200]})
            reasons = {"terms": matched}
            if concept_id is not None:
                reasons["concept"] = concept_id
            if req.get("purpose"):
                reasons["purpose"] = req["purpose"]
            if req.get("unit"):
                reasons["unit"] = req["unit"]
            if material_ref is not None:
                reasons["material"] = material_ref
            origin = repo.unit_material_synthesis_origins.get(synthesis_id)
            fresh = dossier_freshness.get(synthesis_id)
            if fresh is None:
                dossier = repo.unit_material_syntheses.get(synthesis_id)
                material_hashes = {}
                fresh = material_synthesis_freshness(
                    root, unit_id, dossier
                    if isinstance(dossier, dict) else {}, repo=repo,
                    cache=material_hashes)
                dossier_freshness[synthesis_id] = fresh
                observations[f"dossier:{synthesis_id}"] = (
                    f"{fresh['status']}:{','.join(fresh['reasons'])}")
                # Bind the bytes actually read by the shared freshness
                # calculation: two different sources can both be stale
                # for the same reason. Missing files remove an entry;
                # newly available files add one on the next read.
                observations.update({
                    f"dossier-material:{path}": digest
                    for path, digest in material_hashes.items()
                })
            items.append({
                "origin": "unit-assessment",
                "unit_id": unit_id, "synthesis_id": synthesis_id,
                "use_evidence": _evidence_label(
                    evidence.get(assessment.get("source_id")) or {}),
                "route_id": assessment.get("route_id"),
                "source_id": assessment.get("source_id"),
                "locator": assessment.get("locator"),
                "review_status": assessment.get("review_status"),
                "freshness": fresh,
                "concept_ids": assessment.get("concept_ids") or [],
                "match": {**reasons, "excerpts": excerpts},
                "open": {
                    "synthesis": origin.relative_to(root).as_posix()
                    if origin is not None else None,
                    "route_id": assessment.get("route_id"),
                },
            })
        related_items = []
        for note in searched_related:
            item = _analysis_note_item(
                root, note, raw_terms=raw_terms, terms=terms,
                concept_id=concept_id, purpose=req.get("purpose"),
                unit=req.get("unit"), material_ref=material_ref,
                scope="related",
                evidence=evidence, observations=observations,
                include_anchors=include_anchors,
                concept_via=via_by_note.get(note.id))
            if item is not None:
                related_items.append(item)
        # Stable sort: evidence ranks, ties keep insertion order
        # (notes by id, then assessments by unit and route). Without
        # recorded feedback every key is (0, 0) and the order is
        # exactly the pre-ranking stable order. Related notes rank
        # under the same key but append after every direct item.
        items.sort(key=lambda row: (-row["use_evidence"]["positive"],
                                    row["use_evidence"]["mismatch"]))
        related_items.sort(key=lambda row: (
            -row["use_evidence"]["positive"],
            row["use_evidence"]["mismatch"]))
        items.extend(related_items)
        # The continuation binds the normalized filters alongside the
        # observed bytes: equivalent filters (reordered terms, a
        # concept alias for its id) page on, changed ones refuse.
        observations["filter/query"] = " ".join(
            sorted(term.casefold() for term in raw_terms))
        observations["filter/unit"] = req.get("unit") or ""
        observations["filter/concept"] = concept_id or ""
        observations["filter/purpose"] = (req.get("purpose") or "").casefold()
        observations["filter/material"] = material_ref or ""
        observations["filter/related"] = \
            "related" if req.get("include_related") else "direct"
        observed = _observations_digest(observations)
        expected_observations = req.get("expected_observations")
        if expected_observations is not None and expected_observations != observed:
            raise StaleSnapshot(
                "material or filters observed by this query changed "
                "between pages; re-run from offset 0")
        ranked_by = ("recorded stage use-evidence per source: positive "
                     "feedback first, mismatch feedback last; ties keep "
                     "stable order (notes by id, then assessments by "
                     "unit and route)")
        if req.get("include_related"):
            ranked_by += ("; --include-related appends related notes "
                          "under the same ranking")
        returned = items[offset:offset + limit]
        payload = {
            "contract": "material-context",
            "ranked_by": ranked_by,
            "items": returned,
            "total": len(items),
            "next_offset": offset + limit if offset + limit < len(items) else None,
            "observations_sha256": observed,
            "searched": {
                "query_terms": raw_terms, "concept": concept_id,
                "purpose": req.get("purpose"), "unit": req.get("unit"),
                "material": material_ref,
                "include_related": bool(req.get("include_related")),
                "analysis_notes": len(_analysis_notes(repo)),
                "assessments": len(_approved_assessments(repo)),
            },
            "pool": pool,
        }
        if not items:
            payload["empty"] = (
                "no match in the searched records; this never proves "
                "no source explains the topic")
        if not include_anchors and any(
                item.get("origin") == "analysis-note"
                and (item.get("anchors_truncated")
                     or any(row.get("clipped_fields")
                            for row in item.get("anchors", [])
                            if isinstance(row, dict)))
                for item in returned):
            payload["expand"] = {"anchors": _anchor_expansion_command(
                req, limit, snapshot, observed)}
        _snapshot(root, snapshot)
        return Result(
            {"schema_version": 1, "snapshot_id": snapshot, **payload},
            json_dumps=_dumps_compact,
        )
    except StaleSnapshot as exc:
        raise StaleSnapshot(
            str(exc), site=f"{ctx.operation}.stale-snapshot",
            gateway_message=f"los: {exc}", exit_code=3,
        ) from exc
    except WriteRefused as exc:
        if exc.gateway_message is None:
            exc.gateway_message = f"los: {exc}"
        if exc.exit_code is None:
            exc.exit_code = 2
        raise
    except (OSError, UnicodeError) as exc:
        raise WriteRefused(
            str(exc), site=f"{ctx.operation}.read-failed",
            gateway_message=f"los: {exc}", exit_code=2,
        ) from exc


# ---------------------------------------------------------------------------
# Source-intake planning, moved verbatim from commands.source_catalog
# with its converting handlers (SPEC (bs) item 1).


SOURCE_TYPES = frozenset({
    "book", "paper", "lecture", "course", "video", "website",
    "documentation", "software", "conversation", "other",
})
MAX_BATCH = 20

# What a create may carry vs. a correct (D7, R2). Type and authors define the
# work itself, so they are set once; title, year and organization are edition
# metadata and stay correctable. Removals are explicit lists, never inferred
# from an absent key.
CREATE_FIELDS = frozenset({
    "action", "id", "partition", "title", "type", "authors", "organization",
    "year", "url", "identifiers", "discovery", "thematic_group_ids",
})
CORRECT_FIELDS = frozenset({
    "action", "id", "title", "organization", "year", "url", "identifiers",
    "remove_url", "remove_identifiers", "discovery", "thematic_group_ids",
})

PARTITION_FOR_GROUP = {
    "thematic-group-mathematics": "mathematics.yaml",
    "thematic-group-optimization": "optimization.yaml",
    "thematic-group-machine-learning": "machine-learning.yaml",
    "thematic-group-ml-systems": "ml-systems.yaml",
    "thematic-group-data-systems": "data-systems.yaml",
    "thematic-group-algorithms": "algorithms.yaml",
    "thematic-group-software": "software.yaml",
    "thematic-group-method-admin": "method-admin.yaml",
}
SUBJECT_PARTITIONS = frozenset(PARTITION_FOR_GROUP.values())


def _normalize_link(url: str) -> str:
    """A stable comparison form for taught-object identity, not a judgment.

    Scheme and host casefold, the fragment drops, one trailing slash drops.
    Anything that is not an http(s) URL compares as its own stripped text.
    """
    text = url.strip()
    try:
        parts = urlsplit(text)
    except ValueError:
        return text
    if parts.scheme.lower() not in ("http", "https") or not parts.hostname:
        return text
    path = parts.path.rstrip("/") or ""
    query = f"?{parts.query}" if parts.query else ""
    return f"{parts.scheme.lower()}://{parts.hostname.lower()}{path}{query}"

def _registry_link_index(repo) -> dict[str, tuple[str, str]]:
    """Every held address in normalized form -> (source id, where)."""
    index: dict[str, tuple[str, str]] = {}
    for sid in sorted(repo.sources):
        record = repo.sources[sid]
        url = record.get("url")
        if isinstance(url, str) and url.strip():
            index.setdefault(_normalize_link(url), (sid, "url"))
        identifiers = record.get("identifiers") or {}
        if isinstance(identifiers, dict):
            for label in sorted(identifiers):
                address = identifiers[label]
                if isinstance(address, str) and address.strip():
                    index.setdefault(
                        _normalize_link(address), (sid, f"identifiers.{label}"))
    return index

def _cited_elsewhere(root: Path, url: str, exclude: set[Path]) -> str | None:
    """First canonical file citing the exact URL, outside the files rewritten.

    Mirrors the validator's canonical-text walk (Markdown/YAML only, Garden
    and quarantine excluded): a route locator, stage resource or note that
    cites the address keeps it alive, and intake refuses to remove it.
    """
    for tree in CANONICAL_TREES:
        base = root / tree
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if path.suffix.lower() not in (".md", ".yaml", ".yml") \
                    or not path.is_file():
                continue
            try:
                relative = path.resolve().relative_to(root.resolve())
            except (OSError, ValueError):
                continue
            if relative.parts[:2] == ("knowledge", "garden") \
                    or "quarantine" in relative.parts:
                continue
            if path.resolve() in exclude:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if url in text:
                return relative.as_posix()
    return None

def _refuse_outside_allowlist(item: dict, allowed: frozenset[str], sid: str) -> None:
    for field in sorted(set(item) - allowed):
        if field in CREATE_FIELDS:
            raise WriteRefused(f"{sid}: field '{field}' is create-only")
        raise WriteRefused(
            f"{sid}: field '{field}' is outside the intake allowlist "
            "(evaluations, topics, material, routes, selections, notes, "
            "feedback and observations are never written through intake)"
        )

def _require_text(item: dict, field: str, sid: str) -> str:
    value = item.get(field)
    if not isinstance(value, str) or not value.strip():
        raise WriteRefused(f"{sid}: '{field}' must be a non-empty string")
    return value

def _plan_one(root: Path, repo, item: Any, index: int,
              planned: dict[str, tuple[str, str]]) -> tuple[dict, dict, Path]:
    """Validate one intake row; return (record, diff-row, destination)."""
    tag = f"records[{index}]"
    if not isinstance(item, dict):
        raise WriteRefused(f"{tag} must be an object")
    action = item.get("action")
    if action not in ("create", "correct"):
        raise WriteRefused(f"{tag}: 'action' must be 'create' or 'correct'")
    sid = item.get("id")
    if not isinstance(sid, str) or not SOURCE_ID.match(sid):
        raise WriteRefused(
            f"{tag}: 'id' must match source-<slug> "
            "(prospective candidate-source-* ids are never registered as active)"
        )
    known = repo.sources.get(sid)
    if action == "create":
        if known is not None:
            raise WriteRefused(f"{sid}: already registered (existing)")
        _refuse_outside_allowlist(item, CREATE_FIELDS, sid)
        title = _require_text(item, "title", sid)
        kind = item.get("type")
        if kind not in SOURCE_TYPES:
            raise WriteRefused(f"{sid}: 'type' must be one of {sorted(SOURCE_TYPES)}")
        discovery = item.get("discovery")
        if not isinstance(discovery, dict):
            raise WriteRefused(f"{sid}: create needs 'discovery' provenance")
        partition = item.get("partition")
        groups = item.get("thematic_group_ids", [])
        if not isinstance(groups, list) or any(not isinstance(g, str) for g in groups):
            raise WriteRefused(f"{sid}: 'thematic_group_ids' must be a list of ids")
        for gid in groups:
            if gid not in repo.thematic_groups:
                raise WriteRefused(f"{sid}: thematic group '{gid}' is not registered")
        if groups:
            allowed = sorted({PARTITION_FOR_GROUP[g] for g in groups})
            if partition not in allowed:
                raise WriteRefused(
                    f"{sid}: partition '{partition}' does not match its groups "
                    f"(expected one of {allowed})"
                )
        elif partition not in SUBJECT_PARTITIONS and partition != "sources.yaml":
            raise WriteRefused(
                f"{sid}: unclassified partition '{partition}' must be "
                "'sources.yaml' or a subject partition "
                f"({', '.join(sorted(SUBJECT_PARTITIONS))})"
            )
        if not isinstance(partition, str):
            raise WriteRefused(f"{sid}: create needs a 'partition' file")
        record: dict[str, Any] = {"id": sid, "title": title, "type": kind}
        for field in ("authors", "organization", "year", "url", "identifiers",
                      "discovery", "thematic_group_ids"):
            if item.get(field) is not None:
                record[field] = item[field]
        destination = (root / "sources" / "sources.yaml"
                       if partition == "sources.yaml"
                       else root / "sources" / "registry" / partition)
        before: dict[str, Any] = {}
    else:
        if known is None:
            raise WriteRefused(f"{sid}: correcting an unknown id")
        _refuse_outside_allowlist(item, CORRECT_FIELDS, sid)
        record = dict(known)
        url = item.get("url")
        remove_url = item.get("remove_url", False)
        if url is not None and remove_url:
            raise WriteRefused(f"{sid}: 'url' is both replaced and removed")
        if remove_url is True:
            if not record.get("url"):
                raise WriteRefused(f"{sid}: no 'url' held to remove")
        elif remove_url not in (False, None):
            raise WriteRefused(f"{sid}: 'remove_url' must be true to remove")
        remove_labels = item.get("remove_identifiers", [])
        if not isinstance(remove_labels, list) \
                or any(not isinstance(label, str) for label in remove_labels):
            raise WriteRefused(f"{sid}: 'remove_identifiers' must be a list of labels")
        held = record.get("identifiers") or {}
        if not isinstance(held, dict):
            raise WriteRefused(f"{sid}: existing identifiers are not a mapping")
        for label in remove_labels:
            if label not in held:
                raise WriteRefused(f"{sid}: identifiers label '{label}' is not held")
        incoming = item.get("identifiers") or {}
        if not isinstance(incoming, dict):
            raise WriteRefused(f"{sid}: 'identifiers' must be a label->address mapping")
        for label in remove_labels:
            if label in incoming:
                raise WriteRefused(f"{sid}: identifiers label '{label}' is both set and removed")
        for field in ("title", "organization", "year", "url", "discovery",
                      "thematic_group_ids"):
            if item.get(field) is not None:
                record[field] = item[field]
        if incoming:
            merged = dict(held)
            merged.update(incoming)
            record["identifiers"] = merged
        if remove_labels:
            kept = {label: address for label, address in record["identifiers"].items()
                    if label not in set(remove_labels)}
            if kept:
                record["identifiers"] = kept
            else:
                record.pop("identifiers", None)
        if remove_url is True:
            record.pop("url", None)
        groups = record.get("thematic_group_ids", [])
        if not isinstance(groups, list) or any(not isinstance(g, str) for g in groups):
            raise WriteRefused(f"{sid}: 'thematic_group_ids' must be a list of ids")
        for gid in groups:
            if gid not in repo.thematic_groups:
                raise WriteRefused(f"{sid}: thematic group '{gid}' is not registered")
        old_groups = known.get("thematic_group_ids", [])
        old_discovery = known.get("discovery")
        if (isinstance(old_discovery, dict) and groups != old_groups
                and "thematic_group_ids" in item):
            new_basis = record.get("discovery")
            old_pairs = {(b.get("kind"), b.get("ref"))
                         for b in (old_discovery.get("basis") or [])
                         if isinstance(b, dict)}
            new_pairs = {(b.get("kind"), b.get("ref"))
                         for b in ((new_basis or {}).get("basis") or [])
                         if isinstance(b, dict)} if isinstance(new_basis, dict) else set()
            if not (new_pairs - old_pairs):
                raise WriteRefused(
                    f"{sid}: correcting the shelf of a discovered source "
                    "needs a new discovery basis item"
                )
        origin = repo.source_origins.get(sid)
        destination = Path(origin) if origin else root / "sources" / "sources.yaml"
        before = known
    try:
        validate_contract(root, "sources.schema.json", {"sources": [record]})
    except ValueError as exc:
        raise WriteRefused(f"{sid}: {exc}") from exc
    titles = (record.get("discovery") or {}).get("child_titles") or {}
    labels = record.get("identifiers") or {}
    for label in sorted(titles):
        if label not in labels:
            raise WriteRefused(
                f"{sid}: discovery.child_titles key '{label}' "
                "has no matching identifiers label"
            )
    added: list[str] = []
    if action == "create":
        if isinstance(record.get("url"), str):
            added.append(record["url"])
        for address in (record.get("identifiers") or {}).values():
            if isinstance(address, str):
                added.append(address)
    else:
        if item.get("url") is not None and item.get("url") != before.get("url"):
            added.append(item["url"])
        for label, address in incoming.items():
            if held.get(label) != address and isinstance(address, str):
                added.append(address)
    link_index = _registry_link_index(repo)
    for raw in added:
        holder, where = link_index.get(_normalize_link(raw), (None, ""))
        if holder is not None and holder != sid:
            raise WriteRefused(
                f"{sid}: address {raw} is already held by '{holder}' ({where})"
            )
        earlier = planned.get(_normalize_link(raw))
        if earlier is not None and earlier[0] != sid:
            raise WriteRefused(
                f"{sid}: address {raw} is also added by '{earlier[0]}' in this batch"
            )
        planned[_normalize_link(raw)] = (sid, raw)
    if action == "correct":
        removed: list[str] = []
        if remove_url is True and isinstance(before.get("url"), str):
            removed.append(before["url"])
        for label in remove_labels:
            address = held.get(label)
            if isinstance(address, str):
                removed.append(address)
        exclude = {destination.resolve()} if destination.exists() else set()
        for raw in removed:
            cite = _cited_elsewhere(root, raw, exclude)
            if cite is not None:
                raise WriteRefused(
                    f"{sid}: cannot remove {raw} — still cited by {cite}"
                )
        keeps_link = isinstance(record.get("url"), str) \
            or any(isinstance(a, str) for a in (record.get("identifiers") or {}).values()) \
            or isinstance(record.get("material"), str)
        if removed and not keeps_link:
            raise WriteRefused(
                f"{sid}: removal would leave no reachable locator "
                "(url, identifiers address, or material)"
            )
    tracked = [f for f in
               ("title", "type", "authors", "organization", "year", "url",
                "identifiers", "discovery", "thematic_group_ids")
               if f in record or f in before]
    fields = {}
    for field in tracked:
        old, new = before.get(field), record.get(field)
        if old != new:
            fields[field] = {"before": old, "after": new}
    if action == "correct" and not fields:
        raise WriteRefused(f"{sid}: no intake field changes")
    try:
        filename = destination.resolve().relative_to(
            (root / "sources").resolve()).as_posix()
    except ValueError:
        filename = destination.name
    diff_row = {"id": sid, "action": action, "partition": filename, "fields": fields}
    return record, diff_row, destination


def _plan_source_intake(root: Path, repo, items: Any) -> dict:
    """Validate a batch and render its diff, writes and guards.

    Moved from ``commands.source_catalog._plan_intake`` for its
    conversion (SPEC (bs) item 1): the repository now arrives as a
    parameter (``ctx.repo()`` at the call sites) instead of a fresh
    ``load_repo``.
    """
    if not isinstance(items, list) or not items:
        raise WriteRefused("intake payload needs a non-empty 'records' list")
    if len(items) > MAX_BATCH:
        raise WriteRefused(
            f"batch of {len(items)} exceeds the {MAX_BATCH}-record bound "
            "(one transaction and one receipt stay reviewable)"
        )
    planned: dict[str, tuple[str, str]] = {}
    diff = []
    per_file: dict[Path, dict[str, dict]] = {}
    seen: set[str] = set()
    for position, item in enumerate(items):
        record, row, destination = _plan_one(root, repo, item, position, planned)
        if record["id"] in seen:
            raise WriteRefused(f"{record['id']}: named twice in one batch")
        seen.add(record["id"])
        diff.append(row)
        per_file.setdefault(destination, {})[record["id"]] = record
    writes: dict[Path, str] = {}
    for destination, changed in per_file.items():
        if destination.exists():
            try:
                current = yaml.safe_load(destination.read_text(encoding="utf-8"))
            except (OSError, yaml.YAMLError) as exc:
                raise WriteRefused(f"cannot re-read {destination}: {exc}") from exc
            if not isinstance(current, dict) or not isinstance(current.get("sources"), list):
                raise WriteRefused(f"{destination} is not a source registry file")
            kept = [entry for entry in current["sources"]
                    if not (isinstance(entry, dict) and entry.get("id") in changed)]
            order = [entry.get("id") for entry in current["sources"]
                     if isinstance(entry, dict) and entry.get("id") in changed]
            merged = kept + [changed[sid] for sid in order
                             if sid in changed]
            merged += [changed[sid] for sid in sorted(changed) if sid not in set(order)]
            document = {"sources": merged}
        else:
            document = {"sources": [changed[sid] for sid in sorted(changed)]}
        writes[destination] = _dump_yaml(document)
    canonical = json.dumps(diff, sort_keys=True, ensure_ascii=False).encode("utf-8")
    artifact_ids = sorted(seen)
    return {
        "diff": diff,
        "diff_sha256": "sha256:" + hashlib.sha256(canonical).hexdigest(),
        "writes": writes,
        "artifact_ids": artifact_ids,
        "expected_revisions": {sid: artifact_revision(root, sid) for sid in artifact_ids},
    }


@register("source.intake.record", kind="command")
def source_intake_record(ctx: OpContext, req: dict) -> Result:
    """Create metadata-only sources or correct intake-owned fields, atomically."""
    root = ctx.root
    repo = ctx.repo()
    try:
        data = _input_record(req, "intake records")
        plan = _plan_source_intake(root, repo, data.get("records"))
    except WriteRefused as exc:
        message = str(exc)
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.bad-records",
            gateway_message=json.dumps({"ok": False, "error": message}),
            exit_code=2,
        ) from exc
    if req.get("check") is True:
        return Result(
            {
                "ok": True, "check": True, "records": len(plan["diff"]),
                "diff": plan["diff"], "diff_sha256": plan["diff_sha256"],
                "expected_revisions": plan["expected_revisions"],
                "artifact_ids": plan["artifact_ids"],
            },
            json_dumps=_dumps_indented,
        )
    if not req.get("approve"):
        message = "source intake requires explicit approval"
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.needs-approval",
            gateway_message=json.dumps({"ok": False, "error": message}),
            exit_code=2,
        )
    _require_gateway_v2()
    try:
        plan = _plan_source_intake(root, repo, data.get("records"))
    except WriteRefused as exc:
        message = str(exc)
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.bad-records",
            gateway_message=json.dumps({"ok": False, "error": message}),
            exit_code=2,
        ) from exc
    expected_diff = req.get("expected_diff_sha256")
    if not expected_diff:
        message = "apply needs --expected-diff-sha256 from a check run"
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.needs-expected-diff",
            gateway_message=json.dumps({"ok": False, "error": message}),
            exit_code=2,
        )
    if expected_diff != plan["diff_sha256"]:
        message = "intake diff changed since check; re-run --check"
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.diff-changed",
            gateway_message=json.dumps({"ok": False, "error": message}),
            exit_code=2,
        )
    ctx.require_snapshot(req.get("expected_snapshot"))
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site=f"{ctx.operation}.bad-expected-revision",
        ) from exc

    def finish_source_intake_record(confirmation):
        return {"ok": True, **confirmation}

    def refused_stdout_source_intake_record(errors):
        return _dumps_indented({
            "ok": False,
            **({"errors": [str(error) for error in errors]} if errors else {}),
        })

    return Result(
        {"ok": True},
        proposal=TransactionProposal(
            capability="source.intake.record",
            writes=plan["writes"],
            artifact_ids=tuple(plan["artifact_ids"]),
            expected_revisions=expected_revisions,
        ),
        finish=finish_source_intake_record,
        refused_stdout=refused_stdout_source_intake_record,
        json_dumps=_dumps_indented,
    )


# ---------------------------------------------------------------------------
# Source-record-revise planning, moved verbatim from commands.source_catalog
# with its converting handler (SPEC (bs) item 1).


# What a source-record revision may carry. `material` attaches verified local
# bytes to a source that holds none; `evaluations` is an explicit full
# replacement for a stale judgment. Identity and every intake-owned field stay
# with `source.intake.record`; `material_sha256` is request evidence and is
# never stored on the record (the materials manifest owns hashes).
# `material_syntheses` carries reviewed replacement dossiers for exactly the
# units whose approved dossier basis the new material moves.
REVISE_FIELDS = frozenset({"id", "material", "material_sha256", "evaluations",
                           "material_syntheses", "dossier_rebases"})
# Intake's create/correct vocabulary minus identity keys (frozen from the intake
# allowlists, which now live with the converted `source.intake.record`
# handler): revise refuses these with an intake pointer instead of its own
# unknown-field complaint.
INTAKE_OWNED_FIELDS = frozenset({
    "partition", "title", "type", "authors", "organization", "year", "url",
    "identifiers", "remove_url", "remove_identifiers", "discovery",
    "thematic_group_ids",
})
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


def _refuse_outside_revise_allowlist(item: dict, sid: str) -> None:
    for field in sorted(set(item) - REVISE_FIELDS):
        if field in INTAKE_OWNED_FIELDS:
            raise WriteRefused(f"{sid}: field '{field}' is owned by intake")
        raise WriteRefused(
            f"{sid}: field '{field}' is outside the revise allowlist "
            "(only 'material' and 'evaluations' are revised here; identity, "
            "intake-owned fields, topics, routes, selections, notes, feedback "
            "and observations are never written through revision)"
        )

def _resolve_revise_material(root: Path, repo, uri: str,
                             sid: str) -> tuple[str, str, int]:
    """Resolve a requested material URI to (manifest key, live sha256, size).

    Resolution follows the runtime exactly (materials_resolution.
    material_location): id-form URIs through ``repo.materials_root`` — the
    .flat/ alias farm when it exists — with no physical-form fallback, so a
    link the learner could not open is refused here instead of recorded. A
    folder-level reference has no single hashable byte string, so only one
    concrete file is attachable.
    """
    authority = material_uri_authority(uri)
    if authority is None:
        raise WriteRefused(f"{sid}: '{uri}' is not a safe material:// URI")
    if authority != sid:
        raise WriteRefused(
            f"{sid}: material URI authority '{authority}' must equal the source id"
        )
    canonical = canonical_material_uri(uri)
    if canonical is not None and canonical != uri:
        raise WriteRefused(
            f"{sid}: '{uri}' is not the canonical material spelling; "
            f"use '{canonical}'"
        )
    payload = str(uri)[len(MATERIAL_SCHEME):]
    physical = repo.learningos_root / "materials"
    if physical.is_symlink() or not physical.is_dir():
        raise WriteRefused(
            f"{sid}: materials tree not mounted at {physical} — attach needs "
            "the live bytes, not just the URI"
        )
    try:
        resolved = resolve_symlinks_inside(
            physical, repo.materials_root / payload, strict=False)
        relative = resolved.relative_to(physical)
    except (OSError, PathBoundaryError, ValueError):
        raise WriteRefused(
            f"{sid}: '{uri}' does not resolve to a file in the materials tree"
        ) from None
    if resolved.is_dir():
        raise WriteRefused(
            f"{sid}: '{uri}' must resolve to one file, not a directory"
        )
    if not resolved.is_file():
        raise WriteRefused(
            f"{sid}: '{uri}' does not resolve to a file in the materials tree"
        )
    digest = sha256_file(resolved)
    live = digest[len("sha256:"):] if digest.startswith("sha256:") else digest
    return relative.as_posix(), live, resolved.stat().st_size

def _read_unit_dossier(path: Path, sid: str, uid: str) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise WriteRefused(f"{sid}: cannot read the dossier for '{uid}': {exc}") from exc
    if not isinstance(data, dict):
        raise WriteRefused(f"{sid}: dossier for '{uid}' is not a mapping")
    return data

def _read_dossier_status(path: Path, sid: str, uid: str):
    return _read_unit_dossier(path, sid, uid).get("status")

def _dossier_digest(data: dict) -> str:
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()

def _rebase_routes_or_refuse(sid: str, uid: str, live_basis: dict,
                             staged_basis: dict, by_route: dict,
                             comparisons: list,
                             requested_ids: list) -> list[dict]:
    """Changed routes eligible for the dossier rebase shortcut, else refused.

    The shortcut is deliberately narrow: only `material_checksums` may move,
    and every moved route must be screened, evidence-free, analysis-free and
    outside every comparison. Anything else keeps the full reviewed
    replacement path, where a human re-examines the changed evidence.
    """
    for field in _COMPARED_BASIS_FIELDS:
        if field == "material_checksums":
            continue
        if live_basis.get(field) != staged_basis.get(field):
            raise WriteRefused(
                f"{sid}: unit '{uid}' moves '{field}' too — the rebase shortcut "
                "covers only material_checksums; use a full reviewed replacement"
            )
    live_sums = live_basis.get("material_checksums") or {}
    staged_sums = staged_basis.get("material_checksums") or {}
    if set(live_sums) != set(staged_sums):
        raise WriteRefused(
            f"{sid}: unit '{uid}' gains or loses checksummed routes — use a "
            "full reviewed replacement"
        )
    changed = sorted(rid for rid in live_sums if live_sums[rid] != staged_sums[rid])
    if sorted(requested_ids) != changed:
        raise WriteRefused(
            f"{sid}: unit '{uid}' rebase names route_ids {sorted(requested_ids)} "
            f"but the attach moves {changed}; name exactly the moved routes"
        )
    compared: set[str] = set()
    for comparison in comparisons:
        if isinstance(comparison, dict):
            compared.add(comparison.get("left_route_id"))
            compared.add(comparison.get("right_route_id"))
    moved = []
    for rid in changed:
        if rid in compared:
            raise WriteRefused(
                f"{sid}: unit '{uid}' route '{rid}' appears in a comparison — "
                "its narrative may depend on the old material; use a full "
                "reviewed replacement"
            )
        assessment = by_route.get(rid) or {}
        status = assessment.get("review_status")
        if status != "screened":
            raise WriteRefused(
                f"{sid}: unit '{uid}' route '{rid}' is not screened "
                f"({status or 'no status'}) — use a full reviewed replacement"
            )
        if assessment.get("evidence"):
            raise WriteRefused(
                f"{sid}: unit '{uid}' route '{rid}' carries evidence bound to "
                "the old material; use a full reviewed replacement"
            )
        if assessment.get("analysis_refs"):
            raise WriteRefused(
                f"{sid}: unit '{uid}' route '{rid}' carries analysis references "
                "bound to the old material; use a full reviewed replacement"
            )
        moved.append({"route_id": rid, "before": live_sums[rid],
                      "after": staged_sums[rid],
                      "reason": assessment.get("reason")})
    return moved

def _source_referrers(repo, sid: str) -> dict:
    """Every route, dossier and collection entry naming this source.

    Evidence for the reviewer; the basis comparison in `_plan_revise`
    decides which dossiers the new material actually moves, and collection
    entries are listed so a stale operational claim is noticed — this
    operation never rewrites collection content itself.
    """
    routes = []
    for mid in sorted(repo.module_source_maps or {}):
        entries = (repo.module_source_maps[mid] or {}).get("sources") or []
        for entry in entries:
            if not isinstance(entry, dict) or entry.get("source_id") != sid:
                continue
            for route in entry.get("unit_routes") or []:
                if isinstance(route, dict) and route.get("id"):
                    routes.append({
                        "module_id": mid, "unit_id": route.get("unit_id"),
                        "route_id": route.get("id"),
                    })
    routes.sort(key=lambda row: (row["module_id"], row["unit_id"] or "",
                                 row["route_id"]))
    dossiers = set()
    for row in routes:
        unit = (repo.units or {}).get(row["unit_id"])
        path = getattr(unit, "path", None)
        if path is not None and (path.parent / "material-synthesis.yaml").is_file():
            dossiers.add(row["unit_id"])
    collections = []
    for stem in sorted(repo.collections or {}):
        doc = repo.collections[stem] or {}
        for entry in doc.get("entries") or []:
            if isinstance(entry, dict) and entry.get("source") == sid:
                collections.append({"collection": stem,
                                    "group": entry.get("group"),
                                    "why": entry.get("why")})
    return {"routes": routes, "dossiers": sorted(dossiers),
            "collections": collections}


def _plan_source_record_revise(root: Path, repo, item: Any) -> dict:
    """Validate one source-record revision; return its diff, writes, guards.

    Moved from ``commands.source_catalog._plan_revise`` for its
    conversion (SPEC (bs) item 1): the repository now arrives as a
    parameter (``ctx.repo()`` at the call sites) instead of a fresh
    ``load_repo``.
    """
    if not isinstance(item, dict):
        raise WriteRefused("revise payload must be an object")
    sid = item.get("id")
    if not isinstance(sid, str) or not SOURCE_ID.match(sid):
        raise WriteRefused("'id' must match source-<slug>")
    known = repo.sources.get(sid)
    if known is None:
        raise WriteRefused(f"{sid}: revising an unknown source")
    _refuse_outside_revise_allowlist(item, sid)
    record = dict(known)
    if "material" in item:
        uri = item["material"]
        if not isinstance(uri, str) or not uri.strip():
            raise WriteRefused(f"{sid}: 'material' must be a non-empty string")
        if uri != known.get("material"):
            if known.get("material") is not None:
                raise WriteRefused(
                    f"{sid}: already holds {known['material']} — replacing a "
                    "material binding is not supported; it would orphan every "
                    "route and dossier resolved against those bytes"
                )
            want = item.get("material_sha256")
            if not isinstance(want, str) or not _SHA256_HEX.match(want):
                raise WriteRefused(
                    f"{sid}: a material change needs 'material_sha256' as "
                    "64 lowercase hex"
                )
            key, live, _size = _resolve_revise_material(root, repo, uri, sid)
            manifest_path = root / "records" / "materials-manifest.yaml"
            try:
                manifest = yaml.safe_load(
                    manifest_path.read_text(encoding="utf-8")) or {}
            except (OSError, yaml.YAMLError):
                manifest = {}
            recorded = manifest.get("files") or {}
            want_row = None
            for row_key, row in recorded.items():
                if (isinstance(row_key, str) and isinstance(row, dict)
                        and unicodedata.normalize("NFC", row_key)
                        == unicodedata.normalize("NFC", key)):
                    want_row = row
                    break
            if want_row is None:
                raise WriteRefused(
                    f"{sid}: '{key}' is absent from the materials manifest — "
                    "run `make inventory` before attaching it"
                )
            if want_row.get("sha256") != live:
                raise WriteRefused(
                    f"{sid}: live bytes of '{key}' do not match the manifest "
                    "entry — rebuild it (`make inventory`) before attaching"
                )
            if live != want:
                raise WriteRefused(
                    f"{sid}: live bytes of '{key}' do not match the request hash"
                )
            record["material"] = uri
    elif "material_sha256" in item:
        raise WriteRefused(f"{sid}: 'material_sha256' without a 'material' change")
    if "evaluations" in item:
        evaluations = item["evaluations"]
        if not isinstance(evaluations, list):
            raise WriteRefused(f"{sid}: 'evaluations' must be a list of evaluation mappings")
        for position, evaluation in enumerate(evaluations):
            sections = (evaluation.get("useful_sections")
                        if isinstance(evaluation, dict) else None)
            if sections is not None and not isinstance(sections, list):
                raise WriteRefused(f"{sid}: evaluations[{position}].useful_sections must be a list")
            for entry in sections or []:
                if isinstance(entry, dict) and ({"locator", "use"} & set(entry)):
                    raise WriteRefused(
                        f"{sid}: evaluations[{position}].useful_sections uses "
                        "'locator'/'use' pseudo-fields — write one "
                        "section-to-note pair per object instead, e.g. "
                        "{'§4.1, physical PDF pp. 141–149': 'Discrete "
                        "conditioning, reversed urn tree, ...'}"
                    )
        record["evaluations"] = item["evaluations"]
    try:
        validate_contract(root, "sources.schema.json", {"sources": [record]})
    except ValueError as exc:
        raise WriteRefused(f"{sid}: {exc}") from exc
    fields = {}
    for field in ("material", "evaluations"):
        old, new = known.get(field), record.get(field)
        if old != new:
            fields[field] = {"before": old, "after": new}
    if not fields:
        raise WriteRefused(f"{sid}: no source-record changes")
    refers = _source_referrers(repo, sid)
    # Routes without their own vault_path inherit this record's material, so an
    # attach can move a dossier's basis without touching any route (SaD L04).
    # Freshness is therefore computed against the PROPOSED record; every unit
    # whose approved basis moves must ship a reviewed replacement validated
    # against that staged state — or a reviewed rebase when the shortcut's
    # strict conditions hold — in this same transaction.
    affected: list[str] = []
    replacements: dict[str, dict] = {}
    rebased: dict[str, dict] = {}
    dossier_writes: dict[Path, str] = {}
    dossier_publications: list[tuple[str, dict, str]] = []
    if "material" in fields:
        syntheses = item.get("material_syntheses", [])
        if not isinstance(syntheses, list):
            raise WriteRefused(f"{sid}: 'material_syntheses' must be a list")
        requested: dict[str, dict] = {}
        for position, entry in enumerate(syntheses):
            where = f"material_syntheses[{position}]"
            if not isinstance(entry, dict) or set(entry) != {"unit_id", "dossier"}:
                raise WriteRefused(f"{where} needs exactly unit_id and dossier")
            uid, dossier = entry["unit_id"], entry["dossier"]
            if not isinstance(uid, str) or not isinstance(dossier, dict):
                raise WriteRefused(f"{where} needs a unit id and a dossier mapping")
            if uid in requested:
                raise WriteRefused(f"{where} replaces '{uid}' twice")
            requested[uid] = dossier
        rebases = item.get("dossier_rebases", [])
        if not isinstance(rebases, list):
            raise WriteRefused(f"{sid}: 'dossier_rebases' must be a list")
        requested_rebases: dict[str, dict] = {}
        for position, entry in enumerate(rebases):
            where = f"dossier_rebases[{position}]"
            if not isinstance(entry, dict) or set(entry) != {
                    "unit_id", "dossier_digest", "route_ids", "provenance"}:
                raise WriteRefused(
                    f"{where} needs exactly unit_id, dossier_digest, "
                    "route_ids and provenance"
                )
            uid, digest, rids, provenance = (
                entry["unit_id"], entry["dossier_digest"],
                entry["route_ids"], entry["provenance"])
            if not isinstance(uid, str):
                raise WriteRefused(f"{where} needs a unit id")
            if not isinstance(digest, str) or not digest:
                raise WriteRefused(f"{where} needs the current dossier digest")
            if (not isinstance(rids, list) or not rids
                    or not all(isinstance(rid, str) for rid in rids)):
                raise WriteRefused(
                    f"{where} 'route_ids' must be a non-empty list of route ids"
                )
            if (not isinstance(provenance, dict)
                    or not all(isinstance(provenance.get(key), str)
                               and provenance.get(key)
                               for key in ("request_id", "delivery_id",
                                           "provider"))):
                raise WriteRefused(
                    f"{where} 'provenance' must carry request_id, "
                    "delivery_id and provider"
                )
            if uid in requested_rebases:
                raise WriteRefused(f"{where} rebases '{uid}' twice")
            requested_rebases[uid] = entry
        staged = copy.copy(repo)
        staged.sources = {**repo.sources, sid: record}
        required: list[str] = []
        bases: dict[str, tuple[dict, dict]] = {}
        for uid in refers["dossiers"]:
            unit = (repo.units or {}).get(uid)
            if unit is None or getattr(unit, "path", None) is None:
                raise WriteRefused(f"{sid}: unit '{uid}' is not registered")
            try:
                live_basis = current_unit_material_basis(root, uid, repo=repo, cache={})
                staged_basis = current_unit_material_basis(root, uid, repo=staged, cache={})
            except MaterialSynthesisError as exc:
                raise WriteRefused(
                    f"{sid}: cannot establish the dossier basis for '{uid}': {exc}"
                ) from exc
            if any(live_basis[field] != staged_basis[field]
                   for field in _COMPARED_BASIS_FIELDS):
                affected.append(uid)
                bases[uid] = (live_basis, staged_basis)
                dossier_path = unit.path.parent / "material-synthesis.yaml"
                if _read_dossier_status(dossier_path, sid, uid) == "approved":
                    required.append(uid)
        for uid in requested:
            if uid not in required:
                raise WriteRefused(
                    f"{sid}: replacement dossier for '{uid}' is not needed "
                    "(no approved dossier basis changes there)"
                )
        for uid in requested_rebases:
            if uid in requested:
                raise WriteRefused(
                    f"{sid}: unit '{uid}' takes only one of "
                    "'material_syntheses' and 'dossier_rebases'"
                )
            if uid not in required:
                unit = (repo.units or {}).get(uid)
                if unit is None:
                    raise WriteRefused(
                        f"{sid}: unit '{uid}' is not registered"
                    )
                unit_path = getattr(unit, "path", None)
                dossier_path = (unit_path.parent / "material-synthesis.yaml"
                                if unit_path is not None else None)
                if dossier_path is not None and not dossier_path.exists():
                    raise WriteRefused(
                        f"{sid}: rebase for '{uid}' has no dossier to rebase "
                        "(no material-synthesis.yaml there)"
                    )
                raise WriteRefused(
                    f"{sid}: rebase for '{uid}' is not needed "
                    "(no approved dossier basis changes there)"
                )
        for uid in required:
            if uid not in requested and uid not in requested_rebases:
                raise WriteRefused(
                    f"{sid}: attaching material changes the approved dossier "
                    f"basis for '{uid}'; supply a reviewed replacement dossier "
                    "under 'material_syntheses' or a rebase under "
                    "'dossier_rebases'"
                )
        for uid in sorted(requested):
            try:
                validate_unit_material_synthesis(root, uid, requested[uid], repo=staged)
            except MaterialSynthesisError as exc:
                raise WriteRefused(
                    f"{sid}: replacement dossier for '{uid}' is not valid: {exc}"
                ) from exc
            unit = repo.units[uid]
            dossier_path = unit.path.parent / "material-synthesis.yaml"
            live_provenance = (
                _read_unit_dossier(dossier_path, sid, uid).get("basis") or {}
            ).get("ai_provenance")
            submitted = (requested[uid].get("basis") or {}).get("ai_provenance")
            if submitted == live_provenance:
                raise WriteRefused(
                    f"{sid}: replacement dossier for '{uid}' reuses the live "
                    "dossier's provenance unchanged — stamp the reviewed "
                    "replacement with its own request_id/delivery_id "
                    "(provenance must identify the event that produced the "
                    "new basis, as the publish gate requires)"
                )
            dossier_writes[dossier_path] = _dump_yaml(requested[uid])
            dossier_publications.append((uid, requested[uid], dossier_writes[dossier_path]))
        replacements = {uid: requested[uid] for uid in sorted(requested)}
        for uid in sorted(requested_rebases):
            entry = requested_rebases[uid]
            unit = repo.units[uid]
            dossier_path = unit.path.parent / "material-synthesis.yaml"
            live_dossier = _read_unit_dossier(dossier_path, sid, uid)
            if _dossier_digest(live_dossier) != entry["dossier_digest"]:
                raise WriteRefused(
                    f"{sid}: dossier for '{uid}' changed since the rebase was "
                    "prepared; re-run --check"
                )
            live_provenance = (live_dossier.get("basis") or {}).get("ai_provenance")
            if entry["provenance"] == live_provenance:
                raise WriteRefused(
                    f"{sid}: rebase for '{uid}' reuses the live dossier's "
                    "provenance unchanged — stamp the rebase with its own "
                    "request_id/delivery_id (provenance must identify the "
                    "event that produced the new basis, as the publish gate "
                    "requires)"
                )
            by_route = {row["route_id"]: row
                        for row in live_dossier.get("route_assessments", []) or []
                        if isinstance(row, dict) and row.get("route_id")}
            live_basis, staged_basis = bases[uid]
            moved = _rebase_routes_or_refuse(
                sid, uid, live_basis, staged_basis, by_route,
                live_dossier.get("comparisons", []) or [],
                entry["route_ids"])
            try:
                validate_unit_material_synthesis(root, uid, live_dossier, repo=repo)
            except MaterialSynthesisError as exc:
                raise WriteRefused(
                    f"{sid}: dossier for '{uid}' is already stale: {exc}; use "
                    "a full reviewed replacement"
                ) from exc
            rebased_dossier = copy.deepcopy(live_dossier)
            rebased_dossier["basis"] = {
                **staged_basis, "ai_provenance": entry["provenance"]}
            try:
                validate_unit_material_synthesis(root, uid, rebased_dossier, repo=staged)
            except MaterialSynthesisError as exc:
                raise WriteRefused(
                    f"{sid}: rebased dossier for '{uid}' is not valid: {exc}"
                ) from exc
            dossier_writes[dossier_path] = _dump_yaml(rebased_dossier)
            dossier_publications.append((uid, rebased_dossier, dossier_writes[dossier_path]))
            rebased[uid] = {"routes": moved,
                            "dossier_digest": entry["dossier_digest"],
                            "provenance": entry["provenance"]}
    elif "material_syntheses" in item:
        raise WriteRefused(f"{sid}: 'material_syntheses' without a 'material' change")
    elif "dossier_rebases" in item:
        raise WriteRefused(f"{sid}: 'dossier_rebases' without a 'material' change")
    origin = repo.source_origins.get(sid)
    destination = Path(origin) if origin else root / "sources" / "sources.yaml"
    try:
        current = yaml.safe_load(destination.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise WriteRefused(f"cannot re-read {destination}: {exc}") from exc
    if not isinstance(current, dict) or not isinstance(current.get("sources"), list):
        raise WriteRefused(f"{destination} is not a source registry file")
    merged = [record if (isinstance(entry, dict) and entry.get("id") == sid)
              else entry for entry in current["sources"]]
    try:
        filename = destination.resolve().relative_to(
            (root / "sources").resolve()).as_posix()
    except ValueError:
        filename = destination.name
    diff = [{"id": sid, "partition": filename, "fields": fields,
             "refers": refers, "affected_units": affected,
             "replacements": replacements, "rebases": rebased}]
    canonical = json.dumps(diff, sort_keys=True, ensure_ascii=False).encode("utf-8")
    writes = {destination: _dump_yaml({"sources": merged})}
    writes.update(dossier_writes)
    unit_ids = sorted(set(replacements) | set(rebased))
    revisions = {sid: artifact_revision(root, sid)}
    revisions.update({uid: artifact_revision(root, uid) for uid in unit_ids})
    return {
        "diff": diff,
        "diff_sha256": "sha256:" + hashlib.sha256(canonical).hexdigest(),
        "writes": writes,
        "dossier_publications": dossier_publications,
        "artifact_ids": [sid] + unit_ids,
        "expected_revisions": revisions,
    }


@register("source.record.revise", kind="command")
def source_record_revise(ctx: OpContext, req: dict) -> Result:
    """Attach verified local material to one existing source, atomically."""
    root = ctx.root
    repo = ctx.repo()
    try:
        data = _input_record(req, "revise record")
        plan = _plan_source_record_revise(root, repo, data)
    except WriteRefused as exc:
        message = str(exc)
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.bad-record",
            gateway_message=json.dumps({"ok": False, "error": message}),
            exit_code=2,
        ) from exc
    if req.get("check") is True:
        return Result(
            {
                "ok": True, "check": True, "records": len(plan["diff"]),
                "diff": plan["diff"], "diff_sha256": plan["diff_sha256"],
                "expected_revisions": plan["expected_revisions"],
                "artifact_ids": plan["artifact_ids"],
            },
            json_dumps=_dumps_indented,
        )
    if not req.get("approve"):
        message = "source revision requires explicit approval"
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.needs-approval",
            gateway_message=json.dumps({"ok": False, "error": message}),
            exit_code=2,
        )
    _require_gateway_v2()
    try:
        plan = _plan_source_record_revise(root, repo, data)
    except WriteRefused as exc:
        message = str(exc)
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.bad-record",
            gateway_message=json.dumps({"ok": False, "error": message}),
            exit_code=2,
        ) from exc
    expected_diff = req.get("expected_diff_sha256")
    if not expected_diff:
        message = "apply needs --expected-diff-sha256 from a check run"
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.needs-expected-diff",
            gateway_message=json.dumps({"ok": False, "error": message}),
            exit_code=2,
        )
    if expected_diff != plan["diff_sha256"]:
        message = "revision diff changed since check; re-run --check"
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.diff-changed",
            gateway_message=json.dumps({"ok": False, "error": message}),
            exit_code=2,
        )
    ctx.require_snapshot(req.get("expected_snapshot"))
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site=f"{ctx.operation}.bad-expected-revision",
        ) from exc
    if plan["dossier_publications"]:
        records = load_ledger(root)
        request = current_gateway_request()
        for uid, dossier, content in plan["dossier_publications"]:
            claim_id = f"dossier:{dossier['id']}"
            records[claim_id] = publication_lineage_record(
                root, uid, dossier, content, request, prior=records.get(claim_id))
        plan["writes"][root / LEDGER_RELATIVE] = dump_ledger(records)

    def finish_source_record_revise(confirmation):
        return {"ok": True, **confirmation}

    def refused_stdout_source_record_revise(errors):
        return _dumps_indented({
            "ok": False,
            **({"errors": [str(error) for error in errors]} if errors else {}),
        })

    return Result(
        {"ok": True},
        proposal=TransactionProposal(
            capability="source.record.revise",
            writes=plan["writes"],
            artifact_ids=tuple(plan["artifact_ids"]),
            expected_revisions=expected_revisions,
        ),
        finish=finish_source_record_revise,
        refused_stdout=refused_stdout_source_record_revise,
        json_dumps=_dumps_indented,
    )


# ---------------------------------------------------------------------------
# Unit-map-import planning, moved verbatim from commands.unit
# with its converting handler (SPEC (bs) item 2).


# --------------------------------------------------------- map replacement
# Fields a study-map draft does not own. An assembled revision always writes
# `status: pending`, empty attachments and empty feedback, so replacing a map
# with one carries the learner's recorded work away with it. They are carried
# forward from the surviving stage of the same id unless a reviewed reset says
# otherwise.
_PRESERVED_STAGE_STATE = (
    "status",
    "completed",
    "working_note",
    "attachments",
    "source_feedback",
    "detour_id",
)

# The same at map level: lifecycle, the resume pointer, open detours and the
# shelving packet are operational state, not plan content.
_PRESERVED_MAP_STATE = ("status", "current_stage", "detours", "shelving")


def _stage_id_list(map_data: dict) -> list[str]:
    return [
        str(stage.get("id"))
        for stage in (map_data.get("stages") or [])
        if isinstance(stage, dict) and stage.get("id")
    ]

def _relative_order_changed(before: list[str], after: list[str]) -> bool:
    """Whether records present in both sequences changed relative order.

    Adding a stage is not a reorder; moving existing stages around the
    insertion is. Same rule as the module-plan gateway — stated once there and
    mirrored here deliberately, because the two import paths must not offer
    different protections for the same canonical change.
    """
    shared = set(before) & set(after)
    return (
        [record_id for record_id in before if record_id in shared]
        != [record_id for record_id in after if record_id in shared]
    )

def _stage_evidence(root: Path, stage: dict) -> dict:
    """What a stage would take with it if it disappeared from the map."""
    note_ref = str(stage.get("working_note") or "")
    note = root / note_ref if note_ref else None
    note_bytes = 0
    if note is not None and note.is_file():
        try:
            note_bytes = len(note.read_text(encoding="utf-8").strip())
        except OSError:
            note_bytes = -1
    return {
        "stage_id": stage.get("id"),
        "status": stage.get("status"),
        "note_characters": note_bytes,
        "attachments": len(stage.get("attachments") or []),
        "source_feedback": len(stage.get("source_feedback") or []),
        "completed": stage.get("completed"),
    }

def _plan_map_replacement(
    root: Path,
    current: dict,
    incoming: dict,
    *,
    reorder_reason: str | None,
    reset_reason: str | None,
    retire_stage_ids: list[str],
    retire_reason: str | None,
) -> tuple[dict, dict, list[str]]:
    """Merge a reviewed revision onto the map it replaces.

    Returns ``(merged_map, diff, problems)``. ``problems`` being non-empty
    means nothing may be written: a replacement that silently reorders stages,
    resets lifecycle state, or drops a stage carrying recorded work is refused
    rather than applied and reported afterwards.
    """
    problems: list[str] = []
    before = _stage_id_list(current)
    after = _stage_id_list(incoming)
    current_stages = {
        str(stage.get("id")): stage
        for stage in (current.get("stages") or [])
        if isinstance(stage, dict) and stage.get("id")
    }

    retired = [stage_id for stage_id in before if stage_id not in after]
    added = [stage_id for stage_id in after if stage_id not in before]
    declared_retire = list(dict.fromkeys(retire_stage_ids))

    undeclared = [stage_id for stage_id in retired if stage_id not in declared_retire]
    if undeclared:
        problems.append(
            "this revision removes existing stages and their recorded evidence: "
            + ", ".join(undeclared)
            + " — declare each with --retire-stage and give --retire-reason"
        )
    absent = [stage_id for stage_id in declared_retire if stage_id not in retired]
    if absent:
        problems.append(
            "--retire-stage names stages the revision keeps: " + ", ".join(absent)
        )
    if retired and declared_retire and not (retire_reason or "").strip():
        problems.append("--retire-stage requires --retire-reason")

    reordered = _relative_order_changed(before, after)
    if reordered and not (reorder_reason or "").strip():
        problems.append(
            "this revision reorders existing stages; preserve their relative order "
            "or declare --intentional-reorder with a reason"
        )
    if not reordered and (reorder_reason or "").strip():
        problems.append(
            "--intentional-reorder was declared, but this revision does not reorder "
            "existing stages"
        )

    reset = bool((reset_reason or "").strip())
    merged = dict(incoming)
    merged_stages: list[dict] = []
    for stage in incoming.get("stages") or []:
        if not isinstance(stage, dict):
            merged_stages.append(stage)
            continue
        existing = current_stages.get(str(stage.get("id")))
        row = dict(stage)
        if existing is not None and not reset:
            for field in _PRESERVED_STAGE_STATE:
                if field in existing:
                    row[field] = copy.deepcopy(existing[field])
                elif field in row and field not in ("status", "working_note"):
                    row.pop(field, None)
        merged_stages.append(row)
    merged["stages"] = merged_stages

    changed_state: list[str] = []
    if not reset:
        for field in _PRESERVED_MAP_STATE:
            if field not in current:
                continue
            if field == "current_stage":
                continue
            if incoming.get(field) != current.get(field):
                changed_state.append(field)
            merged[field] = copy.deepcopy(current[field])
        pointer = current.get("current_stage")
        if isinstance(pointer, str) and pointer in set(after):
            merged["current_stage"] = pointer
        elif isinstance(pointer, str) and pointer in declared_retire:
            merged["current_stage"] = incoming.get("current_stage")
        elif pointer is not None:
            problems.append(
                f"the resume pointer names {pointer}, which this revision does not "
                "contain; retire it explicitly or keep the stage"
            )
    if merged.get("current_stage") not in set(after):
        problems.append(
            f"current_stage must name a stage in the revision: "
            f"{merged.get('current_stage')!r}"
        )

    dangling = sorted({
        str(detour.get(field))
        for detour in (merged.get("detours") or [])
        if isinstance(detour, dict)
        for field in ("spawned_by_stage", "return_to_stage")
        if isinstance(detour.get(field), str) and detour.get(field) not in set(after)
    })
    if dangling:
        problems.append(
            "preserved detours reference stages this revision does not contain: "
            + ", ".join(dangling)
        )

    diff = {
        "stages_before": before,
        "stages_after": after,
        "stages_added": added,
        "stages_retired": retired,
        "relative_order_changed": reordered,
        "intentional_reorder_reason": (reorder_reason or None),
        "state_reset_reason": (reset_reason or None),
        "retire_reason": (retire_reason or None),
        "preserved_stage_state": [] if reset else sorted(
            set(before) & set(after)
        ),
        "map_state_fields_preserved": [] if reset else sorted(changed_state),
        "resume_stage": merged.get("current_stage"),
        "retired_stage_evidence": [
            _stage_evidence(root, current_stages[stage_id])
            for stage_id in retired
            if stage_id in current_stages
        ],
    }
    return merged, diff, problems


def _on_commit_refused_unit_map_import(errors: list) -> list[str]:
    """The exact commit-refusal lines: the header plus twelve issues."""
    return ["los: study map import rejected by validation",
            *(str(issue) for issue in errors[:12])]


@register("unit.map.import", kind="command")
def unit_map_import(ctx: OpContext, req: dict) -> Result:
    """Create, or revise under preservation rules, the one current study map.

    A first import writes the reviewed draft as given. A ``--replace`` revision
    is a *merge*: the plan content comes from the draft, and the learner's
    recorded work — stage lifecycle, notes, attachments, source feedback, open
    detours, the resume pointer and the shelving packet — is carried forward
    from the map being replaced. Reordering surviving stages, resetting that
    state, and dropping a stage each require their own reviewed declaration,
    so an authorized request can no longer discard operational intent by
    accident. ``--check`` prints the concrete diff and writes nothing.
    """
    root = ctx.root
    try:
        _source, map_bytes = _read_content_bound_file(
            req["file"],
            req.get("file_sha256"),
            label="study-map file",
        )
    except WriteRefused as exc:
        exc.site = f"{ctx.operation}.bad-file"
        exc.gateway_message = f"los: {exc}"
        exc.exit_code = 2
        raise
    check_only = req.get("check") is True
    ctx.require_snapshot(req.get("expected_snapshot"))
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
    target = unit.path.parent / "study-map.yaml"
    if target.exists() and not req.get("replace"):
        message = ("this unit already has a current study map; use --replace "
                   "to make Git the prior-version archive")
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.has-map",
            gateway_message=f"los: {message}",
            exit_code=2,
        )
    try:
        data = yaml.safe_load(map_bytes.decode("utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        message = f"invalid study-map YAML: {exc}"
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.bad-map",
            gateway_message=f"los: {message}",
            exit_code=2,
        ) from exc
    if not isinstance(data, dict) or data.get("unit_id") != req["unit_id"]:
        message = "imported map must be a mapping with the requested unit_id"
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.bad-map",
            gateway_message=f"los: {message}",
            exit_code=2,
        )

    current_map_id = unit.data.get("current_study_map")
    current_map = repo.study_maps.get(current_map_id) if current_map_id else None
    current_data = copy.deepcopy(current_map.data) if current_map is not None else None
    reorder_reason = req.get("intentional_reorder")
    reset_reason = req.get("intentional_state_reset")
    retire_ids = list(req.get("retire_stage") or [])
    retire_reason = req.get("retire_reason")
    diff: dict = {"replacement": current_data is not None}

    if current_data is None:
        for flag, value in (("--intentional-reorder", reorder_reason),
                            ("--intentional-state-reset", reset_reason),
                            ("--retire-stage", retire_ids),
                            ("--retire-reason", retire_reason)):
            if value:
                message = f"{flag} only applies to a replacement of an existing map"
                raise WriteRefused(
                    message,
                    site=f"{ctx.operation}.bad-flags",
                    gateway_message=f"los: {message}",
                    exit_code=2,
                )
    else:
        if current_data.get("id") != data.get("id"):
            message = ("a replacement keeps the study map's identity; "
                       f"expected {current_data.get('id')!r}, got {data.get('id')!r}")
            raise WriteRefused(
                message,
                site=f"{ctx.operation}.bad-map",
                gateway_message=f"los: {message}",
                exit_code=2,
            )
        data, replacement_diff, problems = _plan_map_replacement(
            root, current_data, data,
            reorder_reason=reorder_reason,
            reset_reason=reset_reason,
            retire_stage_ids=retire_ids,
            retire_reason=retire_reason,
        )
        diff.update(replacement_diff)
        if problems:
            message = ("study map replacement preflight failed; "
                       "no canonical files were written")
            extra = tuple(f"- {problem}" for problem in problems)
            raise WriteRefused(
                message,
                site=f"{ctx.operation}.preflight-failed",
                extra_stderr=extra,
                gateway_message="los: " + message + "".join(f"\n{line}" for line in extra),
                exit_code=1,
            )

    try:
        require_current_template(data, "curriculum")
        validate_contract(
            root,
            "study-map.schema.json",
            data,
            label="curriculum plan template v1",
        )
        effective = expand_map(data, repo.module_source_maps.get(unit.module_id, {}),
                               unit.module_id, unit.id)
        if effective != data:
            validate_contract(root, "study-map.schema.json", effective)
    except (PlanTemplateError, ContractValidationError, MaterialReferenceError) as exc:
        message = f"study map creation contract failed: {exc}"
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.contract-failed",
            gateway_message=f"los: {message}",
            exit_code=2,
        ) from exc
    unit_data = dict(unit.data)
    unit_data["current_study_map"] = data.get("id")
    # A first map makes the unit ready to start. A revision must not
    # silently walk an active unit backwards to that state.
    if current_data is None or (reset_reason or "").strip():
        unit_data["status"] = "ready"
    diff["unit_status"] = unit_data["status"]
    diff.setdefault("stages_after", _stage_id_list(data))
    # Stage membership alone does not describe changed teaching content.
    # Show every changed authored field, including changes on surviving
    # stages, before a UI user approves these exact bytes.
    before_stages = {s["id"]: s for s in (current_data or {}).get("stages", [])}
    content_changes = []
    for stage in effective.get("stages", []):
        before = before_stages.get(stage["id"], {})
        for field in sorted(set(before) | set(stage)):
            if field in {"id", *_PRESERVED_STAGE_STATE}:
                continue
            if before.get(field) != stage.get(field):
                content_changes.append({"stage_id": stage["id"], "field": field,
                                        "before": before.get(field), "after": stage.get(field)})
    diff["content_changes"] = content_changes
    diff["map_changes"] = [
        {"field": field, "before": (current_data or {}).get(field), "after": effective.get(field)}
        for field in sorted(set(current_data or {}) | set(effective))
        if field not in {"id", "stages", *_PRESERVED_MAP_STATE}
        and (current_data or {}).get(field) != effective.get(field)
    ]
    writes = {target: _dump_study_map(current_map, data) if current_map else _dump_yaml(data),
              unit.path: _dump_yaml(unit_data)}
    for stage in data.get("stages", []) or []:
        note_ref = stage.get("working_note") if isinstance(stage, dict) else None
        if note_ref:
            note = root / str(note_ref)
            if not note.exists():
                writes[note] = ""
    if check_only:
        return Result(
            {"ok": True, "mode": "check", "unit_id": req["unit_id"],
             "study_map_id": data.get("id"),
             "files_checked": len(writes),
             "canonical_files_written": 0,
             "file_sha256": "sha256:" + hashlib.sha256(map_bytes).hexdigest(),
             "snapshot_id": ctx.snapshot_id(),
             "expected_revisions": {
                 key: artifact_revision(root, key)
                 for key in [req["unit_id"], str(data["id"])]
             },
             "diff": diff},
            json_dumps=_dumps_default,
        )
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site=f"{ctx.operation}.bad-expected-revision",
        ) from exc

    def finish_unit_map_import(confirmation):
        return {"ok": True, "mode": "apply", "unit_id": req["unit_id"],
                "study_map_id": data.get("id"),
                "diff": diff,
                **confirmation}

    return Result(
        {"ok": True},
        proposal=TransactionProposal(
            capability="unit.map.import",
            writes=writes,
            artifact_ids=[req["unit_id"], str(data.get("id") or f"study-map:{req['unit_id']}")],
            expected_revisions=expected_revisions,
        ),
        finish=finish_unit_map_import,
        on_commit_refused=_on_commit_refused_unit_map_import,
        json_dumps=_dumps_default,
    )


def _validate_publication_synthesis(root, unit_id: str, value: dict) -> dict:
    """Validate a publication dossier, typing only the unknown-unit lookup.

    SPEC (cq) 5: the validator's own schema, dossier/request binding,
    then repository lookup order is unchanged; only the structured
    unknown-unit subclass becomes a typed ``NotFound`` with the
    byte-identical complaint. Every other ``MaterialSynthesisError``
    propagates exactly as before, with no prose matching and no new
    repository read.
    """
    try:
        return validate_unit_material_synthesis(root, unit_id, value)
    except MaterialSynthesisUnitNotFound as exc:
        raise NotFound(
            "unit", exc.unit_id, exc.candidates,
            message=str(exc),
            site="unit.material-synthesis.publish.unknown-unit",
            gateway_message=str(exc),
            exit_code=2,
        ) from exc


@register("unit.material-synthesis.publish", kind="command")
def unit_material_synthesis_publish(ctx: OpContext, req: dict) -> Result:
    """Publish one reviewed unit dossier, with lineage, atomically."""
    root = ctx.root
    # Unwrapped, exactly as legacy: admission and dossier validation
    # propagate with both refusal fields None ((ac) pre-existing raise),
    # except the unknown-unit lookup, which is typed (SPEC (cq) 5).
    value = _input_record(req, "unit material synthesis")
    _validate_publication_synthesis(root, req["unit_id"], value)
    basis = current_unit_material_basis(root, req["unit_id"])
    if req.get("check") is True:
        return Result(
            {"ok": True, "check": True, "unit_id": req["unit_id"],
             "basis": basis},
            json_dumps=_dumps_indented,
        )
    if not req.get("approve"):
        message = "unit material synthesis publication requires explicit approval"
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.needs-approval",
            gateway_message=json.dumps({"ok": False, "error": message}),
            exit_code=2,
        )
    _require_gateway_v2()
    # Re-read every canonical basis guard inside the serialized write
    # window. The earlier validation gives fast feedback; this one is the
    # authority for the commit.
    _validate_publication_synthesis(root, req["unit_id"], value)
    ctx.require_snapshot(req.get("expected_snapshot"))
    destination = synthesis_destination(root, req["unit_id"])
    content = _dump_yaml(value)
    request = current_gateway_request()
    lineage = publication_lineage(root, req["unit_id"], value, content, request)
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site=f"{ctx.operation}.bad-expected-revision",
        ) from exc

    def finish_unit_material_synthesis_publish(confirmation):
        return {"ok": True, **confirmation}

    def refused_stdout_unit_material_synthesis_publish(errors):
        return _dumps_indented({
            "ok": False,
            **({"errors": [str(error) for error in errors]} if errors else {}),
        })

    return Result(
        {"ok": True},
        proposal=TransactionProposal(
            capability="unit.material-synthesis.publish",
            writes={destination: content, root / LEDGER_RELATIVE: lineage},
            artifact_ids=(req["unit_id"], value["id"]),
            expected_revisions=expected_revisions,
        ),
        finish=finish_unit_material_synthesis_publish,
        refused_stdout=refused_stdout_unit_material_synthesis_publish,
        json_dumps=_dumps_indented,
    )


# ------------------------------------------- lineage.restamp (PLAN 4.1,
# Task 75). Helpers moved verbatim from commands/lineage_restamp.py; the
# handler converts cmd_lineage_restamp by SPEC 12.


def _dumps_sorted(payload: dict) -> str:
    """The exact lineage encoder: sorted, spaced, unescaped."""
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _canonical_list_bytes(claim_ids) -> bytes:
    return "".join(cid + "\n" for cid in sorted(claim_ids)).encode("utf-8")


def _plan_sha256(plan: dict[str, dict[str, str]]) -> str:
    body = json.dumps(plan, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(body).hexdigest()


def _verify_named(analysis: dict, claim_ids: list[str],
                  claims_sha256: str) -> tuple[list[str], dict]:
    """The reviewed ids, verified against fresh analysis.

    Returns the sorted ids and their verified plan rows. Refuses unknown
    ids, a hash that does not bind the exact list, and every listed
    claim that is not stampable — a listed claim whose judged state
    moved refuses exactly like an unlisted one.
    """
    if claims_list_sha256(claim_ids) != claims_sha256:
        raise WriteRefused(
            "claims_sha256 does not bind these claim ids; re-hash the "
            "exact reviewed list (sorted ids, one per line)")
    rows = analysis["claims"]
    unknown = [cid for cid in claim_ids if cid not in rows]
    if unknown:
        raise WriteRefused(
            "claims outside the supported old-shape set: "
            + ", ".join(sorted(unknown)))
    refused = {
        cid: rows[cid] for cid in claim_ids
        if rows[cid]["verdict"] != ELIGIBLE
    }
    if refused:
        detail = "; ".join(
            f"{cid} is {rows[cid]['verdict']}"
            f" ({', '.join(rows[cid]['reasons']) or rows[cid]['basis']})"
            for cid in sorted(refused))
        raise WriteRefused(f"the re-stamp refuses: {detail}")
    ordered = sorted(claim_ids)
    return ordered, {cid: rows[cid] for cid in ordered}


def _ledger_guards(root: Path) -> tuple[list[str], dict[str, int]]:
    """The transaction artifacts and their current revisions.

    The re-stamp writes only the sidecar ledger, so the transaction
    guards the ledger path itself — the same file-artifact derivation
    the seal-time dry run uses, by construction rather than by a
    second spelling of the path.
    """
    artifacts = transaction_artifacts(root, (), [root / LEDGER_RELATIVE])
    current = load_revisions(root)
    return artifacts, {artifact: current.get(artifact, 0)
                       for artifact in artifacts}


def _lineage_restamp_commit_lines(commit_errors: list) -> list[str]:
    return ["los: lineage re-stamp failed", *commit_errors[:12]]


@register("lineage.restamp", kind="command")
def lineage_restamp(ctx: OpContext, req: dict) -> Result:
    """Narrow old coarse reads, never re-judge (#94)."""
    root = ctx.root
    check = req.get("check", False)
    review_report = req.get("review_report")
    if check and review_report:
        raise WriteRefused(
            "--check and --review-report are mutually exclusive",
            site=f"{ctx.operation}.check-and-review",
            gateway_message="los: --check and --review-report are mutually exclusive",
            exit_code=2,
        )
    claim_ids = list(req.get("claim_ids") or [])
    claims_sha256 = req.get("claims_sha256")
    if review_report:
        if not claim_ids or not claims_sha256:
            raise WriteRefused(
                "reviewed apply needs --claim-ids and --claims-sha256 with --review-report",
                site=f"{ctx.operation}.reviewed-needs-ids",
                gateway_message=(
                    "los: reviewed apply needs --claim-ids and --claims-sha256 "
                    "with --review-report"),
                exit_code=2,
            )
        try:
            if claims_list_sha256(claim_ids) != claims_sha256:
                raise WriteRefused(
                    "claims_sha256 does not bind these claim ids",
                    site=f"{ctx.operation}.reviewed-sha-mismatch",
                    gateway_message="los: claims_sha256 does not bind these claim ids",
                    exit_code=2,
                )
        except LineageError as exc:
            raise WriteRefused(
                str(exc),
                site=f"{ctx.operation}.reviewed-sha-invalid",
                gateway_message=f"los: {exc}",
                exit_code=2,
            ) from exc
        return Result(
            {},
            command_output=apply_reviewed_envelope(
                ctx,
                capability_name="lineage.restamp",
                payload={"claim_ids": sorted(claim_ids),
                         "claims_sha256": claims_sha256},
                reviewed_content=_canonical_list_bytes(claim_ids),
                reviewed_sha256=claims_sha256,
                review_report=review_report,
            ),
        )
    ctx.require_snapshot(req.get("expected_snapshot"))
    try:
        analysis = analyze(root)
    except (LineageError, githistory.GitHistoryError, OSError,
            ValueError) as exc:
        raise WriteRefused(
            f"re-stamp analysis failed: {exc}",
            site=f"{ctx.operation}.analysis-failed",
            gateway_message=f"los: re-stamp analysis failed: {exc}",
            exit_code=2,
        ) from exc
    snapshot = ctx.snapshot_id()
    if check and not claim_ids:
        return Result(
            {"ok": True, "mode": "check", "capability": "lineage.restamp",
             "expected_snapshot": snapshot, **analysis},
            json_dumps=_dumps_sorted,
        )
    if not claim_ids or not claims_sha256:
        raise WriteRefused(
            "lineage-restamp needs --claim-ids with --claims-sha256 (the reviewed list); "
            "--check alone recomputes eligibility",
            site=f"{ctx.operation}.needs-claim-ids",
            gateway_message=(
                "los: lineage-restamp needs --claim-ids with --claims-sha256 "
                "(the reviewed list); --check alone recomputes eligibility"),
            exit_code=2,
        )
    try:
        ordered, planned = _verify_named(analysis, claim_ids, claims_sha256)
    except (WriteRefused, LineageError) as exc:
        raise WriteRefused(
            str(exc),
            site=f"{ctx.operation}.unverified-claims",
            gateway_message=f"los: {exc}",
            exit_code=2,
        ) from exc
    plan = {cid: dict(planned[cid]["new_reads"]) for cid in ordered}
    plan_sha = _plan_sha256(plan)
    if check:
        _artifacts, revisions = _ledger_guards(root)
        payload = {"claim_ids": ordered, "claims_sha256": claims_sha256}
        return Result(
            {"ok": True, "mode": "check", "capability": "lineage.restamp",
             "claim_ids": ordered, "claims_sha256": claims_sha256,
             "plan": plan, "plan_sha256": plan_sha,
             "expected_snapshot": snapshot,
             "expected_revisions": revisions,
             "reviewed_file_sha256": claims_sha256,
             "gateway_envelope": prepare_review_envelope(
                 "lineage.restamp", payload, snapshot, revisions)},
            json_dumps=_dumps_sorted,
        )
    request = current_gateway_request()
    if request is None:
        raise WriteRefused(
            "lineage-restamp applies only through its reviewed report (--review-report) "
            "or a sealed GatewayEnvelopeV2 (`los capability lineage.restamp --payload-file "
            "ENVELOPE.json`); direct CLI application is disabled",
            site=f"{ctx.operation}.direct-apply-disabled",
            gateway_message=(
                "los: lineage-restamp applies only through its reviewed report "
                "(--review-report) or a sealed GatewayEnvelopeV2 (`los capability "
                "lineage.restamp --payload-file ENVELOPE.json`); direct CLI "
                "application is disabled"),
            exit_code=2,
        )
    try:
        records = load_ledger(root)
        stamped = dict(records)
        restamped_by = f"{request.channel}/{request.approval_kind}"
        restamped_on = observations.now().astimezone(_dt.UTC).date().isoformat()
        for cid in ordered:
            prior = records.get(cid)
            if prior is None:
                raise LineageError(f"claim {cid!r} left the ledger")
            stamped[cid] = restamp_claim(
                prior, source_hashes=plan[cid],
                restamped_by=restamped_by, restamped_on=restamped_on)
        text = dump_ledger(stamped)
    except LineageError as exc:
        raise WriteRefused(
            str(exc),
            site=f"{ctx.operation}.restamp-failed",
            gateway_message=f"los: {exc}",
            exit_code=2,
        ) from exc
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site=f"{ctx.operation}.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "mode": "apply", "capability": "lineage.restamp",
         "claim_ids": ordered, "claims_sha256": claims_sha256,
         "plan_sha256": plan_sha},
        proposal=TransactionProposal(
            capability="lineage.restamp",
            writes={root / LEDGER_RELATIVE: text},
            artifact_ids=(),
            expected_revisions=expected_revisions,
            # The envelope's intent hash already binds the claim list;
            # echoing the hash and the count here keeps the receipt
            # directly auditable without reopening the envelope.
            metadata={"claims_sha256": claims_sha256,
                      "claims_count": len(ordered)},
        ),
        on_commit_refused=_lineage_restamp_commit_lines,
        json_dumps=_dumps_sorted,
    )

# -------------------- module.plan.import / unit.plan.revise (PLAN 4.1,
# Task 82). Pure construction lives in learning_os/domain/plan_import.py;
# these helpers (repository reads, gateway context, report presentation)
# moved verbatim from commands/module.py; the handlers convert the three
# entries by SPEC 12 (R1 promotion/compact branches, R4 shared tail).



_LINEAGE_EVIDENCE_KINDS = ("route-locator", "manifest", "repo-file", "external")

def _materials_files(root: Path) -> dict:
    try:
        raw = yaml.safe_load(
            (root / "records" / "materials-manifest.yaml").read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    files = raw.get("files") if isinstance(raw, dict) else None
    return files if isinstance(files, dict) else {}

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


def _dumps_plain(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _dumps_indented_sort(payload: dict) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)


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
            json_dumps=lambda payload: json.dumps(
                payload, indent=2, ensure_ascii=False),
        )
    ctx.require_snapshot(req.get("expected_snapshot"))
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc),
            site=f"{ctx.operation}.bad-expected-revision",
            gateway_message=f"los: {exc}",
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

    def after_commit(code, errors, confirmation):
        if gate_errors:
            _plan_refuse(
                ctx,
                "Master Planning promotion preflight failed; no canonical "
                "files were written",
                "promotion-preflight-failed",
                exit_code=1,
                extra=tuple(gate_errors[:12]),
            )

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
        {"ok": True},
        proposal=TransactionProposal(
            capability="module.plan.import",
            writes=plan.writes,
            artifact_ids=plan.artifact_ids,
            expected_revisions=expected_revisions,
            validate_extra=validate_extra,
        ),
        finish=finish_promotion,
        after_commit=after_commit,
        on_commit_refused=refused_promotion,
        json_dumps=_dumps_plain,
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
        root, repo, module_id, package)
    if lineage_problems:
        _plan_refuse(
            ctx,
            "module plan lineage preflight failed; no canonical files were written",
            "lineage-preflight-failed",
            exit_code=1,
            extra=tuple(f"- {problem}" for problem in lineage_problems),
        )
    if not req.get("check") and (changed_claims or synthesis_entries):
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
            json_dumps=_dumps_indented_sort,
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
        result["files_checked"] = len(writes)
        capability = capability_override or "module.plan.import"
        reviewed_sha = review_input[0] if review_input else package_sha
        payload = review_input[1] if review_input else {
            "module_id": module_id, "file": str(source), "file_sha256": package_sha}
        owners = result["commit_artifact_ids"] if minimal_writes \
            else [module_id, *sorted(seen_units), *synthesis_ids]
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
        return Result(result, json_dumps=_dumps_plain)
    if minimal_writes:
        artifact_ids = _minimal_artifact_ids(
            root, module_id, writes, synthesis_entries)
    else:
        artifact_ids = [module_id, *sorted(seen_units), *synthesis_ids]
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
            gateway_message=f"los: {exc}",
            exit_code=2,
        ) from exc

    def after_commit(code, errors, confirmation):
        if gate_errors:
            _plan_refuse(
                ctx,
                "module plan validation preflight failed; no canonical files were written",
                "validation-preflight-failed",
                exit_code=1,
                extra=tuple(str(issue) for issue in gate_errors[:12]),
            )

    def finish_plan_import(confirmation):
        return {"ok": True, "mode": "apply", "module_id": module_id,
                "units_written": sorted(seen_units), "files_written": len(writes),
                **confirmation}

    def refused_plan_import(errors):
        return ["los: module plan import failed", *errors[:12]]

    return Result(
        {"ok": True},
        proposal=TransactionProposal(
            capability=capability_override or "module.plan.import",
            writes=writes,
            artifact_ids=artifact_ids,
            expected_revisions=expected_revisions,
            validate_extra=validate_extra,
        ),
        finish=finish_plan_import,
        after_commit=after_commit,
        on_commit_refused=refused_plan_import,
        json_dumps=_dumps_plain,
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
            {},
            command_output=apply_reviewed_envelope(
                ctx,
                capability_name="module.plan.import",
                payload={"module_id": req["module_id"], "file": str(source),
                         "file_sha256": apply_sha},
                reviewed_content=revision_bytes,
                reviewed_sha256=apply_sha,
                review_report=req.get("review_report"),
            ),
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
            {},
            command_output=apply_reviewed_envelope(
                ctx,
                capability_name="module.plan.import",
                payload={"module_id": req["module_id"], "file": str(_source),
                         "file_sha256": apply_sha},
                reviewed_content=package_bytes,
                reviewed_sha256=apply_sha,
                review_report=req.get("review_report"),
            ),
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
            {},
            command_output=apply_reviewed_envelope(
                ctx,
                capability_name="unit.plan.revise",
                payload={"unit_id": req["unit_id"], "record": revision},
                reviewed_content=revision_bytes,
                reviewed_sha256=apply_flag,
                review_report=req.get("review_report"),
            ),
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
