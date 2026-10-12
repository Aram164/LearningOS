"""The capability envelope gateway — the machine-facing write surface (ADR-006).

Moved verbatim from commands/capability.py (PLAN 4.1): the CLI half of the
gateway transport adapter.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from learning_os.contracts.capability_catalog import command_definitions
from learning_os.diagnostics import tracer as diag_tracer
from learning_os.diagnostics.context import record_debug, trace_context_from_env
from learning_os.diagnostics.store import bind_store as _bind_diag_store
from learning_os.domain.failures import WriteRefused
from learning_os.ops._legacy_plumbing import _read_structured_file
from learning_os.ops.legacy import (
    _context_from_v2,
    _dispatch,
    _validate_capability_envelope,
)
from learning_os.ops.pipeline import _close_attempt, run_gateway


def _root(args: argparse.Namespace) -> Path:
    if args.root:
        return Path(args.root).resolve()
    return Path(__file__).resolve().parents[3]


# Older human-facing commands intentionally keep path forms for shell use and
# no-write preflights. A V2 approval must additionally name the digest of every
# external file. Each named handler uses the shared single-read helper and
# parses or writes the same byte string that helper verified; reopening the
# pathname after hashing is forbidden.
_FILE_INPUTS_V2: dict[str, tuple[tuple[str, str, bool], ...]] = {
    "capture.create": (("file", "file_sha256", False),),
    "module.plan.import": (("file", "file_sha256", False),),
    "note.revise": (("file", "file_sha256", False),),
    "path.attachment.add": (("file", "file_sha256", False),),
    "project.create": (("file", "file_sha256", False),),
    "project.update": (("file", "file_sha256", False),),
    "review.prepare": (("items_file", "items_file_sha256", False),),
    "stage.attachment.add": (("file", "file_sha256", False),),
    "unit.map.import": (("file", "file_sha256", False),),
    "unit.note.append": (("attachment", "attachment_sha256", True),),
}


def reviewed_envelope_apply(*, root: Path, capability_name: str, payload: dict[str, Any],
                            reviewed_content: bytes, reviewed_sha256: str,
                            review_report: str | None,
                            parser_factory: Callable[[], argparse.ArgumentParser] | None) -> int:
    """Dispatch the saved preflight request without refreshing its authority.

    The caller parsed exactly reviewed_content. The saved report retains the
    complete envelope, including its identity, for exact retry after a lost
    response. Neither snapshot nor revisions are silently rebased here.
    """
    import argparse as _argparse
    import tempfile as _tempfile

    if parser_factory is None:
        print("los: reviewed apply needs the CLI parser factory", file=sys.stderr)
        return 2
    actual = "sha256:" + hashlib.sha256(reviewed_content).hexdigest()
    if actual != reviewed_sha256:
        print("los: reviewed bytes changed since --check; re-run --check, review "
              "the new report and its SHA, then apply that SHA", file=sys.stderr)
        print(json.dumps({"expected": reviewed_sha256, "actual": actual}),
              file=sys.stderr)
        return 2
    if not review_report:
        print("los: reviewed apply requires --review-report with the saved --check JSON",
              file=sys.stderr)
        return 2
    try:
        report = _read_structured_file(review_report)
        envelope = report.get("gateway_envelope")
        if not isinstance(envelope, dict):
            raise WriteRefused("review report has no prepared gateway envelope")
        _validate_capability_envelope(root, envelope, kind="request")
        _context_from_v2(envelope)
        if report.get("ok") is not True or report.get("mode") != "check" \
                or report.get("reviewed_file_sha256") != actual \
                or envelope.get("capability") != capability_name \
                or envelope.get("payload") != payload \
                or envelope.get("expected_snapshot") != report.get("expected_snapshot") \
                or envelope.get("expected_revisions") != report.get("expected_revisions"):
            raise WriteRefused("review report does not match the exact reviewed input and guards")
    except (OSError, ValueError, WriteRefused) as exc:
        print(f"los: {exc}", file=sys.stderr)
        return 2
    fd, tmp_name = _tempfile.mkstemp(prefix="learningos-reviewed-", suffix=".json")
    try:
        with open(fd, "w", encoding="utf-8") as handle:
            json.dump(envelope, handle, ensure_ascii=False)
        args = _argparse.Namespace(
            root=str(root),
            name=capability_name,
            payload_file=tmp_name,
            replay_only=False,
            _parser_factory=parser_factory,
        )
        return cmd_capability(args)
    finally:
        with contextlib.suppress(OSError):
            Path(tmp_name).unlink()


def cmd_capability(args: argparse.Namespace) -> int:
    # Research track #2, Phase 1: observe the UI-propagated trace context.
    # Pure env read plus an opt-in debug record; behavior is identical when
    # tracing is absent, malformed, or its sink fails. Never an input to any
    # guard, hash, receipt, or ledger below.
    record_debug(trace_context_from_env(), operation="capability",
                 extra={"capability": getattr(args, "name", None)})
    root = _root(args)
    # Phase 3A: bind this repository's disposable trace store first, so the
    # attempt span below persists like every later record. Binding is a pure
    # path assignment; persistence itself stays best-effort.
    _bind_diag_store(root)
    # Phase 2A: one attempt span per gateway invocation. All emissions below
    # are sink-gated no-ops by default; every return below closes the span.
    attempt = diag_tracer.begin_attempt(
        {"capability": getattr(args, "name", None)})
    definitions = command_definitions(root)
    # Preserve the legacy no-I/O refusal for an unknown name when there is no
    # envelope to classify. If a real V2 envelope exists, read it so the same
    # unknown name receives the required typed GatewayResultV2 error.
    if args.name not in definitions and args.payload_file != "-" \
            and not Path(args.payload_file).expanduser().is_file():
        print(f"los: unknown or non-public capability: {args.name}", file=sys.stderr)
        return _close_attempt(attempt, 2, "error", {"stage": "core.admission"})
    envelope = _read_structured_file(args.payload_file)
    outcome = run_gateway(
        root, envelope, requested=args.name, definitions=definitions,
        attempt=attempt, replay_only=args.replay_only,
        parser_factory=args._parser_factory)
    if outcome is not None:
        sys.stdout.write(outcome.stdout)
        sys.stderr.write(outcome.stderr)
        return outcome.exit_code
    payload = envelope.get("payload", {})
    request_id = envelope["request_id"]
    try:
        code, result = _dispatch(
            root,
            definitions[args.name],
            envelope,
            payload,
            parser_factory=args._parser_factory,
        )
    except WriteRefused as exc:
        code, result = 2, {"error": str(exc)}
    # The handler folds its own receipt facts into `result`, so the response
    # reads them from there rather than re-deriving them.
    confirmation = result if code == 0 else {}
    response = {
        "request_id": request_id,
        "capability": args.name,
        "ok": code == 0,
        "transaction_id": confirmation.get("transaction_id"),
        "receipt_path": confirmation.get("receipt_path"),
        "result": result if code == 0 else {},
        "error": None if code == 0 else result.get("error", "capability failed"),
    }
    _validate_capability_envelope(root, response, kind="result")
    print(json.dumps(response, indent=2, ensure_ascii=False))
    return _close_attempt(attempt, code, "ok" if code == 0 else "error")
