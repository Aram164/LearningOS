"""Learner-area converted handlers (PLAN D4)."""

from __future__ import annotations

import copy
import json
import re
import sys
from datetime import UTC
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from learning_os import observations
from learning_os.abilities import (
    ability_fingerprint,
    read_ability_observations,
)
from learning_os.contracts.gateway import (
    GatewayRequestContext,
    current_gateway_request,
    gateway_request_context,
    intent_sha256,
    verified_gateway_snapshot,
)
from learning_os.domain.failures import NotFound, Unconfirmed, WriteRefused
from learning_os.domain.suggest import not_found, with_suggestions
from learning_os.learning_runtime import (
    RuntimeInputError,
    collect_requirements,
    read_observations,
    read_stage_results,
    requirement_fingerprint,
    requirement_id_for,
    runtime_path,
    validate_runtime_record,
)
from learning_os.ops._legacy_plumbing import (
    _dump_study_map,
    _dump_yaml,
    _read_content_bound_file,
)
from learning_os.ops.context import OpContext
from learning_os.ops.encoders import dumps_ascii, dumps_unescaped
from learning_os.ops.handlers._shared import (
    require_path_or_error,
    require_stage,
    require_unit_map_or_error,
)
from learning_os.ops.legacy import gesture_allowed
from learning_os.ops.proposal import Result, TransactionProposal
from learning_os.ops.registry import register
from learning_os.revisions import artifact_revision
from learning_os.routes import route_with_identity
from learning_os.transactions import parse_expected_revisions
from learning_os.unit_notes import unit_note_marker


def _on_commit_refused(errors: list) -> list[str]:
    """The exact commit-refusal lines: the first twelve engine issues, verbatim."""
    return list(errors[:12])


STAGE_RESULT_CAPABILITY = "learner.stage-result.append"


#: The one return-to-work record. `los resume` and the app's Home both start
#: here, so they cannot disagree about where the learner left off.
#: Moved verbatim from commands.support with its only writer (SPEC 12).
RESUME_POINTER_PATH = "curriculum/resume.yaml"


def _resume_pointer_write(root: Path, *, module_id: str, unit_id: str,
                          study_map_id: str, stage_id: str) -> dict[Path, str]:
    """The resume-pointer file for one explicit study action.

    Returned as a ``{path: text}`` fragment to merge into the *same*
    ``_write_transaction`` as the records that moved. That is the whole point:
    the pointer is written under the operator lock the caller already holds,
    inside the capability's declared write scope, covered by the same receipt,
    the same post-action scope check, the same validation and the same
    republished projection. A separate write after the transaction would be an
    untracked side effect that could survive a rolled-back change, or be lost
    while the change committed — and the destination would then be lying about
    where the work actually is.

    Until 2026-09-13 nothing wrote this file at all. `curriculum/resume.yaml`
    did not exist; `los resume` silently recovered through "last recorded
    result", and the app's Home, which reads only this pointer, said "Nothing
    to resume yet". Activating a stage in another subject therefore left both
    interfaces pointing at the old one (audit
    `workbench/audits/synthetic-learner-2026-09-12`, F05).
    """
    pointer = {
        "type": "resume-pointer",
        "module_id": str(module_id),
        "unit_id": str(unit_id),
        "study_map_id": str(study_map_id),
        "stage_id": str(stage_id),
        "updated": observations.today().isoformat(),
    }
    return {root / RESUME_POINTER_PATH: _dump_yaml(pointer)}


def _observe_offer(unit_id: str, stage: dict) -> dict:
    """The observation verb for one stage's requirement, or nothing.

    Pure and read-only: when the stage authors a runtime requirement, name
    the exact ``los observe`` invocation that would record evidence against
    it. Otherwise return no keys. Suggesting never writes — the ledger
    still moves only through ``los observe``.
    """
    target = stage.get("runtime_target")
    if not isinstance(target, dict):
        return {}
    requirement_id = requirement_id_for(unit_id, str(stage.get("id", "")))
    # Name the conditions this target actually declares. The offer used to
    # stop at activity and result, so the command it taught could not produce
    # evidence the interpreter would credit, and a difficulty reported through
    # it could not be read as a failure of this target at all (audit
    # `synthetic-learner-2026-09-12`, F02). The flags are prompts to state what
    # happened, never defaults to accept — an unmet condition is dropped, not
    # asserted.
    conditions = [str(name) for name in (target.get("conditions") or [])
                  if str(name).strip()]
    flags = "".join(f" --condition {name}" for name in conditions)
    offer = {
        "observe_requirement": requirement_id,
        "observe_next": f"los observe {requirement_id} --activity <what-you-did> "
                        f"--result <correct|incorrect|partial|abandoned>{flags}",
    }
    if conditions:
        offer["observe_conditions"] = conditions
        offer["observe_note"] = (
            "keep only the conditions that actually held; an omitted one is "
            "read as unknown, never as met"
        )
    return offer


@register("stage.progress.update", kind="command")
def stage_progress(ctx: OpContext, req: dict) -> Result:
    """Move one stage's status and record progress against it."""
    ctx.require_snapshot(req.get("expected_snapshot"))
    _, unit, study_map = require_unit_map_or_error(ctx, req["unit_id"])
    data = copy.deepcopy(study_map.data)
    unit_data = copy.deepcopy(unit.data)
    stages = data.get("stages", []) or []
    stage = require_stage(ctx, data, req["stage_id"])
    action = req["status"]
    if action in {"active", "revisit"}:
        for other in stages:
            if other.get("status") in {"active", "paused"}:
                other["status"] = "pending"
        stage["status"] = "active"
        stage.pop("completed", None)
        data["current_stage"] = stage["id"]
        data["status"] = "active"
        unit_data["status"] = "active"
    elif action == "paused":
        stage["status"] = "paused"
        data["current_stage"] = stage["id"]
        data["status"] = "paused"
        unit_data["status"] = "paused"
    elif action in {"complete", "skipped"}:
        if stage.get("status") != "active":
            raise WriteRefused(
                "complete/skip applies only to the active stage; activate it first",
                site=f"{ctx.operation}.not-active",
                prefixed=True,
                exit_code=2,
            )
        stage["status"] = action
        if action == "complete":
            stage["completed"] = observations.today().isoformat()
        following = next((row for row in stages[stages.index(stage) + 1:]
                          if row.get("status") == "pending"), None)
        if following:
            following["status"] = "active"
            data["current_stage"] = following["id"]
            data["status"] = "active"
            unit_data["status"] = "active"
        else:
            data["status"] = "ready-to-shelve"
            data.setdefault("shelving", {})["state"] = "draft"
            unit_data["status"] = "ready-to-shelve"
    else:
        # The gateway schema and payload_to_namespace refuse unknown
        # values first; this is the last backstop. An open `else` here
        # once recorded an unknown status as `skipped`.
        raise WriteRefused(
            f"unknown stage status: {action} "
            "(choose from active, paused, complete, skipped, revisit)",
            site=f"{ctx.operation}.unknown-status",
            prefixed=True,
            exit_code=2,
        )
    summary = req.get("progress_summary")
    upcoming = req.get("progress_next")
    if summary is not None or upcoming is not None:
        if summary is None or not summary.strip():
            raise WriteRefused(
                "--progress-next needs --progress-summary",
                site=f"{ctx.operation}.needs-summary",
                prefixed=True,
                exit_code=2,
            )
        if upcoming is not None and not upcoming.strip():
            raise WriteRefused(
                "--progress-next must not be blank",
                site=f"{ctx.operation}.blank-next",
                prefixed=True,
                exit_code=2,
            )
        entry = {"updated": observations.today().isoformat(),
                 "summary": summary.strip()}
        if upcoming is not None:
            entry["next"] = upcoming.strip()
        stage["progress"] = entry
    # One rule for every branch: the destination is the stage this action
    # just made current. Activate or revisit and you return to it; pause it
    # and you return to the thing you paused, which is what pausing means;
    # complete or skip and you return to the stage that became current
    # after it, or — when the map has run out of stages — to the finished
    # one, where `resume` can honestly say it is ready to shelve. Other
    # units keep their own active maps; this names where *he* is, not what
    # is open.
    resume_stage = str(data.get("current_stage") or stage["id"])
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site=f"{ctx.operation}.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "unit_id": req["unit_id"], "stage_id": req["stage_id"],
         "status": action, "map_status": data["status"],
         "current_stage": data["current_stage"],
         **({"progress": stage["progress"]} if "progress" in stage else {}),
         **_observe_offer(req["unit_id"], stage)},
        proposal=TransactionProposal(
            capability="stage.progress.update",
            writes={study_map.path: _dump_study_map(study_map, data),
                    unit.path: _dump_yaml(unit_data),
                    **_resume_pointer_write(
                        ctx.root, module_id=unit.module_id, unit_id=req["unit_id"],
                        study_map_id=study_map.id, stage_id=resume_stage)},
            artifact_ids=[req["unit_id"], study_map.id],
            expected_revisions=expected_revisions,
        ),
        on_commit_refused=_on_commit_refused,
        json_dumps=dumps_unescaped,
    )


