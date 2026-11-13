"""The capability envelope gateway — the machine-facing write surface (ADR-006).

Moved verbatim from commands/capability.py (PLAN 4.1): the CLI half of the
gateway transport adapter.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from learning_os.app.gateway import read_structured_file as _read_structured_file
from learning_os.app.pipeline import close_attempt as _close_attempt
from learning_os.app.pipeline import run_gateway
from learning_os.store.contracts.capability_catalog import command_definitions
from learning_os.store.diagnostics import tracer as diag_tracer
from learning_os.store.diagnostics.context import record_debug, trace_context_from_env
from learning_os.store.diagnostics.store import bind_store as _bind_diag_store


def _root(args: argparse.Namespace) -> Path:
    if args.root:
        return Path(args.root).resolve()
    return Path(__file__).resolve().parents[3]


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
    sys.stdout.write(outcome.stdout)
    sys.stderr.write(outcome.stderr)
    return outcome.exit_code
