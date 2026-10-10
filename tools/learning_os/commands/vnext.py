"""LearningOS vNext comparison, archive, planning, backup, and health commands."""

from __future__ import annotations

import json

from learning_os.contracts.gateway import current_gateway_request
from learning_os.domain.failures import WriteRefused
from learning_os.masters_planning import (
    candidate_comparison_destination,
    validate_candidate_comparison,
)
from learning_os.material_synthesis import (
    current_unit_material_basis,
    publication_lineage,
    synthesis_destination,
    validate_unit_material_synthesis,
)
from learning_os.ops._legacy_plumbing import (
    _dump_yaml,
    _input_record_values,
    _operator_lock,
    _require_gateway_v2,
)
from learning_os.semantics.lineage import LEDGER_RELATIVE

from .support import (
    _expected_ok,
    _expected_revisions_from_args,
    _root,
    _write_transaction,
)


def _input_record(args, label: str) -> dict:
    return _input_record_values(
        getattr(args, "record", None), getattr(args, "file", None), label)


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
