"""Ratchet monotonicity against the base (SPEC §2.3) and file validity (§2.4).

Compares the worktree's ``ratchets.yaml``, ``pyproject.toml``
``ignore_imports`` and live A11 surface against ``git show
$LOS_RATCHET_BASE:<file>`` (default base: ``main``). A file absent at the
base is the baseline: every ``ratchets.yaml`` entry must then be
``since: baseline``, and a first-ever ``surface.json`` needs no approvals.
``baselined`` lists the checks whose baseline is recorded; it only grows,
and every check id with entries is listed (amended §2.3 rule 2).
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


def test_surface_diffs_have_approvals(base_ref):
    base_text = _git_show(
        base_ref,
        (ARCH / arch_surface.SURFACE_FILENAME).relative_to(ROOT).as_posix())
    if base_text is None:
        return
    base_flat = arch_surface.flatten_surface(json.loads(base_text))
    live = arch_surface.build_surface(ROOT)
    live_flat = arch_surface.flatten_surface(live)
    diff = arch_surface.diff_keys(base_flat, live_flat)
    if not diff:
        return
    approvals = yaml.safe_load(APPROVALS_PATH.read_text(encoding="utf-8"))["approvals"]
    live_text = arch_surface.dump_surface(live)
    failures = []
    for key in sorted(diff):
        if any(arch_surface.approval_covers(a, key, diff[key]) for a in approvals):
            continue
        text = base_text if diff[key] == "removed" else live_text
        lineno = arch_surface.locate_line(text, key)
        rel = (ARCH / arch_surface.SURFACE_FILENAME).relative_to(ROOT).as_posix()
        failures.append(f"A11 {key}: {diff[key]} — {rel}:{lineno} — {FIX['A11']}")
    assert not failures, "unapproved surface diffs:\n" + "\n".join(failures)
