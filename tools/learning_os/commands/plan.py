"""Read-only access to the single versioned study-map creation template.

Two output shapes, one generator. YAML is what an operator pastes into a new
plan file (system/PLAN-CREATION-SOP.md); `--json` is the ``plan.template``
query the Obsidian interface reads, so the app offers the same template the SOP
prescribes instead of carrying a second copy of the defaults. A template that
only a terminal can reach is a standard the interface cannot apply.
"""

from __future__ import annotations

import json
import sys

import yaml

from learning_os.contracts import (
    PLAN_TEMPLATE_VERSION,
    ContractValidationError,
    PlanTemplateError,
    build_plan_template,
    validate_contract,
)

from .support import _root

PLAN_TEMPLATE_CONTRACT = "plan-template-v1"

_PROFILE_SCHEMAS = {
    "curriculum": "study-map.schema.json",
}


def cmd_plan_template(args) -> int:
    root = _root(args)
    as_json = bool(getattr(args, "json", False))
    schema = _PROFILE_SCHEMAS[args.profile]
    try:
        plan = build_plan_template(
            args.profile,
            title=args.title,
            unit_id=args.unit_id,
            module_id=args.module_id,
        )
        validate_contract(root, schema, plan, label=f"{args.profile} plan template v1")
    except (PlanTemplateError, ContractValidationError) as exc:
        # A refusal has to reach the caller in the shape the caller reads.
        # The interface parses stdout as JSON and would otherwise report the
        # process failure instead of the reason.
        if as_json:
            print(json.dumps({"ok": False, "error": f"cannot build plan template: {exc}"}))
        else:
            print(f"los: cannot build plan template: {exc}", file=sys.stderr)
        return 2

    if not as_json:
        print(yaml.safe_dump(plan, sort_keys=False, allow_unicode=True, width=100), end="")
        return 0

    response = {
        "ok": True,
        "contract": PLAN_TEMPLATE_CONTRACT,
        "profile": args.profile,
        "plan_template_version": PLAN_TEMPLATE_VERSION,
        "schema": schema,
        "plan": plan,
    }
    try:
        validate_contract(
            root, "plan-template.schema.json", response, label=PLAN_TEMPLATE_CONTRACT
        )
    except ContractValidationError as exc:
        # The producer owns this response shape; shipping one that violates its
        # own declaration is the failure the declaration exists to prevent.
        print(json.dumps({"ok": False, "error": f"plan template response invalid: {exc}"}))
        return 2
    print(json.dumps(response, ensure_ascii=False))
    return 0
