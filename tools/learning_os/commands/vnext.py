"""LearningOS vNext comparison, archive, planning, backup, and health commands."""

from __future__ import annotations

import json
from pathlib import Path

from migrations.job_quarantine_collapse import (
    migration_artifact_ids,
)
from migrations.job_quarantine_collapse import (
    plan_migration as plan_job_learning_migration,
)
from migrations.job_quarantine_collapse import (
    plan_sha256 as job_learning_plan_sha256,
)
from migrations.job_quarantine_collapse import (
    verify_plan_inputs as verify_job_learning_plan_inputs,
)
from migrations.route_identity_v13 import plan_migration, plan_sha256

from learning_os.backup_manifest import (
    build_backup_manifest,
    verify_backup_manifest,
    verify_restored_system,
)
from learning_os.contracts.gateway import current_gateway_request
from learning_os.health import build_health_report
from learning_os.legacy_archive import (
    inspect_legacy_archive,
    legacy_archive_lock_destination,
    load_legacy_allowlist,
    load_legacy_archive_lock,
)
from learning_os.masters_planning import (
    candidate_comparison_destination,
    master_catalog_destination,
    masters_planning_dashboard,
    validate_candidate_comparison,
    validate_catalog_revision,
    validate_master_catalog,
)
from learning_os.material_synthesis import (
    current_unit_material_basis,
    synthesis_destination,
    validate_unit_material_synthesis,
)

from .support import (
    WriteRefused,
    _dump_yaml,
    _expected_ok,
    _expected_revisions_from_args,
    _operator_lock,
    _read_structured_file,
    _root,
    _write_transaction,
)


def _input_record(args, label: str) -> dict:
    value = getattr(args, "record", None)
    if value is not None:
        if not isinstance(value, dict):
            raise WriteRefused(f"{label} must be an object")
        return value
    file_name = getattr(args, "file", None)
    if not file_name:
        raise WriteRefused(f"{label} is required")
    return _read_structured_file(file_name)


def _require_gateway_v2() -> None:
    if current_gateway_request() is None:
        raise WriteRefused(
            "this approved write must use GatewayEnvelopeV2; direct CLI publication is disabled"
        )


def _refuse_without_approval(args, label: str) -> int | None:
    if getattr(args, "approve", False):
        return None
    print(json.dumps({"ok": False, "error": f"{label} requires explicit approval"}))
    return 2


def cmd_unit_material_synthesis_publish(args) -> int:
    root = _root(args)
    value = _input_record(args, "unit material synthesis")
    validate_unit_material_synthesis(root, args.unit_id, value)
    basis = current_unit_material_basis(root, args.unit_id)
    if args.check:
        print(json.dumps({"ok": True, "check": True, "unit_id": args.unit_id,
                          "basis": basis}, indent=2, ensure_ascii=False))
        return 0
    denied = _refuse_without_approval(args, "unit material synthesis publication")
    if denied is not None:
        return denied
    _require_gateway_v2()
    with _operator_lock(root):
        # Re-read every canonical basis guard inside the serialized write
        # window. The earlier validation gives fast feedback; this one is the
        # authority for the commit.
        validate_unit_material_synthesis(root, args.unit_id, value)
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        destination = synthesis_destination(root, args.unit_id)
        code, errors, confirmation = _write_transaction(
            root,
            {destination: _dump_yaml(value)},
            capability="unit.material-synthesis.publish",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=(args.unit_id, value["id"]),
        )
    print(json.dumps({
        "ok": code == 0, **confirmation,
        **({"errors": [str(error) for error in errors]} if errors else {}),
    }, indent=2, ensure_ascii=False))
    return code


def cmd_legacy_archive_inspect(args) -> int:
    root = _root(args)
    allowlist = load_legacy_allowlist(root, Path(args.allowlist).expanduser().resolve())
    lock = inspect_legacy_archive(
        root, Path(args.archive_root).expanduser().resolve(), allowlist,
    )
    print(json.dumps(lock, indent=2, ensure_ascii=False))
    return 0


def cmd_legacy_archive_status(args) -> int:
    root = _root(args)
    lock = load_legacy_archive_lock(root)
    value = {
        "schema_version": 1,
        "type": "legacy-archive-status",
        "available": lock is not None,
        "lock": lock,
    }
    from learning_os.contracts.json_schema import validate_contract
    validate_contract(root, "legacy-archive-status.schema.json", value)
    print(json.dumps(value, indent=2, ensure_ascii=False))
    return 0


