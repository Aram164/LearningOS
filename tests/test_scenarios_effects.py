"""Effect scenarios: characterization recordings over a fresh world (SPEC §5).

Parametrized over every (case file, case) in ``tests/scenarios/cases/``.
Without ``LOS_RECORD_SCENARIOS=1`` each case compares against its recording
in ``tests/scenarios/recorded/<operation>/<case-id>.json``; with it, the
recording is written instead. A session may record only for the operations
its kickoff authorizes.

After each case, A2 runs in report mode: ``reconcile`` over the recording
prints violations without failing (the failing comes later, with a2-mode).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
import scenario_harness

CASE_FILES = sorted(scenario_harness.CASES_DIR.glob("*.yaml")) \
    if scenario_harness.CASES_DIR.is_dir() else []


def _collect():
    params = []
    for path in CASE_FILES:
        file_data = scenario_harness.load_case_file(path)
        operation = file_data["operation"]
        for case in file_data.get("cases", []):
            merged = {"fixture": file_data.get("fixture", "rich_world"),
                      "observations": file_data["observations"],
                      "fixture_mtime": file_data.get(
                          "fixture_mtime",
                          scenario_harness.FIXTURE_MTIME_DEFAULT),
                      **case}
            params.append(pytest.param(
                operation, merged,
                id=f"{operation}::{case['id']}"))
    return params


@pytest.fixture(autouse=True)
def _berlin_time(monkeypatch):
    """Pin TZ=Europe/Berlin in-process, restoring afterwards (SPEC §0)."""
    old = os.environ.get("TZ")
    monkeypatch.setenv("TZ", "Europe/Berlin")
    if hasattr(time, "tzset"):
        time.tzset()
    yield
    if old is None:
        os.environ.pop("TZ", None)
    else:
        os.environ["TZ"] = old
    if hasattr(time, "tzset"):
        time.tzset()


@pytest.mark.parametrize("operation,case", _collect())
def test_scenario_effects(operation: str, case: dict, tmp_path: Path):
    workdir = tmp_path / "case"
    workdir.mkdir()
    if case.get("kind") == "sequence":
        actual = scenario_harness.run_sequence(case, operation, workdir)
    else:
        actual = scenario_harness.run_case(case, operation, workdir)
    for violation in scenario_harness.reconcile_recorded(actual):
        print(f"A2 report: {violation}")
    recording_path = (scenario_harness.RECORDED_DIR / operation
                      / f"{case['id']}.json")
    if os.environ.get("LOS_RECORD_SCENARIOS") == "1":
        recording_path.parent.mkdir(parents=True, exist_ok=True)
        recording_path.write_text(scenario_harness.pretty(actual),
                                  encoding="utf-8")
        print(f"recorded {operation}/{case['id']}")
        return
    assert recording_path.is_file(), (
        f"no recording for {operation}/{case['id']}: "
        f"{recording_path} — record it only when the kickoff authorizes it")
    recorded = json.loads(recording_path.read_text(encoding="utf-8"))
    diff = scenario_harness.compare(recorded, actual)
    assert diff is None, (
        f"behaviour changed for {operation}/{case['id']}:\n{diff}")


def _bare_recording(stdout_json: dict, **sections) -> dict:
    """A minimal recording shape for normalize() regression tests."""
    recording = {
        "exit": 0,
        "stdout": json.dumps(stdout_json),
        "stderr": "",
        "stdout_json": stdout_json,
        "receipts": [],
        "revisions_changed": {},
        "idempotency_changed": {},
        "session_ledger_changed": None,
    }
    recording.update(sections)
    return recording


def test_normalize_keeps_authored_text_values_distinct(tmp_path):
    """C2: authored text is never an identity, and compare() reports it."""
    first = scenario_harness.normalize(
        _bare_recording({"ok": True, "note": "scenario-original"}), tmp_path)
    second = scenario_harness.normalize(
        _bare_recording({"ok": True, "note": "scenario-corrupted"}), tmp_path)
    assert first != second
    assert "scenario-original" in json.dumps(first)
    assert "scenario-corrupted" in json.dumps(second)
    diff = scenario_harness.compare(first, second)
    assert diff is not None
    assert "scenario-original" in diff and "scenario-corrupted" in diff


def test_normalize_keeps_transaction_shaped_authored_text_distinct(tmp_path):
    """C8: transaction-shaped authored text is never an identity."""
    first = scenario_harness.normalize(
        _bare_recording(
            {"ok": True, "note": "transaction-20261001-090000-001"}),
        tmp_path)
    second = scenario_harness.normalize(
        _bare_recording(
            {"ok": True, "note": "transaction-20261001-090000-002"}),
        tmp_path)
    assert first != second
    assert "transaction-20261001-090000-001" in json.dumps(first)
    assert "transaction-20261001-090000-002" in json.dumps(second)
    assert "TX1" not in json.dumps(first)
    assert "TX1" not in json.dumps(second)
    diff = scenario_harness.compare(first, second)
    assert diff is not None
    assert "transaction-20261001-090000-001" in diff
    assert "transaction-20261001-090000-002" in diff


def test_normalize_keeps_latency_shaped_authored_text_distinct(tmp_path):
    """C8: latency-shaped authored text is never an elapsed time."""
    first = scenario_harness.normalize(
        _bare_recording({"ok": True, "note": "latency (1.1s)"}), tmp_path)
    second = scenario_harness.normalize(
        _bare_recording({"ok": True, "note": "latency (2.2s)"}), tmp_path)
    assert first != second
    assert "latency (1.1s)" in json.dumps(first)
    assert "latency (2.2s)" in json.dumps(second)
    diff = scenario_harness.compare(first, second)
    assert diff is not None
    assert "latency (1.1s)" in diff and "latency (2.2s)" in diff


def test_normalize_discovers_transaction_ids_from_declared_keys(tmp_path):
    """C8 positive: declared keys and each receipt's own id normalize."""
    tx1 = "transaction-20261001-090000-001"
    tx2 = "transaction-20261001-090000-002"
    tx3 = "transaction-20261001-090000-003"
    tx4 = "transaction-20261001-090000-004"
    authored = "transaction-20261001-090000-005"
    recording = _bare_recording(
        {"ok": True,
         "transaction_id": tx1,
         "receipt_path": f"operations/transactions/{tx1}.yaml",
         "parent_transaction_id": tx2,
         "receipt_id": tx3,
         "note": f"authored {authored} stays"},
        stderr=f"see {tx4}\n",
        receipts=[{"id": tx1, "type": "transaction-receipt"},
                  {"id": tx4, "type": "transaction-receipt"}])
    normalized = scenario_harness.normalize(recording, tmp_path)
    assert normalized["stdout_json"]["transaction_id"] == "TX1"
    assert (normalized["stdout_json"]["receipt_path"]
            == "operations/transactions/TX1.yaml")
    assert normalized["stdout_json"]["parent_transaction_id"] == "TX2"
    assert normalized["stdout_json"]["receipt_id"] == "TX3"
    assert normalized["receipts"][0]["id"] == "TX1"
    assert normalized["receipts"][1]["id"] == "TX4"
    assert normalized["stderr"] == "see TX4\n"
    assert tx4 not in json.dumps(normalized)
    assert normalized["stdout_json"]["note"] == f"authored {authored} stays"
    assert "TX5" not in json.dumps(normalized)


