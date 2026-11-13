"""CLI parser and check-record adapter for ``tools/seal_envelope.py``.

Shared by ``seal_envelope.py``, the A11 surface snapshot, and
``learning_os.adapters.study_broker`` without creating an upward dependency on
the study broker.
"""

from __future__ import annotations

import argparse

from learning_os.store.contracts.gateway import APPROVAL_KINDS, GATEWAY_CHANNELS

SEAL_GUARDS_STDIN_ENV = "LOS_SEAL_GUARDS_STDIN"

_SEAL_DOC = "Seal one GatewayEnvelopeV2 from caller-supplied intent (WORKFLOWS §25c)."


def build_seal_parser(description: str | None = None) -> argparse.ArgumentParser:
    """Build the seal_envelope.py CLI parser (shared by A11 snapshot, CLI, and broker)."""
    parser = argparse.ArgumentParser(description=description or _SEAL_DOC)
    parser.add_argument(
        "--root",
        default=None,
        help="repository root (default: the checkout holding tools/)",
    )
    parser.add_argument(
        "--capability",
        default=None,
        help="capability name (required unless derived from a --guards-from record)",
    )
    parser.add_argument(
        "--payload",
        default=None,
        help="payload JSON, or @PATH to a JSON file (required unless derived from a "
             "--guards-from record)",
    )
    parser.add_argument(
        "--key",
        default=None,
        help="idempotency key (required unless the --guards-from record carries it)",
    )
    parser.add_argument(
        "--request-id",
        default=None,
        help="request id (default: a fresh request-<key>-<random> per run, as §25c step 4 "
             "asks; to retry, resubmit the saved envelope instead of re-sealing)",
    )
    parser.add_argument(
        "--channel",
        default="operator",
        help=f"one of: {', '.join(sorted(GATEWAY_CHANNELS))}",
    )
    parser.add_argument(
        "--session-id",
        default=None,
        help="sealed session identity for this write's ledger rows (default: none — "
             "resolution falls back to LOS_SESSION_ID, then the channel; WORKFLOWS §25c "
             "step 4)",
    )
    parser.add_argument(
        "--approval-kind",
        default="operator-approval",
        help=f"one of: {', '.join(sorted(APPROVAL_KINDS))}",
    )
    parser.add_argument(
        "--snapshot",
        default=None,
        help="expected snapshot (default: read live)",
    )
    parser.add_argument(
        "--revision",
        action="append",
        default=[],
        help="guard ART=REV; repeatable",
    )
    guards = parser.add_mutually_exclusive_group()
    guards.add_argument(
        "--guards",
        default=None,
        choices=("auto",),
        help="guard derivation: 'auto' runs the capability's handler as a gateway dry run "
             "that stops before any write, and reads revisions under the same lock as the "
             "snapshot. Explicit --revision entries override derived ones.",
    )
    guards.add_argument(
        "--guards-from",
        default=None,
        metavar="PATH",
        help="seal from a check record at PATH instead of deriving guards (mutually "
             "exclusive with --guards and explicit guards)",
    )
    parser.add_argument(
        "--check-out",
        default=None,
        metavar="PATH",
        help="with --guards auto on a registered operation, also write the check record "
             "to PATH",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="write the envelope here (default: stdout)",
    )
    parser.add_argument(
        "--submit",
        action="store_true",
        help="seal with derived guards, or with a reviewed --guards-from record's, and "
             "submit through the gateway in this one call, printing its result; a retry "
             "with the same --key and payload replays the committed receipt",
    )
    return parser


def normalize_check_record(record: object) -> object:
    """Normalize a ``--check --report-out`` record to the schema-1 check record shape."""
    if (
        isinstance(record, dict)
        and record.get("schema") is None
        and record.get("mode") == "check"
        and record.get("ok") is True
        and isinstance(record.get("gateway_envelope"), dict)
        and isinstance(record.get("expected_snapshot"), str)
        and isinstance(record.get("expected_revisions"), dict)
    ):
        envelope = record["gateway_envelope"]
        return {
            "schema": 1,
            "ok": record.get("ok"),
            "capability": record.get("capability") or envelope.get("capability"),
            "expected_snapshot": record["expected_snapshot"],
            "expected_revisions": record["expected_revisions"],
            "payload": envelope.get("payload"),
            "idempotency_key": record.get("idempotency_key"),
        }
    return record
