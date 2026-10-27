"""Admin-area converted handlers (PLAN D4)."""

from __future__ import annotations

import copy
import datetime as _dt
import hashlib
import re

import yaml

from learning_os.app.context import OpContext
from learning_os.app.gateway import prepare_review_envelope
from learning_os.app.gateway import read_content_bound_file as _read_content_bound_file
from learning_os.app.handlers._shared import render_creation_check as _render_creation_check
from learning_os.app.proposal import ResponsePayload, Result, TransactionProposal
from learning_os.app.registry import OperationEffects, register
from learning_os.derive.semesters import semester_plan as _semester_plan
from learning_os.domain.failures import NotFound, WriteRefused
from learning_os.domain.render import parse_sections
from learning_os.domain.render import replace_h2_section as _replace_h2_section
from learning_os.domain.suggest import not_found
from learning_os.store.codec import dump_yaml as _dump_yaml
from learning_os.store.codec import render_frontmatter as _render_frontmatter
from learning_os.store.layout import PathBoundaryError, read_bytes_inside
from learning_os.store.revisions import artifact_revision, load_revisions
from learning_os.store.transactions import parse_expected_revisions

ATTEMPT_RESULTS = ("registered", "withdrawn", "sat", "passed", "failed")

#: A semester's canonical identity, as the program record declares it.
_SEMESTER_ID = re.compile(r"^semester-[a-z0-9]+(?:-[a-z0-9]+)*$")


#: A digest-shaped value that was never a real file hash: all zeros.
_PLACEHOLDER_DIGEST = "sha256:" + "0" * 64

_DIGEST_RE = re.compile(r"sha256:[a-f0-9]{64}")








@register("module.attempt.record", kind="command", effects=OperationEffects.CANONICAL_WRITE)
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
    elif "grade" in row:
        # An update restates the stated fact (#27): keeping the previous
        # grade would pin the termin to "passed" forever, because MOD-GRADE
        # refuses a grade on any other result.
        del row["grade"]
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


@register("module.sitting.update", kind="command", effects=OperationEffects.CANONICAL_WRITE)
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


@register("coordination.section.revise", kind="command", effects=OperationEffects.CANONICAL_WRITE)
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


@register("workspace.next-action.update", kind="command", effects=OperationEffects.CANONICAL_WRITE)
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


def _semester_problems(semester) -> list[str]:
    """Why a reviewed semester row cannot become the current one."""
    if not isinstance(semester, dict):
        return ["the package needs a 'semester' mapping"]
    problems: list[str] = []
    semester_id = semester.get("id")
    if not isinstance(semester_id, str) or not _SEMESTER_ID.match(semester_id):
        problems.append(
            "the semester id must match 'semester-<slug>'")
    title = semester.get("title")
    if not isinstance(title, str) or not title.strip():
        problems.append("the semester needs a non-empty title")
    order = semester.get("order")
    if isinstance(order, bool) or not isinstance(order, int) or order < 0:
        problems.append("the semester needs a non-negative integer order")
    return problems


def _semester_fact(row: dict | None) -> dict | None:
    """One semester row, as the report shows it."""
    if not isinstance(row, dict):
        return None
    return {
        "id": row.get("id"),
        "title": row.get("title"),
        "status": row.get("status"),
        "order": row.get("order"),
    }


@register("program.semester.update", kind="command",
           render_check=_render_creation_check, effects=OperationEffects.CANONICAL_WRITE)
