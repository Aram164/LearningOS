"""CLI parity and cli-operations inventory (PLAN D2).

S12 Task 2 stub: enforces ``system/contracts/cli-operations.yaml``.
Task 3 adds the parser parity checks (SPEC 10.7).
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CLI_OPS_PATH = ROOT / "system/contracts/cli-operations.yaml"


def test_cli_operations_lists_every_cli_primary():
    data = yaml.safe_load(CLI_OPS_PATH.read_text(encoding="utf-8"))
    assert data.get("schema") == 1
    operations = data.get("operations", {})
    # 41 cli.* primaries; kinds constrained by SPEC 10.8.
    assert len(operations) == 41, len(operations)
    for name, entry in sorted(operations.items()):
        assert name.startswith("cli."), name
        assert entry.get("cli_command") == name[len("cli."):], name
        assert entry.get("kind") in {"query", "command", "porcelain", "tool"}, name
