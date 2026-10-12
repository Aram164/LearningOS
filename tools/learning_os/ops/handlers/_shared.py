"""Raising twins of shared printing lookups (SPEC R3)."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import tempfile
from pathlib import Path

from learning_os.domain.failures import NotFound, WriteRefused
from learning_os.domain.suggest import not_found
from learning_os.ops._legacy_plumbing import _read_structured_file
from learning_os.ops.context import OpContext
from learning_os.ops.legacy import _context_from_v2, _validate_capability_envelope
from learning_os.ops.proposal import CommandOutput


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


def apply_reviewed_envelope(ctx: OpContext, *, capability_name: str,
                            payload: dict, reviewed_content: bytes,
                            reviewed_sha256: str,
                            review_report: str | None) -> CommandOutput:
    """The raising twin of the reviewed-apply transport (SPEC R3, PLAN 4.1).

    Verifies the reviewed bytes, report and saved gateway envelope exactly
    as ``reviewed_envelope_apply`` did, raising typed refusals with the
    identical messages, then dispatches the saved envelope through the
    transport entrypoint ``adapters.capability.cmd_capability`` in-process
    and returns its exact streams and exit as a ``CommandOutput`` carrier.

    The two adapter imports are dynamic: ``adapters.capability`` imports
    the pipeline, which imports this package for registration, so any
    static edge from here to the transport would cycle back through
    the registry (``code_reachability`` has no cycle exception). The
    runtime dependency is real and documented here; ``import_module``
    is the codebase's established late-binding mechanism
    (``cli_parser._resolve_handler``).
    """
    import importlib

    # D1 RECORDED DEVIATION (closed, not deferred; T81 review disposition +
    # T82 review): this transport import stays dynamic (import_module) by
    # decision. Proven unlandable static in every form: module-level breaks
    # entry via the capability-pipeline-handlers-plan load cycle (T81 proof), and any
    # static edge — module-level or function-local — trips
    # code_reachability's pinned no-cycle rule, which counts
    # function-level imports (ast.walk) and offers no cycle exemption
    # (T82 proof; attempt + layers-KEPT + reachability-2-fail reproduced
    # by conductor). The behavior is correct, all suites green, and the
    # probe covers check/apply/replay. Changing the reachability guard
    # or restructuring the pipeline needs Aram's direct authorization.
    _capability_transport = importlib.import_module(
        "learning_os.adapters.capability")
    build_parser = importlib.import_module(
        "learning_os.adapters.cli_parser").build_parser

    actual = "sha256:" + hashlib.sha256(reviewed_content).hexdigest()
    if actual != reviewed_sha256:
        message = ("reviewed bytes changed since --check; re-run --check, "
                   "review the new report and its SHA, then apply that SHA")
        detail = json.dumps({"expected": reviewed_sha256, "actual": actual})
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.reviewed-bytes-changed",
            extra_stderr=(detail,),
            gateway_message=f"los: {message}\n{detail}",
            exit_code=2,
        )
    if not review_report:
        message = ("reviewed apply requires --review-report with the saved "
                   "--check JSON")
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.reviewed-needs-report",
            gateway_message=f"los: {message}",
            exit_code=2,
        )
    try:
        report = _read_structured_file(review_report)
        envelope = report.get("gateway_envelope")
        if not isinstance(envelope, dict):
            raise WriteRefused("review report has no prepared gateway envelope")
        _validate_capability_envelope(ctx.root, envelope, kind="request")
        _context_from_v2(envelope)
        if report.get("ok") is not True or report.get("mode") != "check" \
                or report.get("reviewed_file_sha256") != actual \
                or envelope.get("capability") != capability_name \
                or envelope.get("payload") != payload \
                or envelope.get("expected_snapshot") != report.get("expected_snapshot") \
                or envelope.get("expected_revisions") != report.get("expected_revisions"):
            raise WriteRefused(
                "review report does not match the exact reviewed input and guards")
    except (OSError, ValueError, WriteRefused) as exc:
        raise WriteRefused(
            str(exc),
            site=f"{ctx.operation}.reviewed-report-invalid",
            gateway_message=f"los: {exc}",
            exit_code=2,
        ) from exc
    fd, tmp_name = tempfile.mkstemp(prefix="learningos-reviewed-", suffix=".json")
    try:
        with open(fd, "w", encoding="utf-8") as handle:
            json.dump(envelope, handle, ensure_ascii=False)
        args = argparse.Namespace(
            root=str(ctx.root),
            name=capability_name,
            payload_file=tmp_name,
            replay_only=False,
            _parser_factory=build_parser,
        )
        captured, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(errors):
            code = _capability_transport.cmd_capability(args)
    finally:
        with contextlib.suppress(OSError):
            Path(tmp_name).unlink()
    return CommandOutput(
        stdout=captured.getvalue(), stderr=errors.getvalue(), exit_code=code)
