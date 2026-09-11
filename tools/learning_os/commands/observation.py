"""Append learner evidence through the existing snapshot/revision transaction.

Two entries, one core. ``observation-append`` is the agent-facing capability
handler: it requires a GatewayEnvelopeV2 and the caller asserts the approved
snapshot. ``observe`` is Aram's own direct path (Finding 0: asymmetric
admission): the producer is the ground truth about himself, the ledger is
append-only with a tested ``--supersedes`` correction path, and the write
lands at the end of a study session — so the snapshot is *taken* under the
operator lock instead of *asserted* by a tired caller. For a single writer
holding a lock that is the same guarantee. The receipt is byte-identical in
shape; only ``approval.kind`` reads ``direct-user-gesture``.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from uuid import uuid4

from learning_os.contracts.gateway import (
    GatewayRequestContext,
    current_gateway_request,
    gateway_request_context,
    intent_sha256,
    verified_gateway_snapshot,
)
from learning_os.fingerprint import canonical_fingerprint
from learning_os.learning_runtime import (
    RuntimeInputError,
    collect_requirements,
    read_observations,
    requirement_fingerprint,
    runtime_path,
    validate_runtime_record,
)
from learning_os.loader import load_repo
from learning_os.revisions import artifact_revision

from .capability import gesture_allowed
from .support import (
    _expected_ok,
    _expected_revisions_from_args,
    _operator_lock,
    _root,
    _write_transaction,
)

OBSERVE_CAPABILITY = "learner.observation.append"


def _append_observation(
    root,
    *,
    workspace_id: str,
    requirement_id: str,
    activity: str,
    result: str,
    conditions,
    tags: str | None,
    assistance: str | None,
    context_note: str | None,
    supersedes: str | None,
    expected_snapshot,
    expected_revisions: dict,
) -> tuple[int, dict]:
    """Shared append core. The caller holds the operator lock and a live
    gateway request. Returns ``(code, result)``; errors are already reported.
    """
    if not _expected_ok(root, expected_snapshot):
        return 3, {}
    repo = load_repo(root)
    workspace = repo.workspaces.get(workspace_id)
    if workspace is None or workspace.archived or workspace.status != "active":
        print("los: observations require a registered active workspace", file=sys.stderr)
        return 2, {}
    try:
        requirements = collect_requirements(repo)
        requirement = next((req for req in requirements if req["id"] == requirement_id), None)
        if requirement is None:
            raise RuntimeInputError(f"unknown requirement: {requirement_id}")
        source = requirement["source_stage"]
        if (source["module_id"] not in workspace.meta.get("module_ids", [])
                and source["unit_id"] not in workspace.meta.get("unit_ids", [])):
            raise RuntimeInputError("requirement is outside the workspace's declared module/unit scope")
        historical = read_observations(repo, requirements)
        ledger = runtime_path(root, workspace.path.parent / "observations.jsonl")
        obs = {
            "id": "observation-" + uuid4().hex,
            "requirement": requirement_id,
            "requirement_sha256": requirement_fingerprint(requirement),
            "activity": activity,
            "result": result,
            "timestamp": datetime.now(UTC).isoformat(),
            "conditions": list(conditions or []),
            "evidence_tags": [tag.strip() for tag in (tags or "").split(",") if tag.strip()],
        }
        if assistance is not None:
            obs["assistance"] = assistance
        if context_note is not None:
            obs["context"] = context_note
        if supersedes:
            prior = next((item for item in historical if item["id"] == supersedes), None)
            if (prior is None or prior["requirement"] != requirement_id
                    or prior["origin"]["path"] != ledger.relative_to(root).as_posix()
                    or any(item.get("supersedes") == prior["id"] for item in historical)):
                raise RuntimeInputError("correction must supersede one uncorrected observation of this requirement in this ledger")
            obs["supersedes"] = supersedes
        validate_runtime_record(repo, "learner-observation", obs)
        try:
            old = ledger.read_text(encoding="utf-8")
        except FileNotFoundError:
            old = ""
        separator = "\n" if old and not old.endswith("\n") else ""
        new = old + separator + json.dumps(obs, sort_keys=True, ensure_ascii=False) + "\n"
        code, errors, confirmation = _write_transaction(
            root, {ledger: new}, capability=OBSERVE_CAPABILITY,
            expected_revisions=expected_revisions, artifact_ids=[workspace.id],
        )
        if code:
            for error in errors[:12]:
                print(error, file=sys.stderr)
            return code, {}
    except (RuntimeInputError, OSError) as exc:
        print(f"los: {exc}", file=sys.stderr)
        return 2, {}
    return 0, {"ok": True, "observation_id": obs["id"],
               "workspace_id": workspace.id, **confirmation}


def cmd_observation_append(args) -> int:
    root = _root(args)
    if current_gateway_request() is None:
        print("los: observations require GatewayEnvelopeV2; direct CLI application is disabled", file=sys.stderr)
        return 2
    with _operator_lock(root):
        code, result = _append_observation(
            root,
            workspace_id=args.workspace,
            requirement_id=args.requirement,
            activity=args.activity,
            result=args.result,
            conditions=args.condition,
            tags=args.tags,
            assistance=args.assistance,
            context_note=args.context,
            supersedes=args.supersedes,
            expected_snapshot=args.expected_snapshot,
            expected_revisions=_expected_revisions_from_args(args),
        )
    if code:
        return code
    print(json.dumps(result))
    return 0


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


def cmd_observe(args) -> int:
    """Record Aram's own evidence with no envelope ceremony.

    The terminal session is the approval: the snapshot and the revision
    guard are taken under the operator lock, and the intent hash is
    computed internally over the same subject the envelope would carry.
    """
    root = _root(args)
    if not gesture_allowed(OBSERVE_CAPABILITY):
        print("los: the direct observation path is not admitted", file=sys.stderr)
        return 2
    with _operator_lock(root):
        snapshot = f"sha256:{canonical_fingerprint(root)}"
        repo = load_repo(root)
        try:
            requirements = collect_requirements(repo)
        except RuntimeInputError as exc:
            print(f"los: {exc}", file=sys.stderr)
            return 2
        requirement = next((req for req in requirements if req["id"] == args.requirement), None)
        if requirement is None:
            print(f"los: unknown requirement: {args.requirement}", file=sys.stderr)
            return 2
        workspace, refusal = _resolve_observe_workspace(repo, requirement, args.workspace)
        if workspace is None:
            print(f"los: {refusal}", file=sys.stderr)
            return 2
        payload: dict = {
            "workspace": workspace.id,
            "requirement": requirement["id"],
            "activity": args.activity,
            "result": args.result,
        }
        if args.assistance is not None:
            payload["assistance"] = args.assistance
        if args.tags is not None:
            payload["tags"] = args.tags
        if args.note is not None:
            payload["context"] = args.note
        if args.condition:
            payload["condition"] = list(args.condition)
        if args.supersedes:
            payload["supersedes"] = args.supersedes
        expected_revisions = {workspace.id: artifact_revision(root, workspace.id)}
        subject = intent_sha256({
            "schema_version": 2,
            "capability": OBSERVE_CAPABILITY,
            "channel": "operator",
            "expected_snapshot": snapshot,
            "expected_revisions": expected_revisions,
            "payload": payload,
        })
        key = uuid4().hex
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
        with gateway_request_context(context), verified_gateway_snapshot(root, snapshot):
            code, result = _append_observation(
                root,
                workspace_id=workspace.id,
                requirement_id=requirement["id"],
                activity=args.activity,
                result=args.result,
                conditions=args.condition,
                tags=args.tags,
                assistance=args.assistance,
                context_note=args.note,
                supersedes=args.supersedes,
                expected_snapshot=snapshot,
                expected_revisions=expected_revisions,
            )
    if code:
        return code
    print(json.dumps(result))
    return 0