def test_normalize_redacts_only_validator_summary_elapsed(tmp_path):
    """C8 positive: only the validator's summary form redacts elapsed time."""
    summary = ("0 error(s), 10 warning(s) — OK (0.2s); warning list: "
               "generated/reports/validation-report.md")
    recording = _bare_recording(
        {"ok": True, "validation": summary, "note": "latency (1.1s)"})
    normalized = scenario_harness.normalize(recording, tmp_path)
    assert normalized["stdout_json"]["validation"] == summary.replace(
        "(0.2s)", "(Xs)")
    assert normalized["stdout_json"]["note"] == "latency (1.1s)"


def test_normalize_orders_a_ledger_only_snapshot(tmp_path):
    """C5: a snapshot seen only in a ledger normalizes, after text ones."""
    text_snap = "sha256:" + "ab" * 32
    ledger_snap = "sha256:" + "cd" * 32
    recording = _bare_recording(
        {"ok": True, "snapshot_after": text_snap},
        revisions_changed={"before": None,
                           "after": {"snapshot_after": ledger_snap}})
    normalized = scenario_harness.normalize(recording, tmp_path)
    assert normalized["stdout_json"]["snapshot_after"] == "SNAP1"
    assert (normalized["revisions_changed"]["after"]["snapshot_after"]
            == "SNAP2")


