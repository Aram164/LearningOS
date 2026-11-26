"""Engine-effect neutrality: the marked engine matches the baseline (S03).

Re-runs the six ``arch_engine_cases`` scenarios and compares them with
``tests/architecture/engine-baseline.json``, recorded on the unmodified
engine. The phase marker (Task 2) must not change any effect.
"""

from __future__ import annotations

import contextvars
import hashlib
import json
import shutil
import sys
import threading
from pathlib import Path

import arch_engine_cases
import pytest
from history_baselines import historical_files

from learning_os.store.transactions import (
    _engine_phase,
    current_engine_phase,
)

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
    # (a) The marker is reset after every case, including exception cases.
    assert current_engine_phase() is None


def test_historical_fixture_matches_frozen_inventory(tmp_path: Path):
    """Historical engine fixtures exclude newer contracts and restore archived ones."""
    historical = historical_files("074f4717e14527798752de84b3c9c4e88348b658")
    expected_paths = set(historical) - {"system/contracts/local-attachments.yaml"}

    root = arch_engine_cases._build_root(tmp_path, "inventory-check")
    actual: dict[str, bytes] = {}
    for contract_root in ("system/schema", "system/contracts"):
        for target in (root / contract_root).rglob("*"):
            if target.is_file():
                actual[target.relative_to(root).as_posix()] = target.read_bytes()

    assert set(actual) == expected_paths
    for relpath in expected_paths:
        assert actual[relpath] == historical[relpath]

    # Explicit positive check: archived manifest-v15 schema is restored with exact bytes.
    v15_rel = "system/contracts/manifest-v15.schema.json"
    assert hashlib.sha256(actual[v15_rel]).hexdigest() == hashlib.sha256(historical[v15_rel]).hexdigest()

    # Explicit negative check: post-074f4717 current contracts never leak in.
    for leaked in (
        "system/contracts/task-scope.yaml",
        "system/contracts/review-consolidation.yaml",
        "system/contracts/review-consolidation.schema.json",
        "system/contracts/agent-plan-input.schema.json",
        "system/contracts/agent-plan-report.schema.json",
    ):
        assert not (root / leaked).exists()


def test_task_scope_mutation_leaves_historical_engine_baseline_unchanged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """Mutating task-scope.yaml or adding a contract in a disposable copy preserves baseline."""
    import conftest

    mutated_repo = tmp_path / "mutated-repo"
    shutil.copytree(conftest.REPO_ROOT / "system" / "schema", mutated_repo / "system" / "schema")
    shutil.copytree(conftest.REPO_ROOT / "system" / "contracts", mutated_repo / "system" / "contracts")
    task_scope = mutated_repo / "system" / "contracts" / "task-scope.yaml"
    task_scope.write_text(
        task_scope.read_text(encoding="utf-8") + "\n# synthetic disposable mutation\n",
        encoding="utf-8",
    )
    (mutated_repo / "system" / "contracts" / "synthetic-future.yaml").write_text(
        "future: true\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(conftest, "REPO_ROOT", mutated_repo)
    monkeypatch.setattr(conftest, "_MINI_REPO_TEMPLATE", None)
    mutated_template: Path | None = None
    try:
        actual = arch_engine_cases.run_all(tmp_path / "engine-run")
        mutated_template = conftest._MINI_REPO_TEMPLATE
    finally:
        if mutated_template is not None:
            shutil.rmtree(mutated_template.parent, ignore_errors=True)

    assert actual == _load_baseline()


def _mini_root(tmp_path: Path):
    from conftest import build_mini_repo
    from repo_builders import add_curriculum

    root = build_mini_repo(tmp_path).resolve()
    add_curriculum(root)
    return root


def test_callbacks_see_no_phase(tmp_path: Path):
    """(b) Caller callbacks run outside any marked region."""
    import arch_engine_cases as cases

    from learning_os.store.transactions import TransactionService

    seen: dict[str, object] = {}

    def _transaction_writes(transaction_id: str):
        seen["transaction_writes"] = current_engine_phase()
        return {}

    def _validate_ok():
        seen["validate_state"] = current_engine_phase()
        return []

    def _publish():
        seen["publish"] = current_engine_phase()
        return None

    def _touched(paths):
        seen["touched"] = current_engine_phase()

    root = _mini_root(tmp_path / "callbacks-ok")
    target = root / "work" / "inbox" / "callback-ok.md"
    with cases._pinned_tz():
        TransactionService(root, clock=cases._clock, _unmediated_test_only=True).commit(
            capability="capture.create",
            writes={target: "ok\n"},
            artifact_ids=["arch-callbacks"],
            transaction_writes=_transaction_writes,
            validate_state=_validate_ok,
            publish=_publish,
            touched=_touched,
        )
    assert seen == {
        "transaction_writes": None,
        "validate_state": None,
        "publish": None,
        "touched": None,
    }
    assert current_engine_phase() is None


def test_rollback_publish_sees_no_phase(tmp_path: Path):
    """(b) Rollback republication runs outside any marked region."""
    import arch_engine_cases as cases

    from learning_os.store.transactions import TransactionFailure, TransactionService

    seen: dict[str, object] = {}

    def _validate_fails():
        seen["validate_state"] = current_engine_phase()
        return ["forced validation failure"]

    def _rollback_publish():
        seen["rollback_publish"] = current_engine_phase()

    root = _mini_root(tmp_path / "callbacks-rollback")
    target = root / "work" / "inbox" / "callback-rollback.md"
    with cases._pinned_tz():
        with pytest.raises(TransactionFailure):
            TransactionService(root, clock=cases._clock, _unmediated_test_only=True).commit(
                capability="capture.create",
                writes={target: "will roll back\n"},
                artifact_ids=["arch-callbacks-rollback"],
                validate_state=_validate_fails,
                rollback_publish=_rollback_publish,
            )
    assert seen == {"validate_state": None, "rollback_publish": None}
    assert current_engine_phase() is None


def test_phase_does_not_leak_into_threads():
    """(c) A thread started inside a marked region sees no marker."""
    if sys.flags.thread_inherit_context:
        pytest.skip("this build inherits context into new threads")
    assert not sys.flags.thread_inherit_context
    seen: list = []

    def _target():
        seen.append(current_engine_phase())

    with _engine_phase("apply"):
        thread = threading.Thread(target=_target)
        thread.start()
        thread.join()
    assert seen == [None]
    assert current_engine_phase() is None


def test_phase_does_not_leak_into_fresh_context():
    """(c) A fresh context sees no marker."""
    with _engine_phase("apply"):
        assert contextvars.Context().run(current_engine_phase) is None
    assert current_engine_phase() is None


def test_copied_context_carries_marker_by_design():
    # copy_context() taken inside a marked region carries the marker by
    # design (Codex K25). That is why the engine wraps one call per `with`:
    # a copied context must never carry a marker into a caller callback.
    with _engine_phase("apply"):
        copied = contextvars.copy_context()
        assert copied.run(current_engine_phase) == "apply"
    assert current_engine_phase() is None
