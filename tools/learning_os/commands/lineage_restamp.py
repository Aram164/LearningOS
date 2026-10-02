"""Governed lineage re-stamp: narrow old coarse reads, never re-judge (#94).

``los lineage-restamp --check`` recomputes mechanical eligibility for
every supported route-covers claim, read-only. ``--check --claim-ids ...
--claims-sha256 ...`` verifies the reviewed plan for exactly those
claims and seals a gateway envelope for it. Apply takes the saved
report (``--review-report``) or a sealed envelope through
``los capability lineage.restamp``: the payload ids plus their hash
bind the exact claim list, fresh analysis re-verifies every claim under
the operator lock, and one receipt-producing transaction narrows exactly
those reads. Any claim whose route row or covered nodes differ from the
judged state refuses, listed or not.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path

from learning_os import githistory
from learning_os.fingerprint import canonical_fingerprint
from learning_os.semantics.lineage import (
    LEDGER_RELATIVE,
    LineageError,
    dump_ledger,
    load_ledger,
    restamp_claim,
)
from learning_os.semantics.restamp import (
    ELIGIBLE,
    analyze,
    claims_list_sha256,
)

from .support import (
    WriteRefused,
    _expected_ok,
    _expected_revisions_from_args,
    _operator_lock,
    _root,
    _write_transaction,
)

CAPABILITY = "lineage.restamp"


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
    from learning_os.revisions import load_revisions
    from learning_os.transactions import transaction_artifacts

    artifacts = transaction_artifacts(root, (), [root / LEDGER_RELATIVE])
    current = load_revisions(root)
    return artifacts, {artifact: current.get(artifact, 0)
                       for artifact in artifacts}


def cmd_lineage_restamp(args) -> int:
    root = _root(args)
    review_report = getattr(args, "review_report", None)
    if getattr(args, "check", False) and review_report:
        print("los: --check and --review-report are mutually exclusive",
              file=sys.stderr)
        return 2
    claim_ids = list(getattr(args, "claim_ids", None) or [])
    claims_sha256 = getattr(args, "claims_sha256", None)
    if review_report:
        if not claim_ids or not claims_sha256:
            print("los: reviewed apply needs --claim-ids and --claims-sha256 "
                  "with --review-report", file=sys.stderr)
            return 2
        try:
            if claims_list_sha256(claim_ids) != claims_sha256:
                raise WriteRefused(
                    "claims_sha256 does not bind these claim ids")
        except LineageError as exc:
            print(f"los: {exc}", file=sys.stderr)
            return 2
        from learning_os.commands.capability import reviewed_envelope_apply

        return reviewed_envelope_apply(
            root=root, capability_name=CAPABILITY,
            payload={"claim_ids": sorted(claim_ids),
                     "claims_sha256": claims_sha256},
            reviewed_content=_canonical_list_bytes(claim_ids),
            reviewed_sha256=claims_sha256,
            review_report=review_report,
            parser_factory=getattr(args, "_parser_factory", None))
    with _operator_lock(root):
        if not _expected_ok(root, getattr(args, "expected_snapshot", None)):
            return 3
        try:
            analysis = analyze(root)
        except (LineageError, githistory.GitHistoryError, OSError,
                ValueError) as exc:
            print(f"los: re-stamp analysis failed: {exc}", file=sys.stderr)
            return 2
        snapshot = f"sha256:{canonical_fingerprint(root)}"
        if getattr(args, "check", False) and not claim_ids:
            print(json.dumps(
                {"ok": True, "mode": "check", "capability": CAPABILITY,
                 "expected_snapshot": snapshot, **analysis},
                ensure_ascii=False, sort_keys=True))
            return 0
        if not claim_ids or not claims_sha256:
            print("los: lineage-restamp needs --claim-ids with --claims-sha256 "
                  "(the reviewed list); --check alone recomputes eligibility",
                  file=sys.stderr)
            return 2
        try:
            ordered, planned = _verify_named(analysis, claim_ids, claims_sha256)
        except (WriteRefused, LineageError) as exc:
            print(f"los: {exc}", file=sys.stderr)
            return 2
        plan = {cid: dict(planned[cid]["new_reads"]) for cid in ordered}
        plan_sha = _plan_sha256(plan)
        if getattr(args, "check", False):
            from learning_os.commands.capability import prepare_review_envelope

            _artifacts, revisions = _ledger_guards(root)
            payload = {"claim_ids": ordered, "claims_sha256": claims_sha256}
            print(json.dumps(
                {"ok": True, "mode": "check", "capability": CAPABILITY,
                 "claim_ids": ordered, "claims_sha256": claims_sha256,
                 "plan": plan, "plan_sha256": plan_sha,
                 "expected_snapshot": snapshot,
                 "expected_revisions": revisions,
                 "reviewed_file_sha256": claims_sha256,
                 "gateway_envelope": prepare_review_envelope(
                     CAPABILITY, payload, snapshot, revisions)},
                ensure_ascii=False, sort_keys=True))
            return 0
        from learning_os.contracts.gateway import current_gateway_request

        request = current_gateway_request()
        if request is None:
            print("los: lineage-restamp applies only through its reviewed "
                  "report (--review-report) or a sealed GatewayEnvelopeV2 "
                  "(`los capability lineage.restamp --payload-file "
                  "ENVELOPE.json`); direct CLI application is disabled",
                  file=sys.stderr)
            return 2
        try:
            records = load_ledger(root)
            stamped = dict(records)
            restamped_by = f"{request.channel}/{request.approval_kind}"
            restamped_on = _dt.datetime.now(_dt.UTC).date().isoformat()
            for cid in ordered:
                prior = records.get(cid)
                if prior is None:
                    raise LineageError(f"claim {cid!r} left the ledger")
                stamped[cid] = restamp_claim(
                    prior, source_hashes=plan[cid],
                    restamped_by=restamped_by, restamped_on=restamped_on)
            text = dump_ledger(stamped)
        except LineageError as exc:
            print(f"los: {exc}", file=sys.stderr)
            return 2
        code, errors, confirmation = _write_transaction(
            root, {root / LEDGER_RELATIVE: text},
            capability=CAPABILITY,
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=(),
            # The envelope's intent hash already binds the claim list;
            # echoing the hash and the count here keeps the receipt
            # directly auditable without reopening the envelope.
            metadata={"claims_sha256": claims_sha256,
                      "claims_count": len(ordered)},
        )
        if code:
            print("los: lineage re-stamp failed", file=sys.stderr)
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code
        print(json.dumps(
            {"ok": True, "mode": "apply", "capability": CAPABILITY,
             "claim_ids": ordered, "claims_sha256": claims_sha256,
             "plan_sha256": plan_sha, **confirmation},
            ensure_ascii=False, sort_keys=True))
        return 0
