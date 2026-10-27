"""One schema authority for agent-plan input shapes."""
from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from learning_os.domain.agent_plans import PlanInput, PlanStepError

SCHEMA_PATH = Path(__file__).resolve().parents[4] / "system/contracts/agent-plan-input.schema.json"

def validate_input(plan: object) -> PlanInput:
    try:
        body = json.dumps(plan, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise PlanStepError("plan must contain finite JSON values") from exc
    if len(body.encode("utf-8")) > 1048576:
        raise PlanStepError("plan input exceeds 1 MiB")
    schema = json.loads(SCHEMA_PATH.read_text())
    errors = sorted(Draft202012Validator(schema).iter_errors(plan), key=lambda e: str(list(e.absolute_path)))
    if errors:
        error = errors[0]
        if list(error.absolute_path) == ["schema_version"]:
            raise PlanStepError("unsupported schema_version; migrate the plan to schema_version: 2")
        location = ".".join(map(str, error.absolute_path)) or "plan"
        raise PlanStepError(f"invalid plan at {location}: {error.message}")
    return cast(PlanInput, plan)
