#!/usr/bin/env python3
"""Seal one GatewayEnvelopeV2 from caller-supplied intent (WORKFLOWS §25c).

The §25c ceremony without hand-rolled hashing: reads the current snapshot
live, takes guards, payload, and identities on the command line, and emits
the sealed envelope. Reads the repository; writes nothing canonical (an
--out path inside the repo is refused — envelopes belong in scratch).

With ``--guards auto`` the guard set is derived, not guessed: the
capability's own handler runs as a gateway dry run that stops at the
transaction boundary before any write, and the artifact set it reaches the
boundary with — computed by the same function the gateway enforces — is
read at the same instant as the snapshot, under the same lock.
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

    Each sealing run is a new attempt with its own key, so a key-derived id is
    never needed. An exact retry does not come back here: it resubmits the
    envelope this run already produced, because replay binds the committed
    request id and refuses a re-sealed envelope under a used key.
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


class _DryRunCapture(Exception):
    """The dry-run handler reached the transaction boundary with this set."""

    def __init__(self, artifacts: list[str]):
        super().__init__("dry run reached the transaction boundary")
        self.artifacts = artifacts


def _derive_guards_auto(root: Path, *, capability: str, payload: dict,
                        key: str, request_id: str, channel: str,
                        approval_kind: str,
                        snapshot: str | None) -> tuple[str, dict[str, int]]:
    """Derive the exact guard set with a gateway dry run.

    Runs the capability's own handler through the gateway's ``_dispatch``
    — the same payload validation, the same namespace, the same handler —
    with the transaction service stubbed to capture the artifact set and
    stop before any write. Returns the snapshot and the artifact set bound
    to the revision ledger read under the same operator lock, so the two
    answer the same instant and a concurrent canonical change still
    refuses the sealed envelope as ``STALE_SNAPSHOT``.

    This adds no authority: the dry run commits nothing, and the sealed
    envelope passes through every gateway guard unchanged.
    """
    import los  # noqa: E402  (imports the parser, not a command)
    from learning_os.commands import support as _support
    from learning_os.commands.capability import _dispatch
    from learning_os.commands.support import WriteRefused
    from learning_os.contracts.capability_catalog import command_definitions
    from learning_os.contracts.gateway import (
        GatewayRequestContext,
        gateway_request_context,
        verified_gateway_snapshot,
    )
    from learning_os.revisions import load_revisions
    from learning_os.transactions import transaction_artifacts

    definitions = command_definitions(root)
    if capability not in definitions:
        raise ValueError(f"unknown capability: {capability}")
    from learning_os.contracts.payloads import subparsers as _subparsers

    command_parser = _subparsers(los.build_parser()).get(
        definitions[capability].cli_command or "")
    if command_parser is None:
        raise ValueError(
            f"capability {capability} declares no CLI command to derive guards from")
    if command_parser.get_default("func") is None:
        raise ValueError(
            f"capability {capability} has no bound handler to derive guards from")

    # Intercept at the class, not at one module's import of it: a handler
    # may commit through ``support._write_transaction`` or through its own
    # ``from learning_os.transactions import TransactionService`` (the AI
    # delivery path does). Patching one module's name would let the second
    # kind reach the real ``commit`` — with this dry run's placeholder
    # approval — so the boundary is the method every instance shares.
    from learning_os import transactions as _transactions

    real_commit = _transactions.TransactionService.commit

    def _dry_run_commit(self, *, artifact_ids=(), writes=None, deletes=(),
                        **_ignored):
        raise _DryRunCapture(transaction_artifacts(
            self.root, artifact_ids, writes or {}, deletes))

    # The request identities are the envelope's own: request-scoped
    # artifacts (capture, garden) derive from the idempotency key, so the
    # dry run must carry the key the envelope will be sealed under. The
    # intent hash is a placeholder — the stubbed boundary never checks
    # approval, and the real envelope's approval is computed afterwards
    # over the derived guards.
    context = GatewayRequestContext(
        request_id=request_id,
        idempotency_key=key,
        capability=capability,
        channel=channel,
        intent_sha256="sha256:" + "0" * 64,
        approval_kind=approval_kind,
        approval_subject_sha256="sha256:" + "0" * 64,
        expected_snapshot=None,  # set once the snapshot below is read
    )
    envelope_stub = {
        "schema_version": GATEWAY_SCHEMA_VERSION,
        "capability": capability,
        "expected_snapshot": snapshot,
        "expected_revisions": {},
    }
    _transactions.TransactionService.commit = _dry_run_commit  # type: ignore[method-assign]
    try:
        with _support._operator_lock(root):
            live_snapshot = snapshot or f"sha256:{source_fingerprint(load_repo(root))}"
            envelope_stub["expected_snapshot"] = live_snapshot
            context = GatewayRequestContext(
                request_id=context.request_id,
                idempotency_key=context.idempotency_key,
                capability=context.capability,
                channel=context.channel,
                intent_sha256=context.intent_sha256,
                approval_kind=context.approval_kind,
                approval_subject_sha256=context.approval_subject_sha256,
                expected_snapshot=live_snapshot,
            )
            with gateway_request_context(context), verified_gateway_snapshot(
                    root, live_snapshot):
                try:
                    code, result = _dispatch(
                        root, definitions[capability], envelope_stub, payload,
                        parser_factory=los.build_parser)
                except _DryRunCapture as captured:
                    revisions = load_revisions(root)
                    return live_snapshot, {
                        artifact: revisions.get(artifact, 0)
                        for artifact in captured.artifacts
                    }
                except WriteRefused as exc:
                    raise ValueError(
                        f"{exc}; fix the payload and seal again") from exc
            if code == 2:
                # The handler refused the payload itself (an unknown id, a
                # failed check): explicit guards cannot fix that, so say so
                # instead of sending the caller on a second refused round trip.
                raise ValueError(
                    f"{result.get('error', capability + ' failed')}; "
                    "fix the payload and seal again")
            raise ValueError(
                "guard derivation stopped before any transaction"
                f" (exit {code}: {result.get('error', capability + ' failed')}); "
                "seal this payload with explicit --revision guards instead")
    finally:
        _transactions.TransactionService.commit = real_commit  # type: ignore[method-assign]


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
                             "per run, as §25c step 4 asks; to retry, resubmit the "
                             "saved envelope instead of re-sealing)")
    parser.add_argument("--channel", default="operator",
                        help=f"one of: {', '.join(sorted(GATEWAY_CHANNELS))}")
    parser.add_argument("--session-id", default=None,
                        help="sealed session identity for this write's ledger "
                             "rows (default: none — resolution falls back to "
                             "LOS_SESSION_ID, then the channel; WORKFLOWS §25c "
                             "step 4)")
    parser.add_argument("--approval-kind", default="operator-approval",
                        help=f"one of: {', '.join(sorted(APPROVAL_KINDS))}")
    parser.add_argument("--snapshot", default=None,
                        help="expected snapshot (default: read live)")
    parser.add_argument("--revision", action="append", default=[],
                        help="guard ART=REV; repeatable")
    parser.add_argument("--guards", default=None, choices=("auto",),
                        help="guard derivation: 'auto' runs the capability's "
                             "handler as a gateway dry run that stops before "
                             "any write, and reads revisions under the same "
                             "lock as the snapshot. Explicit --revision "
                             "entries override derived ones.")
    parser.add_argument("--out", default=None,
                        help="write the envelope here (default: stdout)")
    args = parser.parse_args(argv)

    if args.channel not in GATEWAY_CHANNELS:
        print(f"seal_envelope: unknown channel {args.channel!r}", file=sys.stderr)
        return 2
    sealed_session = args.session_id.strip() if args.session_id else None
    if args.session_id is not None and not sealed_session:
        print("seal_envelope: --session-id must name a session, not blank text",
              file=sys.stderr)
        return 2
    if sealed_session is not None and len(sealed_session) > 128:
        print("seal_envelope: --session-id is longer than 128 characters",
              file=sys.stderr)
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

    request_id = args.request_id or _fresh_request_id(args.key)
    if args.guards == "auto":
        try:
            snapshot, derived = _derive_guards_auto(
                root, capability=args.capability, payload=payload,
                key=args.key, request_id=request_id, channel=args.channel,
                approval_kind=args.approval_kind, snapshot=args.snapshot)
        except (ValueError, OSError) as exc:
            print(f"seal_envelope: {exc}", file=sys.stderr)
            return 2
        revisions = {**derived, **revisions}
        print("seal_envelope: guards auto: "
              + ", ".join(f"{artifact}={revisions[artifact]}"
                          for artifact in sorted(revisions)),
              file=sys.stderr)
    else:
        snapshot = args.snapshot or f"sha256:{source_fingerprint(load_repo(root))}"
    envelope = {
        "schema_version": GATEWAY_SCHEMA_VERSION,
        "request_id": request_id,
        "idempotency_key": args.key,
        "capability": args.capability,
        "channel": args.channel,
        **({"session_id": sealed_session} if sealed_session is not None else {}),
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
