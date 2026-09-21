#!/usr/bin/env python3
"""Resume and verify one curriculum plan transaction from its saved report.

The saved --check JSON is the durable handoff between draft, review,
apply, retry, and verification: this command resolves the request and
receipt identity itself through the idempotency ledger, so a fresh
process resumes without reconstructing paths, revision guards, envelopes,
or retry identity. It never writes canonical data and never issues a
mutation — a failed verification is never permission to apply something
new. Re-running the saved reviewed apply replays the same receipt when
canonical state still matches it, and fails closed without a new commit
when state drifted past the receipt.

The first stdout line is always `state: <name>`:

- committed-and-verified (exit 0): the exact reviewed request committed
  and every post-commit check agrees with the live projection.
- committed-but-verification-failed (exit 1): the receipt exists but the
  live state drifted or the projection is stale; regenerate and re-verify.
- not-applied-or-stale-preflight (exit 3): no committed receipt for this
  exact reviewed request; re-run --check, review, then apply.
- uncertain-requires-replay-lookup (exit 2): the replay lookup itself was
  inconclusive; reconcile the idempotency ledger by hand.
- invalid-evidence (exit 2): the report is not a successful preflight for
  this unit, or the named receipt is not its committed transaction.

Usage:
    .venv/bin/python tools/verify_plan_receipt.py \
        --unit unit-m2-sad-l04 \
        --report /tmp/unit-revise-check.json \
        [--receipt operations/transactions/transaction-....yaml] \
        [--expect-artifacts module-x,unit-y]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent
sys.path.insert(0, str(TOOLS))

from learning_os.commands.capability import (  # noqa: E402
    _context_from_v2,
    _validate_capability_envelope,
    _validate_payload,
)
from learning_os.commands.support import (  # noqa: E402
    WriteRefused,
    _operator_lock,
    _read_structured_file,
)
from learning_os.fingerprint import canonical_fingerprint  # noqa: E402
from learning_os.loader import load_repo  # noqa: E402
from learning_os.material_synthesis import (  # noqa: E402
    MaterialSynthesisError,
    synthesis_destination,
    validate_unit_material_synthesis,
)
from learning_os.transactions import (  # noqa: E402
    TransactionFailure,
    TransactionIdempotencyConflict,
    replay_for_request,
)


class _StalePreflight(Exception):
    """No committed receipt for this exact reviewed request."""


class _UncertainEvidence(Exception):
    """The replay lookup itself was inconclusive."""


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _same_digest(recorded: str | None, actual_hex: str) -> bool:
    # Receipt write rows store bare hex; snapshots carry the sha256: prefix.
    if not recorded:
        return True
    return recorded.removeprefix("sha256:") == actual_hex.removeprefix("sha256:")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", required=False, default=None,
                        help="expected receipt; when omitted the receipt is "
                             "resolved from the report through the ledger")
    parser.add_argument("--unit", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--expect-artifacts", default=None)
    parser.add_argument("--root", default=None)
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else REPO
    try:
        with _operator_lock(root):
            return verify(root, args)
    except _StalePreflight as exc:
        print("state: not-applied-or-stale-preflight")
        print(f"verify-plan-receipt: {exc}; re-run --check, review the new "
              "report, then apply that report", file=sys.stderr)
        return 3
    except _UncertainEvidence as exc:
        print("state: uncertain-requires-replay-lookup")
        print(f"verify-plan-receipt: uncertain outcome: {exc}; inspect "
              "operations/transactions/idempotency.yaml and the receipt it "
              "names, reconcile by hand, and never re-apply blindly",
              file=sys.stderr)
        return 2
    except (OSError, ValueError, yaml.YAMLError, KeyError, TypeError,
            TransactionFailure, WriteRefused) as exc:
        print("state: invalid-evidence")
        print(f"verify-plan-receipt: invalid verification evidence: {exc}", file=sys.stderr)
        return 2


def verify(root: Path, args) -> int:
    failures: list[str] = []
    named_receipt = None
    if args.receipt:
        named_receipt = (root / args.receipt).resolve() \
            if not Path(args.receipt).is_absolute() else Path(args.receipt)
    report = _read_structured_file(args.report)
    if report.get("ok") is not True or report.get("mode") != "check":
        raise ValueError("not a successful preflight report")
    envelope = report.get("gateway_envelope")
    if not isinstance(envelope, dict):
        raise ValueError("report has no gateway envelope")
    _validate_capability_envelope(root, envelope, kind="request")
    capability = envelope["capability"]
    if capability not in {"unit.plan.revise", "module.plan.import"} \
            or report.get("capability") != capability:
        raise ValueError("report is not for a supported plan revision")
    _validate_payload(root, capability, envelope["payload"])
    if envelope["expected_snapshot"] != report.get("expected_snapshot") \
            or envelope["expected_revisions"] != report.get("expected_revisions"):
        raise ValueError("report guards differ from its approved request")
    if args.unit not in report.get("units", {}):
        raise ValueError("target unit was not reviewed in this report")
    if capability == "unit.plan.revise" and envelope["payload"].get("unit_id") != args.unit:
        raise ValueError("request targets another unit")
    # Reuse the production verifier: schema, approval, idempotency ledger,
    # revision ledger, safe paths, authority scopes and final bytes. Request
    # and receipt identity resolve here, from the report alone — the caller
    # never reconstructs them.
    try:
        replay = replay_for_request(root, _context_from_v2(envelope))
    except TransactionIdempotencyConflict as exc:
        raise _StalePreflight(
            "this idempotency key committed a different approved intent "
            f"({exc}); this reviewed request never committed") from exc
    except TransactionFailure as exc:
        raise _UncertainEvidence(str(exc)) from exc
    if replay is None:
        raise _StalePreflight(
            "no committed receipt exists for this exact reviewed request")
    receipt_path = replay.receipt_path.resolve()
    if named_receipt is not None and receipt_path != named_receipt.resolve():
        raise ValueError("receipt is not the committed transaction for this exact reviewed request")
    receipt = replay.receipt
    if receipt["snapshot_before"] != report["expected_snapshot"]:
        raise ValueError("receipt was applied against a different reviewed snapshot")
    expected = report["expected_revisions"]
    if set(receipt["artifact_revisions"]) != set(expected) \
            or set(report.get("commit_artifact_ids", [])) != set(expected):
        raise ValueError("receipt artifact set does not match the preflight")
    for aid, revision in expected.items():
        if receipt["artifact_revisions"][aid] != {"before": revision, "after": revision + 1}:
            raise ValueError(f"unexpected revision change for {aid}")
    service_paths = {"operations/transactions/revisions.yaml", "operations/transactions/idempotency.yaml"}
    written_paths = {row["path"] for row in receipt["writes"]} - service_paths
    if written_paths != set(report.get("expected_write_paths", [])):
        raise ValueError("receipt writes do not match the preflight")
    receipt_hashes = {row["path"]: row["sha256_after"] for row in receipt["writes"]}
    expected_hashes = report.get("expected_write_sha256")
    if not isinstance(expected_hashes, dict) or not expected_hashes \
            or set(expected_hashes) != written_paths - {"operations/transactions/lineage.yaml"} \
            or any(receipt_hashes.get(path) != digest for path, digest in expected_hashes.items()):
        raise ValueError("receipt final bytes do not match the preflight")

    for row in receipt.get("writes", []) or []:
        if not isinstance(row, dict):
            continue
        target = (root / row["path"]).resolve()
        if not target.is_file():
            failures.append(f"receipt write is gone: {row['path']}")
            continue
        if row.get("sha256_after") and not _same_digest(row["sha256_after"], _sha(target)):
            failures.append(f"receipt write changed after commit: {row['path']}")

    current = f"sha256:{canonical_fingerprint(root)}"
    if current != receipt.get("snapshot_after"):
        failures.append("canonical state moved since the receipt snapshot_after; "
                        "regenerate and re-verify")
    manifest_path = root / "generated" / "manifest.json"
    if not manifest_path.is_file():
        failures.append("generated manifest is missing; run tools/generate.py")
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except ValueError as exc:
            failures.append(f"generated manifest is not JSON: {exc}")
        else:
            generated_block = manifest.get("_generated", {}) \
                if isinstance(manifest.get("_generated"), dict) \
                else (manifest.get("generated", {})
                      if isinstance(manifest.get("generated"), dict) else {})
            snapshot_id = manifest.get("snapshot_id") or generated_block.get("snapshot_id")
            if snapshot_id != receipt.get("snapshot_after"):
                failures.append("generated manifest snapshot_id does not match "
                                "the receipt snapshot_after; run tools/generate.py")
            units = {u.get("id") for u in manifest.get("units", []) or []
                     if isinstance(u, dict)}
            if args.unit not in units:
                failures.append(f"target unit does not resolve in the manifest: {args.unit}")

    repo = load_repo(root)
    live_map = ((repo.module_source_maps or {}).get(report.get("module_id", "")) or {})
    rows = [r for s in live_map.get("sources", []) or [] if isinstance(s, dict)
            for r in s.get("unit_routes", []) or [] if isinstance(r, dict) and r.get("id")]
    if len(rows) != report.get("route_counts", {}).get("after"):
        failures.append("live route count does not match the preflight report")
    unit_rows = report["units"][args.unit]
    live_unit_rows = [r for r in rows if r.get("unit_id") == args.unit]
    live_placements = sum(
        len(s.get("resources", []) or [])
        for sm in repo.study_maps.values() if sm.unit_id == args.unit
        for s in (sm.data.get("stages", []) or []) if isinstance(s, dict))
    if len(live_unit_rows) != unit_rows.get("routes_after"):
        failures.append("live unit route count does not match the report")
    if live_placements != unit_rows.get("placements_after"):
        failures.append("live placement count does not match the report")

    try:
        destination = synthesis_destination(root, args.unit)
    except MaterialSynthesisError:
        destination = None
    if destination is not None and destination.is_file():
        try:
            dossier = yaml.safe_load(destination.read_text(encoding="utf-8"))
            validate_unit_material_synthesis(root, args.unit, dossier)
        except Exception as exc:
            failures.append(f"synthesis is not current and complete: {exc}")
    else:
        failures.append(f"no synthesis dossier for the target unit: {args.unit}")

    if args.expect_artifacts:
        expected = {a.strip() for a in args.expect_artifacts.split(",") if a.strip()}
        moved = {a for a, rev in
                 (receipt.get("artifact_revisions", {}) or {}).items()
                 if isinstance(rev, dict) and rev.get("after") != rev.get("before")}
        if moved != expected:
            failures.append(f"artifact set differs: expected={sorted(expected)}, actual={sorted(moved)}")

    if failures:
        print("state: committed-but-verification-failed")
        print("verify-plan-receipt: FAILED", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        print("verify-plan-receipt: the receipt is committed; this failure is "
              "post-commit drift or a stale projection, never permission to "
              "issue a new mutation — regenerate and re-verify, or open a new "
              "preflight if canonical state must change further",
              file=sys.stderr)
        return 1
    print("state: committed-and-verified")
    try:
        receipt_rel = receipt_path.relative_to(root.resolve()).as_posix()
    except ValueError:
        receipt_rel = str(receipt_path)
    print(f"verify-plan-receipt: ok "
          f"(request {envelope.get('request_id')}, receipt {receipt_rel}, "
          f"snapshot {receipt.get('snapshot_after', '')[:19]}…, "
          f"{len(receipt.get('writes', []) or [])} writes, unit {args.unit})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
