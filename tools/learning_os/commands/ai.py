"""Bounded AI actions: prepare a request bundle, import and apply an approved delivery."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from learning_os.ai_actions import AIActionError, AIActionService, StaleDeliveryError
from learning_os.contracts.gateway import current_gateway_request

from .support import (
    WriteRefused,
    _expected_revisions_from_args,
    _operator_lock,
    _publish,
    _record_touched,
    _root,
)


# ------------------------------------------------------------- AI actions
def cmd_ai_action_list(args) -> int:
    actions = AIActionService(_root(args)).list_actions()
    print(json.dumps({"ok": True, "actions": actions}, indent=2, ensure_ascii=False))
    return 0


def cmd_ai_action_prepare(args) -> int:
    root = _root(args)
    with _operator_lock(root):
        service = AIActionService(root)
        request = service.prepare(
            action_id=args.action_id, target_kind=args.target_kind,
            target_id=args.target_id, provider=args.provider,
            expected_snapshot=args.expected_snapshot, request_id=args.request_id,
        )
        _publish(root)
    print(json.dumps({
        "ok": True, "request": service.request_status(request["id"]),
        "bundle_path": service.repository.request_dir(request["id"]).relative_to(root).as_posix(),
    }, indent=2, ensure_ascii=False))
    return 0


def cmd_ai_action_import_delivery(args) -> int:
    root = _root(args)
    with _operator_lock(root):
        service = AIActionService(root)
        delivery = service.import_delivery(Path(args.path))
        _publish(root)
    print(json.dumps({"ok": True, "delivery": delivery}, indent=2, ensure_ascii=False))
    return 0


def cmd_ai_action_validate_delivery(args) -> int:
    result = AIActionService(_root(args)).validate_delivery(args.delivery_id)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def cmd_ai_action_apply_delivery(args) -> int:
    root = _root(args)
    authority = current_gateway_request()
    if authority is None:
        raise WriteRefused(
            "approved delivery application must use GatewayEnvelopeV2"
        )
    if authority.capability != "ai-action.delivery.apply" \
            or authority.approval_kind != "approved-delivery":
        raise WriteRefused(
            "ai-action.delivery.apply requires approved-delivery approval"
        )
    try:
        with _operator_lock(root):
            receipt = AIActionService(root).apply_delivery(
                args.delivery_id,
                delivery_sha256=args.delivery_sha256,
                artifact_sha256=args.artifact_sha256,
                expected_snapshot=args.expected_snapshot,
                expected_revisions=_expected_revisions_from_args(args),
            )
            touched = [root / rel for rel in receipt.pop("touched_paths", [])]
            if touched:
                _record_touched(root, touched)
    except StaleDeliveryError as exc:
        print(str(exc), file=sys.stderr)
        return 3
    except AIActionError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps({
        "ok": True,
        "transaction_id": receipt["transaction_id"],
        "receipt_path": receipt["receipt_path"],
        "snapshot_after": receipt["snapshot_after"],
        "artifact_revisions": receipt["revision_updates"],
        "replayed": receipt.get("replayed", False),
        "receipt": receipt,
    }, indent=2, ensure_ascii=False))
    return 0


def cmd_ai_action_status(args) -> int:
    request = AIActionService(_root(args)).request_status(args.request_id)
    print(json.dumps({"ok": True, "request": request}, indent=2, ensure_ascii=False))
    return 0
