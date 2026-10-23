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

With ``--submit`` the tool also applies what it sealed: one call per write.
The gateway receives the envelope exactly as ``los capability NAME
--payload-file`` would, and the result is printed as that command prints it.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from learning_os.app import handlers  # noqa: F401  (registration side effect)
from learning_os.app import seal as _seal
from learning_os.app.registry import REGISTRY
from learning_os.store.contracts.gateway import (
    APPROVAL_KINDS,
    GATEWAY_CHANNELS,
    GATEWAY_SCHEMA_VERSION,
    intent_sha256,
)
from learning_os.store.fingerprint import canonical_fingerprint


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


def _derive_guards_auto(root: Path, **kwargs) -> tuple[str, dict[str, int]]:
    """The legacy dry-run derivation (``learning_os.app.seal``).

    ``los`` is resolved here, at call time, so the parser in force is the
    one the caller (or a test) installed.
    """
    import los  # noqa: E402  (imports the parser, not a command)

    return _seal.derive_guards_auto(root, parser_factory=los.build_parser, **kwargs)


def _derive_registered_guards(root: Path, **kwargs) -> tuple[str, dict[str, int]]:
    """The registered-operation derivation, with its staged-shadow check."""
    return _seal.derive_registered_guards(root, **kwargs)


def build_parser() -> argparse.ArgumentParser:
    """The seal's CLI surface.

    Factored out of ``main`` so the A11 surface snapshot can introspect the
    same parser that defines the flags, instead of a second copy that drifts.
    """
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
    guards = parser.add_mutually_exclusive_group()
    guards.add_argument("--guards", default=None, choices=("auto",),
                        help="guard derivation: 'auto' runs the capability's "
                             "handler as a gateway dry run that stops before "
                             "any write, and reads revisions under the same "
                             "lock as the snapshot. Explicit --revision "
                             "entries override derived ones.")
    guards.add_argument("--guards-from", default=None, metavar="PATH",
                        help="seal from a check record at PATH instead of "
                             "deriving guards (mutually exclusive with "
                             "--guards and explicit guards)")
    parser.add_argument("--check-out", default=None, metavar="PATH",
                        help="with --guards auto on a registered operation, "
                             "also write the check record to PATH")
    parser.add_argument("--out", default=None,
                        help="write the envelope here (default: stdout)")
    parser.add_argument("--submit", action="store_true",
                        help="seal with derived guards and submit through the "
                             "gateway in this one call, printing its result; "
                             "a retry with the same --key and payload replays "
                             "the committed receipt")
    return parser


