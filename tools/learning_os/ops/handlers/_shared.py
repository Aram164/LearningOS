"""Raising twins of shared printing lookups (SPEC R3)."""

from __future__ import annotations

from learning_os.domain.failures import NotFound, WriteRefused
from learning_os.domain.suggest import not_found
from learning_os.ops.context import OpContext


def require_unit_map_or_error(ctx: OpContext, unit_id: str):
    """The raising twin of support._unit_map_or_error (SPEC R3).

    Loads through ``ctx.repo()`` and returns the same
    ``(repo, unit, study_map)`` triple; both refusals raise with the
    original's identical messages.
    """
    repo = ctx.repo()
    unit = repo.units.get(unit_id)
    if unit is None:
        message = not_found("unit", unit_id, repo.units)
        raise NotFound(
            "unit", unit_id, repo.units,
            site=f"{ctx.operation}.unknown-unit",
            gateway_message=f"los: {message}",
            exit_code=2,
        )
    map_id = unit.data.get("current_study_map")
    study_map = repo.study_maps.get(map_id) if map_id else None
    if study_map is None:
        raise WriteRefused(
            f"unit has no current study map: {unit_id}",
            site=f"{ctx.operation}.no-study-map",
            gateway_message=f"los: unit has no current study map: {unit_id}",
            exit_code=2,
        )
    return repo, unit, study_map


def require_path_or_error(ctx: OpContext, path_id: str):
    """The raising twin of support._path_or_error (SPEC R3).

    Loads through ``ctx.repo()`` and returns the same
    ``(repo, learning_path)`` pair; the refusal raises with the
    original's identical message.
    """
    repo = ctx.repo()
    learning_path = repo.learning_paths.get(path_id)
    if learning_path is None or learning_path.archived:
        active = [key for key, row in repo.learning_paths.items()
                  if not row.archived]
        message = not_found("active learning path", path_id, active)
        raise NotFound(
            "active learning path", path_id, active,
            site=f"{ctx.operation}.unknown-path",
            gateway_message=f"los: {message}",
            exit_code=2,
        )
    return repo, learning_path


def require_stage(ctx: OpContext, data: dict, stage_id: str):
    """The raising twin of the support._stage lookup with its refusal (SPEC R3).

    Returns the stage row; the unknown-stage refusal raises with the
    caller's identical message and candidates.
    """
    stage = next((row for row in data.get("stages", []) or []
                  if isinstance(row, dict) and row.get("id") == stage_id), None)
    if stage is None:
        ids = [str(row["id"]) for row in data.get("stages", []) or []
               if isinstance(row, dict) and row.get("id")]
        message = not_found("stage", stage_id, ids)
        raise NotFound(
            "stage", stage_id, ids,
            site=f"{ctx.operation}.unknown-stage",
            gateway_message=f"los: {message}",
            exit_code=2,
        )
    return stage
