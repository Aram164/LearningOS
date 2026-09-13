"""F05: one return-to-work destination, shared by the CLI and the app.

Before 2026-09-13 nothing in the system wrote `curriculum/resume.yaml`. The
file did not exist. `los resume` quietly recovered through "last recorded
result", the app's Home — which reads only that pointer — said "Nothing to
resume yet", and activating a stage in another subject changed neither: both
interfaces kept sending the learner back to the subject he had just left
(audit `workbench/audits/synthetic-learner-2026-09-12`, F05).

These pin the contract that replaced it: every explicit progress action names
the stage it made current, in the same transaction as the records that moved,
and nothing derived outranks it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from gateway_helpers import approved_v2_cli
from repo_builders import _add_material_overview, add_curriculum, run_los

POINTER = "curriculum/resume.yaml"
UNIT_DIR = "curriculum/modules/module-demo/units/unit-demo-l01"


def _pointer(root: Path) -> dict:
    path = root / POINTER
    if not path.is_file():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _progress(root: Path, status: str, key: str, *,
              unit: str = "unit-demo-l01", stage: str = "stage-demo",
              study_map: str = "study-map-demo-l01"):
    return approved_v2_cli(
        root, "stage-progress", unit, stage, status,
        artifact_ids=[unit, study_map],
        idempotency_key=key,
    )


def _runtime_target(root: Path) -> None:
    """Give the demo stage a requirement so evidence can be recorded here."""
    staged = root / UNIT_DIR / "study-map.yaml"
    data = yaml.safe_load(staged.read_text(encoding="utf-8"))
    data["stages"][0]["concepts"] = ["concept-expected-value"]
    data["stages"][0]["runtime_target"] = {
        "concept": "concept-expected-value",
        "capability": {"kind": "explain", "operands": ["expectation"]},
        "conditions": ["unfamiliar-example"],
        "evidence_spec": ["explain-reason"],
    }
    staged.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
                      encoding="utf-8")


@pytest.fixture()
def repo(mini_repo: Path) -> Path:
    add_curriculum(mini_repo)
    _add_material_overview(mini_repo)
    return mini_repo


def test_activating_a_stage_sets_the_destination(repo: Path):
    """The stale fixture pointer is replaced, not merged with."""
    (repo / POINTER).write_text(
        yaml.safe_dump({
            "type": "resume-pointer", "module_id": "module-demo",
            "unit_id": "unit-demo-l01", "study_map_id": "study-map-demo-l01",
            "stage_id": "stage-demo", "updated": "2020-01-01",
        }, sort_keys=False), encoding="utf-8")
    proc = _progress(repo, "active", "resume-activate")
    assert proc.returncode == 0, proc.stderr
    pointer = _pointer(repo)
    assert {key: pointer.get(key) for key in
            ("type", "module_id", "unit_id", "study_map_id", "stage_id")} == {
        "type": "resume-pointer",
        "module_id": "module-demo",
        "unit_id": "unit-demo-l01",
        "study_map_id": "study-map-demo-l01",
        "stage_id": "stage-demo",
    }
    assert pointer["updated"] != "2020-01-01"


def test_the_pointer_commits_inside_the_same_transaction(repo: Path):
    """Not an untracked side write: the receipt covers it, or it did not happen."""
    proc = _progress(repo, "active", "resume-receipt")
    assert proc.returncode == 0, proc.stderr
    receipt_path = json.loads(proc.stdout)["result"]["receipt_path"]
    receipt = yaml.safe_load((repo / receipt_path).read_text(encoding="utf-8"))
    written = json.dumps(receipt)
    assert POINTER in written, (
        "the resume pointer must appear in its transaction's receipt"
    )


def test_a_failed_pointer_write_rolls_the_whole_change_back(repo: Path):
    """The coupling holds in both directions.

    A destination that moved while the records did not would send him to a
    stage nothing activated; records that moved while the destination did not
    is the F05 defect itself. Blocking the pointer's own atomic temp name must
    therefore take the study map and the unit down with it.
    """
    before_map = (repo / UNIT_DIR / "study-map.yaml").read_text(encoding="utf-8")
    before_unit = (repo / UNIT_DIR / "unit.yaml").read_text(encoding="utf-8")
    before_pointer = (repo / POINTER).read_text(encoding="utf-8")
    blocked = repo / "curriculum/.resume.yaml.tmp"
    blocked.mkdir()
    proc = _progress(repo, "active", "resume-rollback")
    assert proc.returncode == 2
    assert "Traceback" not in proc.stdout + proc.stderr
    assert (repo / POINTER).read_text(encoding="utf-8") == before_pointer
    assert (repo / UNIT_DIR / "study-map.yaml").read_text(encoding="utf-8") == before_map
    assert (repo / UNIT_DIR / "unit.yaml").read_text(encoding="utf-8") == before_unit
    blocked.rmdir()
    assert _progress(repo, "active", "resume-rollback-retry").returncode == 0
    assert _pointer(repo)["stage_id"] == "stage-demo"


def test_pausing_keeps_the_destination_on_the_paused_stage(repo: Path):
    """Pausing means "I am coming back to this", so it stays the destination."""
    assert _progress(repo, "active", "resume-pause-activate").returncode == 0
    assert _progress(repo, "paused", "resume-pause").returncode == 0
    assert _pointer(repo)["stage_id"] == "stage-demo"


def test_completing_follows_the_stage_that_became_current(repo: Path):
    """Finish one stage and the destination is whatever the map made current."""
    assert _progress(repo, "active", "resume-complete-activate").returncode == 0
    proc = _progress(repo, "complete", "resume-complete")
    assert proc.returncode == 0, proc.stderr
    current = json.loads(proc.stdout)["result"]["current_stage"]
    assert _pointer(repo)["stage_id"] == current


def test_the_pointer_outranks_a_more_recent_result_elsewhere(repo: Path):
    """The wrong answer F05 measured: evidence chronology is not intent.

    A result recorded against one stage says nothing about which subject he
    chose to sit down with next, so `resume` must follow the explicit choice.
    """
    _runtime_target(repo)
    assert _progress(repo, "active", "resume-intent").returncode == 0
    observed = run_los(repo, "observe", "req-demo-l01-demo", "--activity",
                       "exercise", "--result", "partial",
                       "--condition", "unfamiliar-example")
    assert observed.returncode == 0, observed.stderr
    proc = run_los(repo, "resume", "--json")
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)["via"] == "resume pointer"


def test_recovery_is_labeled_and_never_silent(repo: Path):
    """A guess must read as a guess on the screen it produces."""
    _runtime_target(repo)
    assert _progress(repo, "active", "resume-recovery").returncode == 0
    observed = run_los(repo, "observe", "req-demo-l01-demo", "--activity",
                       "exercise", "--result", "partial",
                       "--condition", "unfamiliar-example")
    assert observed.returncode == 0, observed.stderr
    (repo / POINTER).unlink()
    proc = run_los(repo, "resume", "--json")
    assert proc.returncode == 0, proc.stderr
    via = json.loads(proc.stdout)["via"]
    assert via != "resume pointer"
    assert "resume pointer missing or stale" in via
