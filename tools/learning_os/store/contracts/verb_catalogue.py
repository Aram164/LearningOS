"""The merged verb catalogue: every CLI verb, once, with what it needs.

Three files used to answer "what does this command do, and how do I find it"
between them, and none of them said which question they answered. The
capability catalogue named the capabilities and, for most of them, the CLI
command that runs them. The CLI operation contract named the remaining
commands and, for those, a kind. The request schemas named all of the
commands and the operation behind each one. An operator who read the
declared entry point was told to read ``capabilities --compact --json`` and
then ``capabilities NAME --json``, and the second call rejected every name
the first contract used, because it wanted the dotted capability id while
every other document used the command.

This module joins the three into one row per verb: the command, the
operation behind it, the capability that serves it, the kind the runtime
gives it, and the tasks whose entry read starts there. It is derived, not
declared, so it cannot drift from the files it reads; the checks that the
declared kind matches the runtime registry live in the test suite, where
the registry is importable.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from learning_os.store.contracts.capability_catalog import (
    CapabilityCatalogError,
    load_capability_catalog,
)
from learning_os.store.contracts.cli_operations import (
    CliOperationsError,
    load_cli_operations,
)
from learning_os.store.contracts.task_scope import (
    TaskScopeError,
    entry_read_expansions,
    entry_read_verbs,
    load_task_scope,
)

REQUESTS_RELATIVE = "system/schema/requests"


class VerbCatalogueError(Exception):
    """The declared surfaces do not join into one catalogue."""

    def __init__(self, problems: list[str]):
        self.problems = list(problems)
        super().__init__("; ".join(self.problems))


@dataclass(frozen=True)
class VerbRow:
    verb: str
    operation: str
    capability: str | None
    kind: str
    surface: str
    writes: bool | None
    tasks: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "verb": self.verb,
            "operation": self.operation,
            "capability": self.capability,
            "kind": self.kind,
            "surface": self.surface,
            "writes": self.writes,
            "tasks": list(self.tasks),
        }


@dataclass(frozen=True)
class TaskRow:
    id: str
    task: str
    entry_read: str
    procedures: tuple[str, ...]
    procedure_text: str | None
    scope: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "task": self.task,
            "entry_read": self.entry_read,
            "procedures": list(self.procedures),
            "procedure_text": self.procedure_text,
            "scope": list(self.scope),
        }


@dataclass(frozen=True)
class VerbCatalogue:
    verbs: tuple[VerbRow, ...]
    tasks: tuple[TaskRow, ...]
    #: Findings that a synthetic repository may produce and the real one may
    #: not: a command it declares that the parser does not have. The real
    #: repository's CLI parity test refuses that; here it is a warning, so a
    #: fixture that registers a test-only capability is not a validation
    #: error.
    warnings: tuple[str, ...] = ()
    #: (name, task id) for every ``capabilities NAME`` an entry read expands:
    #: the task starts at NAME, so reading NAME is reading the task (#22).
    expansions: tuple[tuple[str, str], ...] = ()

    def entered_at(self, *names: str | None) -> list[TaskRow]:
        """The tasks whose entry read is ``capabilities NAME`` for one of ``names``."""
        ids = dict.fromkeys(task_id for name, task_id in self.expansions
                            if name in names)
        return [row for task_id in ids if (row := self.task(task_id)) is not None]

    def verb(self, name: str) -> VerbRow | None:
        for row in self.verbs:
            if row.verb == name:
                return row
        return None

    def capability(self, name: str) -> VerbRow | None:
        for row in self.verbs:
            if row.capability == name:
                return row
        return None

    def operation(self, name: str) -> VerbRow | None:
        for row in self.verbs:
            if row.operation == name:
                return row
        return None

    def task(self, name: str) -> TaskRow | None:
        for row in self.tasks:
            if row.id == name:
                return row
        return None


def _request_operations(root: Path) -> dict[str, str]:
    requests = root / REQUESTS_RELATIVE
    if not requests.is_dir():
        raise VerbCatalogueError([f"request-schema directory is missing: {REQUESTS_RELATIVE}"])
    operations: dict[str, str] = {}
    for path in sorted(requests.glob("*.schema.json")):
        operation = path.name[: -len(".schema.json")]
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise VerbCatalogueError([f"cannot read request schema {path.name}: {exc}"]) from exc
        binding = data.get("x-los-cli-command")
        if not isinstance(binding, dict) or not isinstance(binding.get("name"), str):
            continue
        verb = binding["name"]
        if verb in operations:
            raise VerbCatalogueError([f"CLI command {verb!r} is declared twice"])
        operations[verb] = operation
    if not operations:
        raise VerbCatalogueError(["no CLI command is declared by the request schemas"])
    return operations


def _catalog_capabilities(
    catalogue: Mapping[str, object],
) -> tuple[
    dict[str, dict[str, object]],
    dict[str, dict[str, object]],
    dict[str, dict[str, object]],
]:
    """Capability rows by id, split into public queries, public commands and internal."""
    def section(name: str) -> dict[str, dict[str, object]]:
        rows = catalogue.get(name)
        if not isinstance(rows, dict):
            return {}
        out: dict[str, dict[str, object]] = {}
        for key, value in rows.items():
            if isinstance(key, str) and isinstance(value, dict):
                out[key] = {str(k): v for k, v in value.items()}
        return out

    return section("queries"), section("commands"), section("internal_commands")


def build_verb_catalogue(root: Path) -> VerbCatalogue:
    root = Path(root)
    problems: list[str] = []
    try:
        catalogue = load_capability_catalog(root)
    except CapabilityCatalogError as exc:
        raise VerbCatalogueError([str(exc)]) from exc
    try:
        operations = load_cli_operations(root)
    except CliOperationsError as exc:
        raise VerbCatalogueError([str(exc)]) from exc
    try:
        tasks = load_task_scope(root)
    except TaskScopeError as exc:
        raise VerbCatalogueError([str(exc)]) from exc

    request_operations = _request_operations(root)
    parser_commands = set(request_operations)
    queries, commands, internal = _catalog_capabilities(catalogue)
    public = {**queries, **commands}
    warnings: list[str] = []

    # verb -> (capability id, declared kind) from the capability catalogue.
    catalog_verbs: dict[str, tuple[str, str]] = {}
    for name, row in {**public, **internal}.items():
        command = row.get("cli_command")
        if not isinstance(command, str) or not command:
            continue
        kind = row.get("kind")
        if not isinstance(kind, str) or not kind:
            if command in parser_commands:
                problems.append(
                    f"capability {name} declares the CLI command {command!r} "
                    f"but no kind")
            else:
                warnings.append(
                    f"capability {name} declares the CLI command {command!r}, "
                    f"which the parser does not have, and no kind for it")
            continue
        if command in catalog_verbs:
            problems.append(
                f"CLI command {command!r} is declared by both "
                f"{catalog_verbs[command][0]} and {name}")
            continue
        catalog_verbs[command] = (name, kind)

    # verb -> (operation id, declared kind) from the CLI operation contract.
    operation_verbs: dict[str, tuple[str, str]] = {}
    for operation in operations.values():
        command = operation.cli_command
        if command in operation_verbs:
            problems.append(
                f"CLI command {command!r} is declared twice by the operation contract")
            continue
        operation_verbs[command] = (operation.name, operation.kind)

    for command in set(catalog_verbs) & set(operation_verbs):
        problems.append(
            f"CLI command {command!r} is declared by both the capability "
            f"catalogue and the operation contract")

    declared = {**catalog_verbs, **operation_verbs}
    missing = sorted(set(request_operations) - set(declared))
    extra = sorted(set(declared) - set(request_operations))
    if missing:
        problems.append(
            "no contract declares the CLI command(s): " + ", ".join(missing))
    if extra:
        warnings.append(
            "a contract declares the CLI command(s) the parser does not have: "
            + ", ".join(extra))

    # Which task starts where: at the verb its entry read runs, and at the
    # name a `capabilities NAME` entry read expands.
    task_verbs: dict[str, list[str]] = {}
    expansions: list[tuple[str, str]] = []
    known = {*public, *internal, *request_operations, *tasks}
    for task in tasks.values():
        for verb in entry_read_verbs(task.entry_read):
            task_verbs.setdefault(verb, []).append(task.id)
        for name in entry_read_expansions(task.entry_read):
            if name not in known:
                problems.append(
                    f"task scope {task.id} expands {name!r}, which is no "
                    f"capability, CLI command or task")
                continue
            expansions.append((name, task.id))
    expanded: dict[str, set[str]] = {}
    for name, task_id in expansions:
        expanded.setdefault(name, set()).add(task_id)

    rows: list[VerbRow] = []
    for verb in sorted(request_operations):
        operation_id = request_operations[verb]
        capability: str | None
        surface: str
        writes: bool | None
        if verb in catalog_verbs:
            capability, kind = catalog_verbs[verb]
            surface = "internal" if capability in internal else "catalog"
            writes = True if capability in commands or capability in internal else False
        elif verb in operation_verbs:
            operation_name, kind = operation_verbs[verb]
            capability = operations[operation_name].capability
            if capability is None and operation_name in public:
                capability = operation_name
            surface = "catalog" if capability in public else (
                "internal" if capability in internal else "cli-only")
            writes = True if capability in commands or capability in internal else (
                False if capability in public else None)
        else:
            continue
        rows.append(VerbRow(
            verb=verb,
            operation=operation_id,
            capability=capability,
            kind=kind,
            surface=surface,
            writes=writes,
            tasks=tuple(sorted(
                set(task_verbs.get(verb, [])) | expanded.get(verb, set())
                | (expanded.get(capability, set()) if capability else set()))),
        ))

    task_rows = tuple(
        TaskRow(
            id=task.id,
            task=task.task,
            entry_read=task.entry_read,
            procedures=tuple(link.target for link in task.procedures),
            procedure_text=task.procedure_text,
            scope=task.scope,
        )
        for task in tasks.values()
    )

    if problems:
        raise VerbCatalogueError(problems)
    return VerbCatalogue(verbs=tuple(rows), tasks=task_rows,
                          warnings=tuple(warnings), expansions=tuple(expansions))
