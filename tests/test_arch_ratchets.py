"""Ratchet monotonicity against the base (SPEC §2.3) and file validity (§2.4).

Compares the worktree's ``ratchets.yaml``, ``pyproject.toml``
``ignore_imports`` and live A11 surface against ``git show
$LOS_RATCHET_BASE:<file>`` (default base: ``main``). A file absent at the
base is the baseline: every ``ratchets.yaml`` entry must then be
``since: baseline``, and a first-ever ``surface.json`` needs no approvals.
``baselined`` lists the checks whose baseline is recorded; it only grows,
and every check id with entries is listed (amended §2.3 rule 2).
Surface approvals are single-use: an entry covers a diff only when that
whole entry is absent from the base's ``surface-approvals.yaml`` (§2.3
step 4).
"""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import arch_surface
import pytest
import yaml
from arch_schema_deltas import (
    _before_approved_c1_schema,
    _restore_phase6_descriptions,
    _strip_approved_owner_metadata,
    _strip_bf_description_updates,
)
from test_arch_request_schemas import BU4_FILTER_NOT_LOOKUP

ROOT = Path(__file__).resolve().parent.parent
ARCH = ROOT / arch_surface.ARCHITECTURE_DIR
RATCHETS_PATH = ARCH / arch_surface.RATCHETS_FILENAME
APPROVALS_PATH = ARCH / arch_surface.APPROVALS_FILENAME
PYPROJECT_PATH = ROOT / "pyproject.toml"
MOVES_PATH = ROOT / "tests" / "architecture" / "moves.yaml"

BASE_ENV = "LOS_RATCHET_BASE"
DEFAULT_BASE = "main"

APPROVED_BY_RE = re.compile(r"^Aram \d{4}-\d{2}-\d{2}: .+$")
CHECK_ID_RE = re.compile(r"^A(1[0-9]|[1-9])(-[a-z0-9-]+)?$")

#: Fix sentences from the SPEC §3 table, printed on every failure.
FIX = {
    "A1": "Move the import below the importer's layer, or split the module (PLAN D17).",
    "A2": "Return a TransactionProposal; only TransactionService writes canonical files (PLAN D4).",
    "A3": "Raise a typed failure; classify by type, never by message text (PLAN D3).",
    "A4": "Handlers get the snapshot and lock from the pipeline (PLAN D20).",
    "A5": "Raise NotFound(kind, value, candidates) (PLAN D3).",
    "A6": "Print canonical ids via domain.ids (PLAN D6).",
    "A7": "Render through adapters.cli (PLAN D16).",
    "A8": "Update the transcript, or fix the doc command (PLAN D11).",
    "A9": "Add a scenario that triggers this site and asserts its effects.",
    "A10": "Key the cache on the missing input (PLAN D9).",
    "A11": "Surface changes need an approval line (PLAN A11).",
    "A12": "Behaviour changed; restore it or record a reviewed mismatch.",
    "A13": "Complete the request schema (PLAN D2).",
    "A14": "Import the code from learning_os.domain.codes.",
    "A15": "see SPEC §3 (no fix sentence for this check)",
    "A16": "see SPEC §3 (no fix sentence for this check)",
    "A17": "OpContext members are frozen; a new member needs an approval line (PLAN A17).",
    "A18": "Express the step as a declared gate or a pure renderer; callbacks must not grow or touch the world (PLAN A18).",
    "A19": "Write durable operational state only through its declared owner, and declare an owner for new state (PLAN A19).",
}


def _find_line(text: str, needle: str) -> int:
    for lineno, line in enumerate(text.splitlines(), 1):
        if needle in line:
            return lineno
    return 1


def _git_show(base: str, relpath: str) -> str | None:
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{base}:{relpath}"],
        capture_output=True, text=True)
    if proc.returncode != 0:
        return None
    return proc.stdout


def _load_ratchets(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _ignore_lists(pyproject_text: str) -> dict[str, list[str]]:
    """Contract name -> ignore_imports lines (SPEC §1.2 configuration)."""
    data = tomllib.loads(pyproject_text)
    contracts = (
        data.get("tool", {}).get("importlinter", {}).get("contracts", []) or [])
    lists: dict[str, list[str]] = {}
    for index, contract in enumerate(contracts):
        name = contract.get("name", f"contract[{index}]")
        lists[name] = list(contract.get("ignore_imports", []) or [])
    return lists


#: SPEC §1.2 contracts pinned as a literal table (SPEC §2.3 rule 3).
#: Every field other than ``ignore_imports`` must equal these values.
EXPECTED_CONTRACTS: dict[str, dict] = {
    "A1 layers (PLAN D17)": {
        "type": "layers",
        "containers": ["learning_os"],
        "exhaustive": True,
        "unmatched_ignore_imports_alerting": "error",
        "layers": [
            "adapters",
            "app",
            "derive",
            "store",
            "domain",
        ],
    },
    "A1 transaction writer access (PLAN A2, D4)": {
        "type": "forbidden",
        "source_modules": [
            "learning_os.derive.validation",
            "learning_os.derive.projection",
            "learning_os.derive.semantics",
            "learning_os.derive.search",
            "learning_os.derive.health",
            "learning_os.derive.abilities",
            "learning_os.derive.learning_runtime",
            "learning_os.derive.routes",
            "learning_os.domain",
        ],
        "forbidden_modules": ["learning_os.store.transactions"],
    },
    "A1 transaction service protected (PLAN A1, D14)": {
        "type": "protected",
        "protected_modules": ["learning_os.store.transactions"],
        "allowed_importers": ["learning_os.app"],
        "unmatched_ignore_imports_alerting": "error",
    },
}


def _parse_contracts(pyproject_text: str) -> dict[str, dict]:
    """Contract name -> full contract mapping from TOML text."""
    data = tomllib.loads(pyproject_text)
    contracts = (
        data.get("tool", {}).get("importlinter", {}).get("contracts", []) or [])
    parsed: dict[str, dict] = {}
    for index, contract in enumerate(contracts):
        name = contract.get("name", f"contract[{index}]")
        parsed[name] = dict(contract)
    return parsed


def _contract_set_failures(
        base_text: str | None, current_text: str) -> list[str]:
    """SPEC §2.3 rule 3 (contract set and structure) as a pure check.

    Takes TOML text so fixture tests need no git. One message per
    violation: a deleted contract, a renamed or otherwise unknown
    contract, a missing §1.2 contract, or a field that differs from
    the §1.2 literal (``ignore_imports`` excluded).
    """
    base = _parse_contracts(base_text) if base_text is not None else {}
    current = _parse_contracts(current_text)
    expected_names = set(EXPECTED_CONTRACTS)
    failures: list[str] = []
    for name in sorted(set(base) - set(current)):
        failures.append(f"contract {name!r} present at the base is missing")
    for name in sorted(set(current) - expected_names):
        failures.append(f"contract {name!r} is not a SPEC §1.2 contract")
    for name in sorted(expected_names - set(current)):
        failures.append(f"SPEC §1.2 contract {name!r} is missing")
    for name in sorted(set(current) & expected_names):
        actual = {k: v for k, v in current[name].items()
                  if k not in ("name", "ignore_imports")}
        expected = EXPECTED_CONTRACTS[name]
        if actual != expected:
            failures.append(
                f"contract {name!r} differs from SPEC §1.2: "
                f"expected {expected!r}, found {actual!r}")
    return failures


@pytest.fixture(scope="module")
def base_ref() -> str:
    base = os.environ.get(BASE_ENV, DEFAULT_BASE)
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--verify", "--quiet",
         f"{base}^{{commit}}"],
        capture_output=True, text=True)
    if proc.returncode != 0:
        reason = (f"ratchet base {base!r} does not resolve; "
                  f"set {BASE_ENV} to compare")
        print(reason)
        if os.environ.get("CI"):
            pytest.fail(f"CI requires a resolvable ratchet base: {reason}")
        pytest.skip(reason)
    assert proc.returncode == 0
    return base