def program_semester_update(ctx: OpContext, req: dict) -> Result:
    """Turn one program's current semester, from a reviewed package.

    The term boundary is a curriculum fact, and it used to be changed by
    editing the program record by hand: no receipt, no snapshot, no
    revision, no conflict detection, and nothing that said what the change
    did to the interface (LearningOS #2).

    It writes the program record and nothing else. Exam outcomes,
    registrations, learner state and study work live in the module, unit
    and study-map records, and a term change never touches them. It never
    rolls the term forward on its own either: the reviewed package names
    the semester that becomes current, and the previous one becomes
    ``previous`` — history is kept, never dropped.
    """
    root = ctx.root
    try:
        source, package_bytes = _read_content_bound_file(
            req.get("file"),
            req.get("file_sha256"),
            label="program semester update file",
        )
    except WriteRefused as exc:
        exc.site = "program.semester.update.bad-file"
        exc.gateway_message = f"los: {exc}"
        exc.exit_code = 2
        raise
    try:
        package = yaml.safe_load(package_bytes.decode("utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise WriteRefused(
            f"invalid program semester YAML: {exc}",
            site="program.semester.update.bad-yaml",
            prefixed=True,
            exit_code=2,
        ) from exc
    if not isinstance(package, dict):
        raise WriteRefused(
            "the program semester package must be a mapping",
            site="program.semester.update.bad-package",
            prefixed=True,
            exit_code=2,
        )
    program_id = package.get("program_id")
    if not isinstance(program_id, str) or not program_id.strip():
        raise WriteRefused(
            "the package needs the id of the program whose semester changes",
            site="program.semester.update.bad-package",
            prefixed=True,
            exit_code=2,
        )
    problems = _semester_problems(package.get("semester"))
    if problems:
        message = "the reviewed semester cannot become the current one"
        details = tuple(f"- {problem}" for problem in problems)
        raise WriteRefused(
            message,
            site="program.semester.update.bad-semester",
            extra_stderr=details,
            gateway_message=f"los: {message}" + "".join(f"\n{line}" for line in details),
            exit_code=2,
        )
    repo = ctx.repo()
    program = repo.programs.get(program_id)
    if program is None:
        message = not_found("program", program_id, repo.programs)
        raise NotFound(
            "program", program_id, repo.programs,
            site="program.semester.update.unknown-program",
            gateway_message=f"los: {message}",
            exit_code=2,
        )
    if not program.data.get("semester_bound"):
        message = (f"program {program_id} has no semesters; it is not "
                   "semester-bound")
        raise WriteRefused(
            message,
            site="program.semester.update.not-semester-bound",
            prefixed=True,
            exit_code=2,
        )
    semester = package["semester"]
    plan = _semester_plan(program.data, semester)
    if plan["semesters"] == (program.data.get("semesters") or []):
        message = (f"semester {semester['id']} is already the current semester "
                   f"of {program_id}, with the same title and order; nothing "
                   "to change")
        raise WriteRefused(
            message,
            site="program.semester.update.no-change",
            prefixed=True,
            exit_code=2,
        )
    revised = copy.deepcopy(program.data)
    revised["semesters"] = plan["semesters"]
    writes = {program.path: _dump_yaml(revised)}
    package_sha = "sha256:" + hashlib.sha256(package_bytes).hexdigest()
    listed = sorted(
        module_id for module_id, module in repo.modules.items()
        if module.get("area_id") == program_id
        and module.get("kind") == "academic"
        and str(module.get("status") or "") not in
        ("completed", "archived", "dropped")
    )
    report = {
        "program_id": program_id,
        "current_semester_before": _semester_fact(plan["current_before"]),
        "current_semester_after": _semester_fact(plan["current_after"]),
        "semester_added": plan["added"],
        "module_listing": {
            "rule": "open academic modules; the term does not gate the list",
            "listed_module_ids": listed,
            "changed": False,
        },
        "preserved": "exam outcomes, registrations, learner state and study "
                     "work live in other records and are untouched",
    }
    if req.get("check"):
        expected_revisions = {program_id: load_revisions(root).get(program_id, 0)}
        prepared = {
            "ok": True,
            "check": True,
            "mode": "check",
            "capability": "program.semester.update",
            "reviewed_file_sha256": package_sha,
            "write_paths": [program.path.relative_to(root).as_posix()],
            **report,
            "gateway_envelope": prepare_review_envelope(
                "program.semester.update",
                {"file": str(source), "file_sha256": package_sha},
                ctx.snapshot_id(),
                expected_revisions,
            ),
        }
        return Result(
            prepared,
            proposal=TransactionProposal(
                capability="program.semester.update",
                writes=writes,
                artifact_ids=[program_id],
                expected_revisions=expected_revisions,
            ),
        )
    ctx.require_snapshot(req.get("expected_snapshot"))
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc),
            site=f"{ctx.operation}.bad-expected-revision",
            prefixed=True,
            exit_code=2,
        ) from exc
    return Result(
        ResponsePayload(
            {"ok": True},
            {"ok": True, "mode": "apply", **report},
            confirmation="merge",
        ),
        proposal=TransactionProposal(
            capability="program.semester.update",
            writes=writes,
            artifact_ids=[program_id],
            expected_revisions=expected_revisions,
        ),
    )
