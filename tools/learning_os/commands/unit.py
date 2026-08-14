"""Units, unit map import, and the unit-level note."""

from __future__ import annotations

import copy
import datetime as _dt
import json
import sys
import yaml
from learning_os.loader import load_repo
from pathlib import Path
from .support import WriteRefused, _dump_yaml, _expected_ok, _expected_revisions_from_args, _fresh_manifest, _operator_lock, _print_rows, _root, _unit_map_or_error, _write_transaction

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


def cmd_unit_map_import(args) -> int:
    root = _root(args)
    source = Path(args.file).expanduser().resolve()
    if not source.is_file():
        print(f"los: no such map file: {source}", file=sys.stderr)
        return 2
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
            data = yaml.safe_load(source.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            print(f"los: invalid study-map YAML: {exc}", file=sys.stderr)
            return 2
        if not isinstance(data, dict) or data.get("unit_id") != args.unit_id:
            print("los: imported map must be a mapping with the requested unit_id", file=sys.stderr)
            return 2
        unit_data = dict(unit.data)
        unit_data["current_study_map"] = data.get("id")
        unit_data["status"] = "ready"
        writes = {target: _dump_yaml(data), unit.path: _dump_yaml(unit_data)}
        for stage in data.get("stages", []) or []:
            note_ref = stage.get("working_note") if isinstance(stage, dict) else None
            if note_ref:
                note = root / str(note_ref)
                if not note.exists():
                    writes[note] = ""
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
    print(json.dumps({"ok": True, "unit_id": args.unit_id,
                      "study_map_id": data.get("id")}, ensure_ascii=False))
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
                    matching_route = route
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
        code, errors, _confirmation = _write_transaction(
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
    }, ensure_ascii=False))
    return 0


def _unit_note_marker(metadata: dict) -> str:
    return "<!-- learningos:unit-note " + json.dumps(
        metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ) + " -->"


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
    sources = [Path(raw).expanduser().resolve() for raw in (args.attachment or [])]
    missing = [source for source in sources if not source.is_file()]
    if missing:
        print(f"los: no such attachment: {missing[0]}", file=sys.stderr)
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
            for source in sources:
                target_file = attachment_dir / source.name
                suffix = 2
                while target_file.exists() or target_file in attachment_writes:
                    target_file = attachment_dir / f"{suffix}-{source.name}"
                    suffix += 1
                attachment_writes[target_file] = source.read_bytes()
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
            lines = [_unit_note_marker(metadata), f"## {title}", "", value.rstrip()]
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
    }, ensure_ascii=False))
    return 0
