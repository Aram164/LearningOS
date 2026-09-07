"""Units, unit map import, and the unit-level note."""

from __future__ import annotations

import copy
import datetime as _dt
import json
import sys
from pathlib import Path

import yaml

from learning_os.contracts import (
    ContractValidationError,
    PlanTemplateError,
    require_current_template,
    validate_contract,
)
from learning_os.loader import load_repo
from learning_os.material_refs import MaterialReferenceError, expand_map
from learning_os.routes import route_with_identity
from learning_os.unit_notes import unit_note_marker

from .support import (
    WriteRefused,
    _dump_study_map,
    _dump_yaml,
    _expected_ok,
    _expected_revisions_from_args,
    _fresh_manifest,
    _operator_lock,
    _print_rows,
    _read_content_bound_file,
    _root,
    _unit_map_or_error,
    _write_transaction,
)


def cmd_unit_list(args) -> int:
    manifest = _fresh_manifest(_root(args))
    rows = manifest.get("units", [])
    if args.module_id:
        rows = [row for row in rows if row.get("module_id") == args.module_id]
    if args.component_id:
        rows = [row for row in rows if row.get("component_id") == args.component_id]
    if args.status:
        rows = [row for row in rows if row.get("status") == args.status]
    return _print_rows(rows)


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


def cmd_unit_map_import(args) -> int:
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
    root = _root(args)
    try:
        _source, map_bytes = _read_content_bound_file(
            args.file,
            getattr(args, "file_sha256", None),
            label="study-map file",
        )
    except WriteRefused as exc:
        print(f"los: {exc}", file=sys.stderr)
        return 2
    check_only = bool(getattr(args, "check", False))
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        repo = load_repo(root)
        unit = repo.units.get(args.unit_id)
        if unit is None:
            print(f"los: unit not found: {args.unit_id}", file=sys.stderr)
            return 2
        target = unit.path.parent / "study-map.yaml"
        if target.exists() and not args.replace:
            print("los: this unit already has a current study map; use --replace to make Git the prior-version archive",
                  file=sys.stderr)
            return 2
        try:
            data = yaml.safe_load(map_bytes.decode("utf-8"))
        except (UnicodeDecodeError, yaml.YAMLError) as exc:
            print(f"los: invalid study-map YAML: {exc}", file=sys.stderr)
            return 2
        if not isinstance(data, dict) or data.get("unit_id") != args.unit_id:
            print("los: imported map must be a mapping with the requested unit_id", file=sys.stderr)
            return 2

        current_map_id = unit.data.get("current_study_map")
        current_map = repo.study_maps.get(current_map_id) if current_map_id else None
        current_data = copy.deepcopy(current_map.data) if current_map is not None else None
        reorder_reason = getattr(args, "intentional_reorder", None)
        reset_reason = getattr(args, "intentional_state_reset", None)
        retire_ids = list(getattr(args, "retire_stage", None) or [])
        retire_reason = getattr(args, "retire_reason", None)
        diff: dict = {"replacement": current_data is not None}

        if current_data is None:
            for flag, value in (("--intentional-reorder", reorder_reason),
                                ("--intentional-state-reset", reset_reason),
                                ("--retire-stage", retire_ids),
                                ("--retire-reason", retire_reason)):
                if value:
                    print(f"los: {flag} only applies to a replacement of an existing map",
                          file=sys.stderr)
                    return 2
        else:
            if current_data.get("id") != data.get("id"):
                print("los: a replacement keeps the study map's identity; "
                      f"expected {current_data.get('id')!r}, got {data.get('id')!r}",
                      file=sys.stderr)
                return 2
            data, replacement_diff, problems = _plan_map_replacement(
                root, current_data, data,
                reorder_reason=reorder_reason,
                reset_reason=reset_reason,
                retire_stage_ids=retire_ids,
                retire_reason=retire_reason,
            )
            diff.update(replacement_diff)
            if problems:
                print("los: study map replacement preflight failed; no canonical files were written",
                      file=sys.stderr)
                for problem in problems:
                    print(f"- {problem}", file=sys.stderr)
                return 1

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
            print(f"los: study map creation contract failed: {exc}", file=sys.stderr)
            return 2
        unit_data = dict(unit.data)
        unit_data["current_study_map"] = data.get("id")
        # A first map makes the unit ready to start. A revision must not
        # silently walk an active unit backwards to that state.
        if current_data is None or (reset_reason or "").strip():
            unit_data["status"] = "ready"
        diff["unit_status"] = unit_data["status"]
        writes = {target: _dump_study_map(current_map, data) if current_map else _dump_yaml(data),
                  unit.path: _dump_yaml(unit_data)}
        for stage in data.get("stages", []) or []:
            note_ref = stage.get("working_note") if isinstance(stage, dict) else None
            if note_ref:
                note = root / str(note_ref)
                if not note.exists():
                    writes[note] = ""
        if check_only:
            print(json.dumps({"ok": True, "mode": "check", "unit_id": args.unit_id,
                              "study_map_id": data.get("id"),
                              "files_checked": len(writes),
                              "canonical_files_written": 0,
                              "diff": diff}, ensure_ascii=False))
            return 0
        code, errors, confirmation = _write_transaction(
            root, writes, capability="unit.map.import",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=[args.unit_id, str(data.get("id") or f"study-map:{args.unit_id}")],
        )
        if code:
            print("los: study map import rejected by validation", file=sys.stderr)
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code
    print(json.dumps({"ok": True, "mode": "apply", "unit_id": args.unit_id,
                      "study_map_id": data.get("id"),
                      "diff": diff,
                      **confirmation}, ensure_ascii=False))
    return 0


