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
def cmd_ai_action_import_delivery(args) -> int:
    root = _root(args)
    with _operator_lock(root):
        service = AIActionService(root)
        delivery = service.import_delivery(Path(args.path))
        _publish(root)
    print(json.dumps({"ok": True, "delivery": delivery}, indent=2, ensure_ascii=False))
    return 0
