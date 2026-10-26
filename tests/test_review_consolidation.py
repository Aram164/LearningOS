"""Register completeness: every finding has owner/callers/tests/disposition."""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_register_complete():
    data = yaml.safe_load((ROOT / "system/contracts/review-consolidation.yaml").read_text())
    assert data["schema_version"] == 1
    ids = [f["id"] for f in data["findings"]]
    assert len(ids) == len(set(ids)) == 42
    for f in data["findings"]:
        for field in ("source", "root_cause", "owner", "affected_callers",
                      "regression_tests", "disposition", "installed_status"):
            assert f[field], (f["id"], field)
        assert (ROOT / f["regression_tests"]).exists(), f["id"]
