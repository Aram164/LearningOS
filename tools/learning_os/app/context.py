"""The operation context for the pipeline (PLAN D4)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from learning_os.domain.failures import StaleSnapshot, WriteRefused
from learning_os.domain.snapshot import Repo
from learning_os.store.contracts.gateway import (
    GatewayRequestContext,
    current_gateway_request,
    gateway_snapshot_is_verified,
)
from learning_os.store.fingerprint import canonical_fingerprint
from learning_os.store.loader import load_repo


@dataclass
class OpContext:
    root: Path
    operation: str
    channel: str                       # "cli" | "ui" | "operator" | "codex" | "system-task"
    invocation: str                    # "query" | "command" | "check" | "replay" | "porcelain"
    gateway: GatewayRequestContext | None
    session_id: str | None = None
    lock_timeout_s: float | None = None

    def repo(self) -> Repo:
        """The loaded repository, loaded once and cached on the context."""
        from learning_os.app.read_session import current_session

        session = current_session(self.root)
        if session is not None:
            return session.repository()
        try:
            return self._repo
        except AttributeError:
            self._repo = load_repo(self.root)
            return self._repo

    def snapshot_id(self) -> str:
        """The live snapshot token, walked once and cached on the context."""
        from learning_os.app.read_session import current_session

        session = current_session(self.root)
        if session is not None:
            return session.snapshot
        try:
            return self._snapshot
        except AttributeError:
            self._snapshot = "sha256:" + canonical_fingerprint(self.root)
            return self._snapshot

    def require_snapshot(self, expected: str | None) -> None:
        """Raise unless ``expected`` matches live state.

        The branches of ``commands/support.py:_expected_ok`` as typed
        refusals (SPEC §11.1, amendment (ac)): identical text, and exit 3
        on every false branch. The empty-token branch is not evidence of
        a mismatched live snapshot, so it raises ``WriteRefused`` with an
        explicit exit 3 instead of ``StaleSnapshot``.
        """
        if expected is None:
            return
        request = current_gateway_request()
        if request is not None:
            if request.expected_snapshot != expected:
                raise StaleSnapshot(
                    "handler snapshot does not match the approved gateway intent",
                    prefixed=True,
                )
            # cmd_capability marks this only while it holds the same operator
            # lock through the complete handler dispatch.
            if gateway_snapshot_is_verified(self.root, expected):
                return
        if not expected.strip():
            # An empty token is almost always a scripting slip, not a
            # deliberate unguarded write. Omitting the flag remains the way
            # to write unguarded.
            raise WriteRefused(
                "--expected-snapshot was empty; refusing to write without "
                "a concurrency token",
                prefixed=True,
                exit_code=3,
            )
        actual = self.snapshot_id()
        if actual == expected:
            return
        detail = json.dumps({"expected": expected, "actual": actual})
        if current_gateway_request() is None:
            # Both facts are true; the one that decides the outcome goes
            # first: direct CLI application cannot succeed on any snapshot.
            line = (
                "canonical writes must use GatewayEnvelopeV2; direct CLI "
                "application is disabled — reloading will not change this. "
                "The supplied snapshot is also out of date. Submit the write "
                "with `los capability NAME --payload-file ENVELOPE.json` "
                "(envelope: WORKFLOWS §25c)."
            )
            raise StaleSnapshot(
                f"{line}\n{detail}",
                prefixed=True,
            )
        line = (
            "projection conflict — authored files changed since the app "
            "loaded; reload before writing"
        )
        raise StaleSnapshot(
            f"{line}\n{detail}",
            prefixed=True,
        )
