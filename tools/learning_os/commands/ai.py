"""Bounded AI actions: prepare a request bundle, import and apply an approved delivery."""

from __future__ import annotations

import json
from pathlib import Path

from learning_os.ai_actions import (
    AIActionService,
)
from learning_os.ops._legacy_plumbing import (
    _operator_lock,
    _publish,
)

from .support import (
    _root,
)


# ------------------------------------------------------------- AI actions
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


def cmd_ai_action_append_slices(args) -> int:
    root = _root(args)
    with _operator_lock(root):
        service = AIActionService(root)
        result = service.append_slices(
            request_id=args.request_id, route_id=args.route_id,
            start=args.start, end=args.end, kind=args.kind,
            concept_ids=args.concept_id or [], reason=args.reason,
            material_uri=args.material_uri, expected_snapshot=args.expected_snapshot,
        )
        _publish(root)
    print(json.dumps({"ok": True, "continuation": result}, indent=2, ensure_ascii=False))
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


def cmd_ai_action_status(args) -> int:
    request = AIActionService(_root(args)).request_status(args.request_id)
    print(json.dumps({"ok": True, "request": request}, indent=2, ensure_ascii=False))
    return 0
