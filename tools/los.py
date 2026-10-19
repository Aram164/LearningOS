#!/usr/bin/env python3
"""Learning OS CLI — the stable machine gateway for interface layers (ADR-006).

Agents start here (system/OPERATOR.md):

    .venv/bin/python tools/los.py capabilities --compact --json  # what exists
    .venv/bin/python tools/los.py bootstrap --brief              # session entry, one page
    .venv/bin/python tools/los.py capabilities NAME --json       # one capability + payload schema
    .venv/bin/python tools/los.py inspect ID [ID ...]            # records, one fresh projection
    .venv/bin/python tools/los.py status                         # one-screen repository state

`bootstrap` without --brief/--compact prints the complete projection
(megabytes): a bulk read, never a session start.

Every canonical write is a capability applied as a GatewayEnvelopeV2 through
`capability NAME --payload-file ENVELOPE.json` (WORKFLOWS §25c). Run bare, a
named write command only preflights (`--check`) or refuses. `validate` and
`generate` delegate to tools/validate.py and tools/generate.py, so there is
exactly one implementation of every rule.

Interface layers (the Obsidian UI project, scripts, agents) call THESE
commands instead of parsing YAML or reimplementing rules. Exit codes: 0 ok ·
1 validation errors · 2 usage/environment error · 3 optimistic-concurrency
conflict.
"""

from __future__ import annotations

from learning_os.adapters.cli_entry import run  # noqa: E402
from learning_os.adapters.cli_parser import build_parser  # noqa: E402


def main() -> int:
    return run(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
