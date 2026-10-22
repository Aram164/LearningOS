"""Loader and checks for ``system/contracts/cli-operations.yaml``.

The CLI surface had two declarations that answered the same question with
different words. ``system/contracts/capabilities.yaml`` named a ``cli_command``
for the capabilities it owns, and this file named a ``cli_command`` and a
``kind`` for the operations the catalogue does not own. Neither file said
which one a verb belonged to, and nothing compared the two ``kind`` values
where they overlapped: nine operations declared one kind here and ran under
another.

This module owns the reading of this file. It does not decide which kind is
right — the runtime registry does, and
``learning_os.app.verb_catalogue`` compares the two. What it guarantees is
that the file says what it means: one kind per operation, from the closed
set the runtime understands.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

#: The kinds the runtime lock path understands. ``query`` takes the shared
#: operator lock, ``tool`` takes none, and ``command`` and ``porcelain`` take
#: the exclusive lock.
OPERATION_KINDS = frozenset({"query", "command", "porcelain", "tool"})

CONTRACT_RELATIVE = "system/contracts/cli-operations.yaml"


class CliOperationsError(Exception):
    pass


@dataclass(frozen=True)
class CliOperation:
    name: str
    cli_command: str
    kind: str
    #: The capability this operation serves, when it serves one that the
    #: capability catalogue does not own by name. ``goal.decide`` runs the
    #: internal capability ``goal.decision.record``; without this the verb
    #: would have no capability at all.
    capability: str | None = None


def load_cli_operations(root: Path) -> dict[str, CliOperation]:
    path = root / CONTRACT_RELATIVE
    if not path.is_file():
        raise CliOperationsError(f"CLI operation contract not found: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise CliOperationsError(f"invalid CLI operation contract: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema") != 1:
        raise CliOperationsError(
            "CLI operation contract must declare schema 1")
    operations = data.get("operations")
    if not isinstance(operations, dict) or not operations:
        raise CliOperationsError(
            "CLI operation contract must declare a non-empty operations mapping")
    declared: dict[str, CliOperation] = {}
    for name, row in operations.items():
        if not isinstance(name, str) or not name.strip() or not isinstance(row, dict):
            raise CliOperationsError("invalid CLI operation declaration")
        command = row.get("cli_command")
        if not isinstance(command, str) or not command.strip():
            raise CliOperationsError(
                f"CLI operation {name} has no cli_command")
        kind = row.get("kind")
        if kind not in OPERATION_KINDS:
            raise CliOperationsError(
                f"CLI operation {name} declares kind {kind!r}; the runtime "
                f"understands {', '.join(sorted(OPERATION_KINDS))}")
        if command in (op.cli_command for op in declared.values()):
            raise CliOperationsError(
                f"CLI command {command!r} is declared twice")
        declared[name] = CliOperation(
            name=name,
            cli_command=command.strip(),
            kind=kind,
            capability=row.get("capability"),
        )
    return declared
