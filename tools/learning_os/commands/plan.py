"""Read-only access to the single versioned plan-creation template."""

from __future__ import annotations

import sys

import yaml

from learning_os.contracts import (
    ContractValidationError,
    PlanTemplateError,
    build_plan_template,
    validate_contract,
)

from .support import _root


def cmd_plan_template(args) -> int:
    root = _root(args)
    try:
        plan = build_plan_template(
            args.profile,
            title=args.title,
            unit_id=args.unit_id,
            module_id=args.module_id,
        )
        schema = "study-map.schema.json" if args.profile == "curriculum" else "job-plan.schema.json"
        validate_contract(root, schema, plan, label=f"{args.profile} plan template v1")
    except (PlanTemplateError, ContractValidationError) as exc:
        print(f"los: cannot build plan template: {exc}", file=sys.stderr)
        return 2
    print(yaml.safe_dump(plan, sort_keys=False, allow_unicode=True, width=100), end="")
    return 0
