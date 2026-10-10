"""Plan-area handlers (PLAN D4): material plans, revisions, and reads."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import unicodedata
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlsplit

import yaml

from learning_os.contracts import (
    PLAN_TEMPLATE_VERSION,
    ContractValidationError,
    PlanTemplateError,
    build_plan_template,
)
from learning_os.contracts.gateway import current_gateway_request
from learning_os.contracts.json_schema import validate_contract
from learning_os.domain.failures import (
    NotFound,
    StaleSnapshot,
    ValidationFailed,
    WriteRefused,
    unreadable_refusal,
)
from learning_os.domain.suggest import (
    MAX_SUGGESTIONS,
    expansion,
    suggest,
    with_suggestions,
)
from learning_os.learning_runtime import (
    RuntimeInputError,
    read_stage_results,
    stage_results_for,
)
from learning_os.loading import FRONTMATTER_RE
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
    current_unit_material_basis,
    material_synthesis_freshness,
    publication_lineage_record,
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
    _dump_yaml,
    _evidence_label,
    _freshness_label,
    _guard_rows,
    _map_for_unit,
    _note_bytes,
    _read_structured_file,
    _route_material_files,
    _snapshot,
    _unit_note_scope,
    _use_evidence,
    _window_values,
)
from learning_os.ops._plan_gate import (
    _compose_plan_gate_errors,
    _module_plan_validation_errors,
    _plan_apply_gate,
    _real_perimeter_errors,
)
from learning_os.ops.context import OpContext
from learning_os.ops.proposal import Result, TransactionProposal
from learning_os.ops.registry import register
from learning_os.pathing import PathBoundaryError, resolve_symlinks_inside
from learning_os.revisions import artifact_revision
from learning_os.rules.common import CANONICAL_TREES
from learning_os.semantics.lineage import LEDGER_RELATIVE, dump_ledger, load_ledger
from learning_os.transactions import parse_expected_revisions
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