def test_normalize_replaces_learningos_container(tmp_path):
    """Amendment (y): a sibling path normalizes, ROOT/MATERIALS unchanged."""
    container = tmp_path / "LearningOS"
    root = container / "repository"
    sibling = str(container / "obsidian-ui" / "x")
    recording = _bare_recording(
        {"sibling": sibling},
        stdout=f"root {root} sibling {sibling}",
        stderr=f"materials {container / 'materials'} sibling {sibling}")
    normalized = scenario_harness.normalize(recording, root)
    assert normalized["stdout_json"]["sibling"] == "<LEARNINGOS>/obsidian-ui/x"
    assert normalized["stdout"] == (
        "root <ROOT> sibling <LEARNINGOS>/obsidian-ui/x")
    assert normalized["stderr"] == (
        "materials <MATERIALS> sibling <LEARNINGOS>/obsidian-ui/x")


def _git_repo_with_commits(path: Path, count: int) -> list[str]:
    """A git repo with count real commits; returns their SHAs (D7)."""
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "tests@example.invalid"],
                   cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Tests"],
                   cwd=path, check=True)
    shas = []
    for index in range(count):
        (path / f"file-{index}.txt").write_text(
            f"commit {index}\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=path, check=True)
        subprocess.run(["git", "commit", "-qm", f"commit {index}"],
                       cwd=path, check=True)
        shas.append(subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=path, check=True,
            capture_output=True, text=True).stdout.strip())
    return shas


def _v3_unpushed(sha, **overrides):
    """A recorded v3 committed_unpushed envelope (D7 controls)."""
    envelope = {"schema_version": 3, "session_id": "channel:operator",
                "version": 1, "state": "committed_unpushed", "paths": {},
                "review": None, "commit_sha": sha}
    envelope.update(overrides)
    return envelope


def test_normalize_maps_evidence_bound_commit_sha(tmp_path):
    """D7 positive: a git-backed v3 SHA maps in ledger and stderr."""
    (sha,) = _git_repo_with_commits(tmp_path, 1)
    recording = _bare_recording(
        {"ok": True},
        stderr=(f"los: INVALID_REQUEST: already committed as {sha}; "
                "use --push or --close\n"),
        session_ledger_changed={"before": None,
                                "after": _v3_unpushed(sha)})
    first = scenario_harness.normalize(recording, tmp_path)
    assert (first["session_ledger_changed"]["after"]["commit_sha"]
            == "SHA1")
    assert first["stderr"] == (
        "los: already committed as SHA1; use --push or --close\n")
    again = scenario_harness.normalize(recording, tmp_path)
    assert again == first


def test_normalize_rejects_unbacked_commit_sha(tmp_path):
    """D7: a 40-hex naming no fixture commit never maps, ledger or stream."""
    ghost = "ab" * 20
    _git_repo_with_commits(tmp_path, 1)
    recording = _bare_recording(
        {"ok": True},
        stderr=(f"los: already committed as {ghost}; use --push or "
                "--close\n"),
        session_ledger_changed={"before": None,
                                "after": _v3_unpushed(ghost)})
    normalized = scenario_harness.normalize(recording, tmp_path)
    assert (normalized["session_ledger_changed"]["after"]["commit_sha"]
            == ghost)
    assert ghost in normalized["stderr"]
    assert "SHA1" not in json.dumps(normalized)