@register("stage.note.write", kind="command")
def stage_note(ctx: OpContext, req: dict) -> Result:
    """Append to (or replace) a stage's working note."""
    root = ctx.root
    ctx.require_snapshot(req.get("expected_snapshot"))
    _, _, study_map = require_unit_map_or_error(ctx, req["unit_id"])
    stage = require_stage(ctx, study_map.data, req["stage_id"])
    target = root / str(stage.get("working_note", ""))
    if not stage.get("working_note"):
        raise WriteRefused(
            "stage has no working_note",
            site="stage.note.write.no-working-note",
            prefixed=True,
            exit_code=2,
        )
    value = req.get("text") if req.get("text") is not None else sys.stdin.read()
    if not value.strip():
        # `--replace --text ""` used to truncate an existing note to zero
        # bytes and report success. Emptying a note is a deliberate edit,
        # not something a save button should ever do.
        raise WriteRefused(
            "refusing to write an empty note — pass real text",
            site="stage.note.write.empty-note",
            prefixed=True,
            exit_code=2,
        )
    old = target.read_text(encoding="utf-8") if target.is_file() else ""
    if req.get("replace"):
        updated = value.rstrip() + ("\n" if value.strip() else "")
    else:
        divider = "\n" if old and not old.endswith("\n\n") else ""
        updated = old + divider + value.rstrip() + "\n"
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site="stage.note.write.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "unit_id": req["unit_id"],
         "stage_id": req["stage_id"], "working_note": stage["working_note"]},
        proposal=TransactionProposal(
            capability="stage.note.write",
            writes={target: updated},
            artifact_ids=[req["unit_id"]],
            expected_revisions=expected_revisions,
        ),
        on_commit_refused=_on_commit_refused,
        json_dumps=dumps_unescaped,
    )


def _allocate_attachment_path(attachment_dir: Path, source_name: str) -> Path:
    """A destination no existing attachment occupies.

    Attachment bytes are approved canonical content, so the previous holder of a
    name must never be overwritten. A timestamp was not a uniqueness argument:
    it is precise to one second and the name it produced was never itself
    checked, so two uploads of `handwriting.png` within the same second silently
    replaced the first one's bytes.

    Every candidate is checked now, and the counter guarantees the search ends
    on a free name. Checking existence is sufficient here — and only here —
    because every caller allocates while holding the operator lock, so no other
    process can take the name between this check and the transaction that writes
    it.
    """
    target = attachment_dir / source_name
    if not target.exists():
        return target

    stamp = observations.now().replace(tzinfo=None).strftime("%Y%m%d-%H%M%S")
    target = attachment_dir / f"{stamp}-{source_name}"
    if not target.exists():
        return target

    counter = 1
    while True:
        target = attachment_dir / f"{stamp}-{counter}-{source_name}"
        if not target.exists():
            return target
        counter += 1


@register("stage.attachment.add", kind="command")
def stage_attach(ctx: OpContext, req: dict) -> Result:
    """Attach a content-bound file beside a stage's working note."""
    root = ctx.root
    try:
        source, source_bytes = _read_content_bound_file(
            req["file"],
            req.get("file_sha256"),
            label="stage attachment",
        )
    except WriteRefused as exc:
        raise WriteRefused(
            str(exc),
            site="stage.attachment.add.bad-file",
            prefixed=True,
            exit_code=2,
        ) from exc
    ctx.require_snapshot(req.get("expected_snapshot"))
    _, _, study_map = require_unit_map_or_error(ctx, req["unit_id"])
    data = copy.deepcopy(study_map.data)
    stage = require_stage(ctx, data, req["stage_id"])
    note_path = root / stage["working_note"]
    attachment_dir = note_path.parent / "attachments"
    target = _allocate_attachment_path(attachment_dir, source.name)
    rel = target.relative_to(root).as_posix()
    stage.setdefault("attachments", []).append(
        {"path": rel, "label": req.get("label") or source.stem})
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site="stage.attachment.add.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "unit_id": req["unit_id"],
         "stage_id": req["stage_id"], "attachment": rel},
        proposal=TransactionProposal(
            capability="stage.attachment.add",
            writes={study_map.path: _dump_study_map(study_map, data),
                    target: source_bytes},
            artifact_ids=[req["unit_id"], study_map.id],
            expected_revisions=expected_revisions,
        ),
        on_commit_refused=_on_commit_refused,
        json_dumps=dumps_unescaped,
    )


@register("path.note.write", kind="command")
def path_note(ctx: OpContext, req: dict) -> Result:
    """Append to (or replace) a learning-path stage note."""
    root = ctx.root
    ctx.require_snapshot(req.get("expected_snapshot"))
    _, learning_path = require_path_or_error(ctx, req["path_id"])
    stage = require_stage(ctx, learning_path.data, req["stage_id"])
    note_ref = stage.get("notes_path")
    if not note_ref:
        raise WriteRefused(
            f"stage has no notes_path: {req['stage_id']}",
            site="path.note.write.no-notes-path",
            prefixed=True,
            exit_code=2,
        )
    text_value = req.get("text") if req.get("text") is not None else sys.stdin.read()
    if not text_value.strip():
        raise WriteRefused(
            "refusing to write an empty note — pass real text",
            site="path.note.write.empty-note",
            prefixed=True,
            exit_code=2,
        )
    target = root / str(note_ref)
    old = target.read_text(encoding="utf-8") if target.is_file() else ""
    if req.get("replace"):
        updated = text_value.rstrip() + ("\n" if text_value.strip() else "")
    else:
        divider = "\n" if old and not old.endswith("\n\n") else ""
        updated = old + divider + text_value.rstrip() + "\n"
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site="path.note.write.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "path_id": req["path_id"],
         "stage_id": req["stage_id"], "notes_path": note_ref},
        proposal=TransactionProposal(
            capability="path.note.write",
            writes={target: updated},
            artifact_ids=[req["path_id"]],
            expected_revisions=expected_revisions,
        ),
        on_commit_refused=_on_commit_refused,
        json_dumps=dumps_unescaped,
    )