def _submit(root: Path, args: argparse.Namespace, payload: dict,
            session_id: str | None) -> int:
    """Seal in process and hand the envelope to the gateway (agent-cost D1).

    The envelope is the per-key retry file ``learning_os.app.seal`` keeps, so
    the gateway reads exactly the bytes a retry would resubmit. The commit
    validates the real tree once; the staged-shadow check ``--guards auto``
    runs is skipped, because it would only run the same rules again.
    """
    import los  # noqa: E402  (imports the parser, not a command)
    from learning_os.adapters.capability import cmd_capability
    from learning_os.domain.failures import TransactionFailure, WriteRefused

    try:
        _seal.seal_with_key(
            root, capability=args.capability, payload=payload, key=args.key,
            parser_factory=los.build_parser, channel=args.channel,
            approval_kind=args.approval_kind, session_id=session_id)
    except (OSError, ValueError, WriteRefused, TransactionFailure) as exc:
        print(f"seal_envelope: {exc}", file=sys.stderr)
        return 2
    return cmd_capability(argparse.Namespace(
        root=str(root), name=args.capability,
        payload_file=str(_seal.retry_path(root, args.key)),
        replay_only=False, _parser_factory=los.build_parser))


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # S13 candidate J13-J14c: flag-combination usage errors, first.
    if args.check_out and args.guards_from:
        print("seal_envelope: --check-out cannot be combined with --guards-from",
              file=sys.stderr)
        return 2
    if args.guards_from and args.revision:
        print("seal_envelope: --guards-from cannot be combined with explicit "
              "--revision guards", file=sys.stderr)
        return 2
    if args.guards_from and args.snapshot:
        print("seal_envelope: --guards-from cannot be combined with explicit "
              "--snapshot", file=sys.stderr)
        return 2
    if args.check_out and args.guards != "auto":
        print("seal_envelope: --check-out requires --guards auto", file=sys.stderr)
        return 2
    if args.submit:
        # A one-call write derives every guard itself and keeps its envelope
        # as retry state, so an explicit guard, identity or output would be a
        # second, conflicting source for the same fact.
        clashing = [flag for flag, value in (
            ("--guards-from", args.guards_from), ("--revision", args.revision),
            ("--snapshot", args.snapshot), ("--request-id", args.request_id),
            ("--check-out", args.check_out), ("--out", args.out)) if value]
        if clashing:
            print(f"seal_envelope: --submit derives its own guards and request "
                  f"id; drop {', '.join(clashing)}", file=sys.stderr)
            return 2

    if args.channel not in GATEWAY_CHANNELS:
        print(f"seal_envelope: unknown channel {args.channel!r}", file=sys.stderr)
        return 2
    if args.channel == "ui":
        # The `ui` channel is the app's own expression of "a human pressed a
        # button", and admission admits a direct-user-gesture only from it
        # (learning_os.app.admission.gesture_allowed). The app builds its
        # envelopes in process, so nothing here is what the app uses; sealing
        # one from the command line would let a shell claim the app's
        # provenance. The channel stays in GATEWAY_CHANNELS for the app.
        print("seal_envelope: the 'ui' channel is the application's own "
              "provenance; the CLI cannot claim it", file=sys.stderr)
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
        payload = _seal.load_payload(args.payload)
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

    if args.submit:
        return _submit(root, args, payload, sealed_session)

    request_id = args.request_id or _seal.fresh_request_id(args.key)
    if args.guards_from:
        try:
            record = json.loads(
                Path(args.guards_from).read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            print(f"seal_envelope: {exc}", file=sys.stderr)
            return 2
        # S13 candidate J9-J12: record validation, in SPEC order.
        if not isinstance(record, dict) or record.get("schema") != 1:
            print("seal_envelope: --guards-from record schema must be 1",
                  file=sys.stderr)
            return 2
        if record.get("ok") is not True:
            print("seal_envelope: --guards-from record reports a failed check",
                  file=sys.stderr)
            return 2
        if record.get("capability") != args.capability:
            print(f"seal_envelope: --guards-from record is for capability "
                  f"{record.get('capability')!r}, not {args.capability!r}",
                  file=sys.stderr)
            return 2
        if isinstance(payload, dict):
            sealing = {key: value for key, value in payload.items()
                       if key != "check"}
        else:
            sealing = payload
        if (json.dumps(sealing, sort_keys=True)
                != json.dumps(record.get("payload"), sort_keys=True)):
            print("seal_envelope: --guards-from record payload differs from "
                  "the sealing payload", file=sys.stderr)
            return 2
        snapshot = record["expected_snapshot"]
        revisions = dict(record["expected_revisions"])
    elif args.guards == "auto":
        if args.check_out and args.capability not in REGISTRY:
            print("seal_envelope: --check-out requires a registered operation",
                  file=sys.stderr)
            return 2
        if args.capability in REGISTRY:
            try:
                snapshot, derived = _derive_registered_guards(
                    root, capability=args.capability, payload=payload,
                    key=args.key, request_id=request_id, channel=args.channel,
                    approval_kind=args.approval_kind, snapshot=args.snapshot,
                    check_out=args.check_out)
            except (ValueError, OSError) as exc:
                print(f"seal_envelope: {exc}", file=sys.stderr)
                return 2
        else:
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
        snapshot = args.snapshot or f"sha256:{canonical_fingerprint(root)}"
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