# ---- file validity (needs no base) ------------------------------------------


def test_ratchets_file_is_valid():
    assert RATCHETS_PATH.is_file(), f"missing {RATCHETS_PATH.relative_to(ROOT)}"
    data = _load_ratchets(RATCHETS_PATH)
    assert data.get("schema") == 1, "ratchets.yaml: schema must be 1"
    baselined = data.get("baselined", [])
    assert isinstance(baselined, list), "ratchets.yaml: baselined must list check ids"
    for check_id in baselined:
        assert isinstance(check_id, str) and CHECK_ID_RE.match(check_id), (
            f"ratchets.yaml: unknown baselined id {check_id!r}")
    assert isinstance(data.get("checks"), dict), "ratchets.yaml: checks must map"
    for check_id, entries in data["checks"].items():
        assert CHECK_ID_RE.match(check_id), f"ratchets.yaml: unknown check id {check_id!r}"
        assert isinstance(entries, list), f"ratchets.yaml: {check_id} must list entries"
        for entry in entries:
            assert isinstance(entry.get("signature"), str), (
                f"ratchets.yaml: {check_id} entry needs a string signature")
            assert (isinstance(entry.get("count"), int)
                    and entry["count"] >= 1), (
                f"ratchets.yaml: {check_id} entry needs a count >= 1")
            since = entry.get("since")
            assert since in ("baseline", "approved"), (
                f"ratchets.yaml: {check_id} entry since must be baseline | approved")
            approved_by = entry.get("approved_by")
            if since == "approved":
                assert (isinstance(approved_by, str)
                        and APPROVED_BY_RE.match(approved_by)), (
                    f"ratchets.yaml: {check_id} approved entry needs an "
                    f"approved_by matching ^Aram YYYY-MM-DD: ...")
            else:
                assert approved_by is None, (
                    f"ratchets.yaml: {check_id} baseline entry must not carry approved_by")


def test_surface_approvals_file_is_valid():
    assert APPROVALS_PATH.is_file(), f"missing {APPROVALS_PATH.relative_to(ROOT)}"
    data = yaml.safe_load(APPROVALS_PATH.read_text(encoding="utf-8"))
    assert data.get("schema") == 1, "surface-approvals.yaml: schema must be 1"
    assert isinstance(data.get("approvals"), list), (
        "surface-approvals.yaml: approvals must list entries")
    for entry in data["approvals"]:
        for field in ("key", "change", "plan_ref", "pre_approved_by"):
            assert isinstance(entry.get(field), str), (
                f"surface-approvals.yaml: entry needs a string {field}")
        assert entry["change"] in ("added", "removed", "changed"), (
            "surface-approvals.yaml: change must be added | removed | changed")


# ---- monotonicity against the base (SPEC §2.3) -------------------------------