def _on_path_progress_refused(errors: list) -> list[str]:
    """The exact path-progress commit-refusal lines: the prefix plus the first twelve engine issues, verbatim."""
    return ["los: path update rejected by validation", *errors[:12]]


@register("path.progress.update", kind="command")
def path_progress(ctx: OpContext, req: dict) -> Result:
    """Move one learning-path stage's status."""
    ctx.require_snapshot(req.get("expected_snapshot"))
    _, learning_path = require_path_or_error(ctx, req["path_id"])
    data = learning_path.data
    stages = data.get("stages", []) or []
    stage = require_stage(ctx, data, req["stage_id"])
    if req["status"] in {"complete", "skipped"} and stage.get("status") != "active":
        raise WriteRefused(
            "only the active stage can be completed or skipped; activate it first",
            site="path.progress.update.not-active",
            prefixed=True,
            exit_code=2,
        )
    if req["status"] == "active":
        for other in stages:
            if other.get("status") == "active":
                other["status"] = "pending"
        stage["status"] = "active"
        stage.pop("completed", None)
        data["current_stage"] = stage["id"]
        data["status"] = "active"
    elif req["status"] in {"complete", "skipped"}:
        stage["status"] = req["status"]
        if req["status"] == "complete":
            stage["completed"] = observations.today().isoformat()
        following = next((s for s in stages[stages.index(stage) + 1:]
                          if s.get("status") == "pending"), None)
        if following:
            following["status"] = "active"
            data["current_stage"] = following["id"]
            data["status"] = "active"
        else:
            data["status"] = "ready-to-shelve"
            shelving = data.setdefault("shelving", {})
            shelving["state"] = "draft"
    else:
        raise WriteRefused(
            f"unknown path status: {req['status']} "
            "(choose from active, complete, skipped)",
            site="path.progress.update.unknown-status",
            prefixed=True,
            exit_code=2,
        )
    data["updated"] = observations.today().isoformat()
    rendered = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site="path.progress.update.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "path_id": req["path_id"],
         "stage_id": req["stage_id"], "status": req["status"],
         "path_status": data["status"],
         "current_stage": data["current_stage"]},
        proposal=TransactionProposal(
            capability="path.progress.update",
            writes={learning_path.path: rendered},
            artifact_ids=[req["path_id"]],
            expected_revisions=expected_revisions,
        ),
        on_commit_refused=_on_path_progress_refused,
        json_dumps=dumps_unescaped,
    )


def _on_path_attach_refused(errors: list) -> list[str]:
    """The exact path-attach commit-refusal lines: the prefix plus the first twelve engine issues, verbatim."""
    return ["los: attachment rejected by validation", *errors[:12]]


@register("path.attachment.add", kind="command")
def path_attach(ctx: OpContext, req: dict) -> Result:
    """Attach a content-bound file to a learning-path stage."""
    root = ctx.root
    try:
        source, source_bytes = _read_content_bound_file(
            req["file"],
            req.get("file_sha256"),
            label="path attachment",
        )
    except WriteRefused as exc:
        raise WriteRefused(
            str(exc),
            site="path.attachment.add.bad-file",
            prefixed=True,
            exit_code=2,
        ) from exc
    ctx.require_snapshot(req.get("expected_snapshot"))
    _, learning_path = require_path_or_error(ctx, req["path_id"])
    data = learning_path.data
    stage = require_stage(ctx, data, req["stage_id"])
    workspace = learning_path.path.parent.parent
    attachment_dir = workspace / "scratch" / "paths" / learning_path.id \
        / "attachments" / stage["id"]
    target = _allocate_attachment_path(attachment_dir, source.name)
    rel = target.relative_to(root).as_posix()
    stage.setdefault("attachments", []).append({
        "path": rel, "label": req.get("label") or source.stem})
    data["updated"] = observations.today().isoformat()
    rendered = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site="path.attachment.add.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "path_id": req["path_id"],
         "stage_id": req["stage_id"], "attachment": rel},
        proposal=TransactionProposal(
            capability="path.attachment.add",
            writes={learning_path.path: rendered, target: source_bytes},
            artifact_ids=[req["path_id"]],
            expected_revisions=expected_revisions,
        ),
        on_commit_refused=_on_path_attach_refused,
        json_dumps=dumps_unescaped,
    )


@register("detour.create", kind="command")
def detour_create(ctx: OpContext, req: dict) -> Result:
    """Open a scoped detour off one stage."""
    ctx.require_snapshot(req.get("expected_snapshot"))
    _, unit, study_map = require_unit_map_or_error(ctx, req["unit_id"])
    data = copy.deepcopy(study_map.data)
    stage = require_stage(ctx, data, req["stage_id"])
    base = re.sub(r"[^a-z0-9]+", "-", req["title"].lower()).strip("-") or "gap"
    did = f"detour-{base}"
    existing = {row.get("id") for row in data.get("detours", []) or []}
    if did in existing:
        suffix = 2
        while f"{did}-{suffix}" in existing:
            suffix += 1
        did = f"{did}-{suffix}"
    detour = {"id": did, "title": req["title"], "spawned_by_stage": req["stage_id"],
              "classification": req["classification"], "status": "open",
              "return_to_stage": req["stage_id"]}
    data.setdefault("detours", []).append(detour)
    stage["detour_id"] = did
    if req["classification"] == "required-now":
        stage["status"] = "paused"
        data["status"] = "paused"
        unit_data = copy.deepcopy(unit.data)
        unit_data["status"] = "paused"
    elif req["classification"] in {"helpful-now", "deferred", "reference-only"}:
        unit_data = unit.data
    else:
        raise WriteRefused(
            f"unknown detour classification: {req['classification']} "
            "(choose from required-now, helpful-now, deferred, "
            "reference-only)",
            site="detour.create.unknown-classification",
            prefixed=True,
            exit_code=2,
        )
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site="detour.create.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "detour": detour},
        proposal=TransactionProposal(
            capability="detour.create",
            writes={study_map.path: _dump_study_map(study_map, data),
                    unit.path: _dump_yaml(unit_data)},
            artifact_ids=[req["unit_id"], study_map.id],
            expected_revisions=expected_revisions,
        ),
        on_commit_refused=_on_commit_refused,
        json_dumps=dumps_unescaped,
    )


def _stage(data: dict, stage_id: str):
    return next((row for row in data.get("stages", []) or []
                 if isinstance(row, dict) and row.get("id") == stage_id), None)


