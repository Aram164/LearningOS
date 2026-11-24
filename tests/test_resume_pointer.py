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
from repo_builders import _add_material_overview, add_curriculum, run_los, write_yaml

from learning_os.derive.projection.manifest import build_manifest
from learning_os.derive.validation import validate
from learning_os.store.loader import load_repo

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


def test_a_failed_pointer_write_rolls_the_whole_change_back(
    repo: Path, monkeypatch: pytest.MonkeyPatch,
):
    """The coupling holds in both directions.

    A destination that moved while the records did not would send him to a
    stage nothing activated; records that moved while the destination did not
    is the F05 defect itself. Failing the pointer's atomic write mid-commit
    must therefore take the study map and the unit down with it.
    """
    from gateway_helpers import approved_v2_envelope

    import learning_os.store.transactions as transaction_module
    from learning_os.app.pipeline import run_gateway
    from learning_os.domain.failures import TransactionFailure
    from learning_os.store.contracts.capability_catalog import command_definitions
    from learning_os.store.diagnostics import tracer as diag_tracer

    before_map = (repo / UNIT_DIR / "study-map.yaml").read_text(encoding="utf-8")
    before_unit = (repo / UNIT_DIR / "unit.yaml").read_text(encoding="utf-8")
    before_pointer = (repo / POINTER).read_text(encoding="utf-8")
    envelope = approved_v2_envelope(
        repo,
        capability="stage.progress.update",
        payload={"unit_id": "unit-demo-l01", "stage_id": "stage-demo", "status": "active"},
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key="resume-rollback",
    )
    pointer_target = (repo / POINTER).resolve()
    real_write = transaction_module.atomic_write_bytes

    def fail_pointer_write(path: Path, content: bytes) -> None:
        if Path(path).resolve() == pointer_target:
            raise TransactionFailure("injected resume pointer write failure")
        real_write(path, content)

    with monkeypatch.context() as patch:
        patch.setattr(transaction_module, "atomic_write_bytes", fail_pointer_write)
        outcome = run_gateway(
            repo,
            envelope,
            requested="stage.progress.update",
            definitions=command_definitions(repo),
            attempt=diag_tracer.begin_attempt({"capability": "stage.progress.update"}),
            replay_only=False,
        )
    assert outcome.exit_code == 2
    assert "Traceback" not in outcome.stdout + outcome.stderr
    assert (repo / POINTER).read_text(encoding="utf-8") == before_pointer
    assert (repo / UNIT_DIR / "study-map.yaml").read_text(encoding="utf-8") == before_map
    assert (repo / UNIT_DIR / "unit.yaml").read_text(encoding="utf-8") == before_unit
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


def _errors(root: Path) -> list:
    return [issue for issue in validate(load_repo(root)) if issue.severity == "E"]


def _add_second_module(root: Path) -> None:
    """A second academic module that owns no units and an empty source map."""
    module = yaml.safe_load(
        (root / "curriculum/modules/module-demo/module.yaml").read_text(encoding="utf-8"))
    module.update({"id": "module-other", "title": "Other Module", "unit_order": []})
    write_yaml(root / "curriculum/modules/module-other/module.yaml", module)
    write_yaml(root / "curriculum/modules/module-other/source-map.yaml", {
        "type": "module-source-map", "module_id": "module-other", "sources": [],
    })


def test_a_pointer_to_another_valid_module_resolves_nowhere(repo: Path):
    """Every ID exists, yet the declared module does not own the unit.

    Shape-valid is not coherent: validation names the broken ownership,
    the manifest publishes no pointer, and the CLI keeps its existing
    recovery/refusal path instead of resuming into the wrong module.
    """
    _add_second_module(repo)
    assert _errors(repo) == []
    assert build_manifest(load_repo(repo), "T1")["resume_pointer"]["stage_id"] == "stage-demo"

    pointer = _pointer(repo)
    pointer["module_id"] = "module-other"
    (repo / POINTER).write_text(
        yaml.safe_dump(pointer, sort_keys=False), encoding="utf-8")

    assert [issue.code for issue in _errors(repo)] == ["REF-RESUME-OWNER"]
    assert build_manifest(load_repo(repo), "T1")["resume_pointer"] == {}
    proc = run_los(repo, "resume", "--json")
    if proc.returncode == 0:
        # A menu payload carries no via at all; either way, the CLI must
        # not resume into the wrong module.
        assert json.loads(proc.stdout).get("via") != "resume pointer"
    else:
        assert proc.returncode == 2, proc.stderr

    pointer["module_id"] = "module-demo"
    (repo / POINTER).write_text(
        yaml.safe_dump(pointer, sort_keys=False), encoding="utf-8")
    assert _errors(repo) == []
    assert build_manifest(load_repo(repo), "T1")["resume_pointer"]["stage_id"] == "stage-demo"


