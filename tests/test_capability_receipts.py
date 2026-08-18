"""Every canonical write must report the receipt it produced.

``_write_transaction`` hands back ``(code, errors, confirmation)``, and the
confirmation carries ``transaction_id``, ``receipt_path`` and
``artifact_revisions``. ``cmd_capability`` reads those three fields out of the
handler's *own* JSON result, so a handler that binds the confirmation and never
spreads it answers ``transaction_id: null, receipt_path: null`` on a successful
write that did produce a receipt on disk. Fourteen of the twenty non-Job write
commands did exactly that until 2026-08-18. Nothing failed: the envelope schema
declares both fields nullable, and only ``project.create`` and the Job commands
asserted a non-null receipt. The audit trail existed and was unreachable from
the response that created it.

The structural assertion below is deliberately not an end-to-end sweep. Driving
all 27 capabilities would need 27 hand-built fixtures and would still only cover
the capabilities someone remembered to write a fixture for; the defect is one
missing spread per handler, and the parser finds it in every handler that
exists, including ones added after this file was written. One round trip through
the real gateway follows it, so the property is anchored to observed behaviour
and not only to syntax.
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
COMMANDS = REPO_ROOT / "tools" / "learning_os" / "commands"

# Helpers that commit a transaction and hand its receipt facts back to the
# caller. `_write_transaction` returns `(code, errors, confirmation)`; the Job
# surface's `_commit` returns the confirmation block on its own.
_PRODUCERS = {"_write_transaction": 2, "_commit": None}


def _callee(node: ast.AST) -> str | None:
    if not isinstance(node, ast.Call):
        return None
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _binding(assign: ast.Assign) -> str | None:
    """The name this assignment binds the confirmation block to, if any."""
    callee = _callee(assign.value)
    if callee not in _PRODUCERS:
        return None
    index = _PRODUCERS[callee]
    target = assign.targets[0]
    if index is None:
        return target.id if isinstance(target, ast.Name) else None
    if isinstance(target, ast.Tuple) and len(target.elts) > index:
        element = target.elts[index]
        return element.id if isinstance(element, ast.Name) else None
    return None


def _spread_names(function: ast.AST) -> set[str]:
    """Names unpacked with ``**`` anywhere inside this function."""
    names: set[str] = set()
    for node in ast.walk(function):
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if key is None and isinstance(value, ast.Name):
                    names.add(value.id)
        elif isinstance(node, ast.Call):
            for keyword in node.keywords:
                if keyword.arg is None and isinstance(keyword.value, ast.Name):
                    names.add(keyword.value.id)
    return names


def _committing_functions() -> list[tuple[str, str, str, int]]:
    """(module, function, bound name, line) for every transaction commit site."""
    found: list[tuple[str, str, str, int]] = []
    for path in sorted(COMMANDS.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for function in ast.walk(tree):
            if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for node in ast.walk(function):
                if not isinstance(node, ast.Assign):
                    continue
                name = _binding(node)
                if name is not None:
                    found.append((path.name, function.name, name, node.lineno))
    return found


COMMIT_SITES = _committing_functions()


def test_the_command_surface_actually_commits_transactions():
    """Guard the guard: a parser change that finds nothing must not read green."""
    modules = {module for module, _, _, _ in COMMIT_SITES}
    assert len(COMMIT_SITES) >= 20, COMMIT_SITES
    assert {"stage.py", "unit.py", "note.py", "detour.py", "review.py",
            "source.py", "module.py", "job_write.py"} <= modules


@pytest.mark.parametrize(
    ("module", "function", "bound", "line"),
    COMMIT_SITES,
    ids=[f"{m}::{f}:{n}" for m, f, _, n in COMMIT_SITES],
)
def test_every_committed_write_reports_its_receipt(
    module: str, function: str, bound: str, line: int
):
    tree = ast.parse((COMMANDS / module).read_text(encoding="utf-8"))
    target = next(
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == function
    )
    assert bound in _spread_names(target), (
        f"{module}:{line} {function}() commits a transaction and binds its "
        f"receipt to '{bound}' without ever spreading it into the JSON it "
        f"reports. The write produces a receipt on disk; the capability "
        f"envelope will answer transaction_id: null. Add **{bound} to the "
        f"reported dict."
    )


def test_a_write_capability_returns_its_receipt_through_the_envelope(
    mini_repo: Path, repo_root: Path, tmp_path: Path
):
    """The end-to-end half: one of the fourteen, through the real gateway."""
    envelope = {
        "request_id": "request-note-evidence",
        "capability": "note.evidence.add",
        "payload": {
            "note_id": "note-demo",
            "evidence_type": "derivation",
            "ref": "workspace://workspace-demo",
        },
    }
    request = tmp_path / "request.json"
    request.write_text(json.dumps(envelope), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(repo_root / "tools/los.py"), "--root", str(mini_repo),
         "capability", "note.evidence.add", "--payload-file", str(request)],
        cwd=repo_root, text=True, capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    response = json.loads(result.stdout)
    assert response["ok"] is True
    assert response["transaction_id"], "a successful write reported no transaction"
    assert response["receipt_path"].startswith("operations/transactions/")
    assert (mini_repo / response["receipt_path"]).is_file(), (
        "the response named a receipt that is not on disk"
    )
