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


@pytest.mark.parametrize("status,reason", [
    (None, None),
    ("skipped", "skipped testcase"),
    ("failure", "failing testcase"),
    ("error", "failing testcase"),
])
def test_zero_skip_junit_accepts_only_clean_nonempty_runs(tmp_path, status, reason):
    import check_shard_completeness as checker

    xml_path = tmp_path / "seatbelt.xml"
    root = ET.Element("testsuite")
    row = ET.SubElement(root, "testcase", classname="tests.test_study_launch", name="test_one")
    if status:
        ET.SubElement(row, status)
    ET.ElementTree(root).write(xml_path)
    if reason is None:
        assert "1 testcases passed, 0 skipped" in checker.check_zero_skip_junit(xml_path)
    else:
        with pytest.raises(SystemExit, match=reason):
            checker.check_zero_skip_junit(xml_path)


def test_zero_skip_junit_refuses_missing_or_empty_xml(tmp_path):
    import check_shard_completeness as checker

    with pytest.raises(SystemExit, match="missing zero-skip JUnit XML"):
        checker.check_zero_skip_junit(tmp_path / "absent.xml")
    empty = tmp_path / "empty.xml"
    ET.ElementTree(ET.Element("testsuite")).write(empty)
    with pytest.raises(SystemExit, match="zero testcases"):
        checker.check_zero_skip_junit(empty)


def test_mandatory_prefix_passes_when_unrelated_tests_skip(suite):
    checker, manifest, junit = suite
    _results(junit, GOOD)
    out = checker.check(
        junit,
        manifest,
        require_passed_prefixes=["tests/test_example.py::test_one"],
    )
    assert "1/1 mandatory witnesses passed" in out
    assert "0 allowed mandatory skips" in out


def test_mandatory_prefix_refuses_when_mandatory_test_skips(suite):
    checker, manifest, junit = suite
    _results(junit, GOOD)
    with pytest.raises(SystemExit, match="mandatory witness skipped: tests/test_example.py::TestGroup::test_two\\[x\\.y\\]"):
        checker.check(
            junit,
            manifest,
            require_passed_prefixes=["tests/test_example.py::"],
        )


def test_mandatory_prefix_refuses_zero_collected_matches(suite):
    checker, manifest, junit = suite
    _results(junit, GOOD)
    with pytest.raises(SystemExit, match="matched zero collected tests"):
        checker.check(
            junit,
            manifest,
            require_passed_prefixes=["tests/test_nonexistent.py::"],
        )


def test_allow_skip_permits_only_named_mandatory_witness(suite, monkeypatch):
    checker, manifest, junit = suite
    _results(junit, GOOD)
    out = checker.check(
        junit,
        manifest,
        require_passed_prefixes=["tests/test_example.py::"],
        allow_skips={"tests/test_example.py::TestGroup::test_two[x.y]": "known fixture condition"},
    )
    assert "1 allowed mandatory skips" in out
    assert "1/2 mandatory witnesses passed" in out

    monkeypatch.setattr(
        checker.sys,
        "argv",
        [
            "check_shard_completeness.py",
            "--junit-dir", str(junit),
            "--manifest", str(manifest),
            "--require-passed-prefix", "tests/test_example.py::",
            "--allow-skip", "tests/test_example.py::TestGroup::test_two[x.y]=known reason",
        ],
    )
    assert checker.main() == 0

    with pytest.raises(SystemExit, match="expected NODE_ID=REASON"):
        checker._parse_allow_skip(["missing-equals"])


@pytest.mark.parametrize("name", ["validate.yml", "release-pair.yml"])
def test_both_workflows_use_the_shared_identity_and_collision_checks(name):
    import check_shard_completeness as checker

    root = Path(__file__).resolve().parents[1]
    workflow = yaml.safe_load((root / ".github/workflows" / name).read_text())
    runs = [step.get("run", "") for job in workflow["jobs"].values() for step in job["steps"]]
    assert any(
        "tools/check_shard_completeness.py --junit-dir ../junit-in "
        "--zero-skip-junit ../seatbelt-in/seatbelt.xml" in run
        for run in runs
    )
    for prefix in checker.MANDATORY_PAIRED_WITNESS_PREFIXES:
        assert any(
            f"--require-passed-prefix {prefix}" in run
            and "tools/check_shard_completeness.py" in run
            for run in runs
        ), f"{name} missing --require-passed-prefix {prefix}"
    assert any("copy_audit_logs(parts[leg][2], audit)" in run for run in runs)