@register("detour.resolve", kind="command")
def detour_resolve(ctx: OpContext, req: dict) -> Result:
    """Resolve a detour and reactivate its return stage."""
    ctx.require_snapshot(req.get("expected_snapshot"))
    _, unit, study_map = require_unit_map_or_error(ctx, req["unit_id"])
    data = copy.deepcopy(study_map.data)
    detour = next((row for row in data.get("detours", []) or []
                   if row.get("id") == req["detour_id"]), None)
    if detour is None:
        known = [row.get("id") for row in data.get("detours", []) or []
                 if isinstance(row, dict) and row.get("id")]
        message = not_found("detour", req["detour_id"], known)
        raise NotFound(
            "detour", req["detour_id"], known,
            site="detour.resolve.unknown-detour",
            gateway_message=f"los: {message}",
            exit_code=2,
        )
    detour["status"] = "resolved"
    if req.get("resolution"):
        detour["resolution"] = req["resolution"]
    target_stage = _stage(data, detour["return_to_stage"])
    for other in data.get("stages", []) or []:
        if other.get("status") in {"active", "paused"}:
            other["status"] = "pending"
    target_stage["status"] = "active"
    data["current_stage"] = target_stage["id"]
    data["status"] = "active"
    unit_data = copy.deepcopy(unit.data)
    unit_data["status"] = "active"
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site="detour.resolve.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "detour_id": req["detour_id"],
         "return_to_stage": target_stage["id"]},
        proposal=TransactionProposal(
            capability="detour.resolve",
            writes={study_map.path: _dump_study_map(study_map, data),
                    unit.path: _dump_yaml(unit_data)},
            artifact_ids=[req["unit_id"], study_map.id],
            expected_revisions=expected_revisions,
        ),
        on_commit_refused=_on_commit_refused,
        json_dumps=dumps_unescaped,
    )


@register("source.feedback.record", kind="command")
def source_feedback(ctx: OpContext, req: dict) -> Result:
    """Record source feedback against an exact unit/stage/source."""
    ctx.require_snapshot(req.get("expected_snapshot"))
    repo, _, study_map = require_unit_map_or_error(ctx, req["unit_id"])
    if req["source_id"] not in repo.sources:
        message = not_found("source", req["source_id"], repo.sources)
        raise NotFound(
            "source", req["source_id"], repo.sources,
            site="source.feedback.record.unknown-source",
            gateway_message=f"los: {message}",
            exit_code=2,
        )
    data = copy.deepcopy(study_map.data)
    stage = require_stage(ctx, data, req["stage_id"])
    entry = {"source_id": req["source_id"], "feedback": req["feedback"],
             "recorded": observations.today().isoformat()}
    resource_id = req.get("resource_id")
    if resource_id:
        # Resolve against THIS stage before writing. The validator rejects a
        # dangling resource_id, but failing here gives the caller the actual
        # id list instead of a post-hoc validation error, and keeps the
        # transaction from being attempted at all.
        resources = {str(r.get("id")): r for r in (stage.get("resources") or [])
                     if isinstance(r, dict) and r.get("id")}
        target = resources.get(resource_id)
        if target is None:
            known = (", ".join(sorted(resources))
                     or "(this stage has no identified resources)")
            refusal = with_suggestions(
                f"resource not found on stage {req['stage_id']}: {resource_id}",
                resource_id, resources)
            raise NotFound(
                "resource", resource_id, resources,
                message=f"{refusal}\n     known: {known}",
                site="source.feedback.record.unknown-resource",
                gateway_message=f"los: {refusal}\n     known: {known}",
                exit_code=2,
            )
        declared = target.get("source_id")
        if declared and declared != req["source_id"]:
            raise WriteRefused(
                f"resource {resource_id} belongs to {declared}, "
                f"not {req['source_id']}",
                site="source.feedback.record.wrong-source",
                prefixed=True,
                exit_code=2,
            )
        entry["resource_id"] = resource_id
    if req.get("note"):
        entry["note"] = req["note"]
    stage.setdefault("source_feedback", []).append(entry)
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site="source.feedback.record.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "unit_id": req["unit_id"],
         "stage_id": req["stage_id"], "feedback": entry},
        proposal=TransactionProposal(
            capability="source.feedback.record",
            writes={study_map.path: _dump_study_map(study_map, data)},
            artifact_ids=[req["unit_id"], study_map.id],
            expected_revisions=expected_revisions,
        ),
        on_commit_refused=_on_commit_refused,
        json_dumps=dumps_unescaped,
    )


def _unit_note_target(root: Path, unit) -> tuple[Path, str]:
    declared = str(unit.data.get("working_note") or "").strip()
    target = root / declared if declared else unit.path.parent / "notes.md"
    try:
        rel = target.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise WriteRefused("unit working note must stay inside the repository") from exc
    return target, rel


@register("unit.note.append", kind="command")
def unit_note(ctx: OpContext, req: dict) -> Result:
    """Append one session-level section to the unit working note."""
    root = ctx.root
    value = req.get("text") if req.get("text") is not None else sys.stdin.read()
    if not value.strip():
        raise WriteRefused(
            "refusing to write an empty unit note — pass real text",
            site="unit.note.append.empty-note",
            prefixed=True,
            exit_code=2,
        )
    raw_sources = list(req.get("attachment") or [])
    source_hashes = list(req.get("attachment_sha256") or [])
    if source_hashes and len(source_hashes) != len(raw_sources):
        raise WriteRefused(
            "--attachment-sha256 must be repeated once per --attachment",
            site="unit.note.append.attachment-sha-count",
            prefixed=True,
            exit_code=2,
        )
    try:
        sources = [
            _read_content_bound_file(
                raw,
                source_hashes[index] if index < len(source_hashes) else None,
                label=f"unit-note attachment[{index}]",
            )
            for index, raw in enumerate(raw_sources)
        ]
    except WriteRefused as exc:
        raise WriteRefused(
            str(exc),
            site="unit.note.append.bad-file",
            prefixed=True,
            exit_code=2,
        ) from exc

    ctx.require_snapshot(req.get("expected_snapshot"))
    _, unit, study_map = require_unit_map_or_error(ctx, req["unit_id"])
    stage_ids = list(dict.fromkeys(req.get("stage_id") or []))
    allowed = {row.get("id") for row in study_map.data.get("stages", []) or []}
    unknown = [stage_id for stage_id in stage_ids if stage_id not in allowed]
    if unknown:
        raise NotFound(
            "stage", unknown[0], allowed,
            message=f"stage does not belong to unit '{req['unit_id']}': {unknown[0]}",
            site="unit.note.append.unknown-stage",
            gateway_message=(f"los: stage does not belong to unit "
                             f"'{req['unit_id']}': {unknown[0]}"),
            exit_code=2,
        )

    unit_data = copy.deepcopy(unit.data)
    try:
        target, rel = _unit_note_target(root, unit)
    except WriteRefused as exc:
        raise WriteRefused(
            str(exc),
            site="unit.note.append.note-outside-repo",
            prefixed=True,
            exit_code=2,
        ) from exc
    old = target.read_text(encoding="utf-8") if target.is_file() else ""
    recorded_at = observations.now().replace(microsecond=0).isoformat()
    title = " ".join((req.get("title") or "Learning session note").split()) \
        or "Learning session note"

    attachments: list[dict] = []
    attachment_writes: dict[Path, bytes] = {}
    stamp = observations.now().replace(tzinfo=None).strftime("%Y%m%d-%H%M%S")
    attachment_dir = unit.path.parent / "attachments" / f"unit-note-{stamp}"
    try:
        for source, source_bytes in sources:
            target_file = attachment_dir / source.name
            suffix = 2
            while target_file.exists() or target_file in attachment_writes:
                target_file = attachment_dir / f"{suffix}-{source.name}"
                suffix += 1
            attachment_writes[target_file] = source_bytes
            attachments.append({
                "path": target_file.relative_to(root).as_posix(),
                "label": source.stem,
            })

        metadata = {
            "recorded_at": recorded_at,
            "title": title,
            "stage_ids": stage_ids,
            "attachments": attachments,
        }
        lines = [unit_note_marker(metadata), f"## {title}", "", value.rstrip()]
        if attachments:
            lines.extend(["", "### Attachments", ""] + [
                f"- [{item['label']}]({Path(item['path']).relative_to(unit.path.parent.relative_to(root)).as_posix()})"
                for item in attachments
            ])
        section = "\n".join(lines).rstrip() + "\n"
        divider = "\n" if old and not old.endswith("\n\n") else ""
        updated = old + divider + section
        if not unit_data.get("working_note"):
            unit_data["working_note"] = rel
        writes: dict[Path, str | bytes] = {
            target: updated,
            unit.path: _dump_yaml(unit_data),
            **attachment_writes,
        }
        try:
            expected_revisions = parse_expected_revisions(req.get("expected_revision"))
        except ValueError as exc:
            raise WriteRefused(str(exc)) from exc
        return Result(
            {"ok": True, "unit_id": req["unit_id"], "working_note": rel,
             "recorded_at": recorded_at, "stage_ids": stage_ids,
             "attachments": attachments},
            proposal=TransactionProposal(
                capability="unit.note.append",
                writes=writes,
                artifact_ids=[req["unit_id"]],
                expected_revisions=expected_revisions,
            ),
            on_commit_refused=_on_commit_refused,
            json_dumps=dumps_unescaped,
        )
    except (OSError, WriteRefused) as exc:
        raise WriteRefused(
            f"cannot write unit note: {exc}",
            site="unit.note.append.write-failed",
            prefixed=True,
            exit_code=2,
        ) from exc


