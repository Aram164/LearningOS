"""`program.semester.update`: the term boundary as a governed write.

The current semester used to be changed by editing the program record by
hand: no receipt, no snapshot, no revision, no conflict detection, and
nothing that told the operator what the change did to the interface
(LearningOS #2). These tests pin the properties that make it a governed
write rather than a hand edit:

* exactly one file is written — the program record — and the receipt says so;
* the previous semester becomes ``previous`` and no semester record is
  dropped: history is kept;
* exam outcomes, registrations, learner state and study work are untouched,
  because they live in other records;
* the term never rolls forward on its own: the reviewed package names the
  semester that becomes current;
* the report says what the interface will show, and what stays as it was.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from gateway_helpers import approved_v2_call, file_sha256

from learning_os.store.revisions import artifact_revision

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def repo(mini_repo: Path) -> Path:
    from repo_builders import add_curriculum

    add_curriculum(mini_repo)
    return mini_repo


def _package(program_id: str = "program-bachelors", *,
             semester_id: str = "semester-wise-2026",
             title: str = "WiSe 2026/27",
             order: int = 2) -> str:
    return (
        f"program_id: {program_id}\n"
        "semester:\n"
        f"  id: {semester_id}\n"
        f"  title: {title}\n"
        f"  order: {order}\n"
    )


def _write(root: Path, name: str, text: str) -> Path:
    """The reviewed draft, outside the repository: an input, not a write."""
    path = root.parent / "drafts" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _payload(path: Path) -> dict:
    return {"file": str(path), "file_sha256": file_sha256(path)}


def _result(proc) -> dict:
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:  # pragma: no cover - diagnostics only
        raise AssertionError(
            f"expected JSON, got exit {proc.returncode}\n"
            f"stdout: {proc.stdout}\nstderr: {proc.stderr}") from exc


def _semesters(root: Path) -> list[dict]:
    program = yaml.safe_load(
        (root / "curriculum/programs/program-bachelors.yaml")
        .read_text(encoding="utf-8"))
    return program["semesters"]


# --------------------------------------------------------------------------
# the write
# --------------------------------------------------------------------------

def test_the_update_writes_only_the_program_record(repo: Path):
    package = _write(repo, "semester.yaml", _package())
    proc = approved_v2_call(
        repo, capability="program.semester.update",
        payload=_payload(package), artifact_ids=["program-bachelors"],
        idempotency_key="semester-turn-1")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    result = _result(proc)
    assert result["ok"] is True
    receipt = yaml.safe_load(
        (repo / result["receipt_path"]).read_text(encoding="utf-8"))
    assert [row["path"] for row in receipt["writes"]] == [
        "curriculum/programs/program-bachelors.yaml",
    ]
    assert receipt["capability"] == "program.semester.update"
    assert receipt["artifact_revisions"]["program-bachelors"] == {
        "before": 0, "after": 1}
    assert artifact_revision(repo, "program-bachelors") == 1


def test_the_previous_semester_becomes_previous_and_history_is_kept(repo: Path):
    package = _write(repo, "semester.yaml", _package())
    proc = approved_v2_call(
        repo, capability="program.semester.update",
        payload=_payload(package), artifact_ids=["program-bachelors"],
        idempotency_key="semester-turn-2")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    rows = {row["id"]: row for row in _semesters(repo)}
    assert set(rows) == {"semester-sose-2026", "semester-wise-2026"}
    assert rows["semester-sose-2026"]["status"] == "previous"
    assert rows["semester-wise-2026"]["status"] == "current"
    assert rows["semester-wise-2026"]["title"] == "WiSe 2026/27"


def test_the_update_preserves_everything_it_does_not_own(repo: Path):
    """Exam outcomes, registrations, learner state and study work stay."""
    module = repo / "curriculum/modules/module-demo/module.yaml"
    study_map = repo / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
    unit = repo / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    before = {path: path.read_bytes() for path in (module, study_map, unit)}
    package = _write(repo, "semester.yaml", _package())
    proc = approved_v2_call(
        repo, capability="program.semester.update",
        payload=_payload(package), artifact_ids=["program-bachelors"],
        idempotency_key="semester-turn-3")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    for path, content in before.items():
        assert path.read_bytes() == content, path
    # The module record still carries its own attempts and sittings.
    record = yaml.safe_load(module.read_text(encoding="utf-8"))
    assert record["attempts"]
    assert record["examination"]["sittings"]
    assert record["semester"] == "sose-2026"


def test_the_report_names_the_term_before_and_after(repo: Path):
    package = _write(repo, "semester.yaml", _package())
    proc = approved_v2_call(
        repo, capability="program.semester.update",
        payload=_payload(package), artifact_ids=["program-bachelors"],
        idempotency_key="semester-turn-4")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    result = _result(proc)["result"]
    assert result["current_semester_before"]["id"] == "semester-sose-2026"
    assert result["current_semester_after"]["id"] == "semester-wise-2026"
    assert result["semester_added"] is True
    # The module list is not gated by the term, so it does not change.
    assert result["module_listing"]["changed"] is False
    assert result["module_listing"]["listed_module_ids"] == ["module-demo"]


# --------------------------------------------------------------------------
# the refusals
# --------------------------------------------------------------------------

def test_an_unknown_program_refuses(repo: Path):
    package = _write(repo, "semester.yaml", _package("program-unknown"))
    proc = approved_v2_call(
        repo, capability="program.semester.update",
        payload=_payload(package), artifact_ids=["program-bachelors"],
        idempotency_key="semester-unknown")
    assert proc.returncode != 0
    assert "program-unknown" in _result(proc)["error"]["message"]
    assert _semesters(repo)[0]["status"] == "current"


def test_the_already_current_semester_refuses(repo: Path):
    package = _write(
        repo, "semester.yaml",
        _package(semester_id="semester-sose-2026", title="SoSe 2026", order=1))
    proc = approved_v2_call(
        repo, capability="program.semester.update",
        payload=_payload(package), artifact_ids=["program-bachelors"],
        idempotency_key="semester-no-change")
    assert proc.returncode != 0
    assert "nothing to change" in _result(proc)["error"]["message"]


def test_a_semester_without_an_id_refuses(repo: Path):
    package = _write(repo, "semester.yaml",
                     "program_id: program-bachelors\nsemester:\n"
                     "  title: WiSe 2026/27\n  order: 2\n")
    proc = approved_v2_call(
        repo, capability="program.semester.update",
        payload=_payload(package), artifact_ids=["program-bachelors"],
        idempotency_key="semester-bad")
    assert proc.returncode != 0
    assert "semester id" in _result(proc)["error"]["message"]


def test_a_direct_cli_apply_is_refused(repo: Path):
    """The capability is applied as a gateway envelope, never by hand."""
    package = _write(repo, "semester.yaml", _package())
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "los.py"), "--root", str(repo),
         "program-semester-update", "--file", str(package),
         "--file-sha256", file_sha256(package),
         "--expected-snapshot", "sha256:" + "0" * 64],
        capture_output=True, text=True)
    assert proc.returncode != 0
    assert "GatewayEnvelopeV2" in proc.stderr
    assert _semesters(repo)[0]["status"] == "current"


def test_an_identical_retry_replays_the_original_success(repo: Path):
    from gateway_helpers import approved_v2_envelope, run_v2_capability

    package = _write(repo, "semester.yaml", _package())
    envelope = approved_v2_envelope(
        repo, capability="program.semester.update", payload=_payload(package),
        artifact_ids=["program-bachelors"], idempotency_key="semester-replay")
    first = run_v2_capability(repo, envelope)
    assert first.returncode == 0, first.stdout + first.stderr
    second = run_v2_capability(repo, envelope)
    assert second.returncode == 0, second.stdout + second.stderr
    assert _result(second)["transaction_id"] == _result(first)["transaction_id"]
    assert _result(second).get("replayed") is True
    assert artifact_revision(repo, "program-bachelors") == 1


# --------------------------------------------------------------------------
# the preflight
# --------------------------------------------------------------------------

def test_the_check_reports_the_term_change_and_the_listing(repo: Path):
    package = _write(repo, "semester.yaml", _package())
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "los.py"), "--root", str(repo),
         "program-semester-update", "--file", str(package), "--check"],
        capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["check"] is True
    assert payload["current_semester_before"]["id"] == "semester-sose-2026"
    assert payload["current_semester_after"]["id"] == "semester-wise-2026"
    assert payload["expected_write_paths"] == [
        "curriculum/programs/program-bachelors.yaml"]
    # Nothing was written.
    assert _semesters(repo)[0]["status"] == "current"