def test_a_pointer_to_a_map_owned_by_another_unit_resolves_nowhere(repo: Path):
    """The named map exists but belongs to a different unit of the module."""
    module_path = repo / "curriculum/modules/module-demo/module.yaml"
    module = yaml.safe_load(module_path.read_text(encoding="utf-8"))
    module["unit_order"] = ["unit-demo-l01", "unit-other-l01"]
    write_yaml(module_path, module)
    other_dir = repo / "curriculum/modules/module-demo/units/unit-other-l01"
    other_unit = yaml.safe_load(
        (repo / UNIT_DIR / "unit.yaml").read_text(encoding="utf-8"))
    other_unit.update({
        "id": "unit-other-l01", "title": "Other lecture", "order": 2,
        "current_study_map": "study-map-other-l01",
    })
    write_yaml(other_dir / "unit.yaml", other_unit)
    other_map = yaml.safe_load(
        (repo / UNIT_DIR / "study-map.yaml").read_text(encoding="utf-8"))
    other_map.update({
        "id": "study-map-other-l01", "unit_id": "unit-other-l01",
        "current_stage": "stage-other",
    })
    note_rel = ("curriculum/modules/module-demo/units/unit-other-l01"
                "/stages/stage-other/notes.md")
    (repo / note_rel).parent.mkdir(parents=True, exist_ok=True)
    (repo / note_rel).write_text("", encoding="utf-8")
    other_map["stages"] = [dict(other_map["stages"][0], id="stage-other",
                                title="Other stage", working_note=note_rel)]
    write_yaml(other_dir / "study-map.yaml", other_map)
    assert _errors(repo) == []

    pointer = _pointer(repo)
    pointer.update({"study_map_id": "study-map-other-l01", "stage_id": "stage-other"})
    (repo / POINTER).write_text(
        yaml.safe_dump(pointer, sort_keys=False), encoding="utf-8")

    assert [issue.code for issue in _errors(repo)] == ["REF-RESUME-OWNER"]
    assert build_manifest(load_repo(repo), "T1")["resume_pointer"] == {}
    proc = run_los(repo, "resume", "--json")
    if proc.returncode == 0:
        assert json.loads(proc.stdout).get("via") != "resume pointer"
    else:
        assert proc.returncode == 2, proc.stderr


def test_a_malformed_pointer_id_resolves_nowhere(repo: Path):
    """A non-string ID is a schema error, never a crash.

    Validation names the shape, the manifest publishes no pointer, and
    the CLI keeps its normal recovery/refusal path.
    """
    pointer = _pointer(repo)
    pointer["module_id"] = []
    (repo / POINTER).write_text(
        yaml.safe_dump(pointer, sort_keys=False), encoding="utf-8")

    assert "SCHEMA" in [issue.code for issue in _errors(repo)]
    assert build_manifest(load_repo(repo), "T1")["resume_pointer"] == {}
    proc = run_los(repo, "resume", "--json")
    assert "Traceback" not in proc.stdout + proc.stderr
    if proc.returncode == 0:
        assert json.loads(proc.stdout).get("via") != "resume pointer"
    else:
        assert proc.returncode == 2, proc.stderr


def test_recovery_is_labeled_and_never_silent(repo: Path):
    """A guess must read as a guess on the screen it produces. With
    selectable choices, recovery asks: the menu carries the labeled trail
    as clearly secondary context, and nothing claims a destination."""
    _runtime_target(repo)
    assert _progress(repo, "active", "resume-recovery").returncode == 0
    observed = run_los(repo, "observe", "req-demo-l01-demo", "--activity",
                       "exercise", "--result", "partial",
                       "--condition", "unfamiliar-example")
    assert observed.returncode == 0, observed.stderr
    (repo / POINTER).unlink()
    proc = run_los(repo, "resume", "--json")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["contract"] == "resume-study-options"
    assert "via" not in payload
    historical = payload["recovery"]["historical"]
    assert historical["via"] != "resume pointer"
    assert "resume pointer missing or stale" in historical["via"]
    assert payload["recovery"]["pointer"] == "missing"


def test_a_terminal_stage_pointer_still_resolves_exactly(repo: Path):
    """Completion is where the learner stopped, not a reason to disown the
    pointer: the resolver applies no status filter, so a pointer naming a
    terminal stage opens exactly that stage."""
    assert _progress(repo, "active", "resume-terminal-activate").returncode == 0
    proc = _progress(repo, "complete", "resume-terminal-complete")
    assert proc.returncode == 0, proc.stderr
    assert _pointer(repo)["stage_id"] == "stage-demo"
    result = run_los(repo, "resume", "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["via"] == "resume pointer"
    assert payload["content"]["stage"]["stage_id"] == "stage-demo"