def _selection_used_by_current_map(repo, unit, route: dict, source_id: str,
                                   locator: str) -> bool:
    """Derive usage from the current map before editing a material choice.

    A stable route ID is authoritative when the resource has one. Older
    resources identify a choice by its exact source and locator; a shared
    source alone never means that this particular route is used.
    """
    study_map = repo.study_maps.get(unit.data.get("current_study_map"))
    if study_map is None:
        return False
    # Compact references retain identity even with a stage-specific locator;
    # expansion drops material_ref, so inspect the authored reference for this
    # mutation precondition, falling back for programmatically built maps.
    map_data = study_map.authored_data if study_map.authored_data is not None else study_map.data
    for stage in map_data.get("stages", []) or []:
        for resource in stage.get("resources", []) or []:
            material_ref = resource.get("material_ref")
            route_id = resource.get("route_id") or (
                material_ref.get("route_id") if isinstance(material_ref, dict) else None)
            if route_id:
                if route_id == route["id"]:
                    return True
            elif (resource.get("source_id"), resource.get("locator")) == (
                    source_id, locator):
                return True
    return False


@register("unit.source-selection.set", kind="command")
def unit_source_selection(ctx: OpContext, req: dict) -> Result:
    """Persist one learner choice without changing the complete material menu."""
    ctx.require_snapshot(req.get("expected_snapshot"))
    repo = ctx.repo()
    unit = repo.units.get(req["unit_id"])
    if unit is None:
        message = not_found("unit", req["unit_id"], repo.units)
        raise NotFound(
            "unit", req["unit_id"], repo.units,
            site="unit.source-selection.set.unknown-unit",
            gateway_message=f"los: {message}",
            exit_code=2,
        )
    if req["source_id"] not in repo.sources:
        message = not_found("source", req["source_id"], repo.sources)
        raise NotFound(
            "source", req["source_id"], repo.sources,
            site="unit.source-selection.set.unknown-source",
            gateway_message=f"los: {message}",
            exit_code=2,
        )

    source_map = repo.module_source_maps.get(unit.module_id, {})
    matching_route = None
    for source in source_map.get("sources", []) or []:
        if not isinstance(source, dict) or source.get("source_id") != req["source_id"]:
            continue
        for route in source.get("unit_routes", []) or []:
            if (
                isinstance(route, dict)
                and route.get("unit_id") == req["unit_id"]
                and route.get("locator") == req["locator"]
            ):
                matching_route = route_with_identity(
                    unit.module_id, req["source_id"], route
                )
                break
        if matching_route is not None:
            break
    if matching_route is None:
        raise WriteRefused(
            "selection must match one rich material route on this unit "
            f"({req['source_id']} · {req['locator']})",
            site="unit.source-selection.set.no-matching-route",
            prefixed=True,
            exit_code=2,
        )

    unit_data = copy.deepcopy(unit.data)
    selections = list(unit_data.get("source_selections", []) or [])
    index = next((
        i for i, row in enumerate(selections)
        if isinstance(row, dict)
        and row.get("source_id") == req["source_id"]
        and row.get("locator") == req["locator"]
    ), None)

    if req["action"] == "select":
        purpose = str(req.get("purpose") or matching_route.get("angle") or "Chosen learning material").strip()
        if not purpose:
            raise WriteRefused(
                "a selected material needs a purpose",
                site="unit.source-selection.set.missing-purpose",
                prefixed=True,
                exit_code=2,
            )
        replacement = {
            "route_id": matching_route["id"],
            "source_id": req["source_id"],
            "locator": req["locator"],
            "purpose": purpose,
        }
        if index is None:
            selections.append(replacement)
        else:
            if selections[index].get("stage_ids"):
                replacement["stage_ids"] = list(selections[index]["stage_ids"])
            selections[index] = replacement
        selected = True
    elif req["action"] == "remove":
        if index is not None and _selection_used_by_current_map(
                repo, unit, matching_route, req["source_id"], req["locator"]):
            raise WriteRefused(
                "this choice is used by the current study path; remove it "
                "from those stages before removing the choice",
                site="unit.source-selection.set.used-by-map",
                prefixed=True,
                exit_code=2,
            )
        if index is not None:
            selections.pop(index)
        selected = False
    else:
        raise WriteRefused(
            f"unknown source-selection action: {req['action']} "
            "(choose from select, remove)",
            site="unit.source-selection.set.unknown-action",
            prefixed=True,
            exit_code=2,
        )

    unit_data["source_selections"] = selections
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site="unit.source-selection.set.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "unit_id": req["unit_id"],
         "source_id": req["source_id"], "locator": req["locator"],
         "selected": selected},
        proposal=TransactionProposal(
            capability="unit.source-selection.set",
            writes={unit.path: _dump_yaml(unit_data)},
            artifact_ids=[req["unit_id"]],
            expected_revisions=expected_revisions,
        ),
        on_commit_refused=_on_commit_refused,
        json_dumps=dumps_unescaped,
    )


