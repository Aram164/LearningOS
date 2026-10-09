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

import json
import os
import re
import subprocess
import tomllib
from pathlib import Path

import arch_surface
import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
ARCH = ROOT / arch_surface.ARCHITECTURE_DIR
RATCHETS_PATH = ARCH / arch_surface.RATCHETS_FILENAME
APPROVALS_PATH = ARCH / arch_surface.APPROVALS_FILENAME
PYPROJECT_PATH = ROOT / "pyproject.toml"

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
            "adapters : commands",
            "ops : ai_actions : masters_planning : material_synthesis",
            "rules : genout : semantics : search : health : abilities : learning_runtime : routes : evidence",
            "store : loading : loader : contracts : derived : diagnostics : transactions : fingerprint : githistory : pathing : revisions : validation_cache : warning_baseline : backup_manifest : legacy_archive : materials_resolution : material_slices : material_analysis : garden : manifest_identity : observations",
            "domain : digests : material_inventory : material_refs : route_identity : unit_notes : render",
        ],
    },
    "A1 transaction writer access (PLAN A2, D4)": {
        "type": "forbidden",
        "source_modules": [
            "learning_os.rules",
            "learning_os.genout",
            "learning_os.semantics",
            "learning_os.search",
            "learning_os.health",
            "learning_os.abilities",
            "learning_os.learning_runtime",
            "learning_os.routes",
            "learning_os.domain",
        ],
        "forbidden_modules": ["learning_os.transactions"],
    },
    "A1 transaction service protected (PLAN A1, D14)": {
        "type": "protected",
        "protected_modules": ["learning_os.transactions"],
        "allowed_importers": ["learning_os.ops"],
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
  "adapters : commands",
  "ops : ai_actions : masters_planning : material_synthesis",
  "rules : genout : semantics : search : health : abilities : learning_runtime : routes : evidence",
  "store : loading : loader : contracts : derived : diagnostics : transactions : fingerprint : githistory : pathing : revisions : validation_cache : warning_baseline : backup_manifest : legacy_archive : materials_resolution : material_slices : material_analysis : garden : manifest_identity : observations",
  "domain : digests : material_inventory : material_refs : route_identity : unit_notes : render",
]
ignore_imports = []

[[tool.importlinter.contracts]]
name = "A1 transaction writer access (PLAN A2, D4)"
type = "forbidden"
source_modules = ["learning_os.rules", "learning_os.genout", "learning_os.semantics", "learning_os.search", "learning_os.health", "learning_os.abilities", "learning_os.learning_runtime", "learning_os.routes", "learning_os.domain"]
forbidden_modules = ["learning_os.transactions"]
ignore_imports = []

[[tool.importlinter.contracts]]
name = "A1 transaction service protected (PLAN A1, D14)"
type = "protected"
protected_modules = ["learning_os.transactions"]
allowed_importers = ["learning_os.ops"]
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
  "adapters : commands",
  "ops : ai_actions : masters_planning : material_synthesis",
  "rules : genout : semantics : search : health : abilities : learning_runtime : routes : evidence",
  "store : loading : loader : contracts : derived : diagnostics : transactions : fingerprint : githistory : pathing : revisions : validation_cache : warning_baseline : backup_manifest : legacy_archive : materials_resolution : material_slices : material_analysis : garden : manifest_identity : observations",
  "domain : digests : material_inventory : material_refs : route_identity : unit_notes : render",
]
ignore_imports = []

[[tool.importlinter.contracts]]
name = "A1 transaction writer access (PLAN A2, D4)"
type = "forbidden"
source_modules = ["learning_os.rules", "learning_os.genout", "learning_os.semantics", "learning_os.search", "learning_os.health", "learning_os.abilities", "learning_os.learning_runtime", "learning_os.routes", "learning_os.domain"]
forbidden_modules = ["learning_os.transactions"]
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
        '\n  "domain : digests : material_inventory : material_refs : route_identity : unit_notes : render",',
        "", 1)
    failures = _contract_set_failures(_TOML_THREE_CONTRACTS, weakened)
    assert failures, "a removed layer must fail"
    assert any("differs from SPEC" in f for f in failures)


def test_contract_weakened_allowed_importers_fails():
    weakened = _TOML_THREE_CONTRACTS.replace(
        'allowed_importers = ["learning_os.ops"]',
        'allowed_importers = ["learning_os.ops", "learning_os.commands"]', 1)
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
    assert _surface_rule("cli.inspect") == "A11"
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