def cmd_unit_source_selection(args) -> int:
    """Persist one learner choice without changing the complete material menu."""
    root = _root(args)
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        repo = load_repo(root)
        unit = repo.units.get(args.unit_id)
        if unit is None:
            print(f"los: unit not found: {args.unit_id}", file=sys.stderr)
            return 2
        if args.source_id not in repo.sources:
            print(f"los: source not found: {args.source_id}", file=sys.stderr)
            return 2

        source_map = repo.module_source_maps.get(unit.module_id, {})
        matching_route = None
        for source in source_map.get("sources", []) or []:
            if not isinstance(source, dict) or source.get("source_id") != args.source_id:
                continue
            for route in source.get("unit_routes", []) or []:
                if (
                    isinstance(route, dict)
                    and route.get("unit_id") == args.unit_id
                    and route.get("locator") == args.locator
                ):
                    matching_route = route_with_identity(
                        unit.module_id, args.source_id, route
                    )
                    break
            if matching_route is not None:
                break
        if matching_route is None:
            print(
                "los: selection must match one rich material route on this unit "
                f"({args.source_id} · {args.locator})",
                file=sys.stderr,
            )
            return 2

        unit_data = copy.deepcopy(unit.data)
        selections = list(unit_data.get("source_selections", []) or [])
        index = next((
            i for i, row in enumerate(selections)
            if isinstance(row, dict)
            and row.get("source_id") == args.source_id
            and row.get("locator") == args.locator
        ), None)

        if args.action == "select":
            purpose = str(args.purpose or matching_route.get("angle") or "Chosen learning material").strip()
            if not purpose:
                print("los: a selected material needs a purpose", file=sys.stderr)
                return 2
            replacement = {
                "route_id": matching_route["id"],
                "source_id": args.source_id,
                "locator": args.locator,
                "purpose": purpose,
            }
            if index is None:
                selections.append(replacement)
            else:
                if selections[index].get("stage_ids"):
                    replacement["stage_ids"] = list(selections[index]["stage_ids"])
                selections[index] = replacement
            selected = True
        else:
            if index is not None and selections[index].get("stage_ids"):
                print(
                    "los: this choice is used by the current study path; remove it "
                    "from those stages before removing the choice",
                    file=sys.stderr,
                )
                return 2
            if index is not None:
                selections.pop(index)
            selected = False

        unit_data["source_selections"] = selections
        code, errors, confirmation = _write_transaction(
            root,
            {unit.path: _dump_yaml(unit_data)},
            capability="unit.source-selection.set",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=[args.unit_id],
        )
        if code:
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code

    print(json.dumps({
        "ok": True,
        "unit_id": args.unit_id,
        "source_id": args.source_id,
        "locator": args.locator,
        "selected": selected,
        **confirmation,
    }, ensure_ascii=False))
    return 0


def _unit_note_target(root: Path, unit) -> tuple[Path, str]:
    declared = str(unit.data.get("working_note") or "").strip()
    target = root / declared if declared else unit.path.parent / "notes.md"
    try:
        rel = target.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise WriteRefused("unit working note must stay inside the repository") from exc
    return target, rel