@register("learner.stage-result.append", kind="command")
def stage_result(ctx: OpContext, req: dict) -> Result:
    """Append an untargeted learner result against a unit/stage."""
    root = ctx.root
    if current_gateway_request() is None:
        raise WriteRefused(
            "stage results require GatewayEnvelopeV2; direct CLI application is disabled",
            site="learner.stage-result.append.direct-cli",
            prefixed=True,
            exit_code=2,
        )
    ctx.require_snapshot(req.get("expected_snapshot"))
    repo = ctx.repo()
    workspace = repo.workspaces.get(req["workspace"])
    if workspace is None or workspace.archived or workspace.status != "active":
        raise WriteRefused(
            "stage results require a registered active workspace",
            site="learner.stage-result.append.bad-workspace",
            prefixed=True,
            exit_code=2,
        )
    try:
        unit = repo.units.get(req["unit"])
        if unit is None:
            raise RuntimeInputError(f"unknown unit: {req['unit']}")
        study_map = repo.study_maps.get((unit.data or {}).get("current_study_map"))
        if study_map is None or study_map.unit_id != unit.id \
                or study_map.module_id != unit.module_id:
            raise RuntimeInputError(f"unit {unit.id} has no current study map")
        stage = next((item for item in study_map.data.get("stages", [])
                      if isinstance(item, dict) and item.get("id") == req["stage"]), None)
        if stage is None:
            raise RuntimeInputError(
                f"unknown stage {req['stage']} in unit {unit.id}")
        if (unit.module_id not in workspace.meta.get("module_ids", [])
                and unit.id not in workspace.meta.get("unit_ids", [])):
            raise RuntimeInputError("stage is outside the workspace's declared module/unit scope")
        historical = read_stage_results(repo)
        ledger = runtime_path(root, workspace.path.parent / "stage-results.jsonl")
        row = {
            "id": "stage-result-" + observations.new_hex(),
            "unit": unit.id,
            "stage": stage["id"],
            "activity": req["activity"],
            "result": req["result"],
            "timestamp": observations.now().astimezone(UTC).isoformat(),
            "conditions": list(req.get("condition") or []),
        }
        if req.get("assistance") is not None:
            row["assistance"] = req["assistance"]
        if req.get("note") is not None:
            row["note"] = req["note"]
        if req.get("supersedes"):
            prior = next((item for item in historical if item["id"] == req["supersedes"]), None)
            if (prior is None or prior["unit"] != unit.id
                    or prior["stage"] != stage["id"]
                    or prior["origin"]["path"] != ledger.relative_to(root).as_posix()
                    or any(item.get("supersedes") == prior["id"] for item in historical)):
                raise RuntimeInputError("correction must supersede one uncorrected stage result of this unit/stage in this ledger")
            row["supersedes"] = req["supersedes"]
        validate_runtime_record(repo, "learner-stage-result", row)
        try:
            old = ledger.read_text(encoding="utf-8")
        except FileNotFoundError:
            old = ""
        separator = "\n" if old and not old.endswith("\n") else ""
        new = old + separator + json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n"
        try:
            expected_revisions = parse_expected_revisions(req.get("expected_revision"))
        except ValueError as exc:
            raise WriteRefused(str(exc)) from exc
        return Result(
            {"ok": True, "stage_result_id": row["id"],
             "workspace_id": workspace.id, "unit": unit.id,
             "stage": stage["id"], "credit": "none"},
            proposal=TransactionProposal(
                capability=STAGE_RESULT_CAPABILITY,
                writes={ledger: new},
                artifact_ids=[workspace.id],
                expected_revisions=expected_revisions,
            ),
            on_commit_refused=_on_commit_refused,
            json_dumps=dumps_ascii,
        )
    except (RuntimeInputError, OSError) as exc:
        raise WriteRefused(
            str(exc),
            site="learner.stage-result.append.invalid-input",
            prefixed=True,
            exit_code=2,
        ) from exc


OBSERVE_CAPABILITY = "learner.observation.append"


def _stage_index(repo):
    """Every study-map stage: ``stage_id -> (unit_id, has_target)``.

    Only the current map of each unit is indexed: a stage id that exists
    solely on a superseded map is not observable, and naming it as a
    stage would point at work that no longer resolves.
    """
    index = {}
    for unit in repo.units.values():
        study_map = repo.study_maps.get((unit.data or {}).get("current_study_map"))
        if study_map is None or study_map.unit_id != unit.id:
            continue
        for stage in study_map.data.get("stages", []):
            if isinstance(stage, dict) and isinstance(stage.get("id"), str):
                index.setdefault(stage["id"], (
                    unit.id, isinstance(stage.get("runtime_target"), dict)))
    return index


def _unknown_requirement_message(repo, requirements, value):
    """Refuse an unresolvable id with the way forward named.

    A stage id whose stage carries no ``runtime_target`` is the ordinary
    untargeted case — most stages have no target — so it names the stage,
    the untargeted ``stage-result`` path, and the target-authoring
    ``unit-plan-revise`` path instead of crying unknown. A stage id that
    already has a target names the requirement id to observe. Anything
    else is a mistyped id, with suggestions over requirements and stages.
    """
    stages = _stage_index(repo)
    if value in stages:
        unit_id, has_target = stages[value]
        if has_target:
            requirement_id = next(
                (req["id"] for req in requirements
                 if req.get("source_stage", {}).get("stage_id") == value
                 and req.get("source_stage", {}).get("unit_id") == unit_id),
                None,
            )
            observed = f" {requirement_id}" if requirement_id else ""
            return (f"stage {value} (unit {unit_id}) already has a requirement "
                    f"target; observe the requirement id{observed} instead of "
                    f"the stage id")
        return (f"stage {value} (unit {unit_id}) has no requirement target; "
                f"record the result without credit via `stage-result "
                f"--workspace WORKSPACE --unit {unit_id} --stage {value} "
                f"--activity ACTIVITY --result RESULT`, or author a target "
                f"with `unit-plan-revise {unit_id} --file REVISION.yaml "
                f"--check` adding a runtime_target stage patch (WORKFLOWS §8)")
    return with_suggestions(f"unknown requirement: {value}", value,
                            [*(req["id"] for req in requirements), *stages])


def _condition_notice(requirement: dict, obs: dict) -> dict:
    """Say what this record does and does not establish, while he can still fix it.

    The write succeeded either way — the ledger is his, and refusing a report
    of difficulty because it lacked flags would be worse than accepting it.
    But a report that cannot be read as a failure of the current target needs
    to say so at the moment it is filed. It used to persist silently and leave
    the requirement reading `demonstrated`, `satisfied`, no next steps: the
    successful save was the only feedback, and it concealed that the report
    had no effect (audit `synthetic-learner-2026-09-12`, F02).
    """
    if obs["result"] not in {"incorrect", "partial"}:
        return {}
    declared = set(requirement.get("conditions", []))
    refuted = sorted(declared & set(obs.get("conditions_not_met", [])))
    if refuted:
        return {"refuted_conditions": refuted,
                "interpretation_notice": (
                    f"recorded as a different situation ({', '.join(refuted)} "
                    f"did not hold), so it is not read as a failure of this "
                    f"target and resets nothing")}
    missing = sorted(declared - set(obs.get("conditions", [])))
    if not missing:
        return {"interpretation_notice":
                "recorded under every condition this target declares; it is "
                "read as a failure of this target"}
    flags = " ".join(f"--condition {name}" for name in missing)
    not_met = " ".join(f"--condition-not-met {name}" for name in missing)
    return {
        "unstated_conditions": missing,
        "interpretation_notice": (
            f"this result does not say whether the target's conditions held "
            f"({', '.join(missing)}), so it is held as unresolved: it is not "
            f"read as a failure of this target, and the successes recorded "
            f"before it stop counting toward a current conclusion until this "
            f"is settled. Settle it by superseding this record — "
            f"los observe {requirement['id']} --activity {obs['activity']} "
            f"--result {obs['result']} --supersedes {obs['id']} — adding "
            f"{flags} for the conditions that held, or {not_met} for the ones "
            f"that did not. Two distinct qualified activities recorded after "
            f"this also establish a new basis, without claiming the missing "
            f"facts were ever known."
        ),
    }


