"""Admin-area converted handlers (PLAN D4)."""

from __future__ import annotations

import copy
import datetime as _dt
import hashlib
import re

from learning_os.app.context import OpContext
from learning_os.app.proposal import Result, TransactionProposal
from learning_os.app.registry import register
from learning_os.domain.failures import NotFound, WriteRefused
from learning_os.domain.render import parse_sections
from learning_os.domain.render import replace_h2_section as _replace_h2_section
from learning_os.domain.suggest import not_found
from learning_os.store.codec import dump_yaml as _dump_yaml
from learning_os.store.codec import render_frontmatter as _render_frontmatter
from learning_os.store.layout import PathBoundaryError, read_bytes_inside
from learning_os.store.revisions import artifact_revision
from learning_os.store.transactions import parse_expected_revisions

ATTEMPT_RESULTS = ("registered", "withdrawn", "sat", "passed", "failed")


#: A digest-shaped value that was never a real file hash: all zeros.
_PLACEHOLDER_DIGEST = "sha256:" + "0" * 64

_DIGEST_RE = re.compile(r"sha256:[a-f0-9]{64}")


def _refused_first_twelve(errors: list) -> list[str]:
    """The exact commit-refusal lines: the first twelve engine issues, verbatim."""
    return list(errors[:12])


def _refused_all(errors: list) -> list[str]:
    """The exact commit-refusal lines: every engine issue, verbatim."""
    return list(errors)


def _refused_next_action(errors: list) -> list[str]:
    """The exact commit-refusal lines: the rejection header plus the first twelve engine issues, verbatim."""
    return ["los: next-action update rejected by validation", *errors[:12]]


@register("module.attempt.record", kind="command")
def module_attempt(ctx: OpContext, req: dict) -> Result:
    """Record one exam attempt fact in the owning module's module.yaml."""
    if req["termin"] not in (1, 2, 3):
        message = f"--termin must be 1, 2 or 3, got {req['termin']!r}"
        raise WriteRefused(
            message,
            site="module.attempt.record.bad-termin",
            prefixed=True,
            exit_code=2,
        )
    if req["result"] not in ATTEMPT_RESULTS:
        message = (f"--result must be one of {', '.join(ATTEMPT_RESULTS)}, "
                   f"got {req['result']!r}")
        raise WriteRefused(
            message,
            site="module.attempt.record.bad-result",
            prefixed=True,
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
            prefixed=True,
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
                prefixed=True,
                exit_code=2,
            )
        grade = float(grade)
        if not 1.0 <= grade <= 5.0:
            message = ("--grade must be between 1.0 and 5.0, "
                       f"got {req['grade']!r}")
            raise WriteRefused(
                message,
                site="module.attempt.record.grade-out-of-range",
                prefixed=True,
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


    )


@register("module.sitting.update", kind="command")
def module_sitting(ctx: OpContext, req: dict) -> Result:
    """Record one sitting's withdrawal deadline in the owning module.yaml."""
    if req["termin"] not in (1, 2, 3):
        message = f"--termin must be 1, 2 or 3, got {req['termin']!r}"
        raise WriteRefused(
            message,
            site="module.sitting.update.bad-termin",
            prefixed=True,
            exit_code=2,
        )
    try:
        _dt.date.fromisoformat(req["withdrawal_deadline"])
    except (TypeError, ValueError) as exc:
        message = ("--withdrawal-deadline must be an ISO date (YYYY-MM-DD), "
                   f"got {req['withdrawal_deadline']!r}")
        raise WriteRefused(
            message,
            site="module.sitting.update.bad-deadline",
            prefixed=True,
            exit_code=2,
        ) from exc
    ctx.require_snapshot(req.get("expected_snapshot"))
    repo = ctx.repo()
    module = repo.modules.get(req["module_id"])
    if module is None:
        message = not_found("module", req["module_id"], repo.modules)
        raise NotFound(
            "module", req["module_id"], repo.modules,
            site="module.sitting.update.unknown-module",
            gateway_message=f"los: {message}",
            exit_code=2,
        )
    module_path = repo.module_origins[req["module_id"]]
    data = copy.deepcopy(module)
    sittings = (data.get("examination") or {}).get("sittings") or []
    row = next((candidate for candidate in sittings
                if isinstance(candidate, dict)
                and candidate.get("termin") == req["termin"]), None)
    if row is None:
        known = sorted({sitting.get("termin") for sitting in sittings
                        if isinstance(sitting, dict)
                        and sitting.get("termin") is not None})
        message = (f"module {req['module_id']} has no sitting for termin "
                   f"{req['termin']} (known termins: {known or 'none'})")
        raise WriteRefused(
            message,
            site="module.sitting.update.no-sitting",
            prefixed=True,
            exit_code=2,
        )
    row["withdrawal_deadline"] = req["withdrawal_deadline"]
    try:
        expected_revisions = parse_expected_revisions(
            req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site="module.sitting.update.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "module_id": req["module_id"], "termin": req["termin"],
         "withdrawal_deadline": req["withdrawal_deadline"]},
        proposal=TransactionProposal(
            capability="module.sitting.update",
            writes={module_path: _dump_yaml(data)},
            artifact_ids=[req["module_id"]],
            expected_revisions=expected_revisions,
        ),


    )