def _move_map():
    spec = importlib.util.spec_from_file_location(
        "move_map", ROOT / "tools" / "move_map.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _range_moves(base_ref: str) -> list[dict]:
    """Moves recorded now but not at the base: those made since the base (OD9)."""
    def entries(text):
        data = yaml.safe_load(text) if text else None
        return list((data or {}).get("moves") or [])
    current = entries(MOVES_PATH.read_text(encoding="utf-8")
                      if MOVES_PATH.is_file() else None)
    base = entries(_git_show(base_ref, MOVES_PATH.relative_to(ROOT).as_posix()))
    seen = {(m["from"], m["to"]) for m in base}
    return [m for m in current if (m["from"], m["to"]) not in seen]


def _translate_one(signature: str, move: dict) -> str:
    """One recorded move applied to a base signature or ignore line.

    A ledger entry is a file or package move (``tools/…/x.py``, ``tools/…/pkg/``)
    or a definition move (``<file>::<name>`` to ``<file>::<name>``).
    """
    path, sep, rest = signature.partition("::")
    if "::" in move["from"]:
        prefix = move["from"] + "::"
        if signature.startswith(prefix):
            return move["to"] + "::" + signature[len(prefix):]
        return signature
    translate = _move_map().translate
    if sep and path == move["from"] and "/" not in path:
        return move["to"] + sep + rest
    if sep and "/" in path:
        return translate([move], path) + sep + rest
    left, arrow, right = signature.partition(" -> ")
    if arrow:
        return translate([move], left.strip()) + arrow + translate([move], right.strip())
    return signature


def _translated(signature: str, moves: list[dict]) -> str:
    """A base signature or ignore line under the moves made since the base, in order."""
    for move in moves:
        signature = _translate_one(signature, move)
    return signature


def _ratchet_failures(base_data: dict | None,
                      current_data: dict) -> list[tuple[str, str, str]]:
    """SPEC §2.3 rule 2 as a pure check: ``(rule, subject, detail)`` per violation.

    ``base_data`` is the parsed base ``ratchets.yaml``, or None when the file
    is absent at the base. A missing ``baselined`` key counts as an empty
    list, both at the base and now.
    """
    failures: list[tuple[str, str, str]] = []
    base = base_data or {}
    base_lined: list = base.get("baselined") or []
    current_lined: list = current_data.get("baselined") or []
    base_checks: dict = base.get("checks") or {}
    current_checks: dict = current_data.get("checks") or {}
    for check_id in base_lined:
        if check_id not in current_lined:
            failures.append((check_id.split("-")[0], check_id,
                             "removed from baselined"))
    for check_id, entries in current_checks.items():
        if entries and check_id not in current_lined:
            failures.append((check_id.split("-")[0], check_id,
                             "has entries but is not in baselined"))
    for check_id, entries in current_checks.items():
        rule = check_id.split("-")[0]
        if check_id in base_lined:
            base_counts = {entry["signature"]: entry["count"]
                           for entry in base_checks.get(check_id, []) or []}
            for entry in entries or []:
                signature, count = entry["signature"], entry["count"]
                if base_counts.get(signature, 0) >= count:
                    continue
                if not (entry.get("since") == "approved"
                        and isinstance(entry.get("approved_by"), str)
                        and APPROVED_BY_RE.match(entry["approved_by"])):
                    failures.append((rule, signature,
                                     "new or higher exception count "
                                     f"(base {base_counts.get(signature, 0)}, "
                                     f"now {count}) without an approval"))
        else:
            for entry in entries or []:
                if not (entry.get("since") == "baseline"
                        and entry.get("approved_by") is None):
                    failures.append((rule, entry["signature"],
                                     "check new at the base must record "
                                     "since: baseline"))
    return failures


def test_ratchets_are_monotonic_vs_base(base_ref):
    current = _load_ratchets(RATCHETS_PATH)
    base_text = _git_show(base_ref, RATCHETS_PATH.relative_to(ROOT).as_posix())
    base = yaml.safe_load(base_text) if base_text is not None else None
    moves = _range_moves(base_ref)
    if base and moves:
        for entries in (base.get("checks") or {}).values():
            for entry in entries or []:
                entry["signature"] = _translated(entry["signature"], moves)
    current_text = RATCHETS_PATH.read_text(encoding="utf-8")
    rel = RATCHETS_PATH.relative_to(ROOT).as_posix()
    failures = []
    for rule, subject, detail in _ratchet_failures(base, current):
        lineno = _find_line(current_text, subject)
        failures.append(
            f"{rule} {subject}: {detail} — {rel}:{lineno} — {FIX[rule]}")
    assert not failures, "\n".join(failures)


# ---- rule 2 against fixture YAML (no git) -----------------------------------

_FIXTURE_BASE_EMPTY = """
schema: 1
baselined: []
checks: {}
"""

_FIXTURE_BASE_A3 = """
schema: 1
baselined: [A3-prose]
checks:
  A3-prose:
    - signature: "tools/learning_os/commands/x.py::cmd_y::substring::snap"
      count: 1
      since: baseline
      approved_by: null
"""

_FIXTURE_CURRENT_A3_BASELINE = """
schema: 1
baselined: [A3-prose]
checks:
  A3-prose:
    - signature: "tools/learning_os/commands/x.py::cmd_y::substring::snap"
      count: 1
      since: baseline
      approved_by: null
"""


def test_introduced_check_with_baselined_entry_passes():
    base = yaml.safe_load(_FIXTURE_BASE_EMPTY)
    current = yaml.safe_load(_FIXTURE_CURRENT_A3_BASELINE)
    assert _ratchet_failures(base, current) == []


def test_introduced_check_without_baselined_entry_fails():
    base = yaml.safe_load(_FIXTURE_BASE_EMPTY)
    current = yaml.safe_load(_FIXTURE_CURRENT_A3_BASELINE)
    current["baselined"] = []
    failures = _ratchet_failures(base, current)
    assert len(failures) == 1
    assert failures[0][1] == "A3-prose"
    assert "baselined" in failures[0][2]


def test_raised_count_for_established_check_fails():
    base = yaml.safe_load(_FIXTURE_BASE_A3)
    current = yaml.safe_load(_FIXTURE_BASE_A3)
    current["checks"]["A3-prose"][0]["count"] = 2
    failures = _ratchet_failures(base, current)
    assert len(failures) == 1
    assert "without an approval" in failures[0][2]


def test_approved_raise_for_established_check_passes():
    base = yaml.safe_load(_FIXTURE_BASE_A3)
    current = yaml.safe_load(_FIXTURE_BASE_A3)
    current["checks"]["A3-prose"][0]["count"] = 2
    current["checks"]["A3-prose"][0]["since"] = "approved"
    current["checks"]["A3-prose"][0]["approved_by"] = "Aram 2026-10-04: fixture approval"
    assert _ratchet_failures(base, current) == []


def test_removing_id_from_baselined_fails():
    base = yaml.safe_load(_FIXTURE_BASE_A3)
    current = yaml.safe_load(_FIXTURE_BASE_A3)
    current["baselined"] = []
    current["checks"] = {}
    failures = _ratchet_failures(base, current)
    assert len(failures) == 1
    assert failures[0][1] == "A3-prose"
    assert "removed from baselined" in failures[0][2]


def test_fix_sentences_cover_a17_through_a19():
    assert FIX["A17"] == ("OpContext members are frozen; a new member needs "
                          "an approval line (PLAN A17).")
    assert FIX["A18"] == ("Express the step as a declared gate or a pure renderer; "
                          "callbacks must not grow or touch the world (PLAN A18).")
    assert FIX["A19"] == ("Write durable operational state only through its declared owner, "
                          "and declare an owner for new state (PLAN A19).")


def test_moved_entry_is_not_new_after_translation():
    base = {"baselined": ["A3"], "checks": {"A3": [
        {"signature": "tools/learning_os/old.py::f::substring::x",
         "count": 1, "since": "baseline", "approved_by": None}]}}  # type: ignore[dict-item]
    current = {"baselined": ["A3"], "checks": {"A3": [
        {"signature": "tools/learning_os/bar/old.py::f::substring::x",
         "count": 1, "since": "baseline", "approved_by": None}]}}  # type: ignore[dict-item]
    moves = [{"from": "tools/learning_os/old.py",
              "to": "tools/learning_os/bar/old.py"}]
    for entries in (base.get("checks") or {}).values():
        for entry in entries or []:
            entry["signature"] = _translated(entry["signature"], moves)
    assert _ratchet_failures(base, current) == []


def test_new_entry_still_fails_after_translation():
    base = {"baselined": ["A3"], "checks": {"A3": [
        {"signature": "tools/learning_os/old.py::f::substring::x",
         "count": 1, "since": "baseline", "approved_by": None}]}}  # type: ignore[dict-item]
    current = {"baselined": ["A3"], "checks": {"A3": [
        {"signature": "tools/learning_os/bar/old.py::f::substring::x",
         "count": 2, "since": "baseline", "approved_by": None}]}}  # type: ignore[dict-item]
    moves = [{"from": "tools/learning_os/old.py",
              "to": "tools/learning_os/bar/old.py"}]
    for entries in (base.get("checks") or {}).values():
        for entry in entries or []:
            entry["signature"] = _translated(entry["signature"], moves)
    assert len(_ratchet_failures(base, current)) == 1


def _ignore_imports_failures(base_lists: dict[str, list[str]],
                             current_lists: dict[str, list[str]],
                             approved: set[str]) -> list[str]:
    """SPEC §2.3 rule 3 as a pure check: the added line per violation.

    A contract absent from the base is being introduced: its list is its own
    baseline. An established contract's list must stay a subset of the base
    list, apart from approved additions.
    """
    failures: list[str] = []
    for name, lines in sorted(current_lists.items()):
        if name not in base_lists:
            continue
        for line in sorted(set(lines) - set(base_lists.get(name, []))):
            if line in approved:
                continue
            failures.append(line)
    return failures


def test_ignore_imports_are_a_subset_of_base(base_ref):
    current_lists = _ignore_lists(PYPROJECT_PATH.read_text(encoding="utf-8"))
    base_text = _git_show(base_ref, "pyproject.toml")
    base_lists = _ignore_lists(base_text) if base_text is not None else {}
    moves = _range_moves(base_ref)
    base_lists = {name: [_translated(line, moves) for line in lines]
                  for name, lines in base_lists.items()}
    approved = {e["signature"] for e in
                _load_ratchets(RATCHETS_PATH)["checks"].get("A1-layers-approved", [])
                if e["since"] == "approved"}
    current_text = PYPROJECT_PATH.read_text(encoding="utf-8")
    failures = []
    for line in _ignore_imports_failures(base_lists, current_lists, approved):
        lineno = _find_line(current_text, line)
        failures.append(
            f"A1 {line}: ignore_imports addition without an "
            f"A1-layers-approved entry — pyproject.toml:{lineno} — {FIX['A1']}")
    assert not failures, "\n".join(failures)


def test_new_contract_is_its_own_baseline():
    base_lists: dict[str, list[str]] = {}
    current_lists = {"A1 layers (PLAN D17)": ["learning_os.a -> learning_os.b"]}
    assert _ignore_imports_failures(base_lists, current_lists, set()) == []


def test_established_contract_addition_needs_approval():
    base_lists = {"A1 layers (PLAN D17)": ["learning_os.a -> learning_os.b"]}
    current_lists = {"A1 layers (PLAN D17)": ["learning_os.a -> learning_os.b",
                                              "learning_os.c -> learning_os.d"]}
    assert _ignore_imports_failures(base_lists, current_lists, set()) == [
        "learning_os.c -> learning_os.d"]
    assert _ignore_imports_failures(
        base_lists, current_lists, {"learning_os.c -> learning_os.d"}) == []


def test_contract_set_and_structure_match_spec(base_ref):
    current_text = PYPROJECT_PATH.read_text(encoding="utf-8")
    base_text = _git_show(base_ref, "pyproject.toml")
    failures = []
    for detail in _contract_set_failures(base_text, current_text):
        lineno = _find_line(current_text, "tool.importlinter")
        failures.append(f"A1 {detail} — pyproject.toml:{lineno} — {FIX['A1']}")
    assert not failures, "\n".join(failures)


# ---- rule 3 contract set against fixture TOML (no git) -----------------------

_TOML_THREE_CONTRACTS = """
[tool.importlinter]
root_package = "learning_os"

[[tool.importlinter.contracts]]
name = "A1 layers (PLAN D17)"
type = "layers"
containers = ["learning_os"]
exhaustive = true
unmatched_ignore_imports_alerting = "error"
layers = [
  "adapters",
  "app",
  "derive",
  "store",
  "domain",
]
ignore_imports = []

[[tool.importlinter.contracts]]
name = "A1 transaction writer access (PLAN A2, D4)"
type = "forbidden"
source_modules = ["learning_os.derive.validation", "learning_os.derive.projection", "learning_os.derive.semantics", "learning_os.derive.search", "learning_os.derive.health", "learning_os.derive.abilities", "learning_os.derive.learning_runtime", "learning_os.derive.routes", "learning_os.domain"]
forbidden_modules = ["learning_os.store.transactions"]
ignore_imports = []

[[tool.importlinter.contracts]]
name = "A1 transaction service protected (PLAN A1, D14)"
type = "protected"
protected_modules = ["learning_os.store.transactions"]
allowed_importers = ["learning_os.app"]
unmatched_ignore_imports_alerting = "error"
ignore_imports = []
"""

_TOML_TWO_CONTRACTS = """
[tool.importlinter]
root_package = "learning_os"

[[tool.importlinter.contracts]]
name = "A1 layers (PLAN D17)"
type = "layers"
containers = ["learning_os"]
exhaustive = true
unmatched_ignore_imports_alerting = "error"
layers = [
  "adapters",
  "app",
  "derive",
  "store",
  "domain",
]
ignore_imports = []

[[tool.importlinter.contracts]]
name = "A1 transaction writer access (PLAN A2, D4)"
type = "forbidden"
source_modules = ["learning_os.derive.validation", "learning_os.derive.projection", "learning_os.derive.semantics", "learning_os.derive.search", "learning_os.derive.health", "learning_os.derive.abilities", "learning_os.derive.learning_runtime", "learning_os.derive.routes", "learning_os.domain"]
forbidden_modules = ["learning_os.store.transactions"]
ignore_imports = []
"""


def test_contract_deletion_fails():
    failures = _contract_set_failures(
        _TOML_THREE_CONTRACTS, _TOML_TWO_CONTRACTS)
    assert failures, "deleting a contract must fail"
    assert any("A1 transaction service protected" in f for f in failures)


def test_contract_rename_with_ignores_under_new_name_fails():
    renamed = _TOML_THREE_CONTRACTS.replace(
        'name = "A1 layers (PLAN D17)"',
        'name = "A1 layers renamed"', 1)
    renamed = renamed.replace(
        "ignore_imports = []",
        'ignore_imports = ["learning_os.a -> learning_os.b"]', 1)
    failures = _contract_set_failures(_TOML_THREE_CONTRACTS, renamed)
    assert failures, "renaming a contract must fail"
    assert any("not a SPEC" in f for f in failures)


def test_contract_weakened_exhaustive_fails():
    weakened = _TOML_THREE_CONTRACTS.replace(
        "exhaustive = true", "exhaustive = false", 1)
    failures = _contract_set_failures(_TOML_THREE_CONTRACTS, weakened)
    assert failures, "exhaustive = false must fail"
    assert any("differs from SPEC" in f for f in failures)


def test_contract_weakened_layer_removed_fails():
    weakened = _TOML_THREE_CONTRACTS.replace(
        '\n  "domain",',
        "", 1)
    failures = _contract_set_failures(_TOML_THREE_CONTRACTS, weakened)
    assert failures, "a removed layer must fail"
    assert any("differs from SPEC" in f for f in failures)


def test_contract_weakened_allowed_importers_fails():
    weakened = _TOML_THREE_CONTRACTS.replace(
        'allowed_importers = ["learning_os.app"]',
        'allowed_importers = ["learning_os.app", "learning_os.commands"]', 1)
    failures = _contract_set_failures(_TOML_THREE_CONTRACTS, weakened)
    assert failures, "widened allowed_importers must fail"
    assert any("differs from SPEC" in f for f in failures)


def test_introducing_protected_contract_passes():
    assert _contract_set_failures(
        _TOML_TWO_CONTRACTS, _TOML_THREE_CONTRACTS) == []


def _unapproved_surface_diffs(base_flat: dict[str, object],
                              current_flat: dict[str, object],
                              base_approvals: list[dict],
                              current_approvals: list[dict]) -> dict[str, str]:
    """SPEC §2.3 step 4 as a pure check: each uncovered diff keyed to its change.

    An approval covers a diff only when that whole entry is absent from the
    base approvals (single-use). Takes flattened surfaces so fixture tests
    need no git.
    """
    usable = [entry for entry in current_approvals
              if entry not in (base_approvals or [])]
    return {
        key: change
        for key, change in arch_surface.diff_keys(
            base_flat, current_flat).items()
        if not any(arch_surface.approval_covers(entry, key, change)
                   for entry in usable)
    }


def _surface_rule(key: str) -> str:
    """The check id owning a surface key: A17 freezes opcontext members."""
    return "A17" if key.startswith("opcontext.") else "A11"


def test_surface_diffs_have_approvals(base_ref):
    base_text = _git_show(
        base_ref,
        (ARCH / arch_surface.SURFACE_FILENAME).relative_to(ROOT).as_posix())
    if base_text is None:
        return
    base_flat = arch_surface.flatten_surface(json.loads(base_text))
    live = arch_surface.build_surface(ROOT)
    live_flat = arch_surface.flatten_surface(live)
    base_approvals_text = _git_show(
        base_ref, APPROVALS_PATH.relative_to(ROOT).as_posix())
    base_approvals = (
        yaml.safe_load(base_approvals_text)["approvals"]
        if base_approvals_text is not None else [])
    approvals = yaml.safe_load(APPROVALS_PATH.read_text(encoding="utf-8"))["approvals"]
    uncovered = _unapproved_surface_diffs(
        base_flat, live_flat, base_approvals, approvals)
    if not uncovered:
        return
    live_text = arch_surface.dump_surface(live)
    failures = []
    for key in sorted(uncovered):
        text = base_text if uncovered[key] == "removed" else live_text
        lineno = arch_surface.locate_line(text, key)
        rel = (ARCH / arch_surface.SURFACE_FILENAME).relative_to(ROOT).as_posix()
        rule = _surface_rule(key)
        failures.append(f"{rule} {key}: {uncovered[key]} — {rel}:{lineno} — {FIX[rule]}")
    assert not failures, "unapproved surface diffs:\n" + "\n".join(failures)


def test_opcontext_surface_keys_use_the_a17_sentence():
    assert _surface_rule("opcontext.root") == "A17"
    assert _surface_rule("opcontext.require_snapshot") == "A17"
    assert _surface_rule("project.inspect") == "A11"
    assert _surface_rule("tools.seal_envelope.py") == "A11"


# ---- step 4 single-use against fixture surfaces (no git) ----------------------

def _approval(key: str, change: str) -> dict:
    return {"key": key, "change": change, "plan_ref": "PLAN A11",
            "pre_approved_by": "Aram 2026-10-04: fixture approval"}


def test_new_approval_covers_its_key():
    uncovered = _unapproved_surface_diffs(
        {"cli.a": [1]}, {"cli.a": [2]}, [],
        [_approval("cli.a", "changed")])
    assert uncovered == {}


def test_approval_present_at_base_covers_nothing():
    entry = _approval("cli.a", "changed")
    uncovered = _unapproved_surface_diffs(
        {"cli.a": [1]}, {"cli.a": [2]}, [entry], [entry])
    assert uncovered == {"cli.a": "changed"}


def test_wildcard_present_at_base_does_not_cover_new_key():
    entry = _approval("cli.*", "added")
    uncovered = _unapproved_surface_diffs(
        {}, {"cli.new": [1]}, [entry], [entry])
    assert uncovered == {"cli.new": "added"}


# ---- SPEC §3.7 item 5: the converter change adds only `type` ------------------

#: The two item-5 approvals, identified by their exact entries. While new
#: relative to the base, every changed key they cover must differ from the
#: base only by the added `type` field. Once at the base, they check nothing.
_CONVERTER_APPROVALS = (
    {"key": "cli.*", "change": "changed",
     "plan_ref": "PLAN A11 (shape completion: converter)",
     "pre_approved_by": "Aram 2026-10-03: accepted PLAN revision 4"},
    {"key": "tools.*", "change": "changed",
     "plan_ref": "PLAN A11 (shape completion: converter)",
     "pre_approved_by": "Aram 2026-10-03: accepted PLAN revision 4"},
)


def test_converter_change_adds_only_type(base_ref):
    base_text = _git_show(
        base_ref,
        (ARCH / arch_surface.SURFACE_FILENAME).relative_to(ROOT).as_posix())
    if base_text is None:
        return
    base_approvals_text = _git_show(
        base_ref, APPROVALS_PATH.relative_to(ROOT).as_posix())
    base_approvals = (
        yaml.safe_load(base_approvals_text)["approvals"]
        if base_approvals_text is not None else [])
    current_approvals = yaml.safe_load(
        APPROVALS_PATH.read_text(encoding="utf-8"))["approvals"]
    new_converter = [entry for entry in _CONVERTER_APPROVALS
                     if entry in current_approvals
                     and entry not in base_approvals]
    if not new_converter:
        return
    base_flat = arch_surface.flatten_surface(json.loads(base_text))
    live = arch_surface.build_surface(ROOT)
    live_flat = arch_surface.flatten_surface(live)
    live_text = arch_surface.dump_surface(live)
    rel = (ARCH / arch_surface.SURFACE_FILENAME).relative_to(ROOT).as_posix()
    failures = []
    diff = arch_surface.diff_keys(base_flat, live_flat)
    for key in sorted(diff):
        change = diff[key]
        if change != "changed":
            continue
        if not any(arch_surface.approval_covers(entry, key, change)
                   for entry in new_converter):
            continue
        stripped = [{name: value for name, value in option.items()
                     if name != "type"}
                    for option in live_flat[key]]
        if (stripped != base_flat[key]
                or any("type" not in option for option in live_flat[key])):
            lineno = arch_surface.locate_line(live_text, key)
            failures.append(
                f"A11 {key}: converter approval covers more than the added "
                f"type field — {rel}:{lineno} — {FIX['A11']}")
    assert not failures, "\n".join(failures)


# ---- amendment (u) item 1: a conversion changes only the schema handler -----

#: A conversion's surface entry, by shape (amendment (u) item 1): one per
#: converted operation, verbatim from the kickoff. While new relative to
#: the base, the covered request-schema file must differ from the base
#: only in ``x-los-cli-command.handler``, rebound to the invoke adapter.
#: Once at the base, it checks nothing.
_D4_CONVERSION_PLAN_REF_RE = re.compile(r"^PLAN D4 \([^:]+: [^ ]+ converted\)$")
_D4_CONVERSION_APPROVED_BY = "Aram 2026-10-03: accepted PLAN revision 4"


def _is_d4_conversion_entry(entry: dict) -> bool:
    key = entry.get("key", "")
    plan_ref = entry.get("plan_ref", "")
    return (
        key.startswith("request_schemas.")
        and key.endswith(".schema.json")
        and entry.get("change") == "changed"
        and isinstance(plan_ref, str)
        and _D4_CONVERSION_PLAN_REF_RE.match(plan_ref) is not None
        and entry.get("pre_approved_by") == _D4_CONVERSION_APPROVED_BY
    )


def _assert_alias_schema_identical(operation: str, old_text: str,
                                   new_text: str) -> None:
    """Alias request schemas never change (SPEC (ay) item 2)."""
    if old_text != new_text:
        raise AssertionError(f"{operation} is an alias and must not change")
    for text in (old_text, new_text):
        doc = json.loads(text)
        if "$ref" not in doc or "properties" in doc:
            raise AssertionError(f"{operation} is not a pure alias")


def _strip_bu4_filter_flip(operation: str, old: dict, new: dict
                           ) -> tuple[dict, dict]:
    """Strip exactly the SPEC (bu) 4 filter flip; fail on any deviation.

    Returns ``(old, new)`` copies with the enumerated pair's
    ``x-los-lookup`` restored to its base value. Raises when the pointer
    is missing, the base is not lookup-true, or the tip is not
    flipped to false; every other difference stays for the exact
    recursive comparison.
    """
    allowed = {pointer for (op, pointer) in BU4_FILTER_NOT_LOOKUP
               if op == operation}
    old_copy = copy.deepcopy(old)
    new_copy = copy.deepcopy(new)
    for pointer in allowed:
        parts = pointer.split("/")[1:]
        old_node = old_copy
        new_node = new_copy
        try:
            for part in parts:
                old_node = old_node[part]
                new_node = new_node[part]
        except (KeyError, TypeError):
            raise AssertionError(
                f"filter pointer {pointer} is missing") from None
        if old_node.get("x-los-lookup") is not True:
            raise AssertionError(
                f"filter pointer {pointer} is not lookup at base")
        if new_node.get("x-los-lookup") is not False:
            raise AssertionError(
                f"filter pointer {pointer} is not flipped to false")
        new_node["x-los-lookup"] = True
    return old_copy, new_copy


def test_converted_request_schema_changes_only_the_handler(base_ref):
    base_approvals_text = _git_show(
        base_ref, APPROVALS_PATH.relative_to(ROOT).as_posix())
    base_approvals = (
        yaml.safe_load(base_approvals_text)["approvals"]
        if base_approvals_text is not None else [])
    current_approvals = yaml.safe_load(
        APPROVALS_PATH.read_text(encoding="utf-8"))["approvals"]
    new_entries = [entry for entry in current_approvals
                   if _is_d4_conversion_entry(entry)
                   and entry not in base_approvals]
    if not new_entries:
        return
    failures = []
    for entry in new_entries:
        key = entry["key"]
        fname = key[len("request_schemas."):]
        operation = fname[:-len(".schema.json")]
        rel = f"system/schema/requests/{fname}"
        base_text = _git_show(base_ref, rel)
        if base_text is None:
            failures.append(f"A11 {key}: no {rel} at the base — {FIX['A11']}")
            continue
        old = json.loads(base_text)
        new = json.loads((ROOT / rel).read_text(encoding="utf-8"))
        try:
            old, new = _strip_approved_owner_metadata(operation, old, new)
        except AssertionError as exc:
            failures.append(f"A11 {key}: {exc} — {rel} — {FIX['A11']}")
            continue
        old, new = _strip_bf_description_updates(operation, old, new)
        try:
            old, new = _strip_bu4_filter_flip(operation, old, new)
        except AssertionError as exc:
            failures.append(f"A11 {key}: {exc} — {rel} — {FIX['A11']}")
            continue
        want = f"learning_os.adapters.cli.invoke:{operation}"
        if set(new) != set(old):
            failures.append(
                f"A11 {key}: conversion changes top-level keys "
                f"{sorted(set(new) ^ set(old))} — {rel} — {FIX['A11']}")
            continue
        for top in old:
            if top != "x-los-cli-command" and new[top] != old[top]:
                failures.append(
                    f"A11 {key}: conversion changes {top!r} — "
                    f"{rel} — {FIX['A11']}")
        if "x-los-cli-command" not in old or "x-los-cli-command" not in new:
            failures.append(
                f"A11 {key}: conversion needs a cli-command binding — "
                f"{rel} — {FIX['A11']}")
            continue
        old_cmd = old["x-los-cli-command"]
        new_cmd = new["x-los-cli-command"]
        if set(new_cmd) != set(old_cmd):
            failures.append(
                f"A11 {key}: conversion changes cli-command keys "
                f"{sorted(set(new_cmd) ^ set(old_cmd))} — {rel} — {FIX['A11']}")
            continue
        for name in old_cmd:
            if name != "handler" and new_cmd[name] != old_cmd[name]:
                failures.append(
                    f"A11 {key}: conversion changes cli-command {name!r} — "
                    f"{rel} — {FIX['A11']}")
        if new_cmd["handler"] != want:
            failures.append(
                f"A11 {key}: conversion handler is {new_cmd['handler']!r}, "
                f"want {want!r} — {rel} — {FIX['A11']}")
        if old_cmd["handler"] == new_cmd["handler"]:
            failures.append(
                f"A11 {key}: conversion changes no handler — "
                f"{rel} — {FIX['A11']}")
    assert not failures, "\n".join(failures)


def test_request_schema_aliases_are_byte_identical_to_base(base_ref):
    # B2 retires aliases. Verify all 40 effective requests against their
    # former primary schemas; all unlisted shape differences still fail.
    mapping = json.loads((ARCH / "operation-moves.json").read_text())
    assert len(mapping) == 40 and len(set(mapping.values())) == 40
    for old_name, new_name in mapping.items():
        rel = f"system/schema/requests/{old_name}.schema.json"
        new_rel = f"system/schema/requests/{new_name}.schema.json"
        old_text = _git_show(base_ref, rel)
        new = _before_approved_c1_schema(new_name, (ROOT / new_rel).read_bytes())
        if old_text is None:
            assert not (ROOT / rel).exists(), rel
            # A post-C1 base already carries the same approved additions.
            # Compare both sides in the historical context, keeping the
            # exact approved-byte checks in _before_approved_c1_schema.
            old = _before_approved_c1_schema(
                new_name, _git_show(base_ref, new_rel).encode("utf-8"))
        else:
            old = json.loads(old_text)
            old["$id"] = "learningos/requests/" + new_name
            old["x-los-cli-command"]["handler"] = "learning_os.adapters.cli.invoke:" + new_name
            if new_name in {"backup.manifest", "health.report", "legacy.archive.inspect", "legacy.archive.status", "masters-planning.dashboard"}:
                old["x-los-cli-command"]["operation_kind"] = "tool"
            if new_name in {"repository.validate", "projection.generate"}:
                old["properties"]["json"] = json.loads(_git_show(base_ref, "system/schema/requests/cli.health-report.schema.json"))["properties"]["json"]
        new = _restore_phase6_descriptions(new_name, old, new)
        assert new == old, new_name


def test_contract_rises_at_most_one_version_per_branch(base_ref):
    """v57-v61 were five bumps in one evening for one issue (#12).

    Every bump moved the fixture snapshot and forced a re-record, and no
    other branch ever adopted the intermediate shapes. A branch may raise
    ``contract_version`` by at most one over its base; later schema
    iterations on the same branch fold into that entry in place, and the
    entries the base already adopted never change.
    """
    from learning_os.store.contracts.data_contract import load_contract

    rel = "system/contracts/data-contract.yaml"
    current = load_contract(ROOT / rel)
    assert current is not None, rel
    base_text = _git_show(base_ref, rel)
    if base_text is None:
        pytest.skip(f"{rel} is absent at the ratchet base {base_ref}")
    base_contract = yaml.safe_load(base_text)
    base_version = int(base_contract["contract_version"])
    rose = int(current["contract_version"]) - base_version
    assert rose <= 1, (
        f"{rel} rose {base_version} -> {current['contract_version']} on this "
        "branch; a branch may add at most one contract version — fold the "
        "later schema iterations into the branch's entry with "
        "schema_contract.py --rebump (see test_contract_rebump.py)")
    base_history = {int(e["version"]): e
                    for e in base_contract.get("history") or []}
    for entry in current["history"]:
        version = int(entry["version"])
        if version <= base_version:
            assert entry == base_history.get(version), (
                f"{rel} history v{version} differs from {base_ref}: "
                "--rebump may only rewrite an entry this branch added above "
                "the base, never one the base already adopted")


def _owner_purity_docs():
    old = {
        "properties": {
            "id": {"type": "string",
                   "x-los-cli": {"default": None, "required": True}},
            "more_ids": {"type": "array",
                         "items": {"type": "string"},
                         "x-los-cli": {"default": None}},
            "json": {"type": "boolean"},
        },
        "required": ["id"],
    }
    new = copy.deepcopy(old)
    new["properties"]["id"]["x-los-id-owner"] = "inspect-reference"
    new["properties"]["id"]["x-los-lookup"] = True
    new["properties"]["more_ids"]["items"]["x-los-id-owner"] = (
        "inspect-reference")
    new["properties"]["more_ids"]["items"]["x-los-lookup"] = True
    return old, new


def test_owner_metadata_strip_accepts_only_the_approved_pair():
    old, new = _owner_purity_docs()
    stripped_old, stripped_new = _strip_approved_owner_metadata(
        "project.inspect", old, new)
    assert stripped_new == stripped_old
    assert stripped_new["properties"] == old["properties"]

    def rejects(mutator):
        _, mutant = _owner_purity_docs()
        mutator(mutant)
        with pytest.raises(AssertionError):
            _strip_approved_owner_metadata("project.inspect", old, mutant)

    def drop_owner(doc):
        del doc["properties"]["id"]["x-los-id-owner"]

    def wrong_owner(doc):
        doc["properties"]["id"]["x-los-id-owner"] = "other-owner"

    def lookup_one(doc):
        doc["properties"]["id"]["x-los-lookup"] = 1

    def lookup_zero(doc):
        doc["properties"]["more_ids"]["items"]["x-los-lookup"] = 0

    def changed_type(doc):
        doc["properties"]["id"]["type"] = "integer"

    def missing_node(doc):
        del doc["properties"]["more_ids"]["items"]

    for mutator in (drop_owner, wrong_owner, lookup_one, lookup_zero,
                    changed_type, missing_node):
        rejects(mutator)

    # Base-pinned metadata may not change either.
    pinned_old, pinned_new = _owner_purity_docs()
    pinned_old["properties"]["id"]["x-los-id-owner"] = "inspect-reference"
    pinned_old["properties"]["id"]["x-los-lookup"] = True
    pinned_new["properties"]["id"]["x-los-id-owner"] = "other-owner"
    with pytest.raises(AssertionError):
        _strip_approved_owner_metadata("project.inspect", pinned_old, pinned_new)


def test_owner_metadata_leaves_other_diffs_for_exact_compare():
    old, new = _owner_purity_docs()

    def differs(mutator):
        _, mutant = _owner_purity_docs()
        mutator(mutant)
        _, stripped = _strip_approved_owner_metadata(
            "project.inspect", old, mutant)
        assert stripped["properties"] != old["properties"]

    def extra_keyword(doc):
        doc["properties"]["id"]["additionalProperties"] = False

    def changed_default(doc):
        doc["properties"]["id"]["x-los-cli"]["default"] = "x"

    def changed_required(doc):
        doc["properties"]["id"]["x-los-cli"]["required"] = False

    def unknown_pointer(doc):
        doc["properties"]["json"]["x-los-id-owner"] = "inspect-reference"
        doc["properties"]["json"]["x-los-lookup"] = True

    for mutator in (extra_keyword, changed_default, changed_required,
                    unknown_pointer):
        differs(mutator)


def test_alias_identity_rejects_a_changed_alias():
    old_text = json.dumps({"$ref": "project.inspect.schema.json",
                           "x-governs": "project.inspect"}, indent=2)
    _assert_alias_schema_identical("project.inspect", old_text, old_text)
    new_text = json.dumps({"$ref": "other.schema.json",
                           "x-governs": "project.inspect"}, indent=2)
    with pytest.raises(AssertionError):
        _assert_alias_schema_identical("project.inspect", old_text, new_text)
    not_alias = json.dumps({"properties": {}}, indent=2)
    with pytest.raises(AssertionError):
        _assert_alias_schema_identical(
            "project.inspect", not_alias, not_alias)


def _bf_description_docs():
    old = {
        "properties": {
            "unit_id": {"type": "string",
                        "description":
                            "unit_id (no description in the parser yet)"},
            "progress_summary": {
                "type": "string",
                "description":
                    "progress_summary (no description in the parser yet)"},
        },
    }
    new = copy.deepcopy(old)
    new["properties"]["unit_id"]["description"] = (
        "unit whose stage to update")
    return old, new


def test_bf_description_strip_accepts_only_the_listed_replacement():
    old, new = _bf_description_docs()
    _, stripped = _strip_bf_description_updates(
        "stage.progress.update", old, new)
    assert stripped == old

    def differs(mutator):
        base, _ = _bf_description_docs()
        mutant = copy.deepcopy(base)
        mutator(mutant)
        _, stripped_mutant = _strip_bf_description_updates(
            "stage.progress.update", base, mutant)
        assert stripped_mutant != base

    def unlisted_pointer(doc):
        doc["properties"]["progress_summary"]["description"] = (
            "record where work stopped")

    def keeps_mark(doc):
        doc["properties"]["unit_id"]["description"] = (
            "unit_id (no description in the parser yet) v2")

    def non_string(doc):
        doc["properties"]["unit_id"]["description"] = 5

    def other_keyword(doc):
        doc["properties"]["unit_id"]["description"] = (
            "unit whose stage to update")
        doc["properties"]["unit_id"]["type"] = "integer"

    for mutator in (unlisted_pointer, keeps_mark, non_string,
                    other_keyword):
        differs(mutator)


def _strip_bf_then_bu4(operation: str, old: dict, new: dict
                       ) -> tuple[dict, dict]:
    """The real A11 order: BF descriptions, then the BU4 lookup flip."""
    mid_old, mid_new = _strip_bf_description_updates(operation, old, new)
    return _strip_bu4_filter_flip(operation, mid_old, mid_new)


def test_bu4_filter_flip_accepts_only_the_enumerated_lookup_change():
    rel = "system/schema/requests/module.list.schema.json"
    new = json.loads((ROOT / rel).read_text(encoding="utf-8"))
    # The historical transition is a unit fixture, independent of whether
    # the ratchet base already contains the approved lookup flip.
    old = copy.deepcopy(new)
    old["properties"]["program_id"]["x-los-lookup"] = True
    _, stripped = _strip_bf_then_bu4("module.list", old, new)
    assert stripped["properties"] == old["properties"]

    def rejects(mutator):
        mutant = copy.deepcopy(new)
        mutator(mutant)
        with pytest.raises(AssertionError):
            _strip_bf_then_bu4("module.list", old, mutant)

    def flipped_back(doc):
        doc["properties"]["program_id"]["x-los-lookup"] = True

    def deleted_node(doc):
        del doc["properties"]["program_id"]

    for mutator in (flipped_back, deleted_node):
        rejects(mutator)

    # A reversed base (not lookup-true) is rejected too.
    reversed_base = copy.deepcopy(old)
    reversed_base["properties"]["program_id"]["x-los-lookup"] = False
    with pytest.raises(AssertionError):
        _strip_bf_then_bu4("module.list", reversed_base, new)

    # Another operation's annotation change is not stripped: it stays
    # for the exact comparison, which fails it.
    _, untouched = _strip_bf_then_bu4("note.content", old, new)
    assert untouched == new

    def differs(mutator):
        mutant = copy.deepcopy(new)
        mutator(mutant)
        _, stripped_mutant = _strip_bf_then_bu4(
            "module.list", old, mutant)
        assert stripped_mutant["properties"] != old["properties"]

    def extra_keyword(doc):
        doc["properties"]["program_id"]["additionalProperties"] = False

    def changed_default(doc):
        doc["properties"]["program_id"]["x-los-cli"]["default"] = "x"

    def flipped_kind(doc):
        doc["properties"]["program_id"]["x-los-id-kind"] = "unit"

    def other_pointer(doc):
        doc["properties"]["status"]["x-los-lookup"] = False

    for mutator in (extra_keyword, changed_default, flipped_kind,
                    other_pointer):
        differs(mutator)

    # SPEC (cq) 2: the same composed allowance for the two
    # plan.template generation seeds (plan.template inherits
    # through its alias and its file never changes).
    seed_rel = "system/schema/requests/plan.template.schema.json"
    seed_new = json.loads((ROOT / seed_rel).read_text(encoding="utf-8"))
    seed_old = copy.deepcopy(seed_new)
    for field in ("unit_id", "module_id"):
        seed_old["properties"][field]["x-los-lookup"] = True
    _, seed_stripped = _strip_bf_then_bu4(
        "plan.template", seed_old, seed_new)
    assert seed_stripped["properties"] == seed_old["properties"]

    def seed_rejects(mutator):
        mutant = copy.deepcopy(seed_new)
        mutator(mutant)
        with pytest.raises(AssertionError):
            _strip_bf_then_bu4("plan.template", seed_old, mutant)

    def retained_unit_true(doc):
        doc["properties"]["unit_id"]["x-los-lookup"] = True

    def retained_module_true(doc):
        doc["properties"]["module_id"]["x-los-lookup"] = True

    def deleted_seed(doc):
        del doc["properties"]["unit_id"]

    for mutator in (retained_unit_true, retained_module_true,
                    deleted_seed):
        seed_rejects(mutator)

    # A reversed base at either seed pointer is rejected too.
    reversed_seed = copy.deepcopy(seed_old)
    reversed_seed["properties"]["module_id"]["x-los-lookup"] = False
    with pytest.raises(AssertionError):
        _strip_bf_then_bu4("plan.template", reversed_seed, seed_new)

    # Another operation's annotation change is not stripped.
    _, seed_untouched = _strip_bf_then_bu4(
        "note.content", seed_old, seed_new)
    assert seed_untouched == seed_new

    def seed_differs(mutator):
        mutant = copy.deepcopy(seed_new)
        mutator(mutant)
        _, stripped_mutant = _strip_bf_then_bu4(
            "plan.template", seed_old, mutant)
        assert stripped_mutant["properties"] != seed_old["properties"]

    def seed_extra_keyword(doc):
        doc["properties"]["module_id"]["additionalProperties"] = False

    def seed_changed_default(doc):
        doc["properties"]["unit_id"]["x-los-cli"]["default"] = "x"

    def seed_changed_type(doc):
        doc["properties"]["unit_id"]["type"] = "integer"

    def seed_flipped_kind(doc):
        doc["properties"]["module_id"]["x-los-id-kind"] = "unit"

    def seed_drifted_description(doc):
        # The json leaf is outside the BF description list: a
        # description change there is not an allowance.
        doc["properties"]["json"]["description"] = "another envelope story"

    def seed_other_pointer(doc):
        doc["properties"]["title"]["x-los-lookup"] = False

    for mutator in (seed_extra_keyword, seed_changed_default,
                    seed_changed_type, seed_flipped_kind,
                    seed_drifted_description, seed_other_pointer):
        seed_differs(mutator)


def test_operation_move_changes_only_the_declared_identifier():
    move = {"from": "cli.health-report", "to": "health.report"}
    assert _translate_one("cli.health-report::diagnostic", move) == "health.report::diagnostic"
    assert _translate_one("cli.health-report-other::diagnostic", move) == "cli.health-report-other::diagnostic"
    assert _translate_one("health.report::diagnostic", move) == "health.report::diagnostic"
    assert _translate_one("tools/x.py::cli.health-report", move) == "tools/x.py::cli.health-report"


@pytest.mark.parametrize("index", range(9))
@pytest.mark.parametrize("mutation", ["description", "constraint", "metadata"])
def test_phase6_description_allowance_preserves_all_other_schema_guards(index, mutation):
    table = json.loads((ARCH / "phase6-description-updates.json").read_text())
    change = table["changes"][index]
    operation = Path(change["schema"]).name.removesuffix(".schema.json")
    before = json.loads((ROOT / change["schema"]).read_text())
    after = copy.deepcopy(before)
    old_node, new_node = before, after
    for part in change["pointer"].split("/")[1:-1]:
        old_node, new_node = old_node[part], new_node[part]
    old_node["description"] = change["old"]
    assert _restore_phase6_descriptions(operation, before, after) == before
    if mutation == "description":
        new_node["description"] += " unauthorized"
        with pytest.raises(AssertionError):
            _restore_phase6_descriptions(operation, before, after)
    else:
        new_node["maxLength" if mutation == "constraint" else "x-los-id-owner"] = 100 if mutation == "constraint" else "different-owner"
        assert _restore_phase6_descriptions(operation, before, after) != before
