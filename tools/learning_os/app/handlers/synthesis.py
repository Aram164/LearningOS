"""Material synthesis publication and lineage restamping."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path

from learning_os.app.claim_admission import lineage_artifacts
from learning_os.app.context import OpContext
from learning_os.app.encoders import dumps_indented
from learning_os.app.gateway import prepare_review_envelope
from learning_os.app.handlers._shared import apply_reviewed_envelope
from learning_os.app.handlers._shared import input_record as _input_record
from learning_os.app.handlers._shared import require_gateway_v2 as _require_gateway_v2
from learning_os.app.proposal import ResponsePayload, Result, TransactionProposal
from learning_os.app.registry import register
from learning_os.derive.material_synthesis import (
    MaterialSynthesisUnitNotFound,
    current_unit_material_basis,
    publication_lineage,
    synthesis_destination,
    validate_unit_material_synthesis,
)
from learning_os.derive.semantics.lineage import (
    LEDGER_RELATIVE,
    LineageError,
    dump_ledger,
    load_ledger,
    restamp_claim,
)
from learning_os.derive.semantics.restamp import ELIGIBLE, analyze, claims_list_sha256
from learning_os.domain.failures import NotFound, WriteRefused
from learning_os.store import observations
from learning_os.store.codec import dump_yaml as _dump_yaml
from learning_os.store.contracts.gateway import current_gateway_request
from learning_os.store.revisions import load_revisions
from learning_os.store.session import githistory
from learning_os.store.transactions import parse_expected_revisions, transaction_artifacts


def _validate_publication_synthesis(root, unit_id: str, value: dict) -> dict:
    """Validate a publication dossier, typing only the unknown-unit lookup.

    SPEC (cq) 5: the validator's own schema, dossier/request binding,
    then repository lookup order is unchanged; only the structured
    unknown-unit subclass becomes a typed ``NotFound`` with the
    byte-identical complaint. Every other ``MaterialSynthesisError``
    propagates exactly as before, with no prose matching and no new
    repository read.
    """
    try:
        return validate_unit_material_synthesis(root, unit_id, value)
    except MaterialSynthesisUnitNotFound as exc:
        raise NotFound(
            "unit", exc.unit_id, exc.candidates,
            message=str(exc),
            site="unit.material-synthesis.publish.unknown-unit",
            gateway_message=str(exc),
            exit_code=2,
        ) from exc


@register("unit.material-synthesis.publish", kind="command")
def unit_material_synthesis_publish(ctx: OpContext, req: dict) -> Result:
    """Publish one reviewed unit dossier, with lineage, atomically."""
    root = ctx.root
    # Unwrapped, exactly as legacy: admission and dossier validation
    # propagate with both refusal fields None ((ac) pre-existing raise),
    # except the unknown-unit lookup, which is typed (SPEC (cq) 5).
    value = _input_record(req, "unit material synthesis")
    _validate_publication_synthesis(root, req["unit_id"], value)
    basis = current_unit_material_basis(root, req["unit_id"])
    artifacts = lineage_artifacts((req["unit_id"], value["id"]))
    if req.get("check") is True:
        return Result(
            {"ok": True, "check": True, "unit_id": req["unit_id"],
             "basis": basis, "artifact_ids": artifacts,
             "expected_revisions": {aid: load_revisions(root).get(aid, 0) for aid in artifacts}},

        )
    if not req.get("approve"):
        message = "unit material synthesis publication requires explicit approval"
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.needs-approval",
            gateway_message=json.dumps({"ok": False, "error": message}),
            exit_code=2,
        )
    _require_gateway_v2()
    # Re-read every canonical basis guard inside the serialized write
    # window. The earlier validation gives fast feedback; this one is the
    # authority for the commit.
    _validate_publication_synthesis(root, req["unit_id"], value)
    ctx.require_snapshot(req.get("expected_snapshot"))
    destination = synthesis_destination(root, req["unit_id"])
    content = _dump_yaml(value)
    request = current_gateway_request()
    lineage = publication_lineage(root, req["unit_id"], value, content, request)
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site=f"{ctx.operation}.bad-expected-revision",
        ) from exc

    def finish_unit_material_synthesis_publish(confirmation):
        return {"ok": True, **confirmation}

    def refused_stdout_unit_material_synthesis_publish(errors):
        return dumps_indented({
            "ok": False,
            **({"errors": [str(error) for error in errors]} if errors else {}),
        })

    return Result(
        ResponsePayload({"ok": True}, finish_unit_material_synthesis_publish({}), confirmation='merge'),
        proposal=TransactionProposal(
            capability="unit.material-synthesis.publish",
            writes={destination: content, root / LEDGER_RELATIVE: lineage},
            artifact_ids=tuple(artifacts),
            expected_revisions=expected_revisions,
        ),



    )


def _canonical_list_bytes(claim_ids) -> bytes:
    return "".join(cid + "\n" for cid in sorted(claim_ids)).encode("utf-8")


def _plan_sha256(plan: dict[str, dict[str, str]]) -> str:
    body = json.dumps(plan, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(body).hexdigest()


def _verify_named(analysis: dict, claim_ids: list[str],
                  claims_sha256: str) -> tuple[list[str], dict]:
    """The reviewed ids, verified against fresh analysis.

    Returns the sorted ids and their verified plan rows. Refuses unknown
    ids, a hash that does not bind the exact list, and every listed
    claim that is not stampable — a listed claim whose judged state
    moved refuses exactly like an unlisted one.
    """
    if claims_list_sha256(claim_ids) != claims_sha256:
        raise WriteRefused(
            "claims_sha256 does not bind these claim ids; re-hash the "
            "exact reviewed list (sorted ids, one per line)")
    rows = analysis["claims"]
    unknown = [cid for cid in claim_ids if cid not in rows]
    if unknown:
        raise WriteRefused(
            "claims outside the supported old-shape set: "
            + ", ".join(sorted(unknown)))
    refused = {
        cid: rows[cid] for cid in claim_ids
        if rows[cid]["verdict"] != ELIGIBLE
    }
    if refused:
        detail = "; ".join(
            f"{cid} is {rows[cid]['verdict']}"
            f" ({', '.join(rows[cid]['reasons']) or rows[cid]['basis']})"
            for cid in sorted(refused))
        raise WriteRefused(f"the re-stamp refuses: {detail}")
    ordered = sorted(claim_ids)
    return ordered, {cid: rows[cid] for cid in ordered}


def _ledger_guards(root: Path) -> tuple[list[str], dict[str, int]]:
    """The transaction artifacts and their current revisions.

    The re-stamp writes only the sidecar ledger, so the transaction
    guards the ledger path itself — the same file-artifact derivation
    the seal-time dry run uses, by construction rather than by a
    second spelling of the path.
    """
    artifacts = transaction_artifacts(root, (), [root / LEDGER_RELATIVE])
    current = load_revisions(root)
    return artifacts, {artifact: current.get(artifact, 0)
                       for artifact in artifacts}


def _lineage_restamp_commit_lines(commit_errors: list) -> list[str]:
    return ["los: lineage re-stamp failed", *commit_errors[:12]]


@register("lineage.restamp", kind="command")
def lineage_restamp(ctx: OpContext, req: dict) -> Result:
    """Narrow old coarse reads, never re-judge (#94)."""
    root = ctx.root
    check = req.get("check", False)
    review_report = req.get("review_report")
    if check and review_report:
        raise WriteRefused(
            "--check and --review-report are mutually exclusive",
            site=f"{ctx.operation}.check-and-review",
            prefixed=True,
            exit_code=2,
        )
    claim_ids = list(req.get("claim_ids") or [])
    claims_sha256 = req.get("claims_sha256")
    if review_report:
        if not claim_ids or not claims_sha256:
            raise WriteRefused(
                "reviewed apply needs --claim-ids and --claims-sha256 with --review-report",
                site=f"{ctx.operation}.reviewed-needs-ids",
                prefixed=True,
                exit_code=2,
            )
        try:
            if claims_list_sha256(claim_ids) != claims_sha256:
                raise WriteRefused(
                    "claims_sha256 does not bind these claim ids",
                    site=f"{ctx.operation}.reviewed-sha-mismatch",
                    prefixed=True,
                    exit_code=2,
                )
        except LineageError as exc:
            raise WriteRefused(
                str(exc),
                site=f"{ctx.operation}.reviewed-sha-invalid",
                prefixed=True,
                exit_code=2,
            ) from exc
        return Result(
            apply_reviewed_envelope(ctx, capability_name='lineage.restamp', payload={'claim_ids': sorted(claim_ids), 'claims_sha256': claims_sha256}, reviewed_content=_canonical_list_bytes(claim_ids), reviewed_sha256=claims_sha256, review_report=review_report),

        )
    ctx.require_snapshot(req.get("expected_snapshot"))
    try:
        analysis = analyze(root)
    except (LineageError, githistory.GitHistoryError, OSError,
            ValueError) as exc:
        raise WriteRefused(
            f"re-stamp analysis failed: {exc}",
            site=f"{ctx.operation}.analysis-failed",
            prefixed=True,
            exit_code=2,
        ) from exc
    snapshot = ctx.snapshot_id()
    if check and not claim_ids:
        return Result(
            {"ok": True, "mode": "check", "capability": "lineage.restamp",
             "expected_snapshot": snapshot, **analysis},

        )
    if not claim_ids or not claims_sha256:
        raise WriteRefused(
            "lineage-restamp needs --claim-ids with --claims-sha256 (the reviewed list); "
            "--check alone recomputes eligibility",
            site=f"{ctx.operation}.needs-claim-ids",
            prefixed=True,
            exit_code=2,
        )
    try:
        ordered, planned = _verify_named(analysis, claim_ids, claims_sha256)
    except (WriteRefused, LineageError) as exc:
        raise WriteRefused(
            str(exc),
            site=f"{ctx.operation}.unverified-claims",
            prefixed=True,
            exit_code=2,
        ) from exc
    plan = {cid: dict(planned[cid]["new_reads"]) for cid in ordered}
    plan_sha = _plan_sha256(plan)
    if check:
        _artifacts, revisions = _ledger_guards(root)
        payload = {"claim_ids": ordered, "claims_sha256": claims_sha256}
        return Result(
            {"ok": True, "mode": "check", "capability": "lineage.restamp",
             "claim_ids": ordered, "claims_sha256": claims_sha256,
             "plan": plan, "plan_sha256": plan_sha,
             "expected_snapshot": snapshot,
             "expected_revisions": revisions,
             "reviewed_file_sha256": claims_sha256,
             "gateway_envelope": prepare_review_envelope(
                 "lineage.restamp", payload, snapshot, revisions)},

        )
    request = current_gateway_request()
    if request is None:
        raise WriteRefused(
            "lineage-restamp applies only through its reviewed report (--review-report) "
            "or a sealed GatewayEnvelopeV2 (`los capability lineage.restamp --payload-file "
            "ENVELOPE.json`); direct CLI application is disabled",
            site=f"{ctx.operation}.direct-apply-disabled",
            prefixed=True,
            exit_code=2,
        )
    try:
        records = load_ledger(root)
        stamped = dict(records)
        restamped_by = f"{request.channel}/{request.approval_kind}"
        restamped_on = observations.now().astimezone(_dt.UTC).date().isoformat()
        for cid in ordered:
            prior = records.get(cid)
            if prior is None:
                raise LineageError(f"claim {cid!r} left the ledger")
            stamped[cid] = restamp_claim(
                prior, source_hashes=plan[cid],
                restamped_by=restamped_by, restamped_on=restamped_on)
        text = dump_ledger(stamped)
    except LineageError as exc:
        raise WriteRefused(
            str(exc),
            site=f"{ctx.operation}.restamp-failed",
            prefixed=True,
            exit_code=2,
        ) from exc
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site=f"{ctx.operation}.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "mode": "apply", "capability": "lineage.restamp",
         "claim_ids": ordered, "claims_sha256": claims_sha256,
         "plan_sha256": plan_sha},
        proposal=TransactionProposal(
            capability="lineage.restamp",
            writes={root / LEDGER_RELATIVE: text},
            artifact_ids=(),
            expected_revisions=expected_revisions,
            # The envelope's intent hash already binds the claim list;
            # echoing the hash and the count here keeps the receipt
            # directly auditable without reopening the envelope.
            metadata={"claims_sha256": claims_sha256,
                      "claims_count": len(ordered)},
        ),


    )