@register("coordination.section.revise", kind="command")
def coordination_section_revise(ctx: OpContext, req: dict) -> Result:
    """Revise one reviewed coordination section, never a curriculum record."""
    root = ctx.root
    path = root / "work/COORDINATION.md"
    ctx.require_snapshot(req.get("expected_snapshot"))
    if req["section"] not in {"Commitments", "Priorities", "Dependencies",
                              "Deferrals"}:
        raise WriteRefused(
            "unknown coordination section",
            site="coordination.section.revise.unknown-section",
            prefixed=True,
            exit_code=2,
        )
    if path.is_symlink() or not path.is_file():
        raise WriteRefused(
            "coordination must be an existing regular file",
            site="coordination.section.revise.no-coordination-file",
            prefixed=True,
            exit_code=2,
        )
    try:
        original = read_bytes_inside(root, path)
    except (OSError, PathBoundaryError) as exc:
        message = f"cannot read coordination safely: {exc}"
        raise WriteRefused(
            message,
            site="coordination.section.revise.read-failed",
            prefixed=True,
            exit_code=2,
        ) from exc
    digest = "sha256:" + hashlib.sha256(original).hexdigest()
    supplied = req.get("expected_content_sha256")
    if supplied is None and not req.get("check"):
        message = ("coordination.section.revise apply requires "
                   "--expected-content-sha256: the current content digest is "
                   f"{digest} (read it with `inspect coordination`)")
        raise WriteRefused(
            message,
            site="coordination.section.revise.missing-digest",
            prefixed=True,
            exit_code=2,
        )
    if supplied is not None:
        if not _DIGEST_RE.fullmatch(supplied):
            message = (f"malformed content digest {supplied!r}; the current "
                       f"content digest is {digest} "
                       "(read it with `inspect coordination`)")
            raise WriteRefused(
                message,
                site="coordination.section.revise.malformed-digest",
                prefixed=True,
                exit_code=2,
            )
        if supplied != digest:
            if supplied == _PLACEHOLDER_DIGEST:
                message = (f"placeholder content digest {supplied}; the current "
                           f"content digest is {digest} "
                           "(read it with `inspect coordination`)")
                raise WriteRefused(
                    message,
                    site="coordination.section.revise.placeholder-digest",
                    prefixed=True,
                    exit_code=2,
                )
            message = ("reviewed coordination content changed before use: "
                       f"supplied {supplied}, current is {digest}; re-read with "
                       "`inspect coordination`")
            raise WriteRefused(
                message,
                site="coordination.section.revise.content-changed",
                prefixed=True,
                exit_code=3,
            )
    if not req["text"].strip():
        raise WriteRefused(
            "coordination section text must not be blank",
            site="coordination.section.revise.blank-text",
            prefixed=True,
            exit_code=2,
        )
    _, injected = parse_sections(req["text"])
    _, sections = parse_sections(original.decode("utf-8"))
    targets = [section for section in sections
               if section.heading == req["section"]]
    if injected or len(targets) != 1:
        raise WriteRefused(
            "replace exactly one existing section; new section headings refuse",
            site="coordination.section.revise.new-heading",
            prefixed=True,
            exit_code=2,
        )
    revised = _replace_h2_section(original.decode("utf-8"), req["section"],
                                  req["text"])
    if req.get("check"):
        return Result({
            "ok": True, "section": req["section"],
            "before": "\n".join(targets[0].lines).strip(),
            "after": req["text"].strip(),
            "expected_content_sha256": digest,
            "expected_snapshot": ctx.snapshot_id(),
            "expected_revisions": {"coordination": artifact_revision(
                root, "coordination")},
            "write_paths": ["work/COORDINATION.md"],
        })
    try:
        expected_revisions = parse_expected_revisions(
            req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc),
            site="coordination.section.revise.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "section": req["section"]},
        proposal=TransactionProposal(
            capability="coordination.section.revise",
            writes={path: revised},
            artifact_ids=["coordination"],
            expected_revisions=expected_revisions,
        ),


    )


@register("workspace.next-action.update", kind="command")
def workspace_next_action(ctx: OpContext, req: dict) -> Result:
    """Replace one active workspace's Next Action section."""
    root = ctx.root
    text = req["next_action"]
    if not isinstance(text, str) or not text.strip():
        raise WriteRefused(
            "--next-action must not be blank",
            site="workspace.next-action.update.blank-action",
            prefixed=True,
            exit_code=2,
        )
    ctx.require_snapshot(req.get("expected_snapshot"))
    repo = ctx.repo()
    workspace = repo.workspaces.get(req["workspace_id"])
    if workspace is None:
        message = f"workspace not found: {req['workspace_id']}"
        raise NotFound(
            "workspace", req["workspace_id"], repo.workspaces,
            message=message,
            site="workspace.next-action.update.unknown-workspace",
            gateway_message=f"los: {message}",
            exit_code=2,
        )
    if workspace.archived or workspace.status != "active":
        message = f"workspace is not active: {req['workspace_id']}"
        raise WriteRefused(
            message,
            site="workspace.next-action.update.workspace-not-active",
            prefixed=True,
            exit_code=2,
        )
    try:
        body = _replace_h2_section(workspace.body, "Next Action", text)
    except ValueError as exc:
        raise WriteRefused(
            str(exc),
            site="workspace.next-action.update.no-next-action",
            prefixed=True,
            exit_code=2,
        ) from exc
    try:
        expected_revisions = parse_expected_revisions(
            req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc),
            site="workspace.next-action.update.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "workspace_id": req["workspace_id"],
         "path": workspace.path.relative_to(root).as_posix()},
        proposal=TransactionProposal(
            capability="workspace.next-action.update",
            writes={workspace.path: _render_frontmatter(workspace.meta, body)},
            artifact_ids=[req["workspace_id"]],
            expected_revisions=expected_revisions,
        ),


    )
