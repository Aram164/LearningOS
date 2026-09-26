#!/usr/bin/env python3
"""Seal one GatewayEnvelopeV2 from caller-supplied intent (WORKFLOWS §25c).

The §25c ceremony without hand-rolled hashing: reads the current snapshot
live, takes guards, payload, and identities on the command line, and emits
the sealed envelope. Reads the repository; writes nothing canonical (an
--out path inside the repo is refused — envelopes belong in scratch).
"""

from __future__ import annotations

import argparse
import json
import secrets
import sys
from pathlib import Path

from learning_os.contracts.gateway import (
    APPROVAL_KINDS,
    GATEWAY_CHANNELS,
    GATEWAY_SCHEMA_VERSION,
    intent_sha256,
)
from learning_os.fingerprint import source_fingerprint
from learning_os.loader import load_repo

# capability-envelope.schema.json bounds request_id at 128 characters.
REQUEST_ID_MAX = 128


def _fresh_request_id(key: str) -> str:
    """Mint a new request id for this sealing run (WORKFLOWS §25c step 4).

    An exact retry keeps its idempotency key by design, so a key-derived id
    would repeat across attempts, and `los operations` would merge them into
    one explanation (a refused attempt reads as the committed one).
    """
    suffix = secrets.token_hex(4)
    stem = key[:REQUEST_ID_MAX - len("request--") - len(suffix)]
    return f"request-{stem}-{suffix}"


def _parse_revision(spec: str) -> tuple[str, int]:
    artifact, sep, revision = spec.partition("=")
    if not sep or not artifact.strip():
        raise ValueError(f"revision must look like ART=REV, got {spec!r}")
    try:
        number = int(revision)
    except ValueError as exc:
        raise ValueError(f"revision must look like ART=REV, got {spec!r}") from exc
    if number < 0:
        raise ValueError(f"revision must look like ART=REV, got {spec!r}")
    return artifact.strip(), number


def _load_payload(spec: str) -> dict:
    text = Path(spec[1:]).read_text(encoding="utf-8") if spec.startswith("@") else spec
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"payload is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None,
                        help="repository root (default: the checkout holding tools/)")
    parser.add_argument("--capability", required=True, help="capability name")
    parser.add_argument("--payload", required=True,
                        help="payload JSON, or @PATH to a JSON file")
    parser.add_argument("--key", required=True, help="idempotency key")
    parser.add_argument("--request-id", default=None,
                        help="request id (default: a fresh request-<key>-<random> "
                             "per run, as §25c step 4 asks)")
    parser.add_argument("--channel", default="operator",
                        help=f"one of: {', '.join(sorted(GATEWAY_CHANNELS))}")
    parser.add_argument("--approval-kind", default="operator-approval",
                        help=f"one of: {', '.join(sorted(APPROVAL_KINDS))}")
    parser.add_argument("--snapshot", default=None,
                        help="expected snapshot (default: read live)")
    parser.add_argument("--revision", action="append", default=[],
                        help="guard ART=REV; repeatable")
    parser.add_argument("--out", default=None,
                        help="write the envelope here (default: stdout)")
    args = parser.parse_args(argv)

    if args.channel not in GATEWAY_CHANNELS:
        print(f"seal_envelope: unknown channel {args.channel!r}", file=sys.stderr)
        return 2
    if args.approval_kind not in APPROVAL_KINDS:
        print(f"seal_envelope: unknown approval kind {args.approval_kind!r}",
              file=sys.stderr)
        return 2
    try:
        revisions = dict(_parse_revision(spec) for spec in args.revision)
    except ValueError as exc:
        print(f"seal_envelope: {exc}", file=sys.stderr)
        return 2
    try:
        payload = _load_payload(args.payload)
    except (ValueError, OSError) as exc:
        print(f"seal_envelope: {exc}", file=sys.stderr)
        return 2

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parent.parent
    if args.out:
        target = Path(args.out).resolve()
        if target == root or root in target.parents:
            print("seal_envelope: refusing to write the envelope inside the "
                  "repository; point --out at scratch", file=sys.stderr)
            return 2

    snapshot = args.snapshot or f"sha256:{source_fingerprint(load_repo(root))}"
    envelope = {
        "schema_version": GATEWAY_SCHEMA_VERSION,
        "request_id": args.request_id or _fresh_request_id(args.key),
        "idempotency_key": args.key,
        "capability": args.capability,
        "channel": args.channel,
        "expected_snapshot": snapshot,
        "expected_revisions": revisions,
        "payload": payload,
    }
    envelope["approval"] = {
        "kind": args.approval_kind,
        "subject_sha256": intent_sha256(envelope),
    }
    text = json.dumps(envelope, indent=2, sort_keys=True, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