@register("learner.observation.append", kind="command")
def observation_append(ctx: OpContext, req: dict) -> Result:
    """Append one immutable learner observation against a requirement."""
    root = ctx.root
    if current_gateway_request() is None:
        raise WriteRefused(
            "observations require GatewayEnvelopeV2; direct CLI application is disabled",
            site="learner.observation.append.direct-cli",
            prefixed=True,
            exit_code=2,
        )
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(str(exc)) from exc
    ctx.require_snapshot(req.get("expected_snapshot"))
    repo = ctx.repo()
    workspace = repo.workspaces.get(req["workspace"])
    if workspace is None or workspace.archived or workspace.status != "active":
        raise WriteRefused(
            "observations require a registered active workspace",
            site="learner.observation.append.bad-workspace",
            prefixed=True,
            exit_code=2,
        )
    try:
        requirements = collect_requirements(repo)
        requirement = next((row for row in requirements
                            if row["id"] == req["requirement"]), None)
        if requirement is None:
            raise RuntimeInputError(
                _unknown_requirement_message(repo, requirements, req["requirement"]))
        source = requirement["source_stage"]
        if (source["module_id"] not in workspace.meta.get("module_ids", [])
                and source["unit_id"] not in workspace.meta.get("unit_ids", [])):
            raise RuntimeInputError("requirement is outside the workspace's declared module/unit scope")
        historical = read_observations(repo, requirements)
        ledger = runtime_path(root, workspace.path.parent / "observations.jsonl")
        obs = {
            "id": "observation-" + observations.new_hex(),
            "requirement": req["requirement"],
            "requirement_sha256": requirement_fingerprint(requirement),
            "activity": req["activity"],
            "result": req["result"],
            "timestamp": observations.now().astimezone(UTC).isoformat(),
            "conditions": list(req.get("condition") or []),
            "evidence_tags": [tag.strip() for tag in (req.get("tags") or "").split(",") if tag.strip()],
        }
        refuted = list(req.get("condition_not_met") or [])
        if refuted:
            both = sorted(set(obs["conditions"]) & set(refuted))
            if both:
                raise RuntimeInputError(
                    "a condition cannot be recorded as both met and not met: "
                    + ", ".join(both))
            obs["conditions_not_met"] = refuted
        if req.get("assistance") is not None:
            obs["assistance"] = req.get("assistance")
        if req.get("context") is not None:
            obs["context"] = req.get("context")
        if req.get("supersedes"):
            prior = next((item for item in historical if item["id"] == req["supersedes"]), None)
            if (prior is None or prior["requirement"] != req["requirement"]
                    or prior["origin"]["path"] != ledger.relative_to(root).as_posix()
                    or any(item.get("supersedes") == prior["id"] for item in historical)):
                raise RuntimeInputError("correction must supersede one uncorrected observation of this requirement in this ledger")
            obs["supersedes"] = req["supersedes"]
        validate_runtime_record(repo, "learner-observation", obs)
        try:
            old = ledger.read_text(encoding="utf-8")
        except FileNotFoundError:
            old = ""
        separator = "\n" if old and not old.endswith("\n") else ""
        new = old + separator + json.dumps(obs, sort_keys=True, ensure_ascii=False) + "\n"
        return Result(
            {"ok": True, "observation_id": obs["id"],
             "workspace_id": workspace.id,
             **_condition_notice(requirement, obs)},
            proposal=TransactionProposal(
                capability=OBSERVE_CAPABILITY,
                writes={ledger: new},
                artifact_ids=[workspace.id],
                expected_revisions=expected_revisions,
            ),
            on_commit_refused=_on_commit_refused,
            json_dumps=dumps_ascii,
        )
    except (RuntimeInputError, OSError) as exc:
        raise WriteRefused(
            str(exc),
            site="learner.observation.append.invalid-input",
            prefixed=True,
            exit_code=2,
        ) from exc


def _resolve_observe_workspace(repo, requirement, explicit_id):
    """Return ``(workspace, refusal)`` for the direct path.

    An explicit id behaves exactly like ``observation-append``. An omitted
    id resolves the single active workspace covering the requirement's
    module or unit scope; zero or several candidates refuse rather than
    guess, because the ledger line cannot move workspaces afterwards.
    """
    source = requirement["source_stage"]

    def covers(workspace) -> bool:
        return (source["module_id"] in workspace.meta.get("module_ids", [])
                or source["unit_id"] in workspace.meta.get("unit_ids", []))

    if explicit_id is not None:
        workspace = repo.workspaces.get(explicit_id)
        if workspace is None or workspace.archived or workspace.status != "active":
            return None, "observations require a registered active workspace"
        if not covers(workspace):
            return None, "requirement is outside the workspace's declared module/unit scope"
        return workspace, ""
    candidates = sorted(
        workspace.id for workspace in repo.workspaces.values()
        if not workspace.archived and workspace.status == "active" and covers(workspace)
    )
    if not candidates:
        return None, (f"no active workspace covers requirement {requirement['id']}; "
                      "pass --workspace to choose one")
    if len(candidates) > 1:
        return None, (f"requirement {requirement['id']} is covered by "
                      f"{len(candidates)} workspaces ({', '.join(candidates)}); "
                      "pass --workspace to choose one")
    return repo.workspaces[candidates[0]], ""