def test_normalize_rejects_malformed_commit_sha(tmp_path):
    """D7: null, mistyped, misshapen or mis-stated SHAs never map."""
    (sha,) = _git_repo_with_commits(tmp_path, 1)
    bad_values = ["not-a-sha", sha[:39], sha + "0", sha.upper(), None,
                  12345]
    for bad in bad_values:
        recording = _bare_recording(
            {"ok": True},
            session_ledger_changed={"before": None,
                                    "after": _v3_unpushed(bad)})
        normalized = scenario_harness.normalize(recording, tmp_path)
        assert (normalized["session_ledger_changed"]["after"]["commit_sha"]
                == bad), bad
        assert "SHA1" not in json.dumps(normalized), bad
    for envelope in (_v3_unpushed(sha, state="recording"),
                     _v3_unpushed(sha, schema_version=2),
                     {"schema_version": 3, "session_id": "channel:operator",
                      "version": 1, "state": "committed_unpushed",
                      "paths": {}, "review": None}):
        recording = _bare_recording(
            {"ok": True},
            session_ledger_changed={"before": None, "after": envelope})
        normalized = scenario_harness.normalize(recording, tmp_path)
        assert (normalized["session_ledger_changed"]["after"].get(
            "commit_sha") == envelope.get("commit_sha"))
        assert "SHA1" not in json.dumps(normalized)


def test_normalize_preserves_unrelated_hex(tmp_path):
    """D7: only the bound ledger value and refusal template map."""
    (sha,) = _git_repo_with_commits(tmp_path, 1)
    other = "cd" * 20
    row_digest = "ef" * 32
    recording = _bare_recording(
        {"ok": True, "note_body": f"mentions {sha} in prose",
         "custom_field": other},
        stdout=f"op returned {sha}\n",
        stderr=f"saved note {sha}\n",
        session_ledger_changed={
            "before": None,
            "after": _v3_unpushed(
                sha, paths={"work/x.md": {"channel": "operator",
                                          "recorded_at":
                                          "2026-10-01T07:00:00+00:00",
                                          "sha256": row_digest,
                                          "state": "file"}})})
    normalized = scenario_harness.normalize(recording, tmp_path)
    assert (normalized["session_ledger_changed"]["after"]["commit_sha"]
            == "SHA1")
    assert sha in normalized["stdout_json"]["note_body"]
    assert normalized["stdout_json"]["custom_field"] == other
    assert sha in normalized["stdout"]
    assert normalized["stderr"] == f"saved note {sha}\n"
    row = normalized["session_ledger_changed"]["after"]["paths"][
        "work/x.md"]
    assert row["sha256"] == row_digest


def test_normalize_numbers_distinct_commits_distinctly(tmp_path):
    """D7: two backed commits keep distinct stable tokens across steps."""
    sha_a, sha_b = _git_repo_with_commits(tmp_path, 2)
    assert sha_a != sha_b
    recording = {
        "steps": [
            _bare_recording(
                {"ok": True},
                session_ledger_changed={
                    "before": None, "after": _v3_unpushed(sha_a)}),
            _bare_recording(
                {"ok": True},
                stderr=(f"los: already committed as {sha_b}; use --push "
                        "or --close\n"),
                session_ledger_changed={
                    "before": _v3_unpushed(sha_a),
                    "after": _v3_unpushed(sha_b)}),
        ]
    }
    normalized = scenario_harness.normalize(recording, tmp_path)
    first, second = normalized["steps"]
    assert first["session_ledger_changed"]["after"]["commit_sha"] == "SHA1"
    assert second["session_ledger_changed"]["before"]["commit_sha"] == "SHA1"
    assert second["session_ledger_changed"]["after"]["commit_sha"] == "SHA2"
    assert "already committed as SHA2;" in second["stderr"]
    assert sha_a not in json.dumps(normalized)
    assert sha_b not in json.dumps(normalized)


