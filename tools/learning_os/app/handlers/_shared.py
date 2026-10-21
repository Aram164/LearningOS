"""Raising twins of shared printing lookups (SPEC R3)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from learning_os.app.context import OpContext
from learning_os.app.gateway import context_from_v2 as _context_from_v2
from learning_os.app.gateway import read_structured_file as _read_structured_file
from learning_os.app.gateway import validate_capability_envelope as _validate_capability_envelope
from learning_os.app.proposal import GatewayDispatch
from learning_os.domain.failures import NotFound, ValidationFailed, WriteRefused
from learning_os.domain.suggest import not_found
from learning_os.store.revisions import artifact_revision

NOTES_PREFIX = Path("knowledge/notes")


def render_creation_check(record: dict, prepared: dict) -> dict:
    """Today's ``--check`` output from the shadow check record.

    The record is the canonical validation of the exact writes this
    request would make, staged on a shadow copy of the repository. A
    package the apply would refuse is refused here with the same text: a
    check that says ok for something the write refuses is worse than no
    check, because it is a promise the system does not keep.
    """
    if not record["ok"]:
        raise ValidationFailed(
            "canonical validation failed: "
            + "; ".join(map(str, record["errors"][:8])))
    return {
        **prepared,
        "ok": True,
        "check": True,
        "expected_snapshot": record["expected_snapshot"],
        "expected_revisions": record["expected_revisions"],
        "expected_write_paths": record["writes"],
        "warnings_delta": record.get("warnings_delta", []),
    }


def guard_rows(root, artifacts):
    return {rid: artifact_revision(root, rid) for rid in sorted(set(artifacts))}


def map_for_unit(repo, unit_id):
    maps = [sm for sm in repo.study_maps.values() if sm.unit_id == unit_id]
    if len(maps) > 1:
        raise WriteRefused(f"unit {unit_id} has ambiguous study maps")
    return maps[0] if maps else None


def input_record(req: dict, label: str) -> dict:
    """The inline record or structured file, from the request (SPEC §12).

    Moved from ``commands.collection_entry`` with ``args.<dest>`` retargeted
    to the request dict; the source and publish units share this copy.
    """
    value = req.get("record")
    if value is not None:
        if not isinstance(value, dict):
            raise WriteRefused(f"{label} must be an object")
        return value
    file_name = req.get("file")
    if not file_name:
        raise WriteRefused(f"{label} is required")
    return _read_structured_file(file_name)


def require_gateway_v2() -> None:
    """Refuse a direct CLI apply of an approved write (SPEC §12).

    Moved verbatim from ``commands.collection_entry``; the source units
    share this copy, and ``commands.vnext`` keeps its own for platform.
    """
    from learning_os.store.contracts.gateway import current_gateway_request

    if current_gateway_request() is None:
        raise WriteRefused(
            "this approved write must use GatewayEnvelopeV2; direct CLI publication is disabled"
        )


def inbox_search_rows(root: Path) -> list[dict]:
    """One discovery row per inbox file, matched on names only, never bytes.

    Inbox drops are arbitrary files (binary captures included), so the
    metadata search reads no content here: the haystack is the file name
    and path. Content stays behind ``inbox-read``, which refuses non-text.
    Raises OSError when the listing itself fails; a missing inbox is empty.
    """
    inbox = root / "work" / "inbox"
    if not inbox.is_dir():
        return []
    rows = []
    for path in sorted(inbox.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(inbox).as_posix()
        if any(part.startswith(".") for part in rel.split("/")):
            continue
        rows.append({"id": rel, "type": "inbox-item", "title": path.name,
                     "path": f"work/inbox/{rel}"})
    return rows

def discovery_row(rec):
    """One stable discovery row, shared by search and inbox-list."""
    return {k: rec.get(k) for k in
            ("id", "type", "title", "path", "status",
             "state", "deprecated")}

def content_envelope(contract, ref_key, ref, relpath, raw, content, offset, limit):
    return {
        "contract": contract, ref_key: ref, "path": relpath,
        "content_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "offset": offset, "offset_unit": "unicode_characters",
        "total_characters": len(content),
        "start_line": content.count("\n", 0, offset) + 1,
        "content": content[offset:offset + limit],
        "next_offset": offset + limit if offset + limit < len(content) else None,
    }

def window_values(offset: int, limit: int, expected_snapshot: str | None,
                   maximum: int) -> tuple[int, int]:
    """Offset/limit validation with the exact commands.reads._window rules."""
    if offset < 0 or not 1 <= limit <= maximum:
        raise WriteRefused(f"offset must be nonnegative and limit between 1 and {maximum}")
    if offset and not expected_snapshot:
        raise WriteRefused("continuation requires --expected-snapshot from the previous response")
    return offset, limit


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
            prefixed=True,
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
                            review_report: str | None) -> GatewayDispatch:
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
            prefixed=True,
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
            prefixed=True,
            exit_code=2,
        ) from exc
    return GatewayDispatch(envelope)