def cmd_unit_note(args) -> int:
    """Append one session-level section to the unit working note.

    The note belongs to the unit/session context, never to one selected stage.
    Referenced stage ids are evidence/context only and must belong to the unit's
    current study map. Existing stage notes remain readable compatibility data.
    """
    root = _root(args)
    value = args.text if args.text is not None else sys.stdin.read()
    if not value.strip():
        print("los: refusing to write an empty unit note — pass real text", file=sys.stderr)
        return 2
    raw_sources = list(args.attachment or [])
    source_hashes = list(getattr(args, "attachment_sha256", None) or [])
    if source_hashes and len(source_hashes) != len(raw_sources):
        print("los: --attachment-sha256 must be repeated once per --attachment",
              file=sys.stderr)
        return 2
    try:
        sources = [
            _read_content_bound_file(
                raw,
                source_hashes[index] if index < len(source_hashes) else None,
                label=f"unit-note attachment[{index}]",
            )
            for index, raw in enumerate(raw_sources)
        ]
    except WriteRefused as exc:
        print(f"los: {exc}", file=sys.stderr)
        return 2

    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        repo, unit, study_map = _unit_map_or_error(root, args.unit_id)
        if unit is None or study_map is None:
            return 2
        stage_ids = list(dict.fromkeys(args.stage_id or []))
        allowed = {row.get("id") for row in study_map.data.get("stages", []) or []}
        unknown = [stage_id for stage_id in stage_ids if stage_id not in allowed]
        if unknown:
            print(f"los: stage does not belong to unit '{args.unit_id}': {unknown[0]}", file=sys.stderr)
            return 2

        unit_data = copy.deepcopy(unit.data)
        try:
            target, rel = _unit_note_target(root, unit)
        except WriteRefused as exc:
            print(f"los: {exc}", file=sys.stderr)
            return 2
        old = target.read_text(encoding="utf-8") if target.is_file() else ""
        recorded_at = _dt.datetime.now().astimezone().replace(microsecond=0).isoformat()
        title = " ".join((args.title or "Learning session note").split()) or "Learning session note"

        attachments: list[dict] = []
        attachment_writes: dict[Path, bytes] = {}
        stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        attachment_dir = unit.path.parent / "attachments" / f"unit-note-{stamp}"
        try:
            for source, source_bytes in sources:
                target_file = attachment_dir / source.name
                suffix = 2
                while target_file.exists() or target_file in attachment_writes:
                    target_file = attachment_dir / f"{suffix}-{source.name}"
                    suffix += 1
                attachment_writes[target_file] = source_bytes
                attachments.append({
                    "path": target_file.relative_to(root).as_posix(),
                    "label": source.stem,
                })

            metadata = {
                "recorded_at": recorded_at,
                "title": title,
                "stage_ids": stage_ids,
                "attachments": attachments,
            }
            lines = [unit_note_marker(metadata), f"## {title}", "", value.rstrip()]
            if attachments:
                lines.extend(["", "### Attachments", ""] + [
                    f"- [{item['label']}]({Path(item['path']).relative_to(unit.path.parent.relative_to(root)).as_posix()})"
                    for item in attachments
                ])
            section = "\n".join(lines).rstrip() + "\n"
            divider = "\n" if old and not old.endswith("\n\n") else ""
            updated = old + divider + section
            if not unit_data.get("working_note"):
                unit_data["working_note"] = rel
            writes: dict[Path, str | bytes] = {
                target: updated,
                unit.path: _dump_yaml(unit_data),
                **attachment_writes,
            }
            code, errors, confirmation = _write_transaction(
                root, writes, capability="unit.note.append",
                expected_revisions=_expected_revisions_from_args(args),
                artifact_ids=[args.unit_id],
            )
            if code:
                for issue in errors[:12]:
                    print(issue, file=sys.stderr)
                return code
        except (OSError, WriteRefused) as exc:
            print(f"los: cannot write unit note: {exc}", file=sys.stderr)
            return 2


    print(json.dumps({
        "ok": True, "unit_id": args.unit_id, "working_note": rel,
        "recorded_at": recorded_at, "stage_ids": stage_ids,
        "attachments": attachments,
        **confirmation,
    }, ensure_ascii=False))
    return 0
