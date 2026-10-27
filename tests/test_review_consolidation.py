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
        assert (ROOT / f["regression_tests"]).is_file(), f["id"]
        assert (ROOT / f["owner_path"]).is_file(), f["id"]
        assert isinstance(f["caller_paths"], list) and f["caller_paths"], f["id"]
        assert all((ROOT / path).is_file() for path in f["caller_paths"]), f["id"]
        assert f["hosted_ci_status"] == f["installed_status"] == "external-promotion-record"
    # Distinct inherited defects must link their actual owning suites rather
    # than an unrelated runner test whose existence alone would pass.
    by_id = {f["id"]: f for f in data["findings"]}
    assert by_id["G31"]["regression_tests"] == "tests/test_claim_status_audits.py"
    assert by_id["O41"]["regression_tests"] == "tests/test_note_evidence.py"
    assert "../obsidian-ui/src/main.ts" in by_id["R51"]["caller_paths"]