@register("cli.observe", kind="command")
def cli_observe(ctx: OpContext, req: dict) -> Result:
    """Record Aram's own evidence directly; the terminal session is the approval."""
    root = ctx.root
    if not gesture_allowed(OBSERVE_CAPABILITY):
        raise WriteRefused(
            "the direct observation path is not admitted",
            site="cli.observe.not-admitted",
            prefixed=True,
            exit_code=2,
        )
    snapshot = ctx.snapshot_id()
    repo = ctx.repo()
    try:
        requirements = collect_requirements(repo)
    except RuntimeInputError as exc:
        raise WriteRefused(
            str(exc),
            site="cli.observe.invalid-target",
            prefixed=True,
            exit_code=2,
        ) from exc
    requirement = next((row for row in requirements
                        if row["id"] == req["requirement"]), None)
    if requirement is None:
        message = _unknown_requirement_message(
            repo, requirements, req["requirement"])
        raise WriteRefused(
            message,
            site="cli.observe.unknown-requirement",
            prefixed=True,
            exit_code=2,
        )
    workspace, refusal = _resolve_observe_workspace(
        repo, requirement, req.get("workspace"))
    if workspace is None:
        raise WriteRefused(
            refusal,
            site="cli.observe.unresolved-workspace",
            prefixed=True,
            exit_code=2,
        )
    payload: dict = {
        "workspace": workspace.id,
        "requirement": requirement["id"],
        "activity": req["activity"],
        "result": req["result"],
    }
    if req.get("assistance") is not None:
        payload["assistance"] = req["assistance"]
    if req.get("tags") is not None:
        payload["tags"] = req["tags"]
    if req.get("note") is not None:
        payload["context"] = req["note"]
    if req.get("condition"):
        payload["condition"] = list(req["condition"])
    if req.get("condition_not_met"):
        payload["condition_not_met"] = list(req["condition_not_met"])
    if req.get("supersedes"):
        payload["supersedes"] = req["supersedes"]
    expected_revisions = {workspace.id: artifact_revision(root, workspace.id)}
    subject = intent_sha256({
        "schema_version": 2,
        "capability": OBSERVE_CAPABILITY,
        "channel": "operator",
        "expected_snapshot": snapshot,
        "expected_revisions": expected_revisions,
        "payload": payload,
    })
    key = observations.new_hex()
    context = GatewayRequestContext(
        request_id=f"observe-{key}",
        idempotency_key=f"observe-{key}",
        capability=OBSERVE_CAPABILITY,
        channel="operator",
        intent_sha256=subject,
        approval_kind="direct-user-gesture",
        approval_subject_sha256=subject,
        expected_snapshot=snapshot,
    )
    core_req = {
        "workspace": workspace.id,
        "requirement": requirement["id"],
        "activity": req["activity"],
        "result": req["result"],
        "expected_snapshot": snapshot,
        "expected_revision": [
            f"{workspace.id}={expected_revisions[workspace.id]}"],
        "assistance": req.get("assistance"),
        "tags": req.get("tags"),
        "context": req.get("note"),
        "condition": req.get("condition"),
        "condition_not_met": req.get("condition_not_met"),
        "supersedes": req.get("supersedes"),
    }
    with gateway_request_context(context), verified_gateway_snapshot(
            root, snapshot):
        core = observation_append(ctx, core_req)
    return Result(
        core.payload,
        proposal=core.proposal,
        on_commit_refused=_on_commit_refused,
        json_dumps=dumps_ascii,
        gesture=context,
    )


def _valid_work_ref(value: str) -> bool:
    if not value.startswith(("conversation://", "note://", "project://", "curriculum/")):
        return False
    if any(character.isspace() for character in value):
        return False
    if value.startswith("curriculum/"):
        path = value.split("#", 1)[0]
        parts = path.split("/")
        return "\\" not in path and len(parts) > 1 and all(
            part not in ("", ".", "..") for part in parts)
    return True


@register("learner.ability-observation.append", kind="command")
def ability_observation_append(ctx: OpContext, req: dict) -> Result:
    """Record an exact learner-confirmed claim; the V2 approval binds payload."""
    root = ctx.root
    request = current_gateway_request()
    if request is None:
        raise WriteRefused(
            "ability observations require GatewayEnvelopeV2",
            site="learner.ability-observation.append.direct-cli",
            prefixed=True,
            exit_code=2,
        )
    ctx.require_snapshot(req.get("expected_snapshot"))
    repo = ctx.repo()
    workspace = repo.workspaces.get(req["workspace"])
    if workspace is None or workspace.archived or workspace.status != "active":
        raise WriteRefused(
            "a registered active workspace must own this work",
            site="learner.ability-observation.append.bad-workspace",
            prefixed=True,
            exit_code=2,
        )
    ability = repo.abilities.get(req["ability"])
    if (ability is None or ability.get("review", {}).get("state") != "reviewed"
            or ability.get("lifecycle") == "retired"):
        raise WriteRefused(
            "evidence requires an active reviewed ability identity",
            site="learner.ability-observation.append.unknown-ability",
            prefixed=True,
            exit_code=2,
        )
    if not _valid_work_ref(req["work_ref"]):
        raise WriteRefused(
            "work-ref must safely point to conversation, note, project, or curriculum work",
            site="learner.ability-observation.append.bad-work-ref",
            prefixed=True,
            exit_code=2,
        )
    if not req["confirmation_ref"].startswith(("conversation://", "note://")):
        raise Unconfirmed(
            "confirmation-ref must point to Aram's confirmation",
            site="learner.ability-observation.append.bad-confirmation-ref",
            prefixed=True,
            exit_code=2,
        )
    if (request.channel == "ui" and req["confirmation_ref"] !=
            f"conversation://learningos-app/{request.idempotency_key}"):
        raise Unconfirmed(
            "app confirmation-ref must name this exact request",
            site="learner.ability-observation.append.bad-app-confirmation",
            prefixed=True,
            exit_code=2,
        )
    try:
        history = read_ability_observations(repo)
        path = runtime_path(root, workspace.path.parent / "ability-observations.jsonl")
        if req.get("supersedes"):
            prior = next((row for row in history if row["id"] == req["supersedes"]), None)
            if (prior is None or prior["ability_id"] != req["ability"]
                    or prior["origin"]["path"] != path.relative_to(root).as_posix()
                    or any(row.get("supersedes") == prior["id"] for row in history)):
                raise WriteRefused("correction must supersede one uncorrected observation in this ledger")
        row = {
            "id": "ability-observation-" + observations.new_hex(),
            "ability_id": req["ability"],
            "ability_sha256": ability_fingerprint(ability),
            "claim": req["claim"],
            "work_ref": req["work_ref"],
            "confirmation_ref": req["confirmation_ref"],
            "activity": req["activity"],
            "result": req["result"],
            "timestamp": observations.now().astimezone(UTC).isoformat(),
            "conditions": list(req.get("condition") or []),
            "evidence_tags": list(req.get("evidence_tag") or []),
            "assistance": req["assistance"],
            "confirmed_by": "learner",
        }
        if req.get("condition_not_met"):
            row["conditions_not_met"] = list(req.get("condition_not_met"))
        if req.get("supersedes"):
            row["supersedes"] = req["supersedes"]
        if set(row["conditions"]) & set(row.get("conditions_not_met", [])):
            raise WriteRefused("condition cannot be both met and not met")
        schema = json.loads((root / "system/schema/ability-observation.schema.json").read_text())
        errors = sorted(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(row), key=str)
        if errors:
            raise WriteRefused(f"ability observation: {errors[0].message}")
        old = path.read_text(encoding="utf-8") if path.exists() else ""
        new = old + ("\n" if old and not old.endswith("\n") else "")
        new += json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n"
        try:
            expected_revisions = parse_expected_revisions(req.get("expected_revision"))
        except ValueError as exc:
            raise WriteRefused(str(exc)) from exc
        return Result(
            {"ok": True, "observation_id": row["id"]},
            proposal=TransactionProposal(
                capability="learner.ability-observation.append",
                writes={path: new},
                artifact_ids=[workspace.id],
                expected_revisions=expected_revisions,
            ),
            on_commit_refused=_on_commit_refused,
            json_dumps=dumps_ascii,
        )
    except (WriteRefused, OSError, ValueError) as exc:
        raise WriteRefused(
            str(exc),
            site="learner.ability-observation.append.invalid-input",
            prefixed=True,
            exit_code=2,
        ) from exc