def cmd_legacy_archive_lock_publish(args) -> int:
    root = _root(args)
    value = _input_record(args, "Legacy archive lock")
    # Reuse the exact public reader validation before the write boundary.
    from learning_os.contracts.json_schema import validate_contract
    validate_contract(root, "legacy-archive-lock.schema.json", value)
    denied = _refuse_without_approval(args, "Legacy archive lock publication")
    if denied is not None:
        return denied
    _require_gateway_v2()
    with _operator_lock(root):
        validate_contract(root, "legacy-archive-lock.schema.json", value)
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        destination = legacy_archive_lock_destination(root)
        code, errors, confirmation = _write_transaction(
            root, {destination: _dump_yaml(value)},
            capability="legacy.archive.lock.publish",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=("legacy-archive-lock",),
        )
    print(json.dumps({
        "ok": code == 0, **confirmation,
        **({"errors": [str(error) for error in errors]} if errors else {}),
    }, indent=2, ensure_ascii=False))
    return code


def cmd_masters_planning_dashboard(args) -> int:
    value = masters_planning_dashboard(
        _root(args), confirmed=bool(args.confirm_masters_planning),
    )
    print(json.dumps(value, indent=2, ensure_ascii=False))
    return 0


def cmd_masters_planning_catalog_update(args) -> int:
    root = _root(args)
    value = validate_master_catalog(root, _input_record(args, "Master Planning catalog"))
    validate_catalog_revision(root, value)
    denied = _refuse_without_approval(args, "Master Planning catalog update")
    if denied is not None:
        return denied
    _require_gateway_v2()
    with _operator_lock(root):
        value = validate_master_catalog(root, value)
        validate_catalog_revision(root, value)
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        code, errors, confirmation = _write_transaction(
            root, {master_catalog_destination(root): _dump_yaml(value)},
            capability="masters-planning.catalog.update",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=("master-planning-catalog",),
        )
    print(json.dumps({
        "ok": code == 0, **confirmation,
        **({"errors": [str(error) for error in errors]} if errors else {}),
    }, indent=2, ensure_ascii=False))
    return code


def cmd_masters_planning_comparison_publish(args) -> int:
    root = _root(args)
    value = validate_candidate_comparison(
        root, _input_record(args, "prospective source comparison")
    )
    if value["candidate_module_id"] != args.candidate_module_id:
        raise WriteRefused("comparison candidate_module_id does not match the command")
    denied = _refuse_without_approval(args, "prospective comparison publication")
    if denied is not None:
        return denied
    _require_gateway_v2()
    with _operator_lock(root):
        value = validate_candidate_comparison(root, value)
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        destination = candidate_comparison_destination(root, value["id"])
        code, errors, confirmation = _write_transaction(
            root, {destination: _dump_yaml(value)},
            capability="masters-planning.comparison.publish",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=(args.candidate_module_id, value["id"]),
        )
    print(json.dumps({
        "ok": code == 0, **confirmation,
        **({"errors": [str(error) for error in errors]} if errors else {}),
    }, indent=2, ensure_ascii=False))
    return code


