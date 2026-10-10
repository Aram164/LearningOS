"""Admin-area converted handlers (PLAN D4)."""

from __future__ import annotations

import copy
import datetime as _dt
import json

from learning_os.domain.failures import NotFound, WriteRefused
from learning_os.domain.suggest import not_found
from learning_os.ops._legacy_plumbing import _dump_yaml
from learning_os.ops.context import OpContext
from learning_os.ops.proposal import Result, TransactionProposal
from learning_os.ops.registry import register
from learning_os.transactions import parse_expected_revisions

ATTEMPT_RESULTS = ("registered", "withdrawn", "sat", "passed", "failed")


def _dumps_admin(payload: dict) -> str:
    """The exact admin encoder: default separators, unescaped."""
    return json.dumps(payload, ensure_ascii=False)


def _refused_first_twelve(errors: list) -> list[str]:
    """The exact commit-refusal lines: the first twelve engine issues, verbatim."""
    return list(errors[:12])


@register("module.attempt.record", kind="command")
def module_attempt(ctx: OpContext, req: dict) -> Result:
    """Record one exam attempt fact in the owning module's module.yaml."""
    if req["termin"] not in (1, 2, 3):
        message = f"--termin must be 1, 2 or 3, got {req['termin']!r}"
        raise WriteRefused(
            message,
            site="module.attempt.record.bad-termin",
            gateway_message=f"los: {message}",
            exit_code=2,
        )
    if req["result"] not in ATTEMPT_RESULTS:
        message = (f"--result must be one of {', '.join(ATTEMPT_RESULTS)}, "
                   f"got {req['result']!r}")
        raise WriteRefused(
            message,
            site="module.attempt.record.bad-result",
            gateway_message=f"los: {message}",
            exit_code=2,
        )
    try:
        _dt.date.fromisoformat(req["date"])
    except (TypeError, ValueError) as exc:
        message = (f"--date must be an ISO date (YYYY-MM-DD), "
                   f"got {req['date']!r}")
        raise WriteRefused(
            message,
            site="module.attempt.record.bad-date",
            gateway_message=f"los: {message}",
            exit_code=2,
        ) from exc
    grade = req.get("grade")
    if grade is not None:
        if isinstance(grade, bool) or not isinstance(grade, (int, float)):
            message = ("--grade must be a number between 1.0 and 5.0, "
                       f"got {grade!r}")
            raise WriteRefused(
                message,
                site="module.attempt.record.bad-grade",
                gateway_message=f"los: {message}",
                exit_code=2,
            )
        grade = float(grade)
        if not 1.0 <= grade <= 5.0:
            message = ("--grade must be between 1.0 and 5.0, "
                       f"got {req['grade']!r}")
            raise WriteRefused(
                message,
                site="module.attempt.record.grade-out-of-range",
                gateway_message=f"los: {message}",
                exit_code=2,
            )
    ctx.require_snapshot(req.get("expected_snapshot"))
    repo = ctx.repo()
    module = repo.modules.get(req["module_id"])
    if module is None:
        message = not_found("module", req["module_id"], repo.modules)
        raise NotFound(
            "module", req["module_id"], repo.modules,
            site="module.attempt.record.unknown-module",
            gateway_message=f"los: {message}",
            exit_code=2,
        )
    module_path = repo.module_origins[req["module_id"]]
    data = copy.deepcopy(module)
    attempts = data.get("attempts") or []
    data["attempts"] = attempts
    row = next((candidate for candidate in attempts
                if isinstance(candidate, dict)
                and candidate.get("termin") == req["termin"]), None)
    if row is None:
        row = {"termin": req["termin"]}
        attempts.append(row)
    row["date"] = req["date"]
    row["result"] = req["result"]
    if grade is not None:
        row["grade"] = grade
    if req.get("notes") is not None:
        row["notes"] = req["notes"]
    try:
        expected_revisions = parse_expected_revisions(
            req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site="module.attempt.record.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "module_id": req["module_id"], "attempt": row},
        proposal=TransactionProposal(
            capability="module.attempt.record",
            writes={module_path: _dump_yaml(data)},
            artifact_ids=[req["module_id"]],
            expected_revisions=expected_revisions,
        ),
        on_commit_refused=_refused_first_twelve,
        json_dumps=_dumps_admin,
    )
