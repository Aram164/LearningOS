"""Every declared set has a checker, and the register of them is complete.

This is the keystone the 2026-09-03 audit asked for. The repository's pattern —
a declared set, a discovered set, an executable comparison — was applied to
record schemas and to normative prose and held exactly where it was applied.
It was never applied to the declarations themselves, so a contract could be
added to `system/contracts/` with no checker and nothing noticed.

The assertions are deliberately about the *code*, not the data. Coverage is a
property of what is wired up, and `make check` runs against records; a test is
the right home and costs the pre-commit hook nothing.
"""

from __future__ import annotations

import importlib
import inspect
import re
from pathlib import Path

import pytest
import yaml

from learning_os.rules.core import Validator

ROOT = Path(__file__).resolve().parents[1]
REGISTER_RELATIVE = "system/contracts/contract-register.yaml"
CONTRACTS = ROOT / "system" / "contracts"


def _register() -> dict:
    return yaml.safe_load((ROOT / REGISTER_RELATIVE).read_text(encoding="utf-8"))


REGISTER = _register()
ROWS = REGISTER["contracts"]


def _declared_yaml_on_disk() -> set[str]:
    """Every YAML declaration under system/contracts/, at any depth."""
    return {
        path.relative_to(ROOT).as_posix()
        for path in CONTRACTS.rglob("*.yaml")
        if path.is_file()
    }


# ---- completeness ----------------------------------------------------------

def test_the_register_accounts_for_every_declaration_on_disk():
    """Set equality, not a count — the same choice the corpus index makes.

    A count passes while one contract is swapped for another; only set equality
    catches the contract nobody registered.
    """
    exempt = {row["path"] for row in REGISTER.get("exempt", ())}
    registered = {row["declaration"] for row in ROWS}
    on_disk = _declared_yaml_on_disk()

    unregistered = on_disk - registered - exempt
    assert not unregistered, (
        "declaration(s) under system/contracts/ that nothing registers: "
        + ", ".join(sorted(unregistered))
        + f" — add a row to {REGISTER_RELATIVE} naming what enforces it"
    )

    phantom = registered - on_disk
    assert not phantom, (
        "registered but not on disk: " + ", ".join(sorted(phantom))
    )


def test_every_exemption_states_a_reason_and_exists():
    """An exemption with no reason is an unrecorded decision."""
    for row in REGISTER.get("exempt", ()):
        assert row.get("reason", "").strip(), f"{row['path']} is exempt with no reason"
        assert (ROOT / row["path"]).is_file(), f"exempt path is not on disk: {row['path']}"


def test_no_declaration_is_both_registered_and_exempt():
    exempt = {row["path"] for row in REGISTER.get("exempt", ())}
    registered = {row["declaration"] for row in ROWS}
    assert not (exempt & registered), sorted(exempt & registered)


# ---- every row names something real ----------------------------------------

@pytest.mark.parametrize("row", ROWS, ids=lambda row: row["declaration"])
def test_the_declaration_exists(row):
    assert (ROOT / row["declaration"]).is_file()


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row["declaration"])
def test_the_checker_imports(row):
    importlib.import_module(row["checker"])


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row["declaration"])
def test_the_named_test_exists(row):
    """`enforced_by: runtime` must not become `enforced by nothing`.

    A row that is enforced away from the validator is only as good as the test
    that exercises that path, so the register is required to name one.
    """
    assert (ROOT / row["test"]).is_file(), row["test"]


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row["declaration"])
def test_enforcement_is_one_of_the_two_declared_kinds(row):
    assert row["enforced_by"] in {"validator", "runtime"}


# ---- the two that earn the file --------------------------------------------

@pytest.mark.parametrize(
    "row",
    [r for r in ROWS if r["enforced_by"] == "validator"],
    ids=lambda row: row["declaration"],
)
def test_a_validator_contract_is_actually_wired_into_run(row):
    """Existing is not enough — `run()` has to call it.

    A `check_*` method that exists and is never called is invisible in a green
    run and is exactly the failure this register is for. Reading the source of
    `run()` is deliberate: it proves the wiring without running the validator.
    """
    method = row["validator_method"]
    assert callable(getattr(Validator, method, None)), (
        f"{method} is not a method on Validator"
    )
    assert method in inspect.getsource(Validator.run), (
        f"Validator.run() never calls {method} — the checker exists but does "
        "not run, which no green validation run would reveal"
    )


def _reports_errors(method_name: str, *, depth: int = 1) -> bool:
    """Whether ``method_name`` reports at error severity, directly or one hop.

    Direct `self.err(` is the common case. `check_hygiene` shows the other
    shape — a method whose whole body delegates to private `self._helper()`
    calls — so a checker that delegates must not read as a downgrade. What is
    caught either way is the case that matters: a method that reports, and
    reports only warnings.
    """
    source = inspect.getsource(getattr(Validator, method_name))
    if "self.err(" in source:
        return True
    if depth:
        for helper in set(re.findall(r"self\.(_[A-Za-z0-9_]+)\(", source)):
            if callable(getattr(Validator, helper, None)) and _reports_errors(
                helper, depth=depth - 1
            ):
                return True
    return False


@pytest.mark.parametrize(
    "row",
    [r for r in ROWS if r.get("severity") == "error"],
    ids=lambda row: row["declaration"],
)
def test_an_error_contract_reports_at_error_severity(row):
    """Catches a silent downgrade from `self.err` to `self.warn`.

    Severity is chosen at the call site in this codebase — there is no per-code
    table — so the checker's own source is the only place to check it. A rule
    quietly downgraded to a warning still passes every validation run, which is
    exactly why it needs a test rather than a green `make check`.
    """
    assert _reports_errors(row["validator_method"]), (
        f"{row['validator_method']} is registered at severity 'error' but "
        "reports no error, directly or through its helpers — a rule downgraded "
        "to a warning is invisible in a passing run"
    )


# ---- the live half ---------------------------------------------------------

@pytest.mark.full_repo
def test_every_validator_wired_contract_check_is_registered():
    """The reverse direction: a `check_*_contract` method nobody declared.

    Without this, a checker could be added to `run()` and left out of the
    register, and the register would still pass by being a subset.
    """
    registered = {
        row["validator_method"] for row in ROWS if row["enforced_by"] == "validator"
    }
    run_source = inspect.getsource(Validator.run)
    called = {
        name
        for name in dir(Validator)
        if name.startswith("check_")
        and name.endswith("_contract")
        and name in run_source
    }
    assert called <= registered, (
        "contract check(s) wired into run() but absent from the register: "
        + ", ".join(sorted(called - registered))
    )