def test_normalize_rejects_incorrect_stream_binding(tmp_path):
    """D7: a refusal naming an unbound SHA stays raw; the ledger maps."""
    (sha,) = _git_repo_with_commits(tmp_path, 1)
    stranger = "ab" * 20
    recording = _bare_recording(
        {"ok": True},
        stderr=(f"los: already committed as {stranger}; use --push or "
                "--close\n"),
        session_ledger_changed={"before": None,
                                "after": _v3_unpushed(sha)})
    normalized = scenario_harness.normalize(recording, tmp_path)
    assert (normalized["session_ledger_changed"]["after"]["commit_sha"]
            == "SHA1")
    assert stranger in normalized["stderr"]
    assert "SHA1" not in normalized["stderr"]


def test_failed_push_live_runs_compare_equal(tmp_path):
    """D7 end to end: two live failed-push runs normalize identically."""
    doc = scenario_harness.load_case_file(
        scenario_harness.CASES_DIR / "cli.session-end.yaml")
    bare = next(item for item in doc["cases"] if item["id"] == "failed-push")
    case = {"fixture": doc.get("fixture", "rich_world"),
            "observations": doc["observations"],
            "fixture_mtime": doc.get(
                "fixture_mtime", scenario_harness.FIXTURE_MTIME_DEFAULT),
            **bare}
    first = scenario_harness.run_sequence(case, doc["operation"],
                                          tmp_path / "a")
    second = scenario_harness.run_sequence(case, doc["operation"],
                                           tmp_path / "b")
    assert "SHA1" in json.dumps(first)
    assert first == second


def _subparser(command: str):
    sys.path.insert(0, str(scenario_harness.REPO_ROOT / "tools"))
    try:
        import los
        from learning_os.store.contracts.payloads import subparsers
    finally:
        del sys.path[0]
    return subparsers(los.build_parser())[command]


def test_request_rendering_round_trips():
    """C3: each field renders by its own argparse action and parses back."""
    root = scenario_harness.REPO_ROOT
    request = {"unit_id": "unit-demo-l01",
               "selected": ["stage-demo", "stage-demo-pending"],
               "approve": True}
    argv = scenario_harness.request_to_argv("review.apply", request, root)
    assert argv == ["unit-demo-l01", "--selected", "stage-demo",
                   "stage-demo-pending", "--approve"]
    parsed = _subparser("shelving-apply").parse_args(argv)
    assert parsed.unit_id == request["unit_id"]
    assert parsed.selected == request["selected"]
    assert parsed.approve is True
    request = {"claim_ids": ["claim-a", "claim-b"],
               "expected_revision": ["unit-demo-l01=3",
                                     "study-map-demo-l01=1"]}
    argv = scenario_harness.request_to_argv("lineage.restamp", request, root)
    assert argv == ["--claim-ids", "claim-a", "claim-b",
                   "--expected-revision", "unit-demo-l01=3",
                   "--expected-revision", "study-map-demo-l01=1"]
    parsed = _subparser("lineage-restamp").parse_args(argv)
    assert parsed.claim_ids == request["claim_ids"]
    assert parsed.expected_revision == request["expected_revision"]
    request = {"goal_id": ["lineage-stale:claim-1",
                           "evidence-superseded:obs-2"],
               "reject": True}
    argv = scenario_harness.request_to_argv("cli.goal", request, root)
    assert argv == ["lineage-stale:claim-1", "evidence-superseded:obs-2",
                   "--reject"]
    parsed = _subparser("goal").parse_args(argv)
    assert parsed.goal_id == request["goal_id"]
    assert parsed.reject is True
