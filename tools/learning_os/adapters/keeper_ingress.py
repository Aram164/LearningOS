"""The Atlas Keeper's broker-internal write ingress (2B, CL-30; ADR-024).

The study broker's ``keeper`` profile runs this module, never a shell::

    python -I -m learning_os.adapters.keeper_ingress

It reads one JSON request from its stdin pipe, ``{"token", "tool", "argv",
"stdin"}``, and goes on only when the pipe carries the token whose SHA-256 the
broker placed in ``LOS_KEEPER_INGRESS_SHA256``. It passes Keeper ingress
explicitly to the gateway or the sealer:

- ``seal``: ``tools/seal_envelope.py`` with ``argv`` (the broker has already
  forced the Keeper's channel, approval kind and capability);
- ``capability``: ``los.py capability`` with ``argv``. The app's
  ``ui-capability`` entry is refused here.

``stdin`` is what the tool reads as its own stdin (an envelope or a reviewed
check record).

Limit, recorded in ADR-024: a same-user process can build this handshake on
purpose. That stays inside the trusted-host statement. What the ingress
removes is the one-flag route: no ``los.py`` subcommand and no seal flag lets
a host shell claim Keeper provenance.
"""

from __future__ import annotations

import hashlib
import hmac
import io
import json
import os
import runpy
import secrets
import stat
import sys
from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import cast

from learning_os.store.contracts.gateway import INGRESS_KEEPER

MODULE = "learning_os.adapters.keeper_ingress"
HANDSHAKE_ENV = "LOS_KEEPER_INGRESS_SHA256"
TOOLS = frozenset({"seal", "capability"})
#: The request is one envelope or check record plus argv: bounded like the
#: broker's own request frames.
MAX_REQUEST_BYTES = 8 * 1024 * 1024

_CORE_ROOT = Path(__file__).resolve().parents[3]


def token_digest(token: str) -> str:
    return "sha256:" + hashlib.sha256(token.encode("utf-8")).hexdigest()


def new_handshake() -> tuple[str, str]:
    """A fresh one-time token and the digest the child's environment carries."""
    token = secrets.token_hex(32)
    return token, token_digest(token)


def request_text(token: str, tool: str, argv: list[str], stdin_text: str | None) -> str:
    """The exact stdin a broker writes for one Keeper ingress call."""
    if tool not in TOOLS:
        raise ValueError(f"unknown Keeper ingress tool: {tool!r}")
    return json.dumps({"token": token, "tool": tool, "argv": list(argv),
                       "stdin": stdin_text})


def _refuse(reason: str) -> int:
    print(f"keeper ingress: {reason}", file=sys.stderr)
    return 2


def _read_request() -> tuple[dict[str, object] | None, str | None]:
    try:
        mode = os.fstat(sys.stdin.fileno()).st_mode
    except (OSError, ValueError):
        return None, "stdin is not the study broker's pipe"
    if not stat.S_ISFIFO(mode):
        return None, "stdin is not the study broker's pipe"
    raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
    if len(raw) > MAX_REQUEST_BYTES:
        return None, "the request is larger than a Keeper request can be"
    try:
        request: object = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, "the request is not JSON"
    if not isinstance(request, dict):
        return None, "the request is not a JSON object"
    return cast(dict[str, object], request), None


def _run_seal(argv: list[str]) -> int:
    namespace = runpy.run_path(str(_CORE_ROOT / "tools" / "seal_envelope.py"),
                               run_name="learningos_keeper_seal")
    seal = cast(Callable[..., int], namespace["main"])
    return seal(argv, ingress=INGRESS_KEEPER)


def _run_capability(argv: list[str]) -> int:
    from learning_os.adapters.capability import cmd_capability
    from learning_os.adapters.cli_entry import run
    from learning_os.adapters.cli_parser import build_parser

    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:
        return int(exc.code or 2)
    if getattr(args, "func", None) is not cmd_capability:
        return _refuse("the Keeper submits through `capability` only")
    args.func = partial(cmd_capability, ingress=INGRESS_KEEPER)
    return int(run(args))


def main() -> int:
    """Verify the broker's handshake, then run one tool as the Keeper's ingress."""
    expected = os.environ.pop(HANDSHAKE_ENV, None)
    if not expected:
        return _refuse("only the study broker's Keeper profile starts this ingress "
                       "(`study_launch.py --profile keeper`)")
    request, problem = _read_request()
    if problem is not None:
        return _refuse(problem)
    assert request is not None
    token = request.get("token")
    if not isinstance(token, str) or not hmac.compare_digest(token_digest(token), expected):
        return _refuse("the handshake does not match this Keeper run")
    tool = request.get("tool")
    argv = request.get("argv")
    stdin_text = request.get("stdin")
    if not isinstance(tool, str) or tool not in TOOLS:
        return _refuse(f"unknown tool {tool!r}")
    if not isinstance(argv, list) or not all(isinstance(item, str) for item in argv):
        return _refuse("argv must be a list of strings")
    if stdin_text is not None and not isinstance(stdin_text, str):
        return _refuse("stdin must be text")
    previous = sys.stdin
    sys.stdin = io.StringIO(stdin_text or "")
    try:
        if tool == "seal":
            return _run_seal(argv)
        return _run_capability(argv)
    finally:
        sys.stdin = previous


if __name__ == "__main__":
    raise SystemExit(main())
