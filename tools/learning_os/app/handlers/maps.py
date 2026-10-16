"""Unit study maps: the plan template and map import."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import yaml

from learning_os.app.context import OpContext
from learning_os.app.gateway import read_content_bound_file as _read_content_bound_file
from learning_os.app.proposal import ResponsePayload, Result, TransactionProposal
from learning_os.app.registry import register
from learning_os.domain.failures import NotFound, WriteRefused
from learning_os.domain.material_refs import MaterialReferenceError, expand_map
from learning_os.domain.suggest import not_found
from learning_os.store.codec import dump_study_map as _dump_study_map
from learning_os.store.codec import dump_yaml as _dump_yaml
from learning_os.store.contracts import (
    PLAN_TEMPLATE_VERSION,
    ContractValidationError,
    PlanTemplateError,
    build_plan_template,
    require_current_template,
)
from learning_os.store.contracts.json_schema import validate_contract
from learning_os.store.revisions import artifact_revision
from learning_os.store.transactions import parse_expected_revisions

PLAN_TEMPLATE_CONTRACT = "plan-template-v1"

_PROFILE_SCHEMAS = {
    "curriculum": "study-map.schema.json",
}


def _human_plan_template(payload: dict) -> str:
    """The paste-ready YAML the operator reads (SPEC §12)."""
    return yaml.safe_dump(
        payload["plan"], sort_keys=False, allow_unicode=True, width=100
    ).removesuffix("\n")


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
    return Result(response)


_PRESERVED_STAGE_STATE = (
    "status",
    "completed",
    "working_note",
    "attachments",
    "source_feedback",
    "detour_id",
)


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
            prefixed=True,
            exit_code=2,
        )
    try:
        data = yaml.safe_load(map_bytes.decode("utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        message = f"invalid study-map YAML: {exc}"
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.bad-map",
            prefixed=True,
            exit_code=2,
        ) from exc
    if not isinstance(data, dict) or data.get("unit_id") != req["unit_id"]:
        message = "imported map must be a mapping with the requested unit_id"
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.bad-map",
            prefixed=True,
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
                    prefixed=True,
                    exit_code=2,
                )
    else:
        if current_data.get("id") != data.get("id"):
            message = ("a replacement keeps the study map's identity; "
                       f"expected {current_data.get('id')!r}, got {data.get('id')!r}")
            raise WriteRefused(
                message,
                site=f"{ctx.operation}.bad-map",
                prefixed=True,
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
            prefixed=True,
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
        ResponsePayload({"ok": True}, finish_unit_map_import({}), confirmation='merge'),
        proposal=TransactionProposal(
            capability="unit.map.import",
            writes=writes,
            artifact_ids=[req["unit_id"], str(data.get("id") or f"study-map:{req['unit_id']}")],
            expected_revisions=expected_revisions,
        ),



    )
