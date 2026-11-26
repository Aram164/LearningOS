"""The interface's interrupted-write recovery, against this Core.

A mock gateway once confirmed every envelope the UI sent, including the ones
the real gateway refused — so the suite was green while every capture in the
vault was being rejected. Recovery cannot be verified that way at all: its
entire premise is "Core has already seen this exact request", and only Core can
say whether it recognises it.

So this test builds a real mini repository, runs the UI's real `GatewayClient`
through `obsidian-ui/tests/gateway-recovery-harness.js`, and then asks the
filesystem the only question that matters: after an interruption and a replay,
is there **one** canonical file, **one** receipt, and **one** idempotency
entry?

Standalone Core runs skip when the sibling UI is absent, because Core is
usable without it. `make system-check` is the paired gate and requires it —
see the `test_the_paired_gate_requires_this_harness` guard below.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

UI_ROOT = Path(__file__).resolve().parents[2] / "obsidian-ui"
HARNESS = UI_ROOT / "tests" / "gateway-recovery-harness.js"

pytestmark = [
    pytest.mark.skipif(
        not HARNESS.is_file() or shutil.which("node") is None,
        reason="the sibling obsidian-ui harness (or Node) is not available",
    ),
    pytest.mark.paired,
]


#: The first stage's rows before the harness appends to it (`_structural_fixture`).
STRUCTURAL_FIXTURE_RESOURCE_IDS = (
    "resource-original",
    "resource-demo-book-appendix",
    None,
    "resource-second",
)


def _run_harness(repo_root: Path, mini_repo: Path) -> dict:
    result = subprocess.run(
        [
            "node",
            str(HARNESS),
            "--core-root", str(repo_root),
            "--repo", str(mini_repo),
            "--python", sys.executable,
        ],
        cwd=str(UI_ROOT),
        capture_output=True,
        text=True,
        timeout=900,
        env={**os.environ, "TMPDIR": str(mini_repo.parent)},
    )
    assert result.returncode == 0, (
        f"the UI recovery harness failed\n--- stdout ---\n{result.stdout}"
        f"\n--- stderr ---\n{result.stderr}"
    )
    marker = [line for line in result.stdout.splitlines()
              if line.startswith("HARNESS_RESULT ")]
    assert marker, f"the harness printed no result:\n{result.stdout}"
    return json.loads(marker[-1][len("HARNESS_RESULT "):])


def _idempotency_entries(mini_repo: Path) -> dict:
    ledger = mini_repo / "operations" / "transactions" / "idempotency.yaml"
    if not ledger.is_file():
        return {}
    return yaml.safe_load(ledger.read_text(encoding="utf-8"))["entries"]


@pytest.fixture(scope="module")
def recovery_run(repo_root: Path, tmp_path_factory) -> tuple[dict, Path]:
    """One harness run, shared by the assertions below.

    Each scenario spawns the real CLI several times, so running the harness
    once and asking several questions of the result keeps this test honest
    without making it the slowest thing in the suite. `build_mini_repo` is the
    same builder the `mini_repo` fixture uses — the synthetic repository is
    described in exactly one place.
    """
    from conftest import build_mini_repo
    from repo_builders import _structural_fixture

    mini = build_mini_repo(tmp_path_factory.mktemp("ui-recovery"))
    _structural_fixture(mini)
    return _run_harness(repo_root, mini), mini


def _receipt(mini: Path, scenario: dict) -> dict:
    path = mini / scenario["receipt_path"]
    assert path.is_file(), f"{scenario['receipt_path']} is not a receipt in this repository"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_an_interrupted_capture_replays_into_one_canonical_write(recovery_run):
    results, mini = recovery_run
    scenario = results["textCaptureReplay"]
    assert scenario["attempts"] == 2, "one interruption earns exactly one replay"
    assert scenario["identical"] is True
    assert scenario["replayed"] is True, (
        "Core has to recognise the retry as the transaction it already committed"
    )
    receipt = _receipt(mini, scenario)
    assert receipt["id"] == scenario["transaction_id"]
    writes = [entry["path"] for entry in receipt["writes"]]
    assert len(writes) == 1 and (mini / writes[0]).is_file()


def test_a_restart_recovers_the_original_transaction(recovery_run):
    results, mini = recovery_run
    scenario = results["restartRecovery"]
    assert scenario["identical"] is True, "the restarted app resent the persisted bytes"
    assert scenario["replayed"] is True
    receipt = _receipt(mini, scenario)
    assert receipt["request"]["idempotency_key"] == scenario["idempotency_key"]
    assert receipt["id"] == scenario["transaction_id"]
    assert receipt["request"]["channel"] == "ui"


def test_a_faulted_receipt_publication_stays_unresolved_then_replays(recovery_run):
    """A real faulted Core response reaches the real UI client (S1).

    Core's receipt-parent sync fails after the receipt is visible; the UI
    must keep the original envelope blocked, then a restarted instance
    replays those exact bytes into one canonical effect.
    """
    results, mini = recovery_run
    scenario = results["faultedPublicationReplay"]
    assert scenario["blocked_phase"] == "blocked"
    assert scenario["envelope_preserved"] is True
    assert scenario["identical"] is True
    assert scenario["replayed"] is True
    receipt = _receipt(mini, scenario)
    assert receipt["id"] == scenario["transaction_id"]
    assert receipt["request"]["idempotency_key"] == scenario["idempotency_key"]


def test_a_garden_seed_replays_under_its_request_scoped_guard(recovery_run):
    results, mini = recovery_run
    scenario = results["gardenSeedReplay"]
    assert scenario["replayed"] is True
    assert scenario["identical"] is True
    entry = _idempotency_entries(mini)[scenario["idempotency_key"]]
    assert entry["capability"] == "garden.seed.create"


def test_a_committed_file_capture_replays_without_rereading_its_source(recovery_run):
    results, mini = recovery_run
    scenario = results["fileCaptureReplayAfterSourceChanged"]
    assert scenario["identical"] is True, (
        "a rebuilt envelope would have had to re-hash a file that was deleted"
    )
    assert scenario["replayed"] is True
    assert (mini / scenario["receipt_path"]).is_file()


def test_an_interrupted_compact_append_replays_into_one_placement(recovery_run):
    """The learner's reviewed click, through the real client, against real Core."""
    results, mini = recovery_run
    scenario = results["compactAppendReplay"]
    assert scenario["attempts"] == 2, "one interruption earns exactly one replay"
    assert scenario["identical"] is True
    assert scenario["replayed"] is True
    assert scenario["approval_kind"] == "direct-user-gesture"
    receipt = _receipt(mini, scenario)
    assert receipt["id"] == scenario["transaction_id"]
    assert receipt["request"]["channel"] == "ui"
    study_map = yaml.safe_load(
        (mini / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml")
        .read_text(encoding="utf-8"))
    assert [row.get("id") for row in study_map["stages"][0]["resources"]] == [
        *STRUCTURAL_FIXTURE_RESOURCE_IDS, "resource-ui-interrupted-append",
    ], "the existing rows keep their order and the replay adds nothing"


def test_every_replay_produces_exactly_one_receipt_and_one_ledger_entry(recovery_run):
    results, mini = recovery_run
    entries = _idempotency_entries(mini)
    transactions = [scenario["transaction_id"] for scenario in results.values()]
    assert len(set(transactions)) == len(transactions), (
        "each scenario must own a distinct transaction"
    )
    for scenario in results.values():
        key = scenario["idempotency_key"]
        assert key in entries, f"{key} left no idempotency entry"
        assert entries[key]["transaction_id"] == scenario["transaction_id"], (
            "a replay must resolve to the transaction that already happened"
        )
    assert len(entries) == len(results), (
        "one ledger entry per gesture — a replay that created a second key would "
        "have created a second write"
    )
    receipts = sorted(
        (mini / "operations" / "transactions").glob("transaction-*.yaml")
    )
    assert len(receipts) == len(results), (
        f"expected one receipt per gesture, found {[p.name for p in receipts]}"
    )
    # And the canonical files themselves: four captures (three text —
    # including the faulted-publication replay — and one file) and one
    # Garden seed. Five gestures, five artefacts, no duplicates.
    inbox = sorted(p.name for p in (mini / "work" / "inbox").iterdir())
    garden = sorted(p.name for p in (mini / "knowledge" / "garden").iterdir())
    assert len(inbox) == 4, f"one canonical file per capture, found {inbox}"
    assert len(garden) == 1, f"one canonical file per seed, found {garden}"


def test_the_paired_gate_requires_this_harness(repo_root: Path):
    """`make system-check` must fail loudly if the harness disappears.

    A cross-repository test that silently skips is worse than no test: the gate
    stays green while the thing it was added to verify stops being verified.
    """
    makefile = (repo_root / "Makefile").read_text(encoding="utf-8")
    assert "tests/test_ui_gateway_recovery.py" in makefile, (
        "system-check must require the Core-side recovery driver by name"
    )
    assert "gateway-recovery-harness.js" in makefile, (
        "system-check must assert the UI recovery harness is present"
    )
    assert "tests/test_ui_phase3_live_writes.py" in makefile, (
        "system-check must require the Core-side live-writes driver by name"
    )
    assert "live-writes-harness.js" in makefile, (
        "system-check must assert the UI live-writes harness is present"
    )
    assert "tests/test_operations_gate.py" in makefile, (
        "system-check must require the Core-side operations-gate driver by name"
    )
    assert "operations-gate-harness.js" in makefile, (
        "system-check must assert the UI operations-gate harness is present"
    )


@pytest.mark.parametrize(
    "omitted_rel",
    [
        "repository/tests/test_ui_gateway_recovery.py",
        "obsidian-ui/tests/gateway-recovery-harness.js",
        "repository/tests/test_ui_phase3_live_writes.py",
        "obsidian-ui/tests/live-writes-harness.js",
        "repository/tests/test_operations_gate.py",
        "obsidian-ui/tests/operations-gate-harness.js",
    ],
)
def test_system_check_refuses_when_required_harness_is_missing(
    repo_root: Path, tmp_path: Path, omitted_rel: str,
):
    """Invoke `make system-check` in a temp pair and prove missing any required harness fails."""
    pair_root = tmp_path / "pair"
    core = pair_root / "repository"
    ui = pair_root / "obsidian-ui"
    (core / "tests").mkdir(parents=True)
    (ui / "tests").mkdir(parents=True)
    shutil.copy(repo_root / "Makefile", core / "Makefile")
    (ui / "package.json").write_text('{"name": "obsidian-ui"}\n', encoding="utf-8")

    required_files = [
        "repository/tests/test_ui_gateway_recovery.py",
        "obsidian-ui/tests/gateway-recovery-harness.js",
        "repository/tests/test_ui_phase3_live_writes.py",
        "obsidian-ui/tests/live-writes-harness.js",
        "repository/tests/test_operations_gate.py",
        "obsidian-ui/tests/operations-gate-harness.js",
    ]
    for rel in required_files:
        if rel != omitted_rel:
            (pair_root / rel).write_text("// stub\n", encoding="utf-8")

    stub_bin = tmp_path / "bin"
    stub_bin.mkdir()
    for tool_name in ("node", "npm"):
        stub = stub_bin / tool_name
        stub.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        stub.chmod(0o755)
    stub_py = tmp_path / "stub_py.py"
    stub_py.write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
    env = {**os.environ, "PATH": f"{stub_bin}{os.pathsep}{os.environ['PATH']}"}

    proc = subprocess.run(
        ["make", "--silent", "system-check", f"PY={sys.executable} {stub_py}"],
        cwd=core,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode != 0
    missing_name = Path(omitted_rel).name
    assert missing_name in proc.stderr, proc.stderr

    # Positive control: restoring the omitted file makes the guard succeed.
    (pair_root / omitted_rel).write_text("// stub\n", encoding="utf-8")
    ok_proc = subprocess.run(
        ["make", "--silent", "system-check", f"PY={sys.executable} {stub_py}"],
        cwd=core,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert ok_proc.returncode == 0, ok_proc.stdout + ok_proc.stderr
