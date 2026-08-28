"""The warning policy is executable, and it cannot be gamed by an equal total.

The gate this replaces was prose: "0 errors, 0 warnings" in one document,
"warnings never block" in another, 535 warnings on disk. These tests pin the
policy that resolved the disagreement — zero errors, warnings visible, no NEW
signature — and in particular pin the one property a count does not have.
"""

from __future__ import annotations

import importlib.util
import json
from collections import Counter
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location(
    "warning_baseline", ROOT / "tools" / "warning_baseline.py")
wb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wb)

_SCHEMA = json.loads(
    (ROOT / "system" / "contracts" / "validation-warning-baseline.schema.json")
    .read_text(encoding="utf-8"))


def _write(root: Path, signatures: dict[tuple[str, str], int]) -> None:
    wb.write_baseline(root, Counter(signatures), "test fixture")


# ---- the delta -------------------------------------------------------------

def test_an_unchanged_set_has_no_delta():
    same = Counter({("LOCATOR-VAGUE", "a.yaml"): 3})
    assert wb.delta(same, same) == ([], [])


def test_a_new_signature_is_a_regression():
    before = Counter({("LOCATOR-VAGUE", "a.yaml"): 3})
    after = Counter({("LOCATOR-VAGUE", "a.yaml"): 3, ("ROUTE-ANGLE-DETAIL-MISSING", "b.yaml"): 1})
    regressions, repairs = wb.delta(before, after)
    assert len(regressions) == 1 and "ROUTE-ANGLE-DETAIL-MISSING" in regressions[0]
    assert repairs == []


def test_a_grown_signature_is_a_regression():
    before = Counter({("LOCATOR-VAGUE", "a.yaml"): 3})
    after = Counter({("LOCATOR-VAGUE", "a.yaml"): 4})
    regressions, _ = wb.delta(before, after)
    assert len(regressions) == 1 and "3 → 4" in regressions[0]


def test_a_shrunk_signature_is_a_repair_not_a_failure():
    before = Counter({("LOCATOR-VAGUE", "a.yaml"): 3})
    after = Counter({("LOCATOR-VAGUE", "a.yaml"): 1})
    regressions, repairs = wb.delta(before, after)
    assert regressions == []
    assert len(repairs) == 1


def test_an_equal_total_does_not_hide_a_trade():
    """The property a count does not have, and the reason for the signature."""
    before = Counter({("LOCATOR-VAGUE", "a.yaml"): 2, ("LOCATOR-VAGUE", "b.yaml"): 2})
    after = Counter({("LOCATOR-VAGUE", "a.yaml"): 1, ("LOCATOR-VAGUE", "b.yaml"): 3})
    assert sum(before.values()) == sum(after.values())
    regressions, repairs = wb.delta(before, after)
    assert len(regressions) == 1
    assert len(repairs) == 1


# ---- the file --------------------------------------------------------------

def test_a_written_baseline_round_trips(tmp_path):
    signatures = {("LOCATOR-VAGUE", "a.yaml"): 3, ("HYGIENE-UNFILED", ""): 1}
    _write(tmp_path, signatures)
    loaded, meta = wb.load_baseline(tmp_path)
    assert loaded == Counter(signatures)
    assert meta["total"] == 4
    assert meta["distinct_signatures"] == 2
    assert meta["note"]


def test_a_written_baseline_satisfies_its_schema(tmp_path):
    from jsonschema import Draft202012Validator

    _write(tmp_path, {("LOCATOR-VAGUE", "a.yaml"): 3})
    data = yaml.safe_load(
        (tmp_path / wb.BASELINE_RELATIVE).read_text(encoding="utf-8"))
    Draft202012Validator(_SCHEMA).validate(data)


def test_a_missing_baseline_reads_as_empty_not_as_a_pass(tmp_path):
    loaded, meta = wb.load_baseline(tmp_path)
    assert loaded == Counter() and meta == {}
    # With an empty baseline every current warning is new, so the gate fires.
    regressions, _ = wb.delta(loaded, Counter({("LOCATOR-VAGUE", "a.yaml"): 1}))
    assert regressions


def test_environmental_warnings_are_excluded_by_name():
    """They describe the machine, not the content, and differ per checkout."""
    from learning_os.rules.common import ENVIRONMENTAL_WARNINGS

    for code in ("MATERIALS-OFFLINE", "MATERIALS-DRIFT", "HYGIENE-VIEWS"):
        assert code in ENVIRONMENTAL_WARNINGS


# ---- the live repository ---------------------------------------------------

@pytest.mark.full_repo
def test_the_recorded_baseline_still_matches_this_repository():
    current, errors = wb.collect(ROOT)
    baseline, meta = wb.load_baseline(ROOT)
    assert meta, "no baseline recorded"
    assert errors == [], "\n".join(errors)
    regressions, _ = wb.delta(baseline, current)
    assert regressions == [], "\n".join(regressions)


@pytest.mark.full_repo
def test_no_environmental_warning_reached_the_recorded_baseline():
    from learning_os.rules.common import ENVIRONMENTAL_WARNINGS

    baseline, _ = wb.load_baseline(ROOT)
    for code, _path in baseline:
        assert code not in ENVIRONMENTAL_WARNINGS, code
