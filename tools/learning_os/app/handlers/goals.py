"""Goals-area converted handlers (PLAN D4, D8)."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from learning_os.app.admission import gesture_allowed
from learning_os.app.context import OpContext
from learning_os.app.proposal import ResponsePayload, Result, TransactionProposal
from learning_os.app.registry import register
from learning_os.derive.semantics.claim_audits import (
    AuditError,
    AuditRecord,
    ClaimBasis,
    audit_records,
    authorization_from_mapping,
    eligible_pool,
    result_from_mapping,
)
from learning_os.derive.semantics.claim_status import judgment_basis, observe_claims
from learning_os.derive.semantics.lineage import from_dict, load_ledger
from learning_os.derive.semantics.scan import intelligence_scan
from learning_os.domain.failures import NotFound, ValidationFailed, WriteRefused
from learning_os.domain.suggest import not_found
from learning_os.store import observations
from learning_os.store.contracts.gateway import GatewayRequestContext, intent_sha256
from learning_os.store.loading.yamlio import UniqueKeySafeLoader
from learning_os.store.revisions import artifact_revision
from learning_os.store.session_ledger import current_session_id as _current_session_id
from learning_os.store.session_ledger import load_session_paths as _load_session_paths
from learning_os.store.session_ledger import record_touched as _record_touched
from learning_os.store.session_ledger import session_ledger as _session_ledger

GOAL_CAPABILITY = "goal.decision.record"

LEDGER_RELATIVE = "operations/goal-ledger.yaml"


def _validate_ledger(root, data: dict) -> list[str]:
    schema = json.loads(
        (root / "system/schema/goal-ledger.schema.json").read_text(
            encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(data),
        key=str,
    )
    return [f"goal ledger: {error.message}" for error in errors]


def _goal_on_commit_refused(errors: list) -> list[str]:
    """The exact commit-refusal lines: the first twelve engine issues, verbatim."""
    return list(errors[:12])


def _render_goal_check(record: dict, payload: dict) -> dict:
    """Today's ``--check`` output from the check record (SPEC §12 R4).

    Refuses with the canonical validation text when the record failed,
    else returns the review payload: the reviewed sha, the decided ids
    with their before/after rows, and the state.
    """
    if not record["ok"]:
        raise ValidationFailed(
            "canonical validation failed: "
            + "; ".join(map(str, record["errors"][:8])))
    return {
        "ok": True,
        "check": True,
        "reviewed_sha256": payload["reviewed_sha256"],
        "goal_ids": payload["goal_ids"],
        "state": payload["state"],
        "changes": payload["changes"],
        **({"audits": payload["audits"]} if "audits" in payload else {}),
    }


@register("goal.decide", kind="command", render_check=_render_goal_check)
def goal(ctx: OpContext, req: dict) -> Result:
    """Record Aram's explicit decision on a proposed goal."""
    root = ctx.root
    if not gesture_allowed(GOAL_CAPABILITY):
        raise WriteRefused(
            "the direct goal path is not admitted",
            site="goal.decide.not-admitted",
            prefixed=True,
            exit_code=2,
        )
    supplied = req["goal_id"] if isinstance(req["goal_id"], list) else [req["goal_id"]]
    goal_ids = [item.strip() for item in supplied if isinstance(item, str)]
    if len(goal_ids) != len(supplied) or not goal_ids or len(set(goal_ids)) != len(goal_ids) \
            or any(not item or any(char.isspace() for char in item)
                   or any(char in item for char in "*?[]") for item in goal_ids):
        raise WriteRefused(
            "supply distinct exact goal ids, each one whitespace-free token; patterns are refused",
            site="goal.decide.bad-goal-ids",
            prefixed=True,
            exit_code=2,
        )
    state = ("authorized" if req.get("authorize") else "rejected" if req.get("reject")
             else "deferred" if req.get("defer") else "closed")
    revisit_on = req.get("revisit_on")
    if revisit_on is not None:
        if state != "deferred":
            raise WriteRefused(
                "--revisit-on requires --defer",
                site="goal.decide.revisit-needs-defer",
                prefixed=True,
                exit_code=2,
            )
        try:
            if not isinstance(revisit_on, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", revisit_on):
                raise ValueError("not YYYY-MM-DD")
            day = _dt.date.fromisoformat(revisit_on)
        except (TypeError, ValueError):
            raise WriteRefused(
                "--revisit-on needs an ISO date (YYYY-MM-DD)",
                site="goal.decide.bad-revisit",
                prefixed=True,
                exit_code=2,
            ) from None
        if day <= observations.today():
            raise WriteRefused(
                "--revisit-on must be a future date",
                site="goal.decide.past-revisit",
                prefixed=True,
                exit_code=2,
            )
    snapshot = ctx.snapshot_id()
    path = root / LEDGER_RELATIVE
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raw = ""
    except OSError as exc:
        raise WriteRefused(
            f"cannot read the goal ledger: {exc}",
            site="goal.decide.unreadable-ledger",
            prefixed=True,
            exit_code=2,
        ) from exc
    if not raw.strip():
        data: dict = {"schema_version": 1, "type": "goal-ledger", "decisions": {}}
    else:
        try:
            loaded = yaml.load(raw, Loader=UniqueKeySafeLoader)
        except yaml.YAMLError as exc:
            raise WriteRefused(
                f"the goal ledger is malformed, refusing to clobber it: {exc}",
                site="goal.decide.malformed-ledger",
                prefixed=True,
                exit_code=2,
            ) from exc
        if not isinstance(loaded, dict):
            raise WriteRefused(
                "the goal ledger is malformed, refusing to clobber it",
                site="goal.decide.malformed-ledger",
                prefixed=True,
                exit_code=2,
            )
        data = loaded
    decisions = data.get("decisions")
    if not isinstance(decisions, dict):
        raise WriteRefused(
            "the goal ledger is malformed, refusing to clobber it",
            site="goal.decide.malformed-ledger",
            prefixed=True,
            exit_code=2,
        )
    problems = _validate_ledger(root, data)
    if problems:
        raise WriteRefused(problems[0], site="goal.decide.invalid-ledger", prefixed=True, exit_code=2)
    audit_changes = None
    audit_intent = None
    try:
        audits = audit_records(data.get("audits"))
        audit_ids = [gid for gid in goal_ids if gid.startswith("claims-audit:")]
        if req.get("audit_file") and (len(goal_ids) != 1 or len(audit_ids) != 1 or state not in {"authorized", "closed"}):
            raise AuditError("--audit-file requires one exact audit with --authorize or --close")
        if audit_ids and state in {"authorized", "closed"}:
            if not req.get("audit_file") or len(goal_ids) != 1:
                raise AuditError("audit authorization and closure require one reviewed --audit-file")
            try:
                value = yaml.load(Path(req["audit_file"]).read_text(encoding="utf-8"), Loader=UniqueKeySafeLoader)
            except (OSError, UnicodeError, yaml.YAMLError) as exc:
                raise AuditError(f"cannot read audit file: {exc}") from exc
            gid = audit_ids[0]
            audit_intent = intent_sha256({"schema_version": 2, "capability": GOAL_CAPABILITY,
                "channel": "operator", "session_id": req.get("session_id"), "payload": {
                    "goal_ids": goal_ids, "state": state, "note": req.get("note"), "audit": value}})
            prior = audits.get(gid)
            if state == "authorized":
                authorization = authorization_from_mapping(value)
                if authorization.goal_id != gid:
                    raise AuditError("audit id differs from the supplied full pool")
                if prior is not None:
                    if prior.authorization != authorization:
                        raise AuditError("audit was already frozen; redraw is refused")
                    updated = prior
                else:
                    statuses = observe_claims(root, audits=audits)
                    pool = eligible_pool(statuses.values())
                    if authorization.pool != pool:
                        raise AuditError("audit authorization must freeze the complete current eligible pool")
                    updated = AuditRecord(authorization)
            else:
                if prior is None:
                    raise AuditError("audit closure requires its preserved authorization")
                result = result_from_mapping(value, prior.authorization)
                if prior.result is not None and prior.result != result:
                    raise AuditError("audit already has a different immutable result")
                records = load_ledger(root)
                historical = set()
                for row in records.values():
                    while True:
                        historical.add(ClaimBasis(row.claim_id, judgment_basis(row)))
                        if row.supersedes is None:
                            break
                        row = from_dict(dict(row.supersedes))
                if not set(prior.authorization.pool).issubset(historical):
                    raise AuditError("audit pool contains a basis absent from current lineage and its history")
                report = Path(result.report_path)
                if not report.is_absolute():
                    report = root / report
                try:
                    checksum = hashlib.sha256(report.read_bytes()).hexdigest()
                except OSError as exc:
                    raise AuditError(f"audit report is unreadable: {exc}") from exc
                if checksum != result.report_sha256.removeprefix("sha256:"):
                    raise AuditError("audit report digest differs from its reviewed bytes")
                updated = AuditRecord(prior.authorization, result, prior.authorization_reviewed_sha256, prior.result_reviewed_sha256, prior.authorization_intent_sha256, prior.result_intent_sha256)
            original_review = (prior.authorization_reviewed_sha256 if state == "authorized" else prior.result_reviewed_sha256) if prior else ""
            original_intent = (prior.authorization_intent_sha256 if state == "authorized" else prior.result_intent_sha256) if prior else ""
            if not req.get("check") and original_review and req.get("reviewed_sha256") == original_review and audit_intent == original_intent:
                return Result({"ok": True, "goal_id": gid, "state": decisions.get(gid, {}).get("state"), "replayed": True})
            audits[gid] = updated
            data["audits"] = {key: row.payload() for key, row in sorted(audits.items())}
            audit_changes = {"goal_id": gid, "before": prior.payload() if prior else None,
                             "after": updated.payload()}
    except (AuditError, ValueError) as exc:
        raise WriteRefused(str(exc), site="goal.decide.invalid-audit", prefixed=True, exit_code=2) from exc
    # Only decidable ids: a goal in the current scan, or already in the
    # ledger (a goal that stopped being detected can still be closed or
    # re-decided). Unknown ids refuse before anything is written, so a
    # batch is all-or-nothing. A scan that cannot be read degrades to
    # ledger-only rather than inventing candidates.
    try:
        scan_ids = {goal.goal_id for goal in intelligence_scan(root)}
        scan_failed: Exception | None = None
    except Exception as exc:  # noqa: BLE001 - fail closed to ledger-only
        scan_ids = set()
        scan_failed = exc
    known = {key for key in decisions if isinstance(key, str)} | scan_ids | set(audits)
    unknown = [goal_id for goal_id in goal_ids if goal_id not in known]
    if unknown:
        lines = []
        if scan_failed is not None:
            lines.append(f"the live scan is unavailable ({scan_failed}); "
                         f"deciding only ledger-known ids")
        candidates = sorted(known)
        for goal_id in unknown:
            lines.append(not_found("goal", goal_id, candidates))
        extra = tuple(f"los: {line}" for line in lines[1:])
        # The raise stays a direct NotFound construction so the A9
        # site collector sees the literal site; the existing extra
        # stderr lines attach to the constructed failure on capture,
        # like the exc.site capture the collector already supports.
        try:
            raise NotFound(
                "goal", unknown[0], candidates,
                message=lines[0],
                site="goal.decide.unknown-goal",
                gateway_message="los: " + lines[0] + "".join(f"\n{line}" for line in extra),
                exit_code=2,
            )
        except NotFound as exc:
            exc.extra_stderr = extra
            raise
    if state == "rejected" and (not isinstance(req.get("note"), str) or not req["note"].strip()):
        raise WriteRefused("--reject requires a nonempty --note", site="goal.decide.reject-needs-note", prefixed=True, exit_code=2)
    entry: dict = {"state": state, "decided_at": observations.today().isoformat()}
    if revisit_on is not None:
        entry["revisit_on"] = revisit_on
    if req.get("note") is not None:
        entry["note"] = req["note"]
    reviewed = {
        "ledger_bytes_sha256": "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        "goal_ids": goal_ids,
        "decision": entry,
    }
    if audit_changes is not None:
        reviewed["audit"] = audit_changes
    review_sha = "sha256:" + hashlib.sha256(json.dumps(
        reviewed, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")).hexdigest()
    if audit_changes is not None:
        proof_key = "authorization_reviewed_sha256" if state == "authorized" else "result_reviewed_sha256"
        data["audits"][audit_changes["goal_id"]].setdefault(proof_key, review_sha)
        intent_key = "authorization_intent_sha256" if state == "authorized" else "result_intent_sha256"
        data["audits"][audit_changes["goal_id"]].setdefault(intent_key, audit_intent)
    data["decisions"] = {**decisions, **{goal_id: dict(entry) for goal_id in goal_ids}}
    problems = _validate_ledger(root, data)
    if problems:
        raise WriteRefused(
            problems[0],
            site="goal.decide.invalid-ledger",
            prefixed=True,
            exit_code=2,
        )
    payload = {
        "goal_ids": goal_ids,
        "state": state,
        "reviewed_sha256": review_sha,
        "changes": [{"goal_id": goal_id, "before": decisions.get(goal_id),
                     "after": entry} for goal_id in goal_ids],
    }
    if audit_changes is not None:
        payload["audits"] = audit_changes
    new_text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    explicit_session = req.get("session_id")

    def touched(paths) -> None:
        _record_touched(root, paths, session_id=explicit_session)

    ledger_artifact = f"file:{LEDGER_RELATIVE}"
    expected_revisions = {ledger_artifact: artifact_revision(root, ledger_artifact)}
    proposal = TransactionProposal(
        capability=GOAL_CAPABILITY,
        writes={path: new_text},
        artifact_ids=(ledger_artifact,),
        expected_revisions=expected_revisions,
        publish=None,
        rollback_publish=None,
        touched=touched,
    )
    key = observations.new_hex()
    subject = intent_sha256({
        "schema_version": 2,
        "capability": GOAL_CAPABILITY,
        "channel": "operator",
        "expected_snapshot": snapshot,
        "expected_revisions": expected_revisions,
        "payload": reviewed,
    })
    # The explicit session travels sealed on the gesture, exactly as a
    # gateway envelope seals it, so the commit path resolves this write's
    # owner the same way the custom touched callback claims it below.
    # Nothing else reads the sealed identity during the commit.
    context = GatewayRequestContext(
        request_id=f"goal-{key}",
        idempotency_key=f"goal-{key}",
        capability=GOAL_CAPABILITY,
        channel="operator",
        intent_sha256=subject,
        approval_kind="direct-user-gesture",
        approval_subject_sha256=subject,
        expected_snapshot=snapshot,
        session_id=explicit_session,
    )

    def finish(confirmation: dict) -> dict:
        result = {"ok": True, "state": state}
        result["goal_id" if len(goal_ids) == 1 else "goal_ids"] = goal_ids[0] if len(goal_ids) == 1 else goal_ids
        if revisit_on is not None:
            result["revisit_on"] = revisit_on
        return result

    if req.get("check"):
        return Result(
            ResponsePayload(payload, finish({}), confirmation='omit'),
            proposal=proposal,



            gesture=context,
        )
    expected = req.get("reviewed_sha256")
    if ((len(goal_ids) > 1 or audit_changes is not None) and expected is None) or (expected is not None and expected != review_sha):
        raise WriteRefused(
            "batch apply needs the exact --check reviewed-sha256; changed ledger or decisions require a fresh review",
            site="goal.decide.batch-needs-review",
            prefixed=True,
            exit_code=3,
        )
    # The decision joins the caller's session, so session-end lists and
    # commits the ledger with the rest of the session's writes. Identity
    # resolves exactly as the gateway and session-end do (explicit
    # --session-id, then the envelope, then LOS_SESSION_ID, then the
    # channel). Preflight the own ledger first: a corrupt ledger refuses
    # before the decision is written, never after.
    own_session = _current_session_id(explicit=explicit_session)
    if _session_ledger(root, own_session).is_file():
        try:
            _load_session_paths(root, own_session)
        except WriteRefused as exc:
            raise WriteRefused(
                str(exc),
                site="goal.decide.unreadable-session",
                prefixed=True,
                exit_code=2,
            ) from exc
    return Result(
        ResponsePayload(payload, finish({}), confirmation='omit'),
        proposal=proposal,



        gesture=context,
    )
