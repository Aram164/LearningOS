"""LearningOS vNext comparison, archive, planning, backup, and health commands."""

from __future__ import annotations

import json

from learning_os.contracts.gateway import current_gateway_request
from learning_os.domain.failures import WriteRefused
from learning_os.legacy_archive import (
    legacy_archive_lock_destination,
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
    publication_lineage,
    synthesis_destination,
    validate_unit_material_synthesis,
)
from learning_os.ops._legacy_plumbing import (
    _dump_yaml,
    _operator_lock,
    _read_structured_file,
)
from learning_os.semantics.lineage import LEDGER_RELATIVE

from .support import (
    _expected_ok,
    _expected_revisions_from_args,
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
        content = _dump_yaml(value)
        request = current_gateway_request()
        lineage = publication_lineage(root, args.unit_id, value, content, request)
        code, errors, confirmation = _write_transaction(
            root,
            {destination: content, root / LEDGER_RELATIVE: lineage},
            capability="unit.material-synthesis.publish",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=(args.unit_id, value["id"]),
        )
    print(json.dumps({
        "ok": code == 0, **confirmation,
        **({"errors": [str(error) for error in errors]} if errors else {}),
    }, indent=2, ensure_ascii=False))
    return code


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
