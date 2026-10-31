"""The agent read catalog (PLAN D7): verbs that only read, with their params.

The catalog is the discovery surface for read-only agent work: every listed
verb runs as a read with no session, alone or as a stdin plan. An operation
admitted here is either registered ``read`` or carries a Core-declared
``read_when`` mode; anything else makes the build refuse, so the list can
never hide a writer. Params come from the effective request schemas.
"""
from __future__ import annotations

from pathlib import Path

from learning_os.app.registry import REGISTRY, OperationEffects
from learning_os.store.contracts.requests import request_schema

READ_VERBS = (
    "bootstrap", "resume", "inspect", "search", "unit-list", "module-list",
    "plan-edit-context", "material-context", "material-span", "study-sequence",
    "note-read", "related", "ability-context", "semantic", "intelligence-scan",
    "inbox-list", "inbox-read", "program-list", "project-list", "operations",
    "plan-template", "capabilities",
)

RULES = (
    "Everything listed here only reads and cannot change a record.",
    "One read: .venv/bin/los VERB ARGS. Several reads in one call: pass a plan "
    "on stdin to .venv/bin/python tools/agent_run.py - --root .",
    "Before any write, read system/OPERATOR.md. Writes go through tools/seal_envelope.py.",
)

_SKIPPED_PARAMS = ("json", "expected_snapshot")


def _param_rows(root: Path, operation: str) -> list[dict]:
    schema = request_schema(root, operation)
    required = set(schema.get("required", []))
    rows: list[dict] = []
    for name, spec in schema.get("properties", {}).items():
        if name in _SKIPPED_PARAMS:
            continue
        cli = spec.get("x-los-cli", {})
        if cli.get("transport_only"):
            continue
        row: dict = {"name": name}
        position = cli.get("position")
        if position is not None:
            row["position"] = position
        flags = cli.get("flags") or []
        if flags:
            row["flags"] = flags
        kind = spec.get("x-los-id-kind")
        if kind is not None:
            row["kind"] = kind
        if name in required:
            row["required"] = True
        rows.append(row)
    return rows


def build_catalog(root, verb_to_operation: dict) -> dict:
    """Build the read catalog for ``root``; refuse any listed verb that writes."""
    root = Path(root)
    reads: list[dict] = []
    for verb in READ_VERBS:
        operation = verb_to_operation.get(verb)
        entry = REGISTRY.get(operation)
        if entry is None or not (entry.effects == OperationEffects.READ
                                 or entry.read_when is not None):
            raise ValueError(
                f"read catalog refuses verb {verb!r} (operation {operation!r}): "
                "not a declared read")
        reads.append({"verb": verb, "operation": operation,
                      "params": _param_rows(root, operation), "slots": []})
    return {"contract": "agent-read-catalog-v1", "rules": list(RULES), "reads": reads}