def cmd_route_identity_migrate(args) -> int:
    """Apply the exact reviewed v13 route diff as one Core transaction."""

    root = _root(args)
    denied = _refuse_without_approval(args, "route identity v13 migration")
    if denied is not None:
        return denied
    _require_gateway_v2()
    with _operator_lock(root):
        plan = plan_migration(root, review=args.review)
        if not plan.ready:
            problems = sorted({problem.code for problem in plan.problems})
            raise WriteRefused(
                f"ambiguous migration is not applicable; resolve problems: {problems}"
            )
        if not plan.changes:
            raise WriteRefused("route identity v13 migration has no changes to apply")
        actual_plan_sha256 = plan_sha256(plan)
        if args.plan_sha256 != actual_plan_sha256:
            raise WriteRefused(
                "route migration diff changed after approval "
                f"(expected {args.plan_sha256}, actual {actual_plan_sha256})"
            )
        if not _expected_ok(root, args.expected_snapshot):
            return 3

        artifact_ids: set[str] = set()
        for change in plan.changes:
            relative = change.path.relative_to(root).parts
            if len(relative) == 4 and relative[:2] == ("curriculum", "modules") \
                    and relative[3] == "source-map.yaml":
                artifact_ids.add(relative[2])
            elif len(relative) == 6 and relative[:2] == ("curriculum", "modules") \
                    and relative[3] == "units" and relative[5] == "unit.yaml":
                artifact_ids.add(relative[4])
            else:  # pragma: no cover - plan_migration owns this closed file set
                raise WriteRefused(
                    "route migration planned an undeclared canonical target: "
                    + change.path.relative_to(root).as_posix()
                )

        code, errors, confirmation = _write_transaction(
            root,
            {change.path: change.after for change in plan.changes},
            capability="route.identity.migrate",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=artifact_ids,
        )
    print(json.dumps({
        "ok": code == 0,
        "plan_sha256": actual_plan_sha256,
        "changed_files": [
            change.path.relative_to(root).as_posix() for change in plan.changes
        ],
        **confirmation,
        **({"errors": [str(error) for error in errors]} if errors else {}),
    }, indent=2, ensure_ascii=False))
    return code


def cmd_job_learning_migrate(args) -> int:
    """Collapse the exact approved legacy Job learning set into Core."""

    root = _root(args)
    denied = _refuse_without_approval(args, "legacy Job learning migration")
    if denied is not None:
        return denied
    _require_gateway_v2()
    with _operator_lock(root):
        plan = plan_job_learning_migration(root)
        if not plan.ready:
            problems = sorted({problem.code for problem in plan.problems})
            raise WriteRefused(
                f"legacy Job learning migration is not applicable; resolve: {problems}"
            )
        if not plan.changes and not plan.deletions:
            raise WriteRefused("legacy Job learning migration has no changes to apply")
        actual_plan_sha256 = job_learning_plan_sha256(plan)
        if args.plan_sha256 != actual_plan_sha256:
            raise WriteRefused(
                "legacy Job learning migration changed after approval "
                f"(expected {args.plan_sha256}, actual {actual_plan_sha256})"
            )
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        drift = verify_job_learning_plan_inputs(plan)
        if drift:
            summary = sorted({problem.code for problem in drift})
            raise WriteRefused(
                f"legacy Job learning inputs changed after approval: {summary}"
            )
        try:
            artifact_ids = migration_artifact_ids(plan)
        except ValueError as exc:  # closed target set owned by the planner
            raise WriteRefused(str(exc)) from exc

        code, errors, confirmation = _write_transaction(
            root,
            {change.path: change.after for change in plan.changes},
            deletes=(deletion.path for deletion in plan.deletions),
            capability="legacy.job-learning.migrate",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=artifact_ids,
        )
    print(json.dumps({
        "ok": code == 0,
        "plan_sha256": actual_plan_sha256,
        "statistics": dict(sorted(plan.statistics.items())),
        "changed_files": [
            change.path.relative_to(root).as_posix() for change in plan.changes
        ],
        "deleted_files": [
            deletion.path.relative_to(root).as_posix() for deletion in plan.deletions
        ],
        **confirmation,
        **({"errors": [str(error) for error in errors]} if errors else {}),
    }, indent=2, ensure_ascii=False))
    return code


def cmd_health_report(args) -> int:
    report = build_health_report(_root(args))
    print(json.dumps(report, indent=2, ensure_ascii=False))
    # Attention is report data, not a transport failure: the UI must be able to
    # render the remedies even when one check is red.
    return 0


def cmd_backup_manifest(args) -> int:
    manifest = build_backup_manifest(
        _root(args),
        ui_root=Path(args.ui_root).expanduser().resolve() if args.ui_root else None,
        materials_root=(Path(args.materials_root).expanduser().resolve()
                        if args.materials_root else None),
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


def cmd_backup_verify(args) -> int:
    root = _root(args)
    value = _read_structured_file(args.manifest)
    verifier = verify_backup_manifest if args.checksums_only else verify_restored_system
    result = verifier(
        root,
        value,
        restored_core=Path(args.restored_core).expanduser().resolve(),
        restored_ui=Path(args.restored_ui).expanduser().resolve(),
        restored_materials=Path(args.restored_materials).expanduser().resolve(),
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 1
