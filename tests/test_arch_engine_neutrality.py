"""Engine-effect neutrality: the marked engine matches the baseline (S03).

Re-runs the six ``arch_engine_cases`` scenarios and compares them with
``tests/architecture/engine-baseline.json``, recorded on the unmodified
engine. The phase marker (Task 2) must not change any effect.
"""

from __future__ import annotations

import json
from pathlib import Path

import arch_engine_cases
import pytest

BASELINE_PATH = (
    Path(__file__).resolve().parent / "architecture" / "engine-baseline.json")


def _load_baseline() -> dict[str, dict]:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", arch_engine_cases.CASE_NAMES)
def test_engine_matches_baseline(case: str, tmp_path: Path):
    baseline = _load_baseline()
    assert case in baseline, f"baseline has no case {case!r}"
    record = arch_engine_cases.run_case(case, tmp_path)
    assert record == baseline[case]
