"""Negative evidence for the shared hosted-suite completeness proof."""
from __future__ import annotations

import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def suite(tmp_path, monkeypatch):
    import check_shard_completeness as checker

    monkeypatch.chdir(tmp_path)
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/test_example.py").write_text("")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"legs": {"one": ["tests/test_example.py"]}}))
    ids = ["tests/test_example.py::test_one", "tests/test_example.py::TestGroup::test_two[x.y]"]
    monkeypatch.setattr(checker.subprocess, "run", lambda *a, **kw:
                        subprocess.CompletedProcess(a, 0, "\n".join(ids) + "\n2 tests collected\n", ""))
    junit = tmp_path / "junit"
    junit.mkdir()
    return checker, manifest, junit


def _results(junit, cases):
    root = ET.Element("testsuite")
    for classname, name, status in cases:
        row = ET.SubElement(root, "testcase", classname=classname, name=name)
        if status:
            ET.SubElement(row, status)
    ET.ElementTree(root).write(junit / "junit-one.xml")


GOOD = [("tests.test_example", "test_one", None),
        ("tests.test_example.TestGroup", "test_two[x.y]", "skipped")]


def test_exact_identities_pass_with_skips_visible(suite):
    checker, manifest, junit = suite
    _results(junit, GOOD)
    assert "2 executed test IDs" in checker.check(junit, manifest)
    assert "1 skipped" in checker.check(junit, manifest)


@pytest.mark.parametrize("cases,reason", [
    ([GOOD[0], GOOD[0]], "identities differ"),
    ([GOOD[0]], "identities differ"),
    ([GOOD[0], ("tests.test_example", "test_unknown", None)], "no collected node ID"),
    ([GOOD[0], (*GOOD[1][:2], "failure")], "failing testcase"),
    ([GOOD[0], (*GOOD[1][:2], "error")], "failing testcase"),
])
def test_invalid_evidence_refuses(suite, cases, reason):
    checker, manifest, junit = suite
    _results(junit, cases)
    with pytest.raises(SystemExit, match=reason):
        checker.check(junit, manifest)


def test_missing_junit_refuses(suite):
    checker, manifest, junit = suite
    with pytest.raises(SystemExit, match="identities differ"):
        checker.check(junit, manifest)


def test_audit_filename_collision_preserves_the_first_log(tmp_path):
    import check_shard_completeness as checker

    first, second, merged = [tmp_path / p for p in ("first", "second", "merged")]
    for path in (first, second, merged):
        path.mkdir()
    (first / "same.jsonl").write_text("first evidence\n")
    (second / "same.jsonl").write_text("second evidence\n")
    checker.copy_audit_logs(first, merged)
    with pytest.raises(FileExistsError):
        checker.copy_audit_logs(second, merged)
    assert (merged / "same.jsonl").read_text() == "first evidence\n"


@pytest.mark.parametrize("name", ["validate.yml", "release-pair.yml"])
def test_both_workflows_use_the_shared_identity_and_collision_checks(name):
    root = Path(__file__).resolve().parents[1]
    workflow = yaml.safe_load((root / ".github/workflows" / name).read_text())
    runs = [step.get("run", "") for job in workflow["jobs"].values() for step in job["steps"]]
    assert any("tools/check_shard_completeness.py --junit-dir ../junit-in" in run for run in runs)
    assert any("copy_audit_logs(parts[leg][2], audit)" in run for run in runs)