def test_mandatory_paired_prefixes_match_workflows_and_system_check(tmp_path, monkeypatch):
    import check_shard_completeness as checker

    root = Path(__file__).resolve().parents[1]
    assert set(checker.MANDATORY_PAIRED_WITNESS_PREFIXES) == {
        "tests/test_ui_phase3_live_writes.py::",
        "tests/test_ui_gateway_recovery.py::",
        "tests/test_operations_gate.py::",
        "tests/test_contract_differential.py::",
    }
    makefile = (root / "Makefile").read_text(encoding="utf-8")
    section = makefile.split("system-check:", 1)[1]
    assert "tools/generate.py" in section
    assert "unset PYTEST_ADDOPTS" in section
    assert "tools/check_shard_completeness.py" in section
    assert "--require-mandatory-paired" in section

    for rel in (
        "tests/test_ui_phase3_live_writes.py",
        "tests/test_ui_gateway_recovery.py",
        "tests/test_operations_gate.py",
        "tests/test_contract_differential.py",
    ):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("# stub\n", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({
        "legs": {"all": [
            "tests/test_ui_phase3_live_writes.py",
            "tests/test_ui_gateway_recovery.py",
            "tests/test_operations_gate.py",
            "tests/test_contract_differential.py",
        ]},
        "node_shards": {},
    }), encoding="utf-8")
    ids = [
        "tests/test_ui_phase3_live_writes.py::test_live",
        "tests/test_ui_gateway_recovery.py::test_gw",
        "tests/test_operations_gate.py::test_ops",
        "tests/test_contract_differential.py::test_diff",
    ]
    collected = "\n".join(ids)
    junit = tmp_path / "junit"
    junit.mkdir()
    (junit / "junit-system-check.xml").write_text(
        "<testsuite>"
        '<testcase classname="tests.test_ui_phase3_live_writes" name="test_live"/>'
        '<testcase classname="tests.test_ui_gateway_recovery" name="test_gw"/>'
        '<testcase classname="tests.test_operations_gate" name="test_ops"/>'
        '<testcase classname="tests.test_contract_differential" name="test_diff"><skipped/></testcase>'
        "</testsuite>",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PYTEST_ADDOPTS", "-k nope")
    seen_envs: list[dict[str, str]] = []

    def _fake_collect(*a, **kw):
        seen_envs.append(dict(kw.get("env") or {}))
        return subprocess.CompletedProcess(a, 0, collected, "")

    monkeypatch.setattr(checker.subprocess, "run", _fake_collect)
    monkeypatch.setattr(
        checker.sys,
        "argv",
        [
            "check_shard_completeness.py",
            "--junit-dir", str(junit),
            "--manifest", str(manifest),
            "--require-mandatory-paired",
        ],
    )
    with pytest.raises(
        SystemExit,
        match="mandatory witness skipped: tests/test_contract_differential.py::test_diff",
    ):
        checker.main()

    (junit / "junit-system-check.xml").write_text(
        "<testsuite>"
        '<testcase classname="tests.test_ui_phase3_live_writes" name="test_live"/>'
        '<testcase classname="tests.test_ui_gateway_recovery" name="test_gw"/>'
        '<testcase classname="tests.test_operations_gate" name="test_ops"/>'
        '<testcase classname="tests.test_contract_differential" name="test_diff"/>'
        "</testsuite>",
        encoding="utf-8",
    )
    assert checker.main() == 0
    assert seen_envs and all("PYTEST_ADDOPTS" not in e for e in seen_envs)
