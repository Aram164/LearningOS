"""Academic modules and the module plan import, including its contract and routing checks."""

from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
from pathlib import Path

import yaml

from learning_os.loader import load_repo
from learning_os.render import replace_h2_section as _replace_h2_section
from learning_os.rules import validate
from learning_os.rules.common import ENVIRONMENTAL_WARNINGS

from .support import (
    _atomic_text,
    _dump_yaml,
    _expected_ok,
    _expected_revisions_from_args,
    _fresh_manifest,
    _operator_lock,
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


def _module_plan_contract_problems(root: Path, package: dict) -> list[str]:
    """Verify the human review evidence required before a plan is executable."""
    problems: list[str] = []
    contract = package.get("plan_contract")
    if not isinstance(contract, dict) or contract.get("version") != 1:
        return ["plan_contract.version must be 1 (see system/PLAN-CREATION-SOP.md)"]
    audit_ref = contract.get("coverage_audit")
    if not isinstance(audit_ref, str) or not audit_ref.strip():
        problems.append("plan_contract.coverage_audit must name the completed audit")
    else:
        audit = (root / audit_ref).resolve()
        try:
            audit.relative_to(root.resolve())
        except ValueError:
            problems.append("plan_contract.coverage_audit must stay inside the repository")
        else:
            if not audit.is_file():
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


def _module_plan_validation_errors(root: Path, writes: dict[Path, str]) -> list:
    """Validate planned files in a small shadow repository without canonical writes."""
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
        return [issue for issue in validate(load_repo(shadow), online=False)
                if issue.severity == "E"
                or (issue.severity == "W"
                    and issue.code not in ENVIRONMENTAL_WARNINGS)]


def cmd_module_plan_import(args) -> int:
    """Apply one reviewable, module-scoped curriculum plan as a transaction.

    This gateway exists for the structural part of WORKFLOWS §23: a lecture
    batch may add units, their current study maps, module source routing, and
    explicit workspace joins together. It never deletes units or creates
    durable notes, and every stage remains bounded to the requested module.
    """
    root = _root(args)
    source = Path(args.file).expanduser().resolve()
    if not source.is_file():
        print(f"los: no such module plan file: {source}", file=sys.stderr)
        return 2
    try:
        package = yaml.safe_load(source.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
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
    if not args.check and not args.expected_snapshot:
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
            writes[unit_dir / "study-map.yaml"] = _dump_yaml(map_data)
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
        try:
            errors = _module_plan_validation_errors(root, writes)
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
            result = {"ok": True, "mode": "check", "module_id": args.module_id,
                      "units_checked": sorted(seen_units), "files_checked": len(writes),
                      "canonical_files_written": 0}
        else:
            code, errors, confirmation = _write_transaction(
                root, writes, capability="module.plan.import",
                expected_revisions=_expected_revisions_from_args(args),
                artifact_ids=[args.module_id, *sorted(seen_units)],
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
